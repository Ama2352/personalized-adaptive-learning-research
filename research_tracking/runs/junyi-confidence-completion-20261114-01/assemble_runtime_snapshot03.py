"""Ghép snapshot A2 mới sau Gate runtime và giữ nguyên mọi đầu vào nghiên cứu."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
gate_output=ROOT/'experiments/akt/results/modal-junyi-a2-a3-final-cpu-20261114-03'
receipt=json.loads((gate_output/'receipt.json').read_text())
assert receipt['status']=='MODAL_CPU_GATE_VERIFIED' and receipt['download_inventory_verified']
guard=json.loads((gate_output/'app-budget-guard.json').read_text())
assert guard['stop_acknowledged'] is True
preparation=json.loads((HERE/'linux03/source-gate-preparation.json').read_text())
assert receipt['source_build_sha256']==preparation['source_build_sha256']
archive=gate_output/'artifacts.zip'
assert hashlib.sha256(archive.read_bytes()).hexdigest()==receipt['archive_sha256']
with zipfile.ZipFile(archive) as saved:
    raw=saved.read('gate2-current.json')
    with (HERE/'linux03/gate2-current.json').open('xb') as stream:
        stream.write(raw)
old=json.loads((HERE/'a2-stage-inputs02.json').read_text())
request=json.loads(json.dumps(old))
request['archives']['source']=dict(path=preparation['source'],sha256=preparation['source_sha256'])
request['archives']['cpu_gate']=dict(path=archive.relative_to(ROOT).as_posix(),sha256=receipt['archive_sha256'])
assert request['worker']==old['worker'] and request['local_files']==old['local_files']
with (HERE/'a2-stage-inputs03.json').open('x',encoding='utf-8') as stream:
    json.dump(request,stream,ensure_ascii=False,indent=2)
    stream.write('\n')
ledger_path=ROOT/'research_tracking/COMPUTE_BUDGET.json'
ledger=json.loads(ledger_path.read_text())
assert ledger['new_allocations']==[dict(id='junyi-a2-a3-final-source-cpu-20261114-03',cap_usd=.15,
    purpose_vi='Gate Linux source sửa đường dẫn báo cáo runtime, tối đa600giâyCPU, không GPU.')]
settlement=dict(id='junyi-a2-a3-final-source-cpu-20261114-03',
    status='COMPLETE_GATE_VERIFIED_ARTIFACTS_DOWNLOADED_APP_STOPPED',cap_usd=.15,
    reserved_upper_closed_usd=.15,actual_isolated_cost_usd=None,stop_acknowledged=True)
ledger['closed_reservations'].append(settlement)
ledger['historical_usage_reserved_upper_usd']+=.15
ledger['new_allocations']=[dict(id='junyi-a2-staged-h100-20261114-09',cap_usd=2.6,
    purpose_vi='A2 source sửa runtime sau Gate mới, CPU provider trước H100, input image local.')]
ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (HERE/'linux03/settlement.json').open('x',encoding='utf-8') as stream:
    json.dump(settlement,stream,ensure_ascii=False,indent=2)
execution=json.loads((HERE/'a2-training-request08.json').read_text())
execution.update(execution_id='modal-junyi-a2-staged-h100-20261114-09',
    allocation_id='junyi-a2-staged-h100-20261114-09')
with (HERE/'a2-training-request09.json').open('x',encoding='utf-8') as stream:
    json.dump(execution,stream,ensure_ascii=False,indent=2)
    stream.write('\n')
print(json.dumps(dict(status='RUNTIME_SNAPSHOT_INPUTS_READY',gate=receipt.get('test_result'),
    inputs_unchanged=True,worker_request_unchanged=True)))
