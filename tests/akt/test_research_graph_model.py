"""Recipe26: fixture tự tạo, không corpus/teacher/solver/optimizer update.

Đề xuất native inventory cho ROOT: một backbone/wrapper/gate, tám lần chạy
Architecture.forward, năm logical autograd.backward, không optimizer constructor
hoặc step. Bảy call qua wrapper + một native control; nguyên batch tối đa2x6.
Các test ticket dùng stub primitive (không phải bằng chứng Adam đã thực thi).
"""
from dataclasses import replace

import numpy as np
import pytest
import torch

from knowledge_tracing.akt import research_graph_model as model
from knowledge_tracing.akt import research_graph_context as context
from knowledge_tracing.akt import research_graph_condition as condition
from knowledge_tracing.akt import research_simulator_data as data
from knowledge_tracing.akt.config import AKTConfig, PROJECT_ROOT
from knowledge_tracing.akt.types import TrainingWindow, WindowInputs
from knowledge_tracing.akt.tensors import AKTBatch, collate_windows
from knowledge_tracing.edge_confidence_artifact import (
    LoadedEdgePredictiveScore, LoadedMethod24Scores, Method24TrainingBinding, PUBLIC)
from knowledge_tracing.simulator_bridge import ItemQuery, Observation, SimulatorBank, SimulatorItem, identity_hash
from knowledge_tracing.simulator_data import ObservableTrajectory
from knowledge_tracing.simulator_research_data import ResearchSplitPlan, ResearchProvenance, ShardLimits

H = 'a' * 64


def handmade():
    plan = ResearchSplitPlan('HANDMADE_MODEL_NO_GENERATED_CORPUS', 42, 10, 1, H)
    # V1 full reference bank:28concepts x3difficulties. Only i0/i1/i2 at1200
    # occur in observations; the other81items do not enlarge train vocabulary.
    bank = SimulatorBank('HANDMADE_NO_FITTED_MODEL', tuple(
        SimulatorItem(f'i{i}' if difficulty == 1200 else f'i{i}-{difficulty}', f'c{i:02d}', difficulty)
        for i in range(28) for difficulty in (1050, 1200, 1350)))
    shards = {}
    for role_id, role in enumerate(('train', 'selection', 'calibration')):
        trajectories = []
        for ordinal, assignment in enumerate(plan.split_plan.assignments(role)):
            # Even learners see active c01; odd learners see unsupported c02.
            child = 'i1' if ordinal % 2 == 0 else 'i2'
            rows = tuple(Observation(ItemQuery('i0' if rank % 2 == 0 else child,
                1000+rank, role_id*100000 + ordinal*100 + rank + 1), int(rank % 2 == 0)) for rank in range(6))
            trajectories.append(ObservableTrajectory(assignment.learner_id, plan.split_plan.identity,
                identity_hash(bank.identity), 'handmade_observables_only', rows))
        provenance = ResearchProvenance(role, plan.identity, plan.split_plan.identity, identity_hash(bank.identity),
            H, (('collector', H), ('environment', H)), H, 'handmade_observables_only', 'unix_seconds_utc', 'UTC', False)
        shards[role] = data.ResearchAKTShard(plan, bank, role, tuple(trajectories), provenance,
            provenance.identity, ShardLimits(len(trajectories), 6, len(trajectories)*6))
    train = data.prepare_research_phase('select_train80', shards=(shards['train'],))
    encoding = data.fit_research_encoding(train)
    binding = condition.GraphTrain80Binding('HANDMADE_NOT_FILE_OR_FIT_ATTESTED', H, H, plan.identity,
        shards['train'].provenance.identity, H, identity_hash(bank.identity),
        shards['train'].audit['audit']['shard_sha256'], shards['selection'].audit['audit']['shard_sha256'],
        shards['calibration'].audit['audit']['shard_sha256'])
    public = tuple(sorted((name, H) for name in PUBLIC))
    training = Method24TrainingBinding(binding.corpus_id, H, H, plan.identity,
        binding.train_provenance_sha256, H, binding.domain_sha256, H, H, H, public,
        (('src/knowledge_tracing/edge_confidence.py', H),), (('HANDMADE_NOT_RUNTIME_PROOF', H),))
    edges = (('c00', 'c01'), ('c00', 'c02'))
    nodes = tuple(sorted({i.concept_id for i in bank.items}))
    scores = (LoadedEdgePredictiveScore(*edges[0], True, .75, None, 30, 25, 5, 20, .01, 150, 200),
        LoadedEdgePredictiveScore(*edges[1], False, None, 'insufficient_eligible_learners', 30, 2, 28, 2, None, None, 200))
    loaded = LoadedMethod24Scores('declared', nodes, edges, scores, training,
        (('MANUFACTURED_NO_ARTIFACT_READ', H),), H, H, H, 2352, 2352)
    setup = condition.prepare_research_graph_condition(variant='A3', graph_mode='expert_declared', bank=bank,
        nodes=nodes, edges=edges, train80=binding, expected_sources=condition.source_inventory(),
        topology_source_sha256=H, loaded_scores=loaded, expected_method24_training=training,
        expected_scores_sha256=loaded.identity)
    limits = context.ResearchGraphContextLimits(100, 6, 100, 20, 200, 100, 1000, 1024**2, 20.)
    def index(phase):
        return context.prepare_research_graph_context(phase, encoding, setup, limits=limits,
            fit80_encoding_sha256=encoding.identity, context=100, target_block=100)
    train_index = index(train)
    prediction = data.prepare_research_phase('raw_selection10', shards=(shards['selection'],))
    prediction_index = index(prediction)
    entries = tuple(data.iter_research_windows(train, encoding, context=100, target_block=100, training=True))
    # Sort by actual source-row identity: learner IDs themselves are hash ordered.
    entries = tuple(sorted(entries, key=lambda e: int(e.window.inputs.source_rows[0])))
    config = AKTConfig(phase='simulator-research', run_id='graph-core-handmade',
        output_dir=PROJECT_ROOT/'experiments/akt/results/graph-core-handmade',
        max_train_users=8, max_val_users=1, max_targets_per_side=100, max_total_targets=200,
        max_steps=1, max_seconds=60., max_wall_seconds=90., max_rss_bytes=2*1024**3,
        min_available_ram_bytes=1024**3)
    return dict(config=config, encoding=encoding, condition=setup, index=train_index,
        prediction_index=prediction_index, entries=entries)


