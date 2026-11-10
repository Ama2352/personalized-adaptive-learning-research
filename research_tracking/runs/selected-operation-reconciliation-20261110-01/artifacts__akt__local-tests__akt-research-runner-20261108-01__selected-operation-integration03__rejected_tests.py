"""Fixtures producer, không chứng nhận bytes hoặc actual execution receipts."""
from copy import deepcopy
from dataclasses import asdict, replace
import json
import unittest

from knowledge_tracing import research_admission as admission
from knowledge_tracing.research_selected_metadata import (
    validate_selected_metadata, validate_engineering_operation, CLAIM_ARTIFACTS, ENGINEERING_CONTROLLERS,
)
from knowledge_tracing.research_selection_io import FileRef
from knowledge_tracing.simulator_bridge import identity_hash
from test_research_selected_checkpoint import fixture as checkpoint_fixture
from test_research_selected_rows import H


def fixture(candidate='A0'):
    checkpoint = checkpoint_fixture(candidate)
    selected = checkpoint['claim']
    source_hashes = {'src/knowledge_tracing/example.py': H}
    selected = replace(selected, sources_sha256=identity_hash(source_hashes))
    context = asdict(selected.context)
    spec = dict(context=context, run_id='fixture')
    if not candidate.startswith('A'):
        selected = replace(selected, config_sha256=identity_hash(spec))
    wire = json.loads(json.dumps(asdict(selected)))
    refs = {role: FileRef('run/' + filename, H, 100) for role, filename in dict(
        invocation='invocation.json', complete='COMPLETE.json', terminal='selected-terminal.json',
        claim='selected-claim.json', coverage='selection/coverage.json', checkpoint_complete='checkpoint/COMPLETE.json',
        checkpoint_metadata='checkpoint/metadata.json', checkpoint='checkpoint/state.pt',
        predictions='selection/predictions.csv', targets='selection/targets.csv', events='events.jsonl',
        runtime='runtime.json', config_or_spec='spec.json').items()}
    terminal = dict(kind=selected.terminal_kind, status=selected.status, candidate_id=candidate,
        selected_epoch=1, complete_fit_epochs=2, external_freeze_authority=False,
        refit_started=False, calibration_used_for_selection=False)
    coverage = dict(full_targets=1, supported_targets=1, unsupported_targets=0, objective=selected.epoch_objective_id)
    identity = dict(refit_allowed=False, calibration_allowed=False)
    complete = dict(terminal_sha256=H, claim_sha256=H)
    if candidate.startswith('A'):
        spec = dict(stage={name: wire[name] for name in ('context', 'candidate_id', 'config_sha256',
            'sources_sha256', 'runtime_sha256', 'graph_condition_sha256', 'graph_train_role_sha256')})
        identity.update(external_freeze_authority=False, config_sha256=H,
                        native_evidence=dict(build_hashes=source_hashes))
        invocation = dict(scope='MAIN_SELECTED_ONLY_NO_REFIT', spec=spec, identity=identity)
        terminal.update(system_selection_performed=False, fresh_best_reload=True,
            raw_prediction_sha256=H, target_sha256=H, journal_sha256=H,
            checkpoint=dict(checkpoint_sha256=H, complete_sha256=H),
            weights_phase=selected.weights_phase, prediction_phase=selected.prediction_phase)
        complete.update(status='COMPLETE_MAIN_SELECTED_ONLY_CANDIDATE', main_matrix_complete=False,
            system_winner=None, refit_calibration_performed=False,
            outputs_sha256={ref.path.removeprefix('run/'): H for name, ref in refs.items()
                            if name not in ('complete', 'runtime', 'config_or_spec')})
        coverage['population_scheme'] = 'full-query-keys-and-observable-shard-bindings-v1'
        terminal['full_selection'] = deepcopy(coverage)
    else:
        identity.update(candidate_id=candidate, context=context, spec_sha256=selected.config_sha256,
            source_files=source_hashes, sources_sha256=selected.sources_sha256, runtime_sha256=H)
        invocation = dict(scope=candidate.lower() + '_main_selected_only_v1', candidate_id=candidate,
                          spec=spec, identity=identity)
        terminal.update(checkpoint_sha256=H, complete_sha256=H,
                        source_sha256=selected.sources_sha256, runtime_sha256=H)
        complete.update(status='COMPLETE_' + candidate + '_MAIN_SELECTED_ONLY', system_freeze_performed=False)
        coverage.update(unsupported_counts={}, population=dict(scheme=admission.POPULATION_SCHEME,
            full_keys_sha256=H, full_keys_labels_sha256=H))
    documents = dict(invocation=invocation, complete=complete, terminal=terminal, claim=wire, coverage=coverage,
                     checkpoint_complete=checkpoint['complete'], checkpoint_metadata=checkpoint['metadata'])
    return dict(documents=documents, artifact_refs=refs,
        expected_claim_binding={name: value for name, value in wire.items() if name not in CLAIM_ARTIFACTS},
        expected_checkpoint_identity=checkpoint['expected_identity'],
        producer_source_files={name: FileRef('snapshots/example.py', digest, 1) for name, digest in source_hashes.items()},
        population=admission.PopulationExpectation(selected.context, 1, H, H))


