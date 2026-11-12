"""Đo strict loader và session đã strict-admit trên cohort thật có giới hạn."""
import argparse
import gc
import json
from pathlib import Path
import statistics
import sys
import time

from benchmark_bounded import ROOT, consume, sha
from knowledge_tracing.akt.research_junyi_engineering import prepare_inputs
from knowledge_tracing.akt.research_junyi_window_cache import JunyiWindowCacheSession, iter_junyi_window_cache


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-stem',default='bounded-reader-session-benchmark')
    args = parser.parse_args()
    if Path(args.output_stem).name != args.output_stem:
        raise ValueError('Local evidence output basename required')
    evidence = Path(__file__).with_name('actual-bounded-result.json')
    original = json.loads(evidence.read_text(encoding='utf-8'))
    assert all(sha(ROOT/name) == expected for name, expected in original['source_pins'].items())
    cohort = ROOT/'artifacts/akt/junyi-cohorts/cuda-engineering320x300-20261112-01'
    roles = ROOT/'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01/roles.json'
    views, encoding, learners, _ = prepare_inputs(cohort, roles,
        cohort_sha256=original['source_pins'][(cohort/'manifest.json').relative_to(ROOT).as_posix()],
        roles_sha256=original['source_pins'][roles.relative_to(ROOT).as_posix()])
    del learners
    cache = original['role_results']['train']
    options = dict(view=views['train'], encoding=encoding, source_data_sha256=cache['source_data_sha256'],
        expected_target_rows=11833, expected_manifest_sha256=cache['receipt']['manifest_sha256'])
    admitted = JunyiWindowCacheSession(ROOT/cache['root'], **options)
    assert admitted.strict_records_verified == 315
    factories = dict(strict=lambda: iter_junyi_window_cache(ROOT/cache['root'], **options),
                     admitted=admitted.iter_windows)
    samples = []
    for iteration, order in enumerate((('strict','admitted'),('admitted','strict'),('strict','admitted')), 1):
        for name in order:
            gc.collect()
            started = time.perf_counter()
            population = consume(factories[name])
            elapsed = time.perf_counter()-started
            sample = dict(iteration=iteration, reader=name, seconds=elapsed,
                          targets_per_second=11833/elapsed, population=population)
            samples.append(sample)
            print(json.dumps(sample), flush=True)
    medians = {name:statistics.median(row['seconds'] for row in samples if row['reader']==name)
               for name in factories}
    admitted.assert_boundary()
    assert 'torch' not in sys.modules
    assert all(sha(ROOT/name) == expected for name, expected in original['source_pins'].items())
    output = dict(status='ACTUAL_BOUNDED_ADMITTED_READER_BENCHMARK_COMPLETE', iterations=3,
        strict_admission_records=admitted.strict_records_verified, strict_admission_seconds=admitted.strict_seconds,
        samples=samples, median_seconds=medians, admitted_over_strict_wall_ratio=medians['admitted']/medians['strict'],
        source_evidence_sha256=sha(evidence), source_pins=original['source_pins'],
        module_sha256=sha(ROOT/'src/knowledge_tracing/akt/research_junyi_window_cache.py'),
        limitations='Local Windows, cohort320,315windows, warm OS cache; chưa đo fullJunyi hoặc GPU pipeline.',
        torch_imported=False, cloud_execution=False, training_performed=False)
    with Path(__file__).with_name(args.output_stem+'.json').open('x',encoding='utf-8') as stream:
        json.dump(output,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps(dict(medians=medians,admitted_over_strict_wall_ratio=output['admitted_over_strict_wall_ratio'])),flush=True)


if __name__ == '__main__':
    main()
