from __future__ import annotations

import json

import duckdb
import numpy as np
import pandas as pd
import pytest

from knowledge_tracing.gam_kt.data import build_problem_type_sidecar, verify_problem_type_mapping
from knowledge_tracing.gam_kt.difficulty import fit_difficulty
from knowledge_tracing.gam_kt.evaluation import score_frame
from knowledge_tracing.gam_kt.replay import predict_then_update
from knowledge_tracing.gam_kt.runner import _read_checkpoint
from knowledge_tracing.gam_kt.splits import assert_student_disjoint, validate_frozen_assignments


def _raw(path, records):
    columns = [
        "user_id", "exercise", "problem_type", "problem_number", "topic_mode",
        "suggested", "review_mode", "time_done", "time_taken",
        "time_taken_attempts", "correct", "count_attempts", "hint_used",
        "count_hints", "hint_time_taken_list", "earned_proficiency", "points_earned",
    ]
    pd.DataFrame(records, columns=columns).to_csv(path, index=False)


def test_mapping_uses_source_row_and_verifies_identity_after_duplicate_removal(tmp_path):
    raw = tmp_path / "raw.csv"
    row_a = ["u1", "e1", "tpl-A", "1", "t", "0", "0", "100", "3", "1", "1", "1", "0", "0", "", "0", "1"]
    row_dup = row_a.copy()
    row_b = ["u2", "e2", "", "2", "t", "1", "0", "200", "4", "1", "0", "1", "0", "0", "", "0", "0"]
    _raw(raw, [row_a, row_dup, row_b])
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    con = duckdb.connect()
    try:
        con.execute("CREATE TABLE c(source_row BIGINT,user_id VARCHAR,exercise VARCHAR,time_done BIGINT,correct INTEGER,suggested INTEGER,order_id BIGINT)")
        con.execute("INSERT INTO c VALUES (1,'u1','e1',100,1,0,1),(3,'u2','e2',200,0,1,1)")
        con.execute(f"COPY c TO '{str(canonical / 'rows.parquet').replace(chr(39), chr(39)*2)}' (FORMAT PARQUET)")
        lineage = tmp_path / "duplicates.parquet"
        con.execute("COPY (SELECT 2::BIGINT duplicate_source_row, 1::BIGINT retained_source_row) TO ? (FORMAT PARQUET)", [str(lineage)])
    finally:
        con.close()
    sidecar = tmp_path / "sidecar"
    build_problem_type_sidecar(raw, sidecar, chunk_rows=2)
    report = verify_problem_type_mapping(sidecar, canonical, lineage)
    assert report["canonical_rows"] == 2
    assert report["mapped_rows"] == 2
    assert report["duplicate_rows_verified"] == 1
    con = duckdb.connect()
    try:
        mapping = con.execute(f"SELECT * FROM read_parquet('{sidecar / 'source_sidecar.parquet'}')").df().set_index("source_row")
    finally:
        con.close()
    assert mapping.loc[1, "problem_type"] == "tpl-A"
    assert mapping.loc[3, "problem_type"] == "unknown_template"


def test_mapping_rejects_wrong_identity_even_when_source_row_exists(tmp_path):
    raw = tmp_path / "raw.csv"
    row = ["u1", "e1", "tpl", "1", "t", "0", "0", "100", "3", "1", "1", "1", "0", "0", "", "0", "1"]
    _raw(raw, [row])
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    con = duckdb.connect()
    try:
        con.execute("CREATE TABLE c(source_row BIGINT,user_id VARCHAR,exercise VARCHAR,time_done BIGINT,correct INTEGER,suggested INTEGER,order_id BIGINT)")
        con.execute("INSERT INTO c VALUES (1,'wrong-user','e1',100,1,0,1)")
        con.execute(f"COPY c TO '{str(canonical / 'rows.parquet').replace(chr(39), chr(39)*2)}' (FORMAT PARQUET)")
        lineage = tmp_path / "duplicates.parquet"
        con.execute("COPY (SELECT NULL::BIGINT duplicate_source_row, NULL::BIGINT retained_source_row WHERE false) TO ? (FORMAT PARQUET)", [str(lineage)])
    finally:
        con.close()
    sidecar = tmp_path / "sidecar"
    build_problem_type_sidecar(raw, sidecar, chunk_rows=2)
    with pytest.raises(ValueError, match="identity mismatch"):
        verify_problem_type_mapping(sidecar, canonical, lineage)


