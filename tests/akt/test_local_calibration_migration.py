"""Kiểm đường join/fit local bằng dữ liệu tổng hợp, không network."""
import json
from pathlib import Path
import pytest
from test_cloud_calibration_numeric_join import numeric_case,cloud_case,case
from scripts.akt import local_calibration_migration as local
from scripts.akt.local_response_calibration import LocalCalibrationBudget
from knowledge_tracing.akt import research_junyi_calibration as producer
from knowledge_tracing.akt import cloud_calibration_numeric_join as joined


def test_relocation_preserves_nonpaths_and_rejects_traversal(tmp_path):
    value={'path':local.LINUX_VOLUME+'/run/part.json','sha256':'f'*64,'nested':[local.LINUX_VOLUME+'/x']}
    result=local.relocate(value,tmp_path)
    assert result['path']==str(tmp_path/'run/part.json') and result['sha256']==value['sha256']
    assert value['path'].startswith(local.LINUX_VOLUME)
    with pytest.raises(ValueError):
        local.relocate(local.LINUX_VOLUME+'/../secret',tmp_path)


@pytest.mark.parametrize('variant',['A2','A3'])
def test_join_stops_before_old_fit_and_spool_matches_v1(cloud_case,variant,monkeypatch):
    value=cloud_case
    arguments=numeric_case(value,variant)
    def forbidden(*args,**kwargs):
        raise AssertionError('old materializing fit must not run')
    monkeypatch.setattr(joined,'fit_volume_calibration',forbidden)
    result=local.join_raw_only(value['paths'],value['phase'],value['encoding'],**arguments)
    raw=Path(result['raw'])
    manifest=json.loads((raw/'manifest.json').read_text())
    assert manifest['status']=='complete' and manifest['prediction_rows']==20
    shards={row['path']:local.sha(raw/row['path']) for row in manifest['shards']}
    actual=local.fit_raw_spooled(raw,value['paths'],value['phase'],binding=arguments['binding'],
        population=value['population'],source_pins=value['pins'],expected_manifest_sha256=local.sha(raw/'manifest.json'),
        shard_sha256=shards,max_learner_events=10,output=value['output']/'local-fit',budget=LocalCalibrationBudget(max_targets=20))
    expected=producer.fit_response_temperature_from_raw_export(raw,value['paths'],value['phase'],
        binding=arguments['binding'],population=value['population'],source_pins=value['pins'],
        expected_population_identity=value['population']['identity'],expected_manifest_sha256=local.sha(raw/'manifest.json'),
        shard_sha256=shards,max_targets=20,max_learner_events=10,output=value['output']/'baseline-fit')
    assert actual.to_payload()==expected.to_payload()


@pytest.mark.parametrize('writer_status',['COLAB_CPU_WRITER_STOPPED','LOCAL_CPU_WRITER_STOPPED'])
def test_partial_restore_requires_closed_writer_and_immutable_inventory(tmp_path,writer_status):
    source=tmp_path/'snapshot';source.mkdir()
    identity={'phase':'junyi_response_calibration'}
    manifest={'identity':identity,'status':'incomplete','shards':[{'path':'part-0.parquet'}]}
    (source/'manifest.json').write_text(json.dumps(manifest))
    (source/'part-0.parquet').write_bytes(b'original shard')
    marker=tmp_path/'STOP.json'
    stopped_field='remote_process_absent' if writer_status.startswith('COLAB') else 'local_process_absent'
    marker.write_text(json.dumps(dict(status=writer_status,**{stopped_field:True},raw_manifest_sha256=local.sha(source/'manifest.json'))))
    snapshot=dict(path=str(source),manifest_sha256=local.sha(source/'manifest.json'),
        files={p.name:dict(bytes=p.stat().st_size,sha256=local.sha(p)) for p in source.iterdir()},
        writer_stop_receipt=dict(path=str(marker),sha256=local.sha(marker)))
    local._restore_partial(snapshot,tmp_path/'restored',identity)
    assert (tmp_path/'restored/part-0.parquet').read_bytes()==b'original shard'
    (source/'part-0.parquet').write_bytes(b'changed')
    with pytest.raises(ValueError,match='member changed'):
        local._restore_partial(snapshot,tmp_path/'bad',identity)


def test_artifact_mount_declaration_is_scoped(tmp_path):
    previous=producer.CLOUD_CALIBRATION_ARTIFACT_ROOT
    with local.local_artifact_root(tmp_path) as root:
        assert root.validate_output(tmp_path/'new')==tmp_path/'new'
        with pytest.raises(ValueError):
            root.validate_output(tmp_path.parent/'outside')
    assert producer.CLOUD_CALIBRATION_ARTIFACT_ROOT==previous


