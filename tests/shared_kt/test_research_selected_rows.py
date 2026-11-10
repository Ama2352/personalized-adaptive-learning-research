"""Kiểm join/giải mã thuần bằng fixtures, không model hoặc chọn winner."""
from dataclasses import asdict, replace
import json
import unittest

from knowledge_tracing import research_admission as admission
from knowledge_tracing.research_selected_rows import decode_selected_claim, normalize_selected_row
from knowledge_tracing.research_selection_io import csv_fields

H = 'a' * 64


def claim(candidate='A0', reason=None):
    context = admission.MainSelectionContext('grade10_simulator', admission.PROTOCOL21,
        admission.RECIPE26, admission.ALLOCATION, H, H, H, H, 'b' * 64)
    artifact = admission.ArtifactClaim(H, 100)
    graph = candidate not in ('A0', 'SAKT')
    return admission.SelectedCandidateClaim(candidate, context, admission.TERMINAL_KIND,
        'SELECTED_ONLY_COMPLETE', 'selected_fit80', 'raw_selection10', 'select_train80',
        1, 2, artifact, artifact, artifact, artifact, artifact, H, H, H, H, H, H, H, H,
        H if candidate.startswith('A') else None, H if graph else None,
        H if graph else None, 'disabled' if not graph else
        ('learned' if candidate.endswith('_LEARNED') else 'expert'),
        'FIXTURE_ONLY', 1, 0 if reason else 1, ((reason, 1),) if reason else (), False, False)


def rows(candidate='A0', reason=None):
    base = dict(learner_id='learner', item_id='item,quoted', timestamp='100', source_row='1',
        global_rank='0', history_hash_scheme=admission.HISTORY_SCHEME, history_sha256=H,
        origin_role='selection', phase_scope='raw_selection10', phase_sha256=H,
        encoding_sha256=H, correct='1', probability='' if reason else '0.12345678901234568',
        support_reason=reason or 'supported', input_support_reason=reason or 'cold_query_only',
        window_id='' if reason else H, history_available='' if reason else '0',
        history_used='' if reason else '0', context_reset='' if reason else 'False')
    return tuple({name: base[name] for name in csv_fields(candidate, kind)}
                 for kind in ('predictions', 'targets'))


class SelectedRowTests(unittest.TestCase):
    def test_json_roundtrip_all_nine_claims(self):
        for candidate in admission.REQUIRED_CANDIDATE_IDS:
            original = claim(candidate)
            self.assertEqual(decode_selected_claim(json.loads(json.dumps(asdict(original)))), original)

    def test_reject_unknown_fields_and_nested_object_types(self):
        document = json.loads(json.dumps(asdict(claim())))
        for altered in (dict(document, authority=True), dict(document, context=[]),
                        dict(document, checkpoint={'sha256': H, 'size_bytes': 100, 'path': 'x'}),
                        dict(document, unsupported_counts=[['oov_item', True]])):
            with self.subTest(altered=altered), self.assertRaises(ValueError):
                decode_selected_claim(altered)

    def test_supported_rows_all_producers_preserve_binary64(self):
        for candidate in admission.REQUIRED_CANDIDATE_IDS:
            prediction, target = rows(candidate)
            result = normalize_selected_row(prediction, target, claim(candidate))
            self.assertEqual(result.probability, float(prediction['probability']))
            self.assertEqual(result.key.item_id, 'item,quoted')
            self.assertEqual(result.correct, 1)

    def test_actual_unsupported_schemas(self):
        for candidate, reasons in (('A0', ('oov_item',)), ('SAKT', ('oov_item', 'cold_unsupported')),
                                   ('GKT', ('oov_item', 'unsupported_history'))):
            for reason in reasons:
                prediction, target = rows(candidate, reason)
                result = normalize_selected_row(prediction, target, claim(candidate, reason))
                self.assertIsNone(result.probability)
                self.assertEqual(result.support_reason, reason)

    def test_reject_key_label_phase_and_column_mismatches(self):
        prediction, target = rows()
        changes = ({'item_id': 'other'}, {'timestamp': '0100'}, {'global_rank': '-1'},
                   {'source_row': str(2**63)}, {'correct': 'True'}, {'phase_scope': 'calibration'},
                   {'encoding_sha256': 'b' * 64}, {'extra': 'value'})
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                normalize_selected_row(prediction, dict(target, **change), claim())

    def test_reject_nonfinite_imputed_and_mismatched_support(self):
        prediction, target = rows()
        for text in ('nan', 'inf', '-0.1', '1.1', ' 0.5', '0.5 ', 'None', ''):
            with self.subTest(text=text), self.assertRaises(ValueError):
                normalize_selected_row(dict(prediction, probability=text), target, claim())
        with self.assertRaises(ValueError):
            normalize_selected_row(dict(prediction, support_reason='oov_item'), target, claim())
        for candidate in ('SAKT', 'GKT'):
            prediction, target = rows(candidate, 'oov_item')
            with self.assertRaises(ValueError):
                normalize_selected_row(dict(prediction, probability='0.5'), target, claim(candidate, 'oov_item'))

    def test_reject_geometry_and_input_reason_mismatches(self):
        prediction, target = rows()
        for change in ({'window_id': 'window'}, {'history_used': '1'}, {'context_reset': '0'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                normalize_selected_row(dict(prediction, **change), target, claim())
        prediction, target = rows('A0', 'oov_item')
        with self.assertRaises(ValueError):
            normalize_selected_row(dict(prediction, window_id=H), target, claim('A0', 'oov_item'))
        for candidate in ('SAKT', 'GKT'):
            prediction, target = rows(candidate)
            with self.assertRaises(ValueError):
                normalize_selected_row(dict(prediction, input_support_reason='invented'), target, claim(candidate))

    def test_reject_non_string_rows_and_non_selected_claim(self):
        prediction, target = rows()
        with self.assertRaises(ValueError):
            normalize_selected_row(dict(prediction, probability=0.5), target, claim())
        with self.assertRaises(ValueError):
            normalize_selected_row(prediction, target, asdict(claim()))
        with self.assertRaises(ValueError):
            replace(claim(), prediction_phase='raw_calibration10')


if __name__ == '__main__':
    unittest.main()
