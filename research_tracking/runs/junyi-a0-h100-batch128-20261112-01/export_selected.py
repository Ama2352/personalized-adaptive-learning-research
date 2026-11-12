"""Xuất checkpointA0 đã chọn thành một file.pt trênD, giữ byte gốc."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import zipfile

ROOT=Path(__file__).resolve().parents[3]
BUNDLE=Path(__file__).resolve().parent
LOGICAL='modal-junyi-a0-b128-h100-20261112-01'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--execution',required=True)
args=parser.parse_args()
assert re.fullmatch(r'modal-junyi-a0-b128-h100-20261112-[0-9]{2}',args.execution)
native=ROOT/'experiments/akt/results'/args.execution
receipt=json.loads((native/'receipt.json').read_text())
assert receipt['status']=='JUNYI_A0_SELECTED_ONLY_COMPLETE'
assert receipt['download_inventory_verified'] is True
assert json.loads((native/'app-budget-guard.json').read_text())['stop_acknowledged'] is True
terminal=receipt['worker_result']['terminal']
epoch=terminal['selected_epoch']
member=f'experiments/akt/results/{LOGICAL}/checkpoints/epoch-{epoch:03d}/state.pt'
output=ROOT/'experiments/akt/results/model-export-a0-batch128-20261112-01'
assert output.resolve().drive.upper()=='D:'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


assert sha(native/'artifacts.zip')==receipt['archive_sha256']
request=json.loads((BUNDLE/'request.json').read_text(encoding='utf-8'))
encoding=ROOT/request['inputs']['encoding_file']
source=ROOT/request['archives']['source']['path']
assert sha(encoding)==request['inputs']['encoding_sha256']
assert sha(source)==request['archives']['source']['sha256']
with zipfile.ZipFile(native/'artifacts.zip') as archive:
    inventory=json.loads(archive.read('SHA256.json'))
    pin=inventory[member]
    assert pin['sha256']==terminal['checkpoint_sha256']
    metadata=json.loads(archive.read(member.rsplit('/',1)[0]+'/metadata.json'))
    assert metadata['identity']['config']['batch_size']==128
    plan=dict(source_archive=(native/'artifacts.zip').relative_to(ROOT).as_posix(),
        archive_sha256=receipt['archive_sha256'],source_member=member,checkpoint=pin,
        destination=str(output/'A0_JUNYI_SELECTED.pt'),selected_epoch=epoch)
    with (BUNDLE/'selected-export-plan.json').open('x') as stream:
        stream.write(json.dumps(plan,indent=2)+'\n')
    output.mkdir(exist_ok=False)
    temporary=output/'A0_JUNYI_SELECTED.pt.partial'
    digest=hashlib.sha256()
    with archive.open(member) as original,temporary.open('xb') as target:
        while block:=original.read(1024*1024):
            target.write(block)
            digest.update(block)
        target.flush()
        os.fsync(target.fileno())
    assert temporary.stat().st_size==pin['bytes'] and digest.hexdigest()==pin['sha256']
    os.rename(temporary,output/'A0_JUNYI_SELECTED.pt')
assert sha(output/'A0_JUNYI_SELECTED.pt')==pin['sha256']
with zipfile.ZipFile(output/'SUPPORT.zip','x',zipfile.ZIP_STORED) as support:
    support.write(source,'source.zip')
    support.write(encoding,'encoding.json')
    support.write(BUNDLE/'request.json','selected-request.json')
index=dict(model='A0',dataset='Junyi',phase='selected_fit80',batch_size=128,
    selected_epoch=epoch,complete_epochs=terminal['complete_epochs'],
    checkpoint_file='A0_JUNYI_SELECTED.pt',checkpoint_sha256=pin['sha256'],
    checkpoint_bytes=pin['bytes'],metadata=metadata,
    selection_metrics=terminal['validation'],
    model_class='knowledge_tracing.akt.model.AKTAdapter',
    source_archive=plan['source_archive'],source_member=member,
    support_sha256=sha(output/'SUPPORT.zip'),refit_completed=False,
    calibration_completed=False,independent_evaluation_completed=False)
(output/'MODEL_INDEX.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(output/'README.md').write_text(f'''# A0 Junyi đã chọn checkpoint trênH100

`A0_JUNYI_SELECTED.pt` là checkpoint epoch{epoch}, được chọn sau{terminal['complete_epochs']}epoch bằng early stopping trênselection. Lượt này dùngbatch128, không đồ thị, khôngRasch, seed42 và vocabulary717exercise.

File.pt giữ nguyên model_state_dict, optimizer_state_dict và RNG từcheckpoint gốc. MODEL_INDEX.json chứa cấu hình, metadata, nguồn và phạm vi kết quả. SUPPORT.zip giữ source đã dùng, encoding và request. Nạp checkpoint bằng torch.load với map_location="cpu", weights_only=True trong.venv củaKLTN. Dự đoán cần dựng đúng AKTAdapter và dùng vocabulary/context theo source.

Đã kiểm SHA trước và sau sao chép. Pipeline đã nạp lại chính checkpoint được chọn và xuất đủ1.600.343dự đoánselection. Refit90, calibration và đánh giá độc lập còn ở các bước tiếp theo. Bộ này là checkpoint đã chọn trêntrain80/selection10. Chưa có kết quả đánh giá ngoài tập chọn epoch.

Toàn bộ file trong thư mục này nằm trênD. Checkpoint trung gian cùng logs giữ trong output gốc theo run.
''',encoding='utf-8')
result=dict(status='EXPORTED_SELECTED_A0_ON_D',output=str(output),selected_epoch=epoch,
    checkpoint_sha256=pin['sha256'],checkpoint_bytes=pin['bytes'],
    refit_completed=False,independent_evaluation_completed=False)
(BUNDLE/'selected-export-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
