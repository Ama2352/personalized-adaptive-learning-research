"""Nạp trọng số A0 nghiên cứu vào backend dự báo tuần tự trên CPU.

Giữ metadata checkpoint gốc. Loader không chọn epoch/mô hình, refit, hiệu chỉnh
hoặc cấp quyền closed-loop. Caller phải ghim checkpoint đã chọn cho mục đích
đánh giá của mình. Optimizer và RNG huấn luyện không được khôi phục khi suy luận.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import torch

from knowledge_tracing.simulator_bridge import SimulatorBank, identity_hash
from . import research_graph_checkpoint as checkpoint
from .config import AKTConfig, validate_config
from .model import AKTAdapter
from .online import AKTOnlineBackend, RECIPE_FIELDS, simulator_model_identity
from .research_simulator_data import ResearchAKTEncoding


def load_research_a0_online(directory: Path, config: AKTConfig, bank: SimulatorBank, *,
                            encoding: ResearchAKTEncoding, expected_identity: dict,
                            expected_complete_sha256: str,
                            limits: checkpoint.GraphCheckpointLimits) -> AKTOnlineBackend:
    """Complete-epoch A0 → cùng vocabulary/window geometry, không tạo optimizer.

    CPU inference có thể đọc state CPU đã serialize từ producer CPU hoặc CUDA.
    Runtime inference phải ẩn CUDA, theo ràng buộc CPU hiện hành của checkpoint.
    Đây là loader cho artifact owned/trusted đã ghim SHA, không cho pickle lạ.
    """
    validate_config(config)
    if config.device != 'cpu' or config.phase != 'simulator-research':
        raise ValueError('research A0 online requires simulator-research CPU inference')
    if type(encoding) is not ResearchAKTEncoding or type(bank) is not SimulatorBank:
        raise ValueError('typed research encoding and simulator bank required')
    encoding.assert_integrity()
    inspected = checkpoint.inspect_graph_epoch_state(directory, expected_identity=expected_identity,
        expected_complete_sha256=expected_complete_sha256, limits=limits)
    metadata = json.loads(inspected.metadata_bytes)
    identity = metadata['identity']
    condition = identity['condition']
    if (condition.get('variant') != 'A0' or condition.get('graph_mode') != 'none'
            or condition.get('nodes') != [] or condition.get('edges') != []
            or condition.get('edge_weights') != [] or condition.get('method24_scores') is not None
            or identity_hash(condition) != identity['condition_sha256']):
        raise ValueError('only graph-free A0 checkpoint can use this backend')
    fields = tuple(name for name in RECIPE_FIELDS if name != 'device')
    if any(identity['config'].get(name) != getattr(config, name) for name in fields):
        raise ValueError('research A0 inference recipe mismatch')
    if (identity['encoding'] != checkpoint._json(encoding.payload())
            or identity['encoding_sha256'] != encoding.identity
            or encoding.domain_sha256 != identity_hash(bank.identity)):
        raise ValueError('research A0 encoding or simulator domain mismatch')
    exercise_encoding = encoding.exercise_encoding()
    binding = identity['neural_binding']
    if (binding.get('encoding_sha256') != encoding.identity
            or binding.get('vocabulary_sha256') != identity_hash(list(exercise_encoding.vocabulary.values))
            or binding.get('phase_scope') != encoding.optimization_scope
            or binding.get('encoding_fit_scope') != encoding.optimization_scope
            or binding.get('selection_freeze_sha256') != encoding.selection_freeze_sha256):
        raise ValueError('research A0 neural encoding lineage mismatch')
    online_identity = simulator_model_identity(config, bank, exercise_encoding)
    raw = checkpoint._bytes(inspected.reference.directory/'state.pt', limits.max_checkpoint_bytes)
    if hashlib.sha256(raw).hexdigest() != inspected.reference.checkpoint_sha256:
        raise ValueError('research A0 checkpoint changed before deserialization')
    checkpoint._torch()  # CPU boundary before loading tensors or constructing a model.
    payload = torch.load(io.BytesIO(raw), map_location='cpu', weights_only=True)
    checkpoint._closed(payload, ('identity', 'receipt', 'model_state_dict', 'optimizer_state_dict',
        'rng', 'module_modes'), 'research A0 payload schema')
    if payload['identity'] != identity or checkpoint._json(payload['receipt']) != metadata['receipt']:
        raise ValueError('research A0 payload identity or epoch mismatch')
    state = payload['model_state_dict']
    if (not isinstance(state, dict) or not state
            or any(not isinstance(name, str) or not name.startswith('backbone.') for name in state)):
        raise ValueError('research A0 state contains non-backbone parameters')
    if checkpoint._state_sha(state) != metadata['receipt']['model_sha256']:
        raise ValueError('research A0 model state digest mismatch')
    if sum(value.numel()*value.element_size() for value in state.values()) > limits.max_tensor_bytes:
        raise ValueError('research A0 model tensor byte cap')
    backbone_state = {name.removeprefix('backbone.'): value for name, value in state.items()}
    # Initializing the container must not consume the simulator's random stream.
    with torch.random.fork_rng(devices=[]):
        adapter = AKTAdapter(config, exercise_encoding)
        adapter.native.load_state_dict(backbone_state, strict=True)
        adapter.native.eval()
    verified = checkpoint.inspect_graph_epoch_state(directory, expected_identity=expected_identity,
        expected_complete_sha256=expected_complete_sha256, limits=limits)
    if verified != inspected:
        raise ValueError('research A0 checkpoint changed during load')
    encoding.assert_integrity()
    return AKTOnlineBackend(adapter, bank, checkpoint_id=inspected.reference.checkpoint_sha256,
        checkpoint_identity=online_identity)
