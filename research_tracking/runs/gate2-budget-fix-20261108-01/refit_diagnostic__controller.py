from pathlib import Path
import datetime as dt,hashlib,json,os,platform,subprocess,sys,time,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
PY=ROOT/'.venv/Scripts/python.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():
 paths=sorted((ROOT/'src/knowledge_tracing/akt').glob('*.py'))+[ROOT/'tests/akt/test_refit_recovery.py',ROOT/'requirements-akt.lock.txt',ROOT/'artifacts/akt/dependencies/upstream/akt.py']
 return {str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in paths}
def dump(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
before=sources();parent_env={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','CUDA_VISIBLE_DEVICES')}
env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(ROOT/'src')+os.pathsep+str(ROOT/'third_party'))
n=int(env.get('GIT_CONFIG_COUNT','0'));env[f'GIT_CONFIG_KEY_{n}']='safe.directory';env[f'GIT_CONFIG_VALUE_{n}']=(ROOT/'artifacts/akt/dependencies/upstream').as_posix();env['GIT_CONFIG_COUNT']=str(n+1)
bootstrap=r"""from pathlib import Path
import json,os,sys,torch
out=Path(sys.argv[1])
(out/'process_metadata.json').write_text(json.dumps({'python':sys.version,'torch':torch.__version__,'threads':torch.get_num_threads(),'interop_threads':torch.get_num_interop_threads(),'cpu_count':os.cpu_count(),'cuda_available':torch.cuda.is_available(),'cuda_initialized':torch.cuda.is_initialized(),'environment':{k:os.environ.get(k) for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','CUDA_VISIBLE_DEVICES']}},indent=2)+'\\n')
import pytest
raise SystemExit(pytest.main(['tests/akt/test_refit_recovery.py::test_refit_recovery_matches_uninterrupted_weights_adam_rng','-q','-p','no:cacheprovider','--basetemp',str(out/'t'),'--junitxml',str(out/'pytest.xml')]))
"""
(OUT/'child.py').write_text(bootstrap,encoding='utf-8')
command=[str(PY),'-B',str(OUT/'child.py'),str(OUT)]
started=time.perf_counter();utc_start=dt.datetime.now(dt.timezone.utc).isoformat();timed_out=False;error=None;rc=None
with (OUT/'pytest.log').open('xb') as stream:
 try:rc=subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=45).returncode
 except subprocess.TimeoutExpired as e:timed_out=True;error=repr(e)
 except Exception as e:error=repr(e)
elapsed=time.perf_counter()-started;after=sources()
receipt={'schema_version':1,'role':'isolated CPU synthetic exact-test diagnosis, not Gate2 publication','command':command,'parent_environment':parent_env,'unconstrained_current_torch_metadata':{'threads':12,'interop_threads':12,'cpu_count':16,'torch':'2.7.1+cpu','cuda_available':False,'cuda_initialized':False,'scope':'separate import-only current process; not historical Gate20 metadata'},'timeout_seconds':45,'elapsed_seconds':elapsed,'utc_started':utc_start,'utc_finished':dt.datetime.now(dt.timezone.utc).isoformat(),'returncode':rc,'timed_out':timed_out,'error':error,'source_sha256_before':before,'source_sha256_after':after,'all_sources_unchanged':before==after,'source_drift_keys':[k for k in before.keys()|after.keys() if before.get(k)!=after.get(k)],'host_suspend_status':'UNKNOWN','system_power_event_query':{'command_scope':'System Microsoft-Windows-Kernel-Power IDs42/107 max10 timestamps only','status':'unavailable','exception_type':'System.UnauthorizedAccessException','message':'Attempted to perform an unauthorized operation.','escalation':False},'limitations':['one bounded exact refit test, no full suite','thread-limited run differs from historical unspecified thread environment','no conclusion of suspend or regression cause','no source/config/Gate pointer edits by diagnostic']}
if (OUT/'pytest.xml').exists():receipt['junit']=[s.attrib for s in ET.parse(OUT/'pytest.xml').getroot().iter('testsuite')]
dump('run.json',receipt)
dump('artifact_sha256.json',{p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='artifact_sha256.json'})
print(json.dumps({k:receipt[k] for k in ('returncode','timed_out','elapsed_seconds','all_sources_unchanged','source_drift_keys','junit') if k in receipt},indent=2))
