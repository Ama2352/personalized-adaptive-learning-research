"""Đọc checkpoint đã đóng và billing để báo tiến độ, không train hoặc benchmark."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
LOGICAL = 'modal-junyi-a0-b128-h100-20261112-01'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--epoch',type=int,choices=range(1,21),required=True)
parser.add_argument('--sequence',type=int,choices=(1,2,3,4),required=True)
args = parser.parse_args()
execution=f'modal-junyi-a0-b128-h100-20261112-{args.sequence:02d}'
monitor='monitor.jsonl' if args.sequence==1 else f'monitor{args.sequence:02d}.jsonl'
records=[json.loads(line) for line in (BUNDLE/monitor).read_text(encoding='utf-8').splitlines()]
container=next(row['container_id'] for row in reversed(records) if row.get('container_id'))
os.environ['MODAL_CONFIG_PATH']=str(ROOT/'artifacts/akt/private/modal.toml')
os.environ['MODAL_PROFILE']='kltn'
os.environ['TEMP']=os.environ['TMP']=str(ROOT/'artifacts/akt/runtime/modal-client-temp')
sys.path.insert(0,str(ROOT/'experiments/akt'))
from modal_graph_selected import read_billing

billing=asyncio.run(read_billing())
(BUNDLE/f'billing-epoch{args.epoch:03d}.json').write_text(json.dumps(billing,indent=2)+'\n')
code=f"""from pathlib import Path
import torch,json
r=Path('/opt/kltn/experiments/akt/results/{LOGICAL}')
p=r/'checkpoints/epoch-{args.epoch:03d}/state.pt'
assert (p.parent/'COMPLETE.json').exists()
v=torch.load(p,map_location='cpu',weights_only=True)
stats=[json.loads(p.read_text()) for p in r.glob('epoch-{args.epoch:03d}-*-training.json')]
stats=[row for row in stats if row['complete']]
assert len(stats)==1
print(json.dumps(dict(epoch={args.epoch},progress=v['progress'],training=stats[0])))
"""
result=subprocess.run([sys.executable,'-B','-m','modal','container','exec','--no-pty',
    container,'--','/opt/kltn/.venv/bin/python','-B','-c',code],capture_output=True,
    text=True,timeout=30,check=True)
snapshot=json.loads(result.stdout)
with (BUNDLE/f'epoch{args.epoch:02d}-snapshot.json').open('x') as stream:
    stream.write(json.dumps(snapshot,indent=2)+'\n')
latest=snapshot['progress']['history'][-1]
print(json.dumps(dict(epoch=args.epoch,selection_log_loss=latest['validation']['native_bce'],
    validation_seconds=latest['validation_seconds'],stopper=snapshot['progress']['stopper'],
    credits_used=billing['billing']['adjustments']['Credits'])))
