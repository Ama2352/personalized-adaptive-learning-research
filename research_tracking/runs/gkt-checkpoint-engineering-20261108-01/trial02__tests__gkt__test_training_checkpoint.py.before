"""Weights-only toy persistence; one shared actual Adam update, hard cap4."""
import copy
from dataclasses import replace
import hashlib
import io
import json
import os
from pathlib import Path
import time

import pytest
import torch

from knowledge_tracing.gkt import GKTBinding, GKTKernelConfig
from knowledge_tracing.gkt.recurrent import GKTStaticRecurrentCandidate, RECIPE_ID, GRU_VARIANT, EVIDENCE_ROLE
from knowledge_tracing.gkt import training as tr
from knowledge_tracing.gkt import training_checkpoint as cp


@pytest.fixture(scope='module', autouse=True)
def bounded_cpu(tmp_path_factory):
    ledger = Path(os.environ.get('GKT_CHECKPOINT_UPDATE_LEDGER', tmp_path_factory.getbasetemp() / 'updates.jsonl'))
    original = torch.optim.Adam.step; threads = torch.get_num_threads(); torch.set_num_threads(2)
    def counted(optimizer, *args, **kwargs):
        rows = ledger.read_text().splitlines() if ledger.exists() else []
        assert len(rows) < 4, 'checkpoint suite optimizer budget exhausted BEFORE update'
        with ledger.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'update': len(rows) + 1, 'monotonic': time.perf_counter()}) + '\n')
        return original(optimizer, *args, **kwargs)
    torch.optim.Adam.step = counted
    try:
        with torch.random.fork_rng(devices=[]):
            torch.random.default_generator.manual_seed(42)
            yield
    finally:
        torch.optim.Adam.step = original; torch.set_num_threads(threads)


@pytest.fixture(scope='module')
def artifact(tmp_path_factory):
    c = GKTKernelConfig(3, 2, 2, 2, 'static', 'concept', True, True)
    binding = GKTBinding('toy-checkpoint-not-research-domain', 'a' * 64, ('A', 'B', 'C'), 'concept')
    adjacency = torch.tensor([[0., .5, 0.], [.2, 0., .3], [0., .4, 0.]], dtype=torch.float64, device='cpu')
    model = GKTStaticRecurrentCandidate(c, binding, adjacency, recipe_id=RECIPE_ID, mlp_hidden_dim=3,
        normalization='none', dropout=0, initial_state_policy='zeros', gru_variant=GRU_VARIANT)
    settings = tr.GKTTrainingSettings('adam', .01, (.8, .9), 1e-7, 0., .5,
                                      'mean_bce_on_explicit_loss_mask', 'float64')
    optimizer = torch.optim.Adam(model.parameters(), lr=settings.lr, betas=settings.betas, eps=settings.eps,
                                  weight_decay=settings.weight_decay, foreach=False, fused=False)
    ids = torch.tensor([[0, 1, 2, 0]], device='cpu'); mask = torch.ones_like(ids, dtype=torch.bool)
    batch = tr.bind_train_batch(query_ids=ids, responses=torch.tensor([[0, 1, 1, 0]], device='cpu'),
        event_valid_mask=mask, loss_mask=mask, initial_state=model.initial_state(1, binding=binding, graph_sha256=model.graph_sha256),
        learner_ids=('handmade-one',), source_rows=torch.tensor([[1, 2, 3, 4]], device='cpu'),
        global_ranks=torch.tensor([[0, 1, 2, 3]], device='cpu'), binding=binding,
        graph_sha256=model.graph_sha256, recipe_sha256=model.recipe_sha256,
        initial_state_model_sha256=tr.model_digest(model), role=tr.TRAIN_ROLE, synthetic_only=True,
        source_sha256=tr.source_identity())
    result = tr.train_gkt_batch(model, optimizer, batch, settings=settings,
        budget=tr.GKTStepBudget(4, 16, 60., 0, 0, time.perf_counter()))
    parent = tmp_path_factory.mktemp('weights')
    saved = cp.save_engineering_weights(parent / 'completed', model, result,
        approval_reference='USER_GKT04_TOY_ENGINEERING_NOT_FITTED', max_checkpoint_bytes=1_000_000)
    return model, result, batch, saved


