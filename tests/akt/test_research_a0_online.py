"""A0 checkpoint thật trên fixture48targets → dự báo online; không corpus thật."""
from dataclasses import replace
import copy
import hashlib
import io
import json
import uuid

import numpy as np
import pytest
import torch

from knowledge_tracing.akt import research_a0_online as online
from knowledge_tracing.akt import research_graph_checkpoint as checkpoint
from knowledge_tracing.akt import research_graph_condition as condition
from knowledge_tracing.akt import research_graph_context as context
from knowledge_tracing.akt import research_graph_model as model
from knowledge_tracing.akt.training import train_epoch
from knowledge_tracing.akt.research_simulator_data import iter_research_windows
from knowledge_tracing.simulator_bridge import ItemQuery, OnlineSession
import test_research_graph_model as core_fixture


LIMITS = checkpoint.GraphCheckpointLimits(64*1024**2, 1024**2, 64*1024**2)
H = 'a'*64


@pytest.fixture(scope='module')
def native_case():
    case = core_fixture.handmade()
    config = replace(case['config'], run_id='a0-online-fixture-'+uuid.uuid4().hex[:10], max_steps=2)
    config = replace(config, output_dir=config.project_root/'experiments/akt/results'/config.run_id)
    setup = condition.prepare_research_graph_condition(variant='A0', graph_mode='none',
        bank=case['bank'], nodes=(), edges=(), train80=case['condition'].train80,
        expected_sources=condition.source_inventory())
    def index(phase):
        return context.prepare_research_graph_context(phase, case['encoding'], setup,
            limits=case['index'].limits, fit80_encoding_sha256=case['encoding'].identity,
            context=config.context, target_block=config.target_block)
    train_index, prediction_index = index(case['train']), index(case['prediction'])
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(42)
        adapter = model.ResearchGraphAKTAdapter(config=config, encoding=case['encoding'],
            index=train_index, condition=setup)
    optimizer = torch.optim.Adam(adapter.native.parameters(), lr=config.lr,
        betas=config.betas, eps=config.eps, weight_decay=config.weight_decay)
    tracker = checkpoint.GraphAdamParticipation(adapter, optimizer, event_sink=lambda event: None)
    profile = checkpoint.GraphCheckpointProfile(
        hashlib.sha256((config.project_root/checkpoint.PROTOCOL21_PATH).read_bytes()).hexdigest(),
        checkpoint.RECIPE_SHA256, H, H, tracker.initial_backbone_sha256, H,
        'selected_fit_candidate', None)
    identity = checkpoint.graph_checkpoint_identity(config=config, encoding=case['encoding'],
        condition=setup, index=train_index, profile=profile)
    tracker.begin_epoch(1)
    stats = train_epoch(adapter, lambda: iter(case['entries']), optimizer=optimizer, epoch=1,
        budget=dict(max_steps=2, max_targets=48, max_seconds=60., max_rss_bytes=1024**3,
            min_available_ram_bytes=2*1024**3), batch_factory=tracker.collate, progress_callback=tracker.progress)
    assert stats.complete and stats.valid_targets == 48 and stats.optimizer_steps == 2
    receipt = tracker.finish_epoch(stats)
    (config.output_dir/'checkpoints').mkdir(parents=True, exist_ok=False)
    reference = checkpoint.save_graph_epoch_state(config.output_dir/'checkpoints/epoch-1',
        adapter=adapter, optimizer=optimizer, participation=tracker, epoch_receipt=receipt,
        expected_identity=identity, profile=profile, limits=LIMITS)
    adapter.set_context_index(prediction_index)
    case.update(config=config, adapter=adapter, reference=reference, identity=identity)
    return case


def load(case, **changes):
    arguments = dict(directory=case['reference'].directory, config=case['config'], bank=case['bank'],
        encoding=case['encoding'], expected_identity=case['identity'],
        expected_complete_sha256=case['reference'].complete_sha256, limits=LIMITS)
    arguments.update(changes)
    return online.load_research_a0_online(**arguments)


