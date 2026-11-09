"""Episode continuity prospective theo PDF, caller cấp draws, không sở hữu RNG.

Không chạy matrix hoặc xác nhận lịch sử. Profile/tape dựng tay không chứng minh
phân phối Gaussian; oracle chỉ được world dùng và xuất ở sidecar riêng.
"""

from collections.abc import Mapping
from dataclasses import asdict, dataclass
import math

from ..simulator_bridge import identity_hash
from .simulator import Paper1PdfController, Paper1PdfLearner, _bank

VERSION = 'paper1-pdf-continuity-supplied-episode-v1'


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _domain(bank, chapters):
    _, nodes = _bank(bank)
    _need(1 <= len(nodes) <= 28 and isinstance(chapters, Mapping) and set(chapters) == set(nodes)
          and all(type(value) is str and value.strip() for value in chapters.values()),
          'bounded bank and exact explicit chapter map required')
    return nodes, tuple((node, chapters[node]) for node in nodes)


@dataclass(frozen=True)
class InitialProfile:
    bank_sha256: str
    chapters: tuple[tuple[str, str], ...]
    persona: str
    function_chapter: str
    normal_z: tuple[tuple[str, float], ...]
    initial_latent: tuple[tuple[str, float], ...]
    initial_estimates: tuple[tuple[str, float], ...]

    @property
    def identity(self):
        return identity_hash(asdict(self))


def initialize_profile(bank, *, chapters, persona, function_chapter, normal_z_by_node) -> InitialProfile:
    """Scale/shift supplied z theo IV.A; không clip initial latent hoặc tự rút mẫu."""
    nodes, chapter_pairs = _domain(bank, chapters)
    _need(persona in ('US', 'UW', 'FW') and type(persona) is str, 'explicit PDF persona required')
    _need(type(function_chapter) is str and function_chapter in dict(chapter_pairs).values(),
          'explicit existing function chapter required')
    _need(isinstance(normal_z_by_node, Mapping) and set(normal_z_by_node) == set(nodes)
          and all(_finite(value) for value in normal_z_by_node.values()), 'exact finite supplied z required')
    latent, estimates, z_pairs = [], [], []
    for node, chapter in chapter_pairs:
        function_weak = persona == 'FW' and chapter == function_chapter
        if persona == 'US':
            mean = 1400.
        elif persona == 'UW':
            mean = 1050.
        else:
            mean = 1000. if function_weak else 1250.
        z = float(normal_z_by_node[node])
        value = mean+50.*z
        _need(math.isfinite(value), 'finite initialized latent required')
        z_pairs.append((node, z))
        latent.append((node, value))
        estimates.append((node, 1050. if function_weak else 1200.))
    return InitialProfile(identity_hash(bank.identity), chapter_pairs, persona, function_chapter,
                          tuple(z_pairs), tuple(latent), tuple(estimates))


@dataclass(frozen=True)
class ObservableInteraction:
    step: int
    item_id: str
    concept_id: str
    chapter: str
    difficulty: float
    probability: float
    estimated_before: float
    previous_interactions: int
    previous_item_exposures: int
    correct: int
    estimated_after: float


@dataclass(frozen=True)
class OracleInteraction:
    step: int
    item_id: str
    concept_id: str
    probability_true: float
    latent_before: float
    latent_after: float


@dataclass(frozen=True)
class SuppliedEpisode:
    version: str
    profile_sha256: str
    graph_sha256: str
    horizon: int
    stop_reason: str
    budget_exhausted: bool
    observable: tuple[ObservableInteraction, ...]
    oracle: tuple[OracleInteraction, ...]
    final_estimates: tuple[tuple[str, float], ...]
    final_latent: tuple[tuple[str, float], ...]
    concept_attempts: tuple[tuple[str, int], ...]
    item_exposures: tuple[tuple[str, int], ...]
    metrics: tuple[tuple[str, int | float], ...]

    @property
    def identity(self):
        return identity_hash(asdict(self))


def run_continuity_episode_supplied(bank, profile, *, chapters, edges, traversal_order,
                                    response_uniforms_by_node, horizon) -> SuppliedEpisode:
    """Một episode với tape đúng horizon/node, index theo concept N trước update.

    Mọi tape được kiểm/copy trước khi tạo controller/world. Hàm sở hữu các state
    mới, không sửa bank/profile/tape caller. Không cấp RNG hoặc quyền matrix.
    """
    nodes, chapter_pairs = _domain(bank, chapters)
    _need(type(horizon) is int and 1 <= horizon <= 500, 'explicit horizon1..500 required')
    _need(type(profile) is InitialProfile, 'supplied InitialProfile required')
    expected = initialize_profile(bank, chapters=dict(chapter_pairs), persona=profile.persona,
        function_chapter=profile.function_chapter, normal_z_by_node=dict(profile.normal_z))
    _need(profile == expected, 'profile bank/chapter/derived-state binding changed')
    _need(isinstance(response_uniforms_by_node, Mapping) and set(response_uniforms_by_node) == set(nodes),
          'exact response tape node set required')
    tape = {}
    for node in nodes:
        values = response_uniforms_by_node[node]
        _need(type(values) in (tuple, list) and len(values) == horizon
              and all(_finite(value) and 0 <= value < 1 for value in values),
              'exact horizon of finite response uniforms in[0,1) required')
        tape[node] = tuple(float(value) for value in values)
    _need(type(edges) in (tuple, list) and len(edges) <= len(nodes)*(len(nodes)-1)
          and all(type(pair) in (tuple, list) and len(pair) == 2 for pair in edges), 'bounded explicit edges required')
    _need(type(traversal_order) in (tuple, list) and len(traversal_order) == len(nodes),
          'explicit complete traversal order required')
    graph_edges = tuple(tuple(pair) for pair in edges)
    order = tuple(traversal_order)
    controller = Paper1PdfController(bank, chapters=dict(chapter_pairs), edges=graph_edges,
        traversal_order=order, initial_estimates=dict(profile.initial_estimates))
    world = Paper1PdfLearner(bank, initial_latent=dict(profile.initial_latent))
    observable, oracle = [], []
    for _ in range(horizon):
        before = controller.snapshot()
        prediction = controller.predict_next()
        if prediction is None:
            break
        uniform = tape[prediction.concept_id][prediction.previous_interactions]
        response = world.respond(prediction.item_id, outcome_uniform=uniform)
        controller.observe(prediction, response.correct)
        after = controller.snapshot()
        observable.append(ObservableInteraction(prediction.step, prediction.item_id, prediction.concept_id,
            prediction.chapter, prediction.difficulty, prediction.probability, prediction.estimated_before,
            prediction.previous_interactions, before['item_exposures'][prediction.item_id], response.correct,
            after['estimated_elo'][prediction.concept_id]))
        oracle.append(OracleInteraction(prediction.step, prediction.item_id, prediction.concept_id,
            response.probability_true, response.latent_before, response.latent_after))
    final = controller.snapshot()
    complete = not controller.ready_set()
    return SuppliedEpisode(VERSION, profile.identity,
        identity_hash(dict(bank=bank.identity, chapters=chapter_pairs, edges=graph_edges, traversal_order=order)),
        horizon, 'ALL_ESTIMATED_MASTERED' if complete else 'HORIZON_REACHED', len(observable) == horizon,
        tuple(observable), tuple(oracle), tuple(sorted(final['estimated_elo'].items())),
        tuple(sorted(world.diagnostic_snapshot()['latent_ability'].items())),
        tuple(sorted(final['concept_attempts'].items())), tuple(sorted(final['item_exposures'].items())),
        tuple(sorted(controller.metrics().items())))
