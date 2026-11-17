import hashlib
import json
from pathlib import Path

import pytest

from scripts.akt import colab_cpu_execution as cpu
from scripts.akt import colab_session as auth


SPEC = {'variant':'VARIANT_CPU','accelerator':'NONE','shape':'SHAPE_STANDARD'}


class Client:
    def __init__(self, *, tier='SUBSCRIPTION_TIER_FREE', existing=True):
        self.tier, self.existing = tier, existing
        self.calls = []
        self.runtime = {'name':'runtimes/cpu1','runtimeSpec':SPEC}

    def call(self, tool, arguments=None):
        self.calls.append((tool, arguments))
        if tool == 'get_subscription':
            return {'tier':self.tier}
        if tool == 'list_runtime_specs':
            return {'runtimeSpecs':[{'key':SPEC,'eligible':True}]}
        if tool == 'list_runtimes':
            return {'runtimes':[self.runtime] if self.existing else []}
        if tool == 'get_runtime':
            return self.runtime
        raise AssertionError(tool)


def context(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, 'PRIVATE', tmp_path)
    return tmp_path / 'cpu.json'


def test_paid_subscription_stops_before_any_mutation(tmp_path, monkeypatch):
    state = context(tmp_path, monkeypatch)
    monkeypatch.setattr(cpu, '_mutate', lambda *args: pytest.fail('mutation forbidden'))
    with pytest.raises(auth.ColabSessionError, match='FREE'):
        cpu.ensure_cpu_runtime(Client(tier='SUBSCRIPTION_TIER_PRO'), state)


def test_reuses_cpu_without_touching_existing_user_sessions(tmp_path, monkeypatch):
    state = context(tmp_path, monkeypatch)
    monkeypatch.setattr(cpu, '_mutate', lambda *args: pytest.fail('create forbidden'))
    result = cpu.ensure_cpu_runtime(Client(), state)
    assert result['name'] == 'runtimes/cpu1' and not result['owned']


def test_create_pin_written_before_send_and_timeout_reattaches_identical(tmp_path, monkeypatch):
    state = context(tmp_path, monkeypatch)
    sent = []
    def mutation(client, tool, arguments):
        persisted = json.loads(state.read_text())
        assert persisted['runtime_request']['arguments'] == arguments
        assert arguments['runtime']['runtimeSpec'] == SPEC
        sent.append(arguments)
        if len(sent) == 1:
            raise auth.ColabSessionError('COLAB_RPC_ERROR_4')
        return {'name':'runtimes/newcpu','runtimeSpec':SPEC}
    monkeypatch.setattr(cpu, '_mutate', mutation)
    with pytest.raises(auth.ColabSessionError):
        cpu.ensure_cpu_runtime(Client(existing=False), state)
    assert json.loads(state.read_text())['runtime_request']['status'] == 'UNCERTAIN'
    assert cpu.ensure_cpu_runtime(Client(existing=False), state)['owned']
    assert sent[0] == sent[1]


def test_ineligible_or_accelerated_runtime_never_admitted(tmp_path, monkeypatch):
    state = context(tmp_path, monkeypatch)
    client = Client()
    client.runtime = {'name':'runtimes/gpu','runtimeSpec':dict(SPEC,variant='VARIANT_GPU',accelerator='H100')}
    original = client.call
    client.call = lambda tool, args=None: {'runtimeSpecs':[]} if tool == 'list_runtime_specs' else original(tool,args)
    monkeypatch.setattr(cpu, '_mutate', lambda *args: pytest.fail('mutation forbidden'))
    with pytest.raises(auth.ColabSessionError, match='ELIGIBLE'):
        cpu.ensure_cpu_runtime(client, state)


