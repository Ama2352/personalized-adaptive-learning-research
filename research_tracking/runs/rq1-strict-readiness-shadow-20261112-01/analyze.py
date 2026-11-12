"""Hậu kiểm frontier strict trên cùng trạng thái đã lưu, không gọi mô hình."""

import csv
import ctypes
from ctypes import wintypes
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time


START = time.monotonic()
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / 'research_tracking/runs/rq1-closed-loop-reconstruction-20261108-02'
EXPOSURE = ROOT / 'research_tracking/runs/rq1-ready-set-exposure-20261108-01'
PINS = {
    SOURCE / 'accepted_fast__observed_metadata.jsonl.gz': '1ab8dcd5c5521c1f4055887f8d53032592a74e71949e9caaed83898c6efeb5ce',
    SOURCE / 'simulator_input__edges.csv': 'ecd910d8df52f8790997391de657ea0f9e8357446212c168b73e500d0facc2fb',
    SOURCE / 'prep__closed_loop_native_source_snapshot.json': 'a080cd079742d83dfef6a78f807d17c62f58dcdff9f8b36e38cc13f4ca428ec8',
    EXPOSURE / 'event_membership_flags.csv': 'd23005485c8d0f118f6371c88083eb2334093c1c5193ef2bad224355a8818f31',
}


