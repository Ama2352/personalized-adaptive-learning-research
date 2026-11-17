"""Nối raw và fit V1 giới hạn RAM trên local, source KT frozen giữ nguyên."""
import argparse
from contextlib import contextmanager
from dataclasses import asdict
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sys
import time

LINUX_VOLUME='/__modal/volumes/vo-dv1975utRQbmagCjA0brSe'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def need(value,reason):
    if not value:
        raise ValueError(reason)


def relocate(value,root):
    """Chỉ đổi prefix Volume tuyệt đối, không sửa bytes của artifact nguồn."""
    if isinstance(value,dict):
        return {key:relocate(item,root) for key,item in value.items()}
    if isinstance(value,list):
        return [relocate(item,root) for item in value]
    if isinstance(value,str) and (value==LINUX_VOLUME or value.startswith(LINUX_VOLUME+'/')):
        relative=PurePosixPath(value).relative_to(LINUX_VOLUME)
        need('..' not in relative.parts and '\\' not in value,'canonical Volume relocation required')
        return str(Path(root).joinpath(*relative.parts))
    return value


@contextmanager
def local_artifact_root(root):
    """Đổi duy nhất mount declaration trong process, giữ các guard path gốc."""
    from knowledge_tracing.akt import research_junyi_calibration as producer
    root=Path(root).absolute()
    need(root.is_dir() and root.resolve()==root,'physical local artifact root required')
    previous=producer.CLOUD_CALIBRATION_ARTIFACT_ROOT
    producer.CLOUD_CALIBRATION_ARTIFACT_ROOT=root
    try:
        yield producer.CalibrationFitArtifactRoot(root)
    finally:
        producer.CLOUD_CALIBRATION_ARTIFACT_ROOT=previous


class _RawReady(Exception):
    def __init__(self,publication):
        self.publication=publication


@contextmanager
def prediction_json_retry():
    """Giữ serializer gốc, dùng lịch retry Windows của runner đã có."""
    from knowledge_tracing.akt import prediction
    original=prediction._write_json_atomic
    def write(path,payload):
        for delay in (0.05,0.1,0.2,0.4,None):
            try:
                return original(path,payload)
            except PermissionError as error:
                if getattr(error,'winerror',None) not in (5,32,33) or delay is None:
                    raise
                print('WINDOWS_JSON_RETRY',str(path),getattr(error,'winerror',None),flush=True)
                time.sleep(delay)
    prediction._write_json_atomic=write
    try:
        yield
    finally:
        prediction._write_json_atomic=original


def _restore_partial(snapshot,destination,identity):
    """Sao chép snapshot đã đóng sang output mới, không sửa bản khôi phục."""
    source=Path(snapshot['path']).absolute()
    need(source.is_dir() and source.resolve()==source,'physical partial snapshot required')
    marker=snapshot['writer_stop_receipt']
    need(sha(marker['path'])==marker['sha256'],'writer-stop receipt changed')
    closed=json.loads(Path(marker['path']).read_text(encoding='utf-8'))
    writer_stopped=(closed.get('status')=='COLAB_CPU_WRITER_STOPPED' and closed.get('remote_process_absent') is True
        or closed.get('status')=='LOCAL_CPU_WRITER_STOPPED' and closed.get('local_process_absent') is True)
    need(writer_stopped
         and closed.get('raw_manifest_sha256')==snapshot['manifest_sha256'],
         'old partial writer must be stopped for this snapshot')
    manifest_path=source/'manifest.json'
    need(sha(manifest_path)==snapshot['manifest_sha256'],'partial manifest changed')
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    need(manifest['identity']==identity and manifest['status']=='incomplete','partial frozen prediction identity mismatch')
    names={'manifest.json',*(entry['path'] for entry in manifest['shards'])}
    need(names==set(snapshot['files']) and all(Path(name).name==name for name in names),'partial snapshot inventory coverage changed')
    need({p.name for p in source.glob('part-*.parquet')}==names-{'manifest.json'},'unlisted partial Parquet preserved for review')
    for name,pin in snapshot['files'].items():
        path=source/name
        need(not path.is_symlink() and path.resolve()==path and path.stat().st_size==pin['bytes'] and sha(path)==pin['sha256'],
             'partial snapshot member changed')
    destination.mkdir()
    (destination/'.pending').mkdir()
    for name in sorted(names):
        shutil.copyfile(source/name,destination/name)
        need(sha(destination/name)==snapshot['files'][name]['sha256'],'partial copy changed')
    return manifest