@pytest.mark.parametrize('timeout_once', [False, True])
def test_execution_completion_is_not_sent_twice(tmp_path, monkeypatch, timeout_once):
    state = context(tmp_path, monkeypatch)
    root = tmp_path / 'repo'
    script = root / 'scripts/akt/approved.py'
    script.parent.mkdir(parents=True)
    script.write_text('print(1)\n')
    monkeypatch.setattr(cpu, 'ROOT', root)
    calls = []
    def mutation(client, tool, arguments):
        calls.append((tool, arguments))
        saved = json.loads(state.read_text())
        if tool == 'create_session':
            assert saved['session_request']['arguments'] == arguments
            return {'name':arguments['parent']+'/sessions/'+arguments['sessionId']}
        assert tool == 'execute_code'
        assert saved['executions']['calib-a2']['arguments'] == arguments
        if timeout_once and sum(name == 'execute_code' for name, _ in calls) == 1:
            raise auth.ColabSessionError('COLAB_RPC_ERROR_4')
        return {'session':arguments['session'],'executionId':arguments['executionId'],
                'stdout':'SECRET https://private.example/', 'result':'done'}
    monkeypatch.setattr(cpu, '_mutate', mutation)
    expected = hashlib.sha256(script.read_bytes()).hexdigest()
    if timeout_once:
        with pytest.raises(auth.ColabSessionError):
            cpu.execute_script(Client(), state, script, expected, 'calib-a2')
        saved = json.loads(state.read_text())
        assert saved['executions']['calib-a2']['status'] == 'UNCERTAIN'
    first = cpu.execute_script(Client(), state, script, expected, 'calib-a2')
    second = cpu.execute_script(Client(), state, script, expected, 'calib-a2')
    assert first == second and first['status'] == 'COMPLETE'
    sent = [args for tool, args in calls if tool == 'execute_code']
    assert len(sent) == (2 if timeout_once else 1)
    assert all(arguments == sent[0] for arguments in sent)
    assert 'SECRET' not in json.dumps(first) and 'https://' not in json.dumps(first)


def test_untrusted_or_changed_script_rejected(tmp_path, monkeypatch):
    state = context(tmp_path, monkeypatch)
    script = tmp_path / 'outside.py'
    script.write_text('print(1)')
    monkeypatch.setattr(cpu, '_mutate', lambda *args: pytest.fail('mutation forbidden'))
    with pytest.raises(auth.ColabSessionError):
        cpu.execute_script(Client(), state, script, '0'*64, 'phase')


def test_bad_runtime_response_is_never_marked_complete(tmp_path, monkeypatch):
    state = context(tmp_path, monkeypatch)
    calls = []
    def mutation(*args):
        calls.append(args)
        return {'name':'runtimes/incorrect','runtimeSpec':dict(SPEC,accelerator='H100')}
    monkeypatch.setattr(cpu, '_mutate', mutation)
    with pytest.raises(auth.ColabSessionError):
        cpu.ensure_cpu_runtime(Client(existing=False), state)
    assert json.loads(state.read_text())['runtime_request']['status'] == 'FAILED'
    with pytest.raises(auth.ColabSessionError):
        cpu.ensure_cpu_runtime(Client(existing=False), state)
    assert len(calls) == 1


def test_terminal_create_failure_is_not_retried(tmp_path, monkeypatch):
    state = context(tmp_path, monkeypatch)
    calls = []
    def mutation(*args):
        calls.append(args)
        raise auth.ColabSessionError('COLAB_RPC_ERROR_9')
    monkeypatch.setattr(cpu, '_mutate', mutation)
    for _ in range(2):
        with pytest.raises(auth.ColabSessionError):
            cpu.ensure_cpu_runtime(Client(existing=False), state)
    assert len(calls) == 1


def test_tampered_pending_create_cannot_change_tool(tmp_path, monkeypatch):
    state = context(tmp_path, monkeypatch)
    state.write_text(json.dumps({'version':1,'executions':{},'runtime_request':{
        'tool':'execute_code','status':'PENDING','arguments':{'runtime':{'runtimeSpec':SPEC},'requestId':'wrong'}}}))
    monkeypatch.setattr(cpu, '_mutate', lambda *args: pytest.fail('mutation forbidden'))
    with pytest.raises(auth.ColabSessionError):
        cpu.ensure_cpu_runtime(Client(existing=False), state)
