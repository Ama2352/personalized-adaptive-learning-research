"""Recovery audit giữ raw Parquet và helper gốc, chỉ ở process CPU riêng."""
import importlib.util
import json
from pathlib import Path

import duckdb
import pytest
from test_cloud_calibration_fit import cloud_case
from test_junyi_calibration_producer import case
from knowledge_tracing.akt import prediction
from knowledge_tracing.akt.types import KTEvent,LearnerEvents

spec=importlib.util.spec_from_file_location('calibration_audit_transaction',
    Path(__file__).resolve().parents[2]/'scripts/akt/calibration_audit_transaction.py')
recovery=importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)


@pytest.fixture
def failed_raw(cloud_case,monkeypatch):
    case=cloud_case
    root=case['arguments']['artifact_root'].root
    raw=root/'run/a0-raw-old01/payloads/raw'
    identity=json.loads((case['raw']/'manifest.json').read_text())['identity']
    original=prediction._expected_insert
    def fail_audit(*args):raise RuntimeError('synthetic expected-row failure')
    monkeypatch.setattr(prediction,'_expected_insert',fail_audit)
    with pytest.raises(RuntimeError,match='synthetic expected-row failure'):
        prediction.export_predictions(prediction.iter_predictions(case['adapter'],iter(case['learners'])),raw,
            expected_learners_factory=lambda:iter(case['learners']),identity=identity,
            artifact_root=case['arguments']['artifact_root'])
    monkeypatch.setattr(prediction,'_expected_insert',original)
    marker=root/'run/a0-cpu-join-operation-old01/payloads/FAILED.json'
    marker.parent.mkdir(parents=True)
    marker.write_text(json.dumps(dict(stage='cpu-join',error_type='RuntimeError')))
    case['recover_raw']=raw
    case['recover_kwargs']=dict(binding=case['binding'],population=case['population'],source_pins=case['pins'],
        expected_manifest_sha256=recovery.sha256_file(raw/'manifest.json'),writer_closed_marker=marker,
        expected_writer_closed_sha256=recovery.sha256_file(marker),artifact_root=case['arguments']['artifact_root'],
        receipt_output=root/'run/a0-audit-recovery01/payloads')
    return case


def test_recovery_reuses_identical_parquet_and_original_audit(failed_raw,monkeypatch):
    case=failed_raw
    raw=case['recover_raw']
    before={p.name:recovery.sha256_file(p) for p in raw.glob('*.parquet')}
    old_wal=b'synthetic prior interrupted WAL'
    (raw/'.audit.tmp.duckdb.wal').write_bytes(old_wal)
    insert=prediction._expected_insert
    prepare=prediction._prepare_output
    monkeypatch.setattr(prediction,'iter_predictions',lambda *_:pytest.fail('Recovery cannot call model'))
    result=recovery.resume_completed_raw_audit(raw,case['paths'],case['phase'],**case['recover_kwargs'])
    assert result['prediction_rows']==20 and result['shards']==2
    assert json.loads((raw/'manifest.json').read_text())['status']=='complete'
    assert {p.name:recovery.sha256_file(p) for p in raw.glob('*.parquet')}==before
    assert prediction._expected_insert is insert and prediction._prepare_output is prepare
    assert (case['recover_kwargs']['receipt_output']/'BEFORE_MANIFEST.json').is_file()
    assert (case['recover_kwargs']['receipt_output']/'before-audit/.audit.tmp.duckdb.wal').read_bytes()==old_wal


@pytest.mark.parametrize('mode',['not_closed','other_attempt'])
def test_recovery_requires_matching_writer_closed_marker(failed_raw,mode):
    case=failed_raw
    options=case['recover_kwargs']
    if mode=='not_closed':
        options['writer_closed_marker'].unlink()
    else:
        other=options['writer_closed_marker'].parents[2]/'other-operation/payloads/FAILED.json'
        other.parent.mkdir(parents=True)
        other.write_text(json.dumps(dict(stage='cpu-join')))
        options['writer_closed_marker']=other
        options['expected_writer_closed_sha256']=recovery.sha256_file(other)
    with pytest.raises(ValueError):
        recovery.resume_completed_raw_audit(case['recover_raw'],case['paths'],case['phase'],**options)
    assert not options['receipt_output'].exists()


