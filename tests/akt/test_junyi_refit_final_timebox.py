"""Timebox cuối chỉ đổi deadline vận hành, giữ nguyên worker và identity model."""
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'experiments/akt'))
import modal_junyi_refit as controller


@pytest.fixture
def final_epoch(tmp_path, monkeypatch):
    monkeypatch.setattr(controller, 'ROOT', tmp_path)
    run = 'unit-a2-refit'
    prior = tmp_path / 'experiments/akt/results/unit-prior'
    relative = f'{run}/checkpoints/refit-batch-epoch-9-step-1200-abc/state.pt'
    checkpoint = prior / 'files/outputs' / relative
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b'checkpoint-fixture-only')
    digest = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    metadata = checkpoint.parent / 'metadata.json'
    metadata.write_text(json.dumps(dict(checkpoint_sha256=digest, checkpoint_bytes=checkpoint.stat().st_size)))
    marker = checkpoint.parent / 'COMPLETE.json'
    marker.write_text(json.dumps(dict(checkpoint_sha256=digest, metadata_sha256=hashlib.sha256(metadata.read_bytes()).hexdigest())))
    files = {}
    for path in (checkpoint, metadata, marker):
        key = path.relative_to(prior / 'files').as_posix()
        files[key] = dict(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    receipt = dict(status='PARTIAL_JUNYI_REFIT90', files=files,
        worker_result=dict(terminal=dict(complete_epochs=8, frozen_epochs=9)))
    (prior / 'remote-inventory.json').write_text(json.dumps(receipt))
    (prior / 'COMPLETE.json').write_text(json.dumps(dict(status='LOCAL_ARTIFACTS_VERIFIED_GPU_STOPPED')))
    (prior / 'app-budget-guard.json').write_text(json.dumps(dict(stop_acknowledged=True)))
    worker = dict(purpose='refit90', variant='A2', logical_run_id=run, frozen_epochs=9,
        refit_request=dict(path='refit.json', sha256='a' * 64),
        config=dict(phase='junyi-research', run_id=run, batch_size=128, seed=42,
            max_wall_seconds=600, max_seconds=580), profile=dict(max_vram_bytes=16 * 1024**3))
    request = dict(status='USER_APPROVED', approval_reference='synthetic-test', execution_id='unit-final',
        gpu='H100', child_timeout_seconds=360, function_timeout_seconds=400, watchdog_seconds=440,
        reserved_usd_per_run=.70, final_epoch_timebox=True,
        resume_checkpoint='experiments/akt/results/' + relative, resume_sha256=digest,
        resume_inventory=(prior / 'remote-inventory.json').relative_to(tmp_path).as_posix())
    return worker, request, prior, checkpoint


def test_verified_final_epoch_accepts_short_timebox_without_changing_config(final_epoch):
    worker, request, _, _ = final_epoch
    before = json.dumps(worker, sort_keys=True)
    result = controller.validate_refit_execution(request, worker)
    assert result['upper_usd'] < .70
    assert json.dumps(worker, sort_keys=True) == before


@pytest.mark.parametrize('mutation', ['flag', 'hash', 'unfinished', 'epoch', 'marker', 'stopped', 'cap'])
def test_short_timebox_rejects_unverified_or_unsafe_final_epoch(final_epoch, mutation):
    worker, request, prior, checkpoint = final_epoch
    if mutation == 'flag':
        request.pop('final_epoch_timebox')
    if mutation == 'hash':
        checkpoint.write_bytes(b'changed')
    if mutation == 'unfinished':
        (prior / 'COMPLETE.json').write_text(json.dumps(dict(status='DOWNLOADING')))
    if mutation == 'epoch':
        path = prior / 'remote-inventory.json'
        receipt = json.loads(path.read_text())
        receipt['worker_result']['terminal']['complete_epochs'] = 7
        path.write_text(json.dumps(receipt))
    if mutation == 'marker':
        (checkpoint.parent / 'COMPLETE.json').write_text('{}')
    if mutation == 'stopped':
        (prior / 'app-budget-guard.json').write_text(json.dumps(dict(stop_acknowledged=False)))
    if mutation == 'cap':
        request['reserved_usd_per_run'] = .10
    with pytest.raises((ValueError, PermissionError)):
        controller.validate_refit_execution(request, worker)
