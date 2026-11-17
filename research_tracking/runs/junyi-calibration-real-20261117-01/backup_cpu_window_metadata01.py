"""Sao lưu hai JSON cache đã pin qua storage API, không compute Modal."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import warnings

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts/akt'))


async def fetch(target, windows):
    import modal
    volume = modal.Volume.from_name('kltn-junyi-calibration-artifacts-v1', environment_name='main')
    specifications = [
        ('WINDOW_MANIFEST.json', windows['path'] + '/manifest.json', windows['manifest_sha256']),
        ('WINDOW_ADMISSION.json', windows['admission_path'], windows['admission_sha256'])]
    entries = []
    for name, physical, expected in specifications:
        path = physical.split('/vo-dv1975utRQbmagCjA0brSe/', 1)[1]
        existing = target / name
        if existing.exists() and hashlib.sha256(existing.read_bytes()).hexdigest() == expected:
            entries.append({'path': name, 'bytes': existing.stat().st_size,
                            'sha256': expected, 'volume_path': path})
            continue
        data = bytearray()
        reader = volume.read_file.aio(path)
        try:
            async for block in reader:
                if len(data) + len(block) > 2 * 1024**2:
                    raise ValueError('Metadata vượt2MiB.')
                data.extend(block)
        finally:
            await reader.aclose()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('Metadata SHA không khớp frozen cache receipt.')
        output = target / name
        if output.exists():
            if output.read_bytes() != data:
                raise ValueError('Metadata đã lưu có nội dung khác.')
        else:
            output.write_bytes(data)
        entries.append({'path': name, 'bytes': len(data), 'sha256': expected, 'volume_path': path})
    return entries


def main():
    os.environ['MODAL_CONFIG_PATH'] = str(ROOT / 'artifacts/akt/private/modal2016.toml')
    os.environ['MODAL_PROFILE'] = 'kltn2016'
    warnings.filterwarnings('ignore', message='Your Modal token .*')
    target = HERE / 'free-cpu-window-metadata01'
    target.mkdir(exist_ok=True)
    cache = json.loads((HERE / 'CPU_CACHE_RESULT02.json').read_text(encoding='utf-8'))['result']
    entries = asyncio.run(asyncio.wait_for(fetch(target, cache['windows']), timeout=60))
    import drive_resumable_upload as core
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    private = ROOT / 'artifacts/akt/private/free-cpu-window-metadata01'
    private.mkdir(exist_ok=True)
    plan = dict(source=str(target), files=[dict(path=row['path'], **core.hashes(target / row['path'])) for row in entries],
                bytes=sum(r['bytes'] for r in entries), folder_name='calibration-free-cpu-window-metadata-20261117-01',
                parent_id='1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7', account='honguyenminhsang2005@gmail.com')
    credentials = Credentials.from_authorized_user_file(str(ROOT / 'artifacts/akt/private/drive-upload/token.json'))
    published = []
    with core.single_writer(private / 'upload.lock'), AuthorizedSession(credentials) as session:
        uploader = core.Uploader(session, plan, private / 'state02.json', target, chunk_bytes=256 * 1024, retries=2)
        uploader.run()
        for row, pin in zip(entries, plan['files']):
            metadata = uploader.metadata(uploader.state['files'][row['path']]['remote_id'])
            parent = uploader.state['folders']['.']
            if not uploader.matches(metadata, pin, parent) or metadata.get('sha256Checksum') != row['sha256']:
                raise ValueError('Drive metadata readback SHA chưa đạt.')
            published.append(dict(row, file_id=metadata['id'], folder_id=parent))
    result = dict(status='FREE_CPU_WINDOW_METADATA_DRIVE_SHA256_VERIFIED', files=published,
                  paid_compute_started=False, binary_saved_locally=False)
    core.atomic_json(HERE / 'FREE_CPU_WINDOW_METADATA_DRIVE01.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
