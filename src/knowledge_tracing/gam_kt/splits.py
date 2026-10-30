"""Read-only validation and ordering utilities for frozen BKT assignments."""

from __future__ import annotations

import pandas as pd


def validate_frozen_assignments(assignments: pd.DataFrame, *, expected_students: int | None = None) -> None:
    required = {"user_id", "partition", "fold"}
    if not required <= set(assignments.columns):
        raise ValueError(f"Missing assignment fields: {sorted(required - set(assignments.columns))}")
    if assignments.user_id.isna().any() or assignments.user_id.astype(str).eq("").any():
        raise ValueError("Empty assignment user_id")
    if assignments.user_id.duplicated().any():
        raise ValueError("duplicate user assignment")
    if expected_students is not None and len(assignments) != expected_students:
        raise ValueError(f"Expected {expected_students} students, got {len(assignments)}")
    if not set(assignments.partition).issubset({"development", "test"}):
        raise ValueError("Unknown partition in frozen assignments")
    dev = assignments[assignments.partition == "development"]
    test = assignments[assignments.partition == "test"]
    if not dev.fold.isin(range(5)).all() or not test.fold.eq(-1).all():
        raise ValueError("Invalid fold assignment")
    if set(dev.user_id) & set(test.user_id):
        raise ValueError("Development/Test student overlap")
    if not set(dev.fold.unique()) <= set(range(5)):
        raise ValueError("Frozen Development fold is outside 0..4")


def assert_student_disjoint(train: pd.DataFrame, validation: pd.DataFrame) -> None:
    overlap = set(train.user_id.astype(str)) & set(validation.user_id.astype(str))
    if overlap:
        raise ValueError(f"Student leakage across train/validation: {len(overlap)} users")


def order_user_events(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"user_id", "time_done", "source_row"}
    if not required <= set(frame.columns):
        raise ValueError(f"Missing ordering fields: {sorted(required - set(frame.columns))}")
    return frame.sort_values(["user_id", "time_done", "source_row"], kind="mergesort").reset_index(drop=True)
