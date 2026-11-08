"""Split/schema mô phỏng: tách roles, không giả fold Junyi hoặc nhận oracle.

Seeds là danh tính RNG khai báo, chưa chứng minh độc lập hay độ đa dạng learner.
Module không generate simulation, fit model, chọn allocation hoặc mở final data.
"""

from dataclasses import asdict, dataclass

from .simulator_bridge import ItemQuery, Observation, SimulatorBank, identity_hash


ROLES = ('train', 'selection', 'calibration', 'final')
STREAMS = ('latent', 'response', 'behavior')


def _text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('expected nonempty identifier')


def _sha(value):
    if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('expected SHA-256 identity')


@dataclass(frozen=True)
class LearnerAssignment:
    learner_id: str
    role: str
    seed_family: str
    stream_seeds: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class SimulatorSplitPlan:
    namespace: str
    root_seed: int
    role_counts: tuple[tuple[str, int], ...]

    def __post_init__(self):
        _text(self.namespace)
        if type(self.root_seed) is not int or not 0 <= self.root_seed < 2**63:
            raise ValueError('invalid root seed')
        counts = tuple(self.role_counts)
        if (len(counts) != len(ROLES) or any(not isinstance(pair, tuple) or len(pair) != 2 for pair in counts)
                or {pair[0] for pair in counts} != set(ROLES)
                or any(type(count) is not int or count < 1 for _, count in counts)):
            raise ValueError('explicit positive counts required for all four roles')
        normalized = tuple((role, dict(counts)[role]) for role in ROLES)
        object.__setattr__(self, 'role_counts', normalized)
        assignments = self.assignments()
        for values in ([a.learner_id for a in assignments], [a.seed_family for a in assignments],
                       [seed for a in assignments for _, seed in a.stream_seeds]):
            if len(values) != len(set(values)):
                raise ValueError('learner/seed collision; choose a new declared namespace')

    @property
    def identity(self):
        return identity_hash({'schema_version': 1, **asdict(self)})

    def assignments(self, role=None):
        if role is not None and role not in ROLES:
            raise ValueError('unknown simulator role')
        result = []
        for name, count in self.role_counts:
            if role is not None and name != role:
                continue
            for ordinal in range(count):
                family = identity_hash({'schema_version': 1, 'namespace': self.namespace,
                    'root_seed': self.root_seed, 'role': name, 'ordinal': ordinal})
                seeds = tuple((stream, int(identity_hash([family, stream])[:16], 16)) for stream in STREAMS)
                result.append(LearnerAssignment('sim-' + identity_hash([family, 'learner']), name, family, seeds))
        return tuple(result)


@dataclass(frozen=True)
class ObservableTrajectory:
    learner_id: str
    plan_sha256: str
    domain_sha256: str
    collection_policy_id: str
    observations: tuple[Observation, ...]

    def __post_init__(self):
        _text(self.learner_id)
        _text(self.collection_policy_id)
        _sha(self.plan_sha256)
        _sha(self.domain_sha256)
        if not self.observations or any(type(item) is not Observation or type(item.query) is not ItemQuery
                                        for item in self.observations):
            raise ValueError('expected nonempty observable trajectory')
        object.__setattr__(self, 'observations', tuple(self.observations))

    def payload(self):
        return asdict(self)

    @classmethod
    def from_payload(cls, payload):
        required = {'learner_id', 'plan_sha256', 'domain_sha256', 'collection_policy_id', 'observations'}
        if not isinstance(payload, dict) or set(payload) != required:
            raise ValueError('unknown or missing trajectory fields; oracle metadata forbidden')
        rows = payload['observations']
        if not isinstance(rows, (list, tuple)):
            raise ValueError('invalid observations')
        result = []
        for row in rows:
            if not isinstance(row, dict) or set(row) != {'query', 'correct'}:
                raise ValueError('unknown or missing observation fields')
            query = row['query']
            if not isinstance(query, dict) or set(query) != {'item_id', 'timestamp', 'source_row'}:
                raise ValueError('unknown or missing query fields')
            result.append(Observation(ItemQuery(**query), row['correct']))
        return cls(**{**payload, 'observations': tuple(result)})


def validate_role_shard(trajectories, *, plan: SimulatorSplitPlan, bank: SimulatorBank,
                        role: str, max_events_per_learner: int):
    """Chỉ nhận shard role yêu cầu; không cần đọc các shard khác để audit train.

source_row phải unique trong shard; collection policy chỉ là metadata audit.
Không xác minh RNG thật đã được generator dùng: cần generator manifest riêng.
"""
    if role not in ROLES:
        raise ValueError('explicit simulator role required')
    expected = {a.learner_id for a in plan.assignments(role)}
    if type(max_events_per_learner) is not int or max_events_per_learner < 1:
        raise ValueError('explicit positive event budget required')
    seen, rows, items, policies = set(), set(), set(), set()
    domain = identity_hash(bank.identity)
    events = 0
    shard = tuple(trajectories)
    for trajectory in shard:
        if not isinstance(trajectory, ObservableTrajectory):
            raise ValueError('invalid trajectory schema')
        learner = trajectory.learner_id
        if learner not in expected or learner in seen:
            raise ValueError('wrong-role or duplicate learner')
        if trajectory.plan_sha256 != plan.identity or trajectory.domain_sha256 != domain:
            raise ValueError('trajectory plan/domain mismatch')
        if len(trajectory.observations) > max_events_per_learner:
            raise ValueError('trajectory exceeds event budget')
        seen.add(learner)
        policies.add(trajectory.collection_policy_id)
        previous = None
        for observation in trajectory.observations:
            query = observation.query
            key = query.timestamp, query.source_row
            if query.item_id not in bank.item_ids:
                raise ValueError('item outside simulator domain')
            if query.source_row in rows or (previous is not None and key <= previous):
                raise ValueError('duplicate source row or chronology violation')
            rows.add(query.source_row)
            items.add(query.item_id)
            previous = key
            events += 1
    if seen != expected:
        raise ValueError('missing expected learners in requested role shard')
    return {'schema_version': 1, 'role': role, 'plan_sha256': plan.identity, 'domain_sha256': domain,
            'learners': len(seen), 'targets': events, 'observed_items': sorted(items),
            'unobserved_bank_items': sorted(set(bank.item_ids) - items),
            'collection_policy_ids': sorted(policies),
            'shard_sha256': identity_hash([t.payload() for t in sorted(shard, key=lambda t: t.learner_id)]),
            'scope': 'schema/coverage only; no empirical independence, calibration or model metrics'}


def training_observations(trajectories, *, plan, bank, max_events_per_learner):
    """Chỉ xuất observable sequences thuộc train, không giả fold Junyi.

Trả về observations và learner key; policy/seed/latent metadata không vào features.
Đây chưa là adapter training AKT hay refit với selection.
"""
    shard = tuple(trajectories)
    validate_role_shard(shard, plan=plan, bank=bank, role='train',
                        max_events_per_learner=max_events_per_learner)
    return tuple((t.learner_id, t.observations) for t in sorted(shard, key=lambda t: t.learner_id))