class ProducerMetadataTests(unittest.TestCase):
    def test_three_schemas_and_nine_conditions(self):
        for candidate in admission.REQUIRED_CANDIDATE_IDS:
            self.assertEqual(validate_selected_metadata(**fixture(candidate)).candidate_id, candidate)

    def test_exact_document_ref_roles_and_reviewed_binding(self):
        for section in ('documents', 'artifact_refs', 'expected_claim_binding'):
            data = fixture()
            data[section]['extra'] = 'value'
            with self.subTest(section=section), self.assertRaises(ValueError):
                validate_selected_metadata(**data)

    def test_terminal_flags_counts_epochs_and_complete_links(self):
        for candidate in ('A0', 'SAKT', 'GKT'):
            for section, key, wrong in (('terminal', 'refit_started', True),
                    ('terminal', 'selected_epoch', True), ('terminal', 'complete_fit_epochs', 3),
                    ('complete', 'claim_sha256', 'b' * 64), ('coverage', 'supported_targets', True),
                    ('coverage', 'objective', 'other')):
                data = fixture(candidate)
                data['documents'][section][key] = wrong
                with self.subTest(candidate=candidate, key=key), self.assertRaises(ValueError):
                    validate_selected_metadata(**data)

    def test_historical_source_snapshot_and_runtime_mismatch(self):
        for candidate in ('A0', 'SAKT', 'GKT'):
            data = fixture(candidate)
            data['producer_source_files']['src/knowledge_tracing/example.py'] = FileRef('snapshots/new.py', 'b' * 64, 1)
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                validate_selected_metadata(**data)
            data = fixture(candidate)
            data['artifact_refs']['runtime'] = FileRef('runtime.json', 'b' * 64, 100)
            with self.assertRaises(ValueError):
                validate_selected_metadata(**data)

    def test_akt_inventory_and_no_premature_system_selection(self):
        for section, key, wrong in (('complete', 'system_winner', 'A0'),
                ('terminal', 'system_selection_performed', True), ('terminal', 'fresh_best_reload', False)):
            data = fixture()
            data['documents'][section][key] = wrong
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_selected_metadata(**data)
        data = fixture()
        data['documents']['complete']['outputs_sha256']['selection/predictions.csv'] = 'b' * 64
        with self.assertRaises(ValueError):
            validate_selected_metadata(**data)
        data = fixture()
        data['documents']['terminal']['full_selection']['full_targets'] = 2
        with self.assertRaises(ValueError):
            validate_selected_metadata(**data)

    def test_baseline_population_and_spec_mismatch(self):
        for candidate in ('SAKT', 'GKT'):
            data = fixture(candidate)
            data['documents']['coverage']['population']['full_keys_labels_sha256'] = 'b' * 64
            with self.assertRaises(ValueError):
                validate_selected_metadata(**data)
            data = fixture(candidate)
            data['documents']['invocation']['spec']['run_id'] = 'changed'
            with self.assertRaises(ValueError):
                validate_selected_metadata(**data)

    def test_claim_byte_size_and_checkpoint_provenance_mismatch(self):
        data = fixture()
        data['artifact_refs']['predictions'] = FileRef('run/selection/predictions.csv', H, 101)
        with self.assertRaises(ValueError):
            validate_selected_metadata(**data)
        data = fixture()
        data['expected_checkpoint_identity']['neural_binding']['encoding_sha256'] = 'b' * 64
        with self.assertRaises(ValueError):
            validate_selected_metadata(**data)


