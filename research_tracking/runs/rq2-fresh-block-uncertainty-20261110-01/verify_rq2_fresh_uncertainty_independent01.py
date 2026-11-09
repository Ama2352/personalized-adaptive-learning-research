"""Kiểm Decimal từ CSV đã lưu, không redraw, không import analyzer/kernel."""
import time
START = time.perf_counter()
import csv
from decimal import Decimal, localcontext
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import threading

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OUTPUT = PREP/"rq2_fresh_uncertainty_independent01.json"
FAMILY = ("K1000", "K1150", "K1150_minus_K1000")
KPATH = ROOT/"research_tracking/runs/rq2-fresh-graph-recovery-20261110-01/experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-03/conditional_lambda_contrasts.json"
PINS = {
    PREP/"rq2-fresh-block-uncertainty01/summary.json": "d51ed3a9e02b57b12ec8e7821f6d2a8b58b615634f704e442dea1891e461edcd",
    PREP/"rq2-fresh-block-uncertainty01/bootstrap_means.csv": "9087e919579dbec8fbc6f02e020283ba4d0f467b1903ee257835f62cb5d4bfbd",
    PREP/"rq2-fresh-block-uncertainty01/result.json": "7738c3b761e54f44c4dfeff3acfc1b7fcdc00efd5bddb06464caae118901f6a9",
    PREP/"rq2-fresh-block-uncertainty01-outer/result.json": "91a869a890b7ac233cbce112f08bd215c0fd5eea6b5307f85eabf1d04da1c6b3",
    PREP/"ROOT_RQ2_EXPLORATORY_UNCERTAINTY_REVIEW01.md": "f5f931bbcc4e14dcbb2f0d5c87c4bb55628ee826094f3529438f688bc8b33042",
    PREP/"RQ2_FRESH_BLOCK_UNCERTAINTY_SPEC01.md": "83f6cfde91ecbd12053de14da1f16295846aded1f798d0592b4cd61aa4b67da8",
    KPATH: "f48f5ec7f6683d8285288a5bffa05e46be2365d244aa83990c6797b43a721a38",
}
TOLERANCE = Decimal("1e-12")  # Chỉ so số học, không thay population/CI hoặc dấu.


def need(condition, message):
    if not condition:
        raise ValueError(message)


def raw(path):
    content = path.read_bytes()
    need(len(content) <= 1024*1024 and hashlib.sha256(content).hexdigest() == PINS[path], "Input drift hoặc vượt cap")
    return content


def decoded(path):
    return json.loads(raw(path), parse_float=Decimal)


def percentile(values, numerator):
    ordered = sorted(values)
    position = Decimal(len(ordered)-1)*Decimal(numerator)/Decimal(120)
    index = int(position)
    return ordered[index] + (position-index)*(ordered[index+1]-ordered[index])


