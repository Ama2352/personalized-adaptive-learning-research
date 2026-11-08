"""Controller kiểm synthetic offline, hard timeout60s; không gọi discovery main."""
import hashlib,json,os,subprocess,sys,time,xml.etree.ElementTree as E
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
OUT=HERE/'trial01'
inputs=[HERE/'discovery.py',HERE/'test_discovery.py',HERE/'discovery_profile01.json',HERE.parent/'fresh_install_verified_profile_v3.py']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={p.relative_to(ROOT).as_posix():sha(p) for p in inputs}
for p in inputs:
    target=OUT/(p.name+'.snapshot');target.open('xb').write(p.read_bytes());assert sha(target)==sha(p)
env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
cmd=[sys.executable,'-B','-m','pytest',str(HERE/'test_discovery.py'),'-q','-p','no:cacheprovider','--basetemp',str(OUT/'pytest-tmp'),'--junitxml',str(OUT/'pytest.xml')]
start=time.monotonic();error=None;rc=None
with (OUT/'pytest.log').open('xb') as f:
    try:rc=subprocess.run(cmd,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
    except BaseException as e:error=type(e).__name__+': '+str(e)
elapsed=time.monotonic()-start
counts=[]
if (OUT/'pytest.xml').exists():counts=[dict(x.attrib) for x in E.parse(OUT/'pytest.xml').getroot().iter('testsuite')]
after={p.relative_to(ROOT).as_posix():sha(p) for p in inputs}
result={'status':'PASS' if rc==0 and before==after and elapsed<=60 else 'FAILED_RETAIN_LOGS','returncode':rc,'error':error,'controller_seconds':elapsed,'timeout_seconds':60,'command':cmd,'junit_suites':counts,'source_sha256_before':before,'source_sha256_after':after,'model_or_target_probe_calls':0,'optimizer_steps':0,'network_install_gpu_calls':0,'limits':'Synthetic filesystem/snapshot/AST/CLI-parser tests only; no actual Linux discovery or target subprocess.'}
(OUT/'run.json').open('x',encoding='utf-8').write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result))
raise SystemExit(0 if result['status']=='PASS' else 1)
