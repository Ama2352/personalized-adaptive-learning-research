"""RESDATA01→AKT windows/target ledger; không allocation/model/optimizer.

Scopes research giữ riêng với simulator_engineering. Prefix chain gắn toàn bộ
observable past, không phải OnlineSession.history_sha256 vốn có model binding.
Identity/source seals là consistency checks hợp tác, không training authority.
"""
from collections import Counter
from dataclasses import asdict, dataclass, field
import hashlib
from pathlib import Path

import numpy as np

from knowledge_tracing.shared_kt import CausalSequenceInputs, StableVocabulary
from knowledge_tracing.simulator_bridge import ItemQuery, SimulatorBank, identity_hash
from knowledge_tracing.simulator_research_data import (ResearchProvenance, ResearchSplitPlan,
    SelectionFreeze, ShardLimits, audit_research_shard, prepare_refit_view)
from .encoding import ExerciseEncoding, encode_exercises
from .types import TrainingWindow
from .windows import iter_window_slices, slice_causal_inputs

PREFIX_SCHEME = 'observable-prefix-chain-v1'
SCOPES = {'select_train80': ('train',), 'raw_selection10': ('selection',),
          'refit_union90': ('train', 'selection'), 'calibration_predict': ('calibration',)}
OPTIMIZATION_SCOPES = ('select_train80', 'refit_union90')


def _sha(value):
    if type(value) is not str or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('SHA256 required')


def source_identity():
    root = Path(__file__).resolve().parents[3]
    names = ('shared_kt.py', 'simulator_bridge.py', 'simulator_data.py', 'simulator_research_data.py',
             'akt/research_simulator_data.py', 'akt/windows.py', 'akt/types.py', 'akt/encoding.py',
             'akt/provenance.py', 'akt/config.py')
    return tuple((name, hashlib.sha256((root / 'src/knowledge_tracing' / name).read_bytes()).hexdigest()) for name in names)


@dataclass(frozen=True)
class ResearchAKTShard:
    plan: ResearchSplitPlan
    bank: SimulatorBank
    role: str
    trajectories: tuple
    provenance: ResearchProvenance
    expected_provenance_sha256: str
    limits: ShardLimits

    def __post_init__(self):
        self.audit

    @property
    def audit(self):
        return audit_research_shard(self.trajectories, plan=self.plan, bank=self.bank, role=self.role,
            provenance=self.provenance, expected_provenance_sha256=self.expected_provenance_sha256,
            limits=self.limits, reference_items=self.bank.item_ids if type(self.bank) is SimulatorBank else ())

    @property
    def identity(self):
        return self.audit['receipt_sha256']


@dataclass(frozen=True)
class ResearchPhaseData:
    scope: str
    shards: tuple[ResearchAKTShard, ...]
    selection_freeze: SelectionFreeze | None = None
    sources_sha256: tuple = field(init=False, repr=False)
    content_sha256: str = field(init=False)

    def __post_init__(self):
        if self.scope not in SCOPES or type(self.shards) is not tuple or any(type(s) is not ResearchAKTShard for s in self.shards):
            raise ValueError('explicit research scope and exact audited shards required')
        if tuple(s.role for s in self.shards) != SCOPES[self.scope]:
            raise ValueError('scope/role inputs mismatch; calibration cannot train/refit')
        first = self.shards[0]
        if any(s.plan != first.plan or s.bank != first.bank for s in self.shards):
            raise ValueError('phase plan/bank mismatch')
        if self.scope == 'refit_union90':
            self._refit_view()  # Revalidate real roles/receipts/freeze/row uniqueness.
        elif self.scope == 'calibration_predict':
            freeze = self.selection_freeze
            if (type(freeze) is not SelectionFreeze or freeze.research_plan_sha256 != first.plan.identity
                    or freeze.bank_sha256 != identity_hash(first.bank.identity)):
                raise ValueError('calibration requires matching raw-selection freeze lineage')
        elif self.selection_freeze is not None:
            raise ValueError('selection freeze not accepted before selection')
        object.__setattr__(self, 'sources_sha256', source_identity())
        object.__setattr__(self, 'content_sha256', identity_hash(self._payload()))

    def _refit_view(self):
        tr, se = self.shards
        return prepare_refit_view(tr.trajectories, se.trajectories, plan=tr.plan, bank=tr.bank,
            train_provenance=tr.provenance, selection_provenance=se.provenance,
            expected_train_provenance_sha256=tr.expected_provenance_sha256,
            expected_selection_provenance_sha256=se.expected_provenance_sha256,
            train_limits=tr.limits, selection_limits=se.limits, reference_items=tr.bank.item_ids,
            freeze=self.selection_freeze)

    def _payload(self):
        return dict(schema_version=1, scope=self.scope, role_receipts=[s.audit for s in self.shards],
            selection_freeze=None if self.selection_freeze is None else asdict(self.selection_freeze),
            history_hash_scheme=PREFIX_SCHEME, sources_sha256=self.sources_sha256,
            refit_view_sha256=self._refit_view().identity if self.scope == 'refit_union90' else None)

    def assert_integrity(self):
        if self.sources_sha256 != source_identity() or self.content_sha256 != identity_hash(self._payload()):
            raise ValueError('research phase/source/input drift')

    @property
    def identity(self):
        self.assert_integrity()
        return self.content_sha256

    @property
    def manifest(self):
        self.assert_integrity()
        return {**self._payload(), 'phase_sha256': self.content_sha256,
                'scope_limit': 'data geometry/coverage only; no execution or fitted authorization'}

    @property
    def trajectories(self):
        return tuple(sorted((t for s in self.shards for t in s.trajectories), key=lambda t: t.learner_id))


