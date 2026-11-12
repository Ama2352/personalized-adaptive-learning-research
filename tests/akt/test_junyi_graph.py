"""A1 Junyi giữ graph đầy đủ và chỉ lấy responses ở native prefix."""
from dataclasses import asdict, replace

import numpy as np
import pytest

from knowledge_tracing.shared_kt import PrerequisiteGraph, StableVocabulary
from knowledge_tracing.akt.encoding import ExerciseEncoding
from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView, JunyiResearchEncoding
from knowledge_tracing.akt.research_junyi_graph import (
    AUDIT_SCHEMA, JunyiGraphCondition, JunyiGraphPhaseSession, junyi_prefix_evidence)
from knowledge_tracing.akt.research_junyi_roles import JunyiResearchRoles, make_junyi_research_roles
from knowledge_tracing.akt.types import KTEvent, LearnerEvents, UnseenTarget, WindowInputs
from knowledge_tracing.akt.windows import iter_windows


@pytest.fixture
def case():
    roles = make_junyi_research_roles([(str(i), i % 5, 'development') for i in range(40)])
    train = JunyiPhaseView(roles, 'select_train80', roles.train_users[:2], roles.identity)
    selection = JunyiPhaseView(roles, 'raw_selection10', roles.selection_users[:1], roles.identity)
    native = ExerciseEncoding(StableVocabulary(('A', 'B', 'C')), dict(A=2, B=2, C=2))
    encoding = JunyiResearchEncoding(native, train)
    graph = PrerequisiteGraph.from_edges(('A', 'B', 'C', 'ISOLATED', 'UNFIT'),
                                         (('A', 'C'), ('B', 'C'), ('UNFIT', 'C')))
    condition = JunyiGraphCondition(encoding, graph, 'a'*64)
    return encoding, selection, condition


def windows(case, items, responses):
    encoding, selection, _ = case
    user = selection.users[0]
    learner = LearnerEvents(user, 0, tuple(KTEvent(user, item, 100+i, i+1, correct, 0, 0)
        for i, (item, correct) in enumerate(zip(items, responses))))
    return list(iter_windows(learner, encoding.native, training=False))


def evidence(case, window):
    return junyi_prefix_evidence(window, condition=case[2], view=case[1])


def parent_at(row, name):
    return next(parent for parent in row.audit.parents if parent.parent == name)


def test_condition_preserves_unfitted_and_isolated_graph_nodes(case):
    encoding, _, condition = case
    assert len(condition.graph.nodes) == 5
    assert ('UNFIT', 'C') in condition.graph.edges
    assert 'ISOLATED' in condition.graph.nodes
    assert condition.identity == JunyiGraphCondition(encoding, condition.graph, 'a'*64).identity
    assert condition.identity != JunyiGraphCondition(encoding, condition.graph, 'b'*64).identity


@pytest.mark.parametrize('variant', ['A0', 'A2', 'A3'])
def test_unimplemented_variants_do_not_fake_fitted_confidence(case, variant):
    encoding, _, condition = case
    with pytest.raises(ValueError, match='Only A1'):
        JunyiGraphCondition(encoding, condition.graph, 'a'*64, variant=variant)


@pytest.mark.parametrize('graph', [
    PrerequisiteGraph(('A', 'B', 'C'), (('A', 'C'), ('A', 'C'))),
    PrerequisiteGraph(('A', 'B', 'C'), (('A', 'A'),)),
    PrerequisiteGraph(('A', 'B', 'C'), (('MISSING', 'C'),)),
    PrerequisiteGraph(('A', 'B', 'C'), (('A', 'B'), ('B', 'A'))),
    PrerequisiteGraph(('A', 'B', 'C'), (('A', 'C'),), 'dependent_to_prerequisite'),
    PrerequisiteGraph(('A', 'A', 'B', 'C'), (('A', 'C'),)),
    PrerequisiteGraph(('A', 'B'), (('A', 'B'),)),
])
def test_malformed_or_vocabulary_incomplete_graph_rejected(case, graph):
    with pytest.raises(ValueError):
        JunyiGraphCondition(case[0], graph, 'a'*64)


def test_topology_requires_external_pin(case):
    with pytest.raises(ValueError, match='SHA256'):
        JunyiGraphCondition(case[0], case[2].graph, 'unpinned')


def test_refit_encoding_cannot_be_relabelled_train80(case):
    encoding, selection, condition = case
    train = encoding.fit_view
    refit = JunyiPhaseView(train.roles, 'refit_union90', (*train.users, *selection.users), train.roles.identity)
    with pytest.raises(ValueError, match='TRAIN80'):
        JunyiGraphCondition(JunyiResearchEncoding(encoding.native, refit), condition.graph, 'a'*64)


