"""Probe CUDA Junyi đã được cấp quyền, kiểm cache và prediction batch thật."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback
import zipfile

ROOT = Path('/opt/kltn')
REQUEST = json.loads(Path('/opt/probe-request.json').read_text())
RUN = REQUEST['run_id']
assert REQUEST['status']=='USER_APPROVED' and REQUEST['approval_reference'].strip()
assert REQUEST['gpu'] in ('L4','T4') and REQUEST['authorized_batch_usd']<=.5
assert re.fullmatch(r'modal-junyi-optimization-'+REQUEST['gpu'].lower()+r'-[0-9]{8}-[0-9]{2}',RUN)
OPERATION = ROOT/'experiments/akt/results'/(RUN+'-operation')
OPERATION.mkdir(parents=True,exist_ok=False)
started = time.monotonic()


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def extract_pinned(archive):
    with zipfile.ZipFile(archive) as saved:
        pins = json.loads(saved.read('MANIFEST.json'))['files']
        assert len(saved.namelist())==len(set(saved.namelist()))
        for name,value in pins.items():
            assert not Path(name).is_absolute() and '..' not in Path(name).parts and ':' not in name and '\\' not in name
            raw = saved.read(name)
            digest = value if isinstance(value,str) else value['sha256']
            assert hashlib.sha256(raw).hexdigest()==digest
            path = ROOT/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(raw)


def verify_native_recovery(config, encoding, train_view, data, source_identity):
    """So hai đường continuous/resumed trên cùng source, model và sampler."""
    import gc
    import random
    from knowledge_tracing.akt.training import train_epoch, _seed
    from knowledge_tracing.akt.checkpoint import load_recovery_checkpoint
    from knowledge_tracing.akt.research_junyi_window_cache import JunyiWindowCacheSession
    session = JunyiWindowCacheSession(ROOT/data['train_window_cache'],view=train_view,encoding=encoding,
        source_data_sha256=source_identity,expected_target_rows=11833,
        expected_manifest_sha256=data['train_window_manifest_sha256'])
    identity = dict(kind='junyi_cuda_native_recovery_probe_v1',source_identity=source_identity,
        encoding_identity=encoding.identity,train_view=train_view.identity,seed=42)
    recovery_root = config.output_dir/'batch-recovery'
    recovery_root.mkdir(exist_ok=True)
    published = {}

    def publish(path):
        directory = config.output_dir/'checkpoints'/path.stem
        directory.mkdir(parents=True)
        os.link(path,directory/'state.pt')
        digest = sha(path)
        write_json(directory/'metadata.json',dict(checkpoint_sha256=digest,
            checkpoint_bytes=path.stat().st_size,identity=identity,scope='technical_recovery_probe'))
        write_json(directory/'COMPLETE.json',dict(checkpoint_sha256=digest,
            metadata_sha256=sha(directory/'metadata.json')))

    def new_model():
        _seed(42)
        with torch.device('cpu'):
            adapter = AKTAdapter(config,encoding.native)
        optimizer = torch.optim.Adam(adapter.native.parameters(),lr=config.lr,betas=config.betas,
            eps=config.eps,weight_decay=config.weight_decay,foreach=False,fused=False,capturable=False,
            differentiable=False,amsgrad=False,maximize=False,decoupled_weight_decay=False)
        return adapter,optimizer

    def clone_tree(value):
        if torch.is_tensor(value):
            return value.detach().cpu().clone()
        if isinstance(value,np.ndarray):
            return value.copy()
        if isinstance(value,dict):
            return {key:clone_tree(item) for key,item in value.items()}
        if isinstance(value,(tuple,list)):
            return type(value)(clone_tree(item) for item in value)
        return value

    def snapshot(adapter,optimizer):
        torch.cuda.synchronize()
        return clone_tree(dict(model=adapter.native.state_dict(),optimizer=optimizer.state_dict(),
            python_rng=random.getstate(),numpy_rng=np.random.get_state(),torch_cpu_rng=torch.get_rng_state(),
            cuda_rng=torch.cuda.get_rng_state_all()))

    def assert_same(left,right,path='state'):
        if torch.is_tensor(left):
            assert torch.is_tensor(right) and left.dtype==right.dtype and torch.equal(left,right),path
        elif isinstance(left,np.ndarray):
            assert isinstance(right,np.ndarray) and left.dtype==right.dtype and np.array_equal(left,right),path
        elif isinstance(left,dict):
            assert isinstance(right,dict) and left.keys()==right.keys(),path
            for key in left:
                assert_same(left[key],right[key],path+'.'+str(key))
        elif isinstance(left,(tuple,list)):
            assert type(left) is type(right) and len(left)==len(right),path
            for index,(a,b) in enumerate(zip(left,right)):
                assert_same(a,b,path+'.'+str(index))
        else:
            assert type(left) is type(right) and left==right,path

    def train(adapter,optimizer,label,max_steps,resume=None):
        def callback(path):
            publish(path)
            published[label] = path
        return train_epoch(adapter,session.iter_windows,optimizer=optimizer,epoch=1,
            budget=dict(max_steps=max_steps,max_targets=11833,max_seconds=100,
                max_rss_bytes=config.max_rss_bytes,min_available_ram_bytes=config.min_available_ram_bytes,
                phase=config.phase,run_id=config.run_id,resource_sample_limit=128,progress_resource_samples=False),
            recovery=dict(checkpoint_dir=recovery_root,identity=identity,prefix='probe-'+label,
                checkpoint_every_steps=40,resume_checkpoint=resume,checkpoint_callback=callback))

    adapter,optimizer = new_model()
    continuous = train(adapter,optimizer,'continuous',79)
    continuous_state = snapshot(adapter,optimizer)
    del adapter,optimizer
    gc.collect()
    torch.cuda.empty_cache()
    adapter,optimizer = new_model()
    partial = train(adapter,optimizer,'partial',40)
    assert partial.optimizer_steps==40 and partial.complete is False
    resume = published['partial']
    resume_sha = sha(resume)
    del adapter,optimizer
    gc.collect()
    torch.cuda.empty_cache()
    adapter,optimizer = new_model()
    resumed = train(adapter,optimizer,'resumed',79,resume=resume)
    resumed_state = snapshot(adapter,optimizer)
    assert_same(continuous_state,resumed_state)
    assert continuous.complete and resumed.complete
    assert continuous.optimizer_steps==resumed.optimizer_steps==79
    assert continuous.valid_targets==resumed.valid_targets==11833
    assert continuous.loss_sum==resumed.loss_sum
    final_samplers = []
    for label in ('continuous','resumed'):
        saved = load_recovery_checkpoint(published[label],expected_identity=identity,device='cpu')
        final_samplers.append(saved['resume_state']['sampler_state'])
        del saved
    assert final_samplers[0]==final_samplers[1] and final_samplers[0]['consumed_windows']==315
    session.assert_boundary()
    proof = dict(status='EXACT_NATIVE_CUDA_MODEL_ADAM_RNG_SAMPLER_RECOVERY_PASS',
        scope='technical_recovery_probe',source_identity=source_identity,encoding_identity=encoding.identity,
        resume_checkpoint_sha256=resume_sha,continuous_steps=79,partial_steps=40,resumed_new_steps=39,
        actual_optimizer_updates=158,actual_scored_target_exposures=23666,
        partial_scored_targets=partial.valid_targets,
        resumed_new_scored_targets=resumed.valid_targets-partial.valid_targets,
        completed_epoch_targets=11833,completed_epoch_windows=315,
        model_exact=True,optimizer_exact=True,all_rng_exact=True,sampler_exact=True,loss_sum_exact=True,
        sampler_prefix_sha256=final_samplers[0]['prefix_sha256'],loss_sum=continuous.loss_sum)
    write_json(OPERATION/'native-recovery-proof.json',proof)
    return proof


result = dict(status='FAILED',full_junyi_benchmark=False)
try:
    extract_pinned('/opt/kltn-input.zip')
    extract_pinned('/opt/junyi-data.zip')
    preflight = ROOT/'artifacts/akt/preflight'
    preflight.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile('/opt/cpu-gate.zip') as saved:
        for name,entry in json.loads(saved.read('SHA256.json')).items():
            raw = saved.read(name)
            assert hashlib.sha256(raw).hexdigest()==entry['sha256']
            if name.startswith('gate2-'):
                assert Path(name).name==name
                (preflight/name).write_bytes(raw)
    lock = ROOT/'artifacts/akt/runtime/modal-linux-cuda.lock.txt'
    lock.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile('/opt/locked-cu126.txt',lock)
    upstream = ROOT/'artifacts/akt/dependencies/upstream'
    os.environ.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_COUNT='3',
        GIT_CONFIG_KEY_0='core.fsmonitor',GIT_CONFIG_VALUE_0='false',
        GIT_CONFIG_KEY_1='safe.directory',GIT_CONFIG_VALUE_1=str(upstream),
        GIT_CONFIG_KEY_2='core.autocrlf',GIT_CONFIG_VALUE_2='false',
        GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__',
        CUDA_VISIBLE_DEVICES='0',CUBLAS_WORKSPACE_CONFIG=':4096:8',OMP_NUM_THREADS='2',
        MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
    runtime = preflight/(RUN+'-runtime.json')
    subprocess.run([sys.executable,'-I','-B',str(ROOT/'scripts/akt/check_runtime.py'),
        '--upstream',str(upstream),'--device','cuda','--lock-file',str(lock),'--output',str(runtime)],
        check=True,timeout=35)
    sys.path.insert(0,str(ROOT/'src'))
    import duckdb
    import numpy as np
    import pandas as pd
    import torch
    from knowledge_tracing.akt.config import AKTConfig,DataPaths,ResearchCUDAExecutionProfile
    from knowledge_tracing.akt.authorization import config_hash,require_gate2_evidence
    from knowledge_tracing.akt.research_junyi_engineering import prepare_inputs,write_json
    from knowledge_tracing.akt.research_junyi_selection import JunyiSelectedInputs,run_a0_junyi_selected,_identity
    from knowledge_tracing.akt.model import AKTAdapter
    from knowledge_tracing.akt.checkpoint import load_checkpoint
    from knowledge_tracing.akt.prediction import iter_predictions
    from knowledge_tracing.akt.prediction_batch import iter_predictions_batched
    from knowledge_tracing.gam_kt.evaluation import _metrics
    data = REQUEST['data']
    cohort = ROOT/data['cohort_root']
    roles = ROOT/data['roles_path']
    views,encoding,learners,_ = prepare_inputs(cohort,roles,
        cohort_sha256=data['cohort_manifest_sha256'],roles_sha256=data['roles_sha256'])
    frames = [dict(user_id=event.user_id,exercise=event.exercise,time_done=event.time_done,
                   source_row=event.source_row,correct=event.correct,suggested=event.suggested)
              for role in ('train','selection') for learner in learners[role] for event in learner.events]
    canonical = OPERATION/'canonical.parquet'
    assignments = OPERATION/'assignments.parquet'
    assignments_frame = pd.DataFrame([dict(user_id=learner.user_id,fold=learner.fold,partition='development')
        for role in ('train','selection') for learner in learners[role]])
    with duckdb.connect(config=dict(memory_limit='256MB',threads='1',temp_directory='')) as con:
        con.register('events',pd.DataFrame(frames))
        con.register('assignments',assignments_frame)
        con.execute('COPY events TO ? (FORMAT PARQUET, COMPRESSION ZSTD)',[str(canonical)])
        con.execute('COPY assignments TO ? (FORMAT PARQUET, COMPRESSION ZSTD)',[str(assignments)])
    paths = DataPaths(canonical,assignments,cohort/'manifest.json',roles)
    source_identity = _identity(dict(cache=data['cohort_manifest_sha256'],roles=data['roles_sha256']))
    inputs = JunyiSelectedInputs(paths,views['train'],views['selection'],11833,1530,source_identity)
    config = AKTConfig(phase='junyi-research',run_id=RUN,output_dir=ROOT/'experiments/akt/results'/RUN,
        execution_enabled=True,device='cuda',outer_fold=4,max_train_users=256,max_val_users=32,
        max_targets_per_side=11833,max_total_targets=59165,max_steps=395,max_seconds=300,max_wall_seconds=360,
        max_rss_bytes=6*1024**3,min_available_ram_bytes=256*1024**2)
    profile = ResearchCUDAExecutionProfile(2*1024**3)
    torch.set_num_threads(2)
    torch.set_default_dtype(torch.float32)
    torch.use_deterministic_algorithms(True,warn_only=False)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.set_float32_matmul_precision('highest')
    torch.cuda.set_per_process_memory_fraction(profile.max_vram_bytes/torch.cuda.get_device_properties(0).total_memory,0)
    gpu_name = torch.cuda.get_device_name(0)
    assert REQUEST['gpu'] in gpu_name
    gate = require_gate2_evidence(config,lock_file=lock)
    prepared = {key:data[key] for key in ('encoding_sha256','encoding_receipt_sha256','train_window_manifest_sha256')}
    grant = dict(status=REQUEST['status'],approval_reference=REQUEST['approval_reference'],
        purpose='bounded_engineering',workload_epochs=5,prepared_inputs=prepared,
        binding=dict(candidate_id='A0',phase='junyi_selected_only',config_sha256=config_hash(config),
            inputs_identity=inputs.identity,gate_sha256=gate['report_sha256'],runtime_sha256=sha(runtime)))
    authorization = OPERATION/'authorization.json'
    write_json(authorization,grant)
    write_json(OPERATION/'config.json',asdict(config))
    write_json(OPERATION/'preflight.json',dict(gpu_name=gpu_name,gate=gate,source_identity=source_identity,
        train_targets=11833,selection_targets=1530,full_junyi_benchmark=False))
    fit_started = time.monotonic()
    terminal = run_a0_junyi_selected(config,profile,inputs,authorization_file=authorization,
        expected_authorization_sha256=sha(authorization),runtime_report=runtime,lock_file=lock,
        encoding_file=ROOT/data['encoding_file'],expected_encoding_sha256=data['encoding_sha256'],
        encoding_receipt=ROOT/data['encoding_receipt'],expected_encoding_receipt_sha256=data['encoding_receipt_sha256'],
        train_window_cache=ROOT/data['train_window_cache'],
        expected_train_window_manifest_sha256=data['train_window_manifest_sha256'])
    fit_seconds = time.monotonic()-fit_started
    history = terminal['history']
    assert len(history)==5 or terminal['status']=='JUNYI_A0_SELECTED_ONLY_COMPLETE'
    assert history and len(history)<=5 and terminal['optimizer_steps']==79*len(history)
    assert terminal['trained_targets']==11833*len(history)
    latest = config.output_dir/'checkpoints'/f"epoch-{history[-1]['epoch']:03d}"
    metadata = json.loads((latest/'metadata.json').read_text())
    payload = load_checkpoint(latest/'state.pt',expected_identity=metadata['identity'],device='cuda')
    with torch.device('cpu'):
        adapter = AKTAdapter(config,encoding.native)
    adapter.native.load_state_dict(payload['model_state_dict'])
    del payload
    adapter.checkpoint_id = sha(latest/'state.pt')
    torch.cuda.synchronize()
    probe_started = time.monotonic()
    legacy = list(iter_predictions(adapter,learners['selection']))
    torch.cuda.synchronize()
    legacy_seconds = time.monotonic()-probe_started
    probe_started = time.monotonic()
    batched = list(iter_predictions_batched(adapter,learners['selection']))
    torch.cuda.synchronize()
    batched_seconds = time.monotonic()-probe_started
    assert len(legacy)==len(batched)==1530
    maximum_delta = 0.
    with (OPERATION/'batch-selection-predictions.jsonl').open('x') as stream:
        for before,after in zip(legacy,batched):
            left,right = asdict(before),asdict(after)
            p,q = left.pop('prediction'),right.pop('prediction')
            assert left==right and (p is None)==(q is None)
            if p is not None:
                maximum_delta = max(maximum_delta,abs(p-q))
            stream.write(json.dumps(asdict(after),allow_nan=False)+'\n')
    assert maximum_delta<=1e-6
    supported = [asdict(row) for row in batched if row.prediction is not None]
    assert len(supported)==1405
    del adapter
    recovery_proof = verify_native_recovery(config,encoding,views['train'],data,source_identity)
    assert terminal['optimizer_steps']+recovery_proof['actual_optimizer_updates']<=553
    assert terminal['trained_targets']+recovery_proof['actual_scored_target_exposures']<=82831
    result = dict(status='VERIFIED_JUNYI_OPTIMIZATION_PROBE',gpu=gpu_name,
        full_junyi_benchmark=False,selected_terminal=terminal,fit_seconds=fit_seconds,
        complete_training_epochs=len(history),optimizer_steps=terminal['optimizer_steps'],
        trained_targets=terminal['trained_targets'],selection_targets=1530,supported=1405,oov=125,
        legacy_prediction_seconds=legacy_seconds,batched_prediction_seconds=batched_seconds,
        max_probability_delta=maximum_delta,metadata_population_exact=True,
        supported_metrics=_metrics(pd.DataFrame(supported)),checkpoint_sha256=sha(latest/'state.pt'),
        native_recovery_proof=recovery_proof,
        total_actual_optimizer_updates=terminal['optimizer_steps']+158,
        total_actual_scored_target_exposures=terminal['trained_targets']+23666)
except BaseException as error:
    result.update(error_type=type(error).__name__,error=str(error))
    (OPERATION/'failure.log').write_text(traceback.format_exc())
finally:
    result['elapsed_seconds'] = time.monotonic()-started
    (OPERATION/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
raise SystemExit(0 if result['status']=='VERIFIED_JUNYI_OPTIMIZATION_PROBE' else 1)
