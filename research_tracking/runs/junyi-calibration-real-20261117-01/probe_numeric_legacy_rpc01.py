"""Probe đọc metadata Volume bằng RPC inline, không chạy compute."""
import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
import time
import warnings

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


async def main():
    output = HERE / 'A2_LEGACY_RPC_PROBE01.json'
    if output.exists():
        raise FileExistsError('Không ghi đè probe đã đóng.')
    os.environ['MODAL_CONFIG_PATH'] = str(ROOT / 'artifacts/akt/private/modal2016.toml')
    os.environ['MODAL_PROFILE'] = 'kltn2016'
    os.environ['MODAL_LOGLEVEL'] = 'ERROR'
    logging.getLogger('modal').setLevel(logging.ERROR)
    warnings.filterwarnings('ignore', message='Your Modal token .*')
    from modal.client import _Client
    from modal_proto import api_pb2
    gpu = json.loads((HERE / 'A2_GPU_RESULT01.json').read_text(encoding='utf-8'))
    path = 'junyi-calibration-real-20261117-01/a2-numeric/payloads/RECEIPT.json'
    result = {'path': path, 'rpc': 'VolumeGetFile', 'chunk_bytes': 32768,
              'paid_compute_started': False, 'binary_saved_locally': False,
              'expected_sha256': gpu['result']['receipt_sha256'], 'calls': 0}
    started = time.monotonic()
    client = None
    try:
        client = await asyncio.wait_for(_Client.from_env(), timeout=30)
        identity = await asyncio.wait_for(client._stub.TokenInfoGet(api_pb2.TokenInfoGetRequest()), timeout=30)
        if identity.workspace_name != 'honguyenminhsang2016':
            raise ValueError('Workspace không khớp.')
        result['workspace'] = identity.workspace_name
        data, total = bytearray(), None
        while total is None or len(data) < total:
            response = await asyncio.wait_for(client._stub.VolumeGetFile(api_pb2.VolumeGetFileRequest(
                volume_id='vo-dv1975utRQbmagCjA0brSe', path=path,
                start=len(data), len=32768)), timeout=30)
            result['calls'] += 1
            if response.WhichOneof('data_oneof') != 'data':
                result['status'] = 'INLINE_UNAVAILABLE'
                result['data_blob_id_present'] = bool(response.data_blob_id)
                break
            if (response.start != len(data) or response.len != len(response.data)
                    or not 0 < response.size <= 2 * 1024**2
                    or not 0 < response.len <= 32768
                    or (total is not None and response.size != total)):
                raise ValueError('RPC byte-range metadata không khớp.')
            total = response.size
            data.extend(response.data)
            if len(data) > total:
                raise ValueError('RPC trả vượt source size.')
        else:
            digest = hashlib.sha256(data).hexdigest()
            if digest != result['expected_sha256']:
                raise ValueError('Receipt SHA không khớp GPU result.')
            receipt = json.loads(data)
            assert receipt['status'] == 'COMPLETE' and receipt['binding']['variant'] == 'A2'
            result.update(status='INLINE_PINNED_METADATA_READ_PASS', bytes=len(data),
                          sha256=digest, shards=len(receipt['shards']))
    except Exception as error:
        result['status'] = 'READ_STOPPED'
        result['error_type'] = type(error).__name__
        # Chỉ lưu mã RPC, không đưa thông điệp có URL hoặc credentials vào log.
        status = getattr(error, 'status', None)
        if status is not None:
            result['rpc_status'] = str(status)
    finally:
        if client is not None:
            await client._close()
        result['seconds'] = time.monotonic() - started
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    asyncio.run(main())
