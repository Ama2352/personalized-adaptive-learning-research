"""Producer calibration Junyi có target/prefix provenance và snapshot frozen.

Các API này kiểm hợp đồng dữ liệu, không cấp quyền thực thi hoặc chọn model.
Caller giữ grant, Gate/runtime và kiểm integrity canonical data của từng run.
"""
from dataclasses import asdict, dataclass
from itertools import zip_longest
import hashlib
import json
from pathlib import Path
import zipfile

from knowledge_tracing.response_calibration import (
    CalibrationPartition, CalibrationTarget, PredictionBinding, fit_temperature)
from .comparison_contract import TRAINING_FIELDS
from .prediction import iter_predictions, _validate_record, export_predictions, _write_json_atomic
from .provenance import sha256_file
from .research_junyi_data import JunyiPhaseView, JunyiResearchEncoding, iter_junyi_phase_learners
from .types import LearnerEvents,PredictionRecord


def _need(value, message):
    if not value:
        raise ValueError(message)


def _identity(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def inference_source_identity():
    from .config import PROJECT_ROOT
    paths=tuple(sorted(Path(__file__).parent.glob('*.py')))+tuple(PROJECT_ROOT/name for name in (
        'src/knowledge_tracing/response_calibration.py','src/knowledge_tracing/simulator_bridge.py',
        'src/knowledge_tracing/shared_kt.py','docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md',
        'artifacts/akt/dependencies/upstream/akt.py'))
    return _identity({path.relative_to(PROJECT_ROOT).as_posix():sha256_file(path) for path in paths})


def _native_seal(native):
    """Seal cùng process, bắt thay object hoặc in-place update thông thường."""
    return [[kind,name,id(value),value._version,list(value.shape),str(value.dtype),str(value.device)]
            for kind,items in (('parameter',native.named_parameters()),('buffer',native.named_buffers()))
            for name,value in items]


@dataclass(frozen=True)
class RefitCalibrationPredictor:
    adapter: object
    encoding: JunyiResearchEncoding
    binding: PredictionBinding
    receipt: dict

    def assert_boundary(self):
        self.encoding.assert_for(self.encoding.fit_view)
        _need(not getattr(self.adapter,'_calibration_attach_failed',False),
              'failed checkpoint attachment cannot be reused')
        _need(self.receipt['checkpoint_sha256']==self.binding.checkpoint_sha256
              and getattr(self.adapter,'checkpoint_id',None)==self.binding.checkpoint_sha256,
              'frozen predictor checkpoint binding mismatch')
        _need(self.binding.model_source_sha256==self.receipt['inference_source_sha256']
              ==inference_source_identity(),'inference source drift')
        _need(self.binding.vocabulary_sha256==self.encoding.identity
              and self.binding.split_sha256==self.encoding.fit_view.roles.identity,
              'frozen predictor vocabulary/split mismatch')
        _need(self.adapter.encoding==self.encoding.native
              and json.loads(json.dumps(asdict(self.adapter.config),default=str))==self.receipt['inference_config']
              and getattr(self.adapter,'graph_enabled',None)==self.receipt['graph_enabled'],
              'frozen predictor inference configuration changed')
        _need(getattr(getattr(self.adapter,'condition',None),'identity',None)
              ==self.receipt['training_identity'].get('condition'),
              'frozen predictor graph/confidence condition changed')
        _need(_native_seal(self.adapter.native)==self.receipt['native_state_seal'],
              'frozen predictor parameters/buffers changed')


def attach_refit_export(adapter, encoding, export, *, expected_index_sha256, binding,
                        max_checkpoint_bytes):
    """Tái dùng snapshot loader, chỉ gắn model weights, giữ training identity cũ.

    Caller dựng đúng A0/A1/A2/A3 adapter bằng config/graph/confidence đã ghim.
    Inference source được ghi riêng, không sửa identity bên trong snapshot.
    """
    export=Path(export)
    index_path=export/'MODEL_INDEX.json'
    _need(sha256_file(index_path)==expected_index_sha256,'refit export index changed')
    index=json.loads(index_path.read_text(encoding='utf-8'))
    _need(type(encoding) is JunyiResearchEncoding and encoding.fit_view.scope=='refit_union90'
          and encoding.fit_view.full_role_coverage,'full refit90 encoding required')
    encoding.assert_for(encoding.fit_view)
    _need(type(binding) is PredictionBinding and binding.vocabulary_sha256==encoding.identity
          and binding.split_sha256==encoding.fit_view.roles.identity,'prediction binding encoding/roles mismatch')
    _need(type(max_checkpoint_bytes) is int and max_checkpoint_bytes>0,'checkpoint memory cap required')
    filename=index['checkpoint_file']
    _need('/' not in filename and '\\' not in filename and filename not in ('','.','..'),'checkpoint basename required')
    checkpoint=export/filename
    _need(index['phase']=='refit90' and index['identity']['phase']=='junyi_refit90'
          and checkpoint.stat().st_size==index['checkpoint_bytes']<=max_checkpoint_bytes
          and index['checkpoint_sha256']==binding.checkpoint_sha256==sha256_file(checkpoint),
          'completed refit checkpoint pin mismatch')
    _need(index['identity']['encoding']==encoding.identity,'refit export encoding mismatch')
    support=export/'SUPPORT.zip'
    _need(sha256_file(support)==index['support_sha256'],'refit support archive changed')
    with zipfile.ZipFile(support) as archive:
        info=archive.infolist()
        _need(len({row.filename for row in info})==len(info)
              and sum(row.file_size for row in info)<=32*1024**2,'bounded unique support members required')
        inventory=json.loads(archive.read('INVENTORY.json'))
        _need(set(archive.namelist())==set(inventory)|{'INVENTORY.json'},'support inventory coverage mismatch')
        for name,pin in inventory.items():
            raw=archive.read(name)
            _need(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],
                  'support member pin mismatch')
        load=lambda name:json.loads(archive.read(name))
        training_config=load('inputs/config.json')
        training_identity=load('run-manifest.json')
        complete=load('COMPLETE.json')
        metadata=load('metadata.json')
        roles=load('inputs/roles.json')
    _need(_identity(roles)==encoding.fit_view.roles.identity,'support roles differ from fitted encoding')
    _need(training_identity==index['identity']==metadata['identity']
          and metadata['checkpoint_sha256']==index['checkpoint_sha256']
          and complete['status']=='JUNYI_REFIT90_COMPLETE'
          and complete['frozen_epochs']==complete['complete_epochs']==index['epochs']
          and complete['checkpoint_sha256']==index['checkpoint_sha256'],'support final-refit lifecycle mismatch')
    current_config=json.loads(json.dumps(asdict(adapter.config),default=str))
    _need(all(training_config[key]==current_config[key] for key in TRAINING_FIELDS),
          'inference adapter training/architecture configuration mismatch')
    variant=getattr(getattr(adapter,'condition',None),'variant','A0')
    _need(index['identity']['variant']==variant and index['model']==variant+'_JUNYI_REFIT',
          'inference adapter variant mismatch')
    if variant!='A0':
        _need(adapter.research_encoding is encoding
              and adapter.condition.identity==index['identity']['condition'],
              'inference graph/confidence condition mismatch')
    _need(adapter.encoding==encoding.native,'inference native vocabulary mismatch')
    source=inference_source_identity()
    _need(binding.model_source_sha256==source,'binding must pin current inference source')
    from .checkpoint import load_training_snapshot
    import torch
    payload=load_training_snapshot(checkpoint,expected_identity=index['identity'],device='cpu')
    _need(sha256_file(checkpoint)==binding.checkpoint_sha256,'checkpoint changed during attachment')
    progress=payload['progress']
    _need(progress.get('complete') is True and progress.get('role')=='junyi_refit90'
          and progress['epoch']==index['epochs'] and len(progress['history'])==index['epochs'],
          'snapshot final refit progress mismatch')
    _need(payload['encoding']==dict(values=list(encoding.native.vocabulary.values),
          train_support_students=encoding.native.train_support_students),'snapshot vocabulary mismatch')
    _need(payload['model_state_dict'] and all(torch.isfinite(v).all().item()
          for v in payload['model_state_dict'].values()),'nonfinite refit weights')
    expected_state=adapter.native.state_dict()
    _need(set(expected_state)==set(payload['model_state_dict']) and all(
        expected_state[name].shape==value.shape and expected_state[name].dtype==value.dtype
        for name,value in payload['model_state_dict'].items()),'snapshot architecture/dtype mismatch')
    try:
        adapter.native.load_state_dict(payload['model_state_dict'],strict=True)
    except Exception:
        adapter._calibration_attach_failed=True
        raise
    adapter.checkpoint_id=binding.checkpoint_sha256
    receipt=dict(index_sha256=expected_index_sha256,checkpoint_sha256=binding.checkpoint_sha256,
                 training_identity=training_identity,inference_source_sha256=source,
                 inference_device=str(adapter.config.device),
                 inference_config=current_config,graph_enabled=getattr(adapter,'graph_enabled',None),
                 native_state_seal=_native_seal(adapter.native))
    result=RefitCalibrationPredictor(adapter,encoding,binding,receipt)
    result.assert_boundary()
    return result


