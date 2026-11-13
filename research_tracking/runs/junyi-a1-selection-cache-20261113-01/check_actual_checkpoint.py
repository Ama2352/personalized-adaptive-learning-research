"""Probe CPU hữu hạn từ checkpoint epoch1 thật, source2 cô lập và compact mới."""
import copy
import argparse
import hashlib
import json
import os
import random
from pathlib import Path
import sys
import time
import types
import zipfile

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device',choices=('cpu','cuda'),default='cpu')
    parser.add_argument('--output-name',default='actual-checkpoint-parity.json')
    parser.add_argument('--shard-index',type=int)
    args=parser.parse_args()
    assert Path(args.output_name).name==args.output_name and args.output_name.endswith('.json')
    import numpy as np
    import psutil
    import torch
    from knowledge_tracing.akt.config import AKTConfig,ResearchCUDAExecutionProfile
    from knowledge_tracing.akt.research_junyi_selection import load_full_selected_cache
    from knowledge_tracing.akt.research_junyi_data import load_prepared_junyi_encoding
    from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition,JunyiGraphPhaseSession
    from knowledge_tracing.akt.research_junyi_window_cache import _load_shard
    from knowledge_tracing.akt.research_junyi_compact import build_compact_context
    from knowledge_tracing.akt import research_graph_model as current_native
    from knowledge_tracing.akt import research_junyi_graph_model as current_adapter
    from knowledge_tracing.akt.checkpoint import restore_checkpoint
    from knowledge_tracing.shared_kt import PrerequisiteGraph
    started=time.perf_counter()
    torch.set_num_threads(2)
    torch.manual_seed(42)
    torch.use_deterministic_algorithms(True)
    request=json.loads((ROOT/'research_tracking/runs/junyi-a1-selected-20261113-01/request05.json').read_text())
    checkpoint=ROOT/'experiments/akt/results/modal-junyi-a1-b128-h100-20261113-05/checkpoints/train-epoch-001/state.pt'
    digest=hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    assert digest=='eb614e5fcd3f8d1c3d19d51d0c088ee075e6924ca8560fbf1b893b9df9d224e9'
    payload=torch.load(checkpoint,map_location='cpu',weights_only=True)
    assert payload['progress']['epoch']==1 and payload['progress']['validation_complete'] is False
    source=ROOT/request['archives']['source']['path']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==request['archives']['source']['sha256']
    modules={}
    with zipfile.ZipFile(source) as archive:
        pins=json.loads(archive.read('MANIFEST.json'))['files']
        for filename in ('research_graph_model','research_junyi_graph_model'):
            name='src/knowledge_tracing/akt/'+filename+'.py'
            raw=archive.read(name);pin=pins[name];pin=pin if isinstance(pin,str) else pin['sha256']
            assert hashlib.sha256(raw).hexdigest()==pin
            module_name='knowledge_tracing.akt._source2_'+filename
            module=types.ModuleType(module_name);module.__package__='knowledge_tracing.akt'
            # Source frozen được kiểm từ ZIP; __file__ giữ root vật lý cho guard.
            module.__file__=str(ROOT/name)
            sys.modules[module_name]=module
            exec(compile(raw,str(source)+'!/'+name,'exec'),module.__dict__)
            modules[filename]=module
    old_native=modules['research_graph_model'];old_adapter=modules['research_junyi_graph_model']
    for name in ('ResearchGraphNative','_evidence_sha','source_inventory'):
        setattr(old_adapter,name,getattr(old_native,name))
    profile=None
    if args.device=='cpu':
        # Chỉ admission CPU của probe, không phát hành runtime/Gate hoặc quyền train.
        for module in (old_native,old_adapter,current_native,current_adapter):
            module.validate_config=lambda *args,**kwargs:None
    else:
        profile=ResearchCUDAExecutionProfile(**payload['identity']['profile'])
        torch.backends.cuda.matmul.allow_tf32=False
        torch.backends.cudnn.allow_tf32=False
        torch.backends.cudnn.benchmark=False
        torch.set_float32_matmul_precision('highest')
        torch.cuda.set_per_process_memory_fraction(profile.max_vram_bytes/torch.cuda.get_device_properties(0).total_memory,0)
    data=request['inputs']
    inputs=load_full_selected_cache(ROOT/data['selected_cache_root'],ROOT/data['roles_path'],
        expected_manifest_sha256=data['selected_cache_manifest_sha256'],expected_roles_sha256=data['roles_sha256'])
    encoding=load_prepared_junyi_encoding(ROOT/data['encoding_file'],ROOT/data['encoding_receipt'],
        view=inputs.train,source_data_sha256=inputs.source_identity,
        expected_file_sha256=data['encoding_sha256'],expected_receipt_sha256=data['encoding_receipt_sha256'])
    topology=json.loads((ROOT/request['graph_file']).read_text())
    condition=JunyiGraphCondition(encoding,PrerequisiteGraph.from_edges(topology['nodes'],topology['corrected_edges']),request['graph_sha256'])
    phase=JunyiGraphPhaseSession(condition,inputs.train)
    cache=ROOT/data['train_window_cache'];manifest=json.loads((cache/'manifest.json').read_text())
    if args.shard_index is None:
        cohort=json.loads((ROOT/'artifacts/akt/colab/junyi-real-t4-cohort-20261113-01/cohort.json').read_text())
        shard_indices=cohort['train_shard_indices']
    else:
        assert 0<=args.shard_index<len(manifest['shards'])
        shard_indices=(args.shard_index,)
    records=()
    for shard_index in shard_indices:
        entry=manifest['shards'][shard_index]
        candidates=tuple(_load_shard(cache/entry['name'],entry,manifest))
        active=build_compact_context(tuple(e.window for e in candidates),phase).arrays()[1].any(axis=1)
        indices=np.flatnonzero(active)[:2]
        if len(indices)==2:
            records=tuple(candidates[int(index)] for index in indices)
            break
    assert len(records)==2,'Technical probe requires two windows with observed prerequisites'
    values=dict(payload['identity']['config'])
    values.update(project_root=ROOT,source_root=ROOT/'artifacts/akt/dependencies/upstream',
        run_id='actual-checkpoint-parity',output_dir=ROOT/'experiments/akt/results/actual-checkpoint-parity',device=args.device)
    values['betas']=tuple(values['betas'])
    config=AKTConfig(**values)
    adapters=[old_adapter.JunyiGraphAKTAdapter(config=config,encoding=encoding,condition=condition,phase=phase,cuda_profile=profile),
              current_adapter.JunyiGraphAKTAdapter(config=config,encoding=encoding,condition=condition,phase=phase,compact_context=True,cuda_profile=profile)]
    snapshots=[]
    for adapter in adapters:
        assert time.perf_counter()-started<180 and psutil.Process().memory_info().rss<(6 if profile else 1)*1024**3
        optimizer=torch.optim.Adam(adapter.native.parameters(),lr=config.lr,betas=config.betas,eps=config.eps,
                                   weight_decay=config.weight_decay,foreach=False,fused=False)
        restore_checkpoint(adapter,optimizer,copy.deepcopy(payload))
        probabilities=adapter.predict_windows(tuple(e.window for e in records))
        result=adapter.step(adapter.collate_training(records),optimizer)
        snapshots.append(dict(probabilities=probabilities,loss=result['loss_sum'],targets=result['valid_targets'],
            model={k:v.detach().clone() for k,v in adapter.native.state_dict().items()},
            gradients={k:None if v.grad is None else v.grad.detach().clone() for k,v in adapter.native.named_parameters()},
            optimizer=optimizer.state_dict(),rng=(random.getstate(),np.random.get_state(),torch.get_rng_state().clone(),
                torch.cuda.get_rng_state_all() if profile else [])))
    def equal(a,b):
        if torch.is_tensor(a):assert torch.equal(a,b)
        elif isinstance(a,np.ndarray):assert np.array_equal(a,b)
        elif isinstance(a,dict):
            assert a.keys()==b.keys()
            for key in a:equal(a[key],b[key])
        elif isinstance(a,(list,tuple)):
            assert len(a)==len(b)
            for first,second in zip(a,b):equal(first,second)
        else:assert a==b
    equal(*snapshots)
    output=dict(status='PASS_ACTUAL_CHECKPOINT_'+args.device.upper()+'_SOURCE2_COMPACT_EXACT',checkpoint_sha256=digest,
        source_identity=payload['identity'],max_absolute_drift=0.,windows=len(records),targets=snapshots[0]['targets'],
        alpha=float(payload['model_state_dict']['alpha']),elapsed_seconds=time.perf_counter()-started,
        shard_index=shard_index,active_graph_targets=int(build_compact_context(tuple(e.window for e in records),phase).arrays()[1].sum()),
        checks=dict(probability=True,loss=True,gradient=True,model=True,optimizer=True,rng=True,targets=True),
        gpu_used=profile is not None,
        limits_vi='Hai window TRAIN80 thật và một bước Adam tạm, không thay checkpoint nghiên cứu. '
                  'CPU tắt admission CUDA chỉ trong process probe. CUDA dùng đầy đủ profile/guard.')
    with (HERE/args.output_name).open('x',encoding='utf-8') as stream:
        stream.write(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k!='source_identity'},ensure_ascii=False))


if __name__=='__main__':
    main()
