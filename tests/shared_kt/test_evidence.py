"""Evidence corruption phải bị phát hiện trước khi dùng để trích dẫn."""

import hashlib
import json

import pytest

from knowledge_tracing.evidence import verify_evidence_bundle
from knowledge_tracing.evidence import record_evidence_run
import knowledge_tracing.evidence as evidence_module


def test_evidence_bundle_detects_corruption_and_incomplete_run(tmp_path):
    data = tmp_path / 'result.json'
    data.write_text('{}', encoding='utf-8')
    manifest = {'status': 'completed', 'outputs_sha256': {'result.json': hashlib.sha256(data.read_bytes()).hexdigest()}}
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    assert verify_evidence_bundle(tmp_path)['artifacts'] == 1
    data.write_text('changed', encoding='utf-8')
    with pytest.raises(ValueError, match='mismatch'):
        verify_evidence_bundle(tmp_path)
    manifest['status'] = 'failed'
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    with pytest.raises(ValueError, match='incomplete'):
        verify_evidence_bundle(tmp_path)


def test_evidence_bundle_rejects_parent_path(tmp_path):
    (tmp_path / 'manifest.json').write_text(json.dumps({
        'status': 'completed', 'outputs_sha256': {'../outside': 'fake'}}), encoding='utf-8')
    with pytest.raises(ValueError, match='unsafe'):
        verify_evidence_bundle(tmp_path)


def test_recording_preserves_failure_and_rejects_reused_run_id(tmp_path, monkeypatch):
    monkeypatch.setattr(evidence_module.subprocess, 'check_output', lambda *args, **kwargs: 'synthetic-head\n')
    source = tmp_path / 'source.py'
    source.write_text('original', encoding='utf-8')
    with pytest.raises(RuntimeError, match='controlled failure'):
        with record_evidence_run(tmp_path, 'failure', metadata={'kind':'synthetic'}, sources=[source], note='Fixture'):
            raise RuntimeError('controlled failure')
    run = tmp_path / 'research_tracking/runs/failure'
    assert json.loads((run/'manifest.json').read_text())['status'] == 'failed'
    assert 'controlled failure' in (run/'execution.log').read_text()
    with pytest.raises(FileExistsError):
        with record_evidence_run(tmp_path, 'failure', metadata={}, sources=[source], note='Fixture'):
            pass


def test_recording_rejects_source_drift_before_completion(tmp_path, monkeypatch):
    monkeypatch.setattr(evidence_module.subprocess, 'check_output', lambda *args, **kwargs: 'synthetic-head\n')
    source = tmp_path / 'source.py'
    source.write_text('original', encoding='utf-8')
    with pytest.raises(ValueError, match='source changed'):
        with record_evidence_run(tmp_path, 'drift', metadata={}, sources=[source], note='Fixture'):
            source.write_text('changed', encoding='utf-8')
