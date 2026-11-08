"""Pure handmade metadata; không Method24 artifact/corpus/model/solver thực.

LoadedMethod24Scores dưới đây là container fixture UNVERIFIED, không receipt fit.
Tests chứng minh admission/converter consistency, không xác minh lại producer.
"""
from dataclasses import FrozenInstanceError, replace
import builtins
import hashlib
import importlib

import pytest

from knowledge_tracing.akt import research_graph_condition as condition
from knowledge_tracing.edge_confidence_artifact import (LoadedEdgePredictiveScore,
    LoadedMethod24Scores, Method24TrainingBinding, PUBLIC, SEMANTICS)
from knowledge_tracing.simulator_bridge import SimulatorBank, SimulatorItem, identity_hash


def h(label):
    return hashlib.sha256(label.encode()).hexdigest()


@pytest.fixture(autouse=True)
def no_neural_solver_or_array_import(monkeypatch):
    original = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name.split('.')[0] in {'numpy', 'torch', 'sklearn', 'scipy', 'pandas', 'joblib'}:
            raise AssertionError('stdlib condition must not import: ' + name)
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', guarded)


@pytest.fixture
def case(monkeypatch):
    # No parser is executed, even though metadata types are reused.
    from knowledge_tracing import edge_confidence_artifact as reader
    monkeypatch.setattr(reader, 'load_method24_scores', lambda *a, **k: pytest.fail('no actual artifact reads'))
    bank = SimulatorBank('UNVERIFIED_HANDMADE_METADATA_NOT_RESEARCH_CORPUS', tuple(
        SimulatorItem('item-' + str(i), 'c' + str(i).zfill(2), 1200) for i in range(28)))
    nodes = tuple(sorted({i.concept_id for i in bank.items}))
    edges = (('c00', 'c01'), ('c00', 'c02'))
    public = {name: h(name) for name in PUBLIC}
    public.update({'corpus.json': h('corpus'), 'DONE.json': h('done'), 'train.jsonl': h('train observable')})
    training = Method24TrainingBinding('HANDMADE_NOT_REAL_CORPUS', h('corpus'), h('done'), h('logical plan'),
        h('train provenance'), h('train observable'), identity_hash(bank.identity), h('method source'),
        h('method config'), h('runtime profile'), tuple(sorted(public.items())),
        (('src/knowledge_tracing/edge_confidence.py', h('method source')),),
        (('UNVERIFIED-runtime-metadata', h('runtime bytes')),))
    train80 = condition.GraphTrain80Binding(training.corpus_id, training.corpus_sha256,
        training.corpus_done_sha256, training.plan_sha256, training.train_provenance_sha256,
        training.train_observable_sha256, training.domain_sha256, h('audited train shard'),
        h('audited selection shard'), h('audited calibration shard'))
    scores = (LoadedEdgePredictiveScore(*edges[0], True, 0., None, 30, 25, 5, 20, -.01, 0, 200),
              LoadedEdgePredictiveScore(*edges[1], False, None, 'insufficient_eligible_learners', 30, 2, 28, 2, None, None, 200))
    loaded = LoadedMethod24Scores('declared', nodes, edges, scores, training,
        (('MANUFACTURED_NO_FILE', h('envelope')),), h('prepared'), h('producer result'), h('exported graph'), 2352, 2352)
    return dict(bank=bank, nodes=nodes, edges=edges, train80=train80, training=training, loaded=loaded)


def build(case, variant='A3', **changes):
    args = dict(variant=variant, graph_mode='expert_declared', bank=case['bank'],
        nodes=case['nodes'], edges=case['edges'], train80=case['train80'],
        expected_sources=condition.source_inventory(), topology_source_sha256=h('expert graph'))
    if variant in ('A2', 'A3'):
        args.update(loaded_scores=case['loaded'], expected_method24_training=case['training'],
                    expected_scores_sha256=case['loaded'].identity)
    args.update(changes)
    return condition.prepare_research_graph_condition(**args)


