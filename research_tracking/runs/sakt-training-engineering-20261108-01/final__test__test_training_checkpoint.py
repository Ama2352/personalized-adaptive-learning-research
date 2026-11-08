"""Completed engineering raw-state roundtrip, binding negatives và adapter parity."""

from copy import deepcopy
from dataclasses import replace
import hashlib
import io
import json
import os
from pathlib import Path

import numpy as np
import pytest
import torch

from knowledge_tracing.akt.types import KTEvent, LearnerEvents
from knowledge_tracing.shared_kt import CausalSequenceInputs
from knowledge_tracing.sakt.adapter import SAKTInferenceSpec, inference_identity, load_frozen_sakt
from knowledge_tracing.sakt.config import SAKTConfig
from knowledge_tracing.sakt.training import (SAKTTrainingConfig, collate_target_batch, evaluate_sakt,
                                            state_digest, train_synthetic_sakt)
from knowledge_tracing.sakt.training_data import SAKTDataRecipe, prepare_sakt_training_data
from knowledge_tracing.sakt import training_checkpoint as checkpoint
from knowledge_tracing.simulator_bridge import SimulatorBank, SimulatorItem


@pytest.fixture(scope='module', autouse=True)
def cpu_budget(tmp_path_factory):
    ledger = Path(os.environ.get('SAKT_TRAINING_UPDATE_LEDGER', tmp_path_factory.getbasetemp() / 'optimizer_updates.jsonl'))
    ledger.parent.mkdir(parents=True, exist_ok=True)
    original = torch.optim.Adam.step
    def counted(optimizer, *args, **kwargs):
        previous = ledger.read_text(encoding='utf-8').splitlines() if ledger.exists() else []
        assert len(previous) < 32, 'global synthetic optimizer budget exhausted BEFORE next update'
        with ledger.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'step': len(previous) + 1, 'test': os.environ.get('PYTEST_CURRENT_TEST'),
                                     'module': __name__, 'device': 'cpu'}) + '\n')
        return original(optimizer, *args, **kwargs)
    patch = pytest.MonkeyPatch(); patch.setattr(torch.optim.Adam, 'step', counted)
    threads = torch.get_num_threads(); torch.set_num_threads(1)
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(42)
        yield
    torch.set_num_threads(threads); patch.undo()


def learner(user, items, labels, start):
    return LearnerEvents(user, 1, tuple(KTEvent(user, item, i + 10, start + i, int(label), 0, 1)
                                      for i, (item, label) in enumerate(zip(items, labels))))


def prepare(padding='right', cold='query_only'):
    train = learner('train', 'ABAB', [0, 1, 0, 1], 1)
    val = learner('validation', 'ACBA', [1, 0, 1, 0], 101)
    recipe = SAKTDataRecipe(2, padding, cold, 'sliding_last_context', 'window_relative_interaction_rank')
    return prepare_sakt_training_data((train,), (val,), domain='synthetic-checkpoint-not-research',
                                      recipe=recipe, synthetic_only=True), val


@pytest.fixture(scope='module')
def artifact(tmp_path_factory):
    d, _ = prepare()
    mc = SAKTConfig(2, 3, 8, 2, 4, 0., 1e-5)
    tc = SAKTTrainingConfig('adam', .01, (.9, .999), 1e-8, 0., 1., 1, 4, 42,
                            'mean_bce_on_eligible_targets', 2, 64, 30., 'cpu', 'float32')
    result = train_synthetic_sakt(d, model_config=mc, training_config=tc)
    path = tmp_path_factory.mktemp('sakt_ckpt') / 'synthetic_engineering_state.pt'
    saved = checkpoint.save_engineering_weights(path, result)
    return result, saved, d


def load(saved, **changes):
    values = dict(path=saved['checkpoint'], expected_sidecar_sha256=saved['sidecar_sha256'],
                  expected_identity=saved['identity'], max_checkpoint_bytes=1_000_000)
    values.update(changes); return checkpoint.load_engineering_weights(**values)


