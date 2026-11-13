"""Đối chiếu A1 scalar/vector trên GPU đã cấp, tiến trình và nguồn riêng.

Script không gọi Modal, không sửa source/trọng số tiến trình training. Fixture
tổng hợp batch128x200, 100 target/window. Output không nghiệm thu migration.
"""
import argparse
from dataclasses import replace
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import threading
import time
import traceback

OLD_SHA = '997fe9191388738954c0f4aeb1f7062c9c1e3cf6646a5b2486d2618b5c02c177'
NEW_SHA = '3a3a45634ba7ea84520472f57c1828b28a705b9d2a8a10f8476510cf682507e5'
TOLERANCES = dict(loss=dict(atol=1e-6, rtol=1e-6), probabilities=dict(atol=1e-7, rtol=1e-6),
    gradients=dict(atol=1e-7, rtol=1e-5), parameters=dict(atol=2e-7, rtol=2e-5),
    adam_moments=dict(atol=1e-7, rtol=1e-5))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('/opt/kltn'))
    parser.add_argument('--new-native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    external = args.new_native.resolve()
    output = args.output.resolve()
    if external.is_relative_to(root) or not external.is_file() or len(external.parents) < 4:
        parser.error('New native phải ở cây nguồn riêng đủ sâu, bên ngoài root đang training')
    if output.exists():
        parser.error('Output mới, không ghi đè bằng chứng')
    old_path = root / 'src/knowledge_tracing/akt/research_graph_model.py'
    if sha(old_path) != OLD_SHA or sha(external) != NEW_SHA:
        parser.error('Nguồn old/new khác SHA đã kiểm, dừng trước CUDA')
    output.mkdir(parents=True)
    started = time.monotonic()
    result = dict(status='FAILED_PRESERVED', scope='H100_SYNTHETIC_A1_SCALAR_VECTOR_PARITY',
        source_sha256=dict(old=OLD_SHA, new=NEW_SHA), tolerances=TOLERANCES,
        max_wall_seconds=90, max_additional_uss_bytes=2*1024**3,
        training_process_changed=False, fixture_optimizer_steps_per_model_per_alpha=1,
        alphas=[], data='synthetic_only', training_epochs=0, new_cloud_job_started=False)
    stop = threading.Event()
    monitor = None
    old_signal = {}
    def deadline(_signum, _frame):
        raise TimeoutError('GPU parity probe vượt 90 giây')
    def memory_exhausted(_signum, _frame):
        raise MemoryError('GPU parity probe vượt thêm 2 GiB private USS')
    try:
        old_signal[signal.SIGALRM] = signal.signal(signal.SIGALRM, deadline)
        old_signal[signal.SIGUSR1] = signal.signal(signal.SIGUSR1, memory_exhausted)
        signal.alarm(90)
        import psutil
        import torch
        process = psutil.Process()
        assert process.memory_info().rss < 6*1024**3, 'Torch base RSS exceeds sixGiB'
        baseline_rss = process.memory_info().rss
        baseline_uss = process.memory_full_info().uss
        result['baseline_uss_bytes'] = baseline_uss
        result['baseline_rss_bytes'] = baseline_rss
        result['memory_scope_vi'] = 'Tối đa2GiB private tăng thêm sau import Torch, tối đa6GiB RSS toàn tiến trình; import CUDA Torch đã cần khoảng3,4GiB trong VM này.'
        result['peak_rss_bytes'] = baseline_rss
        def sample_memory():
            while not stop.wait(.2):
                rss = process.memory_info().rss
                result['peak_rss_bytes'] = max(result['peak_rss_bytes'], rss)
                uss = process.memory_full_info().uss
                result['peak_uss_bytes'] = max(result.get('peak_uss_bytes',baseline_uss),uss)
                if uss-baseline_uss > 2*1024**3 or rss > 6*1024**3:
                    os.kill(os.getpid(), signal.SIGUSR1)
                    return
        monitor = threading.Thread(target=sample_memory, daemon=True)
        monitor.start()
        os.environ.update(CUBLAS_WORKSPACE_CONFIG=':4096:8', CUDA_VISIBLE_DEVICES='0',
            OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
            PYTHONDONTWRITEBYTECODE='1')
        sys.path.insert(0, str(root/'src'))
        import numpy as np
        import torch
        from knowledge_tracing.akt.config import AKTConfig, ResearchCUDAExecutionProfile
        from knowledge_tracing.akt import research_graph_model as old_module
        from knowledge_tracing.akt.encoding import ExerciseEncoding
        from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView, JunyiResearchEncoding
        from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition, JunyiGraphPhaseSession
        from knowledge_tracing.akt.research_junyi_roles import make_junyi_research_roles
        from knowledge_tracing.akt.tensors import collate_windows
        from knowledge_tracing.akt.types import KTEvent, LearnerEvents
        from knowledge_tracing.akt.windows import iter_windows
        from knowledge_tracing.shared_kt import PrerequisiteGraph, StableVocabulary
        assert Path(old_module.__file__).resolve() == old_path
        spec = importlib.util.spec_from_file_location('knowledge_tracing.akt.vector_probe_native', external)
        assert spec is not None and spec.loader is not None
        new_module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = new_module
        spec.loader.exec_module(new_module)
        assert new_module.ResearchGraphNative is not old_module.ResearchGraphNative
        torch.set_num_threads(2)
        torch.set_default_dtype(torch.float32)
        torch.use_deterministic_algorithms(True, warn_only=False)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cudnn.benchmark = False
        torch.set_float32_matmul_precision('highest')
        assert torch.cuda.is_available() and torch.cuda.device_count() == 1
        result.update(gpu=torch.cuda.get_device_name(0), torch=torch.__version__, cuda=torch.version.cuda)
        assert 'H100' in result['gpu'], 'Probe chỉ chạy trên H100 đã cấp'
        profile = ResearchCUDAExecutionProfile(16*1024**3, recipe_id='cgakt-cuda-fp32-batch128-v2')
        torch.cuda.set_per_process_memory_fraction(profile.max_vram_bytes/torch.cuda.get_device_properties(0).total_memory, 0)
        config = replace(AKTConfig(), phase='junyi-research', device='cuda', outer_fold=4,
            execution_enabled=True, run_id='a1-vector-parity-check',
            output_dir=root/'experiments/akt/results/a1-vector-parity-check', batch_size=128,
            protocol_version='akt-nr-exercise-v2-batch128', max_train_users=640, max_val_users=64,
            max_targets_per_side=25600, max_total_targets=25600, max_steps=1,
            max_seconds=85, max_wall_seconds=90, max_rss_bytes=2*1024**3, min_available_ram_bytes=1)
        roles = make_junyi_research_roles([(str(index), index % 5, 'development') for index in range(1000)])
        train = JunyiPhaseView(roles, 'select_train80', roles.train_users, roles.identity)
        values = tuple(['A', 'B', 'C']+[f'fixture-{index:03d}' for index in range(714)])
        encoding = JunyiResearchEncoding(ExerciseEncoding(StableVocabulary(values), {value:1 for value in values}), train)
        condition = JunyiGraphCondition(encoding, PrerequisiteGraph.from_edges(values, (('A','C'),('B','C'))), 'f'*64)
        phase = JunyiGraphPhaseSession(condition, train)
        entries = []
        for index, user in enumerate(train.users[:128]):
            learner = LearnerEvents(user, 0, tuple(KTEvent(user, ('A','B','C')[rank%3], rank+1,
                index*200+rank+1, 1 if rank%3 != 2 else (index+rank)%2, 0, 0) for rank in range(200)))
            candidates = tuple(iter_windows(learner, encoding.native, training=True))
            assert len(candidates) == 2
            entries.append(candidates[1])
        windows = tuple(entry.window for entry in entries)
        evidence = tuple(phase.prefix_evidence(window) for window in windows)
        batch = collate_windows(windows, n_items=717, device='cuda:0', targets=[entry.targets for entry in entries])
        assert tuple(batch.q_data.shape) == (128,200) and int((batch.loss_targets>=0).sum()) == 12800
        result.update(batch_shape=[128,200], targets=12800, vocabulary=717,
            active_targets=sum(any(parent.support>0 for parent in item.audit.parents)
                               for row in evidence for item in row if item is not None))
        assert result['active_targets'] > 0
        torch.manual_seed(42)
        old = old_module.ResearchGraphNative(config=config, n_items=717, condition=condition, cuda_profile=profile)
        new = new_module.ResearchGraphNative(config=config, n_items=717, condition=condition, cuda_profile=profile)
        initial = {name:value.detach().cpu().clone() for name,value in old.state_dict().items()}
        result['fixture_prepared_seconds'] = time.monotonic()-started

        def measured_step(native, optimizer):
            native.train()
            optimizer.zero_grad(set_to_none=True)
            timings = {}
            def measure(name, operation):
                torch.cuda.synchronize()
                at = time.perf_counter()
                value = operation()
                torch.cuda.synchronize()
                timings[name] = time.perf_counter()-at
                return value
            torch.cuda.reset_peak_memory_stats()
            measure('bind', lambda: native.bind(batch, evidence, enabled=True))
            loss, probabilities, count = measure('forward', lambda: native(batch.q_data,batch.qa_data,batch.loss_targets))
            measure('backward', lambda: (loss/count).backward())
            gradients = {name:None if parameter.grad is None else parameter.grad.detach().cpu().clone()
                         for name,parameter in native.named_parameters()}
            norm = measure('clip', lambda: torch.nn.utils.clip_grad_norm_(native.parameters(), config.max_grad_norm,
                                                                         error_if_nonfinite=True))
            measure('optimizer', optimizer.step)
            snapshot = dict(loss=loss.detach().cpu(), probabilities=probabilities.detach().cpu(), count=count.detach().cpu(),
                gradients=gradients, parameters={name:value.detach().cpu().clone() for name,value in native.named_parameters()},
                moments={name:{key:value.detach().cpu().clone() if torch.is_tensor(value) else value
                               for key,value in optimizer.state[parameter].items()}
                         for name,parameter in native.named_parameters()},
                norm=norm.detach().cpu(), cpu_rng=torch.get_rng_state(), cuda_rng=torch.cuda.get_rng_state(0))
            return snapshot, dict(stages_seconds=timings, staged_seconds=sum(timings.values()),
                peak_allocated_vram_bytes=torch.cuda.max_memory_allocated(),
                peak_reserved_vram_bytes=torch.cuda.max_memory_reserved(),
                timing_scope='CUDA-synchronized stages, excludes CPU copies of gradient/parameter comparison snapshots')

        for index, alpha in enumerate((0., .75)):
            record = dict(alpha=alpha, status='RUNNING')
            result['alphas'].append(record)
            for native in (old,new):
                native.load_state_dict(initial, strict=True)
                with torch.no_grad():
                    native.alpha.fill_(alpha)
            optimizers = {name:torch.optim.Adam(native.parameters(), lr=config.lr, betas=config.betas, eps=config.eps,
                weight_decay=config.weight_decay, foreach=False, fused=False)
                for name,native in (('old',old),('new',new))}
            rng_cpu = torch.get_rng_state().clone()
            rng_cuda = torch.cuda.get_rng_state(0).clone()
            snapshots = {}
            order = ('old','new') if index == 0 else ('new','old')
            for name in order:
                torch.set_rng_state(rng_cpu)
                torch.cuda.set_rng_state(rng_cuda,0)
                snapshots[name], record[name] = measured_step(old if name=='old' else new, optimizers[name])
            left, right = snapshots['old'], snapshots['new']
            assert torch.equal(left['count'],right['count']) and int(left['count']) == 12800
            assert torch.equal(left['cpu_rng'],right['cpu_rng']) and torch.equal(left['cuda_rng'],right['cuda_rng'])
            differences = {}
            for name in ('loss','probabilities'):
                differences[name] = float((left[name]-right[name]).abs().max())
                torch.testing.assert_close(left[name],right[name],**TOLERANCES[name])
            for group in ('gradients','parameters','moments'):
                maximum = 0.
                for name in left[group]:
                    first, second = left[group][name], right[group][name]
                    assert (first is None) == (second is None), (group,name)
                    if first is None:
                        continue
                    pairs = first.items() if group == 'moments' else [(name,first)]
                    for key,value in pairs:
                        other = second[key] if group == 'moments' else second
                        torch.testing.assert_close(value,other,**TOLERANCES['adam_moments' if group=='moments' else group],msg=f'{group}/{name}/{key}')
                        maximum = max(maximum,float((value-other).abs().max()))
                differences[group] = maximum
            assert left['gradients']['alpha'] is not None and abs(float(left['gradients']['alpha']))>0
            record.update(status='PASS', max_absolute_drift=differences, dropout_rng_matches=True)
            print(json.dumps(dict(event='ALPHA_PARITY_COMPLETE',result=record)),flush=True)
            del snapshots, optimizers
        assert sha(old_path) == OLD_SHA and sha(external) == NEW_SHA
        result['status'] = 'PASS_H100_A1_SCALAR_VECTOR_PARITY'
    except BaseException as error:
        result.update(error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
    finally:
        signal.alarm(0)
        stop.set()
        if monitor is not None:
            monitor.join(timeout=1)
        for name, handler in old_signal.items():
            signal.signal(name,handler)
        result['elapsed_seconds'] = time.monotonic()-started
        (output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False),flush=True)
    return 0 if result['status']=='PASS_H100_A1_SCALAR_VECTOR_PARITY' else 1


if __name__ == '__main__':
    raise SystemExit(main())
