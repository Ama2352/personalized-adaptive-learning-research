"""Refit synthetic CPU, admission CUDA mock rõ, kiểm native/RNG/resume."""
from dataclasses import replace
import json

import pytest
import torch

from knowledge_tracing.akt.config import AKTConfig
from knowledge_tracing.akt.encoding import ExerciseEncoding
from knowledge_tracing.akt.model import AKTAdapter
from knowledge_tracing.akt import research_graph_model as native_graph
from knowledge_tracing.akt import research_junyi_graph_model as graph_model
from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView, JunyiResearchEncoding
from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition, JunyiGraphPhaseSession
from knowledge_tracing.akt.research_junyi_roles import make_junyi_research_roles
from knowledge_tracing.akt.research_junyi_refit import _run_epochs, JunyiRefitInputs
from knowledge_tracing.akt.research_junyi_confidence_binding import JunyiConfidenceBinding
from knowledge_tracing.akt.research_graph_condition import OperationalEdgeWeight
from knowledge_tracing.akt.training import _seed
from knowledge_tracing.akt.types import LearnerEvents, KTEvent
from knowledge_tracing.akt.windows import iter_windows
from knowledge_tracing.shared_kt import PrerequisiteGraph, StableVocabulary


@pytest.fixture
def case(monkeypatch):
    monkeypatch.setattr(native_graph, 'validate_config', lambda *args, **kwargs: None)
    monkeypatch.setattr(graph_model, 'validate_config', lambda *args, **kwargs: None)
    roles = make_junyi_research_roles([(str(i), i % 5, 'development') for i in range(20)])
    train = JunyiPhaseView(roles, 'select_train80', roles.train_users, roles.identity)
    refit = JunyiPhaseView(roles, 'refit_union90',
        tuple(sorted((*roles.train_users, *roles.selection_users))), roles.identity)
    calibration = JunyiPhaseView(roles, 'calibration_predict', roles.calibration_users, roles.identity)
    native = ExerciseEncoding(StableVocabulary(('A', 'B', 'C')), dict(A=2, B=2, C=2))
    origin = JunyiResearchEncoding(native, train)
    encoding = JunyiResearchEncoding(native, refit)
    graph = PrerequisiteGraph.from_edges(('A', 'B', 'C'), (('A', 'C'),))
    confidence = JunyiConfidenceBinding(train.identity, origin.identity, 'a' * 64, 'b' * 64, 'c' * 64,
        (OperationalEdgeWeight('A', 'C', True, .75, None, .75),))
    config = AKTConfig(phase='junyi-research', device='cpu', outer_fold=4, d_model=16, heads=2,
        d_ff=32, final_fc=16, batch_size=2, dropout=.2)
    entries = []
    for index, user in enumerate(refit.users):
        learner = LearnerEvents(user, 0, tuple(KTEvent(user, item, i + 1, index * 10 + i + 1, i % 2, 0, 0)
            for i, item in enumerate(('A', 'C', 'B', 'C', 'A', 'C'))))
        entries.extend(iter_windows(learner, native, training=True))
    def condition(variant):
        return JunyiGraphCondition(encoding, graph, 'a' * 64, variant=variant,
            confidence=None if variant == 'A1' else confidence, train80_origin=origin)
    def adapter(variant):
        _seed(42)
        if variant == 'A0':
            return AKTAdapter(config, native)
        cond = condition(variant)
        return graph_model.JunyiGraphAKTAdapter(config=config, encoding=encoding, condition=cond,
            phase=JunyiGraphPhaseSession(cond, refit), compact_context=True)
    return dict(roles=roles, train=train, refit=refit, calibration=calibration, origin=origin,
                encoding=encoding, condition=condition, adapter=adapter, entries=entries)


