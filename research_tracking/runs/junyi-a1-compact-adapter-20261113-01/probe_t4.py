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
    result=dict(status='FAILED_PRESERVED',scope='SYNTHETIC_T4_A1_COLLATE_AND_STEP',
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
            execution_enabled=True,run_id='a1-compact-t4',output_dir=root/'experiments/akt/results/a1-compact-t4',
            batch_size=128,protocol_version='akt-nr-exercise-v2-batch128',max_train_users=640,max_val_users=64,
            max_targets_per_side=25600,max_total_targets=25600,max_steps=1,max_seconds=175,
            max_wall_seconds=180,max_rss_bytes=2*1024**3,min_available_ram_bytes=1)
        roles=make_junyi_research_roles([(str(index),index%5,'development') for index in range(1000)])
        train=JunyiPhaseView(roles,'select_train80',roles.train_users,roles.identity)
        values=tuple(['A','B','C']+[f'fixture-{index:03d}' for index in range(714)])
        encoding=JunyiResearchEncoding(ExerciseEncoding(StableVocabulary(values),{value:1 for value in values}),train)
        condition=JunyiGraphCondition(encoding,PrerequisiteGraph.from_edges(values,(('A','C'),('B','C'))),'f'*64)
        session=JunyiGraphPhaseSession(condition,train)
        entries=[]
        for index,user in enumerate(train.users[:128]):
            learner=LearnerEvents(user,0,tuple(KTEvent(user,('A','B','C')[rank%3],rank+1,
                index*200+rank+1,1 if rank%3!=2 else (index+rank)%2,0,0) for rank in range(200)))
            entries.append(tuple(iter_windows(learner,encoding.native,training=True))[1])
        entries=tuple(entries)
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
                record=adapter.step(adapter.collate_training(entries),optimizers[name])
                states[name]=dict(loss=record['loss_sum'],targets=record['valid_targets'],
                    parameters={key:value.detach().cpu().clone() for key,value in adapter.native.state_dict().items()},
                    gradients={key:None if value.grad is None else value.grad.detach().cpu().clone()
                               for key,value in adapter.native.named_parameters()},
                    optimizer=optimizers[name].state_dict(),cpu_rng=torch.get_rng_state().clone(),
                    cuda_rng=torch.cuda.get_rng_state(0).clone())
            # Optimizer state tensors nằm trên GPU, so sánh trước reset bước đo.
            drift=compare(states['reference'],states['compact'])
            assert states['reference']['targets']==12800
            result['parity'].append(dict(alpha=alpha,status='PASS',max_absolute_drift=drift,
                                        loss=states['reference']['loss'],targets=12800))
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
            for _ in range(4):
                adapter.step(adapter.collate_training(entries),optimizer)
            torch.cuda.synchronize()
            elapsed=time.perf_counter()-at
            result['training'].append(dict(method=name,block=block,steps=4,seconds=elapsed,
                                           targets=4*12800,targets_per_second=4*12800/elapsed))
            phase[0]='idle'
        result['peak_allocated_vram_bytes']=torch.cuda.max_memory_allocated()
        result['peak_reserved_vram_bytes']=torch.cuda.max_memory_reserved()
        result['status']='PASS_T4_COMPACT_ADAPTER_PARITY_AND_TIMING'
    except BaseException as error:
        result.update(error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc())
    finally:
        signal.alarm(0)
        stopped.set()
        if monitor is not None: monitor.join(timeout=4)
        result['elapsed_seconds']=time.monotonic()-started
        result['limits_vi']='Fixture tổng hợp, reference/compact cùng source, collate+step có prefix và checksum. Chưa gồm SQL/cache I/O, validation, checkpoint hoặc toàn epoch Junyi/H100. Một phép đo ABBA, GPU samples có tương quan và ranh giới phase xấp xỉ.'
        (output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({key:value for key,value in result.items() if key not in ('samples','traceback')},ensure_ascii=False))
    return 0 if result['status']=='PASS_T4_COMPACT_ADAPTER_PARITY_AND_TIMING' else 1


if __name__=='__main__':
    raise SystemExit(main())
