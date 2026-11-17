"""CPU numeric outer→Parquet compact raw/calibrated, không nạp weights/Torch."""
import argparse
from dataclasses import asdict
import hashlib
from itertools import zip_longest
import json
from pathlib import Path
import sys
from types import SimpleNamespace


def need(value,message):
    if not value:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def pinned(path,expected):
    need(sha(path)==expected,'pinned outer input changed')
    return json.loads(Path(path).read_text(encoding='utf-8'))


def export_outer_numeric(paths,view,encoding,*,binding,calibration,calibration_data_sha256,
        compatibility,cache_receipt,cache_sha256,gpu_receipt,gpu_sha256,source_pins,
        expected_source_sha256,output,max_learner_events,path_map=None,rows_per_shard=32768):
    """Đủ target/role/OOV/source checks mới ghi COMPLETE, đầu vào giữ nguyên."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    from knowledge_tracing.akt.research_junyi_calibration import inference_source_identity,_source_pins
    from knowledge_tracing.akt.research_junyi_data import iter_junyi_phase_learners
    from knowledge_tracing.akt.research_junyi_numeric_predictions import NumericBinding,NumericShard,iter_numeric_prediction_records
    from knowledge_tracing.akt.research_junyi_window_cache import window_cache_key
    from knowledge_tracing.akt.research_junyi_graph_cache import _digest,FORMAT
    from knowledge_tracing.akt.prediction_batch import prepare_prediction_windows
    from knowledge_tracing.akt.evaluation import iter_calibrated_predictions
    from knowledge_tracing.akt.types import PredictionRecord
    if __package__:
        from . import free_outer_evaluation as outer
    else:
        import free_outer_evaluation as outer
    need(type(rows_per_shard) is int and 0<rows_per_shard<=32768,'bounded compact outer rows required')
    need(view.scope=='outer_evaluation' and view.full_role_coverage and view.allowed_folds==(4,), 'full independent outer phase required')
    view.assert_integrity();encoding.assert_for(view)
    need(encoding.fit_view.scope=='refit_union90' and encoding.fit_view.full_role_coverage,'frozen refit90 encoding required')
    need(inference_source_identity()==expected_source_sha256==binding.model_source_sha256,'outer frozen source mismatch')
    need(binding.vocabulary_sha256==encoding.identity and binding.split_sha256==view.roles.identity,'outer binding encoding/roles mismatch')
    _source_pins(paths,source_pins)
    source=json.loads(Path(paths.canonical_manifest).read_text(encoding='utf-8'))
    need(source.get('status')=='FULL_OUTER_SOURCE_PREPARED' and source.get('purpose')=='JUNYI_REFIT90_OUTER_EVALUATION_SOURCE'
         and source.get('phase_identity')==view.identity and source.get('roles_identity')==view.roles.identity
         and source.get('encoding_identity')==encoding.identity and source['counts']['learners']==len(view.users)
         and source.get('holdout_events_included') is False,
         'outer-only source metadata required')
    for name in ('canonical','assignments'):
        path=getattr(paths,name);pin=source['outputs'][path.name]
        need(path.stat().st_size==pin['bytes'] and sha(path)==pin['sha256'],'outer source data changed')
    need(binding.domain_sha256==sha(paths.canonical) and binding.domain_sha256!=calibration_data_sha256,'separate outer/calibration domains required')
    fitted,current=asdict(calibration.binding),asdict(binding)
    need(fitted.pop('domain_sha256')==calibration_data_sha256,'calibrator domain mismatch')
    current.pop('domain_sha256')
    provenance=None
    if compatibility is not None:
        provenance=outer.validate_compatibility(compatibility,checkpoint_sha256=binding.checkpoint_sha256,
            calibration_identity=calibration.identity,calibrated_source=fitted.pop('model_source_sha256'),
            current_source=current.pop('model_source_sha256'))
    need(fitted==current,'calibrator binding mismatch')
    calibrated_probe=iter_calibrated_predictions(iter(()),calibration=calibration,binding=calibration.binding)
    list(calibrated_probe)  # public admission trước khi tạo bất kỳ output nào
    cache=pinned(cache_receipt,cache_sha256);gpu=pinned(gpu_receipt,gpu_sha256)
    resolve=lambda value:Path((path_map or {}).get(str(value),str(value)))
    window=cache['windows']
    window_path=resolve(str(window['path']).rstrip('/\\')+'/manifest.json')
    admission_path=resolve(window['admission_path'])
    manifest=pinned(window_path,window['manifest_sha256']);admission=pinned(admission_path,window['admission_sha256'])
    expected_key=window_cache_key(view,encoding,binding.domain_sha256,expected_target_rows=source['counts']['targets'])
    summary=window['summary']
    need(cache['status']=='JUNYI_OUTER_CPU_CACHES_COMPLETE' and cache['phase']=='outer_evaluation'
         and cache['phase_identity']==view.identity and cache['roles_identity']==view.roles.identity
         and cache['encoding_identity']==encoding.identity and cache['source_pins']==source_pins
         and cache['source_data_sha256']==binding.domain_sha256 and cache['dataset_sha256']==sha(paths.canonical_manifest),
         'outer cache binding mismatch')
    need(manifest['status']=='COMPLETE' and manifest['key']==expected_key and manifest['summary']==summary
         and admission['kind']=='JUNYI_CPU_WINDOW_ADMISSION_V1' and admission['key']==expected_key
         and admission['manifest_sha256']==window['manifest_sha256'] and admission['summary']==summary
         and admission['shards']==manifest['shards'] and admission['strict_records_verified']==summary['records'],
         'outer window admission mismatch')
    numeric=NumericBinding(**gpu['binding']);numeric.validate()
    need(binding.model_id==numeric.variant+'_JUNYI_REFIT' and numeric.checkpoint_id==numeric.checkpoint_sha256==binding.checkpoint_sha256
         and numeric.phase_sha256==view.identity and numeric.encoding_sha256==encoding.identity
         and numeric.source_sha256==expected_source_sha256 and numeric.window_manifest_sha256==window['manifest_sha256'],
         'outer numeric checkpoint/phase/source mismatch')
    graph=None if numeric.variant=='A0' else cache['graphs'][numeric.variant]
    graph_identity=None if graph is None else _digest((FORMAT,graph['sha256'],json.dumps(graph['binding'],sort_keys=True)))
    counts=gpu['counts'];total=source['counts']['targets'];oov=source['counts']['oov_targets']
    need(gpu['kind']=='JUNYI_CACHED_NUMERIC_INFERENCE_V1' and gpu['status']=='COMPLETE'
         and gpu['roles_sha256']==view.roles.identity and gpu['source_data_sha256']==binding.domain_sha256
         and gpu['dataset_sha256']==cache['dataset_sha256'] and gpu['window_admission_sha256']==window['admission_sha256']
         and gpu['graph_cache_identity']==graph_identity and counts['targets']==total
         and counts['fitted_targets']==total-oov and counts['oov_targets']==oov
         and counts['records']==summary['records'] and counts['windows']==summary['windows']
         and summary['target_rows']==total and summary['unseen_targets']==oov,
         'complete GPU outer snapshot/counts mismatch')
    shards=tuple(NumericShard(resolve(row['manifest_path']),row['manifest_sha256']) for row in gpu['shards'])
    adapter=SimpleNamespace(config=SimpleNamespace(context=100,target_block=100,batch_size=128),
        encoding=encoding.native,checkpoint_id=binding.checkpoint_sha256)
    factory=lambda:outer._checked_learners(lambda:iter_junyi_phase_learners(paths,view),view,max_learner_events)
    records=iter_numeric_prediction_records(adapter,prepare_prediction_windows(adapter,factory()),shards,
        binding=numeric,expected_records=total,expected_windows=counts['windows'],expected_targets=total-oov)
    expected=(event for learner in factory() for event in learner.events)
    output=Path(output).absolute()
    need(output.resolve()==output and not output.exists() and not any(p.is_symlink() or getattr(p,'is_junction',lambda:False)() for p in output.parents),
         'new physical outer output required')
    output.mkdir(parents=True)
    (output/'config.json').write_text(json.dumps(dict(binding=asdict(binding),calibration=calibration.to_payload(),
        source_pins=source_pins,cache_receipt=str(cache_receipt),cache_sha256=cache_sha256,
        gpu_receipt=str(gpu_receipt),gpu_sha256=gpu_sha256,source_compatibility=provenance,
        path_map=path_map or {},max_learner_events=max_learner_events,rows_per_shard=rows_per_shard),indent=2)+'\n',encoding='utf-8')
    schema=pa.schema([(name,pa.float64() if name in ('prediction','raw_prediction','calibrated_prediction') else
        pa.string() if name in ('user_id','exercise','prediction_kind','window_id','checkpoint_id') else
        pa.bool_() if name in ('is_fallback','context_reset') else pa.int64())
        for name in (*PredictionRecord.__dataclass_fields__,'raw_prediction','calibrated_prediction')])
    buffer=[];files=[];digest=hashlib.sha256();seen=known=unseen=0
    def flush():
        if not buffer:
            return
        name=f'part-{len(files):05d}.parquet';path=output/name
        pq.write_table(pa.Table.from_pylist(buffer,schema=schema),path,compression='zstd',row_group_size=rows_per_shard)
        files.append(dict(path=name,rows=len(buffer),bytes=path.stat().st_size,sha256=sha(path)))
        buffer.clear()
    current_row={}
    def checked_records():
        for record,event in zip_longest(records,expected):
            need(record is not None and event is not None and outer._key(record)==outer._key(event),'outer source key/label/order mismatch')
            supported=event.exercise in encoding.native.train_support_students
            need((supported and record.prediction is not None and record.prediction_kind=='fitted')
                 or (not supported and record.prediction is None and record.prediction_kind=='unseen' and record.train_support_students==0),
                 'outer fitted/OOV mismatch')
            current_row.update(record=record,supported=supported)
            yield record
    try:
        calibrated=iter_calibrated_predictions(checked_records(),calibration=calibration,binding=calibration.binding)
        for adjusted in calibrated:
            record=current_row['record'];supported=current_row['supported']
            row=asdict(record);row.update(raw_prediction=record.prediction,calibrated_prediction=adjusted.prediction)
            buffer.append(row);seen+=1;known+=int(supported);unseen+=int(not supported)
            digest.update(json.dumps(outer._key(record),separators=(',',':')).encode()+b'\n')
            if len(buffer)==rows_per_shard:
                flush()
        flush()
        need((seen,known,unseen)==(total,total-oov,oov),'outer final target coverage mismatch')
        _source_pins(paths,source_pins)
        need(sha(paths.canonical)==binding.domain_sha256 and sha(gpu_receipt)==gpu_sha256 and sha(cache_receipt)==cache_sha256,
             'outer inputs changed during export')
        need(sha(paths.assignments)==source['outputs'][paths.assignments.name]['sha256'],'outer assignments changed during export')
        receipt=dict(status='COMPLETE_OUTER_NUMERIC_CPU_EXPORT',phase='outer_evaluation',binding=asdict(binding),
            calibration_identity=calibration.identity,calibration_binding=asdict(calibration.binding),source_compatibility=provenance,
            targets=seen,fitted_targets=known,oov_targets=unseen,learners=len(view.users),source_keys_sha256=digest.hexdigest(),
            source_pins=source_pins,cache_sha256=cache_sha256,gpu_receipt_sha256=gpu_sha256,
            rows_per_shard=rows_per_shard,files=files,helper_sha256=sha(__file__),prediction_column='raw',
            raw_column='raw_prediction',calibrated_column='calibrated_prediction',labels_used_for_fitting=False,
            config_sha256=sha(output/'config.json'))
        (output/'COMPLETE.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
        return receipt
    finally:
        records.close()
        expected.close()


def score_export(output,*,expected_complete_sha256):
    """Chỉ materialize3cột numeric, reuse vector metrics GAM/AKT hiện hữu."""
    import pyarrow.parquet as pq
    from knowledge_tracing.gam_kt.evaluation import _metrics
    output=Path(output)
    receipt=pinned(output/'COMPLETE.json',expected_complete_sha256)
    need(receipt['status']=='COMPLETE_OUTER_NUMERIC_CPU_EXPORT','complete outer export required for metrics')
    for entry in receipt['files']:
        need(Path(entry['path']).name==entry['path'] and sha(output/entry['path'])==entry['sha256'],'outer metric shard pin changed')
    table=pq.read_table([str(output/entry['path']) for entry in receipt['files']],
        columns=['correct','raw_prediction','calibrated_prediction'])
    frame=table.to_pandas();del table
    need(len(frame)==receipt['targets'] and int(frame.raw_prediction.isna().sum())==receipt['oov_targets']
         and frame.raw_prediction.isna().equals(frame.calibrated_prediction.isna()),'outer metric coverage mismatch')
    supported=frame[frame.raw_prediction.notna()]
    result=dict(status='OUTER_NATIVE_SHARED_METRICS',total_targets=len(frame),predicted_targets=len(supported),
        oov_targets=receipt['oov_targets'],ece_bins=15,accuracy_threshold=.5,calibration_fitted_on_outer=False,
        raw=_metrics(supported[['correct','raw_prediction']].rename(columns={'raw_prediction':'prediction'})),
        calibrated=_metrics(supported[['correct','calibrated_prediction']].rename(columns={'calibrated_prediction':'prediction'})),
        complete_sha256=expected_complete_sha256,paired_baseline_comparison='PENDING_SEPARATE_MATCHED_ROW_JOIN',
        confidence_intervals='PENDING_PAIRED_LEARNER_ANALYSIS')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--request-sha256',required=True)
    args=parser.parse_args()
    repository=Path(__file__).resolve().parents[2]
    python=repository/'.venv'/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
    need(Path(sys.executable).resolve()==python.resolve(),'repository venv Python required')
    request=pinned(args.request,args.request_sha256)
    source=Path(request['source_root']).absolute()
    need(source.resolve()==source and (source/'src/knowledge_tracing').is_dir()
         and source.is_relative_to(repository/'artifacts/akt/local-calibration'),'physical frozen source required')
    output=Path(request['output']).absolute()
    need(output.is_relative_to(repository/'experiments/akt/results') or output.is_relative_to(repository/'artifacts/akt/local-calibration'),
         'owned outer output directory required')
    need(not any(name=='knowledge_tracing' or name.startswith('knowledge_tracing.') for name in sys.modules),
         'choose frozen source before KT import')
    sys.path.insert(0,str(source/'src'))
    sys.path.insert(1,str(repository/'scripts/akt'))
    import free_outer_evaluation as outer
    from knowledge_tracing.akt.config import DataPaths,PROJECT_ROOT
    from knowledge_tracing.akt.research_junyi_inference import inspect_cpu_refit_export,JunyiCPUInferenceBudget,_identity
    from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView
    from knowledge_tracing.response_calibration import PredictionBinding,TemperatureCalibration
    need(PROJECT_ROOT==source and request['source_identity']==outer.NEW_SOURCE,'exact approved outer guard source required')
    variant=request['variant'];index=request['export_index']
    need(variant in ('A0','A1','A2','A3'),'explicit outer variant required')
    assets=inspect_cpu_refit_export(Path(index['path']).parent,expected_index_sha256=index['sha256'],
        output=source/'experiments/akt/results'/('outer-cpu-'+variant.lower()),run_id='outer-cpu-'+variant.lower(),
        budget=JunyiCPUInferenceBudget(**request['inspection_budget']))
    need(assets['index']['model']==variant+'_JUNYI_REFIT','requested outer variant/export mismatch')
    encoding=assets['encoding'];roles=encoding.fit_view.roles
    view=JunyiPhaseView(roles,'outer_evaluation',roles.outer_validation_users,roles.identity)
    paths=DataPaths(**{name:Path(path) for name,path in request['data_paths'].items()})
    calibration_pin=request['calibration'];payload=pinned(calibration_pin['path'],calibration_pin['sha256'])
    calibration_binding=PredictionBinding(**payload['binding'])
    calibration=TemperatureCalibration.from_payload(payload,binding=calibration_binding)
    compatibility_pin=request['compatibility']
    compatibility=pinned(compatibility_pin['path'],compatibility_pin['sha256'])
    binding=PredictionBinding(assets['index']['model'],assets['index']['checkpoint_sha256'],encoding.identity,roles.identity,
        _identity(dict(domain='junyi_exercises',values=encoding.native.vocabulary.values)),
        _identity(dict(domain='junyi_logged_response',reference_bank='not_applicable')),request['source_identity'],sha(paths.canonical))
    result=export_outer_numeric(paths,view,encoding,binding=binding,calibration=calibration,
        calibration_data_sha256=request['calibration_data_sha256'],compatibility=compatibility,
        cache_receipt=request['cache_receipt']['path'],cache_sha256=request['cache_receipt']['sha256'],
        gpu_receipt=request['gpu_receipt']['path'],gpu_sha256=request['gpu_receipt']['sha256'],source_pins=request['source_pins'],
        expected_source_sha256=request['source_identity'],output=Path(request['output']),
        max_learner_events=request['max_learner_events'],path_map=request.get('path_map'))
    if request.get('metrics',False):
        summary=score_export(request['output'],expected_complete_sha256=sha(Path(request['output'])/'COMPLETE.json'))
        (Path(request['output'])/'METRICS.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    main()
