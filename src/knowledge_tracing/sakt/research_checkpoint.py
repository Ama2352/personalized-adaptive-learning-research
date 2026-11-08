"""Persistence CPU FP32 ở cuối epoch; không lifecycle/selected-fit authority.

Chỉ caller-owned model/Adam hoặc SGD, không constructor/pickle callable/cursor.
Nguồn và profile hashes là consistency contract hợp tác, không runtime attestation.
Restore toàn trạng thái RNG có chủ đích; không hứa giữ RNG hiện tại của caller.
Validation đi trước mutation; exception trong load_state_dict không có rollback.
"""
from dataclasses import asdict, dataclass
import hashlib
import io
import json
import math
import os
from pathlib import Path
import random
from types import SimpleNamespace

import numpy as np
import torch

from knowledge_tracing.akt.filesystem import publish_new_file
from knowledge_tracing.simulator_bridge import identity_hash
from .model import SAKTCore
from . import research_training as training
from .research_data import SAKTResearchView
from .training import state_digest

ROOT = Path(__file__).resolve().parents[3]
ROLE = 'sakt_research_training_state_epoch_boundary_only'


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def _sha(value):
    _need(type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value), 'SHA256 required')


def _count(value):
    _need(type(value) is int and 0 <= value < 2**63, 'nonnegative signed count required')


def _json(value):
    try:
        return json.loads(json.dumps(value, sort_keys=True, allow_nan=False))
    except (TypeError, ValueError) as error:
        raise ValueError('finite JSON metadata required') from error


@dataclass(frozen=True)
class SAKTCheckpointProfile:
    protocol_sha256: str
    runtime_sha256: str
    profile_sha256: str
    run_reference: str

    def __post_init__(self):
        for name in ('protocol_sha256', 'runtime_sha256', 'profile_sha256'):
            _sha(getattr(self, name))
        _need(type(self.run_reference) is str and bool(self.run_reference.strip()), 'explicit run reference required')


@dataclass(frozen=True)
class SAKTCheckpointLimits:
    max_checkpoint_bytes: int
    max_metadata_bytes: int
    max_tensor_bytes: int

    def __post_init__(self):
        for value in asdict(self).values():
            _count(value); _need(value > 0, 'positive explicit persistence byte limits required')


@dataclass(frozen=True)
class SAKTEpochProgress:
    completed_epochs: int
    optimizer_steps: int
    optimized_targets: int

    def __post_init__(self):
        for value in asdict(self).values():
            _count(value)
        _need((self.completed_epochs == 0) == (self.optimizer_steps == self.optimized_targets == 0), 'complete cumulative epoch counters required')
        _need(self.completed_epochs <= self.optimizer_steps <= self.optimized_targets, 'steps/target counters inconsistent')


def source_identity():
    root = Path(__file__).resolve().parents[3]/'src/knowledge_tracing'
    result = dict(training.source_identity())
    for name in ('__init__.py', 'sakt/research_checkpoint.py', 'akt/__init__.py', 'akt/filesystem.py'):
        result[name] = hashlib.sha256((root/name).read_bytes()).hexdigest()
    return tuple(sorted(result.items()))


def _optimizer(model, optimizer):
    _need(type(optimizer) in (torch.optim.Adam, torch.optim.SGD), 'only explicit native Adam/SGD persistence supported')
    actual = training._optimizer_identity(model, optimizer)
    _need(not any(g.get('capturable') or g.get('fused') or g.get('differentiable') for g in optimizer.param_groups), 'ordinary CPU optimizer required')
    return dict(optimizer_class=actual['optimizer_class'], defaults=actual['defaults'],
                groups=[dict(parameters=g['parameters'], settings=g['settings']) for g in actual['groups']])


def research_checkpoint_identity(model, view, spec, optimizer, *, profile):
    """Identity portable; không object IDs và không tạo/load model."""
    _need(type(model) is SAKTCore and type(view) is SAKTResearchView
          and type(spec) is training.SAKTResearchSpec and type(profile) is SAKTCheckpointProfile, 'exact typed research checkpoint context')
    _need(view.phase.scope in ('select_train80', 'refit_union90'), 'only optimization-phase epoch boundary may be saved/restored')
    _need(profile.protocol_sha256 == view.phase.shards[0].plan.protocol_sha256, 'profile protocol/view identity mismatch')
    vocabulary = view.vocabulary.values
    _need(model.config.num_items == len(vocabulary) and model.config.max_length >= view.recipe.context+1, 'model/vocabulary/geometry mismatch')
    _need(all(p.device.type == 'cpu' and p.dtype == torch.float32 and p.requires_grad and torch.isfinite(p).all()
              for p in model.parameters()), 'finite trainable CPU FP32 model required')
    return _json(dict(schema_version=1, role=ROLE, model_config=asdict(model.config), view_sha256=view.identity,
        corpus_sha256=view.corpus_sha256, phase_scope=view.phase.scope, phase_sha256=view.phase.identity,
        encoding_sha256=view.encoding.identity, vocabulary_sha256=identity_hash(list(vocabulary)),
        bank_identity=view.phase.shards[0].bank.identity, recipe=asdict(view.recipe), spec=asdict(spec),
        optimizer=_optimizer(model, optimizer), profile=asdict(profile), sources_sha256=source_identity(),
        restore_scope='completed_epoch_boundary', iterator_resume_supported=False, fitted_research_model=False,
        gradients_saved=False, selection_state_saved=False, global_budget_saved=False))


