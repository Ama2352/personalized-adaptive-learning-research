"""Chạy bounded collector với exact child Git profile, parent giữ nguyên."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    started = time.perf_counter()
    assert Path(sys.prefix).resolve() == ROOT / '.venv'
    worker = PREP / 'collect_main_engineering10x84_01.py'
    outer = PREP / 'run_main_engineering10x84_01.py'
    request = PREP / 'main_engineering10x84_request01.ROOT.json'
    worker_sha = '121386eef563fb88ac04e7c66849f169cf8de548fffaaee8c38be6c86f045e77'
    outer_sha = 'a728ac14a6be6c42efb8123a6f368d8ebd51436c3b40656e474097c13450abab'
    request_sha = 'b99e6825b2b0c03316b6e4c167c682f820432c3b01a611c2199270e848eabe60'
    assert sha(worker) == worker_sha and sha(outer) == outer_sha and sha(request) == request_sha
    expected = json.loads((PREP / 'runtime_schema2_main177_01_packet.json').read_bytes())['git_environment']
    parent = dict(os.environ)
    inherited = {k: v for k, v in parent.items() if k.startswith(('GIT_', 'GH_'))}
    display = {'GIT_PAGER', 'GH_PAGER'}
    assert not set(inherited) - set(expected) - display
    environment = dict(parent)
    for name in display:
        environment.pop(name, None)
    environment.update(expected)
    assert {k: v for k, v in environment.items() if k.startswith(('GIT_', 'GH_'))} == expected
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-B', str(outer),
               '--request', request.relative_to(ROOT).as_posix(), '--request-sha256', request_sha,
               '--worker-sha256', worker_sha, '--outer-sha256', outer_sha,
               '--approval-reference', 'ROOT_ENGINEERING10X84_COLLECTION_REVIEW01']
    out = PREP / 'engineering10x84-profile-launch01'
    out.mkdir(exist_ok=False)
    write(out / 'reservation.json', dict(command=command, child_git_profile=expected,
          excluded_display_variable_names=sorted(set(inherited) & display), timeout_seconds=75))
    result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, timeout=75)
    for name, raw in (('stdout.log', result.stdout), ('stderr.log', result.stderr)):
        assert len(raw) <= 131072
        with (out / name).open('xb') as stream:
            stream.write(raw)
    record = dict(returncode=result.returncode, elapsed_seconds=time.perf_counter() - started,
                  parent_environment_unchanged=dict(os.environ) == parent,
                  stdout_sha256=sha(out / 'stdout.log'), stderr_sha256=sha(out / 'stderr.log'))
    write(out / 'result.json', record)
    print(json.dumps(record))
    raise SystemExit(result.returncode if record['parent_environment_unchanged'] else 1)


if __name__ == '__main__':
    main()