@pytest.fixture(scope='module')
def case():
    fixture = handmade()
    # Capture the RNG immediately after real backbone construction: the new
    # alpha/gate branch must consume no additional native RNG draws.
    original = model.build_native
    observed = {}
    def build(*args, **kwargs):
        native = original(*args, **kwargs)
        observed['after_backbone'] = torch.get_rng_state().clone()
        return native
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(42)
        model.build_native = build
        try:
            adapter = model.ResearchGraphAKTAdapter(config=fixture['config'], encoding=fixture['encoding'],
                index=fixture['index'], condition=fixture['condition'])
        finally:
            model.build_native = original
        fixture['construction_rng_preserved'] = torch.equal(torch.get_rng_state(), observed['after_backbone'])
        fixture['adapter'] = adapter
        yield fixture


def gradients(native):
    return {name: None if p.grad is None else p.grad.detach().clone() for name, p in native.named_parameters()}


def equal_gradients(a, b):
    assert a.keys() == b.keys()
    for name in a:
        assert (a[name] is None) == (b[name] is None), name
        if a[name] is not None:
            assert torch.equal(a[name], b[name]), name


def test_cpu_adapter_identity_keeps_legacy_payload_shape(case):
    adapter = case['adapter']
    assert adapter.cuda_profile is None and adapter._cuda_profile_sha is None
    expected = dict(recipe=model.RECIPE,condition=adapter._condition_sha,encoding=adapter._encoding_sha,
                    config=adapter._config_sha,sources=adapter._sources)
    assert adapter.identity == identity_hash(expected)


def copy_batch(batch, *, qa=None, targets=None):
    return AKTBatch(batch.q_data.clone(), batch.qa_data.clone() if qa is None else qa,
        batch.loss_targets.clone() if targets is None else targets,
        batch.valid_mask.clone(), batch.target_mask.clone(), batch.source_rows.copy())