def learned(case):
    edges = tuple((p, c) for p in case['nodes'] for c in case['nodes'] if p < c)[:31]
    records = tuple(LoadedEdgePredictiveScore(p, c, True, .5, None, 30, 25, 5, 20, .01, 100, 200) for p, c in edges)
    loaded = replace(case['loaded'], graph_binding='method24_learned', declared_edges=edges, edge_scores=records)
    return edges, loaded


def test_import_is_stdlib_only():
    importlib.reload(condition)


def test_supported_zero_and_unsupported_null_stay_distinct(case):
    result = build(case)
    supported, missing = result.edge_weights
    assert supported.supported and supported.source_score == supported.operational_weight == 0.
    assert not missing.supported and missing.source_score is None and missing.operational_weight == 0.
    assert missing.unsupported_reason == 'insufficient_eligible_learners'
    assert result.method24_scores is case['loaded']
    payload = result.kernel_confidence_kwargs()
    assert payload == dict(kind='estimated_probability', values=(('c00', 'c01', 0.), ('c00', 'c02', 0.)),
                          fitted_role='train', provenance_sha256=result.identity)
    assert result.confidence_semantics == SEMANTICS
    assert 'edge_truth' in result.confidence_semantics


@pytest.mark.parametrize('variant', ['A2', 'A3'])
def test_confidence_variants_preserve_expert_edges_even_unsupported(case, variant):
    result = build(case, variant)
    assert result.edges == case['edges'] and len(result.edge_weights) == 2
    assert result.graph_confidence_refit_policy == 'frozen_train80_through_neural_refit90'
    assert result.architecture['alpha_initial'] == 0.
    assert result.architecture['message_dimension'] == 1
    assert result.architecture['gate'] == ('sigmoid_linear_4_to_1' if variant == 'A3' else 'fixed_one')


def test_a0_does_not_require_method24_or_graph(case):
    result = build(case, 'A0', graph_mode='none', nodes=(), edges=(), topology_source_sha256=None)
    assert result.edges == result.edge_weights == () and result.method24_scores is None
    assert result.kernel_confidence_kwargs()['kind'] == 'fixed_uniform'
    assert result.architecture['alpha_initial'] is None
    assert result.architecture['system_fallback'] == 'independently_trained_A0_checkpoint'


def test_a1_retains_declared_topology_without_estimator(case):
    result = build(case, 'A1')
    assert result.edges == case['edges'] and result.method24_scores is None
    assert result.kernel_confidence_kwargs()['values'] == tuple((p, c, 1.) for p, c in case['edges'])
    assert result.kernel_confidence_kwargs()['fitted_role'] is None


def test_missing_isolated_concept_is_not_an_implicit_induced_subgraph(case):
    with pytest.raises(ValueError, match='all bank concepts'):
        build(case, 'A1', nodes=case['nodes'][:-1])


@pytest.mark.parametrize('variant', ['A1', 'A2', 'A3'])
def test_learned_topology_exact31_requires_loader_even_uniform_a1(case, variant):
    edges, loaded = learned(case)
    result = build(case, variant, graph_mode='method24_learned', edges=edges,
        topology_source_sha256=loaded.exported_graph_sha256, loaded_scores=loaded,
        expected_method24_training=case['training'], expected_scores_sha256=loaded.identity)
    assert len(result.edges) == 31
    assert {e.operational_weight for e in result.edge_weights} == ({1.} if variant == 'A1' else {.5})


@pytest.mark.parametrize('field,value', [('score_semantics', 'P_edge_true'), ('fit_scope', 'refit90'),
    ('oracle_inputs_used', True), ('graph_binding', 'method24_learned')])
def test_nonresearch_or_wrong_mode_loader_rejected(case, field, value):
    loaded = replace(case['loaded'], **{field: value})
    with pytest.raises(ValueError):
        build(case, loaded_scores=loaded, expected_scores_sha256=loaded.identity)


@pytest.mark.parametrize('change', ['missing', 'extra', 'duplicate', 'reordered'])
def test_exact_edge_population(case, change):
    a, b = case['loaded'].edge_scores
    records = {'missing': (a,), 'extra': (a, b, replace(a, parent_id='c01', child_id='c02')),
               'duplicate': (a, a), 'reordered': (b, a)}[change]
    loaded = replace(case['loaded'], edge_scores=records)
    with pytest.raises(ValueError, match='edge scores'):
        build(case, loaded_scores=loaded, expected_scores_sha256=loaded.identity)


