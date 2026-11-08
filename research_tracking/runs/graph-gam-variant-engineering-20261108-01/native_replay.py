"""Sequential one-step-ahead prediction/update semantics."""

from __future__ import annotations

import math


def predict_then_update(model, exercise, problem_type, difficulty, timestamp, correct) -> float:
    prediction = float(model.predict(exercise, problem_type, difficulty, timestamp))
    if not math.isfinite(prediction) or not 0.0 <= prediction <= 1.0:
        raise FloatingPointError(f"Invalid GAM-KT probability: {prediction}")
    model.update(exercise, problem_type, difficulty, timestamp, int(correct), prediction)
    return prediction