def prepare_research_phase(scope, *, shards, selection_freeze=None):
    return ResearchPhaseData(scope, shards, selection_freeze)


@dataclass(frozen=True)
class ResearchAKTEncoding:
    research_plan_sha256: str
    domain_sha256: str
    optimization_scope: str
    optimization_phase_sha256: str
    origin_shard_sha256: tuple[tuple[str, str], ...]
    selection_freeze_sha256: str | None
    learners: int
    support: tuple[tuple[str, int], ...]
    sources_sha256: tuple
    content_sha256: str
    history_hash_scheme: str = PREFIX_SCHEME

    def payload(self):
        return {k: v for k, v in asdict(self).items() if k != 'content_sha256'}

    def assert_integrity(self):
        if (self.optimization_scope not in OPTIMIZATION_SCOPES or self.history_hash_scheme != PREFIX_SCHEME
                or self.sources_sha256 != source_identity() or self.content_sha256 != identity_hash(self.payload())
                or type(self.learners) is not int or self.learners < 1 or not self.support
                or self.support != tuple(sorted(self.support)) or len(dict(self.support)) != len(self.support)
                or any(type(item) is not str or not item or type(n) is not int or not 1 <= n <= self.learners for item, n in self.support)):
            raise ValueError('encoding lineage/support/source drift')
        for value in (self.research_plan_sha256, self.domain_sha256, self.optimization_phase_sha256, self.content_sha256): _sha(value)
        expected_roles = SCOPES[self.optimization_scope]
        if tuple(role for role, _ in self.origin_shard_sha256) != expected_roles:
            raise ValueError('encoding role lineage')
        for _, value in self.origin_shard_sha256: _sha(value)
        if self.optimization_scope == 'refit_union90': _sha(self.selection_freeze_sha256)
        elif self.selection_freeze_sha256 is not None: raise ValueError('unexpected refit freeze')

    @property
    def identity(self):
        self.assert_integrity()
        return self.content_sha256

    def exercise_encoding(self):
        self.assert_integrity()
        return ExerciseEncoding(StableVocabulary(tuple(item for item, _ in self.support)), dict(self.support))


def fit_research_encoding(phase: ResearchPhaseData):
    if type(phase) is not ResearchPhaseData or phase.scope not in OPTIMIZATION_SCOPES:
        raise ValueError('vocabulary only from select_train80 or explicit refit_union90')
    phase.assert_integrity()
    support = Counter()
    for t in phase.trajectories: support.update({o.query.item_id for o in t.observations})
    first = phase.shards[0]
    value = dict(research_plan_sha256=first.plan.identity, domain_sha256=identity_hash(first.bank.identity),
        optimization_scope=phase.scope, optimization_phase_sha256=phase.identity,
        origin_shard_sha256=tuple((s.role, s.audit['audit']['shard_sha256']) for s in phase.shards),
        selection_freeze_sha256=None if phase.selection_freeze is None else phase.selection_freeze.identity,
        learners=len(phase.trajectories), support=tuple(sorted(support.items())),
        sources_sha256=source_identity(), history_hash_scheme=PREFIX_SCHEME)
    result = ResearchAKTEncoding(**value, content_sha256=identity_hash(value))
    result.assert_integrity()
    return result


