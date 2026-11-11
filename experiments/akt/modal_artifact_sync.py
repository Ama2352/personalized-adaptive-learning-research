"""Đồng bộ checkpoint đã đóng từ native filesystem, giữ marker hoàn tất cuối."""
import hashlib
import json
import os
from pathlib import Path
import shutil


def sha_file(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def copy_complete_checkpoint(source, destination):
    source, destination = Path(source), Path(destination)
    expected_files = {'state.pt', 'metadata.json', 'COMPLETE.json'}
    assert source.is_dir() and {p.name for p in source.iterdir()} == expected_files
    assert not any(p.is_symlink() for p in source.iterdir())
    assert (source/'metadata.json').stat().st_size <= 1024**2
    assert (source/'COMPLETE.json').stat().st_size <= 1024**2
    assert (source/'state.pt').stat().st_size <= 64*1024**2
    metadata = json.loads((source/'metadata.json').read_bytes())
    complete = json.loads((source/'COMPLETE.json').read_bytes())
    assert sha_file(source/'metadata.json') == complete['metadata_sha256']
    assert sha_file(source/'state.pt') == metadata['checkpoint_sha256'] == complete['checkpoint_sha256']
    assert (source/'state.pt').stat().st_size == metadata['checkpoint_bytes']
    pins = {name: sha_file(source/name) for name in expected_files}
    destination.mkdir(parents=True, exist_ok=True)
    assert not destination.is_symlink()
    assert {p.name for p in destination.iterdir()} <= expected_files
    # Marker cuối chỉ xuất hiện sau khi cả state và metadata đã được đối chiếu.
    for name in ('state.pt', 'metadata.json', 'COMPLETE.json'):
        target = destination/name
        assert not target.is_symlink()
        if target.exists():
            assert sha_file(target) == pins[name], 'durable checkpoint differs, preserve for investigation'
        else:
            with (source/name).open('rb') as incoming, target.open('xb') as outgoing:
                shutil.copyfileobj(incoming, outgoing, length=1024**2)
                outgoing.flush()
                os.fsync(outgoing.fileno())
            assert sha_file(target) == pins[name]
    assert all(sha_file(source/name) == pin for name, pin in pins.items())
    return dict(checkpoint_sha256=pins['state.pt'], complete_sha256=pins['COMPLETE.json'],
                bytes=metadata['checkpoint_bytes'])
