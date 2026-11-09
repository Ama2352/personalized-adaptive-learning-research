"""Core CG-AKT recipe26 cho research; chưa trainer/checkpoint/fitted backend.

Context đã seal chỉ chứa observables quá khứ. TrainingWindow.targets chỉ đi vào
loss; caller vẫn phải cấp đúng truth sidecar của phase, đây không là attestation
nhãn/corpus. Ticket và source pins là consistency contract hợp tác, không sandbox
chống caller sửa private attributes. Không cấp quyền execution hoặc chọn model.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from knowledge_tracing.simulator_bridge import identity_hash
from .config import AKTConfig, ResearchCUDAExecutionProfile, validate_config
from .device_budget import cuda_budget_snapshot
from .model import AKTAdapter
from . import research_graph_condition as conditions
from . import research_graph_context as contexts
from . import research_simulator_data as data
from .tensors import AKTBatch, collate_windows
from .types import TrainingWindow, WindowInputs
from .upstream import build_native

ROOT = Path(__file__).resolve().parents[3]
RECIPE = conditions.RECIPE
SOURCE_PATHS = tuple(sorted((
    'src/knowledge_tracing/akt/research_graph_model.py',
    'src/knowledge_tracing/akt/research_graph_context.py',
    'src/knowledge_tracing/akt/research_graph_condition.py',
    'src/knowledge_tracing/akt/research_simulator_data.py',
    'src/knowledge_tracing/akt/model.py', 'src/knowledge_tracing/akt/config.py',
    'src/knowledge_tracing/akt/device_budget.py',
    'src/knowledge_tracing/akt/tensors.py', 'src/knowledge_tracing/akt/types.py',
    'src/knowledge_tracing/akt/upstream.py', 'src/knowledge_tracing/akt/provenance.py',
    'artifacts/akt/dependencies/upstream/akt.py',
    'artifacts/akt/dependencies/upstream/README.md',
    'artifacts/akt/dependencies/upstream/LICENSE',
)))


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def source_inventory():
    """Byte pins; constructor build_native còn xác minh Git upstream chuẩn."""
    rows = []
    alias = lambda p: p.is_symlink() or getattr(p, 'is_junction', lambda: False)()
    _need(ROOT.is_dir() and not alias(ROOT) and ROOT.resolve() == ROOT.absolute(), 'physical project root required')
    for relative in SOURCE_PATHS:
        path = ROOT
        for component in relative.split('/'):
            path /= component
            _need(not alias(path), 'model source alias rejected')
        _need(path.is_file() and path.stat().st_size <= 262144, 'bounded model source required')
        payload = path.read_bytes()
        _need(len(payload) <= 262144, 'model source byte cap')
        rows.append((relative, hashlib.sha256(payload).hexdigest()))
    return tuple(rows)


def _array_sha(value):
    value = np.ascontiguousarray(value)
    return identity_hash((str(value.dtype), tuple(value.shape), hashlib.sha256(value.tobytes()).hexdigest()))


def _config_sha(config):
    return identity_hash(json.loads(json.dumps(asdict(config), default=str, allow_nan=False)))


def _batch_sha(batch, *, device):
    _need(type(batch) is AKTBatch, 'exact AKTBatch required')
    rows = {}
    for name in ('q_data', 'qa_data', 'loss_targets', 'valid_mask', 'target_mask'):
        value = getattr(batch, name)
        _need(type(value) is torch.Tensor and value.device == device, 'plain batch tensors on the explicit execution device required')
        rows[name] = _array_sha(value.detach().cpu().contiguous().numpy())
    rows['source_rows'] = _array_sha(batch.source_rows)
    return identity_hash(rows)


def _cuda_profile_sha(profile):
    if profile is None:
        return None
    _need(type(profile) is ResearchCUDAExecutionProfile, 'exact CUDA profile required')
    profile.__post_init__()
    return identity_hash(asdict(profile))


def _cuda_execution_check(profile, *, synchronize=False):
    """Validate caller setup, never configure flags/fraction or reset peaks."""
    _need(profile is not None, 'explicit CUDA execution profile required')
    _cuda_profile_sha(profile)
    _need(torch.get_default_dtype() == torch.float32, 'CUDA execution requires FP32 default dtype')
    _need(os.environ.get('CUBLAS_WORKSPACE_CONFIG') == profile.cublas_workspace_config,
          'caller must configure the CUDA workspace before initialization')
    _need(torch.are_deterministic_algorithms_enabled() is True
          and torch.is_deterministic_algorithms_warn_only_enabled() is False
          and torch.backends.cuda.matmul.allow_tf32 is False
          and torch.backends.cudnn.allow_tf32 is False
          and torch.backends.cudnn.benchmark is False
          and torch.get_float32_matmul_precision() == 'highest', 'actual CUDA backend flags differ from recipe28')
    _need(torch.cuda.is_available() is True, 'CUDA cannot fall back to CPU')
    count, current = torch.cuda.device_count(), torch.cuda.current_device()
    _need(type(count) is int and count == 1 and type(current) is int and current == 0,
          'exactly one actual CUDA device0 required')
    total = torch.cuda.get_device_properties(0).total_memory
    fraction = torch.cuda.get_per_process_memory_fraction(0)
    _need(type(total) is int and total >= profile.max_vram_bytes
          and type(fraction) in (int, float) and math.isfinite(fraction)
          and abs(fraction - profile.max_vram_bytes/total) <= 1e-12,
          'caller CUDA allocator fraction differs from the explicit budget')
    if synchronize:
        torch.cuda.synchronize(0)
    return cuda_budget_snapshot(torch.cuda, max_vram_bytes=profile.max_vram_bytes)


def _evidence_sha(evidence):
    _need(type(evidence) is tuple and all(type(row) is tuple for row in evidence), 'immutable evidence rows required')
    return identity_hash(tuple(tuple(None if item is None else asdict(item) for item in row) for row in evidence))


def _features(audit):
    parents = audit.parents
    support = sum(p.support for p in parents if p.support > 0)
    n = len(parents)
    mean = sum(p.confidence for p in parents) / n if n else 0.
    variance = sum((p.confidence - mean)**2 for p in parents) / n if n else 0.
    fraction = sum(p.support > 0 for p in parents) / n if n else 0.
    return (support / (1. + support), mean, variance, fraction)


@dataclass(frozen=True)
class _Call:
    batch: AKTBatch
    payload_sha256: str
    evidence: tuple
    evidence_sha256: str
    enabled: bool


class ResearchGraphNative(nn.Module):
    """Đăng ký mọi parameter; giữ đúng sáu thao tác backbone upstream.

    Context được tiêu thụ trước forward, cả khi lỗi; không global/thread-local
    context, hook hay monkeypatch thuật toán upstream.
    """
    def __init__(self, *, config, n_items, condition, cuda_profile=None):
        super().__init__()
        validate_config(config, cuda_profile=cuda_profile)
        self.cuda_profile = cuda_profile
        self._cuda_profile_sha = _cuda_profile_sha(cuda_profile)
        self._device = torch.device('cpu' if cuda_profile is None else cuda_profile.device)
        if cuda_profile is not None:
            _cuda_execution_check(cuda_profile)
        self.variant = condition.variant
        self.condition_sha256 = condition.identity
        self._recipe_identity = (self.variant, self.condition_sha256)
        # Branch construction must not consume a second backbone RNG stream.
        with torch.device('cpu'):
            self.backbone = build_native(config, n_items=n_items)
            if self.variant != 'A0':
                self.alpha = nn.Parameter(torch.zeros((), dtype=torch.float32, device='cpu'))
            else:
                self.register_parameter('alpha', None)
            if self.variant == 'A3':
                with torch.random.fork_rng(devices=[]):
                    self.gate = nn.Linear(4, 1, device='cpu', dtype=torch.float32)
                    nn.init.zeros_(self.gate.weight); nn.init.zeros_(self.gate.bias)
            else:
                self.gate = None
        if cuda_profile is not None:
            self.to(self._device)
            _need(all(p.device == self._device and p.dtype == torch.float32 for p in self.parameters()),
                  'CUDA wrapper placement must finish before parameter ownership is cached')
            _cuda_execution_check(cuda_profile, synchronize=True)
        self._call = None
        self._parameter_ids = tuple(id(p) for p in self.parameters())

    def bind(self, batch, evidence, *, enabled, expected_evidence_sha256=None):
        _need(self._call is None and type(enabled) is bool, 'one outstanding native context only')
        _need((self.variant, self.condition_sha256) == self._recipe_identity, 'native variant/condition drift')
        _need(_cuda_profile_sha(self.cuda_profile) == self._cuda_profile_sha, 'native CUDA execution profile drift')
        _need(len(evidence) == batch.q_data.shape[0], 'context/batch row mismatch')
        _need(all(len(row) <= batch.q_data.shape[1] for row in evidence), 'context/batch length mismatch')
        for row, items in enumerate(evidence):
            for local, item in enumerate(items):
                if item is not None:
                    _need(bool(batch.target_mask[row, local]) and bool(batch.valid_mask[row, local]), 'context outside target mask')
                    _need(item.local_position == local and item.source_row == int(batch.source_rows[row, local]), 'context target identity mismatch')
        digest = _evidence_sha(evidence)
        _need(expected_evidence_sha256 is None or digest == expected_evidence_sha256,
              'expected native evidence drift')
        self._call = _Call(batch, _batch_sha(batch, device=self._device), evidence, digest, enabled)

    def clear_context(self):
        self._call = None

    def forward(self, q_data, qa_data, target):
        # Noncapturable/nonfused Adam scalar state must retain CPU ambient allocation.
        with torch.device('cpu'):
            result = self._forward(q_data, qa_data, target)
        if self.cuda_profile is not None:
            _cuda_execution_check(self.cuda_profile, synchronize=True)
        return result

    def _forward(self, q_data, qa_data, target):
        call, self._call = self._call, None
        _need(call is not None, 'native forward requires a fresh one-use bound context')
        _need((self.variant, self.condition_sha256) == self._recipe_identity, 'native variant/condition drift')
        _need(q_data is call.batch.q_data and qa_data is call.batch.qa_data and target is call.batch.loss_targets,
              'foreign tensor identity for context ticket')
        _need(_cuda_profile_sha(self.cuda_profile) == self._cuda_profile_sha, 'native CUDA execution profile drift')
        if self.cuda_profile is not None:
            _cuda_execution_check(self.cuda_profile)
        _need(_batch_sha(call.batch, device=self._device) == call.payload_sha256, 'batch changed after binding')
        _need(_evidence_sha(call.evidence) == call.evidence_sha256, 'native bound evidence drift')
        _need(tuple(id(p) for p in self.parameters()) == self._parameter_ids, 'registered parameter identity changed')
        _need(all(p.device == self._device and p.dtype == torch.float32 for p in self.parameters()),
              'FP32 parameters on the explicit execution device required')
        active = []
        if call.enabled and self.variant != 'A0':
            for row, items in enumerate(call.evidence):
                for local, item in enumerate(items):
                    if item is None:
                        continue
                    audit = item.audit
                    _need(audit.target_fitted, 'unfitted query cannot enter graph forward')
                    observed = tuple(p for p in audit.parents if p.support > 0)
                    mass = sum(p.confidence for p in observed)
                    if mass > 0:
                        message = sum(p.confidence * (p.mean_observed_correctness - .5) for p in observed) / max(1., mass)
                        active.append((row, local, message, _features(audit)))
        if not active:
            # Includes A0, whole-off, empty graph and all-confidence-mass zero.
            return self.backbone(q_data, qa_data, target)
        # Exact NonRasch upstream operations; no inverse sigmoid or attention edit.
        q_embed = self.backbone.q_embed(q_data)
        responses = (qa_data - q_data) // self.backbone.n_question
        qa_embed = self.backbone.qa_embed(responses) + q_embed
        hidden = self.backbone.model(q_embed, qa_embed)
        joined = torch.cat([hidden, q_embed], dim=-1)
        base_logits = self.backbone.out(joined).reshape(q_data.shape)
        base_probabilities = torch.sigmoid(base_logits)
        residual = torch.zeros_like(base_logits)
        applied = torch.zeros_like(q_data, dtype=torch.bool)
        for row, local, message, features in active:
            gate = (torch.sigmoid(self.gate(base_logits.new_tensor(features))).reshape(())
                    if self.gate is not None else base_logits.new_ones(()))
            # Alpha=0 is deliberately not a shortcut: d(loss)/d(alpha) survives.
            residual[row, local] = self.alpha * gate * message
            applied[row, local] = True
        logits = base_logits + residual
        probabilities = torch.where(applied, torch.sigmoid(logits), base_probabilities)
        labels = target.reshape(-1)
        mask = labels > -.9
        loss = F.binary_cross_entropy_with_logits(logits.reshape(-1)[mask], labels[mask].float(), reduction='none').sum()
        _need(bool(torch.isfinite(loss)) and bool(torch.isfinite(probabilities).all()), 'nonfinite graph objective/output')
        return loss, probabilities.reshape(-1), mask.sum()


@dataclass(frozen=True)
class _TrainingTicket:
    batch: AKTBatch
    batch_sha256: str
    context: tuple
    index_sha256: str
    window_ids: tuple[str, ...]
    evidence_sha256: str


class ResearchGraphAKTAdapter:
    """Research composition tái dùng AKTAdapter.step, không thêm train loop.

    Không fitted export/checkpoint/optimizer factory hoặc quyền fit. Có thể đổi
    index train→selection cùng encoding80 mà không giữ trajectory/truth của các
    role khác trong model.
    """
    def __init__(self, *, config: AKTConfig, encoding: data.ResearchAKTEncoding,
                 index: contexts.ResearchGraphContextIndex, condition: conditions.ResearchGraphCondition,
                 cuda_profile: ResearchCUDAExecutionProfile | None = None):
        _need(type(config) is AKTConfig and config.phase == 'simulator-research', 'explicit research config required')
        validate_config(config, cuda_profile=cuda_profile)
        _need(config.source_root == ROOT / 'artifacts/akt/dependencies/upstream'
              and torch.get_default_dtype() == torch.float32, 'pinned native root and FP32 construction required')
        _need(type(encoding) is data.ResearchAKTEncoding and type(condition) is conditions.ResearchGraphCondition,
              'typed research encoding/condition required')
        self.config = config
        self.cuda_profile = cuda_profile
        self._cuda_profile_sha = _cuda_profile_sha(cuda_profile)
        self._device = torch.device('cpu' if cuda_profile is None else cuda_profile.device)
        self.research_encoding = encoding
        self.encoding = encoding.exercise_encoding()
        self.condition = condition
        self._condition_sha = condition.identity
        self._encoding_sha = encoding.identity
        self._config_sha = _config_sha(config)
        self._sources = source_inventory()
        self._ticket = None
        self._optimizer = None
        self._failed = False
        self.set_context_index(index)
        self.native = ResearchGraphNative(config=config, n_items=len(self.encoding.vocabulary.values), condition=condition,
                                          cuda_profile=cuda_profile)
        self._parameters = tuple(self.native.parameters())
        self._integrity(full=True)  # Constructor/attach boundary, not per batch.

    @property
    def identity(self):
        self._integrity(full=True)
        payload = dict(recipe=RECIPE, condition=self._condition_sha,
            encoding=self._encoding_sha, config=self._config_sha, sources=self._sources)
        if self.cuda_profile is not None:
            payload['cuda_execution_profile'] = asdict(self.cuda_profile)
        return identity_hash(payload)

    def _integrity(self, *, full=False):
        _need(not self._failed, 'failed adapter cannot be reused')
        _need(self.condition.identity == self._condition_sha and self.research_encoding.identity == self._encoding_sha,
              'condition/encoding changed')
        _need(_config_sha(self.config) == self._config_sha and source_inventory() == self._sources,
              'model config/source drift')
        _need(_cuda_profile_sha(self.cuda_profile) == self._cuda_profile_sha, 'adapter CUDA execution profile drift')
        self.index.check_access_header(self._context_seal)
        _need(self.index.content_sha256 == self._index_sha == self._context_seal.root_sha256, 'context index changed')
        if full:
            self.index.assert_integrity()
        if hasattr(self, 'native'):
            _need(self.native.cuda_profile is self.cuda_profile and self.native._device == self._device,
                  'native/adapter execution profile mismatch')
            _need(self.native.variant == self.condition.variant and self.native.condition_sha256 == self._condition_sha,
                  'native variant/condition drift')
            _need(tuple(id(p) for p in self.native.parameters()) == tuple(id(p) for p in self._parameters),
                  'owned registered model parameters changed')

    def set_context_index(self, index):
        _need(self._ticket is None, 'consume training ticket before changing phase')
        _need(type(index) is contexts.ResearchGraphContextIndex, 'typed graph context index required')
        seal = index.seal_for_access()
        _need(index.condition_sha256 == self._condition_sha and index.encoding_sha256 == self._encoding_sha,
              'context condition/encoding mismatch')
        _need(index.context == self.config.context and index.target_block == self.config.target_block,
              'context/native geometry mismatch')
        _need(index.vocabulary_sha256 == identity_hash(self.encoding.vocabulary.values), 'context vocabulary mismatch')
        self.index, self._index_sha, self._context_seal = index, seal.root_sha256, seal

    def audit_context_boundary(self):
        """Audit toàn cache trước/sau epoch hoặc prediction pass do caller quản.

        Hot path kiểm selected records; unselected nested drift có thể chỉ bị
        phát hiện ở boundary. Fail sau updates là partial, không có rollback.
        Method này không tự cấp trainer/checkpoint/execution authority.
        """
        self._integrity(full=True)
        return dict(index_sha256=self._index_sha, condition_sha256=self._condition_sha,
                    encoding_sha256=self._encoding_sha)

    def _collate(self, windows, targets=None):
        _need(1 <= len(windows) <= self.config.batch_size and all(type(w) is WindowInputs for w in windows),
              'bounded typed windows required')
        _need(len({w.window_id for w in windows}) == len(windows), 'duplicate window IDs')
        _need(all(1 <= len(w.inputs.item_ids) <= self.config.max_length for w in windows), 'window length cap')
        evidence = self.index.for_windows(tuple(windows), access_seal=self._context_seal)
        batch = collate_windows(windows, n_items=len(self.encoding.vocabulary.values), device=self._device, targets=targets)
        return batch, evidence

    def collate_training(self, entries: Sequence[TrainingWindow]) -> AKTBatch:
        self._integrity()
        _need(self._ticket is None, 'one outstanding training ticket only')
        _need(self.index.neural_binding.phase_scope in ('select_train80', 'refit_union90'), 'prediction phase cannot train')
        _need(all(type(e) is TrainingWindow for e in entries), 'typed TrainingWindow required')
        batch, evidence = self._collate(tuple(e.window for e in entries), [e.targets for e in entries])
        self._ticket = _TrainingTicket(batch, _batch_sha(batch, device=self._device), evidence, self._index_sha,
            tuple(e.window.window_id for e in entries), _evidence_sha(evidence))
        return batch

    def step(self, batch: AKTBatch, optimizer: torch.optim.Optimizer) -> dict:
        self._integrity()
        ticket, self._ticket = self._ticket, None
        _need(ticket is not None and batch is ticket.batch and ticket.batch_sha256 == _batch_sha(batch, device=self._device)
              and ticket.index_sha256 == self._index_sha, 'fresh exact unchanged training ticket required')
        self.index.check_selected_records(ticket.window_ids, access_seal=self._context_seal)
        _need(_evidence_sha(ticket.context) == ticket.evidence_sha256, 'training ticket evidence drift')
        _need(type(optimizer) is torch.optim.Adam, 'explicit existing research Adam required')
        actual = tuple(p for group in optimizer.param_groups for p in group['params'])
        _need(len(actual) == len(self._parameters) and len({id(p) for p in actual}) == len(actual)
              and {id(p) for p in actual} == {id(p) for p in self._parameters}, 'optimizer must own every model parameter exactly once')
        _need(self._optimizer is optimizer or (self._optimizer is None and not optimizer.state), 'same initially fresh owned optimizer required')
        for group in optimizer.param_groups:
            _need(all(group[k] == getattr(self.config, k) for k in ('lr', 'betas', 'eps', 'weight_decay')), 'optimizer/config mismatch')
            _need(all(group.get(k, False) is False for k in ('maximize', 'capturable', 'differentiable', 'amsgrad', 'decoupled_weight_decay'))
                  and all(group.get(k) in (None, False) for k in ('foreach', 'fused')), 'unsupported Adam behavior')
            if self.cuda_profile is not None:
                _need(group.get('foreach') is False and group.get('fused') is False, 'CUDA Adam requires explicit foreach=False/fused=False')
        _need(self.native.training, 'training mode required before optimizer step')
        self._optimizer = optimizer
        try:
            self.native.bind(batch, ticket.context, enabled=True, expected_evidence_sha256=ticket.evidence_sha256)
            # Exact AKTBatch and .native ownership preserve the public primitive.
            with torch.device('cpu'):
                result = AKTAdapter.step(self, batch, optimizer)
            if self.cuda_profile is not None:
                _cuda_execution_check(self.cuda_profile, synchronize=True)
            self._integrity()
            self.index.check_selected_records(ticket.window_ids, access_seal=self._context_seal)
            _need(_evidence_sha(ticket.context) == ticket.evidence_sha256, 'training ticket evidence drift after primitive')
            return result
        except BaseException:
            self._failed = True
            raise
        finally:
            self.native.clear_context()

    def predict_windows(self, windows: Sequence[WindowInputs]) -> list[np.ndarray]:
        """Selected-record checks; caller bao toàn pass bằng boundary audit.

        Không full-audit tại mỗi call vì runner có thể gọi theo từng batch.
        Không coi một batch thành nghiệm thu toàn phase/corpus.
        """
        self._integrity()
        _need(self._ticket is None, 'prediction cannot consume/skip pending training ticket')
        modes = tuple((module, module.training) for module in self.native.modules())
        output = []
        try:
            self.native.eval()
            devices = [] if self.cuda_profile is None else [0]
            with torch.random.fork_rng(devices=devices), torch.inference_mode():
                for start in range(0, len(windows), self.config.batch_size):
                    group = tuple(windows[start:start+self.config.batch_size])
                    batch, evidence = self._collate(group)
                    window_ids = tuple(w.window_id for w in group)
                    digest = _evidence_sha(evidence)
                    self.index.check_selected_records(window_ids, access_seal=self._context_seal)
                    self.native.bind(batch, evidence, enabled=True, expected_evidence_sha256=digest)
                    _, probabilities, _ = self.native(batch.q_data, batch.qa_data, batch.loss_targets)
                    self.index.check_selected_records(window_ids, access_seal=self._context_seal)
                    _need(_evidence_sha(evidence) == digest, 'prediction evidence drift after forward')
                    values = probabilities.reshape(batch.q_data.shape).cpu().numpy().astype(np.float64)
                    _need(np.isfinite(values).all() and ((values >= 0) & (values <= 1)).all(), 'invalid graph probabilities')
                    output.extend(values[row, :len(w.inputs.item_ids)].copy() for row, w in enumerate(group))
            self._integrity()
            if self.cuda_profile is not None:
                _cuda_execution_check(self.cuda_profile, synchronize=True)
            return output
        finally:
            self.native.clear_context()
            for module, training in modes:
                module.training = training
