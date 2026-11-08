"""Toy source parity/guards; không dataset, fit/CV hoặc scientific defaults."""

from dataclasses import asdict, dataclass, field, replace
from functools import lru_cache
import hashlib
import json
import math
import os
from pathlib import Path
import sys
from types import ModuleType

import networkx as nx
import numpy as np
import pandas as pd
import pytest

from knowledge_tracing.gam_kt import variant_factory as vf
from knowledge_tracing.gam_kt.replay import predict_then_update

DOMAIN = 'synthetic-junyi-shaped-variant-toy'
NODES = ('A', 'B', 'C')
EDGES = (('A', 'C'), ('B', 'C'))
TOPICS = {'A': 'algebra', 'B': 'geometry', 'C': 'algebra'}
AREAS = {node: 'math' for node in NODES}
ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / ('paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/'
                   'source/junyi_cycle_corrected_ablation_confirmation.ipynb')
CELL_SHA = '5fc0adbf8fcb454b73bbdd3294bb20e17c2a08ec9eb496b7383677f38b04a5fc'
UPDATES = []


@pytest.fixture(scope='module', autouse=True)
def update_budget(tmp_path_factory):
    """Đếm cả native candidate/reference update calls, cap512 trước mỗi update."""
    UPDATES.clear()
    def counted(model, *args):
        original = model.update
        def update(*values):
            assert len(UPDATES) < 512
            UPDATES.append({'call': len(UPDATES) + 1, 'test': os.environ.get('PYTEST_CURRENT_TEST')})
            return original(*values)
        model.update = update
        try:
            return predict_then_update(model, *args)
        finally:
            model.update = original
    patch = pytest.MonkeyPatch()
    patch.setattr(vf, 'predict_then_update', counted)
    yield counted
    patch.undo()
    path = Path(os.environ.get('GRAPH_GAM_UPDATE_LEDGER', tmp_path_factory.getbasetemp() / 'toy_update_ledger.json'))
    assert not path.exists()
    path.write_text(json.dumps({'actual_native_update_calls':len(UPDATES), 'hard_cap':512,
                               'optimizer_steps':0, 'global_fit_calls':0, 'calls':UPDATES}, indent=2)+'\n',encoding='utf-8')


def recipe(signal=False, adaptation=False, weight=0., decay=0., label='explicit-toy'):
    return vf.GAMVariantRecipe(DOMAIN, label, signal, adaptation, weight, decay, vf.native_source_sha256())


def graph(edges=EDGES, nodes=NODES, **changes):
    values = dict(domain=DOMAIN, nodes=nodes, edges=edges, direction=vf.DIRECTION,
                  origin='caller_declared_synthetic_fixture', provenance_id='inline-toy-graph-v1',
                  provenance_sha256=hashlib.sha256(b'inline-toy-graph-v1').hexdigest(),
                  graph_sha256=vf.graph_sha256(domain=DOMAIN,nodes=nodes,edges=edges,direction=vf.DIRECTION))
    values.update(changes)
    return vf.GAMGraphBinding(**values)


def factory(recipe_value=None, graph_value=None, topics=None, areas=None):
    return vf.build_variant_factory(dict(TOPICS) if topics is None else topics,
        dict(AREAS) if areas is None else areas, recipe=recipe() if recipe_value is None else recipe_value,
        graph_binding=graph() if graph_value is None else graph_value, synthetic_only=True)


def query(exercise='C', row=1, days=2):
    return vf.GAMQuery(exercise, 'template-1', 1210., pd.Timestamp('2026-01-01',tz='UTC')+pd.Timedelta(days=days), row)


