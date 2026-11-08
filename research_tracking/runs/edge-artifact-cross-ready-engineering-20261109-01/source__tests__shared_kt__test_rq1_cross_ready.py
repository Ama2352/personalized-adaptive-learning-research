"""Pure synthetic joins/set arithmetic; không mở sourcebundle hoặc model."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

PATH=Path(__file__).resolve().parents[2]/'scripts/research/analyze_rq1_cross_ready.py'
SPEC=importlib.util.spec_from_file_location('rq1_cross_ready_pure',PATH)
a=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(a)


def fixture():
    legacy=[];side=[]
    for variant in a.VARIANTS:
        full=variant=='graph_package';cid='B' if full else 'C'
        row=dict(variant=variant,learner_id='20000-PG',event_id='0',correct=1,probability=.4,
            mastery={'A':.6 if full else .4,'B':.2,'C':.3},mastered=['A'] if full else [],ready=['A',cid],action=cid)
        meta=dict(variant=variant,learner_id='20000-PG',event_id='0',seed=20000,profile='PG',
            correct=1,probability=.4,legacy_row_sha256=a.row_sha(row),preview_is_served=False,
            preview_timestamp_argument=None,preview_capture_phase='after_native_preview_select',
            query_capture_phase='before_delegate_predict',update_pairing_verified=True,phases=list(a.PHASES),
            query=dict(concept='A',question='logged',difficulty=1050.,timestamp_iso='2026-01-01T00:00:00+00:00',timestamp_ns=0),
            preview=dict(concept=cid,question='Q'+cid,difficulty=1050.))
        legacy.append(row);side.append(meta)
    flag=dict(seed=20000,profile='PG',event_id='0',learner_id='20000-PG',P_changed=False,S_event_changed=True,
        S_concept_pairs_changed=1,M_event_changed=True,M_concept_crossings=1,R_event_changed=True,
        R_membership_symmetric_difference=2,preview_concept_changed=True,preview_question_changed=True,
        preview_difficulty_changed=False,full_preview_tuple_changed=True)
    return legacy,side,[flag]


def calculate(records):
    return a.paired_events(*records,expected_keys={(20000,'PG',0)},node_count=3)


def test_known_sets_and_neither_winner_cross_membership():
    row=calculate(fixture())[0]
    assert row['M_added']==['A'] and row['M_removed']==[]
    assert row['R_added']==['B'] and row['R_removed']==['C'] and row['R_intersection']==['A']
    assert row['MRA_signature']=='111' and row['membership_signature']=='1100'
    assert row['membership_category']=='NEITHER_WINNER_CROSS_RECORDED_READY'


def test_own_ready_outside_is_retained_and_qid_only_preview_change_not_dropped():
    legacy,side,flags=fixture();full=legacy[1];meta=side[1]
    full['action']='C';meta['preview']=dict(concept='C',question='Qdifferent',difficulty=1050.)
    meta['legacy_row_sha256']=a.row_sha(full);flags[0]['preview_concept_changed']=False
    rows=calculate((legacy,side,flags));row=rows[0]
    assert not row['full_preview_in_own_R'] and row['empty_preview_in_own_R']
    assert row['interpretation_limited_by_own_R'] and row['membership_category']=='OWN_RECORDED_R_MEMBERSHIP_LIMITED'
    assert row['full_preview_tuple_changed'] and not row['preview_concept_changed'] and len(rows)==1


@pytest.mark.parametrize('bad',['duplicate','missing','extra','query','label','stale_flag'])
def test_join_or_reconciliation_failure_never_intersects_to_favorable_subset(bad):
    legacy,side,flags=fixture()
    if bad=='duplicate':legacy.append(deepcopy(legacy[0]))
    if bad=='missing':side.pop()
    if bad=='extra':
        extra=deepcopy(legacy[0]);extra['event_id']='99';legacy.append(extra)
    if bad=='query':side[1]['query']['question']='wrong_query'
    if bad=='label':
        legacy[1]['correct']=side[1]['correct']=0;side[1]['legacy_row_sha256']=a.row_sha(legacy[1])
    if bad=='stale_flag':flags[0]['R_event_changed']=False
    with pytest.raises(ValueError):calculate((legacy,side,flags))


def test_all_zero_joint_cells_and_all_membership_cells_kept():
    summary=a.summarize_group(calculate(fixture()),'manufactured')
    assert len(summary['joint_MRA_cells'])==8 and len(summary['membership_cells'])==16
    assert sum(v['count'] for v in summary['joint_MRA_cells'])==1
    assert sum(v['count']==0 for v in summary['joint_MRA_cells'])==7
    assert sum(v['count']==0 for v in summary['membership_cells'])==15
