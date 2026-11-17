"""Đọc Volume bằng API và tạo ZIP xác định trong RAM, không thuê compute."""
from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import PurePosixPath
import queue
import re
import threading
import zipfile

MAX_MEMBER = 2 * 1024**2
MAX_ARCHIVE = 256 * 1024**2
PREFIX = 'junyi-calibration-real-20261117-01/'


def make_plan(entries):
    """Đóng pin danh sách đã được caller đối chiếu receipt/manifest nguồn."""
    core = {'entries': entries, 'total_bytes': sum(e['bytes'] for e in entries)}
    core['source_plan_sha256'] = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(',', ':')).encode('ascii')
    ).hexdigest()
    validate_plan(core)
    return core


def validate_plan(plan):
    if set(plan) != {'entries', 'total_bytes', 'source_plan_sha256'}:
        raise ValueError('Sai schema archive plan.')
    entries = plan['entries']
    if not isinstance(entries, list) or not 0 < len(entries) <= 1024:
        raise ValueError('Số member không hợp lệ.')
    names, paths = set(), set()
    for entry in entries:
        if set(entry) != {'archive_name', 'volume_path', 'bytes', 'sha256'}:
            raise ValueError('Sai schema member.')
        name, path = entry['archive_name'], entry['volume_path']
        for value in (name, path):
            if not isinstance(value, str) or not value.isascii() or '\\' in value:
                raise ValueError('Đường dẫn phải là ASCII POSIX.')
            parsed = PurePosixPath(value)
            if parsed.is_absolute() or '..' in parsed.parts or str(parsed) != value:
                raise ValueError('Đường dẫn không canonical.')
        if not re.fullmatch(PREFIX + r'a[23]-numeric/payloads/(?:config\.json|RECEIPT\.json|shard-\d{6}\.(?:json|npz))', path):
            raise ValueError('Member ngoài run numeric A2/A3 được phép.')
        if name != path or name in names or path in paths:
            raise ValueError('Member trùng hoặc đổi tên nguồn.')
        if type(entry['bytes']) is not int or not 0 < entry['bytes'] <= MAX_MEMBER:
            raise ValueError('Member vượt giới hạn RAM nguồn 2 MiB.')
        if not re.fullmatch('[0-9a-f]{64}', entry['sha256']):
            raise ValueError('SHA256 không hợp lệ.')
        names.add(name)
        paths.add(path)
    core = {'entries': entries, 'total_bytes': sum(e['bytes'] for e in entries)}
    digest = hashlib.sha256(json.dumps(core, sort_keys=True, separators=(',', ':')).encode('ascii')).hexdigest()
    if type(plan['total_bytes']) is not int or core['total_bytes'] != plan['total_bytes'] or digest != plan['source_plan_sha256']:
        raise ValueError('Source plan thay đổi hoặc tổng bytes sai.')
    if _size(entries) > MAX_ARCHIVE:
        raise ValueError('Archive vượt 256 MiB.')


def _size(entries):
    return 22 + sum(30 + len(e['archive_name']) + e['bytes'] + 16 + 46 + len(e['archive_name']) for e in entries)


def zip_size(plan):
    validate_plan(plan)
    return _size(plan['entries'])


async def build_numeric_plan(volume, *, variant, receipt_sha256, expected_counts):
    """Đọc metadata nhỏ, nối receipt đã pin đến từng manifest và payload.

    Chỉ API Volume, không tạo App. Không đọc NPZ trong bước lập kế hoạch.
    Config GPU được caller giữ riêng trong hồ sơ request đã nghiệm thu.
    """
    if variant not in {'A2', 'A3'} or not re.fullmatch('[0-9a-f]{64}', receipt_sha256):
        raise ValueError('Variant/receipt pin không hợp lệ.')
    directory = PREFIX + variant.lower() + '-numeric/payloads/'
    entries_by_name = {}
    async for item in volume.iterdir.aio(directory, recursive=False):
        name = PurePosixPath(item.path).name
        if name in entries_by_name:
            raise ValueError('Volume listing trùng tên.')
        entries_by_name[name] = item

    async def metadata(path, digest):
        item = entries_by_name.get(PurePosixPath(path).name)
        if item is None or not 0 < item.size <= MAX_MEMBER:
            raise ValueError('Thiếu metadata hoặc size không hợp lệ.')
        data = bytearray()
        reader = volume.read_file.aio(path)
        try:
            async for block in reader:
                if len(data) + len(block) > item.size:
                    raise ValueError('Metadata vượt size pin.')
                data.extend(block)
        finally:
            await reader.aclose()
        if len(data) != item.size or hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('Metadata SHA/size mismatch.')
        return json.loads(data), {'archive_name': path, 'volume_path': path,
                                  'bytes': item.size, 'sha256': digest}

    receipt, receipt_entry = await metadata(directory + 'RECEIPT.json', receipt_sha256)
    if (receipt.get('kind') != 'JUNYI_CACHED_NUMERIC_INFERENCE_V1'
            or receipt.get('status') != 'COMPLETE'
            or receipt.get('binding', {}).get('variant') != variant
            or receipt.get('counts') != expected_counts):
        raise ValueError('Receipt không khớp kết quả GPU đã pin.')
    shards = receipt.get('shards')
    if not isinstance(shards, list) or not 0 < len(shards) <= 510:
        raise ValueError('Số shard không hợp lệ.')
    result = [receipt_entry]
    windows = targets = 0
    seen = set()
    # Tám metadata reader nhỏ đồng thời, tối đa 16 MiB payload tạm.
    for start in range(0, len(shards), 8):
        batch = shards[start:start + 8]
        paths = []
        for index, shard in enumerate(batch, start):
            path = directory + f'shard-{index:06d}.json'
            declared = shard['manifest_path']
            if not (declared == path or declared.endswith('/' + path)):
                raise ValueError('Shard path ngoài numeric run đã pin.')
            paths.append(path)
        manifests = await asyncio.gather(*(metadata(path, shard['manifest_sha256']) for path, shard in zip(paths, batch)))
        for index, (manifest, entry) in enumerate(manifests, start):
            if (manifest.get('kind') != 'JUNYI_NUMERIC_PREDICTIONS_V1'
                    or manifest.get('binding') != receipt['binding']
                    or manifest.get('shard_index') != index
                    or manifest.get('payload') != f'shard-{index:06d}.npz'):
                raise ValueError('Numeric shard binding/index không khớp.')
            for window in manifest['windows']:
                if window['window_id'] in seen:
                    raise ValueError('Window trùng giữa shards.')
                seen.add(window['window_id'])
                windows += 1
                targets += window['targets']
            payload = directory + manifest['payload']
            item = entries_by_name.get(manifest['payload'])
            if item is None:
                raise ValueError('Thiếu NPZ nguồn.')
            result.extend([entry, {'archive_name': payload, 'volume_path': payload,
                                   'bytes': item.size, 'sha256': manifest['payload_sha256']}])
    if windows != expected_counts['windows'] or targets != expected_counts['fitted_targets']:
        raise ValueError('Window/target counts không khớp receipt.')
    return make_plan(result)


