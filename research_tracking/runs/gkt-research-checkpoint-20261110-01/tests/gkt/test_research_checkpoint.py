"""Candidate kiểm checkpoint GKT29; CHƯA chạy hoặc cấp phép native.

Typed corpus dựng tay, không collector/publication/fitted baseline. Fixture dùng
2 models/2 Adam và 3 complete epoch calls, mỗi call8learners×4events/2batches.
Tổng6 actual updates/6 forwards/96 target exposures nếu toàn fixture hoàn tất.
Negatives chỉ serialize/validate, không thêm neural update. ROOT cấp budget và
đếm calls riêng trước chạy; danh sách dưới đây không phải kết quả đã nghiệm thu.
"""
from dataclasses import replace
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import random
import sys
from types import SimpleNamespace

import numpy as np
import pytest
import torch


ROOT = Path(__file__).resolve().parents[2]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
    return module


import knowledge_tracing.gkt.research_checkpoint as cp
old_path = sys.path[:]
try:
    sys.path.insert(0, str(ROOT/'tests/gkt'))
    helper = _load('gkt_checkpoint_handmade_helpers', ROOT/'tests/gkt/test_research_training.py')
    data_helper = sys.modules['test_research_data']
    assert Path(data_helper.__file__).resolve() == ROOT/'tests/gkt/test_research_data.py'
finally:
    sys.path[:] = old_path


def caller_rng():
    ns = np.random.get_state()
    return dict(python=random.getstate(), numpy=(ns[0], ns[1].tolist(), *ns[2:]), torch=torch.get_rng_state().clone())


def handmade_public():
    old = helper.data_fixture()
    protocol = hashlib.sha256((ROOT/'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md').read_bytes()).hexdigest()
    plan = replace(old.plan, protocol_sha256=protocol)
    roles = tuple(data_helper.role_data(plan, old.bank, old.limits, role.role, tuple(
        replace(t, plan_sha256=plan.split_plan.identity) for t in role.trajectories)) for role in old.roles)
    return data_helper.seal(replace(old, plan=plan, roles=roles))


@pytest.fixture(scope='module')
def completed(tmp_path_factory):
    prepared = helper.view(handmade_public())
    root = tmp_path_factory.mktemp('gktcp')
    own = root/'artifacts/akt/local-tests/handmade'; own.mkdir(parents=True)
    doc = root/'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md'
    doc.parent.mkdir(parents=True)
    doc.write_bytes((ROOT/'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md').read_bytes())
    previous_root, threads = cp.ROOT, torch.get_num_threads()
    cp.ROOT = root
    try:
        torch.set_num_threads(2)
        with torch.random.fork_rng(devices=[]):
            native = helper.model(prepared)
            initial = cp._clone(dict(native.state_dict()))
            native.eval()
            optimizer, used, budget = helper.adam(native), helper.progress(native), helper.budget()
            spec = helper.rt.GKTResearchSpec(1, 4, 1.)
            profile = cp.GKTCheckpointProfile(prepared.phase.shards[0].plan.protocol_sha256,
                'b'*64, 'c'*64, cp.state_digest(native), 'HANDMADE_NOT_RUNTIME_OR_FIT_AUTHORITY')
            limits = cp.GKTCheckpointLimits(8*2**20, 2**18, 8*2**20)
            before = caller_rng()
            result = helper.rt.train_research_epoch(native, prepared, optimizer=optimizer,
                spec=spec, budget=budget, progress=used)
            assert cp._same(caller_rng(), before)
            identity = cp.research_checkpoint_identity(native, prepared, spec, optimizer, budget=budget, profile=profile)
            reference = cp.save_epoch_state(own/'epoch1', native, prepared, spec, optimizer, budget=budget,
                progress=used, epoch_result=result, profile=profile, expected_identity=identity, limits=limits)
            assert cp._same(caller_rng(), before)
            payload = torch.load(io.BytesIO((reference['directory']/'state.pt').read_bytes()),
                                 map_location='cpu', weights_only=True)
            second = helper.rt.train_research_epoch(native, prepared, optimizer=optimizer,
                spec=replace(spec, epoch=2), budget=budget, progress=used)
            fresh = helper.model(prepared); fresh.train()
            fresh_optimizer = helper.adam(fresh)
            yield SimpleNamespace(view=prepared, root=root, own=own, model=native, optimizer=optimizer,
                progress=used, spec=spec, budget=budget, profile=profile, limits=limits, initial=initial,
                result=result, second=second, identity=identity, reference=reference, payload=payload,
                fresh=fresh, fresh_optimizer=fresh_optimizer)
    finally:
        cp.ROOT = previous_root
        torch.set_num_threads(threads)


def restore(f, directory=None, complete_sha=None, **changes):
    values = dict(budget=f.budget, fresh_progress=helper.progress(f.fresh), profile=f.profile,
                  expected_identity=f.identity, expected_complete_sha256=complete_sha or f.reference['complete_sha256'], limits=f.limits)
    values.update(changes)
    return cp.restore_epoch_state(directory or f.reference['directory'], f.fresh, f.view, f.spec,
                                  f.fresh_optimizer, **values)


