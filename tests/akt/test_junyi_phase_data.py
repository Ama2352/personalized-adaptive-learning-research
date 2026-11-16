"""Kiểm ranh giới role/encoding/causal windows của adapter Junyi, không NN."""
from dataclasses import replace
from pathlib import Path
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from knowledge_tracing.akt.config import DataPaths
from knowledge_tracing.akt.research_junyi_roles import make_junyi_research_roles
from knowledge_tracing.akt.research_junyi_data import (
    JunyiPhaseView, fit_junyi_research_encoding, iter_junyi_phase_learners, iter_junyi_research_windows)
from knowledge_tracing.akt.types import KTEvent,LearnerEvents,TrainingWindow,UnseenTarget,WindowInputs


@pytest.fixture
def case():
    roles=make_junyi_research_roles([(str(i),i%5,'development') for i in range(40)])
    def view(scope,users):return JunyiPhaseView(roles,scope,tuple(users),roles.identity)
    train=view('select_train80',roles.train_users[:2])
    selection=view('raw_selection10',roles.selection_users[:1])
    calibration=view('calibration_predict',roles.calibration_users[:1])
    refit=view('refit_union90',(*train.users,*selection.users))
    paths=DataPaths(*(Path('unused') for _ in range(4)))
    def learner(user,items=('A','B','A')):
        return LearnerEvents(user,0,tuple(KTEvent(user,item,100+i,i+1,i%2,0,0) for i,item in enumerate(items)))
    def stream(_paths,*,user_ids,**kwargs):return iter(learner(user) for user in user_ids)
    return roles,view,train,selection,calibration,refit,paths,learner,stream


def test_phase_rejects_cross_role_and_outer_validation(case):
    roles,view,*_=case
    for scope,user in [('select_train80',roles.selection_users[0]),
                       ('raw_selection10',roles.calibration_users[0]),
                       ('calibration_predict',roles.train_users[0]),
                       ('select_train80',roles.outer_validation_users[0])]:
        with pytest.raises(ValueError,match='scope'):view(scope,[user])


def test_wrong_role_identity_or_unsupported_phase_rejected(case):
    roles,view,*_=case
    with pytest.raises(ValueError,match='identity'):
        JunyiPhaseView(roles,'select_train80',roles.train_users,'0'*64)
    with pytest.raises(ValueError,match='view'):
        view('holdout',roles.outer_validation_users)


def test_overlapping_roles_are_rejected(case):
    roles,*_=case
    bad=replace(roles,selection_users=(roles.train_users[0],))
    with pytest.raises(ValueError,match='overlap'):
        JunyiPhaseView(bad,'select_train80',bad.train_users,bad.identity)


def test_vocab_fit_is_train_only_and_prediction_has_no_loss_labels(case):
    roles,view,train,selection,calibration,refit,paths,learner,stream=case
    with patch('knowledge_tracing.akt.data.iter_development_learners',side_effect=stream) as reader:
        encoding=fit_junyi_research_encoding(paths,train)
        assert encoding.native.vocabulary.values==('A','B')
        assert all(value==2 for value in encoding.native.train_support_students.values())
        assert all(isinstance(row,TrainingWindow) for row in iter_junyi_research_windows(paths,train,encoding))
        assert all(isinstance(row,WindowInputs) for row in iter_junyi_research_windows(paths,selection,encoding))
        assert all(call.kwargs['allowed_folds']==(0,1,2,3) for call in reader.call_args_list)
        with pytest.raises(ValueError,match='vocabulary'):
            fit_junyi_research_encoding(paths,selection)


def test_calibration_requires_refit_encoding(case):
    roles,view,train,selection,calibration,refit,paths,learner,stream=case
    with patch('knowledge_tracing.akt.data.iter_development_learners',side_effect=stream):
        selected_encoding=fit_junyi_research_encoding(paths,train)
        with pytest.raises(ValueError,match='phase'):
            list(iter_junyi_research_windows(paths,calibration,selected_encoding))
        refit_encoding=fit_junyi_research_encoding(paths,refit)
        assert list(iter_junyi_research_windows(paths,calibration,refit_encoding))
        with pytest.raises(ValueError,match='phase'):
            list(iter_junyi_research_windows(paths,selection,refit_encoding))


def test_changed_encoding_and_optimizer_cohort_rejected(case):
    roles,view,train,selection,calibration,refit,paths,learner,stream=case
    with patch('knowledge_tracing.akt.data.iter_development_learners',side_effect=stream):
        encoding=fit_junyi_research_encoding(paths,train)
        with pytest.raises(ValueError,match='cohorts'):
            list(iter_junyi_research_windows(paths,view('select_train80',train.users[:1]),encoding))
        encoding.native.train_support_students['A']=999
        with pytest.raises(ValueError,match='changed'):
            list(iter_junyi_research_windows(paths,selection,encoding))


