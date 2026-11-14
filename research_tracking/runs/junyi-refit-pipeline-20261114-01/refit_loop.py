"""Loop hữu hạn refit9epoch×4 đã được giao, dừng lỗi/ngân sách, không tự đổi recipe."""
import argparse
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('advance_refit_owned',HERE/'advance_refit.py')
advance=importlib.util.module_from_spec(spec);spec.loader.exec_module(advance)

def read(p):return json.loads(p.read_text())
def write(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def child(command,log):
    with log.open('x',encoding='utf-8') as stream:
        code=subprocess.call([sys.executable,'-B',*command],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
    if code:raise RuntimeError('Child failed; inspect '+log.name)

def inspect_completed(request):
    output=ROOT/'experiments/akt/results'/read(request)['execution_id']
    result=output/'stage-result.json'
    end=time.monotonic()+3600
    while not result.exists():
        if (output/'local-failure.json').exists():raise RuntimeError('Controller failure: '+str(output))
        if time.monotonic()>end:raise TimeoutError('No staged artifact receipt within3600seconds')
        time.sleep(5)
    receipt=read(output/'remote-inventory.json')
    assert read(output/'app-budget-guard.json')['stop_acknowledged']
    assert read(output/'COMPLETE.json')['status']=='LOCAL_ARTIFACTS_VERIFIED_GPU_STOPPED'
    if receipt['status']=='FAILED':raise RuntimeError('Numerical worker failed: '+str(output))
    assert receipt['status'] in ('PARTIAL_JUNYI_REFIT90','JUNYI_REFIT90_COMPLETE')
    advance.settle(request)
    return receipt

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');args=parser.parse_args()
    if not args.run:
        print(json.dumps(dict(status='NO_EXECUTION',scope='A0–A3refit90;9epoch;H100;total30USD')));return
    status=dict(status='RUNNING_FIXED_REFIT_MATRIX',started_at_utc=datetime.now(timezone.utc).isoformat(),models={})
    try:
        for variant in ('a0','a1','a2','a3'):
            snapshot=ROOT/f'artifacts/akt/staged/junyi-{variant}-refit-bounded-20261114-04'
            assert read(snapshot/'CPU_CHECK.json')['status']=='PASS_LOCAL_STAGE_INPUTS'
            previous=None
            first=5 if variant=='a0' else 1
            for attempt in range(first,21):
                request=HERE/f'{variant}-refit-execution{attempt:02}.json'
                if variant=='a0' and attempt==5:
                    pass  # Đợt này đã được root khởi chạy, chỉ chờ nghiệm thu.
                else:
                    advance.prepare_next(variant,attempt,previous)
                    child(['experiments/akt/modal_junyi_refit.py','--snapshot',str(snapshot),'--request',str(request),'--run'],HERE/f'{variant}-refit-execution{attempt:02}.log')
                receipt=inspect_completed(request)
                terminal=receipt['worker_result']['terminal']
                status['models'][variant]=dict(status=receipt['status'],complete_epochs=terminal['complete_epochs'],frozen_epochs=terminal['frozen_epochs'],last_request=request.name)
                (HERE/'refit-loop-progress.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
                if receipt['status']=='JUNYI_REFIT90_COMPLETE':
                    assert terminal['complete_epochs']==terminal['frozen_epochs']==9
                    advance.promote(variant,request)
                    child(['scripts/akt/export_junyi_refit_model.py','--request',str(HERE/f'refit-request-{variant}-bounded02.json'),'--output',f'experiments/akt/results/model-export-{variant}-refit-20261114-01'],HERE/f'{variant}-refit-export01.log')
                    status['models'][variant]['model_export']=f'experiments/akt/results/model-export-{variant}-refit-20261114-01'
                    break
                previous=request
            else:raise RuntimeError('Bounded tranche count exceeded')
        status['status']='FOUR_REFITS_COMPLETE_EXPORTED_CALIBRATION_PENDING'
    except BaseException as error:
        status.update(status='STOPPED_REQUIRES_ROOT_REVIEW',error_type=type(error).__name__,error=str(error))
        raise
    finally:
        status['updated_at_utc']=datetime.now(timezone.utc).isoformat()
        (HERE/'refit-loop-progress.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
