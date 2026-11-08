"""Research corpus split/provenance/support contracts; no generation or fitting.

Reuses frozen observable validators. Provenance/freeze hashes bind caller-provided
artifacts; they do not attest that a generator/selector actually ran correctly.
"""
from collections import Counter
from dataclasses import asdict, dataclass, field

from .simulator_bridge import SimulatorBank, identity_hash
from .simulator_data import ObservableTrajectory, ROLES, SimulatorSplitPlan, validate_role_shard

PROTOCOL_ID = 'S04A-S05B-GROUP-V1-20261108'
DEVELOPMENT_ROLES = ('train', 'selection', 'calibration')
MAX_PLAN_LEARNERS = 10000  # Metadata allocation ceiling, not a scientific cohort default.


def _sha(value):
    if type(value) is not str or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('explicit lowercase SHA-256 required')


def _positive(value):
    if type(value) is not int or value < 1:
        raise ValueError('explicit positive integer required')


def _text(value):
    if type(value) is not str or not value.strip():
        raise ValueError('explicit nonempty text required')


@dataclass(frozen=True)
class ResearchSplitPlan:
    namespace: str
    root_seed: int
    development_learners: int
    final_learners: int
    protocol_sha256: str
    split_plan: SimulatorSplitPlan = field(init=False, repr=False)

    def __post_init__(self):
        _text(self.namespace)
        _sha(self.protocol_sha256)
        _positive(self.development_learners)
        _positive(self.final_learners)
        if (type(self.root_seed) is not int or not 0 <= self.root_seed < 2**63
                or self.development_learners % 10
                or self.development_learners + self.final_learners > MAX_PLAN_LEARNERS):
            raise ValueError('exact 80/10/10 counts and bounded metadata plan required; no rounding')
        tenth = self.development_learners // 10
        counts = (('train', 8*tenth), ('selection', tenth), ('calibration', tenth),
                  ('final', self.final_learners))
        object.__setattr__(self, 'split_plan', SimulatorSplitPlan(
            'research-v1:' + self.namespace, self.root_seed, counts))

    @property
    def identity(self):
        return identity_hash({'protocol_id': PROTOCOL_ID, 'protocol_sha256': self.protocol_sha256,
                              'split_plan_sha256': self.split_plan.identity,
                              'development_learners': self.development_learners,
                              'final_learners': self.final_learners})

    def manifest(self):
        assignments = self.split_plan.assignments()
        return {'protocol_id': PROTOCOL_ID, 'research_plan_sha256': self.identity,
                'split_plan_sha256': self.split_plan.identity,
                'protocol_sha256': self.protocol_sha256,
                'role_counts': dict(self.split_plan.role_counts),
                'assignments': [asdict(a) for a in assignments],
                'refit_roles': ['train', 'selection'], 'calibration_in_refit': False,
                'final_events_read': False,
                'scope': 'planned identities/seed namespaces; not empirical independence or generated corpus'}


@dataclass(frozen=True)
class ResearchProvenance:
    role: str
    research_plan_sha256: str
    split_plan_sha256: str
    bank_sha256: str
    environment_graph_sha256: str
    source_bindings: tuple[tuple[str, str], ...]
    collection_recipe_sha256: str
    collection_policy_id: str
    timestamp_unit: str
    timezone: str
    logging_policy_oracle_access: bool

    def __post_init__(self):
        if self.role not in ROLES:
            raise ValueError('explicit role required')
        for value in (self.research_plan_sha256, self.split_plan_sha256, self.bank_sha256,
                      self.environment_graph_sha256, self.collection_recipe_sha256):
            _sha(value)
        _text(self.collection_policy_id)
        if (type(self.source_bindings) is not tuple or not self.source_bindings
                or any(type(pair) is not tuple or len(pair) != 2 for pair in self.source_bindings)):
            raise ValueError('immutable source bindings required')
        for name, digest in self.source_bindings:
            _text(name)
            _sha(digest)
        names = [name for name, _ in self.source_bindings]
        if len(names) != len(set(names)) or not {'collector', 'environment'} <= set(names):
            raise ValueError('unique collector/environment source bindings required')
        object.__setattr__(self, 'source_bindings', tuple(sorted(self.source_bindings)))
        if (self.timestamp_unit != 'unix_seconds_utc' or self.timezone != 'UTC'
                or self.logging_policy_oracle_access is not False):
            raise ValueError('explicit UTC clock and oracle-free logging-policy provenance required')

    @property
    def identity(self):
        return identity_hash(asdict(self))


@dataclass(frozen=True)
class ShardLimits:
    max_learners: int
    max_events_per_learner: int
    max_total_events: int

    def __post_init__(self):
        for value in (self.max_learners, self.max_events_per_learner, self.max_total_events):
            _positive(value)


