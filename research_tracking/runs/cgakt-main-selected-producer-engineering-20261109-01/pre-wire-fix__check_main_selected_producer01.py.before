"""ROOT-only source/controller01:16 mocked cases, no actual main grant/fit."""
import time
START,WALL=time.perf_counter(),time.time()
from contextlib import redirect_stdout,redirect_stderr
from pathlib import Path
import argparse
import hashlib
import importlib
import json
import math
import os
import platform
import sys
import threading
import xml.etree.ElementTree as ET

R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent;SELF=Path(__file__).resolve()
PACKET=P/'main_selected_producer_pure01_allocation.json'
OUT=P/'main-selected-producer-pure01';OWNED=P/'main-selected-producer-pure01-owned'
TMP=R/'artifacts/akt/local-tests/msr01'
HELPER='scripts/research/windows_owned_worker.py'
HELPER_SHA='0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'
CAP=60.;WORKER_CAP=50.;CLEANUP=3.
BLOCKED={'numpy','pandas','torch','scipy','sklearn','joblib','pyBKT','modal','boto3'}
TESTS=('tests/akt/test_research_main_execution.py','tests/akt/test_research_selected_runner.py')
DOMAIN=('knowledge_tracing','knowledge_tracing.akt','knowledge_tracing.akt.research_main_execution',
 'knowledge_tracing.akt.research_selected_runner','knowledge_tracing.akt.research_main_stage',
 'knowledge_tracing.akt.research_execution','knowledge_tracing.akt.research_runner',
 'knowledge_tracing.akt.research_lifecycle','knowledge_tracing.akt.config','knowledge_tracing.akt.authorization',
 'knowledge_tracing.akt.provenance','knowledge_tracing.research_admission','knowledge_tracing.research_selection',
 'knowledge_tracing.simulator_bridge','knowledge_tracing.simulator_data','knowledge_tracing.simulator_research_data',
 'knowledge_tracing.simulator_corpus_reader')


def need(ok,message):
    if not ok:raise ValueError(message)


def elapsed():return max(time.perf_counter()-START,time.time()-WALL)


def sha(path):
    need(path.is_file() and not path.is_symlink() and not getattr(path,'is_junction',lambda:False)(),'physical pinned file')
    with path.open('rb') as stream:raw=stream.read(16*1024**2+1)
    need(len(raw)<=16*1024**2,'bounded source/runtime/receipt file');return hashlib.sha256(raw).hexdigest()


def write(path,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    need(len(raw)<=1024**2,'small controller receipt')
    with path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())


def packet(pin):
    need(type(pin) is str and len(pin)==64 and sha(PACKET)==pin,'exact ROOT-reviewed allocation SHA')
    value=json.loads(PACKET.read_bytes())
    need(value['expected_tests']==16 and value['whole_seconds']==CAP and value['worker_seconds']==WORKER_CAP
         and value['cleanup_seconds']==CLEANUP and value['test_files']==list(TESTS)
         and value['model_or_data_execution_authorized'] is False,'fixed16 mock-only allocation')
    return value


def snapshots(value):return ({n:sha(R/n) for n in value['source_pins']},{n:sha(Path(n)) for n in value['runtime_pins']})


