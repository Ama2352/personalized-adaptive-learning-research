"""Source-row mapping between raw Junyi ProblemLog and canonical BKT rows."""

from __future__ import annotations

import json
from pathlib import Path
import shutil

import duckdb
import numpy as np
import pandas as pd

from knowledge_tracing.bkt_baseline.preprocess import ORIGINAL_COLUMNS


def _q(path: str | Path) -> str:
    return "'" + str(Path(path).resolve()).replace("'", "''") + "'"


def _binary(values: pd.Series, name: str) -> pd.Series:
    lowered = values.astype(str).str.strip().str.lower()
    result = lowered.map({"true": 1, "1": 1, "1.0": 1, "false": 0, "0": 0, "0.0": 0})
    if result.isna().any():
        raise ValueError(f"ProblemLog has invalid {name} values")
    return result.astype("int8")


def build_problem_type_sidecar(
    raw_csv: str | Path,
    output_dir: str | Path,
    *,
    assignments_parquet: str | Path | None = None,
    chunk_rows: int = 100_000,
    memory_limit: str = "2GB",
    threads: int = 4,
) -> dict:
    """Stream a compact source-row map, preserving raw row identity for audit."""
    source, output = Path(raw_csv).resolve(), Path(output_dir).resolve()
    destination = output / "source_sidecar.parquet"
    if not source.is_file():
        raise FileNotFoundError(source)
    if destination.exists():
        raise FileExistsError(destination)
    if chunk_rows < 1:
        raise ValueError("chunk_rows must be positive")
    parts = output / "parts"
    scratch = output / "duckdb_tmp"
    parts.mkdir(parents=True, exist_ok=True)
    scratch.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{memory_limit}'")
    con.execute(f"SET threads={int(threads)}")
    con.execute(f"SET temp_directory={_q(scratch)}")
    raw_count = 0
    mapped_count = 0
    development_users = None
    if assignments_parquet is not None:
        assignments = Path(assignments_parquet).resolve()
        if not assignments.is_file():
            raise FileNotFoundError(assignments)
        development_users = set(con.execute(
            f"SELECT user_id FROM read_parquet({_q(assignments)}) WHERE partition='development'"
        ).fetchnumpy()["user_id"].tolist())
    try:
        reader = pd.read_csv(source, dtype=str, keep_default_na=False, chunksize=chunk_rows, encoding="utf-8")
        for part_index, chunk in enumerate(reader):
            if list(chunk.columns) != ORIGINAL_COLUMNS:
                raise ValueError("Unexpected Junyi ProblemLog schema")
            source_rows = np.arange(raw_count + 1, raw_count + len(chunk) + 1, dtype=np.int64)
            raw_count += len(chunk)
            if development_users is not None:
                keep = chunk.user_id.astype(str).isin(development_users).to_numpy()
                chunk = chunk.loc[keep].copy()
                source_rows = source_rows[keep]
            if chunk.empty:
                continue
            frame = pd.DataFrame({
                "source_row": source_rows,
                "user_id": chunk["user_id"].astype(str),
                "exercise": chunk["exercise"].astype(str),
                "time_done": pd.to_numeric(chunk["time_done"], errors="raise").astype("int64"),
                "correct": _binary(chunk["correct"], "correct"),
                "suggested": _binary(chunk["suggested"], "suggested"),
                "problem_type": chunk["problem_type"].where(chunk["problem_type"].ne(""), "unknown_template").astype(str),
            })
            con.register("part_df", frame)
            part_path = parts / f"part-{part_index:05d}.parquet"
            con.execute(f"COPY part_df TO {_q(part_path)} (FORMAT PARQUET, COMPRESSION ZSTD)")
            con.unregister("part_df")
            mapped_count += len(frame)
    finally:
        con.close()
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{memory_limit}'")
    con.execute(f"SET threads={int(threads)}")
    con.execute(f"SET temp_directory={_q(scratch)}")
    try:
        con.execute(f"COPY (SELECT * FROM read_parquet({_q(parts / '*.parquet')}) ORDER BY source_row) TO {_q(destination)} (FORMAT PARQUET, COMPRESSION ZSTD)")
        sidecar_rows = con.execute(f"SELECT COUNT(*) FROM read_parquet({_q(destination)})").fetchone()[0]
    finally:
        con.close()
    # These are our own intermediate chunks and DuckDB spill files, not source artifacts.
    shutil.rmtree(parts)
    if scratch.is_dir() and not any(scratch.iterdir()):
        scratch.rmdir()
    manifest = {
        "raw_csv": str(source),
        "raw_rows_scanned": int(raw_count),
        "mapped_rows": int(mapped_count),
        "scope": "development only" if development_users is not None else "all source rows",
        "sidecar_rows": int(sidecar_rows),
        "source_row": "one-based logical CSV record before canonical exact deduplication",
        "problem_type_empty_policy": "unknown_template (matches Junyi source preprocessing)",
        "sidecar": str(destination),
    }
    (output / "sidecar_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def verify_problem_type_mapping(
    sidecar_dir: str | Path,
    canonical_dir: str | Path,
    duplicate_lineage: str | Path,
    assignments_parquet: str | Path | None = None,
) -> dict:
    """Verify source_row joins and required identity fields after exact dedup."""
    sidecar = Path(sidecar_dir).resolve() / "source_sidecar.parquet"
    canonical_glob = Path(canonical_dir).resolve() / "**" / "*.parquet"
    lineage = Path(duplicate_lineage).resolve()
    if not sidecar.is_file() or not lineage.is_file() or not Path(canonical_dir).is_dir():
        raise FileNotFoundError("Sidecar, canonical data, and duplicate lineage are required")
    con = duckdb.connect()
    try:
        con.execute(f"CREATE VIEW s AS SELECT * FROM read_parquet({_q(sidecar)})")
        con.execute(f"CREATE VIEW c_all AS SELECT * FROM read_parquet({_q(canonical_glob)}, hive_partitioning=true)")
        if assignments_parquet is not None:
            con.execute(f"CREATE VIEW a AS SELECT * FROM read_parquet({_q(assignments_parquet)})")
            con.execute("CREATE VIEW c AS SELECT c_all.* FROM c_all JOIN a USING(user_id) WHERE a.partition='development'")
        else:
            con.execute("CREATE VIEW c AS SELECT * FROM c_all")
        con.execute(f"CREATE VIEW d AS SELECT * FROM read_parquet({_q(lineage)})")
        canonical_rows, sidecar_rows, duplicate_rows = con.execute(
            "SELECT (SELECT COUNT(*) FROM c), (SELECT COUNT(*) FROM s), "
            "(SELECT COUNT(*) FROM d JOIN s keep ON d.retained_source_row=keep.source_row)"
        ).fetchone()
        duplicate_source_keys = con.execute("SELECT COUNT(*) FROM (SELECT source_row FROM s GROUP BY source_row HAVING COUNT(*)<>1)").fetchone()[0]
        missing = con.execute("SELECT COUNT(*) FROM c LEFT JOIN s USING(source_row) WHERE s.source_row IS NULL").fetchone()[0]
        mismatch = con.execute(
            "SELECT COUNT(*) FROM c JOIN s USING(source_row) WHERE "
            "CAST(c.user_id AS VARCHAR)<>s.user_id OR CAST(c.exercise AS VARCHAR)<>s.exercise "
            "OR CAST(c.time_done AS BIGINT)<>s.time_done OR CAST(c.correct AS INTEGER)<>s.correct"
        ).fetchone()[0]
        untracked_rows = con.execute(
            "SELECT COUNT(*) FROM s LEFT JOIN c USING(source_row) "
            "LEFT JOIN d ON d.duplicate_source_row=s.source_row "
            "WHERE c.source_row IS NULL AND d.duplicate_source_row IS NULL"
        ).fetchone()[0]
        bad_lineage = con.execute(
            "SELECT COUNT(*) FROM d JOIN s retained ON d.retained_source_row=retained.source_row "
            "LEFT JOIN c r ON d.retained_source_row=r.source_row "
            "LEFT JOIN s dup ON d.duplicate_source_row=dup.source_row "
            "LEFT JOIN s keep ON d.retained_source_row=keep.source_row "
            "WHERE r.source_row IS NULL OR dup.source_row IS NULL OR keep.source_row IS NULL "
            "OR dup.user_id<>keep.user_id OR dup.exercise<>keep.exercise "
            "OR dup.time_done<>keep.time_done OR dup.correct<>keep.correct "
            "OR dup.suggested<>keep.suggested OR dup.problem_type<>keep.problem_type"
        ).fetchone()[0]
        if duplicate_source_keys or missing or mismatch or bad_lineage or untracked_rows or canonical_rows != sidecar_rows - duplicate_rows:
            raise ValueError(
                "source_row identity mismatch or duplicate lineage failure: "
                f"duplicate_keys={duplicate_source_keys}, missing={missing}, mismatched={mismatch}, "
                f"bad_lineage={bad_lineage}, untracked={untracked_rows}, canonical={canonical_rows}, raw={sidecar_rows}, duplicates={duplicate_rows}"
            )
        counts = con.execute(
            "SELECT COUNT(DISTINCT problem_type), COUNT(*) FILTER (WHERE problem_type='unknown_template') FROM c JOIN s USING(source_row)"
        ).fetchone()
        return {
            "canonical_rows": int(canonical_rows),
            "raw_rows": int(sidecar_rows),
            "scope": "development only" if assignments_parquet is not None else "all source rows",
            "mapped_rows": int(canonical_rows - missing - mismatch),
            "duplicate_rows_verified": int(duplicate_rows),
            "problem_type_values": int(counts[0]),
            "unknown_template_rows": int(counts[1]),
            "identity_fields_verified": ["user_id", "exercise", "time_done", "correct"],
            "lineage_fields_verified": ["user_id", "exercise", "time_done", "correct", "suggested", "problem_type"],
        }
    finally:
        con.close()