def authenticated_payload(f, path, mutate):
    payload = cp._clone(f.payload)
    mutate(payload)
    with io.BytesIO() as buffer:
        torch.save(payload, buffer)
        raw = buffer.getvalue()
    meta = json.loads((f.reference['directory']/'metadata.json').read_bytes())
    meta.update(checkpoint_sha256=cp._hash(raw), checkpoint_bytes=len(raw))
    # Authenticated corrupted state: bypass only byte checks, NOT semantic validators.
    if set(payload['model']) == set(f.payload['model']):
        meta['model_sha256'] = cp.state_digest(SimpleNamespace(state_dict=lambda: payload['model']))
    encoded = (json.dumps(meta, sort_keys=True)+'\n').encode()
    complete = (json.dumps(dict(schema_version=1, status='COMPLETE_GKT_EPOCH_STATE',
        metadata_sha256=cp._hash(encoded), checkpoint_sha256=cp._hash(raw)), sort_keys=True)+'\n').encode()
    path.mkdir()
    for name, value in (('state.pt', raw), ('metadata.json', encoded), ('COMPLETE.json', complete)):
        (path/name).write_bytes(value)
    return cp._hash(complete)


@pytest.mark.parametrize('field,value', [('protocol_sha256', 'z'*64), ('runtime_sha256', ''),
    ('initial_model_sha256', 'A'*64), ('run_reference', '')])
def test_profile_rejects_invalid_bindings(field, value):
    values = dict(protocol_sha256='a'*64, runtime_sha256='b'*64, profile_sha256='c'*64,
                  initial_model_sha256='d'*64, run_reference='handmade')
    values[field] = value
    with pytest.raises(ValueError):
        cp.GKTCheckpointProfile(**values)


@pytest.mark.parametrize('value', [0, -1, True])
def test_limits_are_explicit_positive_integers(value):
    with pytest.raises(ValueError):
        cp.GKTCheckpointLimits(value, 1000, 1000)


def test_saved_identity_excludes_fitted_and_global_rng_claims(completed):
    f = completed
    assert f.identity['restore_scope'] == 'completed_epoch_only'
    assert f.identity['rng_semantics'] == 'owned_progress_cpu_dropout_only_caller_global_rng_unchanged'
    assert not f.identity['fitted_research_model'] and not f.identity['lifecycle_resume_supported']
    assert f.payload['counters']['complete_train_epochs'] == 1
    assert f.payload['counters']['adam_returned'] == 2


@pytest.mark.parametrize('kind', ['missing_adam', 'negative_second', 'overcount', 'adjacency',
                                 'bn_variance', 'bn_counter', 'rng', 'mode_bool', 'extra_model', 'gradient_state'])
def test_authenticated_malformed_state_rejected_before_mutation(completed, kind):
    f = completed
    def mutate(payload):
        if kind == 'missing_adam':
            payload['adam']['state'].clear()
        elif kind == 'negative_second':
            next(iter(payload['adam']['state'].values()))['exp_avg_sq'].fill_(-1)
        elif kind == 'overcount':
            next(iter(payload['adam']['state'].values()))['step'].fill_(3)
        elif kind == 'adjacency':
            payload['model']['adjacency'][0, 1] = 0
        elif kind == 'bn_variance':
            payload['model']['self_mlp.bn.running_var'][0] = -1
        elif kind == 'bn_counter':
            payload['model']['self_mlp.bn.num_batches_tracked'].fill_(-1)
        elif kind == 'rng':
            payload['owned_rng'] = torch.zeros(2, dtype=torch.uint8)
        elif kind == 'mode_bool':
            payload['module_modes'][0] = ('', 1)
        elif kind == 'extra_model':
            payload['model']['unregistered'] = torch.zeros(1)
        else:
            next(iter(payload['adam']['state'].values()))['exp_avg'].requires_grad_(True)
    path = f.own/('invalid-'+kind)
    complete = authenticated_payload(f, path, mutate)
    before, caller = cp._clone(dict(f.fresh.state_dict())), caller_rng()
    with pytest.raises((ValueError, RuntimeError)):
        restore(f, path, complete)
    assert cp._same(dict(f.fresh.state_dict()), before)
    assert not f.fresh_optimizer.state and cp._same(caller_rng(), caller)


def test_wrong_identity_and_partial_members_refuse_load(completed):
    f = completed
    bad = dict(f.identity, encoding_sha256='0'*64)
    with pytest.raises(ValueError, match='identity'):
        restore(f, expected_identity=bad)
    path = f.own/'partial'; path.mkdir()
    (path/'state.pt').write_bytes(b'partial')
    with pytest.raises(ValueError, match='partial'):
        restore(f, directory=path)
    assert not f.fresh_optimizer.state