def audit_research_shard(trajectories, *, plan, bank, role, provenance,
                         expected_provenance_sha256, limits, reference_items):
    """Audit only requested development role; final data rejected before iteration.

No source I/O, generator calls or oracle-sidecar fields are accepted. Source and
policy metadata are declarations bound to an externally pinned identity.
"""
    if role not in DEVELOPMENT_ROLES:
        raise ValueError('final events are inaccessible to development audit')
    if (type(plan) is not ResearchSplitPlan or type(bank) is not SimulatorBank
            or type(provenance) is not ResearchProvenance or type(limits) is not ShardLimits):
        raise ValueError('typed research plan/bank/provenance/limits required')
    _sha(expected_provenance_sha256)
    if (provenance.identity != expected_provenance_sha256 or provenance.role != role
            or provenance.research_plan_sha256 != plan.identity
            or provenance.split_plan_sha256 != plan.split_plan.identity
            or provenance.bank_sha256 != identity_hash(bank.identity)):
        raise ValueError('provenance/role/plan/domain binding mismatch')
    if (type(reference_items) is not tuple or not reference_items
            or any(type(i) is not str for i in reference_items)
            or len(reference_items) != len(set(reference_items))
            or set(reference_items) != set(bank.item_ids)):
        raise ValueError('reference items must cover the complete bank; no subset renormalization')
    concepts = {}
    for item in bank.items:
        concepts.setdefault(item.concept_id, []).append(item.difficulty)
    if (len(bank.items) != 84 or len(concepts) != 28
            or any(sorted(values) != [1050., 1200., 1350.] for values in concepts.values())):
        raise ValueError('protocol V1 requires 28 concepts with exactly three reference difficulties')
    expected_count = dict(plan.split_plan.role_counts)[role]
    if (type(trajectories) is not tuple or len(trajectories) != expected_count
            or len(trajectories) > limits.max_learners):
        raise ValueError('complete bounded role tuple required')
    total = 0
    for trajectory in trajectories:
        if type(trajectory) is not ObservableTrajectory:
            raise ValueError('exact observable trajectory schema required; no oracle subclasses')
        if trajectory.collection_policy_id != provenance.collection_policy_id:
            raise ValueError('trajectory logging policy does not match pinned provenance')
        total += len(trajectory.observations)
        if total > limits.max_total_events:
            raise ValueError('role exceeds explicit total-event budget')
    audit = validate_role_shard(trajectories, plan=plan.split_plan, bank=bank, role=role,
                                max_events_per_learner=limits.max_events_per_learner)
    event_counts, learner_counts = Counter(), Counter()
    for trajectory in trajectories:
        values = [event.query.item_id for event in trajectory.observations]
        event_counts.update(values)
        learner_counts.update(set(values))
    item_to_concept = {i.item_id: i.concept_id for i in bank.items}
    items = [{'item_id': item, 'concept_id': item_to_concept[item],
              'events': event_counts[item], 'learners': learner_counts[item]}
             for item in sorted(bank.item_ids)]
    missing = sorted(item for item in reference_items if not learner_counts[item])
    result = {'schema_version': 1, 'protocol_id': PROTOCOL_ID, 'role': role,
              'research_plan_sha256': plan.identity, 'provenance_sha256': provenance.identity,
              'provenance': asdict(provenance), 'limits': asdict(limits), 'audit': audit,
              'item_support': items, 'reference_items': list(reference_items),
              'missing_reference_items': missing, 'reference_complete': not missing,
              'train_vocabulary': sorted(learner_counts) if role == 'train' else None,
              'scope': 'observable corpus/provenance/support only; no generator, fitted model or readiness claim'}
    result['receipt_sha256'] = identity_hash(result)
    return result


@dataclass(frozen=True)
class SelectionFreeze:
    research_plan_sha256: str
    bank_sha256: str
    train_shard_sha256: str
    selection_shard_sha256: str
    selector_artifact_sha256: str
    selected_epoch: int
    stage: str

    def __post_init__(self):
        for value in (self.research_plan_sha256, self.bank_sha256, self.train_shard_sha256,
                      self.selection_shard_sha256, self.selector_artifact_sha256):
            _sha(value)
        _positive(self.selected_epoch)
        if self.stage != 'raw_selection_before_refit':
            raise ValueError('selector must be frozen on raw selection before refit')

    @property
    def identity(self):
        return identity_hash(asdict(self))


@dataclass(frozen=True)
class ResearchRefitView:
    trajectories: tuple[ObservableTrajectory, ...]
    learner_origin_roles: tuple[tuple[str, str], ...]
    research_plan_sha256: str
    bank_sha256: str
    train_receipt_sha256: str
    selection_receipt_sha256: str
    freeze: SelectionFreeze

    @property
    def role(self):
        return 'refit_train_plus_selection'  # Deliberately not a fake legacy train shard.

    @property
    def identity(self):
        return identity_hash(asdict(self))

    def observable_sequences(self):
        return tuple((t.learner_id, t.observations) for t in self.trajectories)


def prepare_refit_view(train, selection, *, plan, bank, train_provenance, selection_provenance,
                       expected_train_provenance_sha256, expected_selection_provenance_sha256,
                       train_limits, selection_limits, reference_items, freeze):
    """Explicit 90% union; no calibration/final argument or role relabeling."""
    train_receipt = audit_research_shard(train, plan=plan, bank=bank, role='train',
        provenance=train_provenance, expected_provenance_sha256=expected_train_provenance_sha256,
        limits=train_limits, reference_items=reference_items)
    selection_receipt = audit_research_shard(selection, plan=plan, bank=bank, role='selection',
        provenance=selection_provenance, expected_provenance_sha256=expected_selection_provenance_sha256,
        limits=selection_limits, reference_items=reference_items)
    if (type(freeze) is not SelectionFreeze or freeze.research_plan_sha256 != plan.identity
            or freeze.bank_sha256 != identity_hash(bank.identity)
            or freeze.train_shard_sha256 != train_receipt['audit']['shard_sha256']
            or freeze.selection_shard_sha256 != selection_receipt['audit']['shard_sha256']):
        raise ValueError('stale or foreign selection freeze')
    source_rows = [o.query.source_row for t in train + selection for o in t.observations]
    if len(source_rows) != len(set(source_rows)):
        raise ValueError('source rows must remain unique across refit role union')
    rows = tuple(sorted(train + selection, key=lambda t: t.learner_id))
    origins = tuple(sorted([(t.learner_id, 'train') for t in train]
                           + [(t.learner_id, 'selection') for t in selection]))
    return ResearchRefitView(rows, origins, plan.identity, identity_hash(bank.identity),
                             train_receipt['receipt_sha256'], selection_receipt['receipt_sha256'], freeze)
