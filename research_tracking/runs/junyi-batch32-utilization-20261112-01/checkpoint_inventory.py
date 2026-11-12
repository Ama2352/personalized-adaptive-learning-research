"""Kiểm checkpoint thật trong archive, không import hoặc nạp Torch."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
entries = []


def verify(archive, member, expected):
    with zipfile.ZipFile(ROOT/archive) as saved:
        info = saved.getinfo(member)
        with saved.open(member) as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == expected
    return dict(archive=archive, member=member, bytes=info.file_size, sha256=expected,
                verified_local_checkpoint=True)


index = json.loads((ROOT/'research_tracking/runs/modal-akt-graph-selected-20261112-01/checkpoint-index.json').read_text())
assert len(index['entries']) == 7
for row in index['entries']:
    checkpoint = row['selected_checkpoint']
    entry = verify(row['archive'], checkpoint['archive_member_directory']+'/state.pt', checkpoint['state_sha256'])
    entry.update(model=row['candidate_id'], dataset='Grade10', phase=row['phase'],
                 selected_epoch=row['selected_epoch'], volume=checkpoint['volume_name'],
                 volume_directory=checkpoint['volume_directory'])
    entries.append(entry)
native = ROOT/'experiments/akt/results/modal-junyi-main-selected-t4-20261112-06'
receipt = json.loads((native/'receipt.json').read_text())
for epoch, purpose in [(5, 'temporary_best_by_min_delta'), (6, 'latest_complete_epoch')]:
    key = f'epoch-{epoch:03d}'
    entry = verify(str((native/'artifacts.zip').relative_to(ROOT)),
        'experiments/akt/results/modal-junyi-main-selected-t4-20261112-01/checkpoints/'+key+'/state.pt',
        receipt['checkpoint_transfers'][key]['checkpoint_sha256'])
    entry.update(model='A0', dataset='Junyi', phase='partial_selected_fit80', epoch=epoch,
                 purpose=purpose, final_selected_epoch=None,
                 volume='kltn-akt-modal-junyi-main-selected-t4-20261112-01')
    entries.append(entry)
native = ROOT/'experiments/akt/results/modal-junyi-batch-utilization-t4-20261112-01'
receipt = json.loads((native/'receipt.json').read_text())
entry = verify(str((native/'artifacts.zip').relative_to(ROOT)),
    'experiments/akt/results/'+native.name+'/checkpoints/batch-032/state.pt',
    receipt['checkpoint_transfers']['batch-032']['checkpoint_sha256'])
entry.update(model='A0_batch32_engineering', dataset='repeated_Junyi_TRAIN80_packet',
             phase='engineering_only', full_dataset_training=False,
             volume='kltn-akt-'+native.name)
entries.append(entry)
result = dict(status='PASS_LOCAL_CHECKPOINT_HASHES', entries=entries,
              Grade10_saved_epoch_checkpoint_count=sum(len(row['saved_epochs']) for row in index['entries']),
              H100_started=False)
(BUNDLE/'checkpoint-inventory.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(dict(status=result['status'], checked_checkpoints=len(entries),
                      Grade10_saved_epochs=result['Grade10_saved_epoch_checkpoint_count'])), flush=True)
