"""Direct pytest.main,20s cumulative/self-timer; không child/native/model."""
import time
START=time.perf_counter()
import hashlib
import json
import os
from pathlib import Path
import sys
import threading

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
SOURCES=[ROOT/'scripts/research/collect_development_corpus.py',
         ROOT/'tests/shared_kt/test_development_corpus_worker.py',
         ROOT/'experiments/akt/configs/simulator-research-corpus01.json',Path(__file__).resolve()]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path,value):
    with path.open('x',encoding='utf-8') as handle:
        json.dump(value,handle,ensure_ascii=False,indent=2);handle.write('\n')

if __name__=='__main__':
    assert Path(sys.executable).absolute()==ROOT/'.venv/Scripts/python.exe'
    assert not any(n in sys.modules for n in ('numpy','pandas','torch'))
    os.environ.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTEST_ADDOPTS='',PYTHONDONTWRITEBYTECODE='1',
        CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    ledger=PREP/'budget.json'
    previous=json.loads(ledger.read_bytes()) if ledger.exists() else []
    spent=sum(r['controller_seconds'] for r in previous)
    remaining=20-spent;assert remaining>.1
    trial=PREP/sys.argv[1];trial.mkdir()
    before={p.relative_to(ROOT).as_posix():sha(p) for p in SOURCES}
    snapshots=trial/'source-before';snapshots.mkdir()
    for path in SOURCES:
        dest=snapshots/path.name;dest.write_bytes(path.read_bytes());assert sha(dest)==sha(path)
    dump(trial/'reservation.json',dict(status='RESERVED_PURE_MOCK_ORCHESTRATION_NOT_NATIVE',source_sha256=before,
        cumulative_spent_seconds=spent,max_cumulative_seconds=20,actual_collection_model_calls=0))
    def timeout():
        with (trial/'timeout.txt').open('x',encoding='utf-8') as handle:handle.write('Cumulative20s expired; no fabricated test counts.\n')
        os._exit(124)  # Exact current pure-test process, no nested Popen or children.
    timer=threading.Timer(max(.001,remaining-(time.perf_counter()-START)),timeout);timer.daemon=True;timer.start()
    import pytest
    command=['tests/shared_kt/test_development_corpus_worker.py','-q','-p','no:cacheprovider','-o','addopts=',
             '--basetemp='+str(trial/'tmp'),'--junitxml='+str(trial/'pytest.xml')]
    original_out,original_err=sys.stdout,sys.stderr
    with (trial/'pytest.log').open('x',encoding='utf-8') as log:
        try:
            sys.stdout=sys.stderr=log
            rc=pytest.main(command)
        finally:
            sys.stdout,sys.stderr=original_out,original_err
    after={p.relative_to(ROOT).as_posix():sha(p) for p in SOURCES}
    heavy=[n for n in ('numpy','pandas','torch') if n in sys.modules]
    elapsed=time.perf_counter()-START
    result=dict(returncode=int(rc),controller_seconds=elapsed,cumulative_seconds=spent+elapsed,
        max_cumulative_seconds=20,source_before_sha256=before,source_after_sha256=after,
        sources_unchanged=before==after,actual_heavy_modules_loaded=heavy,
        actual_collection_publisher_reader_model_process_remote_calls=0,
        scope='Actual driver orchestration with manufactured module/plan/results stubs and temporary filesystem only',
        limitation='Not actual corpus, teacher counts, seed/source attestation, native readiness or hardOSquota proof.')
    dump(trial/'run.json',result)
    previous.append(dict(trial=sys.argv[1],controller_seconds=elapsed,returncode=int(rc)))
    ledger.write_text(json.dumps(previous,indent=2)+'\n',encoding='utf-8')
    timer.cancel()
    print(json.dumps(result))
    assert before==after and not heavy and spent+elapsed<=20