def test_transaction_failure_rolls_back_and_restores_original_helper():
    first=LearnerEvents('a',0,(KTEvent('a','i',0,1,0,0,0),))
    duplicate=LearnerEvents('b',0,(KTEvent('b','i',0,1,1,0,0),))
    original=prediction._expected_insert
    with duckdb.connect() as con:
        with pytest.raises(duckdb.ConstraintException):
            with recovery.transactional_expected_insert():
                prediction._expected_insert(con,lambda:iter((first,duplicate)))
        assert con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name='expected'").fetchone()[0]==0
    assert prediction._expected_insert is original


@pytest.mark.parametrize('fault', [None, 'tasks_running', 'wrong_request'])
def test_cancelled_writer_requires_tasks_zero_and_original_authorization(failed_raw, fault):
    case=failed_raw
    options=case['recover_kwargs']
    old_marker=options['writer_closed_marker']
    old_marker.unlink()
    config_path=old_marker.parent/'config.json'
    config=dict(stage='cpu-join',request=dict(run_id='run',variant='A0'),
        authorization=dict(stage='cpu-join',allocation_id='old01',request_sha256='8'*64))
    config_path.write_text(json.dumps(config))
    receipt=old_marker.parents[3]/'external-stop.json'
    value=dict(kind='MODAL_CPU_WRITER_STOPPED_V1',status='APP_STOPPED',tasks=0,stage='cpu-join',
        app_id='ap-synthetic',run_id='run',operation_tranche='a0-cpu-join-operation-old01',
        allocation_id='old01',request_sha256='8'*64,
        operation_config_sha256=recovery.sha256_file(config_path))
    if fault=='tasks_running':value['tasks']=1
    if fault=='wrong_request':value['request_sha256']='9'*64
    receipt.write_text(json.dumps(value))
    options['writer_closed_marker']=receipt
    options['expected_writer_closed_sha256']=recovery.sha256_file(receipt)
    if fault:
        with pytest.raises(ValueError,match='external stop receipt'):
            recovery.resume_completed_raw_audit(case['recover_raw'],case['paths'],case['phase'],**options)
        assert not options['receipt_output'].exists()
    else:
        result=recovery.resume_completed_raw_audit(case['recover_raw'],case['paths'],case['phase'],**options)
        assert result['prediction_rows']==20


@pytest.mark.parametrize('name', ['part-unlisted.parquet', '.pending/unlisted.parquet.tmp'])
def test_recovery_preserves_unlisted_files_and_rejects_cleanup(failed_raw, name):
    case=failed_raw
    path=case['recover_raw']/name
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(b'preserve')
    with pytest.raises(ValueError,match='unlisted'):
        recovery.resume_completed_raw_audit(case['recover_raw'],case['paths'],case['phase'],**case['recover_kwargs'])
    assert path.read_bytes()==b'preserve'
    assert not case['recover_kwargs']['receipt_output'].exists()


