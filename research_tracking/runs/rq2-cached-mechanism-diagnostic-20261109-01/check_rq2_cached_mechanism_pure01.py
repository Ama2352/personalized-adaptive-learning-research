"""ROOT chạy16 unittest tổng hợp trong owned Job, ghi resource và call ledger."""
import time
START, WALL = time.perf_counter(), time.time()
from pathlib import Path
import argparse
import functools
import hashlib
import importlib
import json
import os
import platform
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
SELF = Path(__file__).resolve()
PACKET = PREP/'rq2_cached_mechanism_pure01_packet.json'
OUT = PREP/'rq2-cached-mechanism-pure01'
OWNED = PREP/'rq2-cached-mechanism-pure01-owned'
HELPER = ROOT/'scripts/research/windows_owned_worker.py'
HELPER_SHA = '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'
SCIENTIFIC = {'numpy','pandas','torch','sklearn','scipy','duckdb','pyBKT','modal','boto3'}
EXPECTED_CALLS = dict(fixture=22,validate_trace=20,endpoint_table=12,analyze=9,
    arm_summary=88,pair_summary=88,trace_rows=6,validate_manifest=7,main=0,sha=0)


def need(ok, message):
    if not ok: raise ValueError(message)


def elapsed():
    return max(time.perf_counter()-START,time.time()-WALL)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write(path, value):
    raw = (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    need(len(raw) <= 1024**2,'receipt1MiB cap')
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def packet(expected_sha):
    raw = PACKET.read_bytes()
    need(len(raw) <= 65536 and hashlib.sha256(raw).hexdigest() == expected_sha,'external exact packet')
    value = json.loads(raw)
    need(value['kind'] == 'RQ2_SYNTHETIC_PARSER_JOIN_UNITTEST_ALLOCATION'
         and value['expected_methods'] == 16 and value['expected_calls'] == EXPECTED_CALLS
         and value['limits'] == dict(whole_seconds=60,worker_seconds=54,cleanup_seconds=3,
                                    max_rss_bytes=1024**3,min_available_ram_bytes=2*1024**3), 'fixed finite test profile')
    need(all(sha(ROOT/name) == digest for name,digest in value['source_sha256'].items()),'three source pins')
    return value


def worker(expected_sha):
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import worker_gate
    owner = worker_gate()
    need(Path(sys.prefix).resolve() == ROOT/'.venv','repository .venv')
    allocation = packet(expected_sha)
    need(not any(name.split('.')[0] in SCIENTIFIC for name in sys.modules),'cold stdlib start')
    runtime_temp = OUT/'runtime-temp'
    runtime_temp.mkdir(exist_ok=False)
    temp_keys = ('TEMP','TMP','TMPDIR')
    old_temp = {key:os.environ.get(key) for key in temp_keys}
    old_cache = tempfile.tempdir
    for key in temp_keys: os.environ[key] = str(runtime_temp)
    tempfile.tempdir = None
    need(Path(tempfile.gettempdir()).resolve() == runtime_temp.resolve(),'owned temporary discovery')
    denied, commands = [], []
    metadata_phase = [True]
    system_cmd = Path(os.environ['SystemRoot'])/'System32/cmd.exe'
    need(system_cmd.is_absolute() and system_cmd.is_file() and not system_cmd.is_symlink()
         and not getattr(system_cmd,'is_junction',lambda:False)(),'literal system metadata executable')
    fixed_cmd = os.path.normcase(os.path.abspath(str(system_cmd)))
    allowed_commands = {fixed_cmd.casefold()+' /c "ver"','"'+fixed_cmd.casefold()+'" /c "ver"'}
    protected = [ROOT/name for name in ('dataset','paper1','paper2','research_tracking',
        'experiments','venv','.wsl','artifacts/bkt_baseline','artifacts/simulator')]
    def audit(event, values):
        if event == 'subprocess.Popen':
            if (metadata_phase[0] and len(commands)<3 and type(values[0]) is str and type(values[1]) is str
                    and os.path.normcase(os.path.abspath(values[0])) == fixed_cmd
                    and values[1].strip().casefold() in allowed_commands):
                commands.append(dict(executable=values[0],command=values[1])); return
            denied.append(dict(event=event)); raise RuntimeError('only bounded metadata child allowed')
        if event == 'os.system' or event.startswith('os.spawn') or event.startswith('socket.') and event != 'socket.gethostname':
            denied.append(dict(event=event)); raise RuntimeError('process/network guard')
        if event == 'import' and (str(values[0]).split('.')[0] in SCIENTIFIC
                                 or str(values[0]).startswith('knowledge_tracing')):
            denied.append(dict(event=event,module=str(values[0]))); raise RuntimeError('data/model/framework imports forbidden')
        if event in ('open','os.listdir','os.scandir') and values and isinstance(values[0],(str,bytes,os.PathLike)):
            name = os.path.normcase(os.path.abspath(os.fsdecode(values[0])))
            if any(name == os.path.normcase(str(base)) or name.startswith(os.path.normcase(str(base))+os.sep) for base in protected):
                denied.append(dict(event=event,path=name)); raise RuntimeError('cached/protected research input access forbidden')
            path = Path(name)
            if path.suffix.lower() in ('.gz','.csv','.parquet','.pt','.pth','.ckpt','.npy','.npz') and not path.is_relative_to(runtime_temp):
                denied.append(dict(event=event,path=name)); raise RuntimeError('only owned handmade gzip fixtures')
    sys.addaudithook(audit)
    try:
        native_os = platform.uname()._asdict()
    finally:
        metadata_phase[0] = False
    import psutil
    process = psutil.Process()
    born = process.create_time()
    resources = dict(samples=0,peak_rss_bytes=0,minimum_available_ram_bytes=None)
    resource_errors, errors = [], []
    stop = threading.Event()
    def sample():
        need(process.create_time() == born,'owned PID identity')
        memory = process.memory_info()
        peak = max(memory.rss,getattr(memory,'peak_wset',0))
        available = int(psutil.virtual_memory().available)
        resources['peak_rss_bytes'] = max(resources['peak_rss_bytes'],peak)
        previous = resources['minimum_available_ram_bytes']
        resources['minimum_available_ram_bytes'] = available if previous is None else min(previous,available)
        resources['samples'] += 1
        need(peak <= 1024**3 and available >= 2*1024**3,'pure resource limits')
    def monitor():
        while not stop.wait(.1):
            try: sample()
            except BaseException as error:
                resource_errors.append(repr(error))
                write(OUT/'resource-failure.json',dict(errors=resource_errors,resources=resources))
                os._exit(125)
    sample()
    watcher = threading.Thread(target=monitor,daemon=True); watcher.start()
    timer = threading.Timer(max(.001,54.-elapsed()),lambda:os._exit(124))
    timer.daemon=True; timer.start()
    calls = {name:0 for name in EXPECTED_CALLS}
    observed_rows = dict(constructed_trace=0,constructed_endpoint=0,constructed_contrast=0,
                         validate_trace_input=0,gzip_invocations=0,maximum_gzip_fixture_bytes=0)
    originals, executed = [], []
    counts = None
    try:
        sys.path.insert(0,str(PREP))
        need('analyze_rq2_cached_mechanism01' not in sys.modules
             and 'test_rq2_cached_mechanism01' not in sys.modules,'fresh normal fixture module imports')
        analysis = importlib.import_module('analyze_rq2_cached_mechanism01')
        tests = importlib.import_module('test_rq2_cached_mechanism01')
        need(Path(analysis.__file__).resolve() == PREP/'analyze_rq2_cached_mechanism01.py'
             and Path(tests.__file__).resolve() == PREP/'test_rq2_cached_mechanism01.py'
             and tests.analysis is analysis,'actual pinned module entrypoints')
        def observe(module,name):
            original = getattr(module,name)
            @functools.wraps(original)
            def counted(*args,**kwargs):
                calls[name] += 1
                need(calls[name] <= EXPECTED_CALLS[name],'finite pure function call reservation')
                if name == 'validate_trace':
                    observed_rows['validate_trace_input'] += len(args[0])
                if name == 'trace_rows':
                    path = args[0]
                    need(path.resolve().is_relative_to(runtime_temp.resolve()) and path.stat().st_size <= 1000,
                         'owned gzip payload<=1000B')
                    observed_rows['gzip_invocations'] += 1
                    observed_rows['maximum_gzip_fixture_bytes'] = max(observed_rows['maximum_gzip_fixture_bytes'],path.stat().st_size)
                value = original(*args,**kwargs)
                if name == 'fixture':
                    need(tuple(map(len,value[:3])) == (36,12,3),'exact manufactured fixture geometry')
                    observed_rows['constructed_trace'] += len(value[0])
                    observed_rows['constructed_endpoint'] += len(value[1])
                    observed_rows['constructed_contrast'] += len(value[2])
                return value
            originals.append((module,name,original))
            setattr(module,name,counted)
        observe(tests,'fixture')
        for name in EXPECTED_CALLS:
            if name != 'fixture': observe(analysis,name)
        suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
        need(suite.countTestCases() == 16,'exact sixteen unittest methods')
        class RecordedResult(unittest.TextTestResult):
            def startTest(self,test):
                executed.append(test.id()); super().startTest(test)
        result = unittest.TextTestRunner(verbosity=2,resultclass=RecordedResult).run(suite)
        counts = dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
                      unexpected_successes=len(result.unexpectedSuccesses),expected_failures=len(result.expectedFailures))
        need(counts == dict(tests=16,failures=0,errors=0,skipped=0,unexpected_successes=0,expected_failures=0)
             and len(set(executed)) == 16 and result.wasSuccessful(),'all16 methods complete with no failures/errors/skips')
        need(calls == EXPECTED_CALLS,'exact pure call population')
        need(observed_rows['constructed_trace'] == 792 and observed_rows['constructed_endpoint'] == 264
             and observed_rows['constructed_contrast'] == 66 and observed_rows['validate_trace_input'] == 720,
             'actual manufactured row counts')
        need(all(sha(ROOT/name) == digest for name,digest in allocation['source_sha256'].items()),'source3 posthash')
    except BaseException as error:
        errors.append(dict(type=type(error).__name__,message=str(error)))
    finally:
        for module,name,original in reversed(originals): setattr(module,name,original)
        restored = all(getattr(module,name) is original for module,name,original in originals)
        stop.set(); watcher.join(timeout=.5)
        try: sample()
        except BaseException as error: resource_errors.append(repr(error))
        for key,value in old_temp.items():
            if value is None: os.environ.pop(key,None)
            else: os.environ[key] = value
        tempfile.tempdir = old_cache
        temp_restored = all(os.environ.get(key) == value for key,value in old_temp.items()) and tempfile.tempdir is old_cache
        heavy = sorted(name for name in sys.modules if name.split('.')[0] in SCIENTIFIC or name.startswith('knowledge_tracing'))
        accepted = (not errors and not resource_errors and not denied and not heavy and restored and temp_restored
                    and not watcher.is_alive() and elapsed()<54)
        write(OUT/'worker-result.json',dict(status='ACCEPTED_SYNTHETIC_RQ2_16_PENDING_OUTER' if accepted else 'REJECTED_SYNTHETIC_RQ2',
            counts=counts,executed_test_ids=executed,calls=calls,expected_calls=EXPECTED_CALLS,rows=observed_rows,
            errors=errors,resource_errors=resource_errors,forbidden=denied,heavy_modules=heavy,methods_restored=restored,
            temporary_state_restored=temp_restored,monitor_stopped=not watcher.is_alive(),resources=resources,
            native_windows_metadata=native_os,metadata_commands=commands,metadata_phase_closed=not metadata_phase[0],
            source_after={name:sha(ROOT/name) for name in allocation['source_sha256']},packet_sha256=expected_sha,
            ownership=owner,elapsed_seconds=elapsed(),cached_data_accesses=0 if not denied else None,
            scope_vi='16method handmade arrays/gzip. Call wrappers observe actual parser/join functions. Cached research inputs are denied by audit.'))
        timer.cancel()
    raise SystemExit(0 if accepted else 1)


