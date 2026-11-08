"""A0/A1 toy forward/backward, không adoption CG-AKT hoặc fitted trainer.

Pinned NonRasch submodule bridge, không hook/patch/inverse-sigmoid/detach loss.
Dataclass/SHA binding là consistency in-process, không cryptographic attestation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import wraps
import hashlib
from pathlib import Path

import numpy as np
import torch
from torch import nn

from knowledge_tracing.graph_augmentation import PreparedGraphContext, apply_graph_residual, prepare_graph_context
from knowledge_tracing.graph_context import EdgeConfidence
from knowledge_tracing.shared_kt import PrerequisiteGraph
from knowledge_tracing.simulator_bridge import identity_hash
from .config import AKTConfig, PROJECT_ROOT, validate_config
from .model import AKTAdapter
from .online import inference_recipe
from .simulator_data import SimulatorEncoding, SimulatorShard, SimulatorUnseenQuery, iter_simulator_windows
from .tensors import AKTBatch, collate_windows

RECIPE = "engineering-observed-parent-mean-v1"


def _cpu(function):
    @wraps(function)
    def guarded(*args, **kwargs):
        if torch.cuda.is_available() or torch.cuda.is_initialized():
            raise RuntimeError("graph prototype requires CUDA hidden/unavailable and uninitialized")
        config = kwargs.get("config") or (getattr(args[0],"config",None) if args else None)
        previous_threads = torch.get_num_threads()
        with torch.device("cpu"):
            try:
                if type(config) is AKTConfig and type(config.threads) is int and 1 <= config.threads <= 2:
                    torch.set_num_threads(config.threads)
                return function(*args, **kwargs)
            finally:
                torch.set_num_threads(previous_threads)
    return guarded


@dataclass(frozen=True)
class GraphPrototypeSpec:
    variant: str
    feature_recipe: str
    approval_reference: str
    history_scope: str
    weight_role: str = "engineering_only"

    def __post_init__(self):
        if self.variant not in {"A0", "A1"} or self.feature_recipe != RECIPE:
            raise ValueError("only explicit A0/A1 parent-mean engineering recipe; A2/A3 not implemented")
        if self.history_scope != "effective_window" or self.weight_role != "engineering_only":
            raise ValueError("matched-window engineering scope only")
        if not isinstance(self.approval_reference, str) or not self.approval_reference.strip():
            raise ValueError("explicit prototype approval reference required")


@dataclass(frozen=True)
class QueryEvidence:
    learner_id: str
    source_row: int
    global_rank: int
    window_id: str
    evidence: PreparedGraphContext


@dataclass(frozen=True)
class GraphAKTBatch:
    base: AKTBatch
    contexts: tuple[tuple[QueryEvidence | None, ...], ...]
    model_binding: str
    window_ids: tuple[str, ...]
    payload_sha256: str
    unseen_targets: tuple[tuple[str, int, int], ...]
    source_identity_sha256: str


@dataclass(frozen=True)
class GraphForwardDetails:
    native_result: tuple
    base_probabilities: torch.Tensor
    applied_mask: torch.Tensor
    hidden: torch.Tensor | None
    base_logits: torch.Tensor | None
    augmented_logits: torch.Tensor | None


def _scope(config, shard, encoding, graph):
    if type(config) is not AKTConfig or type(shard) is not SimulatorShard or type(encoding) is not SimulatorEncoding:
        raise ValueError("exact config/observable shard/train encoding required")
    validate_config(config)
    if (config.phase != "smoke" or config.device != "cpu" or config.dropout != 0
            or config.context != 100 or config.target_block != 100 or config.max_length != 200
            or config.threads > 2 or config.recovery is not None):
        raise ValueError("CPU d32 dropout0 existing smoke geometry only")
    if config.source_root.resolve() != (PROJECT_ROOT/"artifacts/akt/dependencies/upstream").resolve():
        raise ValueError("trusted pinned upstream path only")
    if shard.role not in {"train", "selection"}:
        raise ValueError("no calibration/final/refit")
    shard.audit
    if (len(shard.trajectories) > 2 or shard.max_events_per_learner > 12
            or len(shard.bank.items) > 8 or len({i.concept_id for i in shard.bank.items}) > 4
            or not shard.bank.environment_id.startswith("synthetic-akt-graph-engineering-")):
        raise ValueError("tiny synthetic graph prototype domain/bounds required")
    if (type(graph) is not PrerequisiteGraph or graph != PrerequisiteGraph.from_edges(graph.nodes, graph.edges)
            or len(graph.nodes) > 4 or len(graph.edges) > 16
            or not set(graph.nodes) <= {i.concept_id for i in shard.bank.items}):
        raise ValueError("concept graph canonical/domain/bounds mismatch")
    # The actual existing adapter checks role/domain/train-only support and OOV.
    tuple(iter_simulator_windows(shard, encoding, context=config.context, target_block=config.target_block, training=False))


def _source_inventory(config):
    native = sorted(Path(__file__).parent.glob("*.py"))
    helpers = [Path(__file__).parent.parent/name for name in
               ("simulator_data.py","simulator_bridge.py","shared_kt.py","graph_context.py","graph_augmentation.py")]
    paths = native + helpers + [config.source_root/"akt.py"]
    return {p.relative_to(PROJECT_ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def _binding(config, bank, encoding, graph, sources):
    return identity_hash({"engineering_bank": bank.identity, "encoding": encoding.identity,
                          "graph": asdict(graph), "inference_recipe": inference_recipe(config),
                          "feature_recipe": RECIPE,"source_identity":identity_hash(sources)})


def _confidence(graph):
    return EdgeConfidence("fixed_uniform",tuple((p,c,1.) for p,c in graph.edges),
                          identity_hash({"kind":"declared_fixed_graph","graph":asdict(graph),"recipe":RECIPE}))


def _payload(base, contexts, windows, binding, unseen):
    tensors = {}
    for name in ("q_data", "qa_data", "loss_targets", "valid_mask", "target_mask"):
        value = getattr(base, name)
        if value.device.type != "cpu":
            raise ValueError("CPU tensors required")
        tensors[name] = {"dtype": str(value.dtype), "shape": list(value.shape),
                         "sha256": hashlib.sha256(value.detach().contiguous().numpy().tobytes()).hexdigest()}
    return identity_hash({"tensors": tensors, "source_rows": base.source_rows.tolist(),
                          "contexts": [[None if q is None else asdict(q) for q in row] for row in contexts],
                          "window_ids": windows, "model_binding": binding, "unseen": unseen})


@_cpu
def prepare_graph_batch(shard: SimulatorShard, encoding: SimulatorEncoding, *, config: AKTConfig,
                        graph: PrerequisiteGraph, window_ids: tuple[str, ...] | None = None) -> GraphAKTBatch:
    """Build only from role-bound full observable prefixes, never re-anchor slices.

