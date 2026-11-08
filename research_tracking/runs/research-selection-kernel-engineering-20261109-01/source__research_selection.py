"""GRAPH13: response-pooled common-U selection statistics, stdlib only.

NO I/O, corpus, model, artifact admission or external-freeze authority. Caller
must separately admit ALL nine selected-only candidates before any main refit:
A0, A1/A2/A3 x EXPERT/LEARNED, SAKT, GKT. This kernel receives only A0 + four
eligible A1/A3 sufficient statistics; comparison-only candidates are not waived.

LL from rounded per-learner sums preserves the response-pooled estimand, but
fsum(learner sums) need not be bitwise identical to fsum(all rows)/sklearn mean.
Known-answer canonical fixture tolerance is 1e-12; eligibility has NO epsilon.
Cooperative clocks/work caps are not OS hard interruption or input attestation.
"""
from dataclasses import dataclass
import hashlib
import json
import math
import random
import time

REQUIRED_CANDIDATE_IDS = ('A0','A1_EXPERT','A1_LEARNED','A2_EXPERT','A2_LEARNED',
                          'A3_EXPERT','A3_LEARNED','SAKT','GKT')
ELIGIBLE_GRAPH_IDS = ('A1_EXPERT','A1_LEARNED','A3_EXPERT','A3_LEARNED')
COMMON_MODEL_IDS = ('A0', *ELIGIBLE_GRAPH_IDS)
REPLICATES = 2000
SEED = 42
RNG_ID = 'cpython-random-MT19937-randrange-v1'
QUANTILE_ID = 'linear-type7-v1'
ROW_LOSS_ID = 'binary64-two-class-eps-clip-mathlog-v1'
AGGREGATION_ID = 'binary64-learner-sums-fsum-response-pooled-v1'
CANONICAL_FIXTURE_ABS_TOLERANCE = 1e-12
EPSILON = 2.**-52
MAX_ROW_LOSS = -math.log(EPSILON)
MAX_LEARNERS = 100000
MAX_TARGETS = 10**9
MAX_WORK_UNITS = 10**9
_clock = time.perf_counter
_make_rng = random.Random


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def _integer(value, maximum, *, zero=False):
    _need(type(value) is int and (0 if zero else 1) <= value <= maximum,
          'bounded exact integer required')


def _learner_id(value):
    _need(type(value) is str and 0 < len(value) <= 256 and value == value.strip(),
          'bounded nonempty learner identity required')


def binary_row_log_loss(probability: float, correct: int) -> float:
    """Canonical formula: form binary complement BEFORE independent f64 clips."""
    _need(type(probability) is float and math.isfinite(probability) and 0 <= probability <= 1,
          'finite binary64 raw probability required')
    _need(type(correct) is int and correct in (0, 1), 'exact binary label required')
    classes = (1. - probability, probability)
    p = min(1. - EPSILON, max(EPSILON, classes[correct]))
    return -math.log(p)


@dataclass(frozen=True)
class CandidateLossSum:
    candidate_id: str
    target_count: int
    loss_sum: float

    def _validate(self):
        _need(type(self.candidate_id) is str and self.candidate_id in COMMON_MODEL_IDS,
              'candidate outside fixed common models')
        _integer(self.target_count, MAX_TARGETS)
        _need(type(self.loss_sum) is float and math.isfinite(self.loss_sum)
              and 0 <= self.loss_sum <= self.target_count * MAX_ROW_LOSS,
              'finite nonnegative canonical-range loss sum required')

    def __post_init__(self):
        self._validate()


@dataclass(frozen=True)
class LearnerCommonStatistics:
    learner_id: str
    common_target_count: int
    candidates: tuple[CandidateLossSum, ...]

    def _validate(self):
        _learner_id(self.learner_id)
        _integer(self.common_target_count, MAX_TARGETS)
        _need(type(self.candidates) is tuple and len(self.candidates) == 5
              and all(type(c) is CandidateLossSum for c in self.candidates), 'exact five typed candidate sums')
        for c in self.candidates:
            c._validate()
        _need({c.candidate_id for c in self.candidates} == set(COMMON_MODEL_IDS)
              and all(c.target_count == self.common_target_count for c in self.candidates),
              'five models must have identical common-U target counts')

    def __post_init__(self):
        self._validate()


@dataclass(frozen=True)
class CommonPopulationCoverage:
    # Caller declaration only; no per-candidate/full-key admission occurs here.
    full_target_count: int
    zero_contribution_learner_ids: tuple[str, ...]

    def _validate(self):
        _integer(self.full_target_count, MAX_TARGETS)
        ids = self.zero_contribution_learner_ids
        _need(type(ids) is tuple and len(ids) <= MAX_LEARNERS, 'bounded zero-contribution coverage tuple')
        for value in ids:
            _learner_id(value)
        _need(len(set(ids)) == len(ids), 'duplicate zero-contribution learner')

    def __post_init__(self):
        self._validate()


