"""Final Development-only pyBKT refit in the verified WSL C++ environment."""

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
import sys
import threading
import time

import duckdb
import numpy as np
import psutil


PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))
ARTIFACTS = PROJECT / "artifacts/bkt_baseline"
RUN = PROJECT / "experiments/bkt_baseline/results/wsl_cpp/final_cpp"
MODELS = RUN / "models"
SCRATCH = RUN / "scratch"
CV_MANIFEST = PROJECT / "experiments/bkt_baseline/results/wsl_cpp/cv_cpp/run_manifest.json"
EXPECTED_E_STEP_HASH = "2c63eba0983cbff184f90a80ad811b921ce5b27b8f63425f136a0f62b00d553f"
BASE_SEED, NUM_FITS, TOL, MAXITER = 42, 1, 0.005, 100


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, data: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False), encoding="utf-8")
    temporary.replace(path)


def seed_for(skill: str) -> int:
    tagged = f"junyi-bkt-fit-v1|{BASE_SEED}|final-{NUM_FITS}|{skill}".encode()
    return int.from_bytes(hashlib.sha256(tagged).digest()[:4], "big")


def slug(skill: str) -> str:
    return hashlib.sha256(skill.encode("utf-8")).hexdigest()[:16]


def numeric_values(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from numeric_values(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from numeric_values(child)
    elif isinstance(value, np.ndarray):
        if np.issubdtype(value.dtype, np.number):
            yield value.astype(float, copy=False)
    elif isinstance(value, (int, float, np.number)) and not isinstance(value, bool):
        yield np.asarray(value, dtype=float)


def coefficients(model, skill: str) -> dict:
    result = {}
    for name, value in model.coef_[skill].items():
        array = np.asarray(value)
        result[name] = float(array) if array.ndim == 0 else array.tolist()
    return result


def validate_model(model, skill: str) -> None:
    if skill not in model.fit_model or skill not in model.coef_:
        raise RuntimeError(f"Missing fitted model for {skill}")
    values = list(numeric_values(model.fit_model[skill]))
    if not values or any(not np.isfinite(value).all() for value in values):
        raise FloatingPointError(f"Non-finite or empty model parameters for {skill}")
    params = coefficients(model, skill)
    for key in ("prior", "learns", "guesses", "slips", "forgets"):
        if key not in params or not np.isfinite(np.asarray(params[key], dtype=float)).all():
            raise FloatingPointError(f"Missing/non-finite {key} for {skill}")
    if not np.allclose(np.asarray(params["forgets"], dtype=float), 0.0, atol=1e-12):
        raise RuntimeError(f"forget parameters are not fixed at zero for {skill}")
    for key in ("prior", "learns", "guesses", "slips"):
        array = np.asarray(params[key], dtype=float)
        if ((array < 0) | (array > 1)).any():
            raise FloatingPointError(f"Out-of-range probability parameter {key} for {skill}")


def main() -> None:
    tmpdir = Path(os.environ.get("TMPDIR", "/tmp")).resolve()
    pycache = Path(os.environ.get("PYTHONPYCACHEPREFIX", "/tmp/pycache")).resolve()
    if any(not str(path).startswith("/mnt/d/") for path in (RUN, MODELS, SCRATCH, tmpdir, pycache)):
        raise RuntimeError("Final-fit outputs, DuckDB scratch, TMPDIR and pycache must be on D:")
    if (RUN / "final.json").exists():
        raise FileExistsError(f"Refusing to overwrite completed final fit: {RUN / 'final.json'}")
    RUN.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    (RUN / "tmp").mkdir(parents=True, exist_ok=True)
    (RUN / "pycache").mkdir(parents=True, exist_ok=True)

    cv_manifest = json.loads(CV_MANIFEST.read_text(encoding="utf-8-sig"))
    cv = json.loads((PROJECT / "experiments/bkt_baseline/results/wsl_cpp/cv_cpp/cv/cv.json").read_text(encoding="utf-8-sig"))
    if cv_manifest.get("status") != "complete":
        raise RuntimeError("Completed WSL C++ Development CV is required before final refit")
    if cv_manifest["runtime"].get("E_step_sha256") != EXPECTED_E_STEP_HASH:
        raise RuntimeError("Completed CV used an unexpected patched C++ backend")
    if cv_manifest["protocol_identity"].get("num_fits") != NUM_FITS or cv_manifest["protocol_identity"].get("base_seed") != BASE_SEED:
        raise RuntimeError("CV configuration differs from frozen final-refit configuration")
    if cv.get("num_fits") != NUM_FITS or cv.get("base_seed") != BASE_SEED or len(cv.get("folds", [])) != 5:
        raise RuntimeError("CV result protocol is incomplete or mismatched")

    canonical_path = ARTIFACTS / "derived/manifest.json"
    split_path = ARTIFACTS / "splits/manifest.json"
    assignments_path = ARTIFACTS / "splits/assignments.parquet"
    canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
    split = json.loads(split_path.read_text(encoding="utf-8"))
    inputs = cv_manifest["inputs"]
    if canonical["canonical_rows"] != inputs["canonical_rows"]:
        raise RuntimeError("Canonical row count differs from approved CV inputs")
    if sha256(canonical_path) != inputs["canonical_manifest_sha256"]:
        raise RuntimeError("Canonical manifest changed since CV")
    if sha256(assignments_path) != inputs["assignments_sha256"]:
        raise RuntimeError("Global student assignments changed since CV")
    if split["development_students"] != 198084 or split["seed"] != 42:
        raise RuntimeError("Expected 198,084 Development students and split seed 42")

    e_spec = importlib.util.find_spec("pyBKT.fit.E_step")
    p_spec = importlib.util.find_spec("pyBKT.fit.predict_onestep_states")
    if not e_spec or not e_spec.origin or not e_spec.origin.endswith(".so"):
        raise RuntimeError(f"Compiled C++ E_step not loaded: {e_spec}")
    if not p_spec or not p_spec.origin or not p_spec.origin.endswith(".so"):
        raise RuntimeError(f"Compiled C++ one-step predictor not loaded: {p_spec}")
    e_path, p_path = Path(e_spec.origin).resolve(), Path(p_spec.origin).resolve()
    if sha256(e_path) != EXPECTED_E_STEP_HASH:
        raise RuntimeError("Loaded C++ E_step binary differs from the patched CV binary")
    em_module = importlib.import_module("pyBKT.fit.EM_fit")
    em_path = Path(em_module.__file__).resolve()
    em_source_hash = sha256(PROJECT / "third_party/pyBKT/source-cpp/pyBKT/fit/EM_fit.py")
    if sha256(em_path) != em_source_hash:
        raise RuntimeError("Installed EM_fit convergence source differs from patched project source")

    from knowledge_tracing.bkt_baseline.config import preflight
    resource_preflight = preflight(RUN)
    runtime = {
        "backend": "CAHLR/pyBKT 1.4.3 C++",
        "pyBKT_version": importlib.metadata.version("pyBKT"),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "pandas_version": importlib.metadata.version("pandas"),
        "scikit_learn_version": importlib.metadata.version("scikit-learn"),
        "scipy_version": importlib.metadata.version("scipy"),
        "duckdb_version": duckdb.__version__,
        "psutil_version": importlib.metadata.version("psutil"),
        "platform": platform.platform(),
        "E_step_path": str(e_path), "E_step_sha256": sha256(e_path),
        "predict_onestep_states_path": str(p_path), "predict_onestep_states_sha256": sha256(p_path),
        "EM_fit_source_path": str(em_path), "EM_fit_source_sha256": sha256(em_path),
        "E_step_source_sha256": sha256(PROJECT / "third_party/pyBKT/source-cpp/pyBKT/fit/E_step.cpp"),
        "model": "standard BKT; one model per exercise; forgets=False; variant flags off",
        "num_fits": NUM_FITS, "tol": TOL, "maxiter": MAXITER, "base_seed": BASE_SEED,
    }
    identity = {
        "cv_run_manifest_sha256": sha256(CV_MANIFEST),
        "canonical_manifest_sha256": sha256(canonical_path),
        "assignments_sha256": sha256(assignments_path),
        "backend_sha256": runtime["E_step_sha256"],
        "patch_source_sha256": runtime["E_step_source_sha256"],
        "em_source_sha256": runtime["EM_fit_source_sha256"],
        "configuration": {"num_fits": NUM_FITS, "forgets": False, "tol": TOL, "maxiter": MAXITER, "base_seed": BASE_SEED},
    }
    manifest_path = RUN / "run_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("identity") != identity or manifest.get("status") == "complete":
            raise RuntimeError("Existing final-fit manifest is incompatible or already complete")
    else:
        manifest = {"status": "prepared", "created_utc": datetime.now(timezone.utc).isoformat(), "identity": identity}

    process = psutil.Process()
    peak = [process.memory_info().rss]
    stop = threading.Event()

    def sample_rss():
        while not stop.wait(0.5):
            try:
                peak[0] = max(peak[0], process.memory_info().rss)
            except psutil.Error:
                return

    monitor = threading.Thread(target=sample_rss, daemon=True)
    monitor.start()
    original_em = em_module.EM_fit
    current_trace = []

    def checked_em(*args, **kwargs):
        kwargs["tol"], kwargs["maxiter"] = TOL, MAXITER
        fitted, trace = original_em(*args, **kwargs)
        values = np.asarray(trace, dtype=float).reshape(-1)
        if values.size == 0 or not np.isfinite(values).all():
            raise FloatingPointError("Empty/non-finite EM training likelihood")
        current_trace[:] = values.tolist()
        return fitted, trace

    em_module.EM_fit = checked_em
    store = None
    start = time.perf_counter()
    completed = dict(manifest.get("completed", {}))
    failures = []
    try:
        from knowledge_tracing.bkt_baseline.pipeline import DataStore
        from knowledge_tracing.bkt_baseline.adapter import fit_skill

        store = DataStore(ARTIFACTS / "derived/canonical", assignments_path, SCRATCH)
        support = store.development_support()
        skills = support.exercise.astype(str).tolist()
        if len(skills) != 720 or skills != cv_manifest.get("skills"):
            raise RuntimeError("Development exercise inventory differs from completed CV")
        dev_skill_students = support.train_students + support.validation_students
        if support.empty or (dev_skill_students <= 0).any():
            raise RuntimeError("At least one exercise has no Development students")
        dev_students = int(store.con.execute(
            "SELECT COUNT(DISTINCT a.user_id) FROM assignments a WHERE a.partition='development'"
        ).fetchone()[0])
        if dev_students != 198084:
            raise RuntimeError(f"Expected 198084 Development students, got {dev_students}")

        manifest.update({
            "status": "running", "started_utc": datetime.now(timezone.utc).isoformat(),
            "runtime": runtime, "identity": identity,
            "inputs": {"canonical_rows": canonical["canonical_rows"], "development_students": dev_students,
                       "development_exercises": len(skills), "canonical_manifest": str(canonical_path),
                       "assignments": str(assignments_path), "cv_manifest": str(CV_MANIFEST)},
            "outputs_on_D": str(RUN),
            "temporary_and_cache_paths": {"TMPDIR": str(tmpdir), "PYTHONPYCACHEPREFIX": str(pycache), "duckdb": str(SCRATCH)},
            "resource_preflight": resource_preflight, "completed": completed,
        })
        atomic_json(manifest_path, manifest)

        for index, skill in enumerate(skills, 1):
            filename = f"{slug(skill)}.pkl"
            model_path = MODELS / filename
            saved = completed.get(skill)
            if saved and model_path.is_file() and sha256(model_path) == saved.get("model_sha256"):
                print(f"Final fit resumed {index}/{len(skills)}: {skill}", flush=True)
                continue
            current_trace.clear()
            data = store.load_development_skill(skill)
            dev_data = data[data["fold"].notna()].copy()
            if dev_data["user_id"].nunique() != int(support.loc[support.exercise == skill, "train_students"].iloc[0]) + int(support.loc[support.exercise == skill, "validation_students"].iloc[0]):
                raise RuntimeError(f"Development skill student count mismatch: {skill}")
            fit_seed = seed_for(skill)
            fit_start = time.perf_counter()
            model = fit_skill(dev_data, skill, NUM_FITS, fit_seed)
            validate_model(model, skill)
            trace = np.asarray(current_trace, dtype=float)
            if trace.size == 0 or not np.isfinite(trace).all():
                raise FloatingPointError(f"Missing/non-finite likelihood trace for {skill}")
            decreases = np.diff(trace)
            if decreases.size and float(decreases.min()) < -1e-6:
                raise FloatingPointError(f"EM training likelihood decreased unexpectedly for {skill}: {float(decreases.min())}")
            final_delta = abs(float(trace[-1] - trace[-2])) if trace.size > 1 else None
            stopped_by_tol = bool(final_delta is not None and final_delta < TOL)
            hit_maxiter = bool(trace.size == MAXITER and not stopped_by_tol)
            temp_model = model_path.with_suffix(".pkl.tmp")
            model.save(str(temp_model))
            temp_model.replace(model_path)
            record = {
                "exercise": skill, "model_file": filename, "model_sha256": sha256(model_path),
                "fit_seed": fit_seed, "development_students": int(data.user_id.nunique()),
                "development_interactions": int(len(data)), "em_iterations": int(trace.size),
                "final_training_log_likelihood": float(trace[-1]), "training_log_likelihood_trace": trace.tolist(),
                "final_abs_likelihood_delta": final_delta, "stopped_by_tol": stopped_by_tol,
                "hit_maxiter": hit_maxiter, "tol": TOL, "maxiter": MAXITER,
                "wall_seconds": time.perf_counter() - fit_start, "peak_rss_bytes": int(peak[0]),
                "parameters": coefficients(model, skill),
            }
            completed[skill] = record
            manifest["completed"] = completed
            manifest["progress"] = {"finished_exercises": len(completed), "total_exercises": len(skills), "current_exercise": skill}
            manifest["peak_rss_bytes"] = max(int(manifest.get("peak_rss_bytes", 0)), peak[0])
            atomic_json(manifest_path, manifest)
            print(f"Final fit {len(completed)}/{len(skills)}: {skill}, rows={len(data)}, EM={trace.size}, {record['wall_seconds']:.2f}s", flush=True)

        if set(completed) != set(skills):
            raise RuntimeError("Final refit ended with missing exercises")
        # Confirm inputs and frozen CV evidence remained unchanged throughout fit.
        if sha256(canonical_path) != identity["canonical_manifest_sha256"] or sha256(assignments_path) != identity["assignments_sha256"]:
            raise RuntimeError("Canonical inputs or student assignments changed during final refit")
        if sha256(CV_MANIFEST) != identity["cv_run_manifest_sha256"]:
            raise RuntimeError("Completed CV manifest changed during final refit")
        elapsed = time.perf_counter() - start
        peak[0] = max(peak[0], process.memory_info().rss)
        totals = {
            "trained_exercises": len(completed), "training_interactions": sum(int(r["development_interactions"]) for r in completed.values()),
            "training_student_skill_pairs": sum(int(r["development_students"]) for r in completed.values()),
            "converged_by_tolerance": sum(bool(r["stopped_by_tol"]) for r in completed.values()),
            "hit_maxiter": sum(bool(r["hit_maxiter"]) for r in completed.values()),
            "minimum_em_iterations": min(int(r["em_iterations"]) for r in completed.values()),
            "maximum_em_iterations": max(int(r["em_iterations"]) for r in completed.values()),
            "mean_em_iterations": float(np.mean([r["em_iterations"] for r in completed.values()])),
            "non_finite_likelihoods": 0, "non_finite_parameters": 0,
        }
        final_result = {"status": "complete", "runtime": runtime, "configuration": identity["configuration"],
                        "inputs": manifest["inputs"], "totals": totals,
                        "fits": [{key: value for key, value in completed[s].items() if key != "training_log_likelihood_trace"} for s in skills],
                        "holdout_test_used": False}
        atomic_json(RUN / "final.json", final_result)
        manifest.update({"status": "complete", "completed_utc": datetime.now(timezone.utc).isoformat(),
                         "wall_seconds": elapsed, "peak_rss_bytes": int(peak[0]), "totals": totals,
                         "final_result": str(RUN / "final.json"), "holdout_test_used": False})
        atomic_json(manifest_path, manifest)
        print(json.dumps({"status": "complete", "exercises": len(completed), "wall_seconds": elapsed,
                         "peak_rss_bytes": int(peak[0]), "totals": totals, "output": str(RUN)}, indent=2), flush=True)
    except BaseException as exc:
        manifest.update({"status": "failed", "failed_utc": datetime.now(timezone.utc).isoformat(),
                         "last_error": f"{type(exc).__name__}: {exc}", "completed": completed,
                         "peak_rss_bytes": int(max(peak[0], process.memory_info().rss))})
        atomic_json(manifest_path, manifest)
        raise
    finally:
        if store is not None:
            store.close()
        em_module.EM_fit = original_em
        stop.set()
        monitor.join(timeout=2)


if __name__ == "__main__":
    main()
