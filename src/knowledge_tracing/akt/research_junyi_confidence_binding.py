"""Gắn điểm ổn định dự báo TRAIN80 vào cạnh Junyi cho A2/A3.

Đây là hợp đồng lineage của artifact đã fit, không cấp quyền training.
Điểm unsupported giữ lý do và trọng số vận hành bằng 0.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

from ..edge_confidence import EdgeConfidenceRecipe, EdgeSummary
from .research_graph_condition import OperationalEdgeWeight

SEMANTICS = 'conditional_predictive_stability_not_edge_truth_probability'
HISTORY = 'effective_native_window_prefix'


def _sha(value):
    if type(value) is not str or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('Pinned SHA256 required')


@dataclass(frozen=True)
class JunyiConfidenceBinding:
    train_view_identity: str
    encoding_identity: str
    topology_source_sha256: str
    recipe_identity: str
    fit_artifact_sha256: str
    weights: tuple[OperationalEdgeWeight, ...]
    semantics: str = SEMANTICS
    history_scope: str = HISTORY

    def __post_init__(self):
        self.assert_integrity()

    def assert_integrity(self):
        for value in (self.train_view_identity, self.encoding_identity, self.topology_source_sha256,
                      self.recipe_identity, self.fit_artifact_sha256):
            _sha(value)
        if self.semantics != SEMANTICS or self.history_scope != HISTORY:
            raise ValueError('Junyi predictive stability and native-window history required')
        if type(self.weights) is not tuple or any(type(row) is not OperationalEdgeWeight for row in self.weights):
            raise ValueError('Immutable typed edge weights required')
        pairs = tuple((row.parent_id, row.child_id) for row in self.weights)
        if pairs != tuple(sorted(set(pairs))):
            raise ValueError('Canonical unique confidence edges required')
        for row in self.weights:
            row.__post_init__()

    @property
    def identity(self):
        self.assert_integrity()
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def binding_from_child_results(results, *, condition, recipe, fit_artifact_sha256):
    """Chỉ nhận kết quả fitter Junyi hiện có, giữ đủ cạnh của topology đã chốt."""
    from .research_junyi_graph import JunyiGraphCondition
    from .research_junyi_confidence import FEATURE_RECIPE, FOLD_RECIPE
    if type(condition) is not JunyiGraphCondition or condition.variant != 'A1':
        raise ValueError('Expert A1 topology must precede confidence fitting')
    condition.assert_integrity()
    if type(recipe) is not EdgeConfidenceRecipe:
        raise ValueError('Approved confidence recipe required')
    edges = []
    seen_children = set()
    for result in results:
        if (result['feature_recipe'] != FEATURE_RECIPE or result['fold_recipe'] != FOLD_RECIPE
                or result['train_view_identity'] != condition.encoding.fit_view.identity
                or result['recipe_identity'] != recipe.identity):
            raise ValueError('Confidence fit lineage/history mismatch')
        child = result['child']
        if child in seen_children:
            raise ValueError('Duplicate fitted child')
        seen_children.add(child)
        for summary in result['edges']:
            if type(summary) is not EdgeSummary or summary.child_id != child:
                raise ValueError('Typed matching child summary required')
            edges.append(OperationalEdgeWeight(summary.parent_id, child, summary.supported,
                summary.confidence, summary.reason, float(summary.confidence) if summary.supported else 0.))
    weights = tuple(sorted(edges, key=lambda row: (row.parent_id, row.child_id)))
    if tuple((row.parent_id, row.child_id) for row in weights) != condition.graph.edges:
        raise ValueError('Confidence must cover every declared edge exactly once')
    return JunyiConfidenceBinding(condition.encoding.fit_view.identity, condition.encoding.identity,
        condition.topology_source_sha256, recipe.identity, fit_artifact_sha256, weights)


def save_binding(binding, path):
    if type(binding) is not JunyiConfidenceBinding:
        raise ValueError('Typed confidence binding required')
    binding.assert_integrity()
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(dict(schema='junyi-confidence-binding-v1', identity=binding.identity,
                       binding=asdict(binding)), stream, sort_keys=True, indent=2)
        stream.write('\n')


def load_binding(path, *, expected_sha256):
    _sha(expected_sha256)
    path = Path(path)
    if path.is_symlink() or path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError('Bounded regular confidence artifact required')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError('Confidence artifact SHA256 mismatch')
    payload = json.loads(raw)
    if set(payload) != {'schema', 'identity', 'binding'} or payload['schema'] != 'junyi-confidence-binding-v1':
        raise ValueError('Confidence artifact schema mismatch')
    fields = dict(payload['binding'])
    fields['weights'] = tuple(OperationalEdgeWeight(**row) for row in fields['weights'])
    binding = JunyiConfidenceBinding(**fields)
    if binding.identity != payload['identity']:
        raise ValueError('Confidence artifact identity mismatch')
    return binding
