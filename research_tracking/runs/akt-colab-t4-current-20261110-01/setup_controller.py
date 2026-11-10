"""Chuẩn bị rồi kiểm CPU hiện hành; từng bước giữ kết quả, không chạy training chính."""
import hashlib,json,os,subprocess,sys,time,traceback
from pathlib import Path
ROOT=Path('/content/kltn-current-t4-20261110-01')
OUT=ROOT/'artifacts/akt/runtime/t4-setup01'
OUT.mkdir(exist_ok=False)
started=time.monotonic()
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(ROOT/'src'))
result=dict(status='STARTED',scope='Free T4 isolated setup; no model steps',modal_spend_usd=0,model_training=False)
def save():
    result['elapsed_seconds']=time.monotonic()-started
    (OUT/'status.json').write_text(json.dumps(result,indent=2)+'\n')
def run(label,command,timeout):
    result.update(stage=label);save()
    (OUT/(label+'-command.json')).write_text(json.dumps(command,indent=2))
    with (OUT/(label+'.log')).open('xb') as log:
        subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=timeout,check=True)
try:
    assert subprocess.check_output(['nvidia-smi','--query-gpu=name','--format=csv,noheader'],text=True,timeout=10).strip() == 'Tesla T4'
    run('venv',[sys.executable,'-I','-B','-m','venv','--without-pip',str(ROOT/'.venv')],30)
    assert 'include-system-site-packages = false' in (ROOT/'.venv/pyvenv.cfg').read_text().lower()
    upstream=ROOT/'artifacts/akt/dependencies/upstream'
    upstream.parent.mkdir(parents=True,exist_ok=True)
    run('clone',['git','clone','--no-checkout','https://github.com/arghosh/AKT.git',str(upstream)],180)
    run('pin',['git','-C',str(upstream),'checkout','--detach','01b7e8d7d7c862cabc9467108e3e7f2555653a88'],60)
    run('source-verify',[sys.executable,'-I','-B','-c',"import sys;sys.path.insert(0,"+repr(str(ROOT/'src'))+");from pathlib import Path;from knowledge_tracing.akt.provenance import verify_upstream;print(verify_upstream(Path("+repr(str(upstream))+"),'01b7e8d7d7c862cabc9467108e3e7f2555653a88'))"],30)
    assert sum(p.stat().st_size for p in upstream.rglob('*') if p.is_file())<=128*1024**2
    run('install',[str(ROOT/'.venv/bin/python'),'-I','-B',str(ROOT/'artifacts/akt/runtime/t4-input01/install_controller.py')],650)
    accepted=json.loads((ROOT/'artifacts/akt/runtime/isolated-install01/result.json').read_text())
    assert accepted['status']=='ISOLATED_ENV_READY_GPU_UNTESTED'
    result.update(status='ISOLATED_ENV_READY_GPU_UNTESTED')
except BaseException as error:
    result.update(status='FAILED_NO_AUTOMATIC_RETRY',error_type=type(error).__name__,error=str(error))
    (OUT/'failure.log').write_text(traceback.format_exc())
finally:
    save();print(json.dumps(result),flush=True)
