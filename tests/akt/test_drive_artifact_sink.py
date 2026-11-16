"""Cloud sink fake: namespace, strictSHA, Volumecommit và processresume."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re

import pytest
import requests

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('cloud_drive_sink',ROOT/'scripts/akt/drive_artifact_sink.py')
sink=importlib.util.module_from_spec(spec)
spec.loader.exec_module(sink)
core=sink.core


def response(status,body=None,**headers):
    r=requests.Response();r.status_code=status;r.headers.update(headers)
    r._content=json.dumps(body or {}).encode()
    return r


class Drive:
    def __init__(self):
        self.account=sink.DRIVE_ACCOUNT
        self.items={sink.DRIVE_PARENT:dict(id=sink.DRIVE_PARENT,name='KLTN',mimeType=core.FOLDER,parents=['root'])}
        self.calls=[]
        self.sequence=0
        self.sessions={}
        self.crash=False
        self.missing_sha=False
        self.bad_sha=False
        self.file_gets=0
        self.corrupt_on_readback=False
        self.before_data=None

    def request(self,method,url,**kw):
        self.calls.append((method,url,kw))
        if url==core.API+'/about':
            return response(200,dict(user=dict(emailAddress=self.account)))
        if url==core.API+'/files/generateIds':
            self.sequence+=1;return response(200,dict(ids=[f'id{self.sequence}']))
        if url==core.API+'/files':
            if method=='POST':
                item=dict(kw['json']);self.items[item['id']]=item;return response(200,item)
            query=kw['params']['q']
            match=re.match(r"'([^']+)' in parents and name = '([^']+)'",query)
            assert match
            return response(200,dict(files=[m for m in self.items.values()
                if match[1] in m.get('parents',[]) and m['name']==match[2]]))
        if url.startswith(core.API+'/files/'):
            item=self.items.get(url.rsplit('/',1)[-1])
            if item is None:return response(404)
            item=dict(item)
            if 'size' in item:
                self.file_gets+=1
                if self.missing_sha:item.pop('sha256Checksum',None)
                if self.bad_sha or self.corrupt_on_readback and self.file_gets>=2:item['sha256Checksum']='0'*64
            return response(200,item)
        if method=='POST' and url==core.UPLOAD:
            key='session'+str(len(self.sessions)+1)
            self.sessions[key]=dict(metadata=dict(kw['json']),content=bytearray(),total=int(kw['headers']['X-Upload-Content-Length']))
            return response(200,Location=core.UPLOAD+'?upload_id='+key)
        assert method=='PUT'
        session=self.sessions[url.split('upload_id=')[1]]
        data=kw['data']
        if data:
            if self.before_data:self.before_data()
            start=int(kw['headers']['Content-Range'].split()[1].split('-')[0])
            assert start==len(session['content'])
            session['content'].extend(data)
            if self.crash:
                self.crash=False;raise KeyboardInterrupt
        content=bytes(session['content'])
        if len(content)==session['total']:
            item=dict(session['metadata'],size=str(len(content)),mimeType='application/octet-stream',
                md5Checksum=hashlib.md5(content).hexdigest(),sha256Checksum=hashlib.sha256(content).hexdigest())
            self.items[item['id']]=item
            return response(200,item)
        return response(308,**({'Range':f'bytes=0-{len(content)-1}'} if content else {}))


@pytest.fixture
def case(tmp_path):
    root=tmp_path/'volume'
    source=root/'run1/tranche1/payloads'
    source.mkdir(parents=True)
    (source/'model.pt').write_bytes(bytes(range(256))*2048)
    drive=Drive()
    state=root/'run1/tranche1/.drive-state/state.json'
    evidence=root/'run1/tranche1/drive-evidence'
    commits=[]
    def commit():
        value=core.read_json(state) if state.exists() else {}
        commits.append(dict(has_uri=any('session_url' in e for e in value.get('files',{}).values()),
            strict=bool(value.get('strict_batch_verified')),receipt=(evidence/'RECEIPTS.json').exists(),
            strict_receipt=(evidence/'STRICT_ACCEPTANCE.json').exists(),calls=len(drive.calls)))
    def run(**overrides):
        options=dict(source_root=source,files=['model.pt'],run_id='run1',tranche_id='tranche1',
            volume_commit=commit,max_total_bytes=1024**2,cloud_root=root,chunk_bytes=256*1024,retries=1,sleep=lambda _:None)
        options.update(overrides)
        return sink.publish_with_session(drive,**options)
    return dict(root=root,source=source,drive=drive,state=state,evidence=evidence,commits=commits,run=run,commit=commit)


def test_full_batch_namespace_sha_and_receipts_commit(case):
    result=case['run']()
    assert result['status']=='DRIVE_SHA256_VERIFIED' and result['account']==sink.DRIVE_ACCOUNT
    folders=[m for m in case['drive'].items.values() if m.get('mimeType')==core.FOLDER]
    run=next(m for m in folders if m['name']=='run1')
    tranche=next(m for m in folders if m['name']=='tranche1')
    assert run['parents']==[sink.DRIVE_PARENT] and tranche['parents']==[run['id']]
    state=core.read_json(case['state'])
    assert state['strict_batch_verified'] and state['files']['model.pt']['strict_verified']
    assert case['commits'][-1]['strict_receipt'] and case['commits'][-1]['receipt']


def test_uri_durable_before_first_chunk_and_resume_after_process_interrupt(case):
    case['drive'].before_data=lambda:pytest.fail('URI must be persisted') if not any(c['has_uri'] for c in case['commits']) else None
    case['drive'].crash=True
    with pytest.raises(KeyboardInterrupt):case['run']()
    assert any(c['has_uri'] for c in case['commits'])
    assert len(case['drive'].sessions)==1
    result=case['run']()
    assert result['status']=='DRIVE_SHA256_VERIFIED' and len(case['drive'].sessions)==1
    data=[kw for method,url,kw in case['drive'].calls if method=='PUT' and kw['data']]
    assert data[1]['headers']['Content-Range'].startswith('bytes 262144-')


@pytest.mark.parametrize('failure',['missing_sha','bad_sha'])
def test_md5_complete_never_promoted_without_server_sha(case,failure):
    setattr(case['drive'],failure,True)
    with pytest.raises(sink.ArtifactSinkError,match='SHA-256'):case['run']()
    state=core.read_json(case['state'])
    assert not state['strict_batch_verified'] and not state['files']['model.pt']['strict_verified']
    assert not (case['evidence']/'STRICT_ACCEPTANCE.json').exists()


def test_legacy_md5_flag_reverified_on_restart(case):
    result=case['run']()
    state=core.read_json(case['state'])
    state['files']['model.pt'].pop('strict_verified')
    core.atomic_json(case['state'],state)
    case['drive'].missing_sha=True
    with pytest.raises(sink.ArtifactSinkError,match='SHA-256'):case['run']()
    assert not core.read_json(case['state'])['strict_batch_verified']
    case['drive'].missing_sha=False
    assert case['run']()['files'][0]['file_id']==result['files'][0]['file_id']
    assert len(case['drive'].sessions)==1


def test_late_readback_failure_clears_strict_batch(case):
    case['drive'].corrupt_on_readback=True
    with pytest.raises(sink.ArtifactSinkError,match='readback'):case['run']()
    assert not core.read_json(case['state'])['strict_batch_verified']


def test_wrong_account_has_no_drive_writes(case):
    case['drive'].account='other@example.com'
    with pytest.raises(RuntimeError,match='Tài khoản'):case['run']()
    assert all(method=='GET' for method,_,_ in case['drive'].calls)


def test_failed_commit_stops_before_drive_request(case):
    def fail():raise OSError('fake volume failure')
    with pytest.raises(OSError):case['run'](volume_commit=fail)
    assert not case['drive'].calls


def test_final_receipt_commit_failure_cannot_return_success(case):
    def fail_after_receipt():
        case['commit']()
        if (case['evidence']/'STRICT_ACCEPTANCE.json').exists():
            raise OSError('fake receipt commit failure')
    with pytest.raises(OSError,match='receipt commit'):
        case['run'](volume_commit=fail_after_receipt)
    assert len(case['drive'].sessions)==1
    result=case['run']()
    assert result['status']=='DRIVE_SHA256_VERIFIED'
    assert len(case['drive'].sessions)==1


def test_modified_immutable_plan_rejected(case):
    case['run']()
    (case['source']/'model.pt').write_bytes(b'new model')
    before=len(case['drive'].calls)
    with pytest.raises(sink.ArtifactSinkError,match='Plan tranche'):case['run']()
    assert len(case['drive'].calls)==before


def test_same_bytes_new_mtime_resume_keeps_session_and_content_plan(case):
    case['drive'].crash=True
    with pytest.raises(KeyboardInterrupt):case['run']()
    plan_path=case['root']/'run1/tranche1/ARTIFACT_PLAN.json'
    original=plan_path.read_bytes()
    payload=case['source']/'model.pt'
    stat=payload.stat()
    os.utime(payload,ns=(stat.st_atime_ns,stat.st_mtime_ns+2_000_000_000))
    result=case['run']()
    assert result['status']=='DRIVE_SHA256_VERIFIED'
    assert len(case['drive'].sessions)==1
    assert plan_path.read_bytes()==original
    assert 'SOURCE_METADATA_REBOUND_AFTER_CONTENT_REHASH' in (case['evidence']/'events.jsonl').read_text()
    assert core.read_json(case['state'])['plan']['files'][0]['mtime_ns']==payload.stat().st_mtime_ns


def test_same_size_changed_bytes_and_restored_mtime_rejected(case):
    case['run']()
    payload=case['source']/'model.pt'
    stat=payload.stat()
    payload.write_bytes(b'changed'+payload.read_bytes()[7:])
    os.utime(payload,ns=(stat.st_atime_ns,stat.st_mtime_ns))
    before=len(case['drive'].calls)
    with pytest.raises(sink.ArtifactSinkError,match='Plan tranche'):case['run']()
    assert len(case['drive'].calls)==before


def test_nested_payload_folder_keys_separate_from_namespace(case):
    directory=case['source']/'namespace/run'
    directory.mkdir(parents=True)
    (directory/'config.json').write_text('{"seed":42}')
    result=case['run'](files=['model.pt','namespace/run/config.json'])
    assert len(result['files'])==2
    state=core.read_json(case['state'])
    assert state['folders']['namespace/run']!=state['folders']['payload/namespace/run']


def test_public_environment_does_not_persist_oauth(case,monkeypatch,capsys):
    from google.auth.transport import requests as transport
    monkeypatch.setattr(sink.platform,'system',lambda:'Linux')
    monkeypatch.setattr(sink,'CLOUD_ROOT',case['root'])
    info=dict(client_id='CLIENT_PRIVATE_LITERAL',client_secret='CLIENT_SECRET_LITERAL',
              refresh_token='REFRESH_PRIVATE_LITERAL',token='ACCESS_PRIVATE_LITERAL')
    monkeypatch.setenv(sink.TOKEN_ENV,json.dumps(info))
    class Session:
        def __init__(self,credentials):pass
        def __enter__(self):return case['drive']
        def __exit__(self,*args):return False
    monkeypatch.setattr(transport,'AuthorizedSession',Session)
    result=sink.publish_from_environment(source_root=case['source'],files=['model.pt'],run_id='run1',
        tranche_id='tranche1',volume_commit=case['commit'],max_total_bytes=1024**2,chunk_bytes=262144)
    assert result['status']=='DRIVE_SHA256_VERIFIED'
    public=capsys.readouterr().out
    persisted=''.join(p.read_text() for p in case['root'].rglob('*.json'))
    assert all(value not in public+persisted for value in info.values())


def test_secret_error_suppresses_payload_and_uri(case,monkeypatch,capsys):
    from google.oauth2.credentials import Credentials
    monkeypatch.setattr(sink.platform,'system',lambda:'Linux')
    monkeypatch.setattr(sink,'CLOUD_ROOT',case['root'])
    monkeypatch.setenv(sink.TOKEN_ENV,json.dumps(dict(client_id='x',client_secret='secret',refresh_token='refresh')))
    def fail(*args,**kwargs):raise ValueError('secret https://www.googleapis.com/upload/drive/v3/files?upload_id=PRIVATE')
    monkeypatch.setattr(Credentials,'from_authorized_user_info',fail)
    with pytest.raises(sink.ArtifactSinkError) as error:sink.publish_from_environment(
        source_root=case['source'],files=['model.pt'],run_id='run1',tranche_id='tranche1',
        volume_commit=case['commit'],max_total_bytes=1024**2)
    assert 'secret' not in str(error.value) and 'upload_id' not in str(error.value)
    assert error.value.__suppress_context__
    assert 'PRIVATE' not in capsys.readouterr().out


@pytest.mark.parametrize('name',['../secret','/absolute','token.json','.private/file','nested/credentials.json'])
def test_private_or_traversal_files_rejected(case,name):
    with pytest.raises(sink.ArtifactSinkError):case['run'](files=[name])


def test_empty_or_over_budget_file_explicitly_rejected(case):
    (case['source']/'empty.txt').touch()
    with pytest.raises(sink.ArtifactSinkError,match='rỗng'):case['run'](files=['empty.txt'])
    with pytest.raises(sink.ArtifactSinkError,match='ngân sách'):case['run'](max_total_bytes=10)


def test_public_entry_rejects_local_windows(monkeypatch):
    monkeypatch.setattr(sink.platform,'system',lambda:'Windows')
    with pytest.raises(sink.ArtifactSinkError,match='Linux cloud'):sink.publish_from_environment(
        source_root='unused',files=[],run_id='run',tranche_id='tranche',volume_commit=lambda:None,max_total_bytes=1)