class MemoryCounters(ctypes.Structure):
    _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
        (name, ctypes.c_size_t) for name in (
            'PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage',
            'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
            'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]


def current_rss():
    counters = MemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return counters.PeakWorkingSetSize


def guard():
    assert time.monotonic() - START < 60, 'Vượt cap60giây'
    peak = current_rss()
    assert peak <= 256 * 1024**2, 'Vượt RSS256MiB'
    return peak


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    assert sys.platform == 'win32', 'Receipt RAM dùng Windows API'
    inventory = {}
    for path, expected in PINS.items():
        guard()
        assert not path.is_symlink() and path.stat().st_size <= 2 * 1024**2
        actual = digest(path)
        assert actual == expected, str(path)
        inventory[path.relative_to(ROOT).as_posix()] = {'sha256': actual, 'bytes': path.stat().st_size}
    source = json.loads((SOURCE / 'prep__closed_loop_native_source_snapshot.json').read_text(encoding='utf-8'))
    selector = source['definitions']['CoverageAwareSelectorMixin']['source']
    assert 'self.selection_counts[p] >= MIN_PREREQUISITE_EXPOSURES' in selector
    assert 'self.mastery_score(x)' in selector
    with (SOURCE / 'simulator_input__edges.csv').open(encoding='utf-8-sig', newline='') as stream:
        edges = [(row['source'], row['target']) for row in csv.DictReader(stream)]
    assert len(edges) == len(set(edges)) == 31
    with (EXPOSURE / 'event_membership_flags.csv').open(encoding='utf-8-sig', newline='') as stream:
        expected_flags = {
            (int(row['seed']), row['profile'], row['variant'], int(row['step'])): row
            for row in csv.DictReader(stream)}
    assert len(expected_flags) == 3240
    trajectory_counts = {}
    groups = {}
    seen = set()
    nodes = None
    total_bytes = 0
    missing_score_rows = 0
    output_fields = ['seed', 'profile', 'variant', 'step', 'ready_size', 'strict_frontier_size',
                     'removed_by_exposure_count', 'strict_frontier_empty',
                     'served_outside_strict_frontier', 'served_is_root']
    with (HERE / 'events.csv').open('x', encoding='utf-8', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=output_fields)
        writer.writeheader()
        with gzip.open(SOURCE / 'accepted_fast__observed_metadata.jsonl.gz', 'rb') as stream:
            while raw := stream.readline(65537):
                guard()
                assert len(raw) <= 65536 and raw.endswith(b'\n')
                total_bytes += len(raw)
                assert total_bytes <= 64 * 1024**2
                row = json.loads(raw)
                key = row['seed'], row['profile'], row['variant'], row['step']
                assert key in expected_flags and key not in seen
                seen.add(key)
                trajectory = key[:3]
                counts, next_step = trajectory_counts.setdefault(trajectory, (Counter(), 0))
                assert row['step'] == next_step
                assert row['mastery_ready_capture_phase'] == 'during_selection_before_bookkeeping'
                mastery = row['mastered_decisions']
                assert len(mastery) == 28 and all(type(value) is bool for value in mastery.values())
                calls = [call for call in row['mastery_calls'] if call['direct_caller'] == 'ready_set']
                order = [call['concept'] for call in calls[:28]]
                assert len(set(order)) == 28 and set(order) == set(mastery)
                assert all(call['mastered'] == mastery[call['concept']] for call in calls)
                if nodes is None:
                    nodes = order
                    parents = {node: [] for node in nodes}
                    for parent, child in edges:
                        assert parent in parents and child in parents and parent != child
                        parents[child].append(parent)
                assert nodes == order
                strict = [node for node in nodes if not mastery[node]
                          and all(mastery[parent] for parent in parents[node])]
                baseline = [node for node in nodes if not mastery[node]
                            and all(mastery[parent] or counts[parent] >= 6 for parent in parents[node])]
                assert baseline and baseline == row['ready_set'], 'Baseline source frontier phải khớp exact'
                assert set(strict) <= set(baseline)
                served = row['served_tuple']['concept']
                assert served in baseline
                flag = expected_flags[key]
                outside = served not in strict
                assert outside == (flag['served_class'] == 'exposure_exception')
                assert flag['served_is_root'] == str(not parents[served])
                missing_score_rows += int(set(nodes) != {call['concept'] for call in row['mastery_score_calls']})
                measurement = {
                    'events': 1, 'ready_memberships': len(baseline),
                    'strict_frontier_memberships': len(strict),
                    'removed_by_exposure_memberships': len(baseline) - len(strict),
                    'changed_frontier_events': int(strict != baseline),
                    'strict_frontier_empty_events': int(not strict),
                    'served_outside_strict_frontier': int(outside),
                    'served_roots': int(not parents[served]),
                }
                for group in ('pooled', f'variant:{key[2]}', f'profile:{key[1]}:{key[2]}',
                              f'trajectory:{key[0]}:{key[1]}:{key[2]}'):
                    groups.setdefault(group, Counter()).update(measurement)
                writer.writerow(dict(zip(output_fields, (*key, len(baseline), len(strict),
                    len(baseline) - len(strict), not strict, outside, not parents[served]))))
                counts[served] += 1
                trajectory_counts[trajectory] = counts, next_step + 1
    assert seen == set(expected_flags) and len(trajectory_counts) == 27
    assert all(value[1] == 120 for value in trajectory_counts.values())
    assert groups['pooled']['served_outside_strict_frontier'] == 2041
    assert groups['pooled']['served_roots'] == 500
    for path, pin in PINS.items():
        assert digest(path) == pin
    assert not any(name in sys.modules for name in ('torch', 'numpy', 'pandas'))
    result = {
        'status': 'PASS_SAME_STATE_STRICT_FRONTIER_DESCRIPTION',
        'scope_vi': 'Bỏ ngoại lệ exposure ở frontier trên từng trạng thái lịch sử giữ nguyên. Không áp fallback, không dựng candidate/action và không rollout.',
        'groups': {key: dict(value) for key, value in sorted(groups.items())},
        'full_score_vector_missing_rows': missing_score_rows,
        'independent_unit': 'reused_seed_family', 'seed_families': 3,
        'new_independent_samples': 0, 'model_calls': 0, 'world_calls': 0,
        'counterfactual_actions_computed': 0, 'elapsed_seconds': time.monotonic() - START,
        'peak_rss_bytes': guard(), 'decompressed_input_bytes': total_bytes,
        'baseline_ready_sets_exact': len(seen), 'exposure_flag_agreements': len(seen),
    }
    for name, value in (('inputs.json', inventory), ('summary.json', result)):
        with (HERE / name).open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
