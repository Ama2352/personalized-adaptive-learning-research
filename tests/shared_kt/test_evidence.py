"""Evidence corruption phải bị phát hiện trước khi dùng để trích dẫn."""

import hashlib
import json

import pytest

from knowledge_tracing.evidence import verify_evidence_bundle


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