def _source_pins(paths, expected):
    _need(set(expected)=={'canonical_manifest','split_manifest'},'pinned source metadata required')
    actual={name:sha256_file(getattr(paths,name)) for name in expected}
    _need(actual==expected,'calibration source metadata changed')
    return actual


def _expected_rows(learners, view, *, max_targets, max_learner_events):
    """Keys từ full observed prehistory, trước current response và độc lập predictor."""
    _need(type(view) is JunyiPhaseView and view.scope=='calibration_predict'
          and view.full_role_coverage,'full calibration phase required')
    view.assert_integrity()
    seen=set()
    allowed=frozenset(view.users)
    total=0
    previous=None
    for learner in learners:
        _need(type(learner) is LearnerEvents and learner.user_id in allowed
              and learner.user_id not in seen and learner.fold in view.allowed_folds
              and learner.events and len(learner.events)<=max_learner_events,
              'calibration learner scope/size mismatch')
        _need(previous is None or previous<learner.user_id,'canonical calibration learner order required')
        seen.add(learner.user_id)
        previous=learner.user_id
        history=_identity(dict(recipe='junyi-full-observed-prehistory-v1',learner=learner.user_id))
        previous_event=None
        for event in learner.events:
            _need(event.user_id==learner.user_id and event.fold==learner.fold
                  and type(event.source_row) is int and event.source_row>0
                  and type(event.correct) is int and event.correct in (0,1)
                  and type(event.suggested) is int and event.suggested in (0,1),
                  'calibration source event identity mismatch')
            rank=(event.time_done,event.source_row)
            _need(previous_event is None or previous_event<rank,'calibration event chronology mismatch')
            previous_event=rank
            total+=1
            _need(total<=max_targets,'calibration target memory cap exceeded')
            key=(learner.user_id,str(event.source_row),event.exercise,history)
            yield event,key
            history=_identity(dict(previous=history,event=asdict(event)))
    _need(seen==allowed,'calibration learner coverage incomplete')
    view.assert_integrity()


