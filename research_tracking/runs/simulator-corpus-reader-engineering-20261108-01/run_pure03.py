"""Reader pure03 cùng process; giữ nguyên UNKNOWN01/failed02, ghi lỗi trước XML."""
import time
STARTED = time.perf_counter()
import builtins
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
PREP = Path(__file__).resolve().parent
TRIAL = PREP/'trial03'
PRIOR_SECONDS = 29.56646766238098
TRIAL01_SECONDS = 28.01250386238098
OLD_RECEIPT_SHA256 = '8e139c5ed8d5ae52d9bcf823dc00b5e2941d54a6fd82da309caf1121d7e393b6'
EXPECTED_READER = 'e582bf293e7699f1dc98096fcc693437610f2253bddb11ba4fff8952a35f6a90'
EXPECTED_TEST = 'b92ecab03a1bbcef58406cd6e3cf53628a76181511497a446ee9c44753e0e2fb'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    with (TRIAL/name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def timeout():
    try:
        elapsed = time.perf_counter()-STARTED
        write('timeout-sentinel.json', dict(status='TIMEOUT_UNKNOWN_TEST_COUNTS',
            pid=os.getpid(), exit_code=124, controller_elapsed_seconds=elapsed,
            prior_charged_seconds=PRIOR_SECONDS, cumulative_seconds=PRIOR_SECONDS+elapsed,
            cap_seconds=90, timer_seconds=55,
            limitation='GIL-dependent Timer; no hard OS quota; _exit skips finally; no descendants expected'))
    finally:
        os._exit(124)


def main():
    if sys.prefix != str(ROOT/'.venv') or Path(sys.executable).absolute() != ROOT/'.venv/Scripts/python.exe':
        raise ValueError('exact project .venv interpreter required')
    TRIAL.mkdir()
    timer = threading.Timer(max(.001, 55.-(time.perf_counter()-STARTED)), timeout)
    timer.daemon = True; timer.start()
    before = {}; code = None; error = None; counts = None; paths = ()
    controller_errors = []; report_errors = []; denied_processes = []
    original_import = builtins.__import__
    def audit(event,args):
        if event != 'subprocess.Popen':
            return
        # Không đọc/lưu args: có thể chứa argv/env/credentials.
        value = dict(event=event, caller_stack=traceback.format_stack(limit=10),
                     status='DENIED_BEFORE_CHILD_LAUNCH')
        denied_processes.append(value)
        with (TRIAL/'denied-processes.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(value,ensure_ascii=False)+'\n');stream.flush();os.fsync(stream.fileno())
        raise RuntimeError('subprocess denied by reader03 audit hook before launch')
    class ErrorCapture:
        def pytest_collectreport(self,report):
            if report.failed:
                self.save('collection',str(report.longrepr))
        def pytest_internalerror(self,excrepr,excinfo):
            self.save('pytest_internalerror',str(excrepr))
        def save(self,kind,text):
            value = dict(kind=kind,trace=text[:65536],trace_truncated=len(text)>65536)
            report_errors.append(value)
            with (TRIAL/'pytest-errors.jsonl').open('a',encoding='utf-8') as stream:
                stream.write(json.dumps(value,ensure_ascii=False)+'\n');stream.flush();os.fsync(stream.fileno())
    try:
        old_path = PREP/'trial01/receipt.json'
        if sha(old_path) != OLD_RECEIPT_SHA256:
            raise ValueError('historical timeout receipt changed')
        old = json.loads(old_path.read_bytes())
        if old['counts'] is not None or old['controller_elapsed_seconds'] != TRIAL01_SECONDS or old['exit_code'] is not None:
            raise ValueError('trial01 must remain UNKNOWN, not relabeled PASS')
        paths = tuple(old['source_sha256_before'])
        before = {name:sha(ROOT/name) for name in paths}
        if (len(paths) != 12 or before != old['source_sha256_before'] or before != old['source_sha256_after']
                or before['src/knowledge_tracing/simulator_corpus_reader.py'] != EXPECTED_READER
                or before['tests/shared_kt/test_simulator_corpus_reader.py'] != EXPECTED_TEST):
            raise ValueError('frozen reader/test/dependency bytes changed')
        write('sources_before.json', before)
        snapshots = TRIAL/'source_snapshots'; snapshots.mkdir()
        for index, name in enumerate(paths):
            raw = (ROOT/name).read_bytes()
            if hashlib.sha256(raw).hexdigest() != before[name]:
                raise ValueError('source changed before snapshot')
            with (snapshots/f'{index:02d}__{Path(name).name}.before').open('xb') as stream:
                stream.write(raw)
        for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):
            os.environ[key] = '2'
        os.environ.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='none')
        def no_torch(name,*args,**kwargs):
            if name == 'torch' or name.startswith('torch.') or name in (
                    'knowledge_tracing.akt.model','knowledge_tracing.akt.training'):
                raise AssertionError('no neural imports in reader pure02')
            return original_import(name,*args,**kwargs)
        builtins.__import__ = no_torch
        sys.addaudithook(audit)  # Process riêng, không có native/model và không remove hook.
        os.chdir(ROOT); sys.path.insert(0,str(ROOT/'src'))
        with (TRIAL/'stdout.log').open('x',encoding='utf-8') as out, (TRIAL/'stderr.log').open('x',encoding='utf-8') as err:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                import pytest
                code = int(pytest.main(['tests/shared_kt/test_simulator_corpus_reader.py', '-q', '-p', 'no:cacheprovider',
                    '--basetemp='+str(TRIAL/'tmp'), '--junitxml='+str(TRIAL/'junit.xml')],plugins=[ErrorCapture()]))
    except BaseException:
        error = traceback.format_exc()
    finally:
        builtins.__import__ = original_import
        # Lưu original outcome TRƯỚC mọi sourceposthash/XMLparse có thể lỗi.
        try:
            write('pytest_outcome.json',dict(pytest_exit_code=code,original_exception=error,
                  reported_errors=report_errors,denied_process_events=len(denied_processes)))
        except BaseException:
            controller_errors.append(dict(stage='outcome_persistence',trace=traceback.format_exc()))
        after = {}
        try:
            after = {name:sha(ROOT/name) for name in paths}
            write('sources_after.json', after)
        except BaseException:
            controller_errors.append(dict(stage='source_posthash',trace=traceback.format_exc()))
        junit_error = None
        try:
            if (TRIAL/'junit.xml').is_file():
                suites = list(ET.parse(TRIAL/'junit.xml').getroot().iter('testsuite'))
                counts = {key:sum(int(s.attrib.get(key,0)) for s in suites)
                          for key in ('tests','failures','errors','skipped')}
            else:
                junit_error = 'JUnit file missing'
        except BaseException:
            junit_error = traceback.format_exc()
        elapsed = time.perf_counter()-STARTED
        accepted = (code == 0 and error is None and not report_errors and not controller_errors
                    and not denied_processes and junit_error is None and before == after and len(before) == 12
                    and counts is not None and counts['tests'] > 0
                    and all(counts[k] == 0 for k in ('failures','errors','skipped'))
                    and 'torch' not in sys.modules and sha(PREP/'trial01/receipt.json') == OLD_RECEIPT_SHA256
                    and elapsed <= 60. and PRIOR_SECONDS+elapsed <= 90.)
        receipt = dict(status='PASS_PUBLIC_READER_FIXTURES_NOT_ACTUAL_CORPUS' if accepted else 'FAILED_OR_REJECTED',
            controller_elapsed_seconds=elapsed, new_call_cap_seconds=60, prior_charged_seconds=PRIOR_SECONDS,
            cumulative_seconds=PRIOR_SECONDS+elapsed, cumulative_cap_seconds=90, timer_seconds=55,
            historical_trial01='UNKNOWN_TIMEOUT_NO_JUNIT_RETAINED', historical_trial02='COLLECTION_FAILED_INVALID_JUNIT_RETAINED',
            old_receipt_sha256=OLD_RECEIPT_SHA256,
            pid=os.getpid(), python=sys.executable, prefix=sys.prefix, pytest_exit_code=code, counts=counts,
            original_pytest_exception=error,controller_errors=controller_errors,junit_parse_error=junit_error,
            reported_errors=report_errors,denied_process_events=len(denied_processes),
            source_before_after_equal=before == after, torch_imported='torch' in sys.modules,
            model_calls=0,optimizer_updates=0,teacher_collection_calls=0,subprocess_calls=0,
            actual_research_corpus_read=False, actual_runtime_gate=False,
            fixture_origin='publisher tmp corpus of handmade observables; mocked source/memory; native teacher forbidden',
            timer_limitation='GIL-dependent Timer, not hard OS quota; _exit skips finally',
            elapsed_scope='controller through JUnit parse/posthash; outer tool wall must also pass new60/cumulative90')
        write('receipt.json', receipt)
        timer.cancel()
        print(json.dumps(receipt,ensure_ascii=False))
    return 0 if accepted else 1


if __name__ == '__main__':
    raise SystemExit(main())
