"""Kiểm file giả cho bản sao checkpoint; không tạo model hoặc dùng GPU."""
import hashlib
import json
from pathlib import Path
import runpy

import pytest

sync = runpy.run_path('experiments/akt/modal_artifact_sync.py')['copy_complete_checkpoint']


def checkpoint(root):
    root.mkdir()
    (root/'state.pt').write_bytes(b'FAKE_FILE_BYTES_NO_MODEL')
    state = hashlib.sha256((root/'state.pt').read_bytes()).hexdigest()
    metadata = dict(checkpoint_sha256=state, checkpoint_bytes=(root/'state.pt').stat().st_size)
    (root/'metadata.json').write_text(json.dumps(metadata))
    (root/'COMPLETE.json').write_text(json.dumps(dict(checkpoint_sha256=state,
        metadata_sha256=hashlib.sha256((root/'metadata.json').read_bytes()).hexdigest())))
    return root


def test_copy_is_exact_and_repeat_preserves_bytes(tmp_path):
    source = checkpoint(tmp_path/'source')
    target = tmp_path/'durable'
    first = sync(source, target)
    before = {p.name: p.read_bytes() for p in target.iterdir()}
    assert sync(source, target) == first
    assert before == {p.name: p.read_bytes() for p in target.iterdir()}


@pytest.mark.parametrize('name', ['state.pt', 'metadata.json', 'COMPLETE.json'])
def test_corrupt_source_stops_before_durable_publication(tmp_path, name):
    source = checkpoint(tmp_path/'source')
    (source/name).write_bytes(b'corrupted')
    target = tmp_path/'durable'
    with pytest.raises((AssertionError, json.JSONDecodeError)):
        sync(source, target)
    assert not target.exists()


def test_existing_different_file_is_preserved(tmp_path):
    source = checkpoint(tmp_path/'source')
    target = tmp_path/'durable'; target.mkdir()
    (target/'state.pt').write_bytes(b'prior failed partial')
    with pytest.raises(AssertionError, match='preserve'):
        sync(source, target)
    assert (target/'state.pt').read_bytes() == b'prior failed partial'
    assert not (target/'COMPLETE.json').exists()


def test_partial_same_bytes_can_finish_without_overwrite(tmp_path):
    source = checkpoint(tmp_path/'source')
    target = tmp_path/'durable'; target.mkdir()
    (target/'state.pt').write_bytes((source/'state.pt').read_bytes())
    sync(source, target)
    assert (target/'COMPLETE.json').read_bytes() == (source/'COMPLETE.json').read_bytes()
