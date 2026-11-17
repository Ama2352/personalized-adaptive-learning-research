"""Runner CPU Colab nhận access token ngắn hạn, không nhận refresh/client secret."""
import argparse
import atexit
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
import venv
import zipfile

API = 'https://www.googleapis.com/drive/v3'
DEPENDENCIES = ('numpy==2.5.4','pandas==3.0.6','duckdb==1.5.6','psutil==7.2.2',
    'requests==2.34.2','google-auth==2.62.1','scikit-learn==1.9.1','scipy==1.18.1','pyarrow==26.0.1')
FILES = {'free_cpu_calibration.py','drive_resumable_upload.py','modal_calibration_input_stage.py','calibration_audit_transaction.py'}


def bootstrap_venv(source):
    """Dùng uv có sẵn, chỉ cài vào venv dự án và giữ cache trong source."""
    source = Path(source)
    executable = shutil.which('uv')
    need(executable is not None, 'PREINSTALLED_UV_REQUIRED')
    python = source/'.venv/bin/python'
    if not python.exists():
        venv.EnvBuilder(with_pip=False).create(source/'.venv')
    environment = dict(os.environ, UV_CACHE_DIR=str(source/'artifacts/akt/uv-cache'))
    subprocess.run([executable,'pip','install','--python',str(python),*DEPENDENCIES],
        env=environment,check=True)
    return python


def failure_detail(error):
    """Chỉ ghi tên chương trình và mã lỗi, tránh lộ tham số hay output bí mật."""
    if isinstance(error, subprocess.CalledProcessError):
        command = error.cmd[0] if isinstance(error.cmd,(list,tuple)) and error.cmd else ''
        name = Path(command).name
        return dict(command=name if name.replace('-','').replace('_','').replace('.','').isalnum() else 'subprocess',
            returncode=error.returncode)
    return None


def checkpoint_write(path, state):
    path,state = Path(path),Path(state)
    if not path.is_relative_to(state):
        return False
    parts = path.relative_to(state).parts
    return ((len(parts) == 1 and parts[0] in ('A2_PROGRESS.json','A3_PROGRESS.json'))
            or (len(parts) == 3 and parts[0] == '.sessions' and parts[2] == 'state.json'))


def need(value, reason):
    if not value:
        raise RuntimeError(reason)


def token_only_credentials(path, factory=None):
    """Credential refresh chỉ đọc access token mới mà root đưa vào file."""
    if factory is None:
        from google.oauth2.credentials import Credentials
        factory = Credentials
    def read_token(request=None, scopes=None):
        value = json.loads(Path(path).read_text(encoding='utf-8'))
        need(set(value) == {'access_token','expiry'}, 'TOKEN_FILE_MUST_CONTAIN_ACCESS_AND_EXPIRY_ONLY')
        expiry = datetime.fromisoformat(value['expiry'].replace('Z','+00:00')).astimezone(timezone.utc).replace(tzinfo=None)
        need(isinstance(value['access_token'],str) and value['access_token']
             and expiry > datetime.now(timezone.utc).replace(tzinfo=None)+timedelta(minutes=3), 'DRIVE_ACCESS_TOKEN_RENEWAL_REQUIRED')
        return value['access_token'],expiry
    token,expiry = read_token()
    return factory(token=token,expiry=expiry,scopes=['https://www.googleapis.com/auth/drive'],refresh_handler=read_token)


def private_folder(session):
    response = session.get(API+'/files',params={'q':"'root' in parents and name='KLTN_AKT_PRIVATE' and trashed=false",
        'fields':'files(id,shared,mimeType)'},timeout=60)
    need(response.status_code == 200, 'PRIVATE_FOLDER_LOOKUP_FAILED')
    rows = response.json().get('files',[])
    if not rows:
        response = session.post(API+'/files',json={'name':'KLTN_AKT_PRIVATE',
            'mimeType':'application/vnd.google-apps.folder','parents':['root']},
            params={'fields':'id,shared,mimeType'},timeout=60)
        need(response.status_code in (200,201), 'PRIVATE_FOLDER_CREATE_FAILED')
        rows = [response.json()]
    need(len(rows) == 1 and rows[0].get('shared') is False
         and rows[0].get('mimeType') == 'application/vnd.google-apps.folder', 'STATE_FOLDER_MUST_BE_UNSHARED')
    return rows[0]['id']