def operation_fixture(candidate='A0'):
    worker = dict(status=ENGINEERING_CONTROLLERS[candidate][1], error=None, request_sha256=H,
        cuda_initialized=False, observer_restored=True, monitor_stopped=True, denied=[], monitor_errors=[],
        source_before={'source.py': H}, source_after={'source.py': H}, research_main_matrix_completed=False,
        elapsed_seconds=1., native_outputs={'run/output.json': dict(sha256=H, bytes=100)},
        job_query_handle_closed=True, resources=dict(samples=1, peak_worker_rss_bytes=100,
            peak_family_rss_bytes=100, minimum_available_ram_bytes=4 * 2**30))
    owned = dict(status='ACCEPTED_OWNED_PROCESS_LAUNCH_NOT_SCIENTIFIC_ACCEPTANCE', accepted=True,
        GO_released=True, actual_worker_in_job_before_GO=True, cleanup_accepted=True, popen_handle_closed=True,
        returncode=0, job_active_after_cleanup=0, errors=[], cleanup_errors=[], automatic_retry=False,
        worker_sha256=H, elapsed_seconds=2., max_seconds=580.)
    outer = dict(status=ENGINEERING_CONTROLLERS[candidate][0], owned_receipt=owned, worker_result=worker,
        request_sha256=H, environment_restored=True, automatic_retry=False, error=None,
        research_matrix_completed=False, cuda_readiness=False, elapsed_seconds=3., outer_cap_seconds=600)
    data = dict(candidate_id=candidate, outer=outer, owned=owned, worker=worker,
        request_ref=FileRef('request.json', H, 100), worker_ref=FileRef('worker.py', H, 100),
        expected_source_hashes={'source.py': H}, native_refs={'run/output.json': FileRef('run/output.json', H, 100)})
    if candidate in ('SAKT', 'GKT'):
        outer.update(errors=[], full_main_matrix_completed=False, refit_or_calibration_performed=False,
            gpu_ready=False, owned_launch_requested=True, worker_GO_released=True, authorization_sha256=H,
            whole_cap_seconds=600)
        worker.update(environment_and_sys_restored=True, job_query_handle_closed=True,
            full_main_matrix_completed=False, refit_or_calibration_performed=False, authorization_sha256=H,
            input_before={'input.json': H}, input_after={'input.json': H},
            runtime_before={'python': H}, runtime_after={'python': H})
        data.update(expected_input_hashes={'input.json': H}, expected_runtime_hashes={'python': H})
    return data


class OperationReceiptTests(unittest.TestCase):
    def test_four_exact_controller_profiles(self):
        for candidate in ENGINEERING_CONTROLLERS:
            self.assertIsNone(validate_engineering_operation(**operation_fixture(candidate)))
        data = operation_fixture()
        data['candidate_id'] = 'A3_EXPERT'
        with self.assertRaises(ValueError):
            validate_engineering_operation(**data)

    def test_no_status_only_acceptance_or_boolean_exit_codes(self):
        for section, key, wrong in (('outer', 'status', 'ACCEPTED'), ('outer', 'environment_restored', False),
                ('worker', 'denied', ['network']), ('owned', 'returncode', False),
                ('owned', 'cleanup_accepted', False), ('owned', 'job_active_after_cleanup', 1),
                ('owned', 'max_seconds', float('inf')), ('outer', 'elapsed_seconds', float('nan'))):
            data = operation_fixture()
            data[section][key] = wrong
            with self.subTest(section=section, key=key), self.assertRaises(ValueError):
                validate_engineering_operation(**data)

    def test_source_input_request_worker_and_output_bindings(self):
        for candidate in ENGINEERING_CONTROLLERS:
            for section, key, wrong in (('worker', 'source_after', {}), ('worker', 'request_sha256', 'b' * 64),
                    ('worker', 'native_outputs', {}), ('owned', 'worker_sha256', 'b' * 64)):
                data = operation_fixture(candidate)
                data[section][key] = wrong
                with self.subTest(candidate=candidate, key=key), self.assertRaises(ValueError):
                    validate_engineering_operation(**data)
        for candidate in ('SAKT', 'GKT'):
            data = operation_fixture(candidate)
            data['worker']['runtime_after'] = {}
            with self.assertRaises(ValueError):
                validate_engineering_operation(**data)

    def test_independent_receipt_consistency_and_scope(self):
        data = operation_fixture()
        data['outer']['owned_receipt'] = dict(data['owned'], cleanup_accepted=False)
        with self.assertRaises(ValueError):
            validate_engineering_operation(**data)
        for candidate in ('SAKT', 'GKT'):
            data = operation_fixture(candidate)
            data['outer']['full_main_matrix_completed'] = True
            with self.assertRaises(ValueError):
                validate_engineering_operation(**data)


if __name__ == '__main__':
    unittest.main()
