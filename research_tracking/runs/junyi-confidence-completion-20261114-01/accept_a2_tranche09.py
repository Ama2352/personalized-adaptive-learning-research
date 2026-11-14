"""Nghiệm thu 7 epoch thật, checkpoint/RNG và cấp lượt tiếp tục A2 trong trần dự án."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
output=ROOT/'experiments/akt/results/modal-junyi-a2-staged-h100-20261114-09'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    import torch
    torch.set_num_threads(1)
    complete=json.loads((output/'COMPLETE.json').read_text())
    stage=json.loads((output/'stage-result.json').read_text())
    remote=json.loads((output/'remote-inventory.json').read_text())
    guard=json.loads((output/'app-budget-guard.json').read_text())
    assert complete['status']==stage['status']=='LOCAL_ARTIFACTS_VERIFIED_GPU_STOPPED'
    assert guard['stop_acknowledged'] is True
    assert remote['status']==stage['worker_status']=='PARTIAL_SELECTED_ONLY_NOT_FINAL'
    assert complete['files']==len(remote['files'])==125
    terminal=remote['worker_result']['terminal']
    assert [row['epoch'] for row in terminal['history']]==list(range(1,8))
    assert terminal['optimizer_steps']==7*1818 and terminal['trained_targets']==7*13347331
    population='c26bac9fbbdcf488dc1c8d7b953663158b53216d980676de70b67819fc470b64'
    assert all(row['validation']['targets']==1600343 and row['validation']['population_sha256']==population
               and row['validation']['oov']==0 for row in terminal['history'])
    key='outputs/junyi-a2-expert-selected-20261114-01/checkpoints/epoch-007/state.pt'
    checkpoint=output/'files'/key
    assert sha(checkpoint)==remote['files'][key]['sha256']
    payload=torch.load(checkpoint,map_location='cpu',weights_only=True)
    assert payload['progress']['epoch']==7 and payload['progress']['validation_complete'] is True
    assert payload['progress']['optimizer_steps']==12726
    assert payload['progress']['stopper']['best_epoch']==6
    assert all(torch.isfinite(value).all().item() for value in payload['model_state_dict'].values())
    assert payload['optimizer_state_dict']['state']
    assert all(name in payload for name in ('python_rng','numpy_rng','torch_rng','cuda_rng'))
    assert len(payload['cuda_rng'])==1
    acceptance=dict(status='PASS_A2_SEVEN_EPOCHS_CHECKPOINT_AND_ARTIFACTS',complete_epochs=7,
        checkpoint=checkpoint.relative_to(ROOT).as_posix(),checkpoint_sha256=sha(checkpoint),
        best_observed_epoch=6,history=terminal['history'],sampler_resume='epoch8-after-complete-epoch7',
        selection_population_matched=True,checkpoint_tensors_finite=True,optimizer_rng_present=True,
        archive_sha256=complete['archive_sha256'],gpu_stopped=True)
    with (HERE/'a2-tranche09-acceptance.json').open('x',encoding='utf-8') as stream:
        json.dump(acceptance,stream,ensure_ascii=False,indent=2)
    ledger_path=ROOT/'research_tracking/COMPUTE_BUDGET.json'
    ledger=json.loads(ledger_path.read_text())
    old=json.loads((HERE/'a2-training-request09.json').read_text())
    assert len(ledger['new_allocations'])==1 and ledger['new_allocations'][0]['id']==old['allocation_id']
    seconds=max(event['elapsed_seconds'] for event in guard['events'])+60
    upper=seconds*.00133472
    assert upper<old['reserved_usd_per_run']
    settlement=dict(id=old['allocation_id'],status='PARTIAL_SEVEN_EPOCHS_VERIFIED_APP_STOPPED',
        reserved_upper_closed_usd=upper,elapsed_upper_seconds=seconds,
        actual_isolated_cost_usd=None,stop_acknowledged=True)
    ledger['closed_reservations'].append(settlement)
    ledger['historical_usage_reserved_upper_usd']+=upper
    request=dict(old,execution_id='modal-junyi-a2-staged-h100-20261114-10',
        allocation_id='junyi-a2-staged-h100-20261114-10',
        resume_checkpoint='experiments/akt/results/'+key[len('outputs/'):],
        resume_sha256=remote['files'][key]['sha256'],
        resume_inventory=(output/'remote-inventory.json').relative_to(ROOT).as_posix())
    ledger['new_allocations']=[dict(id=request['allocation_id'],cap_usd=2.6,
        purpose_vi='Tiếp tục A2 từ epoch007 đã nghiệm thu, cùng input/recipe, tối đa một H100.')]
    envelope=ledger['historical_usage_reserved_upper_usd']+3+2.6
    assert envelope<=30
    ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for name,value in [('a2-training-request10.json',request),('a2-tranche09-settlement.json',settlement)]:
        with (HERE/name).open('x',encoding='utf-8') as stream:
            json.dump(value,stream,ensure_ascii=False,indent=2)
            stream.write('\n')
    print(json.dumps(dict(status=acceptance['status'],reserved_upper_usd=upper,
        next_reserved_usd=2.6,conservative_project_envelope=envelope)),flush=True)


if __name__=='__main__':
    main()
