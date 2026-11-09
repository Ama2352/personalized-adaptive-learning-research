"""Fixtures tổng hợp cho parser/join, không tạo world hoặc gọi KT model."""

import copy
import gzip
import json
from pathlib import Path
import tempfile
import unittest

import analyze_rq2_cached_mechanism01 as analysis


SEEDS = (1,)
PROFILES = ('PG', 'PY', 'PYH')
QUESTIONS = {'Q0': dict(concept='C0', difficulty=1050.),
             'Q1': dict(concept='C1', difficulty=1200.)}
ROOTS = {'C0'}


def fixture():
    """Known-answer arrays chỉ phục vụ kiểm arithmetic và identity."""
    rows, endpoints, contrasts = [], [], []
    values = {'PG': (2., 2., 3., 3.), 'PY': (2., 3., 1., 1.), 'PYH': (1., 1., 3., 4.)}
    for profile_index, profile in enumerate(PROFILES):
        group = {}
        for g in (False, True):
            for m in (False, True):
                value = values[profile][int(g) * 2 + int(m)]
                group[g, m] = value
                endpoints.append(dict(seed=1, profile=profile, graph_on=g,
                    prerequisite_mechanism_on=m, latent_identity=str(profile_index + 1) * 64,
                    random_stream_identity='a' * 64, outcome=value))
                for step in range(3):
                    concept = 'C0' if profile == 'PG' else 'C1'
                    if profile == 'PY' and g and m and step == 1:
                        concept = 'C0'
                    rows.append(dict(seed=1, profile=profile, graph_on=g, mechanism_on=m,
                        step=step, concept=concept, question='Q0' if concept == 'C0' else 'Q1',
                        prediction=.5, y=int(profile != 'PG' and m and step == 2),
                        p_true=.5, theta_before=1200., learning_gain=1., challenge_match=.5,
                        prereq_violation=int(concept == 'C1'),
                        prerequisite_deficit=.25 if concept == 'C1' else 0., gap_days=0.))
        off, on = group[True, False] - group[False, False], group[True, True] - group[False, True]
        contrasts.append(dict(seed=1, profile=profile, graph_effect_mechanism_on=on,
                              graph_effect_mechanism_off=off, interaction_contrast=on - off))
    summary = {r['profile']: dict(paired_seeds=1, mean_interaction=r['interaction_contrast']) for r in contrasts}
    return rows, endpoints, contrasts, summary


def validate(rows):
    return analysis.validate_trace(rows, seeds=SEEDS, profiles=PROFILES, steps=3,
                                   questions=QUESTIONS, roots=ROOTS)


def run_fixture(parts):
    rows, endpoints, contrasts, summary = parts
    return analysis.analyze(validate(rows), analysis.endpoint_table(endpoints, seeds=SEEDS, profiles=PROFILES),
                            contrasts, summary, seeds=SEEDS, profiles=PROFILES, roots=ROOTS)


