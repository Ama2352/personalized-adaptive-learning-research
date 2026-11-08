"""Controller V1 dùng reference correctness; không đọc latent state hoặc đáp án.

Tách khỏi selector Paper2 lịch sử. Caller phải probe và calibrate cùng prehistory,
sau đó predict served item trước interact/observe. Module chỉ chọn và bookkeep.
"""

from dataclasses import asdict, dataclass
import math
from numbers import Real

from .simulator_bridge import SimulatorBank, identity_hash


PROTOCOL_ID = 'S04A-S05B-GROUP-V1-20261108'
TAU_REFERENCE = 0.5637150147511514
TARGET_SUCCESS = 0.70
# Sai số tuyệt đối trên probability-distance; không chọn bằng nhiễu float.
ITEM_DISTANCE_TOLERANCE = 1e-12


def _sha(value):
    if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('expected SHA-256')


def _probability(value):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError('reference unsupported or invalid probability')
    return float(value)


@dataclass(frozen=True)
class ControllerState:
    concept_counts: tuple[tuple[str, int], ...] = ()
    item_counts: tuple[tuple[str, int], ...] = ()
    recent_concepts: tuple[str, ...] = ()
    current_chapter: str | None = None

    def __post_init__(self):
        for name in ('concept_counts', 'item_counts'):
            rows = tuple(getattr(self, name))
            if any(not isinstance(row, tuple) or len(row) != 2 or not isinstance(row[0], str)
                   or not row[0] or type(row[1]) is not int or row[1] < 0 for row in rows):
                raise ValueError('invalid controller counts')
            if len({key for key, _ in rows}) != len(rows):
                raise ValueError('duplicate controller count')
            object.__setattr__(self, name, tuple(sorted(rows)))
        recent = tuple(self.recent_concepts)
        if len(recent) > 3 or any(not isinstance(cid, str) or not cid for cid in recent):
            raise ValueError('invalid recent concepts')
        if self.current_chapter is not None and (not isinstance(self.current_chapter, str) or not self.current_chapter):
            raise ValueError('invalid chapter')
        object.__setattr__(self, 'recent_concepts', recent)


@dataclass(frozen=True)
class ControllerDecision:
    concept_id: str
    item_id: str
    next_state: ControllerState
    trace: dict


def select_from_reference_snapshot(*, bank: SimulatorBank, parents: dict, chapters: dict,
                                   state: ControllerState, history_sha256: str,
                                   reference_snapshot: dict) -> ControllerDecision:
    """Nối output score_reference_bank vào controller, giữ prehistory hiện hành.

    Caller vẫn phải predict served item rồi interact/observe; không dùng P trong
    snapshot để thay một served-item prediction ticket của OnlineSession.
    """
    if (not isinstance(reference_snapshot, dict)
            or reference_snapshot.get('recipe') != 'response-temperature-reference-v1'
            or reference_snapshot.get('tau_ref') != TAU_REFERENCE
            or reference_snapshot.get('total_concepts') != 28
            or reference_snapshot.get('supported_concepts') != 28
            or not isinstance(reference_snapshot.get('concepts'), dict)):
        raise ValueError('incomplete or incompatible calibrated reference snapshot')
    if len({item.concept_id for item in bank.items}) != 28:
        raise ValueError('V1 snapshot requires complete28concept bank')
    required = {'history_sha256', 'reference_history_sha256', 'bank_identity',
                'calibration_sha256', 'item_calibrated_probabilities'}
    if not required.issubset(reference_snapshot):
        raise ValueError('missing reference snapshot binding')
    if reference_snapshot['history_sha256'] != history_sha256:
        raise ValueError('stale reference snapshot')
    concept_scores = {}
    for cid, record in reference_snapshot['concepts'].items():
        if not isinstance(record, dict) or 'score' not in record:
            raise ValueError('invalid reference concept record')
        concept_scores[cid] = record['score']
    return select_reference_activity(bank=bank, parents=parents, chapters=chapters,
        concept_scores=concept_scores,
        item_probabilities=reference_snapshot['item_calibrated_probabilities'],
        state=state, history_sha256=history_sha256,
        reference_history_sha256=reference_snapshot['reference_history_sha256'],
        calibration_id=reference_snapshot['calibration_sha256'],
        reference_bank_identity=reference_snapshot['bank_identity'])


