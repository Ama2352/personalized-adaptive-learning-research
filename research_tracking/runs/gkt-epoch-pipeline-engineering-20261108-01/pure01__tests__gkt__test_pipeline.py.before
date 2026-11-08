"""Portable PURE data/selector/export contracts; no neural model or Adam update.

The reviewed two-epoch model phase has a separate artifact controller, never
enabled implicitly by this default unit suite.
"""
from dataclasses import replace
import csv
import time

import pytest
import torch

from knowledge_tracing.gkt import GKTBinding, GKTKernelConfig
from knowledge_tracing.gkt.core import adjacency_sha256
from knowledge_tracing.gkt.recurrent import RECIPE_ID, GRU_VARIANT, GKTStaticRecurrentCandidate
from knowledge_tracing.gkt.training_data import (GKTObservableShard, GKTDataRecipe, GKTGraphProvenance,
                                               prepare_gkt_training_data)
from knowledge_tracing.gkt.pipeline import GKTEpochPlan, GKTPipelineBudget, collate_sequences, select_epoch, export_predictions
from knowledge_tracing.simulator_data import ObservableTrajectory, SimulatorSplitPlan
from knowledge_tracing.simulator_bridge import ItemQuery, Observation, SimulatorBank, SimulatorItem, identity_hash


@pytest.fixture(autouse=True)
def no_model_or_optimizer(monkeypatch):
    def forbidden(*a, **k): pytest.fail('PURE phase must not construct neural models or optimize')
    monkeypatch.setattr(GKTStaticRecurrentCandidate, '__init__', forbidden)
    monkeypatch.setattr(torch.optim.Adam, 'step', forbidden)


def data_parts():
    plan = SimulatorSplitPlan('gkt06-handmade-engineering', 42,
        (('train', 2), ('selection', 1), ('calibration', 1), ('final', 1)))
    bank = SimulatorBank('gkt06-observable-fixture', tuple(SimulatorItem(item, node, 1.) for item, node in
        [('a', 'A'), ('a2', 'A'), ('b', 'B'), ('c', 'C')]))
    def trajectory(learner, names, labels, first_row):
        return ObservableTrajectory(learner, plan.identity, identity_hash(bank.identity), 'handmade-not-collector',
            tuple(Observation(ItemQuery(item, i, first_row + i), answer) for i, (item, answer) in enumerate(zip(names, labels))))
    train_ids = [x.learner_id for x in plan.assignments('train')]
    val_id = plan.assignments('selection')[0].learner_id
    train = GKTObservableShard(plan, bank, 'train', 12, (
        trajectory(train_ids[0], ('a', 'b', 'a'), (0, 1, 1), 1),
        trajectory(train_ids[1], ('a2', 'a', 'b'), (1, 0, 1), 11)))
    selection = GKTObservableShard(plan, bank, 'selection', 12,
        (trajectory(val_id, ('a', 'b', 'c', 'a'), (0, 1, 1, 0), 101),))
    nodes = ('A', 'B', 'C'); binding = GKTBinding(bank.environment_id, identity_hash(nodes), nodes, 'concept')
    config = GKTKernelConfig(3, 2, 2, 2, 'static', 'concept', True, True)
    graph = torch.tensor([[0., .4, 0.], [.2, 0., .7], [0., .3, 0.]], dtype=torch.float64, device='cpu')
    recipe = GKTDataRecipe(RECIPE_ID, 3, 'none', 0., 'zeros', GRU_VARIANT, 'float64',
                           'full_prefix', 'query_only', 'unsupported_history', 'train_observed_items_only')
    provenance = GKTGraphProvenance('caller_declared_static', adjacency_sha256(graph), bank.environment_id, binding.node_order_sha256)
    return dict(train_shard=train, selection_shard=selection, model_config=config, node_binding=binding,
        adjacency=graph, graph_provenance=provenance, item_node_registry={'a': 'A', 'a2': 'A', 'b': 'B', 'c': 'C'},
        recipe=recipe, synthetic_only=True)


def prepared(**changes):
    values = data_parts(); values.update(changes); return prepare_gkt_training_data(**values)


def plan(**changes):
    values = dict(max_epochs=2, batch_size=2, shuffle_seed=42, selection_policy='min_selection_mean_bce',
                  min_delta=0., tie_policy='earliest_epoch')
    values.update(changes); return GKTEpochPlan(**values)


