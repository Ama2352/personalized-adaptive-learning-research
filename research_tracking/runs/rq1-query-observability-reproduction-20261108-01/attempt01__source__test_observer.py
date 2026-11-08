"""Spy tests chỉ dummy objects; không native policy/simulator/RNG draws."""
import copy
import io
import json
import random

import pytest

from observer import Context,PolicyObserver,exact


class Timestamp:
    value=123456789
    def isoformat(self):return '2026-01-01T06:00:00+00:00'


class Spy:
    copies=0
    def __init__(self):self.predicts=0;self.updates=0;self.selects=0;self.current_chapter='before';self.counter={'A':0}
    def predict(self,*args):self.predicts+=1;return .25
    def select(self):self.selects+=1;self.counter['A']+=1;return ('A','item-real-return',1200.)
    def update(self,*args):self.updates+=1;return 'updated'
    def __deepcopy__(self,memo):
        type(self).copies+=1
        new=object.__new__(type(self));new.__dict__=copy.deepcopy(self.__dict__,memo);return new


def setup():
    sink=io.StringIO();context=Context(20000,'PG',sink);native=Spy();proxy=PolicyObserver(native,'graph_free',context)
    return native,proxy,context,sink


def prepare():
    native,proxy,context,sink=setup();timestamp=Timestamp();p=proxy.predict('A','query-actual',1000.,timestamp)
    copied=copy.deepcopy(proxy);selected=copied.select()
    legacy={'variant':'graph_free','event_id':'0','learner_id':'20000-PG','probability':p,'action':selected[0],'correct':1}
    context.legacy(legacy)
    return native,proxy,context,sink,timestamp,legacy,copied


def test_exactly_one_delegate_call_and_real_preview_tuple_and_assignment():
    Spy.copies=0;native,proxy,context,sink,timestamp,legacy,copied=prepare()
    assert native.predicts==1 and native.updates==native.selects==0 and Spy.copies==1
    assert native.counter=={'A':0} and copied.counter=={'A':1}
    assert proxy.update('A','query-actual',1000.,timestamp,1,.25)=='updated'
    proxy.current_chapter='after';proxy.counter['A']+=1
    assert native.current_chapter=='after' and native.counter=={'A':1} and 'current_chapter' not in vars(proxy)
    assert native.updates==1 and copied.updates==0
    row=json.loads(sink.getvalue());assert row['query']['question']=='query-actual'
    assert row['preview']=={'concept':'A','question':'item-real-return','difficulty':1200.}
    assert row['preview_timestamp_argument'] is None and row['preview_is_served'] is False
    assert row['query_capture_phase']=='before_delegate_predict' and row['update_pairing_verified']
    assert not context.pending and context.completed=={'graph_free':1}


def test_query_logged_before_delegate_and_observer_does_not_consume_rng():
    native,proxy,context,sink=setup();before=random.getstate()
    def predict(*args):
        assert context.pending['graph_free']['query']['question']=='query-actual'
        assert context.pending['graph_free']['phases']==['before_predict']
        return .25
    native.predict=predict;proxy.predict('A','query-actual',1000.,Timestamp())
    assert random.getstate()==before and native.updates==native.selects==0


@pytest.mark.parametrize('change',['query','label','probability'])
def test_update_pairing_rejects_before_delegate(change):
    native,proxy,context,sink,timestamp,legacy,copied=prepare()
    qid='wrong' if change=='query' else 'query-actual';y=0 if change=='label' else 1;p=.5 if change=='probability' else .25
    with pytest.raises(ValueError):proxy.update('A',qid,1000.,timestamp,y,p)
    assert native.updates==0 and not sink.getvalue()


def test_missing_preview_duplicate_predict_and_duplicate_copy_reject():
    native,proxy,context,sink=setup();proxy.predict('A','query-actual',1000.,Timestamp())
    with pytest.raises(ValueError):proxy.predict('A','query-actual',1000.,Timestamp())
    with pytest.raises(ValueError):context.legacy({'variant':'graph_free','event_id':'0','learner_id':'20000-PG'})
    copy.deepcopy(proxy)
    with pytest.raises(ValueError):copy.deepcopy(proxy)
    assert native.predicts==1


def test_missing_prediction_and_real_select_forbidden():
    native,proxy,context,sink=setup()
    with pytest.raises(ValueError):copy.deepcopy(proxy)
    with pytest.raises(ValueError):proxy.select()
    with pytest.raises(ValueError):proxy.update('A','query-actual',1000.,Timestamp(),1,.25)
    assert native.selects==native.updates==0


@pytest.mark.parametrize('field,value',[('event_id','1'),('learner_id','other'),('probability',.5),('action','B')])
def test_legacy_identity_prediction_action_mismatch(field,value):
    native,proxy,context,sink=setup();proxy.predict('A','query-actual',1000.,Timestamp());copy.deepcopy(proxy).select()
    legacy={'variant':'graph_free','event_id':'0','learner_id':'20000-PG','probability':.25,'action':'A','correct':1}
    legacy[field]=value
    with pytest.raises(ValueError):context.legacy(legacy)


def test_exact_float_value_type_and_signed_zero_not_tolerance():
    assert exact({'x':[.25,1]}, {'x':[.25,1]})
    assert not exact(.25,.250000000000001)
    assert not exact(0.,-0.) and not exact(1,True) and not exact(1,1.)
