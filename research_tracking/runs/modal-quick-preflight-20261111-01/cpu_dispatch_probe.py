"""Canary CPU Modal để phân biệt dispatch chung và cấp GPU, nằm trong pilot0,50USD."""
import os
os.environ['MODAL_CONFIG_PATH']='D:/Dev/KLTN/artifacts/akt/private/modal.toml'
os.environ['MODAL_PROFILE']='kltn'
import json
from pathlib import Path
import modal
app=modal.App('kltn-akt-cpu-dispatch-check')
@app.function(image=modal.Image.debian_slim(python_version='3.13'),cpu=0.125,memory=128,timeout=15,retries=0,max_containers=1)
def probe():
    return dict(container_executed=True)
if __name__=='__main__':
    result=dict(status='FAILED')
    try:
        with modal.enable_output():
            with app.run(environment_name='main'):
                call=probe.spawn()
                result.update(status='PASS',response=call.get(timeout=45))
    except Exception as error:
        result.update(error_type=type(error).__name__,error=str(error))
    Path('research_tracking/runs/modal-quick-preflight-20261111-01/cpu-dispatch-result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
