"""Đo ba lượt đọc native/cache cohort Junyi thật, không Torch hoặc training."""
import cProfile
import gc
import hashlib
import json
from pathlib import Path
import pstats
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'src'))
from knowledge_tracing.akt.research_junyi_engineering import prepare_inputs
from knowledge_tracing.akt.research_junyi_data import iter_junyi_research_windows
from knowledge_tracing.akt.research_junyi_window_cache import iter_junyi_window_cache
from knowledge_tracing.akt.types import TrainingWindow, UnseenTarget


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def consume(factory):
    count = targets = tokens = 0
    for record in factory():
        count += 1
        if type(record) is UnseenTarget:
            targets += 1
        else:
            window = record.window if type(record) is TrainingWindow else record
            targets += int(window.target_mask.sum())
            tokens += len(window.inputs.item_ids)
    result = dict(records=count, targets=targets, tokens=tokens)
    assert result == dict(records=315, targets=11833, tokens=17733)
    return result


def main():
    evidence = Path(__file__).with_name('actual-bounded-result.json')
    original = json.loads(evidence.read_text(encoding='utf-8'))
    assert all(sha(ROOT/name) == expected for name, expected in original['source_pins'].items())
    cohort = ROOT/'artifacts/akt/junyi-cohorts/cuda-engineering320x300-20261112-01'
    roles = ROOT/'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01/roles.json'
    views, encoding, learners, options = prepare_inputs(cohort, roles,
        cohort_sha256=original['source_pins'][(cohort/'manifest.json').relative_to(ROOT).as_posix()],
        roles_sha256=original['source_pins'][roles.relative_to(ROOT).as_posix()])
    del learners
    cache = original['role_results']['train']
    view = views['train']
    factories = dict(native=lambda: iter_junyi_research_windows(None, view, encoding, **options),
        cached=lambda: iter_junyi_window_cache(ROOT/cache['root'], view=view, encoding=encoding,
            source_data_sha256=cache['source_data_sha256'], expected_target_rows=11833,
            expected_manifest_sha256=cache['receipt']['manifest_sha256']))
    samples = []
    for iteration, order in enumerate((('native','cached'), ('cached','native'), ('native','cached')), 1):
        for name in order:
            gc.collect()
            started = time.perf_counter()
            population = consume(factories[name])
            elapsed = time.perf_counter()-started
            sample = dict(iteration=iteration, reader=name, seconds=elapsed,
                          targets_per_second=11833/elapsed, population=population)
            samples.append(sample)
            print(json.dumps(sample), flush=True)
    profiler = cProfile.Profile()
    profiler.runcall(consume, factories['cached'])
    profile = []
    for (filename, line, function), values in pstats.Stats(profiler).stats.items():
        if filename.endswith('research_junyi_window_cache.py'):
            primitive, calls, own, cumulative, _ = values
            profile.append(dict(function=function, line=line, calls=calls,
                                own_seconds=own, cumulative_seconds=cumulative))
    medians = {name: statistics.median(row['seconds'] for row in samples if row['reader']==name)
               for name in factories}
    assert 'torch' not in sys.modules
    assert all(sha(ROOT/name) == expected for name, expected in original['source_pins'].items())
    output = dict(status='ACTUAL_BOUNDED_READER_BENCHMARK_COMPLETE', iterations=3, samples=samples,
        median_seconds=medians, cached_over_native_wall_ratio=medians['cached']/medians['native'],
        cached_profile_functions=sorted(profile,key=lambda row:row['cumulative_seconds'],reverse=True),
        source_evidence_sha256=sha(evidence), source_pins=original['source_pins'],
        module_sha256=sha(ROOT/'src/knowledge_tracing/akt/research_junyi_window_cache.py'),
        limitations='Local Windows, cohort320,315trainingwindows, shared OS cache. Không suy runtime fullJunyi hoặc GPUtraining.',
        torch_imported=False, cloud_execution=False, training_performed=False)
    with Path(__file__).with_name('bounded-reader-benchmark.json').open('x',encoding='utf-8') as stream:
        json.dump(output,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps(dict(medians=medians, cached_over_native_wall_ratio=output['cached_over_native_wall_ratio'])),flush=True)


if __name__ == '__main__':
    main()
