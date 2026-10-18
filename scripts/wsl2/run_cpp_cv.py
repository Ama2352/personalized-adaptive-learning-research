"""Run/resume the full Development-only CV in the isolated WSL C++ environment."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import statistics
import sys
import threading
import time

import duckdb
import numpy as np
import psutil

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))
ARTIFACTS = PROJECT / "artifacts/bkt_baseline"
RUN = PROJECT / "experiments/bkt_baseline/results/wsl_cpp/cv_cpp"
CV_OUT = RUN / "cv"
SCRATCH = RUN / "scratch"
WINDOWS_CV_PROGRESS = ARTIFACTS / "cv/cv_progress.json"
WINDOWS_CV_SHARD = ARTIFACTS / "cv/fold=0/73f5a45a98954cf5.parquet"
EXPECTED_E_STEP_HASH = "2c63eba0983cbff184f90a80ad811b921ce5b27b8f63425f136a0f62b00d553f"
BASE_SEED = 42
NUM_FITS = 1
TOL = 0.005
MAXITER = 100


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def atomic_json(path: Path, obj: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, allow_nan=False), encoding="utf-8")
    tmp.replace(path)


def aggregate_group(fold_results: list[dict], group_path: tuple[str, ...]) -> dict:
    groups = []
    for fold in fold_results:
        value = fold
        for key in group_path:
            value = value[key]
        groups.append(value)

    def mean_sd(values):
        defined = [float(v) for v in values if v is not None and math.isfinite(float(v))]
        return {
            "mean": statistics.mean(defined) if defined else None,
            "sample_sd": statistics.stdev(defined) if len(defined) > 1 else None,
            "defined_folds": len(defined),
        }

    names = ("auc", "log_loss", "brier", "ece", "accuracy")
    return {
        "total_rows_per_fold": [g["total_rows"] for g in groups],
        "scored_rows_per_fold": [g["scored_rows"] for g in groups],
        "coverage": mean_sd([g["coverage"] for g in groups]),
        "unseen_rows_per_fold": [g["unseen_rows"] for g in groups],
        "unseen_skills_per_fold": [g["unseen_skills"] for g in groups],
        "metrics": {name: mean_sd([g["metrics"][name] for g in groups]) for name in names},
    }


def aggregate_details(fold_results: list[dict]) -> dict:
    return {
        "overall": aggregate_group(fold_results, ("overall",)),
        "suggested": {
            label: aggregate_group(fold_results, ("suggested", label))
            for label in ("suggested", "non_suggested")
        },
        "rarity": {
            band: aggregate_group(fold_results, ("rarity", band))
            for band in ("unseen", "1-9", "10-49", "50-99", "100-999", ">=1000")
        },
        "aggregation": "unweighted mean and sample standard deviation across five folds; undefined metric folds omitted and counted",
    }


def markdown_report(result: dict, details: dict, manifest: dict) -> str:
    def pm(stat):
        if stat["mean"] is None:
            return "NA"
        if stat["sample_sd"] is None:
            return f"{stat['mean']:.6f} ± NA"
        return f"{stat['mean']:.6f} ± {stat['sample_sd']:.6f}"

    lines = [
        "# Junyi standard BKT — WSL2 C++ Development 5-fold CV",
        "",
        "## Thiết lập",
        "",
        f"- Backend: CAHLR/pyBKT {manifest['runtime']['pyBKT_version']} với C++ extension đã xác minh; SHA-256 E-step `{manifest['runtime']['E_step_sha256']}`.",
        f"- Dữ liệu và split: canonical `{manifest['inputs']['canonical_rows']:,}` dòng; assignments SHA-256 `{manifest['inputs']['assignments_sha256']}`; 5 fold theo student như manifest Windows.",
        f"- Cấu hình: standard BKT, một model mỗi exercise, `num_fits={NUM_FITS}`, `tol={TOL}`, `maxiter={MAXITER}`, seed gốc `{BASE_SEED}`, `forgets=False`; không dùng `suggested` làm predictor.",
        "- Dự đoán tuần tự one-step-ahead; metric dùng các skill được fit trong fold. Skill unseen giữ prediction null và chỉ tính coverage.",
        "- Kết quả bên dưới là trung bình không trọng số ± độ lệch chuẩn mẫu trên 5 fold.",
        "",
        "## Overall",
        "",
        "| Metric | Mean ± sample SD |",
        "|---|---:|",
    ]
    for key in ("auc", "log_loss", "brier", "ece", "accuracy"):
        lines.append(f"| {key} | {pm(details['overall']['metrics'][key])} |")
    coverage = details["overall"]["coverage"]
    lines += [
        "",
        f"Coverage fitted rows: {pm(coverage)}.",
        f"Rows theo fold: `{details['overall']['total_rows_per_fold']}`; fitted: `{details['overall']['scored_rows_per_fold']}`; unseen: `{details['overall']['unseen_rows_per_fold']}`.",
        f"Exercise unseen theo fold: `{details['overall']['unseen_skills_per_fold']}`.",
        "",
        "## Theo suggested",
        "",
        "| Nhóm | Coverage mean ± SD | AUC | Log Loss | Brier | ECE | Accuracy |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for label, display in (("suggested", "Suggested"), ("non_suggested", "Non-suggested")):
        group = details["suggested"][label]
        metrics = group["metrics"]
        lines.append("| " + display + " | " + " | ".join([pm(group["coverage"])] + [pm(metrics[n]) for n in ("auc", "log_loss", "brier", "ece", "accuracy")]) + " |")
    lines += ["", "## Theo độ hiếm skill", "", "| Training students / nhóm | Coverage mean ± SD | AUC | Log Loss | Brier | ECE | Accuracy | Unseen rows theo fold |", "|---|---:|---:|---:|---:|---:|---:|---|"]
    for band, group in details["rarity"].items():
        metrics = group["metrics"]
        lines.append("| " + band + " | " + " | ".join([pm(group["coverage"])] + [pm(metrics[n]) for n in ("auc", "log_loss", "brier", "ece", "accuracy")] + [str(group["unseen_rows_per_fold"])] ) + " |")
    lines += [
        "",
        "## Tài nguyên và tính tái lập",
        "",
        f"- Trạng thái: `{manifest['status']}`; số job đã checkpoint: {manifest.get('completed_jobs', 'NA')}.",
        f"- Wall-time thực tế: {manifest.get('wall_seconds', 'NA')} giây ({manifest.get('wall_seconds', 0) / 3600:.3f} giờ). Peak RSS tiến trình: {manifest.get('peak_rss_bytes', 0) / 1024**3:.3f} GiB.",
        f"- Phiên bản và patch hash đầy đủ nằm trong `run_manifest.json`; checkpoint riêng tại `cv/cv_progress.json`.",
        "- Chỉ Development CV được chạy; không final refit và không đánh giá holdout Test.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    if not str(RUN).startswith("/mnt/d/") or not str(SCRATCH).startswith("/mnt/d/"):
        raise RuntimeError("CV outputs/temp must remain on drive D")
    tmpdir = Path(os.environ.get("TMPDIR", "/tmp")).resolve()
    pycache = Path(os.environ.get("PYTHONPYCACHEPREFIX", "/tmp/pycache")).resolve()
    if not str(tmpdir).startswith("/mnt/d/") or not str(pycache).startswith("/mnt/d/"):
        raise RuntimeError("TMPDIR and Python bytecode cache must remain on drive D")
    RUN.mkdir(parents=True, exist_ok=True)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    (RUN / "tmp").mkdir(parents=True, exist_ok=True)
    (RUN / "pycache").mkdir(parents=True, exist_ok=True)
    from knowledge_tracing.bkt_baseline.config import preflight
    resource_preflight = preflight(RUN)
    if CV_OUT.resolve() == (ARTIFACTS / "cv").resolve():
        raise RuntimeError("Refusing to use/overwrite Windows CV checkpoint directory")
    if (CV_OUT / "cv.json").exists():
        raise FileExistsError(f"Completed WSL CV already exists: {CV_OUT / 'cv.json'}")

    canonical_manifest_path = ARTIFACTS / "derived/manifest.json"
    split_manifest_path = ARTIFACTS / "splits/manifest.json"
    assignments_path = ARTIFACTS / "splits/assignments.parquet"
    pilot_path = ARTIFACTS / "pilot/pilot.json"
    canonical_manifest = json.loads(canonical_manifest_path.read_text(encoding="utf-8"))
    split_manifest = json.loads(split_manifest_path.read_text(encoding="utf-8"))
    pilot = json.loads(pilot_path.read_text(encoding="utf-8"))
    windows_progress_before = sha256(WINDOWS_CV_PROGRESS)
    windows_shard_before = sha256(WINDOWS_CV_SHARD)
    windows_protocol = json.loads(WINDOWS_CV_PROGRESS.read_text(encoding="utf-8"))["protocol"]
    if windows_protocol["seed"] != BASE_SEED or windows_protocol["num_fits"] != NUM_FITS or windows_protocol["folds"] != 5:
        raise RuntimeError("Existing Windows CV protocol differs from approved settings")
    if pilot["selected_num_fits"] != NUM_FITS:
        raise RuntimeError("Windows Development pilot selected a different num_fits")

    e_spec = importlib.util.find_spec("pyBKT.fit.E_step")
    p_spec = importlib.util.find_spec("pyBKT.fit.predict_onestep_states")
    if not e_spec or not e_spec.origin or not e_spec.origin.endswith(".so"):
        raise RuntimeError(f"Compiled C++ E_step missing: {e_spec}")
    if not p_spec or not p_spec.origin or not p_spec.origin.endswith(".so"):
        raise RuntimeError(f"Compiled C++ one-step predictor missing: {p_spec}")
    e_path, p_path = Path(e_spec.origin).resolve(), Path(p_spec.origin).resolve()
    e_hash = sha256(e_path)
    if e_hash != EXPECTED_E_STEP_HASH:
        raise RuntimeError(f"Unexpected C++ E_step binary hash: {e_hash}")
    source_e_hash = sha256(PROJECT / "third_party/pyBKT/source-cpp/pyBKT/fit/E_step.cpp")
    source_em_hash = sha256(PROJECT / "third_party/pyBKT/source-cpp/pyBKT/fit/EM_fit.py")
    em_module = importlib.import_module("pyBKT.fit.EM_fit")
    installed_em_hash = sha256(Path(em_module.__file__).resolve())
    if installed_em_hash != source_em_hash:
        raise RuntimeError("Installed pyBKT EM convergence source differs from patched D: source")
    runtime = {
        "backend": "CAHLR/pyBKT 1.4.3 C++",
        "pyBKT_version": importlib.metadata.version("pyBKT"),
        "python_version": platform.python_version(),
        "numpy_version": importlib.metadata.version("numpy"),
        "pandas_version": importlib.metadata.version("pandas"),
        "duckdb_version": duckdb.__version__,
        "scikit_learn_version": importlib.metadata.version("scikit-learn"),
        "psutil_version": importlib.metadata.version("psutil"),
        "scipy_version": importlib.metadata.version("scipy"),
        "platform": platform.platform(),
        "E_step_path": str(e_path),
        "E_step_sha256": e_hash,
        "predict_onestep_states_path": str(p_path),
        "predict_onestep_states_sha256": sha256(p_path),
        "E_step_source_sha256": source_e_hash,
        "EM_fit_source_sha256": source_em_hash,
        "installed_EM_fit_source_sha256": installed_em_hash,
        "num_fits": NUM_FITS,
        "model": "standard BKT, one model per exercise, forgets=False, variant flags off",
        "tol": TOL,
        "maxiter": MAXITER,
        "base_seed": BASE_SEED,
        "split_seed": split_manifest["seed"],
    }

    manifest_path = RUN / "run_manifest.json"
    protocol_identity = {
        "backend": runtime["backend"], "E_step_sha256": e_hash,
        "E_step_source_sha256": source_e_hash, "EM_fit_source_sha256": source_em_hash,
        "num_fits": NUM_FITS, "tol": TOL, "maxiter": MAXITER, "base_seed": BASE_SEED,
        "folds": 5, "split_seed": split_manifest["seed"],
        "canonical_manifest_sha256": sha256(canonical_manifest_path),
        "assignments_sha256": sha256(assignments_path),
    }
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["protocol_identity"] != protocol_identity:
            raise RuntimeError("Existing WSL checkpoint identity differs; refusing incompatible resume")
        if manifest.get("status") == "complete":
            raise FileExistsError("WSL CV is already complete")
        if manifest.get("attempts") and manifest["attempts"][-1].get("status") == "running":
            resume_time = datetime.now(timezone.utc)
            previous_attempt = manifest["attempts"][-1]
            previous_start = datetime.fromisoformat(previous_attempt["started_utc"])
            previous_attempt.update({
                "status": "interrupted_resumed",
                "ended_utc": resume_time.isoformat(),
                "wall_seconds": (resume_time - previous_start).total_seconds(),
                "note": "Prior runner process was no longer active; resumed from durable WSL skill-fold checkpoints.",
            })
    else:
        manifest = {
            "status": "prepared", "protocol_identity": protocol_identity,
            "attempts": [], "created_utc": datetime.now(timezone.utc).isoformat(),
        }

    attempt = {"started_utc": datetime.now(timezone.utc).isoformat(), "status": "running"}
    manifest["status"] = "running"
    manifest["runtime"] = runtime
    manifest["inputs"] = {
        "canonical_manifest": str(canonical_manifest_path),
        "canonical_manifest_sha256": protocol_identity["canonical_manifest_sha256"],
        "source_csv_sha256": canonical_manifest["input_sha256"],
        "canonical_rows": canonical_manifest["canonical_rows"],
        "split_manifest": str(split_manifest_path),
        "assignments_file": str(assignments_path),
        "assignments_sha256": protocol_identity["assignments_sha256"],
        "development_students": split_manifest["development_students"],
        "test_students": split_manifest["test_students"],
        "development_fold_students": split_manifest["development_fold_students"],
        "selected_num_fits": pilot["selected_num_fits"],
    }
    manifest["outputs_on_D"] = str(RUN)
    manifest["resource_preflight"] = resource_preflight
    manifest["temporary_and_cache_paths"] = {"TMPDIR": str(tmpdir), "PYTHONPYCACHEPREFIX": str(pycache), "duckdb": str(SCRATCH), "pip_cache": str(PROJECT / ".wsl/pip-cache")}
    manifest["windows_checkpoint_hashes_before"] = {"progress": windows_progress_before, "fold0_shard": windows_shard_before}
    manifest["attempts"].append(attempt)
    atomic_json(manifest_path, manifest)

    process = psutil.Process()
    peak = [process.memory_info().rss]
    stop_sample = threading.Event()

    def sample_rss():
        while not stop_sample.wait(0.5):
            try:
                peak[0] = max(peak[0], process.memory_info().rss)
            except psutil.Error:
                return

    sampler = threading.Thread(target=sample_rss, name="rss-sampler", daemon=True)
    sampler.start()
    start_wall = time.perf_counter()
    em_calls = 0
    em_iteration_sum = 0
    em_min_iterations = None
    em_max_iterations = 0
    original_em = em_module.EM_fit

    def checked_em(*args, **kwargs):
        nonlocal em_calls, em_iteration_sum, em_min_iterations, em_max_iterations
        kwargs["tol"] = TOL
        kwargs["maxiter"] = MAXITER
        fitted_model, trace = original_em(*args, **kwargs)
        values = np.asarray(trace, dtype=float).reshape(-1)
        if values.size == 0 or not np.isfinite(values).all():
            raise FloatingPointError("Non-finite or empty likelihood trace; stopping CV")
        n = int(values.size)
        em_calls += 1
        em_iteration_sum += n
        em_min_iterations = n if em_min_iterations is None else min(em_min_iterations, n)
        em_max_iterations = max(em_max_iterations, n)
        return fitted_model, trace

    em_module.EM_fit = checked_em
    store = None
    try:
        from knowledge_tracing.bkt_baseline.pipeline import DataStore, run_cv

        store = DataStore(ARTIFACTS / "derived/canonical", assignments_path, SCRATCH)
        skills = store.development_support().exercise.astype(str).tolist()
        if skills != windows_protocol["skills"]:
            raise RuntimeError("WSL Development exercise inventory differs from existing Windows CV protocol")
        if not skills:
            raise RuntimeError("No Development exercises found")
        manifest["skills"] = skills
        manifest["expected_job_count_upper_bound"] = len(skills) * 5
        atomic_json(manifest_path, manifest)

        # The Windows checkpoint is only read for compatibility/integrity; all writes go to RUN/cv.
        result = run_cv(store, CV_OUT, skills=skills, num_fits=NUM_FITS, seed=BASE_SEED)
        details = aggregate_details(result["folds"])
        atomic_json(RUN / "cv_aggregate_details.json", details)
        wall_seconds = time.perf_counter() - start_wall
        peak[0] = max(peak[0], process.memory_info().rss)
        progress = json.loads((CV_OUT / "cv_progress.json").read_text(encoding="utf-8"))
        if progress["protocol"] != {"skills": skills, "num_fits": NUM_FITS, "seed": BASE_SEED, "folds": 5}:
            raise RuntimeError("Completed WSL CV checkpoint protocol mismatch")
        if len(result["folds"]) != 5:
            raise RuntimeError("CV aggregation did not produce all five folds")
        if any(fold.get("overall", {}).get("metrics") is None for fold in result["folds"]):
            raise RuntimeError("Missing fold metrics")
        if sha256(WINDOWS_CV_PROGRESS) != windows_progress_before or sha256(WINDOWS_CV_SHARD) != windows_shard_before:
            raise RuntimeError("Windows checkpoint changed while WSL CV ran")
        completed_at = datetime.now(timezone.utc)
        created_at = datetime.fromisoformat(manifest["created_utc"])
        total_wall_seconds = (completed_at - created_at).total_seconds()
        history_rss = max((int(record.get("peak_rss_bytes", 0)) for record in progress["completed"].values()), default=0)
        total_peak_rss = max(peak[0], history_rss, int(manifest.get("peak_rss_bytes", 0)))
        attempt.update({"status": "complete", "ended_utc": completed_at.isoformat(), "wall_seconds": wall_seconds})
        manifest.update({
            "status": "complete", "completed_utc": completed_at.isoformat(),
            "wall_seconds": total_wall_seconds, "active_attempt_wall_seconds": sum(float(a.get("wall_seconds", 0)) for a in manifest["attempts"]),
            "peak_rss_bytes": total_peak_rss,
            "memory_measurement": "0.5s RSS sampling per live attempt; resumed history also includes max per-fit RSS saved in durable checkpoints",
            "em_fit_calls": em_calls, "em_iteration_count": {
                "sum": em_iteration_sum, "min": em_min_iterations, "max": em_max_iterations,
                "mean": em_iteration_sum / em_calls if em_calls else None,
            },
            "completed_jobs": len(progress["completed"]),
            "cv_output": str(CV_OUT),
            "windows_checkpoint_hashes_after": {"progress": sha256(WINDOWS_CV_PROGRESS), "fold0_shard": sha256(WINDOWS_CV_SHARD)},
            "aggregate": result["aggregate"],
        })
        atomic_json(manifest_path, manifest)
        report = markdown_report(result, details, manifest)
        (RUN / "results_vi.md").write_text(report, encoding="utf-8")
        print(json.dumps({"status": manifest["status"], "skills": len(skills), "completed_jobs": manifest["completed_jobs"], "wall_seconds": wall_seconds, "peak_rss_bytes": peak[0], "aggregate": result["aggregate"], "results": str(RUN / "results_vi.md")}, indent=2))
    except BaseException as exc:
        elapsed = time.perf_counter() - start_wall
        peak[0] = max(peak[0], process.memory_info().rss)
        attempt.update({"status": "failed", "ended_utc": datetime.now(timezone.utc).isoformat(), "wall_seconds": elapsed, "error": f"{type(exc).__name__}: {exc}"})
        manifest.update({"status": "failed", "last_error": attempt["error"], "peak_rss_bytes": peak[0], "em_fit_calls": em_calls})
        atomic_json(manifest_path, manifest)
        raise
    finally:
        if store is not None:
            store.close()
        em_module.EM_fit = original_em
        stop_sample.set()
        sampler.join(timeout=2)


if __name__ == "__main__":
    main()
