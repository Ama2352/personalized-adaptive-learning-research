from concurrent.futures import ThreadPoolExecutor
import os
from threading import Barrier

import pytest

from knowledge_tracing.akt.filesystem import publish_new_file
import knowledge_tracing.akt.filesystem as filesystem


def test_publish_rejects_existing_destination_and_preserves_both_files(tmp_path):
    source = tmp_path / 'new.tmp'
    destination = tmp_path / 'existing.pt'
    source.write_bytes(b'new')
    destination.write_bytes(b'historical')
    with pytest.raises(FileExistsError):
        publish_new_file(source, destination)
    assert source.read_bytes() == b'new'
    assert destination.read_bytes() == b'historical'


def test_competing_publishers_have_one_winner_without_partial_output(tmp_path):
    destination = tmp_path / 'checkpoint.pt'
    barrier = Barrier(2)
    contents = [b'a' * 10000, b'b' * 10000]
    sources = [tmp_path / 'a.tmp', tmp_path / 'b.tmp']
    for source, content in zip(sources, contents):
        source.write_bytes(content)

    def publish(index):
        barrier.wait(timeout=10)
        try:
            publish_new_file(sources[index], destination)
            return True
        except FileExistsError:
            return False

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(publish, range(2)))
    assert sum(outcomes) == 1
    winner = outcomes.index(True)
    assert destination.read_bytes() == contents[winner]
    assert not sources[winner].exists()
    assert sources[1 - winner].read_bytes() == contents[1 - winner]


def test_publish_propagates_permission_failure_without_copy_fallback(tmp_path, monkeypatch):
    source = tmp_path / 'new.tmp'
    destination = tmp_path / 'checkpoint.pt'
    source.write_bytes(b'new')

    def deny(*args, **kwargs):
        raise PermissionError('filesystem denied publication')

    monkeypatch.setattr(filesystem.os, 'rename' if os.name == 'nt' else 'link', deny)
    with pytest.raises(PermissionError, match='denied'):
        publish_new_file(source, destination)
    assert source.read_bytes() == b'new'
    assert not destination.exists()
