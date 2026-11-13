"""Confidence Junyi trên dữ liệu giả, gồm solver Method24 CPU thật."""
from dataclasses import asdict,replace
from pathlib import Path
import hashlib
import json

import pytest

from knowledge_tracing.edge_confidence import EdgeConfidenceRecipe, EdgeRuntimeBinding
from knowledge_tracing.shared_kt import PrerequisiteGraph,StableVocabulary
from knowledge_tracing.akt.encoding import ExerciseEncoding
from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView,JunyiResearchEncoding
from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition,JunyiGraphPhaseSession
from knowledge_tracing.akt.research_junyi_roles import make_junyi_research_roles
from knowledge_tracing.akt.research_junyi_confidence import (
    iter_surrogate_rows,surrogate_fold_assignments,fit_child_confidence)
from knowledge_tracing.akt.types import KTEvent,LearnerEvents
from knowledge_tracing.akt.windows import iter_windows


@pytest.fixture
def recipe():
    return EdgeConfidenceRecipe('train-lagged-edge-confidence-v1',42,3,1.,5.,1.,1e-6,200,1e-6,200,20)


@pytest.fixture
def case():
    roles=make_junyi_research_roles([(str(i),i%5,'development') for i in range(100)])
    view=JunyiPhaseView(roles,'select_train80',roles.train_users,roles.identity)
    values=tuple(['A','B','C']+[f'fixture-{i:03d}' for i in range(714)])
    encoding=JunyiResearchEncoding(ExerciseEncoding(StableVocabulary(values),{item:1 for item in values}),view)
    graph=PrerequisiteGraph.from_edges(tuple(sorted((*values,'UNFIT'))),(('A','C'),('B','C'),('UNFIT','C')))
    condition=JunyiGraphCondition(encoding,graph,'a'*64)
    return view,encoding,condition


def make_rows(case,*,users=None,size=12,flip_from=None,items=None):
    view,encoding,condition=case
    users=users or view.users[:1]
    windows=[]
    for index,user in enumerate(users):
        events=[]
        for rank in range(size):
            label=(rank+index)%2
            if flip_from is not None and rank>=flip_from:
                label=1-label
            events.append(KTEvent(user,items[rank] if items else ('A','B','C')[rank%3],
                rank+1,index*10000+rank+1,label,0,0))
        windows.extend(iter_windows(LearnerEvents(user,0,tuple(events)),encoding.native,training=True))
    session=JunyiGraphPhaseSession(condition,view)
    return tuple(iter_surrogate_rows(windows,session,max_targets=10000,max_windows=1000,max_seconds=30))


def test_717_exercises_and_declared_unsupported_parent_are_preserved(case):
    rows=make_rows(case)
    assert len(case[1].native.vocabulary.values)==717
    child=next(row for row in rows if row.child_id=='C')
    assert child.parents==(('A',1,0),('B',1,1),('UNFIT',0,0))
    assert len(child.base)==4


def test_current_and_future_labels_do_not_change_earlier_features(case):
    original=make_rows(case,size=260)
    changed=make_rows(case,size=260,flip_from=150)
    assert len(original)==len(changed)==260
    for before,after in zip(original[:151],changed[:151]):
        assert (before.base,before.parents)==(after.base,after.parents)
    assert original[150].correct!=changed[150].correct
    assert original[151].base!=changed[151].base


def test_oov_resets_parent_evidence(case):
    rows=make_rows(case,size=3,items=('A','OOV','C'))
    assert len(rows)==2
    assert rows[-1].parents==(('A',0,0),('B',0,0),('UNFIT',0,0))
    assert rows[-1].base==(.5,0.,.5,0.)


def test_rollover_uses_native_window_not_full_history(case):
    items=('A',)+('B','C')*260
    rows=make_rows(case,size=len(items),items=items)
    later=next(row for row in rows if row.child_id=='C' and row.global_rank>300)
    assert later.parents[0]==('A',0,0)
    assert later.base[3]<=199/204


