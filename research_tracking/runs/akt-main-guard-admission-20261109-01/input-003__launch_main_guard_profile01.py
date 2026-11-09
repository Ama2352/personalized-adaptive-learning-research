"""Cấp exact Win03 cho child của ba bước guard, không đổi parent environment."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
BUILDER = PREP / 'prepare_main_selected_guard_package01.py'
OUTER = PREP / 'run_prepare_main_selected_guard_package01.py'
GUARD = PREP / 'run_main_selected_guard01.py'
REQUEST = PREP / 'main_selected_actual_guard01_request.ROOT.json'
BUILDER_SHA = 'f1ca0b7f04f021e0e8a57f5c43ca806e1cd6aa94e2c127858ef076a51934d7fb'
OUTER_SHA = 'f49b3741c652726aaf45636694f497231612d0d4a9aedee6d31c34793b4f1235'
GUARD_SHA = '2bcd5d2699fee3e7e209e113e08ad4a6606a791fb5aed2599352553e891b5440'
APPROVAL = 'ROOT_MAIN_A0_GUARD_PACKAGE_REVIEW01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def main(args):
    started = time.perf_counter()
    if Path(sys.prefix).resolve() != ROOT / '.venv':
        raise ValueError('repository .venv only')
    if sha(BUILDER) != BUILDER_SHA or sha(OUTER) != OUTER_SHA or sha(GUARD) != GUARD_SHA:
        raise ValueError('reviewed source drift')
    expected_git = dict(
        GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='nul', GIT_CONFIG_COUNT='3',
        GIT_CONFIG_KEY_0='core.fsmonitor', GIT_CONFIG_VALUE_0='false',
        GIT_CONFIG_KEY_1='safe.directory', GIT_CONFIG_VALUE_1=(ROOT / 'artifacts/akt/dependencies/upstream').as_posix(),
        GIT_CONFIG_KEY_2='core.autocrlf', GIT_CONFIG_VALUE_2='true', GIT_OPTIONAL_LOCKS='0',
        GIT_TERMINAL_PROMPT='0', GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__')
    parent_before = dict(os.environ)
    inherited_git = {key: value for key, value in parent_before.items() if key.startswith(('GIT_', 'GH_'))}
    display = {'GH_PAGER', 'GIT_PAGER'}
    if set(inherited_git) - set(expected_git) - display:
        raise ValueError('unreviewed Git environment names')
    environment = dict(parent_before)
    excluded = sorted(set(inherited_git) & display)
    for key in display:
        environment.pop(key, None)
    environment.update(expected_git)
    if {key: value for key, value in environment.items() if key.startswith(('GIT_', 'GH_'))} != expected_git:
        raise ValueError('exact child Git profile required')
    environment.update(PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void')
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-B']
    if args.mode == 'guard':
        if not args.request_sha256 or sha(REQUEST) != args.request_sha256:
            raise ValueError('Root reviewed actual request SHA required')
        command += [str(GUARD), '--request', REQUEST.relative_to(ROOT).as_posix(),
                    '--request-sha256', args.request_sha256, '--approval-reference', APPROVAL]
    else:
        command += [str(OUTER), '--worker-sha256', BUILDER_SHA, '--outer-sha256', OUTER_SHA,
                    '--approval-reference', APPROVAL]
        if args.mode == 'prepare':
            command += ['--prepare-dry']
        else:
            if not args.dry_sha256:
                raise ValueError('Root exact dry review SHA required')
            command += ['--materialize', '--expected-dry-sha256', args.dry_sha256,
                        '--review-reference', 'ROOT_MAIN_A0_GUARD_EXACT_DRY_REVIEW01']
    output = PREP / ('main-guard-profile-' + args.mode + '01')
    output.mkdir(exist_ok=False)
    write(output / 'reservation.json', dict(command=command, child_git_environment=expected_git,
          excluded_inherited_display_variable_names=excluded, source_pins={
              BUILDER.name: BUILDER_SHA, OUTER.name: OUTER_SHA, GUARD.name: GUARD_SHA},
          timeout_seconds=65, mode=args.mode,
          scope_vi='Chỉ cấu hình child cho operation guard hữu hạn. Parent environment giữ nguyên.'))
    result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, timeout=65, check=False)
    for name, content in (('stdout.log', result.stdout), ('stderr.log', result.stderr)):
        if len(content) > 131072:
            raise ValueError('profile launcher output cap exceeded')
        with (output / name).open('xb') as stream:
            stream.write(content)
    record = dict(returncode=result.returncode, elapsed_seconds=time.perf_counter() - started,
                  parent_environment_unchanged=dict(os.environ) == parent_before,
                  excluded_inherited_display_variable_names=excluded,
                  stdout_sha256=sha(output / 'stdout.log'), stderr_sha256=sha(output / 'stderr.log'))
    write(output / 'result.json', record)
    print(json.dumps(record))
    raise SystemExit(result.returncode if record['parent_environment_unchanged'] else 1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('prepare', 'materialize', 'guard'), required=True)
    parser.add_argument('--dry-sha256')
    parser.add_argument('--request-sha256')
    main(parser.parse_args())
