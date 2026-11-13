"""Adapter A1 Junyi, tái dùng nguyên ResearchGraphNative và AKTAdapter.step.

Phase session chỉ cấp evidence quá khứ của native window. Producer chịu trách
nhiệm grant, source/runtime Gate, checkpoint và lựa epoch của mỗi lượt chạy.
"""
from collections.abc import Sequence
from dataclasses import dataclass
import hashlib

import numpy as np
import torch

from .config import AKTConfig, PROJECT_ROOT, ResearchCUDAExecutionProfile, validate_config
from .model import AKTAdapter
from .research_graph_model import (ResearchGraphNative, _batch_sha, _config_sha,
    _cuda_execution_check, _cuda_profile_sha, _evidence_sha, source_inventory)
from .research_junyi_data import JunyiResearchEncoding
from .research_junyi_graph import JunyiGraphCondition, JunyiGraphPhaseSession
from .research_junyi_compact import (CompactA1Context, CompactConfidenceContext,
    build_compact_context, build_compact_confidence_context)
from .research_junyi_graph_cache import GraphContextCache
from .tensors import AKTBatch, collate_windows
from .types import TrainingWindow, WindowInputs


def _need(value, message):
    if not value:
        raise ValueError(message)


def _source_inventory():
    paths = ('src/knowledge_tracing/akt/research_junyi_graph_model.py',
             'src/knowledge_tracing/akt/research_junyi_graph.py',
             'src/knowledge_tracing/akt/research_junyi_data.py',
             'src/knowledge_tracing/akt/research_junyi_graph_cache.py')
    return (*source_inventory(),*((name,hashlib.sha256((PROJECT_ROOT/name).read_bytes()).hexdigest())
                                  for name in paths))


@dataclass(frozen=True)
class _TrainingTicket:
    batch: AKTBatch
    batch_sha256: str
    evidence: tuple | CompactA1Context | CompactConfidenceContext
    evidence_sha256: str
    phase_identity: str
    graph_enabled: bool