def state_snapshot(session, folder, directory, *, restore=False):
    """Snapshot ZIP nhỏ chứa progress/URI riêng, không lấy file access token."""
    directory = Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    prefix = 'CALIBRATION_CPU_STATE_20261117_'
    if restore:
        if any(directory.glob('A[23]_PROGRESS.json')):
            return
        response = session.get(API+'/files',params={'q':f"'{folder}' in parents and name contains '{prefix}' and trashed=false",
            'fields':'files(id,size,sha256Checksum)','orderBy':'createdTime desc','pageSize':1},timeout=60)
        need(response.status_code == 200, 'STATE_RESTORE_LOOKUP_FAILED')
        rows = response.json().get('files',[])
        if not rows:
            return
        pin = rows[0]
        need(0 < int(pin['size']) <= 16*1024**2, 'STATE_RESTORE_SIZE_REJECTED')
        response = session.get(API+'/files/'+pin['id'],params={'alt':'media'},timeout=90)
        blob = response.content
        need(response.status_code == 200 and len(blob) == int(pin['size'])
             and hashlib.sha256(blob).hexdigest() == pin['sha256Checksum'], 'STATE_RESTORE_SHA_MISMATCH')
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            infos = archive.infolist()
            need(len(infos) <= 128 and len({r.filename for r in infos}) == len(infos)
                 and sum(r.file_size for r in infos) <= 16*1024**2, 'STATE_ARCHIVE_LIMIT_REJECTED')
            for item in infos:
                name = item.filename
                allowed = name in {'A2_PROGRESS.json','A3_PROGRESS.json'} or (
                    name.startswith('.sessions/') and name.endswith('/state.json'))
                need(allowed and '..' not in Path(name).parts and not Path(name).is_absolute()
                     and '\\' not in name and 0 < item.file_size <= 1024**2, 'STATE_MEMBER_REJECTED')
                target = directory/name
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(archive.read(item))
        return
    paths = sorted([*directory.glob('A[23]_PROGRESS.json'),*directory.glob('.sessions/*/state.json')])
    if not paths:
        return
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_STORED) as archive:
        for path in paths:
            need(not path.is_symlink() and path.stat().st_size <= 1024**2, 'STATE_SOURCE_REJECTED')
            archive.write(path,path.relative_to(directory).as_posix())
    blob = buffer.getvalue()
    need(len(blob) <= 16*1024**2, 'STATE_SNAPSHOT_TOO_LARGE')
    digest = hashlib.sha256(blob).hexdigest()
    name = prefix+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'_'+digest[:12]+'.zip'
    boundary = uuid.uuid4().hex
    metadata = json.dumps({'name':name,'parents':[folder]}).encode()
    body = (b'--'+boundary.encode()+b'\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n'+metadata
        +b'\r\n--'+boundary.encode()+b'\r\nContent-Type: application/zip\r\n\r\n'+blob
        +b'\r\n--'+boundary.encode()+b'--\r\n')
    response = session.post('https://www.googleapis.com/upload/drive/v3/files',
        params={'uploadType':'multipart','fields':'id'},data=body,
        headers={'Content-Type':'multipart/related; boundary='+boundary},timeout=90)
    need(response.status_code in (200,201), 'STATE_SNAPSHOT_UPLOAD_FAILED')
    response = session.get(API+'/files/'+response.json()['id'],
        params={'fields':'size,sha256Checksum,parents'},timeout=60)
    pin = response.json()
    need(response.status_code == 200 and int(pin['size']) == len(blob)
         and pin['sha256Checksum'] == digest and folder in pin['parents'], 'STATE_SNAPSHOT_READBACK_FAILED')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload',type=Path,required=True)
    parser.add_argument('--payload-sha256',required=True)
    parser.add_argument('--token-file',type=Path,required=True)
    parser.add_argument('--variant',choices=('A2','A3'),required=True)
    parser.add_argument('--prepared',action='store_true')
    args = parser.parse_args()
    need(os.name == 'posix' and Path('/content').is_dir(), 'COLAB_CPU_SCRATCH_REQUIRED')
    token_path = args.token_file.absolute()
    need(token_path.is_relative_to(Path('/content')) and token_path.resolve() == token_path,
         'OWN_COLAB_TOKEN_PATH_REQUIRED')
    need(not token_path.is_relative_to(Path('/content/kltn-free-cpu-state')), 'TOKEN_MUST_BE_OUTSIDE_STATE')
    atexit.register(token_path.unlink,missing_ok=True)
    raw = args.payload.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == args.payload_sha256, 'PAYLOAD_SHA_MISMATCH')
    payload = json.loads(raw)
    need(set(payload) == {'files','plan','upstream_b64'} and set(payload['files']) == FILES, 'PAYLOAD_SCHEMA_REJECTED')
    tools = Path('/content/kltn-free-cpu-tools')
    tools.mkdir(exist_ok=True)
    for name,text in payload['files'].items():
        (tools/name).write_text(text,encoding='utf-8')
    sys.path.insert(0,str(tools))
    import free_cpu_calibration as free
    from google.auth.transport.requests import AuthorizedSession
    plan = payload['plan']
    source = free.VOLUME/'calibration-inputs-20261117-01/source'
    try:
        with AuthorizedSession(token_only_credentials(args.token_file)) as session:
            account = session.get(API+'/about',params={'fields':'user(emailAddress)'},timeout=60)
            need(account.status_code == 200 and account.json()['user']['emailAddress'] == free.ACCOUNT, 'DRIVE_ACCOUNT_MISMATCH')
            if not args.prepared:
                archive = free.download(session,plan['input'],Path('/content/kltn-free-cpu-input/INPUT.zip'))
                from modal_calibration_input_stage import extract_verified_input
                if not source.exists():
                    extract_verified_input(archive,source)
                else:
                    with zipfile.ZipFile(archive) as zipped:
                        frozen = json.loads(zipped.read('CLOUD_INPUT_PLAN.json'))
                    need(all((source/p['path']).is_file() and free.sha(source/p['path']) == p['sha256'] for p in frozen['files']), 'RESTAGED_SOURCE_CHANGED')
                upstream = source/'artifacts/akt/dependencies/upstream/akt.py'
                data = base64.b64decode(payload['upstream_b64'])
                need(hashlib.sha256(data).hexdigest() == 'ace9e4486ea6d8f8c52310a8ddf27212022136eda719c12d8204fab1bfcfdc67', 'UPSTREAM_SOURCE_CHANGED')
                upstream.parent.mkdir(parents=True,exist_ok=True)
                if upstream.exists():
                    need(upstream.read_bytes() == data, 'RESTAGED_UPSTREAM_CHANGED')
                else:
                    upstream.write_bytes(data)
                python = bootstrap_venv(source)
                env = dict(os.environ,PIP_CACHE_DIR=str(source/'artifacts/akt/pip-cache'))
                if not Path('/artifacts').exists():
                    Path('/artifacts').symlink_to(free.VOLUME,target_is_directory=True)
                need(Path('/artifacts').resolve() == free.VOLUME, 'ARTIFACT_ROOT_CHANGED')
                command = [str(python),'-B',str(Path(__file__).resolve()),'--payload',str(args.payload),
                    '--payload-sha256',args.payload_sha256,'--token-file',str(args.token_file),
                    '--variant',args.variant,'--prepared']
                subprocess.run(command,env=env,check=True)
                return
            sys.path.insert(0,str(source/'src'))
            need(Path(sys.prefix) == source/'.venv', 'PROJECT_VENV_REQUIRED')
            from importlib.metadata import version
            need(all(version(package) == expected for package,expected in
                (entry.split('==') for entry in DEPENDENCIES)), 'PINNED_CPU_DEPENDENCY_MISMATCH')
            from knowledge_tracing.akt.research_junyi_calibration import inference_source_identity
            need(inference_source_identity() == plan['requests'][args.variant]['source_identity'], 'FROZEN_SOURCE_CHANGED')
            need('torch' not in sys.modules, 'UNEXPECTED_TORCH_IMPORT')
            import psutil
            need(psutil.virtual_memory().available >= 4*1024**3, 'ESTIMATED_CPU_RAM_BUDGET_NOT_AVAILABLE')
            state = Path('/content/kltn-free-cpu-state')
            folder = private_folder(session)
            state_snapshot(session,folder,state,restore=True)
            windows = plan['cache']['windows']
            for pin in plan['window_metadata']:
                target = Path(windows['path'])/'manifest.json' if pin['path'] == 'WINDOW_MANIFEST.json' else Path(windows['admission_path'])
                free.download(session,pin,target)
            archive = free.download(session,plan['numeric'][args.variant],Path('/content/kltn-free-cpu-input')/(args.variant+'_NUMERIC.zip'))
            free.extract_numeric(archive,plan['numeric'][args.variant],free.VOLUME,args.variant)
            import drive_resumable_upload as core
            original = core.atomic_json
            status_path = tools/('STATUS_'+args.variant+'.json')
            def persist(path,value):
                original(path,value)
                if checkpoint_write(path,state):
                    if Path(path).parent == state:
                        phase = ('FIT_VERIFIED' if value.get('fit_verified') else 'FIT_UPLOAD' if value.get('pending_fit')
                            else 'RAW_VERIFIED' if value.get('raw_verified') else 'RAW_UPLOAD' if value.get('pending_raw') else 'JOIN_AUDIT')
                        original(status_path,dict(variant=args.variant,phase=phase,pid=os.getpid(),targets=1621484))
                    state_snapshot(session,folder,state)
            core.atomic_json = persist
            try:
                print(json.dumps(dict(status='CALIBRATION_CPU_START',variant=args.variant,targets=1621484)),flush=True)
                with core.single_writer(state/(args.variant+'.lock')):
                    result = free.run_variant(plan['requests'][args.variant],plan['gpu'][args.variant],plan['cache'],session,state)
                print(json.dumps(dict(status='CALIBRATION_CPU_DRIVE_COMPLETE',variant=args.variant,
                    fit_verified=result['fit_verified'],fit_publication=result['fit_publication'])),flush=True)
            finally:
                core.atomic_json = original
                state_snapshot(session,folder,state)
    finally:
        args.token_file.unlink(missing_ok=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        message = str(error)
        safe_reason = message if isinstance(error,RuntimeError) and message.replace('_','').isalnum() and message.isupper() else None
        print(json.dumps(dict(status='CALIBRATION_CPU_STOPPED',error_type=type(error).__name__,reason=safe_reason,
            subprocess=failure_detail(error))),flush=True)
        raise SystemExit(1)
