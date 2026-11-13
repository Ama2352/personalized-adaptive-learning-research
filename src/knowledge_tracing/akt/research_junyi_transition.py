"""Kiểm receipt chuyển nguồn A1 sau epoch1, trước validation.

Hàm chỉ kiểm hợp đồng danh tính và bằng chứng caller cung cấp. Caller kiểm
SHA byte checkpoint, progress và xuất xứ receipt trước khi khôi phục state.
Không nạp tensor, sửa checkpoint hoặc cấp quyền thực thi GPU.
"""

import hashlib
import json
import math


CONFIG_FIELDS = frozenset('''project_root output_dir phase run_id execution_enabled
partition graph source_commit source_root outer_fold device seed context target_block
max_length d_model heads blocks d_ff final_fc dropout kq_same separate_qa n_pid batch_size
lr betas eps weight_decay max_grad_norm inner_val_fraction min_delta patience max_epochs
max_train_users max_val_users max_targets_per_side max_total_targets max_steps max_seconds
max_wall_seconds max_rss_bytes min_available_ram_bytes protocol_version memory_mb threads
fetch_rows recovery'''.split())
PROFILE_FIELDS = frozenset('''max_vram_bytes recipe_id device initialization dtype seed
foreach fused capturable differentiable amsgrad maximize decoupled_weight_decay
clip_foreach deterministic_algorithms deterministic_warn_only matmul_allow_tf32
cudnn_allow_tf32 matmul_precision cudnn_benchmark cublas_workspace_config'''.split())
IDENTITY_FIELDS = frozenset('''kind inputs encoding prediction_implementation config
profile source_build_sha256 candidate_id batch_factory comparison_reference_sha256
validation_batch_size'''.split())
OPTIONAL_IDENTITY_FIELDS = frozenset(('selection_cache_manifest_sha256', 'prefetch_train_windows',
                                      'prefetch_selection_windows'))
FACTORY_FIELDS = frozenset(('condition_sha256', 'encoding_sha256', 'phase_sha256', 'graph_enabled'))
OPTIONAL_FACTORY_FIELDS = frozenset(('context_backend', 'graph_context_cache'))
CHECKS = frozenset(('probability', 'loss', 'gradient', 'model', 'optimizer', 'rng', 'targets'))


def _need(value, message):
    if not value:
        raise ValueError(message)


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def identity_sha256(identity):
    """SHA JSON chuẩn hóa của identity, cùng quy ước producer Junyi."""
    return hashlib.sha256(_json(identity).encode()).hexdigest()


def _sha(value):
    _need(type(value) is str and len(value) == 64
          and all(character in '0123456789abcdef' for character in value), 'SHA256 required')


def _schema(value, required, optional=frozenset()):
    _need(type(value) is dict and required <= set(value) <= required | optional,
          'Missing or unknown transition fields')


def _validate_identity(identity):
    _schema(identity, IDENTITY_FIELDS, OPTIONAL_IDENTITY_FIELDS)
    _schema(identity['config'], CONFIG_FIELDS)
    _schema(identity['profile'], PROFILE_FIELDS)
    _schema(identity['batch_factory'], FACTORY_FIELDS, OPTIONAL_FACTORY_FIELDS)
    _json(identity)
    _need(identity['kind'] == 'junyi_a1_selected_v1' and identity['candidate_id'] == 'A1_EXPERT',
          'A1 expert selected identity required')
    _need(type(identity['validation_batch_size']) is int and identity['validation_batch_size'] == 128
          and identity['prediction_implementation'] == 'batched_windows_v1_batch128',
          'Frozen batch128 validation required')
    for key in ('inputs', 'encoding', 'source_build_sha256', 'comparison_reference_sha256'):
        _sha(identity[key])
    factory = identity['batch_factory']
    for key in ('condition_sha256', 'encoding_sha256', 'phase_sha256'):
        _sha(factory[key])
    _need(factory['encoding_sha256'] == identity['encoding'] and factory['graph_enabled'] is True,
          'Frozen fitted graph encoding required')
    if 'context_backend' in factory:
        _need(factory['context_backend'] in ('reference', 'compact-a1-v1'), 'Unknown context backend')
    if factory.get('graph_context_cache') is not None:
        _sha(factory['graph_context_cache'])
        _need(factory.get('context_backend') == 'compact-a1-v1', 'Graph cache requires compact backend')
    if 'selection_cache_manifest_sha256' in identity:
        _sha(identity['selection_cache_manifest_sha256'])
    for name in ('prefetch_train_windows', 'prefetch_selection_windows'):
        if name in identity:
            _need(type(identity[name]) is bool, 'Boolean prefetch required')


def validate_source_transition(source_identity, target_identity, evidence, *, checkpoint_sha256):
    """Chấp nhận chuyển nguồn có parity tuyệt đối từ checkpoint epoch1 thật.

    Receipt đóng gồm status PASS_ACTUAL_CHECKPOINT_PARITY, checkpoint_sha256,
    source_identity_sha256, target_identity_sha256, max_absolute_drift bằng 0,
    và checks với probability/loss/gradient/model/optimizer/rng/targets đều True.
    """
    _sha(checkpoint_sha256)
    for identity in (source_identity, target_identity):
        _validate_identity(identity)
    _schema(evidence, frozenset(('status', 'checkpoint_sha256', 'source_identity_sha256',
                               'target_identity_sha256', 'max_absolute_drift', 'checks')))
    _need(evidence['status'] == 'PASS_ACTUAL_CHECKPOINT_PARITY', 'Actual checkpoint parity must pass')
    _need(evidence['checkpoint_sha256'] == checkpoint_sha256
          and evidence['source_identity_sha256'] == identity_sha256(source_identity)
          and evidence['target_identity_sha256'] == identity_sha256(target_identity),
          'Parity receipt binding mismatch')
    drift = evidence['max_absolute_drift']
    _need(type(drift) in (int, float) and math.isfinite(drift) and drift == 0,
          'Finite zero parity drift required')
    _schema(evidence['checks'], CHECKS)
    _need(all(value is True for value in evidence['checks'].values()), 'Every parity check must pass')
    mutable_config = frozenset(('run_id', 'output_dir', 'max_seconds', 'max_wall_seconds'))
    for name in CONFIG_FIELDS - mutable_config:
        _need(_json(source_identity['config'][name]) == _json(target_identity['config'][name]),
              'Frozen configuration changed')
    for identity in (source_identity, target_identity):
        for name in ('max_seconds', 'max_wall_seconds'):
            value = identity['config'][name]
            _need(type(value) in (int, float) and math.isfinite(value) and value > 0,
                  'Finite positive resource envelope required')
        for name in ('run_id', 'output_dir'):
            _need(type(identity['config'][name]) is str and bool(identity['config'][name]),
                  'Explicit lineage output required')
    mutable_identity = OPTIONAL_IDENTITY_FIELDS | frozenset(('source_build_sha256', 'config', 'batch_factory'))
    for name in IDENTITY_FIELDS - mutable_identity:
        _need(_json(source_identity[name]) == _json(target_identity[name]), 'Frozen identity changed')
    for name in FACTORY_FIELDS:
        _need(_json(source_identity['batch_factory'][name]) == _json(target_identity['batch_factory'][name]),
              'Frozen graph factory changed')
