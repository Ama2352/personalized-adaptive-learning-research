"""A1 Junyi với native AKT thật trên CPU, admission CUDA được mock rõ.

Các ca này chạy ở Gate Linux đủ RAM. Chưa là chứng nhận CUDA hoặc training
nghiên cứu. Backbone, graph math, backward và Adam step giữ implementation gốc.
"""
from dataclasses import replace

import numpy as np
import pytest
import torch

from knowledge_tracing.akt import research_graph_model as native_graph
from knowledge_tracing.akt import research_junyi_graph_model as model
from knowledge_tracing.akt.config import AKTConfig
from knowledge_tracing.akt.encoding import ExerciseEncoding
from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView, JunyiResearchEncoding
from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition, JunyiGraphPhaseSession
from knowledge_tracing.akt.research_junyi_roles import make_junyi_research_roles
from knowledge_tracing.akt.tensors import collate_windows
from knowledge_tracing.akt.types import KTEvent, LearnerEvents
from knowledge_tracing.akt.windows import iter_windows
from knowledge_tracing.shared_kt import PrerequisiteGraph, StableVocabulary


@pytest.fixture
def setup(tmp_path,monkeypatch):
    # CPU fixture bypasses config admission alone. Production requires typed CUDA.
    monkeypatch.setattr(model,'validate_config',lambda *args,**kwargs:None)
    monkeypatch.setattr(native_graph,'validate_config',lambda *args,**kwargs:None)
    roles = make_junyi_research_roles([(str(i),i%5,'development') for i in range(40)])
    train = JunyiPhaseView(roles,'select_train80',roles.train_users[:2],roles.identity)
    selection = JunyiPhaseView(roles,'raw_selection10',roles.selection_users[:1],roles.identity)
    encoding = JunyiResearchEncoding(
        ExerciseEncoding(StableVocabulary(('A','B','C')),dict(A=2,B=2,C=2)),train)
    config = AKTConfig(phase='junyi-research',device='cpu',outer_fold=4,
        run_id='junyi-graph-unit',output_dir=tmp_path/'run',execution_enabled=True,
        max_train_users=2,max_val_users=1,max_targets_per_side=12,max_total_targets=100,
        max_steps=10,max_seconds=60.,max_wall_seconds=120.,max_rss_bytes=2*1024**3,
        min_available_ram_bytes=1)

    def student(user,*,labels=(1,1,1,1,1,1),items=('A','C','A','C','A','C')):
        return LearnerEvents(user,0,tuple(KTEvent(user,item,100+i,i+1,labels[i],0,0)
                                         for i,item in enumerate(items)))

    def condition(edges=(('A','C'),)):
        graph = PrerequisiteGraph.from_edges(('A','B','C'),edges)
        return JunyiGraphCondition(encoding,graph,'a'*64)

    def adapter(*,edges=(('A','C'),),phase=train,enabled=True):
        cond = condition(edges)
        session = JunyiGraphPhaseSession(cond,phase)
        torch.manual_seed(42)
        return model.JunyiGraphAKTAdapter(config=config,encoding=encoding,condition=cond,
            phase=session,graph_enabled=enabled)

    return dict(config=config,encoding=encoding,train=train,selection=selection,
                student=student,condition=condition,adapter=adapter)


def windows(setup,view,*,training=False,**kwargs):
    learner = setup['student'](view.users[0],**kwargs)
    return tuple(iter_windows(learner,setup['encoding'].native,training=training))


def raw_backbone_predictions(adapter,entries):
    batch = collate_windows(entries,n_items=len(adapter.encoding.vocabulary.values),device='cpu')
    modes = tuple((module,module.training) for module in adapter.native.modules())
    try:
        adapter.native.backbone.eval()
        with torch.no_grad():
            _,p,_ = adapter.native.backbone(batch.q_data,batch.qa_data,batch.loss_targets)
            p = p.reshape(batch.q_data.shape).cpu().numpy().astype(np.float64)
        return [p[row,:len(window.inputs.item_ids)].copy() for row,window in enumerate(entries)]
    finally:
        for module,mode in modes:
            module.training = mode


def adam(adapter,*,parameters=None):
    return torch.optim.Adam(adapter.native.parameters() if parameters is None else parameters,
        lr=adapter.config.lr,betas=adapter.config.betas,eps=adapter.config.eps,
        weight_decay=adapter.config.weight_decay,foreach=False,fused=False)


def test_constructor_builds_exactly_one_native_backbone(setup,monkeypatch):
    calls = []
    original = native_graph.build_native

    def build(config,*,n_items):
        calls.append(n_items)
        return original(config,n_items=n_items)

    monkeypatch.setattr(native_graph,'build_native',build)
    adapter = setup['adapter']()
    assert calls==[3]
    parameters = tuple(adapter.native.parameters())
    assert len({id(p) for p in parameters})==len(parameters)
    assert any(p is adapter.native.alpha for p in parameters)
    assert adapter.native.gate is None


def test_graph_off_is_exact_same_backbone_prediction(setup):
    adapter = setup['adapter'](phase=setup['selection'])
    entries = windows(setup,setup['selection'])
    with torch.no_grad():
        adapter.native.alpha.fill_(1.)
    expected = raw_backbone_predictions(adapter,entries)
    on = adapter.predict_windows(entries)
    adapter.set_graph_enabled(False)
    off = adapter.predict_windows(entries)
    assert all(np.array_equal(a,b) for a,b in zip(expected,off))
    assert np.all(on[0][[1,3,5]]>off[0][[1,3,5]])
    assert np.array_equal(on[0][[0,2,4]],off[0][[0,2,4]])
    assert adapter.native._call is None


