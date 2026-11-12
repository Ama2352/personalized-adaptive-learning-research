"""Xuất một checkpoint đại diện mỗi model sang ổ D, giữ nguyên byte gốc."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
OUTPUT = ROOT/'experiments/akt/results/model-export-20261112-01'
assert OUTPUT.resolve().drive.upper() == 'D:'
assert OUTPUT.resolve().is_relative_to((ROOT/'experiments/akt/results').resolve())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def checked_json(saved, name, expected=None):
    raw = saved.read(name)
    if expected is not None:
        assert hashlib.sha256(raw).hexdigest() == expected
    return json.loads(raw)


entries = []
grade_index = json.loads((ROOT/'research_tracking/runs/modal-akt-graph-selected-20261112-01/checkpoint-index.json').read_text())
for row in grade_index['entries']:
    selected = row['selected_checkpoint']
    directory = selected['archive_member_directory']
    with zipfile.ZipFile(ROOT/row['archive']) as saved:
        metadata = checked_json(saved, directory+'/metadata.json', selected['metadata_sha256'])
        complete = checked_json(saved, directory+'/COMPLETE.json', selected['complete_sha256'])
        size = saved.getinfo(directory+'/state.pt').file_size
    encoding = metadata['identity']['encoding']
    entries.append(dict(model=row['candidate_id'], dataset='Grade10', phase='selected_fit80',
        epoch=row['selected_epoch'], final_research_evaluation_complete=False,
        source_archive=row['archive'], source_member=directory+'/state.pt',
        destination='Grade10/'+row['candidate_id']+'.pt', bytes=size,
        sha256=selected['state_sha256'], checkpoint_metadata=metadata, complete_marker=complete,
        architecture=metadata['producer_config'], condition=metadata['identity']['condition'],
        vocabulary=dict(values=[item for item, count in encoding['support']],
                        train_support_students=dict(encoding['support'])),
        model_class='knowledge_tracing.akt.research_graph_model.ResearchGraphNative'))
native = ROOT/'experiments/akt/results/modal-junyi-main-selected-t4-20261112-06'
receipt = json.loads((native/'receipt.json').read_text())
verification = json.loads((ROOT/'research_tracking/runs/junyi-main-selected-20261112-01/execution06-verification.json').read_text())
assert verification['temporary_early_stopping_best_epoch'] == 5
directory = 'experiments/akt/results/modal-junyi-main-selected-t4-20261112-01/checkpoints/epoch-005'
with zipfile.ZipFile(native/'artifacts.zip') as saved:
    metadata = checked_json(saved, directory+'/metadata.json')
    complete = checked_json(saved, directory+'/COMPLETE.json')
    size = saved.getinfo(directory+'/state.pt').file_size
request = json.loads((ROOT/'research_tracking/runs/junyi-main-selected-20261112-01/request06.json').read_text())
encoding_file = ROOT/request['inputs']['encoding_file']
assert sha(encoding_file) == request['inputs']['encoding_sha256']
encoding = json.loads(encoding_file.read_text())
entries.append(dict(model='A0_BEST_SO_FAR', dataset='Junyi', phase='partial_selected_fit80',
    epoch=5, final_selected_epoch=None, final_research_evaluation_complete=False,
    source_archive=(native/'artifacts.zip').relative_to(ROOT).as_posix(), source_member=directory+'/state.pt',
    destination='Junyi/A0_BEST_SO_FAR.pt', bytes=size,
    sha256=receipt['checkpoint_transfers']['epoch-005']['checkpoint_sha256'],
    checkpoint_metadata=metadata, complete_marker=complete, architecture=metadata['identity']['config'],
    condition=dict(variant='A0', graph_mode='disabled'), vocabulary=encoding,
    model_class='knowledge_tracing.akt.model.AKTAdapter'))
assert len(entries) == 8 and sum(row['dataset'] == 'Grade10' for row in entries) == 7
grade_source = ROOT/'artifacts/akt/modal/modal-checkpoint-pilot-20261112-12/source.zip'
junyi_source = ROOT/request['archives']['source']['path']
assert sha(junyi_source) == request['archives']['source']['sha256']
runtime = ROOT/'artifacts/akt/colab/gpu08-linux-20261108-01/received/resolution-attempt01/candidate-linux-cuda.lock.txt'
sources = dict(entries[0]['checkpoint_metadata']['identity']['sources'])
with zipfile.ZipFile(grade_source) as saved:
    assert all(hashlib.sha256(saved.read(name)).hexdigest() == digest
               for name, digest in sources.items() if name.startswith('src/'))
upstream = {}
for name in ('akt.py', 'README.md', 'LICENSE'):
    relative = 'artifacts/akt/dependencies/upstream/'+name
    raw = (ROOT/relative).read_bytes().replace(b'\r\n', b'\n')
    assert hashlib.sha256(raw).hexdigest() == sources[relative]
    upstream[name] = raw
support_inputs = {'grade10_source.zip':grade_source, 'junyi_source.zip':junyi_source,
                  'runtime.lock.txt':runtime}
plan = dict(destination=str(OUTPUT.resolve()), entries=entries,
            support_inputs={name:dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))
                            for name, path in support_inputs.items()},
            total_checkpoint_bytes=sum(row['bytes'] for row in entries),
            upstream_commit='01b7e8d7d7c862cabc9467108e3e7f2555653a88',
            H100_started=False)
assert shutil.disk_usage(ROOT).free > plan['total_checkpoint_bytes']+10*1024**2
with (BUNDLE/'export-plan.json').open('x', encoding='utf-8') as stream:
    json.dump(plan, stream, ensure_ascii=False, indent=2)
OUTPUT.mkdir(exist_ok=False)
for entry in entries:
    destination = OUTPUT/entry['destination']
    assert destination.resolve().is_relative_to(OUTPUT.resolve()) and destination.resolve().drive.upper() == 'D:'
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix('.pt.partial')
    digest = hashlib.sha256()
    with zipfile.ZipFile(ROOT/entry['source_archive']) as saved:
        with saved.open(entry['source_member']) as source, temporary.open('xb') as target:
            while chunk := source.read(1024*1024):
                target.write(chunk)
                digest.update(chunk)
            target.flush()
            os.fsync(target.fileno())
    assert digest.hexdigest() == entry['sha256'] and temporary.stat().st_size == entry['bytes']
    assert not destination.exists()
    os.rename(temporary, destination)
    entry['exported_path'] = str(destination.resolve())
    print(json.dumps(dict(model=entry['model'], dataset=entry['dataset'], path=str(destination),
                          bytes=entry['bytes'], sha256_verified=True)), flush=True)
with zipfile.ZipFile(OUTPUT/'SUPPORT.zip', 'x', compression=zipfile.ZIP_STORED) as saved:
    for name, path in support_inputs.items():
        saved.write(path, name)
    for name, raw in upstream.items():
        saved.writestr('upstream/'+name, raw)
    with zipfile.ZipFile(ROOT/'artifacts/akt/modal/main60-akt-inputs-20261112-01/research-inputs.zip') as original:
        names = [name for name in original.namelist() if name.endswith('/bank.json')]
        assert len(names) == 1
        saved.writestr('grade10_item_bank.json', original.read(names[0]))
index = dict(format='PyTorch full training checkpoint, original bytes', exported_models=len(entries),
    all_models_final=False, entries=entries, support_archive='SUPPORT.zip',
    support_sha256=sha(OUTPUT/'SUPPORT.zip'), upstream_commit=plan['upstream_commit'],
    source_note='Grade10 source package matches all25 src pins. Three upstream files match normalized Linux pins.',
    inference_note='Custom AKT architecture, use saved source and model class. Research checkpoints are selected-fit80 states, with refit/calibration pending.')
(OUTPUT/'MODEL_INDEX.json').write_text(json.dumps(index, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
(OUTPUT/'README.md').write_text('''# Bộ model AKT đã train — snapshot ngày12/11/2026

## Các file model

`Grade10/` có bảy file A0, A1_EXPERT, A1_LEARNED, A2_EXPERT, A2_LEARNED, A3_EXPERT, A3_LEARNED. Mỗi file là một checkpoint được chọn sau train80/selection10. A0/A1_EXPERT chọn epoch5, năm điều kiện còn lại chọn epoch4.

`Junyi/A0_BEST_SO_FAR.pt` là epoch5 theo quy tắc min_delta0,0001. A0 Junyi đã học qua6epoch, còn chọn epoch cuối. Checkpoint để tiếp tục từ epoch6 nằm trong archive execution06 tại repository. Không dùng file best-so-far thay cho latest khi tiếp tục luồng training đang dở.

## Nội dung gói

Mỗi `.pt` giữ nguyên checkpoint gốc gồm model_state_dict, optimizer_state_dict và RNG. `MODEL_INDEX.json` giữ cấu hình, vocabulary, graph/confidence, metadata gốc, SHA và đường dẫn nguồn. `SUPPORT.zip` giữ source Grade10/Junyi đã dùng, runtime lock, item bank Grade10 và ba file upstream tại commit được ghim. Trên máy khác cần thiết lập upstream Git checkout ở commit ghi trong chỉ mục để đáp ứng kiểm provenance của source.

Đây là checkpoint nghiên cứu đã train. Các cờ fitted_research_model/lifecycle_resume_supported trong metadata gốc được giữ đúng. Refit, calibration và đánh giá độc lập của các model còn phải thực hiện. Model Grade10 và Junyi có vocabulary và checkpoint riêng.

## Đọc file PyTorch

Chạy bằng Python trong `.venv` của KLTN.

```python
import torch
checkpoint = torch.load("Grade10/A3_EXPERT.pt", map_location="cpu", weights_only=True)
weights = checkpoint["model_state_dict"]
```

Đoạn này đọc checkpoint. Để dự đoán, cần dựng đúng model class trong chỉ mục, nạp weights và cấp input/vocabulary/context theo source đi kèm. Gói này chưa cung cấp API inference độc lập hoặc Transformers AutoModel.

Các file model và support nằm trên ổD. Checkpoint trung gian, logs và archive lịch sử có chỉ mục tại repository. H100 đang chờ theo yêu cầu của người dùng.
''', encoding='utf-8')
result = dict(status='EXPORTED_EIGHT_REPRESENTATIVE_MODELS_ON_D', output=str(OUTPUT.resolve()),
              checkpoint_bytes=plan['total_checkpoint_bytes'], model_files=8,
              support_sha256=index['support_sha256'], original_checkpoints_unchanged=True)
(BUNDLE/'export-result.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result), flush=True)
