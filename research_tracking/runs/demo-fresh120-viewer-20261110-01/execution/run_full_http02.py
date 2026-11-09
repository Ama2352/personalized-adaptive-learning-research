"""Kiểm toàn module demo bằng HTTP local, hard timeout cho subprocess test."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

START = time.monotonic()
ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
FILES = ('src/research_demo/__main__.py','src/research_demo/evidence.py','src/research_demo/server.py',
    'src/research_demo/static/index.html','src/research_demo/static/demo.js','tests/demo/test_viewer.py')
assert Path(sys.prefix).resolve()==ROOT/'.venv'


def hashes():
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES}


before = hashes()
environment = os.environ.copy()
environment['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
base = [sys.executable,'-B','-m','pytest','tests/demo/test_viewer.py','-q','-p','no:cacheprovider']
collection_log = HERE/'http02-collection.log'
stdout_log,stderr_log = HERE/'http02-stdout.log',HERE/'http02-stderr.log'
xml = HERE/'http02-junit.xml'
receipt = HERE/'http02-receipt.json'
assert not any(p.exists() for p in (collection_log,stdout_log,stderr_log,xml,receipt,HERE/'http02-temp'))
error = None
code = None
collected = []
counts = None
try:
    with collection_log.open('xb') as output:
        collect = subprocess.run(base+['--collect-only'],cwd=ROOT,env=environment,
            stdout=output,stderr=subprocess.STDOUT,timeout=min(15,58-(time.monotonic()-START)))
    assert collect.returncode==0,'collection failed'
    collected=[line for line in collection_log.read_text(encoding='utf-8').splitlines()
               if line.startswith('tests/demo/test_viewer.py::')]
    assert collected and len(collected)==len(set(collected))
    with stdout_log.open('xb') as output,stderr_log.open('xb') as errors:
        result=subprocess.run(base+['--basetemp',str(HERE/'http02-temp'),'--junitxml',str(xml)],
            cwd=ROOT,env=environment,stdout=output,stderr=errors,timeout=58-(time.monotonic()-START))
    code=result.returncode
    cases=list(ET.parse(xml).getroot().iter('testcase'))
    actual=[node.attrib['classname'].replace('.','/')+'.py::'+node.attrib['name'] for node in cases]
    assert actual==collected,'actual physical cases differ from collection'
    counts=dict(tests=len(cases),failures=sum(c.find('failure') is not None for c in cases),
        errors=sum(c.find('error') is not None for c in cases),skipped=sum(c.find('skipped') is not None for c in cases))
    assert code==0 and counts==dict(tests=len(collected),failures=0,errors=0,skipped=0)
except Exception as exc:
    error=dict(type=type(exc).__name__,message=str(exc))
after=hashes()
elapsed=time.monotonic()-START
accepted=error is None and before==after and elapsed<60
receipt.write_text(json.dumps(dict(accepted=accepted,counts=counts,collected_count=len(collected),
    returncode=code,error=error,source_before=before,source_after=after,elapsed_seconds=elapsed,
    whole_seconds=60,scope='Actual localhost HTTP unit tests, no browser/NN/research simulations.',
    resource_scope='Subprocess wall timeout, no RAM quota claim.',
    command=base),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(accepted=accepted,counts=counts,error=error,elapsed_seconds=elapsed)))
raise SystemExit(0 if accepted else 1)
