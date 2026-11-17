from datetime import datetime, timedelta, timezone
import json
import hashlib
import io
import zipfile
from types import SimpleNamespace

import pytest
from pathlib import Path

from scripts.akt import colab_calibration_token_runner as runner


def token_file(path, token='short-lived'):
    path.write_text(json.dumps(dict(access_token=token,
        expiry=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat())))


def test_access_only_credential_refresh_reads_updated_file(tmp_path):
    path = tmp_path/'access.json'
    token_file(path)
    credential = runner.token_only_credentials(path,factory=lambda **kwargs:SimpleNamespace(**kwargs))
    assert credential.token == 'short-lived'
    token_file(path,'renewed-local-root')
    token,expiry = credential.refresh_handler(object())
    assert token == 'renewed-local-root'
    assert expiry.tzinfo is None
    assert not hasattr(credential,'refresh_token') and not hasattr(credential,'client_secret')


@pytest.mark.parametrize('key', ['refresh_token','client_secret','client_id'])
def test_long_lived_credentials_rejected(tmp_path,key):
    path = tmp_path/'access.json'
    token_file(path)
    value = json.loads(path.read_text())
    value[key] = 'must-stay-on-D'
    path.write_text(json.dumps(value))
    with pytest.raises(RuntimeError,match='ACCESS_AND_EXPIRY_ONLY'):
        runner.token_only_credentials(path,factory=lambda **kwargs:kwargs)


def test_expired_access_requires_root_renewal(tmp_path):
    path = tmp_path/'access.json'
    path.write_text(json.dumps(dict(access_token='expired',expiry='2020-01-01T00:00:00Z')))
    with pytest.raises(RuntimeError,match='RENEWAL_REQUIRED'):
        runner.token_only_credentials(path,factory=lambda **kwargs:kwargs)


def test_shared_private_state_folder_rejected():
    class Session:
        def get(self,*args,**kwargs):
            return SimpleNamespace(status_code=200,json=lambda:{'files':[dict(id='folder',shared=True,mimeType='application/vnd.google-apps.folder')]})
    with pytest.raises(RuntimeError,match='UNSHARED'):
        runner.private_folder(Session())


def test_private_snapshot_roundtrip_excludes_access_file(tmp_path):
    state = tmp_path/'state'
    state.mkdir()
    (state/'A2_PROGRESS.json').write_text('{"raw_verified":true}')
    private = state/'.sessions/a2-fit-freecpu-a2-001'
    private.mkdir(parents=True)
    (private/'state.json').write_text('{"session_url":"PRIVATE_UPLOAD_URI"}')
    (state/'drive-access.json').write_text('{"access_token":"NEVER_ARCHIVE"}')
    class Session:
        blob = None
        def post(self,url,**kwargs):
            body = kwargs['data']
            self.blob = body.split(b'Content-Type: application/zip\r\n\r\n',1)[1].rsplit(b'\r\n--',1)[0]
            assert b'NEVER_ARCHIVE' not in self.blob
            return SimpleNamespace(status_code=200,json=lambda:{'id':'snapshot'})
        def get(self,url,**kwargs):
            pin = dict(id='snapshot',size=len(self.blob),sha256Checksum=hashlib.sha256(self.blob).hexdigest(),parents=['private-folder'])
            if kwargs.get('params',{}).get('alt') == 'media':
                return SimpleNamespace(status_code=200,content=self.blob)
            if url.endswith('/files'):
                return SimpleNamespace(status_code=200,json=lambda:{'files':[pin]})
            return SimpleNamespace(status_code=200,json=lambda:pin)
    session = Session()
    runner.state_snapshot(session,'private-folder',state)
    restored = tmp_path/'restored'
    runner.state_snapshot(session,'private-folder',restored,restore=True)
    assert (restored/'A2_PROGRESS.json').read_text() == '{"raw_verified":true}'
    assert (restored/'.sessions/a2-fit-freecpu-a2-001/state.json').read_text() == '{"session_url":"PRIVATE_UPLOAD_URI"}'
    assert not (restored/'drive-access.json').exists()


