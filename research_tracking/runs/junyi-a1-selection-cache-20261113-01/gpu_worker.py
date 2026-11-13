"""Full Junyi A1 expert selected-only trên TRAIN80/selection10 đã ghim."""
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
RUN = REQUEST['run_id']
OPERATION = ROOT/'experiments/akt/results'/(RUN+'-operation')
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


result = dict(status='FAILED',scope='full_junyi_a1_expert_selected_only',refit_completed=False,calibration_completed=False)
signal.signal(signal.SIGALRM,timeout)
signal.alarm(1800)
try:
    assert REQUEST['status']=='USER_APPROVED' and REQUEST['gpu']=='H100'
    assert REQUEST['max_optimizer_steps']==36360 and REQUEST['max_total_training_targets']==266946620
    extract('/opt/kltn-input.zip')
    extract('/opt/junyi-data.zip')
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
        check=True,timeout=120)
    sys.path.insert(0,str(ROOT/'src'))
    import torch
    from knowledge_tracing.akt.config import AKTConfig,ResearchCUDAExecutionProfile
    from knowledge_tracing.akt.authorization import require_gate2_evidence,preflight,config_hash
    from knowledge_tracing.akt.research_graph_model import _cuda_execution_check
    from knowledge_tracing.akt.research_junyi_selection import load_full_selected_cache,run_junyi_selected
    torch.set_num_threads(2)
    torch.set_default_dtype(torch.float32)
    torch.use_deterministic_algorithms(True,warn_only=False)
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    torch.backends.cudnn.benchmark=False
    torch.set_float32_matmul_precision('highest')
    profile=ResearchCUDAExecutionProfile(16*1024**3,recipe_id='cgakt-cuda-fp32-batch128-v2')
    torch.cuda.set_per_process_memory_fraction(profile.max_vram_bytes/torch.cuda.get_device_properties(0).total_memory,0)
    assert any(gpu in torch.cuda.get_device_name(0) for gpu in ('H100','H200'))
    time_left=REQUEST['local_deadline_unix']-time.time()
    assert time_left>240,'Chưa đủ thời gian cấp checkpoint an toàn, không bắt đầu fit'
    source_config=json.loads(Path('/opt/actual-checkpoint-cpu-parity.json').read_text())['source_identity']['config']
    source_config.update(project_root=ROOT,source_root=ROOT/'artifacts/akt/dependencies/upstream',
        output_dir=ROOT/'experiments/akt/results'/RUN,run_id=RUN)
    source_config['betas']=tuple(source_config['betas'])
    config=AKTConfig(**source_config)
    assert config.max_seconds==1500 and config.max_wall_seconds==1600
    gate=require_gate2_evidence(config,lock_file=lock)
    preflight(config,runtime_report_path=runtime,lock_file=lock,cuda_profile=profile)
    data=REQUEST['inputs']
    inputs=load_full_selected_cache(ROOT/data['selected_cache_root'],ROOT/data['roles_path'],
        expected_manifest_sha256=data['selected_cache_manifest_sha256'],expected_roles_sha256=data['roles_sha256'])
    assert inputs.train_targets==13347331 and inputs.selection_targets==1600343
    assert inputs.train.full_role_coverage and inputs.selection.full_role_coverage
    from knowledge_tracing.akt.research_junyi_data import load_prepared_junyi_encoding
    from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition
    from knowledge_tracing.shared_kt import PrerequisiteGraph
    encoding=load_prepared_junyi_encoding(ROOT/data['encoding_file'],ROOT/data['encoding_receipt'],
        view=inputs.train,source_data_sha256=inputs.source_identity,
        expected_file_sha256=data['encoding_sha256'],expected_receipt_sha256=data['encoding_receipt_sha256'])
    graph_path=ROOT/REQUEST['graph_file']
    assert sha(graph_path)==REQUEST['graph_sha256']
    topology=json.loads(graph_path.read_text())
    condition=JunyiGraphCondition(encoding,
        PrerequisiteGraph.from_edges(topology['nodes'],topology['corrected_edges']),sha(graph_path))
    reference_path=ROOT/REQUEST['comparison_reference_file']
    assert sha(reference_path)==REQUEST['comparison_reference_sha256']
    assert REQUEST['validation_implementation']=='batched_windows_v1_batch128'
    original_reference_sha256=sha(reference_path)
    reference_path=Path('/opt/a0-reused-reference.json')
    replay_path=Path('/opt/a0-reused-replay.json')
    assert sha(reference_path)==REQUEST['reused_a0_reference_sha256']
    assert sha(replay_path)==REQUEST['reused_a0_replay_sha256']
    replay_receipt=json.loads(replay_path.read_text())
    assert replay_receipt['status']=='PASS_SELECTED_A0_CHECKPOINT_BATCH128'
    assert replay_receipt['results'][0]['metrics']['targets']==inputs.selection_targets
    assert replay_receipt['results'][0]['absolute_log_loss_delta']==0
    reused_reference=json.loads(reference_path.read_text())
    assert reused_reference['validation_batch_replay']['original_reference_sha256']==original_reference_sha256
    assert reused_reference['validation_batch_replay']['evidence_sha256']==sha(replay_path)
    shutil.copyfile(replay_path,OPERATION/'a0-validation-replay.json')
    shutil.copyfile(reference_path,OPERATION/'a0-batched-comparison-reference.json')
    effective_reference_sha256=sha(reference_path)
    checkpoint=ROOT/REQUEST['resume_checkpoint']
    assert sha(checkpoint)==REQUEST['resume_checkpoint_sha256']
    canary=ROOT/'research_tracking/runs/junyi-a1-selection-cache-20261113-01/check_actual_checkpoint.py'
    with (OPERATION/'actual-checkpoint-cuda.log').open('x') as log:
        proof=subprocess.run([sys.executable,'-B',str(canary),'--device','cuda',
            '--output-name','actual-checkpoint-gpu-parity.json','--shard-index',
            str(json.loads(Path('/opt/actual-checkpoint-cpu-parity.json').read_text())['shard_index'])],cwd=ROOT,
            stdout=log,stderr=subprocess.STDOUT,timeout=180)
    proof_file=canary.parent/'actual-checkpoint-gpu-parity.json'
    assert proof.returncode==0 and proof_file.is_file(),'Actual checkpoint CUDA canary failed'
    proof_result=json.loads(proof_file.read_text())
    assert proof_result['status']=='PASS_ACTUAL_CHECKPOINT_CUDA_SOURCE2_COMPACT_EXACT'
    assert proof_result['max_absolute_drift']==0 and all(proof_result['checks'].values())
    shutil.copyfile(proof_file,OPERATION/proof_file.name)
    from knowledge_tracing.akt.research_junyi_transition import identity_sha256
    target_identity=json.loads(json.dumps(proof_result['source_identity']))
    target_identity['config']=json.loads(json.dumps(asdict(config),default=str))
    build=json.loads(Path(gate['evidence_path']).read_text())['build_hashes']
    target_identity['source_build_sha256']=identity_sha256(build)
    target_identity['batch_factory'].update(context_backend='compact-a1-v1',graph_context_cache=None)
    target_identity.update(prefetch_train_windows=True,prefetch_selection_windows=True)
    assert target_identity['profile']==asdict(profile)
    transition_file=OPERATION/'source-transition-receipt.json'
    evidence=dict(status='PASS_ACTUAL_CHECKPOINT_PARITY',checkpoint_sha256=sha(checkpoint),
        source_identity_sha256=identity_sha256(proof_result['source_identity']),
        target_identity_sha256=identity_sha256(target_identity),max_absolute_drift=0.,checks=proof_result['checks'])
    write(transition_file,dict(source_identity=proof_result['source_identity'],evidence=evidence))
    prepared=dict(encoding_sha256=data['encoding_sha256'],encoding_receipt_sha256=data['encoding_receipt_sha256'],
                  train_window_manifest_sha256=data['train_window_manifest_sha256'],
                  graph_condition_sha256=condition.identity,
                  comparison_reference_sha256=effective_reference_sha256,validation_batch_size=128)
    prepared.update(resume_checkpoint_sha256=sha(checkpoint),source_transition_sha256=sha(transition_file),
        prefetch_train_windows=True,prefetch_selection_windows=True)
    grant=dict(status='USER_APPROVED',approval_reference=REQUEST['approval_reference'],purpose='main_selected',
        workload_epochs=20,prepared_inputs=prepared,binding=dict(candidate_id='A1_EXPERT',phase='junyi_selected_only',
            config_sha256=config_hash(config),inputs_identity=inputs.identity,
            gate_sha256=gate['report_sha256'],runtime_sha256=sha(runtime)))
    write(OPERATION/'config.json',asdict(config))
    write(OPERATION/'cuda-profile.json',asdict(profile))
    write(OPERATION/'authorization.json',grant)
    write(OPERATION/'input-admission.json',dict(identity=inputs.identity,train_targets=inputs.train_targets,
        selection_targets=inputs.selection_targets,full_train=True,full_selection=True,gate=gate))
    _cuda_execution_check(profile,synchronize=True)
    import threading
    import csv
    stop_telemetry = threading.Event()
    telemetry_errors = []
    def sample_gpu():
        try:
            with (OPERATION/'gpu-telemetry.jsonl').open('x') as log:
                while not stop_telemetry.is_set():
                    query=subprocess.run(['nvidia-smi',
                        '--query-gpu=name,utilization.gpu,memory.used,memory.total,power.draw',
                        '--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=5)
                    values=next(csv.reader(query.stdout.splitlines()))
                    log.write(json.dumps(dict(at_monotonic=time.monotonic(),gpu_name=values[0].strip(),
                        gpu_utilization=float(values[1]),vram_used_mib=float(values[2]),
                        vram_total_mib=float(values[3]),power_w=float(values[4])))+'\n')
                    log.flush()
                    stop_telemetry.wait(2)
        except Exception as error:
            telemetry_errors.append(str(error))
    sampler=threading.Thread(target=sample_gpu,daemon=True)
    sampler.start()
    terminal=run_junyi_selected(config,profile,inputs,authorization_file=OPERATION/'authorization.json',
        expected_authorization_sha256=sha(OPERATION/'authorization.json'),runtime_report=runtime,lock_file=lock,
        encoding_file=ROOT/data['encoding_file'],expected_encoding_sha256=data['encoding_sha256'],
        encoding_receipt=ROOT/data['encoding_receipt'],expected_encoding_receipt_sha256=data['encoding_receipt_sha256'],
        train_window_cache=ROOT/data['train_window_cache'],
        expected_train_window_manifest_sha256=data['train_window_manifest_sha256'],
        resume_checkpoint=checkpoint,expected_resume_sha256=sha(checkpoint),
        source_transition_file=transition_file,expected_source_transition_sha256=sha(transition_file),
        prefetch_train_windows=True,prefetch_selection_windows=True,
        graph_condition=condition,comparison_reference_file=reference_path,
        expected_comparison_reference_sha256=effective_reference_sha256,validation_batch_size=128)
    stop_telemetry.set()
    sampler.join(timeout=6)
    assert not telemetry_errors,telemetry_errors
    assert terminal['status'] in ('PARTIAL_SELECTED_ONLY_NOT_FINAL','JUNYI_A0_SELECTED_ONLY_COMPLETE','JUNYI_A1_SELECTED_ONLY_COMPLETE')
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
raise SystemExit(0 if result['status'] in ('PARTIAL_SELECTED_ONLY_NOT_FINAL','JUNYI_A0_SELECTED_ONLY_COMPLETE','JUNYI_A1_SELECTED_ONLY_COMPLETE') else 1)
