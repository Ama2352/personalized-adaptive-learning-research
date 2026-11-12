"""Đối chiếu cache window cohort kỹ thuật Junyi đã ghim, không Torch/training."""
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'src'))
from knowledge_tracing.akt.research_junyi_engineering import prepare_inputs
from knowledge_tracing.akt.research_junyi_data import iter_junyi_research_windows
from knowledge_tracing.akt.research_junyi_window_cache import (
    build_junyi_window_cache, iter_junyi_window_cache)
from knowledge_tracing.akt.types import TrainingWindow, UnseenTarget


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def equal_record(expected, actual):
    assert type(expected) is type(actual)
    if type(expected) is UnseenTarget:
        assert expected == actual
        return
    if type(expected) is TrainingWindow:
        np.testing.assert_array_equal(expected.targets, actual.targets)
        assert expected.targets.dtype == actual.targets.dtype
        expected, actual = expected.window, actual.window
    assert expected.window_id == actual.window_id
    assert expected.inputs.user_ids == actual.inputs.user_ids
    assert expected.inputs.concept_ids is actual.inputs.concept_ids is None
    for name in ('item_ids', 'timestamps', 'prior_responses', 'source_rows', 'sequence_offsets'):
        left, right = getattr(expected.inputs, name), getattr(actual.inputs, name)
        np.testing.assert_array_equal(left, right)
        assert left.dtype == right.dtype
    for name in ('target_mask', 'global_ranks', 'history_available', 'history_used', 'context_reset'):
        left, right = getattr(expected, name), getattr(actual, name)
        np.testing.assert_array_equal(left, right)
        assert left.dtype == right.dtype


def main():
    request_path = ROOT/'research_tracking/runs/junyi-akt-cuda-engineering-20261112-01/gpu-request.json'
    request = json.loads(request_path.read_text())
    cohort = ROOT/'artifacts/akt/junyi-cohorts/cuda-engineering320x300-20261112-01'
    roles = ROOT/'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01/roles.json'
    pins = {cohort/'manifest.json': request['cohort_sha256'], roles: request['roles_sha256']}
    manifest = json.loads((cohort/'manifest.json').read_text())
    pins.update({cohort/(role+'.jsonl'): manifest['outputs_sha256'][role+'.jsonl']
                 for role in ('train', 'selection')})
    assert all(sha(path) == expected for path, expected in pins.items())
    views, encoding, learners, options = prepare_inputs(cohort, roles,
        cohort_sha256=request['cohort_sha256'], roles_sha256=request['roles_sha256'])
    del learners
    results = {}
    for role, expected_targets in (('train', 11833), ('selection', 1530)):
        view = views[role]
        root = ROOT/'artifacts/akt/window-cache/bounded320-20261112-01'/role
        source_sha = pins[cohort/(role+'.jsonl')]
        started = time.monotonic()
        receipt = build_junyi_window_cache(root,
            iter_junyi_research_windows(None, view, encoding, **options), view=view, encoding=encoding,
            source_data_sha256=source_sha, expected_target_rows=expected_targets)
        build_seconds = time.monotonic()-started
        restored = iter_junyi_window_cache(root, view=view, encoding=encoding,
            source_data_sha256=source_sha, expected_target_rows=expected_targets,
            expected_manifest_sha256=receipt['manifest_sha256'])
        original = iter_junyi_research_windows(None, view, encoding, **options)
        sentinel = object(); compared = 0
        from itertools import zip_longest
        started = time.monotonic()
        for left, right in zip_longest(original, restored, fillvalue=sentinel):
            assert left is not sentinel and right is not sentinel
            equal_record(left, right); compared += 1
        result = dict(receipt=receipt, exact_native_records_compared=compared,
            build_seconds=build_seconds, compare_seconds=time.monotonic()-started,
            root=root.relative_to(ROOT).as_posix(), source_data_sha256=source_sha,
            files={path.name: dict(sha256=sha(path), bytes=path.stat().st_size)
                   for path in sorted(root.iterdir()) if path.is_file()})
        assert compared == receipt['summary']['records']
        results[role] = result
    assert all(sha(path) == expected for path, expected in pins.items())
    assert 'torch' not in sys.modules
    output = dict(status='ACTUAL_BOUNDED_JUNYI_WINDOW_CACHE_EXACT_ROUNDTRIP_PASS',
        source_pins={path.relative_to(ROOT).as_posix(): value for path, value in pins.items()},
        encoding_identity=encoding.identity, roles_identity=views['train'].roles.identity,
        role_results=results, torch_imported=False, cloud_execution=False,
        full_junyi_cache_prepared=False, training_performed=False)
    with Path(__file__).with_name('actual-bounded-result.json').open('x', encoding='utf-8') as stream:
        json.dump(output, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps({role: result['receipt']['summary'] for role, result in results.items()}))


if __name__ == '__main__':
    main()
