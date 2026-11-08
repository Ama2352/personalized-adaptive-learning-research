"""GKT recurrent engineering candidate; KHÔNG final baseline hoặc author parity.

Recipe explicit được review: unary DKVMN specialization M_old=v=m,w=1,
literal Cho2014 reset-before bias-free, zero h0, normnone/dropout0 fixture.
Nguồn và deviations: reports/gkt_recurrence_specification_20261108.md.
Không trainer, fitted adapter, learned graph, dataset IO hoặc calibration.
"""
from dataclasses import asdict, dataclass
import hashlib
import json

import torch
from torch import nn

from .config import GKTBinding, GKTKernelConfig
from .core import StaticGKTKernel, adjacency_sha256

RECIPE_ID='gkt_static_recurrent_convention_v1'
EVIDENCE_ROLE='gkt_recurrent_engineering_convention_unfitted'
GRU_VARIANT='cho2014_reset_before_bias_free'


def _floating(value, shape, reference):
    if (not isinstance(value,torch.Tensor) or tuple(value.shape)!=tuple(shape)
            or value.device.type!='cpu' or value.dtype!=reference.dtype
            or not torch.isfinite(value).all()):
        raise ValueError('finite CPU tensor with bound dtype and exact shape required')


@dataclass(frozen=True)
class GKTRecurrentState:
    values: torch.Tensor
    history_counts: torch.Tensor
    binding: GKTBinding
    graph_sha256: str
    recipe_sha256: str


@dataclass(frozen=True)
class GKTRecurrentReadout:
    logits: torch.Tensor
    probabilities: torch.Tensor
    history_counts: torch.Tensor
    evidence_role: str=EVIDENCE_ROLE


@dataclass(frozen=True)
class GKTRecurrentSequence:
    logits: torch.Tensor
    probabilities: torch.Tensor
    valid_mask: torch.Tensor
    history_counts: torch.Tensor
    final_state: GKTRecurrentState
    evidence_role: str=EVIDENCE_ROLE


class ChoResetBeforeGRU(nn.Module):
    """Literal Cho2014 Eq5–8; reset BEFORE hidden matrix, không PyTorch reset-after."""
    def __init__(self,width,*,dtype):
        super().__init__()
        for name in ('W_r','U_r','W_z','U_z','W_n','U_n'):
            setattr(self,name,nn.Linear(width,width,bias=False,device='cpu',dtype=dtype))

    def forward(self,inputs,previous):
        r=torch.sigmoid(self.W_r(inputs)+self.U_r(previous))
        z=torch.sigmoid(self.W_z(inputs)+self.U_z(previous))
        candidate=torch.tanh(self.W_n(inputs)+self.U_n(r*previous))
        return z*previous+(1-z)*candidate