def test_mapping_scope_excludes_frozen_test_students_but_keeps_global_source_row(tmp_path):
    raw = tmp_path / "raw.csv"
    row_dev = ["u1", "e1", "tpl", "1", "t", "0", "0", "100", "3", "1", "1", "1", "0", "0", "", "0", "1"]
    row_dup = row_dev.copy()
    row_test = ["u2", "e2", "test_tpl", "2", "t", "0", "0", "200", "3", "1", "0", "1", "0", "0", "", "0", "0"]
    _raw(raw, [row_dev, row_dup, row_test])
    assignments = tmp_path / "assignments.parquet"
    lineage = tmp_path / "lineage.parquet"
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    con = duckdb.connect()
    try:
        con.execute("COPY (SELECT * FROM (VALUES ('u1','development',0),('u2','test',-1)) t(user_id,partition,fold)) TO ? (FORMAT PARQUET)", [str(assignments)])
        con.execute("COPY (SELECT 2::BIGINT duplicate_source_row,1::BIGINT retained_source_row) TO ? (FORMAT PARQUET)", [str(lineage)])
        con.execute("COPY (SELECT 1::BIGINT source_row,'u1' user_id,'e1' exercise,100::BIGINT time_done,1::INTEGER correct,0::INTEGER suggested,1::BIGINT order_id) TO ? (FORMAT PARQUET)", [str(canonical / "rows.parquet")])
    finally:
        con.close()
    sidecar = tmp_path / "sidecar"
    manifest = build_problem_type_sidecar(raw, sidecar, assignments_parquet=assignments, chunk_rows=2)
    report = verify_problem_type_mapping(sidecar, canonical, lineage, assignments)
    assert manifest["scope"] == "development only"
    assert manifest["raw_rows_scanned"] == 3
    assert manifest["mapped_rows"] == 2
    assert report["canonical_rows"] == 1
    assert report["duplicate_rows_verified"] == 1
    con = duckdb.connect()
    try:
        rows = con.execute(f"SELECT source_row,user_id FROM read_parquet('{sidecar / 'source_sidecar.parquet'}') ORDER BY source_row").fetchall()
    finally:
        con.close()
    assert rows == [(1, "u1"), (2, "u1")]


def test_frozen_assignment_validation_and_disjointness():
    good = pd.DataFrame({"user_id": ["a", "b", "c"], "partition": ["development", "development", "test"], "fold": [0, 1, -1]})
    validate_frozen_assignments(good, expected_students=3)
    with pytest.raises(ValueError, match="fold"):
        validate_frozen_assignments(good.assign(fold=[0, 5, -1]), expected_students=3)
    with pytest.raises(ValueError, match="duplicate"):
        validate_frozen_assignments(pd.concat([good, good.iloc[[0]]]), expected_students=3)
    with pytest.raises(ValueError, match="leakage"):
        assert_student_disjoint(pd.DataFrame({"user_id": ["a"]}), pd.DataFrame({"user_id": ["a"]}))


def test_difficulty_uses_train_only_and_matches_original_formula():
    train = pd.DataFrame({"exercise": ["e1", "e1", "e2"], "correct": [1, 0, 1]})
    fitted = fit_difficulty(train)
    p_global = 2 / 3
    p_e1 = (1 + 20 * p_global) / 22
    expected = np.clip(1200 - 400 * np.log10(p_e1 / (1 - p_e1)), 800, 1600)
    assert fitted.global_difficulty == pytest.approx(1200 - 400 * np.log10(p_global / (1 - p_global)))
    assert fitted.difficulty["e1"] == pytest.approx(expected)
    assert fitted.get("never_seen") == fitted.global_difficulty


def test_order_ties_use_source_row_and_assignments_are_not_regenerated():
    from knowledge_tracing.gam_kt.splits import order_user_events

    frame = pd.DataFrame({"user_id": ["b", "a", "a"], "time_done": [2, 5, 5], "source_row": [8, 7, 2]})
    ordered = order_user_events(frame)
    assert ordered.source_row.tolist() == [2, 7, 8]
    frozen_path = __import__("pathlib").Path("artifacts/bkt_baseline/splits/assignments.parquet")
    assert frozen_path.is_file()


def test_actual_frozen_assignments_are_unchanged_and_student_disjoint():
    from pathlib import Path
    import hashlib

    path = Path("artifacts/bkt_baseline/splits/assignments.parquet")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == "ee588c5b72fc214295e6eef1839b5110c884f43ab52ab4a792ca82e35812be20"
    con = duckdb.connect()
    try:
        data = con.execute(f"SELECT * FROM read_parquet('{path}')").df()
    finally:
        con.close()
    validate_frozen_assignments(data, expected_students=247_606)
    assert (data.partition == "development").sum() == 198_084
    assert (data.partition == "test").sum() == 49_522
    assert data.loc[data.partition == "development", "fold"].value_counts().to_dict() == {0: 39617, 1: 39617, 2: 39617, 3: 39617, 4: 39616}