@pytest.fixture
def pipeline_case(failed_raw,monkeypatch):
    import sys,shutil
    from dataclasses import asdict,replace
    from test_cloud_calibration_numeric_join import numeric_case
    from test_modal_junyi_calibration import request as make_request
    from knowledge_tracing.akt.research_junyi_graph_cache import _digest,FORMAT
    from knowledge_tracing.akt.research_junyi_inference import _identity
    case=failed_raw
    root=case['arguments']['artifact_root'].root
    old=case['recover_raw'].parents[1]
    new=old.with_name('a1-raw-old01')
    old.rename(new)
    case['recover_raw']=new/'payloads/raw'
    old_marker=case['recover_kwargs']['writer_closed_marker']
    operation=old_marker.parents[1]
    new_operation=operation.with_name('a1-cpu-join-operation-old01')
    operation.rename(new_operation)
    closed=new_operation/'payloads/FAILED.json'
    kwargs=numeric_case(case,'A1')
    gpu_dir=root/'run/a1-numeric/payloads'
    gpu_dir.mkdir(parents=True)
    for path in kwargs['gpu_receipt'].parent.iterdir():
        if path.is_file():shutil.copyfile(path,gpu_dir/path.name)
    numeric=json.loads(kwargs['gpu_receipt'].read_text())
    for shard in numeric['shards']:
        shard['manifest_path']=str(gpu_dir/Path(shard['manifest_path']).name)
    graph=dict(sha256='5'*64,binding=dict(synthetic=True))
    numeric['graph_cache_identity']=_digest((FORMAT,graph['sha256'],json.dumps(graph['binding'],sort_keys=True)))
    receipt=gpu_dir/'RECEIPT.json'
    receipt.write_text(json.dumps(numeric))
    request=make_request()
    request.update(run_id='run',variant='A1',gpu_output='run/a1-numeric/payloads',
        source_identity=case['binding'].model_source_sha256,cpu_budget=dict(max_learner_events=10),
        source_pins=case['pins'])
    cache=dict(source_data_sha256=recovery.sha256_file(case['paths'].canonical),
        windows=dict(manifest_sha256=kwargs['numeric_binding'].window_manifest_sha256,
            admission_sha256=kwargs['expected_window_admission_sha256']),graphs=dict(A1=graph))
    cache_path=root/'cache.json';cache_path.write_text(json.dumps(cache))
    request['cache_receipt']=dict(path=str(cache_path),sha256=recovery.sha256_file(cache_path))
    (gpu_dir/'config.json').write_text(json.dumps(request))
    binding=replace(kwargs['binding'],
        bank_sha256=_identity(dict(domain='junyi_exercises',values=case['encoding'].native.vocabulary.values)),
        reference_sha256=_identity(dict(domain='junyi_logged_response',reference_bank='not_applicable')))
    old_config=dict(binding=asdict(binding),numeric_binding=asdict(kwargs['numeric_binding']),
        gpu_receipt_sha256=recovery.sha256_file(receipt),population_identity=case['population']['identity'],
        source_pins=case['pins'],counts=numeric['counts'],
        window_admission_sha256=kwargs['expected_window_admission_sha256'])
    raw=case['recover_raw']
    (raw.parent/'config.json').write_text(json.dumps(old_config))
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2]/'scripts/akt'))
    import calibration_cloud_worker as worker
    assets=dict(index=dict(model='A1_JUNYI_REFIT',checkpoint_sha256=binding.checkpoint_sha256),
        encoding=case['encoding'],calibration=case['phase'])
    monkeypatch.setattr(worker,'load_inputs',lambda *_:({'A1':assets},case['paths'],case['population']))
    case['pipeline_options']=dict(request=request,root=root,
        gpu_result=dict(receipt_path=str(receipt),receipt_sha256=recovery.sha256_file(receipt)),
        raw_source_pin=dict(path=str(raw/'manifest.json'),sha256=recovery.sha256_file(raw/'manifest.json')),
        closed_marker_pin=dict(path=str(closed),sha256=recovery.sha256_file(closed)),attempt_id='recovery01')
    return case


def test_full_cpu_recovery_reuses_raw_then_archives_fits_and_publishes(pipeline_case):
    case=pipeline_case
    order=[]
    def commit():order.append('commit')
    def publish(publication):
        assert order[-1]=='commit'
        root=case['pipeline_options']['root']
        assert all((root/publication['run_id']/publication['tranche_id']/'payloads'/name).is_file()
                   for name in publication['files'])
        order.append(publication['tranche_id'])
        return dict(status='SYNTHETIC_PUBLISHED',tranche=publication['tranche_id'])
    before={p.name:recovery.sha256_file(p) for p in case['recover_raw'].glob('*.parquet')}
    result=recovery.recover_cpu_calibration(**case['pipeline_options'],volume_commit=commit,publish=publish)
    assert result['status']=='CPU_CALIBRATION_RECOVERY_PUBLISHED'
    assert len(result['publish_receipts'])==3
    assert {p.name:recovery.sha256_file(p) for p in case['recover_raw'].glob('*.parquet')}==before
    assert (case['pipeline_options']['root']/'run/a1-fit-recovery01/payloads/fit/temperature.json').is_file()


def test_full_cpu_recovery_rejects_original_raw_binding_mismatch(pipeline_case):
    case=pipeline_case
    config=case['recover_raw'].parent/'config.json'
    value=json.loads(config.read_text());value['binding']['checkpoint_sha256']='0'*64
    config.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='recovery bindings mismatch'):
        recovery.recover_cpu_calibration(**case['pipeline_options'],volume_commit=lambda:None,
            publish=lambda *_:pytest.fail('Invalid recovery cannot publish'))
    assert json.loads((case['recover_raw']/'manifest.json').read_text())['status']=='incomplete'


def test_recovery_can_reuse_completed_raw_for_new_fit_attempt(failed_raw):
    case=failed_raw
    options=case['recover_kwargs']
    raw=case['recover_raw']
    recovery.resume_completed_raw_audit(raw,case['paths'],case['phase'],**options)
    completed_sha=recovery.sha256_file(raw/'manifest.json')
    options=dict(options,expected_manifest_sha256=completed_sha,
        receipt_output=options['artifact_root'].root/'run/a0-audit-recovery02/payloads')
    result=recovery.resume_completed_raw_audit(raw,case['paths'],case['phase'],**options)
    assert result['prediction_rows']==20
    assert recovery.sha256_file(raw/'manifest.json')==completed_sha
