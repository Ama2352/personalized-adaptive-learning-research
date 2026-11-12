"""Watchdog deadline/stop bằng callback giả, không gọi cloud hoặc nạp Torch."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import threading

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('modal_budget_guard_unit', ROOT/'experiments/akt/modal_budget_guard.py')
guard_module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = guard_module
SPEC.loader.exec_module(guard_module)
OwnedModalApp = guard_module.OwnedModalApp
ModalRunDeadline = guard_module.ModalRunDeadline
ModalAppBudgetGuard = guard_module.ModalAppBudgetGuard


def owned():
    return OwnedModalApp('unit-run', 'ap-UnitRun123', 'kltn-akt-unit-run')


@pytest.mark.parametrize('run,app,name', [
    ('../foreign','ap-Unit','kltn-akt-../foreign'),
    ('unit-run','ap-Unit;echo','kltn-akt-unit-run'),
    ('unit-run','ap-Unit','foreign-app'),
    ('unit-run','','kltn-akt-unit-run'),
])
def test_owned_binding_rejects_unrelated_or_invalid_identifiers(run, app, name):
    with pytest.raises(ValueError):
        OwnedModalApp(run, app, name)


@pytest.mark.parametrize('seconds', [0,-1,True,float('inf'),float('nan')])
def test_deadline_requires_finite_positive_seconds(seconds):
    with pytest.raises(ValueError):
        ModalRunDeadline(seconds)


def test_total_deadline_includes_time_before_guard_attachment():
    now = [100.]
    deadline = ModalRunDeadline(3, clock=lambda:now[0])
    now[0] = 102.
    assert deadline.remaining() == 1.
    now[0] = 103.
    with pytest.raises(guard_module.ModalDeadlineExceeded):
        deadline.remaining()


def test_pending_owned_id_stops_during_app_context_startup(tmp_path):
    stopped = threading.Event()
    app_id = [None]
    calls = []
    binding = guard_module.PendingOwnedModalApp('unit-run','kltn-akt-unit-run',lambda:app_id[0])
    def stop(app):
        calls.append(app)
        stopped.set()
    class StartupContext:
        def __enter__(self):
            app_id[0] = 'ap-UnitRun123'
            assert stopped.wait(2), 'Watchdog did not cover app.run startup'
        def __exit__(self,*args):
            return False
    with pytest.raises(guard_module.ModalDeadlineExceeded):
        with ModalAppBudgetGuard(binding,ModalRunDeadline(.2),stop_app=stop,
                                 diagnostic_path=tmp_path/'guard.json') as guard:
            with StartupContext():
                guard.remaining()
    assert calls == [owned()]


def test_missing_pending_id_is_unconfirmed_and_preserved(tmp_path):
    calls = []
    binding = guard_module.PendingOwnedModalApp('unit-run','kltn-akt-unit-run',lambda:None)
    path = tmp_path/'guard.json'
    with pytest.raises(guard_module.ModalStopUnconfirmed):
        with ModalAppBudgetGuard(binding,ModalRunDeadline(5),stop_app=calls.append,diagnostic_path=path):
            pass
    assert calls == []
    assert any('ID unavailable' in event.get('error','') for event in json.loads(path.read_text())['events'])


def test_success_always_stops_exact_owned_app_once(tmp_path):
    calls = []
    path = tmp_path/'guard.json'
    with ModalAppBudgetGuard(owned(), ModalRunDeadline(5), stop_app=calls.append, diagnostic_path=path) as guard:
        assert 0 < guard.remaining() <= 5
    assert calls == [owned()]
    evidence = json.loads(path.read_text())
    assert evidence['stop_acknowledged'] is True
    assert [row['reason'] for row in evidence['events'] if row['event']=='stop_requested']==['completed']


def test_body_exception_stops_app_and_preserves_original_error(tmp_path):
    calls = []
    with pytest.raises(ValueError, match='worker startup failed'):
        with ModalAppBudgetGuard(owned(), ModalRunDeadline(5), stop_app=calls.append,
                                 diagnostic_path=tmp_path/'guard.json'):
            raise ValueError('worker startup failed')
    assert calls == [owned()]


def test_watchdog_stops_while_main_thread_waits_without_polling(tmp_path):
    stopped = threading.Event()
    calls = []
    def stop(app):
        calls.append(app)
        stopped.set()
    with pytest.raises(guard_module.ModalDeadlineExceeded):
        with ModalAppBudgetGuard(owned(), ModalRunDeadline(.2), stop_app=stop,
                                 diagnostic_path=tmp_path/'guard.json'):
            assert stopped.wait(2), 'Independent watchdog did not stop App while main waited'
    assert calls == [owned()]
    events = json.loads((tmp_path/'guard.json').read_text())['events']
    assert next(row['reason'] for row in events if row['event']=='stop_requested')=='total_deadline'


def test_stop_error_is_retained_and_blocks_success(tmp_path):
    def failed_stop(app):
        raise ConnectionError('stop endpoint unavailable')
    path = tmp_path/'guard.json'
    with pytest.raises(guard_module.ModalStopUnconfirmed):
        with ModalAppBudgetGuard(owned(), ModalRunDeadline(5), stop_app=failed_stop, diagnostic_path=path):
            pass
    events = json.loads(path.read_text())['events']
    failure = next(row for row in events if row['event']=='stop_failed')
    assert failure['error_type']=='ConnectionError'
    assert failure['error']=='stop endpoint unavailable'


def test_hanging_stop_callback_has_bounded_wait(tmp_path):
    release = threading.Event()
    guard = ModalAppBudgetGuard(owned(), ModalRunDeadline(5), stop_app=lambda app:release.wait(2),
        diagnostic_path=tmp_path/'guard.json', stop_wait_seconds=.05)
    try:
        with pytest.raises(guard_module.ModalStopUnconfirmed):
            with guard:
                pass
    finally:
        release.set()
        assert guard._stop_done.wait(2)


def test_diagnostic_write_failure_still_stops_owned_app(tmp_path):
    blocked = tmp_path/'blocked'
    blocked.write_text('parent is a file')
    calls = []
    with pytest.raises(guard_module.ModalGuardDiagnosticError):
        with ModalAppBudgetGuard(owned(), ModalRunDeadline(5), stop_app=calls.append,
                                 diagnostic_path=blocked/'guard.json'):
            pytest.fail('Body should not run with unavailable guard diagnostics')
    assert calls == [owned()]


def test_guard_cannot_be_reused(tmp_path):
    calls = []
    guard = ModalAppBudgetGuard(owned(), ModalRunDeadline(5), stop_app=calls.append,
                               diagnostic_path=tmp_path/'guard.json')
    with guard:
        pass
    with pytest.raises(ValueError, match='single-use'):
        with guard:
            pass
    assert calls == [owned()]


def test_existing_diagnostic_is_preserved_and_owned_app_stopped(tmp_path):
    path = tmp_path/'guard.json'
    path.write_text('historical evidence')
    calls = []
    with pytest.raises(ValueError, match='existing diagnostic preserved'):
        with ModalAppBudgetGuard(owned(),ModalRunDeadline(5),stop_app=calls.append,diagnostic_path=path):
            pytest.fail('Guard body should not start')
    assert calls == [owned()]
    assert path.read_text()=='historical evidence'
    assert len(list(tmp_path.glob('guard.json.arm-error-*.json')))==1


def test_stop_cli_uses_exact_id_argv_and_bounded_subprocess(monkeypatch):
    calls = []
    monkeypatch.setattr(guard_module.subprocess, 'run', lambda args, **kwargs:calls.append((args,kwargs)))
    guard_module.stop_owned_app_cli(owned(), timeout_seconds=12)
    args, kwargs = calls[0]
    assert args == [sys.executable,'-B','-m','modal','app','stop','--yes','ap-UnitRun123']
    assert 0<kwargs['timeout']<=12 and kwargs['check'] is True
    assert kwargs.get('shell',False) is False


def test_stop_cli_timeout_is_reported_to_guard(tmp_path,monkeypatch):
    def expired(args, **kwargs):
        raise subprocess.TimeoutExpired(args, kwargs['timeout'])
    monkeypatch.setattr(guard_module.subprocess,'run',expired)
    with pytest.raises(guard_module.ModalStopUnconfirmed):
        with ModalAppBudgetGuard(owned(),ModalRunDeadline(5),stop_app=guard_module.stop_owned_app_cli,
                                 diagnostic_path=tmp_path/'guard.json'):
            pass


def test_stop_cli_accepts_already_stopped_only_after_owned_state_check(monkeypatch):
    calls = []
    now = [100.]
    monkeypatch.setattr(guard_module.time,'monotonic',lambda:now[0])
    def execute(args, **kwargs):
        calls.append((args,kwargs))
        if 'stop' in args:
            now[0] += 6
            raise subprocess.CalledProcessError(1,args,stderr='App is already stopped.')
        return subprocess.CompletedProcess(args,0,stdout=json.dumps([
            dict(app_id='ap-Unrelated',state='running',tasks='2'),
            dict(app_id=owned().app_id,state='stopped',tasks='0')]))
    monkeypatch.setattr(guard_module.subprocess,'run',execute)
    guard_module.stop_owned_app_cli(owned(),timeout_seconds=15)
    assert calls[1][0]==[sys.executable,'-B','-m','modal','app','list','--json']
    assert calls[0][1]['timeout']==15 and calls[1][1]['timeout']==9


@pytest.mark.parametrize('records',[
    [dict(app_id='ap-UnitRun123',state='running',tasks='0')],
    [dict(app_id='ap-Other',state='stopped',tasks='0')],
    [dict(app_id='ap-UnitRun123',state='stopped',tasks='1')],
])
def test_stop_cli_rejects_running_missing_or_busy_owned_app(monkeypatch,records):
    def execute(args, **kwargs):
        if 'stop' in args:
            raise subprocess.CalledProcessError(1,args,stderr='App is already stopped.')
        return subprocess.CompletedProcess(args,0,stdout=json.dumps(records))
    monkeypatch.setattr(guard_module.subprocess,'run',execute)
    with pytest.raises(RuntimeError,match='not independently confirmed'):
        guard_module.stop_owned_app_cli(owned())


def test_stop_cli_state_query_failure_remains_failure(monkeypatch):
    def execute(args, **kwargs):
        raise subprocess.CalledProcessError(1,args,stderr='query failed')
    monkeypatch.setattr(guard_module.subprocess,'run',execute)
    with pytest.raises(subprocess.CalledProcessError):
        guard_module.stop_owned_app_cli(owned())


def test_stop_cli_waits_for_bounded_state_propagation(monkeypatch):
    states = iter(['ephemeral', 'stopped'])
    queries = []
    monkeypatch.setattr(guard_module.time, 'sleep', lambda seconds: None)
    def execute(args, **kwargs):
        if 'stop' in args:
            raise subprocess.CalledProcessError(1, args)
        queries.append(args)
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps([
            dict(app_id=owned().app_id, state=next(states), tasks='0')]))
    monkeypatch.setattr(guard_module.subprocess, 'run', execute)
    guard_module.stop_owned_app_cli(owned())
    assert len(queries) == 2


def test_import_does_not_load_torch():
    program = """
import importlib.util,sys
spec=importlib.util.spec_from_file_location('modal_guard_fresh',sys.argv[1])
module=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=module
spec.loader.exec_module(module)
assert 'torch' not in sys.modules
"""
    subprocess.run([sys.executable,'-B','-c',program,str(ROOT/'experiments/akt/modal_budget_guard.py')],
                   check=True,timeout=15,capture_output=True,text=True)
