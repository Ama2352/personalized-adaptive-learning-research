"""Probe recovery AKT trong tiến trình mới, chỉ17targets tổng hợp mỗi nhánh.

Continuous5updates so với interrupt2+resume3; không Dev/Holdout/Modal.
CPU dùng equality exact, CUDA tolerance khai báo; RNG/ledger luôn exact.
"""

import argparse
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def validate_output(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('probe output cannot be a symlink')
    output = path.resolve()
    if output.parent != (ROOT / 'experiments/akt/results').resolve():
        raise ValueError('output must be a new direct child of experiments/akt/results')
    if output.exists():
        raise FileExistsError(output)
    return output


def compare_tree(left, right, *, atol, rtol):
    """So mọi model/Adam/RNG leaves; byte/int/scalar metadata phải exact."""
    import torch
    maximum = 0.0
    if isinstance(left, torch.Tensor):
        if not isinstance(right, torch.Tensor) or left.shape != right.shape or left.dtype != right.dtype:
            raise ValueError('state tensor shape/dtype mismatch')
        if left.is_floating_point():
            if not torch.isfinite(left).all() or not torch.isfinite(right).all():
                raise ValueError('nonfinite state tensor')
            if not torch.allclose(left, right, atol=atol, rtol=rtol):
                raise ValueError('floating state mismatch')
            maximum = float((left-right).abs().max().item()) if left.numel() else 0.0
        elif not torch.equal(left, right):
            raise ValueError('integer/RNG state mismatch')
    elif isinstance(left, dict):
        if not isinstance(right, dict) or left.keys() != right.keys():
            raise ValueError('state dictionary mismatch')
        maximum = max((compare_tree(left[k], right[k], atol=atol, rtol=rtol) for k in left), default=0.0)
    elif isinstance(left, (list, tuple)):
        if type(right) is not type(left) or len(left) != len(right):
            raise ValueError('state sequence mismatch')
        maximum = max((compare_tree(a,b,atol=atol,rtol=rtol) for a,b in zip(left,right)), default=0.0)
    elif type(left) is not type(right) or left != right or (isinstance(left,float) and not math.isfinite(left)):
        raise ValueError('scalar state mismatch')
    return maximum


def inventory(directory):
    return {p.name:sha(p) for p in sorted(Path(directory).iterdir()) if p.is_file()}


def _worker(args):
    import random
    import numpy as np
    import torch
    from knowledge_tracing.akt.authorization import gate2_build_hashes
    from knowledge_tracing.akt.checkpoint import save_checkpoint, load_recovery_checkpoint
    from knowledge_tracing.akt.config import AKTConfig, RecoveryOptions, SOURCE_COMMIT
    from knowledge_tracing.akt.encoding import fit_vocabulary
    from knowledge_tracing.akt.model import AKTAdapter
    from knowledge_tracing.akt.prediction import iter_predictions
    from knowledge_tracing.akt.provenance import verify_upstream
    from knowledge_tracing.akt.recovery import semantic_hash
    from knowledge_tracing.akt.training import train_epoch
    from knowledge_tracing.akt.types import KTEvent,LearnerEvents
    from knowledge_tracing.akt.windows import iter_windows

    if args.device == 'cuda' and (not torch.cuda.is_available() or torch.cuda.device_count()!=1):
        raise ValueError('probe requires exactly one available CUDA GPU; no CPU fallback')
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    random.seed(42);np.random.seed(42);torch.manual_seed(42)
    if args.device == 'cuda':
        torch.cuda.manual_seed_all(42)
        torch.cuda.reset_peak_memory_stats()
    directory = args.output_dir.resolve() / args._worker_phase
    directory.mkdir(exist_ok=False)
    config = AKTConfig(output_dir=directory,run_id=directory.name,device=args.device,
        d_model=32,heads=4,d_ff=64,final_fc=32,dropout=.2,batch_size=2,
        context=2,target_block=2,recovery=RecoveryOptions(1))
    source = verify_upstream(config.source_root,SOURCE_COMMIT)
    learner = LearnerEvents('synthetic-recovery',0,tuple(KTEvent('synthetic-recovery',
        'ABC'[i%3],i+1,i+1,i%2,0,0) for i in range(17)))
    encoding = fit_vocabulary([learner])
    identity = {'kind':'synthetic-fresh-process-recovery-v1','source':source,
        'build_hashes':gate2_build_hashes(),'semantic_config_sha256':semantic_hash(config),
        'fixture':'17events/ABC/alternatinglabels/H2T2/batch2','device':args.device}
    model = AKTAdapter(config,encoding)
    optimizer = torch.optim.Adam(model.native.parameters(),lr=config.lr,betas=config.betas,
                                 eps=config.eps,weight_decay=config.weight_decay)
    rows,checkpoints=[],[]
    original_step = model.step
    def recorded_step(batch,opt):
        result = original_step(batch,opt)
        if result['stepped']:
            rows.extend(batch.source_rows[(batch.target_mask & batch.valid_mask).cpu().numpy()].tolist())
        return result
    model.step = recorded_step
    class ProbeInterruption(Exception):
        pass
    def checkpoint(path):
        checkpoints.append(path)
        if args._worker_phase=='interrupted' and '-step-2-' in path.name:
            raise ProbeInterruption('controlled interruption after committed step2')
    recovery = {'identity':identity,'checkpoint_dir':directory,'prefix':'probe','checkpoint_callback':checkpoint}
    if args._worker_phase=='resumed':
        path = args._checkpoint.resolve()
        if path.parent != (args.output_dir/'interrupted').resolve() or sha(path)!=args._checkpoint_sha:
            raise ValueError('resume checkpoint outside immutable interrupted phase or hash mismatch')
        recovery['resume_checkpoint']=path
    factory=lambda:iter_windows(learner,encoding,context=2,target_block=2,training=True)
    status='COMPLETE'
    try:
        stats=train_epoch(model,factory,optimizer=optimizer,epoch=1,
            budget={'max_steps':5,'max_targets':17,'max_seconds':30},recovery=recovery)
    except ProbeInterruption:
        status='INTERRUPTED_AT_STEP2'
        stats=None
    if not checkpoints:
        raise ValueError('probe produced no committed checkpoint')
    payload=load_recovery_checkpoint(checkpoints[-1],expected_identity=identity,device='cpu')
    state=payload['resume_state']
    del payload
    report={'phase':args._worker_phase,'status':status,'checkpoint_name':checkpoints[-1].name,
        'checkpoint_sha256':sha(checkpoints[-1]),'optimized_rows_this_process':rows,
        'sampler_state':state['sampler_state'],'committed_steps':state['optimizer_steps'],
        'cumulative_targets':state['trainer_state']['stats']['valid_targets'],
        'identity':identity,'pid':os.getpid()}
    if status=='COMPLETE':
        if not stats.complete or stats.valid_targets!=17 or stats.optimizer_steps!=5:
            raise ValueError('probe did not finish exact bounded epoch')
        final=directory/'final.pt'
        save_checkpoint(final,model,optimizer,identity=identity,
            progress={'epoch':1,'complete':True,'optimizer_steps':5})
        report['final_checkpoint_sha256']=sha(final)
        model.checkpoint_id=report['final_checkpoint_sha256']
        report['rng_draws']={'python':random.random(),'numpy':float(np.random.random()),
                             'torch_cpu':torch.rand(4).tolist(),
                             'torch_cuda':torch.rand(4,device='cuda').cpu().tolist() if args.device=='cuda' else []}
        report['predictions']=[r.prediction for r in iter_predictions(model,(learner,))]
        report['stats']=asdict(stats)
    elif (state['optimizer_steps']!=2 or not 0<len(rows)<17
          or state['trainer_state']['stats']['valid_targets']!=len(rows)):
        raise ValueError('interruption not at exact committed step2')
    if args.device=='cuda':torch.cuda.synchronize()
    report['torch']=torch.__version__
    report['cuda_build']=torch.version.cuda
    report['gpu_name']=torch.cuda.get_device_name() if args.device=='cuda' else None
    report['peak_vram_bytes']=torch.cuda.max_memory_allocated() if args.device=='cuda' else None
    write_json(directory/'phase.json',report)


def run_probe(output,device):
    if device not in {'cpu','cuda'}:
        raise ValueError('explicit cpu/cuda device required')
    started=time.perf_counter()
    output=validate_output(output);output.mkdir()
    env={**os.environ,'PYTHONPATH':str(ROOT/'src'),'PYTHONDONTWRITEBYTECODE':'1',
         'CUBLAS_WORKSPACE_CONFIG':':4096:8'}
    if device=='cpu':env['CUDA_VISIBLE_DEVICES']=''
    count=int(env.get('GIT_CONFIG_COUNT','0'))
    env.update({f'GIT_CONFIG_KEY_{count}':'safe.directory',
                f'GIT_CONFIG_VALUE_{count}':(ROOT/'artifacts/akt/dependencies/upstream').as_posix(),
                'GIT_CONFIG_COUNT':str(count+1)})
    source_snapshot=None
    try:
        for phase in ('continuous','interrupted','resumed'):
            remaining=180-(time.perf_counter()-started)
            if remaining<=0:raise TimeoutError('total recovery probe wall cap180s')
            command=[sys.executable,'-B',str(Path(__file__).resolve()),'--device',device,
                     '--output-dir',str(output),'--_worker-phase',phase]
            if phase=='resumed':
                before=json.loads((output/'interrupted/phase.json').read_text())
                name=before['checkpoint_name']
                if Path(name).name!=name:raise ValueError('unsafe checkpoint basename')
                command+=['--_checkpoint',str(output/'interrupted'/name),'--_checkpoint-sha',before['checkpoint_sha256']]
                source_snapshot=inventory(output/'interrupted')
            with (output/(phase+'.log')).open('xb') as log:
                result=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,
                                      timeout=min(60,remaining))
            if result.returncode:raise RuntimeError('recovery probe worker failed: '+phase)
        import torch
        a=json.loads((output/'continuous/phase.json').read_text())
        b=json.loads((output/'interrupted/phase.json').read_text())
        c=json.loads((output/'resumed/phase.json').read_text())
        if [a['status'],b['status'],c['status']]!=['COMPLETE','INTERRUPTED_AT_STEP2','COMPLETE']:
            raise ValueError('unexpected recovery phase status')
        if a['identity']!=b['identity'] or a['identity']!=c['identity']:
            raise ValueError('fresh-process fixture identity drift')
        if (a['optimized_rows_this_process']!=b['optimized_rows_this_process']+c['optimized_rows_this_process']
                or sorted(a['optimized_rows_this_process'])!=list(range(1,18))
                or a['sampler_state']!=c['sampler_state'] or a['sampler_state']['consumed_windows']!=9
                or a['rng_draws']!=c['rng_draws']):
            raise ValueError('sample ledger/sampler/RNG mismatch')
        if source_snapshot!=inventory(output/'interrupted'):
            raise ValueError('interrupted source artifacts changed during resume')
        left=torch.load(output/'continuous/final.pt',map_location='cpu',weights_only=True)
        right=torch.load(output/'resumed/final.pt',map_location='cpu',weights_only=True)
        tolerance=0.0 if device=='cpu' else 1e-5
        maximum=compare_tree(left,right,atol=tolerance,rtol=tolerance)
        predictions=compare_tree(torch.tensor(a['predictions']),torch.tensor(c['predictions']),
                                  atol=tolerance,rtol=tolerance)
        report={'status':'passed_synthetic_recovery','device':device,
            'scope':'same-runtime optimizer-boundary interruption/fresh-process resume; not hard-kill/Volume durability',
            'cuda_mid_epoch_resume_verified':device=='cuda','cpu_mid_epoch_resume_verified':device=='cpu',
            'gate4_pass':False,'training_targets_per_logical_branch':17,'updates_per_complete_branch':5,
            'optimizer_updates_total_all_processes':10,'optimized_row_ledger_exact':True,
            'rng_exact':True,'sampler_exact':True,'interrupted_source_immutable':True,
            'floating_atol':tolerance,'floating_rtol':tolerance,'max_state_abs_delta':maximum,
            'max_prediction_abs_delta':predictions,'elapsed_seconds':time.perf_counter()-started,
            'phase_timeout_seconds':60,'total_timeout_seconds':180,
            'source_identity':a['identity'],'phase_pids':[a['pid'],b['pid'],c['pid']],
            'gpu_name':c['gpu_name'],'peak_vram_bytes':c['peak_vram_bytes']}
        write_json(output/'report.json',report)
    except BaseException as error:
        write_json(output/'failure.json',{'status':'FAILED','error_type':type(error).__name__,
                   'error':str(error),'device':device,'gate4_pass':False})
        raise
    finally:
        write_json(output/'SHA256.json',{p.relative_to(output).as_posix():sha(p)
            for p in sorted(output.rglob('*')) if p.is_file() and p.name!='SHA256.json'})
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device',required=True,choices=['cpu','cuda'])
    parser.add_argument('--output-dir',required=True,type=Path)
    parser.add_argument('--_worker-phase',choices=['continuous','interrupted','resumed'],help=argparse.SUPPRESS)
    parser.add_argument('--_checkpoint',type=Path,help=argparse.SUPPRESS)
    parser.add_argument('--_checkpoint-sha',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args._worker_phase:_worker(args)
    else:print(json.dumps(run_probe(args.output_dir,args.device),ensure_ascii=False))
