"""Prototype CPU A1 cố định confidence1, chưa nối vào trainer hoặc checkpoint.

Chỉ dùng shifted responses của native window. Alpha và trọng số model vẫn phải
tính trong forward. Mỗi call giữ kiểm phase/window trước và sau như reference.
"""
import hashlib
import json

import numpy as np


def parent_ids(phase):
    vocabulary=phase.condition.encoding.native.vocabulary.values
    indices={name:index for index,name in enumerate(vocabulary)}
    # Parent ngoài vocabulary không bao giờ có quan sát trong native window.
    return tuple(tuple(indices[parent] for parent in phase._parents_by_child.get(child, ())
                       if parent in indices) for child in vocabulary)


def compact_window(window, phase, parents):
    from knowledge_tracing.akt.research_junyi_graph import _validate_window
    phase._light_check()
    _validate_window(window,phase)
    counts={}
    successes={}
    ids=window.inputs.item_ids
    messages=np.zeros(len(ids),dtype=np.float32)
    active=np.zeros(len(ids),dtype=np.bool_)
    for local,item_id in enumerate(ids):
        if local:
            previous=int(ids[local-1])
            counts[previous]=counts.get(previous,0)+1
            successes[previous]=successes.get(previous,0)+int(window.inputs.prior_responses[local])
        if window.target_mask[local]:
            observed=tuple(parent for parent in parents[int(item_id)] if counts.get(parent,0)>0)
            if observed:
                messages[local]=sum(successes[parent]/counts[parent]-.5 for parent in observed)/len(observed)
                active[local]=True
    phase._light_check()
    return messages,active


def prepare_batch(windows,phase,parents):
    messages=np.zeros((len(windows),200),dtype=np.float32)
    active=np.zeros((len(windows),200),dtype=np.bool_)
    source=hashlib.sha256()
    for row,window in enumerate(windows):
        values,mask=compact_window(window,phase,parents)
        messages[row,:len(values)]=values
        active[row,:len(mask)]=mask
        metadata=(window.window_id,window.inputs.user_ids)
        source.update(json.dumps(metadata,separators=(',',':')).encode())
        for array in (window.inputs.item_ids,window.inputs.timestamps,
                      window.inputs.prior_responses,window.inputs.source_rows,
                      window.inputs.sequence_offsets,window.global_ranks,window.target_mask,
                      window.history_used,window.history_available,window.context_reset):
            source.update(str(array.dtype).encode())
            source.update(json.dumps(array.shape).encode())
            source.update(array.tobytes())
    header=json.dumps(dict(scope=phase.view.identity,condition=phase._condition_identity,
        encoding=phase._encoding_identity,input_sha256=source.hexdigest(),
        shape=messages.shape,recipe='A1_fixed_uniform_one_effective_native_prefix'),
        sort_keys=True,separators=(',',':')).encode()
    # Bytes bất biến để kiểm digest lặp mà không dựng lại audit object.
    payload=(header,messages.tobytes(),active.tobytes())
    return messages,active,payload


def compact_sha(payload):
    digest=hashlib.sha256()
    for part in payload:
        digest.update(len(part).to_bytes(8,'little'))
        digest.update(part)
    return digest.hexdigest()