def test_cv_row_query_reads_only_frozen_development_fold(tmp_path, monkeypatch):
    import knowledge_tracing.gam_kt.runner as runner

    canonical = tmp_path / "canonical" / "exercise=e1"
    canonical.mkdir(parents=True)
    sidecar_dir = tmp_path / "sidecar"
    sidecar_dir.mkdir()
    assignments = tmp_path / "assignments.parquet"
    con = duckdb.connect()
    try:
        con.execute("COPY (SELECT * FROM (VALUES (1::BIGINT,'dev','development',0),(2::BIGINT,'test','test',-1)) t(dummy,user_id,partition,fold)) TO ? (FORMAT PARQUET)", [str(assignments)])
        con.execute("COPY (SELECT * FROM (VALUES (1::BIGINT,'dev','e1',100::BIGINT,1,0,1::BIGINT),(2::BIGINT,'test','e1',200::BIGINT,0,0,1::BIGINT)) t(source_row,user_id,exercise,time_done,correct,suggested,order_id)) TO ? (FORMAT PARQUET)", [str(canonical / "rows.parquet")])
        con.execute("COPY (SELECT * FROM (VALUES (1::BIGINT,'dev','e1',100::BIGINT,1,0,'tpl'),(2::BIGINT,'test','e1',200::BIGINT,0,0,'tpl')) t(source_row,user_id,exercise,time_done,correct,suggested,problem_type)) TO ? (FORMAT PARQUET)", [str(sidecar_dir / "source_sidecar.parquet")])
    finally:
        con.close()
    monkeypatch.setattr(runner, "CANONICAL", tmp_path / "canonical")
    monkeypatch.setattr(runner, "ASSIGNMENTS", assignments)
    monkeypatch.setattr(runner, "SIDECAR_DIR", sidecar_dir)
    con = duckdb.connect()
    try:
        query = runner._user_frame(con, 0)
        rows = query.fetch_df_chunk(1)
    finally:
        con.close()
    assert rows.user_id.tolist() == ["dev"]
    assert rows.source_row.tolist() == [1]


def test_predict_then_update_calls_model_in_correct_order():
    calls = []

    class Model:
        def predict(self, *args):
            calls.append(("predict", self.seen, args[-1]))
            return 0.25

        def update(self, *args):
            calls.append(("update", args[-2], args[-1]))
            self.seen = args[-2]

        seen = None

    model = Model()
    prediction = predict_then_update(model, "e", "tpl", 1200.0, pd.Timestamp("2020-01-01", tz="UTC"), 1)
    assert prediction == 0.25
    assert calls == [("predict", None, pd.Timestamp("2020-01-01", tz="UTC")), ("update", 1, 0.25)]
    assert model.seen == 1


def test_metrics_report_undefined_auc_and_exact_coverage():
    frame = pd.DataFrame({
        "correct": [1, 0, 0], "prediction": [0.9, 0.6, 0.5],
        "suggested": [0, 1, 1], "exercise": ["e1", "e1", "unseen"],
        "is_fallback": [False, False, True],
        "train_support_students": [10, 10, 0],
    })
    result = score_frame(frame)
    assert result["native"]["metrics"]["auc"] == pytest.approx(1.0)
    assert result["supported"]["metrics"]["auc"] == pytest.approx(1.0)
    assert result["native"]["rows"] == 3
    assert result["supported"]["rows"] == 2
    assert result["coverage"]["fallback_rows"] == 1
    assert result["coverage"]["predicted_rows"] == 3
    assert result["suggested"]["suggested"]["metrics"]["auc"] is None
    assert result["native"]["metrics"]["positive_count"] == 1
    assert result["native"]["metrics"]["negative_count"] == 2
    assert result["native"]["metrics"]["log_loss"] == pytest.approx((-np.log(0.9) - np.log(0.4) - np.log(0.5)) / 3)
    assert result["native"]["metrics"]["brier"] == pytest.approx((0.01 + 0.36 + 0.25) / 3)
    assert result["native"]["metrics"]["ece"] == pytest.approx(0.4)
    assert result["native"]["metrics"]["accuracy"] == pytest.approx(1 / 3)
    assert result["train_support_bands"]["unseen"]["fallback_rows"] == 1


def test_checkpoint_resume_requires_matching_identity_and_shard_hash(tmp_path):
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(json.dumps({"identity": {"seed": 42}, "shards": {}}), encoding="utf-8")
    assert _read_checkpoint(checkpoint, {"seed": 42})["identity"] == {"seed": 42}
    with pytest.raises(ValueError, match="Incompatible"):
        _read_checkpoint(checkpoint, {"seed": 43})