def rewritten(tmp_path, saved, *, metadata=None, state_bytes=None):
    path = tmp_path / 'negative_control.pt'
    path.write_bytes(saved['checkpoint'].read_bytes() if state_bytes is None else state_bytes)
    value = json.loads(saved['sidecar'].read_text(encoding='utf-8')) if metadata is None else metadata
    sidecar = path.with_suffix('.json'); sidecar.write_text(json.dumps(value), encoding='utf-8')
    return {**saved, 'checkpoint': path, 'sidecar': sidecar,
            'sidecar_sha256': hashlib.sha256(sidecar.read_bytes()).hexdigest(), 'identity': value['identity']}


def test_positive_raw_state_roundtrip_canonical_betas_and_last_epoch(artifact):
    result, saved, d = artifact
    assert saved['identity']['training_config']['betas'] == [.9, .999]
    model = load(saved)
    assert state_digest(model) == result.model_state_sha256
    before = evaluate_sakt(result.model, d, batch_size=4)
    after = evaluate_sakt(model, d, batch_size=2)
    for a, b in zip(before['predictions'], after['predictions']):
        assert a['probability'] == pytest.approx(b['probability'], abs=1e-7) if a['probability'] is not None else b['probability'] is None
    metadata = json.loads(saved['sidecar'].read_text(encoding='utf-8'))
    assert metadata['complete'] and not metadata['resume_supported'] and not metadata['fitted_research_model']
    assert not hasattr(model, 'as_online_backend')


@pytest.mark.parametrize('padding', ['left', 'right'])
@pytest.mark.parametrize('cold', ['query_only', 'unsupported'])
def test_per_target_window_logits_match_existing_adapter_no_fitted_promotion(artifact, padding, cold):
    _, saved, _ = artifact
    d, val = prepare(padding, cold)
    config = SAKTConfig(**saved['identity']['model_config'])
    bank = SimulatorBank('synthetic-training-parity-not-Grade10', tuple(
        SimulatorItem(name, 'concept-' + name, 1000.) for name in 'ABC'))
    spec = SAKTInferenceSpec(2, 'sliding_last_context', 'window_relative_interaction_rank', cold,
                             padding, 3, 'cpu', 'float32')
    # Test-only unverified inference role; actual training artifact keeps engineering role.
    adapter = load_frozen_sakt(saved['checkpoint'], config, d.vocabulary, bank, spec,
        expected_sha256=saved['checkpoint_sha256'],
        expected_identity=inference_identity(config, d.vocabulary, bank, spec, weight_role='unverified_state'),
        weight_role='unverified_state', max_checkpoint_bytes=1_000_000)
    lookup = {item: index for index, item in enumerate(d.vocabulary.values)}
    inputs = CausalSequenceInputs(np.asarray([lookup.get(e.exercise, -1) for e in val.events], dtype=np.int64),
        np.asarray([e.time_done for e in val.events], dtype=np.int64),
        np.asarray([-1, *[e.correct for e in val.events[:-1]]], dtype=np.int64),
        np.asarray([e.source_row for e in val.events], dtype=np.int64), np.asarray([0, len(val.events)]),
        (val.user_id,) * len(val.events))
    scores = adapter.predict_details(inputs)
    model = load(saved)
    evaluated = evaluate_sakt(model, d, batch_size=3)
    assert evaluated['population']['evaluated_targets'] == evaluated['eligible_targets']
    assert evaluated['population']['unprocessed_eligible_targets'] == 0
    for row, score in zip(evaluated['predictions'], scores):
        assert row['reason'] == score.support_reason
        assert row['history_available'] == score.history_available and row['history_used'] == score.history_used
        assert row['context_reset'] == score.context_reset
        assert row['probability'] == pytest.approx(score.probability, abs=1e-7) if score.probability is not None else row['probability'] is None
    with pytest.raises(NotImplementedError): adapter.as_online_backend()


