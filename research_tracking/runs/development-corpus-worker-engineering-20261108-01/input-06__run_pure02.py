"""Prepare-only second controller: directpytest, auditdeny,20s same ledger."""
import time
START=time.perf_counter()
import builtins
import contextlib
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import threading
import traceback
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
TRIAL=PREP/'trial02'
BASE=ROOT/'artifacts/akt/local-tests/dcw02'
PRIOR_SECONDS=1.2762708999798633
SOURCES=[ROOT/'scripts/research/collect_development_corpus.py',
         ROOT/'tests/shared_kt/test_development_corpus_worker.py',
         ROOT/'experiments/akt/configs/simulator-research-corpus01.json',Path(__file__).resolve()]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(name,value):
    with (TRIAL/name).open('x',encoding='utf-8') as handle:
        json.dump(value,handle,ensure_ascii=False,indent=2,allow_nan=False);handle.write('\n')

def main():
    assert Path(sys.executable).absolute()==ROOT/'.venv/Scripts/python.exe'
    assert sys.prefix==str(ROOT/'.venv') and sys.platform=='win32'
    TRIAL.mkdir()
    old_import=builtins.__import__;old_ver=platform._syscmd_ver;old_cache=platform._uname_cache
    before={};after={};code=None;original_error=None;counts=None;junit_error=None
    controller_errors=[];reported_errors=[];denied=[];fixture=None
    timer=None;accepted=False
    def expire():
        try:
            write('timeout.json',dict(status='TIMEOUT_UNKNOWN_COUNTS',elapsed_seconds=time.perf_counter()-START,
                prior_charged_seconds=PRIOR_SECONDS,max_cumulative_seconds=20,counts=None,
                limitation='GIL-dependent timer; _exit skipsfinally; no hardOSquota proof'))
        finally:os._exit(124)
    def audit(event,args):
        if event=='subprocess.Popen':
            # Do not store argv/env audit arguments.
            value=dict(event=event,status='DENIED_BEFORE_PROCESS_CREATION',stack=traceback.format_stack(limit=8))
            denied.append(value)
            with (TRIAL/'denied-processes.jsonl').open('a',encoding='utf-8') as handle:
                handle.write(json.dumps(value,ensure_ascii=False)+'\n')
            raise RuntimeError('pure worker tests deny subprocess creation')
    def no_heavy(name,*args,**kwargs):
        if name.split('.')[0] in ('numpy','pandas','torch'):
            raise AssertionError('actual heavy import denied by purecontroller: '+name)
        return old_import(name,*args,**kwargs)
    class Capture:
        def save(self,kind,report):
            text=str(report)
            reported_errors.append(dict(kind=kind,trace=text[:65536],truncated=len(text)>65536))
        def pytest_collectreport(self,report):
            if report.failed:self.save('collection',report.longrepr)
        def pytest_internalerror(self,excrepr,excinfo):self.save('internal',excrepr)
        def pytest_runtest_logreport(self,report):
            if report.failed:self.save(report.when,report.longrepr)
    try:
        prior=json.loads((PREP/'trial01/run.json').read_bytes())
        assert prior['controller_seconds']==PRIOR_SECONDS and prior['returncode']==1
        old_counts=ET.parse(PREP/'trial01/pytest.xml').getroot().find('testsuite').attrib
        assert int(old_counts['tests'])==19 and int(old_counts['errors'])==19
        ledger_path=PREP/'budget.json'
        previous=json.loads(ledger_path.read_bytes())
        assert len(previous)==1 and sum(row['controller_seconds'] for row in previous)==PRIOR_SECONDS
        with (TRIAL/'budget-before.json').open('xb') as handle:handle.write(ledger_path.read_bytes())
        assert not BASE.exists(),'shortbasetemp must be exclusive; pytest cannot delete prior artifacts'
        assert not any(n in sys.modules for n in ('numpy','pandas','torch'))
        before={p.relative_to(ROOT).as_posix():sha(p) for p in SOURCES}
        assert before['scripts/research/collect_development_corpus.py']=='09c909570e94ecc5bb87fdc7f4e75848fa53b91ea1317ab20a383bac4362e192'
        assert before['experiments/akt/configs/simulator-research-corpus01.json']=='8e7800482cea61a5f3ab66e4909de996fda57bcc059dd2751c2e4177dbfa263e'
        snapshots=TRIAL/'source-before';snapshots.mkdir()
        for path in SOURCES:
            dest=snapshots/path.name;dest.write_bytes(path.read_bytes());assert sha(dest)==sha(path)
        write('reservation.json',dict(status='PREPARED_PURE_MOCK_NOT_NATIVE',prior_seconds=PRIOR_SECONDS,
              max_cumulative_seconds=20,source_sha256=before,basetemp=str(BASE)))
        version=tuple(sys.getwindowsversion().platform_version)
        assert len(version)==3 and all(type(n) is int and n>=0 for n in version)
        version_string='.'.join(map(str,version))
        def metadata_fixture(system='',release='',version='',supported_platforms=('win32','win16','dos')):
            return (system,release,version_string) if sys.platform in supported_platforms else (system,release,version)
        fixture=dict(kind='TEST_ONLY_PLATFORM_FALLBACK_NOT_RUNTIME',patched_symbol='platform._syscmd_ver',
            actual_value_source='sys.getwindowsversion().platform_version',platform_version=list(version),
            version_string=version_string,platform_module_sha256=sha(Path(platform.__file__)),
            tuple_contract='caller system/release + actual major.minor.build',architecture_patched=False,
            production_library_files_edited=False,clocks_patched=False,data_or_model_patched=False,
            reused_design='simulator-corpus-reader-20261108-01/run_pure04.py')
        write('platform-fallback-fixture.json',fixture)
        platform._syscmd_ver=metadata_fixture
        os.environ.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTEST_ADDOPTS='',PYTHONDONTWRITEBYTECODE='1',
            CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        builtins.__import__=no_heavy;sys.addaudithook(audit)
        timer=threading.Timer(max(.001,20-PRIOR_SECONDS-(time.perf_counter()-START)),expire)
        timer.daemon=True;timer.start()
        with (TRIAL/'pytest.log').open('x',encoding='utf-8') as log:
            with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                import pytest
                code=int(pytest.main(['tests/shared_kt/test_development_corpus_worker.py','-q','-p','no:cacheprovider',
                    '-o','addopts=','--basetemp='+str(BASE),'--junitxml='+str(TRIAL/'pytest.xml')],plugins=[Capture()]))
    except BaseException:
        original_error=traceback.format_exc()
    finally:
        builtins.__import__=old_import;platform._syscmd_ver=old_ver;platform._uname_cache=old_cache
        try:write('pytest-outcome.json',dict(pytest_exit_code=code,original_exception=original_error,
                    reported_errors=reported_errors,denied_process_events=len(denied)))
        except BaseException:controller_errors.append(dict(stage='outcome_persistence',trace=traceback.format_exc()))
        try:after={p.relative_to(ROOT).as_posix():sha(p) for p in SOURCES}
        except BaseException:controller_errors.append(dict(stage='posthash',trace=traceback.format_exc()))
        try:
            suites=list(ET.parse(TRIAL/'pytest.xml').getroot().iter('testsuite'))
            counts={key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ('tests','failures','errors','skipped')}
        except BaseException:junit_error=traceback.format_exc()
        elapsed=time.perf_counter()-START
        heavy=[n for n in ('numpy','pandas','torch') if n in sys.modules]
        accepted=(code==0 and original_error is None and not controller_errors and not reported_errors
            and not denied and not heavy and junit_error is None and before==after and len(before)==4
            and counts==dict(tests=19,failures=0,errors=0,skipped=0) and PRIOR_SECONDS+elapsed<=20)
        receipt=dict(status='PASS_PURE_DRIVER_ORCHESTRATION_MOCKS_NOT_ACTUAL_CORPUS' if accepted else 'FAILED_RETAIN_NO_AUTO_RETRY',
            returncode=code,counts=counts,controller_seconds=elapsed,prior_charged_seconds=PRIOR_SECONDS,
            cumulative_seconds=PRIOR_SECONDS+elapsed,max_cumulative_seconds=20,
            source_before_sha256=before,source_after_sha256=after,sources_unchanged=before==after,
            original_pytest_exception=original_error,reported_errors=reported_errors,controller_errors=controller_errors,
            junit_parse_error=junit_error,actual_heavy_modules_loaded=heavy,denied_process_events=len(denied),
            subprocess_audit_scope='Audit denies subprocess.Popen within this controller/test process; no class replacement',
            platform_metadata_fixture=fixture,actual_native_model_collector_calls=0,
            mock_counts_not_observed_teacher_attempts=True,actual_research_corpus=False,actual_runtime_gate=False,
            historical_trial01='19SETUP_ERRORS_WINDOWS_MAX_PATH_NOT_DRIVER_BUG_RETAINED',
            limitation='Mocks prove orchestration only; timer/cooperativechecks are not a hardOSquota; firsttrial subprocess count was notgloballyaudited.')
        try:
            write('run.json',receipt)
            ledger_path=PREP/'budget.json';rows=json.loads(ledger_path.read_bytes())
            rows.append(dict(trial='trial02',controller_seconds=elapsed,returncode=code))
            ledger_path.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
        finally:
            if timer is not None:timer.cancel()
        print(json.dumps(receipt,ensure_ascii=False))
    return 0 if accepted else 1

if __name__=='__main__':
    raise SystemExit(main())