def budget(**changes):
    values = dict(max_steps=2, max_targets=12, max_seconds=40., max_checkpoint_bytes=1_000_000,
                  max_prediction_bytes=20000, approval_reference='USER_GKT06_HANDMADE_ENGINEERING_ONLY')
    values.update(changes); return GKTPipelineBudget(**values)


def test_train_only_vocabulary_mapping_support_and_role_population():
    data = prepared(); data.assert_integrity()
    assert data.train_item_vocabulary.values == ('a', 'a2', 'b')
    assert dict(data.train_item_support) == {'a': 2, 'a2': 1, 'b': 2}
    assert data.training_map == (('a', 'A'), ('a2', 'A'), ('b', 'B'))
    assert 'c' not in dict(data.training_map) and len(data.registry) == 4
    assert sum(sum(x.loss_mask) for x in data.train) == 6
    selection = data.selection[0]
    assert selection.source_rows == (101, 102, 103, 104)
    assert selection.support_reasons == ('cold_query_only', 'known_history', 'oov_item', 'unsupported_history')
    assert selection.model_valid_mask == (True, True, False, False)
    assert selection.loss_mask == (True, True, False, False)
    assert selection.node_indices == (0, 1, -1, 0)


def test_selection_labels_do_not_fit_item_vocabulary_or_mapping():
    parts = data_parts(); before = prepare_gkt_training_data(**parts)
    trajectory = parts['selection_shard'].trajectories[0]
    changed = replace(trajectory, observations=tuple(Observation(x.query, 1 - x.correct) for x in trajectory.observations))
    parts['selection_shard'] = replace(parts['selection_shard'], trajectories=(changed,))
    after = prepare_gkt_training_data(**parts)
    assert before.training_encoding_identity == after.training_encoding_identity
    assert before.content_sha256 != after.content_sha256


def test_cold_exclusion_keeps_first_real_event_for_future_history():
    parts = data_parts(); parts['recipe'] = replace(parts['recipe'], first_target_policy='unsupported')
    data = prepare_gkt_training_data(**parts)
    assert all(x.model_valid_mask == (True, True, True) for x in data.train)
    assert all(x.loss_mask == (False, True, True) for x in data.train)
    assert data.selection[0].support_reasons[:2] == ('cold_unsupported', 'known_history')


def test_collation_preserves_real_targets_separately_from_computational_mask():
    data = prepared()
    ids, labels, model_valid, loss, rows, ranks, real = collate_sequences(data.selection, dtype=torch.float64)
    assert int(real.sum()) == 4 and int(model_valid.sum()) == int(loss.sum()) == 2
    assert rows.tolist() == [[101, 102, 103, 104]] and ranks.tolist() == [[0, 1, 2, 3]]
    assert ids.tolist() == [[0, 1, -1, 0]] and labels.tolist() == [[0, 1, 1, 0]]
    with pytest.raises(ValueError): collate_sequences(tuple(data.train) * 2, dtype=torch.float64)


def test_prepared_data_mutation_and_source_binding_rejected():
    parts = data_parts(); data = prepare_gkt_training_data(**parts)
    parts['adjacency'].zero_(); data.assert_integrity()  # Caller graph is not the stored clone.
    data.adjacency[0, 1] += .1
    with pytest.raises(ValueError): data.assert_integrity()
    data = prepared(); data.source_sha256.clear()
    with pytest.raises(ValueError): data.assert_integrity()


@pytest.mark.parametrize('case', ['missing_train_map', 'multitag', 'foreignnode', 'wrongconcept', 'domain',
                                'nodevocab', 'graphorder', 'synthetic', 'shared_rows', 'wrongrole'])
def test_invalid_data_roles_mapping_and_identity_rejected(case):
    parts = data_parts()
    if case == 'missing_train_map': parts['item_node_registry'].pop('a')
    elif case == 'multitag': parts['item_node_registry']['a'] = ['A', 'B']
    elif case == 'foreignnode': parts['item_node_registry']['a'] = 'Z'
    elif case == 'wrongconcept': parts['item_node_registry']['a'] = 'B'
    elif case == 'domain': parts['node_binding'] = replace(parts['node_binding'], domain='Grade10')
    elif case == 'nodevocab': parts['node_binding'] = replace(parts['node_binding'], vocabulary_sha256='b' * 64)
    elif case == 'graphorder': parts['graph_provenance'] = replace(parts['graph_provenance'], node_order_sha256='b' * 64)
    elif case == 'synthetic': parts['synthetic_only'] = False
    elif case == 'shared_rows':
        shard = parts['selection_shard']; trajectory = shard.trajectories[0]
        changed = tuple(Observation(ItemQuery(x.query.item_id, x.query.timestamp, i + 1), x.correct)
                        for i, x in enumerate(trajectory.observations))
        parts['selection_shard'] = replace(shard, trajectories=(replace(trajectory, observations=changed),))
    elif case == 'wrongrole': parts['selection_shard'] = parts['train_shard']
    with pytest.raises(ValueError): prepare_gkt_training_data(**parts)


