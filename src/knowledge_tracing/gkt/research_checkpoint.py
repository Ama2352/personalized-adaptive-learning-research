"""Candidate persistence cuối epoch GKT29 CPU FP32, chưa áp dụng canonical.

Caller sở hữu model/Adam/progress và admission. Chỉ lưu dropout RNG thuộc
progress, không đặt lại Python/NumPy/Torch RNG toàn cục. Không lifecycle,
stopper, sampler cursor hoặc quyền tăng budget. Các SHA profile là consistency
bindings, không chứng thực runtime. Restore lỗi sau mutation bắt buộc discard
cả ba containers; không rollback hoặc retry trên progress đã poisoned.
"""
from dataclasses import asdict, dataclass
import hashlib
import io
import json
import math
from pathlib import Path
from types import SimpleNamespace

import torch

from knowledge_tracing.akt import filesystem as filesystem_module
from knowledge_tracing.gkt import config as config_module, research_training as training
from knowledge_tracing.gkt.research_data import GKTResearchView
from knowledge_tracing.gkt.research_model import GKTResearchModel
from knowledge_tracing.sakt import research_checkpoint as shared
from knowledge_tracing.sakt.training import state_digest
from knowledge_tracing.simulator_bridge import identity_hash

ROOT = Path(config_module.__file__).resolve().parents[3]
ROLE = 'gkt_research_complete_epoch_state_no_lifecycle_authority'
_need, _sha, _count = shared._need, shared._sha, shared._count
_json, _closed, _decode = shared._json, shared._closed, shared._decode
_bytes, _hash, _publish = shared._bytes, shared._hash, shared._publish


@dataclass(frozen=True)
class GKTCheckpointProfile:
    protocol_sha256: str
    runtime_sha256: str
    profile_sha256: str
    initial_model_sha256: str
    run_reference: str

    def __post_init__(self):
        for name in ('protocol_sha256', 'runtime_sha256', 'profile_sha256', 'initial_model_sha256'):
            _sha(getattr(self, name))
        _need(type(self.run_reference) is str and bool(self.run_reference.strip()), 'run reference required')


@dataclass(frozen=True)
class GKTCheckpointLimits:
    max_checkpoint_bytes: int
    max_metadata_bytes: int
    max_tensor_bytes: int

    def __post_init__(self):
        for value in asdict(self).values():
            _count(value)
            _need(value > 0, 'positive explicit persistence caps required')