def test_empty_graph_uses_exact_backbone_fallback(setup):
    adapter = setup['adapter'](edges=(),phase=setup['selection'])
    entries = windows(setup,setup['selection'])
    with torch.no_grad():
        adapter.native.alpha.fill_(1.)
    expected = raw_backbone_predictions(adapter,entries)
    actual = adapter.predict_windows(entries)
    assert all(np.array_equal(a,b) for a,b in zip(expected,actual))


def test_native_backward_and_adam_own_alpha_and_backbone(setup):
    adapter = setup['adapter']()
    optimizer = adam(adapter)
    entries = windows(setup,setup['train'],training=True)
    batch = adapter.collate_training(entries)
    before = adapter.native.alpha.detach().clone()
    result = adapter.step(batch,optimizer)
    assert result['stepped'] is True and result['valid_targets']==6
    assert adapter.native.alpha.grad is not None and adapter.native.alpha.grad.item()!=0.
    assert not torch.equal(before,adapter.native.alpha.detach())
    assert adapter.native.alpha in optimizer.state
    assert adapter.native._call is None and adapter._ticket is None


def test_optimizer_missing_alpha_is_rejected(setup):
    adapter = setup['adapter']()
    entries = windows(setup,setup['train'],training=True)
    optimizer = adam(adapter,parameters=adapter.native.backbone.parameters())
    with pytest.raises(ValueError,match='including alpha'):
        adapter.step(adapter.collate_training(entries),optimizer)


def test_phase_switch_separates_prediction_from_training(setup):
    adapter = setup['adapter']()
    selection = JunyiGraphPhaseSession(adapter.condition,setup['selection'])
    adapter.set_phase(selection)
    values = adapter.predict_windows(windows(setup,setup['selection']))
    assert len(values)==1 and values[0].shape==(6,)
    entries = windows(setup,setup['selection'],training=True)
    with pytest.raises(ValueError,match='train80'):
        adapter.collate_training(entries)
    adapter.set_phase(JunyiGraphPhaseSession(adapter.condition,setup['train']))
    assert adapter.audit_context_boundary()['phase_sha256']==setup['train'].identity


def test_pending_training_batch_blocks_phase_toggle_and_prediction(setup):
    adapter = setup['adapter']()
    adapter.collate_training(windows(setup,setup['train'],training=True))
    with pytest.raises(ValueError,match='pending'):
        adapter.set_graph_enabled(False)
    with pytest.raises(ValueError,match='pending'):
        adapter.set_phase(JunyiGraphPhaseSession(adapter.condition,setup['selection']))
    with pytest.raises(ValueError,match='pending'):
        adapter.predict_windows(windows(setup,setup['train']))


def test_foreign_batch_cannot_consume_training_ticket(setup):
    adapter = setup['adapter']()
    batch = adapter.collate_training(windows(setup,setup['train'],training=True))
    copied = replace(batch,q_data=batch.q_data.clone())
    with pytest.raises(ValueError,match='Fresh unchanged'):
        adapter.step(copied,adam(adapter))
    assert adapter.native._call is None and adapter._ticket is None


def test_prediction_restores_nested_module_modes_and_rng(setup):
    adapter = setup['adapter'](phase=setup['selection'])
    adapter.native.train()
    adapter.native.backbone.q_embed.eval()
    modes = tuple(module.training for module in adapter.native.modules())
    rng = torch.get_rng_state().clone()
    adapter.predict_windows(windows(setup,setup['selection']))
    assert tuple(module.training for module in adapter.native.modules())==modes
    assert torch.equal(rng,torch.get_rng_state())


@pytest.mark.parametrize('change',['current_label','future_item'])
def test_current_and_future_information_cannot_change_earlier_predictions(setup,change):
    adapter = setup['adapter'](phase=setup['selection'])
    with torch.no_grad():
        adapter.native.alpha.fill_(1.)
    original = windows(setup,setup['selection'])
    if change=='current_label':
        changed = windows(setup,setup['selection'],labels=(1,1,1,0,1,1))
    else:
        changed = windows(setup,setup['selection'],items=('A','C','A','C','B','B'))
    before = adapter.predict_windows(original)[0]
    after = adapter.predict_windows(changed)[0]
    assert np.array_equal(before[:4],after[:4])


def test_condition_drift_fails_before_forward(setup):
    adapter = setup['adapter'](phase=setup['selection'])
    object.__setattr__(adapter.condition,'variant','A3')
    with pytest.raises(ValueError,match='header changed'):
        adapter.predict_windows(windows(setup,setup['selection']))
    assert adapter.native._call is None


def test_source_drift_detected_at_phase_boundary(setup,monkeypatch):
    adapter = setup['adapter']()
    monkeypatch.setattr(model,'_source_inventory',lambda:adapter._sources+(('unit-drift','b'*64),))
    with pytest.raises(ValueError,match='source changed'):
        adapter.audit_context_boundary()


@pytest.mark.parametrize('value',[0,1,None])
def test_graph_enabled_requires_exact_boolean(setup,value):
    with pytest.raises(ValueError,match='Boolean'):
        setup['adapter'](enabled=value)