Current/future outcomes may exist in a source trajectory; they are never passed
to the message module. Native qa uses existing causal collator/masking unchanged.
"""
    _scope(config, shard, encoding, graph)
    sources = _source_inventory(config)
    entries = tuple(iter_simulator_windows(shard, encoding, context=config.context, target_block=config.target_block, training=False))
    unseen = tuple((e.learner_id, e.query.source_row, e.global_rank) for e in entries if isinstance(e, SimulatorUnseenQuery))
    known = tuple(e for e in entries if not isinstance(e, SimulatorUnseenQuery))
    if window_ids is not None:
        if len(window_ids) != len(set(window_ids)) or not set(window_ids) <= {w.window_id for w in known}:
            raise ValueError("unknown/duplicate window IDs")
        lookup = {w.window_id: w for w in known}
        known = tuple(lookup[i] for i in window_ids)
    if not 1 <= len(known) <= min(4, config.batch_size):
        raise ValueError("select 1..batch_size known windows; OOV never rescued by graph")
    base = collate_windows(known, n_items=len(encoding.support), device="cpu")
    confidence = _confidence(graph)
    trajectories = {t.learner_id:t for t in shard.trajectories}
    contexts = []
    width = base.q_data.shape[1]
    for window in known:
        row = [None]*width
        learner = window.inputs.user_ids[0]
        trajectory = trajectories[learner]
        for local in np.flatnonzero(window.target_mask):
            rank = int(window.global_ranks[local])
            observation = trajectory.observations[rank]
            evidence = prepare_graph_context(bank=shard.bank,graph=graph,confidence=confidence,
                history=trajectory.observations[:rank],query=observation.query,
                trained_items=tuple(item for item,_ in encoding.support),context=config.context,target_block=config.target_block)
            if (observation.query.source_row != int(window.inputs.source_rows[local])
                    or evidence.effective_start != rank-int(window.history_used[local])):
                raise ValueError("global geometry/source-row mismatch")
            row[int(local)] = QueryEvidence(learner,observation.query.source_row,rank,window.window_id,evidence)
        contexts.append(tuple(row))
    contexts = tuple(contexts)
    windows = tuple(w.window_id for w in known)
    binding = _binding(config,shard.bank,encoding,graph,sources)
    if _source_inventory(config)!=sources:
        raise ValueError("source drift during graph batch preparation")
    return GraphAKTBatch(base,contexts,binding,windows,_payload(base,contexts,windows,binding,unseen),unseen,identity_hash(sources))


class GraphAKTPrototype(nn.Module):
    """Fresh native backbone + caller trainable one-feature A1 branch.

