"""Kiểm notebook local: extraction/export thật, GPU và setup được giả lập rõ."""
import ast
import base64
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import pathlib
import platform
import subprocess
import sys
import types
from unittest.mock import patch
import uuid
import zipfile

root=Path.cwd()
notebook=json.loads((root/'notebooks/akt_colab_synthetic.ipynb').read_text(encoding='utf-8'))
sources={c['id']:''.join(c['source']) for c in notebook['cells'] if c['cell_type']=='code'}
for source in sources.values():ast.parse(source)
assert all(not c.get('outputs') and c.get('execution_count') is None for c in notebook['cells'])
for source in sources.values():
    for node in ast.walk(ast.parse(source)):
        if isinstance(node,ast.ImportFrom):assert not (node.module or '').startswith('google.colab')
        if isinstance(node,ast.Import):assert not any(alias.name.startswith('google.colab') for alias in node.names)
work=root/'artifacts/akt/local-tests'/('vscode-notebook-'+uuid.uuid4().hex[:12]);work.mkdir()
PathClass=type(root)
def mapped_path(*args):
    return work/'content' if args==('/content',) else PathClass(*args)
(work/'content').mkdir()
records=[]
def check(name,fn):
    fn();records.append({'case':name,'status':'PASS'})
def execute(name,namespace):exec(compile(sources[name],'<'+name+'>','exec'),namespace)
def raises(kind,fn):
    try:fn()
    except kind:return
    raise AssertionError('expected '+kind.__name__)
def namespace():
    return {'Path':mapped_path,'PurePosixPath':PurePosixPath,'base64':base64,'hashlib':hashlib,
        'io':io,'json':json,'uuid':uuid,'zipfile':zipfile,'os':__import__('os'),
        'subprocess':subprocess,'sys':sys,'COLAB_CONNECTION_OK':True,
        'connection_report':{'status':'MOCK_CONNECTED_GPU','scope':'local harness only; not actual GPU'}}

def connection(mode):
    fake=types.SimpleNamespace(__version__='MOCK_ONLY',version=types.SimpleNamespace(cuda='MOCK'),
        cuda=types.SimpleNamespace(is_available=lambda:mode=='gpu',get_device_name=lambda i:'MOCK_GPU'))
    ns={}
    with patch.dict(sys.modules,{'torch':fake}),patch.object(sys,'platform','win32' if mode=='windows' else 'linux'),patch.object(pathlib,'Path',mapped_path),patch.object(platform,'platform',lambda:'MOCK_PLATFORM'):
        if mode=='gpu':execute('akt-connection',ns);assert ns['COLAB_CONNECTION_OK']
        else:raises(RuntimeError,lambda:execute('akt-connection',ns));assert not ns['COLAB_CONNECTION_OK']
for mode in ('windows','cpu','gpu'):check('connection_'+mode,lambda mode=mode:connection(mode))

valid=namespace();execute('akt-bootstrap',valid)
assert valid['SOURCE_READY'] and len(valid['manifest']['files'])==139
for name,digest in valid['manifest']['files'].items():assert hashlib.sha256((valid['ROOT']/name).read_bytes()).hexdigest()==digest
assert not (valid['ROOT']/'dataset').exists()
records.append({'case':'real_embedded139file_extraction_and_hashes','status':'PASS'})
original_bundle=base64.b64decode(valid['BUNDLE_BASE64'],validate=True)
assert hashlib.sha256(original_bundle).hexdigest()==valid['EXPECTED_BUNDLE_SHA256']
def payload_variant(case):
    with zipfile.ZipFile(io.BytesIO(original_bundle)) as archive:
        entries={name:archive.read(name) for name in archive.namelist()}
    manifest=json.loads(entries['BUNDLE_MANIFEST.json'])
    if case=='unsafe':
        entries['../escape.py']=b'never execute';manifest['files']['../escape.py']=hashlib.sha256(entries['../escape.py']).hexdigest()
    if case=='source_corrupt':entries['scripts/akt/synthetic_recovery_probe.py']+=b'changed'
    if case=='unexpected':entries['extra.txt']=b'extra'
    if case=='missing_probe':
        del entries['scripts/akt/synthetic_recovery_probe.py'];del manifest['files']['scripts/akt/synthetic_recovery_probe.py']
    entries['BUNDLE_MANIFEST.json']=json.dumps(manifest).encode()
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,data in entries.items():archive.writestr(name,data)
    return stream.getvalue()
class Substitute(ast.NodeTransformer):
    def __init__(self,payload,correct_digest):self.payload=payload;self.correct=correct_digest
    def visit_Assign(self,node):
        if any(isinstance(t,ast.Name) and t.id=='BUNDLE_BASE64' for t in node.targets):node.value=ast.Constant(base64.b64encode(self.payload).decode())
        if self.correct and any(isinstance(t,ast.Name) and t.id=='EXPECTED_BUNDLE_SHA256' for t in node.targets):node.value=ast.Constant(hashlib.sha256(self.payload).hexdigest())
        return node
def rejected_payload(case):
    payload=original_bundle+b'tamper' if case=='bundle_hash' else payload_variant(case)
    tree=ast.fix_missing_locations(Substitute(payload,case!='bundle_hash').visit(ast.parse(sources['akt-bootstrap'])))
    ns={**valid,'SOURCE_READY':True}
    before=set((work/'content').iterdir())
    raises(ValueError,lambda:exec(compile(tree,'<mutated-fixture-bootstrap>','exec'),ns))
    assert not ns['SOURCE_READY'] and set((work/'content').iterdir())==before
    assert not (work/'escape.py').exists()
for case in ('bundle_hash','unsafe','source_corrupt','unexpected','missing_probe'):
    check('reject_'+case,lambda case=case:rejected_payload(case))
