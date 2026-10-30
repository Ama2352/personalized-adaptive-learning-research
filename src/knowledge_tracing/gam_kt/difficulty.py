"""Train-only Junyi exercise difficulty preprocessing from the paper source."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd


ALPHA = 20.0
INITIAL_ELO = 1200.0


def probability_to_difficulty(probability: float) -> float:
    p = float(np.clip(probability, 0.05, 0.95))
    return float(np.clip(INITIAL_ELO - 400.0 * np.log10(p / (1.0 - p)), 800.0, 1600.0))


@dataclass(frozen=True)
class DifficultyFit:
    global_difficulty: float
    difficulty: dict[str, float]
    global_correct: float
    exercise_correct: dict[str, float]
    exercise_rows: dict[str, int]
    exercise_students: dict[str, int]

    def get(self, exercise: str) -> float:
        return self.difficulty.get(exercise, self.global_difficulty)


def fit_difficulty(train_rows: pd.DataFrame) -> DifficultyFit:
    """Fit mappings from the supplied training interactions only."""
    if not {"exercise", "correct"} <= set(train_rows.columns) or train_rows.empty:
        raise ValueError("Nonempty training rows with exercise/correct are required")
    if not train_rows.correct.isin([0, 1]).all():
        raise ValueError("correct must be binary")
    global_correct = float(train_rows.correct.mean())
    grouped = train_rows.groupby("exercise", sort=True).agg(
        correct_sum=("correct", "sum"), rows=("correct", "size"),
        students=("user_id", "nunique") if "user_id" in train_rows.columns else ("correct", "size"),
    )
    difficulty, rates, row_counts, student_counts = {}, {}, {}, {}
    for exercise, values in grouped.iterrows():
        count = int(values.rows)
        rate = (float(values.correct_sum) + ALPHA * global_correct) / (count + ALPHA)
        difficulty[str(exercise)] = probability_to_difficulty(rate)
        rates[str(exercise)] = rate
        row_counts[str(exercise)] = count
        student_counts[str(exercise)] = int(values.students)
    return DifficultyFit(
        global_difficulty=probability_to_difficulty(global_correct),
        difficulty=difficulty,
        global_correct=global_correct,
        exercise_correct=rates,
        exercise_rows=row_counts,
        exercise_students=student_counts,
    )


def fit_difficulty_from_frozen_split(canonical_dir: str | Path, assignments_parquet: str | Path, validation_fold: int, output_path: str | Path) -> dict:
    """Aggregate only Development users outside the validation fold."""
    canonical = Path(canonical_dir).resolve() / "**" / "*.parquet"
    assignments = Path(assignments_parquet).resolve()
    con = duckdb.connect()
    try:
        qcanonical = str(canonical).replace("'", "''")
        qassignments = str(assignments).replace("'", "''")
        train_filter = "a.partition='development' AND a.fold<>?"
        global_correct, training_rows, training_students = con.execute(
            f"SELECT AVG(c.correct), COUNT(*), COUNT(DISTINCT c.user_id) "
            f"FROM read_parquet('{qcanonical}', hive_partitioning=true) c "
            f"JOIN read_parquet('{qassignments}') a USING(user_id) WHERE {train_filter}",
            [int(validation_fold)],
        ).fetchone()
        if not training_rows:
            raise ValueError("Frozen training partition is empty")
        grouped = con.execute(
            f"SELECT c.exercise, SUM(c.correct) AS correct_sum, COUNT(*) AS rows, "
            f"COUNT(DISTINCT c.user_id) AS students FROM read_parquet('{qcanonical}', hive_partitioning=true) c "
            f"JOIN read_parquet('{qassignments}') a USING(user_id) WHERE {train_filter} GROUP BY c.exercise ORDER BY c.exercise",
            [int(validation_fold)],
        ).df()
    finally:
        con.close()
    global_correct = float(global_correct)
    global_difficulty = probability_to_difficulty(global_correct)
    grouped["p_smoothed"] = (grouped.correct_sum + ALPHA * global_correct) / (grouped.rows + ALPHA)
    grouped["difficulty"] = grouped.p_smoothed.map(probability_to_difficulty)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    frame = grouped.rename(columns={"rows": "train_rows", "students": "train_students"})[
        ["exercise", "difficulty", "train_rows", "train_students"]
    ]
    con = duckdb.connect()
    try:
        con.register("difficulties", frame)
        con.execute(f"COPY difficulties TO '{str(temporary).replace(chr(39), chr(39)*2)}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    finally:
        con.close()
    temporary.replace(target)
    return {
        "validation_fold": int(validation_fold),
        "training_rows": int(training_rows),
        "training_students": int(training_students),
        "global_correct": global_correct,
        "global_difficulty": global_difficulty,
        "trained_exercises": int(len(frame)),
        "difficulty_path": str(target.resolve()),
    }
