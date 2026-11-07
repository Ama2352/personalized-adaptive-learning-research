"""Low-import CLI and timeout boundary for bounded AKT worker processes."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from .authorization import preflight, require_authorization
from .config import load_config
from .resources import memory_snapshot
from .recovery import validate_source, publish_envelope


def _emit_memory_event(event: str, phase: str, run_id: str, *, snapshot: dict | None = None,
                      **extra) -> dict:
    payload = {'event': event, 'phase': phase, 'run_id': run_id,
               **(snapshot or memory_snapshot()), **extra}
    print(json.dumps(payload, sort_keys=True), file=sys.stderr, flush=True)
    return payload


def _write_captured(payload: str | bytes | None, stream) -> None:
    if not payload:
        return
    if isinstance(payload, bytes):
        payload = payload.decode(errors='replace')
    stream.write(payload)
    if not payload.endswith('\n'):
        stream.write('\n')


def _persist_parent_resources(config, events: list[dict], *, status: str,
                               worker_pid: int | None, elapsed_seconds: float,
                               worker_returncode: int | None = None,
                               stop_reason: str | None = None) -> None:
    output = config.output_dir.resolve()
    expected_parent = (config.project_root.resolve() / 'experiments/akt/results').resolve()
    if output.parent != expected_parent or output.name != config.run_id:
        raise ValueError('unsafe parent resource report path')
    if not output.is_dir():
        return
    path = output / 'watchdog-resources.json'
    temp = path.with_name(path.name + '.tmp')
    payload = {'schema_version': 1, 'run_id': config.run_id, 'phase': config.phase,
               'status': status, 'worker_pid': worker_pid,
               'worker_returncode': worker_returncode,
               'elapsed_seconds': elapsed_seconds, 'stop_reason': stop_reason,
               'parent_events': events,
               'measurement_scope': {'parent_rss_bytes': 'watchdog process-local RSS',
                                     'system_available_ram_bytes': 'system-wide'}}
    with temp.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(payload, stream, sort_keys=True, separators=(',', ':'))
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='AKT Development-only guarded commands')
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('preflight', 'smoke', 'pilot', 'fold-readiness'):
        command = commands.add_parser(name)
        command.add_argument('--config', required=True, type=Path)
        if name in {'smoke', 'pilot'}:
            command.add_argument('--authorization', type=Path)
        if name == 'fold-readiness':
            command.add_argument('--pilot-result', required=True, type=Path)
    return parser


def _worker_args(argv: list[str]) -> tuple[str, Path, Path | None]:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('phase', choices=('smoke', 'pilot'))
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--authorization', type=Path)
    args = parser.parse_args(argv)
    return args.phase, args.config, args.authorization


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == '_execute':
        phase, config_path, _authorization_path = _worker_args(argv[1:])
        config = load_config(config_path)
        _emit_memory_event('worker-before-runtime-import', phase, config.run_id)
        from .runner import _worker_main
        return _worker_main(argv[1:])

    args = _parser().parse_args(argv)
    config = load_config(args.config)
    if args.command == 'preflight':
        print(json.dumps(preflight(config), indent=2, default=str))
        return 0
    if args.command == 'fold-readiness':
        from .runner import prepare_fold_readiness
        result = prepare_fold_readiness(config, pilot_result=args.pilot_result)
        config.output_dir.mkdir(parents=True, exist_ok=True)
        from .runner import _write_json
        _write_json(config.output_dir / 'readiness.json', result)
        print(json.dumps(result, indent=2))
        return 0

    authorization = None
    if args.authorization is not None:
        authorization = json.loads(args.authorization.read_text(encoding='utf-8'))
    require_authorization(config, authorization)
    approved_caps = authorization['caps']
    timeout = approved_caps['max_wall_seconds']
    if timeout is None:
        raise ValueError('smoke/pilot configuration must include a wall-clock cap')
    source = (validate_source(config, current_identity=authorization['identity'], caps=approved_caps)
              if config.recovery is not None else None)
    if source is not None:
        timeout -= source['cumulative_wall_seconds']

    parent_events: list[dict] = []

    def emit(event: str, *, snapshot: dict | None = None, **extra) -> dict:
        payload = _emit_memory_event(event, config.phase, config.run_id,
                                     snapshot=snapshot, **extra)
        parent_events.append(payload)
        return payload

    parent_snapshot = memory_snapshot()
    emit('watchdog-before-worker-spawn', snapshot=parent_snapshot,
         max_rss_bytes=approved_caps['max_rss_bytes'],
         min_available_ram_bytes=approved_caps['min_available_ram_bytes'])
    floor = approved_caps['min_available_ram_bytes']
    if floor is not None and parent_snapshot['system_available_ram_bytes'] < floor:
        raise MemoryError(
            'AKT watchdog refused worker spawn: available-RAM floor violated: '
            f"phase={config.phase}, run_id={config.run_id}, pid={parent_snapshot['pid']}, "
            f"parent_rss_bytes={parent_snapshot['process_rss_bytes']}, "
            f"parent_peak_rss_bytes={parent_snapshot['process_peak_rss_bytes']}, "
            f"system_available_ram_bytes={parent_snapshot['system_available_ram_bytes']}, "
            f"system_total_ram_bytes={parent_snapshot['system_total_ram_bytes']}, "
            f"max_rss_bytes={approved_caps['max_rss_bytes']}, min_available_ram_bytes={floor}")
    worker = [sys.executable, '-m', 'knowledge_tracing.akt.cli', '_execute', args.command,
              '--config', str(args.config.resolve())]
    if args.authorization is not None:
        worker.extend(['--authorization', str(args.authorization.resolve())])
    started = time.perf_counter()
    process = subprocess.Popen(worker, cwd=config.project_root, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True)
    emit('watchdog-after-worker-spawn', worker_pid=process.pid,
         max_rss_bytes=approved_caps['max_rss_bytes'], min_available_ram_bytes=floor)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        if process.poll() is None:
            process.kill()
        stdout, stderr = process.communicate()
        _write_captured(stdout, sys.stdout)
        _write_captured(stderr, sys.stderr)
        elapsed = time.perf_counter() - started
        emit('watchdog-timeout', elapsed_seconds=elapsed, timeout_seconds=timeout,
             worker_pid=process.pid)
        _persist_parent_resources(config, parent_events, status='incomplete',
                                  worker_pid=process.pid, elapsed_seconds=elapsed,
                                  stop_reason='watchdog_timeout')
        publish_envelope(config, authorization=authorization, elapsed_seconds=elapsed)
        raise TimeoutError('smoke/pilot watchdog stopped the child before a complete result') from exc
    returncode = process.wait()
    elapsed = time.perf_counter() - started
    emit('watchdog-after-worker-exit', elapsed_seconds=elapsed,
         worker_returncode=returncode, worker_pid=process.pid)
    status = 'failed' if returncode else 'completed'
    if returncode == 0:
        manifest_path = config.output_dir / 'manifest.json'
        if manifest_path.is_file():
            manifest_status = json.loads(manifest_path.read_text(encoding='utf-8')).get('status')
            if manifest_status in {'completed', 'bounded'}:
                status = manifest_status
    _persist_parent_resources(config, parent_events, status=status,
                              worker_pid=process.pid, elapsed_seconds=elapsed,
                              worker_returncode=returncode,
                              stop_reason=None if returncode == 0 else 'worker_exit_nonzero')
    if status != 'completed':
        publish_envelope(config, authorization=authorization, elapsed_seconds=elapsed)
    _write_captured(stdout, sys.stdout)
    _write_captured(stderr, sys.stderr)
    if returncode:
        raise RuntimeError(f'AKT child process failed with exit code {returncode}')
    return 0
