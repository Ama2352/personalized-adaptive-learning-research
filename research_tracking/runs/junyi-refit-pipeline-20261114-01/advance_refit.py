"""Nghiệm thu tranche refit đã dừng và lập resume trong phạm vi người dùng giao."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent

def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2)
        stream.write('\n')

def settle(request_path):
    request=read(request_path)
    output=ROOT/'experiments/akt/results'/request['execution_id']
    guard=read(output/'app-budget-guard.json')
    assert guard['stop_acknowledged'] is True
    assert read(output/'COMPLETE.json')['status']=='LOCAL_ARTIFACTS_VERIFIED_GPU_STOPPED'
    receipt=read(output/'remote-inventory.json')
    elapsed=max(event['elapsed_seconds'] for event in guard['events'])
    gpu_seconds=receipt['gpu_worker_seconds']
    upper=min(request['reserved_usd_per_run'],(gpu_seconds+60)*.001097+(elapsed+60)*.00023772)
    ledger_path=ROOT/'research_tracking/COMPUTE_BUDGET.json'
    ledger=read(ledger_path)
    assert len(ledger['new_allocations'])==1 and ledger['new_allocations'][0]['id']==request['allocation_id']
    evidence=dict(id=request['allocation_id'],status='STOPPED_ARTIFACTS_VERIFIED_'+receipt['status'],
        reserved_upper_closed_usd=upper,actual_isolated_cost_usd=None,gpu_worker_seconds=gpu_seconds,
        app_elapsed_seconds=elapsed,stop_acknowledged=True,
        evidence=(output/'remote-inventory.json').relative_to(ROOT).as_posix())
    write(HERE/(request['execution_id']+'-settlement.json'),evidence)
    ledger['historical_usage_reserved_upper_usd']+=upper
    ledger['closed_reservations'].append(evidence)
    ledger['new_allocations']=[]
    ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    result=receipt.get('worker_result',{}).get('terminal',{})
    state=read(HERE/'STATE.json')
    variant=result.get('variant') or request['execution_id'].split('-')[2].upper()
    performed = receipt['status'] in ('PARTIAL_JUNYI_REFIT90', 'JUNYI_REFIT90_COMPLETE') and bool(receipt.get('checkpoints'))
    state.update(status='REFIT_TRANCHE_VERIFIED',gpu_started=True,real_data_training_performed=performed,
        active_execution=None,last_execution=request['execution_id'],last_terminal=result)
    state.setdefault('refit_models',{})[variant]=dict(status=receipt['status'],epochs=result.get('complete_epochs'),
        output=output.relative_to(ROOT).as_posix(),checkpoint_export_pending=receipt['status']=='JUNYI_REFIT90_COMPLETE')
    (HERE/'STATE.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(settlement=evidence,terminal=result)))

def prepare_next(variant,attempt,previous):
    assert variant in ('a0','a1','a2','a3') and 1<=attempt<=20
    ledger_path=ROOT/'research_tracking/COMPUTE_BUDGET.json';ledger=read(ledger_path)
    assert ledger['new_allocations']==[]
    request=read(HERE/'a0-refit-execution02.json')
    identifier=f'junyi-{variant}-refit-h100-20261114-{attempt:02}'
    request.update(execution_id='modal-'+identifier,allocation_id=identifier)
    if previous is not None:
        output=ROOT/'experiments/akt/results'/read(previous)['execution_id']
        assert read(output/'app-budget-guard.json')['stop_acknowledged'] is True
        assert read(output/'COMPLETE.json')['status']=='LOCAL_ARTIFACTS_VERIFIED_GPU_STOPPED'
        receipt=read(output/'remote-inventory.json')
        assert receipt['status']=='PARTIAL_JUNYI_REFIT90'
        prefix=f'outputs/junyi-{variant}-refit-20261114-01/checkpoints/'
        candidates=[]
        for name,pin in receipt['files'].items():
            if not name.startswith(prefix) or not name.endswith('/state.pt'):continue
            folder=name.split('/')[-2]
            partial=re.fullmatch(r'refit-batch-epoch-(\d+)-step-(\d+)-[a-f0-9]+',folder)
            complete=re.fullmatch(r'epoch-(\d+)',folder)
            if partial: rank=(int(partial[1]),int(partial[2]))
            elif complete:rank=(int(complete[1]),10**12)
            else:continue
            assert name.rsplit('/',1)[0]+'/COMPLETE.json' in receipt['files']
            candidates.append((rank,name,pin))
        _,name,pin=max(candidates)
        request.update(resume_checkpoint='experiments/akt/results/'+name[len('outputs/'):],resume_sha256=pin['sha256'],
            resume_inventory=(output/'remote-inventory.json').relative_to(ROOT).as_posix())
    cap=request['reserved_usd_per_run']
    if ledger['historical_usage_reserved_upper_usd']+ledger['safety_and_final_inference_reserve_usd']+cap>30:
        raise RuntimeError('BUDGET_ENVELOPE_REQUIRES_RECONCILIATION_BEFORE_NEW_RUN')
    path=HERE/f'{variant}-refit-execution{attempt:02}.json'
    assert not path.exists()
    ledger['new_allocations']=[dict(id=identifier,cap_usd=cap,purpose_vi='RefitH100 tranche600giây, epoch9cốđịnh, không calibration/Holdout.')]
    write(path,request)
    ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(path.relative_to(ROOT).as_posix())

def promote(variant,previous):
    output=ROOT/'experiments/akt/results'/read(previous)['execution_id']
    assert read(output/'COMPLETE.json')['status']=='LOCAL_ARTIFACTS_VERIFIED_GPU_STOPPED'
    receipt=read(output/'remote-inventory.json');assert receipt['status']=='JUNYI_REFIT90_COMPLETE'
    logical=f'junyi-{variant}-refit-20261114-01'
    source=output/'files/outputs'/logical;target=ROOT/'experiments/akt/results'/logical
    assert not target.exists()
    names=['run-manifest.json','COMPLETE.json','checkpoints/epoch-009/state.pt',
        'checkpoints/epoch-009/metadata.json','checkpoints/epoch-009/COMPLETE.json']
    inventory={name:dict(sha256=sha(source/name),bytes=(source/name).stat().st_size) for name in names}
    for name,pin in inventory.items():assert receipt['files']['outputs/'+logical+'/'+name]==pin
    record=dict(source=source.relative_to(ROOT).as_posix(),destination=target.relative_to(ROOT).as_posix(),files=inventory)
    write(HERE/f'{variant}-refit-canonical-copy-inventory.json',record)
    for name,pin in inventory.items():
        destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source/name,destination)
        assert sha(destination)==pin['sha256']
    write(HERE/f'{variant}-refit-canonical-copy-verified.json',dict(status='COPY_SHA_VERIFIED',**record))
    print(target.relative_to(ROOT).as_posix())

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['settle','next','promote'])
    p.add_argument('--request',type=Path)
    p.add_argument('--previous',type=Path)
    p.add_argument('--variant',choices=['a0','a1','a2','a3'])
    p.add_argument('--attempt',type=int)
    a=p.parse_args()
    if a.action=='settle':settle(a.request)
    elif a.action=='next':prepare_next(a.variant,a.attempt,a.previous)
    else:promote(a.variant,a.previous)