def test_folds_are_stable_balanced_and_disjoint_by_learner(case,recipe):
    view=case[0]
    first=surrogate_fold_assignments(view,recipe)
    assert first==surrogate_fold_assignments(view,recipe)
    assert {user for user,_ in first}==set(view.users)
    counts=[sum(f==fold for _,f in first) for fold in range(3)]
    assert max(counts)-min(counts)<=1
    selection=JunyiPhaseView(view.roles,'raw_selection10',view.roles.selection_users,view.roles.identity)
    with pytest.raises(ValueError,match='TRAIN80'):
        surrogate_fold_assignments(selection,recipe)


def test_preparation_rejects_duplicate_targets_and_caps(case):
    view,encoding,condition=case
    user=view.users[0]
    learner=LearnerEvents(user,0,tuple(KTEvent(user,'A',rank+1,rank+1,rank%2,0,0) for rank in range(3)))
    windows=tuple(iter_windows(learner,encoding.native,training=True))
    session=JunyiGraphPhaseSession(condition,view)
    with pytest.raises(ValueError,match='target cap'):
        tuple(iter_surrogate_rows(windows,session,max_targets=2,max_windows=10,max_seconds=30))
    with pytest.raises(ValueError,match='Duplicate'):
        tuple(iter_surrogate_rows((*windows,*windows),session,max_targets=10,max_windows=10,max_seconds=30))


def test_actual_crossfit_keeps_unsupported_null_and_no_oracle(case,recipe,tmp_path):
    import numpy
    import sklearn
    source=Path(__file__).resolve().parents[2]/'src/knowledge_tracing/edge_confidence.py'
    runtime=EdgeRuntimeBinding(sklearn.__version__,numpy.__version__,'b'*64,
        hashlib.sha256(source.read_bytes()).hexdigest())
    rows=tuple(row for row in make_rows(case,users=case[0].users,size=30) if row.child_id=='C')
    result=fit_child_confidence(rows,child='C',parents=('A','B','UNFIT'),view=case[0],
        recipe=recipe,runtime=runtime,max_rows=1000,max_fits=12,max_seconds=30)
    assert len(result['fit_ledger'])==12
    assert len(result['oof'])==len(rows)*3
    assert result['train_view_identity']==case[0].identity
    unseen=next(edge for edge in result['edges'] if edge.parent_id=='UNFIT')
    assert unseen.supported is False and unseen.confidence is None and unseen.reason
    assert unseen.eligible_targets==0
    folds=dict(surrogate_fold_assignments(case[0],recipe))
    for row in result['oof']:
        assert folds[row.learner_id]==row.heldout_fold
    for record in result['fit_ledger']:
        expected=[(row.learner_id,row.source_row) for row in rows
                  if folds[row.learner_id]!=record['heldout_fold']]
        from knowledge_tracing.akt.research_junyi_confidence import _digest
        assert record['training_rows_sha256']==_digest(expected)
        assert record['training_targets']==len(expected)
    for edge in result['edges']:
        if edge.supported:
            assert edge.confidence==edge.bootstrap_positive/200
            assert len(edge.learner_deltas)>=20
    (tmp_path/'crossfit-summary.json').write_text(json.dumps(dict(
        scope='SYNTHETIC_CONFIDENCE_CPU_ONLY',targets=len(rows),learners=len(case[0].users),
        feature_recipe=result['feature_recipe'],fold_recipe=result['fold_recipe'],
        edges=[asdict(edge) for edge in result['edges']],fit_ledger=result['fit_ledger'],
        oof_rows=len(result['oof']),train_view_identity=result['train_view_identity']),
        ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def test_child_fit_rejects_foreign_learner_and_bad_features(case,recipe):
    row=next(row for row in make_rows(case) if row.child_id=='C')
    for change in [dict(learner_id='OUTSIDE_TRAIN80'),dict(base=(.5,.5,.5,float('nan'))),
                   dict(correct=True),dict(source_row=0),dict(global_rank=-1)]:
        with pytest.raises(ValueError):
            fit_child_confidence([replace(row,**change)],child='C',parents=('A','B','UNFIT'),
                view=case[0],recipe=recipe,runtime=None,max_rows=10,max_fits=12,max_seconds=30)
