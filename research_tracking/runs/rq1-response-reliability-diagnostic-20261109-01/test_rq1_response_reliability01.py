"""Fixtures arithmetic/edges cho response reliability, không world/model/cache."""

import math
import unittest

import analyze_rq1_response_reliability01 as analysis


def row(p, y, oracle):
    return dict(prediction=p, y=y, p_true=oracle)


class ResponseReliabilityTests(unittest.TestCase):
    def test_zero_one_and_every_exact_bin_edge(self):
        for edge in range(16):
            value = edge / 15
            result = analysis.response_bins([row(value, 0, value)])
            populated = [b for b in result['bins'] if b['rows']]
            with self.subTest(edge=edge):
                self.assertEqual(len(populated), 1)
                self.assertEqual(populated[0]['bin_index'], min(edge, 14))
                self.assertEqual(populated[0]['right_inclusive'], edge >= 14)

    def test_empty_bins_keep_null_means_and_zero_count(self):
        result = analysis.response_bins([row(0., 0, 0.)])
        self.assertEqual(len(result['bins']), 15)
        for b in result['bins'][1:]:
            self.assertEqual(b['rows'], 0)
            for name in ('mean_prediction', 'mean_correct', 'mean_oracle_probability',
                         'empirical_signed_gap', 'oracle_signed_gap', 'realized_response_residual'):
                self.assertIsNone(b[name])
        self.assertEqual((result['ordinary_ece15'], result['oracle_response_ece15']), (0., 0.))

    def test_oracle_equal_prediction_does_not_force_finite_y_gap_zero(self):
        result = analysis.response_bins([row(.5, 0, .5)])
        b = result['bins'][7]
        self.assertEqual((b['empirical_signed_gap'], b['oracle_signed_gap'],
                          b['realized_response_residual']), (.5, 0., .5))
        self.assertEqual((result['ordinary_ece15'], result['oracle_response_ece15']), (.5, 0.))

    def test_signed_identity_does_not_make_absolute_ece_additive(self):
        result = analysis.response_bins([row(.5, 0, .75)])
        b = result['bins'][7]
        self.assertEqual(b['empirical_signed_gap'], b['oracle_signed_gap'] + b['realized_response_residual'])
        self.assertEqual((result['ordinary_ece15'], result['oracle_response_ece15']), (.5, .25))
        self.assertNotEqual(result['ordinary_ece15'], result['oracle_response_ece15'] + abs(b['realized_response_residual']))
        self.assertIs(result['scalar_ece_decomposition_claimed'], False)

    def test_malformed_probability_answer_oracle_and_schema_reject(self):
        invalid = [row(p, 0, .5) for p in (-.01, 1.01, math.nan, math.inf, True)]
        invalid += [row(.5, y, .5) for y in (-1, 2, True, 1.)]
        invalid += [row(.5, 0, o) for o in (-.1, 1.1, math.nan, False)]
        invalid += [dict(prediction=.5, y=0), dict(prediction=.5, y=0, p_true=.5, mastery=True)]
        for value in invalid:
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):
                analysis.response_bins([value])

    def test_empty_group_has_undefined_ece(self):
        result = analysis.response_bins([])
        self.assertEqual((result['rows'], len(result['bins'])), (0, 15))
        self.assertIsNone(result['ordinary_ece15'])
        self.assertIsNone(result['oracle_response_ece15'])

    def test_all_world_persona_arm_groups_preserved(self):
        seeds, profiles = (1, 2), ('PG', 'PY', 'PYH')
        buckets = {(s, p, g, m): (row(.5, 0, .5), row(.5, 1, .5))
                   for s in seeds for p in profiles for g in (False, True) for m in (False, True)}
        groups = analysis.grouped_reliability(buckets, seeds=seeds, profiles=profiles)
        self.assertEqual(len(groups), 40)
        self.assertEqual([g['rows'] for g in groups if g['level'] == 'world'], [2] * 24)
        self.assertEqual([g['rows'] for g in groups if g['level'] == 'persona_arm'], [4] * 12)
        self.assertEqual([g['rows'] for g in groups if g['level'] == 'arm'], [12] * 4)
        self.assertTrue(all(g['ordinary_ece15'] == g['oracle_response_ece15'] == 0 for g in groups))
        buckets.pop(next(iter(buckets)))
        with self.assertRaises(ValueError):
            analysis.grouped_reliability(buckets, seeds=seeds, profiles=profiles)


if __name__ == '__main__':
    unittest.main()
