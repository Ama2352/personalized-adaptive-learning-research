"""Đối chiếu metadata producer sau khi caller đã kiểm bytes của từng FileRef.

Không thay accepted-operation receipts, source snapshot verification, kiểm CSV
toàn quần thể hoặc quyền freeze/refit. Không đọc file và không import model.
"""
from dataclasses import asdict
import math
from pathlib import PurePosixPath

from .research_admission import PopulationExpectation
from .research_selected_checkpoint import validate_selected_checkpoint, _json
from .research_selected_rows import decode_selected_claim, _exact_fields
from .research_selection_io import FileRef, need
from .simulator_bridge import identity_hash

DOCUMENT_ROLES = ('invocation', 'complete', 'terminal', 'claim', 'coverage',
                  'checkpoint_complete', 'checkpoint_metadata')
ARTIFACT_ROLES = (*DOCUMENT_ROLES, 'checkpoint', 'predictions', 'targets', 'events', 'runtime', 'config_or_spec')
CLAIM_ARTIFACTS = {'terminal': 'terminal', 'checkpoint': 'checkpoint', 'raw_predictions': 'predictions',
                   'targets': 'targets', 'coverage': 'coverage'}

# Bốn controller CPU đã review, không dùng startswith('ACCEPTED') hoặc cho
# controller khác tự thừa kế quyền. Matrix chính cần profile thực thi riêng.
ENGINEERING_CONTROLLERS = {
    'A0': ('ACCEPTED_ACTUAL_TINY_A0_SELECTED_ONLY_ENGINEERING', 'ACTUAL_TINY_A0_SELECTED_ONLY_PENDING_OUTER'),
    'A1_EXPERT': ('ACCEPTED_ACTUAL_A1_EXPERT_SELECTED_ONLY_ENGINEERING', 'ACTUAL_A1_EXPERT_SELECTED_ONLY_PENDING_OUTER'),
    'SAKT': ('ACCEPTED_ACTUAL_SAKT_SELECTED_ONLY_ENGINEERING', 'ACTUAL_SAKT_SELECTED_ENGINEERING_PENDING_OUTER'),
    'GKT': ('ACCEPTED_ACTUAL_GKT_SELECTED_ONLY_ENGINEERING', 'ACTUAL_GKT_SELECTED_ENGINEERING_PENDING_OUTER'),
}


