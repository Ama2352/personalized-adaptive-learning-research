"""Development-only tuning, five-fold CV, final fit, and guarded holdout."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import statistics
import time

import duckdb
import numpy as np
import pandas as pd
import psutil
from pyBKT.models import Model

from .adapter import fit_skill, predict_skill, verify_runtime
from .metrics import score_predictions, score_prediction_shards


def _json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")


def _atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    _json(temporary, payload)
    temporary.replace(path)


def _read_parquet(path: Path) -> pd.DataFrame:
    con = duckdb.connect()
    try:
        escaped = str(path.resolve()).replace("'", "''")
        return con.execute(f"SELECT * FROM read_parquet('{escaped}')").df()
    finally:
        con.close()


def _seed(base: int, skill: str, stage: str) -> int:
    digest = hashlib.sha256(f"junyi-bkt-fit-v1|{base}|{stage}|{skill}".encode()).digest()
    return int.from_bytes(digest[:4], "big")


def _slug(skill: str) -> str:
    return hashlib.sha256(skill.encode("utf-8")).hexdigest()[:16]


def _peak_rss() -> int:
    info = psutil.Process().memory_info()
    return int(getattr(info, "peak_wset", info.rss))


def _coefs(model: Model, skill: str) -> dict:
    result = {}
    for name, value in model.coef_[skill].items():
        arr = np.asarray(value)
        result[name] = float(arr) if arr.ndim == 0 else arr.tolist()
    return result


def _join_prediction(validation: pd.DataFrame, model: Model | None) -> pd.DataFrame:
    result = validation.loc[:, ["source_row", "user_id", "exercise", "correct", "suggested"]].copy()
    if model is None:
        result["prediction"] = np.nan
    else:
        predicted = predict_skill(model, validation)
        result = result.merge(predicted, on="source_row", how="left", validate="one_to_one")
        if result["prediction"].isna().any():
            raise RuntimeError("Missing pyBKT prediction for fitted skill")
    return result


def _write_shard(frame: pd.DataFrame, destination: Path, support: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shard = frame.copy()
    shard["train_skill_students"] = int(support)
    con = duckdb.connect()
    try:
        con.register("shard", shard)
        escaped = str(destination.resolve()).replace("'", "''")
        con.execute(f"COPY (SELECT * FROM shard) TO '{escaped}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    finally:
        con.close()


class DataStore:
    """Read one exercise at a time from canonical Parquet and global assignments."""

    def __init__(self, canonical_dir: str | Path, assignments_parquet: str | Path, scratch_dir: str | Path):
        self.canonical_dir = Path(canonical_dir).resolve()
        self.assignments_parquet = Path(assignments_parquet).resolve()
        scratch = Path(scratch_dir).resolve()
        scratch.mkdir(parents=True, exist_ok=True)
        self.con = duckdb.connect()
        self.con.execute("SET memory_limit = '2GB'")
        self.con.execute("SET threads = 4")
        escaped_scratch = str(scratch).replace("'", "''")
        self.con.execute(f"SET temp_directory = '{escaped_scratch}'")
        canonical_glob = str(self.canonical_dir / "**" / "*.parquet").replace("'", "''")
        assignments = str(self.assignments_parquet).replace("'", "''")
        self.con.execute(f"CREATE VIEW canonical AS SELECT * FROM read_parquet('{canonical_glob}', hive_partitioning=true)")
        self.con.execute(f"CREATE VIEW assignments AS SELECT * FROM read_parquet('{assignments}')")

    def close(self) -> None:
        self.con.close()

    def development_support(self, pilot_fold: int = 0) -> pd.DataFrame:
        return self.con.execute(
            "SELECT c.exercise, "
            "COUNT(DISTINCT c.user_id) FILTER (WHERE a.fold != ?) AS train_students, "
            "COUNT(DISTINCT c.user_id) FILTER (WHERE a.fold = ?) AS validation_students, "
            "COUNT(*) FILTER (WHERE a.fold != ?) AS train_rows "
            "FROM canonical c JOIN assignments a USING (user_id) "
            "WHERE a.partition='development' GROUP BY c.exercise ORDER BY c.exercise",
            [pilot_fold, pilot_fold, pilot_fold],
        ).df()

    def load_development_skill(self, skill: str) -> pd.DataFrame:
        return self.con.execute(
            "SELECT c.*, c.exercise AS skill_name, a.fold "
            "FROM canonical c JOIN assignments a USING (user_id) "
            "WHERE c.exercise=? AND a.partition='development' "
            "ORDER BY c.user_id, c.order_id",
            [skill],
        ).df()

    def test_skills(self) -> list[str]:
        return [row[0] for row in self.con.execute(
            "SELECT DISTINCT c.exercise FROM canonical c JOIN assignments a USING (user_id) "
            "WHERE a.partition='test' ORDER BY c.exercise"
        ).fetchall()]

    def load_test_skill(self, skill: str) -> pd.DataFrame:
        return self.con.execute(
            "SELECT c.*, c.exercise AS skill_name "
            "FROM canonical c JOIN assignments a USING (user_id) "
            "WHERE c.exercise=? AND a.partition='test' "
            "ORDER BY c.user_id, c.order_id",
            [skill],
        ).df()


def select_pilot_skills(support: pd.DataFrame) -> list[str]:
    """Deterministically cover four training-support bands with two skills each."""
    eligible = support[(support.train_students > 0) & (support.validation_students > 0)]
    bands = ((1, 49), (50, 99), (100, 999), (1000, 10**12))
    selected = []
    for low, high in bands:
        options = eligible[(eligible.train_students >= low) & (eligible.train_students <= high)]
        bounded = options[options.train_rows <= 50_000]
        if len(bounded) >= 2:
            options = bounded
        else:
            options = options.sort_values(["train_rows", "exercise"]).head(10)
        names = sorted(options.exercise.tolist(), key=lambda name: (hashlib.sha256(name.encode()).digest(), name))
        selected.extend(names[:2])
    if len(selected) != 8:
        raise RuntimeError(f"Expected eight eligible pilot skills, found {len(selected)}")
    return selected


def run_pilot(
    store,
    output_dir: str | Path,
    *,
    skills: list[str] | None = None,
    num_fits: tuple[int, ...] = (1, 5, 10),
    seeds: tuple[int, ...] = (17, 29, 43),
    pilot_fold: int = 0,
) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if (output / "pilot.json").exists():
        raise FileExistsError(output / "pilot.json")
    chosen_skills = skills or select_pilot_skills(store.development_support(pilot_fold))
    protocol = {
        "skills": chosen_skills,
        "num_fits": list(num_fits),
        "seeds": list(seeds),
        "pilot_fold": pilot_fold,
    }
    progress_path = output / "pilot_progress.json"
    if progress_path.exists():
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        if progress.get("protocol") != protocol:
            raise ValueError("Existing pilot checkpoint uses a different protocol")
    else:
        progress = {"protocol": protocol, "completed": {}}
        _atomic_json(progress_path, progress)
    candidate_runs = []
    total_jobs = len(num_fits) * len(seeds) * len(chosen_skills)
    completed_jobs = len(progress["completed"])
    for count in num_fits:
        for seed in seeds:
            predictions = []
            skill_runs = []
            for skill in chosen_skills:
                key = f"{count}|{seed}|{skill}"
                saved = progress["completed"].get(key)
                shard = output / "progress" / str(count) / str(seed) / f"{_slug(skill)}.parquet"
                if saved:
                    scored = _read_parquet(shard)
                    skill_run = saved["skill_run"]
                    print(f"Pilot resumed {completed_jobs}/{total_jobs}: num_fits={count}, seed={seed}, skill={skill}", flush=True)
                else:
                    data = store.load_development_skill(skill)
                    train = data[data.fold != pilot_fold].copy()
                    validation = data[data.fold == pilot_fold].copy()
                    if train.empty or validation.empty:
                        raise RuntimeError(f"Pilot skill {skill} lacks train or validation rows")
                    # The first initialization is shared by 1/5/10 for this skill and seed.
                    fit_seed = _seed(seed, skill, "pilot")
                    started = time.perf_counter()
                    model = fit_skill(train, skill, count, fit_seed)
                    scored = _join_prediction(validation, model)
                    duration = time.perf_counter() - started
                    skill_run = {
                        "skill": skill,
                        "train_rows": len(train),
                        "validation_rows": len(validation),
                        "fit_seed": fit_seed,
                        "wall_seconds": duration,
                        "peak_rss_bytes": _peak_rss(),
                        "training_likelihood": None,
                        "training_likelihood_note": "not exposed by public pyBKT Model.fit API",
                        "coefficients": _coefs(model, skill),
                        "validation_metrics": score_predictions(scored, {skill: train.user_id.nunique()})["overall"]["metrics"],
                    }
                    _write_shard(scored, shard, train.user_id.nunique())
                    progress["completed"][key] = {"skill_run": skill_run, "shard": str(shard.relative_to(output))}
                    _atomic_json(progress_path, progress)
                    completed_jobs += 1
                    print(f"Pilot progress {completed_jobs}/{total_jobs}: num_fits={count}, seed={seed}, skill={skill}, {duration:.2f}s", flush=True)
                skill_runs.append(skill_run)
                predictions.append(scored)
            pooled = pd.concat(predictions, ignore_index=True)
            support_map = {run["skill"]: int(run["train_rows"] > 0) for run in skill_runs}
            pooled_metrics = score_predictions(pooled, support_map)["overall"]["metrics"]
            candidate_runs.append({
                "num_fits": count,
                "seed": seed,
                "pooled_validation_metrics": pooled_metrics,
                "total_wall_seconds": sum(run["wall_seconds"] for run in skill_runs),
                "skills": skill_runs,
            })
    grouped = {}
    for count in num_fits:
        rows = [run for run in candidate_runs if run["num_fits"] == count]
        losses = [row["pooled_validation_metrics"]["log_loss"] for row in rows]
        grouped[count] = {
            "mean_log_loss": statistics.mean(losses),
            "sd_log_loss": statistics.stdev(losses) if len(losses) > 1 else 0.0,
            "mean_wall_seconds": statistics.mean(row["total_wall_seconds"] for row in rows),
        }
    best = min(item["mean_log_loss"] for item in grouped.values())
    close = [count for count, item in grouped.items() if item["mean_log_loss"] <= best + 0.002]
    best_sd = min(grouped[count]["sd_log_loss"] for count in close)
    stable = [count for count in close if grouped[count]["sd_log_loss"] <= best_sd + 0.005]
    selected = min(stable, key=lambda count: (grouped[count]["mean_wall_seconds"], count))
    result = {
        "runtime": verify_runtime(),
        "pilot_fold": pilot_fold,
        "selected_skills": chosen_skills,
        "num_fits_candidates": list(num_fits),
        "seeds": list(seeds),
        "selection_rule": "within 0.002 mean log loss of best; within 0.005 seed SD of most stable; then fastest mean runtime and smaller num_fits",
        "candidate_summary": {str(key): value for key, value in grouped.items()},
        "selected_num_fits": selected,
        "runs": candidate_runs,
    }
    _atomic_json(output / "pilot.json", result)
    return result


def run_cv(store, output_dir: str | Path, *, skills: list[str] | None = None, num_fits: int, seed: int = 42) -> dict:
    output = Path(output_dir)
    if (output / "cv.json").exists():
        raise FileExistsError(output / "cv.json")
    output.mkdir(parents=True, exist_ok=True)
    selected = skills or store.development_support().exercise.tolist()
    protocol = {"skills": selected, "num_fits": num_fits, "seed": seed, "folds": 5}
    progress_path = output / "cv_progress.json"
    if progress_path.exists():
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        if progress.get("protocol") != protocol:
            raise ValueError("Existing CV checkpoint uses a different protocol")
    else:
        progress = {"protocol": protocol, "completed": {}}
        _atomic_json(progress_path, progress)
    fit_log = []
    total_jobs = len(selected) * 5
    for skill in selected:
        # Avoid reloading a skill's full interaction data after interruption when
        # every fold shard and checkpoint record for that skill are already durable.
        checkpointed = []
        for fold in range(5):
            key = f"{skill}|{fold}"
            shard = output / f"fold={fold}" / f"{_slug(skill)}.parquet"
            saved = progress["completed"].get(key)
            checkpointed.append(bool(saved and shard.is_file()))
        if all(checkpointed):
            fit_log.extend(progress["completed"][f"{skill}|{fold}"] for fold in range(5))
            continue
        data = store.load_development_skill(skill)
        for fold in range(5):
            train = data[data.fold != fold].copy()
            validation = data[data.fold == fold].copy()
            if validation.empty:
                continue
            support = train.user_id.nunique()
            key = f"{skill}|{fold}"
            shard = output / f"fold={fold}" / f"{_slug(skill)}.parquet"
            saved = progress["completed"].get(key)
            if saved and shard.is_file():
                record = saved
                print(f"CV resumed {len(progress['completed'])}/{total_jobs}: skill={skill}, fold={fold}", flush=True)
            else:
                fit_seed = _seed(seed, skill, f"cv-{fold}-{num_fits}")
                started = time.perf_counter()
                model = fit_skill(train, skill, num_fits, fit_seed) if support else None
                predicted = _join_prediction(validation, model)
                _write_shard(predicted, shard, support)
                record = {
                    "skill": skill, "fold": fold, "fit_seed": fit_seed,
                    "train_students": support, "validation_rows": len(validation),
                    "wall_seconds": time.perf_counter() - started,
                    "peak_rss_bytes": _peak_rss(),
                    "coefficients": _coefs(model, skill) if model else None,
                }
                progress["completed"][key] = record
                _atomic_json(progress_path, progress)
                print(f"CV progress {len(progress['completed'])}/{total_jobs}: skill={skill}, fold={fold}, {record['wall_seconds']:.2f}s", flush=True)
            fit_log.append(record)
    fold_results = []
    for fold in range(5):
        fold_results.append(score_prediction_shards(output / f"fold={fold}" / "*.parquet"))
    names = ("auc", "log_loss", "brier", "ece", "accuracy")
    aggregate = {}
    for name in names:
        values = [fold["overall"]["metrics"][name] for fold in fold_results]
        available = [value for value in values if value is not None]
        aggregate[name] = {
            "mean": statistics.mean(available) if available else None,
            "sd": statistics.stdev(available) if len(available) > 1 else None,
            "defined_folds": len(available),
        }
    result = {
        "runtime": verify_runtime(), "num_fits": num_fits, "base_seed": seed,
        "folds": fold_results, "aggregate": aggregate, "fit_log": fit_log,
    }
    _json(output / "cv.json", result)
    return result


def run_final_fit(store, output_dir: str | Path, *, skills: list[str] | None = None, num_fits: int, seed: int = 42) -> dict:
    output = Path(output_dir)
    if (output / "final.json").exists():
        raise FileExistsError(output / "final.json")
    models = output / "models"
    models.mkdir(parents=True, exist_ok=True)
    selected = skills or store.development_support().exercise.tolist()
    fits = []
    for skill in selected:
        data = store.load_development_skill(skill)
        fit_seed = _seed(seed, skill, f"final-{num_fits}")
        started = time.perf_counter()
        model = fit_skill(data, skill, num_fits, fit_seed)
        filename = f"{_slug(skill)}.pkl"
        model.save(str(models / filename))
        fits.append({
            "skill": skill, "model_file": filename, "fit_seed": fit_seed,
            "train_students": data.user_id.nunique(), "train_rows": len(data),
            "wall_seconds": time.perf_counter() - started,
            "peak_rss_bytes": _peak_rss(), "coefficients": _coefs(model, skill),
        })
    result = {"runtime": verify_runtime(), "num_fits": num_fits, "base_seed": seed, "fits": fits}
    _json(output / "final.json", result)
    return result


def run_test_once(store, final_dir: str | Path, output_dir: str | Path) -> dict:
    final = Path(final_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    marker = output / "holdout_started.marker"
    with marker.open("x", encoding="utf-8") as handle:
        handle.write("Test evaluation started; never use this holdout for tuning.\n")
    fits = {row["skill"]: row for row in json.loads((final / "final.json").read_text(encoding="utf-8"))["fits"]}
    for skill in store.test_skills():
        data = store.load_test_skill(skill)
        record = fits.get(skill)
        if record is None:
            model = None
            support = 0
        else:
            model = Model(seed=record["fit_seed"], parallel=False)
            model.load(str(final / "models" / record["model_file"]))
            support = record["train_students"]
        predicted = _join_prediction(data, model)
        _write_shard(predicted, output / "predictions" / f"{_slug(skill)}.parquet", support)
    result = score_prediction_shards(output / "predictions" / "*.parquet")
    _json(output / "test.json", result)
    return result
