"""Primitives theo PDF Paper1, không chạy matrix hoặc tái lập số lịch sử.

PDF SHA984e2f82…9167f4, tr.2–3 Eq.(3)–(9), Algorithm1 và IV.A.
Bank dưới đây là prospective input reuse, chưa chứng minh historical identity.
Profile Gaussian/RNG allocation, B0, unlock policy và runner50seeds chưa có ở đây.
Các primitives nhận state/input khai báo tường minh, không cấp quyền execution.
"""

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

from ..simulator_bridge import SimulatorBank, SimulatorItem


VERSION = 'paper1-pdf-primitives-v1'
PDF_SHA256 = '984e2f825968c212ca7e76db23a4c9501659ed880ecff6dce437590ad49167f4'
AUTHORITY_REFERENCE = 'D37'
MASTERY_ELO = 1250.0
DIFFICULTIES = (1050.0, 1200.0, 1350.0)
LATENT_GAIN = 12.0
LATENT_CAP = 1500.0
PROSPECTIVE_INPUT_VERSION = 'paper1-pdf-paper2-domain-candidate-v1'
PROSPECTIVE_INPUT_SHA256 = (
    ('nodes.csv', '6db464d1fd3df5d4215d51c9f90dc0f7e24f252517252784c80bdb5fa6291650'),
    ('question_bank.csv', 'fb5924ac0d19049ef1a5be23352592e30dfa3a4bde3e3fa07f10979fe0887e4d'),
    ('concept_to_chapter_map.csv', 'aa99cffb251ce6757258d2e87fe707455bc74b6b3917ead1acf48c5e96ee0a17'),
    ('edges_baseline.csv', '9d795fb88d00e5c2ec1d3b2215bb93038a944354c3c4709b6b0aa9d66906c39d'),
    ('edges.csv', 'ecd910d8df52f8790997391de657ea0f9e8357446212c168b73e500d0facc2fb'),
)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def elo_probability(ability: float, difficulty: float) -> float:
    """Eq.(5), sigmoid ổn định số học, không thêm probability clipping."""
    _require(_finite(ability) and _finite(difficulty), 'finite ability/difficulty required')
    logit = ((float(ability)-float(difficulty))/400.0)*math.log(10.0)
    if logit >= 0:
        return 1.0/(1.0+math.exp(-logit))
    value = math.exp(logit)
    return value/(1.0+value)


def dynamic_k(previous_interactions: int) -> float:
    """Eq.(7) dùng N trước update, N=15 đã thuộc mức16."""
    _require(type(previous_interactions) is int and previous_interactions >= 0, 'nonnegative previous count required')
    if previous_interactions < 5:
        return 40.0
    if previous_interactions < 15:
        return 24.0
    return 16.0


def _bank(bank):
    _require(type(bank) is SimulatorBank, 'explicit SimulatorBank required')
    grouped = {}
    for item in bank.items:
        grouped.setdefault(item.concept_id, []).append(item)
    _require(all(len(items) == 3 and tuple(sorted(item.difficulty for item in items)) == DIFFICULTIES
                 for items in grouped.values()), 'exact three fixed difficulties per concept required')
    return {item.item_id: item for item in bank.items}, tuple(sorted(grouped))


def _graph(nodes, chapters, edges, traversal_order):
    _require(isinstance(chapters, Mapping) and set(chapters) == set(nodes)
             and all(type(value) is str and value.strip() for value in chapters.values()),
             'exact concept chapter mapping required')
    order = tuple(traversal_order)
    _require(len(order) == len(set(order)) == len(nodes) and set(order) == set(nodes), 'explicit stable full traversal order required')
    pairs = tuple(edges)
    _require(all(type(pair) is tuple and len(pair) == 2 and pair[0] in nodes and pair[1] in nodes
                 and pair[0] != pair[1] for pair in pairs) and len(set(pairs)) == len(pairs), 'unique declared graph edges required')
    parents = {node: set() for node in nodes}
    for parent, child in pairs:
        parents[child].add(parent)
    remaining = set(nodes)
    while remaining:
        roots = {node for node in remaining if not parents[node].intersection(remaining)}
        _require(roots, 'graph must be a DAG')
        remaining.difference_update(roots)
    return {node: tuple(sorted(values)) for node, values in parents.items()}, order


