"""Canary GPU tối giản, không mount Volume, trong cùng pilot0,50USD."""
import os
if __name__=='__main__':
    os.environ['MODAL_CONFIG_PATH']='D:/Dev/KLTN/artifacts/akt/private/modal.toml'
    os.environ['MODAL_PROFILE']='kltn'
import json,subprocess
from pathlib import Path
import modal
app=modal.App('kltn-akt-gpu-dispatch-check')
@app.function(image=modal.Image.from_id('im-Os3SwcLoqcL5FornDC2AMk'),gpu='L4',cpu=(0.125,1),memory=(1024,4096),timeout=30,startup_timeout=60,retries=0,max_containers=1)
def probe():
    code="import torch,json;print(json.dumps(dict(cuda=torch.cuda.is_available(),torch=torch.__version__,gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)))"
    p=subprocess.run(['/opt/kltn/.venv/bin/python','-I','-B','-c',code],capture_output=True,text=True,timeout=20,check=True)
    return json.loads(p.stdout)
if __name__=='__main__':
    result=dict(status='FAILED')
    try:
        with modal.enable_output():
            with app.run(environment_name='main'):
                call=probe.spawn()
                result.update(status='PASS',response=call.get(timeout=90))
    except Exception as error:
        result.update(error_type=type(error).__name__,error=str(error))
    Path('research_tracking/runs/modal-quick-preflight-20261111-01/gpu-dispatch-result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