def test_incomplete_or_poisoned_epoch_cannot_save(completed):
    f = completed
    identity = cp.research_checkpoint_identity(f.model, f.view, replace(f.spec, epoch=2), f.optimizer,
                                               budget=f.budget, profile=f.profile)
    for changes in ({'complete': False}, {'pending_batch_keys': (('pending', 1, 0),)}):
        with pytest.raises(ValueError, match='complete'):
            cp.save_epoch_state(f.own/'never-partial', f.model, f.view, replace(f.spec, epoch=2), f.optimizer,
                budget=f.budget, progress=f.progress, epoch_result=dict(f.second, **changes),
                profile=f.profile, expected_identity=identity, limits=f.limits)
    assert not (f.own/'never-partial').exists()
    f.progress.poisoned = True
    try:
        with pytest.raises(ValueError, match='healthy'):
            cp.save_epoch_state(f.own/'never-poisoned', f.model, f.view, replace(f.spec, epoch=2), f.optimizer,
                budget=f.budget, progress=f.progress, epoch_result=f.second,
                profile=f.profile, expected_identity=identity, limits=f.limits)
    finally:
        f.progress.poisoned = False
    assert not (f.own/'never-poisoned').exists()


@pytest.mark.parametrize('kind', ['absent', 'empty', 'older_positive', 'zero_initialized'])
def test_participation_format_does_not_copy_sakt_allsteps_assumption(completed, kind):
    # Format unit fixture: không nói các state sửa tay này do epoch thật sinh ra.
    f = completed
    opt = cp._clone(f.payload['adam'])
    number = next(iter(opt['state']))
    if kind == 'absent':
        opt['state'].pop(number)
    elif kind == 'empty':
        opt['state'][number] = {}
    elif kind == 'older_positive':
        opt['state'][number]['step'].fill_(1)
    else:
        for value in opt['state'][number].values():
            value.zero_()
    _, witness = cp._states(f.fresh, f.fresh_optimizer, f.payload['model'], opt,
                            f.payload['counters'], f.limits)
    names = [name for name, _ in f.fresh.named_parameters()]
    name = names[opt['param_groups'][0]['params'].index(number)]
    status = {'absent': 'absent', 'empty': 'empty', 'older_positive': 'state', 'zero_initialized': 'state'}[kind]
    assert next(row for row in witness if row[0] == name)[1:] == [status, int(kind == 'older_positive')]


def test_checkpoint_size_cap_rejects_before_deserialization(completed):
    f = completed
    with pytest.raises(ValueError, match='byte cap'):
        restore(f, limits=replace(f.limits, max_checkpoint_bytes=1))
    assert not f.fresh_optimizer.state


def test_protocol_contradiction_rejects_identity_factory(completed):
    f = completed
    with pytest.raises(ValueError, match='protocol'):
        cp.research_checkpoint_identity(f.fresh, f.view, f.spec, f.fresh_optimizer,
            budget=f.budget, profile=replace(f.profile, protocol_sha256='0'*64))


def test_failed_mutator_poison_requires_discard(completed, monkeypatch):
    f = completed
    progress = helper.progress(f.fresh)
    state = cp._clone(dict(f.fresh.state_dict()))
    def failure(*args, **kwargs):
        raise RuntimeError('explicit synthetic mutator failure')
    with monkeypatch.context() as patch:
        patch.setattr(f.fresh, 'load_state_dict', failure)
        with pytest.raises(RuntimeError, match='mutator failure'):
            restore(f, fresh_progress=progress)
    assert progress.poisoned and not f.fresh_optimizer.state
    assert cp._same(dict(f.fresh.state_dict()), state)


def test_restore_dropout_bn_adam_and_complete_next_epoch(completed):
    f = completed
    caller = caller_rng()
    try:
        restored = restore(f)
        assert cp._same(caller_rng(), caller)
        assert torch.equal(restored.rng_state, f.payload['owned_rng'])
        assert [(name, module.training) for name, module in f.fresh.named_modules()] == f.payload['module_modes']
        assert cp._same(dict(f.fresh.state_dict()), f.payload['model'])
        assert cp._same(f.fresh_optimizer.state_dict(), f.payload['adam'])
        assert not restored.poisoned
        result = helper.rt.train_research_epoch(f.fresh, f.view, optimizer=f.fresh_optimizer,
            spec=replace(f.spec, epoch=2), budget=f.budget, progress=restored)
        assert result['complete'] and result['counters'] == f.second['counters']
        assert cp._same(dict(f.fresh.state_dict()), dict(f.model.state_dict()))
        assert cp._same(f.fresh_optimizer.state_dict(), f.optimizer.state_dict())
        assert torch.equal(restored.rng_state, f.progress.rng_state)
        assert cp._same(caller_rng(), caller)
    finally:
        # Tái lập fresh fixture cho thứ tự test bất kỳ; không extra forward/update.
        f.fresh.load_state_dict(f.initial, strict=True)
        f.fresh_optimizer.state.clear()
        f.fresh.train()
