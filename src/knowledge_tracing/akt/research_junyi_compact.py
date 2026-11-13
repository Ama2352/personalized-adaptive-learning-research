"""Context A1 dạng bytes bất biến, giữ message từ native prefix quá khứ.

Không cache weights/gate hoặc đọc target labels. Kiểm phase ở hai đầu batch,
kiểm geometry từng window. Reference audit vẫn ở research_junyi_graph.py.
"""
from dataclasses import dataclass
import hashlib
import json

import numpy as np

from .research_junyi_graph import JunyiGraphPhaseSession, _validate_window

FORMAT = 'junyi-a1-compact-context-v1'


def _need(ok, message):
    if not ok:
        raise ValueError(message)


@dataclass(frozen=True)
class CompactA1Context:
    shape: tuple[int, int]
    window_ids: tuple[str, ...]
    condition_sha256: str
    encoding_sha256: str
    phase_sha256: str
    messages: bytes
    applied: bytes
    target_mask: bytes
    valid_mask: bytes
    source_rows: bytes

    @property
    def identity(self):
        header=(FORMAT,self.shape,self.window_ids,self.condition_sha256,
                self.encoding_sha256,self.phase_sha256)
        digest=hashlib.sha256(json.dumps(header,separators=(',',':')).encode())
        for payload in (self.messages,self.applied,self.target_mask,self.valid_mask,self.source_rows):
            _need(type(payload) is bytes, 'immutable compact context bytes required')
            digest.update(len(payload).to_bytes(8,'little'))
            digest.update(payload)
        return digest.hexdigest()

    def arrays(self):
        _need(type(self.shape) is tuple and len(self.shape)==2
              and all(type(size) is int and size>0 for size in self.shape)
              and self.shape[1]<=200, 'bounded compact context shape required')
        size=self.shape[0]*self.shape[1]
        _need(all(type(value) is bytes for value in (self.messages,self.applied,
              self.target_mask,self.valid_mask,self.source_rows)), 'immutable compact payload required')
        _need(len(self.messages)==4*size and len(self.source_rows)==8*size
              and all(len(value)==size for value in (self.applied,self.target_mask,self.valid_mask)),
              'compact payload size mismatch')
        for value in (self.applied,self.target_mask,self.valid_mask):
            _need(np.isin(np.frombuffer(value,dtype=np.uint8),(0,1)).all(), 'Boolean compact mask required')
        message=np.frombuffer(self.messages,dtype='<f4').reshape(self.shape)
        active=np.frombuffer(self.applied,dtype=np.bool_).reshape(self.shape)
        target=np.frombuffer(self.target_mask,dtype=np.bool_).reshape(self.shape)
        valid=np.frombuffer(self.valid_mask,dtype=np.bool_).reshape(self.shape)
        _need(np.isfinite(message).all() and np.all(message[~active]==0)
              and not np.any(active & ~(target & valid)), 'invalid compact message or active mask')
        return message,active,target,valid

    def assert_for(self,batch,condition_sha256):
        message,active,target,valid=self.arrays()
        _need(self.condition_sha256==condition_sha256 and self.shape==tuple(batch.q_data.shape),
              'compact condition/batch mismatch')
        _need(type(self.window_ids) is tuple and len(self.window_ids)==self.shape[0]
              and all(type(value) is str and value for value in self.window_ids)
              and len(set(self.window_ids))==len(self.window_ids), 'unique compact window IDs required')
        _need(np.array_equal(target,batch.target_mask.detach().cpu().numpy())
              and np.array_equal(valid,batch.valid_mask.detach().cpu().numpy())
              and np.array_equal(np.frombuffer(self.source_rows,dtype='<i8').reshape(self.shape),
                                 batch.source_rows), 'compact target/source rows mismatch')
        return message,active


def build_compact_context(windows,phase):
    _need(type(phase) is JunyiGraphPhaseSession and type(windows) is tuple and windows,
          'typed phase and nonempty windows required')
    _need(phase.condition.variant=='A1', 'Weighted A2/A3 compact context requires a separate implementation')
    phase._light_check()
    vocabulary=phase.condition.encoding.native.vocabulary.values
    indices={name:index for index,name in enumerate(vocabulary)}
    parents=tuple(tuple(indices[parent] for parent in phase._parents_by_child.get(child,())
                        if parent in indices) for child in vocabulary)
    for window in windows:
        _validate_window(window,phase)
    shape=(len(windows),max(len(window.inputs.item_ids) for window in windows))
    messages=np.zeros(shape,dtype='<f4')
    applied=np.zeros(shape,dtype=np.bool_)
    target=np.zeros(shape,dtype=np.bool_)
    valid=np.zeros(shape,dtype=np.bool_)
    sources=np.full(shape,-1,dtype='<i8')
    for row,window in enumerate(windows):
        ids=window.inputs.item_ids
        counts,successes={},{}
        for local,item_id in enumerate(ids):
            if local:
                previous=int(ids[local-1])
                counts[previous]=counts.get(previous,0)+1
                successes[previous]=successes.get(previous,0)+int(window.inputs.prior_responses[local])
            if window.target_mask[local]:
                observed=tuple(parent for parent in parents[int(item_id)] if counts.get(parent,0)>0)
                if observed:
                    messages[row,local]=sum(successes[parent]/counts[parent]-.5 for parent in observed)/len(observed)
                    applied[row,local]=True
        size=len(ids)
        target[row,:size]=window.target_mask
        valid[row,:size]=True
        sources[row,:size]=window.inputs.source_rows
    phase._light_check()
    return CompactA1Context(shape,tuple(window.window_id for window in windows),
        phase._condition_identity,phase._encoding_identity,phase.view.identity,
        messages.tobytes(),applied.tobytes(),target.tobytes(),valid.tobytes(),sources.tobytes())


