"""Dựng F/K-y từ selection RoleData đã audit, chỉ tính trong bộ nhớ.

Caller lấy PublicRoleData từ public reader đáng tin cậy và ghim context/receipt.
Type và SHA là consistency, không chứng minh nguồn đã chạy reader. Helper không
mở corpus, gọi audit/generator/model, chọn winner hoặc cấp freeze/refit authority.
"""
from dataclasses import dataclass
import hashlib
import math
import time

from knowledge_tracing.research_admission import (
    MainSelectionContext, ModelNeutralKey, PopulationExpectation, HISTORY_SCHEME,
    _canonical as population_bytes,
)
from knowledge_tracing.simulator_bridge import ItemQuery, Observation, identity_hash
from knowledge_tracing.simulator_corpus_reader import PublicRoleData
from knowledge_tracing.simulator_data import ObservableTrajectory
from knowledge_tracing.simulator_research_data import ResearchProvenance


def need(ok, message):
    if not ok:
        raise ValueError(message)


@dataclass(frozen=True)
class PopulationLimits:
    max_learners: int
    max_rows: int
    max_rows_per_learner: int
    max_metadata_bytes: int
    max_seconds: float

    def __post_init__(self):
        for value in (self.max_learners, self.max_rows, self.max_rows_per_learner, self.max_metadata_bytes):
            need(type(value) is int and 0 < value <= 10**7, 'Explicit positive count/byte limit')
        need(type(self.max_seconds) in (int, float) and math.isfinite(self.max_seconds)
             and 0 < self.max_seconds <= 120, 'Explicit cooperative wall limit')


@dataclass(frozen=True)
class SelectionPopulation:
    expectation: PopulationExpectation
    learner_target_counts: tuple[tuple[str, int], ...]
    class_counts: tuple[int, int]
    audit_receipt_sha256: str
    provenance_sha256: str
    role_shard_sha256: str
    elapsed_seconds: float
    scope: str = 'TRUSTED_SELECTION_POPULATION_EXPECTATION_ONLY'
    file_admission_performed: bool = False
    external_freeze_authority: bool = False
    refit_authorized: bool = False