def test_native_eight_forwards_five_logical_backwards_no_optimizer(case):
    adapter = case['adapter']; native = adapter.native
    entries = case['entries'][:2]
    windows = tuple(e.window for e in entries)
    batch = collate_windows(windows, n_items=3, device='cpu', targets=[e.targets for e in entries])
    evidence = case['index'].for_windows(windows)
    assert case['construction_rng_preserved']
    assert set(native.state_dict()) == {'alpha', 'gate.weight', 'gate.bias'} | {
        'backbone.'+name for name in native.backbone.state_dict()}
    assert native.alpha.item() == 0. and torch.count_nonzero(native.gate.weight) == 0 and native.gate.bias.item() == 0.
    assert evidence[0][1].audit.parents[0].confidence == .75
    assert evidence[1][1].audit.parents[0].confidence == 0.

    native.train(); rng = torch.get_rng_state().clone()
    # 1: actual pinned upstream control, with dropout enabled.
    control = native.backbone(batch.q_data, batch.qa_data, batch.loss_targets)
    (control[0]/control[2]).backward()
    control_grad = gradients(native.backbone)
    native.zero_grad(set_to_none=True); torch.set_rng_state(rng)
    # 2: whole branch off must call the exact native path, including gradients.
    native.bind(batch, evidence, enabled=False)
    off = native(batch.q_data, batch.qa_data, batch.loss_targets)
    assert torch.equal(control[0], off[0]) and torch.equal(control[1], off[1]) and torch.equal(control[2], off[2])
    (off[0]/off[2]).backward(); equal_gradients(control_grad, gradients(native.backbone))
    assert native.alpha.grad is None and native.gate.weight.grad is None
    # 3: authentic unsupported edge, mass0, no graph parameters participate.
    zero = collate_windows((windows[1],), n_items=3, device='cpu', targets=[entries[1].targets])
    native.zero_grad(set_to_none=True)
    native.bind(zero, (evidence[1],), enabled=True)
    absent = native(zero.q_data, zero.qa_data, zero.loss_targets)
    (absent[0]/absent[2]).backward()
    assert native.alpha.grad is None and native.gate.weight.grad is None
    # 4: alpha0 must still have a finite nonzero gradient; no alpha-zero bypass.
    native.zero_grad(set_to_none=True); torch.set_rng_state(rng)
    native.bind(batch, evidence, enabled=True)
    initial = native(batch.q_data, batch.qa_data, batch.loss_targets)
    assert torch.equal(initial[1], control[1]) and torch.equal(initial[0], control[0])
    (initial[0]/initial[2]).backward()
    assert torch.isfinite(native.alpha.grad) and native.alpha.grad.abs().item() > 0
    assert native.gate.weight.grad is not None and torch.count_nonzero(native.gate.weight.grad) == 0
    # 5: controlled fixture assignment, not an optimizer update. Cache same-call
    # logits to prove mixed inactive slots reuse this exact dropout/backbone pass.
    native.zero_grad(set_to_none=True); native.eval()
    with torch.no_grad(): native.alpha.fill_(1.)
    cached = []
    hook = native.backbone.out.register_forward_hook(lambda module, args, out: cached.append(out.detach().clone()))
    try:
        native.bind(batch, evidence, enabled=True)
        mixed = native(batch.q_data, batch.qa_data, batch.loss_targets)
    finally:
        hook.remove()
    base = torch.sigmoid(cached[0].reshape(batch.q_data.shape))
    matrix = mixed[1].reshape(batch.q_data.shape)
    inactive = torch.tensor([[not (item is not None and any(p.support > 0 and p.confidence > 0 for p in item.audit.parents))
        for item in row] for row in evidence], dtype=torch.bool)
    assert torch.equal(matrix[inactive], base[inactive])
    assert torch.any(matrix[~inactive] != base[~inactive])
    # Parent correct=1, c=.75 => message=.375; gate=.5 => residual=.1875.
    expected = torch.sigmoid(cached[0].reshape(batch.q_data.shape)[0, 1] + .1875)
    assert torch.equal(matrix[0, 1], expected)
    (mixed[0]/mixed[2]).backward()
    assert native.gate.weight.grad.abs().sum().item() > 0 and native.gate.bias.grad.abs().item() > 0
    assert torch.isfinite(native.alpha.grad)
    # 6: lower-level causal math probe. This intentionally changes qa without
    # claiming a newly admitted research window; the sealed index separately
    # rejects such mutations. Only current t=1 is compared, not later targets.
    qa = batch.qa_data.clone(); qa[0, 1:] = batch.q_data[0, 1:] + 3*(1-(qa[0, 1:]-batch.q_data[0, 1:])//3)
    perturbed = copy_batch(batch, qa=qa, targets=1-batch.loss_targets)
    native.bind(perturbed, evidence, enabled=True)
    causal = native(perturbed.q_data, perturbed.qa_data, perturbed.loss_targets)
    assert torch.equal(causal[1].reshape(batch.q_data.shape)[0, :2], matrix[0, :2])
    # 7: peer learner perturbation cannot affect the first learner.
    qa = batch.qa_data.clone(); qa[1] = batch.q_data[1] + 3*(1-(qa[1]-batch.q_data[1])//3)
    peer = copy_batch(batch, qa=qa)
    native.bind(peer, evidence, enabled=True)
    peer_output = native(peer.q_data, peer.qa_data, peer.loss_targets)
    assert torch.equal(peer_output[1].reshape(batch.q_data.shape)[0], matrix[0])
    # 8: public inference is readonly for state, gradients, RNG and all modes.
    native.backbone.out[2].train(True)
    modes = tuple(m.training for m in native.modules())
    state = {k: v.clone() for k, v in native.state_dict().items()}
    before_grads = gradients(native); before_rng = torch.get_rng_state().clone()
    predictions = adapter.predict_windows(windows)
    assert np.array_equal(np.stack(predictions), matrix.detach().numpy().astype(np.float64))
    assert tuple(m.training for m in native.modules()) == modes and torch.equal(before_rng, torch.get_rng_state())
    equal_gradients(before_grads, gradients(native))
    assert all(torch.equal(state[k], v) for k, v in native.state_dict().items())
    assert native._call is None


@pytest.fixture
def ready(case):
    adapter = case['adapter']
    assert not adapter._failed
    adapter._ticket = None
    adapter._optimizer = None
    adapter.native.clear_context(); adapter.native.train()
    adapter.set_context_index(case['index'])
    yield adapter
    adapter._ticket = None; adapter._optimizer = None; adapter.native.clear_context()


def fake_adam(adapter, *, omit=False):
    # Deliberately bypass optimizer construction: only admission wiring tested.
    optimizer = object.__new__(torch.optim.Adam)
    params = list(adapter.native.parameters())
    optimizer.param_groups = [dict(params=params[:-1] if omit else params, lr=adapter.config.lr,
        betas=adapter.config.betas, eps=adapter.config.eps, weight_decay=adapter.config.weight_decay)]
    optimizer.state = {}
    return optimizer


def test_ticket_exact_batch_and_one_use_with_public_primitive(case, ready, monkeypatch):
    batch = ready.collate_training(case['entries'][:2])
    assert type(batch) is AKTBatch
    seen = []
    def primitive(self, actual, optimizer):
        assert self is ready and actual is batch and self.native._call.batch is actual
        seen.append(actual)
        return {'stepped': False, 'FIXTURE_STUB_NOT_NATIVE_UPDATE': True}
    monkeypatch.setattr(model.AKTAdapter, 'step', primitive)
    result = ready.step(batch, fake_adam(ready))
    assert result['FIXTURE_STUB_NOT_NATIVE_UPDATE'] and len(seen) == 1 and ready.native._call is None
    with pytest.raises(ValueError, match='fresh exact'): ready.step(batch, fake_adam(ready))


@pytest.mark.parametrize('change', ['foreign_batch', 'changed_targets', 'changed_qa', 'missing_parameter', 'wrong_lr'])
def test_ticket_and_owned_optimizer_reject_before_primitive(case, ready, monkeypatch, change):
    batch = ready.collate_training(case['entries'][:2])
    optimizer = fake_adam(ready, omit=change == 'missing_parameter')
    if change == 'foreign_batch': batch = copy_batch(batch)
    if change == 'changed_targets': batch.loss_targets[0, 0] = 1-batch.loss_targets[0, 0]
    if change == 'changed_qa': batch.qa_data[0, 0] += 3
    if change == 'wrong_lr': optimizer.param_groups[0]['lr'] *= 2
    monkeypatch.setattr(model.AKTAdapter, 'step', lambda *args: pytest.fail('primitive must not run'))
    with pytest.raises(ValueError): ready.step(batch, optimizer)
    assert ready.native._call is None and ready._ticket is None


def test_pending_ticket_blocks_prediction_and_phase_switch(case, ready):
    ready.collate_training(case['entries'][:1])
    with pytest.raises(ValueError, match='pending training'): ready.predict_windows((case['entries'][0].window,))
    with pytest.raises(ValueError, match='consume training'): ready.set_context_index(case['prediction_index'])


def test_prediction_phase_cannot_collate_training(case, ready):
    ready.set_context_index(case['prediction_index'])
    with pytest.raises(ValueError, match='prediction phase'): ready.collate_training(case['entries'][:1])


def test_changed_window_rejected_by_context_before_forward(case, ready):
    original = case['entries'][0].window
    changed = replace(original, inputs=replace(original.inputs, prior_responses=original.inputs.prior_responses.copy()))
    changed.inputs.prior_responses[1] = 1-changed.inputs.prior_responses[1]
    with pytest.raises(ValueError, match='payload drift'): ready._collate((changed,))
    assert ready.native._call is None


def test_native_ticket_rejects_tensor_replacement_and_is_consumed(case, ready):
    batch, evidence = ready._collate((case['entries'][0].window,))
    ready.native.bind(batch, evidence, enabled=True)
    with pytest.raises(ValueError, match='foreign tensor'): ready.native(batch.q_data.clone(), batch.qa_data, batch.loss_targets)
    assert ready.native._call is None
    with pytest.raises(ValueError, match='fresh one-use'): ready.native(batch.q_data, batch.qa_data, batch.loss_targets)


def test_source_drift_rejects_before_forward(case, ready, monkeypatch):
    monkeypatch.setattr(model, 'source_inventory', lambda: ())
    with pytest.raises(ValueError, match='source drift'): ready.predict_windows((case['entries'][0].window,))
    assert ready.native._call is None


def test_duplicate_windows_reject_before_native(case, ready):
    entry = case['entries'][0]
    with pytest.raises(ValueError, match='duplicate window'): ready.collate_training((entry, entry))


def test_no_retained_phase_or_other_role_truth(case, ready):
    assert not any(type(value) in (data.ResearchPhaseData, data.ResearchAKTShard) for value in vars(ready).values())
    assert not hasattr(ready.index, 'phase') and not hasattr(ready.index, 'trajectories')
    assert ready._ticket is None and ready.native._call is None


@pytest.mark.parametrize('field,value', [('variant', 'A0'), ('condition_sha256', 'b'*64)])
def test_public_native_recipe_rebinding_rejected_before_forward(case, ready, field, value):
    original = getattr(ready.native, field)
    try:
        setattr(ready.native, field, value)
        with pytest.raises(ValueError, match='native variant/condition drift'):
            ready.predict_windows((case['entries'][0].window,))
        assert ready.native._call is None
    finally:
        setattr(ready.native, field, original)


def test_native_enabled_is_exact_boolean_not_truthy_fallback(case, ready):
    batch, evidence = ready._collate((case['entries'][0].window,))
    for enabled in (0, 1, None, np.bool_(True)):
        with pytest.raises(ValueError, match='one outstanding native context'):
            ready.native.bind(batch, evidence, enabled=enabled)
        assert ready.native._call is None


def test_inference_failure_restores_all_modes_and_clears_context(case, ready, monkeypatch):
    ready.native.backbone.out[2].eval()
    modes = tuple(m.training for m in ready.native.modules())
    def stop(*args): raise ValueError('synthetic collation failure before forward')
    monkeypatch.setattr(ready, '_collate', stop)
    with pytest.raises(ValueError, match='synthetic collation'): ready.predict_windows((case['entries'][0].window,))
    assert tuple(m.training for m in ready.native.modules()) == modes and ready.native._call is None


def test_hotpath_has_no_full_index_serializer_but_explicit_boundaries_do(case, ready, monkeypatch):
    full_calls = []
    def full_payload(self):
        full_calls.append(self)
        raise AssertionError('explicit full cache serialization probe')
    monkeypatch.setattr(context.ResearchGraphContextIndex, '_payload', full_payload)
    ready._integrity()
    batch = ready.collate_training(case['entries'][:1])
    monkeypatch.setattr(model.AKTAdapter, 'step', lambda *args: {'FIXTURE_STUB_NOT_NATIVE_UPDATE': True})
    assert ready.step(batch, fake_adam(ready))['FIXTURE_STUB_NOT_NATIVE_UPDATE']
    assert full_calls == []
    with pytest.raises(AssertionError, match='explicit full cache'):
        ready.audit_context_boundary()
    with pytest.raises(AssertionError, match='explicit full cache'):
        _ = ready.identity
    with pytest.raises(AssertionError, match='explicit full cache'):
        ready.set_context_index(case['prediction_index'])
    assert len(full_calls) == 3


def test_unselected_nested_drift_is_lazy_but_selected_and_full_boundary_reject(case, ready):
    selected = case['entries'][0].window
    other = next(e.window for e in case['entries'] if e.window.window_id != selected.window_id)
    record = next(w for w in ready.index.windows if w.window_id == other.window_id)
    parent = record.contexts[1].audit.parents[0]
    original = parent.mean_observed_correctness
    try:
        object.__setattr__(parent, 'mean_observed_correctness', .25)
        # The documented lazy contract does not scan unselected evidence.
        ready._integrity()
        ready._collate((selected,))
        with pytest.raises(ValueError, match='selected evidence drift'):
            ready._collate((other,))
        with pytest.raises(ValueError, match='payload drift'):
            ready.audit_context_boundary()
    finally:
        object.__setattr__(parent, 'mean_observed_correctness', original)
    ready.audit_context_boundary()


def test_selected_context_drift_stops_before_primitive(case, ready, monkeypatch):
    batch = ready.collate_training(case['entries'][:1])
    parent = ready._ticket.context[0][1].audit.parents[0]
    original = parent.support
    monkeypatch.setattr(model.AKTAdapter, 'step', lambda *args: pytest.fail('no primitive after evidence drift'))
    try:
        object.__setattr__(parent, 'support', original+1)
        with pytest.raises(ValueError, match='selected evidence drift'):
            ready.step(batch, fake_adam(ready))
        assert ready.native._call is None and ready._ticket is None
    finally:
        object.__setattr__(parent, 'support', original)


def test_ticket_evidence_clone_mismatch_stops_with_canonical_index_unchanged(case, ready, monkeypatch):
    batch = ready.collate_training(case['entries'][:1])
    ticket = ready._ticket
    item = ticket.context[0][1]
    parent = replace(item.audit.parents[0], mean_observed_correctness=.25)
    altered = replace(item, audit=replace(item.audit, parents=(parent,)))
    row = (*ticket.context[0][:1], altered, *ticket.context[0][2:])
    ready._ticket = replace(ticket, context=(row,))
    monkeypatch.setattr(model.AKTAdapter, 'step', lambda *args: pytest.fail('no primitive for foreign evidence'))
    with pytest.raises(ValueError, match='training ticket evidence drift'):
        ready.step(batch, fake_adam(ready))
    assert ready.native._call is None
    ready.audit_context_boundary()  # Only ticket clone changed, not the index.


def test_native_bound_evidence_drift_stops_before_backbone(case, ready):
    batch, evidence = ready._collate((case['entries'][0].window,))
    ready.native.bind(batch, evidence, enabled=True, expected_evidence_sha256=model._evidence_sha(evidence))
    parent = evidence[0][1].audit.parents[0]
    original = parent.support
    try:
        object.__setattr__(parent, 'support', original+1)
        with pytest.raises(ValueError, match='native bound evidence drift'):
            ready.native(batch.q_data, batch.qa_data, batch.loss_targets)
        assert ready.native._call is None
    finally:
        object.__setattr__(parent, 'support', original)


def test_lookup_to_native_bind_drift_rejects_expected_digest(case, ready):
    batch, evidence = ready._collate((case['entries'][0].window,))
    expected = model._evidence_sha(evidence)
    parent = evidence[0][1].audit.parents[0]
    original = parent.mean_observed_correctness
    try:
        object.__setattr__(parent, 'mean_observed_correctness', .25)
        with pytest.raises(ValueError, match='expected native evidence drift'):
            ready.native.bind(batch, evidence, enabled=True, expected_evidence_sha256=expected)
        assert ready.native._call is None
    finally:
        object.__setattr__(parent, 'mean_observed_correctness', original)


def test_post_primitive_evidence_drift_has_no_false_success_and_poisoned_adapter(case, ready, monkeypatch):
    batch = ready.collate_training(case['entries'][:1])
    parent = ready._ticket.context[0][1].audit.parents[0]
    original = parent.support
    calls = []
    def primitive(*args):
        calls.append('STUB_BODY_NO_NATIVE_OR_OPTIMIZER')
        object.__setattr__(parent, 'support', original+1)
        return {'stepped': False}
    monkeypatch.setattr(model.AKTAdapter, 'step', primitive)
    try:
        with pytest.raises(ValueError, match='selected evidence drift'):
            ready.step(batch, fake_adam(ready))
        assert calls == ['STUB_BODY_NO_NATIVE_OR_OPTIMIZER'] and ready._failed
        assert ready.native._call is None
        with pytest.raises(ValueError, match='failed adapter'):
            ready.predict_windows((case['entries'][0].window,))
    finally:
        object.__setattr__(parent, 'support', original)
        # Fixture reset only: stub executed no model/optimizer body or update.
        ready._failed = False
