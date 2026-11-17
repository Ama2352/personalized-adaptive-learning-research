import ast
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest


DRIVER = Path(__file__).resolve().parents[2] / 'research_tracking/runs/junyi-calibration-real-20261117-01/run_colab_a3_cpu03.py'
SIGNALS = SimpleNamespace(SIGTERM=15, SIGKILL=9)


def test_driver_uses_staging02_source_and_payload_pins():
    tree = ast.parse(DRIVER.read_text(encoding='utf-8'))
    constants = {node.targets[0].id: ast.literal_eval(node.value)
        for node in tree.body if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Constant)}
    staged = json.loads((DRIVER.parent/'COLAB_CPU_STAGING02.json').read_text(encoding='utf-8'))
    assert constants['RUNNER_SHA'] == staged['files'][0]['sha256']
    assert constants['PAYLOAD_SHA'] == staged['files'][1]['sha256']
    text = DRIVER.read_text(encoding='utf-8')
    assert all(pin['remote'] in text for pin in staged['files'])


def load_main(tmp_path, mode, missing_group=False):
    tree = ast.parse(DRIVER.read_text(encoding='utf-8'))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    events = []
    access = tmp_path / 'private/access.json'
    access.parent.mkdir()
    access.write_text('temporary-access')
    runner, payload = tmp_path / 'runner.py', tmp_path / 'payload.json'
    runner.write_text('runner')
    payload.write_text('payload')
    process = SimpleNamespace(pid=314159, returncode=7 if mode == 'nonzero' else 0)

    def wait(timeout=None):
        events.append(('wait', timeout))
        if mode == 'timeout' and timeout == 10800:
            raise subprocess.TimeoutExpired(['trusted-runner'], timeout)
        return process.returncode

    def popen(command, **kwargs):
        events.append(('popen', command, kwargs))
        if mode == 'popen_fail':
            raise OSError('synthetic launch failure')
        return process

    def killpg(pid, sig):
        assert pid == process.pid
        events.append(('killpg', pid, sig))
        if missing_group:
            raise ProcessLookupError()

    process.wait = wait
    namespace = dict(ACCESS=access, LOG=tmp_path/'output.log', RUNNER=runner, PAYLOAD=payload,
        RUNNER_SHA='pinned', PAYLOAD_SHA='pinned',
        hashlib=SimpleNamespace(sha256=lambda data: SimpleNamespace(hexdigest=lambda: 'pinned')),
        subprocess=SimpleNamespace(Popen=popen, STDOUT=subprocess.STDOUT,
            TimeoutExpired=subprocess.TimeoutExpired, CalledProcessError=subprocess.CalledProcessError),
        os=SimpleNamespace(killpg=killpg), signal=SIGNALS,
        time=SimpleNamespace(sleep=lambda seconds: events.append(('sleep', seconds))))
    from contextlib import suppress
    namespace['suppress'] = suppress
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(DRIVER), 'exec'), namespace)
    return namespace['main'], access, events


@pytest.mark.parametrize('mode', ['normal', 'nonzero', 'timeout', 'popen_fail'])
@pytest.mark.parametrize('missing_group', [False, True])
def test_own_process_group_and_token_cleanup(tmp_path, mode, missing_group):
    main, access, events = load_main(tmp_path, mode, missing_group)
    expected = dict(nonzero=subprocess.CalledProcessError, timeout=subprocess.TimeoutExpired,
                    popen_fail=OSError).get(mode)
    if expected:
        with pytest.raises(expected):
            main()
    else:
        main()
    assert not access.exists()
    popen = next(event for event in events if event[0] == 'popen')
    assert popen[2]['start_new_session'] is True
    assert popen[1][-2:] == ['--variant', 'A3']
    kills = [event for event in events if event[0] == 'killpg']
    if mode == 'timeout':
        assert kills == [('killpg', 314159, SIGNALS.SIGTERM), ('killpg', 314159, SIGNALS.SIGKILL)]
        assert events.index(('killpg', 314159, SIGNALS.SIGTERM)) < events.index(('sleep', 2)) < events.index(('killpg', 314159, SIGNALS.SIGKILL))
        assert events[-1] == ('wait', None)
    else:
        assert not kills