def join_raw_only(paths,view,encoding,*,partial_snapshot=None,publish=None,**arguments):
    """Re-use join public; callback kết thúc sau raw, trước fitter cũ."""
    from knowledge_tracing.akt import prediction
    from knowledge_tracing.akt.cloud_calibration_numeric_join import join_numeric_calibration_snapshot
    from calibration_audit_transaction import transactional_expected_insert
    raw=Path(arguments['artifact_root'].root)/arguments['run_id']/arguments['raw_tranche_id']/'payloads/raw'
    prepare=prediction._prepare_output
    identity=dict(phase='junyi_response_calibration',population=arguments['expected_population_identity'],
        checkpoint=arguments['binding'].checkpoint_sha256,inference_source=arguments['binding'].model_source_sha256,
        prediction_batch_size=128)

    def prepare_partial(output,*,artifact_root=None):
        if Path(output).absolute()!=raw or artifact_root is not arguments['artifact_root']:
            raise ValueError('partial resume admits only one declared raw output')
        arguments['artifact_root'].validate_output(raw)
        _restore_partial(partial_snapshot,raw,identity)
        return raw,raw/'manifest.json'

    def raw_ready(publication):
        publication=json.loads(json.dumps(publication))
        receipt=None if publish is None else publish(publication)
        raise _RawReady(dict(publish_request=publication,publish_receipt=receipt,raw=str(raw)))

    if partial_snapshot is not None:
        prediction._prepare_output=prepare_partial
    try:
        with prediction_json_retry(),transactional_expected_insert():
            join_numeric_calibration_snapshot(paths,view,encoding,on_raw_ready=raw_ready,**arguments)
        raise RuntimeError('raw-ready callback was not reached')
    except _RawReady as completed:
        return completed.publication
    finally:
        prediction._prepare_output=prepare


def fit_raw_spooled(raw,paths,view,*,binding,population,source_pins,expected_manifest_sha256,
        shard_sha256,max_learner_events,output,budget):
    """Hai replay độc lập giữ kiểm target/prefix; không tee, không gom row lists."""
    from knowledge_tracing.akt.research_junyi_calibration import (
        iter_pinned_prediction_export,iter_calibration_observations,_source_pins)
    from knowledge_tracing.akt.research_junyi_data import iter_junyi_phase_learners
    from knowledge_tracing.response_calibration import CalibrationPartition
    if __package__:
        from .local_response_calibration import fit_temperature_spooled
    else:
        from local_response_calibration import fit_temperature_spooled
    raw=Path(raw)
    need(sha(raw/'manifest.json')==expected_manifest_sha256,'raw manifest pin changed')
    manifest=json.loads((raw/'manifest.json').read_text(encoding='utf-8'))
    identity=manifest['identity']
    need(manifest['status']=='complete' and view.scope=='calibration_predict' and view.full_role_coverage
         and binding.split_sha256==view.roles.identity and population['source_pins']==source_pins
         and identity['phase']=='junyi_response_calibration' and identity['population']==population['identity']
         and identity['checkpoint']==binding.checkpoint_sha256 and identity['inference_source']==binding.model_source_sha256,
         'frozen calibration raw phase/roles/checkpoint/source mismatch')
    _source_pins(paths,source_pins)
    output=Path(output).absolute()
    need(output.resolve()==output and not output.exists(),'new physical local fit output required')
    output.mkdir(parents=True)
    def observations():
        records=iter_pinned_prediction_export(raw,expected_manifest_sha256=expected_manifest_sha256,shard_sha256=shard_sha256)
        return iter_calibration_observations(records,iter_junyi_phase_learners(paths,view),view=view,
            binding=binding,population=population,max_targets=budget.max_targets,max_learner_events=max_learner_events)
    roles=view.roles
    partition=CalibrationPartition(roles.identity,roles.calibration_users,
        tuple(sorted((*roles.train_users,*roles.selection_users,*roles.outer_validation_users))),None)
    calibration=fit_temperature_spooled((target for _,target,_ in observations()),binding=binding,partition=partition,
        expected_target_keys=(key for _,_,key in observations()),database=output/'targets.sqlite',budget=budget)
    _source_pins(paths,source_pins)
    (output/'temperature.json').write_text(json.dumps(calibration.to_payload(),indent=2)+'\n',encoding='utf-8')
    return calibration


