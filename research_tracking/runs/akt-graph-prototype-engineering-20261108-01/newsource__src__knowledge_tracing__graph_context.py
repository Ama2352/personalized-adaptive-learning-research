"""Audit graph context past-only; chưa là augmentation, gate hay KT mastery.

Effective window gọi geometry thật của AKT. Full history chỉ sensitivity có nhãn.
Confidence provenance là khai báo cần đối chiếu artifacts, không là calibration.
"""

from dataclasses import asdict, dataclass
import math
from numbers import Real

import numpy as np

from .akt.windows import iter_window_slices
from .shared_kt import PrerequisiteGraph
from .simulator_bridge import ItemQuery, Observation, SimulatorBank, identity_hash


@dataclass(frozen=True)
class EdgeConfidence:
    kind: str
    values: tuple[tuple[str, str, float], ...]
    provenance_sha256: str
    fitted_role: str | None = None

    def __post_init__(self):
        if self.kind not in {'fixed_uniform', 'structural_score', 'estimated_probability', 'oracle_label'}:
            raise ValueError('unknown edge confidence kind')
        if (not isinstance(self.provenance_sha256, str) or len(self.provenance_sha256) != 64
                or any(c not in '0123456789abcdef' for c in self.provenance_sha256)):
            raise ValueError('confidence requires provenance SHA-256')
        if self.fitted_role != ('train' if self.kind == 'estimated_probability' else None):
            raise ValueError('estimated confidence must be train-only; other kinds are not fitted')
        values = []
        for parent, child, value in self.values:
            if (not isinstance(parent, str) or not parent or not isinstance(child, str) or not child
                    or isinstance(value, bool) or not isinstance(value, Real)
                    or not math.isfinite(value) or not 0 <= value <= 1):
                raise ValueError('invalid edge confidence')
            if self.kind == 'fixed_uniform' and value != 1:
                raise ValueError('fixed-uniform confidence must equal one')
            if self.kind == 'oracle_label' and value not in (0, 1):
                raise ValueError('oracle reference labels must be binary')
            values.append((parent, child, float(value)))
        if len({(p, c) for p, c, _ in values}) != len(values):
            raise ValueError('duplicate edge confidence')
        object.__setattr__(self, 'values', tuple(sorted(values)))

    @property
    def identity(self):
        return identity_hash(asdict(self))


def audit_graph_context(*, bank: SimulatorBank, graph: PrerequisiteGraph, confidence: EdgeConfidence,
                        history: tuple[Observation, ...], query: ItemQuery, trained_items,
                        context: int, target_block: int, scope='effective_window', enabled=True,
                        purpose='matched_audit'):
    """Trả support/mean observed correctness, không tạo probability/gate/logit.

Không nhận outcome của query. OOV target không được graph rescue vì baseline
không có fitted prediction. History ngoài effective window chỉ dùng sensitivity.
"""
    if (type(context) is not int or context < 0 or type(target_block) is not int or target_block < 1
            or type(enabled) is not bool):
        raise ValueError('invalid context configuration')
    if scope not in {'effective_window', 'full_history'} or purpose not in {
            'matched_audit', 'history_sensitivity', 'oracle_reference'}:
        raise ValueError('invalid context scope/purpose')
    if scope == 'full_history' and purpose not in {'history_sensitivity', 'oracle_reference'}:
        raise ValueError('full history requires explicit sensitivity/reference purpose')
    if confidence.kind == 'oracle_label' and purpose != 'oracle_reference':
        raise ValueError('oracle confidence is restricted to reference mode')
    canonical = PrerequisiteGraph.from_edges(graph.nodes, graph.edges)
    concepts = {item.concept_id for item in bank.items}
    if graph != canonical or not set(graph.nodes).issubset(concepts):
        raise ValueError('graph direction, canonical form or concept domain mismatch')
    weights = {(p, c): value for p, c, value in confidence.values}
    if set(weights) != set(graph.edges):
        raise ValueError('confidence must cover exactly the declared edges')
    vocabulary = tuple(trained_items)
    if (not vocabulary or len(set(vocabulary)) != len(vocabulary)
            or not set(vocabulary).issubset(bank.item_ids)):
        raise ValueError('invalid trained item vocabulary')
    if not isinstance(query, ItemQuery) or any(not isinstance(item, Observation) for item in history):
        raise ValueError('invalid query/history schema')
    queries = [item.query for item in history] + [query]
    previous, rows = None, set()
    for item in queries:
        key = item.timestamp, item.source_row
        if item.item_id not in bank.item_ids or item.source_row in rows or (previous is not None and key <= previous):
            raise ValueError('query/history chronology, row or domain violation')
        rows.add(item.source_row)
        previous = key
    ids = np.asarray([0 if item.item_id in vocabulary else -1 for item in queries], dtype=np.int64)
    # Chỉ membership quan trọng cho geometry; không cấp numerical ID giả cho model.
    geometry = list(iter_window_slices(ids, np.asarray([0, len(ids)], dtype=np.int64),
                                     context=context, target_block=target_block))[-1]
    fitted = not geometry.unseen
    start = geometry.start if scope == 'effective_window' else 0
    observations = tuple(history[start:]) if fitted else ()
    mapping = {item.item_id: item.concept_id for item in bank.items}
    child = mapping[query.item_id]
    parents = []
    if enabled and fitted:
        for parent, dependent in graph.edges:
            if dependent != child:
                continue
            responses = [o.correct for o in observations if mapping[o.query.item_id] == parent]
            parents.append({'parent': parent, 'support': len(responses), 'confidence': weights[parent, child],
                            'mean_observed_correctness': sum(responses) / len(responses) if responses else None})
    normalizer = sum(p['confidence'] for p in parents if p['support'])
    weighted = (sum(p['confidence'] * p['mean_observed_correctness'] for p in parents if p['support'])
                / normalizer) if normalizer else None
    return {'schema_version': 1, 'scope': scope, 'purpose': purpose, 'enabled': enabled,
            'information_matched': scope == 'effective_window', 'target_fitted': fitted,
            'global_rank': len(history), 'effective_start': geometry.start, 'scope_start': start,
            'query': asdict(query), 'context': context, 'target_block': target_block,
            'trained_items_sha256': identity_hash(sorted(vocabulary)),
            'context_reset': bool(geometry.barrier_applied or geometry.unseen),
            'observed_rows': [o.query.source_row for o in observations],
            'parents': parents, 'weighted_observed_correctness': weighted,
            'observed_confidence_mass': normalizer,
            'graph_sha256': identity_hash(asdict(graph)), 'confidence_sha256': confidence.identity,
            'domain_sha256': identity_hash(bank.identity),
            'scoped_observations_sha256': identity_hash([asdict(o) for o in observations]),
            'scope_limit': 'diagnostic support only; no mastery, calibrated confidence or trained augmentation'}
