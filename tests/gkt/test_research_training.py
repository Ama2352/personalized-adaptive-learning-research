"""Candidate8manufactured compute tests, chưa apply hoặc chạy.

Native workload từ source cần ROOT review riêng. Corpus chỉ là typed fixture,
không publication/teacher/real learner/actual research fit hoặc authority.
"""
from dataclasses import replace
import math

import pytest
import torch

from test_research_data import fixture as data_fixture, role_data, seal, change_labels
from knowledge_tracing.gkt.config import GKTBinding, GKTKernelConfig
from knowledge_tracing.gkt import research_data as rd, research_training as rt
from knowledge_tracing.gkt.research_model import (
    GKTResearchModel, GKTResearchModelSpec, RECIPE_ID, RECIPE_SOURCE_SHA256, EVIDENCE_ROLE,
)
from knowledge_tracing.simulator_bridge import identity_hash


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


def changed_role(corpus, role, transform):
    old = corpus.role_data(role)
    updated = role_data(corpus.plan, corpus.bank, corpus.limits, role, transform(old.trajectories))
    return seal(replace(corpus, roles=tuple(updated if value.role == role else value for value in corpus.roles)))


def selection_items(corpus, indices):
    def update(trajectories):
        return tuple(replace(trajectory, observations=tuple(replace(observation,
            query=replace(observation.query, item_id=corpus.bank.item_ids[index]))
            for observation, index in zip(trajectory.observations, indices))) for trajectory in trajectories)
    return changed_role(corpus, 'selection', update)


def view(corpus, scope='select_train80', encoding=None, graph=None):
    if graph is None:
        graph = rd.GKTResearchGraphBinding(identity_hash(corpus.bank.identity),
            tuple(f'c{index:02d}' for index in range(28)), (('c00', 'c01'),), 'a'*64,
            corpus.role_data('train').audit['audit']['shard_sha256'], 'declared_static_expert')
    return rd.prepare_gkt_research_view(corpus, scope=scope,
        recipe=rd.GKTResearchDataRecipe('concept', 'full_prefix', 'query_only', 'unsupported_history'),
        graph_binding=graph, encoding=encoding)


def model(prepared):
    config = GKTKernelConfig(28, 32, 32, 32, 'static', 'concept', True, True)
    vocabulary = identity_hash(list(prepared.encoding.exercise_encoding().vocabulary.values))
    spec = GKTResearchModelSpec(RECIPE_ID, RECIPE_SOURCE_SHA256, prepared.encoding.optimization_scope,
        prepared.encoding.optimization_phase_sha256, prepared.encoding.identity, vocabulary,
        rt.model_source_identity(), 42, EVIDENCE_ROLE)
    binding = GKTBinding(prepared.graph.domain_sha256, vocabulary, prepared.graph.node_ids, 'concept')
    adjacency = torch.zeros((28, 28), device='cpu', dtype=torch.float32)
    adjacency[0, 1] = 1
    return GKTResearchModel(config, binding, prepared.graph, adjacency, spec=spec)


def adam(native):
    return torch.optim.Adam(native.parameters(), lr=.001, betas=(.9, .999), eps=1e-8,
        weight_decay=0., amsgrad=False, foreach=False, fused=False,
        maximize=False, capturable=False, differentiable=False)


def budget(**changes):
    values = dict(started_at=rt._now(), max_seconds=60., max_rss_bytes=2**30,
        min_available_ram_bytes=2*2**30, max_input_targets=1000, max_prefix_events=10000,
        max_model_calls=100, max_optimizer_steps=8, max_optimized_targets=256, max_scored_targets=256)
    values.update(changes)
    return rt.GKTResearchBudget(**values)


def progress(native):
    return rt.GKTResearchProgress(native.model_binding_sha256, native.initial_dropout_rng_state)


def snapshot(native):
    return {name: tensor.detach().clone() for name, tensor in native.state_dict().items()}


def unchanged(native, state):
    assert native.state_dict().keys() == state.keys()
    for name, value in native.state_dict().items():
        assert torch.equal(value, state[name]), name


