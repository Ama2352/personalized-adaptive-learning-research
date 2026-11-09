"""ROOT-only runner sáu fixture recorder, stdlib, tối đa20giây, chưa chạy.

Không nạp Paper2, world, oracle, dữ liệu hoặc scientific framework.
"""
import time
START = time.perf_counter()

import ast
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
import unittest

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OUT = PREP / "native-panel-pure01"
PINS = {
    "native_panel_observer_candidate01.py": "b54b5f9a0899ec46b3e90d98b283fb34c84adaae5d2f47a581e405962bc936ba",
    "test_native_panel_observer_candidate01.py": "8f2da30e9dfc299e1608658bec8b64a28b622d5b1e7ac6a3708feea08b62a9d1",
}
MODULE = "_native_panel_fixture01"
METHODS = tuple(sorted((
    "test_existing_calls_passthrough_fallback_and_immutable_rows",
    "test_binary64_thresholds_stored_pi_and_timestamp_are_separate",
    "test_invalid_first_pass_and_caught_errors_never_publish",
    "test_partial_install_restores_inherited_descriptor_absence",
    "test_body_cancellation_preserves_primary_and_retries_cleanup_only",
    "test_ticket_scope_no_stale_frame_and_preflight_no_mutations",
)))
EXPECTED = [MODULE + ".NativePanelTests." + name for name in METHODS]
DENIED = []
FORBIDDEN = {"numpy", "pandas", "torch", "scipy", "sklearn", "knowledge_tracing", "modal", "boto3"}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def source_hashes():
    result = {}
    for name in PINS:
        raw = (PREP/name).read_bytes()
        need(len(raw) <= 32*1024, "Source vượt32KiB")
        result[name] = hashlib.sha256(raw).hexdigest()
    return result


def write_json(name, value):
    with (OUT/name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def audit(event, args):
    if event == "import" and str(args[0]).split(".")[0] in FORBIDDEN:
        DENIED.append(event+":"+str(args[0]))
        raise RuntimeError("Không import scientific/model/world modules")
    if event.startswith("socket.") or event in {"subprocess.Popen", "os.system", "os.posix_spawn"}:
        DENIED.append(event)
        raise RuntimeError("Không network/child process trong pure fixtures")


def main():
    need(sys.dont_write_bytecode and Path(sys.prefix).resolve() == ROOT/".venv", "Chỉ .venv -B")
    need(source_hashes() == PINS and not OUT.exists(), "Source drift hoặc output đã có")
    tree = ast.parse((PREP/"test_native_panel_observer_candidate01.py").read_text(encoding="utf-8"))
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "NativePanelTests"]
    need(len(classes) == 1, "Một lớp fixture chính xác")
    actual = sorted(node.name for node in classes[0].body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"))
    need(actual == list(METHODS) and len(set(actual)) == 6, "Đúng sáu method duy nhất")
    need(not FORBIDDEN.intersection(sys.modules), "Cold imports trước kiểm")
    OUT.mkdir()
    write_json("allocation.json", {
        "scope": "SIX_MANUFACTURED_RECORDER_FIXTURES_ONLY_NO_AUTHORITY",
        "whole_cap_seconds": 20, "deadline_exit_seconds": 19,
        "expected_ids": EXPECTED, "source_before": PINS,
        "static_fixture_upper_bounds_not_observed_counts": {
            "manufactured_policy_instances": 10, "capture_attempts": 14,
            "manufactured_is_mastered_bodies": 44},
        "real_policy_world_oracle_model_calls_permitted": 0})
    left = 19 - (time.perf_counter()-START)
    need(left > 0, "Không còn thời gian admission")
    timer = threading.Timer(left, lambda: os._exit(124))
    timer.daemon = True
    timer.start()
    own_sha_before = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    sys.addaudithook(audit)
    collected, started, completed = [], [], []
    error = None
    result = None
    with (OUT/"stdout.log").open("x", encoding="utf-8") as stdout, (OUT/"stderr.log").open("x", encoding="utf-8") as stderr, (OUT/"cases.jsonl").open("x", encoding="utf-8") as journal:
        def event(stage, test):
            journal.write(json.dumps({"stage": stage, "id": test.id(),
                "elapsed_seconds": time.perf_counter()-START})+"\n")
            journal.flush()
            os.fsync(journal.fileno())
        class Result(unittest.TextTestResult):
            def startTest(self, test):
                started.append(test.id())
                event("started", test)
                super().startTest(test)
            def stopTest(self, test):
                completed.append(test.id())
                event("completed", test)
                super().stopTest(test)
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                spec = importlib.util.spec_from_file_location(MODULE, PREP/"test_native_panel_observer_candidate01.py")
                module = importlib.util.module_from_spec(spec)
                sys.modules[MODULE] = module
                spec.loader.exec_module(module)
                suite = unittest.defaultTestLoader.loadTestsFromTestCase(module.NativePanelTests)
                collected = [case.id() for case in suite]
                need(collected == EXPECTED, "Không đúng test IDs sau import")
                result = unittest.TextTestRunner(stream=stderr, verbosity=2, resultclass=Result).run(suite)
        except BaseException as caught:
            error = {"type": type(caught).__name__, "message": str(caught)}
        finally:
            stdout.flush()
            stderr.flush()
            os.fsync(stdout.fileno())
            os.fsync(stderr.fileno())
    counts = None if result is None else {
        "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "expected_failures": len(result.expectedFailures),
        "unexpected_successes": len(result.unexpectedSuccesses)}
    after = source_hashes()
    heavy = sorted(FORBIDDEN.intersection(sys.modules))
    own_sha_after = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    elapsed = time.perf_counter()-START
    accepted = (error is None and counts == {"tests": 6, "failures": 0, "errors": 0,
        "skipped": 0, "expected_failures": 0, "unexpected_successes": 0}
        and collected == started == completed == EXPECTED and after == PINS
        and own_sha_before == own_sha_after and not heavy and not DENIED and elapsed < 20)
    logs = {name: {"sha256": hashlib.sha256((OUT/name).read_bytes()).hexdigest(),
                  "bytes": (OUT/name).stat().st_size}
            for name in ("allocation.json", "stdout.log", "stderr.log", "cases.jsonl")}
    need(all(row["bytes"] <= 256*1024 for row in logs.values()), "Log vượt256KiB")
    write_json("result.json", {"status": "ACCEPTED_SIX_MANUFACTURED_PANEL_FIXTURES" if accepted else "REJECTED_PRESERVE_ALL",
        "elapsed_seconds_before_final": elapsed, "whole_cap_seconds": 20,
        "counts": counts, "collected_ids": collected, "started_ids": started, "completed_ids": completed,
        "source_before": PINS, "source_after": after, "runner_before_sha256": own_sha_before,
        "runner_after_sha256": own_sha_after, "heavy_imports": heavy, "denied": DENIED,
        "error": error, "outputs": logs,
        "scope_vi": "Fixture giả dựng tay. Không native Paper2/world/oracle, không global-panel scientific result."})
    need(time.perf_counter()-START < 20, "Quá whole cap sau receipt")
    timer.cancel()
    timer.join(timeout=0.1)
    print(json.dumps({"accepted": accepted, "counts": counts, "elapsed_seconds": time.perf_counter()-START}))
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
