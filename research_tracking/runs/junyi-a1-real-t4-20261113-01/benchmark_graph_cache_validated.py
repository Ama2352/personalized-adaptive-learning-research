"""Kiểm cache graph theo từng window, chỉ CPU, chưa nối producer.

Khóa cache bao gồm input quá khứ, phase, encoding và graph. Không cache alpha,
trọng số gate, logits hoặc gradient. Các bytes cache vẫn được kiểm integrity.
"""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import random
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))


def window_key(window,phase):
    metadata=(phase._condition_identity,phase._encoding_identity,phase.view.identity,
              window.window_id,window.inputs.user_ids)
    digest=hashlib.sha256(json.dumps(metadata,separators=(',',':')).encode())
    for array in (window.inputs.item_ids,window.inputs.timestamps,window.inputs.prior_responses,
                  window.inputs.source_rows,window.inputs.sequence_offsets,window.target_mask,
                  window.global_ranks,window.history_available,window.history_used,window.context_reset):
        digest.update(str(array.dtype).encode())
        digest.update(json.dumps(array.shape).encode())
        digest.update(array.tobytes())
    return digest.hexdigest()


def cached_batch(windows,phase,cache):
    import numpy as np
    from knowledge_tracing.akt.research_junyi_compact import CompactA1Context
    phase._light_check()
    shape=(len(windows),max(len(window.inputs.item_ids) for window in windows))
    messages=np.zeros(shape,dtype='<f4')
    active=np.zeros(shape,dtype=np.bool_)
    target=np.zeros(shape,dtype=np.bool_)
    valid=np.zeros(shape,dtype=np.bool_)
    sources=np.full(shape,-1,dtype='<i8')
    for row,window in enumerate(windows):
        context,expected_sha=cache[window_key(window,phase)]
        if context.identity!=expected_sha:
            raise ValueError('cached graph context changed')
        # Đã kiểm semantic khi fill; digest trên bytes bất biến xác nhận giữ nguyên.
        values=np.frombuffer(context.messages,dtype='<f4').reshape(context.shape)
        applied=np.frombuffer(context.applied,dtype=np.bool_).reshape(context.shape)
        targets=np.frombuffer(context.target_mask,dtype=np.bool_).reshape(context.shape)
        validity=np.frombuffer(context.valid_mask,dtype=np.bool_).reshape(context.shape)
        size=len(window.inputs.item_ids)
        messages[row,:size]=values[0]
        active[row,:size]=applied[0]
        target[row,:size]=targets[0]
        valid[row,:size]=validity[0]
        sources[row,:size]=np.frombuffer(context.source_rows,dtype='<i8')
    phase._light_check()
    return CompactA1Context(shape,tuple(window.window_id for window in windows),
        phase._condition_identity,phase._encoding_identity,phase.view.identity,
        messages.tobytes(),active.tobytes(),target.tobytes(),valid.tobytes(),sources.tobytes())


