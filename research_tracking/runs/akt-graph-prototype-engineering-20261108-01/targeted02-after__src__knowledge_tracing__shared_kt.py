"""Small, model-neutral contracts shared by future KT implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

import numpy as np


@dataclass(frozen=True)
class StableVocabulary:
    """A deterministic string-to-integer vocabulary."""

    values: tuple[str, ...]

    @classmethod
    def from_values(cls, values: Sequence[Any]) -> "StableVocabulary":
        return cls(tuple(sorted({str(value) for value in values})))

    def encode(self, values: Sequence[Any]) -> np.ndarray:
        lookup = {value: index for index, value in enumerate(self.values)}
        try:
            return np.asarray([lookup[str(value)] for value in values], dtype=np.int64)
        except KeyError as exc:
            raise ValueError(f"unknown vocabulary value: {exc.args[0]}") from exc

    def decode(self, ids: Sequence[int]) -> list[str]:
        try:
            indexes = [int(index) for index in ids]
            if any(index < 0 or index >= len(self.values) for index in indexes):
                raise IndexError
            return [self.values[index] for index in indexes]
        except (IndexError, ValueError) as exc:
            raise ValueError("vocabulary id is out of range") from exc


@dataclass(frozen=True)
class MappingAudit:
    unmapped_exercises: tuple[str, ...]
    ambiguous_exercises: tuple[str, ...]
    graph_nodes_without_mapping: tuple[str, ...]
    exercise_concepts: tuple[tuple[str, tuple[str, ...]], ...]


def audit_exercise_concept_mapping(
    exercise_ids: Sequence[Any],
    mapping: Mapping[Any, Sequence[Any]],
    graph_nodes: Sequence[Any] = (),
) -> MappingAudit:
    normalized = {str(k): tuple(sorted({str(v) for v in values})) for k, values in mapping.items()}
    exercises = tuple(sorted({str(value) for value in exercise_ids}))
    unmapped = tuple(value for value in exercises if not normalized.get(value))
    ambiguous = tuple(value for value in exercises if len(normalized.get(value, ())) > 1)
    graph_unmapped = tuple(sorted(str(node) for node in set(graph_nodes) if not normalized.get(str(node))))
    return MappingAudit(
        unmapped_exercises=unmapped,
        ambiguous_exercises=ambiguous,
        graph_nodes_without_mapping=graph_unmapped,
        exercise_concepts=tuple((exercise, normalized.get(exercise, ())) for exercise in exercises),
    )


@dataclass(frozen=True)
class PrerequisiteGraph:
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    edge_direction: str = "prerequisite_to_dependent"

    @classmethod
    def from_edges(cls, nodes: Sequence[Any], edges: Sequence[tuple[Any, Any]]) -> "PrerequisiteGraph":
        node_set = {str(node) for node in nodes}
        normalized = tuple(sorted({(str(parent), str(child)) for parent, child in edges}))
        for parent, child in normalized:
            if parent not in node_set or child not in node_set:
                raise ValueError(f"edge endpoint missing from graph nodes: {(parent, child)}")
            if parent == child:
                raise ValueError(f"self edge is invalid: {parent}")
        return cls(tuple(sorted(node_set)), normalized)


def validate_fold_isolation(user_ids: Sequence[Any], folds: Sequence[Any]) -> None:
    if len(user_ids) != len(folds):
        raise ValueError("user_ids and folds must have the same length")
    assignments: dict[str, set[str]] = {}
    for user, fold in zip(user_ids, folds):
        assignments.setdefault(str(user), set()).add(str(fold))
    split = sorted(user for user, assigned in assignments.items() if len(assigned) > 1)
    if split:
        raise ValueError(f"users appear in multiple folds: {split[:5]}")


@dataclass(frozen=True)
class CausalSequenceInputs:
    item_ids: np.ndarray
    timestamps: np.ndarray
    prior_responses: np.ndarray
    source_rows: np.ndarray
    sequence_offsets: np.ndarray
    user_ids: tuple[str, ...]
    concept_ids: np.ndarray | None = None


def build_causal_sequence_inputs(
    rows: Sequence[Mapping[str, Any]],
    *,
    user_key: str = "user_id",
    item_key: str = "exercise_id",
    timestamp_key: str = "time_done",
    source_row_key: str = "source_row",
    target_key: str = "correct",
    concept_ids_by_exercise: Mapping[Any, Any] | None = None,
    item_vocabulary: StableVocabulary | None = None,
    concept_vocabulary: StableVocabulary | None = None,
) -> tuple[CausalSequenceInputs, np.ndarray]:
    """Sort rows and expose only shifted responses to model inputs.

    For held-out rows, pass vocabularies built from that fold's training data.
    """
    source_ids = [int(row[source_row_key]) for row in rows]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("source_row must be unique within sequence input")
    if any(int(row[target_key]) not in (0, 1) for row in rows):
        raise ValueError("sequence targets must be binary")
    ordered = sorted(rows, key=lambda row: (str(row[user_key]), row[timestamp_key], int(row[source_row_key])))
    if not ordered:
        empty = np.asarray([], dtype=np.int64)
        return CausalSequenceInputs(empty, empty, empty, empty, np.asarray([0]), ()), empty

    users = [str(row[user_key]) for row in ordered]
    item_vocab = item_vocabulary or StableVocabulary.from_values([row[item_key] for row in ordered])
    item_ids = item_vocab.encode([row[item_key] for row in ordered])
    targets = np.asarray([int(row[target_key]) for row in ordered], dtype=np.int8)
    prior = np.full(len(ordered), -1, dtype=np.int8)
    offsets = [0]
    for index in range(1, len(ordered)):
        if users[index] != users[index - 1]:
            offsets.append(index)
        else:
            prior[index] = targets[index - 1]
    offsets.append(len(ordered))
    timestamps = np.asarray([row[timestamp_key] for row in ordered])
    source_rows = np.asarray([int(row[source_row_key]) for row in ordered], dtype=np.int64)
    concepts = None
    if concept_ids_by_exercise is not None:
        normalized_mapping: dict[str, str] = {}
        for exercise, concept in concept_ids_by_exercise.items():
            if isinstance(concept, (list, tuple, set)):
                values = {str(value) for value in concept}
                if len(values) != 1:
                    raise ValueError(f"exercise has ambiguous concept mapping: {exercise}")
                concept = next(iter(values))
            normalized_mapping[str(exercise)] = str(concept)
        event_concepts = [normalized_mapping.get(str(row[item_key])) for row in ordered]
        if any(concept is None for concept in event_concepts):
            raise ValueError("concept mapping is missing an exercise in sequence input")
        concept_vocab = concept_vocabulary or StableVocabulary.from_values(event_concepts)
        concepts = concept_vocab.encode(event_concepts)
    inputs = CausalSequenceInputs(item_ids, timestamps, prior, source_rows, np.asarray(offsets), tuple(users), concepts)
    return inputs, targets


def causal_attention_mask(sequence_length: int) -> np.ndarray:
    if sequence_length < 0:
        raise ValueError("sequence_length must be nonnegative")
    return np.tril(np.ones((sequence_length, sequence_length), dtype=bool))


@dataclass(frozen=True)
class AlignmentReport:
    aligned_rows: int
    missing_rows: tuple[int, ...]
    extra_rows: tuple[int, ...]


def check_prediction_alignment(
    expected_rows: Sequence[Mapping[str, Any]],
    prediction_rows: Sequence[Mapping[str, Any]],
    *,
    identity_keys: Sequence[str] = ("user_id", "exercise_id", "correct", "suggested"),
    source_row_key: str = "source_row",
) -> AlignmentReport:
    def keyed(rows: Sequence[Mapping[str, Any]], label: str) -> dict[int, Mapping[str, Any]]:
        output: dict[int, Mapping[str, Any]] = {}
        for row in rows:
            key = int(row[source_row_key])
            if key in output:
                raise ValueError(f"duplicate {source_row_key} in {label}: {key}")
            output[key] = row
        return output

    expected, predicted = keyed(expected_rows, "expected rows"), keyed(prediction_rows, "predictions")
    missing = tuple(sorted(expected.keys() - predicted.keys()))
    extra = tuple(sorted(predicted.keys() - expected.keys()))
    for source_row in expected.keys() & predicted.keys():
        for key in identity_keys:
            if expected[source_row].get(key) != predicted[source_row].get(key):
                raise ValueError(f"identity mismatch for source_row={source_row}: {key}")
    return AlignmentReport(len(expected.keys() & predicted.keys()), missing, extra)


def coverage_summary(expected_rows: int, prediction_rows: int, fitted_rows: int) -> dict[str, float | int]:
    if min(expected_rows, prediction_rows, fitted_rows) < 0 or fitted_rows > prediction_rows or prediction_rows > expected_rows:
        raise ValueError("coverage counts must satisfy 0 <= fitted <= predictions <= expected")
    return {
        "expected_rows": expected_rows,
        "prediction_rows": prediction_rows,
        "fitted_rows": fitted_rows,
        "prediction_coverage": prediction_rows / expected_rows if expected_rows else 0.0,
        "fitted_coverage": fitted_rows / expected_rows if expected_rows else 0.0,
    }


@runtime_checkable
class SequenceKTModel(Protocol):
    """Batch sequence API; targets are passed only to fit, never predict."""

    def fit(self, inputs: CausalSequenceInputs, targets: np.ndarray) -> "SequenceKTModel": ...

    def predict(self, inputs: CausalSequenceInputs) -> np.ndarray: ...
