"""Nghiệm thu A3 đã hoàn tất và xuất một model chính trên D."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'experiments/akt')]
from junyi_staged_io import sha, write_new


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    state = read(HERE / 'STATE.json')
    assert state['status'] == 'A3_SELECTED_COMPLETE_PENDING_FINAL_ACCEPTANCE'
    run = ROOT / state['latest_output']
    logical = run / 'files/outputs/junyi-a3-expert-selected-20261114-01'
    remote, complete = read(run / 'remote-inventory.json'), read(run / 'COMPLETE.json')
    terminal = read(logical / 'selected-terminal.json')
    assert terminal == remote['worker_result']['terminal']
    assert terminal['status'] == 'JUNYI_A3_SELECTED_ONLY_COMPLETE'
    assert terminal['full_role_coverage'] and terminal['comparison_population_matched']
    epochs, chosen = terminal['complete_epochs'], terminal['selected_epoch']
    from knowledge_tracing.akt.training import EarlyStopping
    stopper = EarlyStopping(patience=3, min_delta=.0001)
    for row in terminal['history']:
        stopped = stopper.observe(row['epoch'], row['validation']['native_bce'])
        assert not stopped or row['epoch'] == epochs
    assert stopper.best_epoch == chosen
    assert stopper.stale_epochs >= 3 or epochs == 20
    assert terminal['optimizer_steps'] == epochs * 1818
    assert terminal['trained_targets'] == epochs * 13347331
    checkpoint = logical / f'checkpoints/epoch-{chosen:03}/state.pt'
    metadata = read(checkpoint.parent / 'metadata.json')
    assert sha(checkpoint) == terminal['checkpoint_sha256'] == metadata['checkpoint_sha256']
    import torch
    torch.set_num_threads(1)
    payload = torch.load(checkpoint, map_location='cpu', weights_only=True)
    assert payload['identity'] == metadata['identity'] and payload['progress']['epoch'] == chosen
    assert payload['optimizer_state_dict']['state'] and len(payload['cuda_rng']) == 1
    assert all(key in payload for key in ('python_rng', 'numpy_rng', 'torch_rng'))
    assert all(torch.isfinite(value).all().item() for value in payload['model_state_dict'].values())
    learned_graph_parameters = {name: value.detach().cpu().tolist()
        for name, value in payload['model_state_dict'].items() if 'gate.' in name or name.endswith('alpha')}
    assert any('gate.weight' in name for name in learned_graph_parameters)
    assert any('gate.bias' in name for name in learned_graph_parameters)
    del payload
    request = read(ROOT / 'artifacts/akt/staged/junyi-a3-expert-20261114-03/project/gpu-stage-request.json')
    from knowledge_tracing.akt.comparison_contract import TRAINING_FIELDS, require_matched_candidate
    reference = read(ROOT / request['comparison_reference_file'])['reference']
    admission = read(next(logical.glob('comparison-admission-*.json')))
    candidate = dict(admission['candidate'], observed_selection_population_sha256=terminal['validation']['population_sha256'])
    require_matched_candidate(reference, candidate, observed=True)
    assert reference['initial_backbone_sha256'] == terminal['initial_backbone_sha256']
    peers = []
    for folder in ('model-export-a0-batch128-20261112-01',
                   'model-export-a1-batch128-20261113-01', 'model-export-a2-batch128-20261114-01'):
        peer = read(ROOT / 'experiments/akt/results' / folder / 'MODEL_INDEX.json')
        identity = peer['metadata']['identity']
        assert all(identity['config'][key] == metadata['identity']['config'][key] for key in TRAINING_FIELDS)
        assert identity['inputs'] == metadata['identity']['inputs']
        assert identity['encoding'] == metadata['identity']['encoding']
        assert peer['selection_metrics']['population_sha256'] == terminal['validation']['population_sha256']
        peers.append(dict(model=peer['model'], selected_epoch=peer['selected_epoch'],
            complete_epochs=peer['complete_epochs'], native_bce=peer['selection_metrics']['native_bce']))
    # Tái dùng chính hàm kiểm/chấm prediction đã áp dụng cho A2, không sửa hồ sơ cũ.
    scoring_source = ROOT / 'research_tracking/runs/junyi-confidence-completion-20261114-01/finalize_a2_selected.py'
    specification = importlib.util.spec_from_file_location('a2_verified_scoring', scoring_source)
    scoring = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(scoring)
    predictions = logical / terminal['predictions_file']
    assert sha(predictions) == terminal['predictions_sha256']
    metrics = scoring.score_predictions(predictions, terminal)
    metrics['scoring_helper_sha256'] = sha(scoring_source)
    write_new(HERE / 'a3-selection-metrics.json', metrics)
    comparison = dict(status='MATCHED_DEVELOPMENT_SELECTION_INDEPENDENT_EVALUATION_PENDING',
        training_fields_matched=list(TRAINING_FIELDS), rows=1600343, initial_backbone_matched=True,
        models=peers + [dict(model='A3_EXPERT', selected_epoch=chosen, complete_epochs=epochs,
                            native_bce=terminal['validation']['native_bce'])],
        a0_full_epoch_choice_replayed_batch128=False,
        limits_vi='Một seed, selection dùng chọn epoch. A0 lịch sử chọn bằng batch1, chỉ epoch9 đã replay128. '
        'Đánh giá độc lập, bất định và tác động lộ trình còn chờ.')
    write_new(HERE / 'a3-comparison-audit.json', comparison)
    write_new(HERE / 'a3-learned-graph-parameters.json', dict(
        checkpoint_epoch=chosen, parameters=learned_graph_parameters,
        limits_vi='Trọng số đã học. Chưa đo phân bố gate theo từng target hay hiệu ứng graph-off trên tập độc lập.'))
    acceptance = dict(status='PASS_A3_SELECTED_FIT80_ARTIFACT_AND_PREDICTION_CONTRACT',
        selected_epoch=chosen, complete_epochs=epochs, train_targets_per_epoch=13347331,
        selection_targets=1600343, checkpoint_sha256=sha(checkpoint),
        probability_sha256=terminal['validation']['probability_sha256'], predictions_sha256=sha(predictions),
        archive_sha256=complete['archive_sha256'], archive_files=complete['files'],
        optimizer_rng_verified=True, checkpoint_tensors_finite=True, chronology_verified=True,
        early_stopping_replayed_from_history=True,
        model_comparison_boundary_verified=True, refit_completed=False, calibration_completed=False,
        independent_evaluation_completed=False, gpu_stopped=True)
    write_new(HERE / 'a3-final-acceptance.json', acceptance)
    sources = {'source.zip': ROOT / 'artifacts/akt/modal/junyi-a2-a3-final-20261114-03/source.zip',
        'encoding.json': ROOT / request['inputs']['encoding_file'],
        'encoding-receipt.json': ROOT / request['inputs']['encoding_receipt'],
        'graph.json': ROOT / request['graph_file'], 'roles.json': ROOT / request['inputs']['roles_path'],
        'confidence.json': ROOT / request['confidence_file'],
        'confidence-fit-manifest.json': ROOT / request['confidence_fit_artifact'],
        'selected-request.json': ROOT / 'artifacts/akt/staged/junyi-a3-expert-20261114-03/project/gpu-stage-request.json',
        'execution-controller.py': ROOT / 'experiments/akt/modal_junyi_staged.py',
        'execution-artifact-io.py': ROOT / 'experiments/akt/junyi_staged_io.py',
        'execution-controller-tests.py': ROOT / 'tests/akt/test_junyi_staged_local.py',
        'execution-controller-tests.log': HERE / 'local-regression02.log',
        'runtime-linux-cuda.lock.txt': ROOT / request['runtime_lock_file'],
        'runtime-cuda.json': run / 'files/outputs' / (run.name + '-operation') / 'runtime.json',
        'upstream-identity.json': HERE / 'snapshot-dependency-verification.json',
        'upstream-LICENSE': ROOT / 'artifacts/akt/staged/junyi-a3-expert-20261114-03/project/artifacts/akt/dependencies/upstream/LICENSE',
        'comparison-audit.json': HERE / 'a3-comparison-audit.json',
        'selection-metrics.json': HERE / 'a3-selection-metrics.json',
        'learned-graph-parameters.json': HERE / 'a3-learned-graph-parameters.json',
        'acceptance.json': HERE / 'a3-final-acceptance.json'}
    pins = {name: dict(source=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size, sha256=sha(path))
            for name, path in sources.items()}
    export = ROOT / 'experiments/akt/results/model-export-a3-batch128-20261114-01'
    assert not export.exists() and export.resolve().drive.upper() == 'D:'
    write_new(HERE / 'a3-export-plan.json', dict(source_checkpoint=checkpoint.relative_to(ROOT).as_posix(),
        checkpoint_sha256=sha(checkpoint), destination=str(export), support_inputs=pins))
    building = export.with_name(export.name + '.building')
    building.mkdir(exist_ok=False)
    model = building / 'A3_JUNYI_SELECTED.pt'
    with checkpoint.open('rb') as original, model.open('xb') as target:
        shutil.copyfileobj(original, target, 1024 * 1024)
        target.flush()
        os.fsync(target.fileno())
    assert sha(model) == terminal['checkpoint_sha256']
    with zipfile.ZipFile(building / 'SUPPORT.zip', 'x', zipfile.ZIP_DEFLATED) as saved:
        for name, path in sources.items():
            assert sha(path) == pins[name]['sha256']
            saved.write(path, name)
    with zipfile.ZipFile(building / 'SUPPORT.zip') as saved:
        assert set(saved.namelist()) == set(pins)
        assert all(hashlib.sha256(saved.read(name)).hexdigest() == pin['sha256'] for name, pin in pins.items())
    index = dict(model='A3_EXPERT', dataset='Junyi', phase='selected_fit80', batch_size=128,
        selected_epoch=chosen, complete_epochs=epochs, checkpoint_file=model.name,
        checkpoint_sha256=sha(model), checkpoint_bytes=model.stat().st_size, metadata=metadata,
        selection_metrics=terminal['validation'], standard_selection_metrics=metrics,
        model_class='knowledge_tracing.akt.research_junyi_graph_model.JunyiGraphAKTAdapter',
        variant='A3', graph_enabled=True, compact_context=True,
        graph_condition_sha256=terminal['graph_condition_sha256'],
        support_sha256=sha(building / 'SUPPORT.zip'), support_inventory=pins,
        comparison_audit=comparison, source_checkpoint=checkpoint.relative_to(ROOT).as_posix(),
        refit_completed=False, calibration_completed=False, independent_evaluation_completed=False)
    write_new(building / 'MODEL_INDEX.json', index)
    (building / 'README.md').write_text(
        f'# A3 Junyi đã chọn checkpoint\n\nA3 dùng AKT NonRasch, confidence từng cạnh fit trên TRAIN80 '
        f'và cổng học điều chỉnh ảnh hưởng đồ thị. Hoàn tất {epochs}epoch, chọn epoch{chosen}, '
        'seed42, batch train/selection128, vocabulary717bài tập.\n\n'
        '`A3_JUNYI_SELECTED.pt` giữ nguyên model, Adam, RNG và tiến độ. `MODEL_INDEX.json` giữ cấu hình '
        'và phạm vi. `SUPPORT.zip` giữ source, graph, confidence và runtime/provenance. '
        'Đã nạp lại và xuất đủ1.600.343dự đoán selection khớp,0OOV.\n\n'
        'Refit, calibration, đánh giá độc lập và API inference riêng từ gói export còn chờ. '
        'Checkpoint/predictions/logs trung gian giữ tại output theo run trên D.\n', encoding='utf-8')
    assert {path.name for path in building.iterdir()} == {'A3_JUNYI_SELECTED.pt', 'MODEL_INDEX.json', 'SUPPORT.zip', 'README.md'}
    building.rename(export)
    write_new(HERE / 'a3-export-result.json', dict(status='EXPORTED_A3_SELECTED_ON_D', output=str(export),
        checkpoint_sha256=sha(export / model.name), files=sorted(path.name for path in export.iterdir())))
    state.update(status='A3_SELECTED_FIT80_COMPLETE_ARTIFACTS_VERIFIED', selected_epoch=chosen,
                 complete_epochs=epochs, export_model=str(export / 'MODEL_INDEX.json'),
                 acceptance='a3-final-acceptance.json', refit_completed=False,
                 calibration_completed=False, independent_evaluation_completed=False)
    (HERE / 'STATE.json').write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=acceptance['status'], export=str(export), metrics=metrics['metrics'])))


if __name__ == '__main__':
    main()
