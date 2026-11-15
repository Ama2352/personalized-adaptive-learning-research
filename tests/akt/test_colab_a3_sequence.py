"""Chuỗi training cố định dừng khi đủ9epoch, lỗi hoặc thiếu tiến triển."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT/'research_tracking/runs/junyi-refit-pipeline-20261114-01'
SPEC = importlib.util.spec_from_file_location('a3_sequence', HERE/'colab_a3_tranche.py')
SEQUENCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SEQUENCE)


@pytest.fixture
def case(tmp_path,monkeypatch):
    monkeypatch.syspath_prepend(str(HERE))
    transfer = tmp_path/'transfer'
    drive = tmp_path/'drive'
    transfer.mkdir()
    drive.mkdir()
    monkeypatch.setattr(SEQUENCE,'TRANSFER',transfer)
    return transfer,drive


def receipt_for(drive,attempt,epoch,step=None):
    partial = step is not None
    name = f'refit-batch-epoch-{epoch}-step-{step}-abcd' if partial else f'epoch-{epoch:03}'
    receipt = dict(status='PASS_DRIVE_CHECKPOINT_BACKUP',frozen_epochs=9,
        checkpoint=f'experiments/akt/results/logical/checkpoints/{name}/state.pt',checkpoint_sha256='a'*64,
        complete_epochs=epoch-1 if partial else epoch,partial_epoch=epoch if partial else None,
        partial_optimizer_step=step,refit_complete=epoch==9 and not partial)
    manifest = drive/f'backup-{attempt}.json'
    manifest.write_text(json.dumps(receipt))
    (drive/'LATEST.json').write_text(json.dumps(dict(manifest=manifest.name,
        sha256=hashlib.sha256(manifest.read_bytes()).hexdigest())))
    return dict(status='PASS_BOUNDED_NATIVE_WORKER',child_running=False,drive_backup=str(manifest))


def test_stops_immediately_after_ninth_epoch(case,monkeypatch):
    _,drive = case
    calls = []
    def run(attempt,*args):
        calls.append(attempt)
        return receipt_for(drive,attempt,9)
    monkeypatch.setattr(SEQUENCE,'run',run)
    state = SEQUENCE.run_sequence(1,'checkpoints/epoch-008/state.pt','a'*64,drive,5,10800)
    assert calls == [1]
    assert state['status'] == 'COMPLETE_9_EPOCHS_DRIVE_BACKED_UP'


def test_resumes_from_exact_backup_after_each_tranche(case,monkeypatch):
    _,drive = case
    inputs = []
    def run(attempt,checkpoint,digest,*args):
        inputs.append((attempt,checkpoint,digest))
        return receipt_for(drive,attempt,4,attempt*500)
    monkeypatch.setattr(SEQUENCE,'run',run)
    state = SEQUENCE.run_sequence(1,'checkpoints/epoch-003/state.pt','b'*64,drive,2,10800)
    assert state['status'] == 'TRANCHE_LIMIT_CHECKPOINT_SAVED'
    assert inputs[1][1].endswith('refit-batch-epoch-4-step-500-abcd/state.pt')
    assert inputs[1][2] == 'a'*64


def test_stops_on_checkpoint_without_progress(case,monkeypatch):
    _,drive = case
    calls = []
    def run(attempt,*args):
        calls.append(attempt)
        return receipt_for(drive,attempt,3)
    monkeypatch.setattr(SEQUENCE,'run',run)
    with pytest.raises(AssertionError,match='tiến triển'):
        SEQUENCE.run_sequence(1,'checkpoints/epoch-003/state.pt','a'*64,drive,3,10800)
    assert calls == [1]
    assert json.loads((drive/'SEQUENCE_STATUS.json').read_text())['status']=='STOPPED_REQUIRES_REVIEW'


def test_stops_when_training_or_backup_fails(case,monkeypatch):
    _,drive = case
    def run(*args):
        raise RuntimeError('backup failed')
    monkeypatch.setattr(SEQUENCE,'run',run)
    with pytest.raises(RuntimeError,match='backup failed'):
        SEQUENCE.run_sequence(1,'checkpoints/epoch-003/state.pt','a'*64,drive,3,10800)
    assert json.loads((drive/'SEQUENCE_STATUS.json').read_text())['status']=='STOPPED_REQUIRES_REVIEW'