def prepare_calibration_population(paths, view, *, source_pins, max_targets, max_learner_events):
    """Tính manifest nhỏ từ reader, không dùng prediction hoặc checkpoint."""
    _need(type(max_targets) is int and max_targets>0 and type(max_learner_events) is int
          and max_learner_events>0,'bounded calibration population required')
    _source_pins(paths,source_pins)
    population=hashlib.sha256()
    prefixes=hashlib.sha256()
    total=0
    for event,key in _expected_rows(iter_junyi_phase_learners(paths,view),view,
            max_targets=max_targets,max_learner_events=max_learner_events):
        identity=(event.source_row,event.user_id,event.exercise,event.time_done,event.correct,event.suggested,event.fold)
        population.update(json.dumps(identity,separators=(',',':')).encode()+b'\n')
        prefixes.update(json.dumps(key,separators=(',',':')).encode()+b'\n')
        total+=1
    _source_pins(paths,source_pins)
    payload=dict(schema='junyi-calibration-population-v1',roles_identity=view.roles.identity,
                 phase_identity=view.identity,targets=total,source_pins=source_pins,
                 population_sha256=population.hexdigest(),prefix_keys_sha256=prefixes.hexdigest())
    return dict(payload,identity=_identity(payload))


def iter_calibration_observations(records, expected_learners, *, view, binding, population,
                                  max_targets, max_learner_events):
    """Đối chiếu record với event/key độc lập, giữ null OOV và toàn bộ warm-up."""
    _need(population['identity']==_identity({k:v for k,v in population.items() if k!='identity'})
          and population['schema']=='junyi-calibration-population-v1'
          and population['roles_identity']==binding.split_sha256==view.roles.identity
          and population['phase_identity']==view.identity
          and type(population['targets']) is int and 0<population['targets']<=max_targets,
          'calibration population binding mismatch')
    expected=_expected_rows(expected_learners,view,max_targets=max_targets,max_learner_events=max_learner_events)
    digest=hashlib.sha256()
    prefix_digest=hashlib.sha256()
    total=0
    for pair,record in zip_longest(expected,records):
        _need(pair is not None and record is not None,'missing/extra calibration prediction')
        event,key=pair
        _validate_record(record)
        _need(record.checkpoint_id==binding.checkpoint_sha256,'calibration prediction checkpoint mismatch')
        identity=(record.source_row,record.user_id,record.exercise,record.time_done,
                  record.correct,record.suggested,record.fold)
        expected_identity=(event.source_row,event.user_id,event.exercise,event.time_done,
                           event.correct,event.suggested,event.fold)
        _need(identity==expected_identity,'calibration prediction target identity/order mismatch')
        digest.update(json.dumps(identity,separators=(',',':')).encode()+b'\n')
        prefix_digest.update(json.dumps(key,separators=(',',':')).encode()+b'\n')
        target=CalibrationTarget(*key,event.correct,record.prediction,
                                 'supported' if record.prediction is not None else record.prediction_kind)
        total+=1
        yield record,target,key
    _need(total==population['targets'] and digest.hexdigest()==population['population_sha256']
          and prefix_digest.hexdigest()==population['prefix_keys_sha256'],
          'calibration target/prefix population mismatch')


