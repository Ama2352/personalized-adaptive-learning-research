"""Đo chuỗi quyết định trên paired trace, tách probability khỏi mastery."""

from dataclasses import dataclass
import math
from typing import Mapping, Sequence


@dataclass(frozen=True)
class DecisionTrace:
    event_id: str
    learner_id: str
    correct: int
    probability: float | None
    mastery: Mapping[str, float]
    ready: frozenset[str]
    action: str | None
    mastered: frozenset[str] | None = None


def _validate(trace: DecisionTrace) -> None:
    if not trace.event_id or not trace.learner_id or trace.correct not in (0, 1):
        raise ValueError('invalid event identity or label')
    values = list(trace.mastery.values())
    if trace.probability is not None:
        values.append(trace.probability)
    if any(not math.isfinite(p) or not 0 <= p <= 1 for p in values):
        raise ValueError('invalid probability or mastery score')
    if not trace.mastery or not trace.ready.issubset(trace.mastery):
        raise ValueError('invalid concept coverage')
    if trace.action is not None and trace.action not in trace.ready:
        raise ValueError('action outside ready set')
    if trace.mastered is not None and not trace.mastered.issubset(trace.mastery):
        raise ValueError('invalid explicit mastery decisions')


def compare_decision_traces(reference: Sequence[DecisionTrace],
                            candidate: Sequence[DecisionTrace], *, threshold: float,
                            calibration_band: float = 0.05) -> dict:
    """So trace cùng stream. Calibration dùng correctness, không dùng latent mastery.

    Action là concept ID. Caller chịu trách nhiệm tạo trace trước update.
    Summary mô tả paired rows, không cung cấp CI theo event độc lập.
    """
    if not 0 < threshold < 1 or not 0 < calibration_band <= 1:
        raise ValueError('invalid threshold or calibration band')
    if not reference or len(reference) != len(candidate):
        raise ValueError('paired trace coverage mismatch')
    seen = set()
    crossings = concept_rows = ready_changes = action_changes = 0
    probability_rows = probability_changes = 0
    absolute_delta = loss_delta = brier_delta = jaccard_sum = 0.0
    local = {'reference': [], 'candidate': []}
    for left, right in zip(reference, candidate):
        _validate(left)
        _validate(right)
        key = (left.learner_id, left.event_id)
        if key in seen:
            raise ValueError('duplicate event identity')
        seen.add(key)
        if (key != (right.learner_id, right.event_id) or left.correct != right.correct
                or set(left.mastery) != set(right.mastery)):
            raise ValueError('paired identity, label or concept mismatch')
        concept_rows += len(left.mastery)
        if (left.mastered is None) != (right.mastered is None):
            raise ValueError('mastery decision semantics mismatch')
        if left.mastered is not None:
            crossings += len(left.mastered ^ right.mastered)
        else:
            crossings += sum((p >= threshold) != (right.mastery[c] >= threshold)
                             for c, p in left.mastery.items())
        ready_changes += left.ready != right.ready
        action_changes += left.action != right.action
        union = left.ready | right.ready
        jaccard_sum += len(left.ready & right.ready) / len(union) if union else 1.0
        if left.probability is None or right.probability is None:
            continue
        a, b, y = left.probability, right.probability, left.correct
        probability_rows += 1
        probability_changes += a != b
        absolute_delta += abs(a - b)
        a_clip, b_clip = [min(1 - 1e-15, max(1e-15, p)) for p in (a, b)]
        loss_delta += (-y * math.log(b_clip) - (1-y) * math.log(1-b_clip)
                       + y * math.log(a_clip) + (1-y) * math.log(1-a_clip))
        brier_delta += (b-y)**2 - (a-y)**2
        for name, probability in (('reference', a), ('candidate', b)):
            if abs(probability - threshold) <= calibration_band:
                local[name].append((probability, y))
    def average(value):
        return value / probability_rows if probability_rows else None
    calibration = {}
    for name, rows in local.items():
        calibration[name] = {'rows': len(rows),
                             'signed_calibration_gap': sum(p-y for p,y in rows)/len(rows) if rows else None}
    return {'paired_events': len(reference), 'paired_supported_probability_rows': probability_rows,
            'unsupported_probability_pairs': len(reference)-probability_rows,
            'changed_probability_rows': probability_changes,
            'mean_absolute_probability_delta': average(absolute_delta),
            'candidate_minus_reference_log_loss': average(loss_delta),
            'candidate_minus_reference_brier': average(brier_delta),
            'concept_decisions': concept_rows, 'mastery_crossings': crossings,
            'changed_ready_sets': ready_changes, 'mean_ready_jaccard': jaccard_sum/len(reference),
            'changed_actions': action_changes, 'threshold_local_calibration': calibration,
            'scope': 'paired descriptive trace, learner/seed inference required separately'}
