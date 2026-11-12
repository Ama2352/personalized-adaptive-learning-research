"""Chẩn đoán checkpoint Junyi đã có; lưu sai khác trước xét admission."""
from dataclasses import asdict,replace
import hashlib
import itertools
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

ROOT=Path('/opt/kltn')
REQUEST=json.loads(Path('/opt/probe-request.json').read_text())
RUN=REQUEST['run_id']
assert REQUEST['status']=='USER_APPROVED' and REQUEST['approval_reference'].strip()
assert REQUEST['gpu']=='T4' and REQUEST['authorized_batch_usd']<=.2
assert re.fullmatch(r'modal-junyi-numerical-t4-[0-9]{8}-[0-9]{2}',RUN)
OPERATION=ROOT/'experiments/akt/results'/(RUN+'-operation')
OPERATION.mkdir(parents=True,exist_ok=False)
started=time.monotonic()


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def extract_pinned(archive):
    with zipfile.ZipFile(archive) as saved:
        pins=json.loads(saved.read('MANIFEST.json'))['files']
        assert len(saved.namelist())==len(set(saved.namelist()))
        for name,value in pins.items():
            assert not Path(name).is_absolute() and '..' not in Path(name).parts and ':' not in name and '\\' not in name
            raw=saved.read(name)
            digest=value if isinstance(value,str) else value['sha256']
            assert hashlib.sha256(raw).hexdigest()==digest
            path=ROOT/name
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
    extract_pinned('/opt/checkpoint-debug.zip')
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
    from knowledge_tracing.akt.authorization import config_hash,require_gate2_evidence,preflight as check_preflight
    from knowledge_tracing.akt.research_junyi_engineering import prepare_inputs,write_json
    from knowledge_tracing.akt.research_junyi_selection import _identity
    from knowledge_tracing.akt.model import AKTAdapter
    from knowledge_tracing.akt.checkpoint import load_checkpoint
    from knowledge_tracing.akt.prediction import iter_predictions
    from knowledge_tracing.akt.prediction_batch import iter_predictions_batched
    from knowledge_tracing.gam_kt.evaluation import _metrics
    from knowledge_tracing.akt.windows import iter_windows
    from knowledge_tracing.akt.types import UnseenTarget
    data = REQUEST['data']
    cohort = ROOT/data['cohort_root']
    roles = ROOT/data['roles_path']
    views,encoding,learners,_ = prepare_inputs(cohort,roles,
        cohort_sha256=data['cohort_manifest_sha256'],roles_sha256=data['roles_sha256'])
    config = AKTConfig(phase='junyi-research',run_id=RUN,output_dir=ROOT/'experiments/akt/results'/RUN,
        execution_enabled=True,device='cuda',outer_fold=4,max_train_users=256,max_val_users=32,
        max_targets_per_side=11833,max_total_targets=59165,max_steps=395,max_seconds=300,max_wall_seconds=360,
        max_rss_bytes=6*1024**3,min_available_ram_bytes=256*1024**2)
    config.output_dir.mkdir(exist_ok=False)
    profile = ResearchCUDAExecutionProfile(2*1024**3)
    torch.set_num_threads(2)
    torch.set_default_dtype(torch.float32)
    torch.use_deterministic_algorithms(True,warn_only=False)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.set_float32_matmul_precision('highest')
    torch.cuda.set_per_process_memory_fraction(profile.max_vram_bytes/torch.cuda.get_device_properties(0).total_memory,0)
    assert 'T4' in torch.cuda.get_device_name(0)
    gate = require_gate2_evidence(config,lock_file=lock)
    check_preflight(config,runtime_report_path=runtime,lock_file=lock,cuda_profile=profile)
    from knowledge_tracing.akt.research_graph_model import _cuda_execution_check
    _cuda_execution_check(profile,synchronize=True)
    source_identity = _identity(dict(cache=data['cohort_manifest_sha256'],roles=data['roles_sha256']))
    state_path = ROOT/data['checkpoint_state']
    metadata_path = ROOT/data['checkpoint_metadata']
    metadata = json.loads(metadata_path.read_text())
    assert sha(state_path)==data['checkpoint_state_sha256']==metadata['checkpoint_sha256']
    payload = load_checkpoint(state_path,expected_identity=metadata['identity'],device='cuda')
    assert payload['encoding']['values']==list(encoding.native.vocabulary.values)
    assert payload['encoding']['train_support_students']==encoding.native.train_support_students
    old_config = metadata['identity']['config']
    for key in ('d_model','heads','blocks','d_ff','final_fc','dropout','context','target_block','max_length',
                'batch_size','n_pid','graph','source_commit','seed','kq_same','separate_qa'):
        assert old_config[key]==getattr(config,key),key
    with torch.device('cpu'):
        adapter = AKTAdapter(config,encoding.native)
    adapter.native.load_state_dict(payload['model_state_dict'])
    del payload
    adapter.checkpoint_id = sha(state_path)
    write_json(OPERATION/'checkpoint-reference.json',dict(checkpoint_sha256=adapter.checkpoint_id,
        checkpoint_origin_run=old_config['run_id'],metadata_sha256=sha(metadata_path),
        current_gate=gate,source_identity=source_identity,selected_retraining_updates=0))
    target_windows = {}
    known_windows = []
    for learner in learners['selection']:
        for window in iter_windows(learner,encoding.native,training=False):
            if isinstance(window,UnseenTarget):
                target_windows[window.event.source_row] = dict(window_length=None,local_index=None,
                    global_rank=window.global_rank,window_id=None,oov=True)
            else:
                known_windows.append(window)
                for local in np.flatnonzero(window.target_mask):
                    target_windows[int(window.inputs.source_rows[local])] = dict(
                        window_length=len(window.inputs.item_ids),local_index=int(local),
                        global_rank=int(window.global_ranks[local]),window_id=window.window_id,oov=False)
    torch.cuda.synchronize()
    prediction_started = time.monotonic()
    legacy = list(iter_predictions(adapter,learners['selection']))
    torch.cuda.synchronize()
    legacy_seconds = time.monotonic()-prediction_started
    prediction_started = time.monotonic()
    batched = list(iter_predictions_batched(adapter,learners['selection']))
    torch.cuda.synchronize()
    batch_seconds = time.monotonic()-prediction_started
    deltas = []
    metadata_mismatches = 0
    null_mismatches = 0
    with (OPERATION/'paired-predictions.jsonl').open('x') as stream:
        for index,(a,b) in enumerate(itertools.zip_longest(legacy,batched)):
            left = None if a is None else asdict(a)
            right = None if b is None else asdict(b)
            p = None if left is None else left['prediction']
            q = None if right is None else right['prediction']
            left_meta = None if left is None else {key:value for key,value in left.items() if key!='prediction'}
            right_meta = None if right is None else {key:value for key,value in right.items() if key!='prediction'}
            metadata_mismatches += int(left_meta!=right_meta)
            null_mismatches += int((p is None)!=(q is None))
            delta = None if p is None or q is None else abs(p-q)
            if delta is not None:
                deltas.append(delta)
            source_row = left['source_row'] if left is not None else right['source_row']
            stream.write(json.dumps(dict(index=index,legacy=left,batched=right,absolute_delta=delta,
                query_geometry=target_windows.get(source_row)),allow_nan=False)+'\n')
    maximum_delta = max(deltas,default=0.)
    batch_pass = (len(legacy)==len(batched)==1530 and metadata_mismatches==null_mismatches==0
                  and len(deltas)==1405 and maximum_delta<=1e-6)
    numerical = dict(status='NUMERICAL_COMPARISON_RECORDED',tolerance=1e-6,
        checkpoint_sha256=adapter.checkpoint_id,legacy_targets=len(legacy),batched_targets=len(batched),
        supported_pairs=len(deltas),metadata_mismatches=metadata_mismatches,null_mismatches=null_mismatches,
        max_probability_delta=maximum_delta,over_tolerance=sum(delta>1e-6 for delta in deltas),
        delta_quantiles=None if not deltas else np.quantile(deltas,[.5,.9,.99,1]).tolist(),
        legacy_seconds=legacy_seconds,batched_seconds=batch_seconds,batch_tolerance_pass=batch_pass)
    write_json(OPERATION/'numerical-summary.json',numerical)
    perturbations = []
    for window in sorted(known_windows,key=lambda item:(-len(item.inputs.item_ids),item.window_id)):
        size = len(window.inputs.item_ids)
        eligible = np.flatnonzero(window.target_mask & (np.arange(size)<size-2))
        if not len(eligible):
            continue
        query = int(eligible[len(eligible)//2])
        baseline = float(adapter.predict_window(window)[query])
        current_prior = window.inputs.prior_responses.copy()
        current_prior[query+1] = 1-current_prior[query+1]
        current_window = replace(window,inputs=replace(window.inputs,prior_responses=current_prior))
        current = float(adapter.predict_window(current_window)[query])
        future_prior = window.inputs.prior_responses.copy()
        future_prior[query+2:] = 1-future_prior[query+2:]
        future_items = window.inputs.item_ids.copy()
        future_items[query+1:] = (future_items[query+1:]+1)%len(encoding.native.vocabulary.values)
        future_window = replace(window,inputs=replace(window.inputs,prior_responses=future_prior,item_ids=future_items))
        future = float(adapter.predict_window(future_window)[query])
        perturbations.append(dict(window_id=window.window_id,window_length=size,local_index=query,
            global_rank=int(window.global_ranks[query]),source_row=int(window.inputs.source_rows[query]),
            baseline_probability=baseline,current_response_probability=current,future_probability=future,
            current_delta=abs(baseline-current),future_delta=abs(baseline-future)))
        if len(perturbations)>=20:
            break
    causal_pass = bool(perturbations) and all(max(row['current_delta'],row['future_delta'])<=1e-6 for row in perturbations)
    write_json(OPERATION/'causal-perturbation.json',dict(tolerance=1e-6,passed=causal_pass,queries=perturbations))
    del adapter
    # Proof chạy độc lập sau khi đã giữ đầy đủ mọi sai khác số học.
    recovery_proof = verify_native_recovery(config,encoding,views['train'],data,source_identity)
    result = dict(status='DIAGNOSTIC_COMPLETE_BATCH_TOLERANCE_PASS' if batch_pass and causal_pass
                      else 'DIAGNOSTIC_COMPLETE_NOT_BATCH_ADMISSION',
        batch_admitted=batch_pass and causal_pass,selected_retraining_updates=0,
        checkpoint_sha256=data['checkpoint_state_sha256'],numerical_comparison=numerical,
        causal_invariance_pass=causal_pass,native_recovery_proof=recovery_proof,
        technical_optimizer_updates=158,technical_scored_target_exposures=23666,
        full_junyi_benchmark=False)
except BaseException as error:
    result.update(error_type=type(error).__name__,error=str(error))
    (OPERATION/'failure.log').write_text(traceback.format_exc())
finally:
    result['elapsed_seconds'] = time.monotonic()-started
    (OPERATION/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
raise SystemExit(0 if result['status'].startswith('DIAGNOSTIC_COMPLETE_') else 1)
