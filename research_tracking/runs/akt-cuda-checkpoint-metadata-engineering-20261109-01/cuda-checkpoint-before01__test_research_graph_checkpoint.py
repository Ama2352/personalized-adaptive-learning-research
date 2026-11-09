"""GRAPH11: fixtures tự tạo; KHÔNG corpus/teacher/fitted certificate.

Pure subset: -k 'not native' (không construct model/optimizer).
Native subset dùng MỘT module fixture: 8 windows/48 targets, 2 batches complete
E1, 2 constructors/2 Adam, 4 actual updates total nếu có continuation. Hai calls
E2 chỉ là controlled partial continuation, tuyệt đối không complete epoch E2.
ROOT phải duyệt allocation/source/runtime trước chạy; file này chưa được chạy.
"""
from dataclasses import asdict, replace
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import random
import uuid
from unittest.mock import patch

import pytest

from knowledge_tracing.akt import research_graph_checkpoint as cp

H = 'a'*64
LIMITS = cp.GraphCheckpointLimits(64*1024**2, 1024**2, 64*1024**2)
NATIVE_PROOF = {}  # ROOT worker chỉ export JSON nhỏ; không giữ tensors ở đây.


def profile(initial=H):
    return cp.GraphCheckpointProfile(H, cp.RECIPE_SHA256, H, H, initial, H,
        'selected_fit_candidate', None)


def manufactured_identity():
    # Metadata-only inspector fixture; không giả ResearchGraphCondition/train attestation.
    return dict(schema_version=1, role=cp.ROLE, recipe=cp.RECIPE, recipe_sha256=cp.RECIPE_SHA256,
        config=dict(phase='simulator-research', device='cpu'), encoding={}, encoding_sha256=H,
        condition={}, condition_sha256=H, phase_index_sha256=H, phase_sha256=H,
        neural_binding=dict(phase_scope='select_train80'), profile=asdict(profile()),
        sources=[['manufactured-no-native-authority', H]], iterator_resume_supported=False,
        lifecycle_resume_supported=False, fitted_research_model=False, selection_state_saved=False,
        global_budget_saved=False)


def manufactured_files(tmp_path, monkeypatch):
    monkeypatch.setattr(cp, 'ROOT', tmp_path)
    monkeypatch.setattr(cp, 'source_inventory', lambda: (('manufactured-no-native-authority', H),))
    directory = tmp_path/'experiments/akt/results/handmade/checkpoints/epoch-1'
    directory.mkdir(parents=True)
    identity = manufactured_identity()
    receipt = dict(completed_epochs=1, optimizer_body_returns=2, optimized_targets=48,
        parameter_participation=[['backbone.weight', 2], ['alpha', 1]], phase_index_sha256=H,
        windows_sha256=H, targets_sha256=H, ordered_batches_sha256=H, epoch_steps=2, epoch_targets=48,
        model_sha256=H, optimizer_sha256=H)
    raw = b'NOT_A_TORCH_ARCHIVE_INSPECTOR_MUST_NOT_DESERIALIZE'
    metadata = dict(schema_version=1, role=cp.ROLE, identity=identity, receipt=receipt,
        producer_config=dict(run_id='handmade', output_dir='handmade', max_steps=2, max_seconds=30.,
            max_wall_seconds=30., max_rss_bytes=512*1024**2, min_available_ram_bytes=1024**3),
        layout=[['backbone.weight', 'alpha']], state_representation=[['alpha', 'initialized'], ['backbone.weight', 'initialized']],
        checkpoint_sha256=hashlib.sha256(raw).hexdigest(), checkpoint_bytes=len(raw),
        restore_scope='completed_epoch_boundary', iterator_resume_supported=False,
        lifecycle_resume_supported=False, fitted_research_model=False)
    def write(meta=metadata):
        (directory/'state.pt').write_bytes(raw)
        meta_raw = cp._raw(meta); (directory/'metadata.json').write_bytes(meta_raw)
        complete = cp._raw(dict(schema_version=1, status=cp.STATUS,
            metadata_sha256=hashlib.sha256(meta_raw).hexdigest(), checkpoint_sha256=hashlib.sha256(raw).hexdigest()))
        (directory/'COMPLETE.json').write_bytes(complete)
        return hashlib.sha256(complete).hexdigest()
    return directory, identity, metadata, write


