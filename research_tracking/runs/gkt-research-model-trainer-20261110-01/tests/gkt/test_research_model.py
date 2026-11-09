"""Candidate tests sau ROOT áp dụng research_model, chưa được chạy.

Fixture manufactured concept28, không public corpus/teacher/optimizer/fit.
Các methods native bên dưới chỉ được chạy trong allocation ROOT review riêng.
"""

from dataclasses import replace

import pytest
import torch
from torch.nn import functional as F

from knowledge_tracing.gkt.config import GKTBinding, GKTKernelConfig
from knowledge_tracing.gkt.recurrent import GKTRecurrentState
from knowledge_tracing.gkt.research_data import GKTResearchGraphBinding
from knowledge_tracing.gkt.research_model import (
    EVIDENCE_ROLE, RECIPE_ID, RECIPE_SOURCE_SHA256, GKTResearchModel,
    GKTResearchModelSpec, _MaskedOutputMLP,
)


@pytest.fixture(autouse=True)
def cpu_fixture():
    threads = torch.get_num_threads()
    torch.set_num_threads(2)
    try:
        with torch.random.fork_rng(devices=[]):
            torch.random.default_generator.manual_seed(42)
            yield
    finally:
        torch.set_num_threads(threads)


def parts():
    nodes = tuple(f'c{index:02d}' for index in range(28))
    graph = GKTResearchGraphBinding('a'*64, nodes, ((nodes[0], nodes[1]),),
                                    'b'*64, 'c'*64, 'declared_static_expert')
    config = GKTKernelConfig(28, 32, 32, 32, 'static', 'concept', True, True)
    spec = GKTResearchModelSpec(RECIPE_ID, RECIPE_SOURCE_SHA256, 'select_train80',
        'd'*64, 'e'*64, 'f'*64, tuple((name, '1'*64) for name in
        ('config', 'core', 'recurrent', 'research_model')), 42, EVIDENCE_ROLE)
    binding = GKTBinding(graph.domain_sha256, spec.vocabulary_sha256, nodes, 'concept')
    adjacency = torch.zeros((28, 28), device='cpu', dtype=torch.float32)
    adjacency[0, 1] = 1
    return config, binding, graph, adjacency, spec


def make():
    config, binding, graph, adjacency, spec = parts()
    return GKTResearchModel(config, binding, graph, adjacency, spec=spec)


def bound(model):
    return dict(binding=model.binding, graph_sha256=model.graph_sha256)


def initial(model, batch=2):
    return model.initial_state(batch, **bound(model))


def events():
    ids = torch.tensor([[0, 1, 0], [1, 0, 1]], device='cpu', dtype=torch.long)
    answers = torch.tensor([[1, 0, 1], [0, 1, 0]], device='cpu', dtype=torch.long)
    return ids, answers, torch.ones_like(ids, dtype=torch.bool)


def snapshot(module):
    return {name: value.detach().clone() for name, value in module.state_dict().items()}


def assert_snapshot(module, expected):
    current = module.state_dict()
    assert current.keys() == expected.keys()
    for name in expected:
        assert torch.equal(current[name], expected[name]), name


def test_registered_geometry_initial_rng_and_compute_role():
    caller_rng = torch.get_rng_state().clone()
    first, second = make(), make()
    assert torch.equal(torch.get_rng_state(), caller_rng)
    assert sum(parameter.numel() for parameter in first.parameters()) == 24700
    assert len(dict(first.named_parameters())) == 32
    assert_snapshot(second, snapshot(first))
    owned = first.initial_dropout_rng_state
    assert torch.equal(owned, second.initial_dropout_rng_state)
    owned.zero_()
    assert not torch.equal(owned, first.initial_dropout_rng_state)
    output = first.predict(initial(first), torch.tensor([0, 1]), **bound(first))
    assert output.evidence_role == EVIDENCE_ROLE
    assert torch.equal(output.probabilities, torch.full((2,), 0.5))
    assert not hasattr(first, 'fit') and not hasattr(first, 'optimizer')