def _path(directory):
    path = Path(directory).absolute()
    _need(ROOT.resolve() == ROOT.absolute(), 'physical fixed project root required')
    roots = (ROOT/'experiments/sakt/results', ROOT/'artifacts/akt/local-tests')
    _need(any(path.is_relative_to(r) and len(path.relative_to(r).parts) >= 2 for r in roots), 'fresh owned run snapshot directory required')
    cursor = ROOT
    _need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'root alias forbidden')
    for part in path.relative_to(ROOT).parts:
        _need(part not in ('.', '..'), 'unsafe checkpoint path')
        cursor /= part
        _need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'checkpoint path alias forbidden')
    _need(path.resolve() == path, 'checkpoint parent alias forbidden')
    return path


def _bytes(path, cap):
    _need(not path.is_symlink() and not getattr(path, 'is_junction', lambda: False)()
          and path.resolve() == path.absolute(), 'checkpoint member alias forbidden')
    _need(path.is_file() and path.stat().st_size <= cap, 'checkpoint file byte cap')
    before = path.stat()
    with path.open('rb') as stream:
        raw = stream.read(cap+1)
    after = path.stat()
    _need(len(raw) == before.st_size <= cap and (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_size)
          == (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size), 'checkpoint size/stamp drift')
    return raw


def _hash(raw):
    return hashlib.sha256(raw).hexdigest()


def _decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            _need(key not in result, 'duplicate metadata key'); result[key] = value
        return result
    def bad(value):
        raise ValueError('nonfinite metadata')
    def floating(value):
        parsed = float(value); _need(math.isfinite(parsed), 'nonfinite metadata number'); return parsed
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad, parse_float=floating)


def _closed(value, names, message):
    _need(type(value) is dict and set(value) == set(names), message)


def _epoch_progress(model, view, spec, optimizer, result, previous):
    _need(type(previous) is SAKTEpochProgress and type(result) is dict, 'typed previous cumulative progress and epoch receipt required')
    ledger = result.get('ledger', {})
    _need(result.get('status') == 'complete' and result.get('stop_reason') == 'epoch_complete'
          and result.get('role') == 'research_computation_only_no_selected_fit_attestation'
          and result.get('resume_supported') is False and result.get('fitted_research_model') is False
          and ledger.get('complete') is True and ledger.get('input_population_complete') is True
          and ledger.get('rollback') is False and ledger.get('possibly_updated_source_rows') == [], 'complete unambiguous epoch receipt required')
    for name in ('expected_targets', 'seen_targets', 'eligible_targets_seen', 'unsupported_targets_seen', 'expected_eligible_targets',
                 'processed_targets', 'optimized_targets', 'optimizer_steps_started', 'optimizer_steps_body_returned'):
        _count(ledger.get(name))
    eligible = ledger['expected_eligible_targets']
    expected = sum(s.audit['audit']['targets'] for s in view.phase.shards)
    _need(eligible > 0 and ledger['expected_targets'] == ledger['seen_targets'] == expected
          and ledger['eligible_targets_seen'] == ledger['processed_targets'] == ledger['optimized_targets'] == eligible
          and ledger['unsupported_targets_seen'] == expected-eligible
          and ledger['optimizer_steps_started'] == ledger['optimizer_steps_body_returned'] > 0
          and ledger['unseen_targets'] == ledger['unprocessed_seen_eligible_targets'] == 0, 'epoch counters incomplete/pending')
    _need(len(ledger['seen_source_rows']) == len(set(ledger['seen_source_rows'])) == expected
          and len(ledger['processed_source_rows']) == len(set(ledger['processed_source_rows'])) == eligible
          and ledger['processed_source_rows'] == ledger['processing_order_source_rows'], 'epoch population/order incomplete')
    budget = training.SAKTResearchBudget(**result['budget'])
    _need(result['binding'] == training._binding(model, view, spec, optimizer, budget)
          and result['model_state_after'] == state_digest(model), 'epoch model/source/input/optimizer receipt drift')
    _need(type(result['elapsed_seconds']) in (int, float) and math.isfinite(result['elapsed_seconds'])
          and 0 <= result['elapsed_seconds'] < budget.max_seconds, 'epoch late/invalid budget verdict')
    return SAKTEpochProgress(previous.completed_epochs+1, previous.optimizer_steps+ledger['optimizer_steps_body_returned'],
                             previous.optimized_targets+ledger['optimized_targets'])


