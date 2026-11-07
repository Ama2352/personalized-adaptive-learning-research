"""Collector fixture CPU từ phương trình Paper2, không chạy notebook top-level.

Chỉ train shard <=2learner x12events, không là corpus nghiên cứu được duyệt.
Oracle tách riêng; logging policy không đọc theta/profile/graph để chọn item.
"""

import csv
from dataclasses import asdict, dataclass
import hashlib
import time

import numpy as np
import pandas as pd

from .paper2_reference import ROOT, load_reference
from .simulator_bridge import ItemQuery, Observation, SimulatorBank, SimulatorItem, identity_hash
from .simulator_data import ObservableTrajectory, SimulatorSplitPlan, validate_role_shard


MAX_LEARNERS = 2
MAX_EVENTS = 12
CLOCK_UNIT = 'unix_seconds_utc'
COLLECTOR_VERSION = 'paper2-train-fixture-v1'


def canonical_source_provenance(provenance):
    """Path identity chung Windows/Linux; giữ nguyên source bytes/hash lịch sử."""
    return {**provenance, 'notebook': provenance['notebook'].replace('\\', '/'),
            'inputs': {name.replace('\\', '/'): digest for name, digest in provenance['inputs'].items()}}


@dataclass(frozen=True)
class CollectionRecipe:
    policy: str
    events_per_learner: int
    start_unix_seconds: int
    gap_seconds: int
    max_wall_seconds: int

    def __post_init__(self):
        if self.policy not in {'cyclic_items', 'uniform_items'}:
            raise ValueError('fixture logging policy must be explicitly oracle-free')
        if (type(self.events_per_learner) is not int or not 1 <= self.events_per_learner <= MAX_EVENTS
                or type(self.start_unix_seconds) is not int or self.start_unix_seconds < 0
                or type(self.gap_seconds) is not int or self.gap_seconds < 1
                or type(self.max_wall_seconds) is not int or not 1 <= self.max_wall_seconds <= 30):
            raise ValueError('invalid fixture workload/clock budget')
        # Fail trước load/source execution nếu clock không biểu diễn được.
        pd.to_datetime(self.start_unix_seconds + self.gap_seconds * self.events_per_learner, unit='s', utc=True)

    @property
    def identity(self):
        return identity_hash({'collector_version': COLLECTOR_VERSION, 'timestamp_unit': CLOCK_UNIT, **asdict(self)})


@dataclass(frozen=True)
class CollectionResult:
    bank: SimulatorBank
    trajectories: tuple[ObservableTrajectory, ...]
    oracle_sidecar: dict
    manifest: dict


def response_channels(assignment, count):
    """Độc lập namespace outcome/learning; prefix không đổi khi tăng event cap.

Khác cách gọi RNG trong notebook lịch sử: đây là collector version riêng.
Nguồn environment nhận uniforms như cũ; không claim identical published run.
"""
    if type(count) is not int or not 1 <= count <= MAX_EVENTS:
        raise ValueError('response channel count exceeds fixture cap')
    root = dict(assignment.stream_seeds)['response']
    channels, provenance = {}, {}
    for name in ('outcome', 'learning'):
        seed = int(identity_hash([COLLECTOR_VERSION, root, name])[:16], 16)
        rng = np.random.Generator(np.random.PCG64(seed))
        before = rng.bit_generator.state
        values = rng.random(count)
        channels[name] = values
        provenance[name] = {'seed': seed, 'state_before': before, 'state_after': rng.bit_generator.state,
                            'uniforms_sha256': identity_hash(values.tolist())}
    return channels, provenance