def validate_engineering_operation(*, candidate_id, outer, owned, worker,
                                   request_ref, worker_ref, expected_source_hashes,
                                   native_refs, expected_input_hashes=None, expected_runtime_hashes=None):
    """Đối chiếu receipt bốn controller lịch sử, chưa phải main fit admission.

    Caller pin và hash receipt/worker/request/output, kiểm marker vắng mặt lại
    trước publication. Hàm không coi assertion về marker là bằng chứng I/O.
    """
    need(candidate_id in ENGINEERING_CONTROLLERS, 'Unreviewed operation controller')
    need(type(request_ref) is FileRef and type(worker_ref) is FileRef, 'Pinned request/worker required')
    need(type(outer) is dict and type(owned) is dict and type(worker) is dict, 'Operation JSON objects required')
    outer_status, worker_status = ENGINEERING_CONTROLLERS[candidate_id]
    need(outer['status'] == outer_status and worker['status'] == worker_status, 'Exact controller verdict required')
    need(_json(outer['owned_receipt']) == _json(owned) and _json(outer['worker_result']) == _json(worker),
         'Outer/owned/worker receipt mismatch')
    need(outer['request_sha256'] == worker['request_sha256'] == request_ref.sha256,
         'Operation request binding mismatch')
    need(outer['environment_restored'] is True and outer['automatic_retry'] is False
         and worker['error'] is None and worker['cuda_initialized'] is False
         and worker['observer_restored'] is True and worker['monitor_stopped'] is True
         and worker['denied'] == worker['monitor_errors'] == [], 'Operation restoration/error mismatch')
    need(owned['status'] == 'ACCEPTED_OWNED_PROCESS_LAUNCH_NOT_SCIENTIFIC_ACCEPTANCE'
         and owned['accepted'] is True and owned['GO_released'] is True
         and owned['actual_worker_in_job_before_GO'] is True and owned['cleanup_accepted'] is True
         and owned['popen_handle_closed'] is True and type(owned['returncode']) is int and owned['returncode'] == 0
         and type(owned['job_active_after_cleanup']) is int and owned['job_active_after_cleanup'] == 0
         and owned['errors'] == owned['cleanup_errors'] == [] and owned['automatic_retry'] is False
         and owned['worker_sha256'] == worker_ref.sha256, 'Owned process/cleanup/worker binding mismatch')
    need(type(expected_source_hashes) is dict and expected_source_hashes
         and worker['source_before'] == worker['source_after'] == expected_source_hashes,
         'Operation source before/after mismatch')
    resources = worker['resources']
    need(type(resources['samples']) is int and resources['samples'] > 0
         and all(type(resources[name]) is int and 0 <= resources[name] <= 2 * 2**30
                 for name in ('peak_worker_rss_bytes', 'peak_family_rss_bytes'))
         and type(resources['minimum_available_ram_bytes']) is int
         and resources['minimum_available_ram_bytes'] >= 2 * 2**30, 'Reviewed sampled RAM bounds required')
    if candidate_id == 'A1_EXPERT':
        need(worker['job_query_handle_closed'] is True, 'A1 resource query handle must be closed')
    if candidate_id in ('A0', 'A1_EXPERT'):
        need(outer['error'] is None and outer['research_matrix_completed'] is False
             and outer['cuda_readiness'] is False and worker['research_main_matrix_completed'] is False,
             'AKT engineering scope mismatch')
        outer_cap = outer['outer_cap_seconds']
        need(expected_input_hashes is None and expected_runtime_hashes is None,
             'AKT controller uses its reviewed source inventory for operation inputs')
    else:
        need(outer['errors'] == [] and outer['full_main_matrix_completed'] is False
             and outer['refit_or_calibration_performed'] is False and outer['gpu_ready'] is False
             and outer['owned_launch_requested'] is True and outer['worker_GO_released'] is True
             and worker['environment_and_sys_restored'] is True and worker['job_query_handle_closed'] is True
             and worker['full_main_matrix_completed'] is False and worker['refit_or_calibration_performed'] is False,
             'Baseline engineering scope/restoration mismatch')
        need(type(expected_input_hashes) is dict and expected_input_hashes
             and worker['input_before'] == worker['input_after'] == expected_input_hashes
             and type(expected_runtime_hashes) is dict and expected_runtime_hashes
             and worker['runtime_before'] == worker['runtime_after'] == expected_runtime_hashes,
             'Baseline operation input/runtime mismatch')
        need(outer['authorization_sha256'] == worker['authorization_sha256'], 'Baseline authorization mismatch')
        outer_cap = outer['whole_cap_seconds']
    need(type(owned['max_seconds']) in (int, float) and math.isfinite(owned['max_seconds'])
         and 0 < owned['max_seconds'] <= 580, 'Reviewed owned budget required')
    need(type(outer_cap) is int and outer_cap == 600, 'Reviewed outer budget required')
    for value, cap in ((outer['elapsed_seconds'], outer_cap), (worker['elapsed_seconds'], 560),
                       (owned['elapsed_seconds'], owned['max_seconds'])):
        need(type(value) in (int, float) and math.isfinite(value) and 0 <= value < cap,
             'Operation finite elapsed budget required')
    need(type(native_refs) is dict and native_refs and all(type(ref) is FileRef for ref in native_refs.values()),
         'Externally verified full native inventory required')
    need(set(worker['native_outputs']) == set(native_refs), 'Operation native inventory mismatch')
    for path, ref in native_refs.items():
        record = worker['native_outputs'][path]
        need(path == ref.path and record['sha256'] == ref.sha256
             and type(record['bytes']) is int and record['bytes'] == ref.size_bytes,
             'Operation output byte binding mismatch')


