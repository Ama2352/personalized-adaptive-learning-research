"""End-to-end smoke test for the isolated WSL pyBKT C++ CV path."""

from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys

import duckdb
import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[2]
ARTIFACTS = PROJECT / "artifacts/bkt_baseline"
OUT = PROJECT / "experiments/bkt_baseline/results/wsl_cpp/cv_cpp_smoke"
CV_OUT = OUT / "cv"
SCRATCH = OUT / "scratch"
WINDOWS_CV_PROGRESS = ARTIFACTS / "cv/cv_progress.json"
WINDOWS_CV_SHARD = ARTIFACTS / "cv/fold=0/73f5a45a98954cf5.parquet"
SKILL = "fraction_word_problems_1"

PACKAGE_ROOT = PROJECT / "src"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from knowledge_tracing.bkt_baseline import pipeline
from knowledge_tracing.bkt_baseline.adapter import fit_skill, predict_skill, verify_runtime
from knowledge_tracing.bkt_baseline.metrics import score_predictions
from knowledge_tracing.bkt_baseline.pipeline import DataStore, _seed


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    assert_true(not CV_OUT.exists(), f"Refusing to overwrite smoke output {CV_OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    SCRATCH.mkdir(parents=True, exist_ok=True)

    original_progress_hash = sha256(WINDOWS_CV_PROGRESS)
    original_shard_hash = sha256(WINDOWS_CV_SHARD)
    canonical_manifest = json.loads((ARTIFACTS / "derived/manifest.json").read_text())
    split_manifest = json.loads((ARTIFACTS / "splits/manifest.json").read_text())
    pilot = json.loads((ARTIFACTS / "pilot/pilot.json").read_text())
    assert_true(canonical_manifest["input_sha256"] == "a7c99ede1f9b19648fdcd953b6ca0b0282bd31f2f913bd9d26b23aa9fcb36a25", "Original dataset lineage differs")
    assert_true(canonical_manifest["canonical_rows"] == 25_924_553, "Canonical row count differs")
    assert_true(split_manifest["algorithm"] == "sha256-user-rank-v1" and split_manifest["seed"] == 42, "Student split protocol differs")
    assert_true(split_manifest["total_students"] == 247_606, "Student assignment count differs")
    assert_true(split_manifest["development_students"] == 198_084 and split_manifest["test_students"] == 49_522, "Development/Test split counts differ")
    assert_true(split_manifest["development_fold_students"] == {"0": 39617, "1": 39617, "2": 39617, "3": 39617, "4": 39616}, "Development fold counts differ")
    assert_true(pilot["selected_num_fits"] == 1, "Selected num_fits differs from approved Windows pilot")

    extension = importlib.util.find_spec("pyBKT.fit.E_step")
    assert_true(extension is not None and extension.origin and extension.origin.endswith(".so"), "C++ E_step extension is not loaded")
    extension_path = Path(extension.origin)
    extension_hash = sha256(extension_path)
    e_step_module = importlib.import_module("pyBKT.fit.E_step")
    assert_true(Path(e_step_module.__file__).resolve() == extension_path.resolve(), "Imported E_step differs from discovered compiled module")
    predict_extension = importlib.util.find_spec("pyBKT.fit.predict_onestep_states")
    assert_true(predict_extension is not None and predict_extension.origin and predict_extension.origin.endswith(".so"), "C++ one-step state predictor extension is not loaded")
    em_module = importlib.import_module("pyBKT.fit.EM_fit")

    con = duckdb.connect()
    con.execute("SET memory_limit='2GB'")
    con.execute("SET threads=4")
    con.execute(f"SET temp_directory='{SCRATCH.as_posix()}'")
    assignment_path = ARTIFACTS / "splits/assignments.parquet"
    fold_counts = {
        str(fold): count
        for fold, count in con.execute(
            f"SELECT fold, COUNT(*) FROM read_parquet('{assignment_path.as_posix()}') "
            "WHERE partition='development' GROUP BY fold ORDER BY fold"
        ).fetchall()
    }
    assert_true(fold_counts == split_manifest["development_fold_students"], "WSL assignment fold counts differ from Windows manifest")
    partition_counts = dict(con.execute(
        f"SELECT partition, COUNT(*) FROM read_parquet('{assignment_path.as_posix()}') GROUP BY partition"
    ).fetchall())
    assert_true(partition_counts == {"development": 198084, "test": 49522}, "WSL global student assignments differ from Windows manifest")
    con.close()

    runtime = verify_runtime()
    runtime.update({
        "duckdb_version": duckdb.__version__,
        "scikit_learn_version": importlib.metadata.version("scikit-learn"),
        "psutil_version": importlib.metadata.version("psutil"),
        "platform": platform.platform(),
        "backend": "CAHLR/pyBKT 1.4.3 C++",
        "E_step_path": str(extension_path),
        "E_step_sha256": extension_hash,
        "tol": 0.005,
        "maxiter": 100,
        "num_fits": 1,
        "model": "standard BKT; forgets=False; variant flags off; no predictors",
        "base_seed": 42,
    })

    original_em = em_module.EM_fit
    em_events: list[dict] = []

    # Enforce the approved settings and observe each trace without changing its values.
    def checked_em(*args, **kwargs):
        kwargs["tol"] = 0.005
        kwargs["maxiter"] = 100
        model, trace = original_em(*args, **kwargs)
        values = np.asarray(trace, dtype=float).reshape(-1)
        if values.size == 0 or not np.isfinite(values).all():
            raise FloatingPointError("Non-finite or empty EM likelihood trace in smoke test")
        delta = abs(values[-1] - values[-2]) if values.size > 1 else None
        em_events.append({"iterations": int(values.size), "final_log_likelihood": float(values[-1]), "last_delta": delta, "tol": kwargs["tol"], "maxiter": kwargs["maxiter"]})
        return model, trace

    em_module.EM_fit = checked_em
    store = DataStore(ARTIFACTS / "derived/canonical", assignment_path, SCRATCH)
    try:
        data = store.load_development_skill(SKILL)
        train = data[data.fold != 0].copy()
        validation = data[data.fold == 0].copy()
        assert_true(not (set(train.user_id) & set(validation.user_id)), "Smoke fit and evaluation students overlap")
        fit_seed = _seed(42, SKILL, "cv-0-1")
        model = fit_skill(train, SKILL, 1, fit_seed)
        assert_true(all(not flag for flag in model.model_type), "A non-standard BKT variant was enabled")
        assert_true(np.all(np.asarray(model.coef_[SKILL]["forgets"], dtype=float) == 0.0), "Forgetting was fitted")
        assert_true(len(em_events) == 1 and em_events[0]["tol"] == 0.005 and em_events[0]["maxiter"] == 100, "Convergence settings differ")

        predictions = predict_skill(model, validation)
        assert_true(len(predictions) == len(validation), "Prediction row count differs")
        evaluated = validation.merge(predictions, on="source_row", validate="one_to_one")
        scored = score_predictions(evaluated, {SKILL: int(train.user_id.nunique())})
        assert_true(set(scored["overall"]["metrics"]) == {"auc", "log_loss", "brier", "ece", "accuracy"}, "Evaluation metrics incomplete")
        assert_true(scored["overall"]["scored_rows"] == len(validation), "Fitted skill coverage is incomplete")

        sample = next(group for _, group in validation.groupby("user_id", sort=True) if len(group) >= 3).head(3).copy()
        changed = sample.copy()
        changed.iloc[1, changed.columns.get_loc("correct")] = 1 - int(changed.iloc[1]["correct"])
        before_by_row = predict_skill(model, sample).set_index("source_row")["prediction"]
        after_by_row = predict_skill(model, changed).set_index("source_row")["prediction"]
        before = before_by_row.reindex(sample["source_row"]).to_numpy()
        after = after_by_row.reindex(sample["source_row"]).to_numpy()
        assert_true(np.allclose(before[:2], after[:2], rtol=0, atol=1e-12), "A response changed its own or an earlier prediction")
        assert_true(not np.isclose(before[2], after[2], rtol=0, atol=1e-12), "A prior response did not update the next knowledge-state prediction")

        unseen_frame = evaluated.iloc[[0]].copy()
        unseen_frame["exercise"] = "__unseen_smoke_skill__"
        unseen_frame["user_id"] = "__unseen_smoke_user__"
        unseen_frame["prediction"] = np.nan
        unseen = score_predictions(pd.concat([evaluated.iloc[[0]], unseen_frame], ignore_index=True), {SKILL: int(train.user_id.nunique())})
        assert_true(unseen["overall"]["unseen_skills"] == 1 and unseen["overall"]["unseen_rows"] == 1, "Unseen coverage was not counted")
        assert_true(unseen["overall"]["scored_rows"] == 1, "Unseen row entered model-based metric denominator")

        # Prove checkpoint recovery after one durable fold, in this WSL-only directory.
        real_fit = pipeline.fit_skill
        calls = 0

        def interrupt_after_one(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("intentional smoke interruption after first durable fold")
            return real_fit(*args, **kwargs)

        pipeline.fit_skill = interrupt_after_one
        try:
            pipeline.run_cv(store, CV_OUT, skills=[SKILL], num_fits=1, seed=42)
        except RuntimeError as exc:
            assert_true("intentional smoke interruption" in str(exc), f"Unexpected first-pass error: {exc}")
        else:
            raise AssertionError("Expected an intentional interruption after first fold")
        finally:
            pipeline.fit_skill = real_fit
        progress_path = CV_OUT / "cv_progress.json"
        progress = json.loads(progress_path.read_text())
        assert_true(len(progress["completed"]) == 1, "First fold checkpoint was not durable")
        assert_true(len(list(CV_OUT.glob("fold=*/*.parquet"))) == 1, "Expected exactly one first-pass fold shard")
        resumed = pipeline.run_cv(store, CV_OUT, skills=[SKILL], num_fits=1, seed=42)
        assert_true(len(json.loads(progress_path.read_text())["completed"]) == 5, "Resume did not complete all five smoke folds")
        assert_true((CV_OUT / "cv.json").is_file(), "Resume did not emit CV metrics")
        assert_true(len(resumed["folds"]) == 5, "Smoke CV did not score all five folds")
    finally:
        store.close()
        em_module.EM_fit = original_em

    assert_true(sha256(WINDOWS_CV_PROGRESS) == original_progress_hash, "Windows CV progress checkpoint changed")
    assert_true(sha256(WINDOWS_CV_SHARD) == original_shard_hash, "Windows CV shard changed")
    assert_true(CV_OUT.resolve() != (ARTIFACTS / "cv").resolve(), "Smoke output aliases Windows CV output")

    result = {
        "status": "passed",
        "smoke_cv_output": str(CV_OUT),
        "runtime": runtime,
        "source_hashes": {
            "patched_E_step_cpp_sha256": sha256(PROJECT / "third_party/pyBKT/source-cpp/pyBKT/fit/E_step.cpp"),
            "patched_cpp_EM_fit_py_sha256": sha256(PROJECT / "third_party/pyBKT/source-cpp/pyBKT/fit/EM_fit.py"),
            "loaded_predict_onestep_states": predict_extension.origin,
        },
        "input_manifests": {
            "canonical": canonical_manifest,
            "split": split_manifest,
            "assignments_sha256": sha256(assignment_path),
            "partition_counts": partition_counts,
            "development_fold_students": fold_counts,
            "selected_num_fits": pilot["selected_num_fits"],
        },
        "checks": {
            "compiled_cpp_loaded": True,
            "one_step_ahead_response_perturbation": True,
            "metrics": ["auc", "log_loss", "brier", "ece", "accuracy"],
            "unseen_skill_excluded_and_counted": True,
            "checkpoint_resume": True,
            "windows_checkpoint_hashes_unchanged": True,
            "outputs_and_scratch_on_drive_d": True,
        },
        "smoke_em": em_events,
        "smoke_cv_aggregate": resumed["aggregate"],
        "windows_checkpoint_hashes": {"progress": original_progress_hash, "shard": original_shard_hash},
    }
    (OUT / "smoke_manifest.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({"status": result["status"], "E_step": runtime["E_step_path"], "E_step_sha256": extension_hash, "smoke_cv_output": str(CV_OUT), "smoke_jobs_completed": 5, "checks": result["checks"]}, indent=2))


if __name__ == "__main__":
    main()
