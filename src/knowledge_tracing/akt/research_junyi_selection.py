"""A0 Junyi selected-only trên role cố định, có checkpoint cuối epoch.

Refit90 và calibration cần external freeze của allocation theo Recipe26.
Module này không cấp quyền các phase đó hoặc truy cập Holdout.
"""
from dataclasses import asdict, dataclass
import gc
import hashlib
import json
from pathlib import Path
import time
import uuid

from .config import AKTConfig, DataPaths, PROJECT_ROOT, ResearchCUDAExecutionProfile, validate_config
from .research_junyi_data import (JunyiPhaseView, fit_junyi_research_encoding,
                                iter_junyi_phase_learners, iter_junyi_research_windows)
from .research_junyi_engineering import file_sha, write_json
from .research_junyi_roles import JunyiResearchRoles


def _identity(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()


@dataclass(frozen=True)
class JunyiSelectedInputs:
    paths: DataPaths
    train: JunyiPhaseView
    selection: JunyiPhaseView
    train_targets: int
    selection_targets: int
    source_identity: str

    def __post_init__(self):
        if (type(self.paths) is not DataPaths or type(self.train) is not JunyiPhaseView
                or type(self.selection) is not JunyiPhaseView):
            raise ValueError('Typed Junyi paths and phase views required')
        if (self.train.scope != 'select_train80' or self.selection.scope != 'raw_selection10'
                or self.train.roles.identity != self.selection.roles.identity
                or set(self.train.users) & set(self.selection.users)
                or any(type(n) is not int or n <= 0 for n in (self.train_targets,self.selection_targets))
                or type(self.source_identity) is not str or len(self.source_identity)!=64
                or any(c not in '0123456789abcdef' for c in self.source_identity)):
            raise ValueError('Separate fixed train80/selection10 inputs required')

    @property
    def identity(self):
        return _identity(dict(source=self.source_identity,train=self.train.identity,
            selection=self.selection.identity,train_targets=self.train_targets,
            selection_targets=self.selection_targets))


def load_full_selected_cache(cache_root, roles_path, *, expected_manifest_sha256, expected_roles_sha256):
    root = Path(cache_root).resolve()
    allowed = (PROJECT_ROOT/'artifacts/akt/junyi-cohorts').resolve()
    if root == allowed or not root.is_relative_to(allowed):
        raise ValueError('Owned Junyi data cache required')
    manifest_path = root/'manifest.json'
    if file_sha(manifest_path) != expected_manifest_sha256 or file_sha(roles_path) != expected_roles_sha256:
        raise ValueError('Pinned Junyi source changed')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if (manifest.get('status') != 'FULL_TRAIN_SELECTION_CACHE_VERIFIED_NOT_TRAINED'
            or manifest.get('purpose') != 'FULL_JUNYI_TRAIN80_SELECTION10_CACHE'
            or manifest.get('full_role_coverage') is not True
            or any(manifest.get(name) is not False for name in ('calibration_events_included',
                'outer_validation_events_included','holdout_events_included'))):
        raise ValueError('Verified selected-only cache required')
    for name in ('canonical.parquet','assignments.parquet'):
        path = root/name
        entry = manifest['outputs'][name]
        if path.is_symlink() or path.stat().st_size != entry['bytes'] or file_sha(path) != entry['sha256']:
            raise ValueError('Junyi cache output changed')
    payload = json.loads(Path(roles_path).read_text(encoding='utf-8'))
    for name in ('train_users','selection_users','calibration_users','outer_validation_users'):
        payload[name] = tuple(payload[name])
    roles = JunyiResearchRoles(**payload)
    if roles.identity != manifest['roles_identity']:
        raise ValueError('Cache/roles mismatch')
    train = JunyiPhaseView(roles,'select_train80',roles.train_users,roles.identity)
    selection = JunyiPhaseView(roles,'raw_selection10',roles.selection_users,roles.identity)
    counts = {row['role']:row for row in manifest['counts']}
    if counts['train']['learners'] != len(train.users) or counts['selection']['learners'] != len(selection.users):
        raise ValueError('Cache learner count mismatch')
    # Đường dẫn được tạo theo mount hiện tại; không dùng path Windows trong manifest.
    paths = DataPaths(root/'canonical.parquet',root/'assignments.parquet',manifest_path,Path(roles_path))
    return JunyiSelectedInputs(paths,train,selection,int(counts['train']['targets']),
        int(counts['selection']['targets']),_identity(dict(cache=expected_manifest_sha256,roles=expected_roles_sha256)))


def validate_selected_grant(config, inputs, grant, *, config_sha256, gate_sha256, runtime_sha256,
                            prepared_inputs=None, candidate_id='A0'):
    if candidate_id not in ('A0','A1_EXPERT','A2_EXPERT','A3_EXPERT'):
        raise PermissionError('Supported Junyi selected candidate required')
    expected = dict(candidate_id=candidate_id,phase='junyi_selected_only',config_sha256=config_sha256,
                    inputs_identity=inputs.identity,gate_sha256=gate_sha256,runtime_sha256=runtime_sha256)
    if (grant.get('status') != 'USER_APPROVED' or grant.get('binding') != expected
            or grant.get('prepared_inputs',{}) != (prepared_inputs or {})
            or type(grant.get('approval_reference')) is not str or not grant['approval_reference'].strip()
            or type(grant.get('workload_epochs')) is not int
            or not 1 <= grant['workload_epochs'] <= config.max_epochs
            or grant.get('purpose') not in ('bounded_engineering','main_selected')):
        raise PermissionError('Bounded Junyi selected grant mismatch')
    if grant['purpose']=='main_selected' and (grant['workload_epochs']!=20
            or not inputs.train.full_role_coverage or not inputs.selection.full_role_coverage):
        raise PermissionError('Main selected requires full frozen roles and early-stopping envelope')


def _prediction_implementation(batch_size):
    return 'legacy_single_window_v1' if batch_size is None else f'batched_windows_v1_batch{batch_size}'


def _evaluate(adapter, learners, target_count, *, output=None, batch_size=None, selection_cache=None,
              prefetch=False):
    """Giữ hai vector số bounded, stream identity/output thay vì giữ hàng triệu dict."""
    import numpy as np
    import torch
    from .prediction import iter_predictions
    if selection_cache is not None:
        from .research_junyi_selection_cache import SelectionCacheSession
        from .prediction_batch import iter_prepared_predictions_batched
        if type(selection_cache) is not SelectionCacheSession or batch_size is None:
            raise ValueError('Typed selection cache requires admitted prediction batching')
        records=iter_prepared_predictions_batched(adapter,selection_cache.iter_prepared(),batch_size=batch_size,prefetch=prefetch)
    elif batch_size is None:
        records=iter_predictions(adapter,learners)
    else:
        from .prediction_batch import iter_predictions_batched
        records=iter_predictions_batched(adapter,learners,batch_size=batch_size,prefetch=prefetch)
    probabilities = np.empty(target_count,dtype=np.float32)
    labels = np.empty(target_count,dtype=np.float32)
    supported = total = 0
    population = hashlib.sha256()
    previous_user=None
    global_rank=-1
    for record in records:
        total += 1
        if total > target_count:
            raise ValueError('Prediction target count exceeds frozen input')
        key = (record.source_row,record.user_id,record.exercise,record.time_done,record.correct,record.suggested,record.fold)
        population.update(json.dumps(key,separators=(',', ':')).encode()+b'\n')
        if record.prediction is not None:
            probabilities[supported] = record.prediction
            labels[supported] = record.correct
            supported += 1
        if output is not None:
            global_rank=global_rank+1 if record.user_id==previous_user else 0
            previous_user=record.user_id
            exported=asdict(record)
            exported['global_rank']=global_rank
            output.write(json.dumps(exported,allow_nan=False)+'\n')
    if total != target_count or supported == 0:
        raise ValueError('Prediction target population incomplete or unsupported')
    p,y = probabilities[:supported],labels[:supported]
    loss = float(torch.nn.functional.binary_cross_entropy(torch.from_numpy(p),torch.from_numpy(y)).item())
    return dict(targets=total,supported=supported,oov=total-supported,population_sha256=population.hexdigest(),
                native_bce=loss,probability_sha256=hashlib.sha256(p.tobytes()).hexdigest())


def _make_selected_adapter(config, profile, encoding, view, condition, *, context_cache=None):
    if condition is None:
        if context_cache is not None:
            raise ValueError('A0 cannot consume graph context cache')
        from .model import AKTAdapter
        return AKTAdapter(config,encoding.native)
    from .research_junyi_graph import JunyiGraphPhaseSession
    from .research_junyi_graph_model import JunyiGraphAKTAdapter
    return JunyiGraphAKTAdapter(config=config,encoding=encoding,condition=condition,
        phase=JunyiGraphPhaseSession(condition,view),cuda_profile=profile,compact_context=True,
        context_cache=context_cache)


def _comparison_candidate(config, profile, inputs, encoding, initial_backbone, *,
        encoding_file, encoding_receipt, train_window_cache, graph_condition, candidate_id,
        validation_batch_size=None):
    """Đo các định danh đầu vào thực để đối chiếu A0 đã nghiệm thu."""
    from .comparison_contract import TRAINING_FIELDS
    if any(value is None for value in (encoding_file,encoding_receipt,train_window_cache)):
        raise ValueError('Matched comparison requires prepared encoding and window cache')
    config_values = json.loads(json.dumps(asdict(config),default=str))
    candidate = dict(candidate_id=candidate_id,
        data_pins=dict(roles=file_sha(inputs.paths.split_manifest),
            selected_manifest=file_sha(inputs.paths.canonical_manifest),
            encoding=file_sha(encoding_file),encoding_receipt=file_sha(encoding_receipt),
            window_manifest=file_sha(Path(train_window_cache)/'manifest.json')),
        roles_identity=inputs.train.roles.identity,encoding_identity=encoding.identity,
        train_view_identity=inputs.train.identity,train_targets=inputs.train_targets,
        selection_targets=inputs.selection_targets,
        prediction_implementation=_prediction_implementation(validation_batch_size),
        initial_backbone_sha256=initial_backbone,numeric_profile=asdict(profile),
        training_config={key:config_values[key] for key in TRAINING_FIELDS})
    if graph_condition is not None:
        candidate['graph_provenance'] = dict(train_view_identity=graph_condition.encoding.fit_view.identity,
            encoding_identity=graph_condition.encoding.identity,
            history_scope='effective_native_window_prefix',artifact_sha256=graph_condition.identity,
            topology_source_sha256=graph_condition.topology_source_sha256,uses_oracle_labels=False)
        if graph_condition.confidence is not None:
            candidate['graph_provenance'].update(
                confidence_fit_view_identity=graph_condition.confidence.train_view_identity,
                confidence_artifact_sha256=graph_condition.confidence.fit_artifact_sha256)
    return candidate


def run_junyi_selected(config: AKTConfig, profile: ResearchCUDAExecutionProfile,
        inputs: JunyiSelectedInputs, *, authorization_file, expected_authorization_sha256,
        runtime_report, lock_file, encoding_file=None, expected_encoding_sha256=None,
        train_window_cache=None, expected_train_window_manifest_sha256=None,
        resume_checkpoint=None, expected_resume_sha256=None,
        encoding_receipt=None, expected_encoding_receipt_sha256=None, graph_condition=None,
        comparison_reference_file=None, expected_comparison_reference_sha256=None,
        validation_batch_size=None, train_graph_context_cache=None,
        expected_train_graph_context_cache_sha256=None,
        selection_window_cache=None, expected_selection_cache_manifest_sha256=None,
        prefetch_train_windows=False, source_transition_file=None,
        expected_source_transition_sha256=None, prefetch_selection_windows=False,
        train_cache_admission_receipt=None, expected_train_cache_admission_sha256=None,
        selection_graph_context_cache=None, expected_selection_graph_context_cache_sha256=None,
        selection_cpu_admission_file=None, expected_selection_cpu_admission_sha256=None,
        selection_window_admission_file=None, expected_selection_window_admission_sha256=None):
    """A0 hoặc A1 expert, selected fit80/rawbest10 với cùng state machine."""
    validate_config(config,cuda_profile=profile)
    if validation_batch_size is not None and (type(validation_batch_size) is not int
            or not 1<=validation_batch_size<=min(128,config.batch_size)):
        raise ValueError('Validation batch must fit configured training batch and 128 ceiling')
    if config.phase!='junyi-research' or config.execution_enabled is not True:
        raise PermissionError('Explicit Junyi CUDA execution config required')
    if (config.max_train_users<len(inputs.train.users) or config.max_val_users<len(inputs.selection.users)
            or config.max_targets_per_side<max(inputs.train_targets,inputs.selection_targets)):
        raise ValueError('Junyi population exceeds explicit caps')
    if file_sha(authorization_file)!=expected_authorization_sha256:
        raise PermissionError('Authorization file changed')
    grant = json.loads(Path(authorization_file).read_text(encoding='utf-8'))
    if (comparison_reference_file is None)!=(expected_comparison_reference_sha256 is None):
        raise ValueError('Comparison reference path and external pin required together')
    if (graph_condition is not None and grant.get('purpose')=='main_selected'
            and comparison_reference_file is None):
        raise PermissionError('Main graph training requires a pinned A0 comparison reference')
    prepared = {}
    if (train_cache_admission_receipt is None)!=(expected_train_cache_admission_sha256 is None):
        raise ValueError('Train CPU admission receipt and external pin required together')
    if train_cache_admission_receipt is not None:
        if train_window_cache is None or file_sha(train_cache_admission_receipt)!=expected_train_cache_admission_sha256:
            raise ValueError('Train CPU admission must bind a pinned window cache')
        prepared['train_cache_admission_sha256']=expected_train_cache_admission_sha256
    if type(prefetch_selection_windows) is not bool or (prefetch_selection_windows and validation_batch_size is None):
        raise ValueError('Boolean selection prefetch requires admitted batching')
    if prefetch_selection_windows:
        prepared['prefetch_selection_windows']=True
    if (source_transition_file is None)!=(expected_source_transition_sha256 is None):
        raise ValueError('Source transition receipt and external pin required together')
    transition = None
    if source_transition_file is not None:
        if resume_checkpoint is None or graph_condition is None or graph_condition.variant!='A1':
            raise ValueError('Source transition requires A1 checkpoint resume')
        if file_sha(source_transition_file)!=expected_source_transition_sha256:
            raise ValueError('Source transition receipt changed')
        transition=json.loads(Path(source_transition_file).read_text(encoding='utf-8'))
        if set(transition)!= {'source_identity','evidence'}:
            raise ValueError('Explicit source identity and parity evidence required')
        prepared['source_transition_sha256']=expected_source_transition_sha256
    if type(prefetch_train_windows) is not bool or (prefetch_train_windows and train_window_cache is None):
        raise ValueError('Boolean prefetch requires pinned train window cache')
    if prefetch_train_windows:
        prepared['prefetch_train_windows']=True
    if (selection_window_cache is None)!=(expected_selection_cache_manifest_sha256 is None):
        raise ValueError('Selection cache path and pin required together')
    if selection_window_cache is not None:
        if validation_batch_size is None or encoding_file is None:
            raise ValueError('Selection cache requires pinned encoding and admitted batching')
        if file_sha(Path(selection_window_cache)/'manifest.json')!=expected_selection_cache_manifest_sha256:
            raise ValueError('Selection cache manifest changed')
        prepared['selection_cache_manifest_sha256']=expected_selection_cache_manifest_sha256
    if (train_graph_context_cache is None)!=(expected_train_graph_context_cache_sha256 is None):
        raise ValueError('Graph context cache path and pin required together')
    if train_graph_context_cache is not None:
        if graph_condition is None or train_window_cache is None:
            raise ValueError('Graph context cache requires graph condition and pinned native window cache')
        if file_sha(train_graph_context_cache)!=expected_train_graph_context_cache_sha256:
            raise ValueError('Prepared graph context cache changed')
        prepared['train_graph_context_cache_sha256']=expected_train_graph_context_cache_sha256
    for name,path,pin in (
        ('selection_graph_context_cache_sha256',selection_graph_context_cache,expected_selection_graph_context_cache_sha256),
        ('selection_cpu_admission_sha256',selection_cpu_admission_file,expected_selection_cpu_admission_sha256),
        ('selection_window_admission_sha256',selection_window_admission_file,expected_selection_window_admission_sha256)):
        if (path is None)!=(pin is None):
            raise ValueError('Selection prepared file and external SHA required together')
        if path is not None:
            if selection_window_cache is None or file_sha(path)!=pin:
                raise ValueError('Selection prepared artifact changed or has no window cache')
            prepared[name]=pin
    if validation_batch_size is not None:
        prepared['validation_batch_size']=validation_batch_size
    comparison_reference = None
    if comparison_reference_file is not None:
        if file_sha(comparison_reference_file)!=expected_comparison_reference_sha256:
            raise ValueError('Comparison reference changed')
        document = json.loads(Path(comparison_reference_file).read_text(encoding='utf-8'))
        if document.get('status')!='PASS_A0_DATA_LINEAGE_CANDIDATES_PENDING':
            raise ValueError('Verified A0 data-lineage reference required')
        comparison_reference = document['reference']
        if comparison_reference['prediction_implementation']!=_prediction_implementation(validation_batch_size):
            raise ValueError('Prediction batching differs from A0 comparison reference')
        prepared['comparison_reference_sha256']=expected_comparison_reference_sha256
        if grant.get('purpose')=='main_selected':
            verified_inputs=load_full_selected_cache(inputs.paths.canonical.parent,inputs.paths.split_manifest,
                expected_manifest_sha256=comparison_reference['data_pins']['selected_manifest'],
                expected_roles_sha256=comparison_reference['data_pins']['roles'])
            if verified_inputs != inputs:
                raise ValueError('Main comparison inputs differ from verified frozen cache')
    candidate_id = 'A0'
    if graph_condition is not None:
        from .research_junyi_graph import JunyiGraphCondition
        if type(graph_condition) is not JunyiGraphCondition:
            raise ValueError('Typed Junyi graph condition required')
        graph_condition.assert_integrity()
        if graph_condition.encoding.fit_view.identity != inputs.train.identity:
            raise ValueError('Junyi graph condition belongs to a different TRAIN80 cohort')
        candidate_id = graph_condition.variant+'_EXPERT'
        prepared['graph_condition_sha256'] = graph_condition.identity
        if graph_condition.confidence is not None:
            prepared['edge_confidence_identity']=graph_condition.confidence.identity
            prepared['edge_confidence_sha256']=graph_condition.confidence.fit_artifact_sha256
    if (encoding_file is None)!=(expected_encoding_sha256 is None):
        raise ValueError('Encoding path and pin required together')
    if (train_window_cache is None)!=(expected_train_window_manifest_sha256 is None):
        raise ValueError('Window-cache path and pin required together')
    if encoding_file is not None:
        if (encoding_receipt is None or expected_encoding_receipt_sha256 is None
                or file_sha(encoding_file)!=expected_encoding_sha256
                or file_sha(encoding_receipt)!=expected_encoding_receipt_sha256):
            raise ValueError('Prepared encoding changed')
        prepared['encoding_sha256']=expected_encoding_sha256
        prepared['encoding_receipt_sha256']=expected_encoding_receipt_sha256
    if train_window_cache is not None:
        if encoding_file is None or file_sha(Path(train_window_cache)/'manifest.json')!=expected_train_window_manifest_sha256:
            raise ValueError('Prepared window cache requires pinned training encoding')
        prepared['train_window_manifest_sha256']=expected_train_window_manifest_sha256
    if (resume_checkpoint is None)!=(expected_resume_sha256 is None):
        raise ValueError('Resume checkpoint and external pin required together')
    if resume_checkpoint is not None:
        if file_sha(resume_checkpoint)!=expected_resume_sha256:
            raise ValueError('Resume checkpoint changed')
        prepared['resume_checkpoint_sha256']=expected_resume_sha256
    from .authorization import preflight, require_gate2_evidence, config_hash
    gate = require_gate2_evidence(config,lock_file=lock_file)
    preflight(config,runtime_report_path=runtime_report,lock_file=lock_file,cuda_profile=profile)
    validate_selected_grant(config,inputs,grant,config_sha256=config_hash(config),
        gate_sha256=gate['report_sha256'],runtime_sha256=file_sha(runtime_report),prepared_inputs=prepared,
        candidate_id=candidate_id)
    import torch
    from .training import EarlyStopping, EpochStats, train_epoch, _seed
    from .checkpoint import save_checkpoint, load_checkpoint, load_training_snapshot, restore_checkpoint
    from .research_graph_model import _cuda_execution_check
    from .research_runner import _state_hash
    _cuda_execution_check(profile,synchronize=True)
    output = config.output_dir
    output.mkdir(exist_ok=resume_checkpoint is not None and transition is None)
    started = time.monotonic()
    reader_options=dict(temp_dir=PROJECT_ROOT/'artifacts/akt/tmp'/config.run_id)
    if encoding_file is None:
        encoding = fit_junyi_research_encoding(inputs.paths,inputs.train,**reader_options)
    else:
        from .research_junyi_data import load_prepared_junyi_encoding
        encoding=load_prepared_junyi_encoding(encoding_file,encoding_receipt,view=inputs.train,
            source_data_sha256=inputs.source_identity,expected_file_sha256=expected_encoding_sha256,
            expected_receipt_sha256=expected_encoding_receipt_sha256)
    if graph_condition is not None:
        if graph_condition.encoding.identity != encoding.identity:
            raise ValueError('Junyi graph condition encoding differs from admitted training vocabulary')
        encoding = graph_condition.encoding
    if train_window_cache is None:
        windows_factory=lambda:iter_junyi_research_windows(inputs.paths,inputs.train,encoding,**reader_options)
    else:
        from .research_junyi_window_cache import JunyiWindowCacheSession
        cache_session=JunyiWindowCacheSession(train_window_cache,view=inputs.train,
            encoding=encoding,source_data_sha256=inputs.source_identity,expected_target_rows=inputs.train_targets,
            expected_manifest_sha256=expected_train_window_manifest_sha256,prefetch=prefetch_train_windows,
            admission_receipt=train_cache_admission_receipt,
            expected_admission_sha256=expected_train_cache_admission_sha256)
        windows_factory=cache_session.iter_windows
    graph_cache = None
    if train_graph_context_cache is not None:
        from .research_junyi_graph import JunyiGraphPhaseSession
        from .research_junyi_graph_cache import GraphContextCache
        graph_cache = GraphContextCache.open(train_graph_context_cache,
            expected_train_graph_context_cache_sha256,JunyiGraphPhaseSession(graph_condition,inputs.train),
            dataset_sha256=inputs.source_identity,
            window_manifest_sha256=expected_train_window_manifest_sha256)
        if graph_cache.targets!=inputs.train_targets:
            raise ValueError('Graph context cache target population differs')
    selection_session = None
    if selection_window_cache is not None:
        from .research_junyi_selection_cache import SelectionCacheSession
        selection_session=SelectionCacheSession(selection_window_cache,view=inputs.selection,
            encoding=encoding,source_sha256=inputs.source_identity,expected_targets=inputs.selection_targets,
            expected_manifest_sha256=expected_selection_cache_manifest_sha256,
            admission_file=selection_cpu_admission_file,expected_admission_sha256=expected_selection_cpu_admission_sha256,
            window_admission_file=selection_window_admission_file,
            expected_window_admission_sha256=expected_selection_window_admission_sha256)
        if comparison_reference is not None and selection_session.manifest['population_sha256']!=comparison_reference['selection_population_sha256']:
            raise ValueError('Selection cache population differs from A0 reference')
    selection_graph_cache=None
    if selection_graph_context_cache is not None:
        if graph_condition is None:
            raise ValueError('Selection graph cache requires graph condition')
        from .research_junyi_graph import JunyiGraphPhaseSession
        from .research_junyi_graph_cache import GraphContextCache
        selection_graph_cache=GraphContextCache.open(selection_graph_context_cache,
            expected_selection_graph_context_cache_sha256,JunyiGraphPhaseSession(graph_condition,inputs.selection),
            dataset_sha256=inputs.source_identity,
            window_manifest_sha256=selection_session.manifest['window_manifest_sha256'])
    identity = dict(kind='junyi_a0_selected_v1',inputs=inputs.identity,encoding=encoding.identity,
        prediction_implementation=_prediction_implementation(validation_batch_size),
        config=json.loads(json.dumps(asdict(config),default=str)),profile=asdict(profile),
        source_build_sha256=_identity(json.loads(Path(gate['evidence_path']).read_text())['build_hashes']))
    if graph_condition is not None:
        identity.update(kind='junyi_'+graph_condition.variant.lower()+'_selected_v1',candidate_id=candidate_id,
            batch_factory=dict(condition_sha256=graph_condition.identity,encoding_sha256=encoding.identity,
                phase_sha256=inputs.train.identity,graph_enabled=True,
                context_backend='compact-'+graph_condition.variant.lower()+'-v1',
                graph_context_cache=None if graph_cache is None else graph_cache.identity))
    if train_cache_admission_receipt is not None:
        identity['train_cache_admission_sha256']=expected_train_cache_admission_sha256
    if comparison_reference is not None:
        identity['comparison_reference_sha256']=expected_comparison_reference_sha256
    if validation_batch_size is not None:
        identity['validation_batch_size']=validation_batch_size
    if selection_session is not None:
        identity['selection_cache_manifest_sha256']=expected_selection_cache_manifest_sha256
    for name in ('selection_graph_context_cache_sha256','selection_cpu_admission_sha256',
                 'selection_window_admission_sha256'):
        if name in prepared:
            identity[name]=prepared[name]
    if prefetch_train_windows:
        identity['prefetch_train_windows']=True
    if prefetch_selection_windows:
        identity['prefetch_selection_windows']=True
    if transition is not None:
        from .research_junyi_transition import validate_source_transition
        validate_source_transition(transition['source_identity'],identity,transition['evidence'],
            checkpoint_sha256=expected_resume_sha256)
    if resume_checkpoint is None or transition is not None:
        write_json(output/'run-manifest.json',identity)
    elif json.loads((output/'run-manifest.json').read_text())!=identity or (output/'COMPLETE.json').exists():
        raise ValueError('Resume requires identical unfinished logical run')
    attempt_id=uuid.uuid4().hex
    write_json(output/f'attempt-{attempt_id}.json',dict(authorization_sha256=expected_authorization_sha256,
        resume_sha256=expected_resume_sha256,prepared_inputs=prepared))
    _seed(42)
    with torch.device('cpu'):
        adapter = _make_selected_adapter(config,profile,encoding,inputs.train,graph_condition,
            context_cache=graph_cache)
    if graph_condition is not None and identity['batch_factory']!=adapter.audit_context_boundary():
        raise ValueError('Producer batch factory identity differs from bound adapter')
    if graph_condition is not None:
        from types import SimpleNamespace
        initial_backbone=_state_hash(SimpleNamespace(native=adapter.native.backbone))
    else:
        initial_backbone=_state_hash(adapter)
    initial_path=output/'initial-backbone.json'
    if resume_checkpoint is None or transition is not None:
        write_json(initial_path,dict(sha256=initial_backbone,seed=42,encoding_identity=encoding.identity))
    elif json.loads(initial_path.read_text())['sha256']!=initial_backbone:
        raise ValueError('Resume backbone initialization differs from frozen run')
    comparison_candidate = None
    if comparison_reference is not None:
        from .comparison_contract import require_matched_candidate
        comparison_candidate = _comparison_candidate(config,profile,inputs,encoding,initial_backbone,
            encoding_file=encoding_file,encoding_receipt=encoding_receipt,
            train_window_cache=train_window_cache,graph_condition=graph_condition,candidate_id=candidate_id,
            validation_batch_size=validation_batch_size)
        require_matched_candidate(comparison_reference,comparison_candidate)
        write_json(output/f'comparison-admission-{attempt_id}.json',dict(
            status='MATCHED_A0_INPUTS_INITIALIZATION_AND_TRAINING_CONFIG',
            reference_sha256=expected_comparison_reference_sha256,candidate=comparison_candidate,
            expected_selection_population_sha256=comparison_reference['selection_population_sha256']))
    optimizer = torch.optim.Adam(adapter.native.parameters(),lr=config.lr,betas=config.betas,eps=config.eps,
        weight_decay=config.weight_decay,foreach=False,fused=False,capturable=False,differentiable=False,
        amsgrad=False,maximize=False,decoupled_weight_decay=False)
    stopper = EarlyStopping(config.patience,config.min_delta)
    evaluation_options={} if validation_batch_size is None else dict(batch_size=validation_batch_size)
    if prefetch_selection_windows:
        evaluation_options['prefetch']=True
    if selection_session is not None:
        evaluation_options['selection_cache']=selection_session
    steps = targets = 0
    history = []
    population = None
    first_epoch=1
    pending_stats=None
    epoch_resume=None
    if resume_checkpoint is not None:
        source_identity=identity if transition is None else transition['source_identity']
        payload=load_training_snapshot(resume_checkpoint,expected_identity=source_identity,device='cuda')
        if transition is not None:
            progress=payload.get('progress',{})
            stats=progress.get('epoch_stats',{})
            if (payload.get('checkpoint_kind') is not None or progress.get('complete') is not True
                    or progress.get('epoch')!=1 or progress.get('validation_complete') is not False
                    or progress.get('history')!=[] or progress.get('optimizer_steps')!=0
                    or progress.get('valid_targets')!=0 or stats.get('complete') is not True
                    or stats.get('valid_targets')!=inputs.train_targets):
                raise ValueError('Source transition only supports full epoch1 before validation')
            write_json(output/'source-transition.json',dict(
                source_checkpoint_sha256=expected_resume_sha256,receipt_sha256=expected_source_transition_sha256,
                source_identity=source_identity,target_identity=identity,
                scope='complete_epoch1_preserved_validation_pending'))
        if payload.get('checkpoint_kind')=='training_recovery_v1':
            state=payload['resume_state']['trainer_state']['selection_state']
            first_epoch=payload['resume_state']['epoch']
            epoch_resume=Path(resume_checkpoint)
        else:
            restore_checkpoint(adapter,optimizer,payload)
            state=payload['progress']
            first_epoch=state['epoch']+1
            if state.get('validation_complete') is False:
                first_epoch=state['epoch']
                pending_stats=EpochStats(**state['epoch_stats'])
        stopper=EarlyStopping(**state['stopper'])
        history=list(state['history'])
        steps=state['optimizer_steps']
        targets=state['valid_targets']
        population=None if not history else history[-1]['validation']['population_sha256']
        del payload
    recovery_root=output/'batch-recovery'
    recovery_root.mkdir(exist_ok=True)
    def publish_batch(path):
        import os
        directory=output/'checkpoints'/path.stem
        directory.mkdir(parents=True)
        os.link(path,directory/'state.pt')
        cp_sha=file_sha(path)
        write_json(directory/'metadata.json',dict(checkpoint_sha256=cp_sha,
            checkpoint_bytes=path.stat().st_size,identity=identity,scope='partial_epoch_recovery'))
        write_json(directory/'COMPLETE.json',dict(checkpoint_sha256=cp_sha,
            metadata_sha256=file_sha(directory/'metadata.json')))
    for epoch in range(first_epoch,grant['workload_epochs']+1):
        if stopper.stale_epochs>=config.patience:
            break
        remaining = config.max_wall_seconds-(time.monotonic()-started)
        if remaining <= 0 or steps >= config.max_steps or targets >= config.max_total_targets:
            break
        batch_options = {}
        if graph_condition is not None:
            from .research_junyi_graph import JunyiGraphPhaseSession
            adapter.set_phase(JunyiGraphPhaseSession(graph_condition,inputs.train),context_cache=graph_cache)
            batch_options['batch_factory'] = adapter.collate_training
        with (output/f'epoch-{epoch:03d}-{attempt_id}-progress.jsonl').open('x',encoding='utf-8') as log:
            def progress(event):
                if event['training']['optimizer_steps']%100==0 or event['complete_epoch']:
                    log.write(json.dumps(event,allow_nan=False)+'\n')
                    log.flush()
            if pending_stats is None:
                previous_epoch_wall=0.
                if epoch_resume is not None:
                    snapshot=load_training_snapshot(epoch_resume,expected_identity=identity,device='cpu')
                    previous_epoch_wall=snapshot['resume_state']['trainer_state']['stats']['resource']['wall_seconds']
                    del snapshot
                stats = train_epoch(adapter,windows_factory,
                    optimizer=optimizer,epoch=epoch,budget=dict(max_steps=config.max_steps-steps,
                    max_targets=config.max_total_targets-targets,
                    max_seconds=previous_epoch_wall+min(config.max_seconds,max(1.,remaining-30)),
                    max_rss_bytes=config.max_rss_bytes,min_available_ram_bytes=config.min_available_ram_bytes,
                    run_id=config.run_id,phase=config.phase,resource_sample_limit=128,progress_resource_samples=False),
                    progress_callback=progress,recovery=dict(checkpoint_dir=recovery_root,identity=identity,
                        checkpoint_every_steps=1000,resume_checkpoint=epoch_resume,checkpoint_callback=publish_batch,
                        selection_state=dict(stopper=asdict(stopper),history=history,
                                             optimizer_steps=steps,valid_targets=targets)),**batch_options)
            else:
                stats=pending_stats
        pending_stats=None
        epoch_resume=None
        prior_steps,prior_targets=steps,targets
        steps += stats.optimizer_steps
        targets += stats.valid_targets
        write_json(output/f'epoch-{epoch:03d}-{attempt_id}-training.json',asdict(stats))
        if not stats.complete:
            break
        if stats.valid_targets != inputs.train_targets:
            raise ValueError('Complete epoch population differs from frozen train')
        _cuda_execution_check(profile,synchronize=True)
        # Công bố state trước validation để timeout sau train không mất epoch.
        before_validation=output/'checkpoints'/f'train-epoch-{epoch:03d}'
        if not before_validation.exists():
            before_validation.mkdir(parents=True)
            save_checkpoint(before_validation/'state.pt',adapter,optimizer,identity=identity,
                progress=dict(complete=True,epoch=epoch,validation_complete=False,epoch_stats=asdict(stats),
                    stopper=asdict(stopper),history=history,optimizer_steps=prior_steps,valid_targets=prior_targets))
            cp_sha=file_sha(before_validation/'state.pt')
            write_json(before_validation/'metadata.json',dict(checkpoint_sha256=cp_sha,
                checkpoint_bytes=(before_validation/'state.pt').stat().st_size,identity=identity,
                scope='complete_epoch_before_validation'))
            write_json(before_validation/'COMPLETE.json',dict(checkpoint_sha256=cp_sha,
                metadata_sha256=file_sha(before_validation/'metadata.json')))
        adapter.checkpoint_id = f'{config.run_id}-epoch-{epoch}'
        if graph_condition is not None:
            adapter.set_phase(JunyiGraphPhaseSession(graph_condition,inputs.selection),context_cache=selection_graph_cache)
        validation_started=time.monotonic()
        validation = _evaluate(adapter,
            iter_junyi_phase_learners(inputs.paths,inputs.selection,**reader_options),inputs.selection_targets,
            **evaluation_options)
        if comparison_candidate is not None:
            require_matched_candidate(comparison_reference,dict(comparison_candidate,
                observed_selection_population_sha256=validation['population_sha256']),observed=True)
        if population is not None and validation['population_sha256'] != population:
            raise ValueError('Selection population changed across epochs')
        population = validation['population_sha256']
        stop = stopper.observe(epoch,validation['native_bce'])
        history.append(dict(epoch=epoch,validation=validation,validation_seconds=time.monotonic()-validation_started,
                            cuda_resource=_cuda_execution_check(profile,synchronize=True)))
        checkpoint = output/'checkpoints'/f'epoch-{epoch:03d}'
        checkpoint.mkdir(parents=True)
        save_checkpoint(checkpoint/'state.pt',adapter,optimizer,identity=identity,
            progress=dict(complete=True,epoch=epoch,optimizer_steps=steps,valid_targets=targets,
                          stopper=asdict(stopper),history=history,validation_complete=True))
        cp_sha = file_sha(checkpoint/'state.pt')
        write_json(checkpoint/'metadata.json',dict(checkpoint_sha256=cp_sha,
            checkpoint_bytes=(checkpoint/'state.pt').stat().st_size,epoch=epoch,identity=identity))
        write_json(checkpoint/'COMPLETE.json',dict(checkpoint_sha256=cp_sha,
            metadata_sha256=file_sha(checkpoint/'metadata.json')))
        if stop:
            break
    finished = bool(history) and (stopper.stale_epochs>=config.patience or stopper.last_epoch==config.max_epochs)
    if not finished:
        terminal = dict(status='PARTIAL_SELECTED_ONLY_NOT_FINAL',history=history,optimizer_steps=steps,
            trained_targets=targets,selected_epoch=None,external_freeze=False)
        if graph_condition is not None:
            terminal.update(candidate_id=candidate_id,graph_condition_sha256=graph_condition.identity)
        write_json(output/f'partial-terminal-{attempt_id}.json',terminal)
        return terminal
    best = output/'checkpoints'/f'epoch-{stopper.best_epoch:03d}'/'state.pt'
    del adapter,optimizer
    gc.collect()
    torch.cuda.empty_cache()
    payload = load_checkpoint(best,expected_identity=identity,device='cuda')
    with torch.device('cpu'):
        adapter = _make_selected_adapter(config,profile,encoding,inputs.selection,graph_condition,
            context_cache=selection_graph_cache)
    adapter.native.load_state_dict(payload['model_state_dict'])
    del payload
    adapter.checkpoint_id = file_sha(best)
    predictions_file=output/f'raw-best-selection-{attempt_id}.jsonl'
    with predictions_file.open('x',encoding='utf-8') as stream:
        validation = _evaluate(adapter,
            iter_junyi_phase_learners(inputs.paths,inputs.selection,**reader_options),inputs.selection_targets,
            output=stream,**evaluation_options)
    expected = history[stopper.best_epoch-1]['validation']
    if validation!=expected:
        raise ValueError('Best checkpoint reload changed target population or predictions')
    status = ('JUNYI_A0_SELECTED_ONLY_COMPLETE' if graph_condition is None
              else 'JUNYI_'+graph_condition.variant+'_SELECTED_ONLY_COMPLETE')
    terminal = dict(status=status,selected_epoch=stopper.best_epoch,
        complete_epochs=stopper.last_epoch,history=history,optimizer_steps=steps,trained_targets=targets,
        checkpoint_sha256=file_sha(best),encoding_identity=encoding.identity,validation=validation,
        initial_backbone_sha256=initial_backbone,predictions_file=predictions_file.name,
        predictions_sha256=file_sha(predictions_file),
        full_role_coverage=inputs.train.full_role_coverage and inputs.selection.full_role_coverage,
        external_freeze=False,refit_completed=False,calibration_completed=False)
    if graph_condition is not None:
        terminal.update(candidate_id=candidate_id,graph_condition_sha256=graph_condition.identity)
    if comparison_reference is not None:
        terminal.update(comparison_reference_sha256=expected_comparison_reference_sha256,
            comparison_population_matched=True)
    if validation_batch_size is not None:
        terminal.update(validation_batch_size=validation_batch_size,
            prediction_implementation=_prediction_implementation(validation_batch_size))
    write_json(output/'selected-terminal.json',terminal)
    write_json(output/'COMPLETE.json',dict(status=terminal['status'],terminal_sha256=file_sha(output/'selected-terminal.json')))
    return terminal


def run_a0_junyi_selected(config: AKTConfig, profile: ResearchCUDAExecutionProfile,
        inputs: JunyiSelectedInputs, *, authorization_file, expected_authorization_sha256,
        runtime_report, lock_file, encoding_file=None, expected_encoding_sha256=None,
        train_window_cache=None, expected_train_window_manifest_sha256=None,
        resume_checkpoint=None, expected_resume_sha256=None,
        encoding_receipt=None, expected_encoding_receipt_sha256=None,
        comparison_reference_file=None, expected_comparison_reference_sha256=None,
        validation_batch_size=None):
    """Giữ entrypoint và hợp đồng A0 hiện có."""
    return run_junyi_selected(config,profile,inputs,authorization_file=authorization_file,
        expected_authorization_sha256=expected_authorization_sha256,runtime_report=runtime_report,
        lock_file=lock_file,encoding_file=encoding_file,expected_encoding_sha256=expected_encoding_sha256,
        train_window_cache=train_window_cache,
        expected_train_window_manifest_sha256=expected_train_window_manifest_sha256,
        resume_checkpoint=resume_checkpoint,expected_resume_sha256=expected_resume_sha256,
        encoding_receipt=encoding_receipt,expected_encoding_receipt_sha256=expected_encoding_receipt_sha256,
        comparison_reference_file=comparison_reference_file,
        expected_comparison_reference_sha256=expected_comparison_reference_sha256,
        validation_batch_size=validation_batch_size)
