"""Chuẩn bị tiếp source frozen từ partial epoch7, không dispatch hoặc train lại."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
LOGICAL='modal-junyi-a1-b128-h100-20261113-07'
EXECUTION='modal-junyi-a1-b128-h100-20261113-08'


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    native=ROOT/'experiments/akt/results'/LOGICAL
    receipt=json.loads((native/'receipt.json').read_text())
    assert receipt['download_inventory_verified'] and receipt['status']=='PARTIAL_SELECTED_ONLY_NOT_FINAL'
    assert json.loads((native/'app-budget-guard.json').read_text())['stop_acknowledged']
    assert sha(native/'artifacts.zip')==receipt['archive_sha256']
    summary=json.loads((HERE/'tranche07-summary.json').read_text())
    latest=summary['latest_checkpoint']
    names=sorted(name for name in receipt['checkpoint_transfers'] if name.startswith('epoch-') or name==latest)
    controls={}
    for name in ('run-manifest.json','initial-backbone.json','source-transition.json'):
        path=native/name;controls[path.relative_to(ROOT).as_posix()]=path.read_bytes()
    identity=json.loads(controls['experiments/akt/results/'+LOGICAL+'/run-manifest.json'])
    for name in names:
        for filename,pin in receipt['checkpoint_transfers'][name]['files'].items():
            path=native/'checkpoints'/name/filename
            assert path.stat().st_size==pin['bytes'] and sha(path)==pin['sha256']
            controls[path.relative_to(ROOT).as_posix()]=path.read_bytes()
    directory=ROOT/'artifacts/akt/modal'/EXECUTION;directory.mkdir(parents=True,exist_ok=False)
    archive=directory/'resume-control.zip'
    pins={name:hashlib.sha256(raw).hexdigest() for name,raw in controls.items()}
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=1) as saved:
        for name,raw in controls.items():saved.writestr(name,raw)
        saved.writestr('MANIFEST.json',json.dumps(dict(files=pins),sort_keys=True))
    # Cùng worker đã nghiệm thu, bỏ source-transition/canary đã đạt ở07.
    worker=(HERE/'gpu_worker.py').read_text(encoding='utf-8')
    worker=worker.replace("RUN = REQUEST['run_id']", "EXECUTION = REQUEST['run_id']\nRUN = REQUEST['logical_run_id']")
    worker=worker.replace("(RUN+'-operation')", "(EXECUTION+'-operation')")
    worker=worker.replace("    extract('/opt/junyi-data.zip')", "    extract('/opt/junyi-data.zip')\n    extract('/opt/resume-control.zip')")
    worker=worker.replace("source_config=json.loads(Path('/opt/actual-checkpoint-cpu-parity.json').read_text())['source_identity']['config']",
        "source_config=json.loads((ROOT/'experiments/akt/results'/RUN/'run-manifest.json').read_text())['config']")
    start=worker.index("    checkpoint=ROOT/REQUEST['resume_checkpoint']")
    end=worker.index('    prepared=dict(encoding_sha256=',start)
    worker=worker[:start]+'''    checkpoint=ROOT/REQUEST['resume_checkpoint']
    assert sha(checkpoint)==REQUEST['resume_checkpoint_sha256']
'''+worker[end:]
    worker=worker.replace("prepared.update(resume_checkpoint_sha256=sha(checkpoint),source_transition_sha256=sha(transition_file),",
                          "prepared.update(resume_checkpoint_sha256=sha(checkpoint),")
    worker=worker.replace("        source_transition_file=transition_file,expected_source_transition_sha256=sha(transition_file),\n",'')
    controller=(ROOT/'experiments/akt/modal_junyi_main_resume.py').read_text(encoding='utf-8')
    controller=controller.replace("ROOT = Path(__file__).resolve().parent.parent.parent",
        "ROOT = Path(__file__).resolve().parents[3]\nimport sys\nsys.path.insert(0,str(ROOT/'experiments/akt'))")
    controller=controller.replace("BUNDLE = ROOT/'research_tracking/runs/junyi-main-selected-20261112-01'",
        "BUNDLE = Path(__file__).resolve().parent")
    controller=controller.replace("ROOT/'research_tracking/runs/junyi-a0-h100-batch128-20261112-01'",'BUNDLE')
    controller=controller.replace('modal-junyi-a0-b128-h100-','modal-junyi-a1-b128-h100-')
    controller=controller.replace('JUNYI_A0_SELECTED_ONLY_COMPLETE','JUNYI_A1_SELECTED_ONLY_COMPLETE')
    controller=controller.replace('scaledown_window=60','scaledown_window=2')
    controller=controller.replace('import os\n','import os\nimport time\n',1)
    controller=controller.replace('worker_request = dict(request,run_id=run_id,gpu=args.gpu)','worker_request = dict(request,run_id=run_id,gpu=args.gpu,local_deadline_unix=time.time()+2000)')
    marker="    for key,target in (('source','/opt/kltn-input.zip')"
    controller=controller.replace(marker,"    paths['/opt/a0-reused-reference.json']=bundle/'a0-batched-comparison-reference03.json'\n    paths['/opt/a0-reused-replay.json']=bundle/'a0-validation-replay03.json'\n"+marker)
    for name,source in [('resume_worker.py',worker),('resume_controller.py',controller)]:
        ast.parse(source)
        with (HERE/name).open('x',encoding='utf-8') as stream:stream.write(source)
    request=copy.deepcopy(json.loads((HERE/'h100-request07.json').read_text(encoding='utf-8')))
    request.update(run_id=EXECUTION,logical_run_id=LOGICAL,
        allocation_id='junyi-a1-same-source-resume-h100-20261113-01',authorized_batch_usd=3,reserved_usd_per_run=3,
        resume_checkpoint='experiments/akt/results/'+LOGICAL+'/checkpoints/'+latest+'/state.pt',
        resume_checkpoint_sha256=summary['checkpoint_sha256'],worker_sha256=sha(HERE/'resume_worker.py'),
        initialization='same_source_exact_partial_epoch7_resume',actual_checkpoint_cuda_canary_required=False,
        source_transition_required=False,previous_failed_attempt=None,prior_failure_reserved_upper_usd=0,
        decision_vi='Cùng source/Gate/config/logical07, khôi phục sampler/Adam/RNG từstep1797 củaepoch7. '
                    'Giữ cả6checkpoint đã validation để earlystop/nạpbest. Không restart hoặc đổi thông số.')
    request['archives']['resume_control']=dict(path=archive.relative_to(ROOT).as_posix(),sha256=sha(archive))
    with (HERE/'h100-request08.json').open('x',encoding='utf-8') as stream:
        stream.write(json.dumps(request,ensure_ascii=False,indent=2)+'\n')
    assert identity['config']['run_id']==LOGICAL
    assert identity['source_build_sha256']==request['source_build_sha256']
    result=dict(status='SAME_SOURCE_RESUME_PREPARED_NOT_DISPATCHED',logical_run_id=LOGICAL,execution=EXECUTION,
        preserved_epoch_checkpoints=names,source_checkpoint_sha256=summary['checkpoint_sha256'],
        control_archive_sha256=sha(archive),control_archive_bytes=archive.stat().st_size,
        source_build_sha256=identity['source_build_sha256'],remaining_epoch7_steps=21,
        source_frozen=True,new_cpu_gate_required=False)
    (HERE/'resume08-preparation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
