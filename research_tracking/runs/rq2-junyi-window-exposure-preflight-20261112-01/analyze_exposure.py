"""Đo parent-prefix exposure từ TRAIN cache, không materialize nhãn."""

import argparse
from collections import Counter
import csv
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback
import zipfile

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = ROOT / 'artifacts/akt/window-cache/full-train80-20261112-02'
ENCODING = ROOT / 'artifacts/akt/window-cache/full-train80-20261112-02.encoding.json'
GRAPH = ROOT / 'research_tracking/runs/cpu-junyi-graph-reconstruction-20261107-01/graph.json'
MANIFEST_SHA = '43f48045370b6811e537d7936ed307291e1dee88be313c111e4879198556a839'
ENCODING_SHA = '4d5d7330d17f48b3b7d759bc331a99523093cfd249a0f9d7fd455480789c209f'
GRAPH_SHA = 'df7595b1437c46421cd7fea8cc2f3234ff9a69207961c4c34df4a78cae7f80b1'
ALLOWED_ARRAYS = ('offsets', 'metadata', 'item_ids', 'target_mask', 'global_ranks')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


class MemoryCounters(ctypes.Structure):
    _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
        (name, ctypes.c_size_t) for name in (
            'PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage',
            'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
            'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]


def peak_rss():
    counters = MemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return counters.PeakWorkingSetSize


def count_window(item_ids, target_mask, parents):
    first = {}
    target_bits = {}
    for position, raw_id in enumerate(item_ids):
        item = int(raw_id)
        first.setdefault(item, position)
        if target_mask[position]:
            target_bits[item] = target_bits.get(item, 0) | (1 << position)
    result = []
    for child, bits in target_bits.items():
        opportunities = bits.bit_count()
        for edge, parent in parents.get(child, ()):
            parent_position = first.get(parent)
            observed = 0 if parent_position is None else (bits >> (parent_position + 1)).bit_count()
            result.append((edge, opportunities, observed))
    return result


def fixtures():
    parents = {1: [(0, 0)]}
    assert count_window([1, 0, 1], [True, False, True], parents) == [(0, 2, 1)]
    assert count_window([1, 0], [True, False], parents) == [(0, 1, 0)]
    assert count_window([0, 1], [False, True], parents) == [(0, 1, 1)]
    assert count_window([1], [True], parents) == [(0, 1, 0)]
    assert count_window([1, 1], [False, True], {1: [(0, 1)]}) == [(0, 1, 1)]
    assert count_window([1], [True], {1: [(0, 1)]}) == [(0, 1, 0)]
    return dict(status='PASS', cases=6, scope_vi='Current/future parent không là prior, context chỉ góp prefix, window reset và strict j boundary.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('admission', 'full'), default='admission')
    parser.add_argument('--output-name', default='admission01')
    parser.add_argument('--full-review-reference')
    args = parser.parse_args()
    assert Path(args.output_name).name == args.output_name and args.output_name not in ('.', '..')
    if args.mode == 'full':
        assert args.full_review_reference, 'Root review reference required before fullscan'
    output = HERE / args.output_name
    output.mkdir(exist_ok=False)
    start = time.monotonic()
    cap = 15 if args.mode == 'admission' else 180
    counts = Counter(windows=0, targets=0, tokens=0, shards=0, raw_bytes_hashed=0)

    def guard():
        assert time.monotonic() - start < cap, 'Wall budget exceeded'
        assert peak_rss() <= 256 * 1024**2, 'RSS256MiB exceeded'

    try:
        guard()
        fixture_result = fixtures()
        pins = {CACHE / 'manifest.json': MANIFEST_SHA, ENCODING: ENCODING_SHA, GRAPH: GRAPH_SHA}
        for path, pin in pins.items():
            assert sha(path) == pin
        manifest = json.loads((CACHE / 'manifest.json').read_text(encoding='utf-8'))
        complete = json.loads((CACHE / 'COMPLETE.json').read_text(encoding='utf-8'))
        assert complete['manifest_sha256'] == MANIFEST_SHA
        assert manifest['status'] == 'COMPLETE' and manifest['key']['phase_scope'] == 'select_train80'
        assert manifest['key']['expected_target_rows'] == 13347331
        assert manifest['summary']['windows'] == 232662 and manifest['summary']['unseen_targets'] == 0
        encoding = json.loads(ENCODING.read_text(encoding='utf-8'))
        vocabulary = {value: index for index, value in enumerate(encoding['values'])}
        assert len(vocabulary) == 717
        graph = json.loads(GRAPH.read_text(encoding='utf-8'))
        edges = sorted(map(tuple, graph['corrected_edges']))
        assert len(edges) == len(set(edges)) == 976 and len(graph['nodes']) == 835
        parents = {}
        for index, (parent, child) in enumerate(edges):
            if child in vocabulary:
                parents.setdefault(vocabulary[child], []).append((index, vocabulary.get(parent)))
        target_counts = Counter()
        exposed_counts = Counter()
        learner_counts = Counter()
        active_learner = None
        learner_edges = set()
        finished_learners = set()
        next_rank = 0
        entries = manifest['shards'][:16] if args.mode == 'admission' else manifest['shards']
        input_inventory = {str(path.relative_to(ROOT)): dict(sha256=pin, bytes=path.stat().st_size)
                           for path, pin in pins.items()}
        for entry in entries:
            guard()
            name = entry['name']
            assert Path(name).name == name
            path = CACHE / name
            assert not path.is_symlink() and path.stat().st_size == entry['bytes'] <= 64 * 1024**2
            assert sha(path) == entry['sha256']
            input_inventory[str(path.relative_to(ROOT))] = dict(sha256=entry['sha256'], bytes=entry['bytes'])
            counts['raw_bytes_hashed'] += entry['bytes']
            with zipfile.ZipFile(path) as archive:
                assert sum(member.file_size for member in archive.infolist()) <= 32 * 1024**2
            with np.load(path, allow_pickle=False) as saved:
                assert all(name in saved.files for name in ALLOWED_ARRAYS)
                arrays = {name: saved[name] for name in ALLOWED_ARRAYS}
            offsets, metadata = arrays['offsets'], arrays['metadata']
            assert offsets.dtype == np.int64 and len(offsets) == entry['records'] + 1
            assert offsets[0] == 0 and offsets[-1] == entry['tokens'] and np.all(np.diff(offsets) > 0)
            assert metadata.dtype == np.uint8 and metadata.ndim == 1 and metadata.nbytes <= 2 * 1024**2
            records = json.loads(metadata.tobytes())
            assert len(records) == entry['records']
            ids, mask, ranks = arrays['item_ids'], arrays['target_mask'], arrays['global_ranks']
            assert ids.dtype == ranks.dtype == np.int64 and mask.dtype == np.bool_
            assert ids.shape == mask.shape == ranks.shape == (entry['tokens'],)
            assert np.all((ids >= 0) & (ids < 717))
            for index, meta in enumerate(records):
                guard()
                assert meta['kind'] == 'training'
                learner = meta['user_id']
                if learner != active_learner:
                    if active_learner is not None:
                        learner_counts.update(learner_edges)
                        finished_learners.add(active_learner)
                    assert learner not in finished_learners
                    active_learner, learner_edges, next_rank = learner, set(), 0
                begin, end = int(offsets[index]), int(offsets[index + 1])
                assert 1 <= end - begin <= 200
                local_mask = mask[begin:end]
                positions = np.flatnonzero(local_mask)
                assert positions.size and local_mask[positions[0]:].all()
                local_ranks = ranks[begin:end]
                assert np.all(np.diff(local_ranks) == 1) and int(local_ranks[positions[0]]) == next_rank
                next_rank += len(positions)
                for edge, opportunities, observed in count_window(ids[begin:end], local_mask, parents):
                    assert 0 <= observed <= opportunities
                    target_counts[edge] += opportunities
                    exposed_counts[edge] += observed
                    if observed:
                        learner_edges.add(edge)
                counts.update(windows=1, targets=len(positions), tokens=end - begin)
            counts['shards'] += 1
            write(output / 'progress.json', dict(counts, elapsed_seconds=time.monotonic() - start,
                                                peak_rss_bytes=peak_rss()))
        learner_counts.update(learner_edges)
        learners = len(finished_learners) + int(active_learner is not None)
        if args.mode == 'full':
            assert (counts['windows'], counts['targets'], counts['tokens'], learners) == (232662, 13347331, 23936131, 126774)
        for path, pin in pins.items():
            assert sha(path) == pin
        guard()
        with (output / 'edge-exposure.csv').open('x', encoding='utf-8', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(['parent', 'child', 'parent_fitted', 'child_fitted', 'child_targets',
                             'targets_with_prior_parent', 'learners_with_prior_parent'])
            for index, (parent, child) in enumerate(edges):
                writer.writerow([parent, child, parent in vocabulary, child in vocabulary,
                                 target_counts[index], exposed_counts[index], learner_counts[index]])
        result = dict(status='PASS_PARTIAL_ADMISSION_ONLY' if args.mode == 'admission' else 'PASS_FULL_TRAIN80_EXPOSURE',
                      mode=args.mode, full_cohort=args.mode == 'full', counts=dict(counts), observed_learners=learners,
                      last_learner_may_be_partial=args.mode == 'admission', graph_edges=976,
                      supported_edges=sum(exposed_counts[index] > 0 for index in range(976)),
                      fixture_result=fixture_result, arrays_materialized=list(ALLOWED_ARRAYS),
                      correctness_arrays_materialized=[], elapsed_seconds=time.monotonic() - start,
                      cap_seconds=cap, peak_rss_bytes=peak_rss(), full_review_reference=args.full_review_reference,
                      scope_vi='Catalog base duy nhất, native-window prefix, không model/prediction/controls benchmark.',
                      torch_imported='torch' in sys.modules)
        assert not result['torch_imported']
        write(output / 'inputs.json', input_inventory)
        write(output / 'result.json', result)
        print(json.dumps(result, ensure_ascii=False))
    except BaseException as error:
        result = dict(status='FAIL_PRESERVED', error_type=type(error).__name__, error=str(error),
                      counts=dict(counts), elapsed_seconds=time.monotonic() - start, cap_seconds=cap)
        write(output / 'failure.json', result)
        (output / 'failure.log').write_text(traceback.format_exc(), encoding='utf-8')
        raise


if __name__ == '__main__':
    main()
