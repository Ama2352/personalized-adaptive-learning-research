"""Cached response-mixture reliability, source-only until ROOT dispatch.

Một y cho một forecast mean3 của mỗi arm. Không đọc oracle, không đánh giá
mastery truth, không thêm dữ liệu hoặc chạy policy. Import chỉ có stdlib.
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
TRACE = ROOT / 'research_tracking/runs/rq1-prediction-mastery-trace-20261109-01'
OLD = ROOT / 'research_tracking/runs/rq1-fixed-edge-set-contrast-20261108-01'
BANK = ROOT / 'paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/data/simulator_inputs/question_bank.csv'
CONTRACT = PREP / 'rq1_reference_mixture_contract01.json'
SEEDS = (20000, 20001, 20002)
PROFILES = ('PG', 'PY', 'PYH')
VARIANTS = ('graph_package', 'empty_graph_package')
TAU = .5637150147511514
MANIFEST_SHA = 'a45099f30ab6d4e239275fae6e40cf174b2dcac615fcb55a6e2b9d79f0c35ae3'
OLD_MANIFEST_SHA = '906d1698482b78708cf16ce9453a8ed866e7dc0ef47cf0b8dca81c2d89b7b044'
OUTER_SHA = '81cf9dd9df724338d6c8d57e01be16b5d2120d27b9730c186b5eb539803e4594'
RUN_SHA = '891a69a3546599782e530d04c3fa29b53fd832f130399404fe159a5fcab2b178'
BANK_SHA = 'fb5924ac0d19049ef1a5be23352592e30dfa3a4bde3e3fa07f10979fe0887e4d'
PROOF_PINS = {
    OLD / 'historical_runner.py': '402dca905694d850f126e41f3b5dcc91b327e986ae2cfbb240dda739eed8dd45',
    OLD / 'source__paper2_reference.py': 'a12edc72a00ad980799ec50ff26f0cb68f2529e3699e8a57e4f11295693c2cd1',
    TRACE / 'prediction_mastery_trace_worker03.py': 'fc067d67ebc9018722aa66367fc186fe4a10e0f0b112475372f8024d4d74d631',
    PREP / 'analyze_rq1_response_reliability01.py': 'baf5e6a73e3fca66d04f9d8199e9c4174565f2a19d82c9ce2e8eeaef955545a0',
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'duplicate JSON key')
            result[key] = value
        return result

    def bad(value):
        raise ValueError('nonfinite JSON ' + value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def exact(left, right):
    if type(left) is not type(right):
        return False
    if type(left) is float:
        return struct.pack('>d', left) == struct.pack('>d', right)
    if type(left) is dict:
        return set(left) == set(right) and all(exact(left[k], right[k]) for k in left)
    if type(left) in (list, tuple):
        return len(left) == len(right) and all(exact(a, b) for a, b in zip(left, right))
    return left == right


def probability(value):
    need(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1,
         'finite probability, bool forbidden')
    return value


def bank_mapping(raw):
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    need(reader.fieldnames == ['question_id', 'concept_id', 'elo_difficulty'], 'fixed bank schema')
    by_concept, all_items = {}, set()
    for row in reader:
        qid, cid = row['question_id'], row['concept_id']
        need(qid and cid and qid not in all_items, 'unique nonempty bank qid')
        difficulty = float(row['elo_difficulty'])
        need(math.isfinite(difficulty), 'finite bank difficulty')
        by_concept.setdefault(cid, {})[qid] = difficulty
        all_items.add(qid)
    need(len(by_concept) == 28 and len(all_items) == 84, 'exact 28 concepts / 84 items')
    need(all(len(items) == 3 and sorted(items.values()) == [1050., 1200., 1350.]
             for items in by_concept.values()), 'uniform logging gives three equal references per concept')
    return by_concept


def unique_index(rows):
    result = {}
    for row in rows:
        key = row['variant'], row['learner_id'], row['event_id']
        need(key not in result, 'duplicate cached key')
        result[key] = row
    return result


def joined_row(row, legacy, side, bank):
    """Kiểm trước projection. Mỗi arm giữ đúng một y cho forecast mean3."""
    need(type(legacy['correct']) is int and legacy['correct'] in (0, 1), 'one binary response')
    need(exact(legacy['correct'], side['correct']), 'sidecar y identity')
    need(side['update_pairing_verified'] is True
         and side['query_capture_phase'] == 'before_delegate_predict'
         and side['preview_is_served'] is False
         and side['preview_capture_phase'] == 'after_native_preview_select', 'C13 pre-update provenance')
    digest = hashlib.sha256(canonical(legacy)).hexdigest()
    need(row['legacy_row_sha256'] == side['legacy_row_sha256'] == digest, 'legacy exact row binding')
    need(exact(row['query'], side['query']) and exact(row['probability'], legacy['probability'])
         and exact(side['probability'], legacy['probability'])
         and exact(row['full_preview'], side['preview']), 'full query / current P / preview exact')
    need(row['phase'] == 'PRE_CURRENT_UPDATE_NO_LABEL_IN_CAPTURE', 'pre-current-label readout phase')
    need(re.fullmatch('[a-f0-9]{64}', row['frozen_state_sha256']) is not None, 'frozen state binding')
    query = row['query']
    need(query['concept'] in bank, 'queried concept in fixed bank')
    expected = bank[query['concept']]
    refs = row['raw_references']
    need(type(refs) is list and len(refs) == 3, 'three references')
    need(len({item['question'] for item in refs}) == 3, 'no repeated reference qid')
    need({item['question']: item['difficulty'] for item in refs} == expected, 'exact same concept references')
    need(query['question'] in expected and query['difficulty'] == expected[query['question']], 'query belongs to references')
    for item in refs:
        probability(item['probability'])
    current = next(item['probability'] for item in refs if item['question'] == query['question'])
    need(exact(current, row['probability']), 'current reference reuses actual cached P')
    score = sum(item['probability'] for item in refs) / 3
    need(exact(score, row['raw_reference_mean']) and type(row['raw_reference_criterion']) is bool
         and row['raw_reference_criterion'] == (score >= TAU), 'frozen mean3 / threshold arithmetic')
    return dict(seed=row['seed'], profile=row['profile'], event_id=row['event_id'], variant=row['variant'],
                query=query, prediction=score, y=legacy['correct'],
                raw_reference_criterion=score >= TAU, current_item_probability=row['probability'])


def group_specs():
    specs = [('pooled', None, None)]
    specs += [('profile', None, profile) for profile in PROFILES]
    specs += [('seed', seed, None) for seed in SEEDS]
    specs += [('trajectory', seed, profile) for seed in SEEDS for profile in PROFILES]
    return specs


def reliability(rows):
    bins = [[] for _ in range(15)]
    strata = [[], []]
    for row in rows:
        p = probability(row['prediction'])
        y = row['y']
        need(type(y) is int and y in (0, 1), 'binary response, bool forbidden')
        bins[min(int(p * 15), 14)].append((p, y))
        strata[int(p >= TAU)].append((p, y))

    def means(values):
        n = len(values)
        mean_p = math.fsum(p for p, y in values) / n if n else None
        mean_y = math.fsum(y for p, y in values) / n if n else None
        return dict(rows=n, mean_prediction=mean_p, mean_correct=mean_y,
                    empirical_signed_gap=mean_p - mean_y if n else None)

    table = [dict(bin_index=i, left=i / 15, right=(i + 1) / 15,
                  right_inclusive=i == 14, **means(values)) for i, values in enumerate(bins)]
    n = len(rows)
    ece = math.fsum(b['rows'] / n * abs(b['empirical_signed_gap']) for b in table if b['rows']) if n else None
    return dict(rows=n, bins=table, ordinary_ece15=ece,
                threshold_strata=[dict(at_or_above_tau=bool(i), threshold=TAU, **means(values))
                                  for i, values in enumerate(strata)])


def summarize(rows, check=lambda: None):
    result = []
    expected = {'pooled': 1080, 'profile': 360, 'seed': 360, 'trajectory': 120}
    for level, seed, profile in group_specs():
        for variant in VARIANTS:
            check()
            subset = [row for row in rows if row['variant'] == variant
                      and (seed is None or row['seed'] == seed)
                      and (profile is None or row['profile'] == profile)]
            need(len(subset) == expected[level], 'complete group population')
            record = dict(level=level, seed=seed, profile=profile, variant=variant, **reliability(subset))
            record['logged_difficulty_counts'] = {str(int(d)): sum(row['query']['difficulty'] == d for row in subset)
                                                  for d in (1050., 1200., 1350.)}
            need(sum(b['rows'] for b in record['bins']) == len(subset)
                 and sum(s['rows'] for s in record['threshold_strata']) == len(subset), 'complete partitions')
            result.append(record)
    need(len(result) == 32 and sum(len(r['bins']) for r in result) == 480, 'all fixed 32 views / 480 bins')
    return result


def main():
    started, wall = time.perf_counter(), time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--contract-sha256', required=True)
    parser.add_argument('--outer-sha256', required=True)
    parser.add_argument('--output-name', required=True)
    args = parser.parse_args()
    need(args.outer_sha256 == OUTER_SHA and all(re.fullmatch('[a-f0-9]{64}', value)
         for value in (args.source_sha256, args.contract_sha256)), 'exact pins before input parsing')
    need(re.fullmatch('reference-mixture-cached-[a-z0-9-]{1,50}', args.output_name), 'exclusive output namespace')
    sys.path.insert(0, str(ROOT / 'scripts/research'))
    from windows_owned_worker import worker_gate
    owner = worker_gate()

    def audit(event, values):
        if event == 'subprocess.Popen' or event.startswith('socket.') or event in ('os.system', 'os.posix_spawn', 'os.spawn'):
            raise RuntimeError('no child/network')
        if event == 'import' and str(values[0]).split('.')[0] in ('torch', 'numpy', 'pandas', 'knowledge_tracing', 'sklearn', 'scipy'):
            raise RuntimeError('stdlib cached only')
        if event == 'open' and values and isinstance(values[0], (str, bytes)):
            name = str(values[0]).replace('\\', '/').lower()
            if any(part in name for part in ('/dataset/', '/oracle/', '/holdout/', '/artifacts/simulator/corpora/')):
                raise RuntimeError('no oracle/corpus/holdout')
    sys.addaudithook(audit)
    need(not any(name in sys.modules for name in ('torch', 'numpy', 'pandas', 'knowledge_tracing')), 'fresh stdlib only')

    def check():
        need(max(time.perf_counter() - started, time.time() - wall) < 7, 'worker seven-second allocation')

    pins, read_bytes = {}, 0

    def read(path, cap=4 * 1024**2, *, charge=True):
        nonlocal read_bytes
        check()
        path = path.absolute()
        need(path.is_relative_to(ROOT) and path.resolve() == path, 'physical workspace path')
        cursor = ROOT
        for part in path.relative_to(ROOT).parts:
            cursor /= part
            need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'no aliases')
        need(path.is_file() and path.stat().st_size <= cap, 'bounded regular input')
        with path.open('rb') as stream:
            raw = stream.read(cap + 1)
        need(len(raw) <= cap and len(raw) == path.stat().st_size, 'stable bounded read')
        if charge:
            read_bytes += len(raw)
            need(read_bytes <= 12 * 1024**2, 'total compressed / metadata input cap')
        check()
        return raw

    def pinned(path, expected, cap=4 * 1024**2):
        need(re.fullmatch('[a-f0-9]{64}', expected), 'valid input digest')
        raw = read(path, cap)
        need(hashlib.sha256(raw).hexdigest() == expected, 'SHA before parsing ' + path.name)
        pins[path.relative_to(ROOT).as_posix()] = expected
        return raw

    def json_input(path, expected, cap=4 * 1024**2):
        return decode(pinned(path, expected, cap))

    pinned(Path(__file__).resolve(), args.source_sha256, 65536)
    contract = json_input(CONTRACT, args.contract_sha256, 65536)
    need(contract['source_sha256'] == args.source_sha256 and contract['native_outer_sha256'] == OUTER_SHA
         and contract['bins'] == 15 and contract['threshold'] == TAU, 'prospective contract')
    pinned(PREP / 'test_rq1_reference_mixture01.py', contract['test_source_sha256'], 65536)
    for path, pin in PROOF_PINS.items():
        pinned(path, pin)
    manifest = json_input(TRACE / 'manifest.json', MANIFEST_SHA)
    old_manifest = json_input(OLD / 'manifest.json', OLD_MANIFEST_SHA)
    need(manifest['status'] == old_manifest['status'] == 'completed', 'closed source bundles')

    def bundled(name, expected=None):
        pin = manifest['outputs_sha256'][name]
        need(expected is None or pin == expected, 'independently frozen native evidence pin')
        return json_input(TRACE / name, pin)

    outer = bundled('native_outer__final.json', OUTER_SHA)
    owned = bundled('native_outer__owned__receipt.json')
    run = bundled('native__worker_run.json', RUN_SHA)
    validation = bundled('validation.json', '13c90b544299362e56bbd7035c83063e12796d46679a4bbab62a6cdd8ca81f02')
    need(outer['status'] == 'ACCEPTED_FIXED_HISTORY_MASTERY_TRACE_ONLY' and outer['errors'] == []
         and outer['worker_run_sha256'] == RUN_SHA and outer['source_before'] == outer['source_after'], 'accepted whole trace')
    need(owned['accepted'] is True and owned['cleanup_accepted'] is True
         and owned['job_active_after_cleanup'] == 0 and owned['popen_handle_closed'] is True
         and owned['actual_worker_in_job_before_GO'] is True, 'genuine owned cleanup')
    need(run['status'] == 'INNER_ALL2160_LEGACY_AND18_FINAL_FINGERPRINTS_EXACT_PENDING_ROOT'
         and run['errors'] == [] and run['legacy_rows_exact'] == 2160 and len(run['completed_trajectories']) == 18
         and run['profiler_restored'] is True and run['teacher_calls'] == 0 and run['optimizer_steps'] == 0
         and run['source_input_before'] == run['source_input_after'] == outer['source_before'], 'complete 2160 / 18 admission')
    need(run['native_attempts'] == run['native_returns']
         and all(run['native_returns'][k] == v for k, v in dict(predict=6480, update=2160, select=2160, ready_set=4320).items()), 'original exact native calls')
    need(validation['all18CRC'] is True and validation['all2160legacy_admission'] is True
         and validation['all_query_label_joins'] is True and validation['no_rows_dropped'] is True
         and validation['outer_sha256'] == OUTER_SHA and validation['worker_run_sha256'] == RUN_SHA,
         'closed validation admission')
    bank = bank_mapping(pinned(BANK, BANK_SHA, 32768))
    decompressed_bytes = 0

    def gzip_rows(raw, count, cap):
        nonlocal decompressed_bytes
        result, size = [], 0
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
            while True:
                check()
                line = stream.readline(65537)
                if not line:
                    break
                size += len(line)
                decompressed_bytes += len(line)
                need(len(line) <= 65536 and line.endswith(b'\n') and size <= cap
                     and decompressed_bytes <= 40 * 1024**2 and len(result) < count, 'bounded complete gzip')
                result.append(decode(line))
        need(len(result) == count, 'all records and terminal gzip CRC')
        return result

    caches = []
    for name, count, cap in (('observed_legacy.jsonl.gz', 3240, 16 * 1024**2),
                             ('observed_query_sidecar.jsonl.gz', 3240, 8 * 1024**2)):
        raw = pinned(OLD / name, old_manifest['outputs_sha256'][name])
        caches.append(unique_index(gzip_rows(raw, count, cap)))
    legacy, side = caches
    all_old_keys = {(v, f'{seed}-{profile}', str(t)) for v in ('graph_free', *VARIANTS)
                    for seed in SEEDS for profile in PROFILES for t in range(120)}
    need(set(legacy) == set(side) == all_old_keys, 'exact old 3240 keys')
    expected = {(seed, profile, str(t)) for seed in SEEDS for profile in PROFILES for t in range(120)}
    projected, native_keys = [], set()
    for ordinal, trajectory in enumerate(run['completed_trajectories'], 1):
        check()
        name = f'trace-{ordinal:02d}.jsonl.gz'
        need(trajectory['trace_file'] == name and trajectory['gzip_closed'] is True
             and trajectory['trace_records'] == trajectory['exact_legacy_rows'] == trajectory['full_preview_exact'] == 120,
             'complete trajectory and endpoint parity')
        receipt = bundled(f'native__trajectory-{ordinal}.json')
        need(exact(receipt, trajectory), 'trajectory receipt equals accepted run')
        need(all(re.fullmatch('[a-f0-9]{64}', trajectory[key]) for key in ('initial_sha256', 'final_sha256')), 'initial / final fingerprints')
        archived = 'native__' + name
        need(manifest['outputs_sha256'][archived] == trajectory['trace_sha256'], 'stream pin binding')
        raw = pinned(TRACE / archived, trajectory['trace_sha256'])
        need(len(raw) == trajectory['trace_bytes'], 'stream size binding')
        local = set()
        for row in gzip_rows(raw, 120, 2 * 1024**2):
            k = row['seed'], row['profile'], row['event_id']
            key = row['variant'], *k
            need(k in expected and row['variant'] in VARIANTS and key not in native_keys, 'unique valid native key')
            need((row['seed'], row['profile'], row['variant']) == (trajectory['seed'], trajectory['profile'], trajectory['variant']), 'stream identity')
            oldkey = row['variant'], f'{k[0]}-{k[1]}', k[2]
            projected.append(joined_row(row, legacy[oldkey], side[oldkey], bank))
            native_keys.add(key)
            local.add(k)
        need(local == {(trajectory['seed'], trajectory['profile'], str(t)) for t in range(120)}, 'all120 per trajectory')
    need(native_keys == {(v, *key) for v in VARIANTS for key in expected}, 'all2160 arm rows, no subset')
    indexed = {(row['variant'], row['seed'], row['profile'], row['event_id']): row for row in projected}
    for k in expected:
        a, b = (indexed[(variant, *k)] for variant in VARIANTS)
        need(exact(a['query'], b['query']) and exact(a['y'], b['y']), 'all1080 shared query and one response')
    groups = summarize(projected, check)
    # Each arm contributes the same historical y once; no pseudo-reference labels.
    summary = dict(kind='CACHED_RAW_REFERENCE_MIXTURE_RESPONSE_RELIABILITY_ONLY',
                   arm_rows=2160, unique_query_responses=1080, trajectories=9, reused_seed_blocks=3,
                   response_uses_per_arm=1080, reference_probabilities_per_arm_row=3,
                   groups=groups, independent_new_N=0,
                   mastery_truth_accuracy_or_calibration_claimed=False,
                   calibrated_V1_or_fitted_calibrator=False, causal_or_learning_benefit_claimed=False)
    output = PREP / args.output_name
    need(not output.exists() and not output.is_symlink(), 'exclusive new output')
    validation_out = dict(all2160arm_rows=True, all1080query_y_pairs=True, all18CRC=True,
                          all18initial_final_admission=True, source_sampling_proof='FROZEN_EXOGENOUS_UNIFORM_ITEM_LOGGER',
                          bank_concepts=28, bank_items=84, references_per_concept=3, groups=32, bins=480,
                          worker_additional_model_teacher_optimizer_calls=0, new_independent_N=0,
                          source_input_before=pins, source_input_after=None, owner=owner)
    for name, pin in pins.items():
        need(hashlib.sha256(read(ROOT / name, charge=False)).hexdigest() == pin, 'input/source postread SHA')
    validation_out['source_input_after'] = dict(pins)
    check()
    payloads = {'summary.json': canonical(summary) + b'\n',
                'joined_rows.jsonl': b''.join(canonical(row) + b'\n' for row in projected),
                'validation.json': canonical(validation_out) + b'\n'}
    need(sum(map(len, payloads.values())) <= 4 * 1024**2, 'bounded total output')
    output.mkdir()
    output_pins = {}
    for name, raw in payloads.items():
        check()
        with (output / name).open('xb') as stream:
            stream.write(raw)
        output_pins[name] = hashlib.sha256(raw).hexdigest()
    check()
    result = dict(status='ACCEPTED_CACHED_REFERENCE_MIXTURE_RESPONSE_DIAGNOSTIC_ONLY',
                  elapsed_before_receipt_seconds=max(time.perf_counter() - started, time.time() - wall),
                  source_input_before=pins, source_input_after=dict(pins), outputs_sha256=output_pins,
                  source_sha256=args.source_sha256, contract_sha256=args.contract_sha256,
                  arm_rows=2160, unique_query_responses=1080, groups=32, bins=480,
                  no_added_native_calls=True, independent_new_N=0)
    with (output / 'result.json').open('xb') as stream:
        stream.write(canonical(result) + b'\n')
    check()  # ROOT must require clean process exit in addition to this pending result.
    print(json.dumps(dict(status=result['status'], output=output.name, arm_rows=2160,
                          unique_query_responses=1080), ensure_ascii=False))


if __name__ == '__main__':
    main()