def test_prefix_counts_parent_availability_and_native_dataclass_shape(case):
    rows = evidence(case, windows(case, ['A', 'B', 'C'], [1, 0, 1])[0])
    assert parent_at(rows[2], 'A').support == 1
    assert parent_at(rows[2], 'A').mean_observed_correctness == 1.
    assert parent_at(rows[2], 'B').mean_observed_correctness == 0.
    assert parent_at(rows[2], 'UNFIT').support == 0
    assert parent_at(rows[2], 'UNFIT').mean_observed_correctness is None
    assert all(parent.confidence == 1. for parent in rows[2].audit.parents)
    payload = asdict(rows[2])
    assert payload['local_position'] == 2 and payload['source_row'] == 3
    assert payload['audit']['target_fitted'] is True
    assert rows[2].audit.observed_rows == (1, 2)


def test_current_and_future_labels_and_future_item_do_not_change_earlier_evidence(case):
    original = evidence(case, windows(case, ['A', 'C', 'B', 'C'], [1, 0, 0, 1])[0])
    changed = evidence(case, windows(case, ['A', 'C', 'A', 'C'], [1, 1, 1, 0])[0])
    assert original[:2] == changed[:2]


def test_past_response_changes_later_evidence(case):
    original = evidence(case, windows(case, ['A', 'C'], [1, 1])[0])
    changed = evidence(case, windows(case, ['A', 'C'], [0, 1])[0])
    assert original[0] == changed[0]
    assert parent_at(original[1], 'A').mean_observed_correctness == 1.
    assert parent_at(changed[1], 'A').mean_observed_correctness == 0.


def test_oov_barrier_excludes_prior_known_parent_response(case):
    records = windows(case, ['A', 'OOV', 'C', 'B', 'C'], [1, 1, 0, 1, 1])
    assert isinstance(records[1], UnseenTarget)
    reset = records[2]
    assert reset.context_reset.all() and reset.global_ranks[0] == 2
    rows = evidence(case, reset)
    assert parent_at(rows[0], 'A').support == 0
    assert rows[0].audit.observed_rows == ()
    assert parent_at(rows[2], 'B').support == 1
    assert parent_at(rows[2], 'B').mean_observed_correctness == 1.


def test_native_context_limit_excludes_older_history_and_only_targets_have_evidence(case):
    items = ['A']+['B']*199+['C']*10
    records = windows(case, items, [1]*210)
    last = records[2]
    assert isinstance(last, WindowInputs) and last.global_ranks[0] == 100
    rows = evidence(case, last)
    assert all(row is None for row in rows[:100])
    assert rows[100].global_rank == 200
    assert parent_at(rows[100], 'A').support == 0
    assert parent_at(rows[100], 'B').support == 100
    assert rows[100].audit.observed_rows == tuple(range(101, 201))


@pytest.mark.parametrize('change', ['oov', 'prior', 'mask', 'rows', 'ranks', 'user'])
def test_malformed_native_window_rejected(case, change):
    window = windows(case, ['A', 'B', 'C'], [1, 0, 1])[0]
    if change == 'oov':
        window.inputs.item_ids[1] = -1
    elif change == 'prior':
        window.inputs.prior_responses[0] = 0
    elif change == 'mask':
        window.target_mask[1] = False
    elif change == 'rows':
        window.inputs.source_rows[1] = window.inputs.source_rows[0]
    elif change == 'ranks':
        window.global_ranks[1] = 99
    else:
        window = replace(window, inputs=replace(window.inputs, user_ids=('foreign',)*3))
    with pytest.raises(ValueError):
        evidence(case, window)


def test_wrong_role_or_mutated_encoding_rejected(case):
    encoding, selection, condition = case
    window = windows(case, ['A', 'C'], [1, 0])[0]
    calibration = JunyiPhaseView(selection.roles, 'calibration_predict',
        selection.roles.calibration_users[:1], selection.roles.identity)
    with pytest.raises(ValueError, match='phase'):
        junyi_prefix_evidence(window, condition=condition, view=calibration)
    encoding.native.train_support_students['A'] = 999
    with pytest.raises(ValueError, match='changed'):
        evidence(case, window)


def test_phase_encoding_bound_to_exact_train_cohort(case):
    encoding, _, condition = case
    smaller = JunyiPhaseView(encoding.fit_view.roles, 'select_train80',
        encoding.fit_view.users[:1], encoding.fit_view.roles.identity)
    with pytest.raises(ValueError, match='cohorts'):
        junyi_prefix_evidence(windows(case, ['A', 'C'], [1, 0])[0], condition=condition, view=smaller)