@dataclass(frozen=True)
class SelectionKernelLimits:
    max_learners: int
    max_full_targets: int
    max_common_targets: int
    max_index_requests: int
    max_work_units: int
    max_seconds: float

    def _validate(self):
        _integer(self.max_learners, MAX_LEARNERS)
        _integer(self.max_full_targets, MAX_TARGETS)
        _integer(self.max_common_targets, MAX_TARGETS)
        _integer(self.max_index_requests, MAX_WORK_UNITS)
        _integer(self.max_work_units, MAX_WORK_UNITS)
        _need(type(self.max_seconds) in (int, float) and math.isfinite(self.max_seconds)
              and 0 < self.max_seconds <= 120, 'explicit cooperative time cap in (0,120] required')

    def __post_init__(self):
        self._validate()


class SelectionLimitExceeded(RuntimeError):
    """No proposed winner returned on partial resource completion."""
    def __init__(self, reason, index_requests, work_units, elapsed_seconds):
        super().__init__(reason)
        self.reason = reason
        self.index_requests = index_requests
        self.work_units = work_units
        self.elapsed_seconds = elapsed_seconds


class _Budget:
    def __init__(self, limits, started):
        self.limits, self.started = limits, started
        self.index_requests = self.work_units = 0
        self.last_elapsed = 0.

    def check(self):
        now = _clock()
        if type(now) not in (int, float) or not math.isfinite(now):
            raise SelectionLimitExceeded('invalid cooperative clock', self.index_requests, self.work_units, self.last_elapsed)
        elapsed = now - self.started
        if (not math.isfinite(elapsed) or elapsed < self.last_elapsed or elapsed > self.limits.max_seconds):
            raise SelectionLimitExceeded('cooperative time/clock bound', self.index_requests, self.work_units, elapsed)
        self.last_elapsed = elapsed
        return elapsed

    def work(self, amount=1):
        self.work_units += amount
        if self.work_units > self.limits.max_work_units:
            raise SelectionLimitExceeded('work-unit cap', self.index_requests, self.work_units, self.last_elapsed)
        if self.work_units % 256 == 0:
            self.check()


def linear_percentile(values, quantile):
    _need(type(values) in (tuple, list) and values
          and all(type(v) is float and math.isfinite(v) for v in values), 'nonempty finite percentile values')
    _need(type(quantile) in (int, float) and math.isfinite(quantile) and 0 <= quantile <= 1,
          'finite percentile in [0,1]')
    ordered = sorted(values)
    h = (len(ordered)-1) * quantile
    i = math.floor(h)
    return ordered[i] if i == len(ordered)-1 else ordered[i] + (h-i)*(ordered[i+1]-ordered[i])


@dataclass(frozen=True)
class CandidateSelectionStatistics:
    candidate_id: str
    point_log_loss: float
    delta_log_loss_vs_A0: float
    ci025: float | None
    ci975: float | None
    eligible: bool


@dataclass(frozen=True)
class SelectionStatistics:
    status: str
    proposed_winner_id: str
    reason: str
    candidate_statistics: tuple[CandidateSelectionStatistics, ...]
    common_target_count: int
    caller_declared_full_target_count: int
    contributing_learner_ids: tuple[str, ...]
    zero_contribution_learner_ids: tuple[str, ...]
    conditional_single_learner: bool
    draws_sha256: str
    replicates: int
    seed: int
    rng_id: str
    quantile_id: str
    row_loss_id: str
    aggregation_id: str
    index_requests: int
    work_units: int
    elapsed_seconds: float
    required_candidate_ids: tuple[str, ...] = REQUIRED_CANDIDATE_IDS
    nine_candidate_admission_performed: bool = False
    external_freeze_authority: bool = False


