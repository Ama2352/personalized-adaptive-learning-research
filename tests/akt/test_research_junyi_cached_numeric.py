"""Core tổng hợp cho cache→numeric, không runtime CUDA hoặc dữ liệu thật."""
from dataclasses import replace
import json
from types import SimpleNamespace

import pytest

from test_research_junyi_numeric_predictions import fixture
from knowledge_tracing.akt.prediction_batch import iter_predictions_batched
from knowledge_tracing.akt.research_junyi_cached_numeric import CachedNumericBudget, run_cached_numeric
from knowledge_tracing.akt.research_junyi_numeric_predictions import NumericShard, iter_numeric_prediction_records
from knowledge_tracing.akt.types import UnseenTarget
from knowledge_tracing.response_calibration import PredictionBinding


def setup(tmp_path, variant, items):
    adapter, learner, prepared, _, kwargs = fixture(tmp_path / 'original', items, variant)
    binding = kwargs['binding']
    records = tuple(item if isinstance(item, UnseenTarget) else item[0] for item in prepared)
    view = SimpleNamespace(identity=binding.phase_sha256, roles=SimpleNamespace(identity='b' * 64))
    cache = SimpleNamespace(admission_receipt='CPU.json', expected_admission_sha256='c' * 64,
        expected_manifest_sha256=binding.window_manifest_sha256, view=view,
        encoding=SimpleNamespace(identity=binding.encoding_sha256), source_data_sha256='d' * 64,
        expected_target_rows=len(items), assert_boundary=lambda: None, iter_windows=lambda: iter(records))
    pb = PredictionBinding(checkpoint_sha256=binding.checkpoint_sha256,
        model_id=variant + '_JUNYI_REFIT', model_source_sha256=binding.source_sha256,
        split_sha256='b' * 64, vocabulary_sha256=binding.encoding_sha256,
        bank_sha256='f'*64, reference_sha256='f'*64, domain_sha256=cache.source_data_sha256)
    predictor = SimpleNamespace(adapter=adapter, binding=pb, assert_boundary=lambda: None)
    phase = graph = None
    if variant != 'A0':
        phase = SimpleNamespace(condition=SimpleNamespace(variant=variant), view=view)
        graph = SimpleNamespace(windows=kwargs['expected_windows'], targets=kwargs['expected_targets'],
            identity='graph-id', assert_for=lambda phase: None,
            binding=json.dumps(dict(dataset_sha256='e'*64,
                                    window_manifest_sha256=binding.window_manifest_sha256)))
        adapter.set_phase = lambda value, context_cache: setattr(adapter, 'attached_cache', context_cache)
    budget = CachedNumericBudget(60, 1024**3, 1024**3, len(records), kwargs['expected_windows'],
                                len(items), len(items)-kwargs['expected_targets'], batch_size=2)
    args = dict(graph_cache=graph, phase=phase, binding=binding, roles_sha256='b' * 64,
        dataset_sha256='e'*64,
        output_root=tmp_path/'output', budget=budget, snapshot=lambda: dict(rss_bytes=100, vram_bytes=200))
    return predictor, cache, args, prepared, learner, kwargs


@pytest.mark.parametrize('variant', ['A0', 'A1', 'A2', 'A3'])
@pytest.mark.parametrize('items', [['A'], ['X'] * 4, ['A'] * 201 + ['X', 'B']])
def test_core_join_exact_parity(tmp_path, variant, items):
    predictor, cache, args, prepared, learner, kwargs = setup(tmp_path, variant, items)
    expected = list(iter_predictions_batched(predictor.adapter, [learner]))
    result = run_cached_numeric(predictor, cache, **args)
    receipt = json.loads(open(result['receipt_path'], encoding='utf-8').read())
    shards = tuple(NumericShard(**entry) for entry in receipt['shards'])
    actual = list(iter_numeric_prediction_records(predictor.adapter, prepared, shards, **kwargs))
    assert actual == expected
    assert receipt['counts']['targets'] == len(items)
    assert receipt['volume_commit_required'] is True
    assert receipt['timings']['volume_commit_seconds'] is None
    if variant != 'A0':
        assert predictor.adapter.attached_cache is args['graph_cache']
    assert receipt['telemetry']['peak_vram_bytes'] == 200


@pytest.mark.parametrize('mode', ['admission', 'source', 'roles', 'model', 'count', 'graph', 'rss', 'vram', 'wall'])
def test_rejects_bad_inputs_without_complete_receipt(tmp_path, mode):
    predictor, cache, args, _, _, _ = setup(tmp_path, 'A1', ['A'] * 101)
    if mode == 'admission':
        cache.admission_receipt = None
    elif mode == 'source':
        predictor.binding = replace(predictor.binding, model_source_sha256='e' * 64)
    elif mode == 'roles':
        args['roles_sha256'] = 'e' * 64
    elif mode == 'model':
        predictor.binding = replace(predictor.binding, model_id='A2_JUNYI_REFIT')
    elif mode == 'count':
        args['budget'] = replace(args['budget'], expected_records=3)
    elif mode == 'graph':
        args['graph_cache'] = None
    elif mode == 'rss':
        args['snapshot'] = lambda: dict(rss_bytes=2*1024**3, vram_bytes=0)
    elif mode == 'vram':
        args['snapshot'] = lambda: dict(rss_bytes=0, vram_bytes=2*1024**3)
    else:
        args['setup_seconds'] = 61
    with pytest.raises((ValueError, RuntimeError)):
        run_cached_numeric(predictor, cache, **args)
    assert not (args['output_root']/'RECEIPT.json').exists()


def test_existing_output_not_overwritten(tmp_path):
    predictor, cache, args, _, _, _ = setup(tmp_path, 'A0', ['A'])
    run_cached_numeric(predictor, cache, **args)
    with pytest.raises(FileExistsError):
        run_cached_numeric(predictor, cache, **args)


def test_cuda_wrapper_has_no_cpu_fallback(tmp_path):
    from knowledge_tracing.akt.research_junyi_cached_numeric import run_cuda_cached_numeric
    with pytest.raises(ValueError, match='native CUDA'):
        run_cuda_cached_numeric({'cuda_profile': None, 'config': SimpleNamespace(device='cpu')}, None,
            graph_cache=None, phase=None, binding=None, dataset_sha256='e'*64,
            output_root=tmp_path/'new', budget=None)
