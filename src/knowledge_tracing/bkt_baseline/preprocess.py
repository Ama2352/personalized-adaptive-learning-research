"""Disk-backed, exact-value preprocessing of the Junyi ProblemLog CSV."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

import duckdb
import numpy as np
import pandas as pd
import psutil


ORIGINAL_COLUMNS = [
    "user_id", "exercise", "problem_type", "problem_number", "topic_mode",
    "suggested", "review_mode", "time_done", "time_taken",
    "time_taken_attempts", "correct", "count_attempts", "hint_used",
    "count_hints", "hint_time_taken_list", "earned_proficiency", "points_earned",
]


def _sql_path(path: Path) -> str:
    return "'" + str(path.resolve()).replace("'", "''") + "'"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def preprocess_csv(
    input_csv: str | Path,
    output_dir: str | Path,
    *,
    chunk_size: int = 100_000,
    memory_limit: str = "4GB",
    threads: int = 4,
) -> dict:
    """Write a canonical derived dataset and lineage without editing the CSV."""
    source = Path(input_csv).resolve()
    output = Path(output_dir).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if (output / "canonical").exists() or (output / "manifest.json").exists():
        raise FileExistsError(f"Derived dataset already exists in {output}")
    if chunk_size < 1 or threads < 1:
        raise ValueError("chunk_size and threads must be positive")
    output.mkdir(parents=True, exist_ok=True)
    scratch = output / "duckdb_tmp"
    scratch.mkdir(exist_ok=True)
    stage = output / "stage.duckdb"
    started = time.perf_counter()
    con = duckdb.connect(str(stage))
    con.execute(f"SET memory_limit = '{memory_limit}'")
    con.execute(f"SET threads = {int(threads)}")
    con.execute(f"SET temp_directory = {_sql_path(scratch)}")

    raw_rows = 0
    try:
        reader = pd.read_csv(
            source,
            dtype=str,
            keep_default_na=False,
            chunksize=chunk_size,
            encoding="utf-8",
        )
        for chunk in reader:
            if list(chunk.columns) != ORIGINAL_COLUMNS:
                raise ValueError("Unexpected ProblemLog CSV schema")
            chunk.insert(0, "source_row", np.arange(raw_rows + 1, raw_rows + len(chunk) + 1, dtype=np.int64))
            con.register("chunk_df", chunk)
            if raw_rows == 0:
                con.execute("CREATE TABLE raw AS SELECT * FROM chunk_df LIMIT 0")
            con.execute("INSERT INTO raw SELECT * FROM chunk_df")
            con.unregister("chunk_df")
            raw_rows += len(chunk)
        if raw_rows == 0:
            raise ValueError("Empty ProblemLog CSV")

        partition = ", ".join('"' + col + '"' for col in ORIGINAL_COLUMNS)
        con.execute(
            "CREATE TABLE ranked AS SELECT *, "
            f"MIN(source_row) OVER (PARTITION BY {partition}) AS retained_source_row, "
            f"ROW_NUMBER() OVER (PARTITION BY {partition} ORDER BY source_row) AS duplicate_rank "
            "FROM raw"
        )
        canonical_rows = con.execute("SELECT COUNT(*) FROM ranked WHERE duplicate_rank=1").fetchone()[0]
        bad_rows = con.execute(
            "SELECT COUNT(*) FROM ranked WHERE duplicate_rank=1 AND ("
            "user_id='' OR exercise='' OR TRY_CAST(time_done AS BIGINT) IS NULL "
            "OR lower(correct) NOT IN ('true','false','0','1') "
            "OR lower(suggested) NOT IN ('true','false','0','1'))"
        ).fetchone()[0]
        if bad_rows:
            raise ValueError(f"{bad_rows} canonical rows have invalid required fields")

        con.execute(
            "COPY (SELECT source_row AS duplicate_source_row, "
            "retained_source_row FROM ranked WHERE duplicate_rank>1 "
            "ORDER BY source_row) TO "
            f"{_sql_path(output / 'duplicate_lineage.parquet')} "
            "(FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        con.execute(
            "COPY (SELECT source_row, user_id, exercise, "
            "CAST(time_done AS BIGINT) AS time_done, "
            "CASE lower(correct) WHEN 'true' THEN 1 WHEN '1' THEN 1 ELSE 0 END AS correct, "
            "CASE lower(suggested) WHEN 'true' THEN 1 WHEN '1' THEN 1 ELSE 0 END AS suggested, "
            "ROW_NUMBER() OVER (PARTITION BY user_id, exercise "
            "ORDER BY CAST(time_done AS BIGINT), source_row) AS order_id "
            "FROM ranked WHERE duplicate_rank=1 "
            "ORDER BY exercise, user_id, order_id) TO "
            f"{_sql_path(output / 'canonical')} "
            "(FORMAT PARQUET, PARTITION_BY (exercise), COMPRESSION ZSTD)"
        )
        tie_excess = con.execute(
            "SELECT COALESCE(SUM(n-1),0) FROM ("
            "SELECT COUNT(*) AS n FROM ranked WHERE duplicate_rank=1 "
            "GROUP BY user_id, exercise, time_done HAVING COUNT(*)>1)"
        ).fetchone()[0]
    finally:
        con.close()

    peak = psutil.Process().memory_info()
    manifest = {
        "input_csv": str(source),
        "input_sha256": _sha256(source),
        "raw_rows": raw_rows,
        "canonical_rows": canonical_rows,
        "duplicate_rows_removed": raw_rows - canonical_rows,
        "timestamp_tie_excess_after_dedupe": int(tie_excess),
        "ordering": ["user_id", "exercise", "time_done", "source_row"],
        "elapsed_seconds": time.perf_counter() - started,
        "peak_rss_bytes": getattr(peak, "peak_wset", peak.rss),
        "duckdb_version": duckdb.__version__,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    stage.unlink(missing_ok=True)
    return manifest
