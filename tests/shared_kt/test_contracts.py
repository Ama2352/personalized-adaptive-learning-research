import numpy as np
import pytest

from knowledge_tracing.shared_kt import (
    PrerequisiteGraph,
    StableVocabulary,
    audit_exercise_concept_mapping,
    build_causal_sequence_inputs,
    causal_attention_mask,
    check_prediction_alignment,
    coverage_summary,
    validate_fold_isolation,
)


def test_vocabulary_is_stable_and_round_trips():
    vocab = StableVocabulary.from_values(["b", "a", "b", "c"])

    assert vocab.values == ("a", "b", "c")
    assert vocab.encode(["c", "a"]).tolist() == [2, 0]
    assert vocab.decode([1, 2]) == ["b", "c"]
    with pytest.raises(ValueError, match="out of range"):
        vocab.decode([-1])


def test_mapping_audit_reports_missing_and_ambiguous_ids_without_guessing():
    audit = audit_exercise_concept_mapping(
        ["e1", "e2", "e3"],
        {"e1": ["c1"], "e2": ["c1", "c2"]},
        graph_nodes=["e1", "e2"],
    )

    assert audit.unmapped_exercises == ("e3",)
    assert audit.ambiguous_exercises == ("e2",)
    assert audit.graph_nodes_without_mapping == ()


def test_prerequisite_graph_validates_and_preserves_parent_to_dependent_direction():
    graph = PrerequisiteGraph.from_edges(["p", "d"], [("p", "d")])

    assert graph.edges == (("p", "d"),)
    with pytest.raises(ValueError, match="self"):
        PrerequisiteGraph.from_edges(["p"], [("p", "p")])


def test_fold_isolation_rejects_learners_split_across_folds():
    validate_fold_isolation(["u1", "u1", "u2"], [0, 0, 1])
    with pytest.raises(ValueError, match="multiple folds"):
        validate_fold_isolation(["u1", "u1"], [0, 1])


def test_sequence_inputs_sort_chronologically_and_shift_responses():
    rows = [
        {"user_id": "u1", "exercise_id": "b", "time_done": 2, "source_row": 9, "correct": 0},
        {"user_id": "u1", "exercise_id": "a", "time_done": 1, "source_row": 8, "correct": 1},
        {"user_id": "u2", "exercise_id": "a", "time_done": 1, "source_row": 2, "correct": 0},
    ]

    inputs, targets = build_causal_sequence_inputs(rows)

    assert inputs.source_rows.tolist() == [8, 9, 2]
    assert inputs.item_ids.tolist() == [0, 1, 0]
    assert inputs.prior_responses.tolist() == [-1, 1, -1]
    assert inputs.sequence_offsets.tolist() == [0, 2, 3]
    assert targets.tolist() == [1, 0, 0]
    assert not hasattr(inputs, "targets")

    with_concepts, _ = build_causal_sequence_inputs(rows, concept_ids_by_exercise={"a": "c1", "b": "c2"})
    assert with_concepts.concept_ids.tolist() == [0, 1, 0]
    with pytest.raises(ValueError, match="ambiguous"):
        build_causal_sequence_inputs(rows, concept_ids_by_exercise={"a": ["c1", "c2"], "b": "c2"})
    with pytest.raises(ValueError, match="unknown vocabulary"):
        build_causal_sequence_inputs(rows, item_vocabulary=StableVocabulary.from_values(["a"]))


def test_causal_mask_exposes_only_current_and_past_positions():
    assert causal_attention_mask(3).tolist() == [
        [True, False, False],
        [True, True, False],
        [True, True, True],
    ]


def test_alignment_checks_identity_keys_and_coverage():
    expected = [{"source_row": 1, "user_id": "u", "exercise_id": "e", "correct": 1}]
    actual = [{**expected[0], "prediction": 0.7}]
    report = check_prediction_alignment(expected, actual)
    assert report.aligned_rows == 1
    assert report.missing_rows == ()

    with pytest.raises(ValueError, match="identity mismatch"):
        check_prediction_alignment(expected, [{**actual[0], "correct": 0}])
    assert coverage_summary(10, 9, 8)["fitted_coverage"] == 0.8