def export_refit_calibration_predictions(predictor, paths, view, *, population,
        expected_population_identity, source_pins, max_targets, max_learner_events,
        prediction_batch_size, output):
    """Xuất raw predictions với predictor đã attach, không fit temperature.

    Caller chọn CPU/GPU stage và prepared reader/context đúng run contract.
    API này không tự dựng Modal worker hay bảo đảm throughput của full cohort.
    """
    _need(not Path(output).exists(),'new raw calibration export required')
    _need(type(predictor) is RefitCalibrationPredictor,'attached frozen refit predictor required')
    _need(population['identity']==expected_population_identity,'pinned calibration population changed')
    _need(population['source_pins']==source_pins,'population source pin mismatch')
    predictor.assert_boundary()
    predictor.encoding.assert_for(view)
    _source_pins(paths,source_pins)
    from .research_junyi_graph import JunyiGraphPhaseSession
    if hasattr(predictor.adapter,'set_phase'):
        predictor.adapter.set_phase(JunyiGraphPhaseSession(predictor.adapter.condition,view))
    factory=lambda:iter_junyi_phase_learners(paths,view)
    if prediction_batch_size is None:
        records=iter_predictions(predictor.adapter,factory())
    else:
        from .prediction_batch import iter_predictions_batched
        records=iter_predictions_batched(predictor.adapter,factory(),batch_size=prediction_batch_size)
    observations=iter_calibration_observations(records,factory(),view=view,binding=predictor.binding,
        population=population,max_targets=max_targets,max_learner_events=max_learner_events)
    def raw_records():
        for record,_,_ in observations:
            yield record
        predictor.assert_boundary()
        _source_pins(paths,source_pins)
    identity=dict(phase='junyi_response_calibration',population=expected_population_identity,
                  checkpoint=predictor.binding.checkpoint_sha256,inference_source=predictor.receipt['inference_source_sha256'],
                  prediction_batch_size=prediction_batch_size)
    result=export_predictions(raw_records(),Path(output),expected_learners_factory=factory,identity=identity)
    _write_json_atomic(Path(output)/'predictor-receipt.json',predictor.receipt)
    return result


