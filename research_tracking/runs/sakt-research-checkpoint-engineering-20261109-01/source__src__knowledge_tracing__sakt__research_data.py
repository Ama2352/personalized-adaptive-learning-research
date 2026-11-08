"""Public research corpus → SAKT sliding targets, không trainer/fitted authority.

Tái dùng role/phase/encoding audit và prefix-chain đã có trong data-only AKT
module; không gọi AKT model/runner. Recipe/cold policy do caller truyền rõ.
Truth vẫn ở sidecar hoặc training wrapper, không nằm trong causal inputs.
"""
from dataclasses import InitVar, asdict, dataclass, field
import hashlib
from pathlib import Path

import numpy as np

from knowledge_tracing.akt.research_simulator_data import (
    OPTIMIZATION_SCOPES, SCOPES, ResearchAKTEncoding, ResearchAKTShard,
    ResearchPhaseData, ResearchUnseenTarget, fit_research_encoding,
    iter_research_windows, prepare_research_phase, research_scoring_targets,
)
from knowledge_tracing.akt.types import TrainingWindow
from knowledge_tracing.shared_kt import CausalSequenceInputs
from knowledge_tracing.simulator_bridge import ItemQuery, identity_hash
from knowledge_tracing.simulator_corpus_reader import CorpusReadLimits, PublicResearchCorpus
from .training_data import SAKTDataRecipe


def source_identity():
    root = Path(__file__).resolve().parents[3]
    names = ('sakt/__init__.py', 'sakt/research_data.py', 'sakt/training_data.py',
             'simulator_corpus_reader.py', 'simulator_research_data.py',
             'simulator_bridge.py', 'simulator_data.py', 'shared_kt.py',
             'akt/research_simulator_data.py', 'akt/windows.py', 'akt/types.py',
             'akt/encoding.py', 'akt/config.py', 'akt/provenance.py')
    return tuple((name, hashlib.sha256((root / 'src/knowledge_tracing' / name).read_bytes()).hexdigest())
                 for name in names)


@dataclass(frozen=True)
class SAKTResearchView:
    corpus: InitVar[PublicResearchCorpus]
    phase: ResearchPhaseData
    encoding: ResearchAKTEncoding
    recipe: SAKTDataRecipe
    corpus_sha256: str = field(init=False)
    read_limits: CorpusReadLimits = field(init=False)
    sources_sha256: tuple = field(init=False, repr=False)
    content_sha256: str = field(init=False)

    def __post_init__(self, corpus):
        if (type(corpus) is not PublicResearchCorpus or type(self.phase) is not ResearchPhaseData
                or type(self.encoding) is not ResearchAKTEncoding or type(self.recipe) is not SAKTDataRecipe):
            raise ValueError('typed public corpus/phase/encoding/SAKT recipe required')
        corpus.assert_integrity()
        for shard in self.phase.shards:
            role = corpus.role_data(shard.role)
            if (shard.plan != corpus.plan or shard.bank != corpus.bank
                    or shard.trajectories != role.trajectories or shard.provenance != role.provenance
                    or shard.expected_provenance_sha256 != role.provenance.identity
                    or shard.limits != corpus.limits.shard_limits
                    or identity_hash(shard.audit) != identity_hash(role.audit)):
                raise ValueError('phase must preserve public role/provenance/limits/audit')
        # Public API validates scope↔encoding, including refit/freeze lineage.
        research_scoring_targets(self.phase, self.encoding)
        # Retain only selected phase labels. Full corpus is an InitVar; its SHA
        # binds initial provenance, not ongoing disk/source-origin attestation.
        object.__setattr__(self, 'corpus_sha256', corpus.identity)
        object.__setattr__(self, 'read_limits', corpus.limits)
        object.__setattr__(self, 'sources_sha256', source_identity())
        object.__setattr__(self, 'content_sha256', identity_hash(self._payload()))

    def _payload(self):
        return dict(model='sakt', role='research_data_only_no_fit_attestation',
                    corpus_sha256=self.corpus_sha256, phase_sha256=self.phase.identity,
                    encoding_sha256=self.encoding.identity, recipe=asdict(self.recipe),
                    read_limits=asdict(self.read_limits), target_block=1,
                    sources_sha256=self.sources_sha256)

    def assert_integrity(self):
        if self.sources_sha256 != source_identity() or identity_hash(self._payload()) != self.content_sha256:
            raise ValueError('SAKT research corpus/source/recipe/phase/encoding changed')

    @property
    def identity(self):
        self.assert_integrity()
        return self.content_sha256

    @property
    def vocabulary(self):
        self.assert_integrity()
        return self.encoding.exercise_encoding().vocabulary


