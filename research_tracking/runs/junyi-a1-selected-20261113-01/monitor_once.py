"""Đọc tiến độ đúng container A1, không nạp Torch local hoặc tạo GPU mới."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
RUN = 'modal-junyi-a1-b128-h100-20261113-05'
os.environ['MODAL_CONFIG_PATH'] = str(ROOT/'artifacts/akt/private/modal.toml')
os.environ['MODAL_PROFILE'] = 'kltn'
os.environ['TEMP'] = os.environ['TMP'] = str(ROOT/'artifacts/akt/runtime/modal-client-temp')
def command(args):
    return subprocess.run([sys.executable, '-B', '-m', 'modal', *args], check=True,
        capture_output=True, text=True, timeout=35).stdout
dispatch = json.loads((ROOT/'experiments/akt/results'/RUN/'dispatch.json').read_text())
owned = [row for row in json.loads(command(['container','list','--json'])) if row['app_id'] == dispatch['app_id']]
if not owned:
    print(json.dumps(dict(status='NO_LIVE_CONTAINER')))
    raise SystemExit(0)
assert len(owned) == 1
source = 'RUN='+repr(RUN)+'\n'+r'''
import json,subprocess,time
from pathlib import Path
root=Path('/opt/kltn/experiments/akt/results')
output=root/RUN
operation=root/(RUN+'-operation')
result=dict(observed_unix=time.time(),output_exists=output.exists())
replay=operation/'a0-validation-replay.json'
if replay.exists():result['a0_replay']=json.loads(replay.read_text())
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
result['epoch_checkpoints']=sorted(p.name for p in (output/'checkpoints').glob('epoch-*') if (p/'COMPLETE.json').exists())
query=subprocess.run(['nvidia-smi','--query-gpu=name,utilization.gpu,memory.used,memory.total,power.draw','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=5)
result['gpu']=query.stdout.strip()
print(json.dumps(result))
'''
record = json.loads(command(['container','exec','--no-pty',owned[0]['container_id'],'--',
    '/opt/kltn/.venv/bin/python','-B','-c',source]))
record['container_id'] = owned[0]['container_id']
with (BUNDLE/'monitor05.jsonl').open('a',encoding='utf-8') as stream:
    stream.write(json.dumps(record,ensure_ascii=False)+'\n')
print(json.dumps(record,ensure_ascii=False))
