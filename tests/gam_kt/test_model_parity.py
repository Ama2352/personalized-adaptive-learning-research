from __future__ import annotations

import hashlib
import json
import math
from dataclasses import field
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from knowledge_tracing.gam_kt.model import build_model


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = (
    ROOT
    / "drive-download-20261018T084013Z-1-001"
    / "rivf2026_gam_kt_artifact_v20"
    / "rivf2026_gam_kt_artifact_v20"
    / "source"
    / "junyi_cycle_corrected_ablation_confirmation.ipynb"
)
MODEL_CELL_SHA256 = "5fc0adbf8fcb454b73bbdd3294bb20e17c2a08ec9eb496b7383677f38b04a5fc"


def original_model_class():
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    source = "".join(notebook["cells"][11]["source"])
    assert hashlib.sha256(source.encode("utf-8")).hexdigest() == MODEL_CELL_SHA256
    namespace = {
        "FEATURE_DIM": 64,
        "MODEL_INITIAL_ELO": 1200.0,
        "np": np,
        "pd": pd,
        "math": math,
        "hashlib": hashlib,
        "lru_cache": lru_cache,
        "dataclass": __import__("dataclasses").dataclass,
        "field": field,
        "graph": None,
        "topic_map": {},
        "area_map": {},
    }
    exec(compile(source, str(NOTEBOOK), "exec"), namespace)
    return namespace["GAMKTModel"], namespace


def test_integrated_graph_free_model_matches_original_state_and_predictions():
    original_class, original_namespace = original_model_class()
    topics = {"linear_equations": "algebra", "fraction_addition": "fractions"}
    areas = {"linear_equations": "math", "fraction_addition": "math"}
    original_namespace["topic_map"] = topics
    original_namespace["area_map"] = areas
    original_namespace["question_feature_vector"].cache_clear()

    reference = original_class(
        False,
        time_decay_rate=0.0,
        graph_weight=0.0,
        graph_source=None,
        graph_signal_enabled=False,
        graph_adaptation_enabled=False,
    )
    integrated = build_model(topics, areas)

    # Exercise both response branches, interleaved skills, metadata features,
    # elapsed-time uncertainty growth, and a downward mastery-threshold crossing.
    start = pd.Timestamp("2015-01-01T00:00:00Z")
    sequence = [
        ("linear_equations", "template_1", 1210.0, start, 1),
        ("fraction_addition", "template_7", 1160.0, start + pd.Timedelta(hours=2), 0),
        ("linear_equations", "template_2", 1200.0, start + pd.Timedelta(days=8), 0),
        ("fraction_addition", "template_7", 1190.0, start + pd.Timedelta(days=9), 1),
    ]
    reference._state("linear_equations").theta = 1300.1
    integrated._state("linear_equations").theta = 1300.1

    for exercise, problem_type, difficulty, timestamp, correct in sequence:
        expected = reference.predict(exercise, problem_type, difficulty, timestamp)
        actual = integrated.predict(exercise, problem_type, difficulty, timestamp)
        assert actual == expected
        assert math.isfinite(actual) and 0.0 <= actual <= 1.0

        reference.update(exercise, problem_type, difficulty, timestamp, correct, expected)
        integrated.update(exercise, problem_type, difficulty, timestamp, correct, actual)

        expected_state = reference.states[exercise]
        actual_state = integrated.states[exercise]
        assert actual_state.theta == expected_state.theta
        np.testing.assert_array_equal(actual_state.memory, expected_state.memory)
        assert actual_state.pi_task == expected_state.pi_task
        assert actual_state.pi_time == expected_state.pi_time
        assert actual_state.attempts == expected_state.attempts
        assert actual_state.last_timestamp == expected_state.last_timestamp
        assert actual_state.times_forgotten == expected_state.times_forgotten
        assert actual_state.recent_outcomes == expected_state.recent_outcomes

    assert integrated.states["fraction_addition"].attempts == 2