@pytest.mark.parametrize('change', [dict(supported=False), dict(score=None), dict(score=True),
    dict(score=float('nan')), dict(score=1.1), dict(reason='wrong supported reason')])
def test_supported_schema_not_null_filled(case, change):
    edge = replace(case['loaded'].edge_scores[0], **change)
    loaded = replace(case['loaded'], edge_scores=(edge, case['loaded'].edge_scores[1]))
    # NaN cannot even form a finite external identity; this too is rejection.
    with pytest.raises(ValueError):
        build(case, loaded_scores=loaded, expected_scores_sha256=loaded.identity)


@pytest.mark.parametrize('change', [dict(score=0.), dict(reason=None), dict(reason='')])
def test_unsupported_requires_null_plus_reason(case, change):
    loaded = replace(case['loaded'], edge_scores=(case['loaded'].edge_scores[0],
        replace(case['loaded'].edge_scores[1], **change)))
    with pytest.raises(ValueError):
        build(case, loaded_scores=loaded, expected_scores_sha256=loaded.identity)


@pytest.mark.parametrize('field', ['corpus_sha256', 'corpus_done_sha256', 'plan_sha256',
    'train_provenance_sha256', 'train_observable_sha256'])
def test_train80_lineage_not_relabelled(case, field):
    with pytest.raises(ValueError):
        build(case, train80=replace(case['train80'], **{field: h('wrong lineage')}))


@pytest.mark.parametrize('changes', [dict(recipe='engineering-observed-parent-mean-v1'), dict(recipe='draft-D1'),
    dict(variant='oracle'), dict(graph_mode='structural_score'), dict(expected_scores_sha256=h('wrong')),
    dict(expected_method24_training=None), dict(loaded_scores=None), dict(topology_source_sha256='bad')])
def test_admission_tags_and_external_pins(case, changes):
    with pytest.raises(ValueError):
        build(case, **changes)


def test_foreign_bank_rejected(case):
    with pytest.raises(ValueError, match='domain'):
        build(case, bank=SimulatorBank('FOREIGN', case['bank'].items))


@pytest.mark.parametrize('nodes,edges', [
    (('c00', 'c01', 'c00'), ()), (('foreign',), ()),
    (('c00', 'c01'), (('c00', 'c01'), ('c00', 'c01'))),
    (('c00', 'c01'), (('c00', 'c00'),)),
    (('c00', 'c01'), (('c00', 'c01'), ('c01', 'c00')))])
def test_invalid_topology_rejected(case, nodes, edges):
    with pytest.raises(ValueError):
        build(case, 'A1', nodes=nodes, edges=edges)


@pytest.mark.parametrize('change', ['budget', 'nonpositive', 'unsupported', 'source'])
def test_learned_rule_cannot_be_applied_to_partial_dag(case, change):
    edges, loaded = learned(case)
    if change == 'budget':
        edges = edges[:-1]
        loaded = replace(loaded, declared_edges=edges, edge_scores=loaded.edge_scores[:-1])
    elif change == 'nonpositive':
        loaded = replace(loaded, edge_scores=(replace(loaded.edge_scores[0], point_delta=0.),) + loaded.edge_scores[1:])
    elif change == 'unsupported':
        loaded = replace(loaded, edge_scores=(replace(loaded.edge_scores[0], supported=False,
            score=None, reason='insufficient', point_delta=None, bootstrap_positive=None),) + loaded.edge_scores[1:])
    with pytest.raises(ValueError):
        build(case, graph_mode='method24_learned', edges=edges, loaded_scores=loaded,
            expected_scores_sha256=loaded.identity,
            topology_source_sha256=h('wrong') if change == 'source' else loaded.exported_graph_sha256)