def source_identity():
    sources = dict(training.source_identity())
    for name, path in (('gkt/research_checkpoint.py', Path(__file__)),
                       ('sakt/research_checkpoint.py', Path(shared.__file__)),
                       ('akt/filesystem.py', Path(filesystem_module.__file__))):
        sources[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return tuple(sorted(sources.items()))


def research_checkpoint_identity(model, view, spec, optimizer, *, budget, profile):
    """Không object IDs; không state mutable, constructor hoặc authority mới."""
    _need(type(model) is GKTResearchModel and type(view) is GKTResearchView
          and type(spec) is training.GKTResearchSpec and type(budget) is training.GKTResearchBudget
          and type(profile) is GKTCheckpointProfile, 'exact checkpoint context types required')
    spec.__post_init__(); budget.__post_init__(); profile.__post_init__()
    view.assert_integrity()
    model._bound(model.binding, model.graph_sha256)
    training._optimizer(model, optimizer)
    sources = source_identity()
    protocol = hashlib.sha256((ROOT/'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md').read_bytes()).hexdigest()
    _need(profile.protocol_sha256 == view.phase.shards[0].plan.protocol_sha256 == protocol,
          'profile/public plan/source protocol mismatch')
    _need(view.phase.scope in ('select_train80', 'refit_union90')
          and model.spec.phase_scope == view.phase.scope == view.encoding.optimization_scope
          and model.spec.phase_sha256 == view.phase.identity == view.encoding.optimization_phase_sha256
          and model.spec.encoding_sha256 == view.encoding.identity
          and model.graph == view.graph and model.spec.sources_sha256 == training.model_source_identity()
          and model.spec.recipe_source_sha256 == dict(sources)['recipe29'], 'phase/encoding/graph/source mismatch')
    names = {id(parameter): name for name, parameter in model.named_parameters()}
    groups = [dict(parameters=[names[id(p)] for p in group['params']],
                   settings={k: v for k, v in group.items() if k != 'params'})
              for group in optimizer.param_groups]
    return _json(dict(schema_version=1, role=ROLE, model_binding_sha256=model.model_binding_sha256,
        model_spec=asdict(model.spec), config=asdict(model.config), graph=asdict(view.graph),
        adjacency_sha256=model.graph_sha256, view_sha256=view.identity, corpus_sha256=view.corpus_sha256,
        initial_dropout_rng_sha256=_rng(model.initial_dropout_rng_state),
        phase_scope=view.phase.scope, phase_sha256=view.phase.identity, encoding_sha256=view.encoding.identity,
        recipe=asdict(view.recipe), completed_epoch_spec=asdict(spec), optimizer_groups=groups,
        budget=asdict(budget), profile=asdict(profile), source_sha256=sources,
        rng_semantics='owned_progress_cpu_dropout_only_caller_global_rng_unchanged',
        restore_scope='completed_epoch_only', lifecycle_resume_supported=False, fitted_research_model=False))


def _path(directory):
    path = Path(directory).absolute()
    _need(ROOT.resolve() == ROOT.absolute(), 'physical project root required')
    roots = (ROOT/'experiments/gkt/results', ROOT/'artifacts/akt/local-tests')
    _need(any(path.is_relative_to(root) and len(path.relative_to(root).parts) >= 2 for root in roots),
          'owned GKT run checkpoint directory required')
    cursor = ROOT
    for part in ('', *path.relative_to(ROOT).parts):
        _need(part not in ('.', '..'), 'unsafe checkpoint path')
        cursor /= part
        _need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'path alias forbidden')
    _need(path.resolve() == path, 'ancestor alias forbidden')
    return path


def _counters(counters):
    _closed(counters, training._COUNTERS, 'exact progress counters required')
    for value in counters.values():
        _count(value)
    for prefix in ('model_calls', 'sequence', 'tail', 'backward', 'clip', 'adam'):
        _need(counters[prefix+'_started'] == counters[prefix+'_returned'], 'unreturned work at boundary')
    _need(0 < counters['complete_train_epochs'] <= counters['adam_returned'] <= counters['optimized_targets'],
          'completed epochs/steps/targets inconsistent')
    _need(counters['backward_returned'] == counters['clip_returned'] == counters['adam_returned']
          and counters['sequence_returned'] + counters['tail_returned'] == counters['model_calls_returned']
          and counters['sequence_returned'] >= counters['adam_returned']
          and counters['optimized_targets'] + counters['scored_targets'] <= counters['input_targets'],
          'cumulative compute counters inconsistent')