def select_reference_activity(*, bank: SimulatorBank, parents: dict, chapters: dict,
                              concept_scores: dict, item_probabilities: dict,
                              state: ControllerState, history_sha256: str,
                              reference_history_sha256: str, calibration_id: str,
                              reference_bank_identity: dict) -> ControllerDecision:
    """Chọn từ một full preselect probe; thiếu support thì dừng, không dùng0,5.

    identity/history kiểm sự nhất quán input, không chứng minh provenance của
    caller. Calibration pipeline chịu trách nhiệm fitted checkpoint/partition.
    Không mutate inputs, không gọi RNG/model/environment hoặc observe.
    """
    if not isinstance(bank, SimulatorBank) or not isinstance(state, ControllerState):
        raise ValueError('invalid bank or controller state')
    _sha(history_sha256)
    _sha(reference_history_sha256)
    _sha(calibration_id)
    if history_sha256 != reference_history_sha256 or bank.identity != reference_bank_identity:
        raise ValueError('reference history/bank mismatch')
    concepts = tuple(sorted({item.concept_id for item in bank.items}))
    if any(not isinstance(value, dict) for value in (parents, chapters, concept_scores, item_probabilities)):
        raise ValueError('expected explicit controller mappings')
    if set(parents) != set(concepts) or set(chapters) != set(concepts) or set(concept_scores) != set(concepts):
        raise ValueError('incomplete concept mappings or reference support')
    if set(item_probabilities) != set(bank.item_ids):
        raise ValueError('incomplete item reference support')
    scores = {cid: _probability(concept_scores[cid]) for cid in concepts}
    probabilities = {qid: _probability(value) for qid, value in item_probabilities.items()}
    for cid in concepts:
        if not isinstance(parents[cid], (list, tuple)) or len(set(parents[cid])) != len(parents[cid]):
            raise ValueError('invalid parent list')
        if any(parent not in concepts or parent == cid for parent in parents[cid]):
            raise ValueError('unknown parent or self edge')
        if not isinstance(chapters[cid], str) or not chapters[cid]:
            raise ValueError('invalid chapter mapping')
        items = [item.item_id for item in bank.items if item.concept_id == cid]
        if not math.isclose(scores[cid], sum(probabilities[qid] for qid in items) / len(items), rel_tol=0, abs_tol=1e-12):
            raise ValueError('concept score disagrees with equal-weight item reference')
    # Graph phải là DAG; không dùng fallback để giấu graph bị lỗi.
    visited, active = set(), set()
    def visit(cid):
        if cid in active:
            raise ValueError('cyclic controller graph')
        if cid not in visited:
            active.add(cid)
            for parent in parents[cid]:
                visit(parent)
            active.remove(cid)
            visited.add(cid)
    for cid in concepts:
        visit(cid)
    visits, item_visits = dict(state.concept_counts), dict(state.item_counts)
    if (set(visits) - set(concepts) or set(item_visits) - set(bank.item_ids)
            or set(state.recent_concepts) - set(concepts)
            or state.current_chapter is not None and state.current_chapter not in set(chapters.values())):
        raise ValueError('state outside controller domain')
    for cid in concepts:
        if visits.get(cid, 0) != sum(item_visits.get(item.item_id, 0) for item in bank.items if item.concept_id == cid):
            raise ValueError('concept/item bookkeeping mismatch')
    mastered = {cid: scores[cid] >= TAU_REFERENCE for cid in concepts}
    unmastered = [cid for cid in concepts if not mastered[cid]]
    eligible = lambda cid: all(mastered[parent] or visits.get(parent, 0) >= 6 for parent in parents[cid])
    raw_ready = [cid for cid in unmastered if eligible(cid)]
    ready = list(raw_ready)
    ready_reason = 'unmastered_prerequisites_satisfied'
    if not ready:
        if not unmastered:
            ready, ready_reason = list(concepts), 'all_mastered_review'
        else:
            deficits = {cid: sum(not mastered[parent] for parent in parents[cid]) for cid in unmastered}
            ready = [cid for cid in unmastered if deficits[cid] == min(deficits.values())]
            ready_reason = 'minimum_unresolved_prerequisites'
    candidates = list(ready)
    escape = 'none'
    if len(state.recent_concepts) == 3 and len(set(state.recent_concepts)) == 1:
        alternatives = [cid for cid in candidates if cid != state.recent_concepts[-1]]
        if alternatives:
            candidates, escape = alternatives, 'ready_alternative'
        else:
            alternatives = [cid for cid in concepts if cid != state.recent_concepts[-1] and eligible(cid)]
            if alternatives:
                candidates, escape = alternatives, 'spaced_review_outside_ready'
    minimum = min(visits.get(cid, 0) for cid in candidates)
    balanced = [cid for cid in candidates if visits.get(cid, 0) <= minimum + 1]
    keys = {cid: (scores[cid], 0 if chapters[cid] == state.current_chapter else 1,
                  visits.get(cid, 0), cid) for cid in balanced}
    chosen = min(balanced, key=keys.__getitem__)
    pool = [item.item_id for item in bank.items if item.concept_id == chosen]
    item_keys = {qid: (abs(probabilities[qid] - TARGET_SUCCESS), item_visits.get(qid, 0), qid) for qid in pool}
    nearest = min(item_keys[qid][0] for qid in pool)
    nearest_pool = [qid for qid in pool if item_keys[qid][0] <= nearest + ITEM_DISTANCE_TOLERANCE]
    qid = min(nearest_pool, key=lambda item: (item_visits.get(item, 0), item))
    visits[chosen] = visits.get(chosen, 0) + 1
    item_visits[qid] = item_visits.get(qid, 0) + 1
    next_state = ControllerState(tuple(visits.items()), tuple(item_visits.items()),
                                 (state.recent_concepts + (chosen,))[-3:], chapters[chosen])
    trace = {'controller_id': 'reference-controller-v1', 'protocol_id': PROTOCOL_ID,
             'phase': 'preselect_reference', 'history_sha256': history_sha256,
             'bank_identity': dict(bank.identity), 'calibration_id': calibration_id,
             'controller_graph_sha256': identity_hash({cid: sorted(parents[cid]) for cid in concepts}),
             'chapter_map_sha256': identity_hash(chapters),
             'state_before_sha256': identity_hash(asdict(state)),
             'state_after_sha256': identity_hash(asdict(next_state)),
             'mastered': mastered, 'raw_ready': raw_ready, 'ready': ready,
             'ready_reason': ready_reason, 'candidates': candidates, 'escape': escape,
             'balanced': balanced, 'selection_keys': keys, 'item_keys': item_keys,
             'nearest_item_pool': nearest_pool, 'item_distance_tolerance': ITEM_DISTANCE_TOLERANCE,
             'chosen_concept': chosen, 'chosen_item': qid,
             'concept_scores': scores, 'tau_reference': TAU_REFERENCE,
             'item_target_success': TARGET_SUCCESS, 'served_probability': None,
             'semantics': 'reference criterion, not latent mastery or served-item prediction'}
    trace['trace_sha256'] = identity_hash(trace)
    return ControllerDecision(chosen, qid, next_state, trace)
