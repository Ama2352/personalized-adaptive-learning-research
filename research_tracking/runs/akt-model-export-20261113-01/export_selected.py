"""Đối chiếu A0–A1 và xuất gọn A1 đã chọn trên D, giữ nguyên checkpoint nguồn."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
EVIDENCE = ROOT / 'research_tracking/runs/junyi-a1-selection-cache-20261113-01'
LOGICAL = ROOT / 'experiments/akt/results/modal-junyi-a1-b128-h100-20261113-07'
OUTPUT = ROOT / 'experiments/akt/results/model-export-a1-batch128-20261113-01'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.akt.comparison_contract import TRAINING_FIELDS, require_matched_candidate
    a0_folder = ROOT / 'experiments/akt/results/model-export-a0-batch128-20261112-01'
    a0 = read(a0_folder / 'MODEL_INDEX.json')
    assert sha(a0_folder / a0['checkpoint_file']) == a0['checkpoint_sha256']
    terminal = read(LOGICAL / 'selected-terminal.json')
    assert terminal['status'] == 'JUNYI_A1_SELECTED_ONLY_COMPLETE'
    assert terminal['complete_epochs'] == 12 and terminal['selected_epoch'] == 9
    assert read(EVIDENCE / 'final-acceptance.json')['status'] == 'PASS_FINAL_A1_ACCEPTANCE'
    request = read(EVIDENCE / 'h100-request09.json')
    metadata = read(LOGICAL / 'checkpoints/epoch-009/metadata.json')
    identity = metadata['identity']
    reference = read(EVIDENCE / 'a0-batched-comparison-reference03.json')['reference']
    admission = read(next(LOGICAL.glob('comparison-admission-0027236c*.json')))
    # UUID của attempt được lưu trong artifact, không suy khớp từ số target đơn thuần.
    candidate = dict(admission['candidate'], observed_selection_population_sha256=terminal['validation']['population_sha256'])
    require_matched_candidate(reference, candidate, observed=True)
    a0_identity = a0['metadata']['identity']
    for key in TRAINING_FIELDS:
        assert a0_identity['config'][key] == identity['config'][key], key
    assert a0_identity['inputs'] == identity['inputs']
    assert a0_identity['encoding'] == identity['encoding']
    assert a0_identity['profile'] == identity['profile']
    assert a0['selection_metrics']['population_sha256'] == terminal['validation']['population_sha256']
    replay = read(EVIDENCE / 'a0-validation-replay03.json')
    assert replay['status'] == 'PASS_SELECTED_A0_CHECKPOINT_BATCH128'
    assert replay['results'][0]['absolute_log_loss_delta'] == 0
    assert replay['a0_epoch_choice_replayed'] is False
    original_initial = ROOT / 'experiments/akt/results/modal-junyi-a0-b128-h100-20261112-01/initial-backbone.json'
    if original_initial.exists():
        assert read(original_initial)['sha256'] == terminal['initial_backbone_sha256']
    assert reference['initial_backbone_sha256'] == terminal['initial_backbone_sha256']
    comparison = {'status': 'MATCHED_TRAINING_BOUNDARIES_FINAL_EVALUATION_PENDING',
                  'matched_training_fields': list(TRAINING_FIELDS), 'inputs_match': True,
                  'encoding_match': True, 'numeric_profile_match': True, 'initial_backbone_match': True,
                  'selection_population_match': True, 'a0_selected_checkpoint_replayed_batch128': True,
                  'a0_full_epoch_choice_replayed_batch128': False,
                  'a0_validation_implementation': a0_identity['prediction_implementation'],
                  'a1_validation_implementation': identity['prediction_implementation'],
                  'limits_vi': 'A0 chọn epoch bằng batch1, A1 bằng batch128. Chỉ epoch9 A0 đã replay đầy đủ '
                               'với Log Loss bằng nhau, chưa replay ranking toàn12epoch. Refit/calibration/'
                               'đánh giá độc lập còn chờ. Selection chưa đủ kết luận lợi ích của đồ thị.'}
    write(HERE / 'comparison-audit.json', comparison)
    source = LOGICAL / 'checkpoints/epoch-009/state.pt'
    sources = {
        'source.zip': ROOT / request['archives']['source']['path'],
        'encoding.json': ROOT / request['inputs']['encoding_file'],
        'encoding-receipt.json': ROOT / request['inputs']['encoding_receipt'],
        'graph.json': ROOT / request['graph_file'],
        'roles.json': ROOT / request['inputs']['roles_path'],
        'selected-request.json': EVIDENCE / 'h100-request09.json',
        'run-manifest.json': LOGICAL / 'run-manifest.json',
        'source-transition.json': LOGICAL / 'source-transition.json',
    }
    expected = {'source.zip': request['archives']['source']['sha256'],
                'encoding.json': request['inputs']['encoding_sha256'],
                'encoding-receipt.json': request['inputs']['encoding_receipt_sha256'],
                'graph.json': request['graph_sha256'], 'roles.json': request['inputs']['roles_sha256']}
    pins = {name: {'source': path.relative_to(ROOT).as_posix(), 'sha256': sha(path), 'bytes': path.stat().st_size}
            for name, path in sources.items()}
    assert all(pins[name]['sha256'] == value for name, value in expected.items())
    checkpoint_sha = sha(source)
    assert checkpoint_sha == terminal['checkpoint_sha256'] == metadata['checkpoint_sha256']
    assert OUTPUT.resolve().drive.upper() == 'D:' and not OUTPUT.exists()
    plan = {'source_checkpoint': source.relative_to(ROOT).as_posix(), 'sha256': checkpoint_sha,
            'bytes': source.stat().st_size, 'destination': str(OUTPUT / 'A1_JUNYI_SELECTED.pt'), 'support_inputs': pins}
    write(HERE / 'export-plan.json', plan)
    OUTPUT.mkdir(exist_ok=False)
    temporary = OUTPUT / 'A1_JUNYI_SELECTED.pt.partial'
    with source.open('rb') as original, temporary.open('xb') as target:
        shutil.copyfileobj(original, target, length=1024 * 1024)
        target.flush()
        os.fsync(target.fileno())
    assert sha(temporary) == checkpoint_sha and temporary.stat().st_size == plan['bytes']
    temporary.rename(OUTPUT / 'A1_JUNYI_SELECTED.pt')
    with zipfile.ZipFile(OUTPUT / 'SUPPORT.zip', 'x', zipfile.ZIP_DEFLATED) as saved:
        for name, path in sources.items():
            saved.write(path, name)
        saved.write(HERE / 'comparison-audit.json', 'comparison-audit.json')
    index = {'model': 'A1_EXPERT', 'dataset': 'Junyi', 'phase': 'selected_fit80', 'batch_size': 128,
             'selected_epoch': 9, 'complete_epochs': 12, 'checkpoint_file': 'A1_JUNYI_SELECTED.pt',
             'checkpoint_sha256': checkpoint_sha, 'checkpoint_bytes': plan['bytes'], 'metadata': metadata,
             'selection_metrics': terminal['validation'],
             'model_class': 'knowledge_tracing.akt.research_junyi_graph_model.JunyiGraphAKTAdapter',
             'graph_enabled': True, 'graph_condition_sha256': terminal['graph_condition_sha256'],
             'context_backend': 'compact-a1-v1', 'support_sha256': sha(OUTPUT / 'SUPPORT.zip'),
             'support_inventory': pins, 'comparison_audit': comparison, 'refit_completed': False,
             'calibration_completed': False, 'independent_evaluation_completed': False,
             'source_checkpoint': plan['source_checkpoint']}
    write(OUTPUT / 'MODEL_INDEX.json', index)
    (OUTPUT / 'README.md').write_text('''# A1 Junyi đã chọn checkpoint

`A1_JUNYI_SELECTED.pt` giữ nguyên checkpoint epoch 9, chọn sau 12 epoch theo min_delta 0,0001 và patience 3. A1 dùng backbone AKT NonRasch, đồ thị tiên quyết cố định và hệ số ảnh hưởng đồ thị được học. Cấu hình seed 42, batch train 128 và vocabulary 717 bài tập.

Một file .pt giữ model_state_dict, optimizer_state_dict, RNG và tiến độ gốc. MODEL_INDEX.json chứa cấu hình, nguồn và phạm vi. SUPPORT.zip giữ source, encoding, graph và bằng chứng dựng lại. Dự đoán cần đúng JunyiGraphAKTAdapter, vocabulary, graph và lịch sử quá khứ theo source. Nạp file bằng torch.load với map_location="cpu", weights_only=True trong .venv của KLTN.

Pipeline đã nạp lại checkpoint và xuất đủ 1.600.343 dự đoán selection khớp lượt chọn epoch. Refit, calibration và đánh giá độc lập còn chờ. A0–A1 khớp dữ liệu và cấu hình học. A0 chọn epoch bằng validation batch 1, epoch 9 đã replay batch 128 với cùng Log Loss. Ranking toàn 12 epoch A0 bằng batch 128 còn chưa replay.

Toàn bộ gói nằm trên D. Checkpoint trung gian, predictions và logs giữ nguyên tại output theo run. Phép kiểm export chỉ nạp trọng số/schema trên CPU, chưa kiểm một API inference độc lập từ riêng thư mục này.
''', encoding='utf-8')
    assert sha(source) == checkpoint_sha
    write(HERE / 'export-result.json', {'status': 'EXPORTED_A1_SELECTED_ON_D', 'output': str(OUTPUT),
          'checkpoint_sha256': checkpoint_sha, 'checkpoint_bytes': plan['bytes'],
          'source_unchanged': True, 'files': sorted(path.name for path in OUTPUT.iterdir())})
    print(json.dumps({'status': 'EXPORTED_A1_SELECTED_ON_D', 'output': str(OUTPUT), 'checkpoint_bytes': plan['bytes']}))


if __name__ == '__main__':
    main()
