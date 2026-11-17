"""Phân biệt đường CDN của receipt/NPZ bằng API đọc storage, không compute."""
import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import time
from urllib.parse import urlsplit
import warnings

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def safe_host(value):
    return value if isinstance(value, str) and re.fullmatch('[A-Za-z0-9.-]{1,253}', value) else None


async def main():
    output = HERE / 'A2_V2_ROUTE_PROBE01.json'
    if output.exists():
        raise FileExistsError('Không ghi đè probe.')
    os.environ['MODAL_CONFIG_PATH'] = str(ROOT / 'artifacts/akt/private/modal2016.toml')
    os.environ['MODAL_PROFILE'] = 'kltn2016'
    os.environ['MODAL_LOGLEVEL'] = 'ERROR'
    logging.getLogger('modal').setLevel(logging.ERROR)
    warnings.filterwarnings('ignore', message='Your Modal token .*')
    from modal.client import _Client
    from modal_proto import api_pb2
    import aiohttp
    gpu = json.loads((HERE / 'A2_GPU_RESULT01.json').read_text(encoding='utf-8'))
    result = {'paid_compute_started': False, 'binary_saved_locally': False,
              'metadata_protocol': 'VolumeGetFile2', 'download_attempts': 1, 'routes': []}
    started, client = time.monotonic(), None
    try:
        client = await asyncio.wait_for(_Client.from_env(), timeout=20)
        identity = await asyncio.wait_for(client._stub.TokenInfoGet(api_pb2.TokenInfoGetRequest()), timeout=20)
        assert identity.workspace_name == 'honguyenminhsang2016'
        result['workspace'] = identity.workspace_name
        response_to_download = None
        for name in ('RECEIPT.json', 'shard-000000.npz'):
            path = 'junyi-calibration-real-20261117-01/a2-numeric/payloads/' + name
            response = await asyncio.wait_for(client._stub.VolumeGetFile2(api_pb2.VolumeGetFile2Request(
                volume_id='vo-dv1975utRQbmagCjA0brSe', path=path, client_pads_blocks=True)), timeout=20)
            assert 0 < response.size <= 2 * 1024**2 and response.len == response.size
            assert response.start == 0 and len(response.get_urls) == 1
            result['routes'].append({'path': path, 'size': response.size,
                                     'hostnames': [safe_host(urlsplit(u).hostname) for u in response.get_urls]})
            if name == 'RECEIPT.json':
                response_to_download = response
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.get(response_to_download.get_urls[0]) as http:
                result['http_status'] = http.status
                if http.status != 200:
                    raise RuntimeError('HTTP non-200')
                body = await http.content.read(2 * 1024**2 + 1)
                assert len(body) <= response_to_download.size
                body = body.ljust(response_to_download.size, b'\0')
                digest = hashlib.sha256(body).hexdigest()
                assert digest == gpu['result']['receipt_sha256']
                result.update(status='SERIAL_PINNED_RECEIPT_READ_PASS', bytes=len(body), sha256=digest)
    except Exception as error:
        result['status'] = 'ROUTE_READ_STOPPED'
        chain, seen = [], set()
        while error is not None and id(error) not in seen:
            seen.add(id(error))
            item = {'error_type': type(error).__name__}
            hostname = safe_host(getattr(error, 'host', None))
            if hostname:
                item['hostname'] = hostname
            chain.append(item)
            error = error.__cause__ or error.__context__
        result['error_chain'] = chain
    finally:
        if client is not None:
            await client._close()
        result['seconds'] = time.monotonic() - started
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    asyncio.run(main())