check('bootstrap_requires_connection',lambda:raises(RuntimeError,lambda:execute('akt-bootstrap',{**namespace(),'COLAB_CONNECTION_OK':False})))

def setup_case(case):
    ns=namespace();execute('akt-bootstrap',ns)
    commands=[]
    def run(command,**kwargs):
        commands.append(command)
        if case=='timeout':raise subprocess.TimeoutExpired(command,1)
        kwargs['stdout'].write(b'MOCK_SETUP_ONLY\n')
        return subprocess.CompletedProcess(command,0)
    fake=types.SimpleNamespace(run=run,STDOUT=subprocess.STDOUT,
        check_output=lambda *a,**k:json.dumps(['duckdb']))
    ns.update(subprocess=fake,CPU_PORTABILITY_OK=True,CUDA_LIFECYCLE_OK=True,SETUP_OK=True)
    if case=='stale_source':ns['SOURCE_READY']=False
    if case in ('timeout','stale_source'):
        raises(subprocess.TimeoutExpired if case=='timeout' else RuntimeError,lambda:execute('akt-setup',ns))
        assert not ns['SETUP_OK'] and not ns['CPU_PORTABILITY_OK'] and not ns['CUDA_LIFECYCLE_OK']
        assert len(commands)==(1 if case=='timeout' else 0)
        if case=='timeout':assert json.loads((ns['OUTPUT']/'setup-status.json').read_text())['status']=='FAILED'
    else:
        execute('akt-setup',ns);assert ns['SETUP_OK']
        installs=[cmd for cmd in commands if 'install' in cmd]
        assert len(installs)==1 and installs[0][0]==str(ns['ROOT']/'.venv/bin/python')
        assert commands[0][1:]==['-m','venv','--without-pip','--system-site-packages',str(ns['ROOT']/'.venv')]
        assert any('sysconfig.get_path' in str(cmd) and 'sys.prefix' in str(cmd) for cmd in commands)
        assert any(cmd[-1]=='01b7e8d7d7c862cabc9467108e3e7f2555653a88' for cmd in commands)
for case in ('timeout','stale_source','venv_only_success'):check('setup_'+case,lambda case=case:setup_case(case))

def cpu_case(case):
    ns=namespace();execute('akt-bootstrap',ns)
    calls=[]
    def run(command,**kwargs):
        calls.append(command);assert kwargs['timeout']==600 and kwargs['env']['CUDA_VISIBLE_DEVICES']==''
        kwargs['stdout'].write('MOCK_CPU_TESTS_ONLY\n')
        (ns['OUTPUT']/'cpu-tests.xml').write_text('<testsuites><testsuite tests="'+('0' if case=='empty' else '3')+'" failures="0" errors="0" skipped="0"/></testsuites>')
        return subprocess.CompletedProcess(command,0)
    ns.update(subprocess=types.SimpleNamespace(run=run,STDOUT=subprocess.STDOUT),AKT_PY='MOCK',ENV={},SETUP_OK=case!='missing_setup')
    if case=='pass':execute('akt-cpu',ns);assert ns['CPU_PORTABILITY_OK']
    else:
        raises(RuntimeError,lambda:execute('akt-cpu',ns));assert not ns['CPU_PORTABILITY_OK']
        if case=='missing_setup':assert not calls
for case in ('missing_setup','empty','pass'):check('cpu_'+case,lambda case=case:cpu_case(case))
for cellname in ('akt-lifecycle','akt-recovery'):
    check(cellname+'_requires_gates',lambda cellname=cellname:raises(RuntimeError,lambda:execute(cellname,{'CPU_PORTABILITY_OK':False,'CUDA_LIFECYCLE_OK':False})))

def export_case():
    ns=namespace();execute('akt-bootstrap',ns)
    (ns['OUTPUT']/'failure.log').write_text('MOCK_FAILURE_ONLY\n')
    run=ns['ROOT']/'experiments/akt/results/mock';run.mkdir(parents=True)
    (run/'checkpoint.pt').write_bytes(b'MOCK_BYTES_NOT_A_TORCH_CHECKPOINT')
    ns['RUN']=run
    execute('akt-export',ns)
    archive_path=ns['archive_path'];digest=hashlib.sha256(archive_path.read_bytes()).hexdigest()
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        manifest=json.loads(archive.read('RESULT_MANIFEST.json'))
        assert not manifest['cpu_portability_pass'] and not manifest['cuda_lifecycle_pass']
        assert 'failure.log' in manifest['files'] and 'synthetic-run/checkpoint.pt' in manifest['files']
        for name,expected in manifest['files'].items():assert hashlib.sha256(archive.read(name)).hexdigest()==expected
        assert set(archive.namelist())==set(manifest['files'])|{'RESULT_MANIFEST.json'}
    assert archive_path.with_suffix('.zip.sha256').read_text().startswith(digest)
    raises(FileExistsError,lambda:execute('akt-export',ns))
    assert hashlib.sha256(archive_path.read_bytes()).hexdigest()==digest
check('real_failure_export_all_file_hashes_and_no_overwrite',export_case)
check('export_requires_workspace',lambda:raises(RuntimeError,lambda:execute('akt-export',{})))
report={'status':'PASS','cases':records,'case_count':len(records),'code_cells_ast_valid':len(sources),
        'embedded_bundle_sha256':hashlib.sha256(original_bundle).hexdigest(),
        'notebook_sha256':hashlib.sha256((root/'notebooks/akt_colab_synthetic.ipynb').read_bytes()).hexdigest(),
        'scope':'Real local embedded source extraction/ZIP export; mocked GPU/setup/CPU guards. No actual CUDA/Colab execution.'}
(root/'artifacts/akt/local-tests/vscode-notebook-v12-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
