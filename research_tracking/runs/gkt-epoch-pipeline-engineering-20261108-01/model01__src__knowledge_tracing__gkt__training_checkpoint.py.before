"""GKT engineering weights-only; không epoch, fitted certificate hoặc resume.

Chỉ cooperative identity/checksum cho artifact toy đã biết. Không API nhận
untrusted pickle hoặc bằng chứng chống caller forge/reseal toàn bộ metadata.
"""
from dataclasses import asdict, dataclass
import hashlib
import io
import json
import math
import os
from pathlib import Path

import torch

from .config import GKTBinding, GKTKernelConfig
from .core import adjacency_sha256
from .recurrent import GKTStaticRecurrentCandidate, RECIPE_ID, GRU_VARIANT
from . import training as tr

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MAX_CHECKPOINT_BYTES = 1024 * 1024
MAX_JSON_BYTES = 65536
FLAGS = dict(optimizer_saved=False, rng_saved=False, hidden_state_saved=False,
             resume_supported=False, fitted_research_model=False, completion_unit='train_step')


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def source_identity():
    return {**tr.source_identity(), 'src/knowledge_tracing/gkt/training_checkpoint.py': _sha(Path(__file__).read_bytes())}


def _limit(value):
    if type(value) is not int or not 1 <= value <= MAX_CHECKPOINT_BYTES:
        raise ValueError('explicit payload byte ceiling <=1MiB required')


def _directory(value):
    path = Path(value)
    roots = (PROJECT_ROOT / 'artifacts/akt/local-tests', PROJECT_ROOT / 'experiments/gkt/results')
    if (not path.is_absolute() or '..' in path.parts or not any(path != r and path.is_relative_to(r) for r in roots)):
        raise ValueError('checkpoint directory outside approved engineering outputs')
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise ValueError('symlink output parent forbidden')
        if parent == PROJECT_ROOT:
            break
    if path.resolve() != path:
        raise ValueError('physical canonical engineering path required')
    return path


def _read(path, cap):
    if path.is_symlink() or not path.is_file():
        raise ValueError('regular existing artifact required')
    with path.open('rb') as stream:
        data = stream.read(cap + 1)
    if not data or len(data) > cap:
        raise ValueError('artifact byte bound')
    return data


def _publish(directory, name, payload):
    """Atomic no-clobber link; failure giữ pending/partial, không replace overwrite."""
    temporary = directory / (name + '.pending')
    with temporary.open('xb') as stream:
        stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    if _read(temporary, len(payload)) != payload:
        raise ValueError('postwrite byte verification failed')
    os.link(temporary, directory / name)  # Atomic creation, fails if destination exists.
    if name != 'COMPLETE.json':
        temporary.unlink()  # Only owned checked pending file, never recursive cleanup.
    # COMPLETE link is the commit point: no potentially failing cleanup after it.
    # Its pending alias is retained; readers accept only manifest-listed final files.


