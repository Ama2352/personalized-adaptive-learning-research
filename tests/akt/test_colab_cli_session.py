import json

import pytest

from scripts.akt import colab_cli_session as cli
from scripts.akt import colab_session as auth


def test_get_recovers_connection_failure_without_retrying_post(monkeypatch):
    import requests
    calls = []
    def request(method, url, **kwargs):
        calls.append(method)
        if len(calls) == 1:
            raise requests.ConnectionError('synthetic network failure')
        return Response({'ok': True})
    session = type('RetrySession', (), {'request': staticmethod(request)})()
    monkeypatch.setattr(cli.time, 'sleep', lambda seconds: None)
    assert cli.read_json(session, 'GET', 'https://fake.invalid/read') == {'ok': True}
    assert calls == ['GET', 'GET']
    calls.clear()
    with pytest.raises(auth.ColabSessionError, match='ConnectionError'):
        cli.read_json(session, 'POST', 'https://fake.invalid/write')
    assert calls == ['POST']


class Response:
    def __init__(self, value, status=200):
        self.text = ")]}'\n" + json.dumps(value)
        self.status_code = status
    def close(self):
        pass


class Session:
    def __init__(self):
        self.calls = []
        self.assigned = False
        self.rate = 0
        self.free_tokens = None
    def request(self, method, url, **kwargs):
        self.calls.append((method,url,kwargs))
        if url.endswith('ccu-info'):
            usage = dict(currentBalance=0,consumptionRateHourly=self.rate,assignmentsCount=int(self.assigned))
            if self.free_tokens is not None:
                usage['freeCcuQuotaInfo'] = {'remainingTokens':self.free_tokens}
            return Response(usage)
        if url.endswith('assignments'):
            rows = [dict(endpoint='cpu-owned',accelerator='NONE',variant=0,machineShape=0,
                         runtimeProxyInfo={'url':'https://fake.googleusercontent.com/','token':'PRIVATE','tokenExpiresInSeconds':3600})] if self.assigned else []
            return Response(dict(assignments=rows))
        assert url.endswith('/assign')
        assert kwargs['params']['variant'] == 'DEFAULT'
        assert kwargs['params']['accelerator'] == 'NONE'
        assert 'shape' not in kwargs['params']
        if method == 'GET':
            return Response(dict(acc='NONE',variant='DEFAULT',nbh=kwargs['params']['nbh'],token='XSRF_PRIVATE'))
        assert kwargs['headers']['X-Goog-Colab-Token'] == 'XSRF_PRIVATE'
        self.assigned = True
        return Response(dict(endpoint='cpu-owned',accelerator='NONE',variant=0,
                        runtimeProxyInfo={'url':'https://fake.googleusercontent.com/','token':'PRIVATE','tokenExpiresInSeconds':3600}))


def test_cpu_assignment_pins_before_post_and_reuses(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, 'PRIVATE', tmp_path)
    state = tmp_path/'cli.json'
    session = Session()
    original = session.request
    def request(method, url, **kwargs):
        if method == 'POST':
            saved = json.loads(state.read_text())
            assert saved['assign_params'] == kwargs['params']
        return original(method,url,**kwargs)
    session.request = request
    result = cli.ensure_cpu_assignment(session,state)
    assert result['endpoint'] == 'cpu-owned' and result['accelerator'] == 'NONE'
    cli.ensure_cpu_assignment(session,state)
    assert sum(method == 'POST' for method,_,_ in session.calls) == 1


def test_nonzero_consumption_stops_before_assign(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, 'PRIVATE', tmp_path)
    session = Session()
    session.rate = .1
    with pytest.raises(auth.ColabSessionError, match='QUOTA'):
        cli.ensure_cpu_assignment(session,tmp_path/'cli.json')
    assert not any(url.endswith('/assign') for _,url,_ in session.calls)


def test_error_does_not_disclose_body_or_private_url():
    session = Session()
    session.request = lambda *args,**kwargs: Response({'secret':'PRIVATE'},status=403)
    with pytest.raises(auth.ColabSessionError) as error:
        cli.read_json(session,'GET','https://colab.research.google.com/tun/m/assignments')
    assert str(error.value) == 'COLAB_CLI_HTTP_403'


