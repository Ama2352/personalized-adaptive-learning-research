"""Đối chiếu đầu vào và ngân sách học A0–A3 trước khi cấp lượt chạy."""
from copy import deepcopy


TRAINING_FIELDS = (
    'partition', 'source_commit', 'outer_fold', 'seed', 'context', 'target_block',
    'max_length', 'd_model', 'heads', 'blocks', 'd_ff', 'final_fc', 'dropout',
    'kq_same', 'separate_qa', 'n_pid', 'batch_size', 'lr', 'betas', 'eps',
    'weight_decay', 'max_grad_norm', 'inner_val_fraction', 'min_delta',
    'patience', 'max_epochs', 'protocol_version',
)


def _valid_sha256(value):
    return (type(value) is str and len(value) == 64
            and all(char in '0123456789abcdef' for char in value))


def require_matched_candidate(reference, candidate, *, observed=False):
    """Từ chối mismatch thay vì suy khớp từ số lượng target.

    observed=False kiểm đặc tả trước launch. observed=True còn yêu cầu digest
    population đo từ prediction export. Hàm này không cấp GPU hoặc thay grant.
    """
    if candidate.get('candidate_id') not in ('A0', 'A1_EXPERT', 'A1_LEARNED',
                                            'A2_EXPERT', 'A2_LEARNED', 'A3_EXPERT', 'A3_LEARNED'):
        raise ValueError('Candidate identity required')
    for key in ('data_pins', 'roles_identity', 'encoding_identity',
                'train_view_identity', 'train_targets', 'selection_targets',
                'prediction_implementation', 'initial_backbone_sha256', 'numeric_profile'):
        if key not in reference or candidate.get(key) != reference[key]:
            raise ValueError(f'Comparison mismatch: {key}')
    for key in TRAINING_FIELDS:
        if key not in reference['training_config'] or candidate.get('training_config', {}).get(key) != reference['training_config'][key]:
            raise ValueError(f'Training mismatch: {key}')
    if candidate['candidate_id'] != 'A0':
        graph = candidate.get('graph_provenance', {})
        if graph.get('train_view_identity') != reference['train_view_identity']:
            raise ValueError('Graph must bind exact TRAIN80')
        if graph.get('encoding_identity') != reference['encoding_identity']:
            raise ValueError('Graph vocabulary mismatch')
        if graph.get('history_scope') != 'effective_native_window_prefix':
            raise ValueError('Graph history differs from AKT effective history')
        if not _valid_sha256(graph.get('artifact_sha256')) or graph.get('uses_oracle_labels') is not False:
            raise ValueError('Pinned deployable graph artifact required')
        if candidate['candidate_id'].startswith(('A2', 'A3')):
            if graph.get('confidence_fit_view_identity') != reference['train_view_identity']:
                raise ValueError('Confidence must be fitted only on TRAIN80')
            if not _valid_sha256(graph.get('confidence_artifact_sha256')):
                raise ValueError('Fitted confidence artifact required')
    if observed:
        if candidate.get('observed_selection_population_sha256') != reference['selection_population_sha256']:
            raise ValueError('Observed target population differs from A0')
    return deepcopy(candidate)
