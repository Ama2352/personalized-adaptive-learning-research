"""Tích hợp chín producer giả bằng file thật nhỏ, không NN hoặc scientificN."""
from dataclasses import asdict, replace
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from knowledge_tracing import research_admission as admission
from knowledge_tracing import research_selected_files as module
from knowledge_tracing.research_selected_metadata import CLAIM_ARTIFACTS
from knowledge_tracing.research_selection_io import FileReadLimits, FileRef, csv_fields
from knowledge_tracing.simulator_bridge import identity_hash
from test_research_selected_metadata import fixture as metadata_fixture
from test_research_selected_rows import H


def io_limits():
    return FileReadLimits(2**20, 32 * 2**20, 256, 1, 2**20, 2**20, 16384,
                         32, 256, 16384, 64, 4096, 15.)


def admission_limits():
    return admission.AdmissionLimits(8, 32, 16, 288, 10.)


class SelectedFilesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='nine_selected_files_')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def put(self, path, data):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return FileRef(path, hashlib.sha256(data).hexdigest(), len(data))

    def json(self, path, value):
        return self.put(path, (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n').encode())

    def csv(self, path, candidate, kind, rows):
        buffer = io.StringIO(newline='')
        writer = csv.DictWriter(buffer, fieldnames=csv_fields(candidate, kind))
        writer.writeheader()
        writer.writerows(rows)
        return self.put(path, buffer.getvalue().encode())

    def fixture(self, *, wrong_labels=False, different_backbone=False, foreign_key=False, empty_common=False,
                learner_targets=None):
        learner_ranks = (('a', 0), ('a', 1), ('b', 0), ('c', 0)) if learner_targets is None else tuple(
            (learner, rank) for learner, count in learner_targets for rank in range(count))
        keys = tuple(admission.ModelNeutralKey(learner, 'item', ordinal, ordinal, rank,
            admission.HISTORY_SCHEME, H, 'selection') for ordinal, (learner, rank) in
            enumerate(learner_ranks))
        count = len(keys)
        key_hash, label_hash = hashlib.sha256(), hashlib.sha256()
        for ordinal, key in enumerate(keys):
            key_hash.update(admission._canonical(key.values()))
            label_hash.update(admission._canonical((key.values(), ordinal % 2)))
        context = admission.MainSelectionContext(**metadata_fixture()['documents']['claim']['context'])
        population = admission.PopulationExpectation(context, count, key_hash.hexdigest(), label_hash.hexdigest())
        request = dict(schema_version=1, kind=module.REQUEST_KIND, scope=module.REQUEST_SCOPE,
                       population=asdict(population), candidates={}, source_inventory={})
        repo = Path(__file__).resolve().parents[2]
        for logical in module.REQUIRED_SOURCES:
            request['source_inventory'][logical] = asdict(self.put(logical, (repo / logical).read_bytes()))
        source_ref = self.put('snapshots/producer.py', b'# textual fixture only\n')
        source_hashes = {'src/knowledge_tracing/example.py': source_ref.sha256}
        for candidate in admission.REQUIRED_CANDIDATE_IDS:
            base = metadata_fixture(candidate)
            docs, wire = base['documents'], base['documents']['claim']
            directory = 'runs/' + candidate + '/'
            refs = {}
            wire.update(full_targets=count, supported_targets=count-1 if candidate == 'A3_EXPERT' else count,
                unsupported_counts=[['oov_item', 1]] if candidate == 'A3_EXPERT' else [],
                sources_sha256=identity_hash(source_hashes))
            if empty_common and candidate == 'A0':
                wire.update(supported_targets=0, unsupported_counts=[['oov_item', count]])
            if different_backbone and candidate == 'A1_EXPERT':
                wire['initial_backbone_sha256'] = 'b' * 64
                docs['checkpoint_metadata']['identity']['profile']['initial_backbone_sha256'] = 'b' * 64
            coverage = docs['coverage']
            coverage.update(full_targets=count, supported_targets=wire['supported_targets'],
                            unsupported_targets=count-wire['supported_targets'])
            if not candidate.startswith('A'):
                coverage.update(unsupported_counts={}, population=dict(scheme=population.scheme,
                    full_keys_sha256=population.full_keys_sha256, full_keys_labels_sha256=population.full_keys_labels_sha256))
            identity = docs['invocation']['identity']
            if candidate.startswith('A'):
                identity['native_evidence']['build_hashes'] = source_hashes
                docs['invocation']['spec']['stage']['sources_sha256'] = wire['sources_sha256']
            else:
                identity.update(source_files=source_hashes, sources_sha256=wire['sources_sha256'])
                docs['terminal']['source_sha256'] = wire['sources_sha256']
            predictions, targets = [], []
            for ordinal, key in enumerate(keys):
                unsupported = candidate == 'A3_EXPERT' and ordinal == count-1 or empty_common and candidate == 'A0'
                values = dict(**asdict(key), phase_scope='raw_selection10', phase_sha256=H, encoding_sha256=H,
                    correct=(1-ordinal % 2 if wrong_labels and ordinal == 0 else ordinal % 2),
                    probability='' if unsupported else '0.5', support_reason='oov_item' if unsupported else 'supported',
                    input_support_reason='cold_query_only', window_id='' if unsupported else H,
                    history_available='' if unsupported else '0', history_used='' if unsupported else '0',
                    context_reset='' if unsupported else 'False')
                if foreign_key and candidate == 'GKT' and ordinal == 0:
                    values['item_id'] = 'different'
                predictions.append({name: values[name] for name in csv_fields(candidate, 'predictions')})
                targets.append({name: values[name] for name in csv_fields(candidate, 'targets')})
            refs['predictions'] = self.csv(directory+'selection/predictions.csv', candidate, 'predictions', predictions[::-1])
            refs['targets'] = self.csv(directory+'selection/targets.csv', candidate, 'targets', targets)
            refs['coverage'] = self.json(directory+'selection/coverage.json', coverage)
            refs['events'] = self.put(directory+'events.jsonl', b'{"fixture":true}\n')
            refs['runtime'] = self.put(directory+'runtime.json', b'{"fixture":true}\n')
            refs['checkpoint'] = self.put(directory+'checkpoint/state.pt', b'not a tensor checkpoint')
            wire.update(stage_journal_sha256=refs['events'].sha256, runtime_sha256=refs['runtime'].sha256)
            metadata = docs['checkpoint_metadata']
            metadata.update(checkpoint_bytes=refs['checkpoint'].size_bytes, checkpoint_sha256=refs['checkpoint'].sha256)
            profile = metadata['identity']['profile']
            profile['runtime_receipt_sha256' if candidate.startswith('A') else 'runtime_sha256'] = wire['runtime_sha256']
            refs['checkpoint_metadata'] = self.json(directory+'checkpoint/metadata.json', metadata)
            docs['checkpoint_complete'].update(metadata_sha256=refs['checkpoint_metadata'].sha256,
                                               checkpoint_sha256=refs['checkpoint'].sha256)
            refs['checkpoint_complete'] = self.json(directory+'checkpoint/COMPLETE.json', docs['checkpoint_complete'])
            terminal = docs['terminal']
            if candidate.startswith('A'):
                terminal.update(full_selection=coverage, raw_prediction_sha256=refs['predictions'].sha256,
                    target_sha256=refs['targets'].sha256, journal_sha256=refs['events'].sha256,
                    checkpoint=dict(checkpoint_sha256=refs['checkpoint'].sha256,
                                    complete_sha256=refs['checkpoint_complete'].sha256))
                docs['invocation']['spec']['stage']['runtime_sha256'] = wire['runtime_sha256']
            else:
                terminal.update(runtime_sha256=wire['runtime_sha256'], checkpoint_sha256=refs['checkpoint'].sha256,
                                complete_sha256=refs['checkpoint_complete'].sha256)
                identity['runtime_sha256'] = wire['runtime_sha256']
            refs['invocation'] = self.json(directory+'invocation.json', docs['invocation'])
            refs['config_or_spec'] = refs['invocation']
            refs['terminal'] = self.json(directory+'selected-terminal.json', terminal)
            for name, role in CLAIM_ARTIFACTS.items():
                wire[name] = dict(sha256=refs[role].sha256, size_bytes=refs[role].size_bytes)
            refs['claim'] = self.json(directory+'selected-claim.json', wire)
            complete = docs['complete']
            complete.update(claim_sha256=refs['claim'].sha256, terminal_sha256=refs['terminal'].sha256)
            if candidate.startswith('A'):
                complete['outputs_sha256'] = {ref.path.removeprefix(directory): ref.sha256 for role, ref in refs.items()
                                              if role not in ('runtime', 'config_or_spec')}
            refs['complete'] = self.json(directory+'COMPLETE.json', complete)
            request['candidates'][candidate] = dict(artifacts={role: asdict(ref) for role, ref in refs.items()},
                expected_claim_binding={name: value for name, value in wire.items()
                                        if name not in CLAIM_ARTIFACTS},
                expected_checkpoint_identity=metadata['identity'],
                producer_source_files={name: asdict(source_ref) for name in source_hashes})
        return request, population

    def read(self, request, population, **changes):
        return module.read_nine_selected_statistics(self.root, request_ref=self.json('request.json', request),
            population=population, io_limits=io_limits(), admission_limits=replace(admission_limits(), **changes))

    def publish(self, request, population, *, output='research_tracking/runs/review-test', output_limit=None,
                input_limit=None):
        (self.root / 'research_tracking/runs').mkdir(parents=True, exist_ok=True)
        logical = 'src/knowledge_tracing/akt/filesystem.py'
        publisher = self.put(logical, (Path(__file__).resolve().parents[2] / logical).read_bytes())
        return module.publish_nine_statistics_review(self.root, request_ref=self.json('request.json', request),
            population=population, output_directory=output, atomic_publisher_ref=publisher,
            io_limits=input_limit or replace(io_limits(), max_open_files=18), admission_limits=admission_limits(),
            publication_limits=output_limit or module.StatisticsPublicationLimits(2**20, 512*1024, 15.))

    def test_nine_files_to_common_statistics_without_authority(self):
        result = self.read(*self.fixture())
        self.assertEqual((result.statistics.full_targets, result.statistics.common_targets, result.statistics.row_checks), (4, 3, 36))
        self.assertEqual(result.statistics.common_population_coverage.zero_contribution_learner_ids, ('c',))
        self.assertEqual(tuple(row.common_target_count for row in result.statistics.common_statistics), (2, 1))
        for learner in result.statistics.common_statistics:
            for candidate in learner.candidates:
                self.assertAlmostEqual(candidate.loss_sum, learner.common_target_count * math.log(2), places=12)
        self.assertFalse(result.operation_receipts_accepted or result.external_freeze_authority or result.main_refit_authorized)
        self.assertFalse(result.statistics.artifact_bytes_verified or result.statistics.nine_terminal_files_admitted)
        self.assertEqual(result.index_entries, 72)

    def test_fixture_scales_without_changing_original_population(self):
        request, population = self.fixture(learner_targets=(('a', 4), ('b', 4)))
        result = self.read(request, population)
        self.assertEqual((population.full_targets, result.statistics.common_targets, result.index_entries), (8, 7, 144))

    def test_scoped_eighteen_handles_preserve_same_statistics(self):
        request, population = self.fixture()
        original = self.read(request, population)
        result = module.read_nine_selected_statistics(self.root, request_ref=self.json('request.json', request),
            population=population, io_limits=replace(io_limits(), max_open_files=18), admission_limits=admission_limits())
        self.assertEqual(replace(original.statistics, elapsed_seconds=0), replace(result.statistics, elapsed_seconds=0))
        self.assertEqual(original.verified_files, result.verified_files)
        self.assertEqual(original.bytes_read, result.bytes_read)

    def test_missing_candidate_rejected_before_artifact_read(self):
        request, population = self.fixture()
        del request['candidates']['SAKT']
        request['source_inventory'][module.REQUIRED_SOURCES[0]]['path'] = 'does-not-exist'
        with self.assertRaisesRegex(ValueError, 'Exact object fields'):
            self.read(request, population)

    def test_shared_backbone_and_foreign_key_rejected(self):
        for option in ('different_backbone', 'foreign_key'):
            with self.subTest(option=option), self.assertRaises(ValueError):
                self.read(*self.fixture(**{option: True}))

    def test_all_nine_same_wrong_labels_still_rejected(self):
        with self.assertRaisesRegex(ValueError, 'F/K/y'):
            self.read(*self.fixture(wrong_labels=True))

    def test_empty_common_and_row_limits_rejected(self):
        with self.assertRaisesRegex(ValueError, 'EMPTY_COMMON'):
            self.read(*self.fixture(empty_common=True))
        with self.assertRaises(ValueError):
            self.read(*self.fixture(), max_row_checks=35)

    def test_tampered_file_and_request_scope_rejected(self):
        request, population = self.fixture()
        path = self.root / request['candidates']['GKT']['artifacts']['checkpoint']['path']
        path.write_bytes(b'tampered')
        with self.assertRaises(ValueError):
            self.read(request, population)
        request, population = self.fixture()
        request['scope'] = 'RUN_REFIT'
        with self.assertRaises(ValueError):
            self.read(request, population)

    def test_late_source_mutation_rejected_on_final_rehash(self):
        request, population = self.fixture()
        original = module.normalize_selected_row
        changed = False

        def mutate(*args):
            nonlocal changed
            row = original(*args)
            if not changed:
                (self.root / 'snapshots/producer.py').write_bytes(b'# late mutation\n')
                changed = True
            return row

        with patch.object(module, 'normalize_selected_row', side_effect=mutate), self.assertRaises(ValueError):
            self.read(request, population)

    def test_deadline_still_checked_after_result_construction(self):
        from knowledge_tracing import research_selection_io as reader_module
        request, population = self.fixture()
        constructor, clock = module.SelectedFileStatistics, reader_module._now
        constructed = False

        def late_result(*args):
            nonlocal constructed
            result = constructor(*args)
            constructed = True
            return result

        with patch.object(module, 'SelectedFileStatistics', side_effect=late_result), \
                patch.object(reader_module, '_now', side_effect=lambda: clock() + (100 if constructed else 0)), \
                self.assertRaisesRegex(ValueError, 'deadline'):
            self.read(request, population)

    def test_publication_readback_and_no_selection_authority(self):
        complete_ref = self.publish(*self.fixture())
        complete = json.loads((self.root / complete_ref.path).read_bytes())
        self.assertEqual(complete['status'], 'COMPLETE_CACHED_NINE_STATISTICS_REVIEW_V1')
        self.assertTrue(complete['caller_operation_acceptance_required'])
        self.assertFalse(complete['operation_receipts_accepted'] or complete['external_freeze_authority']
                         or complete['main_refit_authorized'] or complete['actual_model_selection'])
        self.assertFalse((self.root / complete_ref.path).with_name('FAILURE.json').exists())
        for ref in complete['outputs'].values():
            raw = (self.root / ref['path']).read_bytes()
            self.assertEqual((hashlib.sha256(raw).hexdigest(), len(raw)), (ref['sha256'], ref['size_bytes']))

    def test_publication_existing_run_and_protected_paths_rejected(self):
        request, population = self.fixture()
        directory = self.root / 'research_tracking/runs/review-test'
        directory.mkdir(parents=True)
        (directory / 'sentinel.txt').write_bytes(b'keep')
        with self.assertRaisesRegex(ValueError, 'Never overwrite'):
            self.publish(request, population)
        self.assertEqual((directory / 'sentinel.txt').read_bytes(), b'keep')
        for path in ('dataset/new', 'artifacts/bkt_baseline/new', 'research_tracking/runs/../new'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.publish(request, population, output=path)

    def test_publication_quota_keeps_failure_without_complete(self):
        with self.assertRaisesRegex(ValueError, 'output quota'):
            self.publish(*self.fixture(), output_limit=module.StatisticsPublicationLimits(18000, 8192, 15.))
        directory = self.root / 'research_tracking/runs/review-test'
        self.assertTrue((directory / 'FAILURE.json').is_file())
        self.assertFalse((directory / 'COMPLETE.json').exists())
        self.assertLessEqual(sum(path.stat().st_size for path in directory.iterdir()), 18000)

    def test_publication_input_budget_is_not_reset_after_statistics(self):
        request, population = self.fixture()
        read = self.read(request, population)
        limits = replace(io_limits(), max_open_files=18,
                         max_total_read_bytes=io_limits().max_file_bytes + read.bytes_read // 2)
        with self.assertRaisesRegex(ValueError, 'remaining cumulative input byte budget'):
            self.publish(request, population, input_limit=limits)
        self.assertFalse((self.root / 'research_tracking/runs/review-test').exists())

    def test_publication_input_mutation_after_complete_has_failure_override(self):
        request, population = self.fixture()
        original = module.publish_new_file

        def mutate(source, destination):
            original(source, destination)
            (self.root / 'snapshots/producer.py').write_bytes(b'# changed after COMPLETE\n')

        with patch.object(module, 'publish_new_file', side_effect=mutate), self.assertRaises(ValueError):
            self.publish(request, population)
        directory = self.root / 'research_tracking/runs/review-test'
        self.assertTrue((directory / 'COMPLETE.json').is_file() and (directory / 'FAILURE.json').is_file())

    def test_publication_output_mutation_after_complete_rejected(self):
        request, population = self.fixture()
        original = module.publish_new_file

        def mutate(source, destination):
            original(source, destination)
            path = destination.parent / 'statistics.json'
            path.write_bytes(path.read_bytes().replace(b'"full_targets":4', b'"full_targets":3'))

        with patch.object(module, 'publish_new_file', side_effect=mutate), self.assertRaisesRegex(ValueError, 'SHA mismatch'):
            self.publish(request, population)
        self.assertTrue((self.root / 'research_tracking/runs/review-test/FAILURE.json').is_file())

    def test_publication_deadline_after_complete_keeps_failure(self):
        request, population = self.fixture()
        publish, clock = module.publish_new_file, module._publication_clock
        complete_written = False

        def late(source, destination):
            nonlocal complete_written
            publish(source, destination)
            complete_written = True

        with patch.object(module, 'publish_new_file', side_effect=late), \
                patch.object(module, '_publication_clock', side_effect=lambda: clock() + (100 if complete_written else 0)), \
                self.assertRaisesRegex(ValueError, 'deadline'):
            self.publish(request, population)
        self.assertTrue((self.root / 'research_tracking/runs/review-test/FAILURE.json').is_file())


if __name__ == '__main__':
    unittest.main()