@pytest.mark.parametrize('bad', [0, -1, True, 1.5, None])
def test_explicit_positive_limits(bad):
    with pytest.raises(ValueError): cp.GraphCheckpointLimits(bad, 100, 100)


@pytest.mark.parametrize('mutation', ['recipe', 'freeze', 'purpose'])
def test_profile_guard(mutation):
    changes = {'recipe': dict(protocol26_sha256=H), 'freeze': dict(external_system_freeze_sha256=H),
        'purpose': dict(purpose='engineering_only')}
    with pytest.raises(ValueError): replace(profile(), **changes[mutation])


def test_refit_requires_external_freeze_distinct_from_local_metadata():
    with pytest.raises(ValueError): replace(profile(), purpose='frozen_candidate_refit')
    assert replace(profile(), purpose='frozen_candidate_refit', external_system_freeze_sha256=H).purpose == 'frozen_candidate_refit'


@pytest.mark.parametrize('source_case', ['missing', 'contradictory', 'matching'])
def test_protocol21_profile_matches_actual_inventory_bytes(source_case):
    # Pure metadata consistency, không fake typed model/data factory.
    sources = () if source_case == 'missing' else ((cp.PROTOCOL21_PATH, 'b'*64 if source_case == 'contradictory' else H),)
    if source_case == 'matching': cp._check_protocol_profile(profile(), sources)
    else:
        with pytest.raises(ValueError): cp._check_protocol_profile(profile(), sources)


def test_inspector_is_bytes_only_not_torch_deserialization(tmp_path, monkeypatch):
    directory, identity, _, write = manufactured_files(tmp_path, monkeypatch)
    monkeypatch.setattr(cp, '_torch', lambda: pytest.fail('inspection must not import/deserialise Torch'))
    inspected = cp.inspect_graph_epoch_state(directory, expected_identity=identity,
        expected_complete_sha256=write(), limits=LIMITS)
    assert inspected.reference.directory == directory


@pytest.mark.parametrize('field,value', [('role', 'engineering_only'), ('fitted_research_model', True),
    ('iterator_resume_supported', True), ('lifecycle_resume_supported', True), ('restore_scope', 'mid_epoch')])
def test_authenticated_wrong_metadata_rejected_before_torch(tmp_path, monkeypatch, field, value):
    directory, identity, meta, write = manufactured_files(tmp_path, monkeypatch)
    meta[field] = value; complete_sha = write()
    monkeypatch.setattr(cp, '_torch', lambda: pytest.fail('metadata rejection must precede Torch'))
    with pytest.raises(ValueError):
        cp.inspect_graph_epoch_state(directory, expected_identity=identity, expected_complete_sha256=complete_sha, limits=LIMITS)


@pytest.mark.parametrize('extra', ['failure.json', 'state.pt.pending', 'unexpected.json'])
def test_partial_failed_extra_files(tmp_path, monkeypatch, extra):
    directory, identity, _, write = manufactured_files(tmp_path, monkeypatch)
    complete_sha = write(); (directory/extra).write_text('preserve failure', encoding='utf-8')
    with pytest.raises(ValueError, match='partial/failed/extra'):
        cp.inspect_graph_epoch_state(directory, expected_identity=identity, expected_complete_sha256=complete_sha, limits=LIMITS)


@pytest.mark.parametrize('which', ['external_complete', 'state_hash', 'metadata_hash', 'byte_cap', 'missing_complete'])
def test_byte_admission(tmp_path, monkeypatch, which):
    directory, identity, _, write = manufactured_files(tmp_path, monkeypatch)
    complete_sha = write(); limits = LIMITS
    if which == 'external_complete': complete_sha = H
    elif which == 'state_hash': (directory/'state.pt').write_bytes(b'altered')
    elif which == 'metadata_hash': (directory/'metadata.json').write_bytes(b'{}')
    elif which == 'missing_complete': (directory/'COMPLETE.json').unlink()
    else: limits = replace(limits, max_checkpoint_bytes=1)
    with pytest.raises(ValueError):
        cp.inspect_graph_epoch_state(directory, expected_identity=identity, expected_complete_sha256=complete_sha, limits=limits)


