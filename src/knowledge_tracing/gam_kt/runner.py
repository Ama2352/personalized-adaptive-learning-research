"""Development-only GAM-KT pilot and five-fold CV orchestration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform
import statistics
import time

import duckdb
import numpy as np
import pandas as pd
import psutil
import sklearn

from .data import build_problem_type_sidecar, verify_problem_type_mapping
from .difficulty import fit_difficulty_from_frozen_split
from .evaluation import score_frame
from .model import build_model
from .replay import predict_then_update
from .splits import validate_frozen_assignments


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CANONICAL = PROJECT_ROOT / "artifacts/bkt_baseline/derived/canonical"
ASSIGNMENTS = PROJECT_ROOT / "artifacts/bkt_baseline/splits/assignments.parquet"
SPLIT_MANIFEST = PROJECT_ROOT / "artifacts/bkt_baseline/splits/manifest.json"
CANONICAL_MANIFEST = PROJECT_ROOT / "artifacts/bkt_baseline/derived/manifest.json"
RAW_CSV = PROJECT_ROOT / "dataset/junyi_ProblemLog_original.csv"
EXERCISE_CSV = PROJECT_ROOT / "dataset/junyi_Exercise_table.csv"
LINEAGE = PROJECT_ROOT / "artifacts/bkt_baseline/derived/duplicate_lineage.parquet"
SIDECAR_DIR = PROJECT_ROOT / "artifacts/gam_kt/derived/source_map"
BKT_CV = PROJECT_ROOT / "experiments/bkt_baseline/results/wsl_cpp/cv_cpp/cv"
RIVF_ROOT = PROJECT_ROOT / "drive-download-20261018T084013Z-1-001/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20"
RIVF_ZIP = PROJECT_ROOT / "drive-download-20261018T084013Z-1-001/rivf2026_gam_kt_artifact_v20.zip"

MODEL_CELL_SHA256 = "5fc0adbf8fcb454b73bbdd3294bb20e17c2a08ec9eb496b7383677f38b04a5fc"
BASE_SEED = 42
PILOT_SEED = 4217
BATCH_USERS = 500


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json(path: Path, value: dict) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")
    temp.replace(path)


def _peak_rss() -> int:
    process = psutil.Process()
    info = process.memory_info()
    return int(getattr(info, "peak_wset", info.rss))


def _provenance() -> dict:
    notebook = RIVF_ROOT / "source/junyi_cycle_corrected_ablation_confirmation.ipynb"
    builder = RIVF_ROOT / "source/build_junyi_cycle_corrected_confirmation.py"
    return {
        "original_artifact_zip": str(RIVF_ZIP),
        "original_artifact_zip_sha256": _sha256(RIVF_ZIP),
        "original_junyi_notebook": str(notebook),
        "original_junyi_notebook_sha256": _sha256(notebook),
        "original_junyi_builder": str(builder),
        "original_junyi_builder_sha256": _sha256(builder),
        "model_cell_index": 11,
        "model_cell_sha256": MODEL_CELL_SHA256,
        "integration_source_sha256": {
            str(path.relative_to(PROJECT_ROOT)): _sha256(path)
            for path in sorted((PROJECT_ROOT / "src/knowledge_tracing/gam_kt").glob("*.py"))
        },
        "integration_note": "Verbatim graph-free Junyi model definitions; orchestration/data adapters only.",
    }


def _runtime_manifest() -> dict:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "duckdb": duckdb.__version__,
        "scikit_learn": sklearn.__version__,
        "psutil": psutil.__version__,
    }


def _resource_preflight() -> dict:
    import shutil

    return {
        "available_ram_bytes": int(psutil.virtual_memory().available),
        "disk_free_bytes": int(shutil.disk_usage(PROJECT_ROOT).free),
    }


def load_metadata(path: Path = EXERCISE_CSV) -> tuple[dict[str, str], dict[str, str], dict]:
    table = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")
    required = {"name", "topic", "area"}
    if not required <= set(table.columns):
        raise ValueError(f"Junyi Exercise table lacks columns: {sorted(required - set(table.columns))}")
    duplicated_names = int(table.name.duplicated(keep="last").sum())
    topics, areas = {}, {}
    # Match source iteration semantics: later duplicate rows replace earlier rows.
    for row in table.itertuples(index=False):
        name = str(row.name)
        if name:
            topics[name] = str(row.topic)
            areas[name] = str(row.area)
    return topics, areas, {
        "exercise_metadata_rows": int(len(table)),
        "exercise_metadata_unique_names": int(len(topics)),
        "duplicate_name_rows_overwritten": duplicated_names,
        "mapped_exercises_with_topic": sum(bool(x) for x in topics.values()),
        "mapped_exercises_with_area": sum(bool(x) for x in areas.values()),
        "missing_values_follow_original_source_fallback": "unknown_topic/unknown_area only when exercise absent from maps; empty CSV metadata remains empty string",
    }


def _validate_local_inputs() -> tuple[pd.DataFrame, dict]:
    assignments = duckdb.connect()
    try:
        frame = assignments.execute(f"SELECT * FROM read_parquet('{str(ASSIGNMENTS).replace(chr(39), chr(39)*2)}')").df()
    finally:
        assignments.close()
    expected = json.loads(SPLIT_MANIFEST.read_text(encoding="utf-8"))
    validate_frozen_assignments(frame, expected_students=expected["total_students"])
    observed = {
        "total_students": len(frame),
        "development_students": int((frame.partition == "development").sum()),
        "test_students": int((frame.partition == "test").sum()),
        "development_fold_students": {str(f): int(((frame.partition == "development") & (frame.fold == f)).sum()) for f in range(5)},
    }
    if any(observed[key] != expected[key] for key in observed):
        raise ValueError("Frozen BKT assignment manifest does not match assignment Parquet")
    return frame, expected


def prepare_source_mapping(*, chunk_rows: int = 100_000) -> dict:
    assignments, split = _validate_local_inputs()
    if not SIDECAR_DIR.exists():
        build = build_problem_type_sidecar(RAW_CSV, SIDECAR_DIR, assignments_parquet=ASSIGNMENTS, chunk_rows=chunk_rows)
    else:
        sidecar_manifest = SIDECAR_DIR / "sidecar_manifest.json"
        sidecar = SIDECAR_DIR / "source_sidecar.parquet"
        if not sidecar_manifest.is_file() or not sidecar.is_file():
            raise FileExistsError(f"Incomplete existing source map: {SIDECAR_DIR}")
        build = json.loads(sidecar_manifest.read_text(encoding="utf-8"))
        if build.get("scope") != "development only":
            raise ValueError("Existing source map is not Development-only")
    verified = verify_problem_type_mapping(SIDECAR_DIR, CANONICAL, LINEAGE, ASSIGNMENTS)
    canonical_manifest = json.loads(CANONICAL_MANIFEST.read_text(encoding="utf-8"))
    if verified["canonical_rows"] != _development_rows():
        raise ValueError("Development row count differs from the canonical/frozen split join")
    result = {
        "source_mapping": build,
        "verification": verified,
        "canonical_sha256": _sha256(CANONICAL_MANIFEST),
        "raw_problem_log_sha256": canonical_manifest["input_sha256"],
        "assignments_sha256": _sha256(ASSIGNMENTS),
        "split_manifest_sha256": _sha256(SPLIT_MANIFEST),
        "holdout_interactions_used": False,
    }
    dest = PROJECT_ROOT / "artifacts/gam_kt/derived/source_map_verification.json"
    _json(dest, result)
    return result


def _development_rows() -> int:
    con = duckdb.connect()
    try:
        canonical = str(CANONICAL / "**" / "*.parquet").replace("'", "''")
        assignments = str(ASSIGNMENTS).replace("'", "''")
        return int(con.execute(
            f"SELECT COUNT(*) FROM read_parquet('{canonical}', hive_partitioning=true) c "
            f"JOIN read_parquet('{assignments}') a USING(user_id) WHERE a.partition='development'"
        ).fetchone()[0])
    finally:
        con.close()


def _timestamp_unit() -> str:
    con = duckdb.connect()
    try:
        canonical = str(CANONICAL / "**" / "*.parquet").replace("'", "''")
        assignments = str(ASSIGNMENTS).replace("'", "''")
        median = float(con.execute(
            f"SELECT quantile_cont(ABS(c.time_done),0.5) FROM read_parquet('{canonical}', hive_partitioning=true) c "
            f"JOIN read_parquet('{assignments}') a USING(user_id) WHERE a.partition='development'"
        ).fetchone()[0])
    finally:
        con.close()
    if median > 1e14:
        return "us"
    if median > 1e11:
        return "ms"
    if median > 1e9:
        return "s"
    return "ns"


def _pilot_users(assignments: pd.DataFrame, *, maximum: int = 2_000) -> list[str]:
    candidates = assignments[(assignments.partition == "development") & (assignments.fold == 0)].user_id.astype(str).tolist()
    ranked = sorted(candidates, key=lambda user: (hashlib.sha256(f"gam-kt-pilot-v1|{PILOT_SEED}|{user}".encode()).digest(), user))
    return ranked[:maximum]


def _user_frame(con: duckdb.DuckDBPyConnection, fold: int, users: list[str] | None = None):
    canonical = str(CANONICAL / "**" / "*.parquet").replace("'", "''")
    assignments = str(ASSIGNMENTS).replace("'", "''")
    sidecar = str(SIDECAR_DIR / "source_sidecar.parquet").replace("'", "''")
    filter_users = ""
    if users is not None:
        if not users:
            raise ValueError("Pilot cohort is empty")
        con.register("pilot_cohort", pd.DataFrame({"user_id": users}))
        filter_users = "JOIN pilot_cohort p USING(user_id)"
    sql = (
        f"SELECT c.user_id, c.exercise, c.time_done, c.source_row, c.correct, c.suggested, s.problem_type "
        f"FROM read_parquet('{canonical}', hive_partitioning=true) c "
        f"JOIN read_parquet('{assignments}') a USING(user_id) "
        f"JOIN read_parquet('{sidecar}') s USING(source_row) {filter_users} "
        "WHERE a.partition='development' AND a.fold=? "
        "ORDER BY c.user_id, c.time_done, c.source_row"
    )
    return con.execute(sql, [int(fold)])


def _write_prediction_shard(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".parquet.tmp")
    con = duckdb.connect()
    try:
        con.register("predictions", frame)
        con.execute(f"COPY predictions TO '{str(temp).replace(chr(39), chr(39)*2)}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    finally:
        con.close()
    temp.replace(path)


def _read_checkpoint(path: Path, identity: dict) -> dict:
    if not path.exists():
        return {"identity": identity, "last_user": None, "completed_users": 0, "next_shard": 0, "elapsed_seconds": 0.0, "shards": {}}
    checkpoint = json.loads(path.read_text(encoding="utf-8"))
    if checkpoint.get("identity") != identity:
        raise ValueError(f"Incompatible GAM-KT checkpoint: {path}")
    for relative, expected_hash in checkpoint.get("shards", {}).items():
        shard = path.parent / relative
        if not shard.is_file() or _sha256(shard) != expected_hash:
            raise ValueError(f"Missing or modified GAM-KT checkpoint shard: {shard}")
    return checkpoint


def _replay(
    *, fold: int, output_dir: Path, topics: dict[str, str], areas: dict[str, str],
    difficulty: dict[str, float], global_difficulty: float, train_support: dict[str, int],
    timestamp_unit: str, users: list[str] | None = None, run_identity: dict,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / "checkpoint.json"
    identity = {**run_identity, "fold": fold, "sample_users_sha256": hashlib.sha256("\n".join(users).encode()).hexdigest() if users is not None else None}
    checkpoint = _read_checkpoint(checkpoint_path, identity)
    con = duckdb.connect()
    con.execute("SET memory_limit='2GB'")
    scratch = output_dir / "duckdb_tmp"
    scratch.mkdir(exist_ok=True)
    con.execute(f"SET temp_directory='{str(scratch).replace(chr(39), chr(39)*2)}'")
    result = _user_frame(con, fold, users)
    batch_users = 0
    output_rows: list[dict] = []
    current_user = None
    current_predictions: list[dict] = []
    model = None
    started = time.perf_counter()
    checkpoint_time = started
    users_started = checkpoint["completed_users"]
    last_user = checkpoint["last_user"]
    shard_index = checkpoint["next_shard"]
    total_predictions = 0

    def commit_user() -> None:
        nonlocal output_rows, batch_users, last_user, shard_index, total_predictions, checkpoint_time
        if not current_predictions:
            return
        output_rows.extend(current_predictions)
        batch_users += 1
        last_user = current_user
        total_predictions += len(current_predictions)
        if batch_users >= BATCH_USERS:
            shard = output_dir / f"part-{shard_index:06d}.parquet"
            _write_prediction_shard(pd.DataFrame(output_rows), shard)
            checkpoint.setdefault("shards", {})[shard.name] = _sha256(shard)
            shard_index += 1
            output_rows = []
            batch_users = 0
            checkpoint.update({"last_user": last_user, "completed_users": checkpoint["completed_users"] + BATCH_USERS, "next_shard": shard_index})
            checkpoint["elapsed_seconds"] += time.perf_counter() - checkpoint_time
            checkpoint_time = time.perf_counter()
            _json(checkpoint_path, checkpoint)
            print(f"GAM-KT fold {fold}: {checkpoint['completed_users']} students completed", flush=True)

    try:
        if last_user is not None:
            # Keep the same student-key lexical ordering as SQL's ORDER BY.
            result = _user_frame_after(con, fold, last_user, users)
        while True:
            frame = result.fetch_df_chunk(1)
            if frame is None or frame.empty:
                break
            frame["timestamp"] = pd.to_datetime(frame.time_done, unit=timestamp_unit, utc=True)
            for row in frame.itertuples(index=False):
                user = str(row.user_id)
                if current_user != user:
                    commit_user()
                    current_user = user
                    current_predictions = []
                    model = build_model(topics, areas)
                exercise = str(row.exercise)
                prediction = predict_then_update(
                    model, exercise, str(row.problem_type), difficulty.get(exercise, global_difficulty),
                    row.timestamp, int(row.correct),
                )
                fallback = exercise not in train_support
                states = model.states[exercise]
                numeric_state = np.concatenate((states.memory.astype(np.float64), np.array([
                    states.theta, states.pi_task, states.pi_time,
                ])))
                if not np.isfinite(numeric_state).all():
                    raise FloatingPointError(f"Non-finite GAM-KT state at source_row={row.source_row}")
                current_predictions.append({
                    "source_row": int(row.source_row), "user_id": user, "exercise": exercise,
                    "correct": int(row.correct), "suggested": int(row.suggested),
                    "prediction": prediction, "is_fallback": fallback,
                    "train_support_students": int(train_support.get(exercise, 0)),
                })
        commit_user()
        if output_rows:
            shard = output_dir / f"part-{shard_index:06d}.parquet"
            _write_prediction_shard(pd.DataFrame(output_rows), shard)
            checkpoint.setdefault("shards", {})[shard.name] = _sha256(shard)
            shard_index += 1
            checkpoint.update({"last_user": last_user, "completed_users": checkpoint["completed_users"] + batch_users, "next_shard": shard_index})
            checkpoint["elapsed_seconds"] += time.perf_counter() - checkpoint_time
            _json(checkpoint_path, checkpoint)
        return {
            "fold": fold,
            "pilot_sample": users is not None,
            "new_users_processed": checkpoint["completed_users"] - users_started,
            "new_prediction_rows": total_predictions,
            "total_completed_users": checkpoint["completed_users"],
            "elapsed_seconds": time.perf_counter() - started,
            "cumulative_elapsed_seconds": checkpoint["elapsed_seconds"],
            "throughput_rows_per_second": total_predictions / max(1e-9, time.perf_counter() - started),
            "peak_rss_bytes": _peak_rss(),
            "last_user": checkpoint["last_user"],
            "output_dir": str(output_dir.resolve()),
        }
    finally:
        con.close()


def _user_frame_after(con, fold: int, last_user: str, users: list[str] | None):
    canonical = str(CANONICAL / "**" / "*.parquet").replace("'", "''")
    assignments = str(ASSIGNMENTS).replace("'", "''")
    sidecar = str(SIDECAR_DIR / "source_sidecar.parquet").replace("'", "''")
    filter_users = ""
    if users is not None:
        con.register("pilot_cohort", pd.DataFrame({"user_id": users}))
        filter_users = "JOIN pilot_cohort p USING(user_id)"
    sql = (
        f"SELECT c.user_id, c.exercise, c.time_done, c.source_row, c.correct, c.suggested, s.problem_type "
        f"FROM read_parquet('{canonical}', hive_partitioning=true) c "
        f"JOIN read_parquet('{assignments}') a USING(user_id) "
        f"JOIN read_parquet('{sidecar}') s USING(source_row) {filter_users} "
        "WHERE a.partition='development' AND a.fold=? AND c.user_id>? "
        "ORDER BY c.user_id, c.time_done, c.source_row"
    )
    return con.execute(sql, [int(fold), last_user])


def _load_difficulty(path: Path) -> tuple[dict[str, float], dict[str, int]]:
    con = duckdb.connect()
    try:
        frame = con.execute(f"SELECT * FROM read_parquet('{str(path).replace(chr(39), chr(39)*2)}')").df()
    finally:
        con.close()
    if not np.isfinite(frame.difficulty).all() or (frame.train_rows <= 0).any():
        raise ValueError("Invalid train-fitted difficulty artifact")
    return frame.set_index("exercise").difficulty.to_dict(), frame.set_index("exercise").train_students.astype(int).to_dict()


def _pilot_common_bkt(prediction_dir: Path, fold: int, sample_users: list[str] | None) -> dict:
    bkt_glob = str(BKT_CV / f"fold={fold}" / "*.parquet").replace("'", "''")
    gam_glob = str(prediction_dir / "part-*.parquet").replace("'", "''")
    con = duckdb.connect()
    try:
        where = "WHERE b.train_skill_students>0"
        if sample_users is not None:
            con.register("pilot_cohort", pd.DataFrame({"user_id": sample_users}))
            where += " AND g.user_id IN (SELECT user_id FROM pilot_cohort)"
        frame = con.execute(
            f"SELECT g.source_row,g.user_id,g.exercise,g.correct,g.suggested,g.train_support_students,b.train_skill_students, "
            f"g.prediction AS gam_prediction, "
            f"b.prediction AS bkt_prediction FROM read_parquet('{gam_glob}') g "
            f"JOIN read_parquet('{bkt_glob}') b USING(source_row) {where}"
        ).df()
    finally:
        con.close()
    if frame.source_row.duplicated().any():
        raise ValueError("Common-row join is not one-to-one")
    if not frame.train_support_students.equals(frame.train_skill_students):
        raise ValueError("GAM-KT and frozen BKT fold training support counts differ")
    gam = frame.rename(columns={"gam_prediction": "prediction", "is_fallback": "is_fallback"})
    bkt = frame.rename(columns={"bkt_prediction": "prediction"})
    # Common comparison is restricted to BKT-fitted rows; GAM's predictions remain native.
    return {"rows": int(len(frame)), "gam": score_frame(gam.assign(is_fallback=False)), "bkt": score_frame(bkt.assign(is_fallback=False))}


def run_pilot(output_dir: str | Path, *, max_users: int = 2_000, chunk_rows: int = 100_000) -> dict:
    output = Path(output_dir).resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Pilot output is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    mapping_report = prepare_source_mapping(chunk_rows=chunk_rows)
    assignments, split = _validate_local_inputs()
    topics, areas, metadata_report = load_metadata()
    users = _pilot_users(assignments, maximum=max_users)
    unit = _timestamp_unit()
    difficulty_path = output / "difficulty_fold0.parquet"
    difficulty_info = fit_difficulty_from_frozen_split(CANONICAL, ASSIGNMENTS, 0, difficulty_path)
    difficulty, support = _load_difficulty(difficulty_path)
    identity = {
        "protocol": "frozen BKT Development fold 0; deterministic GAM pilot student sample",
        "seed": PILOT_SEED,
        "num_users": len(users),
        "canonical_manifest_sha256": _sha256(CANONICAL_MANIFEST),
        "assignments_sha256": _sha256(ASSIGNMENTS),
        "sidecar_sha256": _sha256(SIDECAR_DIR / "source_sidecar.parquet"),
        "source_model_cell_sha256": MODEL_CELL_SHA256,
        "exercise_table_sha256": _sha256(EXERCISE_CSV),
        "timestamp_unit": unit,
        "algorithm": "original graph-free Junyi GAM-KT",
        "provenance": _provenance(),
        "runtime": _runtime_manifest(),
    }
    replay = _replay(
        fold=0, output_dir=output / "predictions", topics=topics, areas=areas,
        difficulty=difficulty, global_difficulty=difficulty_info["global_difficulty"],
        train_support=support, timestamp_unit=unit, users=users, run_identity=identity,
    )
    metrics = _score_prediction_dir(output / "predictions")
    common = _pilot_common_bkt(output / "predictions", 0, users)
    result = {
        "status": "completed",
        "scope": "Development only; fold 0 validation; no Holdout Test observations used",
        "protocol": identity,
        "assignment_manifest": split,
        "mapping_verification": mapping_report["verification"],
        "metadata": metadata_report,
        "timestamp_unit_inferred_from_development_only": unit,
        "difficulty_fit": difficulty_info,
        "replay": replay,
        "native_metrics": metrics,
        "common_row_comparison_with_bkt_fold0": common,
        "estimated_full_cv_seconds_from_observed_throughput": _development_rows() / replay["throughput_rows_per_second"],
        "estimate_basis": "Development fold assignments partition Development students; each Development interaction is validation data exactly once across five folds, so replay rows are not multiplied by five",
        "estimate_limitation": "linear replay-only extrapolation from deterministic fold-0 sample; excludes per-fold difficulty aggregation, I/O, common-row scoring, and reporting overhead",
        "holdout_test_used": False,
        "resource_preflight": _resource_preflight(),
    }
    _json(output / "pilot.json", result)
    _write_vi_report(output / "report_vi.md", result, kind="pilot")
    return result


def _score_prediction_dir(directory: Path) -> dict:
    con = duckdb.connect()
    try:
        glob = str(directory / "part-*.parquet").replace("'", "''")
        frame = con.execute(f"SELECT * FROM read_parquet('{glob}')").df()
    finally:
        con.close()
    return score_frame(frame)


def _aggregate_cv(folds: list[dict]) -> dict:
    metrics = ("auc", "log_loss", "brier", "ece", "accuracy")
    sections = {
        "native": lambda fold: fold["metrics"]["native"],
        "supported": lambda fold: fold["metrics"]["supported"],
        "suggested": lambda fold: fold["metrics"]["suggested"],
        "common_row_gam": lambda fold: fold["common_row_comparison"]["gam"]["native"],
        "common_row_bkt": lambda fold: fold["common_row_comparison"]["bkt"]["native"],
    }
    aggregate = {}
    for section, getter in sections.items():
        aggregate[section] = {}
        groups = ("suggested", "non_suggested") if section == "suggested" else (None,)
        for group in groups:
            group_key = group if group is not None else "overall"
            aggregate[section][group_key] = {}
            aggregate_metric = aggregate[section][group_key]
            for metric in metrics:
                values = []
                for fold in folds:
                    record = getter(fold)
                    if group is not None:
                        record = record[group]
                    value = record["metrics"][metric]
                    if value is not None:
                        values.append(value)
                aggregate_metric[metric] = {
                    "mean": statistics.mean(values) if values else None,
                    "sample_sd": statistics.stdev(values) if len(values) > 1 else (0.0 if values else None),
                    "defined_folds": len(values),
                }
    aggregate["coverage"] = {
        "total_rows": sum(fold["metrics"]["coverage"]["total_rows"] for fold in folds),
        "predicted_rows": sum(fold["metrics"]["coverage"]["predicted_rows"] for fold in folds),
        "fallback_rows": sum(fold["metrics"]["coverage"]["fallback_rows"] for fold in folds),
        "unpredicted_rows": sum(fold["metrics"]["coverage"]["unpredicted_rows"] for fold in folds),
    }
    aggregate["coverage"]["prediction_coverage"] = aggregate["coverage"]["predicted_rows"] / aggregate["coverage"]["total_rows"]
    aggregate["coverage"]["supported_row_coverage"] = (aggregate["coverage"]["predicted_rows"] - aggregate["coverage"]["fallback_rows"]) / aggregate["coverage"]["total_rows"]
    return aggregate


def run_cv(output_dir: str | Path, *, resume: bool = True, chunk_rows: int = 100_000) -> dict:
    output = Path(output_dir).resolve()
    if not resume and output.exists() and any(output.iterdir()):
        raise FileExistsError(f"CV output is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    existing = output / "cv.json"
    if existing.exists():
        raise FileExistsError(f"CV summary already exists: {existing}")
    mapping = prepare_source_mapping(chunk_rows=chunk_rows)
    assignments, split = _validate_local_inputs()
    if set(assignments.loc[assignments.partition == "development", "fold"].unique()) != set(range(5)):
        raise ValueError("Frozen split does not contain exactly five Development folds")
    topics, areas, metadata = load_metadata()
    timestamp_unit = _timestamp_unit()
    run_identity = {
        "protocol": "frozen global user assignments; 5-fold Development CV; chronological online state per user",
        "base_seed": BASE_SEED,
        "model_cell_sha256": MODEL_CELL_SHA256,
        "canonical_manifest_sha256": _sha256(CANONICAL_MANIFEST),
        "assignments_sha256": _sha256(ASSIGNMENTS),
        "source_sidecar_sha256": _sha256(SIDECAR_DIR / "source_sidecar.parquet"),
        "exercise_table_sha256": _sha256(EXERCISE_CSV),
        "timestamp_unit": timestamp_unit,
        "holdout_test_used": False,
        "provenance": _provenance(),
        "runtime": _runtime_manifest(),
    }
    folds = []
    started = time.perf_counter()
    for fold in range(5):
        fold_dir = output / f"fold={fold}"
        difficulty_path = fold_dir / "difficulty.parquet"
        info_path = fold_dir / "difficulty.json"
        if not info_path.exists():
            info = fit_difficulty_from_frozen_split(CANONICAL, ASSIGNMENTS, fold, difficulty_path)
            _json(info_path, info)
        else:
            info = json.loads(info_path.read_text(encoding="utf-8"))
            if not difficulty_path.is_file():
                raise ValueError(f"Missing fold difficulty artifact for fold {fold}")
        difficulty, support = _load_difficulty(difficulty_path)
        replay = _replay(
            fold=fold, output_dir=fold_dir / "predictions", topics=topics, areas=areas,
            difficulty=difficulty, global_difficulty=float(info["global_difficulty"]),
            train_support=support, timestamp_unit=timestamp_unit,
            run_identity={**run_identity, "difficulty_sha256": _sha256(difficulty_path)},
        )
        frame = _load_prediction_frame(fold_dir / "predictions")
        metrics = score_frame(frame)
        common = _common_bkt(fold_dir / "predictions", fold)
        folds.append({"fold": fold, "replay": replay, "metrics": metrics, "common_row_comparison": common, "difficulty_fit": info})
        _json(output / f"fold={fold}.json", folds[-1])
    total_seconds = sum(float(fold["replay"]["cumulative_elapsed_seconds"]) for fold in folds)
    result = {
        "status": "completed",
        "protocol": run_identity,
        "assignments": split,
        "source_mapping": mapping["verification"],
        "metadata": metadata,
        "timestamp_unit_inferred_from_development_only": timestamp_unit,
        "folds": folds,
        "aggregate_mean_sample_sd": _aggregate_cv(folds),
        "total_wall_seconds": time.perf_counter() - started,
        "cumulative_replay_seconds_from_checkpoints": total_seconds,
        "peak_rss_bytes": _peak_rss(),
        "holdout_test_used": False,
        "resource_preflight": _resource_preflight(),
    }
    _json(existing, result)
    _write_vi_report(output / "report_vi.md", result, kind="cv")
    return result


def _load_prediction_frame(directory: Path) -> pd.DataFrame:
    con = duckdb.connect()
    try:
        glob = str(directory / "part-*.parquet").replace("'", "''")
        frame = con.execute(f"SELECT * FROM read_parquet('{glob}')").df()
    finally:
        con.close()
    if frame.source_row.duplicated().any():
        raise ValueError("Duplicate source_row in GAM-KT predictions")
    return frame


def _common_bkt(prediction_dir: Path, fold: int) -> dict:
    bkt_glob = str(BKT_CV / f"fold={fold}" / "*.parquet").replace("'", "''")
    gam_glob = str(prediction_dir / "part-*.parquet").replace("'", "''")
    con = duckdb.connect()
    try:
        frame = con.execute(
            f"SELECT g.source_row,g.user_id,g.exercise,g.correct,g.suggested,g.train_support_students,b.train_skill_students, "
            f"g.prediction AS gam_prediction, "
            f"b.prediction AS bkt_prediction FROM read_parquet('{gam_glob}') g "
            f"JOIN read_parquet('{bkt_glob}') b USING(source_row) "
            "WHERE b.train_skill_students>0 ORDER BY g.source_row"
        ).df()
    finally:
        con.close()
    if frame.source_row.duplicated().any():
        raise ValueError("Common-row BKT join is not one-to-one")
    if not frame.train_support_students.equals(frame.train_skill_students):
        raise ValueError(f"GAM-KT and frozen BKT fold {fold} training support counts differ")
    gam = frame.rename(columns={"gam_prediction": "prediction"})
    bkt = frame.rename(columns={"bkt_prediction": "prediction"})
    return {"rows": int(len(frame)), "gam": score_frame(gam.assign(is_fallback=False)), "bkt": score_frame(bkt.assign(is_fallback=False))}


def _write_vi_report(path: Path, result: dict, *, kind: str) -> None:
    if kind == "pilot":
        replay = result["replay"]
        metric = result["native_metrics"]
        content = [
            "# GAM-KT Development pilot",
            "",
            "Pilot dùng fold 0 của Development và cohort học sinh xác định bằng seed cố định. Holdout Test không được truy vấn.",
            "",
            f"- Học sinh: {replay['total_completed_users']}; interactions: {replay['new_prediction_rows']}; throughput: {replay['throughput_rows_per_second']:.1f} dòng/giây.",
            f"- Wall time: {replay['elapsed_seconds']:.1f} giây; peak RSS tiến trình: {replay['peak_rss_bytes']} byte.",
            f"- Ước lượng 5-fold CV: {result['estimated_full_cv_seconds_from_observed_throughput'] / 3600:.2f} giờ (ngoại suy tuyến tính từ pilot).",
            f"- Coverage: {metric['coverage']['predicted_rows']}/{metric['coverage']['total_rows']}; fallback rows: {metric['coverage']['fallback_rows']}; Brier: {metric['native']['metrics']['brier']}; AUC: {metric['native']['metrics']['auc']}.",
            "- Chi tiết, common-row BKT và giới hạn ngoại suy nằm trong `pilot.json`.",
        ]
        correction = result.get("initial_estimate_correction")
        if correction:
            content.append(
                f"- Sửa ước lượng cũ bị nhân 5: mỗi Development interaction được validation đúng một lần. Ngoại suy replay-only là {correction['corrected_hours']:.2f} giờ; full CV đo thực tế {correction['actual_cv_wall_hours']:.2f} giờ."
            )
    else:
        agg = result["aggregate_mean_sample_sd"]
        mapping = result["source_mapping"]
        content = [
            "# GAM-KT 5-fold Development CV", "",
            "Benchmark chạy graph-free Junyi GAM-KT theo frozen BKT Development protocol; Holdout Test không được truy vấn.",
            "",
            f"Canonical Development có {mapping['canonical_rows']:,} interaction. Sidecar chứa {mapping['raw_rows']:,} raw Development records; {mapping['duplicate_rows_verified']:,} duplicate được xác minh bằng lineage. Mỗi canonical row được ghép theo `source_row` và đối chiếu `user_id`, `exercise`, `time_done`, `correct`.",
            f"Assignments frozen: {result['assignments']['development_students']:,} Development users; năm fold disjoint. Timestamp dùng unit `{result['timestamp_unit_inferred_from_development_only']}` và thứ tự `(user_id, time_done, source_row)`.",
            "Difficulty được fit riêng trên bốn fold train (global correctness, smoothing alpha=20); event validation được dự đoán trước, rồi mới update state bằng đáp án hiện tại. State reset giữa users và giữ xuyên exercise trong cùng user.",
            "Graph, graph adaptation và time decay tắt. `suggested` chỉ dùng để phân nhóm.",
            "",
            "## GAM-KT native metrics",
            "",
            "| Metric | Mean ± sample SD |", "|---|---:|"]
        for name, key in (("AUC", "auc"), ("Log Loss", "log_loss"), ("Brier", "brier"), ("ECE", "ece"), ("Accuracy", "accuracy")):
            item = agg["native"]["overall"][key]
            content.append(f"| {name} | {item['mean']} ± {item['sample_sd']} |")
        content.extend(["", "| Nhóm | AUC mean ± SD | Log Loss mean ± SD | Brier mean ± SD | ECE mean ± SD | Accuracy mean ± SD |", "|---|---:|---:|---:|---:|---:|"])
        for group, label in (("suggested", "suggested"), ("non_suggested", "non-suggested")):
            stats = agg["suggested"][group]
            content.append("| " + label + " | " + " | ".join(f"{stats[key]['mean']} ± {stats[key]['sample_sd']}" for key in ("auc", "log_loss", "brier", "ece", "accuracy")) + " |")
        content.extend(["", "| Support theo số user train trong fold | Validation rows | Fallback rows |", "|---|---:|---:|"])
        band_names = ("unseen", "1-9", "10-49", "50-99", "100-999", ">=1000")
        for band in band_names:
            rows = sum(fold["metrics"]["train_support_bands"][band]["rows"] for fold in result["folds"])
            fallback = sum(fold["metrics"]["train_support_bands"][band]["fallback_rows"] for fold in result["folds"])
            content.append(f"| {band} | {rows} | {fallback} |")
        suggested_counts = {}
        for group in ("suggested", "non_suggested"):
            rows = sum(fold["metrics"]["suggested"][group]["rows"] for fold in result["folds"])
            positives = sum(fold["metrics"]["suggested"][group]["metrics"]["positive_count"] for fold in result["folds"])
            suggested_counts[group] = (rows, positives, rows - positives, positives / rows if rows else None)
        content.extend(["", "| Metric | GAM-KT common rows | BKT common rows |", "|---|---:|---:|"])
        for name, key in (("AUC", "auc"), ("Log Loss", "log_loss"), ("Brier", "brier"), ("ECE", "ece"), ("Accuracy", "accuracy")):
            gam = agg["common_row_gam"]["overall"][key]
            bkt = agg["common_row_bkt"]["overall"][key]
            content.append(f"| {name} | {gam['mean']} ± {gam['sample_sd']} | {bkt['mean']} ± {bkt['sample_sd']} |")
        positives = sum(fold["metrics"]["native"]["metrics"]["positive_count"] for fold in result["folds"])
        negatives = sum(fold["metrics"]["native"]["metrics"]["negative_count"] for fold in result["folds"])
        unseen_names = [f"fold {fold['fold']}: {', '.join(fold['metrics']['coverage']['unseen_exercise_names']) or 'không có'}" for fold in result['folds']]
        fold_times = ", ".join(f"fold {fold['fold']} {fold['replay']['cumulative_elapsed_seconds']:.1f}s" for fold in result['folds'])
        content += ["", f"Coverage: native {agg['coverage']['predicted_rows']}/{agg['coverage']['total_rows']}; supported-only {agg['coverage']['supported_rows']}/{agg['coverage']['total_rows']} ({agg['coverage']['supported_row_coverage']:.6%}); global-difficulty fallback {agg['coverage']['fallback_rows']} rows, không tính vào supported-only/common BKT metrics.", f"Native target counts: correct=1 {positives}; correct=0 {negatives}; prevalence={positives / (positives + negatives):.6f}.", f"Suggested: {suggested_counts['suggested'][0]:,} rows, correct=1 prevalence {suggested_counts['suggested'][3]:.6%}; non-suggested: {suggested_counts['non_suggested'][0]:,} rows, prevalence {suggested_counts['non_suggested'][3]:.6%}.", "Unseen exercises theo fold: " + "; ".join(unseen_names) + ".", "", f"Wall time thực tế của lượt chạy: {result['total_wall_seconds']:.1f} giây ({result['total_wall_seconds'] / 3600:.2f} giờ); peak RSS: {result['peak_rss_bytes']} byte. Replay theo fold: {fold_times}. Fold 4 dài hơn nhiều so với các fold khác; nguyên nhân chưa xác định, vì vậy tổng wall-time giữ nguyên số đo thực tế.", "AUC được tính từng fold; metric của nhóm chỉ có một lớp là null. Xem `cv.json` để có exact denominators, per-fold metrics, support-band metrics, common-row outputs, dependency/source hashes và checkpoint."]
        content.append(f"AUC của suggested cần thận trọng: chỉ có {suggested_counts['suggested'][2]} nhãn âm trong {suggested_counts['suggested'][0]:,} dòng trên toàn bộ CV.")
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
