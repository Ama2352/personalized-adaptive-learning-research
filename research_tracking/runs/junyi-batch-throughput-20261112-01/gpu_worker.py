"""Profile batch shape trên cùng packet Junyi, tách khỏi selected training."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback
import zipfile

ROOT = Path('/opt/kltn')
REQUEST = json.loads(Path('/opt/probe-request.json').read_text())
RUN = REQUEST['run_id']
OUTPUT = ROOT/'experiments/akt/results'/RUN
OPERATION = ROOT/'experiments/akt/results'/(RUN+'-operation')
OUTPUT.mkdir(parents=True,exist_ok=False)
OPERATION.mkdir(parents=True,exist_ok=False)
started = time.monotonic()


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def extract(archive):
    with zipfile.ZipFile(archive) as saved:
        pins = json.loads(saved.read('MANIFEST.json'))['files']
        assert set(saved.namelist())==set(pins)|{'MANIFEST.json'}
        for name,pin in pins.items():
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
            assert ':' not in name and '\\' not in name
            raw = saved.read(name)
            expected = pin if isinstance(pin,str) else pin['sha256']
            assert hashlib.sha256(raw).hexdigest()==expected
            path = ROOT/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(raw)


result = dict(status='FAILED',scope='engineering_batch_shape_profile_only',full_junyi_epoch=False)
try:
    assert REQUEST['status']=='USER_APPROVED' and REQUEST['gpu']=='T4'
    assert REQUEST['max_optimizer_steps']==480 and REQUEST['expected_targets']==56332
    extract('/opt/kltn-input.zip')
    extract('/opt/junyi-data.zip')
    preflight = ROOT/'artifacts/akt/preflight'
    preflight.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile('/opt/cpu-gate.zip') as saved:
        for name,pin in json.loads(saved.read('SHA256.json')).items():
            raw = saved.read(name)
            assert hashlib.sha256(raw).hexdigest()==pin['sha256']
            if name.startswith('gate2-'):
                assert Path(name).name==name
                (preflight/name).write_bytes(raw)
    lock = ROOT/'artifacts/akt/runtime/modal-linux-cuda.lock.txt'
    lock.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile('/opt/locked-cu126.txt',lock)
    upstream = ROOT/'artifacts/akt/dependencies/upstream'
    os.environ.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_COUNT='3',
        GIT_CONFIG_KEY_0='core.fsmonitor',GIT_CONFIG_VALUE_0='false',
        GIT_CONFIG_KEY_1='safe.directory',GIT_CONFIG_VALUE_1=str(upstream),
        GIT_CONFIG_KEY_2='core.autocrlf',GIT_CONFIG_VALUE_2='false',
        GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__',
        CUBLAS_WORKSPACE_CONFIG=':4096:8',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',
        OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
    runtime = preflight/(RUN+'-runtime.json')
    subprocess.run([sys.executable,'-I','-B',str(ROOT/'scripts/akt/check_runtime.py'),
        '--upstream',str(upstream),'--device','cuda','--lock-file',str(lock),'--output',str(runtime)],
        check=True,timeout=35)
    sys.path.insert(0,str(ROOT/'src'))
    sys.path.insert(0,'/opt')
    import numpy as np
    import torch
    from packet_reader import JunyiTrainingPacket
    from knowledge_tracing.akt.config import AKTConfig, ResearchCUDAExecutionProfile
    from knowledge_tracing.akt.model import AKTAdapter
    from knowledge_tracing.akt.training import train_epoch, _seed
    from knowledge_tracing.akt.checkpoint import save_checkpoint, load_checkpoint
    from knowledge_tracing.akt.authorization import require_gate2_evidence, preflight as check_preflight
    from knowledge_tracing.akt.research_graph_model import _cuda_execution_check

    torch.set_num_threads(2)
    torch.set_default_dtype(torch.float32)
    torch.use_deterministic_algorithms(True,warn_only=False)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.set_float32_matmul_precision('highest')
    profile = ResearchCUDAExecutionProfile(2*1024**3)
    torch.cuda.set_per_process_memory_fraction(profile.max_vram_bytes/torch.cuda.get_device_properties(0).total_memory,0)
    assert 'T4' in torch.cuda.get_device_name(0)
    from knowledge_tracing.akt.tensors import collate_windows
    from knowledge_tracing.akt.checkpoint import restore_checkpoint
    from knowledge_tracing.akt.research_runner import _state_hash
    from knowledge_tracing.akt.sampler import iter_shuffled_windows
    from knowledge_tracing.akt.resources import memory_snapshot
    import gc
    import math

    assert REQUEST['actual_benchmark_batch_sizes']==[4,8,16,32]
    assert REQUEST['reference_config_batch_size']==4 and REQUEST['max_target_exposures']==225328
    config = AKTConfig(phase='junyi-research',run_id=RUN,output_dir=OUTPUT,
        execution_enabled=True,device='cuda',outer_fold=4,max_train_users=126774,
        max_val_users=15847,max_targets_per_side=13347331,max_total_targets=225328,
        max_steps=480,max_seconds=320,max_wall_seconds=360,max_rss_bytes=6*1024**3,
        min_available_ram_bytes=256*1024**2)
    gate = require_gate2_evidence(config,lock_file=lock)
    check_preflight(config,runtime_report_path=runtime,lock_file=lock,cuda_profile=profile)
    packet = JunyiTrainingPacket(ROOT/REQUEST['packet_root'],expected_packet_sha256=REQUEST['packet_sha256'])
    records = list(packet.iter_training_windows())
    shuffled = tuple(iter_shuffled_windows(lambda:iter(records),seed=43))
    assert len(shuffled)==1024 and sum(int(row.window.target_mask.sum()) for row in shuffled)==56332
    encoding = packet.encoding.native
    assert len(encoding.vocabulary.values)==717 and config.batch_size==4
    order_sha = hashlib.sha256(json.dumps([row.window.window_id for row in shuffled],separators=(',', ':')).encode()).hexdigest()
    write_json(OPERATION/'packet-admission.json',dict(audit=packet.expected,packet_sha256=packet.identity,
        shuffled_window_order_sha256=order_sha,shuffle_seed=43,full_role_coverage=False))
    write_json(OUTPUT/'run-manifest.json',dict(scope='engineering_batch_shape_profile_only',
        config=json.loads(json.dumps(asdict(config),default=str)),cuda_profile=asdict(profile),
        actual_benchmark_batch_sizes=[4,8,16,32],packet_sha256=packet.identity,
        shuffled_window_order_sha256=order_sha,main_selected_fit=False,reference_config_batch_size=4))

    def fresh():
        _seed(42)
        with torch.device('cpu'):
            adapter = AKTAdapter(config,encoding)
        optimizer = torch.optim.Adam(adapter.native.parameters(),lr=config.lr,betas=config.betas,
            eps=config.eps,weight_decay=config.weight_decay,foreach=False,fused=False,capturable=False,
            differentiable=False,amsgrad=False,maximize=False,decoupled_weight_decay=False)
        return adapter,optimizer

    case_progress = {}

    def run_case(batch_size,expected_initial):
        adapter,optimizer = fresh()
        initial = _state_hash(adapter)
        assert expected_initial is None or initial==expected_initial
        torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
        steps = targets = first_targets = 0
        max_pre_clip = max_post_clip = 0.
        nonzero_gradients = updated_parameters = 0
        rss_peak = 0
        valid_tokens = padded_tokens = 0
        first_finished = None
        training_started = time.monotonic()
        for start in range(0,len(shuffled),batch_size):
            assert time.monotonic()-started<320,'Batch profile workload deadline'
            group = shuffled[start:start+batch_size]
            batch = collate_windows([entry.window for entry in group],n_items=717,device='cuda',
                targets=[entry.targets for entry in group])
            result_step = adapter.step(batch,optimizer)
            torch.cuda.synchronize()
            expected_targets = sum(int(entry.window.target_mask.sum()) for entry in group)
            assert result_step['stepped'] and result_step['valid_targets']==expected_targets
            assert math.isfinite(result_step['loss_sum']) and math.isfinite(result_step['pre_clip_norm'])
            steps += 1;targets += expected_targets
            case_progress.update(successful_optimizer_steps=steps,successful_target_exposures=targets)
            max_pre_clip = max(max_pre_clip,result_step['pre_clip_norm'])
            max_post_clip = max(max_post_clip,result_step['post_clip_norm'])
            nonzero_gradients += int(result_step['pre_clip_norm']>0)
            updated_parameters += int(result_step['parameter_updated'])
            valid_tokens += int(batch.valid_mask.sum().item());padded_tokens += batch.valid_mask.numel()
            snapshot = memory_snapshot();rss_peak = max(rss_peak,snapshot['process_rss_bytes'])
            assert rss_peak<=6*1024**3 and snapshot['system_available_ram_bytes']>=256*1024**2
            if first_finished is None:
                first_finished = time.monotonic();first_targets = expected_targets
        finished = time.monotonic()
        assert targets==56332 and steps==1024//batch_size
        wall = finished-training_started
        resource = _cuda_execution_check(profile,synchronize=True)
        identity = dict(kind='junyi_batch_shape_profile_checkpoint_v1',packet_sha256=packet.identity,
            source_gate=gate['report_sha256'],initial_backbone_sha256=initial,
            reference_config_batch_size=4,actual_benchmark_batch_size=batch_size,
            config=json.loads(json.dumps(asdict(config),default=str)),profile=asdict(profile),
            shuffled_window_order_sha256=order_sha,main_selected_fit=False)
        directory = OUTPUT/'checkpoints'/f'batch-{batch_size:03d}'
        directory.mkdir(parents=True)
        save_checkpoint(directory/'state.pt',adapter,optimizer,identity=identity,
            progress=dict(complete=True,epoch=1,engineering_packet_pass=True,full_junyi_epoch=False,
                optimizer_steps=steps,valid_targets=targets,actual_benchmark_batch_size=batch_size))
        checksum = sha(directory/'state.pt')
        write_json(directory/'metadata.json',dict(checkpoint_sha256=checksum,
            checkpoint_bytes=(directory/'state.pt').stat().st_size,identity=identity))
        write_json(directory/'COMPLETE.json',dict(checkpoint_sha256=checksum,
            metadata_sha256=sha(directory/'metadata.json')))
        baseline = adapter.predict_window(shuffled[0].window).copy()
        del adapter,optimizer,batch
        gc.collect();torch.cuda.empty_cache()
        payload = load_checkpoint(directory/'state.pt',expected_identity=identity,device='cpu')
        reloaded,reloaded_optimizer = fresh()
        restore_checkpoint(reloaded,reloaded_optimizer,payload)
        restored = reloaded.predict_window(shuffled[0].window)
        assert np.array_equal(baseline,restored)
        assert np.isfinite(restored).all()
        del payload,reloaded,reloaded_optimizer
        gc.collect();torch.cuda.empty_cache()
        return dict(status='COMPLETE_ENGINEERING_CASE',actual_benchmark_batch_size=batch_size,
            reference_config_batch_size=4,initial_backbone_sha256=initial,optimizer_steps=steps,
            targets=targets,full_training_wall_seconds=wall,targets_per_second=targets/wall,
            first_batch_seconds=first_finished-training_started,first_batch_targets=first_targets,
            exclude_first_batch_seconds=finished-first_finished,
            exclude_first_batch_targets=targets-first_targets,
            exclude_first_batch_targets_per_second=(targets-first_targets)/(finished-first_finished),
            valid_tokens=valid_tokens,padded_tokens=padded_tokens,padding_tokens=padded_tokens-valid_tokens,
            nonzero_gradient_steps=nonzero_gradients,parameter_update_steps=updated_parameters,
            max_pre_clip_norm=max_pre_clip,max_post_clip_norm=max_post_clip,rss_peak_bytes=rss_peak,
            cuda_resource=resource,checkpoint_sha256=checksum,fresh_reload_first_window_exact=True)

    cases = [];initial = None;oom = None
    for batch_size in (4,8,16,32):
        case_progress.clear()
        try:
            case = run_case(batch_size,initial)
            initial = case['initial_backbone_sha256']
            cases.append(case)
            write_json(OPERATION/f'batch-{batch_size:03d}.json',case)
            print(json.dumps(case,allow_nan=False),flush=True)
        except torch.cuda.OutOfMemoryError as error:
            oom = dict(actual_benchmark_batch_size=batch_size,error_type=type(error).__name__,error=str(error),
                failed_case_optimizer_state_accepted=False,remaining_cases_stopped=True,
                successful_optimizer_steps_before_error=case_progress.get('successful_optimizer_steps',0),
                successful_target_exposures_before_error=case_progress.get('successful_target_exposures',0))
            write_json(OPERATION/'oom.json',oom)
            break
    if oom is None:
        assert len(cases)==4 and sum(case['optimizer_steps'] for case in cases)==480
        assert sum(case['targets'] for case in cases)==225328
    result.update(status='JUNYI_BATCH_PROFILE_COMPLETE' if oom is None else 'PARTIAL_JUNYI_BATCH_PROFILE_OOM',
        scope='engineering_batch_shape_profile_only',cases=cases,oom=oom,
        actual_completed_case_updates=sum(case['optimizer_steps'] for case in cases),
        completed_case_target_exposures=sum(case['targets'] for case in cases),
        known_successful_updates=sum(case['optimizer_steps'] for case in cases)+(oom['successful_optimizer_steps_before_error'] if oom else 0),
        known_successful_target_exposures=sum(case['targets'] for case in cases)+(oom['successful_target_exposures_before_error'] if oom else 0),
        full_main_training=False,selected_protocol_batch_size=4,
        protocol_adoption_requires_separate_decision=True,shuffled_window_order_sha256=order_sha)
except BaseException as error:
    result.update(error_type=type(error).__name__,error=str(error))
    (OPERATION/'failure.log').write_text(traceback.format_exc())
finally:
    result['elapsed_seconds']=time.monotonic()-started
    write_json(OPERATION/'result.json',result)
print(json.dumps(result,allow_nan=False),flush=True)
raise SystemExit(0 if result['status'] in ('JUNYI_BATCH_PROFILE_COMPLETE','PARTIAL_JUNYI_BATCH_PROFILE_OOM') else 1)
