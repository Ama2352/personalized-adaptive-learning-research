"""Full Junyi A0 selected-only trên TRAIN80/selection10 đã ghim."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import traceback
import zipfile

ROOT = Path('/opt/kltn')
REQUEST = json.loads(Path('/opt/probe-request.json').read_text())
EXECUTION = REQUEST['run_id']
RUN = REQUEST['logical_run_id']
OPERATION = ROOT/'experiments/akt/results'/(EXECUTION+'-operation')
OPERATION.mkdir(parents=True,exist_ok=False)
started = time.monotonic()


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2,default=str,allow_nan=False)
        stream.write('\n')


def extract(archive):
    with zipfile.ZipFile(archive) as saved:
        pins = json.loads(saved.read('MANIFEST.json'))['files']
        assert set(saved.namelist())==set(pins)|{'MANIFEST.json'}
        for name,pin in pins.items():
            assert not Path(name).is_absolute() and '..' not in Path(name).parts and ':' not in name and '\\' not in name
            raw = saved.read(name)
            assert hashlib.sha256(raw).hexdigest()==(pin if isinstance(pin,str) else pin['sha256'])
            path = ROOT/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(raw)


def timeout(_signum,_frame):
    raise TimeoutError('Full Junyi worker backup deadline3000s')


result = dict(status='FAILED',scope='full_junyi_a0_selected_only',refit_completed=False,calibration_completed=False)
signal.signal(signal.SIGALRM,timeout)
signal.alarm(3000)
try:
    assert REQUEST['status']=='USER_APPROVED' and REQUEST['gpu']=='T4'
    assert REQUEST['max_optimizer_steps']==1163320 and REQUEST['max_total_training_targets']==266946620
    extract('/opt/kltn-input.zip')
    extract('/opt/junyi-data.zip')
    extract('/opt/resume-control.zip')
    preflight_dir = ROOT/'artifacts/akt/preflight'
    preflight_dir.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile('/opt/cpu-gate.zip') as saved:
        for name,pin in json.loads(saved.read('SHA256.json')).items():
            raw=saved.read(name)
            assert hashlib.sha256(raw).hexdigest()==pin['sha256']
            if name.startswith('gate2-'):
                assert Path(name).name==name
                (preflight_dir/name).write_bytes(raw)
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
    runtime = preflight_dir/(RUN+'-runtime.json')
    subprocess.run([sys.executable,'-I','-B',str(ROOT/'scripts/akt/check_runtime.py'),
        '--upstream',str(upstream),'--device','cuda','--lock-file',str(lock),'--output',str(runtime)],
        check=True,timeout=35)
    sys.path.insert(0,str(ROOT/'src'))
    import torch
    from knowledge_tracing.akt.config import AKTConfig,ResearchCUDAExecutionProfile
    from knowledge_tracing.akt.authorization import require_gate2_evidence,preflight,config_hash
    from knowledge_tracing.akt.research_graph_model import _cuda_execution_check
    from knowledge_tracing.akt.research_junyi_selection import load_full_selected_cache,run_a0_junyi_selected
    torch.set_num_threads(2)
    torch.set_default_dtype(torch.float32)
    torch.use_deterministic_algorithms(True,warn_only=False)
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    torch.backends.cudnn.benchmark=False
    torch.set_float32_matmul_precision('highest')
    profile=ResearchCUDAExecutionProfile(2*1024**3)
    torch.cuda.set_per_process_memory_fraction(profile.max_vram_bytes/torch.cuda.get_device_properties(0).total_memory,0)
    assert 'T4' in torch.cuda.get_device_name(0)
    config=AKTConfig(phase='junyi-research',run_id=RUN,output_dir=ROOT/'experiments/akt/results'/RUN,
        execution_enabled=True,device='cuda',outer_fold=4,max_train_users=126774,max_val_users=15847,
        max_targets_per_side=13347331,max_total_targets=266946620,max_steps=1163320,
        max_seconds=2600,max_wall_seconds=2700,max_rss_bytes=6*1024**3,min_available_ram_bytes=256*1024**2)
    gate=require_gate2_evidence(config,lock_file=lock)
    preflight(config,runtime_report_path=runtime,lock_file=lock,cuda_profile=profile)
    data=REQUEST['inputs']
    inputs=load_full_selected_cache(ROOT/data['selected_cache_root'],ROOT/data['roles_path'],
        expected_manifest_sha256=data['selected_cache_manifest_sha256'],expected_roles_sha256=data['roles_sha256'])
    assert inputs.train_targets==13347331 and inputs.selection_targets==1600343
    assert inputs.train.full_role_coverage and inputs.selection.full_role_coverage
    logical_output = config.output_dir
    assert (logical_output/'run-manifest.json').is_file()
    assert not (logical_output/'COMPLETE.json').exists()
    logical_identity = json.loads((logical_output/'run-manifest.json').read_text())
    previous_execution = REQUEST['resume_from_execution_id']
    assert previous_execution.replace('-','').isalnum()
    selected_checkpoint = None
    for envelope in REQUEST['resume_checkpoints']:
        name = envelope['name']
        assert Path(name).name==name and name not in ('.','..')
        source = Path('/durable')/previous_execution/'checkpoints'/name
        destination = logical_output/'checkpoints'/name
        destination.mkdir(parents=True,exist_ok=False)
        for filename in ('state.pt','metadata.json','COMPLETE.json'):
            expected = envelope['files'][filename]
            original = source/filename
            assert original.stat().st_size==expected['bytes'] and sha(original)==expected['sha256']
            shutil.copyfile(original,destination/filename)
            assert sha(destination/filename)==expected['sha256']
        metadata = json.loads((destination/'metadata.json').read_text())
        assert metadata['identity']==logical_identity
        if name==REQUEST['resume_checkpoint_name']:
            selected_checkpoint = destination/'state.pt'
    assert selected_checkpoint is not None
    if 'batch-epoch-' in REQUEST['resume_checkpoint_name']:
        raw_checkpoint=logical_output/'batch-recovery'/(REQUEST['resume_checkpoint_name']+'.pt')
        raw_checkpoint.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(selected_checkpoint,raw_checkpoint)
        assert sha(raw_checkpoint)==sha(selected_checkpoint)
        selected_checkpoint=raw_checkpoint
    resume_sha = sha(selected_checkpoint)
    assert resume_sha==REQUEST['resume_checkpoint_sha256']
    from knowledge_tracing.akt.checkpoint import load_training_snapshot
    payload=load_training_snapshot(selected_checkpoint,expected_identity=logical_identity,device='cpu')
    write(OPERATION/'recovered-state-admission.json',dict(
        checkpoint_sha256=resume_sha,checkpoint_kind=payload.get('checkpoint_kind','complete_epoch'),
        progress=payload['progress'],
        resume_epoch=payload.get('resume_state',{}).get('epoch'),
        resume_optimizer_steps=payload.get('resume_state',{}).get('optimizer_steps'),
        restored_target_rows=payload.get('resume_state',{}).get('trainer_state',{}).get('stats',{}).get('valid_targets')))
    del payload
    initial_path=logical_output/'initial-backbone.json'
    if not initial_path.exists():
        reconstruction=REQUEST.get('control_reconstruction',{})
        assert reconstruction.get('kind')=='RECONSTRUCTED_FROM_PINNED_SOURCE_AND_CHECKPOINT'
        assert reconstruction.get('initial_backbone_missing') is True
        from knowledge_tracing.akt.training import _seed
        from knowledge_tracing.akt.model import AKTAdapter
        from knowledge_tracing.akt.encoding import load_encoding
        from knowledge_tracing.akt.research_runner import _state_hash
        import gc
        _seed(42)
        with torch.device('cpu'):
            initial_adapter=AKTAdapter(config,load_encoding(ROOT/data['encoding_file']))
        initial_hash=_state_hash(initial_adapter)
        del initial_adapter
        gc.collect()
        torch.cuda.empty_cache()
        write(initial_path,dict(sha256=initial_hash,seed=42,
            encoding_identity=logical_identity['encoding'],
            reconstruction='RECONSTRUCTED_FROM_PINNED_SOURCE_AND_CHECKPOINT',
            historical_initial_hash_comparison_available=False))
        write(OPERATION/'control-reconstruction.json',dict(reconstruction,
            derived_initial_backbone_sha256=initial_hash,training_updates_for_reconstruction=0))
    # Driver chỉ xác nhận sau khi commit controls lên Volume hoàn tất.
    control_wait_started=time.monotonic()
    while not (OPERATION/'control-durable-ack.json').is_file():
        assert time.monotonic()-control_wait_started<60,'Durable control publication deadline'
        time.sleep(.2)
    prepared=dict(encoding_sha256=data['encoding_sha256'],encoding_receipt_sha256=data['encoding_receipt_sha256'],
                  train_window_manifest_sha256=data['train_window_manifest_sha256'])
    prepared['resume_checkpoint_sha256']=resume_sha
    grant=dict(status='USER_APPROVED',approval_reference=REQUEST['approval_reference'],purpose='main_selected',
        workload_epochs=20,prepared_inputs=prepared,binding=dict(candidate_id='A0',phase='junyi_selected_only',
            config_sha256=config_hash(config),inputs_identity=inputs.identity,
            gate_sha256=gate['report_sha256'],runtime_sha256=sha(runtime)))
    write(OPERATION/'config.json',asdict(config))
    write(OPERATION/'cuda-profile.json',asdict(profile))
    write(OPERATION/'authorization.json',grant)
    write(OPERATION/'input-admission.json',dict(identity=inputs.identity,train_targets=inputs.train_targets,
        selection_targets=inputs.selection_targets,full_train=True,full_selection=True,gate=gate))
    _cuda_execution_check(profile,synchronize=True)
    terminal=run_a0_junyi_selected(config,profile,inputs,authorization_file=OPERATION/'authorization.json',
        expected_authorization_sha256=sha(OPERATION/'authorization.json'),runtime_report=runtime,lock_file=lock,
        encoding_file=ROOT/data['encoding_file'],expected_encoding_sha256=data['encoding_sha256'],
        encoding_receipt=ROOT/data['encoding_receipt'],expected_encoding_receipt_sha256=data['encoding_receipt_sha256'],
        train_window_cache=ROOT/data['train_window_cache'],
        expected_train_window_manifest_sha256=data['train_window_manifest_sha256'],
        resume_checkpoint=selected_checkpoint,expected_resume_sha256=resume_sha)
    assert terminal['status'] in ('PARTIAL_SELECTED_ONLY_NOT_FINAL','JUNYI_A0_SELECTED_ONLY_COMPLETE')
    result.update(status=terminal['status'],terminal=terminal,gpu=torch.cuda.get_device_name(0),
        resource=_cuda_execution_check(profile,synchronize=True))
except BaseException as error:
    result.update(error_type=type(error).__name__,error=str(error))
    (OPERATION/'failure.log').write_text(traceback.format_exc())
finally:
    signal.alarm(0)
    result['elapsed_seconds']=time.monotonic()-started
    write(OPERATION/'result.json',result)
print(json.dumps(result,allow_nan=False),flush=True)
raise SystemExit(0 if result['status'] in ('PARTIAL_SELECTED_ONLY_NOT_FINAL','JUNYI_A0_SELECTED_ONLY_COMPLETE') else 1)
