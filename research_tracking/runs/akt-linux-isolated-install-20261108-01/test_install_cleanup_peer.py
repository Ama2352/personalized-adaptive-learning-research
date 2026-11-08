"""Peer mock tests; chỉ exec AST Stage với virtual paths/processes, không chạy stage."""
import ast
import hashlib
import io
import json
from pathlib import Path
import types

path=Path(__file__).parent/'install_stage.py'
expected='28927535b16b66167e4c71a42a406d9a1c138b388806df093434cba6c0010a87'
assert hashlib.sha256(path.read_bytes()).hexdigest()==expected
tree=ast.parse(path.read_bytes())
node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Stage')
calls=[]
class Sig:
    def __init__(self,name):self.name=name
signal=types.SimpleNamespace(SIGTERM=Sig('SIGTERM'),SIGKILL=Sig('SIGKILL'))
os=types.SimpleNamespace(getpgrp=lambda:800,killpg=lambda pgid,sig:calls.append((pgid,sig.name)))
class Expired(Exception):pass
class Proc:
    pid=900;returncode=0
    def poll(self):return 0
    def wait(self,timeout):return 0
subprocess=types.SimpleNamespace(TimeoutExpired=Expired,Popen=lambda *a,**k:Proc())
class VirtualPath:
    def __truediv__(self,name):return self
    def open(self,*a,**k):return io.BytesIO()
    def read_text(self,**k):return 'ok'
clock=types.SimpleNamespace(monotonic=lambda:0.)
namespace={'os':os,'signal':signal,'subprocess':subprocess,'time':clock,'ATTEMPT':VirtualPath(),'ROOT':VirtualPath()}
exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),namespace)
Stage=namespace['Stage'];stage=Stage.__new__(Stage);stage.cleanup=[]
entry={'pgid':900};stage.kill_owned(entry);stage.kill_owned(entry)
assert len(calls)==2 and entry['cleanup_attempted'] and entry['group_cleanup_completed']
def denied(*args):raise PermissionError('synthetic denial')
os.killpg=denied;entry={'pgid':901};stage.kill_owned(entry);stage.kill_owned(entry)
assert entry['cleanup_attempted'] and entry['group_cleanup_completed'] is False
os.killpg=lambda *args:(_ for _ in ()).throw(ProcessLookupError())
entry={'pgid':902};stage.kill_owned(entry);assert entry['group_cleanup_completed']
os.killpg=lambda *args:(_ for _ in ()).throw(AssertionError('must not signal controller'))
entry={'pgid':800};stage.kill_owned(entry);assert entry['group_cleanup_completed'] is False
stage=Stage.__new__(Stage);stage.check=lambda:None;stage.deadline=100.;stage.env={};stage.source_sha=expected;stage.children=[];stage.cleanup=[]
def failed_cleanup(entry):entry.update(cleanup_attempted=True,group_cleanup_completed=False)
stage.kill_owned=failed_cleanup
try:stage.run('fixture',['never-starts-real-process'],20)
except RuntimeError as error:assert 'CLEANUP_UNVERIFIED' in str(error)
else:raise AssertionError('cleanup failure accepted')
assert stage.children[0]['returncode']==0 and stage.children[0]['elapsed_including_cleanup_seconds']==0.
stage=Stage.__new__(Stage);stage.check=lambda:None;stage.deadline=100.;stage.env={};stage.source_sha=expected;stage.children=[];stage.cleanup=[]
stage.kill_owned=lambda entry:entry.update(cleanup_attempted=True,group_cleanup_completed=True)
assert stage.run('fixture',['never-starts-real-process'],20)=='ok'
assert hashlib.sha256(path.read_bytes()).hexdigest()==expected
print(json.dumps({'status':'PASS_MOCKED_CLEANUP_ONLY','checks':6,'source_sha256':expected,
                 'real_stage_subprocesses':0,'installs':0,'network_calls':0,'model_calls':0}))
