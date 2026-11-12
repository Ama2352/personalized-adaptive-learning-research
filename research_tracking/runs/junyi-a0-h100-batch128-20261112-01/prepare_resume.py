"""Chuẩn bị lần nối A0 từ archive đã kiểm, không khởi chạy GPU."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
LOGICAL = 'modal-junyi-a0-b128-h100-20261112-01'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--previous',required=True)
parser.add_argument('--sequence',type=int,choices=(2,3),required=True)
args = parser.parse_args()
assert re.fullmatch(r'modal-junyi-a0-b128-h100-20261112-[0-9]{2}',args.previous)
execution = f'modal-junyi-a0-b128-h100-20261112-{args.sequence:02d}'
assert execution!=args.previous
native = ROOT/'experiments/akt/results'/args.previous
receipt = json.loads((native/'receipt.json').read_text())
assert receipt['status']=='PARTIAL_SELECTED_ONLY_NOT_FINAL'
assert receipt['download_inventory_verified'] is True
assert json.loads((native/'app-budget-guard.json').read_text())['stop_acknowledged'] is True
with (native/'artifacts.zip').open('rb') as stream:
    assert hashlib.file_digest(stream,'sha256').hexdigest()==receipt['archive_sha256']


def order(name):
    complete = re.fullmatch(r'epoch-([0-9]+)',name)
    before_validation = re.fullmatch(r'train-epoch-([0-9]+)',name)
    batch = re.fullmatch(r'inner-batch-epoch-([0-9]+)-step-([0-9]+)-[a-z0-9]+',name)
    if complete:
        return int(complete[1]),2,0
    if before_validation:
        return int(before_validation[1]),1,0
    if batch:
        return int(batch[1]),0,int(batch[2])
    raise ValueError('Unexpected checkpoint namespace')


transfers = receipt['checkpoint_transfers']
latest = max(transfers,key=order)
keep = sorted(name for name in transfers if re.fullmatch(r'epoch-[0-9]+',name) or name==latest)
control_root = ROOT/'artifacts/akt/modal'/execution
control_root.mkdir(parents=True,exist_ok=False)
control_archive = control_root/'resume-control.zip'
with zipfile.ZipFile(native/'artifacts.zip') as archive:
    inventory = json.loads(archive.read('SHA256.json'))
    controls = {}
    for name in ('run-manifest.json','initial-backbone.json'):
        member = f'experiments/akt/results/{LOGICAL}/{name}'
        raw = archive.read(member)
        assert hashlib.sha256(raw).hexdigest()==inventory[member]['sha256']
        controls[member] = raw
    identity = json.loads(controls[f'experiments/akt/results/{LOGICAL}/run-manifest.json'])
    for name in keep:
        for filename,pin in transfers[name]['files'].items():
            member = f'experiments/akt/results/{LOGICAL}/checkpoints/{name}/{filename}'
            assert inventory[member]==pin
        metadata = json.loads(archive.read(
            f'experiments/akt/results/{LOGICAL}/checkpoints/{name}/metadata.json'))
        assert metadata['identity']==identity
    with zipfile.ZipFile(control_archive,'x',zipfile.ZIP_DEFLATED) as output:
        pins = {}
        for member,raw in controls.items():
            output.writestr(member,raw)
            pins[member] = hashlib.sha256(raw).hexdigest()
        output.writestr('MANIFEST.json',json.dumps(dict(files=pins),indent=2))

request = json.loads((BUNDLE/'request.json').read_text(encoding='utf-8'))
request.update(run_id=execution,logical_run_id=LOGICAL,resume_from_execution_id=args.previous,
    allocation_id=f'junyi-a0-batch128-h100-20261112-{args.sequence:02d}',
    resume_checkpoint_name=latest,resume_checkpoint_sha256=transfers[latest]['files']['state.pt']['sha256'],
    resume_checkpoints=[dict(name=name,files=transfers[name]['files']) for name in keep])
with control_archive.open('rb') as stream:
    digest = hashlib.file_digest(stream,'sha256').hexdigest()
request['archives']['resume_control'] = dict(path=control_archive.relative_to(ROOT).as_posix(),sha256=digest)
path = BUNDLE/f'request{args.sequence:02d}.json'
with path.open('x',encoding='utf-8') as stream:
    stream.write(json.dumps(request,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(status='RESUME_PREPARED_NOT_DISPATCHED',execution=execution,
    checkpoint=latest,kept_epoch_checkpoints=len(keep),request=path.relative_to(ROOT).as_posix())))