def test_free_cpu_quota_allows_positive_compute_unit_rate(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, 'PRIVATE', tmp_path)
    session = Session()
    session.rate = .08
    session.free_tokens = '4568'
    result = cli.ensure_cpu_assignment(session,tmp_path/'cli.json')
    assert result['accelerator'] == 'NONE'


def test_kernel_session_is_owned_and_reused_without_deleting_user_session(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, 'PRIVATE', tmp_path)
    state = tmp_path/'cli.json'
    assignment = dict(endpoint='cpu-owned',runtimeProxyInfo={'url':'https://fake.googleusercontent.com/','token':'PRIVATE'})
    monkeypatch.setattr(cli, 'ensure_cpu_assignment', lambda *args: assignment)
    sessions = [{'id':'user-session','path':'content/user.ipynb','kernel':{'id':'user-kernel','name':'python3'}}]
    calls = []
    def proxy_call(proxy, assignment, method, path, **kwargs):
        calls.append((method,path,kwargs))
        if path == 'api/sessions' and method == 'GET':
            return list(sessions)
        if path == 'api/sessions':
            request = kwargs['json']
            saved = json.loads(state.read_text())
            assert saved['kernel_request']['path'] == request['path']
            result = dict(id='own-session',path=request['path'],kernel={'id':'own-kernel','name':'python3'})
            sessions.append(result)
            return result
        return {}
    monkeypatch.setattr(cli, '_proxy_request', proxy_call)
    first = cli.ensure_kernel(object(),state,proxy_session=object())
    second = cli.ensure_kernel(object(),state,proxy_session=object())
    assert first[1] == second[1] and first[1]['kernel_id'] == 'own-kernel'
    assert len([c for c in calls if c[0]=='POST']) == 1
    assert all(c[0] != 'DELETE' for c in calls)
    assert sessions[0]['kernel']['id'] == 'user-kernel'


def test_discovery_closes_transport_without_shutdown(tmp_path, monkeypatch):
    assignment = dict(endpoint='cpu-owned',runtimeProxyInfo={'url':'https://fake.googleusercontent.com/','token':'PRIVATE'})
    kernel = dict(kernel_id='own-kernel',wire_session_id='own-wire')
    monkeypatch.setattr(cli, 'ensure_kernel', lambda *args,**kwargs:(assignment,kernel))
    seen = {}
    class Kernel:
        def __init__(self, **kwargs):
            seen['kwargs'] = kwargs
            self._manager = type('Manager',(),{'client':type('Wire',(),{
                'stop_channels':lambda wire:seen.update(channels_closed=True),
                'kernel_socket':type('Socket',(),{'close':lambda socket:seen.update(socket_closed=True)})()})()})()
        def start(self, **kwargs):
            assert self._own_kernel is False
        def execute(self, code, **kwargs):
            assert kwargs['allow_stdin'] is False
            return {'status':'ok','outputs':[{'output_type':'stream','text':'{"python":"3.test","executable":"/usr/bin/python3","available_memory_bytes":10000000000}\n'}]}
        def stop(self, **kwargs):
            raise AssertionError('Manager stop must never run')
    result = cli.discover_cpu(object(),tmp_path/'state.json',kernel_factory=Kernel)
    assert result['python'] == '3.test'
    assert seen['channels_closed'] and seen['socket_closed']
    assert seen['kwargs']['headers']['X-Colab-Runtime-Proxy-Token'] == 'PRIVATE'
    assert 'PRIVATE' not in json.dumps(result) and 'https://' not in json.dumps(result)


@pytest.mark.parametrize('primary_failure', [False, True])
def test_cleanup_failure_never_hides_primary_discovery_result(tmp_path, monkeypatch, primary_failure):
    assignment = dict(endpoint='cpu-owned',runtimeProxyInfo={'url':'https://fake.googleusercontent.com/','token':'PRIVATE'})
    kernel = dict(kernel_id='own-kernel',wire_session_id='own-wire')
    monkeypatch.setattr(cli,'ensure_kernel',lambda *args,**kwargs:(assignment,kernel))
    class Kernel:
        def __init__(self,**kwargs):
            class Wire:
                kernel_socket = None
                def stop_channels(self):
                    raise TimeoutError('Private cleanup failed')
            self._manager = type('Manager',(),{'client':Wire()})()
        def start(self,**kwargs):
            if primary_failure:
                raise ConnectionError('Private primary failed')
        def execute(self,*args,**kwargs):
            return {'status':'ok','outputs':[{'output_type':'stream','text':'{"python":"test","executable":"python","available_memory_bytes":1000}'}]}
        def stop(self,**kwargs):
            raise TimeoutError('Forbidden manager cleanup')
    if primary_failure:
        with pytest.raises(auth.ColabSessionError,match='CPU_DISCOVERY_ConnectionError'):
            cli.discover_cpu(object(),tmp_path/'state.json',kernel_factory=Kernel)
    else:
        assert cli.discover_cpu(object(),tmp_path/'state.json',kernel_factory=Kernel)['python'] == 'test'


