"""CPU staging đầu vào calibration đã ghim từ Drive sang Modal Volume.

Module chỉ định nghĩa worker. Không gọi cloud khi import hoặc chạy local.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import time
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[2] if os.name == 'nt' else Path('/opt/kltn')
ACCOUNT = 'honguyenminhsang2005@gmail.com'
PARENT = '1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7'
FILE_PARENT = '1xFW0BKnfph3jZdsJABW3WWB8b5TnGCSg'
FILE_ID = '1GlPhrWOLwFNeUiv1unYaEATypWmV9_Vy'
ZIP_SHA = 'a34cee8e961baf7056e8f16159d2b9a25afcca72f3c19b3a37bd0d711aab2d6a'
ZIP_BYTES = 134525060
PLAN_SHA = '0a5aea93f57206d04ee3094f1c13ae6d64aaa0864c95cf67f4e9ebcca7a7baef'
LOCAL_PLAN_FILE_SHA = 'a552518a231ee5d432e88080220e22ab161c196150b42addea08f0f94aed64dc'
API = 'https://www.googleapis.com/drive/v3'
MAX_BYTES = 160 * 1024**2
MAX_FILE = 64 * 1024**2
SAFE_FAILURE_MESSAGES = frozenset({
    'Bounded input download required', 'Drive metadata request failed',
    'Drive input account mismatch', 'Drive input metadata pin mismatch',
    'Drive input folder lineage mismatch', 'Existing input ZIP pin mismatch',
    'Partial input exceeds expected bytes', 'Drive Range response does not match committed offset',
    'Drive media download failed', 'Drive download exceeds byte cap',
    'Input download retry budget exhausted', 'Downloaded input ZIP SHA mismatch',
    'Input ZIP pin mismatch', 'Input ZIP member limits or types rejected',
    'Archive member needs string path', 'Unsafe archive member path',
    'Embedded input plan pin mismatch', 'Input plan coverage mismatch',
    'Existing staged input coverage mismatch', 'Staged input alias rejected',
    'Existing staged input pin mismatch', 'Input member size pin mismatch',
    'Extracted input member SHA mismatch', 'Drive OAuth endpoint mismatch',
})


def record_safe_failure(error, phase, root, volume_commit):
    """Chỉ công bố thông báo tĩnh của worker, không ghi raw HTTP/OAuth/URI."""
    phases = {'MOUNT', 'AUTH', 'DOWNLOAD', 'EXTRACT', 'RECEIPT'}
    message = str(error)
    result = dict(status='CALIBRATION_INPUT_STAGE_FAILED',
        phase=phase if phase in phases else 'UNKNOWN', error_type=type(error).__name__,
        message=message if message in SAFE_FAILURE_MESSAGES else None,
        zip_bytes=None, part_bytes=None)
    if root is not None:
        root = Path(root)
        for name, key in (('INPUT.zip', 'zip_bytes'), ('INPUT.zip.part', 'part_bytes')):
            path = root/name
            if path.is_file():
                result[key] = path.stat().st_size
    print(json.dumps(result, sort_keys=True), flush=True)
    try:
        if root is not None:
            root.mkdir(parents=True, exist_ok=True)
            with (root/('FAILED-'+uuid.uuid4().hex+'.json')).open('x', encoding='utf-8') as stream:
                json.dump(result, stream, sort_keys=True, indent=2)
            volume_commit()
    except Exception:
        print('{"status":"STAGE_FAILURE_DIAGNOSTIC_PERSIST_FAILED"}', flush=True)
    return result


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _path(name):
    if not isinstance(name, str):
        raise ValueError('Archive member needs string path')
    path = PurePosixPath(name)
    if (path.is_absolute() or not path.parts or '..' in path.parts or str(path) != name
            or '\\' in name or ':' in name or len(name) > 240 or any(ord(c) < 32 for c in name)
            or any(p.lower() in {'private', '.private', '.git', 'holdout'} for p in path.parts)):
        raise ValueError('Unsafe archive member path')
    return path


def download_pinned_input(session, directory, *, volume_commit, file_id=FILE_ID,
        expected_sha=ZIP_SHA, expected_bytes=ZIP_BYTES, retries=2, sleep=time.sleep):
    """Resume HTTP Range từ .part đã commit, không giữ OAuth/URI trong state."""
    import requests
    if not 0 < expected_bytes <= MAX_BYTES or not callable(volume_commit):
        raise ValueError('Bounded input download required')
    def metadata(path, params):
        response = session.request('GET', API + path, params=params, timeout=(20, 60), allow_redirects=False)
        if response.status_code != 200:
            raise RuntimeError('Drive metadata request failed')
        return response.json()
    about = metadata('/about', {'fields':'user(emailAddress)'})
    if about['user']['emailAddress'].lower() != ACCOUNT:
        raise ValueError('Drive input account mismatch')
    remote = metadata('/files/' + file_id, {'fields':'id,size,sha256Checksum,parents,trashed'})
    if (remote.get('trashed') or remote.get('id') != file_id or FILE_PARENT not in remote.get('parents', [])
            or int(remote.get('size', -1)) != expected_bytes or remote.get('sha256Checksum') != expected_sha):
        raise ValueError('Drive input metadata pin mismatch')
    folder = metadata('/files/' + FILE_PARENT, {'fields':'id,mimeType,parents,trashed'})
    if (folder.get('trashed') or folder.get('id') != FILE_PARENT
            or folder.get('mimeType') != 'application/vnd.google-apps.folder'
            or PARENT not in folder.get('parents', [])):
        raise ValueError('Drive input folder lineage mismatch')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    completed = directory/'INPUT.zip'
    partial = directory/'INPUT.zip.part'
    if completed.exists():
        if completed.stat().st_size != expected_bytes or sha256(completed) != expected_sha:
            raise ValueError('Existing input ZIP pin mismatch')
        return completed
    if partial.exists() and partial.stat().st_size > expected_bytes:
        raise ValueError('Partial input exceeds expected bytes')
    for attempt in range(retries + 1):
        offset = partial.stat().st_size if partial.exists() else 0
        if offset == expected_bytes:
            break
        response = None
        try:
            response = session.request('GET', API+'/files/'+file_id,
                params={'alt':'media'}, headers={'Range':f'bytes={offset}-'}, stream=True,
                timeout=(20, 90), allow_redirects=False)
            if response.status_code in (429, 500, 502, 503, 504):
                raise requests.ConnectionError('Drive temporarily unavailable')
            if offset:
                match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', response.headers.get('Content-Range',''))
                if (response.status_code != 206 or not match or int(match[1]) != offset
                        or int(match[2]) != expected_bytes-1 or int(match[3]) != expected_bytes):
                    raise ValueError('Drive Range response does not match committed offset')
            elif response.status_code not in (200, 206):
                raise RuntimeError('Drive media download failed')
            with partial.open('ab') as stream:
                for block in response.iter_content(chunk_size=8*1024**2):
                    if not block:
                        continue
                    offset += len(block)
                    if offset > expected_bytes:
                        raise ValueError('Drive download exceeds byte cap')
                    stream.write(block)
                    stream.flush()
                    os.fsync(stream.fileno())
                    volume_commit()
            if offset != expected_bytes:
                raise requests.ConnectionError('Incomplete Drive download')
            break
        except requests.RequestException:
            if attempt == retries:
                raise RuntimeError('Input download retry budget exhausted') from None
            sleep(min(4, 2**attempt))
        finally:
            if response is not None:
                response.close()
    if sha256(partial) != expected_sha:
        raise ValueError('Downloaded input ZIP SHA mismatch')
    os.replace(partial, completed)
    volume_commit()
    return completed


def extract_verified_input(archive_path, target, *, expected_zip_sha=ZIP_SHA, expected_plan_sha=PLAN_SHA):
    """Đối chiếu ZIP/plan/member SHA trước công bố source directory."""
    archive_path, target = Path(archive_path), Path(target)
    if archive_path.stat().st_size > MAX_BYTES or sha256(archive_path) != expected_zip_sha:
        raise ValueError('Input ZIP pin mismatch')
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        names = [m.filename for m in members]
        if (len(members) > 257 or len(set(names)) != len(names)
                or sum(m.file_size for m in members) > MAX_BYTES
                or any(m.file_size > MAX_FILE or stat.S_ISLNK(m.external_attr >> 16)
                       or m.is_dir() or m.flag_bits & 1 for m in members)):
            raise ValueError('Input ZIP member limits or types rejected')
        for name in names:
            _path(name)
        raw = archive.read('CLOUD_INPUT_PLAN.json')
        if len(raw) > 1024**2 or hashlib.sha256(raw).hexdigest() != expected_plan_sha:
            raise ValueError('Embedded input plan pin mismatch')
        plan = json.loads(raw)
        rows = plan['files']
        if (plan['schema'] != 'junyi-calibration-cloud-inputs-v1' or not 1 <= len(rows) <= 256
                or len({r['path'] for r in rows}) != len(rows)
                or set(names) != {r['path'] for r in rows} | {'CLOUD_INPUT_PLAN.json'}
                or sum(r['bytes'] for r in rows) != plan['bytes'] or plan['bytes'] > MAX_BYTES):
            raise ValueError('Input plan coverage mismatch')
        if target.exists():
            existing = {p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()}
            if existing != {row['path'] for row in rows}:
                raise ValueError('Existing staged input coverage mismatch')
            for row in rows:
                path = target/_path(row['path'])
                if any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)()
                       for p in (path, *path.parents) if p.is_relative_to(target)):
                    raise ValueError('Staged input alias rejected')
                if path.stat().st_size != row['bytes'] or sha256(path) != row['sha256']:
                    raise ValueError('Existing staged input pin mismatch')
            return plan
        staging = target.with_name(target.name+'.partial-'+uuid.uuid4().hex)
        staging.mkdir(parents=True, exist_ok=False)
        for row in rows:
            relative = _path(row['path'])
            info = archive.getinfo(row['path'])
            if info.file_size != row['bytes'] or not 0 <= row['bytes'] <= MAX_FILE:
                raise ValueError('Input member size pin mismatch')
            path = staging/relative
            path.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            with archive.open(info) as source, path.open('xb') as output:
                while block := source.read(1024**2):
                    digest.update(block)
                    output.write(block)
            if digest.hexdigest() != row['sha256']:
                raise ValueError('Extracted input member SHA mismatch')
        os.replace(staging, target)
        return plan


def create_app():
    """Định nghĩa CPU worker; root quyết định app.run và hạn mức riêng."""
    from modal_junyi_calibration import require_cpu_orchestration_authorization
    require_cpu_orchestration_authorization()
    import modal
    volume = modal.Volume.from_name('kltn-junyi-calibration-artifacts-v1', environment_name='main', version=2)
    image = (modal.Image.debian_slim(python_version='3.13')
        .pip_install('requests==2.34.2', 'google-auth==2.62.1')
        .env({'PYTHONPATH':'/opt/kltn/scripts/akt'})
        .add_local_file(str(ROOT/'scripts/akt/modal_calibration_input_stage.py'), '/opt/kltn/scripts/akt/modal_calibration_input_stage.py'))
    app = modal.App('kltn-calibration-input-stage-cpu')

    @app.function(image=image, cpu=1, memory=1024, timeout=600, startup_timeout=180, serialized=True,
        routing_region='ap-south',
        max_containers=1, retries=0, scaledown_window=2, single_use_containers=True,
        volumes={'/artifacts':volume}, secrets=[modal.Secret.from_name(
            'kltn-drive-artifacts-sang2005-20261117', environment_name='main', required_keys=['KLTN_DRIVE_OAUTH_JSON'])])
    def stage():
        from google.auth.transport.requests import AuthorizedSession
        from google.oauth2.credentials import Credentials
        phase = 'MOUNT'
        root = None
        try:
            volume.reload()
            root = Path('/artifacts').resolve(strict=True)/'calibration-inputs-20261117-01'
            phase = 'AUTH'
            info = json.loads(os.environ['KLTN_DRIVE_OAUTH_JSON'])
            if info.get('token_uri', 'https://oauth2.googleapis.com/token') != 'https://oauth2.googleapis.com/token':
                raise ValueError('Drive OAuth endpoint mismatch')
            credentials = Credentials.from_authorized_user_info(info, ['https://www.googleapis.com/auth/drive'])
            with AuthorizedSession(credentials) as session:
                phase = 'DOWNLOAD'
                archive = download_pinned_input(session, root, volume_commit=volume.commit)
            phase = 'EXTRACT'
            plan = extract_verified_input(archive, root/'source')
            phase = 'RECEIPT'
            receipt = dict(status='CALIBRATION_CLOUD_INPUTS_STAGED', source_root=str(root/'source'),
                input_drive_file_id=FILE_ID, zip_sha256=ZIP_SHA, plan_sha256=PLAN_SHA,
                local_plan_file_sha256=LOCAL_PLAN_FILE_SHA,
                bytes=plan['bytes'], files=plan['files'], gpu=False)
            receipt_path = root/'STAGED.json'
            receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
            volume.commit()
            return dict(status=receipt['status'], source_root=receipt['source_root'],
                files=len(plan['files']), bytes=plan['bytes'], receipt_path=str(receipt_path),
                receipt_sha256=sha256(receipt_path), zip_sha256=ZIP_SHA, plan_sha256=PLAN_SHA, gpu=False)
        except Exception as error:
            diagnostic = record_safe_failure(error, phase, root, volume.commit)
            raise RuntimeError('CPU input staging stopped: '+diagnostic['phase']+' '+
                diagnostic['error_type']+' '+(diagnostic['message'] or 'unclassified error')) from None
    return app, stage