def validate_selected_metadata(*, documents, artifact_refs, expected_claim_binding,
                               expected_checkpoint_identity, producer_source_files, population):
    """Kiểm đúng ba schema, trả typed claim khai báo đã đối chiếu metadata."""
    _exact_fields(documents, DOCUMENT_ROLES)
    _exact_fields(artifact_refs, ARTIFACT_ROLES)
    need(all(type(value) is dict for value in documents.values()), 'JSON document objects required')
    need(all(type(ref) is FileRef for ref in artifact_refs.values()), 'Typed externally pinned refs required')
    need(type(population) is PopulationExpectation, 'Independent population expectation required')
    claim = decode_selected_claim(documents['claim'])
    binding = {name: value for name, value in asdict(claim).items() if name not in CLAIM_ARTIFACTS}
    need(_json(binding) == _json(expected_claim_binding), 'Exact reviewed claim binding mismatch')
    need(claim.context == population.context and claim.full_targets == population.full_targets,
         'Claim/independent population mismatch')
    for name, role in CLAIM_ARTIFACTS.items():
        artifact, ref = getattr(claim, name), artifact_refs[role]
        need((artifact.sha256, artifact.size_bytes) == (ref.sha256, ref.size_bytes), 'Claim artifact bytes mismatch')
    need(claim.stage_journal_sha256 == artifact_refs['events'].sha256
         and claim.runtime_sha256 == artifact_refs['runtime'].sha256, 'Journal/runtime pin mismatch')
    complete, terminal = documents['complete'], documents['terminal']
    need(complete['terminal_sha256'] == artifact_refs['terminal'].sha256
         and complete['claim_sha256'] == artifact_refs['claim'].sha256, 'COMPLETE terminal/claim linkage mismatch')
    for name in ('kind', 'status', 'candidate_id', 'selected_epoch', 'complete_fit_epochs'):
        expected = claim.terminal_kind if name == 'kind' else getattr(claim, name)
        need(_json(terminal[name]) == _json(expected), 'Terminal selected claim mismatch')
    for name in ('external_freeze_authority', 'refit_started', 'calibration_used_for_selection'):
        need(terminal[name] is False, 'Selected-only terminal scope required')
    coverage = documents['coverage']
    for name in ('full_targets', 'supported_targets'):
        need(type(coverage[name]) is int and coverage[name] == getattr(claim, name), 'Coverage count mismatch')
    need(type(coverage['unsupported_targets']) is int
         and coverage['unsupported_targets'] == claim.full_targets - claim.supported_targets
         and coverage['objective'] == claim.epoch_objective_id, 'Coverage objective/support mismatch')
    invocation = documents['invocation']
    identity, spec = invocation['identity'], invocation['spec']
    need(identity['refit_allowed'] is False and identity['calibration_allowed'] is False,
         'Selected invocation scope required')
    need(type(producer_source_files) is dict and producer_source_files
         and all(type(name) is str and type(ref) is FileRef for name, ref in producer_source_files.items()),
         'Externally verified historical source snapshots required')
    source_hashes = {name: ref.sha256 for name, ref in producer_source_files.items()}
    if claim.candidate_id.startswith('A'):
        need(invocation['scope'] == 'MAIN_SELECTED_ONLY_NO_REFIT'
             and identity['external_freeze_authority'] is False, 'AKT selected invocation required')
        stage = spec['stage']
        need(_json(stage['context']) == _json(asdict(claim.context))
             and stage['candidate_id'] == claim.candidate_id, 'AKT stage context/candidate mismatch')
        for name in ('config_sha256', 'sources_sha256', 'runtime_sha256',
                     'graph_condition_sha256', 'graph_train_role_sha256'):
            need(stage[name] == getattr(claim, name), 'AKT stage claim mismatch')
        need(identity['config_sha256'] == claim.config_sha256
             and identity['native_evidence']['build_hashes'] == source_hashes, 'AKT source/config binding mismatch')
        need(complete['status'] == 'COMPLETE_MAIN_SELECTED_ONLY_CANDIDATE'
             and complete['main_matrix_complete'] is False and complete['system_winner'] is None
             and complete['refit_calibration_performed'] is False
             and terminal['system_selection_performed'] is False and terminal['fresh_best_reload'] is True,
             'AKT completion scope mismatch')
        for name, role in (('raw_prediction_sha256', 'predictions'), ('target_sha256', 'targets'),
                           ('journal_sha256', 'events')):
            need(terminal[name] == artifact_refs[role].sha256, 'AKT terminal exports mismatch')
        need(terminal['checkpoint']['checkpoint_sha256'] == artifact_refs['checkpoint'].sha256
             and terminal['checkpoint']['complete_sha256'] == artifact_refs['checkpoint_complete'].sha256,
             'AKT terminal checkpoint mismatch')
        need(terminal['weights_phase'] == claim.weights_phase
             and terminal['prediction_phase'] == claim.prediction_phase, 'AKT terminal phase mismatch')
        need(_json(terminal['full_selection']) == _json(coverage), 'AKT terminal coverage mismatch')
        run_directory = PurePosixPath(artifact_refs['complete'].path).parent
        for role in ('invocation', 'terminal', 'claim', 'coverage', 'checkpoint_complete',
                     'checkpoint_metadata', 'checkpoint', 'predictions', 'targets', 'events'):
            path = PurePosixPath(artifact_refs[role].path)
            need(path.is_relative_to(run_directory)
                 and complete['outputs_sha256'][path.relative_to(run_directory).as_posix()] == artifact_refs[role].sha256,
                 'AKT COMPLETE output inventory mismatch')
        need(coverage['population_scheme'] == 'full-query-keys-and-observable-shard-bindings-v1',
             'Keep original AKT population scheme')
    else:
        family = claim.candidate_id.lower()
        need(invocation['scope'] == family + '_main_selected_only_v1'
             and invocation['candidate_id'] == identity['candidate_id'] == claim.candidate_id,
             'Baseline invocation family mismatch')
        need(_json(spec['context']) == _json(asdict(claim.context))
             and _json(identity['context']) == _json(asdict(claim.context)), 'Baseline context mismatch')
        need(identity_hash(spec) == identity['spec_sha256'] == claim.config_sha256
             and identity['source_files'] == source_hashes and identity['sources_sha256'] == claim.sources_sha256
             and identity['runtime_sha256'] == claim.runtime_sha256, 'Baseline spec/source/runtime mismatch')
        need(complete['status'] == 'COMPLETE_' + claim.candidate_id + '_MAIN_SELECTED_ONLY'
             and complete['system_freeze_performed'] is False, 'Baseline completion scope mismatch')
        need(terminal['checkpoint_sha256'] == artifact_refs['checkpoint'].sha256
             and terminal['complete_sha256'] == artifact_refs['checkpoint_complete'].sha256
             and terminal['source_sha256'] == claim.sources_sha256
             and terminal['runtime_sha256'] == claim.runtime_sha256, 'Baseline terminal binding mismatch')
        need(_json(coverage['unsupported_counts']) == _json(dict(claim.unsupported_counts)),
             'Baseline unsupported reason counts mismatch')
        need(coverage['population'] == dict(scheme=population.scheme,
             full_keys_sha256=population.full_keys_sha256, full_keys_labels_sha256=population.full_keys_labels_sha256),
             'Baseline independent population hash mismatch')
    need(identity_hash(source_hashes) == claim.sources_sha256, 'Historical source vector digest mismatch')
    validate_selected_checkpoint(claim=claim, complete=documents['checkpoint_complete'],
        metadata=documents['checkpoint_metadata'], complete_ref=artifact_refs['checkpoint_complete'],
        metadata_ref=artifact_refs['checkpoint_metadata'], checkpoint_ref=artifact_refs['checkpoint'],
        expected_identity=expected_checkpoint_identity)
    return claim
