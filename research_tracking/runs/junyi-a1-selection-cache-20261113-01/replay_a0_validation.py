"""Kiểm checkpoint A0 đã chọn trên selection, không chọn lại epoch."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import time


def replay(config, inputs, encoding, operation, original_reference, plan_path):
    import torch
    from knowledge_tracing.akt.model import AKTAdapter
    from knowledge_tracing.akt.research_junyi_data import iter_junyi_phase_learners
    from knowledge_tracing.akt.research_junyi_selection import _evaluate
    from knowledge_tracing.akt.training import EarlyStopping

    plan = json.loads(Path(plan_path).read_text())
    assert [row['epoch'] for row in plan['checkpoints']] == [9]
    adapter = AKTAdapter(config, encoding.native)
    results = []
    started = time.monotonic()
    output = operation / 'a0-validation-replay.json'
    for row in plan['checkpoints']:
        path = Path(row['remote_path'])
        with path.open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == row['sha256']
        payload = torch.load(path, map_location='cpu', weights_only=True)
        assert payload['progress']['complete'] is True and payload['progress']['epoch'] == row['epoch']
        assert tuple(payload['encoding']['values']) == encoding.native.vocabulary.values
        assert payload['identity']['prediction_implementation'] == 'legacy_single_window_v1'
        adapter.native.load_state_dict(payload['model_state_dict'], strict=True)
        del payload
        adapter.checkpoint_id = row['sha256']
        before = time.monotonic()
        metrics = _evaluate(adapter, iter_junyi_phase_learners(inputs.paths, inputs.selection,
            temp_dir=config.project_root/'artifacts/akt/tmp'/config.run_id), inputs.selection_targets,
            batch_size=128)
        legacy = row['legacy_validation']
        for key in ('targets', 'supported', 'oov', 'population_sha256'):
            assert metrics[key] == legacy[key], ('A0 target mismatch', key)
        delta = abs(metrics['native_bce'] - legacy['native_bce'])
        result = dict(epoch=row['epoch'], metrics=metrics, legacy_metrics=legacy,
            seconds=time.monotonic()-before, absolute_log_loss_delta=delta)
        results.append(result)
        output.write_text(json.dumps(dict(status='IN_PROGRESS', results=results), indent=2)+'\n')
        assert delta < plan['max_absolute_log_loss_delta'], 'A0 validation loss exceeds frozen sufficient bound'
        print(json.dumps(dict(event='A0_VALIDATION_BATCH128_REPLAY', **result)), flush=True)
    output.write_text(json.dumps(dict(status='PASS_SELECTED_A0_CHECKPOINT_BATCH128', results=results,
        selected_epoch=9, a0_epoch_choice_replayed=False, seconds=time.monotonic()-started,
        scope='FULL_SELECTION_1600343_TARGETS_SELECTED_EPOCH9_INFERENCE_ONLY'), indent=2)+'\n')
    del adapter
    torch.cuda.empty_cache()
    reference = json.loads(Path(original_reference).read_text())
    reference['reference']['prediction_implementation'] = 'batched_windows_v1_batch128'
    reference['validation_batch_replay'] = dict(evidence=str(output),
        evidence_sha256=hashlib.sha256(output.read_bytes()).hexdigest(), selected_epoch=9,
        a0_epoch_choice_replayed=False, a0_historical_epoch_selection_mode='legacy_single_window_v1',
        adoption_reference='Người dùng chọn validation batch128 cho A1 ngày13/11/2026, ưu tiên training, giữ giới hạn chưa replay chọn epoch A0.',
        original_reference_sha256=hashlib.sha256(Path(original_reference).read_bytes()).hexdigest())
    destination = operation / 'a0-batched-comparison-reference.json'
    destination.write_text(json.dumps(reference, indent=2)+'\n')
    return destination
