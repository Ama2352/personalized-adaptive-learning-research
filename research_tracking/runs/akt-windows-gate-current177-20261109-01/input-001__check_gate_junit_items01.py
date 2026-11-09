"""ROOT worker54s cho99 focused fixtures, identity check trước test bodies."""
import time
START = time.perf_counter()
from pathlib import Path
import hashlib
import json
import os
import platform
import sys
import threading
import tempfile
import xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts/research'))
from windows_owned_worker import worker_gate,safe,bounded

PINS = {'scripts/akt/refresh_gate2.py':'8689c5b4737f4eae00459f4a3bc85c22206f58974274304fa4411e36f9acc055',
        'tests/akt/test_gate2_refresh.py':'268ace8716285c35db15caaae1efc819776795e3ef931f2e14f41b9cbe2a1e3c'}
COLLECTION = PREP/'gate-collection10/remaining/result.json'
COLLECTION_SHA = 'fd353373f4a7faf40d29643695bcb21d5b7252d1794eca7232c20c17ccbd76cd'
PACKET = PREP/'gate_junit_items01_packet.json'
PACKET_SHA = 'ce48d3d576c68503e84d56edb2d9b431d30aa3e7d28bd952e4ab87ddaa8b367a'
JUNIT_SHA = '557b8978c66b8010fafc50ada4bf56333f9927f31b2b5909fe4c1a9df1a3c0f0'
OUT = PREP/'gate-junit-items01'
BASE = PREP/'gji01'


def need(ok,reason):
    if not ok: raise ValueError(reason)


def sha(path): return hashlib.sha256(bounded(path,32*1024**2)).hexdigest()