def test_oov_remains_unsupported(case):
    roles,view,train,selection,calibration,refit,paths,learner,stream=case
    with patch('knowledge_tracing.akt.data.iter_development_learners',side_effect=stream):
        encoding=fit_junyi_research_encoding(paths,train)
    with patch('knowledge_tracing.akt.data.iter_development_learners',return_value=iter([learner(selection.users[0],('C','A','B'))])):
        windows=list(iter_junyi_research_windows(paths,selection,encoding))
        assert isinstance(windows[0],UnseenTarget)
        assert windows[1].context_reset.all()
        assert windows[1].inputs.prior_responses[0]==-1


@pytest.mark.parametrize('mode',['foreign','duplicate','missing','outer_fold','reverse'])
def test_bad_reader_stream_rejected(case,mode):
    roles,view,train,selection,calibration,refit,paths,learner,stream=case
    row=learner(train.users[0]);other=learner(train.users[1])
    rows={'foreign':[learner('foreign')],'duplicate':[row,row], 'missing':[row],
          'outer_fold':[replace(row,fold=4)],'reverse':[replace(row,events=tuple(reversed(row.events))),other]}[mode]
    with patch('knowledge_tracing.akt.data.iter_development_learners',return_value=iter(rows)):
        with pytest.raises(ValueError):list(iter_junyi_phase_learners(paths,train))


def test_bounded_cohort_is_not_labeled_full_role(case):
    roles,view,train,*_=case
    assert not train.full_role_coverage
    assert view('select_train80',roles.train_users).full_role_coverage


def test_outer_view_is_read_only_and_rejects_inner_learners(case):
    roles,view,*_=case
    outer=view('outer_evaluation',roles.outer_validation_users)
    assert outer.full_role_coverage and not outer.optimization
    assert outer.allowed_folds==(4,)
    for user in (*roles.train_users,*roles.selection_users,*roles.calibration_users):
        with pytest.raises(ValueError,match='scope'):
            view('outer_evaluation',[user])
    with pytest.raises(ValueError,match='vocabulary'):
        fit_junyi_research_encoding(None,outer)


def test_outer_reader_uses_only_fold4_and_refit90_encoding(case):
    roles,view,train,selection,calibration,refit,paths,learner,stream=case
    outer=view('outer_evaluation',roles.outer_validation_users[:1])
    with patch('knowledge_tracing.akt.data.iter_development_learners',side_effect=stream):
        train_encoding=fit_junyi_research_encoding(paths,train)
        refit_encoding=fit_junyi_research_encoding(paths,refit)
    with pytest.raises(ValueError,match='phase'):
        list(iter_junyi_research_windows(paths,outer,train_encoding))
    row=learner(outer.users[0])
    row=replace(row,fold=4,events=tuple(replace(event,fold=4) for event in row.events))
    with patch('knowledge_tracing.akt.data.iter_development_learners',return_value=iter([row])) as reader:
        windows=list(iter_junyi_research_windows(paths,outer,refit_encoding))
    assert windows and all(isinstance(window,WindowInputs) for window in windows)
    assert reader.call_args.kwargs['allowed_folds']==(4,)


@pytest.mark.parametrize('mode',['inner_fold','mixed_event_fold','wrong_user','missing'])
def test_outer_reader_rejects_foreign_or_incomplete_stream(case,mode):
    roles,view,train,selection,calibration,refit,paths,learner,stream=case
    outer=view('outer_evaluation',roles.outer_validation_users[:1])
    row=learner(outer.users[0])
    row=replace(row,fold=4,events=tuple(replace(event,fold=4) for event in row.events))
    rows={'inner_fold':[replace(row,fold=0)],
          'mixed_event_fold':[replace(row,events=(replace(row.events[0],fold=0),*row.events[1:]))],
          'wrong_user':[learner(train.users[0])], 'missing':[]}[mode]
    with patch('knowledge_tracing.akt.data.iter_development_learners',return_value=iter(rows)):
        with pytest.raises(ValueError):
            list(iter_junyi_phase_learners(paths,outer))


def test_outer_evaluation_cannot_reuse_engineering_cohort_cache(case):
    roles,view,*_=case
    outer=view('outer_evaluation',roles.outer_validation_users[:1])
    with pytest.raises(ValueError,match='engineering cohort'):
        list(iter_junyi_phase_learners(None,outer,cache_root=Path('unused')))


@pytest.mark.parametrize('field,value', [('expected_roles_identity','0'*64),
                                       ('identity','0'*64),('scope','select_train80')])
def test_outer_content_drift_rejected_before_reader_access(case,field,value):
    roles,view,*_=case
    outer=view('outer_evaluation',roles.outer_validation_users[:1])
    object.__setattr__(outer,field,value)
    with patch('knowledge_tracing.akt.data.iter_development_learners') as reader:
        with pytest.raises(ValueError,match='identity'):
            list(iter_junyi_phase_learners(None,outer))
        reader.assert_not_called()
