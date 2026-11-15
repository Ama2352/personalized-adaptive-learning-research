"""Kiểm sao lưu Drive bằng filesystem tạm, không kết nối Google hoặc CUDA."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('colab_backup', ROOT/'research_tracking/runs/junyi-refit-pipeline-20261114-01/colab_a3_backup.py')
BACKUP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BACKUP)


def checkpoint(logical, name, content=b'synthetic-model'):
    folder = logical/'checkpoints'/name
    folder.mkdir(parents=True)
    (folder/'state.pt').write_bytes(content)
    metadata = dict(checkpoint_sha256=hashlib.sha256(content).hexdigest(),checkpoint_bytes=len(content))
    (folder/'metadata.json').write_text(json.dumps(metadata))
    (folder/'COMPLETE.json').write_text(json.dumps(dict(checkpoint_sha256=metadata['checkpoint_sha256'],
        metadata_sha256=BACKUP.sha(folder/'metadata.json'))))
    return folder


@pytest.fixture
def case(tmp_path):
    root = tmp_path/'project'
    logical = root/'experiments/akt/results/logical-a3'
    logical.mkdir(parents=True)
    (root/'gpu-stage-request.json').write_text(json.dumps(dict(logical_run_id='logical-a3',frozen_epochs=9)))
    (logical/'run-manifest.json').write_text('{}')
    operation = root/'experiments/akt/results/attempt-001-operation'
    operation.mkdir()
    (operation/'execution.json').write_text(json.dumps(dict(execution_id='attempt-001')))
    drive = tmp_path/'drive'
    drive.mkdir()
    return root,logical,operation,drive


def test_full_epoch_backup_and_repeat_preserve_manifest(case):
    root,logical,operation,drive = case
    checkpoint(logical,'epoch-003')
    manifest = BACKUP.backup(root,operation,drive)
    original = manifest.read_bytes()
    receipt = json.loads(original)
    assert receipt['complete_epochs'] == 3 and receipt['partial_epoch'] is None
    assert receipt['refit_complete'] is False
    (operation/'controller-result.json').write_text('{"status":"PASS"}')
    assert BACKUP.backup(root,operation,drive) == manifest
    assert manifest.read_bytes() == original
    pointer = json.loads((drive/'LATEST.json').read_text())
    assert pointer['sha256'] == BACKUP.sha(manifest)
    for relative,pin in receipt['files'].items():
        assert BACKUP.sha(drive/pin['drive_relative']) == pin['sha256']
        assert (root/relative).read_bytes() == (drive/pin['drive_relative']).read_bytes()


def test_partial_checkpoint_is_newer_than_prior_full_epoch(case):
    root,logical,operation,drive = case
    checkpoint(logical,'epoch-003')
    checkpoint(logical,'refit-batch-epoch-4-step-500-abcd')
    receipt = json.loads(BACKUP.backup(root,operation,drive).read_text())
    assert receipt['complete_epochs'] == 3 and receipt['partial_epoch'] == 4
    assert receipt['partial_optimizer_step'] == 500


def test_complete_epoch_wins_over_last_batch_of_same_epoch(case):
    root,logical,operation,drive = case
    checkpoint(logical,'epoch-003')
    checkpoint(logical,'refit-batch-epoch-3-step-2040-abcd')
    receipt = json.loads(BACKUP.backup(root,operation,drive).read_text())
    assert receipt['complete_epochs'] == 3 and receipt['partial_epoch'] is None


@pytest.mark.parametrize('filename',['state.pt','metadata.json'])
def test_tampered_source_rejected_before_publish(case,filename):
    root,logical,operation,drive = case
    folder = checkpoint(logical,'epoch-003')
    (folder/filename).write_bytes(b'corrupt')
    with pytest.raises((AssertionError,json.JSONDecodeError)):
        BACKUP.backup(root,operation,drive)
    assert not (drive/'LATEST.json').exists()


def test_existing_drive_file_corruption_is_detected(case):
    root,logical,operation,drive = case
    checkpoint(logical,'epoch-003')
    receipt = json.loads(BACKUP.backup(root,operation,drive).read_text())
    pin = receipt['files'][receipt['checkpoint']]
    (drive/pin['drive_relative']).write_bytes(b'changed')
    with pytest.raises(AssertionError):
        BACKUP.backup(root,operation,drive)


def test_restore_into_fresh_runtime_preserves_checkpoint(case,tmp_path):
    root,logical,operation,drive = case
    checkpoint(logical,'epoch-003')
    checkpoint(logical,'refit-batch-epoch-4-step-500-abcd')
    BACKUP.backup(root,operation,drive)
    fresh = tmp_path/'fresh'
    receipt = BACKUP.restore(fresh,drive)
    assert BACKUP.sha(fresh/receipt['checkpoint']) == receipt['checkpoint_sha256']
    assert BACKUP.restore(fresh,drive) == receipt


def test_restore_rejects_manifest_path_escape(case,tmp_path):
    root,logical,operation,drive = case
    checkpoint(logical,'epoch-003')
    BACKUP.backup(root,operation,drive)
    (drive/'LATEST.json').write_text(json.dumps(dict(manifest='../outside.json',sha256='a'*64)))
    with pytest.raises(AssertionError):
        BACKUP.restore(tmp_path/'fresh',drive)
