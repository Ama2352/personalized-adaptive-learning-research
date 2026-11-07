"""Kernel residual trên fixture CPU: không instantiate AKT hoặc optimizer."""

from dataclasses import replace

import pytest
import torch

from knowledge_tracing.graph_augmentation import (
    apply_graph_residual, prepare_graph_context,
)
from knowledge_tracing.graph_context import EdgeConfidence, audit_graph_context
from knowledge_tracing.shared_kt import PrerequisiteGraph
from knowledge_tracing.simulator_bridge import ItemQuery, Observation, SimulatorBank, SimulatorItem


def fixture():
    bank = SimulatorBank('residual-fixture', tuple(SimulatorItem(i, c, 0) for i, c in
                                                [('a', 'A'), ('b', 'B'), ('c', 'C'), ('oov', 'A')]))
    graph = PrerequisiteGraph.from_edges(['A', 'B', 'C'], [('A', 'C'), ('B', 'C')])
    confidence = EdgeConfidence('structural_score', (('A', 'C', .25), ('B', 'C', .5)), '1' * 64)
    history = tuple(Observation(ItemQuery(item, rank, rank + 1), int(item == 'a'))
                    for rank, item in enumerate('aaab'))
    return dict(bank=bank, graph=graph, confidence=confidence, history=history,
                query=ItemQuery('c', 4, 5), trained_items=('a', 'b', 'c'), context=3, target_block=2)


def apply(evidence, **kwargs):
    return apply_graph_residual(torch.tensor(.125, dtype=torch.float64), evidence=evidence,
                                binding=evidence.binding, **kwargs)


def test_prepared_evidence_reuses_audit_without_renormalizing_or_losing_provenance():
    kwargs = fixture()
    evidence = prepare_graph_context(**kwargs)
    audited = audit_graph_context(**kwargs)
    assert evidence.observed_rows == tuple(audited['observed_rows'])
    assert evidence.effective_start == audited['effective_start']
    assert [p.__dict__ for p in evidence.parents] == audited['parents']
    assert evidence.binding.domain_sha256 == audited['domain_sha256']
    assert evidence.binding.trained_items_sha256 == audited['trained_items_sha256']
    assert evidence.confidence_sha256 == audited['confidence_sha256']
    assert evidence.graph_sha256 == audited['graph_sha256']
    assert evidence.scoped_observations_sha256 == audited['scoped_observations_sha256']


@pytest.mark.parametrize('confidence,expected_mass,expected', [
    ((.25, .5), .75, -.375), ((1., 1.), 2., -.25), ((.1, .2), .3, -.15),
])
def test_explicit_gate_signed_influence_and_absolute_confidence(confidence, expected_mass, expected):
    kwargs = fixture()
    kwargs['confidence'] = EdgeConfidence('structural_score', tuple(
        (parent, 'C', value) for parent, value in zip(('A', 'B'), confidence)), '2' * 64)
    evidence = prepare_graph_context(**kwargs)
    result = apply(evidence, edge_messages=torch.tensor([[2., 1.], [-2., 0.]], dtype=torch.float64),
                   readout=torch.tensor([1., -1.], dtype=torch.float64),
                   gate=torch.tensor(.5, dtype=torch.float64))
    assert result.applied and result.confidence_mass == pytest.approx(expected_mass)
    assert result.normalizer == max(1, expected_mass)
    assert result.residual.item() == pytest.approx(expected)
    assert result.logit.item() == pytest.approx(.125 + expected)


