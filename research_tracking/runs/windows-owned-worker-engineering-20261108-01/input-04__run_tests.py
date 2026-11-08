"""ONE direct unittest invocation;20s cumulative timer,0native/model data."""
import time
START=time.perf_counter()
import hashlib
import io
import json
from pathlib import Path
import sys
import threading
import unittest
import os

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
SOURCES=[ROOT/'scripts/research/windows_owned_worker.py',PREP/'test_launcher.py',Path(__file__).resolve()]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path,value):
    with path.open('x',encoding='utf-8') as handle:
        json.dump(value,handle,ensure_ascii=False,indent=2);handle.write('\n')

if __name__=='__main__':
    assert Path(sys.executable).absolute()==ROOT/'.venv/Scripts/python.exe'
    assert not (PREP/'trial01').exists()
    trial=PREP/'trial01';trial.mkdir()
    snapshots=trial/'source-before';snapshots.mkdir()
    before={p.relative_to(ROOT).as_posix():sha(p) for p in SOURCES}
    for path in SOURCES:
        copy=snapshots/path.name;copy.write_bytes(path.read_bytes());assert sha(copy)==sha(path)
    dump(trial/'reservation.json',dict(status='ONE_PURE_SYNTHETIC_ATTEMPT_RESERVED',source_sha256=before,
                                     budget_seconds=20,native_model_collector_remote_calls=0))
    def expire():
        with (trial/'timeout.txt').open('x',encoding='utf-8') as handle:handle.write('20s timer fired; no fabricated test counts.\n')
        os._exit(124)  # Exact current test process; owned Job handles close on exit.
    timer=threading.Timer(max(.001,20-(time.perf_counter()-START)),expire);timer.daemon=True;timer.start()
    sys.path.insert(0,str(PREP))
    import test_launcher
    suite=unittest.defaultTestLoader.loadTestsFromModule(test_launcher)
    with (trial/'unittest.log').open('x',encoding='utf-8') as log:
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    after={p.relative_to(ROOT).as_posix():sha(p) for p in SOURCES}
    elapsed=time.perf_counter()-START
    receipt=dict(status='PASS_PURE_WINDOWS_OWNED_JOB_TESTS' if result.wasSuccessful() and before==after and elapsed<=20 else 'FAILED_RETAIN_NO_AUTO_RETRY',
        tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
        elapsed_seconds=elapsed,cumulative_seconds=elapsed,max_cumulative_seconds=20,
        source_before_sha256=before,source_after_sha256=after,native_model_collector_remote_calls=0,
        limitation='Pure sleeping processes/metadata only; no native timeout simulation or scientific acceptance. Timer/cooperative checks are not a hardOSquota proof.')
    dump(trial/'run.json',receipt)
    timer.cancel()
    print(json.dumps(receipt))
