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

    result=dict(status='FAILED_PRESERVED',scope='REAL_JUNYI_T4_STEADY_PIPELINE_PROFILE',

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

            execution_enabled=True,run_id='a1-real-t4-profile',output_dir=root/'experiments/akt/results/a1-real-t4-profile',

            batch_size=128,protocol_version='akt-nr-exercise-v2-batch128',max_train_users=256,max_val_users=64,

            max_targets_per_side=2097152,max_total_targets=2097152,max_steps=224,max_seconds=175,

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

            assert workloads['optimizer_steps']+1<=224

            assert workloads['training_targets']+count<=2097152

            record=adapter.step(adapter.collate_training(group),optimizer)

            assert record['valid_targets']==count

            workloads['optimizer_steps']+=1;workloads['training_targets']+=count

            return record

        import gc
        import psutil
        from contextlib import ExitStack
        from unittest.mock import patch
        from knowledge_tracing.akt.model import AKTAdapter
        from knowledge_tracing.akt.tensors import collate_windows
        from knowledge_tracing.akt.config import validate_config
        from knowledge_tracing.akt import research_graph_model as native_module
        from knowledge_tracing.akt import research_junyi_graph_model as adapter_module
        validate_config(config,cuda_profile=profile)
        process=psutil.Process()
        result['conditions']=[]
        result['max_steps']=224
        result['max_training_targets']=2097152
        result['max_rss_bytes']=6*1024**3
        result['resource_samples']=[]
        def sample():
            while not stopped.wait(.5):
                row=subprocess.run(['nvidia-smi','--query-gpu=utilization.gpu,memory.used,power.draw,clocks.current.sm,temperature.gpu',
                    '--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=3)
                rss=process.memory_info().rss
                result['samples'].append(dict(phase=phase[0],at=time.monotonic(),values=row.stdout.strip(),returncode=row.returncode,rss_bytes=rss))
                if rss>result['max_rss_bytes']:
                    result['resource_failure']='RSS exceeded sixGiB'
                    os.kill(os.getpid(),signal.SIGALRM)
                    return
        monitor=threading.Thread(target=sample,daemon=True)
        monitor.start()
        def digest_state(state):
            digest=hashlib.sha256()
            for key,value in state.items():
                digest.update(key.encode());digest.update(value.detach().cpu().contiguous().numpy().tobytes())
            return digest.hexdigest()
        def wrapped_region(label,function):
            def wrapper(*args,**kwargs):
                with torch.profiler.record_function(label):
                    return function(*args,**kwargs)
            return wrapper
        for name in ('A0_streaming','A1_streaming','A1_preloaded'):
            phase[0]='setup-'+name
            torch.manual_seed(42);torch.cuda.manual_seed_all(42)
            if name.startswith('A0'):
                adapter=AKTAdapter(config,encoding.native)
            else:
                adapter=JunyiGraphAKTAdapter(config=config,encoding=encoding,condition=condition,
                    phase=session,cuda_profile=profile,compact_context=True)
            adapter.native.train()
            initial={key:value.detach().cpu().clone() for key,value in adapter.native.state_dict().items()}
            initial_sha=digest_state(initial)
            optimizer=torch.optim.Adam(adapter.native.parameters(),lr=config.lr,betas=config.betas,
                eps=config.eps,weight_decay=config.weight_decay,foreach=False,fused=False)
            def make_batch(group):
                if name.startswith('A0'):
                    return collate_windows([entry.window for entry in group],n_items=len(values),device='cuda:0',targets=[entry.targets for entry in group])
                return adapter.collate_training(group)
            def step(group):
                count=sum(int(entry.window.target_mask.sum()) for entry in group)
                assert workloads['optimizer_steps']+1<=224 and workloads['training_targets']+count<=2097152
                before=time.perf_counter()
                with torch.profiler.record_function('batch_prepare'):
                    batch=make_batch(group)
                prepared=time.perf_counter()
                with torch.profiler.record_function('model_adapter_step'):
                    record=adapter.step(batch,optimizer)
                finished=time.perf_counter()
                workloads['optimizer_steps']+=1;workloads['training_targets']+=count
                assert record['valid_targets']==count
                return dict(targets=count,prepare_seconds=prepared-before,step_seconds=finished-prepared,
                            forward_seconds=record['forward_seconds'],backward_launch_seconds=record['backward_seconds'],
                            clip_seconds=record['gradient_clip_seconds'],optimizer_seconds=record['optimizer_seconds'])
            # Làm nóng hai batch trước đoạn ghi utilization và throughput.
            for begin in range(0,len(entries),128):step(entries[begin:begin+128])
            torch.cuda.synchronize()
            phase[0]=name
            at=time.perf_counter()
            records=[];reads=[]
            while time.perf_counter()-at<15 and len(records)<64:
                io_at=time.perf_counter()
                actual=entries if name.endswith('preloaded') else read('train')
                reads.append(time.perf_counter()-io_at)
                for begin in range(0,len(actual),128):records.append(step(actual[begin:begin+128]))
            torch.cuda.synchronize()
            elapsed=time.perf_counter()-at
            result['conditions'].append(dict(name=name,seconds=elapsed,steps=len(records),
                targets=sum(row['targets'] for row in records),targets_per_second=sum(row['targets'] for row in records)/elapsed,
                read_seconds=sum(reads),batch_prepare_seconds=sum(row['prepare_seconds'] for row in records),
                adapter_step_seconds=sum(row['step_seconds'] for row in records),step_records=records,initial_state_sha256=initial_sha))
            phase[0]='idle'
            if name=='A1_streaming':
                # Profiling tách khỏi đoạn tính tốc độ để giữ rõ overhead dụng cụ.
                phase[0]='profiler'
                with ExitStack() as stack:
                    for module,attribute,label in [
                        (adapter_module,'build_compact_context','graph_context_CPU'),
                        (adapter_module,'_batch_sha','batch_integrity_hash'),
                        (native_module,'_batch_sha','batch_integrity_hash'),
                        (adapter_module,'_evidence_sha','evidence_digest'),
                        (native_module,'_evidence_sha','evidence_digest'),
                        (adapter_module,'_cuda_execution_check','cuda_guard'),
                        (native_module,'_cuda_execution_check','cuda_guard'),
                        (JunyiGraphAKTAdapter,'_integrity','adapter_integrity')]:
                        stack.enter_context(patch.object(module,attribute,wrapped_region(label,getattr(module,attribute))))
                    with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,torch.profiler.ProfilerActivity.CUDA],
                                                record_shapes=False,profile_memory=False,with_stack=False) as profiler:
                        for _ in range(2):
                            with torch.profiler.record_function('input_read_validate'):
                                actual=read('train')
                            for begin in range(0,len(actual),128):step(actual[begin:begin+128])
                    torch.cuda.synchronize()
                profiler.export_chrome_trace(str(output/'torch-trace.json'))
                averages=profiler.key_averages()
                rows=[]
                for item in averages:
                    rows.append(dict(key=item.key,count=item.count,self_cpu_us=item.self_cpu_time_total,
                        total_cpu_us=item.cpu_time_total,self_device_us=getattr(item,'self_device_time_total',0),
                        total_device_us=getattr(item,'device_time_total',0)))
                (output/'profile-operations.json').write_text(json.dumps(rows,indent=2)+'\n')
                (output/'profile-cpu.txt').write_text(averages.table(sort_by='self_cpu_time_total',row_limit=35))
                device_key='self_device_time_total' if rows and hasattr(next(iter(averages)),'self_device_time_total') else 'self_cuda_time_total'
                (output/'profile-device.txt').write_text(averages.table(sort_by=device_key,row_limit=35))
                del profiler,averages
                phase[0]='idle'
            # Không tạo research model từ profiler; phục hồi đúng khởi tạo rồi bỏ bản tạm.
            adapter.native.load_state_dict(initial,strict=True)
            assert digest_state(adapter.native.state_dict())==initial_sha
            result['conditions'][-1]['initial_state_restored']=True
            del optimizer,adapter,initial
            gc.collect();torch.cuda.empty_cache()
        result['workload']=workloads
        result['status']='PASS_REAL_T4_STEADY_PIPELINE_PROFILE'
    except BaseException as error:
        result.update(error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc())
    finally:
        signal.alarm(0)
        stopped.set()
        if monitor is not None:monitor.join(timeout=4)
        result['elapsed_seconds']=time.monotonic()-started
        result['limits_vi']='Mỗi condition15giây hoặc64step, warmup2step, cohort thật lặp để đo kỹ thuật. A0/A1 là đối chiếu chi phí pipeline, không so chất lượng mô hình. A1_preloaded chỉ bỏ đọc/kiểm NPZ lặp, chưa là prefetch production. Profiler4step riêng, giữ kiểm integrity qua wrapper gọi nguyên hàm. Khởi tạo được phục hồi sau từng condition. Không chọn model/epoch, không dùng checkpoint nghiên cứu, không suy ra H100.'
        (output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({key:value for key,value in result.items() if key not in ('samples','traceback')},ensure_ascii=False))
    return 0 if result['status']=='PASS_REAL_T4_STEADY_PIPELINE_PROFILE' else 1

if __name__=='__main__':
    raise SystemExit(main())
