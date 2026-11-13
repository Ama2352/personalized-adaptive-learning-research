"""Đọc tiến độ đúng container A1, không nạp Torch local hoặc tạo GPU mới."""
import json
import base64
import hashlib
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
RUN = 'modal-junyi-a1-b128-h100-20261113-08'
LOGICAL = 'modal-junyi-a1-b128-h100-20261113-07'
os.environ['MODAL_CONFIG_PATH'] = str(ROOT/'artifacts/akt/private/modal.toml')
os.environ['MODAL_PROFILE'] = 'kltn'
os.environ['TEMP'] = os.environ['TMP'] = str(ROOT/'artifacts/akt/runtime/modal-client-temp')
def command(args):
    value=subprocess.run([sys.executable,'-B','-m','modal',*args],check=True,capture_output=True,text=True,timeout=35)
    if not value.stdout.strip():
        diagnostic=dict(status='MONITOR_EMPTY_STDOUT',stdout_length=len(value.stdout),stderr_tail=value.stderr[-1800:])
        (BUNDLE/'monitor-empty-diagnostic.json').write_text(json.dumps(diagnostic,ensure_ascii=False,indent=2))
        raise RuntimeError('Monitor empty stdout; diagnostic saved')
    return value.stdout
dispatch = json.loads((ROOT/'experiments/akt/results'/RUN/'dispatch.json').read_text())
owned = [row for row in json.loads(command(['container','list','--json'])) if row['app_id'] == dispatch['app_id']]
if not owned:
    print(json.dumps(dict(status='NO_LIVE_CONTAINER')))
    raise SystemExit(0)
assert len(owned) == 1
snapshot_name='live-monitor.json'
source = 'RUN='+repr(RUN)+'\nLOGICAL='+repr(LOGICAL)+'\n'+r'''
import json,subprocess,time,base64,hashlib
from pathlib import Path
root=Path('/opt/kltn/experiments/akt/results')
output=root/LOGICAL
operation=root/(RUN+'-operation')
result=dict(observed_unix=time.time(),observed_monotonic=time.monotonic(),output_exists=output.exists())
proof=operation/'actual-checkpoint-gpu-parity.json'
if proof.exists():
    raw_proof=proof.read_bytes()
    value=json.loads(raw_proof)
    result['_full_gpu_proof']=dict(sha256=hashlib.sha256(raw_proof).hexdigest(),payload=base64.b64encode(raw_proof).decode())
    result['gpu_checkpoint_parity']={k:value[k] for k in ('status','max_absolute_drift','targets','alpha')}
proof_log=operation/'actual-checkpoint-cuda.log'
if proof_log.exists():result['canary_log_tail']=proof_log.read_text()[-1600:]
telemetry=operation/'gpu-telemetry.jsonl'
if telemetry.exists():
    lines=telemetry.read_text().splitlines()[-30:]
    samples=[json.loads(line) for line in lines]
    if samples:result['recent_gpu_mean']=sum(row['gpu_utilization'] for row in samples)/len(samples)
    result['recent_gpu_samples']=len(samples)

replay=operation/'a0-validation-replay.json'
if replay.exists():result['a0_replay_status']=json.loads(replay.read_text()).get('status')
failure=operation/'failure.log'
if failure.exists():result['failure']=failure.read_text()[-3000:]
progress=sorted(output.glob('epoch-*-progress.jsonl'),key=lambda p:p.stat().st_mtime)
if progress:
    with progress[-1].open('rb') as stream:
        stream.seek(max(0,progress[-1].stat().st_size-20000))
        raw=stream.read()
    for line in reversed(raw.splitlines()):
        try:
            result['training']=json.loads(line)
            result['progress_file']=progress[-1].name
            break
        except ValueError:pass
result['train_epochs']=[]
for path in sorted(output.glob('epoch-*-training.json')):
    try:
        value=json.loads(path.read_text())
        result['train_epochs'].append(dict(epoch=int(path.name.split('-')[1]),complete=value['complete'],steps=value['optimizer_steps'],targets=value['valid_targets'],wall_seconds=value['resource']['wall_seconds'],forward_seconds=value['forward_seconds'],backward_seconds=value['backward_seconds'],gradient_clip_seconds=value['gradient_clip_seconds'],optimizer_seconds=value['optimizer_seconds']))
    except (ValueError,KeyError):pass
result['epoch_checkpoints']=sorted(p.name for p in (output/'checkpoints').glob('epoch-*') if (p/'COMPLETE.json').exists())
query=subprocess.run(['nvidia-smi','--query-gpu=name,utilization.gpu,memory.used,memory.total,power.draw','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=5)
result['gpu']=query.stdout.strip()
snapshot=Path('/durable')/RUN/'live-monitor.json'
snapshot.write_text(json.dumps(result))
import modal
modal.Volume.from_name('kltn-akt-modal-junyi-a1-b128-h100-20261113-07').commit()
print(json.dumps(result))
'''
# Dùng Volume receipt để tránh phụ thuộc stdout CLI có lúc rỗng.
try:
    command(['container','exec','--no-pty',owned[0]['container_id'],'--',
        '/opt/kltn/.venv/bin/python','-B','-c',source])
except RuntimeError:
    pass
import modal
volume=modal.Volume.from_name('kltn-akt-modal-junyi-a1-b128-h100-20261113-07',create_if_missing=False)
raw=b''.join(volume.read_file(RUN+'/'+snapshot_name))
record=json.loads(raw)
proof=record.pop('_full_gpu_proof',None)
if proof is not None:
    raw=base64.b64decode(proof['payload'],validate=True)
    assert hashlib.sha256(raw).hexdigest()==proof['sha256']
    destination=BUNDLE/'actual-checkpoint-gpu-parity.json'
    if destination.exists():assert destination.read_bytes()==raw
    else:destination.write_bytes(raw)
record['container_id'] = owned[0]['container_id']
with (BUNDLE/'monitor08.jsonl').open('a',encoding='utf-8') as stream:
    stream.write(json.dumps(record,ensure_ascii=False)+'\n')
visible={k:v for k,v in record.items() if k not in ('training','canary_log_tail','container_id')}
if 'training' in record:
    t=record['training'];r=t['training']
    visible['training']=dict(epoch=t['epoch'],complete_epoch=t['complete_epoch'],steps=r['optimizer_steps'],targets=r['valid_targets'],wall_seconds=r['resource']['wall_seconds'])
print(json.dumps(visible,ensure_ascii=False))

