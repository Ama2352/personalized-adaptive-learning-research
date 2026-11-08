"""GRAPH16 evidence/geometry handmade; không model/backend/fitted/corpus calls."""
from dataclasses import asdict, replace
import builtins
import copy

import numpy as np
import pytest

from knowledge_tracing.akt import research_graph_online as online
from knowledge_tracing.simulator_bridge import ItemQuery, Observation, identity_hash
import test_research_graph_context as handmade


@pytest.fixture(autouse=True)
def no_neural_or_solver_imports(monkeypatch):
    original = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name.split('.')[0] in {'torch', 'sklearn', 'scipy', 'pandas', 'joblib'} or name in {
                'knowledge_tracing.akt.online', 'knowledge_tracing.akt.model',
                'knowledge_tracing.akt.research_graph_model'}:
            raise AssertionError('online evidence must not import model/solver: '+name)
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', guarded)


@pytest.fixture(scope='module')
def case():
    return handmade.make_case(handmade.make_shards())


def rows(case):
    return sorted(case['phase'].trajectories, key=lambda t: t.learner_id)[0]


def arguments(case, rank=199):
    trajectory = rows(case)
    return dict(bank=case['shards']['train'].bank, encoding=case['encoding'], condition=case['condition'],
        history=trajectory.observations[:rank], query=trajectory.observations[rank].query,
        learner_id=trajectory.learner_id, namespace=online.NAMESPACE,
        limits=online.ResearchGraphOnlineLimits(205, 200), context=100, target_block=100)


def prepare(case, rank=199, **changes):
    args = arguments(case, rank); args.update(changes)
    return online.prepare_research_graph_online(**args)


@pytest.mark.parametrize('rank', [0,99,100,102,103,199,200,204])
def test_offline_dynamic_evidence_and_exact_causal_prefix_geometry(case, rank):
    result = prepare(case, rank)
    result.assert_integrity()
    assert result.role == 'constructed_observable_online_query_not_fitted'
    assert result.global_rank == rank
    trajectory = rows(case)
    if rank == 102:
        old = next(o for o in case['index'].unsupported_targets
                   if o.learner_id == trajectory.learner_id and o.global_rank == rank)
        assert old.query == result.query
        assert result.support_reason == 'unseen_item'
        assert result.window is result.evidence is None
        assert not result.audit.target_fitted and not result.audit.parents and not result.audit.observed_rows
        assert (result.history_available, result.history_used, result.context_reset) == (102,0,True)
        return
    offline = next(w for w in case['windows'] if w.inputs.user_ids[0] == trajectory.learner_id
                   and np.any(w.target_mask & (w.global_ranks == rank)))
    local = int(np.flatnonzero(offline.global_ranks == rank)[0])
    expected = handmade.evidence(case, 0, rank)
    assert result.audit == expected.audit
    assert result.evidence.local_position == local
    assert result.evidence.audit == result.audit
    assert result.evidence.window_id == result.window.window_id != offline.window_id
    assert len(result.window.inputs.item_ids) == local+1
    for name in ('item_ids','timestamps','prior_responses','source_rows'):
        assert np.array_equal(getattr(result.window.inputs,name), getattr(offline.inputs,name)[:local+1])
    assert np.array_equal(result.window.inputs.sequence_offsets, [0,local+1])
    for name in ('target_mask','global_ranks','history_available','history_used','context_reset'):
        assert np.array_equal(getattr(result.window,name), getattr(offline,name)[:local+1])
    assert (result.history_available,result.history_used,result.context_reset) == (
        int(offline.history_available[local]),int(offline.history_used[local]),bool(offline.context_reset[local]))
    assert result.window.inputs.prior_responses[0] == -1


def test_counterfactual_items_share_event_key_but_not_binding_or_graph_query(case):
    args = arguments(case,100)
    first = online.prepare_research_graph_online(**args)
    other = replace(args['query'], item_id='i1-1050')
    second = online.prepare_research_graph_online(**{**args,'query':other})
    assert (first.query.timestamp,first.query.source_row) == (second.query.timestamp,second.query.source_row)
    assert first.history_sha256 == second.history_sha256
    assert first.identity != second.identity and first.window.window_id != second.window.window_id
    assert first.audit.query.item_id == 'i0-1050' and second.audit.query == other
    assert not first.audit.parents and second.audit.parents[0].parent == 'c0'
    assert first.evidence.source_row == second.evidence.source_row


def test_first_query_has_finite_empty_past_and_no_response_input(case):
    result = prepare(case,0)
    assert result.history_available == result.history_used == 0
    assert result.audit.observed_rows == () and result.audit.scoped_observations_sha256 == identity_hash([])
    assert result.window.inputs.prior_responses.tolist() == [-1]
    assert result.evidence.local_position == 0 and result.audit.target_fitted
    assert not hasattr(result, 'probability') and not hasattr(result, 'correct')


