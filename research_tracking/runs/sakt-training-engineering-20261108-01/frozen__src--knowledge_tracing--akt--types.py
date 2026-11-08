"""Kiểu dữ liệu dùng trong pipeline AKT Development."""

from dataclasses import dataclass
import numpy as np

from knowledge_tracing.shared_kt import CausalSequenceInputs


@dataclass(frozen=True)
class KTEvent:
    user_id: str
    exercise: str
    time_done: int
    source_row: int
    correct: int
    suggested: int
    fold: int


@dataclass(frozen=True)
class LearnerEvents:
    user_id: str
    fold: int
    events: tuple[KTEvent, ...]


@dataclass(frozen=True)
class WindowSlice:
    start: int
    stop: int
    target_start: int
    global_ranks: np.ndarray
    unseen: bool
    barrier_applied: bool = False
    history_available: np.ndarray | None = None


@dataclass(frozen=True)
class WindowInputs:
    inputs: CausalSequenceInputs
    target_mask: np.ndarray
    global_ranks: np.ndarray
    history_available: np.ndarray
    history_used: np.ndarray
    context_reset: np.ndarray
    window_id: str


@dataclass(frozen=True)
class TrainingWindow:
    window: WindowInputs
    targets: np.ndarray


@dataclass(frozen=True)
class UnseenTarget:
    event: KTEvent
    global_rank: int


@dataclass(frozen=True)
class PredictionRecord:
    source_row: int
    user_id: str
    exercise: str
    time_done: int
    correct: int
    suggested: int
    fold: int
    prediction: float | None
    prediction_kind: str
    is_fallback: bool
    train_support_students: int
    history_available: int
    history_used: int
    context_reset: bool
    window_id: str
    checkpoint_id: str


WindowRecord = TrainingWindow | WindowInputs | UnseenTarget
