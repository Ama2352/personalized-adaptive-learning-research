"""Đo một pass packet TRAIN80 đã ghim, giữ checkpoint kỹ thuật riêng."""
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


result = dict(status='FAILED',scope='partial_train80_engineering',full_junyi_epoch=False)
try:
    assert REQUEST['status']=='USER_APPROVED' and REQUEST['gpu']=='T4'
    assert REQUEST['max_optimizer_steps']==256 and REQUEST['expected_targets']==56332
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
        check=True,timeout=35)
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
    config = AKTConfig(phase='junyi-research',run_id=RUN,output_dir=OUTPUT,
        execution_enabled=True,device='cuda',outer_fold=4,max_train_users=126774,
        max_val_users=15847,max_targets_per_side=13347331,max_total_targets=56332,
        max_steps=256,max_seconds=240,max_wall_seconds=360,max_rss_bytes=6*1024**3,
        min_available_ram_bytes=256*1024**2)
    gate = require_gate2_evidence(config,lock_file=lock)
    check_preflight(config,runtime_report_path=runtime,lock_file=lock,cuda_profile=profile)
    packet_started = time.monotonic()
    packet = JunyiTrainingPacket(ROOT/REQUEST['packet_root'],
        expected_packet_sha256=REQUEST['packet_sha256'])
    records = list(packet.iter_training_windows())
    encoding = packet.encoding.native
    audit = dict(packet.expected,packet_sha256=packet.identity,
                 full_role_coverage=False,full_train_epoch_complete=False)
    assert len(records)==1024 and len(encoding.vocabulary.values)==717
    write_json(OPERATION/'packet-admission.json',dict(audit=audit,seconds=time.monotonic()-packet_started))
    identity = dict(scope='partial_train80_engineering',packet_sha256=REQUEST['archives']['data']['sha256'],
        source_gate=gate,config=json.loads(json.dumps(asdict(config),default=str)),profile=asdict(profile))
    write_json(OUTPUT/'run-manifest.json',identity)
    _seed(42)
    with torch.device('cpu'):
        adapter = AKTAdapter(config,encoding)
    optimizer = torch.optim.Adam(adapter.native.parameters(),lr=config.lr,betas=config.betas,
        eps=config.eps,weight_decay=config.weight_decay,foreach=False,fused=False,capturable=False,
        differentiable=False,amsgrad=False,maximize=False,decoupled_weight_decay=False)
    torch.cuda.synchronize()
    training_started = time.monotonic()
    stats = train_epoch(adapter,lambda:iter(records),optimizer=optimizer,epoch=1,
        budget=dict(max_steps=256,max_targets=56332,max_seconds=240,max_rss_bytes=6*1024**3,
                    min_available_ram_bytes=256*1024**2,run_id=RUN,phase=config.phase,
                    resource_sample_limit=128,progress_resource_samples=False))
    torch.cuda.synchronize()
    wall = time.monotonic()-training_started
    write_json(OPERATION/'training-stats.json',asdict(stats))
    assert stats.complete and stats.optimizer_steps==256 and stats.valid_targets==56332
    assert stats.collated_windows==1024 and stats.valid_tokens==100032
    directory = OUTPUT/'checkpoints'/'packet-pass-001'
    directory.mkdir(parents=True)
    checkpoint_started = time.monotonic()
    save_checkpoint(directory/'state.pt',adapter,optimizer,identity=identity,
        progress=dict(complete=True,epoch=1,engineering_packet_pass=True,full_junyi_epoch=False,
                      optimizer_steps=stats.optimizer_steps,valid_targets=stats.valid_targets))
    checkpoint_seconds = time.monotonic()-checkpoint_started
    checksum = sha(directory/'state.pt')
    write_json(directory/'metadata.json',dict(checkpoint_sha256=checksum,
        checkpoint_bytes=(directory/'state.pt').stat().st_size,identity=identity))
    write_json(directory/'COMPLETE.json',dict(checkpoint_sha256=checksum,
        metadata_sha256=sha(directory/'metadata.json')))
    baseline = adapter.predict_window(records[0].window).copy()
    payload = load_checkpoint(directory/'state.pt',expected_identity=identity,device='cpu')
    adapter.native.load_state_dict(payload['model_state_dict'])
    reloaded = adapter.predict_window(records[0].window)
    assert (baseline==reloaded).all()
    torch.cuda.synchronize()
    prediction_started = time.monotonic()
    prediction_digest = hashlib.sha256()
    prediction_targets = 0
    for record in records:
        probabilities = adapter.predict_window(record.window)
        scored = probabilities[record.window.target_mask]
        assert np.isfinite(scored).all() and ((scored>=0)&(scored<=1)).all()
        prediction_digest.update(scored.tobytes())
        prediction_targets += len(scored)
    torch.cuda.synchronize()
    prediction_seconds = time.monotonic()-prediction_started
    assert prediction_targets==56332
    resource = _cuda_execution_check(profile,synchronize=True)
    result.update(status='JUNYI_REPRESENTATIVE_BENCHMARK_COMPLETE',gpu=torch.cuda.get_device_name(0),
        optimizer_steps=256,targets=56332,training_wall_seconds=wall,targets_per_second=56332/wall,
        valid_tokens=stats.valid_tokens,padding_tokens=stats.padding_tokens,
        checkpoint_seconds=checkpoint_seconds,checkpoint_sha256=checksum,
        checkpoint_reload_predictions_exact=True,cuda_resource=resource,
        legacy_prediction_seconds=prediction_seconds,prediction_targets=prediction_targets,
        prediction_sha256=prediction_digest.hexdigest(),
        source_and_input_gate=gate,full_junyi_epoch=False)
except BaseException as error:
    result.update(error_type=type(error).__name__,error=str(error))
    (OPERATION/'failure.log').write_text(traceback.format_exc())
finally:
    result['elapsed_seconds'] = time.monotonic()-started
    write_json(OPERATION/'result.json',result)
print(json.dumps(result),flush=True)
raise SystemExit(0 if result['status']=='JUNYI_REPRESENTATIVE_BENCHMARK_COMPLETE' else 1)