def test_current_and_future_labels_are_not_accepted_or_read(case):
    args = arguments(case,100)
    original = online.prepare_research_graph_online(**args)
    trajectory = rows(case)
    changed = tuple(replace(o,correct=1-o.correct) if i >= 100 else o
                    for i,o in enumerate(trajectory.observations))
    revised = online.prepare_research_graph_online(**{**args,'history':changed[:100], 'query':changed[100].query})
    assert original.identity == revised.identity
    with pytest.raises(TypeError):
        online.prepare_research_graph_online(**args, correct=1)


def test_full_history_binding_and_effective_past_have_distinct_scopes(case):
    args = arguments(case,199)
    original = online.prepare_research_graph_online(**args)
    history = list(args['history']); history[0] = replace(history[0],correct=1-history[0].correct)
    outside = online.prepare_research_graph_online(**{**args,'history':tuple(history)})
    assert original.audit == outside.audit and original.history_sha256 != outside.history_sha256
    assert original.window.window_id != outside.window.window_id
    history = list(args['history']); history[-1] = replace(history[-1],correct=1-history[-1].correct)
    inside = online.prepare_research_graph_online(**{**args,'history':tuple(history)})
    assert original.audit.scoped_observations_sha256 != inside.audit.scoped_observations_sha256
    assert original.audit.parents != inside.audit.parents


def test_learner_namespace_changes_binding_without_peer_history(case):
    first = prepare(case,100)
    second = prepare(case,100,learner_id='another-constructed-stream')
    assert first.audit == second.audit and first.history_sha256 != second.history_sha256
    assert first.identity != second.identity
    assert first.window.inputs.user_ids != second.window.inputs.user_ids
    assert prepare(case,100).identity == first.identity


@pytest.mark.parametrize('change', ['namespace','bank','encoding','condition','history_list','duplicate_row',
                                   'time','foreign_item','learner','context','block','history_cap','window_cap'])
def test_invalid_identity_history_domains_and_caps_stop(case, change):
    args = arguments(case,199)
    if change == 'namespace': args['namespace'] = 'junyi_exercise'
    elif change == 'bank': args['bank'] = replace(args['bank'],environment_id='Junyi')
    elif change == 'encoding':
        args['encoding'] = replace(args['encoding'],domain_sha256='f'*64)
    elif change == 'condition':
        args['condition'] = copy.deepcopy(args['condition'])
        object.__setattr__(args['condition'],'graph_sha256','f'*64)
    elif change == 'history_list': args['history'] = list(args['history'])
    elif change == 'duplicate_row': args['query'] = replace(args['query'],source_row=args['history'][-1].query.source_row)
    elif change == 'time': args['query'] = replace(args['query'],timestamp=0)
    elif change == 'foreign_item': args['query'] = replace(args['query'],item_id='outside-bank')
    elif change == 'learner': args['learner_id'] = ''
    elif change == 'context': args['context'] = True
    elif change == 'block': args['target_block'] = 99
    elif change == 'history_cap': args['limits'] = online.ResearchGraphOnlineLimits(198,200)
    elif change == 'window_cap': args['limits'] = online.ResearchGraphOnlineLimits(205,1)
    with pytest.raises(ValueError):
        online.prepare_research_graph_online(**args)


def test_same_timestamp_later_row_and_same_event_alternatives_are_valid(case):
    args = arguments(case,100)
    query = replace(args['query'],timestamp=args['history'][-1].query.timestamp)
    result = online.prepare_research_graph_online(**{**args,'query':query})
    assert result.query == query and result.global_rank == 100


def test_owned_readonly_arrays_and_no_full_objects_retained(case):
    args = arguments(case,199)
    before = tuple(asdict(o) for o in args['history'])
    result = online.prepare_research_graph_online(**args)
    assert tuple(asdict(o) for o in args['history']) == before
    assert not any(name in vars(result) for name in ('history','bank','encoding','condition','phase','corpus'))
    with pytest.raises(ValueError): result.window.inputs.prior_responses[-1] = 0
    assert result.identity == prepare(case,199).identity


@pytest.mark.parametrize('kind', ['window','query','source'])
def test_payload_and_source_tamper_rejected(case,monkeypatch,kind):
    result = prepare(case,199)
    if kind == 'window':
        result.window.inputs.prior_responses.setflags(write=True)
        result.window.inputs.prior_responses[-1] = 1-result.window.inputs.prior_responses[-1]
    elif kind == 'query':
        object.__setattr__(result,'query',replace(result.query,item_id='i0-1050'))
    else:
        monkeypatch.setattr(online,'source_inventory',lambda: (('changed','f'*64),))
    with pytest.raises(ValueError,match='drift'):
        result.assert_integrity()


@pytest.mark.parametrize('values', [(True,200),(0,200),(205,True),(205,201)])
def test_explicit_limits_reject_bool_zero_and_oversized_window(values):
    with pytest.raises(ValueError): online.ResearchGraphOnlineLimits(*values)