def test_spec_and_adam_preflight_reject_before_mutation():
    prepared = view(data_fixture())
    native, spec = model(prepared), rt.GKTResearchSpec(1, 4, 1.)
    optimizer = adam(native)
    state = snapshot(native)
    rng = torch.get_rng_state().clone()
    for change in (dict(epoch=0), dict(epoch=51), dict(batch_size=2), dict(max_grad_norm=True)):
        with pytest.raises(ValueError):
            replace(spec, **change)
    group = optimizer.param_groups[0]
    for key, value in (('lr', .01), ('foreach', None), ('decoupled_weight_decay', True)):
        missing = object()
        old = group.get(key, missing)
        group[key] = value
        try:
            with pytest.raises(ValueError):
                rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=spec,
                                        budget=budget(), progress=progress(native))
        finally:
            if old is missing:
                group.pop(key)
            else:
                group[key] = old
    optimizer.defaults['decoupled_weight_decay'] = True
    with pytest.raises(ValueError, match='Decoupled'):
        rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=spec,
                                budget=budget(), progress=progress(native))
    optimizer.defaults['decoupled_weight_decay'] = False
    first = group['params'][0]
    group['params'].append(first)
    try:
        with pytest.raises(ValueError, match='optimizer'):
            rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=spec,
                                    budget=budget(), progress=progress(native))
    finally:
        group['params'].pop()
    optimizer.state[first] = dict(step=torch.tensor(0., dtype=torch.float64, device='cpu'),
        exp_avg=torch.zeros_like(first), exp_avg_sq=torch.zeros_like(first))
    existing = {key: value.clone() for key, value in optimizer.state[first].items()}
    try:
        with pytest.raises(ValueError, match='scalar step'):
            rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=spec,
                                    budget=budget(), progress=progress(native))
        for key, value in optimizer.state[first].items():
            assert torch.equal(value, existing[key])
    finally:
        optimizer.state.pop(first)
    optimizer.state[first] = dict(step=torch.tensor(0., dtype=torch.float32, device='cpu'),
        exp_avg=torch.zeros_like(first), exp_avg_sq=torch.full_like(first, -1.))
    existing = {key: value.clone() for key, value in optimizer.state[first].items()}
    invalid_moment_progress = progress(native)
    try:
        with pytest.raises(ValueError, match='second moment must be nonnegative'):
            rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=spec,
                                    budget=budget(), progress=invalid_moment_progress)
        assert invalid_moment_progress.counters['model_calls_started'] == 0
        assert invalid_moment_progress.counters['backward_started'] == invalid_moment_progress.counters['adam_started'] == 0
        unchanged(native, state)
        assert torch.equal(torch.get_rng_state(), rng)
        for key, value in optimizer.state[first].items():
            assert torch.equal(value, existing[key])
    finally:
        optimizer.state.pop(first)
    calls = []
    def forbidden(*args, **kwargs):
        calls.append('model entry')
        raise AssertionError('Ambient dtype must be rejected before any model entry')
    default_dtype = torch.get_default_dtype()
    absent = object()
    originals = {name: vars(native).get(name, absent) for name in ('forward', 'predict')}
    try:
        native.forward = forbidden
        native.predict = forbidden
        torch.set_default_dtype(torch.float64)
        used = progress(native)
        with pytest.raises(ValueError, match='ambient default dtype'):
            rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=spec,
                                    budget=budget(), progress=used)
        with pytest.raises(ValueError, match='ambient default dtype'):
            rt.predict_research_gkt(native, prepared, spec=spec, budget=budget(), progress=used)
        assert used.counters['model_calls_started'] == 0
    finally:
        torch.set_default_dtype(default_dtype)
        for name, value in originals.items():
            if value is absent:
                delattr(native, name)
            else:
                setattr(native, name, value)
    assert calls == [] and torch.get_default_dtype() == default_dtype
    unchanged(native, state)
    assert torch.equal(torch.get_rng_state(), rng)
    assert not optimizer.state


