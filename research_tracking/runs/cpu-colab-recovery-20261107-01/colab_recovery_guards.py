"""Kiểm logic notebook bằng subprocess giả; không chạy Colab/CUDA."""
import ast
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import types
import uuid

root = Path.cwd()
notebook = json.loads((root/'notebooks/akt_colab_synthetic.ipynb').read_text(encoding='utf-8'))
for cell in notebook['cells']:
    if cell['cell_type'] == 'code':
        ast.parse(''.join(cell['source']))
old = runpy.run_path(str(root/'research_tracking/runs/cpu-colab-first-20261107-01/guard_checks.py'))
records = old['exercise_guards'](root, notebook)
base = root/'artifacts/akt/local-tests'/('recovery-guards-'+uuid.uuid4().hex[:12])
base.mkdir()
code = ''.join(notebook['cells'][5]['source'])
for case in ('missing_cpu','missing_gpu','source_tamper','exit_nonzero','missing_report',
             'wrong_device','bad_ledger','bad_scope','bad_workload','bad_hash','pass'):
    directory=base/case;directory.mkdir()
    output=directory/'output';output.mkdir()
    (directory/'experiments/akt/results').mkdir(parents=True)
    (directory/'code.py').write_bytes(b'changed' if case=='source_tamper' else b'fixed')
    calls=[]
    def fake_run(command, **kwargs):
        calls.append(command)
        assert command[-3]=='cuda' and kwargs['timeout']==240
        kwargs['stdout'].write('MOCK recovery; không actual GPU\n')
        run=Path(command[-1]);run.mkdir()
        report={'status':'passed_synthetic_recovery','device':'cuda','gate4_pass':False,
                'training_targets_per_logical_branch':17,'updates_per_complete_branch':5,
                'optimizer_updates_total_all_processes':10,'floating_atol':1e-5,'floating_rtol':1e-5,
                'cuda_mid_epoch_resume_verified':True,'optimized_row_ledger_exact':True,
                'rng_exact':True,'sampler_exact':True,'interrupted_source_immutable':True,
                'max_state_abs_delta':0,'max_prediction_abs_delta':0,'elapsed_seconds':1}
        if case=='wrong_device':report['device']='cpu'
        if case=='bad_ledger':report['optimized_row_ledger_exact']=False
        if case=='bad_scope':report['gate4_pass']=True
        if case=='bad_workload':report['optimizer_updates_total_all_processes']=11
        if case!='missing_report':
            path=run/'report.json';path.write_text(json.dumps(report))
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            (run/'SHA256.json').write_text(json.dumps({'report.json':'0'*64 if case=='bad_hash' else digest}))
        return subprocess.CompletedProcess(command,1 if case=='exit_nonzero' else 0)
    fake=types.SimpleNamespace(run=fake_run,STDOUT=subprocess.STDOUT)
    namespace={'ROOT':directory,'OUTPUT':output,'ENV':{},'AKT_PY':'MOCK_ONLY',
        'CPU_PORTABILITY_OK':case!='missing_cpu','CUDA_LIFECYCLE_OK':case!='missing_gpu',
        'manifest':{'files':{'code.py':hashlib.sha256(b'fixed').hexdigest()}},
        'hashlib':hashlib,'json':json,'subprocess':fake}
    failed=False
    try:exec(compile(code,'<recovery-notebook-cell>','exec'),namespace)
    except (RuntimeError,ValueError,subprocess.CalledProcessError,FileNotFoundError):failed=True
    assert failed==(case!='pass'), case
    if case in ('missing_cpu','missing_gpu','source_tamper'):assert not calls
    records.append({'case':'recovery_'+case,'guard_pass':True,'actual_gpu_subprocess_invoked':False})
print(json.dumps({'status':'PASS','cases':records,'code_cells_ast_valid':True,
                  'scope':'Mocked notebook guards only; not actual Colab/CUDA'},ensure_ascii=False,indent=2))
