import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

root=Path.cwd();label=sys.argv[1]
out=root/'artifacts/akt/local-tests'/label;out.mkdir(exist_ok=False)
sources=['src/knowledge_tracing/akt/context.py','src/knowledge_tracing/akt/device_budget.py',
         'src/knowledge_tracing/akt/config.py','src/knowledge_tracing/akt/authorization.py',
         'src/knowledge_tracing/akt/runner.py','src/knowledge_tracing/akt/watchdog.py',
         'tests/akt/test_context.py','tests/akt/test_cuda_budget.py']
hashes={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in sources}
for name in sources:(out/name.replace('/','--')).write_bytes((root/name).read_bytes())
env=dict(os.environ,PYTHONPATH=str(root/'src'),CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
n=int(env.get('GIT_CONFIG_COUNT','0'));env['GIT_CONFIG_COUNT']=str(n+1)
env[f'GIT_CONFIG_KEY_{n}']='safe.directory';env[f'GIT_CONFIG_VALUE_{n}']=(root/'artifacts/akt/dependencies/upstream').as_posix()
command=[sys.executable,'-B','-m','pytest','tests/akt/test_context.py','tests/akt/test_cuda_budget.py',
         'tests/akt/test_runner.py','tests/akt/test_worker_lifecycle.py','tests/akt/test_watchdog.py','tests/akt/test_cli_recovery.py','-q','-p','no:cacheprovider',
         '--basetemp',str(out/'t'),'--junitxml',str(out/'pytest.xml')]
with (out/'pytest.log').open('xb') as log:r=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
assert all(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest for name,digest in hashes.items())
(out/'verification.json').write_text(json.dumps({'returncode':r.returncode,'source_hashes':hashes,'command':command,
 'scope':'CPU tests, CUDAhardwarefake; noactualGPU or cloud; exactprocessupstreamGitrustonly'},indent=2),encoding='utf-8')
print(json.dumps({'returncode':r.returncode,'log':str(out/'pytest.log')}))
raise SystemExit(r.returncode)
