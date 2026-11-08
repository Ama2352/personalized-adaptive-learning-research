"""Descriptive source-path counts only; no model, paired loss, CI or causal inference."""
import argparse
from collections import Counter
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import time

VARIANTS = ('graph_free', 'graph_package', 'empty_graph_package')
PHASES = ['before_selection', 'after_selection_bookkeeping', 'before_predict', 'after_predict',
          'before_environment_interact', 'after_environment_interact', 'legacy_written', 'before_update', 'after_update']
HASH = re.compile(r'^[0-9a-f]{64}$')
PREP = Path(__file__).resolve().parent
ROOT = PREP.parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tuple_key(row):
    item = row['served_tuple']
    return (item['concept'], item['question'], struct.pack('>d', item['difficulty']))


def timestamp_key(row):
    return row['query']['timestamp_iso'], row['query']['timestamp_ns']


def selected_mastered_set(row):
    return {key for key, value in row['mastered_decisions'].items() if value}


def summarize(rows, *, seeds, profiles, steps, node_count, native_ledger=None, check=lambda: None):
    if (not 1 <= len(seeds) <= 3 or not 1 <= len(profiles) <= 3 or not 1 <= steps <= 120
            or not 1 <= node_count <= 28 or len(set(seeds)) != len(seeds) or len(set(profiles)) != len(profiles)):
        raise ValueError('bounded predefined population required')
    expected = {(seed, profile, variant, step) for seed in seeds for profile in profiles
                for variant in VARIANTS for step in range(steps)}
    indexed, node_ids = {}, None
    summed_mastery_calls = summed_score_calls = 0
    for row in rows:
        check()
        key = (row['seed'], row['profile'], row['variant'], row['step'])
        if key not in expected or key in indexed:
            raise ValueError('unexpected/duplicate trajectory event')
        mastered = row['mastered_decisions']
        if len(mastered) != node_count or any(type(v) is not bool for v in mastered.values()):
            raise ValueError('explicit complete M decisions required')
        if node_ids is None:
            node_ids = set(mastered)
        if set(mastered) != node_ids:
            raise ValueError('node identity drift')
        for name in ('ready_set', 'eligible_candidates', 'balanced_candidates'):
            value = row[name]
            if type(value) is not list or not value or len(value) != len(set(value)) or not set(value) <= node_ids:
                raise ValueError('invalid source set/list ' + name)
        r, c, b = row['ready_set'], row['eligible_candidates'], row['balanced_candidates']
        if not set(b) <= set(c) or row['served_tuple']['concept'] not in b:
            raise ValueError('selected not in B subset C')
        if row['phases'] != PHASES or row['select_timestamp_argument'] is not None:
            raise ValueError('phase/time-argument drift')
        if row['is_served_in_simulator'] is not True or row['full_mastery_score_vector_available'] is not False:
            raise ValueError('preview/full-S semantic drift')
        if row['mastery_ready_capture_phase'] != 'during_selection_before_bookkeeping':
            raise ValueError('M/R phase drift')
        if row['prediction_capture_phase'] != 'after_selection_bookkeeping_before_environment_interact':
            raise ValueError('P phase drift')
        for name in ('state_before_selection_sha256', 'state_after_selection_sha256', 'state_after_update_sha256',
                     'legacy_row_sha256', 'outcome_sha256'):
            if not isinstance(row[name], str) or not HASH.fullmatch(row[name]):
                raise ValueError('state/legacy binding missing')
        item, query = row['served_tuple'], row['query']
        if (type(item['difficulty']) is not float or not math.isfinite(item['difficulty'])
                or not isinstance(item['concept'], str) or not isinstance(item['question'], str)
                or any(query[k] != item[k] for k in ('concept', 'question', 'difficulty'))
                or type(query['timestamp_ns']) is not int or not isinstance(query['timestamp_iso'], str)):
            raise ValueError('actual query/served tuple identity drift')
        if type(row['correct']) is not int or row['correct'] not in (0, 1):
            raise ValueError('observed binary label required')
        if type(row['prediction']) is not float or not math.isfinite(row['prediction']):
            raise ValueError('prediction identity invalid; no predictive metric computed')
        for call in row['mastery_calls']:
            if call['concept'] not in mastered or type(call['mastered']) is not bool or mastered[call['concept']] != call['mastered']:
                raise ValueError('captured native mastery return mismatch')
        summed_mastery_calls += len(row['mastery_calls'])
        summed_score_calls += len(row['mastery_score_calls'])
        indexed[key] = row
    if set(indexed) != expected:
        raise ValueError('incomplete predefined population')
    if native_ledger is not None:
        for name in ('select', 'ready_set', 'predict', 'interact', 'update'):
            if native_ledger[name] != len(rows):
                raise ValueError('native call ledger mismatch: ' + name)
        # The pinned native update calls is_mastered once, in addition to selection calls.
        if native_ledger['is_mastered'] != summed_mastery_calls + len(rows):
            raise ValueError('native mastery call ledger mismatch')
        if native_ledger['mastery_score'] != summed_score_calls:
            raise ValueError('native score call ledger mismatch')
    groups, event_flags = [], []
    metric_names = ('R_to_C_setdiff', 'R_to_C_order_onlydiff', 'C_to_B_setdiff',
                    'selected_outside_R', 'selected_M_true', 'selection_state_hash_changed')
    for seed in seeds:
        for profile in profiles:
            for variant in VARIANTS:
                counts = Counter({k: 0 for k in metric_names})
                hist = {k: Counter() for k in ('R', 'C', 'B')}
                for step in range(steps):
                    row = indexed[(seed, profile, variant, step)]
                    r, c, b = row['ready_set'], row['eligible_candidates'], row['balanced_candidates']
                    flags = {'R_to_C_setdiff': set(r) != set(c),
                             'R_to_C_order_onlydiff': set(r) == set(c) and r != c,
                             'C_to_B_setdiff': set(c) != set(b),
                             'selected_outside_R': row['served_tuple']['concept'] not in r,
                             'selected_M_true': row['mastered_decisions'][row['served_tuple']['concept']],
                             'selection_state_hash_changed': row['state_before_selection_sha256'] != row['state_after_selection_sha256']}
                    for key, value in flags.items():
                        counts[key] += int(value)
                    for key, value in [('R', r), ('C', c), ('B', b)]:
                        hist[key][len(value)] += 1
                    event_flags.append({'seed': seed, 'profile': profile, 'variant': variant, 'step': step,
                        **{k: int(v) for k, v in flags.items()}, 'R_size': len(r), 'C_size': len(c), 'B_size': len(b)})
                groups.append({'seed': seed, 'profile': profile, 'variant': variant, 'events': steps,
                               **dict(counts), 'size_histograms': {k: {str(n): v for n, v in sorted(h.items())} for k, h in hist.items()}})
    prefix_groups, prefix_flags = [], []
    for seed in seeds:
        for profile in profiles:
            for candidate in VARIANTS[1:]:
                common, first_break, first_action_diff = True, None, None
                counts = Counter({k: 0 for k in ('common_before_events', 'common_after_events',
                    'M_setdiff_on_common_before', 'R_setdiff_on_common_before', 'C_setdiff_on_common_before',
                    'B_setdiff_on_common_before', 'served_tuple_diff_on_common_before')})
                for step in range(steps):
                    check()
                    left, right = indexed[(seed, profile, 'graph_free', step)], indexed[(seed, profile, candidate, step)]
                    before = common
                    same_tuple = tuple_key(left) == tuple_key(right)
                    same_time = timestamp_key(left) == timestamp_key(right)
                    same_label = left['correct'] == right['correct']
                    if not same_tuple and first_action_diff is None:
                        first_action_diff = {'step': step, 'different_fields': [k for k in
                            ('concept', 'question', 'difficulty') if (
                                struct.pack('>d', left['served_tuple'][k]) != struct.pack('>d', right['served_tuple'][k])
                                if k == 'difficulty' else left['served_tuple'][k] != right['served_tuple'][k])],
                            'common_before': before}
                    differences = {'M_setdiff': selected_mastered_set(left) != selected_mastered_set(right),
                        'R_setdiff': set(left['ready_set']) != set(right['ready_set']),
                        'C_setdiff': set(left['eligible_candidates']) != set(right['eligible_candidates']),
                        'B_setdiff': set(left['balanced_candidates']) != set(right['balanced_candidates']),
                        'served_tuple_diff': not same_tuple} if before else None
                    if before:
                        counts['common_before_events'] += 1
                        for key, value in differences.items():
                            counts[key + '_on_common_before'] += int(value)
                    current_identical = same_tuple and same_time and same_label
                    if before and not current_identical:
                        reasons = [k for k, same in [('served_tuple', same_tuple), ('timestamp', same_time), ('label', same_label)] if not same]
                        first_break = {'step': step, 'reasons': reasons,
                                       'label_only': same_tuple and same_time and not same_label}
                    common = before and current_identical
                    counts['common_after_events'] += int(common)
                    prefix_flags.append({'seed': seed, 'profile': profile, 'candidate': candidate, 'step': step,
                        'common_before': int(before), 'common_after': int(common),
                        'current_same_served_tuple': int(same_tuple), 'current_same_timestamp': int(same_time),
                        'current_same_label': int(same_label),
                        **{k: int(v) if before else '' for k, v in (differences or {k: None for k in
                            ('M_setdiff', 'R_setdiff', 'C_setdiff', 'B_setdiff', 'served_tuple_diff')}).items()}})
                prefix_groups.append({'seed': seed, 'profile': profile, 'candidate': candidate, 'events': steps,
                    **dict(counts), 'first_prefix_break': first_break, 'first_full_served_tuple_diff': first_action_diff})
    return {'status': 'DESCRIPTIVE_CURRENT_SOURCE_RECONSTRUCTION_NOT_CAUSAL', 'trajectory_count': len(groups),
        'events': len(rows), 'trajectories': groups, 'common_prefix_comparison_count': len(prefix_groups),
        'common_prefix': prefix_groups, 'native_call_ledger_verified': native_ledger,
        'all_selected_in_B_subset_C': True, 'new_independent_N': 0,
        'original_a585_whole_source_recovered': False}, event_flags, prefix_flags