def load(saved, **changes):
    args = dict(expected_manifest_sha256=saved['manifest_sha256'], expected_identity=saved['identity'],
                max_checkpoint_bytes=1_000_000)
    args.update(changes)
    return cp.load_engineering_weights(saved['directory'], **args)


def modified(tmp_path, saved, *, state=None, metadata_change=None, manifest_change=None):
    directory = tmp_path / 'modified'; directory.mkdir()
    payload = (saved['directory'] / 'weights.pt').read_bytes()
    if state is not None:
        buffer = io.BytesIO(); torch.save(state, buffer); payload = buffer.getvalue()
    metadata = json.loads((saved['directory'] / 'metadata.json').read_bytes())
    if metadata_change: metadata_change(metadata)
    meta = cp._json(metadata)
    manifest = dict(schema_version=1, status='COMPLETE_ENGINEERING_WEIGHTS_ONLY', files={
        'weights.pt': dict(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest()),
        'metadata.json': dict(bytes=len(meta), sha256=hashlib.sha256(meta).hexdigest())})
    if manifest_change: manifest_change(manifest)
    complete = cp._json(manifest)
    for name, raw in [('weights.pt', payload), ('metadata.json', meta), ('COMPLETE.json', complete)]:
        (directory / name).write_bytes(raw)
    return {**saved, 'directory': directory, 'manifest_sha256': hashlib.sha256(complete).hexdigest()}


def test_completed_weights_reload_exact_graph_predictions_no_resume(artifact):
    model, result, batch, saved = artifact
    loaded = load(saved); restored = loaded.model
    assert tr.model_digest(restored) == result.model_sha256_after == tr.model_digest(model)
    assert torch.equal(restored.adjacency, model.adjacency)
    assert loaded.identity['flags'] == cp.FLAGS and loaded.identity['weight_role'] == tr.WEIGHT_ROLE
    assert loaded.identity['trained_step']['optimizer_steps'] == 1
    assert not restored.training and not hasattr(loaded, 'optimizer') and not hasattr(loaded, 'hidden_state')
    assert (saved['directory'] / 'COMPLETE.json.pending').exists()  # Final publication has no cleanup after commit.
    outputs = []
    for network in (model, restored):
        state = network.initial_state(1, binding=network.binding, graph_sha256=network.graph_sha256)
        outputs.append(network.sequence(batch.query_ids, batch.responses, batch.event_valid_mask,
            initial_state=state, binding=network.binding, graph_sha256=network.graph_sha256))
    assert torch.equal(outputs[0].logits, outputs[1].logits)
    assert torch.equal(outputs[0].probabilities, outputs[1].probabilities)
    assert outputs[1].evidence_role == EVIDENCE_ROLE  # No invented fitted inference role promotion.


def test_cpu_default_meta_and_constructor_rng_preserved(artifact, monkeypatch):
    saved = artifact[3]; rng = torch.random.get_rng_state().clone(); old = torch.get_default_device()
    monkeypatch.setattr(torch.cuda, 'manual_seed_all', lambda *a, **k: pytest.fail('no CUDA RNG mutation'))
    monkeypatch.setattr(torch.cuda, 'is_available', lambda: pytest.fail('no CUDA device query'))
    try:
        torch.set_default_device('meta')
        loaded = load(saved)
    finally:
        torch.set_default_device(old)
    assert torch.equal(torch.random.get_rng_state(), rng)
    assert all(p.device.type == 'cpu' for p in loaded.model.parameters())


@pytest.mark.parametrize('case', ['domain', 'nodes', 'vocabulary', 'graph', 'config', 'source', 'recipe',
    'optimizer_saved', 'rng_saved', 'hidden_saved', 'resume', 'fitted', 'numeric_false', 'epoch', 'steps', 'role'])
