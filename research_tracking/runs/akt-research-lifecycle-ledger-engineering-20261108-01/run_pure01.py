"""Chạy pytest cùng process .venv; Timer hợp tác, không hard OS quota."""
import time
STARTED = time.perf_counter()
import contextlib
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import traceback
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
TRIAL = Path(__file__).resolve().parent / 'trial01'
SOURCES = (
    'src/knowledge_tracing/akt/research_lifecycle.py',
    'tests/akt/test_research_lifecycle.py',
    'src/knowledge_tracing/akt/research_execution.py',
    'src/knowledge_tracing/akt/config.py',
    'src/knowledge_tracing/akt/authorization.py',
    'src/knowledge_tracing/akt/provenance.py',
    'src/knowledge_tracing/simulator_bridge.py',
    'src/knowledge_tracing/simulator_data.py',
    'src/knowledge_tracing/simulator_research_data.py',
    'src/knowledge_tracing/__init__.py',
    'src/knowledge_tracing/akt/__init__.py',
    'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md',
)
EXPECTED = {
    SOURCES[0]: '7a00442d39dd6bb82b4eb5af57b6de2cfa46057ac147d0230bf926d673d1b85b',
    SOURCES[1]: '14b02640009d9e0f1d0fe01bc3249eb11cb72d0f27b0d50aca4056db2a9668bd',
}


def write(name, value):
    with (TRIAL/name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def inventory():
    return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}


def timeout():
    # _exit bỏ qua finally: sentinel không giả là có JUnit cuối cùng.
    try:
        write('timeout-sentinel.json', dict(status='TIMEOUT_UNKNOWN_TEST_COUNTS',
            elapsed_seconds=time.perf_counter()-STARTED, pid=os.getpid(), exit_code=124,
            mechanism='GIL-dependent daemon Timer; no hard OS quota; no descendants expected'))
    finally:
        os._exit(124)


def main():
    if sys.prefix != str(ROOT/'.venv') or Path(sys.executable).absolute() != ROOT/'.venv/Scripts/python.exe':
        raise ValueError('exact project .venv interpreter required')
    TRIAL.mkdir()  # Exclusive attempt; no retry/overwrite.
    timer = threading.Timer(max(.001, 18.0-(time.perf_counter()-STARTED)), timeout)
    timer.daemon = True
    timer.start()
    before = {}; code = None; error = None; counts = None
    try:
        before = inventory()
        write('sources_before.json', before)
        if any(before[path] != digest for path, digest in EXPECTED.items()):
            raise ValueError('reviewed source/test bytes changed before run')
        snapshots = TRIAL/'source_snapshots'; snapshots.mkdir()
        for index, name in enumerate(SOURCES):
            raw = (ROOT/name).read_bytes()
            if hashlib.sha256(raw).hexdigest() != before[name]:
                raise ValueError('source changed before snapshot')
            with (snapshots/f'{index:02d}__{Path(name).name}.before').open('xb') as stream:
                stream.write(raw)
        for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
            os.environ[key] = '2'
        os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
        os.environ['NVIDIA_VISIBLE_DEVICES'] = 'none'
        os.chdir(ROOT)
        sys.path.insert(0, str(ROOT/'src'))
        with (TRIAL/'stdout.log').open('x', encoding='utf-8') as out, (TRIAL/'stderr.log').open('x', encoding='utf-8') as err:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                import pytest
                code = int(pytest.main(['tests/akt/test_research_lifecycle.py', '-q', '-p', 'no:cacheprovider',
                                       '--junitxml='+str(TRIAL/'junit.xml')]))
    except BaseException:
        error = traceback.format_exc()
    finally:
        after = inventory()
        write('sources_after.json', after)
        if (TRIAL/'junit.xml').is_file():
            suites = list(ET.parse(TRIAL/'junit.xml').getroot().iter('testsuite'))
            counts = {key: sum(int(s.attrib.get(key, 0)) for s in suites)
                      for key in ('tests', 'failures', 'errors', 'skipped')}
        elapsed = time.perf_counter()-STARTED
        accepted = (code == 0 and error is None and before == after and counts is not None
                    and counts['tests'] > 0 and all(counts[k] == 0 for k in ('failures', 'errors', 'skipped'))
                    and elapsed <= 20.)
        receipt = dict(status='PASS_PURE_METADATA_NOT_EXECUTION_PROOF' if accepted else 'FAILED_OR_REJECTED',
            controller_elapsed_seconds=elapsed, cumulative_cap_seconds=20., timer_seconds=18.,
            pid=os.getpid(), python=sys.executable, prefix=sys.prefix, pytest_exit_code=code,
            counts=counts, error=error, source_before_after_equal=before == after,
            neural_calls=0, optimizer_steps=0, corpus_reads=0, subprocess_calls=0,
            limitation='Timer depends on GIL; _exit skips finally; no OS quota or native worker proof',
            elapsed_scope='controller entry through JUnit parse and source posthash; outer tool wall checked separately')
        write('receipt.json', receipt)
        timer.cancel()
        print(json.dumps(receipt, ensure_ascii=False))
    return 0 if accepted else 1


if __name__ == '__main__':
    raise SystemExit(main())