def test_session_amortizes_full_role_hash_and_matches_simple_api(case, monkeypatch):
    window = windows(case, ['A', 'C'], [1, 0])[0]
    expected = evidence(case, window)
    original = JunyiResearchRoles.identity.fget
    calls = []
    def counted(roles):
        calls.append(1)
        return original(roles)
    monkeypatch.setattr(JunyiResearchRoles, 'identity', property(counted))
    session = JunyiGraphPhaseSession(case[2], case[1])
    attach_calls = len(calls)
    assert attach_calls > 0
    for _ in range(20):
        assert session.prefix_evidence(window) == expected
    assert len(calls) == attach_calls
    session.assert_boundary()
    assert len(calls) > attach_calls


def test_session_boundary_detects_role_mutation(case):
    session = JunyiGraphPhaseSession(case[2], case[1])
    roles = case[1].roles
    object.__setattr__(roles, 'train_users', (*roles.train_users, 'forged-learner'))
    with pytest.raises(ValueError, match='header|changed'):
        session.assert_boundary()


def test_session_checks_mutable_encoding_content_each_window(case):
    window = windows(case, ['A', 'C'], [1, 0])[0]
    session = JunyiGraphPhaseSession(case[2], case[1])
    case[0].native.train_support_students['A'] = 999
    with pytest.raises(ValueError, match='encoding content'):
        session.prefix_evidence(window)


def test_session_checks_graph_replacement_without_rehashing_full_roles(case):
    window = windows(case, ['A', 'C'], [1, 0])[0]
    session = JunyiGraphPhaseSession(case[2], case[1])
    object.__setattr__(case[2].graph, 'edges', (('B', 'C'),))
    with pytest.raises(ValueError, match='header'):
        session.prefix_evidence(window)


def test_observed_rows_only_include_declared_parent_support(case):
    window = windows(case, ['A', 'C', 'B', 'C'], [1, 0, 1, 1])[0]
    rows = evidence(case, window)
    assert rows[2].audit.parents == ()
    assert rows[2].audit.observed_rows == ()
    assert rows[3].audit.observed_rows == (1, 3)
    assert parent_at(rows[3], 'A').support == 1
    assert parent_at(rows[3], 'B').support == 1
    assert window.inputs.prior_responses.tolist() == [-1, 1, 0, 1]


def test_observed_rows_merge_parent_streams_by_position(case):
    window = windows(case, ['A', 'B', 'A', 'C'], [1, 0, 0, 1])[0]
    window.inputs.source_rows[:] = [40, 10, 30, 20]
    rows = evidence(case, window)
    assert rows[3].audit.observed_rows == (40, 10, 30)
    assert parent_at(rows[3], 'A').support == 2
    assert parent_at(rows[3], 'A').mean_observed_correctness == .5


def test_parent_and_gate_numeric_features_match_full_prefix_definition(case):
    window = windows(case, ['A', 'C', 'B', 'A', 'C', 'B', 'C'], [1, 0, 1, 0, 1, 0, 1])[0]
    rows = evidence(case, window)
    vocabulary = case[0].native.vocabulary.values
    for local, row in enumerate(rows):
        child = vocabulary[int(window.inputs.item_ids[local])]
        declared = [parent for parent, dependent in case[2].graph.edges if dependent == child]
        expected = []
        expected_rows = []
        for parent in declared:
            positions = [i for i in range(local) if vocabulary[int(window.inputs.item_ids[i])] == parent]
            values = [int(window.inputs.prior_responses[i+1]) for i in positions]
            expected.append(dict(parent=parent, support=len(positions), confidence=1.,
                mean_observed_correctness=sum(values)/len(values) if values else None))
            expected_rows.extend(positions)
        assert [asdict(parent) for parent in row.audit.parents] == expected
        assert row.audit.observed_rows == tuple(int(window.inputs.source_rows[i]) for i in sorted(expected_rows))
        assert len(row.audit.observed_rows) == sum(parent.support for parent in row.audit.parents)
        old_features = (sum(parent['support'] for parent in expected),
                        tuple(parent['confidence'] for parent in expected),
                        sum(parent['support'] > 0 for parent in expected))
        new_features = (sum(parent.support for parent in row.audit.parents),
                        tuple(parent.confidence for parent in row.audit.parents),
                        sum(parent.support > 0 for parent in row.audit.parents))
        assert old_features == new_features


def test_parent_row_schema_changes_condition_identity(case):
    import hashlib
    import json
    condition = case[2]
    payload = condition._payload()
    assert payload.pop('audit_schema') == AUDIT_SCHEMA
    old_identity = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert old_identity != condition.identity
