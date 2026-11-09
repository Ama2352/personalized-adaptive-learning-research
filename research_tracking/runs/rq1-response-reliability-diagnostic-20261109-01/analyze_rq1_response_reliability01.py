"""Response reliability thứ cấp từ CPU09 cache, oracle chỉ ở evaluator."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import types

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
CONTRACT = PREP / 'rq1_response_reliability_contract01.json'
CACHE_PARSER = PREP / 'analyze_rq2_cached_mechanism01.py'
CACHE_CONTRACT = PREP / 'rq2_cache_mechanism_contract01.json'
CACHE_PARSER_SHA = '8590381c85fe1e58df4a305c8bf4a33ebd9900d0fa8ffb1f1a93868fb56f1311'
CACHE_CONTRACT_SHA = '23c182f6f03d4f31e694920bd11b6cd697cc1a66a16b5b31d4c46150c9e24fa4'
ACCEPTED_CACHE = PREP / 'rq2-cached-mechanism-native02-outer/final.json'
ACCEPTED_CACHE_SHA = 'ad5170d4cd312b126b78f4fc96b01a4f1809962a7cee820010e2ab86a44d757c'


def need(condition, message):
    if not condition:
        raise ValueError(message)


def response_bins(rows):
    """Bảng15bins theo reporting source, các means của bin rỗng là None."""
    bins = [[] for _ in range(15)]
    for row in rows:
        need(type(row) is dict and set(row) == {'prediction', 'y', 'p_true'}, 'response row schema')
        p, y, oracle = row['prediction'], row['y'], row['p_true']
        need(type(p) in (int, float) and math.isfinite(p) and 0 <= p <= 1, 'valid prediction')
        need(type(oracle) in (int, float) and math.isfinite(oracle) and 0 <= oracle <= 1, 'valid oracle response probability')
        need(type(y) is int and y in (0, 1), 'binary observed answer')
        bins[min(int(p * 15), 14)].append((p, y, oracle))
    count = sum(len(values) for values in bins)
    table = []
    for index, values in enumerate(bins):
        n = len(values)
        mean_p = math.fsum(v[0] for v in values) / n if n else None
        mean_y = math.fsum(v[1] for v in values) / n if n else None
        mean_oracle = math.fsum(v[2] for v in values) / n if n else None
        empirical = mean_p - mean_y if n else None
        oracle_gap = mean_p - mean_oracle if n else None
        residual = mean_oracle - mean_y if n else None
        if n:
            need(abs(empirical - (oracle_gap + residual)) <= 1e-12, 'signed bin decomposition')
        table.append(dict(bin_index=index, left=index / 15, right=(index + 1) / 15,
                          right_inclusive=index == 14, rows=n, mean_prediction=mean_p,
                          mean_correct=mean_y, mean_oracle_probability=mean_oracle,
                          empirical_signed_gap=empirical, oracle_signed_gap=oracle_gap,
                          realized_response_residual=residual))
    empirical_ece = math.fsum(r['rows'] / count * abs(r['empirical_signed_gap'])
                             for r in table if r['rows']) if count else None
    oracle_ece = math.fsum(r['rows'] / count * abs(r['oracle_signed_gap'])
                          for r in table if r['rows']) if count else None
    return dict(rows=count, bins=table, ordinary_ece15=empirical_ece,
                oracle_response_ece15=oracle_ece,
                scalar_ece_decomposition_claimed=False)


def grouped_reliability(buckets, *, seeds, profiles, guard=lambda: None):
    """Giữ120world/12persona-arm/4arm khi gọi trên canonical CPU09 grid."""
    expected = {(s, p, g, m) for s in seeds for p in profiles
                for g in (False, True) for m in (False, True)}
    need(set(buckets) == expected, 'complete source bucket grid')
    result = []

    def append(level, seed, profile, g, m, keys):
        guard()
        projected = (dict(prediction=row['prediction'], y=row['y'], p_true=row['p_true'])
                     for key in keys for row in buckets[key])
        result.append(dict(level=level, seed=seed, profile=profile, graph_on=g,
                           mechanism_on=m, **response_bins(projected)))
        guard()

    for seed in seeds:
        for profile in profiles:
            for g in (False, True):
                for m in (False, True):
                    append('world', seed, profile, g, m, [(seed, profile, g, m)])
    for profile in profiles:
        for g in (False, True):
            for m in (False, True):
                append('persona_arm', None, profile, g, m, [(s, profile, g, m) for s in seeds])
    for g in (False, True):
        for m in (False, True):
            append('arm', None, None, g, m, [(s, p, g, m) for s in seeds for p in profiles])
    return result


def main():
    started, wall = time.perf_counter(), time.time()
    # Handshake thật diễn ra trước argparse/formatter, chỉ một lần.
    sys.path.insert(0, str(ROOT / 'scripts/research'))
    from windows_owned_worker import worker_gate
    owner = worker_gate()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--contract-sha256', required=True)
    parser.add_argument('--output-name', required=True)
    args = parser.parse_args()
    need(Path.cwd().resolve() == ROOT and Path(sys.prefix).resolve() == ROOT / '.venv', 'fixed repository/venv')

    def digest(path):
        need(path.is_file() and not path.is_symlink() and path.stat().st_size <= 65536, 'small source/contract')
        return hashlib.sha256(path.read_bytes()).hexdigest()

    need(digest(Path(__file__)) == args.source_sha256 and digest(CONTRACT) == args.contract_sha256,
         'external source/contract bytes')
    need(digest(CACHE_PARSER) == CACHE_PARSER_SHA and digest(CACHE_CONTRACT) == CACHE_CONTRACT_SHA,
         'frozen parser/cache contract')
    module = types.ModuleType('rq2_reviewed_cache_validation')
    module.__file__ = str(CACHE_PARSER)
    exec(compile(CACHE_PARSER.read_bytes(), str(CACHE_PARSER), 'exec'), module.__dict__)
    contract = module.decode(CONTRACT.read_bytes())
    base = module.decode(CACHE_CONTRACT.read_bytes())
    need(contract['analysis_source_sha256'] == args.source_sha256
         and contract['cache_parser_sha256'] == CACHE_PARSER_SHA
         and contract['cache_contract_sha256'] == CACHE_CONTRACT_SHA, 'new/accepted code binding')
    need(args.output_name == contract['output_name'] and Path(args.output_name).name == args.output_name
         and args.output_name not in ('.', '..'), 'exclusive planned output')
    limits = contract['limits']

    def elapsed():
        return max(time.perf_counter() - started, time.time() - wall)

    def guard():
        need(math.isfinite(elapsed()) and elapsed() <= limits['worker_seconds'], 'worker whole elapsed')

    def write(path, value):
        raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
        need(len(raw) <= limits['output_file_bytes'], 'small output cap')
        with path.open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())

    need(module.sha(ACCEPTED_CACHE, 1024**2)[0] == ACCEPTED_CACHE_SHA, 'actual accepted cache receipt')
    accepted = module.decode(ACCEPTED_CACHE.read_bytes())
    need(accepted['status'] == 'ACCEPTED_CACHED_RQ2_SECONDARY_ANALYSIS' and accepted['errors'] == []
         and accepted['inputs_before'] == accepted['inputs_after'] == {n: r['sha256'] for n, r in base['inputs'].items()},
         'source/grid accepted cache provenance')
    before = {}
    sources = {Path(__file__).relative_to(ROOT).as_posix(): args.source_sha256,
               CACHE_PARSER.relative_to(ROOT).as_posix(): CACHE_PARSER_SHA,
               CACHE_CONTRACT.relative_to(ROOT).as_posix(): CACHE_CONTRACT_SHA,
               CONTRACT.relative_to(ROOT).as_posix(): args.contract_sha256,
               **contract['reporting_source_pins']}
    for name, pin in sources.items():
        need(module.sha(ROOT / name, 1024**2)[0] == pin, 'analysis/reporting source bytes')
    for name, value in base['inputs'].items():
        actual, size = module.sha(ROOT / name, value['bytes'])
        need(actual == value['sha256'] and size == value['bytes'], 'source input bytes')
        before[name] = actual
        guard()
    out = PREP / args.output_name
    out.mkdir(exist_ok=False)
    write(out / 'reservation.json', dict(scope=contract['scope'], owner=owner,
          source_sha256=args.source_sha256, contract_sha256=args.contract_sha256,
          source_before=sources, inputs_before=before, model_calls=0, new_world_transitions=0))
    try:
        paths, grid = base['paths'], base['grid']
        module.validate_manifest(module.decode((ROOT / paths['manifest']).read_bytes()), base)
        questions, roots = module.topology({n: (ROOT / paths[n]).read_bytes() for n in ('nodes', 'edges', 'questions')})
        rows = module.trace_rows(ROOT / paths['traces'], max_compressed=limits['compressed_bytes'],
            max_uncompressed=limits['uncompressed_bytes'], max_line=limits['line_bytes'],
            max_rows=limits['trace_rows'], guard=guard)
        buckets = module.validate_trace(rows, seeds=grid['seeds'], profiles=grid['profiles'],
                                        steps=grid['steps'], questions=questions, roots=roots)
        groups = grouped_reliability(buckets, seeds=grid['seeds'], profiles=grid['profiles'], guard=guard)
        expected_counts = {'world': 120, 'persona_arm': 12, 'arm': 4}
        expected_rows = {'world': 120, 'persona_arm': 1200, 'arm': 3600}
        need(len(groups) == 136 and all(sum(g['level'] == level for g in groups) == count
             for level, count in expected_counts.items()), 'all136 declared groups')
        need(all(g['rows'] == expected_rows[g['level']] and len(g['bins']) == 15
             and sum(b['rows'] for b in g['bins']) == g['rows'] for g in groups), 'group/bin population')
        write(out / 'reliability.json', dict(groups=groups, bin_rule=contract['bin_rule'],
              target='ACTUAL_ITEM_NEXT_RESPONSE_CORRECTNESS', oracle_role='POSTHOC_EVALUATOR_ONLY',
              native_mastery_truth_evaluated=False, response_temperature_fitted=False))
        after = {n: module.sha(ROOT / n, base['inputs'][n]['bytes'])[0] for n in before}
        source_after = {n: module.sha(ROOT / n, 1024**2)[0] for n in sources}
        need(after == before and source_after == sources, 'input/source unchanged')
        guard()
        write(out / 'result.json', dict(status='COMPLETE_RESPONSE_RELIABILITY_PENDING_OUTER_ACCEPTANCE',
              elapsed_seconds=elapsed(), source_sha256=args.source_sha256,
              contract_sha256=args.contract_sha256, accepted_cache_receipt_sha256=ACCEPTED_CACHE_SHA,
              inputs_before=before, inputs_after=after, source_before=sources, source_after=source_after,
              worlds=120, trace_rows=14400, groups=136, bins=2040, repeated_group_row_uses=43200,
              seed_clusters_reused=10, new_independent_seed_families=0,
              actual_model_calls=0, new_world_transitions=0, scalar_ece_additivity_claimed=False,
              scope=contract['scope']))
        manifest = {p.name: dict(sha256=module.sha(p, limits['output_file_bytes'])[0], bytes=p.stat().st_size)
                    for p in sorted(out.iterdir()) if p.is_file()}
        guard()
        write(out / 'output-manifest.json', dict(outputs=manifest))
        guard()
        return 0
    except BaseException as error:
        write(out / 'failure.json', dict(error=repr(error), elapsed_seconds=elapsed(), accepted=False))
        raise


if __name__ == '__main__':
    raise SystemExit(main())
