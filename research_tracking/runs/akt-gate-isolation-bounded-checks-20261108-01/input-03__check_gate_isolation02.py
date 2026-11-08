"""ROOT: một lượt pure tests, không model; timeout cooperative có ghi phạm vi."""
from pathlib import Path
import builtins
import hashlib
import json
import os
import platform
import sys
import threading
import time
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'scripts/research'))
from windows_owned_worker import worker_gate
worker_gate()  # Trước pytest
os.chdir(ROOT)
PREP=Path(__file__).resolve().parent
OUT=PREP/'gate_isolation02'
OUT.mkdir(exist_ok=False)
start=time.perf_counter()
files=['scripts/akt/refresh_gate2.py','tests/akt/test_gate2_refresh.py']
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
before={p:sha(p) for p in files}
(OUT/'before.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
os.environ.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
timer=threading.Timer(34,lambda:os._exit(124));timer.daemon=True;timer.start()
attempted=[]
def audit(event,args):
    if event=='subprocess.Popen':
        attempted.append(event)
        raise AssertionError('ROOT pure-controller actual subprocess denied')
sys.addaudithook(audit)
# Test-only metadata fallback. Không dùng làm RuntimeGate/CUDA chứng nhận.
version=sys.getwindowsversion()
native=tuple(version.platform_version)
old=platform._syscmd_ver
platform._syscmd_ver=lambda system='',release='',version='',supported_platforms=(): ('Windows',str(native[0]),'.'.join(map(str,native)))
platform._uname_cache=None
sys.path.insert(0,str(ROOT/'src'))
rc=None
try:
    import pytest
    args=['tests/akt/test_gate2_refresh.py','-q','-p','no:cacheprovider','--basetemp='+str(OUT/'tmp'),'--junitxml='+str(OUT/'junit.xml')]
    with (OUT/'pytest.log').open('w',encoding='utf-8') as log:
        from contextlib import redirect_stdout,redirect_stderr
        with redirect_stdout(log),redirect_stderr(log):rc=int(pytest.main(args))
finally:
    timer.cancel();platform._syscmd_ver=old;platform._uname_cache=None
    elapsed=time.perf_counter()-start
    after={p:sha(p) for p in files}
    result={'pytest_exit_code':rc,'elapsed_seconds':elapsed,'cap_seconds':60,'prior_conservative_seconds':20,'cumulative_seconds':20+elapsed,
            'source_before':before,'source_after':after,'source_unchanged':before==after,
            'actual_subprocess_attempts':attempted,
            'heavy_modules_loaded':[p for p in ('torch','numpy','pandas','sklearn') if p in sys.modules],
            'test_only_windows_metadata_fallback':{'native_version':native},
            'timeout_scope_vi':'Daemon Timer cooperative/GIL-dependent, không hard OS quota; chỉ pure metadata/stubs, không model/native.',
            'scope_vi':'Không full Gate/research fit/actual solver/CUDA/Colab/Modal.'}
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
assert before==after and 20+elapsed<60 and not attempted
assert not result['heavy_modules_loaded']
raise SystemExit(rc)
