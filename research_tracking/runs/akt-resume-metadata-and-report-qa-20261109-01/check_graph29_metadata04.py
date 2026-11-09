"""Root-only collection/execution metadata; exact native runtime node tách riêng."""
import time
PERF,WALL,MONO=time.perf_counter,time.time,time.monotonic
START,START_WALL,START_MONO=PERF(),WALL(),MONO()
import argparse
from contextlib import redirect_stdout,redirect_stderr
import hashlib
import importlib.util
import json
import os
from pathlib import Path
PATH_OPEN=Path.open
import sys
import threading
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
PACKET=PREP/'graph29_metadata04_packet.json'



def need(ok,message):
    if not ok:raise ValueError(message)


def elapsed():return max(PERF()-START,WALL()-START_WALL,MONO()-START_MONO)


def sha(path):
    with PATH_OPEN(path,'rb') as stream:return hashlib.sha256(stream.read()).hexdigest()


def write(path,value):
    with PATH_OPEN(path,'x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())


def main():
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import worker_gate,safe
    owner=worker_gate()
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('collect','tests'),required=True)
    parser.add_argument('--attempt',required=True)
    parser.add_argument('--packet-sha256',required=True);parser.add_argument('--collection-sha256')
    args=parser.parse_args()
    need(len(args.attempt)==2 and all('0'<=c<='9' for c in args.attempt),'attempt requires exactly two ASCII digits')
    collection=PREP/('graph29-metadata-collection'+args.attempt+'-owned/final.json')
    raw=safe(PACKET).read_bytes()
    need(len(raw)<=131072 and hashlib.sha256(raw).hexdigest()==args.packet_sha256,'reviewed packet SHA')
    packet=json.loads(raw);pins=packet['source_pins'];runtime_pins=packet['runtime_pins']
    cap=packet['allocations'][args.mode]['worker_seconds']
    timer=threading.Timer(max(.001,cap-elapsed()),lambda:os._exit(124));timer.daemon=True;timer.start()
    need(elapsed()<cap and Path(sys.prefix).resolve()==ROOT/'.venv' and sys.dont_write_bytecode is True,'actual .venv/bytecode profile')
    need(not any(n.split('.')[0] in ('torch','numpy','pandas') for n in sys.modules),'cold actual scientific imports')
    before={n:sha(safe(ROOT/n)) for n in pins};runtime_before={n:sha(Path(n)) for n in runtime_pins}
    need(before==pins and runtime_before==runtime_pins,'actual canonical source/runtime pins')
    expected=None
    if args.mode=='tests':
        raw=safe(collection).read_bytes()
        need(args.collection_sha256 and hashlib.sha256(raw).hexdigest()==args.collection_sha256,'Root external actual collection SHA')
        outer=json.loads(raw);expected=outer['child_result']
        need(outer['attempt']==args.attempt and expected['attempt']==args.attempt
             and outer['status']=='ACCEPTED_BATCHC_COLLECTION_ONLY_NOT_TEST_PASS'
             and not (collection.parent/'postwrite_rejection.json').exists() and outer['errors']==[]
             and outer['receipt']['cleanup_accepted'] is True and outer['receipt']['job_active_after_cleanup']==0
             and expected['accepted'] is True
             and expected['source_after']==pins and expected['runtime_after']==runtime_pins
             and expected['test_protocol_entries']==expected['test_body_entries']==0,'accepted same-source collection required')
    else:need(args.collection_sha256 is None,'collection has no prior collection claim')
    suffix=('collection' if args.mode=='collect' else 'tests')+args.attempt
    out=PREP/('graph29-metadata-'+suffix)
    base=ROOT/'artifacts/akt/local-tests'/(('g29c' if args.mode=='collect' else 'g29t')+args.attempt)
    need(not safe(out).exists() and not safe(base).exists(),'fresh owned outputs/basetemp')
    out.mkdir();temporary=out/'runtime-temp';temporary.mkdir()
    sys.path[:0]=[str(ROOT),str(ROOT/'src')]
    keys=('TEMP','TMP','TMPDIR','PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTEST_ADDOPTS','PYTEST_PLUGINS','CUDA_VISIBLE_DEVICES','NVIDIA_VISIBLE_DEVICES')
    env_before={n:os.environ.get(n) for n in keys}
    os.environ.update(TEMP=str(temporary),TMP=str(temporary),TMPDIR=str(temporary),PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
        PYTEST_ADDOPTS='',PYTEST_PLUGINS='',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void')
    sys_before=(sys.prefix,sys.executable,sys.dont_write_bytecode,list(sys.argv),sys.pycache_prefix)
    owned_pycache_prefix=str(temporary/'fresh-bytecode')
    need(not Path(owned_pycache_prefix).exists(),'fresh owned bytecode prefix')
    sys.pycache_prefix=owned_pycache_prefix
    phase=['bootstrap_metadata'];denied=[];metadata={};items=[];deselected=[];collect_errors=[]
    protocol_entries=body_entries=0;rc=None;error=None;counts=None;source_after={};runtime_after={}
    resources=dict(samples=0,observed_peak_rss_bytes=0,observed_minimum_available_ram_bytes=None)
    import psutil
    process=psutil.Process()
    def check():
        need(elapsed()<cap,'same worker deadline using captured real clocks')
        memory=process.memory_info();peak=max(memory.rss,getattr(memory,'peak_wset',0));free=int(psutil.virtual_memory().available)
        resources['samples']+=1;resources['observed_peak_rss_bytes']=max(resources['observed_peak_rss_bytes'],peak)
        previous=resources['observed_minimum_available_ram_bytes']
        resources['observed_minimum_available_ram_bytes']=free if previous is None else min(previous,free)
        need(peak<=128*1024**2 and free>=1024*1024**2,'cooperative metadata RAM cap/floor')
    def event(value):
        with PATH_OPEN(out/'events.jsonl','a',encoding='utf-8') as stream:
            stream.write(json.dumps(dict(seconds=elapsed(),**value),allow_nan=False)+'\n');stream.flush();os.fsync(stream.fileno())
    def reject(message,details=None):
        if len(denied)<8:
            frames=[];frame=sys._getframe(1)
            try:
                while frame is not None and len(frames)<6:
                    frames.append(dict(file=frame.f_code.co_filename[:1024],
                        function=frame.f_code.co_name[:80],line=frame.f_lineno))
                    frame=frame.f_back
            finally:del frame
            denied.append(dict(phase=phase[0],message=message,details=details,
                caller_frames=frames,import_breadcrumbs=list(import_breadcrumbs)))
        raise RuntimeError(message)
    allowed={safe(ROOT/n) for n in pins}|{PACKET.resolve(),collection.resolve()}
    runtimes=(ROOT/'.venv',Path(sys.base_prefix).resolve())
    def owned(path):return path.is_relative_to(out) or path.is_relative_to(base)
    null_count=[0];pytest_stdin_null_reads=[0];import_breadcrumbs=[]
    optional_symlink_count=[0];optional_symlink_records=[]
    pytest_pathlib=ROOT/'.venv/Lib/site-packages/_pytest/pathlib.py'
    def audit(kind,values):
        if kind=='import':
            imported=values[0] if values and type(values[0]) is str else '<non-string>'
            origin=values[1] if len(values)>1 and type(values[1]) is str else None
            import_breadcrumbs.append(dict(name=imported[:256],file=None if origin is None else origin[:1024]))
            del import_breadcrumbs[:-8]
        if kind=='import' and str(values[0]).split('.')[0] in ('torch','numpy','pandas','sklearn','scipy','modal','boto3'):
            reject('real scientific/solver/cloud import event forbidden; existing fixture modules are permitted')
        if kind=='subprocess.Popen' and phase[0]!='bootstrap_metadata':reject('no process after metadata')
        if kind.startswith('socket.') and not(phase[0]=='bootstrap_metadata' and kind=='socket.gethostname'):reject('no network')
        if kind=='os.system' or kind.startswith('os.spawn'):reject('no system/spawn')
        if kind=='open' and values and not isinstance(values[0],int):
            name=os.fsdecode(values[0]);mode=values[1] or '';flags=values[2] if type(values[2]) is int else 0
            writing=any(c in mode for c in 'wax+') or bool(flags&(os.O_WRONLY|os.O_RDWR))
            if writing and name==os.devnull and phase[0]=='bootstrap_metadata':
                need(flags&os.O_RDWR and not flags&(os.O_CREAT|os.O_TRUNC|os.O_APPEND) and null_count[0]<3,'bounded metadata NUL')
                null_count[0]+=1;return
            if not writing and name==os.devnull and phase[0]=='metadata_pytest':
                caller=sys._getframe(1)
                try:
                    exact_capture=(caller.f_code.co_filename==str(ROOT/'.venv/Lib/site-packages/_pytest/capture.py')
                        and caller.f_code.co_name=='__init__' and caller.f_lineno==489)
                finally:del caller
                need(exact_capture and mode=='r' and flags==32896 and pytest_stdin_null_reads[0]<4,
                    'only observed pinned Pytest stdin read of exact os.devnull')
                pytest_stdin_null_reads[0]+=1
                return
            path=Path(name).absolute().resolve()
            if writing:
                if not owned(path):reject('write outside owned fixture/output roots',details=dict(raw_path=name[:2048],resolved_path=str(path)[:2048],mode=mode[:32],flags=flags))
            else:
                cache_source=None
                if path.suffix=='.pyc':
                    try:cache_source=Path(importlib.util.source_from_cache(str(path))).resolve()
                    except ValueError:pass
                if path not in allowed and cache_source not in allowed and not owned(path) and not any(path.is_relative_to(r) for r in runtimes):
                    reject('read outside pinned source/runtime/fixture roots',details=dict(raw_path=name[:2048],resolved_path=str(path)[:2048],mode=mode[:32],flags=flags))
        if kind in ('os.mkdir','os.remove','os.rmdir','os.rename'):
            paths=values[:2] if kind=='os.rename' else values[:1]
            if not all(owned(Path(v).absolute().resolve()) for v in paths):reject('filesystem mutation outside owned roots')
        if kind=='os.symlink' and phase[0]=='metadata_pytest' and len(values)==3 and values[2]==-1:
            caller=sys._getframe(1);pytest_caller=caller.f_back
            try:
                exact_optional=(caller.f_code.co_filename==str(Path(sys.base_prefix)/'Lib/pathlib/_local.py')
                    and caller.f_code.co_name=='symlink_to' and pytest_caller is not None
                    and pytest_caller.f_code.co_filename==str(pytest_pathlib)
                    and pytest_caller.f_code.co_name=='_force_symlink' and pytest_caller.f_lineno==219)
            finally:del caller,pytest_caller
            source=Path(os.fsdecode(values[0]));destination=Path(os.fsdecode(values[1]))
            owned_pair=all(path.is_absolute() and '..' not in path.parts and path.resolve()==path.absolute()
                and path.is_relative_to(base) and path!=base for path in (source,destination))
            if exact_optional and owned_pair:
                optional_symlink_count[0]+=1
                if optional_symlink_count[0]>1024:reject('optional Pytest symlink denial cap')
                if len(optional_symlink_records)<8:
                    optional_symlink_records.append(dict(source=str(source)[:1024],destination=str(destination)[:1024],
                        caller_file=str(pytest_pathlib),caller_function='_force_symlink',caller_line=219))
                # Raise before returning from the audit hook: no OS link is created.
                raise PermissionError('owned optional Pytest current symlink disabled by metadata controller')
        if kind in ('os.link','os.symlink'):reject('no link creation')
    sys.addaudithook(audit)
    try:
        check()
        helper=ROOT/packet['metadata_helper'];helper_raw=helper.read_bytes()
        need(hashlib.sha256(helper_raw).hexdigest()==pins[packet['metadata_helper']],'verified metadata helper bytes')
        namespace=dict(__file__=str(helper),__name__='batchc_real_metadata_only')
        exec(compile(helper_raw,str(helper),'exec'),namespace)
        namespace['native_windows_metadata'](check,metadata);write(out/'native_metadata.json',metadata)
        phase[0]='metadata_pytest'
        import pytest
        from _pytest.junitxml import mangle_test_address
        class Plugin:
            def pytest_collectreport(self,report):
                if report.failed:collect_errors.append(dict(nodeid=report.nodeid,error=str(report.longrepr)))
            def pytest_deselected(self,items):deselected.extend(item.nodeid for item in items)
            def pytest_collection_finish(self,session):
                items.extend(item.nodeid for item in session.items)
                need(0<len(items)<=1024 and len(items)==len(set(items)),'nonempty unique bounded actual IDs')
                need(deselected==packet['deselect_nodeids'],'exact native probe and two realTorch stopper exclusions')
                need(items==packet['expected_nodeids'],'source-derived299 expected IDs, actualsame-source collection required')
                if expected is not None:need(items==expected['nodeids'],'same collected ordered IDs before any test body')
            def pytest_runtest_protocol(self,item,nextitem):
                nonlocal protocol_entries
                check();protocol_entries+=1
                need(args.mode=='tests','collect-only cannot enter test protocol')
            def pytest_runtest_call(self,item):
                nonlocal body_entries
                check();body_entries+=1;event(dict(kind='body_entry',nodeid=item.nodeid))
            def pytest_runtest_logreport(self,report):
                check();event(dict(kind=report.when,nodeid=report.nodeid,outcome=report.outcome))
        exclusions=[value for node in packet['deselect_nodeids'] for value in ('--deselect',node)]
        argv=[*packet['modules'],*exclusions,'--noconftest','-p','no:cacheprovider',
            '-p','no:terminal','-o','addopts=','--basetemp',str(base),'--log-file='+str(out/'pytest-file.log')]
        if args.mode=='collect':argv.append('--collect-only')
        else:argv.extend(['--junitxml',str(out/'junit.xml')])
        need(not base.exists(),'basetemp still absent immediately before pytest deletion API')
        with PATH_OPEN(out/'pytest.log','x',encoding='utf-8') as log,redirect_stdout(log),redirect_stderr(log):
            rc=int(pytest.main(argv,plugins=[Plugin()]))
        mapped=[]
        for node in items:
            names=mangle_test_address(node);mapped.append(('.'.join(names[:-1]),names[-1]))
        need(len(mapped)==len(set(mapped)),'no JUnit identity collision')
        if args.mode=='tests':
            cases=list(ET.parse(out/'junit.xml').iter('testcase'))
            ids=[(case.get('classname'),case.get('name')) for case in cases]
            counts=dict(tests=len(cases),failures=sum(len(list(c.iter('failure'))) for c in cases),
                errors=sum(len(list(c.iter('error'))) for c in cases),skipped=sum(len(list(c.iter('skipped'))) for c in cases))
            need(len(ids)==len(set(ids)) and set(ids)==set(mapped),'all exact physical JUnit identities')
            need(counts==dict(tests=len(items),failures=0,errors=0,skipped=0)
                 and protocol_entries==body_entries==len(items),'all selected cases ran, no partial/skip acceptance')
        else:need(protocol_entries==body_entries==0,'no body execution during collection')
        need(rc==0 and not collect_errors and not denied,'actual pytest/collection outcomes')
        namespace['require_metadata_closed'](metadata);check()
    except BaseException as exc:error=dict(type=type(exc).__name__,message=str(exc))
    finally:
        for name,value in env_before.items():
            if value is None:os.environ.pop(name,None)
            else:os.environ[name]=value
        restored=env_before=={n:os.environ.get(n) for n in keys}
        sys.pycache_prefix=sys_before[4]
        restored=restored and sys_before==(sys.prefix,sys.executable,sys.dont_write_bytecode,list(sys.argv),sys.pycache_prefix) and Path.open is PATH_OPEN
        source_after={n:sha(safe(ROOT/n)) for n in pins};runtime_after={n:sha(Path(n)) for n in runtime_pins}
        cold=not any(n.split('.')[0] in ('torch','numpy','pandas') for n in sys.modules)
        accepted=error is None and cold and restored and source_after==before and runtime_after==runtime_before and elapsed()<cap
        actual_new=[n for n in items if n.partition('[')[0] in packet['added_functions']]
        actual_checkpoint=[n for n in items if n in packet['checkpoint38_reference']['expected_nodeids']]
        result=dict(status=('ACCEPTED_BATCHC_COLLECTION_CHILD' if args.mode=='collect' else 'ACCEPTED_BATCHC_METADATA_CHILD') if accepted else 'REJECTED_BATCHC_METADATA_KEEP_ALL',
            mode=args.mode,attempt=args.attempt,accepted=accepted,pytest_exit_code=rc,error=error,collection_errors=collect_errors,denied=denied,import_breadcrumbs=import_breadcrumbs,
            nodeids=items,deselected_nodeids=deselected,actual_selected_count=len(items),actual_new_nodeids=actual_new,
            actual_prior_nodeids=[n for n in items if n not in actual_new and n not in actual_checkpoint],
            actual_checkpoint_nodeids=actual_checkpoint,counts=counts,
            test_protocol_entries=protocol_entries,test_body_entries=body_entries,source_before=before,source_after=source_after,
            runtime_before=runtime_before,runtime_after=runtime_after,environment_and_sys_restored=restored,
            actual_scientific_modules_absent=cold,resources=resources,resource_scope='COOPERATIVE_HOOK_SAMPLES_NOT_CONTINUOUS_HARD_RSS',
            owner_gate_passed=owner['status']=='OWNED_JOB_GATE_PASSED_NOT_SCIENTIFIC_ACCEPTANCE',packet_sha256=args.packet_sha256,
            collection_outer_sha256=args.collection_sha256,pytest_stdin_null_reads=pytest_stdin_null_reads[0],
            owned_pycache_prefix_used=True,owned_pycache_prefix=owned_pycache_prefix,
            path_open_restored=Path.open is PATH_OPEN,optional_pytest_symlink_blocks=dict(count=optional_symlink_count[0],records=optional_symlink_records),
            elapsed_seconds=elapsed(),cap_seconds=cap)
        write(out/'result.json',result)
        if elapsed()>=cap:
            write(out/'postwrite_rejection.json',dict(status='REJECTED_POSTWRITE_TIME',elapsed_seconds=elapsed()));accepted=False
        timer.cancel()
    raise SystemExit(0 if accepted else 1)


if __name__=='__main__':main()