def main():
    need(sys.dont_write_bytecode and Path(sys.prefix).resolve() == ROOT/".venv" and not OUTPUT.exists(), ".venv -B và output mới")
    timer = threading.Timer(max(.1, 4.8-(time.perf_counter()-START)), lambda: os._exit(124))
    timer.daemon = True
    timer.start()
    def audit(event, values):
        if event == "import" and str(values[0]).split(".")[0] in {"random", "numpy", "pandas", "torch", "knowledge_tracing"}:
            raise RuntimeError("Không RNG, framework hoặc analyzer/kernel")
        if event.startswith("socket.") or event in {"subprocess.Popen", "os.system"}:
            raise RuntimeError("Không network/process")
    sys.addaudithook(audit)
    report = {"status": "REJECTED_PRESERVE", "numeric_absolute_tolerance": str(TOLERANCE),
              "random_calls": 0, "bootstrap_redraws": 0, "draw_sha_recomputed": False}
    try:
        with localcontext() as context:
            context.prec = 60
            summary = decoded(PREP/"rq2-fresh-block-uncertainty01/summary.json")
            worker = decoded(PREP/"rq2-fresh-block-uncertainty01/result.json")
            outer = decoded(PREP/"rq2-fresh-block-uncertainty01-outer/result.json")
            for path in PINS:
                raw(path)
            need(outer["accepted"] is True and outer["returncode"] == 0 and outer["error"] is None
                 and outer["child_receipt"] == worker and worker["source_before"] == worker["source_after"], "Terminal acceptance mismatch")
            need(summary["family_estimands"] == list(FAMILY) and summary["blocks"] == list(range(21010,21020))
                 and summary["replicates"] == 10000 and summary["seed"] == 42 and summary["structural_K1300_tested"] is False
                 and summary["status"] == "POSTHOC_EXPLORATORY_NOT_RQ_COMPLETE", "Family/unit sai")
            need(abs(summary["family_nominal_coverage"]-Decimal(95)/100) <= TOLERANCE
                 and abs(summary["per_interval_nominal_coverage"]-Decimal(59)/60) <= TOLERANCE
                 and abs(summary["lower_quantile"]-Decimal(1)/120) <= TOLERANCE
                 and abs(summary["upper_quantile"]-Decimal(119)/120) <= TOLERANCE, "Bonferroni convention sai")
            rows = decoded(KPATH)
            keys = [(row["block"],row["ability"]) for row in rows]
            need(len(keys) == len(set(keys)) == 30 and set(keys) == {(b,a) for b in range(21010,21020) for a in (1000,1150,1300)}, "K population sai")
            values = {key: Decimal(str(row["lambda_difference"])) for key,row in zip(keys,rows)}
            need(all(values[b,1300] == 0 for b in range(21010,21020)), "Structural control sai")
            blocks = [(values[b,1000], values[b,1150], values[b,1150]-values[b,1000]) for b in range(21010,21020)]
            reader = csv.DictReader(io.StringIO(raw(PREP/"rq2-fresh-block-uncertainty01/bootstrap_means.csv").decode()))
            need(reader.fieldnames == ["replicate", *FAMILY], "CSV schema sai")
            columns = [[],[],[]]
            worst_pair_error = Decimal(0)
            for count,row in enumerate(reader):
                need(count < 10000 and row["replicate"] == str(count) and set(row) == {"replicate", *FAMILY}, "CSV index/grid sai")
                vector = [Decimal(row[name]) for name in FAMILY]
                need(all(v.is_finite() for v in vector), "CSV không hữu hạn")
                worst_pair_error = max(worst_pair_error, abs(vector[2]-(vector[1]-vector[0])))
                for index,value in enumerate(vector):
                    columns[index].append(value)
            need(all(len(column) == 10000 for column in columns) and worst_pair_error <= TOLERANCE, "CSV thiếu hoặc paired arithmetic sai")
            checked, worst = [], Decimal(0)
            need([row["estimand"] for row in summary["estimates"]] == list(FAMILY), "Summary estimands sai")
            for index, estimate in enumerate(summary["estimates"]):
                observed = [row[index] for row in blocks]
                expected = {"mean": sum(observed)/10, "observed_min": min(observed), "observed_max": max(observed),
                    "percentile_lower": percentile(columns[index],1), "percentile_upper": percentile(columns[index],119)}
                differences = {name: abs(value-estimate[name]) for name,value in expected.items()}
                worst = max(worst,*differences.values())
                need(all(v <= TOLERANCE for v in differences.values()), "Mean/type7 numeric mismatch")
                signs = {"positive": sum(v > 0 for v in observed), "negative": sum(v < 0 for v in observed), "zero": sum(v == 0 for v in observed)}
                need(estimate["signs"] == signs and estimate["blocks"] == 10, "Sign/unit mismatch")
                need(min(columns[index]) >= min(observed)-TOLERANCE
                     and max(columns[index]) <= max(observed)+TOLERANCE, "Bootstrap ngoài convex range")
                checked.append({"estimand": FAMILY[index], "decimal_recomputed": {name:str(value) for name,value in expected.items()},
                                "absolute_differences": {name:str(value) for name,value in differences.items()}})
            for path in PINS:
                raw(path)
            need(time.perf_counter()-START < 5 and "random" not in sys.modules, "Cap/RNG import breach")
            report.update(status="PASS_INDEPENDENT_DECIMAL_RECOUNT_NO_REDRAWS", decimal_precision=60,
                checked_estimates=checked, csv_rows=10000, source_blocks=10, family_size=3,
                max_numeric_absolute_difference=str(worst), max_shared_contrast_absolute_error=str(worst_pair_error),
                scope_vi="Mean/min/max/signs từ30K, sáu quantiles từCSV10000rows. Không kiểm lại RNG draw stream bằng redraw.")
    except BaseException as error:
        report["error"] = {"type":type(error).__name__,"message":str(error)}
    report["input_pins_before_after"] = {path.relative_to(ROOT).as_posix(): pin for path,pin in PINS.items()}
    report["elapsed_seconds_before_final"] = time.perf_counter()-START
    report["checker_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with OUTPUT.open("x",encoding="utf-8") as stream:
        json.dump(report,stream,ensure_ascii=False,indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    timer.cancel()
    timer.join(timeout=.1)
    print(json.dumps({"status":report["status"],"elapsed_seconds":time.perf_counter()-START}))
    return 0 if report["status"].startswith("PASS_") and time.perf_counter()-START < 5 else 1


if __name__ == "__main__":
    raise SystemExit(main())
