"""Chuẩn bị A1 nối epoch1, canary checkpoint thật và budget guard; chưa dispatch."""
import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
OLD=ROOT/'research_tracking/runs/junyi-a1-selected-20261113-01'
RUN='modal-junyi-a1-b128-h100-20261113-06'
CPU='modal-junyi-a1-selection-cpu-20261113-01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    old_request=json.loads((OLD/'request05.json').read_text())
    gate=json.loads((ROOT/'experiments/akt/results'/CPU/'receipt.json').read_text())
    assert gate['status']=='MODAL_CPU_GATE_VERIFIED' and gate['download_inventory_verified'] is True
    preparation=json.loads((HERE/'source-gate-preparation.json').read_text())
    assert gate['source_build_sha256']==preparation['source_build_sha256']
    checkpoint=ROOT/'experiments/akt/results/modal-junyi-a1-b128-h100-20261113-05/checkpoints/train-epoch-001/state.pt'
    assert sha(checkpoint)=='eb614e5fcd3f8d1c3d19d51d0c088ee075e6924ca8560fbf1b893b9df9d224e9'
    parity=json.loads((HERE/'actual-checkpoint-parity.json').read_text())
    assert parity['max_absolute_drift']==0 and all(parity['checks'].values())
    worker=(OLD/'gpu_worker.py').read_text(encoding='utf-8')
    begin=worker.index('    actual_wall=min(')
    end=worker.index('    gate=require_gate2_evidence',begin)
    worker=worker[:begin]+'''    source_config=json.loads(Path('/opt/actual-checkpoint-cpu-parity.json').read_text())['source_identity']['config']
    source_config.update(project_root=ROOT,source_root=ROOT/'artifacts/akt/dependencies/upstream',
        output_dir=ROOT/'experiments/akt/results'/RUN,run_id=RUN)
    source_config['betas']=tuple(source_config['betas'])
    config=AKTConfig(**source_config)
    assert config.max_seconds==1500 and config.max_wall_seconds==1600
'''+worker[end:]
    insertion='''    checkpoint=ROOT/REQUEST['resume_checkpoint']
    assert sha(checkpoint)==REQUEST['resume_checkpoint_sha256']
    canary=ROOT/'research_tracking/runs/junyi-a1-selection-cache-20261113-01/check_actual_checkpoint.py'
    with (OPERATION/'actual-checkpoint-cuda.log').open('x') as log:
        proof=subprocess.run([sys.executable,'-B',str(canary),'--device','cuda',
            '--output-name','actual-checkpoint-gpu-parity.json'],cwd=ROOT,
            stdout=log,stderr=subprocess.STDOUT,timeout=180)
    proof_file=canary.parent/'actual-checkpoint-gpu-parity.json'
    assert proof.returncode==0 and proof_file.is_file(),'Actual checkpoint CUDA canary failed'
    proof_result=json.loads(proof_file.read_text())
    assert proof_result['status']=='PASS_ACTUAL_CHECKPOINT_CUDA_SOURCE2_COMPACT_EXACT'
    assert proof_result['max_absolute_drift']==0 and all(proof_result['checks'].values())
    shutil.copyfile(proof_file,OPERATION/proof_file.name)
    from knowledge_tracing.akt.research_junyi_transition import identity_sha256
    target_identity=json.loads(json.dumps(proof_result['source_identity']))
    target_identity['config']=json.loads(json.dumps(asdict(config),default=str))
    build=json.loads(Path(gate['evidence_path']).read_text())['build_hashes']
    target_identity['source_build_sha256']=identity_sha256(build)
    target_identity['batch_factory'].update(context_backend='compact-a1-v1',graph_context_cache=None)
    target_identity.update(prefetch_train_windows=True,prefetch_selection_windows=True)
    assert target_identity['profile']==asdict(profile)
    transition_file=OPERATION/'source-transition-receipt.json'
    evidence=dict(status='PASS_ACTUAL_CHECKPOINT_PARITY',checkpoint_sha256=sha(checkpoint),
        source_identity_sha256=identity_sha256(proof_result['source_identity']),
        target_identity_sha256=identity_sha256(target_identity),max_absolute_drift=0.,checks=proof_result['checks'])
    write(transition_file,dict(source_identity=proof_result['source_identity'],evidence=evidence))
'''
    marker="    prepared=dict(encoding_sha256="
    assert worker.count(marker)==1
    worker=worker.replace(marker,insertion+marker)
    marker="    grant=dict(status='USER_APPROVED'"
    worker=worker.replace(marker,"    prepared.update(resume_checkpoint_sha256=sha(checkpoint),source_transition_sha256=sha(transition_file),\n        prefetch_train_windows=True,prefetch_selection_windows=True)\n"+marker)
    marker='        graph_condition=condition,comparison_reference_file=reference_path,'
    worker=worker.replace(marker,'''        resume_checkpoint=checkpoint,expected_resume_sha256=sha(checkpoint),
        source_transition_file=transition_file,expected_source_transition_sha256=sha(transition_file),
        prefetch_train_windows=True,prefetch_selection_windows=True,
'''+marker)
    worker=worker.replace("('PARTIAL_SELECTED_ONLY_NOT_FINAL','JUNYI_A0_SELECTED_ONLY_COMPLETE')","('PARTIAL_SELECTED_ONLY_NOT_FINAL','JUNYI_A0_SELECTED_ONLY_COMPLETE','JUNYI_A1_SELECTED_ONLY_COMPLETE')")
    # Probe CUDA cần frozen request/source/checkpoint tại đúng path đã pin.
    controller=(OLD/'gpu_controller.py').read_text(encoding='utf-8')
    marker="    for key,target in (('source','/opt/kltn-input.zip')"
    extra='''    paths['/opt/actual-checkpoint-cpu-parity.json']=BUNDLE/'actual-checkpoint-parity.json'
    paths['/opt/kltn/research_tracking/runs/junyi-a1-selection-cache-20261113-01/check_actual_checkpoint.py']=BUNDLE/'check_actual_checkpoint.py'
    old=ROOT/'research_tracking/runs/junyi-a1-selected-20261113-01'
    paths['/opt/kltn/research_tracking/runs/junyi-a1-selected-20261113-01/request05.json']=old/'request05.json'
    source2=ROOT/'artifacts/akt/modal/junyi-a1-selected-20261113-01/source02.zip'
    paths['/opt/kltn/artifacts/akt/modal/junyi-a1-selected-20261113-01/source02.zip']=source2
    paths['/opt/kltn/'+request['resume_checkpoint']]=ROOT/request['resume_checkpoint']
'''
    assert controller.count(marker)==1
    controller=controller.replace(marker,extra+marker)
    controller=controller.replace("scaledown_window=60", "scaledown_window=2")
    for status in ("('PARTIAL_SELECTED_ONLY_NOT_FINAL','JUNYI_A0_SELECTED_ONLY_COMPLETE')",):
        controller=controller.replace(status,"('PARTIAL_SELECTED_ONLY_NOT_FINAL','JUNYI_A0_SELECTED_ONLY_COMPLETE','JUNYI_A1_SELECTED_ONLY_COMPLETE')")
    for name,text in [('gpu_worker.py',worker),('gpu_controller.py',controller)]:
        ast.parse(text)
        with (HERE/name).open('x',encoding='utf-8') as stream:stream.write(text)
    for name in ('replay_a0_validation.py','a0-validation-replay-plan.json',
                 'a0-batched-comparison-reference03.json','a0-validation-replay03.json'):
        with (HERE/name).open('xb') as stream:stream.write((OLD/name).read_bytes())
    request=copy.deepcopy(old_request)
    request.update(run_id=RUN,allocation_id='junyi-a1-compact-resume-h100-20261113-01',
        authorized_batch_usd=3,reserved_usd_per_run=3,
        approval_reference='Người dùng yêu cầu nối A1 H100 sau tối ưu, cho phép tự phân bổ tranche trong tổng30USD.',
        initialization='verified_source2_epoch1_resume_validation_pending',
        resume_checkpoint=checkpoint.relative_to(ROOT).as_posix(),resume_checkpoint_sha256=sha(checkpoint),
        source_build_sha256=gate['source_build_sha256'],prefetch_train_windows=True,prefetch_selection_windows=True,
        selection_disk_cache_enabled=False,graph_context_disk_cache_enabled=False,
        actual_checkpoint_cuda_canary_required=True,worker_sha256=sha(HERE/'gpu_worker.py'))
    request['archives']['source']=dict(path=preparation['source'],sha256=preparation['source_sha256'])
    archive=ROOT/'experiments/akt/results'/CPU/'artifacts.zip'
    request['archives']['cpu_gate']=dict(path=archive.relative_to(ROOT).as_posix(),sha256=sha(archive))
    for key in ('prior_partial_run','prior_partial_checkpoint','prior_partial_checkpoint_sha256'):
        request.pop(key,None)
    write_path=HERE/'h100-request.json'
    with write_path.open('x',encoding='utf-8') as stream:stream.write(json.dumps(request,ensure_ascii=False,indent=2)+'\n')
    result=dict(status='H100_RESUME_PREPARED_NOT_DISPATCHED',run_id=RUN,source_build_sha256=gate['source_build_sha256'],
        request_sha256=sha(write_path),worker_sha256=sha(HERE/'gpu_worker.py'),controller_sha256=sha(HERE/'gpu_controller.py'),
        per_run_cap_usd=3,source_epoch_reused=1,automatic_retry=False,
        financial_source='https://modal.com/pricing',h100_usd_per_second=.001097,
        conservative_max_total_usd=2160*(.001097+4*.00003942+12*.00000667),
        limits_vi='Worker kiểm CUDA checkpoint thật trước resume. Disk cache selection/graph tắt vì lợi ích chưa đủ. '
                  'Gate/rate/cap phải kiểm lại trước dispatch. Không hotpatch source khi GPU chạy.')
    assert result['conservative_max_total_usd']<3
    (HERE/'h100-preparation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    main()
