"""Hai focused invocations chia chung cap10s mới; không reset lịch sử117.8s."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
W=Path(__file__).resolve().parent;OUT=W/'scheme-checks02';OUT.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['discovery.py','discovery02.py','discovery_profile01.json','test_scheme02.py']
before={n:sha(W/n) for n in names}
for n in names:(OUT/(n+'.snapshot')).open('xb').write((W/n).read_bytes())
start=time.monotonic();attempts=[]
for label,source in [('before','discovery.py'),('after','discovery02.py')]:
    remaining=10-(time.monotonic()-start)
    if remaining<=0:raise TimeoutError('shared10second focusedcheck cap')
    command=[sys.executable,'-I','-S','-B',str(W/'test_scheme02.py'),'--source',str(W/source)]
    with (OUT/(label+'.log')).open('xb') as log:
        p=subprocess.run(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=remaining,
                         env=dict(os.environ,CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES=''))
    attempts.append({'label':label,'source':source,'returncode':p.returncode,'command':command})
elapsed=time.monotonic()-start;after={n:sha(W/n) for n in names}
record={'status':'FOCUSED_RED_GREEN_PASS' if attempts[0]['returncode']==1 and attempts[1]['returncode']==0 and before==after and elapsed<=10 else 'FAILED_RETAIN_NO_BROAD_RERUN','attempts':attempts,'focused_tests_each':2,'focused_after_passed':2,'controller_seconds':elapsed,'cap_seconds':10,'previous_suite_cumulative_seconds':117.79799590000766,'new_cap_explicitly_authorized_separate':True,'source_sha256_before':before,'source_sha256_after':after,'optimizer_model_probe_install_gpu_calls':0,'limits':'AST-extracted exact PROBE prefix with Debian-default sysconfig stub. No actual Linux target probe, package repair or 40case suite rerun.'}
(OUT/'run.json').open('x',encoding='utf-8').write(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(record));raise SystemExit(0 if record['status']=='FOCUSED_RED_GREEN_PASS' else 1)