def test_snapshot_rejects_unlisted_or_parent_traversal_member(tmp_path):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer,'w') as archive:
        archive.writestr('.sessions/../../bad/state.json','{}')
    blob = buffer.getvalue()
    pin = dict(id='bad',size=len(blob),sha256Checksum=hashlib.sha256(blob).hexdigest())
    class Session:
        def get(self,url,**kwargs):
            if kwargs.get('params',{}).get('alt') == 'media':
                return SimpleNamespace(status_code=200,content=blob)
            return SimpleNamespace(status_code=200,json=lambda:{'files':[pin]})
    with pytest.raises(RuntimeError,match='MEMBER_REJECTED'):
        runner.state_snapshot(Session(),'private-folder',tmp_path/'state',restore=True)


def test_progress_and_upload_offset_writes_trigger_private_snapshot(tmp_path):
    state = tmp_path/'state'
    assert runner.checkpoint_write(state/'A2_PROGRESS.json',state)
    assert runner.checkpoint_write(state/'.sessions/fit1/state.json',state)
    assert not runner.checkpoint_write(state/'drive-access.json',state)
    assert not runner.checkpoint_write(tmp_path/'outside/state.json',state)


def test_bootstrap_partial_venv_uses_uv_target_only(tmp_path, monkeypatch):
    python = tmp_path/'.venv/bin/python'
    python.parent.mkdir(parents=True)
    python.write_text('partial venv without pip')
    calls = []
    monkeypatch.setattr(runner.shutil, 'which', lambda name: '/usr/local/bin/uv')
    monkeypatch.setattr(runner.subprocess, 'run', lambda command, **kwargs: calls.append((command, kwargs)))
    monkeypatch.setattr(runner.venv, 'EnvBuilder', lambda **kwargs: pytest.fail('must reuse existing venv'))
    assert runner.bootstrap_venv(tmp_path) == python
    command, kwargs = calls[0]
    assert command == ['/usr/local/bin/uv','pip','install','--python',str(python),*runner.DEPENDENCIES]
    assert kwargs['env']['UV_CACHE_DIR'] == str(tmp_path/'artifacts/akt/uv-cache')
    assert kwargs['check'] is True


def test_bootstrap_new_venv_does_not_run_ensurepip(tmp_path, monkeypatch):
    creates = []
    monkeypatch.setattr(runner.shutil, 'which', lambda name: '/usr/local/bin/uv')
    monkeypatch.setattr(runner.venv, 'EnvBuilder', lambda **kwargs: SimpleNamespace(create=lambda path: creates.append((kwargs,path))))
    monkeypatch.setattr(runner.subprocess, 'run', lambda *args, **kwargs: None)
    runner.bootstrap_venv(tmp_path)
    assert creates == [({'with_pip':False},tmp_path/'.venv')]


def test_subprocess_failure_diagnostic_never_exposes_arguments_or_output():
    error = runner.subprocess.CalledProcessError(3,['/bin/uv','secret-token'],output='https://private?token=secret')
    assert runner.failure_detail(error) == {'command':'uv','returncode':3}


def test_notebook_bootstrap_targets_venv_without_ensurepip():
    notebook = Path(__file__).resolve().parents[2]/'notebooks/akt_colab_response_calibration_cpu.ipynb'
    cells = json.loads(notebook.read_text(encoding='utf-8'))['cells']
    bootstrap = next(''.join(cell['source']) for cell in cells
        if cell['cell_type'] == 'code' and 'venv.EnvBuilder(' in ''.join(cell['source']))
    assert 'with_pip=False' in bootstrap and 'with_pip=True' not in bootstrap
    assert "[UV,'pip','install','--python',PYTHON," in bootstrap
    assert 'UV_CACHE_DIR' in bootstrap
    assert 'subprocess,venv,os' in bootstrap