class GKTStaticRecurrentCandidate(nn.Module):
    """Registered network cho một recipe engineering, parameters chưa fit.

    State do caller giữ; binding không chứng nhận graph/vocab train-only hoặc
    fitted weights. Normalization/dropout policy này KHÔNG journal-BN parity.
    """
    def __init__(self,config:GKTKernelConfig,binding:GKTBinding,adjacency:torch.Tensor,*,
                 recipe_id,mlp_hidden_dim,normalization,dropout,initial_state_policy,gru_variant):
        super().__init__()
        if not isinstance(config,GKTKernelConfig) or not isinstance(binding,GKTBinding):
            raise ValueError('typed config and binding required')
        if (recipe_id!=RECIPE_ID or normalization!='none' or initial_state_policy!='zeros'
                or gru_variant!=GRU_VARIANT or type(dropout) not in (int,float) or dropout!=0):
            raise ValueError('explicit approved engineering recipe required; no scientific defaults')
        if type(mlp_hidden_dim) is not int or mlp_hidden_dim<=0 or config.message_dim!=config.state_dim:
            raise ValueError('positive MLP width and message_dim=state_dim required')
        # Existing fixed kernel validates graph before detach/copy; no learned graph.
        # Dense validation in the frozen kernel uses ambient factory defaults.
        with torch.device('cpu'):
            self._kernel=StaticGKTKernel(config,binding,adjacency)
        self.register_buffer('adjacency',adjacency.detach().clone())
        self.config=config;self.binding=binding;self.graph_sha256=self._kernel.adjacency_sha256
        self.recipe_id=recipe_id;self.mlp_hidden_dim=mlp_hidden_dim
        self.normalization=normalization;self.dropout=float(dropout)
        self.initial_state_policy=initial_state_policy;self.gru_variant=gru_variant
        self._dtype=adjacency.dtype
        n,h,e=config.num_nodes,config.state_dim,config.embedding_dim
        self.concept_embedding=nn.Embedding(n,e,device='cpu',dtype=self._dtype)
        self.interaction_embedding=nn.Embedding(2*n,e,device='cpu',dtype=self._dtype)
        def mlp(input_width):
            return nn.Sequential(nn.Linear(input_width,mlp_hidden_dim,device='cpu',dtype=self._dtype),nn.ELU(),
                                 nn.Linear(mlp_hidden_dim,h,device='cpu',dtype=self._dtype),nn.ELU())
        self.self_mlp=mlp(h+e);self.out_mlp=mlp(2*(h+e));self.in_mlp=mlp(2*(h+e))
        self.erase=nn.Linear(h,h,device='cpu',dtype=self._dtype)
        self.add=nn.Linear(h,h,device='cpu',dtype=self._dtype)
        self.gru=ChoResetBeforeGRU(h,dtype=self._dtype)
        self.readout_weight=nn.Parameter(torch.empty(h,device='cpu',dtype=self._dtype))
        self.node_bias=nn.Parameter(torch.zeros(n,device='cpu',dtype=self._dtype))
        nn.init.normal_(self.readout_weight,std=h**-.5)
        self.recipe_sha256=self._recipe_digest()

    def _recipe_digest(self):
        descriptor={'recipe_id':self.recipe_id,'config':asdict(self.config),'dtype':str(self._dtype),
                    'mlp_hidden_dim':self.mlp_hidden_dim,'normalization':self.normalization,
                    'dropout':self.dropout,'initial_state_policy':self.initial_state_policy,'gru_variant':self.gru_variant}
        return hashlib.sha256(json.dumps(descriptor,sort_keys=True,separators=(',',':')).encode()).hexdigest()

    def _bound(self,binding,graph_sha256):
        if (binding!=self.binding or graph_sha256!=self.graph_sha256
                or self._recipe_digest()!=self.recipe_sha256):
            raise ValueError('domain/vocabulary/node order/graph/recipe binding mismatch')
        if (self.adjacency.device.type!='cpu' or self.adjacency.dtype!=self._dtype
                or adjacency_sha256(self.adjacency)!=self.graph_sha256):
            raise ValueError('registered fixed adjacency changed')
        self._kernel._bound(binding,graph_sha256)
        if any(p.device.type!='cpu' or p.dtype!=self._dtype or not torch.isfinite(p).all() for p in self.parameters()):
            raise ValueError('finite CPU parameters with bound dtype required')

    def _state(self,state,binding,graph_sha256):
        self._bound(binding,graph_sha256)
        if (not isinstance(state,GKTRecurrentState) or state.binding!=self.binding
                or state.graph_sha256!=self.graph_sha256 or state.recipe_sha256!=self.recipe_sha256):
            raise ValueError('state domain/node/graph/recipe binding mismatch')
        if not isinstance(state.values,torch.Tensor) or state.values.ndim!=3 or state.values.shape[0]<=0:
            raise ValueError('nonempty [batch,node,state] state required')
        batch=state.values.shape[0]
        _floating(state.values,(batch,self.config.num_nodes,self.config.state_dim),self.adjacency)
        counts=state.history_counts
        if (not isinstance(counts,torch.Tensor) or counts.device.type!='cpu' or counts.dtype!=torch.long
                or counts.shape!=(batch,) or torch.any(counts<0)):
            raise ValueError('nonnegative CPU history counts required')
        return batch

    @staticmethod
    def _integer_ids(value,shape):
        if not isinstance(value,torch.Tensor) or value.shape!=shape or value.device.type!='cpu' or value.dtype!=torch.long:
            raise ValueError('CPU integer IDs/responses with exact shape required')

    def initial_state(self,batch_size,*,binding,graph_sha256):
        self._bound(binding,graph_sha256)
        if type(batch_size) is not int or batch_size<=0:raise ValueError('positive batch size required')
        return GKTRecurrentState(torch.zeros((batch_size,self.config.num_nodes,self.config.state_dim),device='cpu',dtype=self._dtype),
             torch.zeros(batch_size,device='cpu',dtype=torch.long),self.binding,self.graph_sha256,self.recipe_sha256)

    def predict(self,state,query_ids,*,binding,graph_sha256):
        batch=self._state(state,binding,graph_sha256)
        self._integer_ids(query_ids,(batch,))
        # Existing kernel creates arange; force CPU even if caller changed default device.
        with torch.device('cpu'):
            result=self._kernel.readout(state.values,query_ids,self.readout_weight,self.node_bias,
                                        binding=binding,graph_sha256=graph_sha256)
        return GKTRecurrentReadout(result.logits,result.probabilities,state.history_counts.clone())

    def erase_add(self,messages):
        """DKVMN specialization M_old=v=m,w=1: repo convention, NOT author mapping."""
        return messages*(1-torch.sigmoid(self.erase(messages)))+torch.tanh(self.add(messages))

    def observe(self,state,answered_ids,responses,event_valid_mask,*,binding,graph_sha256):
        batch=self._state(state,binding,graph_sha256)
        self._integer_ids(answered_ids,(batch,));self._integer_ids(responses,(batch,))
        valid=event_valid_mask
        if not isinstance(valid,torch.Tensor) or valid.device.type!='cpu' or valid.dtype!=torch.bool or valid.shape!=(batch,):
            raise ValueError('explicit CPU boolean event mask required')
        if (torch.any((answered_ids[valid]<0)|(answered_ids[valid]>=self.config.num_nodes))
                or torch.any((responses[valid]!=0)&(responses[valid]!=1))):
            raise ValueError('active events require known node IDs and binary responses')
        if torch.any(state.history_counts[valid]==torch.iinfo(torch.long).max):
            raise ValueError('active history counter would overflow')
        ids=torch.where(valid,answered_ids,torch.zeros_like(answered_ids))
        answers=torch.where(valid,responses,torch.zeros_like(responses))
        with torch.device('cpu'):
            z=self._kernel.aggregate_after_observation(state.values,ids,answers,self.concept_embedding.weight,
                    self.interaction_embedding.weight,binding=binding,graph_sha256=graph_sha256)
            observed=z[torch.arange(batch,device='cpu'),ids]
            pairs=torch.cat((observed[:,None,:].expand(-1,self.config.num_nodes,-1),z),dim=-1)
            messages=self._kernel.combine_messages(ids,self.self_mlp(observed),self.out_mlp(pairs),self.in_mlp(pairs),
                                                   binding=binding,graph_sha256=graph_sha256)
        proposed=self.gru(self.erase_add(messages.values),state.values)
        _floating(proposed,state.values.shape,self.adjacency)
        support=messages.support_mask & valid[:,None]
        values=torch.where(support[...,None],proposed,state.values)
        return GKTRecurrentState(values,state.history_counts+valid.long(),self.binding,self.graph_sha256,self.recipe_sha256)

    def sequence(self,query_ids,responses,valid_mask,*,initial_state,binding,graph_sha256):
        self._bound(binding,graph_sha256)
        if not isinstance(query_ids,torch.Tensor) or query_ids.ndim!=2 or query_ids.shape[0]<=0:
            raise ValueError('nonempty batch [batch,time] required')
        self._integer_ids(query_ids,query_ids.shape);self._integer_ids(responses,query_ids.shape)
        if (not isinstance(valid_mask,torch.Tensor) or valid_mask.device.type!='cpu' or valid_mask.dtype!=torch.bool
                or valid_mask.shape!=query_ids.shape):raise ValueError('explicit CPU boolean sequence mask required')
        batch,steps=query_ids.shape
        state=self.initial_state(batch,binding=binding,graph_sha256=graph_sha256) if initial_state is None else initial_state
        if self._state(state,binding,graph_sha256)!=batch:raise ValueError('state batch mismatch')
        logits=[];probabilities=[];counts=[]
        for time in range(steps):
            valid=valid_mask[:,time]
            ids=torch.where(valid,query_ids[:,time],torch.zeros_like(query_ids[:,time]))
            readout=self.predict(state,ids,binding=binding,graph_sha256=graph_sha256)
            logits.append(torch.where(valid,readout.logits,torch.zeros_like(readout.logits)))
            probabilities.append(torch.where(valid,readout.probabilities,torch.zeros_like(readout.probabilities)))
            counts.append(readout.history_counts)
            state=self.observe(state,query_ids[:,time],responses[:,time],valid,binding=binding,graph_sha256=graph_sha256)
        empty=torch.zeros((batch,0),device='cpu',dtype=self._dtype)
        return GKTRecurrentSequence(torch.stack(logits,1) if steps else empty,
                torch.stack(probabilities,1) if steps else empty.clone(),valid_mask.clone(),
                torch.stack(counts,1) if steps else torch.zeros((batch,0),device='cpu',dtype=torch.long),state)

    def forward(self,query_ids,responses,valid_mask,*,initial_state,binding,graph_sha256):
        return self.sequence(query_ids,responses,valid_mask,initial_state=initial_state,binding=binding,graph_sha256=graph_sha256)
