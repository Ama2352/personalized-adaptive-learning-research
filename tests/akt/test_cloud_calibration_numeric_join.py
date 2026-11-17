"""Nối numeric GPU sang raw/V1 trên CPU, dữ liệu tổng hợp có OOV."""
from dataclasses import asdict, replace
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import numpy as np
import pytest
from test_cloud_calibration_fit import cloud_case
from test_junyi_calibration_producer import case
from knowledge_tracing.akt import research_junyi_calibration as producer
from knowledge_tracing.akt.cloud_calibration_numeric_join import join_numeric_calibration_snapshot
from knowledge_tracing.akt.prediction_batch import prepare_prediction_windows
from knowledge_tracing.akt.research_junyi_numeric_predictions import NumericBinding, NumericWindow, write_numeric_shard
from knowledge_tracing.akt.research_junyi_window_cache import window_cache_key
from knowledge_tracing.akt.types import UnseenTarget


def numeric_case(case, variant):
    root = case['arguments']['artifact_root'].root
    directory = root / 'gpu-snapshot'
    directory.mkdir()
    binding = replace(case['binding'], model_id=variant + '_JUNYI_REFIT',
                      domain_sha256=producer.sha256_file(case['paths'].canonical))
    prepared = list(prepare_prediction_windows(case['adapter'], case['learners']))
    windows = [entry[0] for entry in prepared if not isinstance(entry, UnseenTarget)]
    source_sha = producer.sha256_file(case['paths'].canonical)
    summary = dict(records=len(prepared), windows=len(windows), unseen_targets=2,
        target_rows=20, window_tokens=sum(len(window.target_mask) for window in windows), learners=2)
    manifest = dict(status='COMPLETE', key=window_cache_key(case['phase'], case['encoding'], source_sha,
        expected_target_rows=20), summary=summary, shards=[])
    manifest_path = directory / 'window-manifest.json'
    manifest_path.write_text(json.dumps(manifest))
    manifest_sha = producer.sha256_file(manifest_path)
    admission = dict(kind='JUNYI_CPU_WINDOW_ADMISSION_V1', key=manifest['key'],
        summary=summary, shards=[], manifest_sha256=manifest_sha, strict_records_verified=summary['records'])
    admission_path = directory / 'window-admission.json'
    admission_path.write_text(json.dumps(admission))
    admission_sha = producer.sha256_file(admission_path)
    numeric = NumericBinding(variant, binding.checkpoint_sha256, binding.checkpoint_sha256,
        case['phase'].identity, case['encoding'].identity, manifest_sha, binding.model_source_sha256)
    shard = write_numeric_shard(directory, 'probabilities-0',
        [NumericWindow.from_window(window) for window in windows],
        [np.full(len(window.target_mask), .9, dtype=np.float64) for window in windows],
        binding=numeric, shard_index=0)
    graph_identity = None if variant == 'A0' else 'f'*64
    receipt = dict(kind='JUNYI_CACHED_NUMERIC_INFERENCE_V1', status='COMPLETE', binding=asdict(numeric),
        roles_sha256=case['phase'].roles.identity, source_data_sha256=source_sha,
        dataset_sha256=case['population']['identity'], window_admission_sha256=admission_sha,
        graph_cache_identity=graph_identity,
        counts=dict(records=len(prepared), windows=len(windows), targets=20, fitted_targets=18, oov_targets=2),
        shards=[dict(manifest_path=str(shard.manifest_path), manifest_sha256=shard.manifest_sha256)])
    receipt_path = directory / 'GPU_COMPLETE.json'
    receipt_path.write_text(json.dumps(receipt))
    kwargs = dict(binding=binding, numeric_binding=numeric, gpu_receipt=receipt_path,
        expected_gpu_receipt_sha256=producer.sha256_file(receipt_path), window_manifest=manifest_path,
        window_admission=admission_path, expected_window_admission_sha256=admission_sha,
        population=case['population'], expected_population_identity=case['population']['identity'],
        source_pins=case['pins'], max_targets=20, max_learner_events=10,
        artifact_root=case['arguments']['artifact_root'], run_id='numeric-calibration',
        raw_tranche_id='raw01', fit_tranche_id='fit01', expected_graph_cache_identity=graph_identity)
    return kwargs


