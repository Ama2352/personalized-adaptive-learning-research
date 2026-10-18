"""Versioned, globally student-disjoint Junyi assignments."""

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path

import duckdb
import pandas as pd


SPLIT_ALGORITHM = "sha256-user-rank-v1"


def _rank(student_id: str, seed: int) -> bytes:
    payload = f"junyi-bkt-split-v1|{seed}|{student_id}".encode("utf-8")
    return hashlib.sha256(payload).digest()


def assign_students(user_ids: Iterable[str], seed: int = 42) -> pd.DataFrame:
    """Assign each unique student once; exactly floor(80%) enter Development."""
    unique = set(user_ids)
    if any(not isinstance(value, str) or not value for value in unique):
        raise ValueError("user IDs must be nonempty strings")
    ranked = sorted(unique, key=lambda value: (_rank(value, seed), value))
    dev_count = 4 * len(ranked) // 5
    records = [
        {
            "user_id": user_id,
            "partition": "development" if position < dev_count else "test",
            "fold": position % 5 if position < dev_count else -1,
        }
        for position, user_id in enumerate(ranked)
    ]
    return pd.DataFrame.from_records(records, columns=["user_id", "partition", "fold"])


def create_split_manifest(canonical_dir: str | Path, output_dir: str | Path, seed: int = 42) -> dict:
    """Persist one assignment for every student in the canonical dataset."""
    canonical = Path(canonical_dir).resolve()
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    destination = output / "assignments.parquet"
    if destination.exists() or (output / "manifest.json").exists():
        raise FileExistsError(output)
    glob = str(canonical / "**" / "*.parquet").replace("'", "''")
    con = duckdb.connect()
    try:
        students = con.execute(
            f"SELECT DISTINCT CAST(user_id AS VARCHAR) AS user_id FROM read_parquet('{glob}')"
        ).fetchnumpy()["user_id"].tolist()
        assignments = assign_students(students, seed=seed)
        con.register("assigned", assignments)
        escaped = str(destination).replace("'", "''")
        con.execute(f"COPY (SELECT * FROM assigned) TO '{escaped}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    finally:
        con.close()
    development = assignments[assignments.partition == "development"]
    test = assignments[assignments.partition == "test"]
    manifest = {
        "algorithm": SPLIT_ALGORITHM,
        "seed": seed,
        "total_students": len(assignments),
        "development_students": len(development),
        "test_students": len(test),
        "development_fold_students": {
            str(fold): int((development.fold == fold).sum()) for fold in range(5)
        },
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
