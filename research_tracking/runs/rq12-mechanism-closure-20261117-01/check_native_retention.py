"""Kiểm hàm quên Paper2 đã đóng nguồn, không chạy notebook/simulator."""
import ast
import copy
import csv
from datetime import datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = HERE / 'ACCEPTANCE.json'
    if output.exists():
        raise FileExistsError('Bundle đã có kết quả, không ghi đè.')
    excerpts_path = ROOT / 'research_tracking/runs/rq2-retention-readout-separation-20261108-01/source_excerpts.json'
    cached_path = excerpts_path.with_name('readouts.json')
    excerpts = json.loads(excerpts_path.read_text(encoding='utf-8'))
    notebook = ROOT / excerpts['notebook']
    if sha(notebook) != excerpts['notebook_sha256']:
        raise ValueError('Notebook frozen SHA thay đổi.')
    document = json.loads(notebook.read_text(encoding='utf-8'))
    namespace = {'math': math, 'pd': SimpleNamespace(Timestamp=datetime)}
    method_pins = {}
    for name in ('theta_at', 'elo_probability'):
        anchor = excerpts['methods'][name]
        cell = ''.join(document['cells'][anchor['cell']]['source'])
        matches = [node for node in ast.walk(ast.parse(cell))
                   if isinstance(node, ast.FunctionDef) and node.name == name]
        assert len(matches) == 1
        actual = matches[0]
        reference = ast.parse(anchor['source']).body[0]
        assert ast.dump(actual, include_attributes=False) == ast.dump(reference, include_attributes=False)
        module = ast.Module(body=[copy.deepcopy(actual)], type_ignores=[])
        exec(compile(ast.fix_missing_locations(module), str(notebook), 'exec'), namespace)
        method_pins[name] = anchor['sha256']
    namespace['TRUE_FORGET_RATE'] = 0.06
    native = namespace['theta_at']
    probability = namespace['elo_probability']
    endpoint = datetime(2026, 1, 31)
    factor = math.exp(-0.06 * 14)
    rows = []
    # last_seen khác nhau và concept chưa luyện, đều giữ invariant native.
    state = SimpleNamespace(
        base={'c0': 850., 'c1': 1000., 'c2': 1200., 'c3': 1100.},
        theta={'c0': 1300., 'c1': 1150., 'c2': 1450., 'c3': 1100.},
        last_seen={'c0': endpoint, 'c1': endpoint - timedelta(days=1),
                   'c2': endpoint - timedelta(days=19), 'c3': None})
    for concept in state.base:
        theta_t = native(state, concept, endpoint)
        theta_14 = native(state, concept, endpoint + timedelta(days=14))
        expected = state.base[concept] + factor * (theta_t - state.base[concept])
        rows.append({'case': 'different_last_seen', 'concept': concept,
                     'theta_T': theta_t, 'theta_D14_native': theta_14,
                     'theta_D14_from_snapshot': expected,
                     'absolute_residual': abs(theta_14 - expected)})
    cached = json.loads(cached_path.read_text(encoding='utf-8'))
    cached_rows = []
    for label in ('A', 'B'):
        base = dict(enumerate(cached['base']))
        gain = cached['states'][label]['gain_vector']
        toy = SimpleNamespace(base=base,
                              theta={c: base[c] + gain[c] for c in base},
                              last_seen={c: endpoint for c in base})
        final = [native(toy, c, endpoint) for c in base]
        retained = [native(toy, c, endpoint + timedelta(days=14)) for c in base]
        for day, snapshot in ((0, final), (14, retained)):
            linear = math.fsum(snapshot[c] - base[c] for c in base) / 28
            soft = math.fsum(probability(snapshot[c], 1250.) - probability(base[c], 1250.) for c in base) / 28
            cached_rows.append({'state': label, 'days_after_T': day,
                                'net_mean_theta_gain': linear, 'native_soft_gain': soft})
    values = {(r['state'], r['days_after_T']): r for r in cached_rows}
    assert values['B', 0]['native_soft_gain'] > values['A', 0]['native_soft_gain']
    assert values['A', 14]['native_soft_gain'] > values['B', 14]['native_soft_gain']
    residual = max(r['absolute_residual'] for r in rows)
    assert residual < 1e-10
    for label in ('A', 'B'):
        assert abs(values[label, 14]['net_mean_theta_gain'] - factor * values[label, 0]['net_mean_theta_gain']) < 1e-10
    for filename, records in [('native_semigroup.csv', rows), ('cached_readout_native.csv', cached_rows)]:
        with (HERE / filename).open('x', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
    assert sha(notebook) == excerpts['notebook_sha256']
    result = {'status': 'ACCEPTED_CONDITIONAL_RETENTION_READOUT_MECHANISM',
              'native_theta_calls': 120, 'native_response_curve_calls': 224,
              'simulator_trajectory_calls': 0, 'new_research_samples': 0,
              'homogeneous_decay_factor_14d': factor,
              'maximum_semigroup_residual': residual,
              'cached_soft_rank_reversal_confirmed_native': True,
              'source_before_after_sha256': sha(notebook), 'native_method_pins': method_pins,
              'inputs': [{'path': str(p.relative_to(ROOT)), 'sha256': sha(p)}
                         for p in (notebook, excerpts_path, cached_path)]}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