def root(args):
    need(args.approval_reference and args.approval_reference.strip(),'ROOT dispatch reference')
    need(not OUT.exists() and not OWNED.exists(),'exclusive attempt')
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import entry,run_owned,safe
    entry()
    allocation = packet(args.packet_sha256)
    self_sha = sha(SELF)
    need(self_sha == args.controller_sha256 and sha(HELPER) == HELPER_SHA,'reviewed controller/helper pins')
    import psutil
    need(psutil.virtual_memory().available >= 2*1024**3,'fresh2GiB before launch')
    safe(OUT).mkdir()
    write(OUT/'before.json',dict(source_sha256=allocation['source_sha256'],controller_sha256=self_sha,
         packet_sha256=args.packet_sha256,approval_reference=args.approval_reference,limits=allocation['limits']))
    receipt, counts, errors, worker_result = None,None,[],None
    try:
        allowance = min(57.,60.-elapsed()-1.)
        need(allowance>=55.,'setup left insufficient worker54/cleanup3 allowance')
        receipt = run_owned(SELF,['--worker','--packet-sha256',args.packet_sha256],OWNED,
            expected_worker_sha256=self_sha,approval_reference=args.approval_reference,
            max_seconds=allowance,cleanup_reserve_seconds=3,max_output_bytes=131072)
        write(OWNED/'receipt.json',receipt)
        need(receipt['accepted'] is True and receipt['returncode']==0 and receipt['cleanup_accepted'] is True
             and receipt['job_active_after_cleanup']==0 and receipt['popen_handle_closed'] is True
             and receipt['actual_worker_in_job_before_GO'] is True and not receipt['errors'],'owned completion/Job0')
        worker_result = json.loads((OUT/'worker-result.json').read_bytes())
        counts = worker_result['counts']
        need(worker_result['status']=='ACCEPTED_SYNTHETIC_RQ2_16_PENDING_OUTER'
             and worker_result['source_after']==allocation['source_sha256'] and worker_result['packet_sha256']==args.packet_sha256
             and worker_result['calls']==EXPECTED_CALLS and worker_result['methods_restored'] is True
             and worker_result['temporary_state_restored'] is True and worker_result['monitor_stopped'] is True
             and worker_result['errors']==worker_result['forbidden']==worker_result['resource_errors']==worker_result['heavy_modules']==[]
             and worker_result['cached_data_accesses']==0 and worker_result['elapsed_seconds']<54,'durable pure worker acceptance')
        need(counts == dict(tests=16,failures=0,errors=0,skipped=0,unexpected_successes=0,expected_failures=0),'exact real unittest result')
        need(all(sha(OWNED/name)==digest for name,digest in receipt['output_sha256'].items()),'raw stream bytes')
        need(sha(SELF)==self_sha and sha(HELPER)==HELPER_SHA and sha(PACKET)==args.packet_sha256
             and all(sha(ROOT/name)==digest for name,digest in allocation['source_sha256'].items()),'final source/packet pins')
        need(psutil.virtual_memory().available>=2*1024**3
             and max(psutil.Process().memory_info().rss,getattr(psutil.Process().memory_info(),'peak_wset',0))<=1024**3,'outer resource check')
    except BaseException as error: errors.append(dict(type=type(error).__name__,message=str(error)))
    outputs = {path.name:dict(bytes=path.stat().st_size,sha256=sha(path)) for path in OUT.iterdir() if path.is_file()}
    accepted = not errors and elapsed()<60
    write(OUT/'result.json',dict(status='ACCEPTED_16_SYNTHETIC_RQ2_METHODS_ONLY' if accepted else 'REJECTED_RQ2_PURE_TEST_ATTEMPT',
        counts=counts,errors=errors,elapsed_seconds=elapsed(),whole_cap_seconds=60,source_sha256=allocation['source_sha256'],
        controller_sha256=self_sha,packet_sha256=args.packet_sha256,owned_receipt=receipt,worker_result=worker_result,
        outputs_before_result=outputs,automatic_retry=False))
    if elapsed()>=60:
        write(OUT/'postwrite-rejection.json',dict(elapsed_seconds=elapsed())); accepted=False
    print(json.dumps(dict(accepted=accepted,counts=counts,elapsed_seconds=elapsed())))
    raise SystemExit(0 if accepted else 1)


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker',action='store_true')
    parser.add_argument('--packet-sha256',required=True)
    parser.add_argument('--controller-sha256')
    parser.add_argument('--approval-reference')
    args = parser.parse_args()
    if args.worker: worker(args.packet_sha256)
    else: root(args)
