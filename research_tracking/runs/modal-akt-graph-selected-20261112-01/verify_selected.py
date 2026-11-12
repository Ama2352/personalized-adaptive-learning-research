"""Nghiệm thu độc lập archive selected graph bằng stdlib, không importTorch."""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', required=True)
    args = parser.parse_args()
    allocation = json.loads((BUNDLE / 'allocation.json').read_text())
    request = json.loads((BUNDLE / allocation['candidate_requests'][args.candidate]).read_text())
    run_id = request['run_id']
    native = ROOT / 'experiments/akt/results' / run_id
    receipt = json.loads((native / 'receipt.json').read_text())
    assert receipt['status'] == 'CUDA_GRAPH_SELECTED_MAIN60_COMPLETE'
    assert receipt['download_inventory_verified'] is True
    assert receipt['worker_result']['candidate_id'] == args.candidate
    archive = native / 'artifacts.zip'
    with archive.open('rb') as stream:
        archive_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert archive_hash == receipt['archive_sha256']
    baseline = json.loads((ROOT / 'experiments/akt/results/modal-main60-a0-selected-20261112-01/receipt.json').read_text())['worker_result']['claim']
    with zipfile.ZipFile(archive) as saved:
        assert saved.testzip() is None
        prefix = f'experiments/akt/results/{run_id}/'

        def read(name):
            return saved.read(prefix + name)

        def document(name):
            return json.loads(read(name))

        complete = document('COMPLETE.json')
        for name, expected in complete['outputs_sha256'].items():
            assert digest(read(name)) == expected, name
        claim = document('selected-claim.json')
        terminal = document('selected-terminal.json')
        epochs = document('fit80/epochs.json')
        coverage = document('selection/coverage.json')
        assert claim['candidate_id'] == args.candidate
        assert digest(read('selected-claim.json')) == complete['claim_sha256']
        assert digest(read('selected-terminal.json')) == claim['terminal']['sha256']
        assert not claim['refit_started'] and not claim['calibration_used_for_selection']
        assert terminal['fresh_best_reload'] is True
        assert claim['initial_backbone_sha256'] == baseline['initial_backbone_sha256']
        assert claim['targets']['sha256'] == baseline['targets']['sha256']
        assert claim['context'] == baseline['context']
        assert claim['encoding_sha256'] == baseline['encoding_sha256']
        bound = json.loads((ROOT / request['condition_file']).read_text())
        assert claim['graph_condition_sha256'] == bound['main_graph_input']['implementation_condition_sha256']
        assert claim['graph_train_role_sha256'] == bound['train80']['train_shard_sha256']
        assert len(epochs) == claim['complete_fit_epochs'] <= 20
        for epoch in epochs:
            assert epoch['receipt']['epoch_steps'] == 36
            assert epoch['receipt']['epoch_targets'] == 10080
        selected = claim['selected_epoch']
        transfer = receipt['checkpoint_transfers'][f'epoch-{selected}']
        assert transfer['checkpoint_sha256'] == claim['checkpoint']['sha256']
        for name, checkpoint in receipt['checkpoint_transfers'].items():
            assert digest(read(f'checkpoints/{name}/state.pt')) == checkpoint['checkpoint_sha256']
            assert digest(read(f'checkpoints/{name}/COMPLETE.json')) == checkpoint['complete_sha256']
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
        counters = terminal['counters']
        assert counters['complete'] == 36 * len(epochs)
        assert counters['complete_targets'] == 10080 * len(epochs)
        for name in ('fit80/epochs.json', 'selection/coverage.json', 'events.jsonl'):
            output = BUNDLE / (args.candidate.lower() + '__' + name.replace('/', '__'))
            with output.open('xb') as stream:
                stream.write(read(name))
    result = dict(status='VERIFIED_MAIN60_GRAPH_CUDA_SELECTED', candidate_id=args.candidate, run_id=run_id,
        epochs=len(epochs), selected_epoch=selected, optimizer_updates=counters['complete'],
        physical_train_target_exposures=counters['complete_targets'], prediction_rows=1260,
        checkpoint_count=len(receipt['checkpoint_transfers']),
        initial_backbone_matches_A0=True, target_population_matches_A0=True,
        graph_condition_matches=True, calibration_used_for_selection=False,
        archive_sha256=archive_hash, archive_bytes=archive.stat().st_size,
        gpu_name=receipt['worker_result']['gpu_name'],
        remote_controller_seconds=receipt['elapsed_seconds'],
        selection_metrics=coverage['full_metrics'],
        limits='Số liệu selection đã dùng chọn epoch. Chưa là đánh giá độc lập hoặc kết quả Junyi/closed-loop.')
    with (BUNDLE / (args.candidate.lower() + '-verification.json')).open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
