"""Đọc chỉ mục checkpoint của đúng lượt đang chạy, không cấp GPU."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import time

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).parent
RUN = 'modal-junyi-main-selected-t4-20261112-03'
LOGICAL_RUN = 'modal-junyi-main-selected-t4-20261112-01'
NATIVE = ROOT/'experiments/akt/results'/RUN
os.environ['MODAL_CONFIG_PATH'] = str(ROOT/'artifacts/akt/private/modal.toml')
os.environ['MODAL_PROFILE'] = 'kltn'
import modal

started = time.monotonic()
volume = modal.Volume.from_name('kltn-akt-'+LOGICAL_RUN)
last_digest = None
with (BUNDLE/'checkpoint-monitor03.jsonl').open('x',encoding='utf-8') as log:
    while time.monotonic()-started<3400:
        observed = dict(observed_at_utc=datetime.now(timezone.utc).isoformat())
        try:
            raw = b''.join(volume.read_file(RUN+'/checkpoint-index.json'))
            index = json.loads(raw)
            digest = hashlib.sha256(raw).hexdigest()
            steps = [tuple(map(int,match.groups())) for name in index
                     if (match:=re.search(r'batch-epoch-(\d+)-step-(\d+)-',name))]
            observed.update(status='DURABLE_CHECKPOINTS_OBSERVED',count=len(index),
                latest_epoch_step=max(steps,default=None),index_sha256=digest)
            if digest!=last_digest:
                target = BUNDLE/f'checkpoint-index03-{len(index):03d}.json'
                if not target.exists():
                    target.write_bytes(raw)
                last_digest = digest
        except Exception as error:
            observed.update(status='WAITING_FOR_DURABLE_INDEX',error_type=type(error).__name__)
        log.write(json.dumps(observed)+'\n')
        log.flush()
        print(json.dumps(observed),flush=True)
        if (NATIVE/'receipt.json').exists():
            break
        guard = NATIVE/'app-budget-guard.json'
        if guard.exists():
            try:
                stopped = json.loads(guard.read_text()).get('stop_acknowledged')
            except json.JSONDecodeError:
                stopped = False
            if stopped:
                break
        time.sleep(60)