def prepare_sakt_research_view(corpus, *, scope, recipe, encoding=None, selection_freeze=None):
    """Không disk I/O corpus hoặc synthetic_only/fake-fold conversion.

    Prediction scopes bắt buộc encoding optimization đã có. Refit90 dùng actual
    train+selection roles với SelectionFreeze, không đổi role thành train giả.
    """
    if (type(corpus) is not PublicResearchCorpus or type(scope) is not str or scope not in SCOPES
            or type(recipe) is not SAKTDataRecipe):
        raise ValueError('typed public corpus, one of four scopes and explicit SAKT recipe required')
    corpus.assert_integrity()
    shards = []
    for role in SCOPES[scope]:
        value = corpus.role_data(role)
        shard = ResearchAKTShard(corpus.plan, corpus.bank, role, value.trajectories,
                                 value.provenance, value.provenance.identity, corpus.limits.shard_limits)
        if identity_hash(shard.audit) != identity_hash(value.audit):
            raise ValueError('public role audit/provenance/limits changed')
        shards.append(shard)
    phase = prepare_research_phase(scope, shards=tuple(shards), selection_freeze=selection_freeze)
    if encoding is None:
        if scope not in OPTIMIZATION_SCOPES:
            raise ValueError('prediction scope requires existing optimization encoding')
        encoding = fit_research_encoding(phase)
    return SAKTResearchView(corpus, phase, encoding, recipe)


@dataclass(frozen=True)
class SAKTResearchInput:
    learner_id: str
    query: ItemQuery
    global_rank: int
    origin_role: str
    phase_sha256: str
    encoding_sha256: str
    history_sha256: str
    history_hash_scheme: str
    support_reason: str
    history_available: int
    history_used: int
    context_reset: bool
    inputs: CausalSequenceInputs | None
    target_mask: np.ndarray | None
    position_ids: np.ndarray | None

    @property
    def eligible(self):
        return self.support_reason in ('known_history', 'cold_query_only')


@dataclass(frozen=True)
class SAKTResearchTrainingTarget:
    inputs: SAKTResearchInput
    target: int  # Loss-only wrapper; never passed to SAKTCore.forward.


def sakt_research_scoring_targets(view):
    """Full truth sidecar và full-prefix hashes; không predictor inputs."""
    if type(view) is not SAKTResearchView:
        raise ValueError('typed SAKT research view required')
    view.assert_integrity()
    result = research_scoring_targets(view.phase, view.encoding)
    view.assert_integrity()
    return result


def iter_sakt_research_inputs(view, *, training):
    """Một entry mỗi target, kể cả OOV/cold unsupported; không lọc denominator.

    Training trả wrapper có label riêng. Prediction chỉ trả input record, không
    current/future labels. Known windows có exactly một terminal target mask.
    """
    if type(view) is not SAKTResearchView or type(training) is not bool:
        raise ValueError('typed SAKT research view and explicit bool training required')
    view.assert_integrity()
    if training and view.phase.scope not in OPTIMIZATION_SCOPES:
        raise ValueError('selection/calibration prediction scope cannot train')
    truth = sakt_research_scoring_targets(view)
    windows = iter_research_windows(view.phase, view.encoding, context=view.recipe.context,
                                   target_block=1, training=training)
    seen = set()
    count = 0
    for window, target in zip(windows, truth, strict=True):
        key = (target.learner_id, target.query.source_row, target.global_rank)
        if key in seen:
            raise ValueError('duplicate SAKT research target')
        seen.add(key)
        count += 1
        if type(window) is ResearchUnseenTarget:
            if (window.learner_id, window.query.source_row, window.global_rank) != key:
                raise ValueError('OOV target/truth alignment mismatch')
            sequence, mask, positions = None, None, None
            # ResearchUnseenTarget has no history_available field. Match the
            # public AKT online OOV geometry: rank - max(0, block_start-context).
            # With mandatory target_block=1, block_start is exactly global_rank;
            # this is also SAKT adapter's nominal pre-barrier context count.
            base = max(0, target.global_rank - view.recipe.context)
            available, used, reset, reason = target.global_rank - base, 0, True, 'oov_item'
        else:
            geometry = window.window if training else window
            sequence = geometry.inputs
            n = len(sequence.item_ids)
            if (n < 1 or n > view.recipe.context + 1 or geometry.target_mask.sum() != 1
                    or not geometry.target_mask[-1]
                    or (sequence.user_ids[-1], int(sequence.source_rows[-1]), int(geometry.global_ranks[-1])) != key):
                raise ValueError('SAKT terminal target/sliding geometry mismatch')
            available, used = int(geometry.history_available[-1]), n - 1
            reset = bool(geometry.context_reset[-1])
            reason = ('known_history' if used else 'cold_query_only'
                      if view.recipe.first_target_policy == 'query_only' else 'cold_unsupported')
            if training and (type(window) is not TrainingWindow or int(window.targets[-1]) != target.correct):
                raise ValueError('training label/truth sidecar mismatch')
            if reason == 'cold_unsupported':
                sequence, mask, positions = None, None, None
            else:
                mask = np.zeros(n, dtype=bool)
                mask[-1] = True
                positions = np.arange(n, dtype=np.int64)
                for array in (sequence.item_ids, sequence.timestamps, sequence.prior_responses,
                              sequence.source_rows, sequence.sequence_offsets, mask, positions):
                    array.flags.writeable = False
        record = SAKTResearchInput(target.learner_id, target.query, target.global_rank, target.origin_role,
            target.phase_sha256, target.encoding_sha256, target.history_sha256, target.history_hash_scheme,
            reason, available, used, reset, sequence, mask, positions)
        yield SAKTResearchTrainingTarget(record, target.correct) if training else record
    if count != len(truth):
        raise ValueError('incomplete SAKT full-target population')
    view.assert_integrity()