def test_current_sources_exact_then_mutation_rejected(case, monkeypatch):
    sources = condition.source_inventory()
    with pytest.raises(ValueError, match='source pins'):
        build(case, expected_sources=sources[:-1])
    result = build(case)
    monkeypatch.setattr(condition, 'source_inventory', lambda: sources[:-1])
    with pytest.raises(ValueError, match='source drift'):
        result.kernel_confidence_kwargs()


def test_condition_immutable_and_sealed(case):
    result = build(case)
    with pytest.raises(FrozenInstanceError):
        result.variant = 'A0'
    object.__setattr__(result, 'edges', ())  # Simulate accidental frozen bypass.
    with pytest.raises(ValueError, match='payload drift'):
        result.assert_integrity()


@pytest.mark.parametrize('scope', ['select_train80', 'raw_selection10', 'refit_union90', 'calibration_predict'])
def test_neural90_separate_lineage_graph_stays80(case, scope):
    result = build(case)
    train80 = result.train80
    shards = {'select_train80': (('train', train80.train_shard_sha256),),
        'raw_selection10': (('selection', train80.selection_shard_sha256),),
        'refit_union90': (('selection', train80.selection_shard_sha256), ('train', train80.train_shard_sha256)),
        'calibration_predict': (('calibration', train80.calibration_shard_sha256),)}[scope]
    after_freeze = scope in ('refit_union90', 'calibration_predict')
    binding = condition.bind_graph_neural_phase(result, phase_scope=scope,
        encoding_sha256=h('encoding90' if after_freeze else 'encoding80'), vocabulary_sha256=h('same actual item values'),
        fit80_encoding_sha256=h('encoding80'),
        encoding_fit_scope='refit_union90' if after_freeze else 'select_train80',
        neural_shards_sha256=shards, selection_freeze_sha256=h('external freeze') if after_freeze else None)
    assert binding.condition_sha256 == result.identity
    assert binding.graph_confidence_train80_sha256 == train80.identity
    assert binding.graph_confidence_refitted_on90 is False
    assert binding.encoding_sha256 == h('encoding90' if after_freeze else 'encoding80')


@pytest.mark.parametrize('change', ['missingfreeze', 'sameencoding', 'wrongfitrole', 'unionrelabeled', 'changedtrain'])
def test_refit_cannot_change_condition_or_fake_origin_roles(case, change):
    result = build(case)
    args = dict(phase_scope='refit_union90', encoding_sha256=h('encoding90'), vocabulary_sha256=h('actual item values'),
        fit80_encoding_sha256=h('encoding80'),
        encoding_fit_scope='refit_union90', selection_freeze_sha256=h('external freeze'),
        neural_shards_sha256=(('selection', result.train80.selection_shard_sha256), ('train', result.train80.train_shard_sha256)))
    if change == 'missingfreeze': args['selection_freeze_sha256'] = None
    elif change == 'sameencoding': args['encoding_sha256'] = args['fit80_encoding_sha256']
    elif change == 'wrongfitrole': args['encoding_fit_scope'] = 'select_train80'
    elif change == 'unionrelabeled': args['neural_shards_sha256'] = (('train', h('union mislabeled')),)
    else: args['neural_shards_sha256'] = (('selection', result.train80.selection_shard_sha256), ('train', h('changed train')))
    with pytest.raises(ValueError):
        condition.bind_graph_neural_phase(result, **args)


@pytest.mark.parametrize('change', [dict(condition_sha256='bad'), dict(phase_scope='oracle_reference'),
    dict(graph_confidence_refitted_on90=True), dict(neural_shards_sha256=(('train', h('union')),)),
    dict(selection_freeze_sha256=None)])
def test_direct_phase_container_rejects_accidental_invalid_shape(change):
    fields = dict(condition_sha256=h('condition'), phase_scope='refit_union90', encoding_sha256=h('encoding90'),
        vocabulary_sha256=h('same item values'), fit80_encoding_sha256=h('encoding80'), encoding_fit_scope='refit_union90',
        neural_shards_sha256=(('selection', h('selection')), ('train', h('train'))),
        selection_freeze_sha256=h('external freeze metadata not authority'), graph_confidence_train80_sha256=h('train80'))
    fields.update(change)
    with pytest.raises(ValueError):
        condition.GraphNeuralPhaseBinding(**fields)
