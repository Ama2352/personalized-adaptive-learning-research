"""Đọc path thực trên CPU mount giống H100, không học hoặc dùng GPU."""
from pathlib import Path
import json,os,sys

def probe():
    import subprocess,os
    code='''import json,sys
from pathlib import Path
sys.path[:0]=['/opt/kltn/src','/opt/kltn/scripts/akt']
import run_junyi_refit as cli
from knowledge_tracing.akt.config import load_config,ResearchCUDAExecutionProfile,PROJECT_ROOT
w=json.loads(Path('/opt/kltn/gpu-stage-request.json').read_text())
r=json.loads(cli.pinned(w['refit_request']).read_text())
p=ResearchCUDAExecutionProfile(**json.loads(cli.pinned(r['cuda_profile']).read_text()))
c=load_config(cli.pinned(r['config']),cuda_profile=p)
base=cli.ROOT/'experiments/akt/results'
print(json.dumps(dict(cli_root=str(cli.ROOT),config_project_root=str(PROJECT_ROOT),output=str(c.output_dir),output_resolved=str(c.output_dir.resolve()),expected_base=str(base),expected_base_resolved=str(base.resolve()),run_id=c.run_id,name=c.output_dir.name,results_is_symlink=base.is_symlink())))'''
    result=subprocess.run(['/opt/kltn/.venv/bin/python','-B','-c',code],cwd='/opt/kltn',env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,timeout=45)
    return dict(returncode=result.returncode,stdout=result.stdout,stderr=result.stderr)

if __name__=='__main__':
    ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
    os.environ.update(MODAL_CONFIG_PATH=str(ROOT/'artifacts/akt/private/modal.toml'),MODAL_PROFILE='kltn')
    sys.path.insert(0,str(ROOT/'experiments/akt'))
    import modal
    from modal_budget_guard import ModalRunDeadline,ModalAppBudgetGuard,PendingOwnedModalApp,stop_owned_app_cli
    app=modal.App('kltn-akt-refit-cpu-path-probe-20261114-03')
    volume=modal.Volume.from_name('kltn-staged-junyi-a0-refit-20261114-01-outputs',version=2)
    function=app.function(image=modal.Image.from_id('im-RWnD8Bgze9GpAnWtYuPyil'),cpu=1,memory=1024,timeout=60,
        max_containers=1,retries=0,scaledown_window=2,volumes={'/opt/kltn/experiments/akt/results':volume.with_mount_options(sub_path='/outputs')})(probe)
    deadline=ModalRunDeadline(150)
    with ModalAppBudgetGuard(PendingOwnedModalApp('refit-cpu-path-probe-20261114-03',app.name,lambda:app.app_id),deadline,stop_app=stop_owned_app_cli,diagnostic_path=HERE/'cpu-path-probe03-guard.json') as guard:
        with modal.enable_output(),app.run(environment_name='main'):
            result=function.spawn().get(timeout=guard.remaining())
    assert json.loads((HERE/'cpu-path-probe03-guard.json').read_text())['stop_acknowledged']
    (HERE/'cpu-path-probe03-result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
