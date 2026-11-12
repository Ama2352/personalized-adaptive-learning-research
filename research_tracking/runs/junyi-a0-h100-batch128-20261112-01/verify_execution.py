"""Nghiệm thu từng trancheH100 bằng receipt/archive/target count, không nạpTorch."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
LOGICAL = 'modal-junyi-a0-b128-h100-20261112-01'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--execution',required=True)
args = parser.parse_args()
assert re.fullmatch(r'modal-junyi-a0-b128-h100-20261112-[0-9]{2}',args.execution)
native = ROOT/'experiments/akt/results'/args.execution
receipt = json.loads((native/'receipt.json').read_text())
assert receipt['download_inventory_verified'] is True
assert receipt['status'] in ('PARTIAL_SELECTED_ONLY_NOT_FINAL','JUNYI_A0_SELECTED_ONLY_COMPLETE')
assert json.loads((native/'app-budget-guard.json').read_text())['stop_acknowledged'] is True
with (native/'artifacts.zip').open('rb') as stream:
    digest = hashlib.file_digest(stream,'sha256').hexdigest()
assert digest==receipt['archive_sha256']
terminal = receipt['worker_result']['terminal']
history = terminal['history']
assert [row['epoch'] for row in history]==list(range(1,len(history)+1))
assert len({row['validation']['population_sha256'] for row in history})==1
assert all(row['validation']['targets']==row['validation']['supported']==1600343
           and row['validation']['oov']==0 for row in history)
with zipfile.ZipFile(native/'artifacts.zip') as archive:
    assert archive.testzip() is None
    inventory = json.loads(archive.read('SHA256.json'))
    assert set(archive.namelist())==set(inventory)|{'SHA256.json'}
    for name,pin in inventory.items():
        with archive.open(name) as stream:
            assert hashlib.file_digest(stream,'sha256').hexdigest()==pin['sha256']
        assert archive.getinfo(name).file_size==pin['bytes']
    identity_name=f'experiments/akt/results/{LOGICAL}/run-manifest.json'
    identity=json.loads(archive.read(identity_name))
    assert identity['config']['batch_size']==128
    assert identity['config']['protocol_version']=='akt-nr-exercise-v2-batch128'
    assert identity['profile']['recipe_id']=='cgakt-cuda-fp32-batch128-v2'
    for name,transfer in receipt['checkpoint_transfers'].items():
        for filename,pin in transfer['files'].items():
            member=f'experiments/akt/results/{LOGICAL}/checkpoints/{name}/{filename}'
            assert inventory[member]==pin
    for suffix in ('run-manifest.json','initial-backbone.json'):
        member=f'experiments/akt/results/{LOGICAL}/{suffix}'
        assert suffix in receipt['durable_control_files']
        assert receipt['durable_control_files'][suffix]==inventory[member]
    training=[]
    for name in sorted(inventory):
        if re.search(r'/epoch-[0-9]{3}-[a-z0-9]+-training.json$',name):
            row=json.loads(archive.read(name))
            if row['complete']:
                assert row['valid_targets']==13347331 and row['optimizer_steps']==1818
                training.append(row)
    for name in inventory:
        if name.endswith('-operation/gpu-telemetry.jsonl'):
            (BUNDLE/(args.execution+'-gpu-telemetry.jsonl')).write_bytes(archive.read(name))
    prediction_rows = prediction_learners = 0
    if receipt['status']=='JUNYI_A0_SELECTED_ONLY_COMPLETE':
        prediction_member=f"experiments/akt/results/{LOGICAL}/{terminal['predictions_file']}"
        assert inventory[prediction_member]['sha256']==terminal['predictions_sha256']
        selected_member=f"experiments/akt/results/{LOGICAL}/checkpoints/epoch-{terminal['selected_epoch']:03d}/state.pt"
        assert inventory[selected_member]['sha256']==terminal['checkpoint_sha256']
        chosen=history[terminal['selected_epoch']-1]['validation']
        assert terminal['validation']['probability_sha256']==chosen['probability_sha256']
        previous_user=None
        previous_order=None
        rank=-1
        with archive.open(prediction_member) as stream:
            for line in stream:
                record=json.loads(line)
                user=record['user_id']
                if user!=previous_user:
                    assert previous_user is None or user>previous_user
                    prediction_learners+=1
                    previous_order=None
                    rank=0
                else:
                    rank+=1
                order=(record['time_done'],record['source_row'])
                assert previous_order is None or order>previous_order
                assert record['global_rank']==rank and record['correct'] in (0,1)
                assert record['fold'] in (0,1,2,3)
                assert record['prediction'] is not None and math.isfinite(record['prediction'])
                assert 0<=record['prediction']<=1
                previous_user,previous_order=user,order
                prediction_rows+=1
        assert prediction_rows==1600343 and prediction_learners==15847
if receipt['status']=='JUNYI_A0_SELECTED_ONLY_COMPLETE':
    assert 1<=terminal['selected_epoch']<=terminal['complete_epochs']<=20
    assert terminal['refit_completed'] is False and terminal['calibration_completed'] is False
    assert terminal['predictions_file'] and terminal['predictions_sha256']
result=dict(status='PASS_ARCHIVE_SOURCE_POPULATION_CHECKPOINTS_STOP',execution=args.execution,
    training_status=receipt['status'],validated_epochs=len(history),history=history,
    selected_epoch=terminal.get('selected_epoch'),optimizer_steps=terminal['optimizer_steps'],
    trained_targets=terminal['trained_targets'],checkpoint_count=len(receipt['checkpoint_transfers']),
    archive_bytes=receipt['archive_bytes'],archive_sha256=digest,training=training,
    exported_prediction_rows=prediction_rows,exported_prediction_learners=prediction_learners,
    refit_completed=False,calibration_completed=False)
path=BUNDLE/(args.execution+'-verification.json')
with path.open('x',encoding='utf-8') as stream:
    stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({key:value for key,value in result.items() if key not in ('history','training')},ensure_ascii=False))