def _check_pair(phase, encoding, training):
    if type(phase) is not ResearchPhaseData or type(encoding) is not ResearchAKTEncoding or type(training) is not bool:
        raise ValueError('typed phase/encoding/boolean training required')
    phase.assert_integrity(); encoding.assert_integrity()
    if training and phase.scope not in OPTIMIZATION_SCOPES:
        raise ValueError('prediction-only selection/calibration cannot train')
    first = phase.shards[0]
    if (encoding.research_plan_sha256 != first.plan.identity or encoding.domain_sha256 != identity_hash(first.bank.identity)
            or not {item for item, _ in encoding.support}.issubset(first.bank.item_ids)):
        raise ValueError('encoding plan/domain mismatch')
    if phase.scope in OPTIMIZATION_SCOPES:
        if encoding.optimization_scope != phase.scope or encoding.optimization_phase_sha256 != phase.identity:
            raise ValueError('optimization data/encoding lineage mismatch')
    elif phase.scope == 'raw_selection10':
        if encoding.optimization_scope != 'select_train80': raise ValueError('raw selection must precede refit vocabulary')
    elif (encoding.optimization_scope != 'refit_union90'
          or encoding.selection_freeze_sha256 != phase.selection_freeze.identity):
        raise ValueError('calibration must use same frozen refit90 lineage')


@dataclass(frozen=True)
class ResearchUnseenTarget:
    learner_id: str
    query: ItemQuery
    global_rank: int
    phase_sha256: str
    support_reason: str = 'oov_item'


@dataclass(frozen=True)
class ResearchScoringTarget:
    learner_id: str
    query: ItemQuery
    correct: int
    global_rank: int
    origin_role: str
    phase_scope: str
    phase_sha256: str
    encoding_sha256: str
    trained_item: bool
    history_sha256: str
    history_hash_scheme: str = PREFIX_SCHEME


def iter_research_windows(phase, encoding, *, context: int, target_block: int, training: bool):
    _check_pair(phase, encoding, training)
    if type(context) is not int or context < 0 or type(target_block) is not int or target_block < 1:
        raise ValueError('explicit valid window geometry required')
    exercise_encoding = encoding.exercise_encoding()
    phase_id = phase.identity
    for t in phase.trajectories:
        rows = t.observations
        ids = encode_exercises([o.query.item_id for o in rows], exercise_encoding)
        labels = np.asarray([o.correct for o in rows], dtype=np.int8)
        prior = np.asarray([-1, *labels[:-1]], dtype=np.int8)
        inputs = CausalSequenceInputs(ids, np.asarray([o.query.timestamp for o in rows], dtype=np.int64), prior,
            np.asarray([o.query.source_row for o in rows], dtype=np.int64), np.asarray([0, len(rows)], dtype=np.int64),
            (t.learner_id,) * len(rows), None)
        for geometry in iter_window_slices(ids, inputs.sequence_offsets, context=context, target_block=target_block):
            if geometry.unseen:
                if training: raise ValueError('unexpected OOV optimization target')
                yield ResearchUnseenTarget(t.learner_id, rows[geometry.start].query, int(geometry.global_ranks[0]), phase_id)
            else:
                window = slice_causal_inputs(inputs, geometry)
                yield TrainingWindow(window, labels[geometry.start:geometry.stop].copy()) if training else window
    phase.assert_integrity(); encoding.assert_integrity()


def research_scoring_targets(phase, encoding):
    """Full target truth sidecar; không truyền result này vào predictor.

    Prefixchain không phụ thuộc model/vocab/scope: cùng learner+bank+past có cùng
    chain giữa model conditions. Current/future response chỉ đổi chain SAU row.
    """
    _check_pair(phase, encoding, False)
    vocabulary = {item for item, _ in encoding.support}
    phase_id, encoding_id = phase.identity, encoding.identity
    roles = {t.learner_id: s.role for s in phase.shards for t in s.trajectories}
    domain = identity_hash(phase.shards[0].bank.identity)
    result = []
    for t in phase.trajectories:
        prefix = identity_hash(dict(scheme=PREFIX_SCHEME, domain_sha256=domain, learner_id=t.learner_id))
        for rank, observation in enumerate(t.observations):
            result.append(ResearchScoringTarget(t.learner_id, observation.query, observation.correct, rank,
                roles[t.learner_id], phase.scope, phase_id, encoding_id, observation.query.item_id in vocabulary, prefix))
            prefix = identity_hash(dict(scheme=PREFIX_SCHEME, previous_sha256=prefix, observation=asdict(observation)))
    phase.assert_integrity(); encoding.assert_integrity()
    return tuple(result)
