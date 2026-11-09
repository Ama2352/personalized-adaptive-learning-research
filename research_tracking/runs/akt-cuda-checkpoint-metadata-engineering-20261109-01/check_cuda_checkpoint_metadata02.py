"""ROOT-only38opaque checkpoint metadata cases; no scientific backend imports."""
import time
PERF,WALL,MONO=time.perf_counter,time.time,time.monotonic
START,START_WALL,START_MONO=PERF(),WALL(),MONO()
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from contextlib import redirect_stdout,redirect_stderr
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
OUT=PREP/'cuda-checkpoint-metadata-tests02'
BASE=ROOT/'artifacts/akt/local-tests/ccm02'
PACKET=PREP/'cuda_checkpoint_metadata02_packet.json'
PATH_OPEN=Path.open


def need(value,message):
    if not value:raise ValueError(message)


def elapsed():return max(PERF()-START,WALL()-START_WALL,MONO()-START_MONO)


def sha(path):
    with PATH_OPEN(path,'rb') as stream:return hashlib.sha256(stream.read()).hexdigest()


def write(name,value):
    with PATH_OPEN(OUT/name,'x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())


sys.path.insert(0,str(ROOT/'scripts/research'))
from windows_owned_worker import worker_gate,safe
owner=worker_gate()
need(len(sys.argv)==2,'ROOT reviewed packet SHA')
packet_raw=safe(PACKET).read_bytes()
need(len(packet_raw)<=131072 and hashlib.sha256(packet_raw).hexdigest()==sys.argv[1],'exact packet')
packet=json.loads(packet_raw);pins=packet['source_pins'];runtime=packet['runtime_pins']
need(all(sha(safe(ROOT/n))==h for n,h in pins.items()) and all(sha(Path(n))==h for n,h in runtime.items()),'current source/runtime')
need(not safe(OUT).exists() and not safe(BASE).exists(),'exclusive metadata02 outputs/basetemp')
OUT.mkdir();temporary=OUT/'runtime-temp';temporary.mkdir()
keys=('TEMP','TMP','TMPDIR','PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTEST_ADDOPTS','PYTEST_PLUGINS','CUDA_VISIBLE_DEVICES','NVIDIA_VISIBLE_DEVICES')
env_before={n:os.environ.get(n) for n in keys}
sys_before=(sys.prefix,sys.executable,sys.dont_write_bytecode,list(sys.argv),sys.pycache_prefix)
temp_before=tempfile.tempdir
os.environ.update(TEMP=str(temporary),TMP=str(temporary),TMPDIR=str(temporary),PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
    PYTEST_ADDOPTS='',PYTEST_PLUGINS='',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void')
tempfile.tempdir=None;sys.pycache_prefix=str(temporary/'fresh-bytecode')
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
timer=threading.Timer(max(.001,24-elapsed()),lambda:os._exit(124));timer.daemon=True;timer.start()
import psutil
process=psutil.Process()
resources=dict(samples=0,observed_peak_rss_bytes=0,observed_minimum_available_ram_bytes=None)
phase=['bootstrap'];denied=[];metadata={};nodes=[];counts=None;rc=None;error=None
null_writes=[0];null_reads=[0];optional_links=[0]


def check():
    need(elapsed()<24,'same24s worker deadline')
    info=process.memory_info();peak=max(int(info.rss),int(getattr(info,'peak_wset',0)))
    free=int(psutil.virtual_memory().available)
    resources['samples']+=1;resources['observed_peak_rss_bytes']=max(resources['observed_peak_rss_bytes'],peak)
    old=resources['observed_minimum_available_ram_bytes'];resources['observed_minimum_available_ram_bytes']=free if old is None else min(old,free)
    need(peak<=128*1024**2 and free>=1024**3,'metadata128/free1024 profile')


def reject(message,details=None):
    if len(denied)<8:denied.append(dict(phase=phase[0],message=message,details=details))
    raise RuntimeError(message)


allowed={safe(ROOT/n) for n in pins}|{PACKET}
runtimes=(ROOT/'.venv',Path(sys.base_prefix).resolve())
def owned(path):return path.is_relative_to(OUT) or path.is_relative_to(BASE)


def audit(kind,values):
    if kind=='import' and str(values[0]).split('.')[0] in ('torch','numpy','pandas','sklearn','scipy','modal','boto3'):
        reject('no actual scientific/solver/cloud imports')
    if kind=='subprocess.Popen' and phase[0]!='bootstrap':reject('no subprocess after real metadata bootstrap')
    if kind.startswith('socket.') and not(phase[0]=='bootstrap' and kind=='socket.gethostname'):reject('no network')
    if kind=='os.system' or kind.startswith('os.spawn'):reject('no system/spawn')
    if kind=='open' and values and not isinstance(values[0],int):
        name=os.fsdecode(values[0]);mode=values[1] or '';flags=values[2] if type(values[2]) is int else 0
        writing=any(c in mode for c in 'wax+') or bool(flags&(os.O_WRONLY|os.O_RDWR))
        if writing and name==os.devnull and phase[0]=='bootstrap':
            need(flags&os.O_RDWR and not flags&(os.O_CREAT|os.O_TRUNC|os.O_APPEND) and null_writes[0]<3,'exact bounded metadata NUL sink')
            null_writes[0]+=1;return
        if not writing and name==os.devnull and phase[0]=='pytest':
            caller=sys._getframe(1)
            try:exact=caller.f_code.co_filename==str(ROOT/'.venv/Lib/site-packages/_pytest/capture.py') and caller.f_code.co_name=='__init__' and caller.f_lineno==489
            finally:del caller
            need(exact and mode=='r' and flags==32896 and null_reads[0]<4,'pinned Pytest stdin NUL read')
            null_reads[0]+=1;return
        path=Path(name).absolute().resolve()
        if writing and not owned(path):reject('write outside owned metadata fixtures',dict(path=name,mode=mode,flags=flags))
        if not writing:
            source=None
            if path.suffix=='.pyc':
                try:source=Path(importlib.util.source_from_cache(str(path))).resolve()
                except ValueError:pass
            if path not in allowed and source not in allowed and not owned(path) and not any(path.is_relative_to(r) for r in runtimes):
                reject('read outside pinned source/runtime/owned fixture',dict(path=name,mode=mode,flags=flags))
    if kind in ('os.mkdir','os.remove','os.rmdir','os.rename'):
        paths=values[:2] if kind=='os.rename' else values[:1]
        if not all(owned(Path(v).absolute().resolve()) for v in paths):reject('mutation outside owned fixtures')
    if kind=='os.symlink':
        caller=sys._getframe(1);parent=caller.f_back
        try:
            exact=(phase[0]=='pytest' and len(values)==3 and values[2]==-1
                and caller.f_code.co_filename==str(Path(sys.base_prefix)/'Lib/pathlib/_local.py') and caller.f_code.co_name=='symlink_to'
                and parent.f_code.co_filename==str(ROOT/'.venv/Lib/site-packages/_pytest/pathlib.py') and parent.f_code.co_name=='_force_symlink' and parent.f_lineno==219)
        finally:del caller,parent
        paths=[Path(os.fsdecode(v)) for v in values[:2]]
        if exact and all(p.is_absolute() and '..' not in p.parts and p.resolve().is_relative_to(BASE) for p in paths):
            need(optional_links[0]<1024,'bounded denied optional Pytest links');optional_links[0]+=1
            raise PermissionError('optional Pytest link disabled before OS creation')
        reject('no actual symlink creation')


sys.addaudithook(audit)
try:
    check()
    helper=safe(ROOT/packet['metadata_helper']);raw=helper.read_bytes()
    need(hashlib.sha256(raw).hexdigest()==pins[packet['metadata_helper']],'exact bytes compiled for metadata helper')
    namespace=dict(__name__='checkpoint_metadata_bootstrap_only',__file__=str(helper))
    exec(compile(raw,str(helper),'exec'),namespace)
    namespace['native_windows_metadata'](check,metadata);write('native_metadata.json',metadata)
    phase[0]='pytest'
    import pytest
    from _pytest.junitxml import mangle_test_address
    class Plugin:
        def pytest_collection_finish(self,session):
            nodes.extend(item.nodeid for item in session.items)
            need(nodes==packet['expected_nodeids'] and len(nodes)==len(set(nodes))==38,'actual exact38 collection before bodies')
        def pytest_runtest_protocol(self,item,nextitem):check()
        def pytest_runtest_logreport(self,report):check()
    argv=['tests/akt/test_research_graph_cuda_checkpoint.py','--noconftest','-p','no:terminal','-p','no:cacheprovider',
        '-o','addopts=','--basetemp',str(BASE),'--log-file='+str(OUT/'pytest-file.log'),'--junitxml',str(OUT/'junit.xml')]
    need(not BASE.exists(),'fresh basetemp before Pytest deletion API')
    with PATH_OPEN(OUT/'pytest.log','x',encoding='utf-8') as log,redirect_stdout(log),redirect_stderr(log):
        rc=int(pytest.main(argv,plugins=[Plugin()]))
    cases=list(ET.parse(OUT/'junit.xml').iter('testcase'))
    counts=dict(tests=len(cases),failures=sum(len(list(c.iter('failure'))) for c in cases),
        errors=sum(len(list(c.iter('error'))) for c in cases),skipped=sum(len(list(c.iter('skipped'))) for c in cases))
    mapped=[]
    for node in nodes:
        names=mangle_test_address(node);mapped.append(('.'.join(names[:-1]),names[-1]))
    actual=[(c.get('classname'),c.get('name')) for c in cases]
    need(len(set(actual))==38 and set(actual)==set(mapped) and counts==dict(tests=38,failures=0,errors=0,skipped=0)
         and rc==0 and denied==[],'full38 physical IDs/0FES/RC0')
    namespace['require_metadata_closed'](metadata);check()
except BaseException as exc:error=dict(type=type(exc).__name__,message=str(exc))
finally:
    for name,value in env_before.items():
        if value is None:os.environ.pop(name,None)
        else:os.environ[name]=value
    sys.pycache_prefix=sys_before[4];tempfile.tempdir=temp_before
    restored=env_before=={n:os.environ.get(n) for n in keys} and tempfile.tempdir==temp_before
    restored=restored and sys_before==(sys.prefix,sys.executable,sys.dont_write_bytecode,list(sys.argv),sys.pycache_prefix) and Path.open is PATH_OPEN
    after={n:sha(safe(ROOT/n)) for n in pins};runtime_after={n:sha(Path(n)) for n in runtime}
    cold=not any(n.split('.')[0] in ('torch','numpy','pandas') for n in sys.modules)
    accepted=error is None and cold and restored and after==pins and runtime_after==runtime and elapsed()<24
    write('result.json',dict(status='ACCEPTED_CURRENT38_CHECKPOINT_METADATA_CHILD' if accepted else 'REJECTED_METADATA_KEEP_ALL',
        counts=counts,pytest_exit_code=rc,error=error,denied=denied,source_before=pins,source_after=after,
        runtime_before=runtime,runtime_after=runtime_after,scientific_modules_absent=cold,environment_and_sys_restored=restored,
        nodeids=nodes,resources=resources,optional_pytest_links_blocked=optional_links[0],elapsed_seconds=elapsed(),cap_seconds=24))
    if elapsed()>=24:write('postwrite_rejection.json',dict(elapsed_seconds=elapsed()));accepted=False
    timer.cancel()
raise SystemExit(0 if accepted else 1)
