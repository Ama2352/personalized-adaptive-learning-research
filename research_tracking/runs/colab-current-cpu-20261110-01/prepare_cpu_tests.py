"""Tạo lượt kiểm AKT baseline CPU, tối đa 450 giây, chỉ fixtures."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
code = '''import hashlib, json, os, subprocess, time, xml.etree.ElementTree as ET
assert SETUP_OK is True
modules = ['test_model.py','test_checkpoint.py','test_upstream_parity.py',
           'test_training.py','test_online_simulator.py','test_windows.py','test_encoding.py']
modules = ['tests/akt/'+name for name in modules]
assert all((ROOT/name).is_file() for name in modules)
before = {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in manifest['files']}
assert before == manifest['files']
env = dict(ENV, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
           PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
command = [AKT_PY,'-B','-m','pytest',*modules,'-q','-p','no:cacheprovider',
           '--basetemp',str(ROOT/'pytest-baseline'), '--junitxml',str(OUTPUT/'baseline-tests.xml')]
(OUTPUT/'baseline-command.json').write_text(json.dumps(command))
started = time.monotonic()
status = {'status':'FAILED', 'scope':'Seven baseline fixture modules on inherited Colab CPU runtime; not full Gate or research training'}
try:
    with (OUTPUT/'baseline-tests.log').open('xb') as log:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=450)
    suites = ET.parse(OUTPUT/'baseline-tests.xml').getroot()
    cases = list(suites.iter('testcase'))
    counts = {tag:sum(1 for c in cases if c.find(tag) is not None) for tag in ('failure','error','skipped')}
    after = {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in manifest['files']}
    assert before == after, 'source drift'
    status.update(returncode=result.returncode, tests=len(cases), counts=counts, source_unchanged=True)
    if result.returncode == 0 and cases and not any(counts.values()): status['status']='PASS'
except BaseException as exc:
    status.update(error_type=type(exc).__name__, error=str(exc))
finally:
    status['elapsed_seconds']=time.monotonic()-started
    (OUTPUT/'baseline-status.json').write_text(json.dumps(status,indent=2))
print(json.dumps(status,indent=2))
print((OUTPUT/'baseline-tests.log').read_text()[-6000:])
'''
compile(code, '<colab-baseline>', 'exec')
(ROOT/'artifacts/akt/colab/requests/current-cpu-baseline-add.json').write_text(
    json.dumps(dict(cellIndex=3, language='python', code=code)), encoding='utf-8')
