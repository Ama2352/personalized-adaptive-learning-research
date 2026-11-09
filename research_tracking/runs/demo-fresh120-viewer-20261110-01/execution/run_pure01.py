"""Kiểm thuần dữ liệu DEMO03, không mở listener hoặc gọi mô hình."""
from pathlib import Path
import contextlib
import hashlib
import json
import os
import platform
import sys
import threading
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
SOURCES = ["src/research_demo/evidence.py", "src/research_demo/server.py",
    "src/research_demo/__main__.py", "src/research_demo/static/index.html",
    "src/research_demo/static/demo.js", "tests/demo/test_viewer.py"]
NAMES = ["test_verified_complete_input_inventory", "test_every_snapshot_is_exact_projection_not_estimated_state",
    "test_curated_catalog_synthetic_only_and_missing_confidence", "test_ui_safe_dom_and_explicit_preview_boundary",
    "test_closed_pins_complete_projection_and_no_raw_or_oracle_fields",
    "test_all_prefix_flags_and_archived_first_break_keys_exact_projection",
    "test_closed_ui_context_and_cached_document_contract", "test_fresh_all_conditions_exact_projection_and_high_control",
    "test_fresh_fixed_condition_allowlist", "test_fresh_population_coupling_and_arithmetic_rejected",
    "test_fresh_tamper_stops_before_listening", "test_fresh_ui_pinned_sources_and_reused_styles",
    "test_fresh_fixed_endpoint_without_socket", "test_fresh_query_route_rejects_without_socket",
    "test_fresh_endpoint_retains_host_and_origin_guard"]

def hashes():
    return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}

def write(name, value):
    with (OUT/name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())

def main():
    started = time.perf_counter()
    if (OUT/"pure01-receipt.json").exists() or (OUT/"pure01-stdout.log").exists():
        raise RuntimeError("Output đã tồn tại")
    timer = threading.Timer(30, lambda: os._exit(124))
    timer.daemon = True
    timer.start()
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    sys.dont_write_bytecode = True
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    temp = OUT/"runtime-temp01"
    temp.mkdir(exist_ok=False)
    for name in ("TEMP", "TMP", "TMPDIR"):
        os.environ[name] = str(temp)
    before = hashes()
    write("pure01-source-before.json", before)
    # Metadata Windows thật được làm nóng trước audit, không thay hàm/giá trị OS.
    metadata = {"system": platform.system(), "release": platform.release(),
                "machine": platform.machine(), "processor": platform.processor(),
                "platform": platform.platform()}
    denied = []
    def audit(event, args):
        if event.startswith("socket.") or event == "subprocess.Popen":
            denied.append(event)
            raise RuntimeError("Pure DEMO03 cấm network/listener/child process")
        if event == "import" and args[0].split(".")[0] in {"torch", "numpy", "pandas", "knowledge_tracing"}:
            denied.append(event+":"+args[0])
            raise RuntimeError("Pure DEMO03 cấm import mô hình/dữ liệu số")
    sys.addaudithook(audit)
    args = ["tests/demo/test_viewer.py::"+name for name in NAMES]
    args += ["-q", "-p", "no:cacheprovider", "--basetemp="+str(OUT/"tmp01"),
             "--junitxml="+str(OUT/"pure01.xml")]
    with (OUT/"pure01-stdout.log").open("x", encoding="utf-8") as stdout, (OUT/"pure01-stderr.log").open("x", encoding="utf-8") as stderr:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            import pytest
            code = int(pytest.main(args))
    after = hashes()
    suites = ET.parse(OUT/"pure01.xml").getroot()
    cases = list(suites.iter("testcase"))
    counts = {tag: sum(len(c.findall(tag)) for c in cases) for tag in ("failure", "error", "skipped")}
    heavy = sorted(set(sys.modules) & {"torch", "numpy", "pandas", "knowledge_tracing"})
    accepted = code == 0 and len(cases) == 39 and not any(counts.values()) and before == after and not denied and not heavy
    write("pure01-receipt.json", {"accepted": accepted, "exit_code": code,
        "elapsed_seconds": time.perf_counter()-started, "cap_seconds": 30,
        "physical_cases": len(cases), "counts": counts, "source_before": before, "source_after": after,
        "selected_nodes": NAMES, "metadata_before_audit": metadata, "denied_after_metadata": denied,
        "heavy_imports": heavy, "scope_vi": "Chỉ dữ liệu và handler chưa bind. Không server/browser/NN hoặc claim full HTTP QA."})
    timer.cancel()
    print(json.dumps({"accepted": accepted, "cases": len(cases), "exit_code": code, "counts": counts}))
    return 0 if accepted else 1

if __name__ == "__main__":
    raise SystemExit(main())
