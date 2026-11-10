"""Đối chiếu metadata producer sau khi caller đã kiểm bytes của từng FileRef.

Không thay accepted-operation receipts, source snapshot verification, kiểm CSV
toàn quần thể hoặc quyền freeze/refit. Không đọc file và không import model.
"""
from dataclasses import asdict
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
