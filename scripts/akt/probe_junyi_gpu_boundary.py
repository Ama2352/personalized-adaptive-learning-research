"""Đo T4 có giới hạn cho A2/A3 cached/direct, giữ parity và checkpoint/resume.

Confidence là fixture kỹ thuật cố định. Không chọn epoch, không đánh giá RQ.
CPU chuẩn bị cache trước khi khởi tạo model CUDA. Không gọi Modal.
"""
import argparse
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--data',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--prepared-receipts',type=Path)
    parser.add_argument('--cache-id',help='Bộ cache CPU đã kiểm, dùng lại cho lượt kiểm mới')
    args=parser.parse_args()
    root=args.root.resolve();data=args.data.resolve() if args.data else root/'benchmark-data'
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    os.environ.update(CUBLAS_WORKSPACE_CONFIG=':4096:8',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',
                      OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
    sys.path.insert(0,str(root/'src'))
    from knowledge_tracing.akt.research_junyi_roles import JunyiResearchRoles
    from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView,JunyiResearchEncoding
    from knowledge_tracing.akt.encoding import load_encoding
    from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition,JunyiGraphPhaseSession
    from knowledge_tracing.akt.research_junyi_confidence_binding import JunyiConfidenceBinding
    from knowledge_tracing.akt.research_graph_condition import OperationalEdgeWeight
    from knowledge_tracing.akt.research_junyi_graph_cache import build_graph_context_cache,GraphContextCache
    from knowledge_tracing.akt.research_junyi_window_cache import _load_shard,_parts
    from knowledge_tracing.shared_kt import PrerequisiteGraph
    result=dict(status='FAILED',scope='TECHNICAL_COHORT_ONLY_NOT_RESEARCH_TRAINING',
        confidence='DETERMINISTIC_FIXTURE_NOT_FITTED',modal_spent_usd=0,
        full_dataset_epochs=0,parity=[],measurements=[],resume=[],gpu_samples=[])
    stop=threading.Event();monitor=None;phase=['cpu_prepare'];began=time.monotonic()
    try:
        cohort=json.loads((data/'cohort.json').read_text())
        for name,digest in cohort['exported_files'].items():
            if sha(data/name)!=digest:raise ValueError('Cohort file SHA mismatch')
        roles_payload=json.loads((data/'roles.json').read_text())
        for name in ('train_users','selection_users','calibration_users','outer_validation_users'):
            roles_payload[name]=tuple(roles_payload[name])
        roles=JunyiResearchRoles(**roles_payload)
        train=JunyiPhaseView(roles,'select_train80',roles.train_users,roles.identity)
        selection=JunyiPhaseView(roles,'raw_selection10',roles.selection_users,roles.identity)
        encoding=JunyiResearchEncoding(load_encoding(data/'encoding.json'),train)
        if encoding.identity!=cohort['export_encoding_identity']:raise ValueError('Encoding identity changed')
        topology=json.loads((data/'graph.json').read_text())
        graph=PrerequisiteGraph.from_edges(topology['nodes'],topology['corrected_edges'])
        weights=tuple(OperationalEdgeWeight(parent,child,True,
            (int(hashlib.sha256((parent+'\n'+child).encode()).hexdigest()[:8],16)%5)/4.,None,
            (int(hashlib.sha256((parent+'\n'+child).encode()).hexdigest()[:8],16)%5)/4.)
            for parent,child in graph.edges)
        confidence=JunyiConfidenceBinding(train.identity,encoding.identity,sha(data/'graph.json'),
                                         'b'*64,'c'*64,weights)
        from knowledge_tracing.akt.research_junyi_confidence_binding import save_binding
        save_binding(confidence,output/'confidence-fixture.json')
        if not args.prepare_only and args.prepared_receipts is None:
            raise ValueError('GPU probe requires caches prepared offline before the GPU run')
        records={}
        for label,view in (('train',train),('selection',selection)):
            records[label]=tuple(_load_shard(data/(label+'.npz'),cohort['outputs'][label],
                                            dict(shard_records=256,max_shard_tokens=51200)))
            for record in records[label]:_parts(record,view,encoding,frozenset(view.users))
        if len(records['train'])!=256 or len(records['selection'])>128:
            raise ValueError('Probe cohort workload changed')
        conditions={};caches={};result['cpu_context_support']=[]
        for variant in ('A2','A3'):
            condition=JunyiGraphCondition(encoding,graph,sha(data/'graph.json'),variant=variant,confidence=confidence)
            conditions[variant]=condition
            for label,view in (('train',train),('selection',selection)):
                windows=tuple(row.window if label=='train' else row for row in records[label])
                cache_id = args.cache_id or output.name
                if Path(cache_id).name != cache_id or cache_id in ('.', '..'):
                    raise ValueError('Invalid cache identifier')
                path=root/'artifacts/akt/graph-context-cache'/cache_id/(variant+'-'+label+'.sqlite')
                session=JunyiGraphPhaseSession(condition,view)
                if args.prepared_receipts is None:
                    receipt=build_graph_context_cache(path,windows,session,dataset_sha256=sha(data/'cohort.json'),
                        window_manifest_sha256=cohort['outputs'][label]['sha256'],expected_windows=len(windows),
                        expected_targets=sum(int(row.target_mask.sum()) for row in windows),
                        max_seconds=180,max_rss_bytes=1024**3)
                else:
                    receipt=json.loads((args.prepared_receipts/(variant+'-'+label+'-cache.json')).read_text())
                    if receipt['windows']!=len(windows):raise ValueError('Offline cache population differs')
                (output/(variant+'-'+label+'-cache.json')).write_text(json.dumps(receipt,indent=2))
                caches[variant,label]=GraphContextCache.open(path,receipt['cache_sha256'],session,
                    dataset_sha256=sha(data/'cohort.json'),window_manifest_sha256=cohort['outputs'][label]['sha256'])
                active=nonzero=0
                for offset in range(0,len(windows),128):
                    arrays=caches[variant,label].batch(windows[offset:offset+128],session).arrays()
                    active+=int(arrays[1].sum());nonzero+=int((arrays[0]!=0).sum())
                result['cpu_context_support'].append(dict(variant=variant,phase=label,
                    active_targets=active,nonzero_messages=nonzero,windows=len(windows)))
        result['cpu_prepare_seconds']=time.monotonic()-began
        result['graph_caches_prepared_offline']=args.prepared_receipts is not None
        if args.prepare_only:
            result['status']='CPU_PREPARED_ONLY_GPU_NOT_RUN'
            return
        import torch
        import numpy as np
        import psutil
        from knowledge_tracing.akt.config import AKTConfig,ResearchCUDAExecutionProfile
        from knowledge_tracing.akt.research_junyi_graph_model import JunyiGraphAKTAdapter
        from knowledge_tracing.akt.training import train_epoch,_seed
        if not torch.cuda.is_available() or 'T4' not in torch.cuda.get_device_name(0):
            raise RuntimeError('Actual Tesla T4 required')
        gpu_started=time.monotonic();phase[0]='gpu_initialize'
        result.update(gpu=torch.cuda.get_device_name(0),torch=torch.__version__,cuda=torch.version.cuda)
        torch.set_num_threads(2);torch.use_deterministic_algorithms(True,warn_only=False)
        torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        torch.backends.cudnn.benchmark=False;torch.set_float32_matmul_precision('highest')
        profile=ResearchCUDAExecutionProfile(12*1024**3,recipe_id='cgakt-cuda-fp32-batch128-v2')
        torch.cuda.set_per_process_memory_fraction(profile.max_vram_bytes/torch.cuda.get_device_properties(0).total_memory,0)
        config=replace(AKTConfig(),phase='junyi-research',device='cuda',outer_fold=4,execution_enabled=True,
            run_id=output.name,output_dir=output,batch_size=128,protocol_version='akt-nr-exercise-v2-batch128',
            max_train_users=256,max_val_users=128,max_targets_per_side=131072,max_total_targets=1048576,
            max_steps=80,max_seconds=360,max_wall_seconds=420,max_rss_bytes=2*1024**3,min_available_ram_bytes=1)
        from dataclasses import asdict
        (output/'cuda-profile.json').write_text(json.dumps(asdict(profile),indent=2))
        (output/'config.json').write_text(json.dumps(asdict(config),default=str,indent=2))
        deadline=time.monotonic()+360
        def watch():
            while not stop.is_set():
                try:
                    query=subprocess.run(['nvidia-smi','--query-gpu=utilization.gpu,memory.used,memory.total,power.draw',
                        '--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=5)
                    values=[float(value.strip()) for value in query.stdout.strip().split(',')]
                    result['gpu_samples'].append(dict(seconds=time.monotonic()-gpu_started,phase=phase[0],
                        utilization=values[0],vram_used_mib=values[1],vram_total_mib=values[2],power_w=values[3]))
                except Exception as error:
                    result.setdefault('telemetry_errors',[]).append(type(error).__name__)
                stop.wait(1)
        monitor=threading.Thread(target=watch,daemon=True);monitor.start()
        steps=0
        def check_time():
            if time.monotonic()>deadline or steps>=80:raise TimeoutError('T4 probe cap reached')
        def make(variant,cached):
            check_time();_seed(42)
            adapter=JunyiGraphAKTAdapter(config=config,encoding=encoding,condition=conditions[variant],
                phase=JunyiGraphPhaseSession(conditions[variant],train),cuda_profile=profile,
                compact_context=True,context_cache=caches[variant,'train'] if cached else None)
            with torch.no_grad():adapter.native.alpha.fill_(.75)
            return adapter
        def adam(adapter):
            return torch.optim.Adam(adapter.native.parameters(),lr=config.lr,betas=config.betas,
                eps=config.eps,weight_decay=config.weight_decay,foreach=False,fused=False)
        def compare(a,b):
            if torch.is_tensor(a):
                torch.testing.assert_close(a,b,atol=1e-7,rtol=1e-5)
            elif isinstance(a,dict):
                if a.keys()!=b.keys():raise AssertionError('State keys differ')
                for key in a:compare(a[key],b[key])
            elif isinstance(a,(tuple,list)):
                if len(a)!=len(b):raise AssertionError('State length differs')
                for x,y in zip(a,b):compare(x,y)
            else:
                if a!=b:raise AssertionError('State scalar differs')
        def step(adapter,optimizer):
            nonlocal steps
            check_time();record=adapter.step(adapter.collate_training(records['train'][:128]),optimizer)
            steps+=1
            return record
        for variant in ('A2','A3'):
            phase[0]=variant+'_parity'
            direct=make(variant,False);cached=make(variant,True)
            optimizers=[adam(direct),adam(cached)]
            state=torch.cuda.get_rng_state().clone();cpu_rng=torch.get_rng_state().clone()
            a=step(direct,optimizers[0]);torch.cuda.set_rng_state(state);torch.set_rng_state(cpu_rng)
            b=step(cached,optimizers[1])
            if a['valid_targets']!=b['valid_targets'] or a['loss_sum']!=b['loss_sum']:
                raise AssertionError('Cached/direct targets or loss differ')
            compare(direct.native.state_dict(),cached.native.state_dict())
            compare(optimizers[0].state_dict(),optimizers[1].state_dict())
            for x,y in zip(direct.native.parameters(),cached.native.parameters()):
                if (x.grad is None)!=(y.grad is None):raise AssertionError('Gradient participation differs')
                if x.grad is not None:compare(x.grad,y.grad)
            for adapter,is_cached in ((direct,False),(cached,True)):
                adapter.set_phase(JunyiGraphPhaseSession(conditions[variant],selection),
                                  context_cache=caches[variant,'selection'] if is_cached else None)
            first=direct.predict_windows(records['selection']);second=cached.predict_windows(records['selection'])
            drift=max(float(np.max(np.abs(x-y))) for x,y in zip(first,second))
            if drift>1e-7:raise AssertionError('Prediction parity exceeds tolerance')
            result['parity'].append(dict(variant=variant,loss_sum=a['loss_sum'],probability_max_abs=drift,status='PASS'))
            del direct,cached,optimizers,first,second;torch.cuda.empty_cache()
            # Hai block AB/BA, cùng seed và dữ liệu, mỗi block warmup1 + đo4 step.
            for block,order in enumerate(((False,True),(True,False))):
                for is_cached in order:
                    mode='cached' if is_cached else 'direct';phase[0]=variant+'_'+mode
                    adapter=make(variant,is_cached);optimizer=adam(adapter)
                    step(adapter,optimizer);torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats()
                    process=psutil.Process();cpu_before=process.cpu_times();start=time.monotonic()
                    count=0
                    for _ in range(4):count+=step(adapter,optimizer)['valid_targets']
                    torch.cuda.synchronize();seconds=time.monotonic()-start;cpu_after=process.cpu_times()
                    result['measurements'].append(dict(variant=variant,mode=mode,block=block,steps=4,
                        targets=count,seconds=seconds,targets_per_second=count/seconds,
                        cpu_seconds=cpu_after.user+cpu_after.system-cpu_before.user-cpu_before.system,
                        peak_vram_allocated_bytes=torch.cuda.max_memory_allocated(),
                        peak_vram_reserved_bytes=torch.cuda.max_memory_reserved()))
                    del adapter,optimizer;torch.cuda.empty_cache()
            phase[0]=variant+'_resume'
            def resume_run(label,limit,resume=None):
                adapter=make(variant,True);optimizer=adam(adapter)
                directory=output/(variant+'-'+label);directory.mkdir()
                recovery=dict(checkpoint_dir=directory,checkpoint_every_steps=1,
                    identity=dict(batch_factory=adapter.audit_context_boundary(),scope='T4_TECHNICAL_RESUME'))
                if resume is not None:recovery['resume_checkpoint']=resume
                stats=train_epoch(adapter,lambda:iter(records['train']),optimizer=optimizer,epoch=1,
                    budget=dict(max_steps=limit,max_targets=131072,max_seconds=60.,max_rss_bytes=2*1024**3,
                                min_available_ram_bytes=1),recovery=recovery,batch_factory=adapter.collate_training)
                return adapter,optimizer,stats,directory
            continuous,continuous_optimizer,full,_=resume_run('continuous',4)
            saved={key:value.detach().cpu().clone() for key,value in continuous.native.state_dict().items()}
            optimizer_state=continuous_optimizer.state_dict()
            del continuous,continuous_optimizer;torch.cuda.empty_cache()
            partial,partial_optimizer,interrupted,directory=resume_run('partial',1)
            if interrupted.complete:raise AssertionError('Expected bounded interruption')
            checkpoint=next(directory.glob('*.pt'))
            del partial,partial_optimizer;torch.cuda.empty_cache()
            resumed,resumed_optimizer,final,_=resume_run('resumed',4,checkpoint)
            compare(saved,{key:value.detach().cpu() for key,value in resumed.native.state_dict().items()})
            compare(optimizer_state,resumed_optimizer.state_dict())
            if not full.complete or not final.complete or full.valid_targets!=final.valid_targets or full.loss_sum!=final.loss_sum:
                raise AssertionError('Resume target/loss population differs')
            result['resume'].append(dict(variant=variant,status='PASS',targets=final.valid_targets,
                                         optimizer_steps=final.optimizer_steps,checkpoint_sha256=sha(checkpoint)))
            del resumed,resumed_optimizer,saved,optimizer_state;torch.cuda.empty_cache()
        result.update(status='T4_PARITY_PERFORMANCE_RESUME_VERIFIED',gpu_phase_seconds=time.monotonic()-gpu_started,
                      total_direct_step_calls=steps,limits='Small fixed cohort; full-fold/Modal billing not measured')
    except BaseException as error:
        import traceback
        result.update(error_type=type(error).__name__,error=str(error))
        (output/'failure.log').write_text(traceback.format_exc())
        raise
    finally:
        stop.set()
        if monitor is not None:monitor.join(timeout=6)
        result['wall_seconds']=time.monotonic()-began
        (output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        pins={str(path.relative_to(output)):dict(bytes=path.stat().st_size,sha256=sha(path))
              for path in output.rglob('*') if path.is_file()}
        (output/'OUTPUTS.json').write_text(json.dumps(pins,indent=2)+'\n')
        print(json.dumps({key:value for key,value in result.items() if key not in ('gpu_samples','measurements')}),flush=True)


if __name__=='__main__':
    main()
