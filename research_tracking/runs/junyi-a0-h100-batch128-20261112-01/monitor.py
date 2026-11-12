"""Đọc tiến độ đúng container A0, không nạp Torch trên máy local."""
import json
import argparse
import os
from pathlib import Path
import subprocess
import sys
import time
import re

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
RUN = 'modal-junyi-a0-b128-h100-20261112-01'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--execution',default=RUN)
args = parser.parse_args()
assert re.fullmatch(r'modal-junyi-a0-b128-h100-20261112-[0-9]{2}',args.execution)
NATIVE = ROOT/'experiments/akt/results'/args.execution
os.environ['MODAL_CONFIG_PATH'] = str(ROOT/'artifacts/akt/private/modal.toml')
os.environ['MODAL_PROFILE'] = 'kltn'
os.environ['TEMP'] = os.environ['TMP'] = str(ROOT/'artifacts/akt/runtime/modal-client-temp')

REMOTE = r'''
import json,subprocess,time
from pathlib import Path
root=Path('/opt/kltn/experiments/akt/results')/RUN
result=dict(observed_unix=time.time(),output_exists=root.exists())
progress=sorted(root.glob('epoch-*-progress.jsonl'),key=lambda p:p.stat().st_mtime)
if progress:
    p=progress[-1]
    with p.open('rb') as stream:
        stream.seek(max(0,p.stat().st_size-16384))
        raw=stream.read()
    lines=raw.splitlines()
    if not raw.endswith(b'\n'):lines=lines[:-1]
    for line in reversed(lines):
        try:
            event=json.loads(line)
            result['progress_file']=p.name
            result['training']=event.get('training')
            result['complete_epoch']=event.get('complete_epoch')
            break
        except ValueError:pass
checkpoints=sorted(p.name for p in (root/'checkpoints').glob('epoch-*') if (p/'COMPLETE.json').exists())
result['validated_epoch_checkpoints']=checkpoints
for name in ['selected-terminal.json','COMPLETE.json']:
    p=root/name
    if p.exists():
        try:result[name]=json.loads(p.read_text())
        except ValueError:pass
query=subprocess.run(['nvidia-smi','--query-gpu=name,utilization.gpu,memory.used,memory.total,power.draw','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=5)
result['gpu']=query.stdout.strip()
print(json.dumps(result))
'''


def command(arguments,timeout=25):
    return subprocess.run([sys.executable,'-B','-m','modal',*arguments],capture_output=True,
        text=True,timeout=timeout,check=True).stdout


started = time.monotonic()
monitor_name = 'monitor.jsonl' if args.execution==RUN else 'monitor'+args.execution[-2:]+'.jsonl'
with (BUNDLE/monitor_name).open('a',encoding='utf-8') as log:
    while time.monotonic()-started<2100:
        guard = json.loads((NATIVE/'app-budget-guard.json').read_text())
        if guard.get('stop_acknowledged'):
            print('App stopped, awaiting artifact verification.',flush=True)
            break
        try:
            dispatch = json.loads((NATIVE/'dispatch.json').read_text())
            owned = [row for row in json.loads(command(['container','list','--json']))
                     if row['app_id']==dispatch['app_id']]
            if owned:
                assert len(owned)==1
                source='RUN='+repr(RUN)+'\n'+REMOTE
                output = command(['container','exec','--no-pty',owned[0]['container_id'],'--',
                    '/opt/kltn/.venv/bin/python','-B','-c',source],timeout=30)
                record=json.loads(output)
                record['container_id']=owned[0]['container_id']
            else:
                record=dict(status='NO_ALLOCATED_CONTAINER')
            record['observed_local']=time.strftime('%Y-%m-%dT%H:%M:%S%z')
            log.write(json.dumps(record,ensure_ascii=False)+'\n')
            log.flush()
            training = record.get('training') or {}
            concise = dict(observed_local=record['observed_local'],gpu=record.get('gpu'),
                progress_file=record.get('progress_file'),steps=training.get('optimizer_steps'),
                targets=training.get('valid_targets'),complete_epoch=record.get('complete_epoch'),
                validated_epoch_checkpoints=record.get('validated_epoch_checkpoints'))
            print(json.dumps(concise,ensure_ascii=False),flush=True)
        except Exception as error:
            record=dict(status='MONITOR_READ_ERROR',error_type=type(error).__name__,error=str(error))
            log.write(json.dumps(record)+'\n')
            log.flush()
            print(json.dumps(record),flush=True)
        time.sleep(45)