No checkpoint import, fit/step/train_epoch integration or selected-model certificate.
Source/metadata binding detects accidental drift, not a hostile in-process caller.
"""
    @_cpu
    def __init__(self, *, config: AKTConfig, train: SimulatorShard, encoding: SimulatorEncoding,
                 graph: PrerequisiteGraph, spec: GraphPrototypeSpec,
                 message_module: nn.Module | None, readout: nn.Parameter | None):
        super().__init__()
        _scope(config,train,encoding,graph)
        if train.role != "train" or type(spec) is not GraphPrototypeSpec:
            raise ValueError("fresh train-bound engineering prototype required")
        self.config,self.spec = config,spec
        self.sources = _source_inventory(config)
        self.source_identity_sha256 = identity_hash(self.sources)
        self.binding = _binding(config,train.bank,encoding,graph,self.sources)
        self.domain = identity_hash(train.bank.identity)
        self.vocabulary = identity_hash(sorted(item for item,_ in encoding.support))
        self.graph_sha256 = identity_hash(asdict(graph))
        self.confidence_sha256 = _confidence(graph).identity
        self.items = tuple(item for item,_ in encoding.support)
        self.recipe = inference_recipe(config)
        if spec.variant=="A0" and (message_module is not None or readout is not None):
            raise ValueError("A0 requires no message module/readout")
        self.message_module,self.readout = message_module,readout
        if spec.variant == "A1":
            if not isinstance(message_module,nn.Module) or not isinstance(readout,nn.Parameter) or readout.ndim != 1 or not 1 <= readout.numel() <= 32:
                raise ValueError("explicit trainable module + 1D readout width1..32 required")
            params = tuple(message_module.parameters())+(readout,)
            if not tuple(message_module.parameters()) or sum(p.numel() for p in params) > 4096:
                raise ValueError("tiny trainable caller module required")
            if any(isinstance(m,nn.Dropout) and m.p != 0 for m in message_module.modules()):
                raise ValueError("deterministic dropout0 prototype branch required")
            if tuple(message_module.buffers()):
                raise ValueError("stateless message module required; no running buffers")
            if any(p.device.type != "cpu" or p.dtype != torch.float32 or not p.requires_grad or not torch.isfinite(p).all() for p in params):
                raise ValueError("CPU FP32 finite trainable branch parameters required")
        self.native = AKTAdapter(config,encoding.exercise_encoding()).native
        if _source_inventory(config)!=self.sources:
            raise ValueError("source drift during graph prototype construction")

    def _validate(self,batch):
        if _source_inventory(self.config)!=self.sources:
            raise ValueError("graph prototype source drift")
        if (type(batch) is not GraphAKTBatch or batch.model_binding != self.binding
                or batch.source_identity_sha256!=self.source_identity_sha256 or inference_recipe(self.config) != self.recipe):
            raise ValueError("domain/vocab/graph/recipe batch binding mismatch")
        if _payload(batch.base,batch.contexts,batch.window_ids,batch.model_binding,batch.unseen_targets) != batch.payload_sha256:
            raise ValueError("graph batch tensor/identity payload drift")
        q=batch.base.q_data
        if (q.ndim != 2 or q.dtype != torch.long or batch.base.qa_data.shape != q.shape
                or len(batch.contexts) != q.shape[0] or any(len(row)!=q.shape[1] for row in batch.contexts)
                or any(p.device.type!="cpu" or p.dtype!=torch.float32 for p in self.native.parameters())):
            raise ValueError("native CPU batch geometry mismatch")
        n=self.native.n_question
        valid=batch.base.valid_mask
        if (torch.any(q[valid]<1) or torch.any(q[valid]>n) or torch.any(q[~valid]!=0)
                or torch.any((batch.base.qa_data[valid]-q[valid])%n!=0)
                or torch.any((batch.base.qa_data[valid]-q[valid])//n<0)
                or torch.any((batch.base.qa_data[valid]-q[valid])//n>1)):
            raise ValueError("item/qa IDs outside native encoding")
        for b,row in enumerate(batch.contexts):
            if len({query.learner_id for query in row if query is not None}) != 1:
                raise ValueError("one learner per graph window required")
            for local,query in enumerate(row):
                if bool(query is not None) != bool((batch.base.target_mask & valid)[b,local]):
                    raise ValueError("graph context must exactly cover target slots")
                if query is None:continue
                e=query.evidence
                if (e.binding.domain_sha256!=self.domain or e.binding.trained_items_sha256!=self.vocabulary
                        or e.graph_sha256!=self.graph_sha256 or e.confidence_sha256!=self.confidence_sha256
                        or e.query.source_row!=query.source_row or query.source_row!=int(batch.base.source_rows[b,local])
                        or e.query.item_id!=self.items[int(q[b,local])-1] or query.window_id!=batch.window_ids[b]
                        or not 0<=query.global_rank<12
                        or e.confidence_kind!="fixed_uniform" or not e.target_fitted
                        or any(p.confidence!=1 for p in e.parents)):
                    raise ValueError("A1 nonoracle fixed confidence/vocabulary scope mismatch")

    def _checked_result(self,result):
        if _source_inventory(self.config)!=self.sources:
            raise ValueError("graph prototype source drift during forward")
        return result

    def _features(self,q,qa):
        """Exactly pinned n_pid0/separate_qaFalse forward's six operations."""
        if self.native.n_pid!=0 or self.native.separate_qa:
            raise ValueError("only pinned NonRasch nonseparate-QA bridge")
        q_embedding=self.native.q_embed(q)
        responses=(qa-q)//self.native.n_question
        qa_embedding=self.native.qa_embed(responses)+q_embedding
        hidden=self.native.model(q_embedding,qa_embedding)
        concatenated=torch.cat([hidden,q_embedding],dim=-1)
        logits=self.native.out(concatenated).reshape(-1)
        return hidden,logits

    @_cpu
    def forward_details(self,batch:GraphAKTBatch,targets:torch.Tensor|None=None,*,enabled=True):
        self._validate(batch)
        if type(enabled) is not bool:raise ValueError("explicit boolean branch flag")
        q,qa=batch.base.q_data,batch.base.qa_data
        if targets is None:targets=torch.full(q.shape,-1.,dtype=torch.float32,device="cpu")
        mask=batch.base.target_mask & batch.base.valid_mask
        if (targets.device.type!="cpu" or targets.dtype!=torch.float32 or targets.shape!=q.shape
                or not torch.isin(targets,torch.tensor([-1.,0.,1.])).all()
                or torch.any((targets>=0)&~mask)):
            raise ValueError("loss labels/mask invalid; labels are not message features")
        active=[bool(query is not None and any(p.support>0 for p in query.evidence.parents))
                for row in batch.contexts for query in row]
        if self.spec.variant=="A0" or not enabled or not any(active):
            native_result=self.native(q,qa,targets)
            return self._checked_result(GraphForwardDetails(native_result,native_result[1],torch.zeros(q.numel(),dtype=torch.bool),None,None,None))
        hidden,z=self._features(q,qa)
        base_p=torch.sigmoid(z)
        augmented=[]
        for index,query in enumerate(query for row in batch.contexts for query in row):
            if not active[index]:
                augmented.append(z[index]);continue
            evidence=query.evidence
            features=z.new_tensor([[p.mean_observed_correctness if p.support else 0.] for p in evidence.parents])
            messages=self.message_module(features)
            result=apply_graph_residual(z[index],evidence=evidence,binding=evidence.binding,
                edge_messages=messages,readout=self.readout,gate=z.new_tensor(1.))
            augmented.append(result.logit)
        augmented=torch.stack(augmented)
        applied=torch.tensor(active,dtype=torch.bool,device="cpu")
        probabilities=torch.where(applied,torch.sigmoid(augmented),base_p)
        labels=targets.reshape(-1);loss_mask=labels>-.9
        loss=nn.BCEWithLogitsLoss(reduction="none")(augmented[loss_mask],labels[loss_mask].float()).sum()+0.
        return self._checked_result(GraphForwardDetails((loss,probabilities,loss_mask.sum()),base_p,applied,hidden,z,augmented))

    def forward(self,batch,targets=None,*,enabled=True):
        return self.forward_details(batch,targets,enabled=enabled).native_result
