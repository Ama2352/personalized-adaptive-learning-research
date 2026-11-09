"""Fixtures thuần dựng tay, không mở cache hoặc dùng policy/world."""
import copy
import math
import unittest
import analyze_observer03_cached_truth01 as api


def fixture(steps=2):
    bank = {'q': dict(concept='c', difficulty=1200.0)}
    history = [dict(seed=21000, profile='PG', graph_on=False, mechanism_on=False, step=t,
        concept='c', question='q', prediction=.5, theta_before=1250.0) for t in range(steps)]
    rows = [dict(native_M=True, pi_task_decayed=.9, pi_task_stored=.55, pi_time_decayed=.05,
        pi_time_stored=.05, prediction=.5, selected=['c', 'q', 1200.0], step=t,
        stored_pi_gate=True, theta_est=1250.0, theta_gate=True, timestamp=api.clock(steps)[t])
        for t in range(steps)]
    observer = dict(live=False, class_attributes_restored=True, cleanup_errors=[], pending_attributes=[])
    on = dict(phase='targeted_on', key=list(api.KEY), events=steps, readouts=rows,
        initial_state_sha256='a'*64, final_state_sha256='b'*64,
        profiler_installed=False, instance_attributes_added=False, observer=observer)
    off = copy.deepcopy(on)
    off['phase'] = 'targeted_off'
    return on, off, history, bank


def native(row, theta, pi):
    row.update(theta_est=theta, pi_task_stored=pi, theta_gate=theta >= 1250.,
        stored_pi_gate=pi <= .55, native_M=theta >= 1250. and pi <= .55)


class Observer03TruthTests(unittest.TestCase):
    def test_inclusive_thresholds_stored_pi_and_binary64_neighbors(self):
        on, off, history, bank = fixture(4)
        native(on['readouts'][1], math.nextafter(1250., -math.inf), .55)
        native(on['readouts'][2], 1250., math.nextafter(.55, math.inf))
        history[3]['theta_before'] = math.nextafter(1250., -math.inf)
        rows = api.joined_rows(on['readouts'], history, bank, steps=4)
        self.assertEqual([r['native_M'] for r in rows], [True, False, False, True])
        self.assertEqual([r['simulator_latent_criterion'] for r in rows], [True, True, True, False])
        self.assertTrue(rows[0]['native_M'])  # Decayed .9 must not replace stored .55.

    def test_all_four_cells_zeros_and_suppression_denominators(self):
        on, off, history, bank = fixture(6)
        configurations = ((1249., .5, 1249.), (1249., .5, 1250.), (1250., .55, 1249.),
                          (1250., .55, 1250.), (1250., .56, 1249.), (1250., .56, 1250.))
        for row, stored, (theta, pi, truth) in zip(on['readouts'], history, configurations):
            native(row, theta, pi)
            stored['theta_before'] = truth
        summary = api.summarize(api.joined_rows(on['readouts'], history, bank, steps=6))
        self.assertEqual(summary['native_M_by_latent'], {'00': 2, '01': 2, '10': 1, '11': 1})
        self.assertEqual(summary['theta_gate_by_latent'], {'00': 1, '01': 1, '10': 2, '11': 2})
        self.assertEqual(summary['uncertainty_suppression_by_latent'], {'latent_false': 1, 'latent_true': 1})
        a, b, h, q = fixture()
        cells = api.summarize(api.joined_rows(a['readouts'], h, q, steps=2))['native_M_by_latent']
        self.assertEqual(cells, {'00': 0, '01': 0, '10': 0, '11': 2})

    def test_missing_duplicate_extra_or_unordered_rows_reject(self):
        for mode in ('missing', 'duplicate', 'extra', 'unordered'):
            with self.subTest(mode=mode):
                on, off, history, bank = fixture()
                if mode == 'missing':
                    history.pop()
                elif mode == 'extra':
                    history.append(copy.deepcopy(history[-1]))
                elif mode == 'duplicate':
                    history[1]['step'] = 0
                else:
                    history.reverse()
                with self.assertRaises(ValueError):
                    api.joined_rows(on['readouts'], history, bank, steps=2)

    def test_wrong_history_key_and_bool_alias_reject(self):
        for field, value in (('seed', 20000), ('profile', 'PY'), ('graph_on', 0), ('mechanism_on', True)):
            on, off, history, bank = fixture()
            history[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                api.joined_rows(on['readouts'], history, bank, steps=2)

    def test_query_bank_prediction_bits_and_clock_reject(self):
        for field in ('concept', 'difficulty', 'prediction', 'timestamp'):
            on, off, history, bank = fixture()
            row = on['readouts'][0]
            if field == 'concept':
                row['selected'][0] = 'other'
            elif field == 'difficulty':
                row['selected'][2] = 1050.
            elif field == 'prediction':
                row['prediction'] = math.nextafter(.5, math.inf)
            else:
                row['timestamp'] = '2026-01-01T00:00:00+00:00'
            with self.subTest(field=field), self.assertRaises(ValueError):
                api.joined_rows(on['readouts'], history, bank, steps=2)
        self.assertEqual(api.clock(29)[28], '2026-01-11T00:00:00+00:00')

    def test_off_on_endpoint_or_scientific_drift_reject(self):
        for mode in ('readout', 'endpoint', 'live', 'key'):
            on, off, history, bank = fixture()
            if mode == 'readout':
                off['readouts'][0]['prediction'] = .4
            elif mode == 'endpoint':
                off['final_state_sha256'] = 'c'*64
            elif mode == 'live':
                on['observer']['live'] = True
            else:
                off['key'][0] = 21001
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                api.phases(on, off, steps=2)
        on, off, history, bank = fixture()
        self.assertIs(api.phases(on, off, steps=2), on['readouts'])

    def test_nonfinite_bool_and_wrong_native_predicate_reject(self):
        for field, value in (('theta_est', math.nan), ('pi_task_stored', True), ('native_M', False),
                             ('theta_gate', 1), ('pi_task_decayed', 1.1)):
            on, off, history, bank = fixture()
            on['readouts'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                api.joined_rows(on['readouts'], history, bank, steps=2)
        on, off, history, bank = fixture()
        history[0]['theta_before'] = math.inf
        with self.assertRaises(ValueError):
            api.joined_rows(on['readouts'], history, bank, steps=2)

    def test_duplicate_json_nonfinite_tokens_and_exact_float_identity(self):
        for raw in (b'{"a":1,"a":2}', b'{"x":NaN}', b'{"x":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                api.decode(raw)
        self.assertFalse(api.exact(False, 0))
        self.assertFalse(api.exact(.0, -.0))
        self.assertFalse(api.exact(.5, math.nextafter(.5, math.inf)))
        self.assertTrue(api.exact(api.KEY, api.KEY))
