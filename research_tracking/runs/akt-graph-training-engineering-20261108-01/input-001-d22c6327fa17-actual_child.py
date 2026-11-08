"""Giám sát global Adam reservations/body returns; không reset sau failure."""
from pathlib import Path
import json,os,sys
import torch
import pytest
from torch.optim.optimizer import register_optimizer_step_pre_hook,register_optimizer_step_post_hook

PREP=Path(__file__).resolve().parent
LEDGER=PREP/'actual_optimizer_events.jsonl'
ATTEMPT=os.environ['KLTN_GRAPH_ATTEMPT_ID']


def read():
    return [json.loads(line) for line in LEDGER.read_text(encoding='utf-8').splitlines()] if LEDGER.exists() else []


def emit(event,optimizer):
    rows=read()
    reservations=sum(r['event']=='optimizer_reservation' for r in rows)
    if event=='optimizer_reservation' and reservations>=4:
        raise RuntimeError('Cumulative actual-stage4optimizer reservation cap; do not reset')
    row=dict(event=event,attempt=ATTEMPT,optimizer_id=id(optimizer),
        optimizer_type=type(optimizer).__name__,test=os.environ.get('PYTEST_CURRENT_TEST'),
        cumulative_reservations=reservations+int(event=='optimizer_reservation'))
    with LEDGER.open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(row,sort_keys=True)+'\n');stream.flush();os.fsync(stream.fileno())


torch.set_num_threads(2)
pre=register_optimizer_step_pre_hook(lambda optimizer,args,kwargs:emit('optimizer_reservation',optimizer))
post=register_optimizer_step_post_hook(lambda optimizer,args,kwargs:emit('optimizer_body_returned',optimizer))
try:
    raise SystemExit(pytest.main(sys.argv[1:]))
finally:
    post.remove();pre.remove()