def test_identity_drift_rejected_before_deserialize(artifact, case, monkeypatch):
    saved = artifact[3]; identity = copy.deepcopy(saved['identity'])
    if case == 'domain': identity['binding']['domain'] = 'Grade10'
    elif case == 'nodes': identity['binding']['node_ids'].reverse()
    elif case == 'vocabulary': identity['binding']['vocabulary_sha256'] = 'b' * 64
    elif case == 'graph': identity['graph_sha256'] = 'b' * 64
    elif case == 'config': identity['model_config']['state_dim'] = 9
    elif case == 'source': identity['source_sha256'] = {}
    elif case == 'recipe': identity['recipe']['normalization'] = 'batchnorm'
    elif case == 'optimizer_saved': identity['flags']['optimizer_saved'] = True
    elif case == 'rng_saved': identity['flags']['rng_saved'] = True
    elif case == 'hidden_saved': identity['flags']['hidden_state_saved'] = True
    elif case == 'resume': identity['flags']['resume_supported'] = True
    elif case == 'fitted': identity['flags']['fitted_research_model'] = True
    elif case == 'numeric_false': identity['flags']['optimizer_saved'] = 0
    elif case == 'epoch': identity['flags']['completion_unit'] = 'epoch'
    elif case == 'steps': identity['trained_step']['optimizer_steps'] = True
    elif case == 'role': identity['weight_role'] = 'research_fitted'
    monkeypatch.setattr(cp.torch, 'load', lambda *a, **k: pytest.fail('identity before deserialize'))
    with pytest.raises(ValueError): load(saved, expected_identity=identity)


@pytest.mark.parametrize('case', ['missing_key', 'extra_key', 'shape', 'dtype', 'nonfinite', 'not_tensor', 'graph'])
def test_serialized_state_strict_tensor_contract(artifact, tmp_path, case):
    model, _, _, saved = artifact
    state = {k: v.detach().clone() for k, v in model.state_dict().items()}; key = 'readout_weight'
    if case == 'missing_key': state.pop(key)
    elif case == 'extra_key': state['unregistered'] = torch.tensor([1.], device='cpu')
    elif case == 'shape': state[key] = state[key][:1]
    elif case == 'dtype': state[key] = state[key].float()
    elif case == 'nonfinite': state[key][0] = float('nan')
    elif case == 'not_tensor': state[key] = [1, 2]
    elif case == 'graph': state['adjacency'][0, 1] += .1
    forged = modified(tmp_path, saved, state=state)
    with pytest.raises(ValueError): load(forged)


def test_digest_validation_checks_bound_buffer_and_payload(artifact, tmp_path, monkeypatch):
    saved = artifact[3]; forged = modified(tmp_path, saved)
    (forged['directory'] / 'weights.pt').write_bytes(b'not authorized weights')
    monkeypatch.setattr(cp.torch, 'load', lambda *a, **k: pytest.fail('payload SHA before deserialize'))
    with pytest.raises(ValueError): load(forged)
    with pytest.raises(ValueError): load(saved, max_checkpoint_bytes=1)
    with pytest.raises(ValueError): load(saved, expected_manifest_sha256='b' * 64)


@pytest.mark.parametrize('case', ['path', 'row_bool', 'oversize'])
def test_manifest_allowlist_and_rows_before_deserialize(artifact, tmp_path, case, monkeypatch):
    def change(manifest):
        if case == 'path': manifest['files']['../outside.pt'] = manifest['files'].pop('weights.pt')
        elif case == 'row_bool': manifest['files']['weights.pt']['bytes'] = True
        elif case == 'oversize': manifest['files']['metadata.json']['bytes'] = 65537
    forged = modified(tmp_path, artifact[3], manifest_change=change)
    monkeypatch.setattr(cp.torch, 'load', lambda *a, **k: pytest.fail('manifest guard before deserialize'))
    with pytest.raises(ValueError): load(forged)