def select_from_common_statistics(learners: tuple[LearnerCommonStatistics, ...], *,
                                  coverage: CommonPopulationCoverage,
                                  limits: SelectionKernelLimits) -> SelectionStatistics:
    """STATISTICS ONLY. Sums cannot prove row-key/label/phase or artifact authority.

    Zero-contribution learners belong in coverage, not the resampling clusters.
    Work units count point/weighted loss terms, index requests, denominator terms
    and delta subtractions, not CPU instructions or every hash/sort operation.
    Fixed 2000-replicate sorting/hashing is also bounded; no adaptive reduction.
    """
    started = _clock()
    _need(type(started) in (int, float) and math.isfinite(started), 'finite initial clock')
    _need(type(limits) is SelectionKernelLimits and type(coverage) is CommonPopulationCoverage, 'typed limits/coverage required')
    limits._validate(); coverage._validate()
    budget = _Budget(limits, started); budget.check()
    _need(type(learners) is tuple and learners, 'EMPTY_COMMON_POPULATION: no statistics or A0 decision')
    _need(len(learners) <= limits.max_learners and len(learners)+len(coverage.zero_contribution_learner_ids) <= limits.max_learners,
          'learner cap including zero-contribution coverage')
    _need(all(type(row) is LearnerCommonStatistics for row in learners), 'typed learner sufficient statistics required')
    for row in learners:
        row._validate()
    ids = tuple(sorted(row.learner_id for row in learners))
    _need(len(set(ids)) == len(ids) and not set(ids).intersection(coverage.zero_contribution_learner_ids),
          'duplicate or overlapping learner identities')
    rows = {row.learner_id:row for row in learners}
    counts = tuple(rows[i].common_target_count for i in ids)
    common = sum(counts); n = len(ids)
    _need(common <= limits.max_common_targets and coverage.full_target_count <= limits.max_full_targets
          and common + len(coverage.zero_contribution_learner_ids) <= coverage.full_target_count,
          'common/full/zero-contribution target coverage caps')
    planned_indexes = REPLICATES * n
    planned_work = 5*n + REPLICATES*(7*n+4) + 4
    _need(planned_indexes <= limits.max_index_requests and planned_work <= limits.max_work_units,
          'fixed2000 bootstrap exceeds index/work caps; no RNG started or R reduction')
    sums = {candidate:tuple(next(c.loss_sum for c in rows[i].candidates if c.candidate_id == candidate) for i in ids)
            for candidate in COMMON_MODEL_IDS}
    budget.check()
    point = {}
    for candidate in COMMON_MODEL_IDS:
        budget.work(n)
        point[candidate] = math.fsum(sums[candidate])/common
    point_deltas = {candidate:point[candidate]-point['A0'] for candidate in ELIGIBLE_GRAPH_IDS}; budget.work(4)
    rng = _make_rng(SEED)  # One private MT19937; global RNG/state untouched by call.
    draw_hash = hashlib.sha256()
    canonical = lambda value: json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')+b'\n'
    draw_hash.update(canonical(dict(algorithm=RNG_ID,seed=SEED,learners=list(ids),R=REPLICATES)))
    deltas = {candidate:[] for candidate in ELIGIBLE_GRAPH_IDS}
    for replicate in range(REPLICATES):
        budget.check(); multiplicities = [0]*n; draw = []
        for ordinal in range(n):
            if ordinal % 256 == 0: budget.check()
            index = rng.randrange(n)
            _need(type(index) is int and 0 <= index < n, 'RNG returned invalid cluster index')
            draw.append(index); multiplicities[index] += 1
            budget.index_requests += 1; budget.work()
            if budget.index_requests > limits.max_index_requests:
                raise SelectionLimitExceeded('index-request cap', budget.index_requests, budget.work_units, budget.last_elapsed)
        draw_hash.update(canonical(draw))
        denominator = sum(w*count for w,count in zip(multiplicities,counts)); budget.work(n)
        _need(denominator > 0, 'contributing clusters must never give zero denominator')
        sampled = {}
        for candidate in COMMON_MODEL_IDS:
            sampled[candidate] = math.fsum(w*loss for w,loss in zip(multiplicities,sums[candidate]))/denominator
            budget.work(n)
        for candidate in ELIGIBLE_GRAPH_IDS:
            value = sampled[candidate]-sampled['A0']
            _need(math.isfinite(value), 'nonfinite bootstrap contrast')
            deltas[candidate].append(value); budget.work()
    budget.check()
    statistics = [CandidateSelectionStatistics('A0',point['A0'],0.,None,None,False)]
    for candidate in ELIGIBLE_GRAPH_IDS:
        lower,upper = linear_percentile(deltas[candidate],.025),linear_percentile(deltas[candidate],.975)
        statistics.append(CandidateSelectionStatistics(candidate,point[candidate],point_deltas[candidate],lower,upper,upper < 0.))
    eligible = [row for row in statistics[1:] if row.eligible]
    winner = min(eligible,key=lambda row:(row.point_log_loss,row.candidate_id)).candidate_id if eligible else 'A0'
    _need(budget.index_requests == planned_indexes and budget.work_units == planned_work, 'complete deterministic work ledger')
    final_elapsed = budget.check()  # Includes quantiles and proposed-winner construction.
    return SelectionStatistics('STATISTICS_ONLY_NO_EXTERNAL_FREEZE',winner,
        'ELIGIBLE_GRAPH_MINIMUM_LL_STABLE_ID_TIE' if eligible else 'NO_GRAPH_UPPER975_LT_ZERO',tuple(statistics),
        common,coverage.full_target_count,ids,tuple(sorted(coverage.zero_contribution_learner_ids)),n == 1,
        draw_hash.hexdigest(),REPLICATES,SEED,RNG_ID,QUANTILE_ID,ROW_LOSS_ID,AGGREGATION_ID,
        budget.index_requests,budget.work_units,final_elapsed)
