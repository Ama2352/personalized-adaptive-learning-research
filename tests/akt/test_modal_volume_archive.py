import asyncio
import hashlib
import io
import json
import threading
from types import SimpleNamespace
import zipfile

import pytest

from scripts.akt.modal_volume_archive import build_numeric_plan, iter_zip_bytes, make_plan, zip_size


class Volume:
    def __init__(self, content):
        self.content = content
        self.closed = 0
        self.read_file = self

    async def aio(self, path):
        try:
            data = self.content[path]
            for offset in range(0, len(data), 1024):
                await asyncio.sleep(0)
                yield data[offset:offset + 1024]
        finally:
            self.closed += 1


def fixture():
    content = {
        'junyi-calibration-real-20261117-01/a2-numeric/payloads/shard-000000.npz': b'a' * 16384,
        'junyi-calibration-real-20261117-01/a2-numeric/payloads/RECEIPT.json': b'{"status":"COMPLETE"}',
    }
    entries = [{'archive_name': path, 'volume_path': path, 'bytes': len(data),
                'sha256': hashlib.sha256(data).hexdigest()} for path, data in content.items()]
    return content, make_plan(entries)


def test_exact_size_roundtrip_and_determinism():
    content, plan = fixture()
    volume = Volume(content)
    data = b''.join(iter_zip_bytes(volume, plan, chunk_size=2048))
    assert len(data) == zip_size(plan)
    assert data == b''.join(iter_zip_bytes(Volume(content), plan, chunk_size=17))
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        assert {name: archive.read(name) for name in archive.namelist()} == content
        assert all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist())
        assert all(info.flag_bits & 8 for info in archive.infolist())
    assert volume.closed == 2


@pytest.mark.parametrize('mutation', ['bytes', 'hash'])
def test_source_mutation_fails(mutation):
    content, plan = fixture()
    key = next(iter(content))
    content[key] = b'x' * (len(content[key]) + (mutation == 'bytes'))
    with pytest.raises(ValueError, match='Nguồn|SHA/bytes'):
        b''.join(iter_zip_bytes(Volume(content), plan))


def test_plan_mutation_fails_before_read():
    content, plan = fixture()
    plan['entries'][0]['sha256'] = '0' * 64
    with pytest.raises(ValueError, match='Source plan'):
        next(iter_zip_bytes(Volume(content), plan))


def test_cancel_closes_reader_and_thread():
    content, plan = fixture()
    volume = Volume(content)
    stream = iter_zip_bytes(volume, plan, chunk_size=128, prefetch=1)
    next(stream)
    stream.close()
    assert volume.closed == 1
    assert not any(t.name == 'kltn-volume-zip' and t.is_alive() for t in threading.enumerate())


@pytest.mark.parametrize('path', ['../bad', 'junyi-calibration-real-20261117-01/a0-numeric/payloads/RECEIPT.json'])
def test_unapproved_path_rejected(path):
    with pytest.raises(ValueError):
        make_plan([{'archive_name': path, 'volume_path': path, 'bytes': 1, 'sha256': '0' * 64}])


def test_oversized_member_rejected():
    content, plan = fixture()
    entries = plan['entries']
    entries[0]['bytes'] = 2 * 1024**2 + 1
    with pytest.raises(ValueError, match='2 MiB'):
        make_plan(entries)


class ConcurrentVolume(Volume):
    def __init__(self, content, *, block_later=False):
        super().__init__(content)
        self.active = self.maximum = self.started = 0
        self.block_later = block_later

    async def aio(self, path):
        self.started += 1
        self.active += 1
        self.maximum = max(self.maximum, self.active)
        try:
            index = int(path.rsplit('-', 1)[1].split('.')[0])
            await asyncio.sleep(60 if self.block_later and index else 0.005)
            yield self.content[path]
        finally:
            self.active -= 1
            self.closed += 1


def concurrent_fixture():
    content = {f'junyi-calibration-real-20261117-01/a2-numeric/payloads/shard-{i:06d}.npz':
               bytes([i]) * (1024 + i) for i in range(8)}
    plan = make_plan([{'archive_name': p, 'volume_path': p, 'bytes': len(b),
                       'sha256': hashlib.sha256(b).hexdigest()} for p, b in content.items()])
    return content, plan