def worker(pin):
    sys.path.insert(0,str(R/'scripts/research'))
    from windows_owned_worker import worker_gate
    owner=worker_gate()  # BEFORE domain/framework/pytest imports.
    value=packet(pin);before,runtime_before=snapshots(value)
    need(before==value['source_pins'] and runtime_before==value['runtime_pins'],'actual source/runtime before')
    need(not OUT.exists() and not TMP.exists(),'exclusive worker outputs/short fixture root')
    OUT.mkdir();TMP.mkdir();runtime_temp=OWNED/'runtime-temp';runtime_temp.mkdir()
    os.chdir(R)
    env_keys=('TEMP','TMP','TMPDIR','PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTEST_ADDOPTS','PYTEST_PLUGINS',
              'PYTHONDONTWRITEBYTECODE','CUDA_VISIBLE_DEVICES','NVIDIA_VISIBLE_DEVICES',
              'OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS')
    env_before={k:os.environ.get(k) for k in env_keys};dontwrite=sys.dont_write_bytecode
    os.environ.update(TEMP=str(runtime_temp),TMP=str(runtime_temp),TMPDIR=str(runtime_temp),
        PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTEST_ADDOPTS='',PYTEST_PLUGINS='',PYTHONDONTWRITEBYTECODE='1',
        CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void');sys.dont_write_bytecode=True
    # No generic write sandbox: pinned tests write only owned TMP/OUT; metadata
    # libraries may honestly open system DEVNULL while bootstrapping Windows.
    phase=['metadata'];denied=[];metadata=dict(phase_closed=False,helper_calls=0,commands=[],outside_phase_popen_attempts=0)
    system_cmd=Path(os.environ['SystemRoot'])/'System32/cmd.exe'
    def audit(event,args):
        if event=='import':
            name=str(args[0])
            if name.split('.')[0] in BLOCKED or name.startswith('knowledge_tracing.') and name not in DOMAIN:
                denied.append('import:'+name);raise RuntimeError('mock-only dependency boundary')
        if event=='subprocess.Popen':
            if phase[0]!='metadata':
                metadata['outside_phase_popen_attempts']+=1;denied.append(event);raise RuntimeError('no test child/native Git/solver')
            fixed=os.path.normcase(os.path.abspath(str(system_cmd)))
            allowed={fixed.casefold()+' /c "ver"','"'+fixed.casefold()+'" /c "ver"'}
            ok=(metadata['helper_calls']<3 and type(args[0]) is str and type(args[1]) is str
                and os.path.normcase(os.path.abspath(args[0]))==fixed and args[1].strip().casefold() in allowed)
            if not ok:denied.append('metadata_command');raise RuntimeError('only real bounded system cmd literal ver')
            metadata['helper_calls']+=1;metadata['commands'].append(dict(executable=args[0],command=args[1]));return
        if event=='os.system' or event.startswith(('os.spawn','os.posix_spawn')) or event.startswith('socket.') and not (phase[0]=='metadata' and event=='socket.gethostname'):
            denied.append(event);raise RuntimeError('no network/undeclared child')
        if event in ('open','os.listdir','os.scandir') and args and isinstance(args[0],(str,bytes,os.PathLike)):
            path=Path(os.path.abspath(os.fsdecode(args[0])))
            for name in ('dataset','artifacts/bkt_baseline','artifacts/simulator/corpora','experiments','venv','.wsl','research_tracking/runs','artifacts/akt/dependencies/upstream'):
                if path==R/name or path.is_relative_to(R/name):
                    denied.append('actual_artifact:'+name);raise RuntimeError('no actual corpus/model/source-loader inputs')
            if path.suffix.lower() in ('.pt','.pth','.ckpt','.safetensors','.parquet'):
                denied.append('binary_data');raise RuntimeError('no model/data binary')
    sys.addaudithook(audit)
    stop=threading.Event();monitor=None;monitor_errors=[];lock=threading.Lock()
    resources=dict(samples=0,observed_peak_rss_bytes=0,observed_minimum_available_ram_bytes=None)
    error=junit_error=None;counts=rc=None;canary=None;identity=False;after={};runtime_after={}
    timer=threading.Timer(52.,lambda:os._exit(124));timer.daemon=True;timer.start()
    def deadline():need(math.isfinite(elapsed()) and 0<=elapsed()<WORKER_CAP,'same worker global deadline')
    try:
        deadline();need(sys.platform=='win32' and system_cmd.is_file(),'real Windows metadata')
        need(not any(n.split('.')[0] in BLOCKED or n=='knowledge_tracing' for n in sys.modules),'cold caller before real imports')
        try:
            actual=platform.uname();processor=platform.processor()
            metadata.update(public_api='platform.uname + platform.processor',system=actual.system,release=actual.release,
                version=actual.version,machine=actual.machine,processor_cache_warmed=type(processor) is str,
                fixture_replaced=False,inside_owned_job=True)
            need(actual.system=='Windows','actual native Windows fields')
        finally:phase[0]='mock_tests';metadata['phase_closed']=True
        deadline();write(OUT/'windows-metadata.json',metadata)
        import psutil
        need(Path(psutil.__file__).resolve()==Path(value['runtime_origins']['psutil']).resolve(),'actual pinned psutil origin')
        process=psutil.Process()
        def memory():
            with lock:
                deadline();info=process.memory_info();peak=max(int(info.rss),int(info.peak_wset));free=int(psutil.virtual_memory().available)
                resources['samples']+=1;resources['observed_peak_rss_bytes']=max(resources['observed_peak_rss_bytes'],peak)
                old=resources['observed_minimum_available_ram_bytes'];resources['observed_minimum_available_ram_bytes']=free if old is None else min(old,free)
                need(peak<=1024**3 and free>=2*1024**3,'observed worker RSS1GiB/free2GiB')
        memory()
        def watch():
            while not stop.wait(.1):
                try:memory()
                except BaseException as failure:
                    monitor_errors.append(type(failure).__name__+':'+str(failure))
                    try:write(OUT/'resource-failure.json',dict(error=monitor_errors[-1],resources=resources))
                    finally:os._exit(125)
        monitor=threading.Thread(target=watch,daemon=True);monitor.start()
        sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(R/'tests/akt'))
        main=importlib.import_module('knowledge_tracing.akt.research_main_execution')
        runner=importlib.import_module('knowledge_tracing.akt.research_selected_runner')
        stage=importlib.import_module('knowledge_tracing.akt.research_main_stage')
        need(not any(n.split('.')[0] in BLOCKED for n in sys.modules),'cold domain imports must remain metadata-only')
        held=(main.MainSelectedExecutionSpec,main.MainSelectedExecution,main.MainGitProfile,runner.MainSelectedExecutionSpec,stage.MainSelectedStageSpec)
        need(held[0] is held[3] and main.MainSelectedStageSpec is held[4],'same actual module classes, no reload aliases')
        origins={n:str(Path(m.__file__).resolve()) for n,m in sys.modules.copy().items() if n in DOMAIN}
        for name,path in origins.items():
            relative='src/'+name.replace('.','/')+('/__init__.py' if name in ('knowledge_tracing','knowledge_tracing.akt') else '.py')
            need(Path(path)==R/relative and sha(Path(path))==before[relative],'real pinned domain origin')
        canary=dict(status='COLD_REAL_METADATA_MODULES_ONLY',origins=origins,scientific_modules_present=[],
            same_execution_spec_class=True,guard_constructed=False,actual_runtime_or_gate_validated=False,model_calls=0)
        write(OUT/'cold-canary.json',canary)
        import pytest
        need(Path(pytest.__file__).resolve()==Path(value['runtime_origins']['pytest']).resolve(),'actual pinned pytest origin')
        class Journal:
            def pytest_collection_modifyitems(self,session,config,items):
                ids=[item.nodeid for item in items];need(len(ids)==len(set(ids))==16,'exact16 unique cases; no subset')
                need({x.split('::')[0].replace('\\','/') for x in ids}==set(TESTS),'exact two test files')
                write(OUT/'collected.json',dict(nodeids=ids,tests=16))
            def pytest_runtest_logreport(self,report):
                with (OUT/'case-events.jsonl').open('a',encoding='utf-8') as stream:
                    stream.write(json.dumps(dict(nodeid=report.nodeid,when=report.when,outcome=report.outcome,
                        elapsed_seconds=elapsed()))+'\n');stream.flush();os.fsync(stream.fileno())
        command=[*TESTS,'-q','--noconftest','-p','no:cacheprovider','--basetemp',str(TMP/'t'),'--junitxml',str(OUT/'junit.xml')]
        with (OUT/'pytest.log').open('x',encoding='utf-8') as log:
            with redirect_stdout(log),redirect_stderr(log):rc=int(pytest.main(command,plugins=[Journal()]))
        a=sys.modules['test_research_main_execution'];b=sys.modules['test_research_selected_runner']
        identity=(a.main is main and b.runner is runner and b.make_case is a.make_case and a.old is main.old
            and a.cfg.AKTConfig is main.old.AKTConfig and runner.MainSelectedExecutionSpec is held[0]
            and (main.MainSelectedExecutionSpec,main.MainSelectedExecution,main.MainGitProfile,runner.MainSelectedExecutionSpec,stage.MainSelectedStageSpec)==held)
        need(identity,'caller/test actual cached class identity after monkeypatch teardown');memory()
    except BaseException as failure:error=dict(type=type(failure).__name__,message=str(failure))
    finally:
        stop.set()
        if monitor is not None:monitor.join(timeout=.5)
        monitor_stopped=monitor is None or not monitor.is_alive()
        try:
            tree=ET.parse(OUT/'junit.xml').getroot()
            counts={k:sum(int(s.get(k,'0')) for s in tree.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
            need(len(list(tree.iter('testcase')))==counts['tests'],'actual JUnit count')
        except BaseException as failure:junit_error=dict(type=type(failure).__name__,message=str(failure))
        try:
            after,runtime_after=snapshots(value)
            need(after==before and runtime_after==runtime_before and sha(PACKET)==pin,'postflight source/runtime/packet pins')
        except BaseException as failure:
            if error is None:error=dict(type=type(failure).__name__,message=str(failure))
        for key,previous in env_before.items():
            if previous is None:os.environ.pop(key,None)
            else:os.environ[key]=previous
        sys.dont_write_bytecode=dontwrite
        scientific=sorted(n for n in sys.modules if n.split('.')[0] in BLOCKED)
        clean_env=all(os.environ.get(k)==v for k,v in env_before.items())
        accepted=(error is None and junit_error is None and rc==0 and counts==dict(tests=16,failures=0,errors=0,skipped=0)
            and not denied and not scientific and identity and clean_env and not monitor_errors and monitor_stopped
            and metadata['phase_closed'] and metadata['outside_phase_popen_attempts']==0 and elapsed()<WORKER_CAP)
        result=dict(status='ACCEPTED_16_MOCKED_MAIN_PRODUCER_CASES_PENDING_OUTER' if accepted else 'REJECTED_KEEP_ALL',
            counts=counts,pytest_exit_code=rc,original_error=error,junit_error=junit_error,source_before=before,source_after=after,
            runtime_before=runtime_before,runtime_after=runtime_after,allocation_sha256=pin,ownership=owner,cold_import=canary,
            cached_caller_class_identity=identity,denied_attempts=denied,scientific_modules_present=scientific,
            native_windows_metadata=metadata,environment_restored=clean_env,monitor_errors=monitor_errors,monitor_stopped=monitor_stopped,
            resources=resources,elapsed_seconds=elapsed(),worker_cap_seconds=WORKER_CAP,model_calls=0,optimizer_calls=0,
            actual_guard_grant=False,actual_gate_or_corpus_acceptance=False,
            scope_vi='16mockfixtures;0actualmodel/corpus/Git/preflight. Metadata helper children are declared separately; not blanket zero-process/sandbox proof.')
        write(OUT/'worker-result.json',result);timer.cancel()
        if elapsed()>=WORKER_CAP:write(OUT/'postwrite_rejection.json',dict(elapsed_seconds=elapsed()));accepted=False
    print(json.dumps(dict(status=result['status'] if accepted else 'REJECTED_KEEP_ALL',counts=counts,elapsed_seconds=elapsed())))
    raise SystemExit(0 if accepted else 1)


def root(pin,approval):
    need(type(approval) is str and bool(approval.strip()),'ROOT review reference required; no implicit execution')
    value=packet(pin);before,runtime_before=snapshots(value)
    need(before==value['source_pins'] and runtime_before==value['runtime_pins'] and sha(R/HELPER)==HELPER_SHA,'root exact preflight pins')
    need(not OUT.exists() and not OWNED.exists() and not TMP.exists(),'new single attempt, no overwrite/retry')
    sys.path.insert(0,str(R/'scripts/research'))
    from windows_owned_worker import run_owned,entry,safe
    entry();safe(OUT);safe(OWNED);safe(TMP)
    import psutil
    need(int(psutil.virtual_memory().available)>=2*1024**3,'ROOT admission free2GiB')
    errors=[];receipt=result=None;after={};runtime_after={};counts=None
    try:
        allowance=min(58.,CAP-elapsed()-2.);need(allowance>10.,'whole60 remaining inclcleanup3/final2')
        receipt=run_owned(SELF,['--worker','--packet-sha256',pin],OWNED,expected_worker_sha256=before[SELF.relative_to(R).as_posix()],
            approval_reference=approval,max_seconds=allowance,cleanup_reserve_seconds=CLEANUP,max_output_bytes=65536)
        write(OWNED/'receipt.json',receipt)
        need(receipt['accepted'] and receipt['cleanup_accepted'] and receipt['actual_worker_in_job_before_GO']
             and receipt['job_active_after_cleanup']==0 and receipt['popen_handle_closed'] and receipt['returncode']==0
             and receipt['errors']==[],'actual owned Job/cleanup verdict')
        for name,digest in receipt['output_sha256'].items():need(name in ('stdout.log','stderr.log') and sha(OWNED/name)==digest,'actual raw logs')
        result=json.loads((OUT/'worker-result.json').read_bytes());counts=result['counts']
        need(result['status']=='ACCEPTED_16_MOCKED_MAIN_PRODUCER_CASES_PENDING_OUTER'
             and counts==dict(tests=16,failures=0,errors=0,skipped=0) and result['pytest_exit_code']==0
             and result['original_error'] is result['junit_error'] is None,'actual complete16, no skip')
        need(result['cold_import']==json.loads((OUT/'cold-canary.json').read_bytes())
             and result['cold_import']['status']=='COLD_REAL_METADATA_MODULES_ONLY'
             and result['cold_import']['guard_constructed'] is False
             and result['actual_guard_grant'] is False and result['actual_gate_or_corpus_acceptance'] is False,
             'cold caller evidence remains metadata only, not actual grant')
        need(result['source_before']==result['source_after']==before and result['runtime_before']==result['runtime_after']==runtime_before
             and result['allocation_sha256']==pin and result['cached_caller_class_identity'] and result['environment_restored']
             and result['monitor_stopped'] and result['monitor_errors']==[] and result['denied_attempts']==[]
             and result['scientific_modules_present']==[] and result['elapsed_seconds']<WORKER_CAP,'worker source/resources/identity')
        meta=result['native_windows_metadata']
        need(meta['phase_closed'] and 0<=meta['helper_calls']<=3 and len(meta['commands'])==meta['helper_calls']
             and meta['outside_phase_popen_attempts']==0 and meta['fixture_replaced'] is False,'honest Windows metadata phase')
        need(result['resources']['observed_peak_rss_bytes']<=1024**3 and result['resources']['observed_minimum_available_ram_bytes']>=2*1024**3,'actual RAM verdict')
        tree=ET.parse(OUT/'junit.xml').getroot();actual={k:sum(int(s.get(k,'0')) for s in tree.iter('testsuite')) for k in counts}
        need(actual==counts and len(list(tree.iter('testcase')))==16 and json.loads((OUT/'collected.json').read_bytes())['tests']==16,'independent actual JUnit/collection')
        need(not any((OUT/n).exists() for n in ('resource-failure.json','postwrite_rejection.json','failure.json')),'no late failure')
    except BaseException as failure:errors.append(dict(type=type(failure).__name__,message=str(failure)))
    try:
        after,runtime_after=snapshots(value);need(after==before and runtime_after==runtime_before and sha(PACKET)==pin,'root postflight pins')
    except BaseException as failure:errors.append(dict(type=type(failure).__name__,message=str(failure)))
    if not OUT.exists():OUT.mkdir()
    accepted=not errors and math.isfinite(elapsed()) and 0<=elapsed()<CAP
    outputs={p.name:sha(p) for p in OUT.iterdir() if p.is_file()}
    final=dict(status='ACCEPTED_16_MOCKED_MAIN_PRODUCER_ENGINEERING_ONLY' if accepted else 'REJECTED_KEEP_PARTIAL',
        errors=errors,counts=counts,source_before=before,source_after=after,runtime_before=runtime_before,runtime_after=runtime_after,
        allocation_sha256=pin,output_sha256=outputs,owned_receipt_sha256=sha(OWNED/'receipt.json') if (OWNED/'receipt.json').exists() else None,
        elapsed_before_receipt_seconds=elapsed(),cap_seconds=CAP,cleanup_reserve_seconds=CLEANUP,automatic_retry=False,
        scope_vi='Mocked guard/training orchestration only; NO actualmainauthorization/Gate/corpus/NN/selectedfit/refit/calibration acceptance.')
    write(OUT/'final.json',final)
    if elapsed()>=CAP:write(OUT/'postwrite_rejection.json',dict(elapsed_seconds=elapsed()));accepted=False
    print(json.dumps(dict(status=final['status'] if accepted else 'REJECTED_KEEP_PARTIAL',counts=counts,elapsed_seconds=elapsed())))
    raise SystemExit(0 if accepted else 1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--worker',action='store_true')
    parser.add_argument('--packet-sha256',required=True);parser.add_argument('--approval-reference');args=parser.parse_args()
    if args.worker:worker(args.packet_sha256)
    else:root(args.packet_sha256,args.approval_reference)
