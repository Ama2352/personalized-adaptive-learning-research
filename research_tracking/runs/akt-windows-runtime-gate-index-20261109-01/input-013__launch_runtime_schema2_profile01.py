"""Chạy đúng runtime audit với child Git profile đã review và lưu raw logs."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PACKET = PREP / 'runtime_schema2_main177_01_packet.json'
OUTER = PREP / 'run_runtime_schema2_main177_01.py'
OUTPUT = PREP / 'runtime-schema2-profile-launch01'
PACKET_SHA256 = 'e4d97a562f4140bfe7b3dbba8bdefda4746ef93d718b6586fc995ac6a31206a9'
OUTER_SHA256 = '03e30c27cd3828861c64daa7463fac7387d235f634f1a8226a803a1f7a745362'
WORKER_SHA256 = '5e931079a709e9ba0cbc0c2677659a21283f9c37c175d4a7467f1b1c776534f2'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def main():
    started = time.perf_counter()
    if Path(sys.prefix).resolve() != ROOT / '.venv':
        raise ValueError('repository .venv required')
    if digest(PACKET) != PACKET_SHA256 or digest(OUTER) != OUTER_SHA256:
        raise ValueError('reviewed source changed')
    allocation = json.loads(PACKET.read_bytes())
    expected_git = allocation['git_environment']
    parent_before = dict(os.environ)
    inherited_git = {name: value for name, value in parent_before.items()
                     if name.startswith(('GIT_', 'GH_'))}
    reviewed_display_names = {'GIT_PAGER', 'GH_PAGER'}
    extra_names = set(inherited_git) - set(expected_git)
    if not extra_names <= reviewed_display_names:
        raise ValueError('unreviewed Git environment variable names')
    child_environment = dict(parent_before)
    for name in reviewed_display_names:
        child_environment.pop(name, None)
    child_environment.update(expected_git)
    child_git = {name: value for name, value in child_environment.items()
                 if name.startswith(('GIT_', 'GH_'))}
    if child_git != expected_git:
        raise ValueError('child profile must match reviewed Win03 exactly')
    OUTPUT.mkdir(exist_ok=False)
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-B', str(OUTER),
               '--worker-sha256', WORKER_SHA256, '--controller-sha256', OUTER_SHA256,
               '--approval-reference', str(PREP / 'ROOT_RUNTIME_SCHEMA2_REVIEW01.md')]
    write_json(OUTPUT / 'reservation.json', dict(
        command=command, packet_sha256=PACKET_SHA256,
        child_git_environment=child_git,
        excluded_inherited_display_variable_names=sorted(extra_names),
        outer_timeout_seconds=65,
        scope_vi='Child dùng Win03 profile đã review, parent giữ nguyên môi trường.'))
    result = subprocess.run(command, cwd=ROOT, env=child_environment,
                            capture_output=True, timeout=65, check=False)
    for name, raw in (('stdout.log', result.stdout), ('stderr.log', result.stderr)):
        if len(raw) > 131072:
            raise ValueError('bounded runtime audit stream exceeded')
        with (OUTPUT / name).open('xb') as stream:
            stream.write(raw)
    unchanged = dict(os.environ) == parent_before
    record = dict(returncode=result.returncode,
                  elapsed_seconds=time.perf_counter() - started,
                  parent_environment_unchanged=unchanged,
                  excluded_inherited_display_variable_names=sorted(extra_names),
                  stdout_sha256=digest(OUTPUT / 'stdout.log'),
                  stderr_sha256=digest(OUTPUT / 'stderr.log'))
    write_json(OUTPUT / 'result.json', record)
    print(json.dumps(record, ensure_ascii=False))
    raise SystemExit(result.returncode if unchanged else 1)

if __name__ == '__main__':
    main()