def test_invalid_metadata_geometry_and_graph_rejected_before_rng_change():
    config, binding, graph, adjacency, spec = parts()
    before = torch.get_rng_state().clone()
    for change in (dict(evidence_role='fitted'), dict(initialization_seed=True),
                   dict(phase_scope='calibration_predict'), dict(recipe_id='author-parity'),
                   dict(sources_sha256=spec.sources_sha256[:-1])):
        with pytest.raises(ValueError):
            replace(spec, **change)
    for change in (dict(num_nodes=4), dict(state_dim=8), dict(embedding_dim=8),
                   dict(message_dim=8), dict(adjacency_kind='dense'), dict(node_unit='exercise_tag')):
        with pytest.raises(ValueError):
            GKTResearchModel(replace(config, **change), binding, graph, adjacency, spec=spec)
    reversed_adjacency = adjacency.T.contiguous()
    with pytest.raises(ValueError, match='adjacency'):
        GKTResearchModel(config, binding, graph, reversed_adjacency, spec=spec)
    with pytest.raises(ValueError, match='binding'):
        GKTResearchModel(config, replace(binding, domain='other'), graph, adjacency, spec=spec)
    with pytest.raises(ValueError, match='FP32'):
        GKTResearchModel(config, binding, graph, adjacency.double(), spec=spec)
    assert torch.equal(torch.get_rng_state(), before)


def test_mlp_empty_and_singleton_fallback_keep_running_buffers():
    mlp = _MaskedOutputMLP(64)
    empty_state, empty_rng = snapshot(mlp), torch.get_rng_state().clone()
    assert mlp(torch.empty((0, 64))).shape == (0, 32)
    assert_snapshot(mlp, empty_state)
    assert torch.equal(torch.get_rng_state(), empty_rng)
    with torch.no_grad():
        mlp.bn.running_mean.fill_(0.25)
        mlp.bn.running_var.fill_(2)
        mlp.bn.weight.fill_(0.75)
        mlp.bn.bias.fill_(-0.1)
    before = snapshot(mlp)
    captured = []
    handle = mlp.second.register_forward_hook(lambda module, args, output: captured.append(output.detach()))
    try:
        rng = torch.get_rng_state().clone()
        output = mlp(torch.ones((1, 64)))
    finally:
        handle.remove()
    expected = (F.elu(captured[0])-0.25)/((torch.tensor(2.0)+1e-5).sqrt())*0.75-0.1
    torch.testing.assert_close(output, expected, rtol=1e-6, atol=1e-6)
    assert not torch.equal(torch.get_rng_state(), rng)
    assert int(mlp.singleton_fallbacks) == 1 and int(mlp.bn.num_batches_tracked) == 0
    for name in ('bn.running_mean', 'bn.running_var', 'bn.num_batches_tracked'):
        assert torch.equal(mlp.state_dict()[name], before[name])
    output.sum().backward()
    assert mlp.bn.weight.grad is not None and torch.isfinite(mlp.bn.weight.grad).all()


def test_bn_two_rows_known_formula_and_running_update():
    mlp = _MaskedOutputMLP(64)
    captured = []
    handle = mlp.second.register_forward_hook(lambda module, args, output: captured.append(output.detach()))
    try:
        output = mlp(torch.arange(128, dtype=torch.float32).reshape(2, 64)/128)
    finally:
        handle.remove()
    values = F.elu(captured[0])
    mean = (values[0]+values[1])/2
    variance = ((values[0]-mean).square()+(values[1]-mean).square())/2
    expected = (values-mean)/(variance+1e-5).sqrt()
    torch.testing.assert_close(output, expected, rtol=1e-5, atol=1e-5)
    torch.testing.assert_close(mlp.bn.running_mean, 0.1*mean, rtol=1e-6, atol=1e-6)
    torch.testing.assert_close(mlp.bn.running_var, 0.9+0.1*(2*variance), rtol=1e-6, atol=1e-6)
    assert int(mlp.bn.num_batches_tracked) == 1 and int(mlp.singleton_fallbacks) == 0