def _budget_counts(counters, view, budget):
    total = sum(len(t.observations) for t in view.phase.trajectories)
    epochs = counters['complete_train_epochs']
    _need(counters['adam_returned'] == epochs*((len(view.phase.trajectories)+3)//4)
          and counters['optimized_targets'] == epochs*total, 'cumulative complete optimization population mismatch')
    for count, cap in (('input_targets', 'max_input_targets'), ('input_prefix_events', 'max_prefix_events'),
                       ('model_calls_started', 'max_model_calls'), ('adam_started', 'max_optimizer_steps'),
                       ('optimized_targets', 'max_optimized_targets'), ('scored_targets', 'max_scored_targets')):
        _need(counters[count] <= getattr(budget, cap), 'saved cumulative budget exceeded')


def _clone(value):
    if type(value) is torch.Tensor:
        return value.detach().clone()
    if type(value) is dict:
        return {k: _clone(v) for k, v in value.items()}
    if type(value) in (list, tuple):
        return type(value)(_clone(v) for v in value)
    return value


def _same(left, right):
    if type(left) is torch.Tensor:
        return type(right) is torch.Tensor and left.dtype == right.dtype and torch.equal(left, right)
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(_same(v, right[k]) for k, v in left.items())
    if type(left) in (list, tuple):
        return len(left) == len(right) and all(_same(a, b) for a, b in zip(left, right))
    return left == right


def _rng(value):
    _need(type(value) is torch.Tensor and value.device.type == 'cpu' and value.dtype == torch.uint8
          and value.layout == torch.strided and value.ndim == 1, 'owned CPU dropout RNG tensor required')
    torch.Generator(device='cpu').set_state(value)
    return _hash(value.contiguous().numpy().tobytes())


def _modes(model, modes):
    _need(type(modes) is list and all(type(row) is tuple and len(row) == 2
          and type(row[0]) is str and type(row[1]) is bool for row in modes)
          and [name for name, _ in modes] == [name for name, _ in model.named_modules()]
          and len({mode for _, mode in modes}) == 1, 'exact coherent native module modes required')


def _tensor(value, *, shape, dtype=torch.float32):
    shared._tensor(value, shape=shape, dtype=dtype)
    _need(not value.requires_grad and value.grad_fn is None, 'detached serialized tensor required')


def _states(model, optimizer, state, opt, counters, limits):
    """Kiểm buffers và từng Adam parameter; không ép step bằng global step."""
    _counters(counters)
    expected = model.state_dict()
    _need(isinstance(state, dict) and list(state) == list(expected), 'registered state keys/order mismatch')
    total = 0
    for name, value in state.items():
        target = expected[name]
        _tensor(value, shape=target.shape, dtype=target.dtype)
        _need(target.dtype in (torch.float32, torch.int64), 'unsupported registered state dtype')
        if target.dtype == torch.int64 or name.endswith('running_var'):
            _need(bool((value >= 0).all()), 'negative BN variance/counter')
        if name == 'adjacency':
            _need(torch.equal(value, model.adjacency), 'checkpoint adjacency differs from fixed graph')
        total += value.numel()*value.element_size()
    _closed(opt, ('state', 'param_groups'), 'ordinary Adam payload schema')
    _need(type(opt['state']) is dict and type(opt['param_groups']) is list
          and len(opt['param_groups']) == len(optimizer.param_groups) == 1, 'one owned Adam group required')
    saved, actual = opt['param_groups'][0], optimizer.param_groups[0]
    _need(type(saved) is dict and type(saved.get('params')) is list
          and len(saved['params']) == len(actual['params'])
          and _json({k: v for k, v in saved.items() if k != 'params'})
          == _json({k: v for k, v in actual.items() if k != 'params'}), 'Adam group settings/order mismatch')
    ids = saved['params']
    for number in ids:
        _count(number)
    _need(len(set(ids)) == len(ids) and all(type(k) is int and k in ids for k in opt['state']),
          'duplicate/foreign Adam parameter index')
    names = {id(p): name for name, p in model.named_parameters()}
    participation = []
    for number, parameter in zip(ids, actual['params']):
        entry = opt['state'].get(number)
        status, steps = 'absent', 0
        if entry is not None:
            _need(type(entry) is dict, 'Adam entry must be dict')
            status = 'empty' if not entry else 'state'
            if entry:
                _closed(entry, ('step', 'exp_avg', 'exp_avg_sq'), 'ordinary Adam moment schema')
                _tensor(entry['step'], shape=torch.Size([]))
                step = entry['step'].item()
                _need(step.is_integer() and 0 <= step <= counters['adam_returned'], 'Adam count outside cumulative steps')
                steps = int(step)
                for key in ('exp_avg', 'exp_avg_sq'):
                    _tensor(entry[key], shape=parameter.shape)
                _need(bool((entry['exp_avg_sq'] >= 0).all()), 'negative Adam second moment')
                total += sum(v.numel()*v.element_size() for v in entry.values())
        _need(number not in opt['state'] or entry is not None, 'None is not absent Adam state')
        participation.append((names[id(parameter)], status, steps))
    _need(total <= limits.max_tensor_bytes, 'tensor byte cap')
    return total, _json(participation)


def _boundary(model, view, spec, optimizer, budget, progress, result):
    _need(type(progress) is training.GKTResearchProgress and not progress.poisoned, 'healthy typed progress required')
    counters = progress.counters
    _counters(counters)
    _budget_counts(counters, view, budget)
    before = result.get('counters_before', {}) if type(result) is dict else {}
    _closed(before, training._COUNTERS, 'epoch counters_before required')
    for value in before.values():
        _count(value)
    total = sum(len(t.observations) for t in view.phase.trajectories)
    prefixes = sum(len(t.observations)*(len(t.observations)-1)//2 for t in view.phase.trajectories)
    batches = (len(view.phase.trajectories)+3)//4
    _need(total > 0 and all(0 < len(t.observations) <= 210 for t in view.phase.trajectories), 'nonempty complete trajectories required')
    _need(result.get('status') == 'complete' and result.get('complete') is True
          and result.get('stop_reason') == 'epoch_complete' and result.get('role') == training.ROLE
          and result.get('rollback') is False and result.get('resume_supported') is False
          and result.get('fitted_research_model') is False and result.get('pending_batch_keys') == ()
          and result.get('cleanup_errors') == [] and result.get('unreturned_sequence_work') is None
          and result.get('original_module_modes_restored') is True, 'complete unambiguous epoch receipt required')
    deltas = dict(input_targets=total, input_prefix_events=prefixes, model_calls_started=batches,
        model_calls_returned=batches, sequence_started=batches, sequence_returned=batches,
        backward_started=batches, backward_returned=batches, clip_started=batches, clip_returned=batches,
        adam_started=batches, adam_returned=batches, optimized_targets=total, returned_sequence_observe_events=total,
        complete_train_epochs=1, tail_started=0, tail_returned=0, scored_targets=0)
    _need(all(counters[k]-before[k] == n for k, n in deltas.items())
          and counters['padded_readout_slots'] >= before['padded_readout_slots']
          and counters['complete_train_epochs'] == spec.epoch, 'epoch full-population/cumulative accounting mismatch')
    params = tuple((name, id(p), p.requires_grad) for name, p in model.named_parameters())
    _need(result.get('counters') == counters and result.get('spec') == asdict(spec)
          and result.get('view_sha256') == view.identity and result.get('source_sha256') == training.source_identity()
          and result.get('model_binding_sha256') == progress.model_binding_sha256 == model.model_binding_sha256
          and progress.parameter_identity == params and progress.optimizer_object_id == id(optimizer)
          and progress.sources_sha256 == training.source_identity()
          and result.get('budget_sha256') == progress.budget_sha256 == identity_hash(asdict(budget))
          and result.get('model_state_after') == state_digest(model)
          and result.get('owned_rng_sha256') == _rng(progress.rng_state), 'epoch receipt/current containers drift')
    elapsed = result.get('elapsed_seconds')
    _need(type(elapsed) in (int, float) and math.isfinite(elapsed) and 0 <= elapsed < budget.max_seconds,
          'late/nonfinite epoch verdict')


class _CappedBuffer(io.BytesIO):
    def __init__(self, cap):
        super().__init__()
        self.cap = cap

    def write(self, raw):
        _need(self.tell()+len(raw) <= self.cap, 'serialized checkpoint byte cap')
        return super().write(raw)


def save_epoch_state(directory, model, view, spec, optimizer, *, budget, progress, epoch_result,
                     profile, expected_identity, limits):
    """Lưu receipt của compute đã hoàn tất; không tự train hoặc chọn epoch."""
    _need(type(limits) is GKTCheckpointLimits, 'typed persistence limits required')
    limits.__post_init__()
    identity = research_checkpoint_identity(model, view, spec, optimizer, budget=budget, profile=profile)
    _need(identity == expected_identity, 'expected checkpoint identity drift')
    _boundary(model, view, spec, optimizer, budget, progress, epoch_result)
    state = {name: tensor.detach().clone() for name, tensor in model.state_dict().items()}
    opt = _clone(optimizer.state_dict())
    tensor_bytes, participation = _states(model, optimizer, state, opt, progress.counters, limits)
    rng = progress.rng_state.detach().clone()
    _need(tensor_bytes+rng.numel() <= limits.max_tensor_bytes, 'tensor plus owned RNG byte cap')
    modes = [(name, module.training) for name, module in model.named_modules()]
    _modes(model, modes)
    payload = dict(identity=identity, counters=dict(progress.counters), model=state, adam=opt,
                   owned_rng=rng, module_modes=modes)
    with _CappedBuffer(limits.max_checkpoint_bytes) as buffer:
        torch.save(payload, buffer)
        raw = buffer.getvalue()
    metadata = dict(schema_version=1, role=ROLE, identity=identity, counters=dict(progress.counters),
        checkpoint_sha256=_hash(raw), checkpoint_bytes=len(raw), model_sha256=state_digest(model),
        participation=participation, owned_rng_sha256=_rng(rng), module_modes=_json(modes))
    meta = (json.dumps(metadata, sort_keys=True, allow_nan=False)+'\n').encode()
    _need(len(meta) <= limits.max_metadata_bytes, 'metadata byte cap before publication')
    directory = _path(directory)
    _need(directory.parent.is_dir(), 'caller-owned run parent required')
    directory.mkdir(exist_ok=False)
    try:
        _publish(directory, 'state.pt', raw, limits.max_checkpoint_bytes)
        _publish(directory, 'metadata.json', meta, limits.max_metadata_bytes)
        _need(research_checkpoint_identity(model, view, spec, optimizer, budget=budget, profile=profile) == identity
              and state_digest(model) == metadata['model_sha256']
              and _rng(progress.rng_state) == metadata['owned_rng_sha256']
              and _same(opt, optimizer.state_dict())
              and _states(model, optimizer, model.state_dict(), optimizer.state_dict(), progress.counters, limits)[1] == participation,
              'source/model/RNG/participation drift during save')
        _need(_bytes(directory/'state.pt', limits.max_checkpoint_bytes) == raw
              and _bytes(directory/'metadata.json', limits.max_metadata_bytes) == meta, 'publication readback drift')
        complete = (json.dumps(dict(schema_version=1, status='COMPLETE_GKT_EPOCH_STATE',
            metadata_sha256=_hash(meta), checkpoint_sha256=_hash(raw)), sort_keys=True)+'\n').encode()
        _publish(directory, 'COMPLETE.json', complete, limits.max_metadata_bytes)
        return dict(directory=directory, complete_sha256=_hash(complete), metadata_sha256=_hash(meta),
                    checkpoint_sha256=_hash(raw), counters=dict(progress.counters), fitted_research_model=False)
    except BaseException as error:
        failure = (json.dumps(dict(status='FAILED_NO_COMPLETE_EPOCH_STATE', error_type=type(error).__name__,
            rollback=False), sort_keys=True)+'\n').encode()
        try:
            _publish(directory, 'failure.json', failure, limits.max_metadata_bytes)
        except Exception as secondary:
            error.add_note('Failure receipt publication: '+type(secondary).__name__)
        raise


def restore_epoch_state(directory, model, view, spec, optimizer, *, budget, fresh_progress, profile,
                        expected_identity, expected_complete_sha256, limits):
    """Validate toàn payload trước mutation; restore vào fresh healthy containers."""
    _need(type(limits) is GKTCheckpointLimits, 'typed persistence limits required')
    limits.__post_init__(); _sha(expected_complete_sha256)
    identity = research_checkpoint_identity(model, view, spec, optimizer, budget=budget, profile=profile)
    _need(identity == expected_identity, 'expected identity mismatch before deserialization')
    _need(state_digest(model) == profile.initial_model_sha256, 'fresh initial model/BN state required')
    _need(type(fresh_progress) is training.GKTResearchProgress and not fresh_progress.poisoned
          and fresh_progress.model_binding_sha256 == model.model_binding_sha256
          and fresh_progress.counters == dict.fromkeys(training._COUNTERS, 0)
          and fresh_progress.budget_sha256 is fresh_progress.parameter_identity
          is fresh_progress.optimizer_object_id is fresh_progress.sources_sha256 is None
          and torch.equal(fresh_progress.rng_state, model.initial_dropout_rng_state)
          and not optimizer.state, 'fresh healthy progress and empty owned Adam required')
    directory = _path(directory)
    _need(directory.is_dir() and {p.name for p in directory.iterdir()}
          == {'state.pt', 'metadata.json', 'COMPLETE.json'}, 'partial/failed/extra checkpoint member')
    complete_raw = _bytes(directory/'COMPLETE.json', limits.max_metadata_bytes)
    _need(_hash(complete_raw) == expected_complete_sha256, 'external COMPLETE SHA mismatch')
    complete = _decode(complete_raw)
    _closed(complete, ('schema_version', 'status', 'metadata_sha256', 'checkpoint_sha256'), 'COMPLETE schema')
    _need(type(complete['schema_version']) is int and complete['schema_version'] == 1
          and complete['status'] == 'COMPLETE_GKT_EPOCH_STATE', 'COMPLETE verdict')
    meta_raw = _bytes(directory/'metadata.json', limits.max_metadata_bytes)
    _need(_hash(meta_raw) == complete['metadata_sha256'], 'metadata SHA mismatch')
    metadata = _decode(meta_raw)
    _closed(metadata, ('schema_version', 'role', 'identity', 'counters', 'checkpoint_sha256', 'checkpoint_bytes',
        'model_sha256', 'participation', 'owned_rng_sha256', 'module_modes'), 'metadata schema')
    _need(type(metadata['schema_version']) is int and metadata['schema_version'] == 1
          and metadata['role'] == ROLE and metadata['identity'] == identity
          and metadata['checkpoint_sha256'] == complete['checkpoint_sha256'], 'metadata identity before load')
    _counters(metadata['counters'])
    _budget_counts(metadata['counters'], view, budget)
    _need(metadata['counters']['complete_train_epochs'] == spec.epoch, 'completed epoch identity mismatch')
    _count(metadata['checkpoint_bytes'])
    for name in ('checkpoint_sha256', 'model_sha256', 'owned_rng_sha256'):
        _sha(metadata[name])
    raw = _bytes(directory/'state.pt', limits.max_checkpoint_bytes)
    _need(len(raw) == metadata['checkpoint_bytes'] and _hash(raw) == metadata['checkpoint_sha256'], 'checkpoint bytes/SHA mismatch')
    payload = torch.load(io.BytesIO(raw), map_location='cpu', weights_only=True)
    _closed(payload, ('identity', 'counters', 'model', 'adam', 'owned_rng', 'module_modes'), 'payload schema')
    _need(payload['identity'] == identity and payload['counters'] == metadata['counters'], 'payload lineage/counters drift')
    size, participation = _states(model, optimizer, payload['model'], payload['adam'], payload['counters'], limits)
    rng_sha = _rng(payload['owned_rng'])
    _need(size+payload['owned_rng'].numel() <= limits.max_tensor_bytes
          and rng_sha == metadata['owned_rng_sha256']
          and participation == metadata['participation'], 'owned RNG/Adam participation mismatch')
    _modes(model, payload['module_modes'])
    _need(_json(payload['module_modes']) == metadata['module_modes']
          and state_digest(SimpleNamespace(state_dict=lambda: payload['model'])) == metadata['model_sha256'], 'state/modes digest mismatch')
    _need(research_checkpoint_identity(model, view, spec, optimizer, budget=budget, profile=profile) == identity,
          'source changed before mutation')
    fresh_progress.poisoned = True
    try:
        model.load_state_dict(payload['model'], strict=True)
        optimizer.load_state_dict(payload['adam'])
        for parameter in model.parameters():
            parameter.grad = None
        for name, module in model.named_modules():
            module.training = dict(payload['module_modes'])[name]
        _need(state_digest(model) == metadata['model_sha256'], 'restored model digest mismatch')
        _need(_states(model, optimizer, model.state_dict(), optimizer.state_dict(), payload['counters'], limits)[1]
              == participation and _same(payload['adam'], optimizer.state_dict()), 'restored Adam state mismatch')
        model._bound(model.binding, model.graph_sha256)
        fresh_progress.rng_state = payload['owned_rng'].detach().clone()
        fresh_progress.counters = dict(payload['counters'])
        fresh_progress.budget_sha256 = identity_hash(asdict(budget))
        fresh_progress.parameter_identity = tuple((n, id(p), p.requires_grad) for n, p in model.named_parameters())
        fresh_progress.optimizer_object_id = id(optimizer)
        fresh_progress.sources_sha256 = training.source_identity()
        fresh_progress.poisoned = False
        return fresh_progress
    except BaseException:
        fresh_progress.poisoned = True
        raise
