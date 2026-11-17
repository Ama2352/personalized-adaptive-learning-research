"""Kiểm compact raw là đổi layout, giữ stream và kết quả V1."""
import json
from pathlib import Path
import pytest
from test_cloud_calibration_fit import cloud_case,case
from knowledge_tracing.akt.research_junyi_calibration import iter_pinned_prediction_export
from scripts.akt.local_calibration_compact import compact_raw_export
from scripts.akt.local_calibration_migration import fit_raw_spooled,sha
from scripts.akt.local_response_calibration import LocalCalibrationBudget


def arguments(raw):
    manifest=json.loads((raw/'manifest.json').read_text())
    return dict(expected_manifest_sha256=sha(raw/'manifest.json'),
        shard_sha256={row['path']:sha(raw/row['path']) for row in manifest['shards']})


@pytest.mark.parametrize('shard_rows',[32768,7])
def test_public_record_stream_and_full_fit_payload_exact(cloud_case,shard_rows):
    value=cloud_case;raw=value['raw']
    before=arguments(raw)
    destination=value['output']/'compact'
    result=compact_raw_export(raw,destination,**before,min_free_bytes=1,max_rows_per_shard=shard_rows)
    after=arguments(destination)
    left=list(iter_pinned_prediction_export(raw,**before))
    right=list(iter_pinned_prediction_export(destination,**after))
    assert left==right and len(left)==20
    assert len({row.user_id for row in right})==2
    assert sum(row.prediction is None for row in right)==2
    assert arguments(raw)==before
    results=[]
    for index,(directory,pins) in enumerate(((raw,before),(destination,after))):
        results.append(fit_raw_spooled(directory,value['paths'],value['phase'],binding=value['binding'],
            population=value['population'],source_pins=value['pins'],max_learner_events=10,
            output=value['output']/('fit'+str(index)),budget=LocalCalibrationBudget(max_targets=20),**pins))
    assert results[0].to_payload()==results[1].to_payload()
    assert result['rows']==20 and result['original_shards']==2 and result['compacted_shards']==(1 if shard_rows==32768 else 3)
    assert all(row['rows']<=shard_rows for row in json.loads((destination/'manifest.json').read_text())['shards'])


@pytest.mark.parametrize('change',['incomplete','manifest','shard','existing','diskcap'])
def test_compact_rejects_invalid_sources_and_preserves_original(cloud_case,change):
    value=cloud_case;raw=value['raw'];pins=arguments(raw)
    output=value['output']/'compact'
    if change=='incomplete':
        manifest=json.loads((raw/'manifest.json').read_text());manifest['status']='incomplete'
        (raw/'manifest.json').write_text(json.dumps(manifest));pins=arguments(raw)
    if change=='manifest': pins['expected_manifest_sha256']='0'*64
    if change=='shard': pins['shard_sha256'][next(iter(pins['shard_sha256']))]='0'*64
    if change=='existing': output.mkdir()
    options=dict(min_free_bytes=1)
    if change=='diskcap': options['max_source_bytes']=1
    original={p.name:sha(p) for p in raw.glob('*.parquet')}
    with pytest.raises(ValueError):
        compact_raw_export(raw,output,**pins,**options)
    assert original=={p.name:sha(p) for p in raw.glob('*.parquet')}
    assert not (output/'COMPLETE.json').exists()


def test_2048_rows_multiple_batches_and_bounded_shards(cloud_case):
    from dataclasses import asdict,replace
    import pyarrow as pa
    import pyarrow.parquet as pq
    value=cloud_case
    templates=list(iter_pinned_prediction_export(value['raw'],**arguments(value['raw'])))
    fitted=next(r for r in templates if r.prediction is not None)
    unseen=next(r for r in templates if r.prediction is None)
    source=value['output']/'synthetic2048';source.mkdir()
    rows=[replace(unseen if i%17==0 else fitted,user_id='learner-'+str(i//1024),
        source_row=i+1,time_done=i) for i in range(2048)]
    entries=[]
    for index in range(2):
        filename=f'part-{index:05d}.parquet'
        pq.write_table(pa.Table.from_pylist([asdict(r) for r in rows[index*1024:(index+1)*1024]]),source/filename)
        entries.append(dict(path=filename,rows=1024,user_id='learner-'+str(index)))
    (source/'manifest.json').write_text(json.dumps(dict(status='complete',identity={'synthetic':True},
        prediction_rows=2048,shards=entries,completed_users=['learner-0','learner-1'])))
    before=arguments(source)
    output=value['output']/'compact2048'
    receipt=compact_raw_export(source,output,**before,min_free_bytes=1,max_rows_per_shard=512)
    assert receipt['compacted_shards']==4
    assert list(iter_pinned_prediction_export(source,**before))==list(iter_pinned_prediction_export(output,**arguments(output)))


@pytest.mark.parametrize('failure',[None,'missing_complete','changed_pin'])
def test_compact_fit_requires_completed_provenance(cloud_case,failure):
    from scripts.akt.local_calibration_migration import raw_storage_lineage
    value=cloud_case;raw=value['raw'];output=value['output']/'lineage-compact'
    compact_raw_export(raw,output,**arguments(raw),min_free_bytes=1)
    manifest=json.loads((output/'manifest.json').read_text())
    pins=arguments(output)['shard_sha256']
    complete=output/'COMPLETE.json'
    if failure=='missing_complete':complete.rename(output/'INCOMPLETE_EVIDENCE.json')
    if failure=='changed_pin':
        receipt=json.loads(complete.read_text());receipt['compact_manifest_sha256']='0'*64
        complete.write_text(json.dumps(receipt))
    if failure is None:
        lineage=raw_storage_lineage(output,manifest,pins)
        assert lineage['manifest']==manifest and lineage['compaction_receipt']['rows']==20
    else:
        with pytest.raises((ValueError,FileNotFoundError)):
            raw_storage_lineage(output,manifest,pins)
