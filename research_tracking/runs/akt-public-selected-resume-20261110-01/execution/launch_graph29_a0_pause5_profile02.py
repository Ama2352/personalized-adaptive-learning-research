"""Root launcher cấp child profile cho từng operation hữu hạn của tiny A0."""
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
APPROVAL = 'ROOT_GRAPH29_A0_PAUSE5_REVIEW01'
PINS = {
    'prepare_graph29_a0_pause5_package01.py': '1ac1860a219519f466d54e55b084166e933b67a9958affcdd1fce38416d4e72c',
    'run_prepare_graph29_a0_pause5_package01.py': '947a562d36486ea379f45058c891039d157d9a7dd5d1cfee4fa814a919524349',
    'check_graph29_a0_pause5_01.py': '11e64f74fdc9da73a04aad44389b4db99ed4639ac877a79e12b2560957576a68',
    'run_graph29_a0_pause5_01.py': 'd18c3602ceb0083d08b448c8c11b89ad361825d64fc53c67a03a68a92f9da904',
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
        request = PREP / 'graph29_a0_pause5_01_request.ROOT.json'
        assert args.request_sha256 and sha(request) == args.request_sha256
        assert (PREP / 'ROOT_GRAPH29_A0_PAUSE5_ACTUAL_FIT_REVIEW01.md').is_file()
        command += [str(PREP / 'run_graph29_a0_pause5_01.py'), '--request', request.relative_to(ROOT).as_posix(),
                    '--request-sha256', args.request_sha256, '--worker-sha256', PINS['check_graph29_a0_pause5_01.py'],
                    '--outer-sha256', PINS['run_graph29_a0_pause5_01.py'], '--approval-reference', APPROVAL]
    else:
        command += [str(PREP / 'run_prepare_graph29_a0_pause5_package01.py'),
                    '--worker-sha256', PINS['prepare_graph29_a0_pause5_package01.py'],
                    '--outer-sha256', PINS['run_prepare_graph29_a0_pause5_package01.py'], '--approval-reference', APPROVAL,
                    '--prepare-dry' if args.mode == 'prepare' else '--materialize']
        if args.mode == 'materialize':
            assert args.dry_sha256 and (PREP / 'ROOT_GRAPH29_A0_PAUSE5_DRY_REVIEW01.md').is_file()
            command += ['--expected-dry-sha256', args.dry_sha256, '--review-reference', 'ROOT_GRAPH29_A0_PAUSE5_DRY_REVIEW01']
    if args.mode == 'fit':
        shim = "import sys,runpy;sys.path.insert(0,sys.argv.pop(1));p=sys.argv[1];sys.argv=sys.argv[1:];runpy.run_path(p,run_name='__main__')"
        command = command[:2] + ['-c', shim, str(ROOT / 'src')] + command[2:]
    output = PREP / ('graph29-a0-pause5-profile-' + args.mode + '02')
    output.mkdir(exist_ok=False)
    timeout = 200 if args.mode == 'fit' else 65
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