def test_complete_epoch_actual_adam_bn_owned_rng_and_modes():
    prepared = view(data_fixture())
    native = model(prepared)
    native.eval()
    optimizer, used, cap = adam(native), progress(native), budget()
    before, caller = snapshot(native), torch.get_rng_state().clone()
    modes = []
    handle = native.register_forward_pre_hook(lambda module, args: modes.append(
        (module.training, torch.is_grad_enabled(), torch.is_inference_mode_enabled())))
    try:
        with torch.no_grad():
            result = rt.train_research_epoch(native, prepared, optimizer=optimizer,
                spec=rt.GKTResearchSpec(1, 4, 1.), budget=cap, progress=used)
    finally:
        handle.remove()
    assert result['complete'] and result['status'] == 'complete' and not result['fitted_research_model']
    assert modes == [(True, True, False), (True, True, False)]
    assert not native.training and all(not module.training for module in native.modules())
    assert used.counters['adam_started'] == used.counters['adam_returned'] == 2
    assert used.counters['optimized_targets'] == 32
    assert used.counters['returned_sequence_observe_events'] == 32
    assert used.counters['complete_train_epochs'] == 1
    assert any(not torch.equal(before[name], parameter) for name, parameter in native.named_parameters())
    assert all(value['training_updates'] == 8 for value in native.normalization_counts.values())
    assert torch.equal(torch.get_rng_state(), caller)
    assert not torch.equal(used.rng_state, native.initial_dropout_rng_state)
    assert math.isfinite(result['mean_loss']) and result['mean_loss'] >= 0
    with pytest.raises(ValueError, match='Contiguous'):
        rt.train_research_epoch(native, prepared, optimizer=optimizer,
            spec=rt.GKTResearchSpec(1, 4, 1.), budget=cap, progress=used)


def test_variable_prefix_prediction_linear_and_manual_causal_parity():
    corpus = changed_role(data_fixture(), 'train', lambda trajectories: tuple(
        replace(trajectory, observations=trajectory.observations[:index % 4+1])
        for index, trajectory in enumerate(trajectories)))
    prepared = view(corpus)
    native = model(prepared)
    used = progress(native)
    before, caller = snapshot(native), torch.get_rng_state().clone()
    result = rt.predict_research_gkt(native, prepared, spec=rt.GKTResearchSpec(1, 4, 1.),
                                    budget=budget(), progress=used)
    assert result['complete'] and len(result['predictions']) == 20
    assert used.counters['sequence_returned'] == used.counters['tail_returned'] == 2
    assert used.counters['model_calls_returned'] == 4 and used.counters['scored_targets'] == 20
    assert used.counters['returned_sequence_observe_events'] == 12
    by_key = {(row['learner_id'], row['global_rank']): row['probability'] for row in result['predictions']}
    native.eval()
    try:
        with torch.no_grad():
            for trajectory in prepared.phase.trajectories:
                state = native.initial_state(1, binding=native.binding, graph_sha256=native.graph_sha256)
                for rank, observation in enumerate(trajectory.observations):
                    node = dict(prepared.train_item_node_map)[observation.query.item_id]
                    ids = torch.tensor([node], device='cpu', dtype=torch.long)
                    p = native.predict(state, ids, binding=native.binding, graph_sha256=native.graph_sha256)
                    assert by_key[trajectory.learner_id, rank] == pytest.approx(float(p.probabilities[0]), abs=1e-6)
                    if rank+1 < len(trajectory.observations):
                        state = native.observe(state, ids, torch.tensor([observation.correct]), torch.tensor([True]),
                                               binding=native.binding, graph_sha256=native.graph_sha256)
    finally:
        native.train()
    unchanged(native, before)
    assert torch.equal(torch.get_rng_state(), caller)
    assert torch.equal(used.rng_state, native.initial_dropout_rng_state)