def test_observe_exact_nonself_pools_padding_and_incident_support():
    model = make()
    state = initial(model)
    state = replace(state, values=torch.arange(2*28*32, dtype=torch.float32).reshape(2, 28, 32)/1000)
    captured = {}
    handles = []
    for name in ('self_mlp', 'out_mlp', 'in_mlp'):
        def capture(module, args, name=name):
            captured[name] = args[0].detach().clone()
        handles.append(getattr(model, name).register_forward_pre_hook(capture))
    try:
        result = model.observe(state, torch.tensor([0, 999]), torch.tensor([1, -8]),
                               torch.tensor([True, False]), **bound(model))
    finally:
        for handle in handles:
            handle.remove()
    own = torch.cat((state.values[0, 0], model.interaction_embedding.weight[28]))
    expected_rows = torch.stack([torch.cat((own, state.values[0, node],
        model.concept_embedding.weight[node])) for node in range(1, 28)])
    assert captured['self_mlp'].shape == (1, 64)
    assert torch.equal(captured['self_mlp'][0], own)
    assert torch.equal(captured['out_mlp'], expected_rows)
    assert torch.equal(captured['in_mlp'], expected_rows)
    assert model.normalization_counts == {
        'self': dict(training_updates=0, singleton_fallbacks=1),
        'out': dict(training_updates=1, singleton_fallbacks=0),
        'in': dict(training_updates=1, singleton_fallbacks=0),
    }
    assert torch.equal(result.values[0, 2:], state.values[0, 2:])
    assert torch.equal(result.values[1], state.values[1])
    assert result.history_counts.tolist() == [1, 0]
    assert not torch.equal(result.values[0, :2], state.values[0, :2])


def test_all_invalid_event_and_sequence_preserve_rng_buffers_and_state():
    model = make()
    state = initial(model)
    before, rng = snapshot(model), torch.get_rng_state().clone()
    result = model.observe(state, torch.tensor([999, -9]), torch.tensor([7, -8]),
                           torch.tensor([False, False]), **bound(model))
    assert result is state
    output = model(torch.full((2, 2), 999), torch.full((2, 2), -8),
                   torch.zeros((2, 2), dtype=torch.bool), initial_state=state, **bound(model))
    assert torch.equal(output.logits, torch.zeros((2, 2)))
    assert output.final_state is state
    assert_snapshot(model, before)
    assert torch.equal(torch.get_rng_state(), rng)


def test_whole_sequence_rejects_late_bad_inputs_before_any_mutation():
    model = make()
    ids, answers, valid = (tensor[:, :2].clone() for tensor in events())
    state = initial(model)
    bad_ids, bad_answers = ids.clone(), answers.clone()
    bad_ids[0, 1] = 28
    bad_answers[0, 1] = 2
    overflowing = replace(state, history_counts=torch.tensor([torch.iinfo(torch.long).max-1, 0]))
    cases = ((bad_ids, answers, state), (ids, bad_answers, state), (ids, answers, overflowing))
    before, rng = snapshot(model), torch.get_rng_state().clone()
    for queries, labels, current in cases:
        values, counts = current.values.clone(), current.history_counts.clone()
        with pytest.raises(ValueError, match='Whole sequence'):
            model(queries, labels, valid, initial_state=current, **bound(model))
        assert_snapshot(model, before)
        assert torch.equal(torch.get_rng_state(), rng)
        assert torch.equal(current.values, values) and torch.equal(current.history_counts, counts)


