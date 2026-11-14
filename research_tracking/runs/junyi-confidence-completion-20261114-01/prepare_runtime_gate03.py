"""Đóng source sửa runtime, tái dùng inventory nguồn và cấp CPU Gate mới."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
target=HERE/'linux03'
target.mkdir(exist_ok=True)
previous=json.loads((HERE/'linux02/source-gate-preparation.json').read_text())
old_run='modal-junyi-a2-a3-final-cpu-20261114-02'
run='modal-junyi-a2-a3-final-cpu-20261114-03'
for name in ('cpu_controller.py','cpu_worker.py'):
    raw=(HERE/'linux02'/name).read_bytes().replace(old_run.encode(),run.encode())
    if (target/name).exists():
        assert (target/name).read_bytes()==raw
    else:
        (target/name).write_bytes(raw)
source=ROOT/'artifacts/akt/modal/junyi-a2-a3-final-20261114-03/source.zip'
source.parent.mkdir(parents=True,exist_ok=True)
pins={}
changed=[]
members={}
with zipfile.ZipFile(ROOT/previous['source']) as old:
    for name,digest in previous['source_files'].items():
        raw=old.read(name)
        assert hashlib.sha256(raw).hexdigest()==digest
        if name.startswith(('src/','scripts/','tests/','experiments/')):
            raw=(ROOT/name).read_bytes()
        pins[name]=hashlib.sha256(raw).hexdigest()
        if pins[name]!=digest:
            changed.append(name)
        members[name]=raw
if source.exists():
    with zipfile.ZipFile(source) as saved:
        assert json.loads(saved.read('MANIFEST.json'))['files']==pins
        assert all(saved.read(name)==raw for name,raw in members.items())
else:
    with zipfile.ZipFile(source,'x',zipfile.ZIP_DEFLATED,compresslevel=1) as saved:
        for name,raw in members.items():
            saved.writestr(name,raw)
        saved.writestr('MANIFEST.json',json.dumps(dict(files=pins),sort_keys=True))
build_hashes={name:pins[name] for name in previous['gate2_build_hashes']}
build=hashlib.sha256(json.dumps(build_hashes,sort_keys=True,separators=(',',':')).encode()).hexdigest()
preparation=dict(previous,status='SOURCE_GATE_PREPARED_NOT_DISPATCHED',run_id=run,
    source=source.relative_to(ROOT).as_posix(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    bytes=source.stat().st_size,source_files=pins,gate2_build_hashes=build_hashes,source_build_sha256=build,
    changed_files=changed,
    worker_sha256=hashlib.sha256((target/'cpu_worker.py').read_bytes()).hexdigest(),
    controller_sha256=hashlib.sha256((target/'cpu_controller.py').read_bytes()).hexdigest())
(target/'source-gate-preparation.json').write_text(json.dumps(preparation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
ledger_path=ROOT/'research_tracking/COMPUTE_BUDGET.json'
ledger=json.loads(ledger_path.read_text())
old=json.loads((HERE/'a2-training-request08.json').read_text())
output=ROOT/'experiments/akt/results'/old['execution_id']
assert json.loads((output/'app-budget-guard.json').read_text())['stop_acknowledged']
assert json.loads((output/'COMPLETE.json').read_text())['status']=='LOCAL_ARTIFACTS_VERIFIED_GPU_STOPPED'
assert len(ledger['new_allocations'])==1 and ledger['new_allocations'][0]['id']==old['allocation_id']
# Guard gồm thời gian upload/image CPU. Tính cả khoảng đó bằng rate GPU làm cận bảo thủ.
guard=json.loads((output/'app-budget-guard.json').read_text())
elapsed=max(event['elapsed_seconds'] for event in guard['events'])
upper=(elapsed+10)*.00133472
settlement=dict(id=old['allocation_id'],status='RUNTIME_OUTPUT_PATH_FAILED_ARTIFACTS_VERIFIED_APP_STOPPED',
    stop_acknowledged=True,reserved_upper_closed_usd=upper,gpu_worker_seconds=6.35158801,
    actual_isolated_cost_usd=None)
ledger['closed_reservations'].append(settlement)
ledger['historical_usage_reserved_upper_usd']+=upper
ledger['new_allocations']=[dict(id='junyi-a2-a3-final-source-cpu-20261114-03',cap_usd=.15,
    purpose_vi='Gate Linux source sửa đường dẫn báo cáo runtime, tối đa600giâyCPU, không GPU.')]
ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(HERE/'a2-runtime-failure-settlement08.json').write_text(json.dumps(settlement,indent=2)+'\n')
print(json.dumps(dict(status='SOURCE_GATE03_READY',source=preparation['source'],
    source_sha256=preparation['source_sha256'],changed=changed)))
