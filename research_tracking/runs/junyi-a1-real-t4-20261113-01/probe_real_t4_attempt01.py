"""Đo cả collate + training step A1 trên T4, fixture tổng hợp và trần 180 giây."""
import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
import traceback


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root=args.root.resolve()
    output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=False)
    result=dict(status='FAILED_PRESERVED',scope='REAL_JUNYI_T4_BOUNDED_THROUGHPUT',
        max_seconds=180,epochs=0,modal_spent_usd=0,parity=[],training=[],samples=[])
    started=time.monotonic()
    stopped=threading.Event()
    phase=['setup']
    monitor=None
    def deadline(_signal,_frame):
        raise TimeoutError('T4 probe exceeded 180 seconds')
    signal.signal(signal.SIGALRM,deadline)
    signal.alarm(180)
    try:
        os.environ.update(CUBLAS_WORKSPACE_CONFIG=':4096:8',OMP_NUM_THREADS='2',
            MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
        sys.path.insert(0,str(root/'src'))
        import torch
        from knowledge_tracing.akt.config import AKTConfig,ResearchCUDAExecutionProfile
        from knowledge_tracing.akt.encoding import ExerciseEncoding
        from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView,JunyiResearchEncoding
        from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition,JunyiGraphPhaseSession
        from knowledge_tracing.akt.research_junyi_graph_model import JunyiGraphAKTAdapter
        from knowledge_tracing.akt.research_junyi_roles import make_junyi_research_roles
        from knowledge_tracing.akt.types import KTEvent,LearnerEvents
        from knowledge_tracing.akt.windows import iter_windows
        from knowledge_tracing.shared_kt import StableVocabulary,PrerequisiteGraph
        assert torch.cuda.is_available() and torch.cuda.device_count()==1
        result.update(gpu=torch.cuda.get_device_name(0),torch=torch.__version__,cuda=torch.version.cuda)
        assert 'T4' in result['gpu']
        torch.set_num_threads(2)
        torch.use_deterministic_algorithms(True,warn_only=False)
        torch.backends.cuda.matmul.allow_tf32=False
        torch.backends.cudnn.allow_tf32=False
        torch.backends.cudnn.benchmark=False
        torch.set_float32_matmul_precision('highest')
        profile=ResearchCUDAExecutionProfile(12*1024**3,recipe_id='cgakt-cuda-fp32-batch128-v2')
        torch.cuda.set_per_process_memory_fraction(profile.max_vram_bytes/torch.cuda.get_device_properties(0).total_memory,0)
        config=replace(AKTConfig(),phase='junyi-research',device='cuda',outer_fold=4,
            execution_enabled=True,run_id='a1-real-t4',output_dir=root/'experiments/akt/results/a1-compact-t4',
            batch_size=128,protocol_version='akt-nr-exercise-v2-batch128',max_train_users=256,max_val_users=64,
            max_targets_per_side=131072,max_total_targets=262144,max_steps=32,max_seconds=175,
            max_wall_seconds=180,max_rss_bytes=2*1024**3,min_available_ram_bytes=1)
        import hashlib
        import numpy as np
        from knowledge_tracing.akt.research_junyi_roles import JunyiResearchRoles
        from knowledge_tracing.akt.encoding import load_encoding
        from knowledge_tracing.akt.research_junyi_window_cache import _load_shard,_parts
        data=root/'benchmark-data'
        cohort=json.loads((data/'cohort.json').read_text())
        for name,digest in cohort['exported_files'].items():
            assert hashlib.sha256((data/name).read_bytes()).hexdigest()==digest
        roles_payload=json.loads((data/'roles.json').read_text())
        for name in ('train_users','selection_users','calibration_users','outer_validation_users'):
            roles_payload[name]=tuple(roles_payload[name])
        roles=JunyiResearchRoles(**roles_payload)
        assert roles.identity==cohort['export_roles_identity']
        train=JunyiPhaseView(roles,'select_train80',roles.train_users,roles.identity)
        selection=JunyiPhaseView(roles,'raw_selection10',roles.selection_users,roles.identity)
        encoding=JunyiResearchEncoding(load_encoding(data/'encoding.json'),train)
        assert encoding.identity==cohort['export_encoding_identity']
        values=encoding.native.vocabulary.values
        topology=json.loads((data/'graph.json').read_text())
        graph=PrerequisiteGraph.from_edges(topology['nodes'],topology['corrected_edges'])
        condition=JunyiGraphCondition(encoding,graph,hashlib.sha256((data/'graph.json').read_bytes()).hexdigest())
        session=JunyiGraphPhaseSession(condition,train)
        cache_bounds=dict(shard_records=256,max_shard_tokens=51200)
        def read(label):
            records=tuple(_load_shard(data/(label+'.npz'),cohort['outputs'][label],cache_bounds))
            view=train if label=='train' else selection
            allowed=frozenset(view.users)
            for record in records:_parts(record,view,encoding,allowed)
            return records
        entries=read('train')
        validation_windows=read('selection')
        with np.load(data/'selection-truth.npz',allow_pickle=False) as saved:
            truth_offsets=saved['offsets'];truth_labels=saved['labels']
        result['population']=dict(train_windows=len(entries),selection_windows=len(validation_windows),
            train_targets=cohort['outputs']['train']['targets'],selection_targets=cohort['outputs']['selection']['targets'],
            train_users=cohort['outputs']['train']['users'],selection_users=cohort['outputs']['selection']['users'],
            graph_edges=len(graph.edges),vocabulary=len(values),learner_ids_aliased=True)
        assert len(entries)==256 and len(validation_windows)<=128
        parity_entries=entries[:128]
        parity_targets=sum(int(entry.window.target_mask.sum()) for entry in parity_entries)
        workloads=dict(optimizer_steps=0,training_targets=0)
        def train_step(adapter,group,optimizer):
            count=sum(int(entry.window.target_mask.sum()) for entry in group)
            assert workloads['optimizer_steps']+1<=32
            assert workloads['training_targets']+count<=262144
            record=adapter.step(adapter.collate_training(group),optimizer)
            assert record['valid_targets']==count
            workloads['optimizer_steps']+=1;workloads['training_targets']+=count
            return record
        adapters={}
        for name in ('reference','compact'):
            torch.manual_seed(42)
            adapters[name]=JunyiGraphAKTAdapter(config=config,encoding=encoding,condition=condition,
                phase=session,cuda_profile=profile,compact_context=name=='compact')
        initial={name:value.detach().cpu().clone() for name,value in adapters['reference'].native.state_dict().items()}
        def reset(adapter,alpha):
            adapter.native.load_state_dict(initial,strict=True)
            adapter.native.train()
            with torch.no_grad(): adapter.native.alpha.fill_(alpha)
            optimizer=torch.optim.Adam(adapter.native.parameters(),lr=config.lr,betas=config.betas,
                eps=config.eps,weight_decay=config.weight_decay,foreach=False,fused=False)
            adapter._optimizer=None
            return optimizer
        def compare(first,second):
            if torch.is_tensor(first):
                torch.testing.assert_close(first,second,atol=1e-7,rtol=1e-5)
                return float((first-second).abs().max()) if first.numel() else 0.
            if isinstance(first,dict):
                assert first.keys()==second.keys()
                return max((compare(first[key],second[key]) for key in first),default=0.)
            if isinstance(first,(list,tuple)):
                assert len(first)==len(second)
                return max((compare(a,b) for a,b in zip(first,second)),default=0.)
            assert first==second
            return 0.
        for alpha in (0.,.75):
            optimizers={name:reset(adapter,alpha) for name,adapter in adapters.items()}
            cpu_rng=torch.get_rng_state().clone()
            cuda_rng=torch.cuda.get_rng_state(0).clone()
            states={}
            for name,adapter in adapters.items():
                torch.set_rng_state(cpu_rng);torch.cuda.set_rng_state(cuda_rng,0)
                record=train_step(adapter,parity_entries,optimizers[name])
                states[name]=dict(loss=record['loss_sum'],targets=record['valid_targets'],
                    parameters={key:value.detach().cpu().clone() for key,value in adapter.native.state_dict().items()},
                    gradients={key:None if value.grad is None else value.grad.detach().cpu().clone()
                               for key,value in adapter.native.named_parameters()},
                    optimizer=optimizers[name].state_dict(),cpu_rng=torch.get_rng_state().clone(),
                    cuda_rng=torch.cuda.get_rng_state(0).clone())
            # Optimizer state tensors nằm trên GPU, so sánh trước reset bước đo.
            drift=compare(states['reference'],states['compact'])
            assert states['reference']['targets']==parity_targets
            result['parity'].append(dict(alpha=alpha,status='PASS',max_absolute_drift=drift,
                                        loss=states['reference']['loss'],targets=parity_targets))
        def sample():
            while not stopped.wait(.25):
                measured=subprocess.run(['nvidia-smi','--query-gpu=utilization.gpu,memory.used,power.draw',
                    '--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=3)
                result['samples'].append(dict(phase=phase[0],at=time.monotonic(),values=measured.stdout.strip(),
                                              returncode=measured.returncode))
        monitor=threading.Thread(target=sample,daemon=True)
        monitor.start()
        torch.cuda.reset_peak_memory_stats()
        for block,name in enumerate(('reference','compact','compact','reference')):
            adapter=adapters[name]
            optimizer=reset(adapter,.75)
            torch.manual_seed(84);torch.cuda.manual_seed_all(84)
            phase[0]=f'{name}-{block}'
            torch.cuda.synchronize()
            at=time.perf_counter()
            io_seconds=0.
            input_targets=0
            for _ in range(2):
                io_at=time.perf_counter()
                actual_entries=read('train')
                io_seconds+=time.perf_counter()-io_at
                for begin in range(0,len(actual_entries),128):
                    group=actual_entries[begin:begin+128]
                    train_step(adapter,group,optimizer)
                    input_targets+=sum(int(entry.window.target_mask.sum()) for entry in group)
            torch.cuda.synchronize()
            elapsed=time.perf_counter()-at
            result['training'].append(dict(method=name,block=block,steps=4,seconds=elapsed,
                file_read_validate_seconds=io_seconds,targets=input_targets,targets_per_second=input_targets/elapsed))
            phase[0]='idle'
        result['validation']=[]
        probabilities={}
        for name,adapter in adapters.items():
            adapter.set_phase(JunyiGraphPhaseSession(condition,selection))
            phase[0]='validation-'+name
            torch.cuda.synchronize();at=time.perf_counter()
            windows=read('selection')
            predictions=adapter.predict_windows(windows)
            collected=[];labels=[]
            population=hashlib.sha256()
            for index,(window,predicted) in enumerate(zip(windows,predictions)):
                mask=window.target_mask
                expected=truth_labels[truth_offsets[index]:truth_offsets[index+1]]
                assert len(expected)==len(predicted)
                collected.extend(predicted[mask]);labels.extend(expected[mask])
                population.update(window.inputs.source_rows[mask].tobytes())
            probabilities[name]=np.asarray(collected)
            assert len(collected)==result['population']['selection_targets']
            torch.cuda.synchronize();elapsed=time.perf_counter()-at
            result['validation'].append(dict(method=name,seconds=elapsed,targets=len(collected),
                population_sha256=population.hexdigest(),finite=bool(np.isfinite(collected).all())))
            phase[0]='idle'
        np.testing.assert_allclose(probabilities['reference'],probabilities['compact'],atol=1e-7,rtol=1e-5)
        assert result['validation'][0]['population_sha256']==result['validation'][1]['population_sha256']
        result['validation_max_probability_drift']=float(np.max(np.abs(probabilities['reference']-probabilities['compact'])))
        # Trạng thái cuối benchmark, không là selected-fit hoặc checkpoint production.
        adapter=adapters['compact']
        from dataclasses import asdict
        import random
        terminal=dict(kind='BOUNDED_THROUGHPUT_TERMINAL_STATE_NOT_RESEARCH_MODEL',
            model=adapter.native.state_dict(),optimizer=adapter._optimizer.state_dict(),
            config=json.loads(json.dumps(asdict(config),default=str)),rng=dict(python=random.getstate(),
                numpy=np.random.get_state(),cpu=torch.get_rng_state(),cuda=torch.cuda.get_rng_state(0)),
            workload=workloads,cohort_sha256=hashlib.sha256((data/'cohort.json').read_bytes()).hexdigest(),
            phase='raw_selection10_after_benchmark',production_resume_supported=False)
        torch.save(terminal,output/'BENCHMARK_STATE.pt')
        result['terminal_state_sha256']=hashlib.sha256((output/'BENCHMARK_STATE.pt').read_bytes()).hexdigest()
        result['workload']=workloads
        result['peak_allocated_vram_bytes']=torch.cuda.max_memory_allocated()
        result['peak_reserved_vram_bytes']=torch.cuda.max_memory_reserved()
        result['status']='PASS_REAL_JUNYI_T4_BOUNDED_THROUGHPUT'
    except BaseException as error:
        result.update(error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc())
    finally:
        signal.alarm(0)
        stopped.set()
        if monitor is not None: monitor.join(timeout=4)
        result['elapsed_seconds']=time.monotonic()-started
        result['limits_vi']='Mẫu thật 256window từ8shard train,88window/64learner selection với tối đa300events mỗi người. Alias learner giữ membership đã frozen, không chia lại. Đo đọc/kiểm NPZ nhỏ, collate+step và prediction; chưa fullSQL/fullcache admission hoặc toàn epoch. Fresh seed42/alpha0,75 cho timing, không dùng checkpoint nghiên cứu. Không chọn epoch hoặc model. T4 không suy ra tốc độ H100. Terminal state chỉ là benchmark.'
        (output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({key:value for key,value in result.items() if key not in ('samples','traceback')},ensure_ascii=False))
    return 0 if result['status']=='PASS_REAL_JUNYI_T4_BOUNDED_THROUGHPUT' else 1


if __name__=='__main__':
    raise SystemExit(main())