@pytest.mark.parametrize('change', ['wrong_phase', 'wrong_source', 'wrong_recipe', 'future_claim'])
def test_expected_identity_guards(tmp_path, monkeypatch, change):
    directory, identity, _, write = manufactured_files(tmp_path, monkeypatch)
    complete_sha = write(); identity = copy.deepcopy(identity)
    if change == 'wrong_phase': identity['neural_binding']['phase_scope'] = 'calibration_predict'
    elif change == 'wrong_source': identity['sources'][0][1] = 'b'*64
    elif change == 'wrong_recipe': identity['recipe'] = 'draft25'
    else: identity['selection_state_saved'] = True
    with pytest.raises(ValueError):
        cp.inspect_graph_epoch_state(directory, expected_identity=identity, expected_complete_sha256=complete_sha, limits=LIMITS)


@pytest.mark.parametrize('raw', [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1e999}'])
def test_strict_json(raw):
    with pytest.raises(ValueError): cp._decode(raw)


def test_junction_rejected_without_actual_junction(tmp_path, monkeypatch):
    monkeypatch.setattr(cp, 'ROOT', tmp_path)
    monkeypatch.setattr(Path, 'is_junction', lambda p: p.name == 'alias', raising=False)
    with pytest.raises(ValueError, match='alias'):
        cp._physical(tmp_path/'experiments/alias/checkpoint')


def test_named_participation_allows_late_branch_not_arbitrary_stale_step():
    assert cp._participation_rows([['backbone', 3], ['alpha', 1], ['gate', 0]], ['backbone', 'alpha', 'gate'], 3)['alpha'] == 1
    with pytest.raises(ValueError): cp._participation_rows([['alpha', 4]], ['alpha'], 3)
    with pytest.raises(ValueError): cp._participation_rows([['alpha', True]], ['alpha'], 3)


def _handmade():
    # Exact existing handmade fixture source is an explicit test dependency,
    # not a generated research corpus or external checkpoint dependency.
    path = Path(__file__).with_name('test_research_graph_model.py')
    spec = importlib.util.spec_from_file_location('_graph11_handmade_fixture_only', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.handmade()


@pytest.fixture(scope='module')
def native_case():
    import torch
    import numpy as np
    from knowledge_tracing.akt import research_graph_model as model, training
    case = _handmade()
    original_threads = torch.get_num_threads(); torch.set_num_threads(2)
    events = []; sinks = lambda event: events.append(copy.deepcopy(event))
    def construct(run_id):
        config = replace(case['config'], run_id=run_id,
            output_dir=case['config'].project_root/'experiments/akt/results'/run_id, max_steps=4)
        with torch.random.fork_rng(devices=[]), torch.device('cpu'):
            torch.random.default_generator.manual_seed(42)
            adapter = model.ResearchGraphAKTAdapter(config=config, encoding=case['encoding'],
                index=case['index'], condition=case['condition'])
        optimizer = torch.optim.Adam(adapter.native.parameters(), lr=config.lr, betas=config.betas,
            eps=config.eps, weight_decay=config.weight_decay)
        return adapter, optimizer
    run_id = 'graph11-handmade-'+uuid.uuid4().hex[:10]
    adapter, optimizer = construct(run_id)
    tracker = cp.GraphAdamParticipation(adapter, optimizer, event_sink=sinks)
    declared_profile = replace(profile(tracker.initial_backbone_sha256), protocol21_sha256=
        hashlib.sha256((adapter.config.project_root/cp.PROTOCOL21_PATH).read_bytes()).hexdigest())
    with pytest.raises(ValueError, match='protocol21 contradicts'):
        cp.graph_checkpoint_identity(config=adapter.config, encoding=case['encoding'], condition=case['condition'],
            index=case['index'], profile=profile(tracker.initial_backbone_sha256))
    identity = cp.graph_checkpoint_identity(config=adapter.config, encoding=case['encoding'],
        condition=case['condition'], index=case['index'], profile=declared_profile)
    # Predeclare grouping using only graph support metadata and frozen sampler43.
    # No loss/gradient/response-dependent favourable batch selection.
    inactive, active = [], []
    for entry in case['entries']:
        record = case['index'].for_windows((entry.window,))[0]
        supported = any(e is not None and any(p.support > 0 and p.confidence > 0 for p in e.audit.parents) for e in record)
        (active if supported else inactive).append(entry)
    assert len(active) == len(inactive) == 4
    permutation = list(range(8)); random.Random(adapter.config.seed+1).shuffle(permutation)
    factory_order = [None]*8
    for position, entry in zip(permutation, inactive+active): factory_order[position] = entry
    budget = dict(max_steps=2, max_targets=48, max_seconds=60., max_rss_bytes=1024**3,
        min_available_ram_bytes=2*1024**3)
    tracker.begin_epoch(1)
    stats = training.train_epoch(adapter, lambda: iter(factory_order), optimizer=optimizer, epoch=1,
        budget=budget, batch_factory=tracker.collate, progress_callback=tracker.progress)
    receipt = tracker.finish_epoch(stats)
    parent = adapter.config.output_dir/'checkpoints'; parent.mkdir(parents=True, exist_ok=False)
    reference = cp.save_graph_epoch_state(parent/'epoch-1', adapter=adapter, optimizer=optimizer,
        participation=tracker, epoch_receipt=receipt, expected_identity=identity, profile=declared_profile, limits=LIMITS)
    inspected = cp.inspect_graph_epoch_state(reference.directory, expected_identity=identity,
        expected_complete_sha256=reference.complete_sha256, limits=LIMITS)
    # Same-input native p/loss/count at E1, eval fork preserves training RNG/modes.
    def evaluate(current):
        from knowledge_tracing.akt.tensors import collate_windows
        modes = [(m, m.training) for m in current.native.modules()]
        windows = tuple(e.window for e in active)
        batch = collate_windows(windows, n_items=len(current.encoding.vocabulary.values), device='cpu',
            targets=[e.targets for e in active])
        evidence = current.index.for_windows(windows)
        try:
            with torch.random.fork_rng(devices=[]), torch.inference_mode():
                current.native.eval(); current.native.bind(batch, evidence, enabled=True)
                return tuple(v.detach().clone() for v in current.native(batch.q_data, batch.qa_data, batch.loss_targets))
        finally:
            current.native.clear_context()
            for m, flag in modes: m.training = flag
    expected_prediction = evaluate(adapter)
    # Keep authenticated E1 payload for validation negatives; no new optimizer.
    payload = torch.load(io.BytesIO((reference.directory/'state.pt').read_bytes()), weights_only=True, map_location='cpu')
    tracker.begin_epoch(2)
    partial_a = training.train_epoch(adapter, lambda: iter(active), optimizer=optimizer, epoch=2,
        budget=budget, batch_factory=tracker.collate, progress_callback=tracker.progress)
    with pytest.raises(ValueError, match='full phase'): tracker.finish_epoch(partial_a)
    control_model = {n: t.detach().clone() for n, t in adapter.native.state_dict().items()}
    control_optimizer = copy.deepcopy(optimizer.state_dict())
    fresh, fresh_optimizer = construct(run_id+'-restore')
    # Different output namespace is deliberately compatible numerical identity.
    assert cp.graph_checkpoint_identity(config=fresh.config, encoding=case['encoding'], condition=case['condition'],
        index=case['index'], profile=declared_profile) == identity
    initial_model = cp._state_sha(fresh.native.state_dict())
    pre_mutation_rejections, negative_binary_references = [], []
    # Hash-authenticated synthetic negatives: actual restore must reject BEFORE
    # either mutator, then SAME still-fresh containers accept valid E1. Six
    # exclusive artifacts remain on disk; buffers/tensors released each turn.
    for bad_kind in ('missing_positive', 'python_rng', 'numpy_rng', 'torch_rng', 'mode_bool', 'mode_name'):
        bad_payload = copy.deepcopy(payload)
        if bad_kind == 'missing_positive':
            number = next(n for n, s in bad_payload['optimizer_state_dict']['state'].items() if s['step'].item() == 2)
            del bad_payload['optimizer_state_dict']['state'][number]
        elif bad_kind == 'python_rng': bad_payload['rng']['python'] = (0, (), None)
        elif bad_kind == 'numpy_rng':
            state = bad_payload['rng']['numpy']; bad_payload['rng']['numpy'] = (state[0], state[1], 625, *state[3:])
        elif bad_kind == 'torch_rng': bad_payload['rng']['torch'] = 'NOT_A_CPU_BYTE_RNG_TENSOR'
        elif bad_kind == 'mode_bool':
            name, _ = bad_payload['module_modes'][0]; bad_payload['module_modes'][0] = (name, 1)
        else: bad_payload['module_modes'][0] = ('FOREIGN_MODULE', True)
        bad_buffer = io.BytesIO(); torch.save(bad_payload, bad_buffer); bad_raw = bad_buffer.getvalue()
        bad_meta = cp._decode(inspected.metadata_bytes)
        bad_meta['checkpoint_sha256'] = hashlib.sha256(bad_raw).hexdigest(); bad_meta['checkpoint_bytes'] = len(bad_raw)
        bad_directory = parent/('authenticated-invalid-'+bad_kind); bad_directory.mkdir(exist_ok=False)
        cp._publish(bad_directory, 'state.pt', bad_raw, LIMITS.max_checkpoint_bytes)
        bad_meta_raw = cp._raw(bad_meta)
        cp._publish(bad_directory, 'metadata.json', bad_meta_raw, LIMITS.max_metadata_bytes)
        bad_complete = cp._raw(dict(schema_version=1, status=cp.STATUS,
            metadata_sha256=hashlib.sha256(bad_meta_raw).hexdigest(), checkpoint_sha256=bad_meta['checkpoint_sha256']))
        cp._publish(bad_directory, 'COMPLETE.json', bad_complete, LIMITS.max_metadata_bytes)
        bad_inspected = cp.inspect_graph_epoch_state(bad_directory, expected_identity=identity,
            expected_complete_sha256=hashlib.sha256(bad_complete).hexdigest(), limits=LIMITS)
        with (patch.object(fresh.native, 'load_state_dict', side_effect=AssertionError('model mutation before validation')),
              patch.object(fresh_optimizer, 'load_state_dict', side_effect=AssertionError('optimizer mutation before validation'))):
            with pytest.raises(ValueError):
                cp.restore_graph_epoch_state(bad_inspected, fresh_adapter=fresh, fresh_owned_optimizer=fresh_optimizer,
                    expected_identity=identity, profile=declared_profile, limits=LIMITS, event_sink=sinks)
        assert cp._state_sha(fresh.native.state_dict()) == initial_model and not fresh_optimizer.state and fresh._optimizer is None
        pre_mutation_rejections.append(bad_kind)
        negative_binary_references.append(dict(kind=bad_kind,
            path=(bad_directory/'state.pt').relative_to(adapter.config.project_root).as_posix(),
            sha256=hashlib.sha256(bad_raw).hexdigest(), bytes=len(bad_raw)))
        del bad_payload, bad_buffer, bad_raw
    # Direct state witnesses: deliberately differ before restore, then compare
    # immediately AFTER restore and BEFORE any evaluation or continuation.
    random.seed(981); np.random.seed(982); torch.random.default_generator.manual_seed(983)
    for name, module in fresh.native.named_modules(): module.training = not dict(payload['module_modes'])[name]
    assert random.getstate() != payload['rng']['python']
    assert not np.array_equal(np.random.get_state()[1], np.asarray(payload['rng']['numpy'][1], dtype=np.uint32))
    assert not torch.equal(torch.get_rng_state(), payload['rng']['torch'])
    assert any(m.training != dict(payload['module_modes'])[n] for n, m in fresh.native.named_modules())
    restored = cp.restore_graph_epoch_state(inspected, fresh_adapter=fresh, fresh_owned_optimizer=fresh_optimizer,
        expected_identity=identity, profile=declared_profile, limits=LIMITS, event_sink=sinks)
    assert random.getstate() == payload['rng']['python']
    ns, saved_ns = np.random.get_state(), payload['rng']['numpy']
    assert ns[0] == saved_ns[0] and np.array_equal(ns[1], np.asarray(saved_ns[1], dtype=np.uint32)) and ns[2:] == saved_ns[2:]
    assert torch.equal(torch.get_rng_state(), payload['rng']['torch'])
    assert [(n, m.training) for n, m in fresh.native.named_modules()] == payload['module_modes']
    actual_prediction = evaluate(fresh)
    e1_counts = dict(restored.counts)
    restored.begin_epoch(2)
    partial_b = training.train_epoch(fresh, lambda: iter(active), optimizer=fresh_optimizer, epoch=2,
        budget=budget, batch_factory=restored.collate, progress_callback=restored.progress)
    with pytest.raises(ValueError, match='full phase'): restored.finish_epoch(partial_b)
    assert all(torch.equal(a, b) for a, b in zip(actual_prediction, expected_prediction))
    assert all(torch.equal(control_model[n], t) for n, t in fresh.native.state_dict().items())
    assert cp._optimizer_sha(control_optimizer) == cp._optimizer_sha(fresh_optimizer.state_dict())
    participation_distribution = {str(count): list(e1_counts.values()).count(count) for count in sorted(set(e1_counts.values()))}
    NATIVE_PROOF.update(role='handmade_complete_epoch_persistence_not_research_fit',
        completed_epoch=dict(epoch=1, targets=stats.valid_targets, windows=stats.windows_processed,
            batches=stats.batches, optimizer_steps=stats.optimizer_steps),
        parameter_participation_e1=e1_counts, participation_count_distribution_e1=participation_distribution,
        direct_three_rng_restored_after_deliberate_perturbation=True,
        all_module_modes_restored_after_deliberate_inversion=True,
        malformed_payloads_rejected_before_either_mutator=pre_mutation_rejections,
        valid_checkpoint=dict(directory=reference.directory.relative_to(adapter.config.project_root).as_posix(),
            complete_sha256=reference.complete_sha256, metadata_sha256=reference.metadata_sha256,
            checkpoint_sha256=reference.checkpoint_sha256,
            checkpoint_bytes=(reference.directory/'state.pt').stat().st_size),
        negative_binary_references=negative_binary_references,
        initial_backbone_sha256=declared_profile.initial_backbone_sha256,
        protocol21_sha256=declared_profile.protocol21_sha256,
        epoch1_prediction_loss_count_exact=True,
        continuous_model_sha256=cp._state_sha(control_model), restored_continuation_model_sha256=cp._state_sha(fresh.native.state_dict()),
        continuous_adam_sha256=cp._optimizer_sha(control_optimizer), restored_continuation_adam_sha256=cp._optimizer_sha(fresh_optimizer.state_dict()),
        continuation_scope='ONE_ACTIVE_BATCH_EACH_NOT_COMPLETE_EPOCH2',
        control_cumulative_bodies=tracker.returned, restored_cumulative_bodies=restored.returned,
        fitted_research_model=False, lifecycle_resume_supported=False)
    try:
        yield dict(adapter=adapter, optimizer=optimizer, tracker=tracker, restored=restored,
            fresh=fresh, fresh_optimizer=fresh_optimizer, profile=declared_profile, identity=identity,
            receipt=receipt, reference=reference, inspected=inspected, payload=payload, e1_counts=e1_counts,
            prediction=actual_prediction, expected_prediction=expected_prediction, stats=stats, events=events,
            control_model=control_model, control_optimizer=control_optimizer,
            pre_mutation_rejections=tuple(pre_mutation_rejections), direct_rng_modes_asserted=True)
    finally:
        tracker.close(); restored.close(); torch.set_num_threads(original_threads)


def test_native_complete_epoch_not_three_partial_calls(native_case):
    c = native_case
    assert c['stats'].complete and c['stats'].windows_processed == 8 and c['stats'].valid_targets == 48
    assert c['receipt'].completed_epochs == 1 and c['receipt'].epoch_steps == 2
    assert c['tracker'].last_receipt is None and c['restored'].last_receipt is None
    assert c['e1_counts']['alpha'] == c['e1_counts']['gate.weight'] == c['e1_counts']['gate.bias'] == 1
    assert c['receipt'].optimizer_body_returns == 2  # Late branch counter < global.
    assert len([e for e in c['events'] if e['kind'] == 'optimizer_started']) == 4
    assert len([e for e in c['events'] if e['kind'] == 'optimizer_body_returned']) == 4


def test_native_exact_e1_parity_and_controlled_partial_continuation(native_case):
    import torch
    c = native_case
    assert all(torch.equal(a, b) for a, b in zip(c['prediction'], c['expected_prediction']))
    assert all(torch.equal(c['control_model'][n], t) for n, t in c['fresh'].native.state_dict().items())
    assert cp._optimizer_sha(c['control_optimizer']) == cp._optimizer_sha(c['fresh_optimizer'].state_dict())
    assert c['fresh']._optimizer is c['fresh_optimizer']
    assert c['restored'].returned == c['tracker'].returned == 3


def test_native_authenticated_payload_rejected_before_either_container_mutation(native_case):
    assert native_case['pre_mutation_rejections'] == ('missing_positive', 'python_rng', 'numpy_rng', 'torch_rng', 'mode_bool', 'mode_name')


def test_native_direct_three_rng_and_all_module_modes_restore(native_case):
    assert native_case['direct_rng_modes_asserted'] is True


def test_native_ambient_float64_rejected_before_adam_body(native_case):
    import torch
    c = native_case
    before = cp._optimizer_sha(c['fresh_optimizer'].state_dict())
    previous = torch.get_default_dtype()
    try:
        torch.set_default_dtype(torch.float64)
        with pytest.raises(ValueError, match='FP32 default dtype required before Adam body'):
            cp._owned(c['fresh'], c['fresh_optimizer'])
    finally:
        torch.set_default_dtype(previous)
    assert cp._optimizer_sha(c['fresh_optimizer'].state_dict()) == before


@pytest.mark.parametrize('change', ['missing_positive', 'stale_positive', 'overcount', 'negative_second',
    'literal_none', 'duplicate_group', 'foreign_state', 'group_lr'])
def test_native_malformed_authenticated_optimizer_before_mutation(native_case, change):
    import torch
    c = native_case; saved = copy.deepcopy(c['payload']['optimizer_state_dict'])
    names = dict(zip(saved['param_groups'][0]['params'], [n for n, _ in c['adapter'].native.named_parameters()]))
    positive = next(i for i, name in names.items() if c['e1_counts'][name] == 2)
    if change == 'missing_positive': del saved['state'][positive]
    elif change == 'stale_positive': saved['state'][positive]['step'].fill_(1)
    elif change == 'overcount': saved['state'][positive]['step'].fill_(3)
    elif change == 'negative_second': saved['state'][positive]['exp_avg_sq'].reshape(-1)[0] = -1
    elif change == 'literal_none': saved['state'][positive] = None
    elif change == 'duplicate_group': saved['param_groups'][0]['params'][1] = saved['param_groups'][0]['params'][0]
    elif change == 'foreign_state': saved['state'][999999] = {}
    else: saved['param_groups'][0]['lr'] *= 2
    before_model = cp._state_sha(c['fresh'].native.state_dict()); before_opt = cp._optimizer_sha(c['fresh_optimizer'].state_dict())
    with pytest.raises(ValueError):
        cp._validate_states(c['fresh'], c['fresh_optimizer'], c['payload']['model_state_dict'], saved,
            counts=c['receipt'].parameter_participation, bodies=2,
            layout=cp._layout(c['fresh'], c['fresh_optimizer']), limits=LIMITS)
    assert cp._state_sha(c['fresh'].native.state_dict()) == before_model
    assert cp._optimizer_sha(c['fresh_optimizer'].state_dict()) == before_opt


def test_native_zero_gradient_participates_while_none_can_be_absent(native_case):
    c = native_case
    started = [e['active_names'] for e in c['events'] if e['kind'] == 'optimizer_started']
    assert 'gate.weight' not in started[0] and 'gate.weight' in started[1]
    # Alpha was exactly zero in the first active batch: gate gradient is a zero
    # tensor, yet native Adam created state and count1. No nonzero gain required.
    layout = cp._layout(c['adapter'], c['optimizer'])[0]
    number = c['payload']['optimizer_state_dict']['param_groups'][0]['params'][layout.index('gate.weight')]
    entry = c['payload']['optimizer_state_dict']['state'][number]
    assert entry['step'].item() == 1 and bool((entry['exp_avg'] == 0).all())


@pytest.mark.parametrize('representation', ['absent', 'empty'])
def test_native_legitimate_never_participated_adam_state(native_case, representation):
    c = native_case; saved = copy.deepcopy(c['payload']['optimizer_state_dict'])
    counts = dict(c['receipt'].parameter_participation)
    layout = cp._layout(c['fresh'], c['fresh_optimizer'])
    number = saved['param_groups'][0]['params'][layout[0].index('gate.bias')]
    counts['gate.bias'] = 0
    if representation == 'absent': del saved['state'][number]
    else: saved['state'][number] = {}
    # Validator-only manufactured state, NOT a saved completed-epoch receipt.
    _, actual = cp._validate_states(c['fresh'], c['fresh_optimizer'], c['payload']['model_state_dict'], saved,
        counts=list(counts.items()), bodies=2, layout=layout, limits=LIMITS)
    assert ('gate.bias', representation) in actual
