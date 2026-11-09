"""Private RNG prospective cho episode continuity, không tái lập draws lịch sử.

Key tách persona/init/response; các branch chung replicate chia sẻ u tại cùng
concept-local practice count. Provenance được đọc khi prepare/run tường minh.
"""

from dataclasses import asdict, dataclass, replace
import hashlib
import json
from pathlib import Path
import random
import re
import sys

from ..simulator_bridge import SimulatorBank, identity_hash
from .episode import InitialProfile, SuppliedEpisode, initialize_profile, run_continuity_episode_supplied

RECIPE = 'paper1-pdf-keyed-private-random-v1'


def _need(ok, message):
    if not ok:
        raise ValueError(message)


@dataclass(frozen=True)
class RNGProvenance:
    implementation: str
    python_version: tuple[int, int, int, str, int]
    python_build: str
    executable: str
    prefix: str
    random_source_path: str
    random_source_sha256: str


def _runtime_provenance():
    path = Path(random.__file__).resolve()
    _need(path.is_file() and path.stat().st_size <= 131072, 'bounded actual random source required')
    with path.open('rb') as stream:
        raw = stream.read(131073)
    _need(len(raw) == path.stat().st_size and len(raw) <= 131072, 'stable random source bytes required')
    return RNGProvenance(sys.implementation.name, tuple(sys.version_info), sys.version,
        sys.executable, sys.prefix, str(path), hashlib.sha256(raw).hexdigest())


def _request(bank, chapters, persona, function_chapter, root_seed, replicate_id, horizon):
    _need(type(root_seed) is int and 0 <= root_seed < 2**63, 'explicit integer root seed0..2**63-1 required')
    _need(type(replicate_id) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,79}', replicate_id),
          'explicit bounded logical replicate ID required')
    _need(type(horizon) is int and 1 <= horizon <= 500, 'explicit horizon1..500 required')
    _need(type(bank) is SimulatorBank and 1 <= len(bank.items) <= 84, 'bounded explicit simulator bank required')
    nodes = tuple(sorted({item.concept_id for item in bank.items}))
    # Existing initializer validates domain, persona and chapter before any RNG.
    checked = initialize_profile(bank, chapters=chapters, persona=persona, function_chapter=function_chapter,
                                 normal_z_by_node=dict.fromkeys(nodes, 0.))
    return nodes, checked.chapters


def _event_seed(*, root_seed, replicate_id, persona, event, concept_id, previous_interactions=None):
    key = dict(version=RECIPE, root_seed=root_seed, replicate_id=replicate_id,
               persona=persona, event=event, concept_id=concept_id)
    if previous_interactions is not None:
        key['previous_interactions'] = previous_interactions
    raw = json.dumps(key, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    return int.from_bytes(hashlib.sha256(raw).digest(), 'big')


def _random_for_event(**key):
    return random.Random(_event_seed(**key))


@dataclass(frozen=True)
class SeededDraws:
    recipe: str
    root_seed: int
    replicate_id: str
    horizon: int
    profile: InitialProfile
    response_uniforms: tuple[tuple[str, tuple[float, ...]], ...]
    runtime: RNGProvenance
    content_sha256: str

    def _payload(self):
        value = asdict(self)
        value.pop('content_sha256')
        return value

    @property
    def identity(self):
        _need(self.recipe == RECIPE and type(self.profile) is InitialProfile
              and type(self.runtime) is RNGProvenance, 'typed prospective draw recipe required')
        _need(self.content_sha256 == identity_hash(self._payload()), 'prepared draw content changed')
        return self.content_sha256

    @property
    def logical_draw_counts(self):
        return dict(initial_normal_events=len(self.profile.normal_z),
                    response_uniform_events=len(self.response_uniforms)*self.horizon)


def prepare_seeded_draws(bank, *, chapters, persona, function_chapter, root_seed, replicate_id, horizon) -> SeededDraws:
    """Mỗi key có Random riêng; profile/tape bất biến, không seed global RNG.

    Fields/seal là consistency contract, không chứng nhận chống caller giả toàn
    bộ metadata hoặc chứng minh statistical independence trên sample hữu hạn.
    """
    nodes, chapter_pairs = _request(bank, chapters, persona, function_chapter, root_seed, replicate_id, horizon)
    runtime = _runtime_provenance()
    common = dict(root_seed=root_seed, replicate_id=replicate_id, persona=persona)
    z = {}
    for node in nodes:
        z[node] = _random_for_event(**common, event='initial_normal', concept_id=node).gauss(0., 1.)
    profile = initialize_profile(bank, chapters=dict(chapter_pairs), persona=persona, function_chapter=function_chapter,
                                 normal_z_by_node=z)
    uniforms = tuple((node, tuple(_random_for_event(**common, event='response_uniform', concept_id=node,
        previous_interactions=n).random() for n in range(horizon))) for node in nodes)
    _need(_runtime_provenance() == runtime, 'runtime/random source changed during preparation')
    pending = SeededDraws(RECIPE, root_seed, replicate_id, horizon, profile, uniforms, runtime, '')
    return replace(pending, content_sha256=identity_hash(pending._payload()))


@dataclass(frozen=True)
class SeededContinuityEpisode:
    draws_sha256: str
    result: SuppliedEpisode

    @property
    def identity(self):
        return identity_hash(dict(draws_sha256=self.draws_sha256, result_sha256=self.result.identity))


def run_continuity_episode_seeded(bank, *, chapters, edges, traversal_order, draws) -> SeededContinuityEpisode:
    """Delegation duy nhất tới supplied core; graph/policy không vào RNG keys."""
    _need(type(draws) is SeededDraws, 'prepared immutable seeded draws required')
    digest = draws.identity
    _, chapter_pairs = _request(bank, chapters, draws.profile.persona, draws.profile.function_chapter,
                                draws.root_seed, draws.replicate_id, draws.horizon)
    _need(_runtime_provenance() == draws.runtime, 'prepared draw runtime/source differs from current process')
    _need(type(draws.response_uniforms) is tuple
          and tuple(node for node, _ in draws.response_uniforms) == tuple(node for node, _ in draws.profile.normal_z),
          'exact canonical prepared tape nodes required')
    result = run_continuity_episode_supplied(bank, draws.profile, chapters=dict(chapter_pairs), edges=edges,
        traversal_order=traversal_order, response_uniforms_by_node=dict(draws.response_uniforms), horizon=draws.horizon)
    _need(draws.identity == digest, 'draws changed during episode')
    return SeededContinuityEpisode(digest, result)