def validate_prospective_domain(bank: SimulatorBank, *, chapters: Mapping[str, str],
                                baseline_edges: Sequence[tuple[str, str]], advanced_edges: Sequence[tuple[str, str]]) -> dict:
    """Kiểm shape prospective28/84/25/31, không đọc hoặc chứng nhận bytes CSV."""
    _, nodes = _bank(bank)
    _require(isinstance(chapters, Mapping) and len(nodes) == 28 and len(bank.items) == 84
             and len(set(chapters.values())) == 3, 'PDF28concept/84item/3chapter domain required')
    _graph(nodes, chapters, baseline_edges, nodes)
    _graph(nodes, chapters, advanced_edges, nodes)
    baseline, advanced = set(baseline_edges), set(advanced_edges)
    _require(len(baseline) == 25 and len(advanced) == 31 and baseline < advanced, 'declared25/31 graphs with baseline subset required')
    intra = lambda pair: chapters[pair[0]] == chapters[pair[1]]
    _require(all(intra(pair) for pair in baseline) and sum(intra(pair) for pair in advanced) == 28
             and sum(intra(pair) for pair in advanced-baseline) == 3, 'exact3intra+3cross additions required')
    return dict(version=PROSPECTIVE_INPUT_VERSION, concepts=28, items=84, baseline_edges=25, advanced_edges=31,
                added_intra=3, added_cross=3, source_bytes_verified=False, historical_identity_claimed=False)


@dataclass(frozen=True)
class Prediction:
    step: int
    item_id: str
    concept_id: str
    chapter: str
    difficulty: float
    probability: float
    estimated_before: float
    previous_interactions: int


class Paper1PdfController:
    """Continuity/Elo state riêng, không giữ learner/world hoặc latent values.

    Fixture domain có thể nhỏ. Canonical28/25/31 cần validation/input hash riêng.
    Có một prediction pending, counts chỉ commit khi observe hợp lệ.
    """
    def __init__(self, bank: SimulatorBank, *, chapters: Mapping[str, str], edges: Sequence[tuple[str, str]],
                 traversal_order: Sequence[str], initial_estimates: Mapping[str, float]):
        self._items, self._nodes = _bank(bank)
        self._parents, self._order = _graph(self._nodes, chapters, edges, traversal_order)
        _require(isinstance(initial_estimates, Mapping) and set(initial_estimates) == set(self._nodes)
                 and all(_finite(v) for v in initial_estimates.values()),
                 'explicit finite initial estimates for every concept required')
        self._bank = bank
        self._chapters = dict(chapters)
        self._estimated = {node: float(initial_estimates[node]) for node in self._nodes}
        self._attempts = dict.fromkeys(self._nodes, 0)
        self._exposures = dict.fromkeys(self._items, 0)
        self._current_chapter = None
        self._history = []
        self._pending = None
        self._pending_payload = None

    def ready_set(self) -> tuple[str, ...]:
        return tuple(node for node in self._order if self._estimated[node] < MASTERY_ELO
                     and all(self._estimated[parent] >= MASTERY_ELO for parent in self._parents[node]))

    def predict_next(self) -> Prediction | None:
        _require(self._pending is None, 'observe the pending prediction before selecting again')
        ready = self.ready_set()
        if not ready:
            return None
        local = tuple(node for node in ready if self._chapters[node] == self._current_chapter)
        candidates = local or ready
        rank = {node: index for index, node in enumerate(self._order)}
        node = min(candidates, key=lambda value: (self._estimated[value], rank[value]))
        item = min((item for item in self._items.values() if item.concept_id == node),
                   key=lambda value: (abs(value.difficulty-self._estimated[node]), self._exposures[value.item_id], value.item_id))
        self._pending = Prediction(len(self._history)+1, item.item_id, node, self._chapters[node], item.difficulty,
            elo_probability(self._estimated[node], item.difficulty), self._estimated[node], self._attempts[node])
        self._pending_payload = tuple(vars(self._pending).items())
        return self._pending

    def observe(self, prediction: Prediction, correct: int) -> None:
        _require(type(correct) is int and correct in (0, 1), 'binary observed response required')
        _require(type(prediction) is Prediction and prediction is self._pending, 'exact pending prediction required')
        _require(tuple(vars(prediction).items()) == self._pending_payload, 'original pending payload changed')
        _require(type(prediction.item_id) is str and prediction.item_id in self._items
                 and prediction.concept_id == self._items[prediction.item_id].concept_id
                 and _finite(prediction.probability) and 0 <= prediction.probability <= 1
                 and _finite(prediction.estimated_before) and _finite(prediction.difficulty),
                 'finite pending prediction and bound item required')
        node = prediction.concept_id
        _require(type(prediction.step) is int and prediction.step == len(self._history)+1
                 and prediction.estimated_before == self._estimated[node]
                 and type(prediction.previous_interactions) is int and prediction.previous_interactions == self._attempts[node]
                 and prediction.chapter == self._chapters[node]
                 and prediction.difficulty == self._items[prediction.item_id].difficulty
                 and prediction.probability == elo_probability(self._estimated[node], prediction.difficulty),
                 'stale or changed prediction before update')
        updated = self._estimated[node] + dynamic_k(self._attempts[node])*(correct-prediction.probability)
        _require(_finite(updated), 'finite updated estimate required')
        self._estimated[node] = updated
        self._attempts[node] += 1
        self._exposures[prediction.item_id] += 1
        self._current_chapter = self._chapters[node]
        self._history.append(self._current_chapter)
        self._pending = None
        self._pending_payload = None

    def snapshot(self) -> dict:
        return dict(version=VERSION, bank_identity=self._bank.identity, estimated_elo=dict(self._estimated),
                    concept_attempts=dict(self._attempts), item_exposures=dict(self._exposures),
                    current_chapter=self._current_chapter, chapter_history=tuple(self._history),
                    committed_interactions=len(self._history), pending_prediction=self._pending)

    def metrics(self) -> dict:
        visited = set()
        previous = None
        switches = reentries = 0
        for chapter in self._history:
            if previous is not None and chapter != previous:
                switches += 1
                reentries += chapter in visited
            visited.add(chapter)
            previous = chapter
        mastered = sum(value >= MASTERY_ELO for value in self._estimated.values())
        return dict(interactions=len(self._history), chapter_switches=switches, chapter_reentry=reentries,
                    estimated_mastered_concepts=mastered, concept_denominator=len(self._nodes),
                    estimated_mastery_rate=mastered/len(self._nodes))