def _tensor(value, *, shape=None, dtype=torch.float32):
    _need(type(value) is torch.Tensor and value.device.type == 'cpu' and value.dtype == dtype
          and value.layout == torch.strided and (shape is None or value.shape == shape)
          and torch.isfinite(value).all(), 'strict finite CPU tensor state required')


def _validate_states(model, optimizer, state, optimizer_state, progress, limits):
    expected = model.state_dict()
    _need(isinstance(state, dict) and state.keys() == expected.keys(), 'model state keys mismatch')
    for name, value in state.items():
        _tensor(value, shape=expected[name].shape)
    _closed(optimizer_state, ('state', 'param_groups'), 'optimizer state schema')
    groups = optimizer_state['param_groups']
    _need(type(groups) is list and len(groups) == len(optimizer.param_groups) and type(optimizer_state['state']) is dict, 'optimizer group schema')
    parameter_map = {}
    for saved, actual in zip(groups, optimizer.param_groups):
        _need(type(saved) is dict and type(saved.get('params')) is list and len(saved['params']) == len(actual['params'])
              and _json({k:v for k,v in saved.items() if k != 'params'}) == _json({k:v for k,v in actual.items() if k != 'params'}), 'optimizer group settings mismatch')
        for number, parameter in zip(saved['params'], actual['params']):
            _count(number); _need(number not in parameter_map, 'duplicate optimizer parameter index')
            parameter_map[number] = parameter
    # SAKTCore luôn gọi toàn bộ các nhánh và train_research_epoch yêu cầu mọi
    # parameter trainable: masking cho zero-gradient tensor, không bỏ khỏi graph.
    # Vì vậy completed epoch phải có state cho mọi Adam parameter; SGD chỉ có
    # momentum buffers ở nhóm momentum>0, còn momentum0 dùng canonical empty.
    required = set(parameter_map) if type(optimizer) is torch.optim.Adam else {
        number for group in groups if group['momentum'] > 0 for number in group['params']}
    _need(set(optimizer_state['state']) == required, 'optimizer state coverage missing/foreign/noncanonical')
    total = sum(v.numel()*v.element_size() for v in state.values())
    for number, entry in optimizer_state['state'].items():
        _need(type(number) is int and number in parameter_map and type(entry) is dict, 'foreign optimizer state')
        parameter = parameter_map[number]
        if type(optimizer) is torch.optim.Adam:
            group = next(g for g in groups if number in g['params'])
            names = {'step', 'exp_avg', 'exp_avg_sq'} | ({'max_exp_avg_sq'} if group['amsgrad'] else set())
            _need(set(entry) == names, 'Adam state schema')
            step = entry['step']
            _need(type(step) is torch.Tensor and step.device.type == 'cpu' and step.numel() == 1
                  and step.dtype in (torch.float32, torch.float64) and torch.isfinite(step).all()
                  and step.item() == progress.optimizer_steps and float(step.item()).is_integer(), 'Adam step counter invalid')
            for name in names-{'step'}:
                _tensor(entry[name], shape=parameter.shape)
            _need(bool((entry['exp_avg_sq'] >= 0).all()), 'negative Adam second moment')
            if group['amsgrad']:
                _need(bool((entry['max_exp_avg_sq'] >= 0).all())
                      and bool((entry['max_exp_avg_sq'] >= entry['exp_avg_sq']).all()), 'invalid AMSGrad second moment maximum')
        else:
            _need(set(entry) == {'momentum_buffer'}, 'SGD momentum state schema')
            _tensor(entry['momentum_buffer'], shape=parameter.shape)
        total += sum(v.numel()*v.element_size() for v in entry.values())
    _need(total <= limits.max_tensor_bytes, 'serialized tensor payload cap')
    return total


def _rng():
    numpy = np.random.get_state()
    return dict(python=random.getstate(), numpy=(numpy[0], numpy[1].tolist(), *numpy[2:]), torch=torch.get_rng_state().clone())


