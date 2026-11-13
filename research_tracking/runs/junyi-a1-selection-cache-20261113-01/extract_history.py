"""Đọc checkpoint đã tải/kiểm SHA, xuất tiến độ và chứng nhận giữ epoch1."""
import hashlib
import json
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', default='checkpoint-download-receipt.json')
    parser.add_argument('--output', default='live-history.json')
    args = parser.parse_args()
    for name in (args.receipt, args.output):
        assert Path(name).name == name and name.endswith('.json')
    import torch
    receipt=json.loads((HERE/args.receipt).read_text())
    rows=receipt['checkpoints']
    assert rows
    last=ROOT/rows[-1]['path']/'state.pt'
    assert hashlib.sha256(last.read_bytes()).hexdigest()==rows[-1]['sha256']
    payload=torch.load(last,map_location='cpu',weights_only=True)
    progress=payload['progress']
    result=dict(status='VERIFIED_CHECKPOINT_HISTORY',run_id=receipt['run_id'],
        checkpoint=rows[-1]['checkpoint'],history=progress['history'],stopper=progress['stopper'],
        optimizer_steps=progress['optimizer_steps'],trained_targets=progress['valid_targets'],
        alpha=float(payload['model_state_dict']['alpha']),refit_completed=False,calibration_completed=False)
    (HERE/args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    del payload
    first=next((row for row in rows if row['checkpoint']=='epoch-001'),None)
    if first is not None and not (HERE/'epoch1-preservation.json').exists():
        original=ROOT/'experiments/akt/results/modal-junyi-a1-b128-h100-20261113-05/checkpoints/train-epoch-001/state.pt'
        old=torch.load(original,map_location='cpu',weights_only=True)
        new=torch.load(ROOT/first['path']/'state.pt',map_location='cpu',weights_only=True)
        def equal(a,b):
            if torch.is_tensor(a):assert torch.equal(a,b)
            elif isinstance(a,dict):
                assert a.keys()==b.keys()
                for key in a:equal(a[key],b[key])
            elif isinstance(a,(tuple,list)):
                assert len(a)==len(b)
                for x,y in zip(a,b):equal(x,y)
            else:assert a==b
        for key in ('model_state_dict','optimizer_state_dict','python_rng','numpy_rng','torch_rng','cuda_rng'):
            equal(old[key],new[key])
        assert new['progress']['optimizer_steps']==1818 and new['progress']['valid_targets']==13347331
        preservation=dict(status='PASS_FULL_EPOCH1_STATE_PRESERVED_THROUGH_VALIDATION',
            source_checkpoint_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
            target_checkpoint_sha256=first['sha256'],model_optimizer_all_rng_exact=True,
            epoch1_training_repeated=False,optimizer_steps=1818,trained_targets=13347331,
            selection_targets=new['progress']['history'][0]['validation']['targets'])
        (HERE/'epoch1-preservation.json').write_text(json.dumps(preservation,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