def prepare_context(payload,volume,variant):
    """Kiểm request/cache gốc, ghi metadata dẫn xuất để dùng trên Windows."""
    from knowledge_tracing.akt.config import DataPaths,PROJECT_ROOT
    from knowledge_tracing.akt.research_junyi_calibration import inference_source_identity
    from knowledge_tracing.akt.research_junyi_inference import inspect_cpu_refit_export,JunyiCPUInferenceBudget,_identity
    from knowledge_tracing.akt.research_junyi_numeric_predictions import NumericBinding
    from knowledge_tracing.akt.research_junyi_graph_cache import _digest,FORMAT
    from knowledge_tracing.response_calibration import PredictionBinding
    need(variant in ('A2','A3'),'local calibration variant A2/A3 required')
    original=payload['plan']
    oldrequest=original['requests'][variant]
    need(oldrequest['mode']=='full' and oldrequest['full_cohort_approved'] and oldrequest['variant']==variant,
         'approved full calibration request required')
    need(hashlib.sha256(json.dumps(original['cache']).encode()).hexdigest()==oldrequest['cache_receipt']['sha256'],
         'original cache receipt pin changed')
    need(inference_source_identity()==oldrequest['source_identity'],'frozen Linux source identity changed')
    plan=relocate(original,volume)
    request,cache=plan['requests'][variant],plan['cache']
    for pin in [*request['exports'].values(),*request['data_paths'].values(),request['population']]:
        need(sha(pin['path'])==pin['sha256'],'local relocated input pin changed')
    source=Path(volume)/'calibration-inputs-20261117-01/source'
    need(PROJECT_ROOT==source,'isolated frozen source required before imports')
    index=request['exports'][variant]
    assets=inspect_cpu_refit_export(Path(index['path']).parent,expected_index_sha256=index['sha256'],
        output=source/'experiments/akt/results'/('local-cpu-'+variant.lower()),run_id='local-cpu-'+variant.lower(),
        budget=JunyiCPUInferenceBudget(**request['cpu_budget']))
    paths=DataPaths(**{key:Path(pin['path']) for key,pin in request['data_paths'].items()})
    population=json.loads(Path(request['population']['path']).read_text(encoding='utf-8'))
    need(population==cache['population'],'relocated population/cache mismatch')
    old_gpu=original['gpu'][variant]
    receipt_path=Path(relocate(old_gpu['receipt_path'],volume))
    need(sha(receipt_path)==old_gpu['receipt_sha256'],'original numeric receipt pin changed')
    numeric=relocate(json.loads(receipt_path.read_text(encoding='utf-8')),volume)
    metadata=Path(volume)/'local-migration-metadata'/variant/sha(__file__)[:16]
    metadata.mkdir(parents=True,exist_ok=True)
    derived=metadata/'GPU_RELOCATED.json'
    derived_text=json.dumps(numeric,indent=2)+'\n'
    if derived.exists():
        need(derived.read_text(encoding='utf-8')==derived_text,'existing numeric relocation changed')
    else:
        derived.write_text(derived_text,encoding='utf-8')
    relocation_text=json.dumps(dict(kind='LOCAL_CALIBRATION_PATH_RELOCATION_V1',
        linux_prefix=LINUX_VOLUME,physical_prefix=str(volume),source_identity=request['source_identity'],
        original_gpu_receipt_sha256=old_gpu['receipt_sha256'],relocated_gpu_receipt_sha256=sha(derived),
        original_request_sha256=hashlib.sha256(json.dumps(oldrequest,sort_keys=True).encode()).hexdigest(),
        relocated_request=request,adapter_sha256=sha(__file__)),indent=2)+'\n'
    relocation_file=metadata/'RELOCATION.json'
    if relocation_file.exists():
        need(relocation_file.read_text(encoding='utf-8')==relocation_text,'existing relocation admission changed')
    else:
        relocation_file.write_text(relocation_text,encoding='utf-8')
    binding=PredictionBinding(assets['index']['model'],assets['index']['checkpoint_sha256'],assets['encoding'].identity,
        assets['calibration'].roles.identity,_identity(dict(domain='junyi_exercises',values=assets['encoding'].native.vocabulary.values)),
        _identity(dict(domain='junyi_logged_response',reference_bank='not_applicable')),request['source_identity'],cache['source_data_sha256'])
    graph=cache['graphs'][variant]
    graph_identity=_digest((FORMAT,graph['sha256'],json.dumps(graph['binding'],sort_keys=True)))
    return dict(paths=paths,view=assets['calibration'],encoding=assets['encoding'],binding=binding,population=population,
        request=request,cache=cache,numeric=NumericBinding(**numeric['binding']),receipt_path=derived,graph_identity=graph_identity)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=('join','fit'),required=True)
    parser.add_argument('--volume',type=Path,required=True)
    parser.add_argument('--payload',type=Path,required=True)
    parser.add_argument('--payload-sha256',required=True)
    parser.add_argument('--variant',choices=('A2','A3'),required=True)
    parser.add_argument('--attempt',type=int,default=100)
    parser.add_argument('--partial-snapshot',type=Path)
    parser.add_argument('--raw',type=Path)
    parser.add_argument('--raw-manifest-sha256')
    parser.add_argument('--max-seconds',type=float,default=7200)
    parser.add_argument('--drive-token-file',type=Path)
    args=parser.parse_args()
    repository=Path(__file__).resolve().parents[2]
    expected_python=repository/'.venv'/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
    need(Path(sys.executable).resolve()==expected_python.resolve(),'repository venv Python required')
    volume=args.volume.absolute()
    allowed=repository/'artifacts/akt/local-calibration'
    need(volume.resolve()==volume and volume.is_relative_to(allowed) and volume.is_dir(),'declared local calibration staging required')
    need(shutil.disk_usage(volume).free>=4*1024**3,'local staging requires4GiB free disk')
    need(1<=args.attempt<=999,'bounded local attempt required')
    source=volume/'calibration-inputs-20261117-01/source'
    need((source/'src/knowledge_tracing').is_dir(),'isolated frozen source missing')
    need(not any(name=='knowledge_tracing' or name.startswith('knowledge_tracing.') for name in sys.modules),'frozen source must be selected before KT import')
    sys.path.insert(0,str(source/'src'))
    sys.path.insert(1,str(repository/'scripts/akt'))
    need(sha(args.payload)==args.payload_sha256,'pinned payload required')
    context=prepare_context(json.loads(args.payload.read_text(encoding='utf-8')),volume,args.variant)
    from local_response_calibration import LocalCalibrationBudget
    import free_cpu_calibration as free
    free.VOLUME=volume
    state=repository/'artifacts/akt/private/local-calibration'/volume.name
    state.mkdir(parents=True,exist_ok=True)
    session=None
    if args.drive_token_file:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import AuthorizedSession
        token=args.drive_token_file.resolve()
        need(token.is_relative_to(repository/'artifacts/akt/private'),'private local Drive credential path required')
        session=AuthorizedSession(Credentials.from_authorized_user_file(str(token)))
    variant=args.variant.lower()
    raw_tranche=f'{variant}-raw-freecpu-{variant}-{args.attempt:03d}'
    fit_tranche=f'{variant}-fit-freecpu-{variant}-{args.attempt:03d}'
    with local_artifact_root(volume) as artifact_root:
        if args.phase=='join':
            request=context['request'];cache=context['cache'];win=cache['windows']
            partial=None if args.partial_snapshot is None else json.loads(args.partial_snapshot.read_text(encoding='utf-8'))
            result=join_raw_only(context['paths'],context['view'],context['encoding'],partial_snapshot=partial,
                publish=None if session is None else lambda publication:free.publish(session,publication,state),
                binding=context['binding'],numeric_binding=context['numeric'],gpu_receipt=context['receipt_path'],
                expected_gpu_receipt_sha256=sha(context['receipt_path']),window_manifest=Path(win['path'])/'manifest.json',
                window_admission=Path(win['admission_path']),expected_window_admission_sha256=win['admission_sha256'],
                population=context['population'],expected_population_identity=context['population']['identity'],
                source_pins=request['source_pins'],max_targets=context['population']['targets'],
                max_learner_events=request['cpu_budget']['max_learner_events'],artifact_root=artifact_root,
                run_id=free.RUN,raw_tranche_id=raw_tranche,fit_tranche_id=fit_tranche,
                expected_graph_cache_identity=context['graph_identity'])
        else:
            need(args.raw is not None and args.raw_manifest_sha256 is not None,'fit requires pinned raw input')
            raw=args.raw.absolute()
            need(raw.is_relative_to(volume) and raw.resolve()==raw,'fit raw must remain in declared staging')
            need(sha(raw/'manifest.json')==args.raw_manifest_sha256,'raw manifest changed before fit')
            manifest=json.loads((raw/'manifest.json').read_text(encoding='utf-8'))
            for row in manifest['shards']:
                need(Path(row['path']).name==row['path'],'raw shard basename required')
            shards={row['path']:sha(raw/row['path']) for row in manifest['shards']}
            payloads=volume/free.RUN/fit_tranche/'payloads'
            artifact_root.validate_output(payloads)
            payloads.mkdir(parents=True)
            calibration=fit_raw_spooled(raw,context['paths'],context['view'],binding=context['binding'],
                population=context['population'],source_pins=context['request']['source_pins'],
                expected_manifest_sha256=args.raw_manifest_sha256,shard_sha256=shards,
                max_learner_events=context['request']['cpu_budget']['max_learner_events'],output=payloads/'fit',
                budget=LocalCalibrationBudget(max_targets=context['population']['targets'],max_seconds=args.max_seconds))
            resource=json.loads((payloads/'fit/targets.receipt.json').read_text(encoding='utf-8'))
            metadata=dict(binding=asdict(context['binding']),population=context['population'],
                raw_manifest_sha256=args.raw_manifest_sha256,raw_shard_sha256=shards,
                source_pins=context['request']['source_pins'],calibration_identity=calibration.identity,
                algorithm='original_v1_solver_sqlite_representation',resource=resource)
            for name,value in (('config.json',metadata),('fit/manifest.json',metadata),('resource.json',resource)):
                (payloads/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
            files=['config.json','fit/temperature.json','fit/manifest.json','resource.json']
            inventory={name:dict(bytes=(payloads/name).stat().st_size,sha256=sha(payloads/name)) for name in files}
            (payloads/'COMPLETE.json').write_text(json.dumps(dict(status='LOCAL_SPOOLED_CALIBRATION_COMPLETE',
                files=inventory,calibration_identity=calibration.identity),indent=2)+'\n',encoding='utf-8')
            files.append('COMPLETE.json')
            publication=dict(run_id=free.RUN,tranche_id=fit_tranche,files=files,
                max_total_bytes=sum((payloads/name).stat().st_size for name in files))
            result=dict(publish_request=publication,publish_receipt=None if session is None else free.publish(session,publication,state),
                calibration=calibration.to_payload())
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    main()