def test_final_label_excluded_and_oov_suffix_all_null_kept():
    corpus = selection_items(data_fixture(), (0, 1, 0, 1))
    training = view(corpus)
    native, cap = model(training), budget()
    used = progress(native)
    arguments = dict(spec=rt.GKTResearchSpec(1, 4, 1.), budget=cap, progress=used)
    selected = view(corpus, 'raw_selection10', training.encoding, training.graph)
    first = rt.predict_research_gkt(native, selected, **arguments)
    changed = change_labels(corpus, 'selection', 0, 3)
    second_view = view(changed, 'raw_selection10', training.encoding, training.graph)
    second = rt.predict_research_gkt(native, second_view, **arguments)
    assert first['predictions'] == second['predictions']
    assert all('correct' not in row for row in second['predictions'])
    score = rt.score_raw_predictions(second_view, second)
    assert score['full_targets'] == score['eligible_targets'] == 4 and math.isfinite(score['raw_response_log_loss'])
    with pytest.raises(ValueError, match='unchanged'):
        rt.score_raw_predictions(second_view, {**second, 'predictions': second['predictions'][:-1]})
    unsupported_corpus = selection_items(corpus, (2, 2, 1, 0))
    unsupported_view = view(unsupported_corpus, 'raw_selection10', training.encoding, training.graph)
    before_calls = used.counters['model_calls_started']
    null = rt.predict_research_gkt(native, unsupported_view, **arguments)
    assert null['complete'] and len(null['predictions']) == 4
    assert all(row['probability'] is None for row in null['predictions'])
    assert used.counters['model_calls_started'] == before_calls
    score = rt.score_raw_predictions(unsupported_view, null)
    assert score == dict(full_targets=4, eligible_targets=0,
                         unsupported_reasons=dict(oov_item=2, unsupported_history=2), raw_response_log_loss=None)


def test_role_quota_and_foreign_prefix_reject_without_model_mutation(monkeypatch):
    corpus = data_fixture()
    training = view(corpus)
    native = model(training)
    optimizer = adam(native)
    state, rng = snapshot(native), torch.get_rng_state().clone()
    selected = view(corpus, 'raw_selection10', training.encoding, training.graph)
    with pytest.raises(ValueError, match='Prediction role'):
        rt.train_research_epoch(native, selected, optimizer=optimizer, spec=rt.GKTResearchSpec(1, 4, 1.),
                                budget=budget(), progress=progress(native))
    used = progress(native)
    bounded = rt.train_research_epoch(native, training, optimizer=optimizer, spec=rt.GKTResearchSpec(1, 4, 1.),
                                     budget=budget(max_optimizer_steps=1), progress=used)
    assert bounded['status'] == 'bounded' and used.poisoned and used.counters['model_calls_started'] == 0
    original = rt.data.iter_gkt_research_inputs
    def foreign(*args, **kwargs):
        stream = original(*args, **kwargs)
        try:
            entry = next(stream)
            yield replace(entry, inputs=replace(entry.inputs, global_rank=1))
        finally:
            stream.close()
    monkeypatch.setattr(rt.data, 'iter_gkt_research_inputs', foreign)
    with pytest.raises(rt.GKTResearchExecutionError, match='population') as caught:
        rt.train_research_epoch(native, training, optimizer=optimizer, spec=rt.GKTResearchSpec(1, 4, 1.),
                                budget=budget(), progress=progress(native))
    assert caught.value.result['counters']['input_targets'] == 1
    assert caught.value.result['counters']['model_calls_started'] == 0
    unchanged(native, state)
    assert torch.equal(torch.get_rng_state(), rng)
    assert not optimizer.state


