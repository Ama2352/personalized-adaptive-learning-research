"""Kiểm allowlist và ZIP bằng fixture nhỏ, không đọc dữ liệu nghiên cứu."""
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile

import pytest

SPEC = importlib.util.spec_from_file_location('calibration_cloud_inputs',
    Path(__file__).resolve().parents[2] / 'scripts/akt/prepare_junyi_calibration_cloud.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


@pytest.mark.parametrize('path', ['../x', '/absolute', 'x\\y', 'a/private/key', 'a/holdout/x',
                                 'a//b', 42, 'C:/escape', 'a\nb', 'x' * 241])
def test_archive_path_rejects_unsafe_names(path):
    with pytest.raises(ValueError):
        module.relative_path(path)


def test_public_source_path_accepted():
    assert str(module.relative_path('src/knowledge_tracing/akt/config.py')).endswith('config.py')


@pytest.fixture
def tiny(tmp_path, monkeypatch):
    # Thay duy nhất Path('/tmp') để kiểm cloud-path contract trên Windows.
    original = module.Path
    def cloud_path(value):
        return tmp_path if value == '/tmp' else original(value)
    monkeypatch.setattr(module, 'Path', cloud_path)
    source = tmp_path / 'source'
    source.mkdir()
    payload = source / 'config.json'
    payload.write_text('{"seed":42}', encoding='utf-8')
    row = dict(path='config.json', bytes=payload.stat().st_size,
               sha256=hashlib.sha256(payload.read_bytes()).hexdigest())
    plan = dict(schema='junyi-calibration-cloud-inputs-v1', files=[row], bytes=row['bytes'])
    monkeypatch.setattr(module, 'allowed_paths', lambda root: ['config.json'])
    return source, payload, plan, tmp_path / 'inputs.zip'


def test_streaming_archive_exact_files_and_pin(tiny):
    source, payload, plan, output = tiny
    receipt = module.write_archive(source, plan, output, max_total_bytes=1024)
    with zipfile.ZipFile(output) as archive:
        assert archive.namelist() == ['config.json', 'CLOUD_INPUT_PLAN.json']
        assert archive.read('config.json') == payload.read_bytes()
        assert json.loads(archive.read('CLOUD_INPUT_PLAN.json')) == plan
    assert receipt['sha256'] == hashlib.sha256(output.read_bytes()).hexdigest()


def test_modified_payload_stops_before_archive_creation(tiny):
    source, payload, plan, output = tiny
    payload.write_bytes(b'changed')
    with pytest.raises(ValueError, match='pin'):
        module.write_archive(source, plan, output, max_total_bytes=1024)
    assert not output.exists()


def test_duplicate_or_budget_stops_before_archive(tiny):
    source, _, plan, output = tiny
    with pytest.raises(ValueError, match='giới hạn'):
        module.write_archive(source, plan, output, max_total_bytes=1)
    plan['files'] *= 2
    with pytest.raises(ValueError, match='giới hạn'):
        module.write_archive(source, plan, output, max_total_bytes=1024)


def test_local_output_rejected(tiny):
    source, _, plan, _ = tiny
    with pytest.raises(ValueError, match='cloud'):
        module.write_archive(source, plan, source.parent.parent / 'outside.zip', max_total_bytes=1024)


def test_change_between_preflight_and_zip_write_detected(tiny, monkeypatch):
    source, payload, plan, output = tiny
    original_hash = module.sha256
    def mutate_after_hash(path):
        digest = original_hash(path)
        if path == payload:
            payload.write_bytes(b'z' * payload.stat().st_size)
        return digest
    monkeypatch.setattr(module, 'sha256', mutate_after_hash)
    with pytest.raises(ValueError, match='trong lúc'):
        module.write_archive(source, plan, output, max_total_bytes=1024)