def reference_model(recipe_value, binding):
    # Chỉ pinned cell11 definitions, không chạy preprocessing/notebook top-level.
    source = ''.join(json.loads(NOTEBOOK.read_text(encoding='utf-8'))['cells'][11]['source'])
    assert hashlib.sha256(source.encode()).hexdigest() == CELL_SHA
    name = '_gam_toy_reference_test'
    module = ModuleType(name)
    scope = module.__dict__
    scope.update(FEATURE_DIM=64,MODEL_INITIAL_ELO=1200.,np=np,pd=pd,math=math,hashlib=hashlib,
                 lru_cache=lru_cache,dataclass=dataclass,field=field,graph=None,
                 topic_map=dict(TOPICS),area_map=dict(AREAS))
    assert name not in sys.modules
    sys.modules[name] = module
    try:
        exec(compile(source,str(NOTEBOOK),'exec'),scope)
    finally:
        del sys.modules[name]
    native_graph = nx.DiGraph();native_graph.add_nodes_from(binding.nodes);native_graph.add_edges_from(binding.edges)
    return scope['GAMKTModel'](recipe_value.graph_signal_enabled or recipe_value.graph_adaptation_enabled,
        time_decay_rate=recipe_value.time_decay_rate,graph_weight=recipe_value.graph_weight,
        graph_source=native_graph,graph_signal_enabled=recipe_value.graph_signal_enabled,
        graph_adaptation_enabled=recipe_value.graph_adaptation_enabled,name=recipe_value.label)


def seed_non_neutral(model):
    for node, theta, uncertainty in [('A',1450.,.4),('B',900.,.8),('C',1300.1,.7)]:
        state = model._state(node)
        state.theta=theta;state.pi_task=uncertainty;state.pi_time=.2
        state.memory=np.linspace(-.1,.1,64,dtype=np.float32)
        state.attempts=7;state.times_forgotten=2;state.recent_outcomes=[0,0,1,0,0,0]
        state.last_timestamp=pd.Timestamp('2026-01-01',tz='UTC')


def snapshot(model):
    return {name:{'theta':state.theta,'memory':state.memory.tolist(),'pi_task':state.pi_task,
        'pi_time':state.pi_time,'attempts':state.attempts,
        'last_timestamp':None if state.last_timestamp is None else state.last_timestamp.isoformat(),
        'recent_outcomes':list(state.recent_outcomes),'times_forgotten':state.times_forgotten}
        for name,state in sorted(model.states.items())}


@pytest.mark.parametrize('signal,adaptation,weight,decay,edges,label',[
    (False,False,0.,0.,(),'source-free-endpoint'),
    (True,False,.35,.02,EDGES,'signal-only-fixed'),
    (True,True,.35,.02,EDGES,'coupled-full-package'),
    (False,False,0.,0.,EDGES,'flags-off-nonempty-control'),
    (True,True,.35,.02,(),'empty-graph-package')])
def test_exact_source_cell_parity_for_explicit_variants(update_budget,signal,adaptation,weight,decay,edges,label):
    r=recipe(signal,adaptation,weight,decay,label);g=graph(edges)
    candidate=factory(r,g).new_learner('toy-learner');reference=reference_model(r,g)
    seed_non_neutral(candidate._model);seed_non_neutral(reference)
    for item,row,day,response in [('C',1,2,0),('C',2,2.25,1),('A',3,10,0),('B',4,11,1)]:
        q=query(item,row,day)
        expected=update_budget(reference,q.exercise,q.problem_type,q.difficulty,q.timestamp,response)
        actual=candidate.step(q,response)
        assert actual.probability == expected
        assert actual.role == vf.ROLE and actual.prior_interactions == row-1
        assert candidate.state_snapshot() == snapshot(reference)
    assert candidate._completed == 4
    assert set(candidate._model.states) == set(reference.states)


def test_parent_signal_positive_control_and_empty_graph_local_difference():
    high=factory(recipe(True,False,.35,.02)).new_learner('high')
    low=factory(recipe(True,False,.35,.02)).new_learner('low')
    high._model._state('A').theta=1550.;low._model._state('A').theta=850.
    assert high.step(query(),0).probability != low.step(query(),0).probability
    empty=factory(recipe(True,True,.35,.02),graph(())).new_learner('empty')
    off=factory(recipe(False,False,.35,.02),graph(())).new_learner('off')
    seed_non_neutral(empty._model);seed_non_neutral(off._model)
    for candidate in (empty,off):
        state=candidate._model._state('C');state.recent_outcomes=[0]*6
    before_empty=empty._model._context('C');before_off=off._model._context('C')
    assert before_empty['graph_signal'] == before_off['graph_signal'] == 0
    assert before_empty['r_neg'] == .9*before_off['r_neg']
    assert before_empty['decay'] == before_off['decay']+.008
    empty.step(query(),0);off.step(query(),0)
    assert empty.state_snapshot() != off.state_snapshot()