def test_training_label_causality_and_manual_sequence_parity():
    model = make()
    saved = snapshot(model)
    ids, answers, valid = events()
    rng = model.initial_dropout_rng_state
    torch.set_rng_state(rng)
    baseline = model(ids, answers, valid, initial_state=None, **bound(model))
    changed = answers.clone()
    changed[:, 1:] = 1-changed[:, 1:]
    model.load_state_dict(saved)
    torch.set_rng_state(rng)
    alternate = model(ids, changed, valid, initial_state=None, **bound(model))
    assert torch.equal(baseline.logits[:, :2], alternate.logits[:, :2])
    model.load_state_dict(saved)
    torch.set_rng_state(rng)
    state, logits = initial(model), []
    for time in range(3):
        logits.append(model.predict(state, ids[:, time], **bound(model)).logits)
        state = model.observe(state, ids[:, time], answers[:, time], valid[:, time], **bound(model))
    assert torch.equal(baseline.logits, torch.stack(logits, dim=1))
    assert torch.equal(baseline.final_state.values, state.values)
    assert all(count['training_updates'] == 3 for count in model.normalization_counts.values())


def test_eval_batch_singleton_parity_frozen_buffers_and_rng():
    model = make()
    ids, answers, valid = events()
    with torch.no_grad():
        model(ids[:, :2], answers[:, :2], valid[:, :2], initial_state=None, **bound(model))
        model.eval()
        before, rng = snapshot(model), torch.get_rng_state().clone()
        batch = model(ids, answers, valid, initial_state=None, **bound(model))
        for learner in range(2):
            one = model(ids[learner:learner+1], answers[learner:learner+1], valid[learner:learner+1],
                        initial_state=None, **bound(model))
            torch.testing.assert_close(batch.logits[learner], one.logits[0], rtol=1e-6, atol=1e-6)
    assert_snapshot(model, before)
    assert torch.equal(torch.get_rng_state(), rng)


def test_training_peer_coupling_and_eval_peer_independence():
    mlp = _MaskedOutputMLP(64)
    with torch.no_grad():
        mlp.first.weight.zero_()
        mlp.first.weight[:, :32].copy_(torch.eye(32))
        mlp.first.bias.zero_()
        mlp.second.weight.copy_(torch.eye(32))
        mlp.second.bias.zero_()
    high = torch.stack((torch.full((64,), 0.25), torch.full((64,), 3.0)))
    low = high.clone()
    low[1] = -3
    saved, rng = snapshot(mlp), torch.get_rng_state().clone()
    upper = mlp(high)
    mlp.load_state_dict(saved)
    torch.set_rng_state(rng)
    lower = mlp(low)
    assert bool((upper[0]-lower[0]).abs().max() > 0.1)
    mlp.eval()
    before, rng = snapshot(mlp), torch.get_rng_state().clone()
    assert torch.equal(mlp(high)[0], mlp(low)[0])
    torch.testing.assert_close(mlp(high)[0], mlp(high[:1])[0], rtol=1e-6, atol=1e-6)
    assert_snapshot(mlp, before)
    assert torch.equal(torch.get_rng_state(), rng)


def test_registered_gradient_paths_and_binding_drift():
    model = make()
    ids, answers, valid = events()
    state = initial(model)
    output = model(ids, answers, valid, initial_state=state, **bound(model))
    F.binary_cross_entropy_with_logits(output.logits, answers.float()).backward()
    for name, parameter in model.named_parameters():
        assert parameter.grad is not None and torch.isfinite(parameter.grad).all(), name
    assert bool(model.gru.W_n.weight.grad.abs().sum() > 0)
    assert torch.equal(state.values, torch.zeros_like(state.values))
    bad = replace(state, recipe_sha256='0'*64)
    with pytest.raises(ValueError, match='binding'):
        model.predict(bad, torch.tensor([0, 1]), **bound(model))
    with pytest.raises(ValueError, match='binding'):
        model.predict(state, torch.tensor([0, 1]), binding=model.binding, graph_sha256='0'*64)
    model.self_mlp.dropout.p = 0
    with pytest.raises(ValueError, match='recipe'):
        model.predict(state, torch.tensor([0, 1]), **bound(model))
