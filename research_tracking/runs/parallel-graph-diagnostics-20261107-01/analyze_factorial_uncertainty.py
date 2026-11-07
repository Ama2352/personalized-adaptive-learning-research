"""Tổng hợp exploratory post-hoc từ aggregates, không chạy simulator/model."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import sys
import time


PROFILES = ('PG', 'PY', 'PYH')
FIELDS = ('graph_effect_mechanism_on', 'graph_effect_mechanism_off', 'interaction_contrast')
SEEDS = tuple(range(21000, 21010))
N_DRAWS = 10000
BOOTSTRAP_SEED = 42
TOLERANCE = 1e-12
INPUTS = (
    'research_tracking/runs/cpu-factorial-20261107-01/contrasts.json',
    'research_tracking/runs/cpu-factorial-20261107-01/summary.json',
    'research_tracking/reports/cpu_pilot_followup_20261107.json',
    'research_tracking/reports/rq12_evidence_synthesis_20261107.md',
    'research_tracking/reports/rq12_evidence_synthesis_20261107.json',
    'research_tracking/reports/cpu_pilots_20261107.md',
    'research_tracking/runs/cpu-factorial-20261107-01/README.md',
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mean(values):
    return math.fsum(values) / len(values)


def quantile(values, probability):
    """Quantile tuyến tính tại rank (n-1)*p; không suy là population CI."""
    ordered = sorted(values)
    rank = (len(ordered) - 1) * probability
    left, right = math.floor(rank), math.ceil(rank)
    return ordered[left] + (rank - left) * (ordered[right] - ordered[left])


def interaction(on_high, off_high, on_zero, off_zero):
    return (on_high - off_high) - (on_zero - off_zero)


def analyze(root):
    started = time.monotonic()
    inventory = [{'path': path, 'sha256': sha256(root / path)} for path in INPUTS]
    records = json.loads((root / INPUTS[0]).read_text(encoding='utf-8'))
    summary = json.loads((root / INPUTS[1]).read_text(encoding='utf-8'))
    followup = json.loads((root / INPUTS[2]).read_text(encoding='utf-8'))
    synthesis = json.loads((root / INPUTS[4]).read_text(encoding='utf-8'))
    assert len(records) == 30
    assert set(summary) == set(PROFILES)
    rows = {}
    for record in records:
        assert set(record) == {'seed', 'profile', *FIELDS}
        key = record['seed'], record['profile']
        assert key not in rows and key[0] in SEEDS and key[1] in PROFILES
        assert all(type(record[field]) in (int, float) and math.isfinite(record[field]) for field in FIELDS)
        assert abs(record[FIELDS[0]] - record[FIELDS[1]] - record[FIELDS[2]]) <= TOLERANCE
        rows[key] = record
    assert set(rows) == {(seed, profile) for seed in SEEDS for profile in PROFILES}
    # Synthesis đã đối chiếu hai aggregate này với manifest gốc; kiểm lại hash.
    prior_checks = {item['path']: item for item in synthesis['selected_output_hash_checks']}
    input_checks = []
    for item in inventory[:2]:
        prior = prior_checks[item['path']]
        assert prior['match'] and prior['sha256'] == prior['manifest_expected_sha256'] == item['sha256']
        input_checks.append({'path': item['path'], 'sha256': item['sha256'],
                             'matches_synthesis_manifest_verification': True})

    values = {profile: [rows[seed, profile][FIELDS[2]] for seed in SEEDS] for profile in PROFILES}
    means = {profile: mean(values[profile]) for profile in PROFILES}
    mean_checks = {}
    for profile in PROFILES:
        assert summary[profile]['paired_seeds'] == len(SEEDS)
        error = abs(means[profile] - summary[profile]['mean_interaction'])
        assert error <= TOLERANCE
        mean_checks[profile] = {'source_mean': summary[profile]['mean_interaction'],
                                'recomputed_mean': means[profile], 'absolute_error': error}

    # Một draw indices dùng đồng thời cả3profiles; không tách các cells/components.
    rng = random.Random(BOOTSTRAP_SEED)
    resampled = {profile: [] for profile in PROFILES}
    index_hash = hashlib.sha256()
    for draw in range(N_DRAWS):
        indices = [rng.randrange(len(SEEDS)) for _ in SEEDS]
        index_hash.update(bytes(indices))
        for profile in PROFILES:
            resampled[profile].append(mean([values[profile][i] for i in indices]))
        if draw % 100 == 0:
            assert time.monotonic() - started < 60, 'CPU budget60s exceeded'

    # Arithmetic negative controls riêng; không dùng PG như chứng cứ equivalence.
    controls = {
        'four_cell_known_answer': interaction(8., 5., 7., 6.) == 2.,
        'identity_lambda_interaction_zero': all(interaction(x, y, x, y) == 0.
                                               for x, y in ((2., 1.), (-2., 3.), (0., 0.))),
        'identity_treatment_interaction_zero': all(interaction(x, x, y, y) == 0.
                                                  for x, y in ((2., 1.), (-2., 3.))),
        'constant_zero_resampling_zero': mean([0.] * len(SEEDS)) == 0.
                                           and quantile([0.] * N_DRAWS, .025) == 0.
                                           and quantile([0.] * N_DRAWS, .975) == 0.,
    }
    assert all(controls.values())
    results = {}
    for profile in PROFILES:
        observed = values[profile]
        leave_one_out = [{'omitted_seed': seed,
                          'mean_interaction': mean(observed[:i] + observed[i + 1:])}
                         for i, seed in enumerate(SEEDS)]
        coverage = followup['mechanism_coverage'][profile]
        results[profile] = {
            'paired_seed_blocks': len(SEEDS),
            'mean_graph_effect_mechanism_on': mean([rows[s, profile][FIELDS[0]] for s in SEEDS]),
            'mean_graph_effect_mechanism_off': mean([rows[s, profile][FIELDS[1]] for s in SEEDS]),
            'mean_interaction': means[profile],
            'seed_interaction_min': min(observed), 'seed_interaction_max': max(observed),
            'seed_interaction_sample_sd': math.sqrt(math.fsum((x - means[profile]) ** 2
                                                            for x in observed) / (len(SEEDS) - 1)),
            'positive_seed_count': sum(x > 0 for x in observed),
            'zero_seed_count': sum(x == 0 for x in observed),
            'negative_seed_count': sum(x < 0 for x in observed),
            'leave_one_seed_out': leave_one_out,
            'leave_one_seed_out_mean_min': min(item['mean_interaction'] for item in leave_one_out),
            'leave_one_seed_out_mean_max': max(item['mean_interaction'] for item in leave_one_out),
            'exploratory_empirical_resampling_mean_quantiles': {
                'q025': quantile(resampled[profile], .025),
                'q975': quantile(resampled[profile], .975),
            },
            'mechanism_on_coverage': {**coverage,
                                     'positive_deficit_fraction': coverage['positive_deficit'] / coverage['events']},
            'initial_min_ability_in_pilot': followup['initial_min_ability_in_pilot'][profile],
            'per_seed_paired_aggregate': [rows[seed, profile] for seed in SEEDS],
        }
    assert all(x == 0 for x in values['PG'])
    assert followup['mechanism_coverage']['PG']['positive_deficit'] == 0
    assert time.monotonic() - started < 60
    return {
        'schema_version': 1,
        'evidence_level': 'EXPLORATORY POST-HOC uncertainty; không confirmatory/final efficacy',
        'estimand': '[(edge-on - edge-off)|lambda0.55 - (edge-on - edge-off)|lambda0]',
        'outcome_unit_vi': 'Net mean theta gain, Elo-scale mean trên28concept, horizon120steps.',
        'treatment_vi': 'Parent signal và parent adaptation bật/tắt cùng nhau; local pathway off cả hai.',
        'conditioning_vi': 'G_env/G_controller lịch sử, graph-correlated initial abilities, cùng base/uniforms trong4cells theo hồ sơ nguồn.',
        'inference_unit_vi': 'Seed block21000–21009; giữ đủ3profiles và contrast đã paired4cells bên trong block. Không resample events/cells riêng.',
        'resampling': {
            'draws': N_DRAWS, 'seed': BOOTSTRAP_SEED, 'rng': 'Python random.Random/MT19937; randrange(10)',
            'draw_size_seed_blocks': 10, 'same_draw_for_all_profiles': True,
            'indices_sha256': index_hash.hexdigest(),
            'indices_hash_encoding': 'Nối10000draws, mỗi draw10index0-based dạng bytes; thứ tựSEEDS tăng dần.',
            'quantile_method': 'Linear interpolation at rank(n-1)*p; p=.025,.975.',
            'interpretation_vi': 'Khoảng percentile của mean khi lấy mẫu lại empirical10seed blocks; không formal population95%CI.',
            'assumptions_vi': 'Chỉ có nghĩa suy rộng nếu seed blocks độc lập/exchangeable và đại diện cho simulator seed law cố định; chưa được pilot xác lập.',
        },
        'family_vi': 'Ba mean interaction theo PG/PY/PYH. Khoảng marginal exploratory, không simultaneous coverage/correction; không pvalues/rejections/heterogeneity test.',
        'limits_vi': [
            'Post-hoc sau khi đã nhìn mean; không preregistration hoặc independent final seeds.',
            'N=10blocks: empirical bootstrap không khôi phục tails chưa thấy, calibration/coverage population chưa bảo đảm.',
            'LOO/range là sensitivity mô tả trên cùng10seed, không CI hoặc favorable-seed selection.',
            'PG structural zero và deficit0/2400 là mechanism không exposed trong pilot; không proof of equivalence hay graph neutral.',
            'Không raw graph gain/time-DiD, không causal efficacy trên Junyi/người học thật.',
            'Không mở outcomes/traces: pairing4cell dựa aggregate và hồ sơ đã lưu, không audit lại latent/random identity từng cell.',
        ],
        'validation': {'records': len(records), 'complete_seed_profile_grid': True,
                       'source_interaction_arithmetic_tolerance': TOLERANCE,
                       'summary_mean_checks': mean_checks, 'arithmetic_negative_controls': controls,
                       'aggregate_source_hash_checks': input_checks, 'cpu_budget_seconds': 60},
        'input_inventory': inventory,
        'analysis_source': {'path': Path(__file__).resolve().relative_to(root).as_posix(),
                            'sha256': sha256(Path(__file__))},
        'profiles': results,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    assert sys.prefix != sys.base_prefix and Path(sys.prefix).resolve() == root / '.venv'
    assert not args.output.exists(), 'Không ghi đè output đã có; chọn đường dẫn mới.'
    started = time.monotonic()
    result = analyze(root)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'records': result['validation']['records'],
                      'profiles': list(PROFILES), 'draws': N_DRAWS,
                      'elapsed_seconds': round(time.monotonic() - started, 6),
                      'output_sha256': sha256(args.output)}, ensure_ascii=False))