def report_text(result):
    lines = ['# Closed-loop: mô tả đường đi selector từ current-source reconstruction', '',
        '**Bản thảo chẩn đoán, không causal/efficacy hoặc hoàn tất RQ1.** Original whole runner a585 vẫn thiếu; candidate d889 đã giữ exact stored legacy projection trong hai passes, không chứng minh recover original source. Metadata chỉ thuộc reconstruction mới, không backfill lịch sử.', '',
        'M là explicit boolean trước bookkeeping; R là returned ready set, C là eligible candidates sau escape, B là balanced candidates; P được tính sau bookkeeping trước interact/current y. State-hash change trong bảng chỉ là khác biệt bytes state quanh selection, không learning/mastery gain.', '',
        '## Toàn bộ trajectories', '',
        '| Seed | Profile | Variant | Events | R→C set | R→C order only | C→B set | Selected ngoài R | Selected M=true | Hash đổi quanh select |',
        '|---|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for g in result['trajectories']:
        lines.append('| ' + ' | '.join(str(g[k]) for k in ('seed', 'profile', 'variant', 'events',
            'R_to_C_setdiff', 'R_to_C_order_onlydiff', 'C_to_B_setdiff', 'selected_outside_R', 'selected_M_true',
            'selection_state_hash_changed')) + ' |')
    lines += ['', 'R/C/B size histograms đủ từng trajectory nằm trong [analysis.json](analysis.json); không lấy mean sizes che mất phân bố. Mọi selected thuộc B⊆C đã được kiểm trên toàn bộ rows. Selected ngoài raw R có thể là escape; selected M=true có thể là review/fallback của nguồn, không tự chứng minh lỗi hoặc vi phạm prerequisite. Empty chỉ là **empty estimator graph**: loader vẫn bind selector vào controller G chung (paper2_reference.py87–92), môi trường G giữ nguyên. Không suy R khác nhau nghĩa là controller graph bị đổi.', '',
        '## Prefix có cùng toàn bộ lịch sử trước current event', '',
        'Prefix chỉ còn common khi mọi actual served tuple +timestamp+y trước đó đều giống; một lần diverge thì không mở lại. Snapshot gây break vẫn có common-before=true. M/R/C/B so bằng sets, action bằng returned tuple ba trường; current label chỉ xác định prefix sau event. First action difference được lưu riêng trên toàn bộ quỹ đạo, kể cả sau label-only break.', '',
        '| Seed | Profile | Candidate | Common-before | Common-after | M/R/C/B setdiff trên common-before | Tuple diff trên common-before | First break | First tuple diff |',
        '|---|---|---|---:|---:|---|---:|---|---|']
    for g in result['common_prefix']:
        br = g['first_prefix_break']; action = g['first_full_served_tuple_diff']
        reason = 'none' if br is None else str(br['step']) + ':' + ','.join(br['reasons']) + (' (label-only)' if br['label_only'] else '')
        first = 'none' if action is None else str(action['step']) + ':' + ','.join(action['different_fields'])
        vector = '/'.join(str(g[k + '_setdiff_on_common_before']) for k in ('M', 'R', 'C', 'B'))
        lines.append('| ' + ' | '.join(map(str, [g['seed'], g['profile'], g['candidate'], g['common_before_events'],
            g['common_after_events'], vector, g['served_tuple_diff_on_common_before'], reason, first])) + ' |')
    lines += ['', 'Giữ đủ tất cả seed/profile/comparisons, gồm zero/negative controls; không chọn ví dụ thuận lợi. [trajectory_flags.csv](trajectory_flags.csv) và [common_prefix_flags.csv](common_prefix_flags.csv) giữ đủ flags. Sau divergence không ghép ΔP/loss/current-query crossings theo cùng ordinal event hoặc diễn giải thành funnel/mediation. Không CI/p-value, ability effect hoặc causal learning benefit; ba seed families đã dùng, new independent N=0. Full S28/calibration/reference mastery và scientific interventions vẫn thiếu. Counter-path counts không phải probability của prerequisite edge đúng.', '',
        'Phân tích chỉ đọc các artifacts đã freeze; không gọi native model/RNG, thay graph/dynamics/hyperparameters, hoặc chạy thêm seed. Raw reconstruction PASS và các phase timers là engineering evidence; không biến failure120s trước thành PASS.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-inventory', type=Path, required=True)
    parser.add_argument('--source-inventory-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--remaining-seconds', type=float, required=True)
    args = parser.parse_args()
    start = time.perf_counter()
    if not math.isfinite(args.remaining_seconds) or not 0 < args.remaining_seconds <= 30:
        raise ValueError('analysis cap30 includes pure fixtures')
    deadline = start + args.remaining_seconds
    def check():
        if time.perf_counter() > deadline:
            raise TimeoutError('descriptive analysis cumulative30s')
    inventory_path = args.source_inventory.resolve()
    if inventory_path.parent != PREP or sha(inventory_path) != args.source_inventory_sha256:
        raise ValueError('frozen analyzer/plan binding')
    inventory = json.loads(inventory_path.read_text())
    def verify():
        for rel, value in inventory['files_sha256'].items():
            if sha(ROOT / rel) != value:
                raise ValueError('frozen analysis input/source drift: ' + rel)
    verify()
    rawroot = PREP / 'closed-loop-fast-model-attempt01'
    output = args.output.resolve()
    if output.parent != PREP or output.exists():
        raise ValueError('exclusive direct prep output required')
    rows = []
    with gzip.open(rawroot / 'observed_metadata.jsonl.gz', 'rt', encoding='utf-8') as stream:
        for line in stream:
            check()
            if len(line) > 65536 or len(rows) >= 3240:
                raise ValueError('bounded metadata rows/line size')
            rows.append(json.loads(line))
    parity = json.loads((rawroot / 'parity.json').read_text())
    ledger = parity['passes'][1]['observed_native_call_ledger']
    result, flags, prefixes = summarize(rows, seeds=(20000, 20001, 20002), profiles=('PG', 'PY', 'PYH'),
        steps=120, node_count=28, native_ledger=ledger, check=check)
    result['source_inventory_sha256'] = args.source_inventory_sha256
    result['definitions'] = inventory['predefined_definitions']
    result['limits_vi'] = inventory['limits_vi']
    verify();check();output.mkdir(exist_ok=False)
    with (output / 'analysis.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2);stream.write('\n')
    for name, records in [('trajectory_flags.csv', flags), ('common_prefix_flags.csv', prefixes)]:
        with (output / name).open('x', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    with (output / 'report_draft.md').open('x', encoding='utf-8') as stream:
        stream.write(report_text(result))
    verify();check()
    receipt = {'status': 'PASS_STORED_DESCRIPTIVE_ANALYSIS_NO_MODEL', 'elapsed_seconds': time.perf_counter()-start,
        'source_inventory_sha256': args.source_inventory_sha256, 'events': len(rows), 'trajectories': 27,
        'common_prefix_comparisons': 18, 'trajectory_flag_rows': len(flags), 'prefix_flag_rows': len(prefixes),
        'model_rng_optimizer_calls': 0, 'new_independent_N': 0,
        'outputs_sha256': {p.name: sha(p) for p in output.iterdir() if p.is_file()}}
    with (output / 'analysis_receipt.json').open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2);stream.write('\n')


if __name__ == '__main__':
    main()
