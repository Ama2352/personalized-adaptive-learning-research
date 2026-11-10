"""Kiểm liên kết JSON checkpoint đã pin, không deserialize tensor hoặc cấp quyền.

Caller phải xác minh bytes của cả ba FileRef bằng reader và ghim identity từ
request đã review. Kết quả hàm này chỉ là một điều kiện của file admission.
"""
import json
from pathlib import PurePosixPath

from .research_admission import SelectedCandidateClaim
from .akt.research_main_stage import CANDIDATE_BINDINGS
from .research_selected_rows import _exact_fields
from .research_selection_io import FileRef, need

AKT_ROLE = 'cgakt_research_complete_epoch_training_state_v1'
SAKT_ROLE = 'sakt_research_training_state_epoch_boundary_only'
GKT_ROLE = 'gkt_research_complete_epoch_state_no_lifecycle_authority'


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def validate_selected_checkpoint(*, claim, complete, metadata, complete_ref,
                                 metadata_ref, checkpoint_ref, expected_identity):
    """Đối chiếu epoch tốt nhất và train80, giữ riêng phase selection của claim."""
    need(type(claim) is SelectedCandidateClaim, 'Typed selected claim required')
    claim.validate()
    for ref, filename in ((complete_ref, 'COMPLETE.json'), (metadata_ref, 'metadata.json'),
                          (checkpoint_ref, 'state.pt')):
        need(type(ref) is FileRef, 'Pinned checkpoint FileRef required')
        need(PurePosixPath(ref.path).name == filename, 'Exact checkpoint filename required')
    need(len({PurePosixPath(ref.path).parent for ref in (complete_ref, metadata_ref, checkpoint_ref)}) == 1,
         'Checkpoint files must share directory')
    _exact_fields(complete, ('schema_version', 'status', 'metadata_sha256', 'checkpoint_sha256'))
    need(type(complete['schema_version']) is int, 'Checkpoint COMPLETE schema')
    need(complete['metadata_sha256'] == metadata_ref.sha256
         and complete['checkpoint_sha256'] == checkpoint_ref.sha256 == claim.checkpoint.sha256
         and checkpoint_ref.size_bytes == claim.checkpoint.size_bytes, 'Checkpoint bytes linkage mismatch')
    need(type(metadata) is dict and type(expected_identity) is dict, 'Pinned JSON identity required')
    need(_json(metadata['identity']) == _json(expected_identity), 'Full checkpoint identity mismatch')
    need(type(metadata['schema_version']) is int and metadata['schema_version'] == complete['schema_version'],
         'Checkpoint metadata schema')
    need(type(metadata['checkpoint_bytes']) is int and metadata['checkpoint_bytes'] == checkpoint_ref.size_bytes
         and metadata['checkpoint_sha256'] == checkpoint_ref.sha256, 'Metadata checkpoint bytes mismatch')
    identity = metadata['identity']
    need(type(identity['schema_version']) is int and identity['fitted_research_model'] is False,
         'Computation checkpoint identity required')
    need(identity['schema_version'] == metadata['schema_version'], 'Identity schema mismatch')
    common = ('schema_version', 'role', 'identity', 'checkpoint_sha256', 'checkpoint_bytes')
    if claim.candidate_id.startswith('A'):
        _exact_fields(metadata, (*common, 'fitted_research_model', 'iterator_resume_supported', 'layout',
            'lifecycle_resume_supported', 'producer_config', 'receipt', 'restore_scope', 'state_representation'))
        need(complete['status'] == 'COMPLETE_CGAKT_EPOCH_TRAINING_STATE'
             and metadata['role'] == identity['role'] == AKT_ROLE, 'AKT checkpoint role/status mismatch')
        need(identity['schema_version'] in (1, 2), 'AKT checkpoint identity schema')
        binding, profile = identity['neural_binding'], identity['profile']
        need(binding['phase_scope'] == binding['encoding_fit_scope'] == 'select_train80'
             and binding['encoding_sha256'] == identity['encoding_sha256'] == claim.encoding_sha256
             and binding['vocabulary_sha256'] == claim.vocabulary_sha256
             and binding['selection_freeze_sha256'] is None, 'AKT train encoding binding mismatch')
        need(profile['purpose'] == 'selected_fit_candidate' and profile['external_system_freeze_sha256'] is None
             and profile['initial_backbone_sha256'] == claim.initial_backbone_sha256
             and profile['runtime_receipt_sha256'] == claim.runtime_sha256
             and profile['protocol21_sha256'] == claim.context.protocol21_sha256
             and profile['protocol26_sha256'] == claim.context.recipe26_sha256
             and profile['candidate_allocation_sha256'] == claim.context.allocation_sha256,
             'AKT selected profile mismatch')
        epoch = metadata['receipt']['completed_epochs']
        need(metadata['fitted_research_model'] is False and metadata['iterator_resume_supported'] is False
             and metadata['lifecycle_resume_supported'] is False
             and metadata['restore_scope'] == 'completed_epoch_boundary', 'AKT checkpoint computation scope')
        variant = next(variant for candidate, variant, _ in CANDIDATE_BINDINGS if candidate == claim.candidate_id)
        graph_mode = {'disabled': 'none', 'expert': 'expert_declared', 'learned': 'method24_learned'}[claim.estimator_graph]
        need(identity['condition']['variant'] == variant and identity['condition']['graph_mode'] == graph_mode
             and identity['condition']['train80']['train_shard_sha256'] == claim.context.train_role_sha256,
             'AKT variant/train role mismatch')
    elif claim.candidate_id == 'SAKT':
        _exact_fields(metadata, (*common, 'progress', 'model_state_sha256', 'restore_scope',
                                'iterator_resume_supported', 'fitted_research_model'))
        need(complete['status'] == 'COMPLETE_SAKT_EPOCH_TRAINING_STATE'
             and metadata['role'] == identity['role'] == SAKT_ROLE, 'SAKT checkpoint role/status mismatch')
        need(metadata['restore_scope'] == 'completed_epoch_boundary'
             and metadata['iterator_resume_supported'] is False and metadata['fitted_research_model'] is False,
             'SAKT checkpoint computation scope')
        need(identity['vocabulary_sha256'] == claim.vocabulary_sha256, 'SAKT vocabulary mismatch')
        epoch = metadata['progress']['completed_epochs']
    else:
        _exact_fields(metadata, (*common, 'counters', 'model_sha256', 'participation', 'owned_rng_sha256', 'module_modes'))
        need(complete['status'] == 'COMPLETE_GKT_EPOCH_STATE'
             and metadata['role'] == identity['role'] == GKT_ROLE, 'GKT checkpoint role/status mismatch')
        need(identity['model_spec']['vocabulary_sha256'] == claim.vocabulary_sha256
             and identity['profile']['initial_model_sha256'] == claim.initial_model_sha256
             and identity['graph']['train80_shard_sha256'] == claim.context.train_role_sha256,
             'GKT model/graph binding mismatch')
        epoch = metadata['counters']['complete_train_epochs']
        need(type(identity['completed_epoch_spec']['epoch']) is int
             and identity['completed_epoch_spec']['epoch'] == epoch, 'GKT epoch spec mismatch')
    if not claim.candidate_id.startswith('A'):
        need(identity['schema_version'] == 1 and identity['phase_scope'] == 'select_train80'
             and identity['encoding_sha256'] == claim.encoding_sha256
             and identity['profile']['runtime_sha256'] == claim.runtime_sha256
             and identity['profile']['protocol_sha256'] == claim.context.protocol21_sha256,
             'Baseline train encoding/profile mismatch')
    need(type(epoch) is int and epoch == claim.selected_epoch, 'Checkpoint must be selected epoch, not last epoch')