def main():
    import numpy as np
    from knowledge_tracing.akt.encoding import load_encoding
    from knowledge_tracing.akt.research_junyi_roles import JunyiResearchRoles
    from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView,JunyiResearchEncoding
    from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition,JunyiGraphPhaseSession
    from knowledge_tracing.akt.research_junyi_window_cache import _load_shard
    from knowledge_tracing.akt.research_junyi_compact import build_compact_context
    from knowledge_tracing.shared_kt import PrerequisiteGraph
    started=time.perf_counter()
    data=ROOT/'artifacts/akt/colab/junyi-real-t4-cohort-20261113-01'
    cohort=json.loads((data/'cohort.json').read_text())
    for name,digest in cohort['exported_files'].items():
        assert hashlib.sha256((data/name).read_bytes()).hexdigest()==digest
    payload=json.loads((data/'roles.json').read_text())
    for name in ('train_users','selection_users','calibration_users','outer_validation_users'):
        payload[name]=tuple(payload[name])
    roles=JunyiResearchRoles(**payload)
    train=JunyiPhaseView(roles,'select_train80',roles.train_users,roles.identity)
    encoding=JunyiResearchEncoding(load_encoding(data/'encoding.json'),train)
    topology=json.loads((data/'graph.json').read_text())
    graph=PrerequisiteGraph.from_edges(topology['nodes'],topology['corrected_edges'])
    condition=JunyiGraphCondition(encoding,graph,hashlib.sha256((data/'graph.json').read_bytes()).hexdigest())
    phase=JunyiGraphPhaseSession(condition,train)
    records=tuple(_load_shard(data/'train.npz',cohort['outputs']['train'],dict(shard_records=256,max_shard_tokens=51200)))
    windows=tuple(record.window for record in records)
    cache={}
    before=time.perf_counter()
    from knowledge_tracing.akt.research_junyi_compact import CompactA1Context
    for begin in range(0,len(windows),128):
        group=windows[begin:begin+128]
        bulk=build_compact_context(group,phase)
        messages,active,target,valid=bulk.arrays()
        sources=np.frombuffer(bulk.source_rows,dtype='<i8').reshape(bulk.shape)
        for row,window in enumerate(group):
            size=len(window.inputs.item_ids)
            context=CompactA1Context((1,size),(window.window_id,),bulk.condition_sha256,
                bulk.encoding_sha256,bulk.phase_sha256,messages[row,:size].tobytes(),
                active[row,:size].tobytes(),target[row,:size].tobytes(),valid[row,:size].tobytes(),
                sources[row,:size].tobytes())
            context.arrays()
            key=window_key(window,phase)
            assert key not in cache
            cache[key]=(context,context.identity)
    build_seconds=time.perf_counter()-before
    timings=[]
    for method in ('direct','cached','cached','direct'):
        at=time.perf_counter()
        hashes=[]
        for begin in range(0,len(windows),128):
            group=windows[begin:begin+128]
            context=build_compact_context(group,phase) if method=='direct' else cached_batch(group,phase,cache)
            hashes.append(context.identity)
        timings.append(dict(method=method,seconds=time.perf_counter()-at,hashes=hashes))
    assert all(row['hashes']==timings[0]['hashes'] for row in timings)
    shuffled=list(windows)
    random.Random(47).shuffle(shuffled)
    for begin in range(0,len(shuffled),97):
        group=tuple(shuffled[begin:begin+97])
        assert build_compact_context(group,phase).identity==cached_batch(group,phase,cache).identity
    # Giữ window_id nhưng đổi prior response phải miss cache.
    sample=next(window for window in windows if len(window.inputs.item_ids)>3)
    prior=sample.inputs.prior_responses.copy()
    prior[-1]=1-prior[-1]
    changed=replace(sample,inputs=replace(sample.inputs,prior_responses=prior))
    assert window_key(changed,phase) not in cache
    other_view=JunyiPhaseView(roles,'raw_selection10',roles.selection_users,roles.identity)
    other_phase=JunyiGraphPhaseSession(condition,other_view)
    assert window_key(sample,other_phase) not in cache
    original,expected_sha=cache[window_key(sample,phase)]
    poisoned=replace(original,messages=b'\x00'*len(original.messages))
    cache[window_key(sample,phase)]=(poisoned,expected_sha)
    try:
        cached_batch((sample,),phase,cache)
    except ValueError:
        corrupt_rejected=True
    else:
        corrupt_rejected=False
    assert corrupt_rejected
    means={name:sum(row['seconds'] for row in timings if row['method']==name)/2 for name in ('direct','cached')}
    result=dict(status='PASS_VALIDATED_IMMUTABLE_GRAPH_CACHE_CPU_PROTOTYPE',windows=len(windows),
        targets=cohort['outputs']['train']['targets'],build_once_seconds=build_seconds,
        timings=timings,mean_seconds=means,warm_component_speedup=means['direct']/means['cached'],
        shuffled_rebatch_identity_matches=True,changed_prior_misses=True,changed_phase_misses=True,
        corrupted_context_rejected=True,semantic_validated_on_fill=True,hash_verified_each_lookup=True,gpu_used=False,production_cache_implemented=False,
        modal_spent_usd=0,elapsed_seconds=time.perf_counter()-started,
        limits_vi='Cache RAM prototype trên256window, chưa cache đĩa toàn TRAIN80 hoặc tích hợp producer. '
                  'Warm lookup vẫn hash toàn input và cache bytes, kiểm phase trước/sau. '
                  'Chỉ tăng tốc phần context CPU, chưa suy ra throughput CUDA hoặc thời gian epoch.')
    (HERE/'graph-cache-validated-prototype.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    main()