def test_native_saved_a0_matches_research_predictions_without_optimizer_or_rng_restore(native_case, monkeypatch):
    case = native_case
    torch_rng = torch.get_rng_state().clone()
    numpy_rng = np.random.get_state()
    def unexpected_optimizer(*args, **kwargs):
        raise AssertionError('inference must not create an optimizer')
    monkeypatch.setattr(torch.optim, 'Adam', unexpected_optimizer)
    backend = load(case)
    assert torch.equal(torch_rng, torch.get_rng_state())
    assert np.array_equal(numpy_rng[1], np.random.get_state()[1])
    assert backend.model_id == case['reference'].checkpoint_sha256
    assert not backend._adapter.native.training
    windows = tuple(iter_research_windows(case['prediction'], case['encoding'],
        context=100, target_block=100, training=False))
    expected = case['adapter'].predict_windows(windows)
    trajectory, = case['prediction'].trajectories
    session = OnlineSession(backend, case['bank'], learner_id=trajectory.learner_id, max_events=7)
    for row, probability in zip(trajectory.observations, expected[0]):
        ticket = session.predict(row.query)
        assert ticket.score.probability == pytest.approx(float(probability), abs=1e-6, rel=0)
        assert session.probe(row.query) == ticket.score
        session.observe(ticket, row.correct)
    assert len(trajectory.observations) == len(expected[0]) == 6
    unseen = next(item for item in case['bank'].item_ids if item not in case['encoding'].exercise_encoding().vocabulary.values)
    query = ItemQuery(unseen, 2000, 999999)
    assert session.predict(query).score.probability is None
    assert torch.equal(torch_rng, torch.get_rng_state())


@pytest.mark.parametrize('change', ['hash', 'domain', 'geometry', 'variant', 'encoding', 'phase'])
def test_native_loader_rejects_incompatible_binding_before_model_creation(native_case, monkeypatch, change):
    case = native_case
    arguments = {}
    if change == 'hash': arguments['expected_complete_sha256'] = H
    if change == 'domain': arguments['bank'] = replace(case['bank'], environment_id='OTHER_DOMAIN')
    if change == 'geometry': arguments['config'] = replace(case['config'], context=99)
    if change == 'variant':
        identity = copy.deepcopy(case['identity']); identity['condition']['variant'] = 'A3'
        arguments['expected_identity'] = identity
    if change == 'encoding': arguments['encoding'] = replace(case['encoding'], learners=99)
    if change == 'phase': arguments['config'] = replace(case['config'], phase='preflight')
    def unexpected_model(*args, **kwargs):
        raise AssertionError('incompatible inputs reached model construction')
    monkeypatch.setattr(online, 'AKTAdapter', unexpected_model)
    with pytest.raises(ValueError): load(case, **arguments)


@pytest.mark.parametrize('change', ['extra_parameter', 'nonfinite', 'digest', 'payload_identity', 'receipt'])
def test_native_loader_rejects_authenticated_inconsistent_payload_before_model(native_case, monkeypatch, change):
    case = native_case
    source = case['reference'].directory
    payload = torch.load(io.BytesIO((source/'state.pt').read_bytes()), weights_only=True, map_location='cpu')
    state = payload['model_state_dict']
    name = next(iter(state))
    if change == 'extra_parameter': state['alpha'] = torch.zeros(1)
    if change == 'nonfinite': state[name].reshape(-1)[0] = float('nan')
    if change == 'digest': state[name].reshape(-1)[0] += 1.
    if change == 'payload_identity': payload['identity']['condition']['variant'] = 'A3'
    if change == 'receipt': payload['receipt']['completed_epochs'] += 1
    buffer = io.BytesIO(); torch.save(payload, buffer); raw = buffer.getvalue()
    metadata = json.loads((source/'metadata.json').read_bytes())
    metadata['checkpoint_sha256'] = hashlib.sha256(raw).hexdigest()
    metadata['checkpoint_bytes'] = len(raw)
    metadata_raw = checkpoint._raw(metadata)
    complete = checkpoint._raw(dict(schema_version=1, status=checkpoint.STATUS,
        metadata_sha256=hashlib.sha256(metadata_raw).hexdigest(), checkpoint_sha256=metadata['checkpoint_sha256']))
    directory = case['config'].output_dir/('negative-'+change)/'epoch-1'
    directory.mkdir(parents=True, exist_ok=False)
    for filename, value in [('state.pt', raw), ('metadata.json', metadata_raw), ('COMPLETE.json', complete)]:
        (directory/filename).write_bytes(value)
    def unexpected_model(*args, **kwargs):
        raise AssertionError('inconsistent payload reached model construction')
    monkeypatch.setattr(online, 'AKTAdapter', unexpected_model)
    with pytest.raises(ValueError):
        load(case, directory=directory, expected_complete_sha256=hashlib.sha256(complete).hexdigest())
