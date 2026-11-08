"""Raw state_dict + bound JSON sidecar cho completed synthetic engineering epoch.

Không optimizer/RNG snapshot, không selected-fit research và không adapter promotion.
"""

from dataclasses import asdict
import hashlib
import io
import json
import os
from pathlib import Path

import torch

from knowledge_tracing.akt.config import PROJECT_ROOT
from .config import SAKTConfig
from .model import SAKTCore
from .training import SAKTTrainingResult, source_identity, state_digest
from .training_data import ENGINEERING_ROLE

MAX_SIDECAR_BYTES = 65536


def _sha(value):
    if type(value) is not str or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('explicit lowercase SHA256 required')


def _path(path):
    path = Path(path).resolve()
    roots = ((PROJECT_ROOT / 'artifacts/akt/local-tests').resolve(),
             (PROJECT_ROOT / 'experiments/sakt/results').resolve())
    if path.suffix != '.pt' or not any(path.is_relative_to(root) and path != root for root in roots):
        raise ValueError('engineering checkpoint outside approved outputs')
    return path


def checkpoint_identity(result):
    return {'schema_version': 1, 'role': ENGINEERING_ROLE, 'model_config': asdict(result.model_config),
            'training_config': asdict(result.training_config), 'data_identity': result.data_identity,
            'source_sha256': result.source_sha256}


def save_engineering_weights(path, result: SAKTTrainingResult):
    if (type(result) is not SAKTTrainingResult or result.status != 'complete'
            or result.role != ENGINEERING_ROLE or result.optimizer_steps < 1
            or result.completed_epochs != result.training_config.epochs
            or not result.history or not all(x['complete_epoch'] for x in result.history)
            or result.source_sha256 != source_identity()
            or result.model.config != result.model_config
            or state_digest(result.model) != result.model_state_sha256):
        raise ValueError('only unchanged completed engineering epoch may be checkpointed')
    path = _path(path); sidecar = path.with_suffix('.json')
    if path.exists() or sidecar.exists(): raise FileExistsError('engineering artifact is exclusive')
    if not path.parent.is_dir(): raise ValueError('caller must create its run directory')
    with path.open('xb') as stream:
        torch.save(result.model.state_dict(), stream); stream.flush(); os.fsync(stream.fileno())
    payload = path.read_bytes()
    metadata = {'identity': checkpoint_identity(result), 'checkpoint_sha256': hashlib.sha256(payload).hexdigest(),
                'model_state_sha256': result.model_state_sha256,
                'completed_epoch': result.completed_epochs, 'optimizer_steps': result.optimizer_steps,
                'complete': True, 'selection_policy': 'last_completed_requested_epoch; no best-epoch selection',
                'resume_supported': False, 'fitted_research_model': False}
    with sidecar.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(metadata, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    return {'checkpoint': path, 'sidecar': sidecar, 'checkpoint_sha256': metadata['checkpoint_sha256'],
            'sidecar_sha256': hashlib.sha256(sidecar.read_bytes()).hexdigest(), 'identity': metadata['identity']}


def load_engineering_weights(path, *, expected_sidecar_sha256, expected_identity, max_checkpoint_bytes):
    path = _path(path)
    _sha(expected_sidecar_sha256)
    if type(max_checkpoint_bytes) is not int or max_checkpoint_bytes < 1:
        raise ValueError('explicit serialized byte budget required')
    with path.with_suffix('.json').open('rb') as stream: sidecar_payload = stream.read(MAX_SIDECAR_BYTES + 1)
    if len(sidecar_payload) > MAX_SIDECAR_BYTES or hashlib.sha256(sidecar_payload).hexdigest() != expected_sidecar_sha256:
        raise ValueError('sidecar size or SHA mismatch')
    metadata = json.loads(sidecar_payload)
    if (type(metadata) is not dict or metadata.get('identity') != expected_identity
            or type(expected_identity) is not dict or expected_identity.get('role') != ENGINEERING_ROLE
            or expected_identity.get('schema_version') != 1
            or expected_identity.get('source_sha256') != source_identity()
            or metadata.get('complete') is not True or metadata.get('resume_supported') is not False
            or metadata.get('fitted_research_model') is not False
            or type(metadata.get('completed_epoch')) is not int or metadata['completed_epoch'] < 1
            or type(metadata.get('optimizer_steps')) is not int or metadata['optimizer_steps'] < 1):
        raise ValueError('engineering identity/completion/source mismatch')
    _sha(metadata.get('checkpoint_sha256'))
    with path.open('rb') as stream: payload = stream.read(max_checkpoint_bytes + 1)
    if not payload or len(payload) > max_checkpoint_bytes or hashlib.sha256(payload).hexdigest() != metadata['checkpoint_sha256']:
        raise ValueError('checkpoint payload budget or SHA mismatch')
    state = torch.load(io.BytesIO(payload), weights_only=True, map_location='cpu')
    if (not isinstance(state, dict) or not state
            or any(type(k) is not str or not isinstance(v, torch.Tensor) or v.device.type != 'cpu'
                   or v.dtype != torch.float32 or not torch.isfinite(v).all() for k, v in state.items())):
        raise ValueError('strict finite CPU FP32 state_dict required')
    config = SAKTConfig(**expected_identity['model_config'])
    with torch.random.fork_rng(devices=[]): model = SAKTCore(config).to(device='cpu', dtype=torch.float32)
    model.load_state_dict(state, strict=True); model.eval()
    if state_digest(model) != metadata['model_state_sha256']:
        raise ValueError('reloaded engineering state digest mismatch')
    return model