def test_wrong_role_shard_and_oracle_payload_rejected_without_fake_folds():
    parts = data_parts()
    with pytest.raises(ValueError): replace(parts['selection_shard'], trajectories=parts['train_shard'].trajectories[:1])
    payload = parts['train_shard'].trajectories[0].payload(); payload['latent_mastery'] = [1.]
    with pytest.raises(ValueError): ObservableTrajectory.from_payload(payload)


def epoch_rows(values):
    return [dict(epoch=i, complete_epoch=True, selection=dict(mean_loss=value,
        population=dict(expected_targets=4, scored_targets=2, unsupported_targets=2, research_fitted_targets=0),
        eligible_population_sha256='eligible-fixed', expected_population_sha256='all-original-fixed'))
        for i, value in enumerate(values, 1)]


@pytest.mark.parametrize('values,delta,expected', [((.8, .7), 0., 2), ((.8, .8), 0., 1),
                                                 ((.8, .9), 0., 1), ((.8, .75), .1, 1)])
def test_explicit_selection_best_tie_worse_and_min_delta(values, delta, expected):
    assert select_epoch(epoch_rows(values), plan(min_delta=delta)) == expected
    assert select_epoch(epoch_rows(values), plan(selection_policy='last_complete_epoch_no_selection')) == 2


@pytest.mark.parametrize('case', ['incomplete', 'changed_eligible', 'changed_all', 'no_eligible', 'nan'])
def test_selector_never_accepts_partial_or_different_population(case):
    rows = epoch_rows((.8, .7))
    if case == 'incomplete': rows[1]['complete_epoch'] = False
    elif case == 'changed_eligible': rows[1]['selection']['eligible_population_sha256'] = 'changed'
    elif case == 'changed_all': rows[1]['selection']['expected_population_sha256'] = 'changed'
    elif case == 'no_eligible': rows[1]['selection']['population']['scored_targets'] = 0
    elif case == 'nan': rows[1]['selection']['mean_loss'] = float('nan')
    with pytest.raises(ValueError): select_epoch(rows, plan())


def test_prediction_csv_keeps_unsupported_rows_not_a_model_fixture(tmp_path):
    # Explicit fake scalar values for FORMAT testing only; no model/checkpoint result claimed.
    rows = [dict(source_row=101, role='selection', correct=0, probability=.25, support_reason='cold_query_only', research_fitted=False),
            dict(source_row=102, role='selection', correct=1, probability=None, support_reason='oov_item', research_fitted=False)]
    path = tmp_path / 'format-only.csv'
    digest = export_predictions(path, rows, checkpoint_manifest_sha256='c' * 64, max_bytes=20000)
    with path.open(newline='') as stream: result = list(csv.DictReader(stream))
    assert len(result) == 2 and result[1]['probability'] == '' and len(digest) == 64
    assert result[1]['research_fitted'] == 'False'
    with pytest.raises(FileExistsError): export_predictions(path, rows, checkpoint_manifest_sha256='c' * 64, max_bytes=20000)
    with pytest.raises(ValueError): export_predictions(tmp_path / 'invalid.csv', [dict(rows[0], probability=float('nan'))],
        checkpoint_manifest_sha256='c' * 64, max_bytes=20000)


@pytest.mark.parametrize('changes', [{'max_epochs': 3}, {'batch_size': 3}, {'shuffle_seed': True},
    {'min_delta': float('nan')}, {'tie_policy': 'latest'}, {'selection_policy': 'implicit'}])
def test_explicit_epoch_plan_required(changes):
    with pytest.raises(ValueError): plan(**changes)


@pytest.mark.parametrize('changes', [{'max_steps': 5}, {'max_targets': 97}, {'max_seconds': 61},
    {'max_checkpoint_bytes': 2**21}, {'max_prediction_bytes': 0}, {'approval_reference': ''}])
def test_bounded_engineering_budget_required(changes):
    with pytest.raises(ValueError): budget(**changes)
