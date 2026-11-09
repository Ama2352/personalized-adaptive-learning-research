"""Root launcher cấp child profile cho từng operation hữu hạn của A1 expert."""
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
APPROVAL = 'ROOT_A1_EXPERT_OPERATIONAL_RETRY03_REVIEW'
PINS = {
    'prepare_a1_expert_engineering_package01.py': '31e1f5fb2884a6e2bf6554c25c80fa03dc4af705e7969e3de8b957a9ca44b736',
    'run_prepare_a1_expert_engineering_package01.py': 'fe3f762d1bb0e371152587369cc4bfe8dce0d3e512b1287495b9dece9bc94195',
    'check_a1_expert_engineering03.py': 'a6fa2e3838d27e288ad1be8ecb33058ef3f7062c0258b4d8b3fb6c765038cc42',
    'run_a1_expert_engineering03.py': '126ad0a9c14ab5c5cd6de6d78bd59efc62a5e4aafb68599f408bf687c74c442c',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main(args):
    started = time.perf_counter()
    assert Path(sys.prefix).resolve() == ROOT / '.venv'
    assert (PREP / (APPROVAL + '.md')).is_file()
    assert all(sha(PREP / name) == pin for name, pin in PINS.items())
    parent = dict(os.environ)
    expected = dict(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='nul', GIT_CONFIG_COUNT='3',
        GIT_CONFIG_KEY_0='core.fsmonitor', GIT_CONFIG_VALUE_0='false', GIT_CONFIG_KEY_1='safe.directory',
        GIT_CONFIG_VALUE_1=(ROOT / 'artifacts/akt/dependencies/upstream').as_posix(),
        GIT_CONFIG_KEY_2='core.autocrlf', GIT_CONFIG_VALUE_2='true', GIT_OPTIONAL_LOCKS='0',
        GIT_TERMINAL_PROMPT='0', GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__')
    inherited = {k: v for k, v in parent.items() if k.startswith(('GIT_', 'GH_'))}
    display = {'GH_PAGER', 'GIT_PAGER'}
    assert all(key in display or key in expected and value == expected[key] for key, value in inherited.items())
    environment = dict(parent)
    for key in display:
        environment.pop(key, None)
    environment.update(expected)
    assert {k: v for k, v in environment.items() if k.startswith(('GIT_', 'GH_'))} == expected
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-B']
    if args.mode == 'fit':
        request = PREP / 'a1_expert_engineering03_request.ROOT.json'
        assert args.request_sha256 and sha(request) == args.request_sha256
        assert (PREP / 'ROOT_A1_EXPERT_OPERATIONAL_RETRY03_ACTUAL_FIT_REVIEW.md').is_file()
        command += [str(PREP / 'run_a1_expert_engineering03.py'), '--request', request.relative_to(ROOT).as_posix(),
                    '--request-sha256', args.request_sha256, '--worker-sha256', PINS['check_a1_expert_engineering03.py'],
                    '--outer-sha256', PINS['run_a1_expert_engineering03.py'], '--approval-reference', APPROVAL]
    else:
        command += [str(PREP / 'run_prepare_a1_expert_engineering_package01.py'),
                    '--worker-sha256', PINS['prepare_a1_expert_engineering_package01.py'],
                    '--outer-sha256', PINS['run_prepare_a1_expert_engineering_package01.py'], '--approval-reference', APPROVAL,
                    '--prepare-dry' if args.mode == 'prepare' else '--materialize']
        if args.mode == 'materialize':
            assert args.dry_sha256 and (PREP / 'ROOT_A1_EXPERT_ENGINEERING_DRY_REVIEW01.md').is_file()
            command += ['--expected-dry-sha256', args.dry_sha256, '--review-reference', 'ROOT_A1_EXPERT_ENGINEERING_DRY_REVIEW01']
    output = PREP / ('a1-expert-engineering-profile-' + args.mode + '03')
    output.mkdir(exist_ok=False)
    timeout = 630 if args.mode == 'fit' else 65
    write(output / 'reservation.json', dict(command=command, child_git_profile=expected,
          excluded_display_variable_names=sorted(set(inherited) & display), timeout_seconds=timeout))
    result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, timeout=timeout)
    for name, raw in (('stdout.log', result.stdout), ('stderr.log', result.stderr)):
        assert len(raw) <= 131072
        with (output / name).open('xb') as stream:
            stream.write(raw)
    record = dict(returncode=result.returncode, elapsed_seconds=time.perf_counter() - started,
                  parent_environment_unchanged=dict(os.environ) == parent,
                  stdout_sha256=sha(output / 'stdout.log'), stderr_sha256=sha(output / 'stderr.log'))
    write(output / 'result.json', record)
    print(json.dumps(record))
    raise SystemExit(result.returncode if record['parent_environment_unchanged'] else 1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('prepare', 'materialize', 'fit'), required=True)
    parser.add_argument('--dry-sha256')
    parser.add_argument('--request-sha256')
    main(parser.parse_args())