def test_constructor_timeout_retries_only_same_known_kernel(tmp_path, monkeypatch):
    import requests
    assignment = dict(endpoint='cpu-owned',runtimeProxyInfo={'url':'https://fake.googleusercontent.com/','token':'PRIVATE'})
    kernel = dict(kernel_id='same-kernel',wire_session_id='same-wire')
    monkeypatch.setattr(cli,'ensure_kernel',lambda *args,**kwargs:(assignment,kernel))
    delays = []
    monkeypatch.setattr(cli.time,'sleep',lambda seconds:delays.append(seconds),raising=False)
    calls,executed = [],[]
    class Kernel:
        def __init__(self,**kwargs):
            calls.append(kwargs)
            if len(calls) < 3:
                raise requests.ConnectTimeout('private endpoint')
            self._manager = type('Manager',(),{'client':type('Wire',(),{'stop_channels':lambda wire:None,'kernel_socket':None})()})()
        def start(self,**kwargs):
            pass
        def execute(self,*args,**kwargs):
            executed.append(True)
            return {'status':'ok','outputs':[{'output_type':'stream','text':'{"python":"test","executable":"python","available_memory_bytes":1000}'}]}
    result = cli.discover_cpu(object(),tmp_path/'state.json',kernel_factory=Kernel)
    assert result['python'] == 'test' and len(calls) == 3 and len(executed) == 1
    assert all(call['kernel_id']=='same-kernel' for call in calls) and delays == [2,4]


@pytest.mark.parametrize('drop_connection',[False,True])
def test_trusted_phase_is_pinned_before_execute_and_never_auto_repeated(tmp_path,monkeypatch,drop_connection):
    import hashlib
    monkeypatch.setattr(auth,'PRIVATE',tmp_path)
    repo = tmp_path/'repo'
    script = repo/'scripts/akt/approved_phase.py'
    script.parent.mkdir(parents=True)
    script.write_text("print('phase')\n")
    monkeypatch.setattr(auth,'ROOT',repo)
    assignment = dict(endpoint='cpu-owned',runtimeProxyInfo={'url':'https://fake.googleusercontent.com/','token':'PRIVATE'})
    kernel = dict(kernel_id='known',wire_session_id='wire')
    monkeypatch.setattr(cli,'ensure_kernel',lambda *args,**kwargs:(assignment,kernel))
    state = tmp_path/'state.json'
    calls = []
    class Kernel:
        def execute(self,code,**kwargs):
            calls.append(code)
            phase = json.loads(state.read_text())['phases']['calibration-a2']
            assert phase['status'] == 'RUNNING_OR_UNCERTAIN'
            assert phase['phase_id'] in code
            assert kwargs['timeout'] == 3600 and kwargs['allow_stdin'] is False
            if drop_connection:
                raise ConnectionError('private URL must stay hidden')
            return {'status':'ok','outputs':[{'output_type':'stream','text':'PRIVATE OUTPUT'}]}
    monkeypatch.setattr(cli,'_connect_kernel',lambda *args,**kwargs:Kernel())
    monkeypatch.setattr(cli,'_close_kernel_transport',lambda *args:None)
    digest = hashlib.sha256(script.read_bytes()).hexdigest()
    if drop_connection:
        with pytest.raises(auth.ColabSessionError,match='UNCERTAIN'):
            cli.execute_phase(object(),state,script,digest,'calibration-a2')
        with pytest.raises(auth.ColabSessionError,match='ALREADY_SENT'):
            cli.execute_phase(object(),state,script,digest,'calibration-a2')
    else:
        result = cli.execute_phase(object(),state,script,digest,'calibration-a2')
        assert result['success'] and 'PRIVATE' not in json.dumps(result)
        assert cli.execute_phase(object(),state,script,digest,'calibration-a2') == result
    assert len(calls) == 1