@pytest.mark.parametrize('case', ['disabled', 'empty', 'zero_confidence', 'no_support', 'zero_gate'])
@pytest.mark.parametrize('dtype', [torch.float32, torch.float64])
def test_fallback_returns_exact_base_tensor_including_signed_zero(case, dtype):
    kwargs = fixture()
    options = {}
    if case == 'disabled':
        options['enabled'] = False
    elif case == 'empty':
        kwargs['graph'] = PrerequisiteGraph.from_edges(['A', 'B', 'C'], [])
        kwargs['confidence'] = EdgeConfidence('fixed_uniform', (), '1' * 64)
    elif case == 'zero_confidence':
        kwargs['confidence'] = EdgeConfidence('structural_score', (('A', 'C', 0), ('B', 'C', 0)), '1' * 64)
    elif case == 'no_support':
        kwargs['history'] = tuple(replace(o, query=replace(o.query, item_id='c')) for o in kwargs['history'])
    else:
        options['gate'] = torch.tensor(0., dtype=dtype)
    evidence = prepare_graph_context(**kwargs)
    base = torch.tensor(-0., dtype=dtype, requires_grad=True)
    # Branch bypass không inspect hoặc tính arithmetic với messages/readout.
    result = apply_graph_residual(base, evidence=evidence, binding=evidence.binding,
                                  edge_messages=torch.tensor(float('nan')), **options)
    assert result.logit is base and not result.applied
    assert result.logit.detach().numpy().tobytes() == base.detach().numpy().tobytes()
    assert torch.signbit(result.logit) and result.residual.item() == 0
    result.logit.backward()
    assert base.grad.item() == 1


def test_active_cpu_gradients_reach_base_gate_messages_and_readout_without_training():
    evidence = prepare_graph_context(**fixture())
    base = torch.tensor(.2, dtype=torch.float64, requires_grad=True)
    messages = torch.tensor([[2., 1.], [-2., 0.]], dtype=torch.float64, requires_grad=True)
    readout = torch.tensor([1., -1.], dtype=torch.float64, requires_grad=True)
    gate = torch.tensor(.5, dtype=torch.float64, requires_grad=True)
    result = apply_graph_residual(base, evidence=evidence, binding=evidence.binding,
                                  edge_messages=messages, readout=readout, gate=gate)
    result.logit.backward()
    assert base.grad.item() == 1
    assert gate.grad.item() == -.75
    assert torch.equal(readout.grad, torch.tensor([-.25, .125], dtype=torch.float64))
    assert torch.equal(messages.grad, torch.tensor([[.125, -.125], [.25, -.25]], dtype=torch.float64))


def test_unobserved_parent_is_masked_even_with_large_projected_message():
    kwargs = fixture()
    kwargs['history'] = kwargs['history'][:3]
    evidence = prepare_graph_context(**kwargs)
    result = apply(evidence, edge_messages=torch.tensor([[1.], [1e9]], dtype=torch.float64),
                   readout=torch.tensor([1.], dtype=torch.float64), gate=torch.tensor(1., dtype=torch.float64))
    assert result.confidence_mass == .25
    assert result.residual.item() == .25


@pytest.mark.parametrize('case', ['current', 'future', 'duplicate', 'alien', 'graph_domain', 'coverage', 'oracle'])
def test_preparation_preserves_history_domain_and_privileged_input_guards(case):
    kwargs = fixture()
    if case == 'current':
        kwargs['history'] += (Observation(kwargs['query'], 1),)
    elif case == 'future':
        kwargs['history'] += (Observation(ItemQuery('a', 5, 6), 0),)
    elif case == 'duplicate':
        kwargs['query'] = ItemQuery('c', 4, 1)
    elif case == 'alien':
        kwargs['query'] = ItemQuery('alien', 4, 5)
    elif case == 'graph_domain':
        kwargs['graph'] = PrerequisiteGraph.from_edges(['alien'], [])
    elif case == 'coverage':
        kwargs['confidence'] = EdgeConfidence('fixed_uniform', (), '1' * 64)
    else:
        kwargs['confidence'] = EdgeConfidence('oracle_label', (('A', 'C', 1), ('B', 'C', 0)), '1' * 64)
    with pytest.raises(ValueError):
        prepare_graph_context(**kwargs)


def test_oracle_reference_requires_explicit_opt_in_at_both_boundaries_even_disabled():
    kwargs = fixture()
    kwargs['confidence'] = EdgeConfidence('oracle_label', (('A', 'C', 1), ('B', 'C', 0)), '1' * 64)
    evidence = prepare_graph_context(**kwargs, oracle_reference=True)
    with pytest.raises(ValueError, match='reference mode'):
        apply(evidence, enabled=False)
    assert not apply(evidence, enabled=False, oracle_reference=True).applied