def iter_pinned_prediction_export(raw, *, expected_manifest_sha256, shard_sha256):
    """Đọc Parquet đã ghim trên local CPU, không dựng model hoặc import Torch."""
    import duckdb
    raw=Path(raw)
    manifest_path=raw/'manifest.json'
    _need(sha256_file(manifest_path)==expected_manifest_sha256,'raw export manifest changed')
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    _need(manifest.get('status')=='complete' and manifest['shards']
          and set(shard_sha256)=={row['path'] for row in manifest['shards']},
          'complete raw export with exact shard pins required')
    fields=','.join(PredictionRecord.__dataclass_fields__)
    for shard in manifest['shards']:
        filename=shard['path']
        _need('/' not in filename and '\\' not in filename and filename.endswith('.parquet'),
              'raw shard basename required')
        path=raw/filename
        _need(sha256_file(path)==shard_sha256[filename],'raw prediction shard changed')
        literal="'"+str(path).replace("'","''")+"'"
        rows=0
        with duckdb.connect(config={'memory_limit':'128MB','threads':'1','temp_directory':''}) as con:
            cursor=con.execute(f'SELECT {fields} FROM read_parquet({literal}) ORDER BY user_id,time_done,source_row')
            while batch:=cursor.fetchmany(2000):
                for values in batch:
                    record=PredictionRecord(*values)
                    _validate_record(record)
                    rows+=1
                    yield record
        _need(rows==shard['rows'] and sha256_file(path)==shard_sha256[filename],
              'raw prediction shard coverage/content changed')
    _need(sha256_file(manifest_path)==expected_manifest_sha256,'raw manifest changed while reading')


def _fit_memory_budget(population, max_targets, max_learner_events):
    _need(type(max_targets) is int and max_targets>0 and type(population['targets']) is int
          and 0<population['targets']<=max_targets
          and type(max_learner_events) is int and max_learner_events>0,'bounded calibration fit required')
    import psutil
    estimate=population['targets']*4096
    if estimate>psutil.virtual_memory().available*.6:
        raise MemoryError('calibration fit materialization exceeds available RAM estimate')
    return estimate