def _validate_identity(identity):
    keys = {'schema_version', 'model_class', 'weight_role', 'model_config', 'binding', 'recipe',
            'graph_sha256', 'recipe_sha256', 'source_sha256', 'trained_step', 'approval_reference', 'flags'}
    if (type(identity) is not dict or set(identity) != keys or type(identity['schema_version']) is not int
            or identity['schema_version'] != 1 or identity['model_class'] != 'GKTStaticRecurrentCandidate'
            or identity['weight_role'] != tr.WEIGHT_ROLE or identity['flags'] != FLAGS
            or identity['source_sha256'] != source_identity()):
        raise ValueError('strict engineering schema/role/source/weights-only flags required')
    if (type(identity['flags']) is not dict or set(identity['flags']) != set(FLAGS)
            or any(identity['flags'][name] is not False for name in FLAGS if name != 'completion_unit')):
        raise ValueError('explicit False weights-only flags required')
    reference = identity['approval_reference']
    if type(reference) is not str or not reference.strip() or len(reference) > 256:
        raise ValueError('bounded explicit approval reference required')
    c = GKTKernelConfig(**identity['model_config'])
    raw_binding = dict(identity['binding'])
    if type(raw_binding.get('node_ids')) is not list:
        raise ValueError('canonical ordered node list required')
    raw_binding['node_ids'] = tuple(raw_binding['node_ids'])
    binding = GKTBinding(**raw_binding)
    recipe = identity['recipe']
    if (type(recipe) is not dict or set(recipe) != {'recipe_id', 'mlp_hidden_dim', 'normalization', 'dropout',
            'initial_state_policy', 'gru_variant', 'precision'} or recipe['recipe_id'] != RECIPE_ID
            or recipe['normalization'] != 'none' or type(recipe['dropout']) not in (int, float) or recipe['dropout'] != 0
            or recipe['initial_state_policy'] != 'zeros' or recipe['gru_variant'] != GRU_VARIANT
            or recipe['precision'] not in ('float32', 'float64') or type(recipe['mlp_hidden_dim']) is not int
            or not 1 <= recipe['mlp_hidden_dim'] <= 8 or c.num_nodes != len(binding.node_ids)
            or c.node_unit != binding.node_unit or c.num_nodes > 4
            or max(c.state_dim, c.embedding_dim, c.message_dim) > 8 or c.message_dim != c.state_dim):
        raise ValueError('explicit tiny bound engineering recipe/geometry required')
    descriptor = {k: recipe[k] for k in ('recipe_id', 'mlp_hidden_dim', 'normalization', 'dropout', 'initial_state_policy', 'gru_variant')}
    descriptor.update(config=asdict(c), dtype='torch.' + recipe['precision'])
    # Native recipe digest uses default ensure_ascii=True and separators, same scalar descriptor.
    recipe_digest = _sha(json.dumps(descriptor, sort_keys=True, separators=(',', ':')).encode())
    if identity['recipe_sha256'] != recipe_digest or not tr._sha(identity['graph_sha256']):
        raise ValueError('recipe/graph digest mismatch')
    step = identity['trained_step']
    required = {'status', 'complete_train_step', 'optimizer_steps', 'cumulative_steps', 'cumulative_targets',
                'selected_targets', 'selected_source_rows', 'observed_events', 'loss_sum', 'mean_loss',
                'grad_norm', 'model_sha256_before', 'model_sha256_after', 'optimizer_sha256_before',
                'optimizer_sha256_after', 'batch_sha256', 'training_source_sha256', 'settings'}
    if (type(step) is not dict or set(step) != required or step['status'] != 'complete'
            or step['complete_train_step'] is not True or type(step['optimizer_steps']) is not int
            or step['optimizer_steps'] != 1 or step['training_source_sha256'] != tr.source_identity()):
        raise ValueError('ordinary completed trained-step receipt required')
    for name, lower, upper in (('cumulative_steps', 1, 8), ('cumulative_targets', 1, 192),
                               ('selected_targets', 1, 24), ('observed_events', 1, 24)):
        if type(step[name]) is not int or not lower <= step[name] <= upper:
            raise ValueError('bounded trained-step counters required')
    n = step['selected_targets']; rows = step['selected_source_rows']
    if (type(rows) is not list or len(rows) != n or any(type(x) is not int or x < 1 for x in rows)
            or len(set(rows)) != n or n > step['observed_events'] or n > step['cumulative_targets']):
        raise ValueError('selected population receipt mismatch')
    for name in ('loss_sum', 'mean_loss', 'grad_norm'):
        if type(step[name]) not in (int, float) or not math.isfinite(step[name]) or step[name] < 0:
            raise ValueError('finite objective/gradient receipt required')
    if not math.isclose(step['mean_loss'], step['loss_sum'] / n, rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError('loss denominator receipt mismatch')
    for name in ('model_sha256_before', 'model_sha256_after', 'optimizer_sha256_before', 'optimizer_sha256_after', 'batch_sha256'):
        if not tr._sha(step[name]):
            raise ValueError('strict trained-step SHA required')
    settings = dict(step['settings'])
    if type(settings.get('betas')) is not list:
        raise ValueError('canonical settings required')
    settings['betas'] = tuple(settings['betas'])
    if tr.GKTTrainingSettings(**settings).precision != recipe['precision']:
        raise ValueError('trained precision/recipe mismatch')
    return c, binding, recipe


def checkpoint_identity(model, train_step_result, *, approval_reference):
    if type(model) is not GKTStaticRecurrentCandidate or type(train_step_result) is not tr.GKTTrainBatchResult:
        raise ValueError('typed ordinary trained model/step receipt required')
    r = train_step_result
    model._bound(model.binding, model.graph_sha256)
    if (r.role != tr.WEIGHT_ROLE or r.model_sha256_after != tr.model_digest(model)
            or r.binding != model.binding or r.graph_sha256 != model.graph_sha256
            or r.recipe_sha256 != model.recipe_sha256):
        raise ValueError('unchanged trained model/binding/recipe required')
    step = {name: getattr(r, name) for name in ('status', 'complete_train_step', 'optimizer_steps',
            'cumulative_steps', 'cumulative_targets', 'selected_targets', 'selected_source_rows', 'observed_events',
            'loss_sum', 'mean_loss', 'grad_norm', 'model_sha256_before', 'model_sha256_after',
            'optimizer_sha256_before', 'optimizer_sha256_after', 'batch_sha256')}
    step.update(training_source_sha256=r.source_sha256, settings=asdict(r.settings))
    identity = dict(schema_version=1, model_class='GKTStaticRecurrentCandidate', weight_role=tr.WEIGHT_ROLE,
        model_config=asdict(model.config), binding=asdict(model.binding),
        recipe=dict(recipe_id=model.recipe_id, mlp_hidden_dim=model.mlp_hidden_dim,
            normalization=model.normalization, dropout=model.dropout, initial_state_policy=model.initial_state_policy,
            gru_variant=model.gru_variant, precision=str(model.adjacency.dtype).split('.')[-1]),
        graph_sha256=model.graph_sha256, recipe_sha256=model.recipe_sha256, source_sha256=source_identity(),
        trained_step=step, approval_reference=approval_reference, flags=FLAGS.copy())
    identity = json.loads(_json(identity))
    _validate_identity(identity)
    return identity


def save_engineering_weights(run_directory, model, train_step_result, *, approval_reference, max_checkpoint_bytes):
    """Fresh owned directory only; failed attempts retained, never reused/overwritten."""
    _limit(max_checkpoint_bytes)
    identity = checkpoint_identity(model, train_step_result, approval_reference=approval_reference)
    before = source_identity(); digest = tr.model_digest(model)
    buffer = io.BytesIO()
    torch.save(model.state_dict(), buffer)
    payload = buffer.getvalue()
    if not payload or len(payload) > max_checkpoint_bytes:
        raise ValueError('serialized weights exceed explicit budget')
    metadata = _json({'identity': identity, 'model_state_sha256': digest})
    if len(metadata) > MAX_JSON_BYTES:
        raise ValueError('metadata byte ceiling')
    directory = _directory(run_directory)
    if not directory.parent.is_dir():
        raise ValueError('caller must prepare approved run parent')
    directory.mkdir(exist_ok=False)
    _publish(directory, 'weights.pt', payload)
    _publish(directory, 'metadata.json', metadata)
    if source_identity() != before or tr.model_digest(model) != digest:
        raise ValueError('source/model drift before COMPLETE publication; retain partial')
    complete = _json(dict(schema_version=1, status='COMPLETE_ENGINEERING_WEIGHTS_ONLY',
        files={'weights.pt': dict(bytes=len(payload), sha256=_sha(payload)),
               'metadata.json': dict(bytes=len(metadata), sha256=_sha(metadata))}))
    _publish(directory, 'COMPLETE.json', complete)
    return {'directory': directory, 'manifest_sha256': _sha(complete), 'identity': identity,
            'checkpoint_sha256': _sha(payload), 'metadata_sha256': _sha(metadata)}


@dataclass(frozen=True)
class GKTLoadedEngineeringWeights:
    model: GKTStaticRecurrentCandidate
    identity: dict
    manifest_sha256: str


def load_engineering_weights(checkpoint_directory, *, expected_manifest_sha256, expected_identity, max_checkpoint_bytes):
    """Không restore optimizer/RNG/hidden state hoặc promote fitted production adapter."""
    _limit(max_checkpoint_bytes)
    if not tr._sha(expected_manifest_sha256):
        raise ValueError('strict expected manifest SHA required')
    c, binding, recipe = _validate_identity(expected_identity)
    before = source_identity()
    directory = _directory(checkpoint_directory)
    complete = _read(directory / 'COMPLETE.json', MAX_JSON_BYTES)
    if _sha(complete) != expected_manifest_sha256:
        raise ValueError('COMPLETE manifest SHA mismatch')
    manifest = json.loads(complete)
    if (type(manifest) is not dict or set(manifest) != {'schema_version', 'status', 'files'}
            or type(manifest['schema_version']) is not int or manifest['schema_version'] != 1
            or manifest['status'] != 'COMPLETE_ENGINEERING_WEIGHTS_ONLY'
            or type(manifest['files']) is not dict or set(manifest['files']) != {'weights.pt', 'metadata.json'}):
        raise ValueError('strict complete file manifest required')
    raw = {}
    for name, limit in (('metadata.json', MAX_JSON_BYTES), ('weights.pt', max_checkpoint_bytes)):
        row = manifest['files'][name]
        if (type(row) is not dict or set(row) != {'bytes', 'sha256'} or type(row['bytes']) is not int
                or not 1 <= row['bytes'] <= limit or not tr._sha(row['sha256'])):
            raise ValueError('bounded file manifest row required')
        raw[name] = _read(directory / name, limit)
        if len(raw[name]) != row['bytes'] or _sha(raw[name]) != row['sha256']:
            raise ValueError('file payload SHA/size mismatch')
    metadata = json.loads(raw['metadata.json'])
    if (type(metadata) is not dict or set(metadata) != {'identity', 'model_state_sha256'}
            or metadata['identity'] != expected_identity
            or metadata['model_state_sha256'] != expected_identity['trained_step']['model_sha256_after']):
        raise ValueError('exact expected trained identity required before deserialize')
    with torch.device('cpu'):
        state = torch.load(io.BytesIO(raw['weights.pt']), weights_only=True, map_location='cpu')
    if not isinstance(state, dict) or 'adjacency' not in state:
        raise ValueError('registered weights/buffers required')
    adjacency = state['adjacency']; dtype = getattr(torch, recipe['precision'])
    if (not isinstance(adjacency, torch.Tensor) or adjacency.device.type != 'cpu' or adjacency.dtype != dtype
            or adjacency.layout != torch.strided or adjacency.shape != (c.num_nodes, c.num_nodes)
            or not torch.isfinite(adjacency).all() or adjacency_sha256(adjacency) != expected_identity['graph_sha256']):
        raise ValueError('actual saved graph must match explicit node/graph binding')
    args = {k: v for k, v in recipe.items() if k != 'precision'}
    with torch.random.fork_rng(devices=[]), torch.device('cpu'):
        model = GKTStaticRecurrentCandidate(c, binding, adjacency, **args)
    reference = model.state_dict()
    if set(state) != set(reference):
        raise ValueError('strict registered state keys required')
    for name, value in state.items():
        if (not isinstance(value, torch.Tensor) or value.device.type != 'cpu' or value.dtype != dtype
                or value.layout != torch.strided or value.shape != reference[name].shape or not torch.isfinite(value).all()):
            raise ValueError('strict finite CPU tensor geometry/dtype required')
    model.load_state_dict(state, strict=True)
    model._bound(binding, expected_identity['graph_sha256'])
    if (source_identity() != before or model.recipe_sha256 != expected_identity['recipe_sha256']
            or tr.model_digest(model) != metadata['model_state_sha256']
            or any(_read(directory / name, MAX_JSON_BYTES if name != 'weights.pt' else max_checkpoint_bytes) != data
                   for name, data in {**raw, 'COMPLETE.json': complete}.items())):
        raise ValueError('reloaded weights/source/file identity changed')
    model.eval()
    return GKTLoadedEngineeringWeights(model, expected_identity, expected_manifest_sha256)