def collect_training_fixture(plan: SimulatorSplitPlan, *, profiles: dict[str, str], recipe: CollectionRecipe):
    """Sinh train-only; profiles và uniforms không đi vào observable schema.

Không có tham số estimator/controller graph. True graph/source giữ cố định.
Role khác chỉ có assignments trong plan, không sinh trajectory hay oracle state.
"""
    started = time.perf_counter()
    if type(recipe) is not CollectionRecipe:
        raise ValueError('explicit collection recipe required')
    assignments = plan.assignments('train')
    if len(assignments) > MAX_LEARNERS:
        raise ValueError('fixture learner cap exceeded; full cohort needs separate protocol/entrypoint')
    if not isinstance(profiles, dict) or set(profiles) != {a.learner_id for a in assignments}:
        raise ValueError('profile metadata must match exactly train learners')

    def deadline():
        if time.perf_counter() - started > recipe.max_wall_seconds:
            raise TimeoutError('collector fixture wall budget exhausted')

    reference = load_reference()
    env_scope = reference['environment']
    if any(profile not in env_scope['PERSONAS'] for profile in profiles.values()):
        raise ValueError('unknown Paper2 profile')
    provenance = canonical_source_provenance(reference['provenance'])
    # Domain gắn source/true-graph/item-bank/clock; behavior distribution thuộc recipe.
    domain = identity_hash({'source': provenance, 'timestamp_unit': CLOCK_UNIT})
    question_path = next(ROOT / name for name in provenance['inputs'] if name.endswith('/question_bank.csv'))
    with question_path.open(encoding='utf-8-sig', newline='') as stream:
        items = tuple(SimulatorItem(row['question_id'], row['concept_id'], float(row['elo_difficulty']))
                      for row in csv.DictReader(stream))
    bank = SimulatorBank('paper2-grade10-collector-' + domain, items)
    if len(bank.items) != 84 or {i.concept_id for i in bank.items} != set(env_scope['nodes']):
        raise ValueError('unexpected reference item bank')
    deadline()
    trajectories, oracle = [], {}
    policy_id = COLLECTOR_VERSION + ':' + recipe.policy
    for ordinal, assignment in enumerate(assignments):
        seeds = dict(assignment.stream_seeds)
        profile = profiles[assignment.learner_id]
        base = env_scope['persona_base_abilities'](profile, seeds['latent'])
        environment = env_scope['LatentStudentEnvironment'](base)
        channels, channel_metadata = response_channels(assignment, recipe.events_per_learner)
        behavior_rng = np.random.Generator(np.random.PCG64(seeds['behavior']))
        behavior_before = behavior_rng.bit_generator.state
        observations, details = [], []
        for rank in range(recipe.events_per_learner):
            deadline()
            # Chọn candidate không nhận oracle hoặc current response.
            index = rank % len(bank.items) if recipe.policy == 'cyclic_items' else int(behavior_rng.integers(len(bank.items)))
            item = bank.items[index]
            seconds = recipe.start_unix_seconds + (rank+1) * recipe.gap_seconds
            timestamp = pd.to_datetime(seconds, unit='s', utc=True)
            result = environment.interact(item.concept_id, item.difficulty, timestamp,
                                           float(channels['outcome'][rank]), float(channels['learning'][rank]))
            query = ItemQuery(item.item_id, seconds, ordinal * MAX_EVENTS + rank+1)
            observations.append(Observation(query, int(result['y'])))
            details.append({'query': asdict(query), 'oracle_result': dict(result),
                            'outcome_uniform': float(channels['outcome'][rank]),
                            'learning_uniform': float(channels['learning'][rank])})
        trajectory = ObservableTrajectory(assignment.learner_id, plan.identity, identity_hash(bank.identity),
                                          policy_id, tuple(observations))
        trajectories.append(trajectory)
        oracle[assignment.learner_id] = {'profile': profile, 'assignment': asdict(assignment),
            'initial_state': base, 'initial_state_sha256': identity_hash(base), 'events': details,
            'latent_seed_source': 'persona_base_abilities(profile, assignment.latent); source hash in manifest',
            'response_rng': channel_metadata, 'behavior_rng': {'seed': seeds['behavior'],
                'state_before': behavior_before, 'state_after': behavior_rng.bit_generator.state},
            'final_snapshot': environment.snapshot(timestamp)}
    audit = validate_role_shard(trajectories, plan=plan, bank=bank, role='train',
                                max_events_per_learner=recipe.events_per_learner)
    # Không chấp nhận source/input bị đổi giữa thời điểm đọc và lúc đóng run.
    sources = {provenance['notebook']: provenance['notebook_sha256'], **provenance['inputs']}
    for name, digest in sources.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('reference source/input changed during collection')
    deadline()
    sidecar = {'scope': 'oracle evaluation/replay only; forbidden as model input', 'learners': oracle}
    manifest = {'schema_version': 1, 'collector_version': COLLECTOR_VERSION, 'role': 'train',
        'scope': 'bounded engineering fixture; not approved research corpus', 'source': provenance,
        'domain': bank.identity, 'plan_sha256': plan.identity, 'recipe': asdict(recipe),
        'recipe_sha256': recipe.identity, 'timestamp_unit': CLOCK_UNIT, 'timezone': 'UTC',
        'first_event': 'start + gap', 'logging_policy_oracle_access': False,
        'rng': 'NumPy PCG64; separate derived outcome/learning channels; behavior independent',
        'numpy_version': np.__version__, 'pandas_version': pd.__version__, 'audit': audit,
        'profile_metadata_sha256': identity_hash(profiles), 'oracle_sidecar_sha256': identity_hash(sidecar),
        'elapsed_seconds': time.perf_counter()-started}
    return CollectionResult(bank, tuple(trajectories), sidecar, manifest)