def test_forward_failure_keeps_bn_rng_and_unknown_inner_work(monkeypatch):
    prepared = view(data_fixture())
    native = model(prepared)
    native.eval()
    optimizer, used = adam(native), progress(native)
    original = native.forward
    def late(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError('injected after actual sequence')
    monkeypatch.setattr(native, 'forward', late)
    caller = torch.get_rng_state().clone()
    with pytest.raises(rt.GKTResearchExecutionError, match='injected') as caught:
        rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=rt.GKTResearchSpec(1, 4, 1.),
                                budget=budget(), progress=used)
    result = caught.value.result
    assert result['counters']['sequence_started'] == 1 and result['counters']['sequence_returned'] == 0
    assert result['unreturned_sequence_work'] == 'UNKNOWN_WITHIN_PENDING_BATCH'
    assert result['model_state_before'] != result['model_state_after'] and len(result['pending_batch_keys']) == 16
    assert used.poisoned and used.counters['adam_started'] == 0
    assert all(value['training_updates'] == 4 for value in native.normalization_counts.values())
    assert not native.training and torch.equal(torch.get_rng_state(), caller)
    assert not torch.equal(used.rng_state, native.initial_dropout_rng_state)

    # Separate progress on the same manufactured model; no additional constructor.
    # The previous failed forward has already changed BN, without Adam work.
    interrupted_progress = progress(native)
    cancellation = KeyboardInterrupt('manufactured cancellation after actual sequence')
    calls = []
    def interrupted(*args, **kwargs):
        calls.append('actual_sequence')
        original(*args, **kwargs)
        raise cancellation
    monkeypatch.setattr(native, 'forward', interrupted)
    cap = budget()
    with pytest.raises(KeyboardInterrupt) as interrupted_error:
        rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=rt.GKTResearchSpec(1, 4, 1.),
                                budget=cap, progress=interrupted_progress)
    assert interrupted_error.value is cancellation
    assert interrupted_progress.poisoned and calls == ['actual_sequence']
    assert interrupted_progress.counters['sequence_started'] == 1
    assert interrupted_progress.counters['sequence_returned'] == 0
    assert interrupted_progress.counters['adam_started'] == interrupted_progress.counters['adam_returned'] == 0
    assert interrupted_progress.counters['complete_train_epochs'] == 0 and not optimizer.state
    assert all(value['training_updates'] == 8 for value in native.normalization_counts.values())
    assert all(not module.training for module in native.modules())
    assert torch.equal(torch.get_rng_state(), caller)
    assert not torch.equal(interrupted_progress.rng_state, native.initial_dropout_rng_state)
    with pytest.raises(ValueError, match='retried'):
        rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=rt.GKTResearchSpec(1, 4, 1.),
                                budget=cap, progress=interrupted_progress)
    assert calls == ['actual_sequence']


def test_adam_exception_after_real_update_has_uncertain_pending_batch(monkeypatch):
    prepared = view(data_fixture())
    native = model(prepared)
    optimizer, used = adam(native), progress(native)
    original = optimizer.step
    def late(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError('injected after actual Adam')
    monkeypatch.setattr(optimizer, 'step', late)
    caller = torch.get_rng_state().clone()
    with pytest.raises(rt.GKTResearchExecutionError, match='actual Adam') as caught:
        rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=rt.GKTResearchSpec(1, 4, 1.),
                                budget=budget(), progress=used)
    result = caught.value.result
    assert result['counters']['adam_started'] == 1 and result['counters']['adam_returned'] == 0
    assert result['counters']['optimized_targets'] == 0 and len(result['pending_batch_keys']) == 16
    assert any(float(state['step']) == 1 for state in optimizer.state.values())
    assert result['model_state_before'] != result['model_state_after'] and used.poisoned
    assert result['rollback'] is False and torch.equal(torch.get_rng_state(), caller)


def test_late_deadline_keeps_returned_step_without_complete_epoch(monkeypatch):
    prepared = view(data_fixture())
    native = model(prepared)
    optimizer, used = adam(native), progress(native)
    clock = [rt._now()]
    monkeypatch.setattr(rt, '_now', lambda: clock[0])
    original = optimizer.step
    def late(*args, **kwargs):
        value = original(*args, **kwargs)
        clock[0] += 61.
        return value
    monkeypatch.setattr(optimizer, 'step', late)
    cap = budget()
    result = rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=rt.GKTResearchSpec(1, 4, 1.),
                                    budget=cap, progress=used)
    assert result['status'] == 'bounded' and not result['complete'] and used.poisoned
    assert used.counters['adam_started'] == used.counters['adam_returned'] == 1
    assert used.counters['optimized_targets'] == 16 and used.counters['complete_train_epochs'] == 0
    with pytest.raises(ValueError, match='retried'):
        rt.train_research_epoch(native, prepared, optimizer=optimizer, spec=rt.GKTResearchSpec(1, 4, 1.),
                                budget=budget(), progress=used)