class _Cancelled(Exception):
    pass


def iter_zip_bytes(volume, plan, chunk_size=8 * 1024**2, *, prefetch=4):
    """Stream ZIP_STORED theo thứ tự pin, đọc trước tối đa bốn member.

    Cap 2 MiB/member, bốn reader và queue2 cho dự toán payload bảo thủ
    dưới 48 MiB, ngoài buffer 8 MiB của transport. Chưa phải đo peak RSS.
    Caller phải close generator trong finally khi upload dừng.
    """
    validate_plan(plan)
    if type(chunk_size) is not int or not 0 < chunk_size <= 8 * 1024**2:
        raise ValueError('Chunk phải nằm trong (0, 8 MiB].')
    if type(prefetch) is not int or not 1 <= prefetch <= 4:
        raise ValueError('Prefetch phải nằm trong [1, 4].')
    # Cố định bản sao để mutation từ caller không thay nguồn giữa stream.
    entries = tuple(dict(e) for e in plan['entries'])
    messages = queue.Queue(maxsize=2)
    stopped = threading.Event()
    state = {}

    def put(item):
        while not stopped.is_set():
            try:
                messages.put(item, timeout=0.05)
                return
            except queue.Full:
                continue
        raise _Cancelled()

    class Sink:
        def __init__(self):
            self.position = 0

        def write(self, data):
            if stopped.is_set():
                raise _Cancelled()
            for start in range(0, len(data), chunk_size):
                put(bytes(data[start:start + chunk_size]))
            self.position += len(data)
            return len(data)

        def tell(self):
            return self.position

        def flush(self):
            pass

    async def read_member(entry):
        data = bytearray()
        digest = hashlib.sha256()
        reader = volume.read_file.aio(entry['volume_path'])
        try:
            async for block in reader:
                if stopped.is_set():
                    raise _Cancelled()
                if len(data) + len(block) > entry['bytes'] or len(block) > MAX_MEMBER:
                    raise ValueError('Nguồn vượt bytes đã pin.')
                data.extend(block)
                digest.update(block)
            if len(data) != entry['bytes'] or digest.hexdigest() != entry['sha256']:
                raise ValueError('SHA/bytes nguồn Volume không khớp.')
            return data
        finally:
            await reader.aclose()

    async def produce():
        sink = Sink()
        pending = {}
        try:
            for index in range(min(prefetch, len(entries))):
                pending[index] = asyncio.create_task(read_member(entries[index]))
            with zipfile.ZipFile(sink, 'w', compression=zipfile.ZIP_STORED, allowZip64=False) as archive:
                for index, entry in enumerate(entries):
                    data = await pending.pop(index)
                    info = zipfile.ZipInfo(entry['archive_name'], (1980, 1, 1, 0, 0, 0))
                    info.create_system = 0
                    info.external_attr = 0x20
                    info.file_size = entry['bytes']
                    with archive.open(info, 'w', force_zip64=False) as member:
                        member.write(data)
                    del data
                    next_index = index + prefetch
                    if next_index < len(entries):
                        pending[next_index] = asyncio.create_task(read_member(entries[next_index]))
        finally:
            for task in pending.values():
                task.cancel()
            await asyncio.gather(*pending.values(), return_exceptions=True)
        if sink.position != _size(entries):
            raise ValueError('Kích thước ZIP không khớp contract.')

    def worker():
        loop = asyncio.new_event_loop()
        state['loop'] = loop
        task = loop.create_task(produce())
        state['task'] = task
        try:
            loop.run_until_complete(task)
            put(None)
        except (asyncio.CancelledError, _Cancelled):
            pass
        except BaseException as error:
            if not stopped.is_set():
                put(error)
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

    thread = threading.Thread(target=worker, name='kltn-volume-zip', daemon=True)
    thread.start()
    try:
        while True:
            item = messages.get()
            if item is None:
                return
            if isinstance(item, BaseException):
                raise item
            yield item
    finally:
        stopped.set()
        loop, task = state.get('loop'), state.get('task')
        if loop is not None and task is not None and not loop.is_closed():
            try:
                loop.call_soon_threadsafe(task.cancel)
            except RuntimeError:
                pass
        thread.join(timeout=5)
        if thread.is_alive():
            raise RuntimeError('Volume reader chưa dừng sau khi hủy stream.')
