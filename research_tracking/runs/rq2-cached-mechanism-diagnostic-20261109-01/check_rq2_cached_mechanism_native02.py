"""Owned bootstrap cho actual main của parser CPU09 đã freeze."""

import argparse
import codecs
import csv
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback
import types

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PARSER = PREP / 'analyze_rq2_cached_mechanism01.py'
CONTRACT = PREP / 'rq2_cache_mechanism_contract01.json'
PARSER_SHA = '8590381c85fe1e58df4a305c8bf4a33ebd9900d0fa8ffb1f1a93868fb56f1311'
CONTRACT_SHA = '23c182f6f03d4f31e694920bd11b6cd697cc1a66a16b5b31d4c46150c9e24fa4'
HELPER_SHA = '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'
INNER = PREP / 'rq2-cache-mechanism-attempt01'
OWNED = PREP / 'rq2-cached-mechanism-native02-owned'
FORBIDDEN = {'knowledge_tracing', 'numpy', 'pandas', 'torch', 'scipy', 'sklearn', 'networkx'}
OUTPUTS = {'reservation.json', 'arm_exposures.json', 'paired_trajectories.json',
           'joined_contrasts.json', 'result.json', 'output-manifest.json', 'failure.json'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if digest(PARSER) != PARSER_SHA or digest(CONTRACT) != CONTRACT_SHA:
        raise ValueError('parser/contract bytes changed')
    contract = json.loads(CONTRACT.read_bytes())
    sys.path.insert(0, str(ROOT / 'scripts/research'))
    import windows_owned_worker as helper
    if digest(Path(helper.__file__)) != HELPER_SHA:
        raise ValueError('owned helper changed')
    bootstrap_denied = []

    def no_process(event, args):
        if event == 'subprocess.Popen' or event.startswith('socket.') or event in (
                'os.system', 'os.posix_spawn', 'os.spawn', 'os.fork', 'os.exec'):
            bootstrap_denied.append(event)
            raise RuntimeError('bootstrap process/network denied')

    sys.addaudithook(no_process)
    # Import stdlib đã review, tránh lazy read sau khi đóng allowlist.
    # Không gọi formatter hoặc OS terminal API trong bootstrap.
    import shutil
    codecs.lookup('utf-8-sig')
    old_display = {name: os.environ.get(name) for name in ('COLUMNS', 'LINES')}
    os.environ['COLUMNS'], os.environ['LINES'] = '80', '24'
    expected_reads = {os.path.normcase(str((ROOT / n).resolve())) for n in contract['inputs']}
    expected_reads.update(os.path.normcase(str(p.resolve())) for p in
                          (PARSER, CONTRACT, Path(__file__), Path(helper.__file__),
                           OWNED / 'launch.json', OWNED / 'GO.json'))
    allowed_outputs = {os.path.normcase(str((INNER / n).resolve())) for n in OUTPUTS}
    allowed_outputs.add(os.path.normcase(str((OWNED / 'ready.json').resolve())))
    scope_path = OWNED / 'scope.json'
    allowed_outputs.add(os.path.normcase(str(scope_path.resolve())))
    denied = []

    def deny(kind):
        denied.append(kind)
        raise RuntimeError('scope denied: ' + kind)

    def audit(event, args):
        if event == 'subprocess.Popen' or event.startswith('socket.') or event in (
                'os.system', 'os.posix_spawn', 'os.spawn', 'os.fork', 'os.exec'):
            deny(event)
        if event == 'import' and str(args[0]).split('.')[0] in FORBIDDEN:
            deny('scientific/model import')
        if event == 'ctypes.dlopen' and str(args[0]).lower() != 'kernel32':
            deny('unreviewed native library')
        if event == 'open' and not isinstance(args[0], int):
            path = os.path.normcase(str(Path(args[0]).resolve()))
            mode = args[1] or ''
            flags = args[2] if type(args[2]) is int else 0
            writing = any(c in mode for c in 'wax+') or bool(flags & (os.O_WRONLY | os.O_RDWR))
            if writing:
                if path not in allowed_outputs:
                    deny('write outside exclusive output files')
            elif path not in expected_reads and path not in allowed_outputs:
                deny('read outside fixed source/input/output allowlist')
        if event == 'os.mkdir' and Path(args[0]).resolve() != INNER:
            deny('mkdir outside planned inner directory')
        if event in ('os.remove', 'os.rename', 'os.rmdir', 'os.link', 'os.symlink'):
            deny('historical filesystem mutation')

    sys.addaudithook(audit)
    result_code = None
    error = None
    try:
        module = types.ModuleType('rq2_frozen_cached_parser')
        module.__file__ = str(PARSER)
        exec(compile(PARSER.read_bytes(), str(PARSER), 'exec'), module.__dict__)
        # argv giữ đúng reviewed owned wrapper, parser thực hiện worker_gate.
        result_code = module.main()
        return result_code
    except BaseException as exc:
        error = dict(type=type(exc).__name__, message=str(exc))
        raise
    finally:
        for name, old_value in old_display.items():
            if old_value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = old_value
        display_restored = all(os.environ.get(name) == value for name, value in old_display.items())
        heavy = sorted(FORBIDDEN.intersection(sys.modules))
        payload = dict(status='FROZEN_PARSER_MAIN_RETURNED' if result_code == 0 else 'PARSER_INCOMPLETE',
                       parser_sha256=digest(PARSER), contract_sha256=digest(CONTRACT),
                       original_main_exit_code=result_code, error=error, denied_events=denied,
                       bootstrap_process_network_denials=bootstrap_denied,
                       display_override=dict(COLUMNS='80', LINES='24'),
                       display_environment_restored=display_restored,
                       unexpected_heavy_modules=heavy, scope='CPU09_ALLOWLISTED_CACHED_SECONDARY_ANALYSIS')
        with scope_path.open('x', encoding='utf-8') as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())


if __name__ == '__main__':
    raise SystemExit(main())