def prepare_selection_population(role_data, context, *, expected_provenance_sha256,
                                 expected_audit_receipt_sha256, limits):
    """Reuse canonical key/record encoding, không dùng model vocabulary hoặc P.

Prefix chain bám research_simulator_data.research_scoring_targets, domain/learner
initial hash rồi append nguyên Observation SAU khi xuất key hiện tại. Sorting K
chỉ dùng cho statistical hash, không sửa chronology hoặc bất kỳ input container.
Không đòi hai lớp hoặc đủ84refs ở helper này. Audit/support thuộc public reader.
"""
    started = time.perf_counter()
    need(type(limits) is PopulationLimits, 'Typed finite population limits')
    limits.__post_init__()

    def guard():
        elapsed = time.perf_counter() - started
        need(math.isfinite(elapsed) and 0 <= elapsed <= limits.max_seconds, 'Population deadline exceeded')
        return elapsed

    need(type(role_data) is PublicRoleData and role_data.role == 'selection', 'Trusted selection role only')
    need(type(context) is MainSelectionContext, 'Typed main context')
    context.validate()
    need(context.environment_id == 'grade10_simulator', 'Current public role bridge is Grade10 only')
    provenance = role_data.provenance
    need(type(provenance) is ResearchProvenance and provenance.role == 'selection'
         and provenance.identity == expected_provenance_sha256
         and provenance.research_plan_sha256 == context.split_sha256
         and provenance.bank_sha256 == context.domain_sha256
         and provenance.timestamp_unit == 'unix_seconds_utc' and provenance.timezone == 'UTC'
         and provenance.logging_policy_oracle_access is False, 'Provenance/domain/role binding')
    need(type(role_data.audit_json) is str and type(role_data.manifest_json) is str
         and len(role_data.audit_json.encode('utf-8')) <= limits.max_metadata_bytes
         and len(role_data.manifest_json.encode('utf-8')) <= limits.max_metadata_bytes, 'Metadata byte cap')
    audit, manifest = role_data.audit, role_data.manifest
    need(type(role_data.class_counts) is tuple and len(role_data.class_counts) == 2
         and all(type(value) is int and value >= 0 for value in role_data.class_counts)
         and type(audit['audit']['learners']) is int and type(audit['audit']['targets']) is int,
         'Exact reader audit count types')
    receipt = audit['receipt_sha256']
    need(receipt == expected_audit_receipt_sha256
         and identity_hash({k: v for k, v in audit.items() if k != 'receipt_sha256'}) == receipt
         and audit['role'] == audit['audit']['role'] == 'selection'
         and audit['research_plan_sha256'] == context.split_sha256
         and audit['provenance_sha256'] == provenance.identity
         and manifest['provenance_sha256'] == provenance.identity
         and audit['audit']['shard_sha256'] == context.selection_role_sha256
         and audit['audit']['domain_sha256'] == context.domain_sha256
         and audit['audit']['plan_sha256'] == provenance.split_plan_sha256, 'Sealed reader audit/manifest binding')
    trajectories = role_data.trajectories
    need(type(trajectories) is tuple and 0 < len(trajectories) <= limits.max_learners
         and audit['audit']['learners'] == len(trajectories), 'Complete bounded learner population')
    records, learners, source_rows, counts, classes = [], set(), set(), [], [0, 0]
    for trajectory in trajectories:
        guard()
        need(type(trajectory) is ObservableTrajectory and trajectory.learner_id not in learners
             and trajectory.plan_sha256 == provenance.split_plan_sha256
             and trajectory.domain_sha256 == context.domain_sha256
             and trajectory.collection_policy_id == provenance.collection_policy_id,
             'Exact unique observable learner/provenance')
        learners.add(trajectory.learner_id)
        observations = trajectory.observations
        need(type(observations) is tuple and 0 < len(observations) <= limits.max_rows_per_learner,
             'Complete bounded chronological observations')
        counts.append((trajectory.learner_id, len(observations)))
        prefix = identity_hash(dict(scheme=HISTORY_SCHEME, domain_sha256=context.domain_sha256,
                                    learner_id=trajectory.learner_id))
        previous = None
        for rank, observation in enumerate(observations):
            guard()
            need(len(records) < limits.max_rows, 'Population row cap')
            need(type(observation) is Observation and type(observation.query) is ItemQuery
                 and type(observation.correct) is int and observation.correct in (0, 1), 'Binary observable target')
            query = observation.query
            chronology = (query.timestamp, query.source_row)
            need(type(query.timestamp) is int and query.timestamp >= 0
                 and type(query.source_row) is int and query.source_row > 0
                 and query.source_row not in source_rows and (previous is None or previous < chronology),
                 'Duplicate source row or nonchronological input')
            key = ModelNeutralKey(trajectory.learner_id, query.item_id, query.timestamp, query.source_row,
                                  rank, HISTORY_SCHEME, prefix, 'selection')
            records.append((key, observation.correct))
            source_rows.add(query.source_row)
            classes[observation.correct] += 1
            previous = chronology
            # Same source equation; current y is not in its own key.
            prefix = identity_hash(dict(scheme=HISTORY_SCHEME, previous_sha256=prefix,
                                        observation={'query': {'item_id': query.item_id,
                                            'timestamp': query.timestamp, 'source_row': query.source_row},
                                            'correct': observation.correct}))
    guard()
    need(len(records) == audit['audit']['targets'] and tuple(classes) == role_data.class_counts,
         'Reader audit count/labels changed')
    # Recompute original role hash before canonical sorting, retaining chronology.
    actual_shard = identity_hash([trajectory.payload() for trajectory in sorted(trajectories, key=lambda t: t.learner_id)])
    need(actual_shard == context.selection_role_sha256, 'Observable shard/label mutation')
    records.sort(key=lambda row: row[0])
    full_hash, label_hash = hashlib.sha256(), hashlib.sha256()
    previous_key = None
    for key, correct in records:
        guard()
        need(previous_key is None or previous_key < key, 'Duplicate canonical K')
        full_hash.update(population_bytes(key.values()))
        label_hash.update(population_bytes((key.values(), correct)))
        previous_key = key
    expectation = PopulationExpectation(context, len(records), full_hash.hexdigest(), label_hash.hexdigest())
    return SelectionPopulation(expectation, tuple(sorted(counts)), tuple(classes), receipt,
                               provenance.identity, actual_shard, guard())
