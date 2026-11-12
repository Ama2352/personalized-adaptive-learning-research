"""CPU8GiB cho16ca native A1 vàchẩn đoán checkpoint, giới hạn600giây VM."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path('/opt/kltn')
RUN = 'modal-junyi-numerical-cpu-20261112-03'
OUTPUT = Path('/cpu-evidence')/RUN
OUTPUT.mkdir(parents=True,exist_ok=False)
started = time.monotonic()


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def unpack(path,expected):
    if sha(path)!=expected:
        raise ValueError('Pinned input archive changed')
    with zipfile.ZipFile(path) as saved:
        pins = json.loads(saved.read('MANIFEST.json'))['files']
        if set(saved.namelist())!=set(pins)|{'MANIFEST.json'}:
            raise ValueError('Input archive members differ from inventory')
        for name,entry in pins.items():
            relative = PurePosixPath(name)
            if (relative.is_absolute() or '..' in relative.parts or '\\' in name
                    or relative.parts[0] in ('dataset','venv','.wsl','.git')
                    or relative.parts[:2]==('artifacts','bkt_baseline')):
                raise ValueError('Unsafe or protected input member')
            raw = saved.read(name)
            digest = entry if isinstance(entry,str) else entry['sha256']
            if hashlib.sha256(raw).hexdigest()!=digest:
                raise ValueError('Input member digest mismatch')
            target = ROOT.joinpath(*relative.parts)
            if not target.resolve().is_relative_to(ROOT.resolve()):
                raise ValueError('Input member escapes project')
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw)
    return {name:(entry if isinstance(entry,str) else entry['sha256']) for name,entry in pins.items()}


def execute(command,log_name,environment,*,max_seconds):
    remaining = 520-(time.monotonic()-started)-15
    if remaining<=0:
        raise TimeoutError('CPU03 worker execution budget exhausted')
    with (OUTPUT/log_name).open('xb') as stream:
        completed = subprocess.run(command,cwd=ROOT,env=environment,stdout=stream,
            stderr=subprocess.STDOUT,timeout=min(max_seconds,remaining))
    return completed.returncode


result = dict(status='FAILED',run_id=RUN,gpu_requested=False,main_training=False,
              full_gate_refreshed=False,max_vm_seconds=600,budget_reserved_usd=.15)
try:
    request = json.loads(Path('/opt/junyi-cpu03-request.json').read_text())
    if request['run_id']!=RUN or request['reserved_usd']>.15:
        raise ValueError('CPU03 request scope mismatch')
    if sha(Path(__file__))!=request['worker_sha256'] or sha(Path('/opt/junyi_cpu_diagnostic.py'))!=request['diagnostic_sha256']:
        raise ValueError('Worker or diagnostic source changed')
    inventory = {}
    for name in ('source','data','checkpoint'):
        incoming = unpack(Path('/opt/junyi-'+name+'03.zip'),request['archives'][name]['sha256'])
        if set(inventory)&set(incoming):
            raise ValueError('Overlapping input packet members')
        inventory.update(incoming)
    environment = dict(os.environ,CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',
        OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1',
        PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONPATH=str(ROOT/'src'),
        GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_COUNT='3',
        GIT_CONFIG_KEY_0='core.fsmonitor',GIT_CONFIG_VALUE_0='false',
        GIT_CONFIG_KEY_1='safe.directory',GIT_CONFIG_VALUE_1=str(ROOT/'artifacts/akt/dependencies/upstream'),
        GIT_CONFIG_KEY_2='core.autocrlf',GIT_CONFIG_VALUE_2='false',GIT_OPTIONAL_LOCKS='0',
        GIT_TERMINAL_PROMPT='0',GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__',
        CPU_DIAG_OUTPUT=str(OUTPUT/'numerical'))
    interpreter = str(ROOT/'.venv/bin/python')
    command = [interpreter,'-B','-m','pytest','-q','-p','no:cacheprovider',
        'tests/akt/test_junyi_graph_model.py',
        '--basetemp='+str(ROOT/'artifacts/akt/local-tests'/RUN),
        '--junitxml='+str(OUTPUT/'a1-native-tests.xml')]
    try:
        result['a1_test_returncode'] = execute(command,'a1-native-tests.log',environment,max_seconds=240)
    except subprocess.TimeoutExpired:
        result['a1_test_returncode'] = 'TIMEOUT'
    xml = OUTPUT/'a1-native-tests.xml'
    if xml.is_file():
        tree = ET.parse(xml).getroot()
        suites = [tree] if tree.tag=='testsuite' else list(tree.iter('testsuite'))
        counts = {key:sum(int(suite.attrib.get(key,0)) for suite in suites)
                  for key in ('tests','failures','errors','skipped')}
        counts['passed'] = counts['tests']-counts['failures']-counts['errors']-counts['skipped']
        result['a1_test_counts'] = counts
    result['diagnostic_returncode'] = execute([interpreter,'-B','/opt/junyi_cpu_diagnostic.py'],
        'numerical-controller.log',environment,max_seconds=240)
    numerical_result = OUTPUT/'numerical/diagnostic-result.json'
    if numerical_result.is_file():
        numerical = json.loads(numerical_result.read_text())
        result['numerical_status'] = numerical['status']
    result['input_files_unchanged'] = all(sha(ROOT/name)==digest for name,digest in inventory.items())
    passed = (result.get('a1_test_returncode')==0 and result.get('a1_test_counts',{}).get('passed')==16
              and result.get('diagnostic_returncode')==0
              and result.get('numerical_status')=='DIAGNOSTIC_COMPLETE_UNADMITTED'
              and result['input_files_unchanged'])
    result['status'] = 'CPU03_DIAGNOSTICS_COMPLETE_UNADMITTED' if passed else 'CPU03_RESULTS_REQUIRE_REVIEW'
except BaseException as error:
    result.update(error_type=type(error).__name__,error=str(error))
    (OUTPUT/'failure.log').write_text(traceback.format_exc())
finally:
    result['elapsed_seconds'] = time.monotonic()-started
    (OUTPUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    files = sorted(path for path in OUTPUT.rglob('*') if path.is_file())
    inventory = {}
    with zipfile.ZipFile(OUTPUT/'artifacts.zip','x',zipfile.ZIP_DEFLATED) as saved:
        for path in files:
            name = path.relative_to(OUTPUT).as_posix()
            inventory[name] = dict(bytes=path.stat().st_size,sha256=sha(path))
            saved.write(path,name)
        saved.writestr('SHA256.json',json.dumps(inventory,indent=2)+'\n')
    result.update(archive_sha256=sha(OUTPUT/'artifacts.zip'),archive_bytes=(OUTPUT/'artifacts.zip').stat().st_size)
print(json.dumps(result),flush=True)
raise SystemExit(0 if result['status']=='CPU03_DIAGNOSTICS_COMPLETE_UNADMITTED' else 1)
