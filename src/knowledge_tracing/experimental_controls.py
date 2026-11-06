"""Hợp đồng đối chiếu factorial theo cùng latent state và random streams."""

from dataclasses import dataclass
import math
from typing import Sequence


@dataclass(frozen=True)
class FactorialOutcome:
    seed: int
    profile: str
    graph_on: bool
    prerequisite_mechanism_on: bool
    latent_identity: str
    random_stream_identity: str
    outcome: float


def paired_mechanism_contrasts(rows: Sequence[FactorialOutcome]) -> list[dict]:
    """Tính (on-off)|mechanism_on trừ (on-off)|mechanism_off.

    Kết quả là interaction contrast. Việc diễn giải nhân quả phụ thuộc thiết kế
    simulator và tính đúng đắn của identity do caller cung cấp.
    """
    if not rows:
        raise ValueError('empty factorial outcomes')
    groups = {}
    for row in rows:
        if (type(row.seed) is not int or not row.profile or not row.latent_identity
                or not row.random_stream_identity or not math.isfinite(row.outcome)
                or type(row.graph_on) is not bool or type(row.prerequisite_mechanism_on) is not bool):
            raise ValueError('invalid factorial outcome')
        group = groups.setdefault((row.seed, row.profile), {})
        condition = row.graph_on, row.prerequisite_mechanism_on
        if condition in group:
            raise ValueError('duplicate factorial condition')
        group[condition] = row
    results = []
    for (seed, profile), group in sorted(groups.items()):
        if len(group) != 4:
            raise ValueError('missing factorial condition')
        if (len({r.latent_identity for r in group.values()}) != 1
                or len({r.random_stream_identity for r in group.values()}) != 1):
            raise ValueError('unpaired latent states or random streams')
        delta_on = group[True, True].outcome - group[False, True].outcome
        delta_off = group[True, False].outcome - group[False, False].outcome
        results.append({'seed': seed, 'profile': profile,
                        'graph_effect_mechanism_on': delta_on,
                        'graph_effect_mechanism_off': delta_off,
                        'interaction_contrast': delta_on - delta_off})
    return results
