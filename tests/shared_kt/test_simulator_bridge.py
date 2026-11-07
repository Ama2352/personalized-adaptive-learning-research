"""Session/reference semantics độc lập model, dùng backend tổng hợp xác định."""

from copy import deepcopy
from dataclasses import replace
import json

import pytest

from knowledge_tracing.simulator_bridge import (SimulatorItem, SimulatorBank, ItemQuery,
    Observation, OnlineScore, OnlineSession, ReferenceSet, probe_references)


def setup(*, learner='u', max_events=10):
    bank = SimulatorBank('synthetic-domain', tuple(SimulatorItem(item, 'C', i)
                                                  for i, item in enumerate(['A','B','R'])))
    class Backend:
        domain = bank.identity
        model_id = 'synthetic-deterministic-fixture'
        def predict_next(self, history, query, *, learner_id):
            if query.item_id == 'R':
                return OnlineScore(None,'unseen_item',len(history),0,False,len(history))
            return OnlineScore(.2+.1*sum(item.correct for item in history), 'fitted',
                                len(history),len(history),False,len(history))
    return OnlineSession(Backend(),bank,learner_id=learner,max_events=max_events)


def test_predict_before_update_and_alternative_probes_do_not_commit():
    session = setup()
    before = session.snapshot()
    first = session.predict(ItemQuery('A',0,1))
    alternative = session.predict(ItemQuery('B',0,1))
    for _ in range(1100):
        assert session.probe(ItemQuery('A',0,1)).probability == .2
    assert session.snapshot() == before
    assert first.score.probability == alternative.score.probability == .2
    session.observe(first,1)
    assert len(session.history) == 1
    assert session.predict(ItemQuery('B',1,2)).score.probability == pytest.approx(.3)
    with pytest.raises(ValueError,match='stale'):
        session.observe(alternative,0)


def test_ticket_foreign_altered_reused_and_reset_are_rejected():
    left,right=setup(),setup(learner='v')
    ticket=left.predict(ItemQuery('A',0,1))
    with pytest.raises(ValueError,match='foreign'):
        right.observe(ticket,1)
    with pytest.raises(ValueError,match='altered'):
        left.observe(replace(ticket,score=replace(ticket.score,probability=.9)),1)
    left.observe(ticket,0)
    with pytest.raises(ValueError,match='stale'):
        left.observe(ticket,0)
    pending=left.predict(ItemQuery('A',1,2))
    left.reset()
    assert left.history == ()
    with pytest.raises(ValueError,match='stale'):
        left.observe(pending,1)
    assert right.history == ()


def test_snapshot_roundtrip_binds_domain_learner_model_and_cap_without_touching_source():
    source=setup()
    source.observe(source.predict(ItemQuery('A',0,1)),1)
    snapshot=json.loads(json.dumps(source.snapshot()))
    destination=setup()
    pending=destination.predict(ItemQuery('B',1,2))
    destination.restore(snapshot)
    assert destination.snapshot() == source.snapshot()
    with pytest.raises(ValueError,match='stale'):
        destination.observe(pending,1)
    for field,value in [('domain',{}),('learner_id','different'),('model_id','other'),('max_events',11)]:
        changed={**snapshot,field:value}
        with pytest.raises(ValueError,match='mismatch'):
            destination.restore(changed)
    corrupted=deepcopy(snapshot)
    corrupted['history'][0]['correct']=0
    with pytest.raises(ValueError,match='hash'):
        destination.restore(corrupted)
    assert snapshot == source.snapshot()


def test_chronology_source_identity_scope_and_outcomes_are_strict():
    session=setup(max_events=1)
    ticket=session.predict(ItemQuery('A',2,2))
    for bad in (True,.5,-1,2):
        with pytest.raises(ValueError,match='binary'):
            session.observe(ticket,bad)
    session.observe(ticket,1)
    for query in (ItemQuery('A',1,3),ItemQuery('A',3,2),ItemQuery('Junyi-other',3,3)):
        with pytest.raises(ValueError):
            session.predict(query)
    # Đọc final state vẫn được, nhưng không vượt interaction budget.
    later=session.predict(ItemQuery('A',3,3))
    with pytest.raises(ValueError,match='budget'):
        session.observe(later,1)
    with pytest.raises(TypeError):
        ItemQuery('A',3,3,correct=1)
    with pytest.raises(TypeError):
        ItemQuery('A',3,3,true_theta=1500)


def test_reference_requires_explicit_weights_and_full_coverage_no_mastery_claim():
    session=setup()
    refs=(ReferenceSet('C',(('A',.5),('B',.5))),)
    before=session.snapshot()
    result=probe_references(session,refs,timestamp=0,source_row=1)
    assert result['scores']['C']['score'] == .2
    assert result['scores']['C']['score_kind']=='mean_reference_correctness'
    assert 'mastered' not in result['scores']['C']
    assert session.snapshot()==before
    result=probe_references(session,(ReferenceSet('C',(('A',.5),('R',.5))),),timestamp=0,source_row=1)
    assert result['scores']['C']['score'] is None
    assert result['scores']['C']['supported_items']==1
    assert result['scores']['C']['missing_items']==('R',)
    with pytest.raises(ValueError,match='weights'):
        ReferenceSet('C',(('A',.3),('B',.3)))
    with pytest.raises(ValueError,match='concept'):
        probe_references(session,(ReferenceSet('Wrong',(('A',1.),)),),timestamp=0,source_row=1)


@pytest.mark.parametrize('field,value',[('timestamp',True),('timestamp',-1),('source_row',0),('source_row',1.5)])
def test_query_rejects_invalid_identity_fields(field,value):
    kwargs=dict(item_id='A',timestamp=0,source_row=1);kwargs[field]=value
    with pytest.raises(ValueError):
        ItemQuery(**kwargs)


def test_domain_and_item_bank_mapping_are_not_numeric_index_transfer():
    session=setup()
    other=replace(session.bank,environment_id='Junyi')
    with pytest.raises(ValueError,match='domain'):
        OnlineSession(session.backend,other,learner_id='u',max_events=10)
    with pytest.raises(ValueError,match='duplicate'):
        SimulatorBank('sim',(SimulatorItem('A','C',1),SimulatorItem('A','D',1)))
    session.backend.model_id='new-checkpoint'
    with pytest.raises(ValueError,match='binding'):
        session.snapshot()
    with pytest.raises(ValueError,match='binding'):
        session.probe(ItemQuery('A',0,1))


def test_reference_weights_and_metadata_are_canonical_immutable_values():
    mutable=[['A',.5],['B',.5]]
    reference=ReferenceSet('C',mutable)
    mutable[0][1]=.9
    assert reference.item_weights == (('A',.5),('B',.5))
    first=SimulatorBank('sim',(SimulatorItem('A','C',1000),))
    second=SimulatorBank('sim',(SimulatorItem('A','C',1000.),))
    assert first.identity == second.identity