@pytest.mark.parametrize('variant', ['A1', 'A2', 'A3'])
def test_refit_preserves_train80_confidence_and_supports_calibration_phase(case, variant):
    adapter = case['adapter'](variant)
    assert adapter.condition.train80_origin is case['origin']
    if variant != 'A1':
        assert adapter.condition.confidence.encoding_identity == case['origin'].identity
        assert adapter.condition.confidence.encoding_identity != case['encoding'].identity
    adapter.set_phase(JunyiGraphPhaseSession(adapter.condition, case['calibration']))
    with pytest.raises(ValueError, match='optimization'):
        adapter.collate_training(case['entries'][:1])
    with pytest.raises(ValueError):
        replace(adapter.condition, train80_origin=None)


def test_refit_rejects_missing_selection_users(case):
    partial = replace(case['refit'], users=case['train'].users)
    with pytest.raises(ValueError, match='Full refit90'):
        JunyiRefitInputs(partial, 5, 'a' * 64, 'b' * 64)


@pytest.mark.parametrize('variant', ['A0', 'A1', 'A2', 'A3'])
def test_native_refit_partial_resume_equals_continuous(case, tmp_path, variant):
    torch.set_num_threads(1)
    targets = len(case['refit'].users) * 6
    budget = dict(max_steps=100, max_targets=targets, max_seconds=60.,
        max_rss_bytes=2 * 1024**3, min_available_ram_bytes=1)
    def make():
        adapter = case['adapter'](variant)
        optimizer = torch.optim.Adam(adapter.native.parameters(), lr=1e-4, foreach=False, fused=False)
        identity = dict(phase='synthetic_refit90', variant=variant)
        if variant != 'A0':
            identity['batch_factory'] = adapter.audit_context_boundary()
        return adapter, optimizer, identity
    continuous, optimizer, identity = make()
    common = dict(epochs=2, targets=targets, max_seconds=120., checkpoint_every_steps=1)
    expected = _run_epochs(continuous, lambda: iter(case['entries']), optimizer=optimizer,
        output=tmp_path / 'continuous', identity=identity, budget=budget, **common)
    assert expected['status'] == 'JUNYI_REFIT90_COMPLETE'
    partial, optimizer, identity = make()
    stopped = _run_epochs(partial, lambda: iter(case['entries']), optimizer=optimizer,
        output=tmp_path / 'resumed', identity=identity, budget=dict(budget, max_steps=1), **common)
    assert stopped['status'] == 'PARTIAL_JUNYI_REFIT90'
    checkpoint = next((tmp_path / 'resumed/batch-recovery').glob('*.pt'))
    resumed, optimizer, identity = make()
    actual = _run_epochs(resumed, lambda: iter(case['entries']), optimizer=optimizer,
        output=tmp_path / 'resumed', identity=identity, budget=budget, resume=checkpoint, **common)
    assert actual['status'] == 'JUNYI_REFIT90_COMPLETE'
    for name, value in continuous.native.state_dict().items():
        assert torch.equal(value, resumed.native.state_dict()[name]), name
    left = torch.load(tmp_path / 'continuous' / expected['checkpoint'], weights_only=True)
    right = torch.load(tmp_path / 'resumed' / actual['checkpoint'], weights_only=True)
    assert torch.equal(left['torch_rng'], right['torch_rng'])
    assert left['numpy_rng'] == right['numpy_rng'] and left['python_rng'] == right['python_rng']
    for key, state in left['optimizer_state_dict']['state'].items():
        for field, value in state.items():
            assert torch.equal(value, right['optimizer_state_dict']['state'][key][field])
    assert [row['valid_targets'] for row in actual['history']] == [targets, targets]
    assert not actual['calibration_performed']
    assert json.loads((tmp_path / 'resumed/COMPLETE.json').read_text())['frozen_epochs'] == 2


def test_refit_origin_mutation_detected_at_batch_boundary(case):
    adapter = case['adapter']('A3')
    case['origin'].native.train_support_students['A'] = 3
    with pytest.raises(ValueError, match='encoding|origin'):
        adapter.collate_training(case['entries'][:1])
