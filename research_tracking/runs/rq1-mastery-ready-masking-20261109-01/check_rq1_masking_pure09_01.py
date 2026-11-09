"""Owned worker cho đúng9fixtures manufactured, không mở cached research inputs."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OUTPUT = PREP / 'rq1-mask-pure09-attempt01'
ANALYZER = 'scripts/research/analyze_rq1_mastery_ready_masking.py'
TEST = 'tests/shared_kt/test_rq1_mastery_ready_masking.py'
PINS = {
    ANALYZER: '33e5fddf96e3559575538de71dcc424b9f72accb2ba6b3eb2cc66c1c55a8d6a9',
    TEST: '2d30113ac7433a88fef0c4daadc27fa9c5389ac775dc54686fd813aeaee6559a',
    'scripts/research/windows_owned_worker.py': '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1',
}
METHODS = (
    'test_all_controller_fields_and_index_order_are_admitted_exactly',
    'test_bool_visit_missing_domain_and_duplicate_parent_rejected',
    'test_canonical_prefix_types_and_event_range',
    'test_child_self_mastered_can_mask_changed_all_parent_gate',
    'test_exposure_six_masks_parent_eligibility_but_not_parent_self_exclusion',
    'test_frontier_and_fallback_are_not_conflated',
    'test_other_unready_parent_masks_changed_parent_without_exposure',
    'test_root_and_parent_units_and_all_zero_cells_remain_distinct',
    'test_visits_five_exposes_child_readiness_difference',
)
IDS = tuple('masking_tests09.MasteryReadyMaskingTests.' + name for name in METHODS)
FORBIDDEN = ('torch', 'numpy', 'pandas', 'knowledge_tracing', 'sklearn', 'scipy')


def need(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    started, wall = time.perf_counter(), time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-sha256', required=True)
    args = parser.parse_args()
    need(sys.dont_write_bytecode and Path(sys.prefix).resolve() == ROOT / '.venv', 'repository .venv and -B')
    sys.path.insert(0, str(ROOT / 'scripts/research'))
    from windows_owned_worker import worker_gate
    owner = worker_gate()

    def elapsed():
        return max(time.perf_counter() - started, time.time() - wall)

    def check():
        need(elapsed() < 12, 'pure worker12s shared clock')

    def sha(path):
        check()
        need(path.is_relative_to(ROOT) and path.resolve() == path and path.is_file(), 'physical workspace source')
        cursor = ROOT
        for part in path.relative_to(ROOT).parts:
            cursor /= part
            need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'no aliases')
        need(path.stat().st_size <= 65536, 'source64KiB')
        return hashlib.sha256(path.read_bytes()).hexdigest()

    expected = dict(PINS)
    expected[Path(__file__).resolve().relative_to(ROOT).as_posix()] = args.source_sha256
    before = {name: sha(ROOT / name) for name in expected}
    need(before == expected and not OUTPUT.exists(), 'exact reviewed sources and fresh test output')
    cold_before = {name: name in sys.modules for name in FORBIDDEN}
    need(not any(cold_before.values()), 'cold stdlib-only pure worker')
    counters = dict(forbidden_import_attempts=0, undeclared_child_attempts=0, socket_attempts=0)

    def audit(event, values):
        if event == 'import' and str(values[0]).split('.')[0] in FORBIDDEN:
            counters['forbidden_import_attempts'] += 1
            raise RuntimeError('pure worker denies native/model imports')
        if event == 'subprocess.Popen' or event in ('os.system', 'os.posix_spawn', 'os.spawn'):
            counters['undeclared_child_attempts'] += 1
            raise RuntimeError('pure worker denies child processes')
        if event.startswith('socket.'):
            counters['socket_attempts'] += 1
            raise RuntimeError('pure worker denies network/local socket metadata')
    sys.addaudithook(audit)
    import unittest
    spec = importlib.util.spec_from_file_location('masking_tests09', ROOT / TEST)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)

    def cases(value):
        for entry in value:
            if isinstance(entry, unittest.TestSuite):
                yield from cases(entry)
            else:
                yield entry.id()

    collected = list(cases(suite))
    need(collected == list(IDS) and suite.countTestCases() == 9, 'exact9 physical unittest IDs, no duplicate/subset')
    OUTPUT.mkdir()
    starts, stops = [], []

    class RecordingResult(unittest.TextTestResult):
        def startTest(self, test):
            check()
            starts.append(test.id())
            super().startTest(test)

        def stopTest(self, test):
            stops.append(test.id())
            super().stopTest(test)
            check()

    with (OUTPUT / 'unittest.log').open('x', encoding='utf-8') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=RecordingResult).run(suite)
        stream.flush()
        os.fsync(stream.fileno())
    need((OUTPUT / 'unittest.log').stat().st_size <= 65536, 'bounded raw test log')
    counts = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                  skipped=len(result.skipped), expected_failures=len(result.expectedFailures),
                  unexpected_successes=len(result.unexpectedSuccesses))
    after = {name: sha(ROOT / name) for name in expected}
    cold_after = {name: name in sys.modules for name in FORBIDDEN}
    accepted = (result.wasSuccessful() and counts == dict(tests=9, failures=0, errors=0, skipped=0,
                expected_failures=0, unexpected_successes=0) and starts == stops == collected
                and before == after and not any(cold_after.values()) and not any(counters.values()))
    check()
    record = dict(status='INNER_ACCEPTED_9_MANUFACTURED_MASKING_FIXTURES_PENDING_ROOT' if accepted else 'REJECTED_KEEP_PURE_FAILURE',
        counts=counts, collected_ids=collected, started_ids=starts, completed_ids=stops,
        source_before=before, source_after=after, cold_before=cold_before, cold_after=cold_after,
        audit_attempts=counters, native_model_calls=0, cached_research_inputs_opened=False,
        native_zero_scope='Cold denied model imports; no universal C-call profiler claim', owner_status=owner['status'],
        elapsed_before_receipt_seconds=elapsed(), worker_cap_seconds=12,
        log_sha256=hashlib.sha256((OUTPUT / 'unittest.log').read_bytes()).hexdigest())
    with (OUTPUT / 'result.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    check()
    print(json.dumps(dict(status=record['status'], counts=counts, elapsed_seconds=elapsed())))
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__':
    main()
