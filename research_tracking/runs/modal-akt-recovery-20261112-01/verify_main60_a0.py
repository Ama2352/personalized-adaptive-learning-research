"""Đối chiếu độc lập archive Main60 A0 bằng stdlib, không nạp tensor."""
import csv
import hashlib
import io
import json
import math
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUN = 'modal-main60-a0-selected-20261112-01'
NATIVE = ROOT / 'experiments/akt/results' / RUN
PREFIX = f'experiments/akt/results/{RUN}/'


def digest(data):
    return hashlib.sha256(data).hexdigest()


receipt = json.loads((NATIVE / 'receipt.json').read_text())
archive = NATIVE / 'artifacts.zip'
with archive.open('rb') as stream:
    archive_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
assert archive_hash == receipt['archive_sha256']
assert archive.stat().st_size == receipt['archive_bytes']
with zipfile.ZipFile(archive) as bundle:
    assert bundle.testzip() is None

    def read(name):
        return bundle.read(PREFIX + name)

    def document(name):
        return json.loads(read(name))

    complete = document('COMPLETE.json')
    for name, expected in complete['outputs_sha256'].items():
        assert digest(read(name)) == expected, name
    claim = document('selected-claim.json')
    terminal = document('selected-terminal.json')
    epochs = document('fit80/epochs.json')
    coverage = document('selection/coverage.json')
    assert digest(read('selected-claim.json')) == complete['claim_sha256']
    assert digest(read('selected-terminal.json')) == claim['terminal']['sha256']
    assert claim['candidate_id'] == 'A0' and claim['estimator_graph'] == 'disabled'
    assert not claim['refit_started'] and not claim['calibration_used_for_selection']
    assert len(epochs) == claim['complete_fit_epochs'] == 8
    assert claim['selected_epoch'] == 5
    for epoch in epochs:
        assert epoch['receipt']['epoch_steps'] == 36
        assert epoch['receipt']['epoch_targets'] == 10080
    checkpoints = receipt['checkpoint_transfers']
    for name, transfer in checkpoints.items():
        assert digest(read(f'checkpoints/{name}/state.pt')) == transfer['checkpoint_sha256']
        assert digest(read(f'checkpoints/{name}/COMPLETE.json')) == transfer['complete_sha256']
    assert len(checkpoints) == 5
    assert claim['checkpoint']['sha256'] == checkpoints['epoch-5']['checkpoint_sha256']
    predictions = list(csv.DictReader(io.StringIO(read('selection/predictions.csv').decode())))
    targets = list(csv.DictReader(io.StringIO(read('selection/targets.csv').decode())))
    assert len(predictions) == len(targets) == coverage['supported_targets'] == 1260
    assert coverage['unsupported_targets'] == 0
    keys = ('learner_id', 'item_id', 'timestamp', 'source_row', 'global_rank', 'history_sha256')
    identities = [tuple(row[key] for key in keys) for row in predictions]
    assert len(set(identities)) == 1260
    assert identities == [tuple(row[key] for key in keys) for row in targets]
    assert len({row['learner_id'] for row in targets}) == 6
    losses, briers = [], []
    for prediction, target in zip(predictions, targets):
        probability, label = float(prediction['probability']), int(target['correct'])
        assert math.isfinite(probability) and 0 < probability < 1
        assert prediction['support_reason'] == 'supported'
        losses.append(-label * math.log(probability) - (1-label) * math.log1p(-probability))
        briers.append((probability-label)**2)
    assert abs(sum(losses)/1260 - coverage['full_metrics']['log_loss']) < 1e-12
    assert abs(sum(briers)/1260 - coverage['full_metrics']['brier']) < 1e-12
    for name in ('fit80/epochs.json', 'selection/coverage.json', 'events.jsonl'):
        output = Path(__file__).parent / ('main60-a0__' + name.replace('/', '__'))
        if output.exists():
            assert output.read_bytes() == read(name)
        else:
            output.write_bytes(read(name))

result = dict(
    status='VERIFIED_MAIN60_A0_CUDA_SELECTED', archive_sha256=archive_hash,
    archive_bytes=archive.stat().st_size, epochs=8, selected_epoch=5,
    optimizer_updates=288, physical_train_target_exposures=80640,
    selection_learners=6, prediction_rows=1260, checkpoints=5,
    independently_recomputed_metrics={key: coverage['full_metrics'][key] for key in ('log_loss', 'brier')},
    selection_metrics=coverage['full_metrics'],
    calibration_used_for_selection=False, refit_complete=False,
    comparative_graph_evidence=False, remote_controller_seconds=receipt['elapsed_seconds'],
    limits='Tập selection đã dùng chọn epoch. Chưa là kết quả đánh giá độc lập hoặc so sánh CG-AKT. Hardware model chưa được ghi riêng trong worker này.'
)
output = Path(__file__).with_name('main60-a0-verification.json')
with output.open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(result, ensure_ascii=False))