@pytest.mark.parametrize('variant', ['A0', 'A1', 'A2', 'A3'])
def test_numeric_join_raw_and_temperature_match_existing_v1(cloud_case, variant):
    case = cloud_case
    kwargs = numeric_case(case, variant)
    baseline = producer.fit_response_temperature_from_raw_export(case['raw'], case['paths'], case['phase'],
        binding=kwargs['binding'], population=case['population'],
        expected_population_identity=case['population']['identity'],
        expected_manifest_sha256=case['arguments']['expected_manifest_sha256'],
        shard_sha256=case['arguments']['shard_sha256'], source_pins=case['pins'],
        max_targets=20, max_learner_events=10, output=case['output'] / 'baseline')
    result = join_numeric_calibration_snapshot(case['paths'], case['phase'], case['encoding'], **kwargs)
    raw = Path(result['raw_payloads']) / 'raw'
    manifest = json.loads((raw / 'manifest.json').read_text())
    assert manifest['prediction_rows'] == 20 and manifest['fitted_rows'] == 18 and manifest['unseen_rows'] == 2
    fit = kwargs['artifact_root'].root / 'numeric-calibration/fit01/payloads/fit/temperature.json'
    assert json.loads(fit.read_text()) == json.loads(json.dumps(baseline.to_payload()))
    request = result['publish_requests'][0]
    assert request['files'] == ['config.json', 'RAW_EXPORT.zip', 'COMPLETE.json']
    with zipfile.ZipFile(Path(result['raw_payloads']) / 'RAW_EXPORT.zip') as archive:
        inventory = json.loads(archive.read('INVENTORY.json'))
        assert set(archive.namelist()) == {'INVENTORY.json', *('raw/' + name for name in inventory)}
        import hashlib
        assert all(hashlib.sha256(archive.read('raw/' + name)).hexdigest() == pin['sha256']
                   for name, pin in inventory.items())


@pytest.mark.parametrize('mode', ['counts', 'phase', 'source', 'graph', 'incomplete', 'archive_cap', 'numeric_payload', 'domain'])
def test_numeric_join_rejects_mismatch_without_completion(cloud_case, mode):
    case = cloud_case
    kwargs = numeric_case(case, 'A1')
    path = kwargs['gpu_receipt']
    receipt = json.loads(path.read_text())
    if mode == 'counts':
        receipt['counts']['targets'] += 1
    elif mode == 'phase':
        kwargs['numeric_binding'] = replace(kwargs['numeric_binding'], phase_sha256='0'*64)
    elif mode == 'source':
        receipt['source_data_sha256'] = '0'*64
    elif mode == 'graph':
        receipt['graph_cache_identity'] = '0'*64
    elif mode == 'incomplete':
        receipt['status'] = 'INCOMPLETE'
    elif mode == 'domain':
        kwargs['binding'] = replace(kwargs['binding'], domain_sha256='0'*64)
    elif mode == 'archive_cap':
        kwargs['max_archive_bytes'] = 10
    else:
        payload = Path(receipt['shards'][0]['manifest_path']).with_suffix('.npz')
        payload.write_bytes(payload.read_bytes() + b'tamper')
    path.write_text(json.dumps(receipt))
    kwargs['expected_gpu_receipt_sha256'] = producer.sha256_file(path)
    with pytest.raises(ValueError):
        join_numeric_calibration_snapshot(case['paths'], case['phase'], case['encoding'], **kwargs)
    root = kwargs['artifact_root'].root / 'numeric-calibration'
    assert not (root / 'raw01/payloads/COMPLETE.json').exists()
    assert not (root / 'fit01/payloads/COMPLETE.json').exists()


def test_cpu_numeric_join_import_does_not_load_torch():
    subprocess.run([sys.executable, '-B', '-c',
        'import sys; import knowledge_tracing.akt.cloud_calibration_numeric_join; assert "torch" not in sys.modules'],
        capture_output=True, text=True, check=True)


@pytest.mark.parametrize('callback_raises', [False, True])
def test_raw_callback_runs_before_fit_and_failure_preserves_raw(cloud_case, monkeypatch, callback_raises):
    from knowledge_tracing.akt import cloud_calibration_numeric_join as joiner
    case = cloud_case
    kwargs = numeric_case(case, 'A0')
    order = []
    payloads = kwargs['artifact_root'].root / 'numeric-calibration/raw01/payloads'

    def on_raw_ready(request):
        assert (payloads / 'COMPLETE.json').is_file()
        assert (payloads / 'RAW_EXPORT.zip').is_file()
        assert request['files'] == ['config.json', 'RAW_EXPORT.zip', 'COMPLETE.json']
        order.append('raw_committed')
        if callback_raises:
            raise RuntimeError('synthetic commit failure')

    def fitter(*args, **options):
        assert order == ['raw_committed']
        order.append('fit')
        return dict(calibration_identity='a'*64, publish_request={'tranche_id': 'fit01'})

    monkeypatch.setattr(joiner, 'fit_volume_calibration', fitter)
    kwargs['on_raw_ready'] = on_raw_ready
    if callback_raises:
        with pytest.raises(RuntimeError, match='synthetic commit failure'):
            joiner.join_numeric_calibration_snapshot(case['paths'], case['phase'], case['encoding'], **kwargs)
        assert order == ['raw_committed']
        assert (payloads / 'COMPLETE.json').is_file()
    else:
        joiner.join_numeric_calibration_snapshot(case['paths'], case['phase'], case['encoding'], **kwargs)
        assert order == ['raw_committed', 'fit']