def _validated_rng(value):
    _closed(value, ('python', 'numpy', 'torch'), 'RNG schema')
    _json(value['python'])
    random.Random().setstate(value['python'])
    ns = value['numpy']
    _need(type(ns) is tuple and len(ns) == 5 and ns[0] == 'MT19937' and type(ns[1]) is list
          and len(ns[1]) == 624 and all(type(x) is int and 0 <= x < 2**32 for x in ns[1])
          and type(ns[2]) is int and 0 <= ns[2] <= 624 and type(ns[3]) is int and ns[3] in (0, 1)
          and type(ns[4]) in (int, float) and math.isfinite(ns[4]), 'NumPy RNG schema')
    numpy = (ns[0], np.asarray(ns[1], dtype=np.uint32), *ns[2:])
    np.random.RandomState().set_state(numpy)
    _tensor(value['torch'], dtype=torch.uint8)
    torch.Generator(device='cpu').set_state(value['torch'])
    return numpy


def _publish(directory, name, raw, cap):
    _need(len(raw) <= cap, 'publication byte cap')
    pending = directory/(name+'.pending')
    with pending.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    publish_new_file(pending, directory/name)


def save_research_training_state(directory, model, view, spec, optimizer, *, profile, epoch_result,
                                previous_progress, expected_identity, limits):
    """Save một completed epoch; previous counters caller-owned, không authority."""
    _need(type(limits) is SAKTCheckpointLimits, 'typed explicit byte limits required')
    identity = research_checkpoint_identity(model, view, spec, optimizer, profile=profile)
    _need(identity == expected_identity, 'expected checkpoint identity drift')
    _need(len(json.dumps(identity, allow_nan=False).encode()) <= limits.max_metadata_bytes, 'identity metadata byte cap')
    progress = _epoch_progress(model, view, spec, optimizer, epoch_result, previous_progress)
    state, opt = model.state_dict(), optimizer.state_dict()
    tensor_bytes = _validate_states(model, optimizer, state, opt, progress, limits)
    modes = [(name, module.training) for name, module in model.named_modules()]
    payload = dict(identity=identity, progress=asdict(progress), model_state_dict=state, optimizer_state_dict=opt,
                   rng=_rng(), module_modes=modes)
    _validated_rng(payload['rng'])
    _need(tensor_bytes+payload['rng']['torch'].numel() <= limits.max_tensor_bytes, 'tensor plus CPU RNG byte cap')
    directory = _path(directory)
    _need(directory.parent.is_dir(), 'caller must own existing run directory')
    directory.mkdir(exist_ok=False)
    try:
        # BytesIO giữ format chuẩn weights_only; estimate/tensor caps đã kiểm trước.
        buffer = io.BytesIO(); torch.save(payload, buffer); raw = buffer.getvalue()
        _need(len(raw) <= limits.max_checkpoint_bytes, 'checkpoint byte cap')
        _publish(directory, 'state.pt', raw, limits.max_checkpoint_bytes)
        metadata = dict(schema_version=1, role=ROLE, identity=identity, progress=asdict(progress),
            checkpoint_sha256=_hash(raw), checkpoint_bytes=len(raw), model_state_sha256=state_digest(model),
            restore_scope='completed_epoch_boundary', iterator_resume_supported=False, fitted_research_model=False)
        meta = (json.dumps(metadata, sort_keys=True, allow_nan=False)+'\n').encode()
        _publish(directory, 'metadata.json', meta, limits.max_metadata_bytes)
        _need(research_checkpoint_identity(model, view, spec, optimizer, profile=profile) == identity
              and state_digest(model) == metadata['model_state_sha256'], 'source/model/optimizer drift during save')
        complete = (json.dumps(dict(schema_version=1, status='COMPLETE_SAKT_EPOCH_TRAINING_STATE',
                                   metadata_sha256=_hash(meta), checkpoint_sha256=_hash(raw)), sort_keys=True)+'\n').encode()
        _publish(directory, 'COMPLETE.json', complete, limits.max_metadata_bytes)
        return dict(directory=directory, complete_sha256=_hash(complete), metadata_sha256=_hash(meta),
                    checkpoint_sha256=_hash(raw), identity=identity, progress=progress,
                    iterator_resume_supported=False, fitted_research_model=False)
    except BaseException as error:
        failure = (json.dumps(dict(status='FAILED_NOT_RESUMABLE', error_type=type(error).__name__,
                                  error=str(error), rollback=False), sort_keys=True)+'\n').encode()
        try:
            with (directory/'failure.json').open('xb') as stream:
                stream.write(failure); stream.flush(); os.fsync(stream.fileno())
        except Exception as secondary:
            error.add_note('Failure receipt could not be persisted: '+type(secondary).__name__)
        raise