def write(path,value):
    with safe(path).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def main():
    owner = worker_gate()
    need(not OUT.exists() and not BASE.exists(), 'exclusive outputs/fresh basetemp before pytest deletion API')
    safe(OUT).mkdir(exist_ok=False); safe(BASE)
    environment_before = dict(os.environ)
    temp_before = tempfile.tempdir
    runtime_temp = OUT/'runtime-temp'; runtime_temp.mkdir(exist_ok=False)
    for key in ('TEMP','TMP','TMPDIR'): os.environ[key] = str(runtime_temp)
    tempfile.tempdir = None
    before = {name:sha(ROOT/name) for name in PINS}
    need(before == PINS and sha(COLLECTION) == COLLECTION_SHA, 'reviewed source/collection pins')
    raw = json.loads(bounded(COLLECTION,8*1024**2))
    previous = [n for n in raw['nodeids'] if n.startswith('tests/akt/test_gate2_refresh.py::')]
    need(sha(PACKET) == PACKET_SHA,'exact source/nodeIDs packet')
    packet = json.loads(bounded(PACKET,65536))
    need(packet['source_pins'] == PINS and packet['old_nodeids'] == previous
         and len(previous) == len(set(previous)) == 77 and len(packet['added_nodeids']) == 22
         and not set(previous).intersection(packet['added_nodeids']), 'actual old77 plus explicit new22 IDs')
    expected = set(packet['expected_nodeids'])
    need(len(expected) == 99 and expected == set(previous+packet['added_nodeids']), 'exact99 population before bodies')
    import psutil
    need(psutil.virtual_memory().available >= 2*1024**3, '2GiB admission')
    resources = dict(samples=0,observed_peak_bytes=0,observed_minimum_available_ram_bytes=None)
    stop = threading.Event()
    def sample():
        memory = psutil.Process().memory_info()
        resources['observed_peak_bytes'] = max(resources['observed_peak_bytes'],memory.rss,getattr(memory,'peak_wset',0))
        available = int(psutil.virtual_memory().available)
        prior = resources['observed_minimum_available_ram_bytes']
        resources['observed_minimum_available_ram_bytes'] = available if prior is None else min(prior,available)
        resources['samples'] += 1
        need(resources['observed_peak_bytes'] <= 1024**3 and available >= 2*1024**3, 'observed1GiB/2GiB resource bounds')
    def watch():
        while not stop.wait(.1):
            try: sample()
            except BaseException as error:
                try: write(OUT/'resource-failure.json',dict(error=str(error),resources=resources))
                finally: os._exit(125)
    sample(); monitor = threading.Thread(target=watch,daemon=True); monitor.start()
    remaining = 54-(time.perf_counter()-START)
    need(remaining > 0,'worker54s exhausted in setup')
    timer = threading.Timer(remaining,lambda:os._exit(124)); timer.daemon=True; timer.start()
    attempted,commands = [],[]
    metadata_phase = [True]
    cmd = Path(os.environ['SystemRoot'])/'System32/cmd.exe'
    need(cmd.is_file() and not cmd.is_symlink() and not cmd.is_junction(),'actual systemcmd')
    def audit(event,values):
        if event == 'subprocess.Popen':
            fixed = os.path.normcase(os.path.abspath(str(cmd)))
            forms = {fixed.casefold()+' /c "ver"','"'+fixed.casefold()+'" /c "ver"'}
            if (metadata_phase[0] and len(commands)<3 and type(values[0]) is str and type(values[1]) is str
                    and os.path.normcase(os.path.abspath(values[0])) == fixed and values[1].strip().casefold() in forms):
                commands.append(dict(executable=values[0],command=values[1])); return
            attempted.append(event); raise RuntimeError('pure fixture subprocess denied after bounded metadata')
        if event == 'import' and str(values[0]).split('.')[0] in ('torch','numpy','pandas','sklearn','scipy','duckdb','modal','boto3','pyBKT'):
            attempted.append('import:'+str(values[0])); raise RuntimeError('heavy/model/cloud import denied')
        if event == 'os.system' or event.startswith('os.spawn') or event.startswith('socket.') and event!='socket.gethostname':
            attempted.append(event); raise RuntimeError('network/process denied')
        if event in ('open','os.listdir','os.scandir') and values and isinstance(values[0],(str,bytes,os.PathLike)):
            path = os.path.normcase(os.path.abspath(os.fsdecode(values[0])))
            for name in ('dataset','artifacts/bkt_baseline','artifacts/simulator/corpora','experiments','venv','.wsl'):
                protected = os.path.normcase(str(ROOT/name))
                if path == protected or path.startswith(protected+os.sep):
                    attempted.append('actual_data'); raise RuntimeError('actual/protected data denied')
    sys.addaudithook(audit)
    try: uname = platform.uname(); metadata = dict(system=uname.system,release=uname.release,version=uname.version,machine=uname.machine)
    finally: metadata_phase[0] = False
    metadata.update(commands=commands,phase_closed=True)
    sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'src'))
    os.chdir(ROOT)
    env_before = environment_before
    for key in list(os.environ):
        if key.startswith('PYTEST_'): os.environ.pop(key,None)
    os.environ.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTEST_ADDOPTS='',PYTEST_PLUGINS='')
    execution_env = dict(os.environ)
    class Collected:
        nodeids = []
        def pytest_collection_finish(self,session):
            self.nodeids = [item.nodeid for item in session.items]
            need(len(self.nodeids) == len(set(self.nodeids)) == 99 and set(self.nodeids) == expected,
                 'exact pinned99 collected identities required before test bodies')
    plugin = Collected()
    rc,errors,counts = None,[],None
    try:
        import pytest
        from contextlib import redirect_stdout,redirect_stderr
        need(not BASE.exists() and BASE.parent == PREP and BASE.resolve().is_relative_to(PREP.resolve()),'fresh owned physical basetemp before pytest')
        with (OUT/'pytest.log').open('x',encoding='utf-8') as log:
            with redirect_stdout(log),redirect_stderr(log):
                rc = int(pytest.main(['tests/akt/test_gate2_refresh.py','-q','-o','addopts=','-p','no:cacheprovider',
                    '--basetemp',str(BASE),'--junitxml',str(OUT/'junit.xml'),
                    '--log-file='+str(OUT/'pytest-file.log')],plugins=[plugin]))
    except BaseException as error: errors.append(dict(stage='pytest',type=type(error).__name__,message=str(error)))
    finally:
        test_environment_unchanged = dict(os.environ) == execution_env
        os.environ.clear(); os.environ.update(env_before)
        tempfile.tempdir = temp_before
        stop.set(); monitor.join(timeout=.5)
        try: sample()
        except BaseException as error: errors.append(dict(stage='final_resource',type=type(error).__name__,message=str(error)))
        try:
            tree = ET.parse(OUT/'junit.xml').getroot()
            counts = {k:sum(int(s.get(k,'0')) for s in tree.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
            need(len(list(tree.iter('testcase'))) == counts['tests'],'actual JUnit population')
            need(sha(ROOT/'.venv/Lib/site-packages/_pytest/junitxml.py') == JUNIT_SHA,'installed JUnit source')
            from _pytest.junitxml import mangle_test_address,bin_xml_escape
            names = []
            for nodeid in expected:
                pieces = mangle_test_address(nodeid); names.append(('.'.join(pieces[:-1]),bin_xml_escape(pieces[-1])))
            actual = [(v.get('classname'),v.get('name')) for v in tree.iter('testcase')]
            need(len(names) == len(set(names)) and len(actual) == len(set(actual)) and set(actual) == set(names),'exact99 JUnit identities')
        except BaseException as error: errors.append(dict(stage='junit',type=type(error).__name__,message=str(error)))
        after = {name:sha(ROOT/name) for name in PINS}
        heavy = [name for name in ('torch','numpy','pandas','sklearn','scipy','duckdb','modal','boto3','pyBKT') if name in sys.modules]
        accepted = (rc == 0 and not errors and counts == dict(tests=99,failures=0,errors=0,skipped=0)
            and len(plugin.nodeids) == len(expected) and set(plugin.nodeids) == expected and before == after == PINS
            and sha(COLLECTION) == COLLECTION_SHA and sha(PACKET) == PACKET_SHA and not heavy and not attempted and not monitor.is_alive()
            and test_environment_unchanged and dict(os.environ) == env_before and tempfile.tempdir is temp_before
            and time.perf_counter()-START < 54)
        result = dict(status='ACCEPTED_FOCUSED_GATE_FIX_PENDING_OUTER' if accepted else 'REJECTED_FOCUSED_GATE_FIX',
            counts=counts,pytest_exit_code=rc,errors=errors,source_before=before,source_after=after,
            actual_nodeids=plugin.nodeids,expected_nodeids=sorted(expected),forbidden_attempts=attempted,
            heavy_modules_loaded=heavy,owner=owner,native_os_metadata=metadata,resources=resources,
            monitor_stopped=not monitor.is_alive(),environment_restored=dict(os.environ)==env_before,
            temporary_cache_restored=tempfile.tempdir is temp_before,owned_runtime_temp=str(runtime_temp),packet_sha256=PACKET_SHA,
            test_environment_unchanged=test_environment_unchanged,
            elapsed_seconds=time.perf_counter()-START,worker_cap_seconds=54,
            scope_vi='99 explicit fixture identities, old77+new22. Real TempPathFactory/XML/filesystem, synthetic child reports.')
        write(OUT/'result.json',result)
        if time.perf_counter()-START >= 54:
            write(OUT/'postwrite-rejection.json',dict(status='REJECTED_WORKER_POSTWRITE_BUDGET')); accepted=False
        timer.cancel()
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__': main()
