"""Profile batch shape trên cùng packet Junyi, tách khỏi selected training."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback
import zipfile

ROOT = Path('/opt/kltn')
REQUEST = json.loads(Path('/opt/probe-request.json').read_text())
RUN = REQUEST['run_id']
OUTPUT = ROOT/'experiments/akt/results'/RUN
OPERATION = ROOT/'experiments/akt/results'/(RUN+'-operation')
OUTPUT.mkdir(parents=True,exist_ok=False)
OPERATION.mkdir(parents=True,exist_ok=False)
started = time.monotonic()


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def extract(archive):
    with zipfile.ZipFile(archive) as saved:
        pins = json.loads(saved.read('MANIFEST.json'))['files']
        assert set(saved.namelist())==set(pins)|{'MANIFEST.json'}
        for name,pin in pins.items():
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
            assert ':' not in name and '\\' not in name
            raw = saved.read(name)
            expected = pin if isinstance(pin,str) else pin['sha256']
            assert hashlib.sha256(raw).hexdigest()==expected
            path = ROOT/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(raw)


result = dict(status='FAILED',scope='engineering_batch32_utilization_only',full_junyi_epoch=False)
try:
    assert REQUEST['status']=='USER_APPROVED' and REQUEST['gpu']=='T4'
    assert REQUEST['max_optimizer_steps']==770 and REQUEST['expected_targets']==56332
    extract('/opt/kltn-input.zip')
    extract('/opt/junyi-data.zip')
    preflight = ROOT/'artifacts/akt/preflight'
    preflight.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile('/opt/cpu-gate.zip') as saved:
        for name,pin in json.loads(saved.read('SHA256.json')).items():
            raw = saved.read(name)
            assert hashlib.sha256(raw).hexdigest()==pin['sha256']
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
        CUBLAS_WORKSPACE_CONFIG=':4096:8',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',
        OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
    runtime = preflight/(RUN+'-runtime.json')
    subprocess.run([sys.executable,'-I','-B',str(ROOT/'scripts/akt/check_runtime.py'),
        '--upstream',str(upstream),'--device','cuda','--lock-file',str(lock),'--output',str(runtime)],
        check=True,timeout=120)
    sys.path.insert(0,str(ROOT/'src'))
    sys.path.insert(0,'/opt')
    import numpy as np
    import torch
    from packet_reader import JunyiTrainingPacket
    from knowledge_tracing.akt.config import AKTConfig, ResearchCUDAExecutionProfile
    from knowledge_tracing.akt.model import AKTAdapter
    from knowledge_tracing.akt.training import train_epoch, _seed
    from knowledge_tracing.akt.checkpoint import save_checkpoint, load_checkpoint
    from knowledge_tracing.akt.authorization import require_gate2_evidence, preflight as check_preflight
    from knowledge_tracing.akt.research_graph_model import _cuda_execution_check

    torch.set_num_threads(2)
    torch.set_default_dtype(torch.float32)
    torch.use_deterministic_algorithms(True,warn_only=False)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.set_float32_matmul_precision('highest')
    profile = ResearchCUDAExecutionProfile(2*1024**3)
    torch.cuda.set_per_process_memory_fraction(profile.max_vram_bytes/torch.cuda.get_device_properties(0).total_memory,0)
    assert 'T4' in torch.cuda.get_device_name(0)
    from knowledge_tracing.akt.tensors import collate_windows
    from knowledge_tracing.akt.checkpoint import restore_checkpoint
    from knowledge_tracing.akt.research_runner import _state_hash
    from knowledge_tracing.akt.sampler import iter_shuffled_windows
    from knowledge_tracing.akt.resources import memory_snapshot
    import gc
    import math

    assert REQUEST['actual_benchmark_batch_sizes']==[32]
    assert REQUEST['reference_config_batch_size']==4 and REQUEST['max_target_exposures']==1358368
    config = AKTConfig(phase='junyi-research',run_id=RUN,output_dir=OUTPUT,
        execution_enabled=True,device='cuda',outer_fold=4,max_train_users=126774,
        max_val_users=15847,max_targets_per_side=13347331,max_total_targets=1358368,
        max_steps=770,max_seconds=320,max_wall_seconds=360,max_rss_bytes=6*1024**3,
        min_available_ram_bytes=256*1024**2)
    gate = require_gate2_evidence(config,lock_file=lock)
    check_preflight(config,runtime_report_path=runtime,lock_file=lock,cuda_profile=profile)
    packet = JunyiTrainingPacket(ROOT/REQUEST['packet_root'],expected_packet_sha256=REQUEST['packet_sha256'])
    records = list(packet.iter_training_windows())
    shuffled = tuple(iter_shuffled_windows(lambda:iter(records),seed=43))
    assert len(shuffled)==1024 and sum(int(row.window.target_mask.sum()) for row in shuffled)==56332
    encoding = packet.encoding.native
    assert len(encoding.vocabulary.values)==717 and config.batch_size==4
    order_sha = hashlib.sha256(json.dumps([row.window.window_id for row in shuffled],separators=(',', ':')).encode()).hexdigest()
    write_json(OPERATION/'packet-admission.json',dict(audit=packet.expected,packet_sha256=packet.identity,
        shuffled_window_order_sha256=order_sha,shuffle_seed=43,full_role_coverage=False))
    write_json(OUTPUT/'run-manifest.json',dict(scope='engineering_batch32_utilization_only',
        config=json.loads(json.dumps(asdict(config),default=str)),cuda_profile=asdict(profile),
        actual_benchmark_batch_sizes=[32],packet_sha256=packet.identity,
        shuffled_window_order_sha256=order_sha,main_selected_fit=False,reference_config_batch_size=4))

    def fresh():
        _seed(42)
        with torch.device('cpu'):
            adapter = AKTAdapter(config,encoding)
        optimizer = torch.optim.Adam(adapter.native.parameters(),lr=config.lr,betas=config.betas,
            eps=config.eps,weight_decay=config.weight_decay,foreach=False,fused=False,capturable=False,
            differentiable=False,amsgrad=False,maximize=False,decoupled_weight_decay=False)
        return adapter,optimizer

    import copy
    import csv
    import threading
    adapter,optimizer = fresh()
    initial_hash = _state_hash(adapter)
    phase = dict(name='warmup',packet_pass=0)
    stop = threading.Event()
    telemetry_errors = []
    def sample_gpu():
        try:
            with (OPERATION/'gpu-telemetry.jsonl').open('x') as stream:
                while not stop.is_set():
                    observed_phase = dict(phase)
                    query = subprocess.run(['nvidia-smi',
                        '--query-gpu=utilization.gpu,memory.used,memory.total,power.draw,clocks.sm,pstate',
                        '--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=4)
                    values = next(csv.reader(query.stdout.splitlines()))
                    stream.write(json.dumps(dict(at_monotonic=time.monotonic(),phase=observed_phase,
                        gpu_utilization=float(values[0]),vram_used_mib=float(values[1]),
                        vram_total_mib=float(values[2]),power_w=float(values[3]),
                        sm_clock_mhz=float(values[4]),pstate=values[5].strip()))+'\n')
                    stream.flush()
                    stop.wait(.5)
        except Exception as error:
            telemetry_errors.append(str(error))
    sampler = threading.Thread(target=sample_gpu,daemon=True)
    sampler.start()
    torch.cuda.reset_peak_memory_stats()
    torch.cuda.synchronize()
    total_targets = total_steps = 0
    passes = []
    for packet_pass in range(24):
        phase.update(name='warmup' if packet_pass==0 else 'stable_training',packet_pass=packet_pass)
        torch.cuda.synchronize()
        pass_started = time.monotonic()
        loss_sum = 0.
        pass_targets = 0
        for offset in range(0,len(shuffled),32):
            assert time.monotonic()-started<320,'Worker deadline'
            group = shuffled[offset:offset+32]
            batch = collate_windows([entry.window for entry in group],n_items=717,device='cuda',
                                    targets=[entry.targets for entry in group])
            metrics = adapter.step(batch,optimizer)
            assert metrics['stepped'] and metrics['valid_targets']==sum(int(e.window.target_mask.sum()) for e in group)
            assert math.isfinite(metrics['loss_sum']) and math.isfinite(metrics['pre_clip_norm'])
            loss_sum += metrics['loss_sum']
            pass_targets += metrics['valid_targets']
            total_steps += 1
            resource = memory_snapshot()
            assert resource['process_rss_bytes']<=6*1024**3
        torch.cuda.synchronize()
        elapsed = time.monotonic()-pass_started
        assert pass_targets==56332
        total_targets += pass_targets
        passes.append(dict(packet_pass=packet_pass,phase=phase['name'],seconds=elapsed,
            scored_targets=pass_targets,targets_per_second=pass_targets/elapsed,
            mean_training_loss=loss_sum/pass_targets,optimizer_steps=32))
        write_json(OPERATION/'progress.json',dict(passes=passes,total_steps=total_steps,total_targets=total_targets))
    phase.update(name='checkpoint',packet_pass=24)
    stop.set()
    sampler.join(timeout=5)
    assert not sampler.is_alive() and not telemetry_errors,telemetry_errors
    assert total_steps==768 and total_targets==1351968
    resource = _cuda_execution_check(profile,synchronize=True)
    identity = dict(kind='batch32_gpu_utilization_engineering',packet_sha256=packet.identity,
        actual_batch_size=32,reference_config_batch_size=4,initial_backbone_sha256=initial_hash,
        source_gate=gate['report_sha256'],shuffled_window_order_sha256=order_sha)
    directory = OUTPUT/'checkpoints/batch-032'
    directory.mkdir(parents=True)
    save_checkpoint(directory/'state.pt',adapter,optimizer,identity=identity,
        progress=dict(complete=True,epoch=1,engineering_packet_passes=24,full_junyi_epoch=False,
                      optimizer_steps=total_steps,valid_targets=total_targets))
    checksum = sha(directory/'state.pt')
    write_json(directory/'metadata.json',dict(identity=identity,checkpoint_sha256=checksum,
        checkpoint_bytes=(directory/'state.pt').stat().st_size))
    write_json(directory/'COMPLETE.json',dict(checkpoint_sha256=checksum,
        metadata_sha256=sha(directory/'metadata.json')))
    prediction_before = adapter.predict_window(shuffled[0].window).copy()
    group = shuffled[:32]
    next_batch = collate_windows([entry.window for entry in group],n_items=717,device='cuda',
                                targets=[entry.targets for entry in group])
    expected_step = adapter.step(next_batch,optimizer)
    expected_hash = _state_hash(adapter)
    expected_optimizer = copy.deepcopy(optimizer.state_dict())
    expected_cpu_rng = torch.get_rng_state().clone()
    expected_cuda_rng = torch.cuda.get_rng_state().clone()
    del adapter,optimizer,batch,next_batch
    gc.collect()
    payload = load_checkpoint(directory/'state.pt',expected_identity=identity,device='cpu')
    reloaded,reloaded_optimizer = fresh()
    restore_checkpoint(reloaded,reloaded_optimizer,payload)
    assert np.array_equal(prediction_before,reloaded.predict_window(shuffled[0].window))
    next_batch = collate_windows([entry.window for entry in group],n_items=717,device='cuda',
                                targets=[entry.targets for entry in group])
    actual_step = reloaded.step(next_batch,reloaded_optimizer)
    assert all(actual_step[key]==value for key,value in expected_step.items() if not key.endswith('_seconds'))
    assert _state_hash(reloaded)==expected_hash
    actual_optimizer = reloaded_optimizer.state_dict()
    assert actual_optimizer['param_groups']==expected_optimizer['param_groups']
    for parameter,states in expected_optimizer['state'].items():
        for name,value in states.items():
            actual = actual_optimizer['state'][parameter][name]
            assert torch.equal(actual,value) if isinstance(value,torch.Tensor) else actual==value
    assert torch.equal(torch.get_rng_state(),expected_cpu_rng)
    assert torch.equal(torch.cuda.get_rng_state(),expected_cuda_rng)
    total_targets += 2*expected_step['valid_targets']
    assert total_targets<=1358368
    write_json(OPERATION/'resume-verification.json',dict(status='PASS_EXACT_NEXT_UPDATE',
        model_optimizer_rng_metrics_exact=True,prediction_reload_exact=True,
        additional_optimizer_steps=2,additional_target_exposures=2*expected_step['valid_targets']))
    result.update(status='JUNYI_BATCH_UTILIZATION_COMPLETE',passes=passes,
        actual_benchmark_batch_size=32,engineering_packet_repeated=True,unique_packet_targets=56332,
        trained_target_exposures=1351968,actual_completed_optimizer_steps=770,
        total_target_exposures_including_resume_check=total_targets,
        reference_config_batch_size=4,main_training_protocol_changed=False,
        checkpoint_reload_and_next_update_exact=True,checkpoint_sha256=checksum,cuda_resource=resource,
        full_main_training=False,independent_quality_evaluation=False)
except BaseException as error:
    result.update(error_type=type(error).__name__,error=str(error))
    (OPERATION/'failure.log').write_text(traceback.format_exc())
finally:
    result['elapsed_seconds']=time.monotonic()-started
    write_json(OPERATION/'result.json',result)
print(json.dumps(result,allow_nan=False),flush=True)
raise SystemExit(0 if result['status']=='JUNYI_BATCH_UTILIZATION_COMPLETE' else 1)