class CachedMechanismTests(unittest.TestCase):
    def test_known_answer_preserves_all_signs_zero_and_counts(self):
        result = run_fixture(fixture())
        self.assertEqual([r['interaction_contrast'] for r in result['joined_contrasts']], [0., -1., 1.])
        self.assertEqual((len(result['arm_exposures']), len(result['paired_trajectories'])), (12, 12))
        self.assertEqual([r['profile'] for r in result['joined_contrasts']], list(PROFILES))

    def test_query_and_label_divergence_are_distinct(self):
        result = run_fixture(fixture())
        pair = next(r for r in result['paired_trajectories'] if r['profile'] == 'PY'
                    and r['axis'] == 'mechanism' and r['fixed_other_flag'])
        self.assertEqual((pair['first_query_difference_step'], pair['first_label_difference_step']), (1, 2))
        self.assertEqual((pair['common_query_prefix_steps'], pair['same_query_steps']), (1, 2))
        self.assertEqual(pair['common_observable_prefix_steps'], 1)

    def test_never_query_divergence_retains_label_difference(self):
        result = run_fixture(fixture())
        pair = next(r for r in result['paired_trajectories'] if r['profile'] == 'PYH'
                    and r['axis'] == 'mechanism' and not r['fixed_other_flag'])
        self.assertIsNone(pair['first_query_difference_step'])
        self.assertEqual((pair['common_query_prefix_steps'], pair['first_label_difference_step']), (3, 2))

    def test_pg_negative_does_not_force_policy_gain_zero(self):
        row = run_fixture(fixture())['joined_contrasts'][0]
        self.assertEqual(row['interaction_contrast'], 0.)
        self.assertEqual(row['graph_effect_mechanism_off'], 1.)
        self.assertEqual(row['graph_effect_mechanism_on'], 1.)

    def test_duplicate_and_missing_trace_rows_reject(self):
        rows = fixture()[0]
        for malformed in (rows + [rows[0]], rows[1:]):
            with self.subTest(size=len(malformed)), self.assertRaises(ValueError):
                validate(malformed)

    def test_wrong_query_boolean_numeric_and_root_reject(self):
        changes = ({'question': 'missing'}, {'concept': 'C1'}, {'graph_on': 1},
                   {'y': True}, {'prerequisite_deficit': float('nan')},
                   {'prerequisite_deficit': .2}, {'extra': 1}, {'step': -1})
        for change in changes:
            rows = fixture()[0]
            rows[0].update(change)
            with self.subTest(change=repr(change)), self.assertRaises(ValueError):
                validate(rows)

    def test_four_cell_latent_and_cross_profile_rng_bindings(self):
        for field in ('latent_identity', 'random_stream_identity'):
            endpoints = fixture()[1]
            endpoints[0][field] = 'f' * 64
            with self.subTest(field=field), self.assertRaises(ValueError):
                analysis.endpoint_table(endpoints, seeds=SEEDS, profiles=PROFILES)

    def test_duplicate_endpoint_and_missing_contrast_reject(self):
        parts = fixture()
        parts[1].append(copy.deepcopy(parts[1][0]))
        with self.assertRaises(ValueError):
            run_fixture(parts)
        parts = fixture()
        parts[2].pop()
        with self.assertRaises(ValueError):
            run_fixture(parts)

    def test_stale_endpoint_and_summary_reject(self):
        parts = fixture()
        parts[1][-1]['outcome'] += 1.
        with self.assertRaises(ValueError):
            run_fixture(parts)
        parts = fixture()
        parts[3]['PY']['mean_interaction'] = .5
        with self.assertRaises(ValueError):
            run_fixture(parts)

    def test_pg_semantic_negative_rejects_label_change(self):
        parts = fixture()
        row = next(r for r in parts[0] if r['profile'] == 'PG' and r['mechanism_on'])
        row['y'] = 1
        with self.assertRaises(ValueError):
            run_fixture(parts)

    def test_true_deficit_exposure_counts_roots_without_dropping(self):
        result = run_fixture(fixture())
        arm = next(r for r in result['arm_exposures'] if r['profile'] == 'PY'
                   and r['graph_on'] and r['mechanism_on'])
        self.assertEqual((arm['events'], arm['root_events'], arm['nonroot_events']), (3, 1, 2))
        self.assertEqual(arm['positive_true_deficit_events'], 2)
        self.assertAlmostEqual(arm['mean_true_deficit'], 1. / 6)

    def test_duplicate_key_and_nonfinite_json_reject(self):
        for raw in ('{"x":1,"x":2}', '{"x":NaN}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                analysis.decode(raw)

    def test_gzip_crc_and_explicit_byte_line_row_caps(self):
        payload = b'{"x":1}\n{"x":2}\n'
        encoded = gzip.compress(payload, mtime=0)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'handmade.jsonl.gz'
            path.write_bytes(encoded)
            base = dict(max_compressed=1000, max_uncompressed=100, max_line=20, max_rows=2, guard=lambda: None)
            self.assertEqual(list(analysis.trace_rows(path, **base)), [{'x': 1}, {'x': 2}])
            for field, limit in (('max_compressed', 1), ('max_uncompressed', 3),
                                 ('max_line', 3), ('max_rows', 1)):
                settings = dict(base, **{field: limit})
                with self.subTest(field=field), self.assertRaises(ValueError):
                    list(analysis.trace_rows(path, **settings))
            corrupted = bytearray(encoded)
            corrupted[-8] ^= 1
            path.write_bytes(corrupted)
            with self.assertRaises(gzip.BadGzipFile):
                list(analysis.trace_rows(path, **base))

    def test_pair_first_and_last_step_and_never(self):
        rows = fixture()[0][:3]
        for step in (0, 2, None):
            other = copy.deepcopy(rows)
            if step is not None:
                other[step]['question'] = 'changed'
            pair = analysis.pair_summary(1, 'fixture', 'mechanism', False, rows, other)
            self.assertEqual(pair['first_query_difference_step'], step)
            self.assertEqual(pair['common_query_prefix_steps'], 3 if step is None else step)

    def test_closed_manifest_hash_binding(self):
        roles = ('outcomes', 'contrasts', 'summary', 'provenance', 'traces')
        contract = dict(grid=dict(seeds=[1], profiles=['PG'], steps=3),
                        paths={r: r + '.json' for r in roles},
                        inputs={r + '.json': dict(sha256='a' * 64) for r in roles})
        manifest = dict(kind='approved_cpu_factorial_pilot', status='completed', seeds=[1],
                        profiles=['PG'], steps=3, cells=4,
                        edge_treatment='S=P=on versus S=P=off, L=off in both',
                        outputs_sha256={r + '.json': 'a' * 64 for r in roles})
        analysis.validate_manifest(manifest, contract)
        manifest['outputs_sha256']['traces.json'] = 'b' * 64
        with self.assertRaises(ValueError):
            analysis.validate_manifest(manifest, contract)

    def test_manifest_study_population_and_treatment_reject(self):
        roles = ('outcomes', 'contrasts', 'summary', 'provenance', 'traces')
        contract = dict(grid=dict(seeds=[1], profiles=['PG'], steps=3),
                        paths={r: r + '.json' for r in roles},
                        inputs={r + '.json': dict(sha256='a' * 64) for r in roles})
        base = dict(kind='approved_cpu_factorial_pilot', status='completed', seeds=[1],
                    profiles=['PG'], steps=3, cells=4,
                    edge_treatment='S=P=on versus S=P=off, L=off in both',
                    outputs_sha256={r + '.json': 'a' * 64 for r in roles})
        for change in ({'status': 'failed'}, {'seeds': [2]}, {'profiles': ['A1300']},
                       {'steps': True}, {'edge_treatment': 'full-versus-empty'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                analysis.validate_manifest(dict(base, **change), contract)


if __name__ == '__main__':
    unittest.main()