def fit_response_temperature_from_raw_export(raw, paths, view, *, binding, population,
        expected_population_identity, expected_manifest_sha256, shard_sha256,
        source_pins, max_targets, max_learner_events, output):
    """Fit scalar T trên local CPU từ raw export đã có, không cần GPU adapter.

    Heuristic 4 KiB/target là estimate bảo thủ chưa đo, không là phương pháp
    thống kê hoặc yêu cầu RAM cố định. fit_temperature vẫn giữ implementation V1.
    """
    from . import prediction
    _need(type(binding) is PredictionBinding,'frozen prediction binding required')
    _need(population['identity']==expected_population_identity and population['source_pins']==source_pins,
          'pinned calibration population/source changed')
    estimate=_fit_memory_budget(population,max_targets,max_learner_events)
    _source_pins(paths,source_pins)
    output=Path(output).resolve()
    allowed=(prediction.PROJECT_ROOT/'experiments/akt/results').resolve()
    _need(output!=allowed and output.is_relative_to(allowed) and not output.exists(),
          'new owned calibration-fit output required')
    raw=Path(raw)
    manifest_path=raw/'manifest.json'
    _need(sha256_file(manifest_path)==expected_manifest_sha256,'raw export manifest changed')
    raw_manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    identity=raw_manifest['identity']
    _need(identity['phase']=='junyi_response_calibration' and identity['population']==expected_population_identity
          and identity['checkpoint']==binding.checkpoint_sha256
          and identity['inference_source']==binding.model_source_sha256,
          'raw prediction checkpoint/population/source binding mismatch')
    records=iter_pinned_prediction_export(raw,expected_manifest_sha256=expected_manifest_sha256,
                                          shard_sha256=shard_sha256)
    factory=lambda:iter_junyi_phase_learners(paths,view)
    observations=iter_calibration_observations(records,factory(),view=view,binding=binding,
        population=population,max_targets=max_targets,max_learner_events=max_learner_events)
    targets=[]
    keys=[]
    for _,target,key in observations:
        targets.append(target)
        keys.append(key)
    roles=view.roles
    partition=CalibrationPartition(roles.identity,roles.calibration_users,
        tuple(sorted((*roles.train_users,*roles.selection_users,*roles.outer_validation_users))),None)
    calibration=fit_temperature(targets,binding=binding,partition=partition,expected_target_keys=tuple(keys))
    _source_pins(paths,source_pins)
    output.mkdir(parents=True,exist_ok=False)
    _write_json_atomic(output/'temperature.json',calibration.to_payload())
    _write_json_atomic(output/'manifest.json',dict(identity=identity,population=population,
        binding=asdict(binding),raw_export=raw_manifest,raw_manifest_sha256=expected_manifest_sha256,
        raw_shard_sha256=shard_sha256,calibration_identity=calibration.identity,
        status=calibration.status,total_targets=len(targets),supported_targets=calibration.supported_targets,
        fitting_source_sha256=inference_source_identity(),estimated_materialization_bytes=estimate,
        memory_estimate_semantics='unmeasured conservative 4096 bytes/target; not measured peak RSS'))
    return calibration


def fit_refit_response_calibration(predictor, paths, view, *, population,
        expected_population_identity, source_pins, max_targets, max_learner_events,
        prediction_batch_size, output):
    """Convenience local/toy nối hai API; không phải entrypoint thuê GPU Modal.

    Run thật có thể trả GPU ngay sau export, chuyển raw artifact về D rồi gọi
    fit_response_temperature_from_raw_export bằng process CPU riêng.
    """
    _fit_memory_budget(population,max_targets,max_learner_events)
    output=Path(output)
    _need(not output.exists(),'new calibration output required')
    raw=output/'raw'
    exported=export_refit_calibration_predictions(predictor,paths,view,population=population,
        expected_population_identity=expected_population_identity,source_pins=source_pins,
        max_targets=max_targets,max_learner_events=max_learner_events,
        prediction_batch_size=prediction_batch_size,output=raw)
    pins={row['path']:sha256_file(raw/row['path']) for row in exported['shards']}
    return fit_response_temperature_from_raw_export(raw,paths,view,binding=predictor.binding,
        population=population,expected_population_identity=expected_population_identity,
        expected_manifest_sha256=sha256_file(raw/'manifest.json'),shard_sha256=pins,
        source_pins=source_pins,max_targets=max_targets,max_learner_events=max_learner_events,
        output=output/'fit')
