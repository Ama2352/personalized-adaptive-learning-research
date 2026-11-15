"""Chuỗi training cố định dừng khi đủ9epoch, lỗi hoặc thiếu tiến triển."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
from contextlib import nullcontext

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


def test_gpu_sampler_records_actual_fields_and_stops(tmp_path,monkeypatch):
    sampled = threading.Event()
    def query(*args,**kwargs):
        sampled.set()
        return SimpleNamespace(stdout='38, 5000, 15360, 65\n')
    monkeypatch.setattr(SEQUENCE.subprocess,'run',query)
    with SEQUENCE.measure_gpu(tmp_path):
        assert sampled.wait(2)
    event = json.loads((tmp_path/'gpu-telemetry.jsonl').read_text().splitlines()[0])
    assert event['gpu_utilization']==38 and event['vram_used_mib']==5000
    assert event['vram_total_mib']==15360


def test_gpu_sampler_failure_is_logged_without_model_step(tmp_path,monkeypatch):
    sampled = threading.Event()
    def query(*args,**kwargs):
        sampled.set()
        raise FileNotFoundError('nvidia-smi unavailable')
    monkeypatch.setattr(SEQUENCE.subprocess,'run',query)
    with SEQUENCE.measure_gpu(tmp_path):
        assert sampled.wait(2)
    event = json.loads((tmp_path/'gpu-telemetry.jsonl').read_text().splitlines()[0])
    assert event['error_type']=='FileNotFoundError'


def test_single_tranche_accepts_exact_prepared_uppercase_variant(case,tmp_path,monkeypatch):
    transfer,_ = case
    root = tmp_path/'project'
    root.mkdir()
    worker = json.loads((HERE/'stage-inputs-a3-short01.json').read_text())['worker']
    assert worker['variant']=='A3'
    (root/'gpu-stage-request.json').write_text(json.dumps(worker))
    checkpoint = root/'experiments/akt/results'/worker['logical_run_id']/'checkpoints/epoch-003/state.pt'
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b'fake state')
    (transfer/'runtime-verified.json').write_text(json.dumps(dict(status='PASS_ISOLATED_CUDA_RUNTIME')))
    monkeypatch.setattr(SEQUENCE,'ROOT',root)
    monkeypatch.setattr(SEQUENCE,'measure_gpu',lambda operation:nullcontext())
    class Worker:
        pid=123
        def __init__(self,command,**kwargs):
            execution = Path(command[-1])
            execution.with_name('result.json').write_text(json.dumps(dict(status='PARTIAL_JUNYI_REFIT90')))
        def wait(self,timeout):
            return 0
        def poll(self):
            return 0
    monkeypatch.setattr(SEQUENCE.subprocess,'Popen',Worker)
    result=SEQUENCE.run(1,checkpoint.relative_to(root).as_posix(),SEQUENCE.sha(checkpoint))
    assert result['status']=='PASS_BOUNDED_NATIVE_WORKER' and not result['child_running']
    assert not (transfer/'training.lock').exists()
