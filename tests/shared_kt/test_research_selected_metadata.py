"""Fixtures producer, không chứng nhận bytes hoặc actual execution receipts."""
from copy import deepcopy
from dataclasses import asdict, replace
import json
import unittest

from knowledge_tracing import research_admission as admission
from knowledge_tracing.research_selected_metadata import validate_selected_metadata, CLAIM_ARTIFACTS
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


if __name__ == '__main__':
    unittest.main()
