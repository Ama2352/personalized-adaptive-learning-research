import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.akt import colab_session as colab


class Credentials:
    valid = False
    expired = True
    refresh_token = 'private-refresh'

    def __init__(self):
        self.refreshed = 0
        self.scopes = list(colab.SCOPES)
        self.granted_scopes = list(colab.SCOPES)

    def has_scopes(self, scopes):
        return True

    def refresh(self, request):
        self.refreshed += 1
        self.valid = True

    def to_json(self):
        return json.dumps({'token': 'private-access', 'refresh_token': self.refresh_token,
                           'client_id':'fake-client','client_secret':'fake-secret',
                           'scopes':self.scopes,
                           'expiry':(datetime.now(timezone.utc)+timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ')})


class Response:
    status_code = 200
    headers = {'Content-Type': 'application/json'}

    def __init__(self, value):
        self.text = json.dumps(value)

    def close(self):
        pass


class Session:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, endpoint, **kwargs):
        self.calls.append(kwargs)
        return Response(self.responses.pop(0))


def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(colab, 'PRIVATE', tmp_path)
    return tmp_path / 'token.json', tmp_path / 'proxy.json'


def test_expired_credential_refresh_persists_without_browser(tmp_path, monkeypatch):
    token, _ = setup(tmp_path, monkeypatch)
    token.write_text('{}')
    credentials = Credentials()
    class Factory:
        @staticmethod
        def from_authorized_user_file(path):
            return credentials
    loaded = colab.load_credentials(token, tmp_path / 'client.json', credentials_type=Factory,
                                     request_factory=lambda: object())
    assert loaded is credentials and credentials.refreshed == 1
    assert json.loads(token.read_text())['refresh_token'] == 'private-refresh'


def test_missing_token_requires_explicit_login(tmp_path, monkeypatch):
    token, _ = setup(tmp_path, monkeypatch)
    with pytest.raises(colab.ColabSessionError, match='LOGIN_REQUIRED'):
        colab.load_credentials(token, tmp_path / 'client.json')


def test_rpc_error_does_not_expose_server_urls_or_tokens(tmp_path, monkeypatch):
    token, proxy = setup(tmp_path, monkeypatch)
    credentials = Credentials()
    session = Session([{'jsonrpc':'2.0','id':1,'error':{'code':403,'message':'https://private.example/?token=SECRET'}}])
    client = colab.ColabClient(session, credentials, token, proxy)
    with pytest.raises(colab.ColabSessionError) as result:
        client.call('get_subscription')
    assert 'SECRET' not in str(result.value) and 'https://' not in str(result.value)
    assert '403' in str(result.value)


def test_runtime_proxy_is_private_and_reused_until_near_expiry(tmp_path, monkeypatch):
    token, proxy = setup(tmp_path, monkeypatch)
    expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    runtime = {'name':'runtimes/existing','runtimeSpec':{'variant':'VARIANT_CPU'},
               'connectionInfo':{'token':'PROXY_SECRET','url':'https://private.example/','expireTime':expires}}
    session = Session([{'jsonrpc':'2.0','id':1,'result':{'structuredContent':runtime}}])
    client = colab.ColabClient(session, Credentials(), token, proxy)
    assert client.runtime('runtimes/existing') == runtime
    assert client.runtime('runtimes/existing') == runtime and len(session.calls) == 1
    safe = colab.public_result(runtime)
    assert 'PROXY_SECRET' not in json.dumps(safe) and 'https://' not in json.dumps(safe)
    assert json.loads(proxy.read_text())['runtimes/existing']['connectionInfo']['token'] == 'PROXY_SECRET'


def test_expired_runtime_proxy_fetches_again(tmp_path, monkeypatch):
    token, proxy = setup(tmp_path, monkeypatch)
    old = {'name':'runtimes/existing','connectionInfo':{'token':'OLD','url':'https://private.example/',
            'expireTime':(datetime.now(timezone.utc)-timedelta(minutes=1)).isoformat()}}
    proxy.write_text(json.dumps({'runtimes/existing':old}))
    new = dict(old, connectionInfo=dict(old['connectionInfo'], token='NEW',
        expireTime=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()))
    session = Session([{'id':1,'result':{'structuredContent':new}}])
    client = colab.ColabClient(session, Credentials(), token, proxy)
    assert client.runtime('runtimes/existing')['connectionInfo']['token'] == 'NEW'
    assert len(session.calls) == 1


def test_sse_terminal_result_is_parsed_without_logging():
    response = Response({})
    response.headers = {'Content-Type':'text/event-stream'}
    response.text = 'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"structuredContent":{"tier":"SUBSCRIPTION_TIER_FREE"}}}\n\n'
    assert colab.parse_response(response)['result']['structuredContent']['tier'] == 'SUBSCRIPTION_TIER_FREE'


def test_compute_tools_and_invalid_runtime_rejected_before_network(tmp_path, monkeypatch):
    token, proxy = setup(tmp_path, monkeypatch)
    session = Session([])
    client = colab.ColabClient(session, Credentials(), token, proxy)
    with pytest.raises(colab.ColabSessionError):
        client.call('create_runtime')
    with pytest.raises(colab.ColabSessionError):
        client.runtime('https://example.invalid/credentials')
    assert not session.calls


def test_private_paths_cannot_escape(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    with pytest.raises(colab.ColabSessionError):
        colab.save_private(tmp_path.parent / 'outside.json', {})


def test_explicit_login_requests_offline_without_logging_auth_url(tmp_path, monkeypatch, capsys):
    token, _ = setup(tmp_path, monkeypatch)
    config = tmp_path / 'desktop.json'
    config.write_text('{}')
    credentials = Credentials()
    credentials.valid = True
    calls = {}
    monkeypatch.setattr(colab, 'edge_browser', lambda: 'kltn-edge', raising=False)
    class Flow:
        @classmethod
        def from_client_secrets_file(cls, path, scopes):
            calls.update(path=path, scopes=scopes)
            return cls()
        def run_local_server(self, **kwargs):
            calls.update(kwargs)
            return credentials
    loaded = colab.load_credentials(token, config, interactive=True, flow_type=Flow)
    assert loaded.has_scopes(colab.SCOPES)
    assert calls['access_type'] == 'offline' and calls['open_browser']
    assert calls['host'] == 'localhost' and calls['port'] == 0
    assert calls['browser'] == 'kltn-edge' and calls['timeout_seconds'] == 600
    assert colab.COLAB_SCOPE in calls['scopes']
    assert 'https://' not in calls['authorization_prompt_message']
    assert capsys.readouterr().out == ''


def test_missing_scope_requires_explicit_new_consent(tmp_path, monkeypatch):
    token, _ = setup(tmp_path, monkeypatch)
    token.write_text('{}')
    credentials = Credentials()
    credentials.valid = True
    credentials.has_scopes = lambda scopes: False
    class Factory:
        @staticmethod
        def from_authorized_user_file(path):
            return credentials
    with pytest.raises(colab.ColabSessionError, match='LOGIN_REQUIRED'):
        colab.load_credentials(token, tmp_path / 'desktop.json', credentials_type=Factory)
    assert token.read_text() == '{}'


def test_read_call_saves_credentials_refreshed_by_authorized_session(tmp_path, monkeypatch):
    token, proxy = setup(tmp_path, monkeypatch)
    credentials = Credentials()
    class RefreshingSession(Session):
        def post(self, *args, **kwargs):
            credentials.refresh(object())
            return super().post(*args, **kwargs)
    client = colab.ColabClient(RefreshingSession([{'id':1,'result':{
        'structuredContent':{'tier':'SUBSCRIPTION_TIER_FREE'}}}]), credentials, token, proxy)
    assert client.call('get_subscription')['tier'] == 'SUBSCRIPTION_TIER_FREE'
    assert credentials.refreshed == 1 and token.is_file()


def test_http_error_body_is_never_exposed(tmp_path, monkeypatch):
    token, proxy = setup(tmp_path, monkeypatch)
    class FailingSession(Session):
        def post(self, *args, **kwargs):
            response = Response({'message':'https://secret.example/?token=SECRET'})
            response.status_code = 403
            return response
    client = colab.ColabClient(FailingSession([]), Credentials(), token, proxy)
    with pytest.raises(colab.ColabSessionError, match='COLAB_HTTP_403') as error:
        client.call('list_runtimes')
    assert 'SECRET' not in str(error.value) and 'https://' not in str(error.value)


@pytest.mark.parametrize('warning', [False, True])
def test_partial_consent_never_saves_requested_scopes_as_granted(tmp_path, monkeypatch, capsys, warning):
    token, _ = setup(tmp_path, monkeypatch)
    config = tmp_path / 'client.json'
    config.write_text('{}')
    monkeypatch.setattr(colab, 'edge_browser', lambda: 'kltn-edge')
    credentials = Credentials()
    credentials.valid = True
    credentials.granted_scopes = ['openid','https://www.googleapis.com/auth/userinfo.email']
    class Flow:
        oauth2session = SimpleNamespace(token={'scope':credentials.granted_scopes})
        @classmethod
        def from_client_secrets_file(cls, *args, **kwargs):
            return cls()
        def run_local_server(self, **kwargs):
            if warning:
                error = Warning('SECRET https://private.example/')
                error.new_scope = credentials.granted_scopes
                error.token = {'access_token':'SECRET','scope':credentials.granted_scopes}
                raise error
            return credentials
    with pytest.raises(colab.ColabSessionError, match='COLAB_RUNTIME') as error:
        colab.load_credentials(token, config, interactive=True, flow_type=Flow)
    assert not token.exists()
    assert 'SECRET' not in str(error.value) and 'https://' not in str(error.value)
    assert capsys.readouterr().out == ''


def test_full_grants_with_extra_scope_warning_can_be_saved_as_actual(tmp_path, monkeypatch):
    token, _ = setup(tmp_path, monkeypatch)
    config = tmp_path / 'client.json'
    config.write_text('{}')
    monkeypatch.setattr(colab, 'edge_browser', lambda: 'kltn-edge')
    actual = ['openid','email',colab.COLAB_SCOPE,'https://www.googleapis.com/auth/drive.file']
    credentials = Credentials()
    credentials.valid = True
    credentials.granted_scopes = actual
    class Flow:
        oauth2session = SimpleNamespace(token={})
        @classmethod
        def from_client_secrets_file(cls, *args, **kwargs):
            return cls()
        def run_local_server(self, **kwargs):
            error = Warning('Scope changed, private token not logged')
            error.new_scope = actual
            error.token = {'access_token':'SECRET','scope':actual}
            raise error
        @property
        def credentials(self):
            assert self.oauth2session.token['scope'] == actual
            return credentials
    loaded = colab.load_credentials(token, config, interactive=True, flow_type=Flow)
    saved = json.loads(token.read_text())
    assert loaded.has_scopes(colab.SCOPES)
    assert saved['scopes'] == sorted(set(colab.SCOPES) | {'https://www.googleapis.com/auth/drive.file'})


def test_partial_automatic_refresh_is_not_persisted_as_full_scope(tmp_path, monkeypatch):
    token, proxy = setup(tmp_path, monkeypatch)
    credentials = Credentials()
    class PartialSession(Session):
        def post(self, *args, **kwargs):
            credentials.granted_scopes = ['openid','email']
            return super().post(*args, **kwargs)
    client = colab.ColabClient(PartialSession([{'id':1,'result':{'structuredContent':{}}}]), credentials, token, proxy)
    with pytest.raises(colab.ColabSessionError, match='COLAB_RUNTIME'):
        client.call('get_subscription')
    assert not token.exists()