class JunyiGraphAKTAdapter:
    """Một backbone cùng alpha A1, phase train80/selection và graph-off rõ ràng."""

    def __init__(self, *, config: AKTConfig, encoding: JunyiResearchEncoding,
                 condition: JunyiGraphCondition, phase: JunyiGraphPhaseSession,
                 cuda_profile: ResearchCUDAExecutionProfile | None = None,
                 graph_enabled: bool = True, compact_context: bool = False,
                 context_cache: GraphContextCache | None = None):
        _need(type(config) is AKTConfig and config.phase=='junyi-research',
              'Explicit Junyi research config required')
        validate_config(config,cuda_profile=cuda_profile)
        _need(type(encoding) is JunyiResearchEncoding and type(condition) is JunyiGraphCondition,
              'Typed Junyi encoding and graph condition required')
        _need(type(graph_enabled) is bool and condition.variant in ('A1','A2','A3'),
              'A1/A2/A3 condition and explicit Boolean graph control required')
        _need(type(compact_context) is bool, 'Boolean compact context control required')
        self._compact_context = compact_context
        self._context_backend = compact_context
        _need(config.source_root==PROJECT_ROOT/'artifacts/akt/dependencies/upstream'
              and torch.get_default_dtype()==torch.float32, 'Pinned FP32 native construction required')
        condition.assert_integrity()
        _need(encoding is condition.encoding and encoding.identity==condition.encoding.identity,
              'Condition must own the exact adapter encoding')
        self.config = config
        self.cuda_profile = cuda_profile
        self.research_encoding = encoding
        self.encoding = encoding.native
        self.condition = condition
        self._condition_sha = condition.identity
        self._encoding_sha = encoding.identity
        self._config_sha = _config_sha(config)
        self._profile_sha = _cuda_profile_sha(cuda_profile)
        self._device = torch.device('cpu' if cuda_profile is None else cuda_profile.device)
        self._sources = _source_inventory()
        self._ticket = None
        self._optimizer = None
        self._failed = False
        self._graph_enabled = graph_enabled
        self.set_phase(phase, context_cache=context_cache)
        # Không gọi AKTAdapter.__init__: native sau đây tạo đúng một backbone.
        self.native = ResearchGraphNative(config=config,n_items=len(self.encoding.vocabulary.values),
                                         condition=condition,cuda_profile=cuda_profile)
        self._parameters = tuple(self.native.parameters())
        self.audit_context_boundary()

    @property
    def graph_enabled(self):
        return self._graph_enabled

    def set_graph_enabled(self, enabled: bool):
        self._integrity()
        _need(type(enabled) is bool and self._ticket is None,
              'Boolean graph control requires no pending training batch')
        self._graph_enabled = enabled

    def set_phase(self, phase: JunyiGraphPhaseSession, *, context_cache=None):
        _need(self._ticket is None and not self._failed, 'Consume pending batch before changing phase')
        _need(type(phase) is JunyiGraphPhaseSession, 'Typed Junyi graph phase session required')
        phase.assert_boundary()
        _need(phase.condition is self.condition and phase.condition.identity==self._condition_sha
              and phase.condition.encoding.identity==self._encoding_sha,
              'Phase condition/encoding mismatch')
        _need(phase.view.scope in ('select_train80','raw_selection10'),
              'A1 Junyi adapter currently supports train80 and selection only')
        _need(phase.condition.encoding.native.vocabulary.values==self.encoding.vocabulary.values,
              'Phase/native vocabulary mismatch')
        _need(context_cache is None or (type(context_cache) is GraphContextCache and self._compact_context),
              'Typed graph cache requires compact context')
        _need(context_cache is None or self.condition.variant=='A1', 'Disk graph cache currently requires A1')
        if context_cache is not None:
            context_cache.assert_for(phase)
        self._context_cache = context_cache
        self._cache_identity = None if context_cache is None else context_cache.identity
        self.phase = phase
        self._phase_identity = phase.view.identity

    def _integrity(self):
        _need(not self._failed, 'Failed Junyi graph adapter cannot be reused')
        _need(_config_sha(self.config)==self._config_sha
              and _cuda_profile_sha(self.cuda_profile)==self._profile_sha, 'Junyi model config/profile changed')
        _need(type(self._graph_enabled) is bool, 'Boolean graph control required')
        _need(type(self._compact_context) is bool and self._compact_context==self._context_backend,
              'Junyi context backend changed')
        # Session kiểm header frozen và hash support nhỏ; full role audit ở boundary.
        self.phase._light_check()
        if self._context_cache is not None:
            _need(type(self._context_cache) is GraphContextCache
                  and self._context_cache.identity == self._cache_identity, 'Graph cache binding changed')
            self._context_cache.assert_for(self.phase)
        else:
            _need(self._cache_identity is None, 'Graph cache binding removed')
        _need(self.phase.view.identity==self._phase_identity
              and self.phase.condition.content_sha256==self._condition_sha
              and self.research_encoding.identity==self._encoding_sha,
              'Junyi model phase/condition/encoding changed')
        _need(self.encoding is self.research_encoding.native
              and self.condition is self.phase.condition, 'Owned encoding and condition required')
        if hasattr(self,'native'):
            _need(self.native.condition_sha256==self._condition_sha and self.native.variant==self.condition.variant
                  and self.native.cuda_profile is self.cuda_profile and self.native._device==self._device,
                  'Native Junyi graph binding changed')
            _need(tuple(id(p) for p in self.native.parameters())==tuple(id(p) for p in self._parameters),
                  'Registered Junyi parameters changed')

    def audit_context_boundary(self):
        self._integrity()
        self.phase.assert_boundary()
        self.research_encoding.assert_for(self.phase.view)
        _need(_source_inventory()==self._sources, 'Junyi graph model source changed')
        return self.recovery_signature()

    def recovery_signature(self):
        """Danh tính graph/collator nhẹ để kiểm tại mỗi batch boundary."""
        self._integrity()
        return dict(condition_sha256=self._condition_sha,encoding_sha256=self._encoding_sha,
                    phase_sha256=self._phase_identity,graph_enabled=self._graph_enabled,
                    context_backend='compact-'+self.condition.variant.lower()+'-v1' if self._compact_context else 'reference',
                    graph_context_cache=self._cache_identity)

    def _collate(self, windows, targets=None):
        _need(1<=len(windows)<=self.config.batch_size
              and all(type(window) is WindowInputs for window in windows), 'Bounded typed windows required')
        _need(len({window.window_id for window in windows})==len(windows), 'Duplicate native window IDs')
        if self._context_cache is not None:
            evidence=self._context_cache.batch(tuple(windows),self.phase)
        elif self._compact_context:
            builder=build_compact_context if self.condition.variant=='A1' else build_compact_confidence_context
            evidence=builder(tuple(windows),self.phase)
        else:
            evidence=tuple(self.phase.prefix_evidence(window) for window in windows)
        batch = collate_windows(windows,n_items=len(self.encoding.vocabulary.values),
                                device=self._device,targets=targets)
        return batch,evidence

    def collate_training(self, entries: Sequence[TrainingWindow]) -> AKTBatch:
        self._integrity()
        _need(self._ticket is None and self.phase.view.scope=='select_train80',
              'Fresh train80 phase required for optimizer batches')
        _need(all(type(entry) is TrainingWindow for entry in entries), 'Typed training windows required')
        batch,evidence = self._collate(tuple(entry.window for entry in entries),[entry.targets for entry in entries])
        self._ticket = _TrainingTicket(batch,_batch_sha(batch,device=self._device),evidence,
            _evidence_sha(evidence),self._phase_identity,self._graph_enabled)
        return batch

    def step(self, batch: AKTBatch, optimizer: torch.optim.Optimizer) -> dict:
        self._integrity()
        ticket,self._ticket = self._ticket,None
        _need(ticket is not None and batch is ticket.batch
              and ticket.batch_sha256==_batch_sha(batch,device=self._device)
              and ticket.phase_identity==self._phase_identity
              and ticket.graph_enabled==self._graph_enabled
              and ticket.evidence_sha256==_evidence_sha(ticket.evidence),
              'Fresh unchanged training batch and evidence required')
        _need(type(optimizer) is torch.optim.Adam, 'Explicit Adam optimizer required')
        owned = tuple(p for group in optimizer.param_groups for p in group['params'])
        _need(len(owned)==len(self._parameters) and len({id(p) for p in owned})==len(owned)
              and {id(p) for p in owned}=={id(p) for p in self._parameters},
              'Adam must own every Junyi parameter exactly once, including alpha')
        _need(self._optimizer is None or self._optimizer is optimizer, 'Same owned Adam required')
        for group in optimizer.param_groups:
            _need(all(group[name]==getattr(self.config,name) for name in ('lr','betas','eps','weight_decay')),
                  'Adam configuration changed')
            _need(all(group.get(name,False) is False for name in
                ('maximize','capturable','differentiable','amsgrad','decoupled_weight_decay'))
                and all(group.get(name) in (None,False) for name in ('foreach','fused')), 'Unsupported Adam behavior')
            if self.cuda_profile is not None:
                _need(group.get('foreach') is False and group.get('fused') is False,
                      'CUDA Adam requires explicit foreach=False and fused=False')
        _need(self.native.training, 'Training mode required')
        self._optimizer = optimizer
        try:
            self.native.bind(batch,ticket.evidence,enabled=self._graph_enabled,
                             expected_evidence_sha256=ticket.evidence_sha256)
            with torch.device('cpu'):
                result = AKTAdapter.step(self,batch,optimizer)
            self._integrity()
            if self.cuda_profile is not None:
                _cuda_execution_check(self.cuda_profile,synchronize=True)
            return result
        except BaseException:
            self._failed = True
            raise
        finally:
            self.native.clear_context()

    def predict_window(self, window: WindowInputs) -> np.ndarray:
        return self.predict_windows([window])[0]

    def predict_windows(self, windows: Sequence[WindowInputs]) -> list[np.ndarray]:
        self._integrity()
        _need(self._ticket is None, 'Prediction cannot skip pending training batch')
        modes = tuple((module,module.training) for module in self.native.modules())
        output = []
        try:
            self.native.eval()
            devices = [] if self.cuda_profile is None else [0]
            with torch.random.fork_rng(devices=devices),torch.inference_mode():
                for start in range(0,len(windows),self.config.batch_size):
                    group = tuple(windows[start:start+self.config.batch_size])
                    batch,evidence = self._collate(group)
                    digest = _evidence_sha(evidence)
                    self.native.bind(batch,evidence,enabled=self._graph_enabled,expected_evidence_sha256=digest)
                    _,probabilities,_ = self.native(batch.q_data,batch.qa_data,batch.loss_targets)
                    _need(_evidence_sha(evidence)==digest, 'Prediction graph evidence changed')
                    values = probabilities.reshape(batch.q_data.shape).cpu().numpy().astype(np.float64)
                    _need(np.isfinite(values).all() and ((values>=0)&(values<=1)).all(),
                          'Invalid Junyi graph probabilities')
                    output.extend(values[row,:len(window.inputs.item_ids)].copy() for row,window in enumerate(group))
            self._integrity()
            if self.cuda_profile is not None:
                _cuda_execution_check(self.cuda_profile,synchronize=True)
            return output
        finally:
            self.native.clear_context()
            for module,mode in modes:
                module.training = mode