def test_estimated_confidence_retains_train_only_declaration_and_is_not_oracle():
    kwargs = fixture()
    values = (('A', 'C', .25), ('B', 'C', .5))
    with pytest.raises(ValueError, match='train-only'):
        EdgeConfidence('estimated_probability', values, '2' * 64, fitted_role='selection')
    kwargs['confidence'] = EdgeConfidence('estimated_probability', values, '2' * 64, fitted_role='train')
    evidence = prepare_graph_context(**kwargs)
    assert evidence.confidence_kind == 'estimated_probability'
    assert evidence.confidence_sha256 == kwargs['confidence'].identity
    assert not apply(evidence, enabled=False).applied


@pytest.mark.parametrize('field', ['domain_sha256', 'trained_items_sha256'])
def test_base_binding_mismatch_rejected_even_when_disabled(field):
    evidence = prepare_graph_context(**fixture())
    binding = replace(evidence.binding, **{field: '0' * 64})
    with pytest.raises(ValueError, match='binding mismatch'):
        apply_graph_residual(torch.tensor(0.), evidence=evidence, binding=binding, enabled=False)


def test_oov_is_not_rescued_or_reported_as_fitted_by_graph():
    kwargs = fixture()
    kwargs['query'] = ItemQuery('oov', 4, 5)
    evidence = prepare_graph_context(**kwargs)
    assert not evidence.target_fitted
    with pytest.raises(ValueError, match='unfitted/OOV'):
        apply(evidence, enabled=False)


def test_old_prefix_perturbation_is_invisible_and_contexts_have_no_shared_state():
    kwargs = fixture()
    original = prepare_graph_context(**kwargs)
    assert original.observed_rows == (2, 3, 4)
    alternate = dict(kwargs, history=(replace(kwargs['history'][0], correct=0),) + kwargs['history'][1:])
    assert prepare_graph_context(**alternate) == original
    different = dict(kwargs, history=tuple(replace(o, correct=1-o.correct) for o in kwargs['history']))
    assert prepare_graph_context(**different) != original
    assert prepare_graph_context(**kwargs) == original


def test_oov_history_barrier_is_reused_before_parent_support():
    kwargs = fixture()
    history = list(kwargs['history'])
    history[2] = replace(history[2], query=replace(history[2].query, item_id='oov'))
    evidence = prepare_graph_context(**dict(kwargs, history=tuple(history)))
    assert evidence.effective_start == 3 and evidence.observed_rows == (4,)
    assert [(p.parent, p.support) for p in evidence.parents] == [('A', 0), ('B', 1)]


@pytest.mark.parametrize('case', ['base_shape', 'base_int', 'base_nan', 'message_shape', 'message_nan',
                                 'message_dtype', 'readout_empty', 'gate_shape', 'gate_nan',
                                 'gate_negative', 'gate_above_one', 'missing_gate'])
def test_tensor_contracts(case):
    evidence = prepare_graph_context(**fixture())
    options = dict(base_logit=torch.tensor(0., dtype=torch.float64),
                   edge_messages=torch.ones((2, 2), dtype=torch.float64),
                   readout=torch.ones(2, dtype=torch.float64), gate=torch.tensor(.5, dtype=torch.float64))
    if case == 'base_shape':
        options['base_logit'] = torch.zeros(1, dtype=torch.float64)
    elif case == 'base_int':
        options['base_logit'] = torch.tensor(0)
    elif case == 'base_nan':
        options['base_logit'] = torch.tensor(float('nan'), dtype=torch.float64)
    elif case == 'message_shape':
        options['edge_messages'] = torch.ones((1, 2), dtype=torch.float64)
    elif case == 'message_nan':
        options['edge_messages'][0, 0] = float('nan')
    elif case == 'message_dtype':
        options['edge_messages'] = options['edge_messages'].float()
    elif case == 'readout_empty':
        options['readout'] = torch.zeros(0, dtype=torch.float64)
    elif case == 'gate_shape':
        options['gate'] = torch.zeros(1, dtype=torch.float64)
    elif case == 'gate_nan':
        options['gate'] = torch.tensor(float('nan'), dtype=torch.float64)
    elif case == 'gate_negative':
        options['gate'] = torch.tensor(-.1, dtype=torch.float64)
    elif case == 'gate_above_one':
        options['gate'] = torch.tensor(1.1, dtype=torch.float64)
    else:
        options.pop('gate')
    with pytest.raises(ValueError):
        apply_graph_residual(evidence=evidence, binding=evidence.binding, **options)