@pytest.mark.parametrize('case', ['bounded', 'zero', 'untrained', 'mutated_model', 'training_source', 'bad_loss'])
def test_save_requires_unchanged_ordinary_trained_receipt(artifact, tmp_path, case):
    model, result, _, _ = artifact
    if case == 'bounded': result = replace(result, status='bounded', complete_train_step=False)
    elif case == 'zero': result = replace(result, optimizer_steps=0)
    elif case == 'untrained': result = replace(result, role='untrained')
    elif case == 'mutated_model':
        model = copy.deepcopy(model)
        with torch.no_grad(): model.node_bias.add_(.1)
    elif case == 'training_source': result = replace(result, source_sha256={})
    elif case == 'bad_loss': result = replace(result, mean_loss=result.mean_loss + 1)
    destination = tmp_path / 'rejected'
    with pytest.raises(ValueError): cp.save_engineering_weights(destination, model, result,
        approval_reference='USER_GKT04_TOY', max_checkpoint_bytes=1_000_000)
    assert not destination.exists()


def test_save_exclusive_and_bounds(artifact, tmp_path):
    model, result, _, saved = artifact
    with pytest.raises(FileExistsError): cp.save_engineering_weights(saved['directory'], model, result,
        approval_reference='USER_GKT04_TOY', max_checkpoint_bytes=1_000_000)
    with pytest.raises(ValueError): cp.save_engineering_weights(tmp_path / 'too_small', model, result,
        approval_reference='USER_GKT04_TOY', max_checkpoint_bytes=1)
    with pytest.raises(ValueError): cp._directory(cp.PROJECT_ROOT / 'dataset' / 'forbidden')
    with pytest.raises(ValueError): cp._directory(cp.PROJECT_ROOT / 'artifacts/akt/local-tests')
    for value in (True, 0, 1024 * 1024 + 1):
        with pytest.raises(ValueError): load(saved, max_checkpoint_bytes=value)


def test_symlink_parent_contract_is_simulated_fail_closed(artifact, monkeypatch):
    directory = artifact[3]['directory']; original = Path.is_symlink
    monkeypatch.setattr(Path, 'is_symlink', lambda self: self == directory or original(self))
    with pytest.raises(ValueError, match='symlink'): load(artifact[3])


def test_partial_failure_before_complete_is_retained_and_rejected(artifact, tmp_path, monkeypatch):
    model, result, _, saved = artifact; directory = tmp_path / 'partial'; original = cp._publish
    def fail_complete(path, name, raw):
        if name == 'COMPLETE.json': raise OSError('injected before atomic COMPLETE publish')
        original(path, name, raw)
    monkeypatch.setattr(cp, '_publish', fail_complete)
    with pytest.raises(OSError): cp.save_engineering_weights(directory, model, result,
        approval_reference='USER_GKT04_TOY', max_checkpoint_bytes=1_000_000)
    assert (directory / 'weights.pt').is_file() and (directory / 'metadata.json').is_file()
    assert not (directory / 'COMPLETE.json').exists()
    with pytest.raises(ValueError): load({**saved, 'directory': directory})


def test_atomic_publish_never_overwrites_existing_destination(tmp_path):
    destination = tmp_path / 'COMPLETE.json'; destination.write_bytes(b'old immutable')
    with pytest.raises(FileExistsError): cp._publish(tmp_path, 'COMPLETE.json', b'new')
    assert destination.read_bytes() == b'old immutable'
    assert (tmp_path / 'COMPLETE.json.pending').read_bytes() == b'new'


def test_source_drift_before_load_and_actual_weights_only_cpu_call(artifact, monkeypatch):
    original = cp.torch.load; calls = []
    def checked(payload, **kwargs):
        assert isinstance(payload, io.BytesIO) and kwargs == dict(weights_only=True, map_location='cpu')
        calls.append(1); return original(payload, **kwargs)
    monkeypatch.setattr(cp.torch, 'load', checked)
    load(artifact[3]); assert len(calls) == 1
    monkeypatch.setattr(cp, 'source_identity', lambda: {})
    with pytest.raises(ValueError): load(artifact[3])
    assert len(calls) == 1