@dataclass(frozen=True)
class WorldResponse:
    item_id: str
    concept_id: str
    correct: int
    probability_true: float
    latent_before: float
    latent_after: float


class Paper1PdfLearner:
    """World riêng, caller cấp uniform. Không tự chọn RNG/Gaussian profile.

    Không clip supplied initial latent. Cap được hiểu literal min(1500,before+12)
    sau feedback. Nếu initial>1500 thì bước cap có thể giảm giá trị, cần giữ rõ
    khi profile generator tương lai chốt Gaussian-tail convention.
    """
    def __init__(self, bank: SimulatorBank, *, initial_latent: Mapping[str, float]):
        self._items, nodes = _bank(bank)
        _require(isinstance(initial_latent, Mapping) and set(initial_latent) == set(nodes)
                 and all(_finite(v) for v in initial_latent.values()),
                 'explicit finite latent state for every concept required')
        self._latent = {node: float(initial_latent[node]) for node in nodes}
        self._interactions = 0

    def respond(self, item_id: str, *, outcome_uniform: float) -> WorldResponse:
        _require(type(item_id) is str and item_id in self._items and _finite(outcome_uniform) and 0 <= outcome_uniform < 1,
                 'known item and explicit uniform in[0,1) required')
        item = self._items[item_id]
        before = self._latent[item.concept_id]
        probability = elo_probability(before, item.difficulty)
        correct = int(outcome_uniform < probability)
        after = min(LATENT_CAP, before+LATENT_GAIN)
        self._latent[item.concept_id] = after
        self._interactions += 1
        return WorldResponse(item.item_id, item.concept_id, correct, probability, before, after)

    def diagnostic_snapshot(self) -> dict:
        return dict(latent_ability=dict(self._latent), interactions=self._interactions,
                    role='WORLD_ORACLE_DIAGNOSTIC_ONLY', initial_latent_clipped=False,
                    post_feedback_cap='min(1500,latent_before+12)')
