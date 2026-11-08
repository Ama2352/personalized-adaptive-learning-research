"""GRAPH12/13: pure main-nine consistency accumulator; NOT_FILE_ADMISSION.

Caller must verify actual files/terminal authority separately. Typed claims,
SHA-shaped fields and this result never grant external freeze/refit permission.
No I/O, parser, corpus/model callback, winner, optimizer or freeze operation.
Required main selected-only producer is not the existing A0 auto-refit pilot.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import time

from .research_selection import (REQUIRED_CANDIDATE_IDS, COMMON_MODEL_IDS,
    CandidateLossSum, LearnerCommonStatistics, CommonPopulationCoverage, binary_row_log_loss)

PROTOCOL21='c0d6e8a698d7d5083986e9848898a643390fc5e76100fc0b8c6286c306e6bea6'
RECIPE26='13a81ad6a5173e1f215e3df01f3917fcbc1cce128c87c93985b57af76faa353a'
ALLOCATION='e939d24e35b66e7da19751fb51e8f9fd696a2aca50442d421c7f3188729644a5'
HISTORY_SCHEME='observable-prefix-chain-v1'
POPULATION_SCHEME='model-neutral-selection-K-y-jsonl-v1'
TERMINAL_KIND='MAIN_SELECTED_ONLY_CANDIDATE_V1'
_clock=time.perf_counter


def _need(ok,message):
    if not ok:raise ValueError(message)


def _sha(value):
    _need(type(value) is str and len(value)==64 and all(c in '0123456789abcdef' for c in value),'lowercase SHA256 required')


def _integer(value,upper,zero=False):
    _need(type(value) is int and (0 if zero else 1)<=value<=upper,'bounded exact integer required')


def _name(value):
    _need(type(value) is str and 0<len(value)<=256 and value==value.strip()
          and not any(ord(c)<32 for c in value),'bounded nonempty identity required')


def _canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')+b'\n'


@dataclass(frozen=True)
class MainSelectionContext:
    environment_id: str
    protocol21_sha256: str
    recipe26_sha256: str
    allocation_sha256: str
    domain_sha256: str
    bank_sha256: str
    split_sha256: str
    train_role_sha256: str
    selection_role_sha256: str

    def validate(self):
        _need(type(self.environment_id) is str and self.environment_id in ('grade10_simulator','junyi_development_outer_fold4'),'one frozen environment required')
        for name,value in asdict(self).items():
            if name!='environment_id':_sha(value)
        _need((self.protocol21_sha256,self.recipe26_sha256,self.allocation_sha256)==(PROTOCOL21,RECIPE26,ALLOCATION),
              'adopted protocol/recipe/allocation required')
        _need(self.train_role_sha256!=self.selection_role_sha256,'distinct train/selection roles required')

    def __post_init__(self):self.validate()


@dataclass(frozen=True)
class ArtifactClaim:
    """Declared bytes/SHA only; not proof a file exists or was verified."""
    sha256: str
    size_bytes: int

    def __post_init__(self):
        _sha(self.sha256);_integer(self.size_bytes,2**40)


@dataclass(frozen=True)
class SelectedCandidateClaim:
    candidate_id: str
    context: MainSelectionContext
    terminal_kind: str
    status: str
    weights_phase: str
    prediction_phase: str
    encoding_fit_scope: str
    selected_epoch: int
    complete_fit_epochs: int
    terminal: ArtifactClaim
    checkpoint: ArtifactClaim
    raw_predictions: ArtifactClaim
    targets: ArtifactClaim
    coverage: ArtifactClaim
    stage_journal_sha256: str
    config_sha256: str
    sources_sha256: str
    runtime_sha256: str
    phase_sha256: str
    encoding_sha256: str
    vocabulary_sha256: str
    initial_model_sha256: str
    initial_backbone_sha256: str | None
    graph_condition_sha256: str | None
    graph_train_role_sha256: str | None
    estimator_graph: str
    epoch_objective_id: str
    full_targets: int
    supported_targets: int
    unsupported_counts: tuple[tuple[str,int],...]
    refit_started: bool
    calibration_used_for_selection: bool

    def validate(self):
        _need(type(self.candidate_id) is str and self.candidate_id in REQUIRED_CANDIDATE_IDS,'fixed main candidate ID required')
        _need(type(self.context) is MainSelectionContext,'typed environment context required');self.context.validate()
        _need((self.terminal_kind,self.status,self.weights_phase,self.prediction_phase,self.encoding_fit_scope)==
              (TERMINAL_KIND,'SELECTED_ONLY_COMPLETE','selected_fit80','raw_selection10','select_train80'),
              'main selected-only claims only; no pilot/refit/calibrated/engineering promotion')
        _need(self.refit_started is False and self.calibration_used_for_selection is False,'selected-only ordering/leakage claim required')
        _integer(self.selected_epoch,10**6);_integer(self.complete_fit_epochs,10**6)
        _need(self.selected_epoch<=self.complete_fit_epochs,'selected epoch must be complete')
        for name in ('terminal','checkpoint','raw_predictions','targets','coverage'):
            value=getattr(self,name);_need(type(value) is ArtifactClaim,'typed artifact claims required');value.__post_init__()
        for name in ('stage_journal_sha256','config_sha256','sources_sha256','runtime_sha256','phase_sha256',
                     'encoding_sha256','vocabulary_sha256','initial_model_sha256'):_sha(getattr(self,name))
        _name(self.epoch_objective_id)
        is_akt=self.candidate_id.startswith(('A0','A1_','A2_','A3_'))
        if is_akt:_sha(self.initial_backbone_sha256)
        else:_need(self.initial_backbone_sha256 is None,'do not equate SAKT/GKT to AKT backbone')
        if self.candidate_id not in ('A0','SAKT'):
            _sha(self.graph_condition_sha256)
            _need(self.graph_train_role_sha256==self.context.train_role_sha256,'graph condition remains TRAIN80 bound')
        else:_need(self.graph_condition_sha256 is None and self.graph_train_role_sha256 is None,'graph-disabled candidate claim required')
        expected_graph='disabled' if self.candidate_id in ('A0','SAKT') else ('learned' if self.candidate_id.endswith('_LEARNED') else 'expert')
        _need(type(self.estimator_graph) is str and self.estimator_graph==expected_graph,'candidate/estimator graph kind mismatch')
        _integer(self.full_targets,10**9);_integer(self.supported_targets,self.full_targets,zero=True)
        _need(type(self.unsupported_counts) is tuple and len(self.unsupported_counts)<=128,'bounded unsupported-reason counts')
        seen=set();total=0
        for row in self.unsupported_counts:
            _need(type(row) is tuple and len(row)==2,'reason/count pair required')
            reason,count=row;_name(reason);_need(reason!='supported' and reason not in seen,'unique unsupported reason required')
            _integer(count,self.full_targets);seen.add(reason);total+=count
        _need(total+self.supported_targets==self.full_targets,'full/supported/unsupported coverage claims disagree')

    def __post_init__(self):self.validate()


@dataclass(frozen=True,order=True)
class ModelNeutralKey:
    learner_id: str
    item_id: str
    timestamp: int
    source_row: int
    global_rank: int
    history_hash_scheme: str
    history_sha256: str
    origin_role: str

    def validate(self):
        _name(self.learner_id);_name(self.item_id)
        for n in ('timestamp','source_row','global_rank'):_integer(getattr(self,n),2**63-1,zero=True)
        _need(self.history_hash_scheme==HISTORY_SCHEME and self.origin_role=='selection','selection/model-neutral observable prefix required')
        _sha(self.history_sha256)

    def __post_init__(self):self.validate()

    def values(self):return tuple(getattr(self,name) for name in self.__dataclass_fields__)


@dataclass(frozen=True)
class RawSelectedRow:
    candidate_id: str
    key: ModelNeutralKey
    correct: int
    probability: float | None
    support_reason: str
    phase_scope: str
    phase_sha256: str
    encoding_sha256: str

    def validate(self):
        _need(type(self.candidate_id) is str and self.candidate_id in REQUIRED_CANDIDATE_IDS,'fixed raw-row candidate ID required')
        _need(type(self.key) is ModelNeutralKey,'typed model-neutral key required');self.key.validate()
        _need(type(self.correct) is int and self.correct in (0,1),'exact binary label required')
        _need(self.phase_scope=='raw_selection10','postrefit/calibration row forbidden')
        _sha(self.phase_sha256);_sha(self.encoding_sha256);_name(self.support_reason)
        if self.probability is None:_need(self.support_reason!='supported','null needs explicit unsupported reason')
        else:
            _need(type(self.probability) is float and math.isfinite(self.probability) and 0<=self.probability<=1
                  and self.support_reason=='supported','raw binary64 probability/support mismatch')

    def __post_init__(self):self.validate()


@dataclass(frozen=True)
class PopulationExpectation:
    context: MainSelectionContext
    full_targets: int
    full_keys_sha256: str
    full_keys_labels_sha256: str
    scheme: str=POPULATION_SCHEME

    def __post_init__(self):
        _need(type(self.context) is MainSelectionContext,'typed context required');self.context.validate()
        _integer(self.full_targets,10**9);_sha(self.full_keys_sha256);_sha(self.full_keys_labels_sha256)
        _need(self.scheme==POPULATION_SCHEME,'do not relabel existing coverage population SHA')


@dataclass(frozen=True)
class AdmissionLimits:
    max_learners: int
    max_rows: int
    max_rows_per_learner: int
    max_row_checks: int
    max_seconds: float

    def __post_init__(self):
        _integer(self.max_learners,100000);_integer(self.max_rows,10**9)
        _integer(self.max_rows_per_learner,100000);_integer(self.max_row_checks,9*10**9)
        _need(type(self.max_seconds) in (int,float) and math.isfinite(self.max_seconds) and 0<self.max_seconds<=120,
              'explicit cooperative time cap required')


@dataclass(frozen=True)
class LearnerCoverage:
    learner_id: str
    full_targets: int
    common_targets: int
    supported_by_candidate: tuple[tuple[str,int],...]


@dataclass(frozen=True)
class CandidateCoverage:
    candidate_id: str
    full_targets: int
    supported_targets: int
    unsupported_counts: tuple[tuple[str,int],...]


@dataclass(frozen=True)
class MainAdmissionStatistics:
    status: str
    context: MainSelectionContext
    common_statistics: tuple[LearnerCommonStatistics,...]
    common_population_coverage: CommonPopulationCoverage
    learner_coverage: tuple[LearnerCoverage,...]
    candidate_coverage: tuple[CandidateCoverage,...]
    full_keys_sha256: str
    full_keys_labels_sha256: str
    common_keys_sha256: str
    candidate_claims_sha256: str
    full_targets: int
    common_targets: int
    row_checks: int
    elapsed_seconds: float
    artifact_bytes_verified: bool=False
    nine_terminal_files_admitted: bool=False
    external_freeze_authority: bool=False


class MainAdmissionAccumulator:
    """Explicit claims -> exact-nine row groups -> statistics, never FROZEN/refit.

    Any failed operation poisons this accumulator; no retry/partial-stat result.
    Only current learner's five loss lists are buffered, then fsum once. This
    avoids nine full tables without inventing a different summation algorithm.
    Caller supplies inert records, not I/O/model iterators or callbacks.
    """
    def __init__(self,expectation,limits):
        _need(type(expectation) is PopulationExpectation and type(limits) is AdmissionLimits,'typed expectation/limits')
        expectation.__post_init__();limits.__post_init__()
        _need(expectation.full_targets<=limits.max_rows and 9*expectation.full_targets<=limits.max_row_checks,'declared row/work cap')
        self.expectation,self.limits=expectation,limits
        self.stage='CANDIDATE_CLAIMS';self.started=_clock();self.last_elapsed=0.
        self.claims={};self.previous=None;self.full=0;self.common=0;self.checks=0
        self.full_hash=hashlib.sha256();self.label_hash=hashlib.sha256();self.common_hash=hashlib.sha256()
        self.supported={c:0 for c in REQUIRED_CANDIDATE_IDS};self.unsupported={c:{} for c in REQUIRED_CANDIDATE_IDS}
        self.statistics=[];self.coverage=[];self.zero=[];self.current=None
        self._clock_check()

    def _clock_check(self):
        now=_clock()
        _need(type(now) in (int,float) and math.isfinite(now) and type(self.started) in (int,float)
              and math.isfinite(self.started),'finite clock required')
        elapsed=now-self.started
        _need(self.last_elapsed<=elapsed<=self.limits.max_seconds,'cooperative admission deadline/clock exceeded')
        self.last_elapsed=elapsed
        return elapsed

    def _guard(self,stage):
        _need(self.stage==stage,'wrong/failed/terminal admission state');self._clock_check()

    def add_candidate(self,claim):
        try:
            self._guard('CANDIDATE_CLAIMS');_need(type(claim) is SelectedCandidateClaim,'typed selected-only claim required');claim.validate()
            _need(claim.context==self.expectation.context and claim.full_targets==self.expectation.full_targets,'foreign environment/population claim')
            _need(claim.candidate_id not in self.claims,'duplicate candidate claim')
            self.claims[claim.candidate_id]=claim;self._clock_check()
        except BaseException:self.stage='FAILED';raise

    def seal_candidate_claims(self):
        try:
            self._guard('CANDIDATE_CLAIMS')
            _need(set(self.claims)==set(REQUIRED_CANDIDATE_IDS),'all nine selected-only claims required before any rows')
            backbones={self.claims[c].initial_backbone_sha256 for c in REQUIRED_CANDIDATE_IDS if c.startswith('A')}
            _need(len(backbones)==1,'A0-A3 shared initial backbone claim mismatch')
            self.claims_digest=hashlib.sha256(_canonical([asdict(self.claims[c]) for c in REQUIRED_CANDIDATE_IDS])).hexdigest()
            self._clock_check();self.stage='SYNCHRONIZED_ROWS'
        except BaseException:self.stage='FAILED';raise

    def _finish_learner(self):
        if self.current is None:return
        cur=self.current
        self.coverage.append(LearnerCoverage(cur['id'],cur['full'],cur['common'],tuple((c,cur['supported'][c]) for c in REQUIRED_CANDIDATE_IDS)))
        if cur['common']:
            sums=tuple(CandidateLossSum(c,cur['common'],math.fsum(cur['losses'][c])) for c in COMMON_MODEL_IDS)
            self.statistics.append(LearnerCommonStatistics(cur['id'],cur['common'],sums))
        else:self.zero.append(cur['id'])
        _need(len(self.coverage)<=self.limits.max_learners,'learner coverage cap')
        self.current=None

    def add_row_group(self,rows):
        try:
            self._guard('SYNCHRONIZED_ROWS')
            _need(type(rows) is tuple and len(rows)==9 and all(type(r) is RawSelectedRow for r in rows),'one exact-nine typed row group')
            _need(tuple(r.candidate_id for r in rows)==REQUIRED_CANDIDATE_IDS,'candidate order/omission/duplicate row')
            for row in rows:
                row.validate();claim=self.claims[row.candidate_id]
                _need(row.phase_sha256==claim.phase_sha256 and row.encoding_sha256==claim.encoding_sha256,'model-specific phase/encoding provenance mismatch')
            first=rows[0];key=first.key
            _need(all(r.key==key and r.correct==first.correct for r in rows),'all nine K/y must match')
            _need(self.previous is None or self.previous<key,'strict canonical K order; duplicate/reordered targets forbidden')
            _need(self.full<self.expectation.full_targets and self.checks+9<=self.limits.max_row_checks,'row/work cap')
            if self.current is None or self.current['id']!=key.learner_id:
                self._finish_learner()
                _need(len(self.coverage)<self.limits.max_learners,'new learner cap')
                self.current=dict(id=key.learner_id,full=0,common=0,supported={c:0 for c in REQUIRED_CANDIDATE_IDS},losses={c:[] for c in COMMON_MODEL_IDS})
            _need(self.current['full']<self.limits.max_rows_per_learner,'bounded per-learner loss buffer')
            common=all(rows[REQUIRED_CANDIDATE_IDS.index(c)].probability is not None for c in COMMON_MODEL_IDS)
            for row in rows:
                c=row.candidate_id
                if row.probability is None:
                    reasons=self.unsupported[c];reasons[row.support_reason]=reasons.get(row.support_reason,0)+1
                    _need(len(reasons)<=128,'unsupported reason vocabulary cap')
                else:self.supported[c]+=1;self.current['supported'][c]+=1
                if common and c in COMMON_MODEL_IDS:self.current['losses'][c].append(binary_row_log_loss(row.probability,row.correct))
            raw=key.values();self.full_hash.update(_canonical(raw));self.label_hash.update(_canonical((raw,first.correct)))
            if common:self.common+=1;self.current['common']+=1;self.common_hash.update(_canonical(raw))
            self.current['full']+=1;self.full+=1;self.checks+=9;self.previous=key;self._clock_check()
        except BaseException:self.stage='FAILED';raise

    def finish(self):
        try:
            self._guard('SYNCHRONIZED_ROWS');self._finish_learner()
            _need(self.full==self.expectation.full_targets and self.full_hash.hexdigest()==self.expectation.full_keys_sha256
                  and self.label_hash.hexdigest()==self.expectation.full_keys_labels_sha256,'full canonical F/K/y admission mismatch')
            for c,claim in self.claims.items():
                _need(self.supported[c]==claim.supported_targets and self.unsupported[c]==dict(claim.unsupported_counts),'actual stream coverage vs terminal claim mismatch')
            _need(self.common>0 and self.statistics,'EMPTY_COMMON_POPULATION: inconclusive, no A0/freeze decision')
            result=MainAdmissionStatistics('NOT_FILE_ADMISSION_STATISTICS_ONLY',self.expectation.context,tuple(self.statistics),
                CommonPopulationCoverage(self.full,tuple(self.zero)),tuple(self.coverage),
                tuple(CandidateCoverage(c,self.full,self.supported[c],tuple(sorted(self.unsupported[c].items()))) for c in REQUIRED_CANDIDATE_IDS),
                self.full_hash.hexdigest(),
                self.label_hash.hexdigest(),self.common_hash.hexdigest(),self.claims_digest,self.full,self.common,self.checks,self._clock_check())
            self._clock_check();self.stage='STATISTICS_ONLY_COMPLETE'
            return result
        except BaseException:self.stage='FAILED';raise