def test_ordered_prefetch_keeps_exact_zip_bytes_and_concurrency():
    content, plan = concurrent_fixture()
    serial, parallel = ConcurrentVolume(content), ConcurrentVolume(content)
    old = b''.join(iter_zip_bytes(serial, plan, prefetch=1))
    new = b''.join(iter_zip_bytes(parallel, plan, prefetch=4))
    assert old == new and len(new) == zip_size(plan)
    assert hashlib.sha256(old).digest() == hashlib.sha256(new).digest()
    assert serial.maximum == 1 and parallel.maximum == 4
    assert serial.closed == parallel.closed == 8


def test_cancel_closes_all_four_inflight_readers():
    content, plan = concurrent_fixture()
    volume = ConcurrentVolume(content, block_later=True)
    stream = iter_zip_bytes(volume, plan, prefetch=4)
    next(stream)
    stream.close()
    assert volume.maximum == 4 and volume.started == volume.closed >= 4
    assert volume.active == 0
    assert not any(t.name == 'kltn-volume-zip' and t.is_alive() for t in threading.enumerate())


def test_bad_sha_cancels_prefetched_readers_before_member_emission():
    content, plan = concurrent_fixture()
    first = next(iter(content))
    content[first] = b'z' * len(content[first])
    volume = ConcurrentVolume(content, block_later=True)
    with pytest.raises(ValueError, match='SHA/bytes'):
        b''.join(iter_zip_bytes(volume, plan, prefetch=4))
    assert volume.started == volume.closed == 4 and volume.active == 0


@pytest.mark.parametrize('prefetch', [0, 5, True])
def test_prefetch_budget_rejected(prefetch):
    content, plan = fixture()
    with pytest.raises(ValueError, match='Prefetch'):
        next(iter_zip_bytes(Volume(content), plan, prefetch=prefetch))


@pytest.mark.parametrize('tamper', [None, 'count', 'binding', 'manifest_sha'])
def test_numeric_plan_receipt_chain(tamper):
    directory = 'junyi-calibration-real-20261117-01/a2-numeric/payloads/'
    payload = b'fake-npz'
    binding = {'variant': 'A2', 'checkpoint_sha256': '1' * 64}
    manifest = {'kind': 'JUNYI_NUMERIC_PREDICTIONS_V1', 'binding': dict(binding),
                'shard_index': 0, 'windows': [{'window_id': 'w1', 'targets': 2}],
                'payload': 'shard-000000.npz', 'payload_sha256': hashlib.sha256(payload).hexdigest()}
    if tamper == 'binding':
        manifest['binding']['checkpoint_sha256'] = '2' * 64
    manifest_bytes = json.dumps(manifest).encode()
    counts = {'windows': 1, 'fitted_targets': 2}
    receipt = {'kind': 'JUNYI_CACHED_NUMERIC_INFERENCE_V1', 'status': 'COMPLETE',
               'binding': binding, 'counts': dict(counts), 'shards': [{
                   'manifest_path': '/__modal/volumes/test/' + directory + 'shard-000000.json',
                   'manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest()}]}
    if tamper == 'count':
        receipt['counts']['windows'] = 2
    if tamper == 'manifest_sha':
        receipt['shards'][0]['manifest_sha256'] = '0' * 64
    receipt_bytes = json.dumps(receipt).encode()
    content = {directory + 'RECEIPT.json': receipt_bytes,
               directory + 'shard-000000.json': manifest_bytes,
               directory + 'shard-000000.npz': payload}
    volume = Volume(content)

    class Listing:
        async def aio(self, path, recursive):
            assert path == directory and not recursive
            for name, data in content.items():
                yield SimpleNamespace(path=name, size=len(data))

    volume.iterdir = Listing()
    operation = build_numeric_plan(volume, variant='A2',
                                   receipt_sha256=hashlib.sha256(receipt_bytes).hexdigest(),
                                   expected_counts=counts)
    if tamper:
        with pytest.raises(ValueError):
            asyncio.run(operation)
    else:
        plan = asyncio.run(operation)
        assert len(plan['entries']) == 3
        assert volume.closed == 2  # Chỉ JSON, chưa đọc NPZ.
        archive = b''.join(iter_zip_bytes(volume, plan))
        assert len(archive) == zip_size(plan)