def test_flags_off_nonempty_and_empty_sourcefree_endpoint_are_exact():
    left=factory(recipe(),graph()).new_learner('same');right=factory(recipe(),graph(())).new_learner('same')
    for row,response in enumerate([0,1,0],1):
        assert left.step(query(row=row,days=row),response).probability == right.step(query(row=row,days=row),response).probability
        assert left.state_snapshot() == right.state_snapshot()


def test_metadata_copy_and_private_cache_crossfactory_and_native_global_isolation():
    from knowledge_tracing.gam_kt import original_junyi
    initial_maps=(original_junyi.topic_map,original_junyi.area_map,original_junyi._configured_maps)
    names=set(sys.modules)
    topics=dict(TOPICS);areas=dict(AREAS)
    first=factory(topics=topics,areas=areas);same=factory()
    other=factory(topics={node:'changed-topic' for node in NODES})
    a,b,c=first.new_learner('A'),same.new_learner('A'),other.new_learner('A')
    for session in (a,b,c):seed_non_neutral(session._model)
    assert first._scope['question_feature_vector'] is not other._scope['question_feature_vector']
    feature_delta=(first._scope['question_feature_vector']('C','template-1')-
                   other._scope['question_feature_vector']('C','template-1'))
    assert np.any(feature_delta)
    for session in (a,b,c):session._model._state('C').memory=feature_delta.copy()
    topics['C']='caller-mutated';areas.clear()
    score_a=a.step(query(),1).probability
    assert score_a == b.step(query(),1).probability
    assert c.step(query(),1).probability != score_a
    assert (original_junyi.topic_map,original_junyi.area_map,original_junyi._configured_maps) == initial_maps
    assert all(getattr(original_junyi,name) is item for name,item in zip(('topic_map','area_map','_configured_maps'),initial_maps))
    assert not any(name.startswith('_gam_toy_variant_') for name in set(sys.modules)-names)
    with pytest.raises(TypeError): first._scope['topic_map']['C']='forbidden'
    original=first.binding;original['topics']['C']='returned-copy-mutation'
    assert first.binding['topics']['C'] == TOPICS['C']


def test_fresh_learner_source_state_isolation_and_query_lazy_initialization():
    f=factory(recipe(True,True,.35,.02));one=f.new_learner('one');two=f.new_learner('two')
    assert one.state_snapshot() == two.state_snapshot() == {}
    one.step(query(),1)
    assert two.state_snapshot() == {}
    # Native predict tạo prior exercise/parents; không claim state-readonly query.
    assert set(one.state_snapshot()) == {'A','B','C'}
    fresh=f.new_learner('one');assert fresh.state_snapshot() == {}
    with pytest.raises(NotImplementedError):one.as_online_backend()
    with pytest.raises(TypeError):vf.GAMVariantSession(f,'bad',one._model)


def test_current_response_not_used_until_update_and_ordering_spy(monkeypatch):
    a=factory(recipe(True,True,.35,.02)).new_learner('one')
    b=factory(recipe(True,True,.35,.02)).new_learner('one')
    seen=[];predict=a._model.predict;update=a._model.update
    def spy_predict(*args):
        assert len(args)==4 and a._model.states=={}
        seen.append('predict');return predict(*args)
    def spy_update(*args):
        assert seen==['predict'] and len(args)==6
        seen.append('update');return update(*args)
    monkeypatch.setattr(a._model,'predict',spy_predict);monkeypatch.setattr(a._model,'update',spy_update)
    assert a.step(query(),0).probability == b.step(query(),1).probability
    assert seen == ['predict','update'] and a.state_snapshot()!=b.state_snapshot()


@pytest.mark.parametrize('changes',[{'graph_signal_enabled':1},{'graph_adaptation_enabled':None},
    {'graph_weight':True},{'time_decay_rate':float('nan')},{'graph_weight':-1},
    {'domain':'Junyi'},{'source_sha256':'bad'}])
def test_recipe_invalid_types_and_unmarked_domain_reject(changes):
    with pytest.raises(ValueError):replace(recipe(),**changes)


