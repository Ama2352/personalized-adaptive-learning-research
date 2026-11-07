import os
import subprocess
import sys
from dataclasses import replace
import json

from knowledge_tracing.akt.config import PROJECT_ROOT


def _python(code: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join(('src', 'third_party'))
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    return subprocess.run([sys.executable, '-B', '-c', code], cwd=PROJECT_ROOT,
                          env=env, capture_output=True, text=True, check=False)


def test_parent_cli_import_does_not_load_heavy_runtime_modules():
    result = _python("""
import sys
import knowledge_tracing.akt.cli
heavy = {'torch', 'duckdb', 'knowledge_tracing.akt.runner', 'knowledge_tracing.akt.model'}
loaded = heavy.intersection(sys.modules)
assert not loaded, f'eager runtime imports: {sorted(loaded)}'
""")
    assert result.returncode == 0, result.stderr


def test_parent_watchdog_requires_authorization_before_spawning(monkeypatch):
    import pytest
    from knowledge_tracing.akt import watchdog

    def must_not_spawn(*args, **kwargs):
        pytest.fail('worker was spawned without authorization')

    monkeypatch.setattr(watchdog.subprocess, 'run', must_not_spawn)
    with pytest.raises(PermissionError, match='authorization'):
        watchdog.main(['smoke', '--config', 'experiments/akt/configs/smoke.json'])


def test_direct_worker_entry_still_requires_authorization():
    result = _python("""
from pathlib import Path
from knowledge_tracing.akt.watchdog import main
config = Path('experiments/akt/configs/smoke.json')
try:
    main(['_execute', 'smoke', '--config', str(config)])
except PermissionError as exc:
    assert 'authorization' in str(exc)
else:
    raise AssertionError('direct worker execution bypassed authorization')
""")
    assert result.returncode == 0, result.stderr


def test_watchdog_refuses_worker_spawn_when_parent_sees_ram_below_floor(tmp_path, monkeypatch):
    import pytest
    from knowledge_tracing.akt import watchdog
    from knowledge_tracing.akt.config import load_config

    config = replace(load_config(PROJECT_ROOT / 'experiments/akt/configs/smoke.json'),
                     execution_enabled=True)
    authorization = {'caps': {'max_wall_seconds': 300,
                              'max_rss_bytes': config.max_rss_bytes,
                              'min_available_ram_bytes': config.min_available_ram_bytes}}
    path = tmp_path / 'synthetic-authorization.json'
    path.write_text(json.dumps(authorization), encoding='utf-8')
    monkeypatch.setattr(watchdog, 'load_config', lambda _: config)
    monkeypatch.setattr(watchdog, 'require_authorization', lambda *args: authorization)
    monkeypatch.setattr(watchdog, 'memory_snapshot', lambda: {
        'pid': 765, 'process_rss_bytes': 123, 'process_peak_rss_bytes': 123,
        'system_available_ram_bytes': config.min_available_ram_bytes - 1,
        'system_total_ram_bytes': 10_000})
    monkeypatch.setattr(watchdog.subprocess, 'Popen',
                        lambda *args, **kwargs: pytest.fail('low-RAM worker must not be spawned'))
    with pytest.raises(MemoryError, match='watchdog.*available-RAM') as error:
        watchdog.main(['smoke', '--config', 'synthetic.json', '--authorization', str(path)])
    assert 'system_available_ram_bytes=1073741823' in str(error.value)
    assert 'min_available_ram_bytes=1073741824' in str(error.value)


def test_watchdog_persists_parent_rss_and_system_ram_snapshots(tmp_path, monkeypatch):
    from knowledge_tracing.akt import watchdog
    from knowledge_tracing.akt.config import load_config

    config = replace(load_config(PROJECT_ROOT / 'experiments/akt/configs/pilot.json'),
                     project_root=tmp_path,
                     run_id='pilot-watchdog-telemetry',
                     output_dir=tmp_path / 'experiments/akt/results/pilot-watchdog-telemetry')
    caps = {'max_train_users': 1024, 'max_val_users': 256, 'max_total_targets': 100000,
            'max_seconds': 900, 'max_wall_seconds': 1200,
            'max_rss_bytes': 2 * 1024**3, 'min_available_ram_bytes': 1024**3}
    approval = {'caps': caps}
    path = tmp_path / 'authorization.json'
    path.write_text(json.dumps(approval), encoding='utf-8')
    monkeypatch.setattr(watchdog, 'load_config', lambda _: config)
    monkeypatch.setattr(watchdog, 'require_authorization', lambda *args: approval)
    snapshots = iter([
        {'pid': 11, 'process_rss_bytes': 100, 'process_peak_rss_bytes': 110,
         'system_available_ram_bytes': 2_000_000_000, 'system_total_ram_bytes': 4_000_000_000},
        {'pid': 11, 'process_rss_bytes': 120, 'process_peak_rss_bytes': 130,
         'system_available_ram_bytes': 1_900_000_000, 'system_total_ram_bytes': 4_000_000_000},
        {'pid': 11, 'process_rss_bytes': 115, 'process_peak_rss_bytes': 130,
         'system_available_ram_bytes': 1_950_000_000, 'system_total_ram_bytes': 4_000_000_000},
    ])
    monkeypatch.setattr(watchdog, 'memory_snapshot', lambda: next(snapshots))

    class CompletedWorker:
        pid = 22
        def communicate(self, timeout=None):
            return ('worker output', '')
        def wait(self):
            return 0

    def spawn(*args, **kwargs):
        config.output_dir.mkdir(parents=True)
        (config.output_dir / 'manifest.json').write_text('{"status":"completed"}', encoding='utf-8')
        return CompletedWorker()
    monkeypatch.setattr(watchdog.subprocess, 'Popen', spawn)

    assert watchdog.main(['pilot', '--config', 'unused.json', '--authorization', str(path)]) == 0

    report = json.loads((config.output_dir / 'watchdog-resources.json').read_text(encoding='utf-8'))
    assert report['status'] == 'completed'
    assert report['worker_pid'] == 22
    assert [event['event'] for event in report['parent_events']] == [
        'watchdog-before-worker-spawn', 'watchdog-after-worker-spawn', 'watchdog-after-worker-exit']
    assert [event['process_rss_bytes'] for event in report['parent_events']] == [100, 120, 115]
    assert [event['system_available_ram_bytes'] for event in report['parent_events']] == [
        2_000_000_000, 1_900_000_000, 1_950_000_000]
