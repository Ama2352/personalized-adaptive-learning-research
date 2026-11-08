from pathlib import Path
import hashlib,json,os,subprocess,sys,time,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[4]
base=ROOT/'artifacts/akt/local-tests';trial=sys.argv[1];out=base/f'linux-gate-tooling-trial-20261108-{trial}';out.mkdir(exist_ok=False)
paths=['scripts/akt/check_runtime.py','scripts/akt/refresh_gate2.py','tests/akt/test_runtime.py','tests/akt/test_gate2_refresh.py']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={n:sha(ROOT/n) for n in paths};copies=[]
for n in paths:
 src=ROOT/n;dst=out/(src.name+'.snapshot');dst.write_bytes(src.read_bytes());copies.append({'source':n,'copy':dst.name,'before':before[n],'after_copy':sha(dst)})
prior=sum(json.loads(p.read_text())['elapsed_seconds'] for p in base.glob('linux-gate-tooling-trial-20261108-*/run.json'))
if prior>=120:raise RuntimeError('cumulative targeted-suite budget exhausted')
cap=min(60,120-prior)
env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(ROOT/'src')+os.pathsep+str(ROOT/'third_party'))
n=int(env.get('GIT_CONFIG_COUNT','0'));env[f'GIT_CONFIG_KEY_{n}']='safe.directory';env[f'GIT_CONFIG_VALUE_{n}']=(ROOT/'artifacts/akt/dependencies/upstream').as_posix();env['GIT_CONFIG_COUNT']=str(n+1)
command=[str(ROOT/'.venv/Scripts/python.exe'),'-B','-m','pytest','tests/akt/test_runtime.py','tests/akt/test_gate2_refresh.py','-q','-p','no:cacheprovider','--basetemp',str(out/'t'),'--junitxml',str(out/'pytest.xml')]
started=time.perf_counter();timedout=False;rc=None;error=None
with (out/'pytest.log').open('xb') as stream:
 try:rc=subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=cap).returncode
 except subprocess.TimeoutExpired as e:timedout=True;error=repr(e)
elapsed=time.perf_counter()-started;after={n:sha(ROOT/n) for n in paths}
r={'command':command,'timeout_seconds':cap,'elapsed_seconds':elapsed,'cumulative_elapsed_seconds':prior+elapsed,'returncode':rc,'timed_out':timedout,'error':error,'optimizer_steps':0,'model_fit_calls':0,'scope':'runtime public-packaging/Gate2 lock tooling; no optimizer/model fit','source_sha256_before':before,'source_sha256_after':after,'all_sources_unchanged':before==after,'copy_inventory':copies}
if (out/'pytest.xml').exists():r['junit']=[s.attrib for s in ET.parse(out/'pytest.xml').getroot().iter('testsuite')]
(out/'run.json').write_text(json.dumps(r,indent=2)+'\n');(out/'run_controller.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({k:r[k] for k in ('returncode','timed_out','elapsed_seconds','cumulative_elapsed_seconds','all_sources_unchanged','junit') if k in r},indent=2))