@dataclass(frozen=True)
class CompactConfidenceContext:
    """Weighted message và bốn gate features đã dựng CPU, giữ A1 riêng."""
    base: CompactA1Context
    variant: str
    features: bytes

    @property
    def identity(self):
        _need(type(self.base) is CompactA1Context and self.variant in ('A2','A3') and type(self.features) is bytes,
              'Typed weighted compact context required')
        return hashlib.sha256((self.base.identity+self.variant).encode()+self.features).hexdigest()

    def arrays(self):
        _need(type(self.base) is CompactA1Context, 'Typed compact base required')
        message,active,target,valid=self.base.arrays()
        _need(self.variant in ('A2','A3') and type(self.features) is bytes
              and len(self.features)==int(np.prod(self.base.shape))*16,
              'Weighted compact feature geometry mismatch')
        features=np.frombuffer(self.features,dtype='<f4').reshape((*self.base.shape,4))
        _need(np.isfinite(features).all() and ((features>=0)&(features<=1)).all()
              and np.all(features[~active]==0), 'Invalid compact gate features')
        return message,active,target,valid,features

    def assert_for(self,batch,condition_sha256):
        self.base.assert_for(batch,condition_sha256)
        message,active,_,_,features=self.arrays()
        return message,active,features


def build_compact_confidence_context(windows,phase):
    _need(type(phase) is JunyiGraphPhaseSession and type(windows) is tuple and windows
          and phase.condition.variant in ('A2','A3'), 'Weighted Junyi phase and windows required')
    phase._light_check()
    vocabulary=phase.condition.encoding.native.vocabulary.values
    indices={name:index for index,name in enumerate(vocabulary)}
    parents=tuple(tuple((indices.get(parent),phase._weights_by_edge[(parent,child)])
                        for parent in phase._parents_by_child.get(child,())) for child in vocabulary)
    for window in windows:
        _validate_window(window,phase)
    shape=(len(windows),max(len(window.inputs.item_ids) for window in windows))
    messages=np.zeros(shape,dtype='<f4')
    active=np.zeros(shape,dtype=np.bool_)
    target=np.zeros(shape,dtype=np.bool_)
    valid=np.zeros(shape,dtype=np.bool_)
    sources=np.full(shape,-1,dtype='<i8')
    features=np.zeros((*shape,4),dtype='<f4')
    for row,window in enumerate(windows):
        counts,successes={},{}
        ids=window.inputs.item_ids
        for local,item_id in enumerate(ids):
            if local:
                previous=int(ids[local-1])
                counts[previous]=counts.get(previous,0)+1
                successes[previous]=successes.get(previous,0)+int(window.inputs.prior_responses[local])
            if not window.target_mask[local]:
                continue
            declared=parents[int(item_id)]
            observed=tuple((parent,weight) for parent,weight in declared if counts.get(parent,0)>0)
            mass=sum(weight for _,weight in observed)
            if mass<=0:
                continue
            messages[row,local]=sum(weight*(successes[parent]/counts[parent]-.5)
                                    for parent,weight in observed)/max(1.,mass)
            support=sum(counts[parent] for parent,_ in observed)
            mean=sum(weight for _,weight in declared)/len(declared)
            variance=sum((weight-mean)**2 for _,weight in declared)/len(declared)
            features[row,local]=(support/(1.+support),mean,variance,len(observed)/len(declared))
            active[row,local]=True
        size=len(ids)
        target[row,:size]=window.target_mask
        valid[row,:size]=True
        sources[row,:size]=window.inputs.source_rows
    phase._light_check()
    base=CompactA1Context(shape,tuple(window.window_id for window in windows),phase._condition_identity,
        phase._encoding_identity,phase.view.identity,messages.tobytes(),active.tobytes(),target.tobytes(),
        valid.tobytes(),sources.tobytes())
    return CompactConfidenceContext(base,phase.condition.variant,features.tobytes())
