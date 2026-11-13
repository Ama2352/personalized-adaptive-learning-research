"""Đo validation A0/A1 từng cửa sổ và batch128 trên T4, dữ liệu giả."""
import argparse
from dataclasses import replace
import gc
import json
import os
from pathlib import Path
import statistics
import sys
import time

os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    output=args.output.resolve()
    if not output.is_relative_to(ROOT/'experiments/akt/results') or output.exists():
        parser.error('Output mới trong experiments/akt/results')
    import numpy as np
    import torch
    from knowledge_tracing.akt.config import AKTConfig,ResearchCUDAExecutionProfile
    from knowledge_tracing.akt.encoding import ExerciseEncoding
    from knowledge_tracing.akt.model import AKTAdapter
    from knowledge_tracing.akt.prediction import iter_predictions
    from knowledge_tracing.akt.prediction_batch import iter_predictions_batched
    from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView,JunyiResearchEncoding
    from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition,JunyiGraphPhaseSession
    from knowledge_tracing.akt.research_junyi_graph_model import JunyiGraphAKTAdapter
    from knowledge_tracing.akt.research_junyi_roles import make_junyi_research_roles
    from knowledge_tracing.akt.research_junyi_selection import _evaluate
    from knowledge_tracing.akt.training import _seed
    from knowledge_tracing.akt.types import KTEvent,LearnerEvents
    from knowledge_tracing.shared_kt import PrerequisiteGraph,StableVocabulary
    if not torch.cuda.is_available() or torch.cuda.device_count()!=1 or 'T4' not in torch.cuda.get_device_name(0):
        raise ValueError('Probe yêu cầu một T4 GPU thực')
    output.mkdir(parents=True)
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    torch.backends.cudnn.benchmark=False
    torch.set_float32_matmul_precision('highest')
    budget=12*1024**3
    torch.cuda.set_per_process_memory_fraction(budget/torch.cuda.get_device_properties(0).total_memory,0)
    profile=ResearchCUDAExecutionProfile(budget,recipe_id='cgakt-cuda-fp32-batch128-v2')
    config=replace(AKTConfig(),phase='junyi-research',device='cuda',outer_fold=4,run_id=output.name,
        output_dir=output,execution_enabled=True,batch_size=128,protocol_version='akt-nr-exercise-v2-batch128',
        max_train_users=640,max_val_users=64,max_targets_per_side=12800,max_total_targets=12800,
        max_steps=1,max_seconds=240,max_wall_seconds=280,max_rss_bytes=8*1024**3,min_available_ram_bytes=1)
    roles=make_junyi_research_roles([(str(index),index%5,'development') for index in range(1000)])
    train=JunyiPhaseView(roles,'select_train80',roles.train_users,roles.identity)
    selection=JunyiPhaseView(roles,'raw_selection10',roles.selection_users[:64],roles.identity)
    values=tuple(['A','B','C']+[f'fixture-{index:03d}' for index in range(714)])
    encoding=JunyiResearchEncoding(ExerciseEncoding(StableVocabulary(values),{item:1 for item in values}),train)
    condition=JunyiGraphCondition(encoding,PrerequisiteGraph.from_edges(values,(('A','C'),('B','C'))),'f'*64)
    learners=tuple(LearnerEvents(user,0,tuple(KTEvent(user,('A','B','C')[rank%3],rank+1,
        index*200+rank+1,(index+rank)%2,0,0) for rank in range(200)))
        for index,user in enumerate(selection.users))
    results=[]
    started=time.monotonic()
    for variant in ('A0','A1'):
        _seed(42)
        with torch.device('cpu'):
            if variant=='A0':
                adapter=AKTAdapter(config,encoding.native)
            else:
                adapter=JunyiGraphAKTAdapter(config=config,encoding=encoding,condition=condition,
                    phase=JunyiGraphPhaseSession(condition,selection),cuda_profile=profile)
                with torch.no_grad():
                    adapter.native.alpha.fill_(1.)
        adapter.checkpoint_id='synthetic-validation-fixture-'+variant
        # Warm-up riêng, không ghi vào thời gian so sánh.
        _evaluate(adapter,iter(learners[:1]),200)
        _evaluate(adapter,iter(learners[:1]),200,batch_size=128)
        timings={1:[],128:[]}
        peaks={1:[],128:[]}
        metrics={}
        for repeat in range(3):
            for batch in ((1,128) if repeat%2==0 else (128,1)):
                torch.cuda.synchronize()
                torch.cuda.reset_peak_memory_stats()
                before=time.perf_counter()
                options={} if batch==1 else dict(batch_size=batch)
                measured=_evaluate(adapter,iter(learners),12800,**options)
                torch.cuda.synchronize()
                timings[batch].append(time.perf_counter()-before)
                peaks[batch].append(torch.cuda.max_memory_allocated())
                if batch in metrics and metrics[batch]!=measured:
                    raise ValueError('Validation không xác định giữa các lượt lặp')
                metrics[batch]=measured
        if metrics[1]['population_sha256']!=metrics[128]['population_sha256']:
            raise ValueError('Target population mismatch')
        legacy=list(iter_predictions(adapter,iter(learners)))
        batched=list(iter_predictions_batched(adapter,iter(learners),batch_size=128))
        if [replace(row,prediction=None) for row in legacy]!=[replace(row,prediction=None) for row in batched]:
            raise ValueError('Target/coverage/order metadata mismatch')
        p=np.asarray([row.prediction for row in legacy],dtype=np.float64)
        q=np.asarray([row.prediction for row in batched],dtype=np.float64)
        np.testing.assert_allclose(q,p,atol=1e-6,rtol=1e-6)
        maximum=float(np.max(np.abs(p-q)))
        mean=float(np.mean(np.abs(p-q)))
        ll_delta=metrics[128]['native_bce']-metrics[1]['native_bce']
        if abs(ll_delta)>1e-6:
            raise ValueError('Log Loss parity tolerance exceeded')
        results.append(dict(variant=variant,targets=12800,learners=64,windows=128,
            legacy_seconds=timings[1],batch128_seconds=timings[128],
            legacy_mean_seconds=statistics.mean(timings[1]),batch128_mean_seconds=statistics.mean(timings[128]),
            speedup=statistics.mean(timings[1])/statistics.mean(timings[128]),
            legacy_peak_vram_bytes=max(peaks[1]),batch128_peak_vram_bytes=max(peaks[128]),
            max_abs_probability_delta=maximum,mean_abs_probability_delta=mean,
            log_loss_delta=ll_delta,population_sha256=metrics[1]['population_sha256'],
            targets_metadata_exact=True,metrics=metrics))
        del adapter,legacy,batched
        gc.collect()
        torch.cuda.empty_cache()
    report=dict(status='PASS_SYNTHETIC_VALIDATION_BATCH128_PARITY',scope='SYNTHETIC_IN_MEMORY_LEARNERS',
        torch=torch.__version__,cuda=torch.version.cuda,gpu=torch.cuda.get_device_name(0),
        vocabulary=717,results=results,seconds=time.monotonic()-started,model_training=False,
        a0_checkpoint_epoch_selection_replayed=False,
        limits_vi='Đo trên dữ liệu giả đã có trong RAM, chưa gồm SQL Junyi/I/O toàn tập. Chưa kiểm lại chọn epoch A0 từ12checkpoint thật.')
    (output/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':
    main()