@pytest.mark.parametrize('field', ['domain', 'vocabulary', 'recipe', 'source', 'config'])
def test_expected_identity_changes_reject(artifact, field):
    _, saved, _ = artifact
    changed = deepcopy(saved['identity'])
    if field == 'domain': changed['data_identity']['domain'] = 'other'
    elif field == 'vocabulary': changed['data_identity']['vocabulary'] = ['B', 'A']
    elif field == 'recipe': changed['data_identity']['recipe']['context'] = 1
    elif field == 'source': changed['source_sha256']['new'] = '0' * 64
    else: changed['model_config']['d_model'] = 9
    with pytest.raises(ValueError): load(saved, expected_identity=changed)


@pytest.mark.parametrize('field', ['schema_bool', 'epoch', 'steps', 'targets', 'resume', 'fitted', 'optimizer', 'huge_geometry'])
def test_rehashed_sidecar_invalid_schema_or_counters_reject_before_torch_load(artifact, tmp_path, monkeypatch, field):
    _, saved, _ = artifact
    metadata = json.loads(saved['sidecar'].read_text(encoding='utf-8'))
    if field == 'schema_bool': metadata['identity']['schema_version'] = True
    elif field == 'epoch': metadata['completed_epoch'] = 2
    elif field == 'steps': metadata['optimizer_steps'] = 33
    elif field == 'targets': metadata['optimized_targets'] = 999
    elif field == 'resume': metadata['resume_supported'] = True
    elif field == 'fitted': metadata['fitted_research_model'] = True
    elif field == 'optimizer': metadata['identity']['training_config']['lr'] = -1
    else: metadata['identity']['model_config']['d_model'] = 10000
    altered = rewritten(tmp_path, saved, metadata=metadata)
    monkeypatch.setattr(checkpoint.torch, 'load', lambda *a, **k: pytest.fail('must reject metadata before deserialize'))
    with pytest.raises(ValueError): load(altered)


def test_checkpoint_payload_sha_and_budget_reject_before_deserialize(artifact, tmp_path, monkeypatch):
    _, saved, _ = artifact
    altered = rewritten(tmp_path, saved, state_bytes=saved['checkpoint'].read_bytes() + b'X')
    monkeypatch.setattr(checkpoint.torch, 'load', lambda *a, **k: pytest.fail('payload must reject first'))
    with pytest.raises(ValueError, match='payload'): load(altered)
    with pytest.raises(ValueError, match='payload'): load(saved, max_checkpoint_bytes=1)
    with pytest.raises(ValueError, match='sidecar'): load(saved, expected_sidecar_sha256='0' * 64)


def test_single_hashed_payload_is_actual_deserialize_argument(artifact, monkeypatch):
    _, saved, _ = artifact
    original = torch.load
    authorized = saved['checkpoint'].read_bytes()
    def inspect_payload(buffer, **kwargs):
        assert isinstance(buffer, io.BytesIO) and buffer.getvalue() == authorized
        assert kwargs == {'weights_only': True, 'map_location': 'cpu'}
        return original(buffer, **kwargs)
    monkeypatch.setattr(checkpoint.torch, 'load', inspect_payload)
    load(saved)


def test_cpu_constructor_under_meta_default_and_caller_rng_preserved(artifact):
    _, saved, _ = artifact
    rng = torch.get_rng_state().clone()
    with torch.device('meta'): model = load(saved)
    assert all(p.device.type == 'cpu' for p in model.parameters())
    assert torch.equal(rng, torch.get_rng_state())


def test_exclusive_output_and_mutated_model_reject(artifact, tmp_path):
    result, saved, _ = artifact
    with pytest.raises(FileExistsError): checkpoint.save_engineering_weights(saved['checkpoint'], result)
    loaded = load(saved)
    with torch.no_grad(): next(loaded.parameters()).add_(1)
    forged = replace(result, model=loaded)
    with pytest.raises(ValueError, match='unchanged'): checkpoint.save_engineering_weights(tmp_path / 'mutated.pt', forged)
    with pytest.raises(ValueError, match='outputs'): checkpoint.save_engineering_weights(Path.cwd() / 'dataset/forbidden.pt', result)