def restore_research_training_state(directory, model, view, spec, optimizer, *, profile,
                                   expected_identity, expected_complete_sha256, limits):
    """Restore caller containers ở completed epoch boundary; không batch cursor."""
    _need(type(limits) is SAKTCheckpointLimits, 'typed explicit byte limits required')
    _sha(expected_complete_sha256)
    identity = research_checkpoint_identity(model, view, spec, optimizer, profile=profile)
    _need(identity == expected_identity, 'expected checkpoint identity drift before deserialization')
    directory = _path(directory)
    _need(directory.is_dir() and {p.name for p in directory.iterdir()} == {'state.pt', 'metadata.json', 'COMPLETE.json'}, 'partial/failed/extra checkpoint files')
    complete_raw = _bytes(directory/'COMPLETE.json', limits.max_metadata_bytes)
    _need(_hash(complete_raw) == expected_complete_sha256, 'external COMPLETE SHA mismatch')
    complete = _decode(complete_raw)
    _closed(complete, ('schema_version', 'status', 'metadata_sha256', 'checkpoint_sha256'), 'COMPLETE schema')
    _need(type(complete['schema_version']) is int and complete['schema_version'] == 1
          and complete['status'] == 'COMPLETE_SAKT_EPOCH_TRAINING_STATE', 'COMPLETE verdict')
    metadata_raw = _bytes(directory/'metadata.json', limits.max_metadata_bytes)
    _need(_hash(metadata_raw) == complete['metadata_sha256'], 'metadata SHA mismatch')
    metadata = _decode(metadata_raw)
    _closed(metadata, ('schema_version', 'role', 'identity', 'progress', 'checkpoint_sha256', 'checkpoint_bytes',
        'model_state_sha256', 'restore_scope', 'iterator_resume_supported', 'fitted_research_model'), 'metadata schema')
    _need(type(metadata['schema_version']) is int and metadata['schema_version'] == 1 and metadata['role'] == ROLE
          and metadata['identity'] == identity and metadata['restore_scope'] == 'completed_epoch_boundary'
          and metadata['iterator_resume_supported'] is False and metadata['fitted_research_model'] is False
          and metadata['checkpoint_sha256'] == complete['checkpoint_sha256'], 'checkpoint identity/role/scope before deserialization')
    progress = SAKTEpochProgress(**metadata['progress'])
    _need(progress.completed_epochs > 0, 'only completed epoch checkpoint')
    _count(metadata['checkpoint_bytes']); _sha(metadata['checkpoint_sha256']); _sha(metadata['model_state_sha256'])
    raw = _bytes(directory/'state.pt', limits.max_checkpoint_bytes)
    _need(len(raw) == metadata['checkpoint_bytes'] and _hash(raw) == metadata['checkpoint_sha256'], 'checkpoint byte/SHA mismatch')
    payload = torch.load(io.BytesIO(raw), map_location='cpu', weights_only=True)
    _closed(payload, ('identity', 'progress', 'model_state_dict', 'optimizer_state_dict', 'rng', 'module_modes'), 'payload schema')
    _need(payload['identity'] == identity and payload['progress'] == metadata['progress'], 'payload context/progress drift')
    tensor_bytes = _validate_states(model, optimizer, payload['model_state_dict'], payload['optimizer_state_dict'], progress, limits)
    _need(state_digest(SimpleNamespace(state_dict=lambda: payload['model_state_dict'])) == metadata['model_state_sha256'],
          'payload model digest mismatch before mutation')
    numpy = _validated_rng(payload['rng'])
    _need(tensor_bytes+payload['rng']['torch'].numel() <= limits.max_tensor_bytes, 'tensor plus CPU RNG byte cap')
    modes = payload['module_modes']; modules = dict(model.named_modules())
    _need(type(modes) is list and all(type(x) is tuple and len(x) == 2 and type(x[0]) is str and type(x[1]) is bool for x in modes)
          and [x[0] for x in modes] == list(modules), 'module mode state mismatch')
    _need(research_checkpoint_identity(model, view, spec, optimizer, profile=profile) == identity, 'source changed before restore')
    model.load_state_dict(payload['model_state_dict'], strict=True)
    optimizer.load_state_dict(payload['optimizer_state_dict'])
    for parameter in model.parameters():
        parameter.grad = None
    for name, mode in modes:
        modules[name].training = mode
    _need(state_digest(model) == metadata['model_state_sha256'], 'restored model digest mismatch')
    random.setstate(payload['rng']['python']); np.random.set_state(numpy); torch.set_rng_state(payload['rng']['torch'])
    return progress
