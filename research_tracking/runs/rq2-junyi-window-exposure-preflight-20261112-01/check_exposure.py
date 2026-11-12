"""Kiểm CSV toàn tập và đối chiếu bitset với seen-set trên 64 window cố định."""

from collections import Counter
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
START = time.monotonic()
spec = importlib.util.spec_from_file_location('exposure_candidate', HERE / 'analyze_exposure.py')
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


def guard():
    assert time.monotonic() - START < 30
    assert candidate.peak_rss() <= 256 * 1024**2


def reference(item_ids, target_mask, parents):
    seen = set()
    opportunities, exposed = Counter(), Counter()
    for item, target in zip(item_ids, target_mask):
        item = int(item)
        if target:
            for edge, parent in parents.get(item, ()):
                opportunities[edge] += 1
                exposed[edge] += int(parent in seen)
        seen.add(item)
    return opportunities, exposed


def main():
    result = json.loads((HERE / 'full01/result.json').read_text(encoding='utf-8'))
    assert result['status'] == 'PASS_FULL_TRAIN80_EXPOSURE'
    manifest_path = candidate.CACHE / 'manifest.json'
    assert candidate.sha(manifest_path) == candidate.MANIFEST_SHA
    assert candidate.sha(candidate.GRAPH) == candidate.GRAPH_SHA
    assert candidate.sha(candidate.ENCODING) == candidate.ENCODING_SHA
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    encoding = json.loads(candidate.ENCODING.read_text(encoding='utf-8'))
    graph = json.loads(candidate.GRAPH.read_text(encoding='utf-8'))
    edges = sorted(map(tuple, graph['corrected_edges']))
    vocabulary = {value: index for index, value in enumerate(encoding['values'])}
    parents = {}
    for index, (parent, child) in enumerate(edges):
        if child in vocabulary:
            parents.setdefault(vocabulary[child], []).append((index, vocabulary.get(parent)))
    with (HERE / 'full01/edge-exposure.csv').open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 976 and [(r['parent'], r['child']) for r in rows] == edges
    categories = Counter()
    totals = Counter()
    for row in rows:
        parent, child = row['parent'], row['child']
        assert row['parent_fitted'] == str(parent in vocabulary)
        assert row['child_fitted'] == str(child in vocabulary)
        targets, exposed, learners = (int(row[name]) for name in (
            'child_targets', 'targets_with_prior_parent', 'learners_with_prior_parent'))
        assert 0 <= learners <= exposed <= targets
        assert learners <= 126774
        if child not in vocabulary:
            categories['child_unfitted'] += 1
            assert targets == exposed == learners == 0
        elif parent not in vocabulary:
            categories['parent_unfitted_child_fitted'] += 1
            assert exposed == learners == 0
        elif exposed == 0:
            categories['both_fitted_no_prior_exposure'] += 1
            assert learners == 0
        else:
            categories['prior_exposure_present'] += 1
        totals.update(edge_target_opportunities=targets, prior_exposed_edge_targets=exposed)
    assert dict(categories) == dict(child_unfitted=58, parent_unfitted_child_fitted=28,
                                    both_fitted_no_prior_exposure=14, prior_exposure_present=876)
    assert totals['edge_target_opportunities'] == 18061909
    assert totals['prior_exposed_edge_targets'] == 5933011
    selected, pins = [], {}
    sample_targets = 0
    for shard_index in (0, 129, 259, 389, 519, 649, 779, 908):
        guard()
        entry = manifest['shards'][shard_index]
        path = candidate.CACHE / entry['name']
        assert candidate.sha(path) == entry['sha256']
        pins[entry['name']] = entry['sha256']
        with np.load(path, allow_pickle=False) as saved:
            offsets, ids, mask = (saved[name] for name in ('offsets', 'item_ids', 'target_mask'))
        assert len(offsets) == entry['records'] + 1
        for record_index in [k * (entry['records'] - 1) // 7 for k in range(8)]:
            guard()
            begin, end = int(offsets[record_index]), int(offsets[record_index + 1])
            expected_opportunities, expected_exposed = reference(ids[begin:end], mask[begin:end], parents)
            actual = candidate.count_window(ids[begin:end], mask[begin:end], parents)
            actual_opportunities = Counter({edge: targets for edge, targets, _ in actual})
            actual_exposed = Counter({edge: observed for edge, _, observed in actual})
            assert expected_opportunities == actual_opportunities
            assert expected_exposed == actual_exposed
            targets = int(mask[begin:end].sum())
            sample_targets += targets
            selected.append(dict(shard_index=shard_index, record_index=record_index,
                                 tokens=end - begin, targets=targets))
    assert len(selected) == 64 and not any(name in sys.modules for name in ('torch', 'pandas'))
    proof = dict(status='PASS_CSV_AND_64_WINDOW_SEEN_SET_PARITY', csv_rows=976,
                 disjoint_edge_categories=dict(categories), edge_target_totals=dict(totals),
                 full_target_population=result['counts']['targets'], sampled_windows=64,
                 sampled_targets=sample_targets, selection=selected, shard_pins=pins,
                 candidate_source_sha256=candidate.sha(HERE / 'analyze_exposure.py'),
                 checker_sha256=candidate.sha(Path(__file__)),
                 arrays_materialized=['offsets', 'item_ids', 'target_mask'],
                 correctness_arrays_materialized=[], full_scan_repeated=False,
                 elapsed_seconds=time.monotonic() - START, peak_rss_bytes=candidate.peak_rss(),
                 cap_seconds=30, scope_vi='Seen-set độc lập kiểm số học bitset trên sample64windows. CSVfull chỉ kiểm tổng và quan hệ, không tái lập mọiwindow.')
    with (HERE / 'independent-full-check.json').open('x', encoding='utf-8') as stream:
        json.dump(proof, stream, ensure_ascii=False, indent=2)
    print(json.dumps({key: value for key, value in proof.items() if key not in ('selection', 'shard_pins')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
