"""Phase views Junyi80/10/10, tái dùng reader/vocabulary/windows hiện có.

Các view dữ liệu không cấp quyền training/refit/evaluation. Producer phải kiểm
authority, nguồn, resource và external freeze của từng phase trước thực thi.
"""
from collections.abc import Iterator
from dataclasses import dataclass, field
import hashlib
import json

from .config import DataPaths
from .encoding import ExerciseEncoding, fit_vocabulary
from .research_junyi_roles import JunyiResearchRoles
from .types import LearnerEvents, WindowRecord
from .windows import iter_windows

PHASE_ROLES = {
    'select_train80': ('train_users',),
    'raw_selection10': ('selection_users',),
    'refit_union90': ('train_users', 'selection_users'),
    'calibration_predict': ('calibration_users',),
}


def _need(condition, reason):
    if not condition:
        raise ValueError(reason)


def _hash(payload):
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()


@dataclass(frozen=True)
class JunyiPhaseView:
    roles: JunyiResearchRoles
    scope: str
    users: tuple[str, ...]
    expected_roles_identity: str
    identity: str = field(init=False)

    def __post_init__(self):
        _need(type(self.roles) is JunyiResearchRoles and self.scope in PHASE_ROLES, 'explicit Junyi role view required')
        _need(self.roles.outer_fold==4 and self.roles.seed==42, 'adopted Junyi fold4/seed42 required')
        _need(self.roles.identity==self.expected_roles_identity, 'frozen role identity mismatch')
        groups=[getattr(self.roles,name) for name in ('train_users','selection_users','calibration_users','outer_validation_users')]
        _need(all(type(group) is tuple and group and all(type(user) is str and user for user in group)
                  and len(set(group))==len(group) for group in groups),'unique nonempty role learners required')
        _need(sum(map(len,groups))==len(set().union(*groups)), 'role overlap')
        allowed=set().union(*(set(getattr(self.roles,name)) for name in PHASE_ROLES[self.scope]))
        _need(type(self.users) is tuple and self.users and len(set(self.users))==len(self.users)
              and set(self.users)<=allowed, 'phase learner scope mismatch')
        object.__setattr__(self,'identity',_hash(dict(roles=self.roles.identity,scope=self.scope,users=self.users)))

    @property
    def optimization(self):
        return self.scope in ('select_train80','refit_union90')

    @property
    def full_role_coverage(self):
        return set(self.users)==set().union(*(set(getattr(self.roles,name)) for name in PHASE_ROLES[self.scope]))


@dataclass(frozen=True)
class JunyiResearchEncoding:
    native: ExerciseEncoding
    fit_view: JunyiPhaseView
    identity: str = field(init=False)

    def _payload(self):
        return dict(fit_view=self.fit_view.identity,values=self.native.vocabulary.values,
                    support=self.native.train_support_students)

    def __post_init__(self):
        _need(type(self.native) is ExerciseEncoding and self.fit_view.optimization,'training-phase encoding required')
        object.__setattr__(self,'identity',_hash(self._payload()))

    def assert_for(self, view):
        _need(self.identity==_hash(self._payload()), 'encoding changed after fit')
        _need(self.fit_view.roles.identity==view.roles.identity,'encoding/split mismatch')
        expected='select_train80' if view.scope in ('select_train80','raw_selection10') else 'refit_union90'
        _need(self.fit_view.scope==expected,'encoding phase mismatch')
        if view.optimization:
            _need(self.fit_view.identity==view.identity,'optimizer and vocabulary cohorts differ')


def iter_junyi_phase_learners(paths: DataPaths, view: JunyiPhaseView, *, fetch_rows=50000,
                             temp_dir=None, stats=None) -> Iterator[LearnerEvents]:
    from .data import iter_development_learners
    _need(type(view) is JunyiPhaseView,'typed Junyi phase required')
    expected=set(view.users)
    seen=set()
    stream=iter_development_learners(paths,user_ids=view.users,allowed_folds=(0,1,2,3),
        fetch_rows=fetch_rows,temp_dir=temp_dir,preserve_user_order=True,stats=stats)
    for learner in stream:
        _need(learner.user_id in expected and learner.user_id not in seen and learner.fold in (0,1,2,3),
              'foreign/duplicate learner or outer fold exposure')
        _need(learner.events and all(event.user_id==learner.user_id and event.fold==learner.fold for event in learner.events),
              'event learner/fold mismatch')
        _need(all((left.time_done,left.source_row)<(right.time_done,right.source_row)
                  for left,right in zip(learner.events,learner.events[1:])), 'nonchronological events')
        seen.add(learner.user_id)
        yield learner
    _need(seen==expected,'incomplete phase learner coverage')


def fit_junyi_research_encoding(paths: DataPaths, view: JunyiPhaseView, **reader_options):
    _need(view.optimization,'selection/calibration cannot fit vocabulary')
    native=fit_vocabulary(iter_junyi_phase_learners(paths,view,**reader_options))
    return JunyiResearchEncoding(native,view)


def iter_junyi_research_windows(paths: DataPaths, view: JunyiPhaseView,
                               encoding: JunyiResearchEncoding, **reader_options) -> Iterator[WindowRecord]:
    encoding.assert_for(view)
    for learner in iter_junyi_phase_learners(paths,view,**reader_options):
        yield from iter_windows(learner,encoding.native,context=100,target_block=100,training=view.optimization)
    encoding.assert_for(view)
