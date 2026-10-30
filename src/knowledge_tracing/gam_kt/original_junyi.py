"""Verbatim graph-free Junyi GAM-KT implementation extracted from the RIVF artifact.

Original notebook: source/junyi_cycle_corrected_ablation_confirmation.ipynb, cell 11.
Source SHA-256: 5fc0adbf8fcb454b73bbdd3294bb20e17c2a08ec9eb496b7383677f38b04a5fc
The model definitions below are copied verbatim; only the metadata globals are
configured by this integration module.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np
import pandas as pd

FEATURE_DIM = 64
MODEL_INITIAL_ELO = 1200.0
graph = None
topic_map = {}
area_map = {}
_configured_maps = None

def sigmoid(value):
    return float(1.0 / (1.0 + math.exp(-float(np.clip(value, -30.0, 30.0)))))

def elo_probability(theta, difficulty):
    return float(1.0 / (1.0 + 10.0 ** ((difficulty - theta) / 400.0)))

def dynamic_k(attempts):
    if attempts < 5:
        return 40.0
    if attempts <= 15:
        return 24.0
    return 16.0

def clip_norm(vector, max_norm=3.0):
    norm = float(np.linalg.norm(vector))
    return vector * (max_norm / norm) if norm > max_norm else vector

def hash_index_and_sign(token, dimension=FEATURE_DIM):
    digest = hashlib.sha256(str(token).encode("utf-8")).digest()
    index = int.from_bytes(digest[:4], "little") % dimension
    sign = 1.0 if digest[4] % 2 == 0 else -1.0
    return index, sign

@lru_cache(maxsize=100_000)
def question_feature_vector(exercise, problem_type):
    vector = np.zeros(FEATURE_DIM, dtype=np.float32)
    tokens = [
        f"exercise={exercise}",
        f"template={problem_type}",
        f"topic={topic_map.get(exercise, 'unknown_topic')}",
        f"area={area_map.get(exercise, 'unknown_area')}",
    ]
    for token in tokens:
        index, sign = hash_index_and_sign(token)
        vector[index] += sign
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm > 0 else vector

@dataclass
class MemoryState:
    theta: float = MODEL_INITIAL_ELO
    memory: np.ndarray = field(default_factory=lambda: np.zeros(FEATURE_DIM, dtype=np.float32))
    pi_task: float = 1.0
    pi_time: float = 0.05
    attempts: int = 0
    last_timestamp: pd.Timestamp | None = None
    recent_outcomes: list = field(default_factory=list)
    times_forgotten: int = 0

class GAMKTModel:
    def __init__(
        self,
        use_graph_context,
        time_decay_rate=0.02,
        graph_weight=0.35,
        graph_source=None,
        graph_signal_enabled=None,
        graph_adaptation_enabled=None,
        name=None,
    ):
        legacy_graph_flag = bool(use_graph_context)
        self.graph_signal_enabled = (
            legacy_graph_flag if graph_signal_enabled is None else bool(graph_signal_enabled)
        )
        self.graph_adaptation_enabled = (
            legacy_graph_flag if graph_adaptation_enabled is None else bool(graph_adaptation_enabled)
        )
        self.use_graph_context = self.graph_signal_enabled or self.graph_adaptation_enabled
        self.graph_source = graph if graph_source is None else graph_source
        self.name = name or ("Graph-GAM-KT" if self.use_graph_context else "GAM-KT")
        self.states = {}
        self.r_pos, self.r_neg = 0.60, 1.00
        self.q_task, self.q_time = 0.04, 0.04
        self.time_decay_rate = float(time_decay_rate)
        self.theta_lr, self.memory_lr = 80.0, 1.00
        self.item_weight, self.graph_weight = 0.80, float(graph_weight)

    def _state(self, exercise):
        if exercise not in self.states:
            self.states[exercise] = MemoryState()
        return self.states[exercise]

    def _graph_summary(self, exercise):
        if not self.use_graph_context:
            return {"signal": 0.0, "uncertainty": 0.0, "deficit": 0.0}
        parents = (
            list(self.graph_source.predecessors(exercise))
            if exercise in self.graph_source else []
        )
        if not parents:
            return {"signal": 0.0, "uncertainty": 0.0, "deficit": 0.0}
        parent_states = [self._state(parent) for parent in parents]
        signal = float(np.mean([(state.theta - 1300.0) / 400.0 for state in parent_states]))
        uncertainty = float(np.mean([state.pi_task for state in parent_states]))
        deficit = float(np.mean([max(0.0, (1300.0 - state.theta) / 400.0) for state in parent_states]))
        return {
            "signal": float(np.clip(signal, -1.5, 1.5)),
            "uncertainty": uncertainty,
            "deficit": deficit,
        }

    def _context(self, exercise):
        state = self._state(exercise)
        summary = self._graph_summary(exercise)
        struggling = len(state.recent_outcomes) >= 5 and np.mean(state.recent_outcomes[-8:]) < 0.40
        q_task = self.q_task
        r_neg = self.r_neg
        decay = self.time_decay_rate
        if self.graph_adaptation_enabled:
            q_task += 0.025 * summary["uncertainty"] + 0.020 * summary["deficit"]
            r_neg *= 0.90 if struggling else 1.0
            decay += 0.004 * state.times_forgotten + 0.004 * summary["deficit"]
        return {
            "q_task": float(np.clip(q_task, 0.01, 0.18)),
            "r_pos": self.r_pos,
            "r_neg": float(np.clip(r_neg, 0.50, 2.00)),
            "decay": float(np.clip(decay, 0.0, 0.10)),
            "graph_signal": summary["signal"],
        }

    def _decayed_uncertainty(self, exercise, timestamp):
        state = self._state(exercise)
        context = self._context(exercise)
        if state.last_timestamp is None:
            return state.pi_task, state.pi_time, context
        days = max(0.0, (timestamp - state.last_timestamp).total_seconds() / 86400.0)
        days = min(days, 365.0)
        return (
            float(np.clip(state.pi_task + context["decay"] * days, 0.0, 1.0)),
            float(np.clip(state.pi_time + context["decay"] * days, 0.0, 1.0)),
            context,
        )

    def predict(self, exercise, problem_type, difficulty, timestamp):
        state = self._state(exercise)
        pi_task, pi_time, context = self._decayed_uncertainty(exercise, timestamp)
        features = question_feature_vector(exercise, problem_type)
        logit_value = (
            math.log(10.0) * (state.theta - difficulty) / 400.0
            + self.item_weight * float(np.dot(state.memory, features))
            + (
                self.graph_weight * context["graph_signal"]
                if self.graph_signal_enabled else 0.0
            )
        )
        raw = sigmoid(logit_value)
        confidence = float(np.clip(1.0 - 0.45 * pi_task - 0.35 * pi_time, 0.10, 1.0))
        return float(np.clip(0.5 + confidence * (raw - 0.5), 1e-6, 1 - 1e-6))

    def update(self, exercise, problem_type, difficulty, timestamp, y, p_pred):
        state = self._state(exercise)
        pi_task, _, context = self._decayed_uncertainty(exercise, timestamp)
        observation_noise = context["r_pos"] if int(y) == 1 else context["r_neg"]
        gain = pi_task / (pi_task + observation_noise)
        residual = float(y - p_pred)
        state.theta += self.theta_lr * gain * residual
        state.memory = clip_norm(
            state.memory + self.memory_lr * gain * residual * question_feature_vector(exercise, problem_type)
        )
        state.pi_task = float(np.clip((1.0 - gain) * pi_task + context["q_task"], 0.01, 1.0))
        state.pi_time = self.q_time
        state.last_timestamp = timestamp
        state.attempts += 1
        was_high = state.theta - self.theta_lr * gain * residual >= 1300.0
        is_high = state.theta >= 1300.0
        if was_high and not is_high:
            state.times_forgotten += 1
        state.recent_outcomes.append(int(y))
        if len(state.recent_outcomes) > 8:
            state.recent_outcomes.pop(0)

def configure_metadata(topics, areas):
    """Bind this run's fixed exercise metadata, retaining the original cache."""
    global topic_map, area_map, _configured_maps
    if _configured_maps is None:
        topic_map = topics
        area_map = areas
        _configured_maps = (topics, areas)
    elif topics is not _configured_maps[0] or areas is not _configured_maps[1]:
        raise RuntimeError("GAM-KT metadata cannot change after model construction")
