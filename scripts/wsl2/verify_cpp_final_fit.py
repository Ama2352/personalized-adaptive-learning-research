"""Verify and finalize metadata for the isolated Development-only C++ refit."""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path

import numpy as np


PROJECT = Path(__file__).resolve().parents[2]
RUN = PROJECT / "experiments/bkt_baseline/results/wsl_cpp/final_cpp"
ARTIFACTS = PROJECT / "artifacts/bkt_baseline"
MANIFEST_PATH = RUN / "run_manifest.json"
FINAL_PATH = RUN / "final.json"
CV_MANIFEST_PATH = PROJECT / "experiments/bkt_baseline/results/wsl_cpp/cv_cpp/run_manifest.json"
TOL, MAXITER = 0.005, 100


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, obj: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, allow_nan=False), encoding="utf-8")
    tmp.replace(path)


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    final = json.loads(FINAL_PATH.read_text(encoding="utf-8"))
    cv = json.loads(CV_MANIFEST_PATH.read_text(encoding="utf-8-sig"))
    if manifest.get("status") != "complete" or final.get("status") != "complete":
        raise RuntimeError("Final refit is not complete")
    if manifest.get("holdout_test_used") is not False or final.get("holdout_test_used") is not False:
        raise RuntimeError("Holdout Test usage marker is not false")
    if str(RUN).startswith("/mnt/d/") is False:
        raise RuntimeError("Final output path is not on D:")

    runtime = manifest["runtime"]
    for distribution, version_key in (
        ("pandas", "pandas_version"),
        ("scikit-learn", "scikit_learn_version"),
        ("scipy", "scipy_version"),
    ):
        installed = importlib.metadata.version(distribution)
        cv_version = cv["runtime"].get(version_key)
        if cv_version != installed:
            raise RuntimeError(f"Dependency version differs from completed CV for {distribution}: {cv_version} vs {installed}")
        runtime[version_key] = installed
    for distribution, version_key in (("pyBKT", "pyBKT_version"), ("numpy", "numpy_version"), ("duckdb", "duckdb_version"), ("psutil", "psutil_version")):
        installed = importlib.metadata.version(distribution)
        if runtime.get(version_key) != installed:
            raise RuntimeError(f"Runtime dependency mismatch for {distribution}: {runtime.get(version_key)} vs {installed}")
    for module_name, expected_key in (
        ("pyBKT.fit.E_step", "E_step_sha256"),
        ("pyBKT.fit.predict_onestep_states", "predict_onestep_states_sha256"),
    ):
        spec = importlib.util.find_spec(module_name)
        if not spec or not spec.origin or not spec.origin.endswith(".so"):
            raise RuntimeError(f"Compiled extension is not loaded: {module_name}")
        path = Path(spec.origin).resolve()
        if str(path) != runtime[expected_key.replace("_sha256", "_path")] or sha256(path) != runtime[expected_key]:
            raise RuntimeError(f"Loaded extension identity/hash mismatch: {module_name}")
    for key, source_path in (
        ("E_step_source_sha256", PROJECT / "third_party/pyBKT/source-cpp/pyBKT/fit/E_step.cpp"),
        ("EM_fit_source_sha256", PROJECT / "third_party/pyBKT/source-cpp/pyBKT/fit/EM_fit.py"),
    ):
        if sha256(source_path) != runtime[key]:
            raise RuntimeError(f"Patched source changed after refit: {source_path}")

    cv_identity = manifest["identity"]
    if sha256(CV_MANIFEST_PATH) != cv_identity["cv_run_manifest_sha256"]:
        raise RuntimeError("Completed CV manifest changed since the final refit")
    if cv.get("status") != "complete" or len(cv.get("skills", [])) != 720:
        raise RuntimeError("CV inventory/status mismatch")
    if sha256(ARTIFACTS / "derived/manifest.json") != cv_identity["canonical_manifest_sha256"]:
        raise RuntimeError("Canonical dataset manifest changed")
    if sha256(ARTIFACTS / "splits/assignments.parquet") != cv_identity["assignments_sha256"]:
        raise RuntimeError("Global split assignment changed")

    checkpoint = manifest["completed"]
    final_fits = {record["exercise"]: record for record in final["fits"]}
    if set(checkpoint) != set(cv["skills"]) or set(final_fits) != set(checkpoint):
        raise RuntimeError("Final skill mapping differs from CV Development inventory")
    model_paths = []
    bad_likelihoods, bad_parameters, likelihood_decreases = [], [], []
    maxiter_exercises = []
    converged = 0
    for skill in cv["skills"]:
        record = checkpoint[skill]
        summary = final_fits[skill]
        model_path = RUN / "models" / record["model_file"]
        if not model_path.is_file() or sha256(model_path) != record["model_sha256"]:
            raise RuntimeError(f"Model file missing or hash mismatch for {skill}")
        if record["model_file"] != summary["model_file"] or record["model_sha256"] != summary["model_sha256"]:
            raise RuntimeError(f"Manifest/final model mapping differs for {skill}")
        model_paths.append(model_path)

        trace = np.asarray(record["training_log_likelihood_trace"], dtype=np.float64)
        if (trace.size != int(record["em_iterations"]) or trace.size == 0 or
                not np.isfinite(trace).all() or not np.isfinite(float(record["final_training_log_likelihood"])) or
                not np.isclose(trace[-1], float(record["final_training_log_likelihood"]), rtol=0, atol=1e-10)):
            bad_likelihoods.append(skill)
            continue
        if trace.size > 1 and float(np.diff(trace).min()) < -1e-6:
            likelihood_decreases.append(skill)
        params = record["parameters"]
        for name, value in params.items():
            values = np.asarray(value, dtype=np.float64)
            if not np.isfinite(values).all():
                bad_parameters.append(skill)
                break
            if name in ("prior", "learns", "guesses", "slips", "forgets") and ((values < -1e-12) | (values > 1 + 1e-12)).any():
                bad_parameters.append(skill)
                break
        if not np.allclose(np.asarray(params["forgets"], dtype=float), 0, atol=1e-12):
            bad_parameters.append(skill)
        delta = float(abs(trace[-1] - trace[-2])) if trace.size > 1 else None
        stopped_by_tol = bool(delta is not None and delta < TOL)
        hit_maxiter = bool(trace.size == MAXITER and not stopped_by_tol)
        record["final_abs_likelihood_delta"] = delta
        record["stopped_by_tol"] = stopped_by_tol
        record["hit_maxiter"] = hit_maxiter
        summary["final_abs_likelihood_delta"] = delta
        summary["stopped_by_tol"] = stopped_by_tol
        summary["hit_maxiter"] = hit_maxiter
        if hit_maxiter:
            maxiter_exercises.append({
                "exercise": skill, "iterations": int(trace.size),
                "final_abs_likelihood_delta": delta,
                "final_training_log_likelihood": float(trace[-1]),
            })
        converged += int(stopped_by_tol)

    if bad_likelihoods or bad_parameters or likelihood_decreases:
        raise FloatingPointError(json.dumps({
            "bad_likelihoods": bad_likelihoods,
            "bad_parameters": bad_parameters,
            "likelihood_decreases": likelihood_decreases,
        }))
    if len(model_paths) != 720 or len({p.name for p in model_paths}) != 720:
        raise RuntimeError("Expected 720 distinct saved model files")

    # Deserialize each saved model to ensure artifacts remain loadable and mapped to the right exercise.
    from pyBKT.models import Model
    for skill, path in zip(cv["skills"], model_paths):
        model = Model(seed=42, num_fits=1, parallel=False)
        model.load(str(path))
        if skill not in model.coef_:
            raise RuntimeError(f"Serialized model is not loadable/mapped to {skill}")
        for name, expected in checkpoint[skill]["parameters"].items():
            if not np.allclose(np.asarray(model.coef_[skill][name], dtype=float), np.asarray(expected, dtype=float), rtol=0, atol=1e-12):
                raise RuntimeError(f"Serialized coefficients differ from manifest for {skill}/{name}")

    totals = final["totals"]
    totals.update({
        "trained_exercises": len(checkpoint),
        "training_interactions": sum(int(r["development_interactions"]) for r in checkpoint.values()),
        "training_student_skill_pairs": sum(int(r["development_students"]) for r in checkpoint.values()),
        "converged_by_tolerance": converged,
        "hit_maxiter": len(maxiter_exercises),
        "minimum_em_iterations": min(int(r["em_iterations"]) for r in checkpoint.values()),
        "maximum_em_iterations": max(int(r["em_iterations"]) for r in checkpoint.values()),
        "mean_em_iterations": float(np.mean([r["em_iterations"] for r in checkpoint.values()])),
        "non_finite_likelihoods": 0,
        "non_finite_parameters": 0,
    })
    final["totals"] = totals
    final["runtime"] = runtime
    final["convergence_warnings"] = maxiter_exercises
    atomic_json(FINAL_PATH, final)

    mapping = [{
        "exercise": skill,
        "model_file": checkpoint[skill]["model_file"],
        "model_sha256": checkpoint[skill]["model_sha256"],
        "development_students": checkpoint[skill]["development_students"],
        "development_interactions": checkpoint[skill]["development_interactions"],
    } for skill in cv["skills"]]
    atomic_json(RUN / "skill_mapping.json", {"skills": mapping, "count": len(mapping)})

    # Retain the failed pre-fit guard as an audit note, but don't leave stale failure state on a complete run.
    old_error = manifest.pop("last_error", None)
    old_failed_utc = manifest.pop("failed_utc", None)
    if old_error:
        manifest["superseded_preflight_attempt"] = {
            "failed_utc": old_failed_utc,
            "error": old_error,
            "note": "Pre-fit guard used fold-specific CV support; it failed before fitting any model. The corrected full Development refit completed successfully.",
        }
    manifest["totals"] = totals
    manifest["convergence_warnings"] = maxiter_exercises
    manifest["verification"] = {
        "status": "passed_with_convergence_warnings" if maxiter_exercises else "passed",
        "verified_models": len(model_paths),
        "model_sha256_matches": len(model_paths),
        "serialized_models_loadable": len(model_paths),
        "parameters_finite_and_in_range": True,
        "likelihood_traces_finite_and_monotone": True,
        "holdout_test_read_or_used": False,
        "completed_cv_input_hashes_match": True,
    }
    atomic_json(MANIFEST_PATH, manifest)
    print(json.dumps({
        "verification": manifest["verification"],
        "totals": totals,
        "nonconverged": maxiter_exercises,
        "skill_mapping": str(RUN / "skill_mapping.json"),
        "final_json": str(FINAL_PATH),
    }, indent=2))


if __name__ == "__main__":
    main()