@pytest.mark.parametrize('changes',[{'direction':'dependent_to_prerequisite'},
    {'domain':'synthetic-other'},{'graph_sha256':'0'*64},{'origin':'train_learned'},
    {'edges':(('A','A'),)},{'edges':(('A','C'),('C','A'))},{'edges':(('A','D'),)},
    {'nodes':tuple(str(i) for i in range(17))}])
def test_graph_invalid_binding_direction_size_and_cycles_reject(changes):
    with pytest.raises(ValueError):graph(**changes)


def test_hard_edge_ceiling_and_canonical_nodes():
    nodes=tuple(f'N{i:02d}' for i in range(16))
    edges=tuple((a,b) for index,a in enumerate(nodes) for b in nodes[index+1:])[:65]
    with pytest.raises(ValueError):graph(edges=edges,nodes=nodes)
    with pytest.raises(ValueError):graph(nodes=('B','A','C'))


def test_factory_rejects_domain_metadata_source_and_synthetic_scope(monkeypatch):
    with pytest.raises(ValueError):factory(graph_value=graph(domain='synthetic-other',graph_sha256=vf.graph_sha256(domain='synthetic-other',nodes=NODES,edges=EDGES,direction=vf.DIRECTION)))
    with pytest.raises(ValueError):factory(topics={'A':'only-one'})
    with pytest.raises(ValueError):factory(recipe_value=replace(recipe(),source_sha256='0'*64))
    with pytest.raises(ValueError):vf.build_variant_factory(dict(TOPICS),dict(AREAS),recipe=recipe(),graph_binding=graph(),synthetic_only=False)
    session=factory().new_learner('one')
    monkeypatch.setattr(vf,'native_source_sha256',lambda:'0'*64)
    with pytest.raises(ValueError,match='binding'):session.step(query(),1)


def test_binding_mutations_reject_before_native_update(monkeypatch):
    f=factory();session=f.new_learner('one')
    monkeypatch.setattr(session._model,'update',lambda *args:pytest.fail('must reject before update'))
    monkeypatch.setattr(session._model,'graph_weight',.7)
    with pytest.raises(ValueError,match='settings'):session.step(query(),1)
    g=factory();g._scope['topic_map']={'A':'tampered','B':'geometry','C':'algebra'}
    with pytest.raises(ValueError,match='binding'):g.new_learner('two')


def test_caller_graph_and_recipe_tampering_rejected_and_sources_bound():
    binding=graph();r=recipe();f=factory(r,binding)
    assert set(f.binding['implementation_source_sha256']) == {'original_junyi.py','variant_factory.py','replay.py'}
    with pytest.raises(AttributeError):binding.edges=()
    object.__setattr__(binding,'edges',())
    with pytest.raises(ValueError,match='binding'):f.new_learner('one')
    other=factory(r)
    with pytest.raises(AttributeError):r.graph_weight=.7
    object.__setattr__(r,'graph_weight',.7)
    with pytest.raises(ValueError,match='binding'):other.new_learner('two')


@pytest.mark.parametrize('changes',[{'difficulty':float('inf')},{'source_row':True},
    {'source_row':0},{'timestamp':pd.Timestamp('2026-01-01')},{'exercise':''}])
def test_query_invalid_type_timestamp_and_response(changes):
    with pytest.raises(ValueError):replace(query(),**changes)


def test_unknown_duplicate_backward_and_response_reject_without_update():
    session=factory().new_learner('one')
    for event,label in [(query('D'),0),(query(),True),(query(),2)]:
        with pytest.raises(ValueError):session.step(event,label)
    assert session.state_snapshot()=={}
    session.step(query(),1)
    for event in (query(),query(row=2,days=1)):
        with pytest.raises(ValueError):session.step(event,0)
    assert session._completed==1


def test_hard32_interactions_per_session_before_native_call(monkeypatch):
    session=factory().new_learner('one')
    for row in range(1,33):session.step(query(row=row,days=row),row%2)
    before=session.state_snapshot()
    monkeypatch.setattr(session._model,'predict',lambda *args:pytest.fail('33rd native call forbidden'))
    with pytest.raises(ValueError,match='exceeds32'):session.step(query(row=33,days=33),0)
    assert session.state_snapshot()==before and session._completed==32