def test_prediction_json_retry_only_transient_windows_errors(monkeypatch,tmp_path):
    from knowledge_tracing.akt import prediction
    calls=[]
    error=PermissionError('transient sharing denial');error.winerror=5
    original=prediction._write_json_atomic
    def flaky(path,payload):
        calls.append(path)
        if len(calls)<3: raise error
        return original(path,payload)
    monkeypatch.setattr(prediction,'_write_json_atomic',flaky)
    monkeypatch.setattr(local.time,'sleep',lambda seconds:None)
    with local.prediction_json_retry():
        prediction._write_json_atomic(tmp_path/'state.json',{'value':1})
    assert len(calls)==3 and prediction._write_json_atomic is flaky
    assert json.loads((tmp_path/'state.json').read_text())=={'value':1}


@pytest.mark.parametrize('winerror',[None,5])
def test_prediction_json_retry_is_bounded_and_preserves_failure(monkeypatch,tmp_path,winerror):
    from knowledge_tracing.akt import prediction
    calls=[]
    error=PermissionError('persistent denial')
    if winerror is not None:error.winerror=winerror
    def denied(*args):
        calls.append(1);raise error
    monkeypatch.setattr(prediction,'_write_json_atomic',denied)
    monkeypatch.setattr(local.time,'sleep',lambda seconds:None)
    with local.prediction_json_retry(),pytest.raises(PermissionError) as caught:
        prediction._write_json_atomic(tmp_path/'state.json',{})
    assert caught.value is error and len(calls)==(1 if winerror is None else 5)


@pytest.mark.skipif(__import__('os').name!='nt',reason='Windows reader sharing semantics')
def test_real_windows_reader_release_allows_atomic_retry(tmp_path):
    import threading
    from knowledge_tracing.akt import prediction
    path=tmp_path/'manifest.json';path.write_text('{}')
    reader=path.open('r')
    release=threading.Timer(0.08,reader.close)
    release.start()
    try:
        with local.prediction_json_retry():
            prediction._write_json_atomic(path,{'next':1})
        assert json.loads(path.read_text())=={'next':1}
    finally:
        release.join(timeout=2)
        reader.close()


def test_resume_partial_reuses_completed_shard_and_adds_remaining_learner(cloud_case,tmp_path,monkeypatch):
    value=cloud_case
    arguments=numeric_case(value,'A2')
    monkeypatch.setattr(joined,'fit_volume_calibration',lambda *a,**k:pytest.fail('old fit forbidden'))
    full=local.join_raw_only(value['paths'],value['phase'],value['encoding'],**arguments)
    original=Path(full['raw'])
    manifest=json.loads((original/'manifest.json').read_text())
    first=manifest['shards'][0]
    source=tmp_path/'stopped-partial';source.mkdir()
    import shutil
    shutil.copyfile(original/first['path'],source/first['path'])
    partial=dict(schema_version=1,status='incomplete',identity=manifest['identity'],
        shards=[first],completed_users=[first['user_id']],prediction_rows=first['rows'])
    (source/'manifest.json').write_text(json.dumps(partial))
    marker=tmp_path/'STOP.json'
    marker.write_text(json.dumps(dict(status='COLAB_CPU_WRITER_STOPPED',remote_process_absent=True,raw_manifest_sha256=local.sha(source/'manifest.json'))))
    snapshot=dict(path=str(source),manifest_sha256=local.sha(source/'manifest.json'),
        writer_stop_receipt=dict(path=str(marker),sha256=local.sha(marker)),
        files={p.name:dict(bytes=p.stat().st_size,sha256=local.sha(p)) for p in source.iterdir()})
    before={p.name:local.sha(p) for p in source.iterdir()}
    arguments.update(raw_tranche_id='raw-resume',fit_tranche_id='fit-resume')
    resumed=local.join_raw_only(value['paths'],value['phase'],value['encoding'],partial_snapshot=snapshot,**arguments)
    destination=Path(resumed['raw'])
    actual=json.loads((destination/'manifest.json').read_text())
    assert actual['status']=='complete' and actual['prediction_rows']==20 and len(actual['completed_users'])==2
    assert local.sha(destination/first['path'])==before[first['path']]
    assert before=={p.name:local.sha(p) for p in source.iterdir()}
