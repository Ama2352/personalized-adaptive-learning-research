"""Nghiệm thu A2 selected-fit, chấm file dự đoán và xuất gọn model trên D."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
RUN=ROOT/'experiments/akt/results/modal-junyi-a2-staged-h100-20261114-10'
LOGICAL=RUN/'files/outputs/junyi-a2-expert-selected-20261114-01'
EXPORT=ROOT/'experiments/akt/results/model-export-a2-batch128-20261114-01'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write(path,value):
    if path.exists():
        if read(path)!=value:
            raise ValueError('Artifact đã tồn tại với nội dung khác, cần giữ phiên bản riêng')
        return
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2)
        stream.write('\n')


def score_predictions(path,terminal):
    import numpy as np
    import pandas as pd
    from knowledge_tracing.gam_kt.evaluation import _metrics
    count=terminal['validation']['targets']
    probabilities=np.empty(count,dtype=np.float32)
    labels=np.empty(count,dtype=np.int8)
    population=hashlib.sha256()
    seen=set()
    previous_user=None
    previous_key=None
    previous_rank=-1
    observed=0
    with path.open(encoding='utf-8') as stream:
        for index,line in enumerate(stream):
            assert index<count
            row=json.loads(line)
            assert row['correct'] in (0,1) and row['prediction'] is not None
            user=row['user_id']
            key=(row['time_done'],row['source_row'])
            if user==previous_user:
                assert key>=previous_key and row['global_rank']==previous_rank+1
            else:
                assert user not in seen and row['global_rank']==0
                seen.add(user)
            previous_user,previous_key,previous_rank=user,key,row['global_rank']
            identity=(row['source_row'],user,row['exercise'],row['time_done'],row['correct'],row['suggested'],row['fold'])
            population.update(json.dumps(identity,separators=(',',':')).encode()+b'\n')
            probabilities[index]=row['prediction']
            labels[index]=row['correct']
            observed=index+1
    assert observed==count and len(seen)==15847
    assert np.isfinite(probabilities).all() and ((probabilities>=0)&(probabilities<=1)).all()
    assert population.hexdigest()==terminal['validation']['population_sha256']
    assert hashlib.sha256(probabilities.tobytes()).hexdigest()==terminal['validation']['probability_sha256']
    metrics=_metrics(pd.DataFrame(dict(correct=labels,prediction=probabilities.astype(np.float64))))
    return dict(rows=count,learners=len(seen),metrics=metrics,coverage=dict(supported=count,oov=0),
        probability_sha256=terminal['validation']['probability_sha256'],
        population_sha256=population.hexdigest(),chronology_verified=True,
        metric_source='knowledge_tracing.gam_kt.evaluation._metrics',ece_bins=15,
        native_epoch_selection_bce=terminal['validation']['native_bce'],
        interpretation_vi='Điểm trên selection dùng chọn epoch. Đánh giá độc lập và khoảng bất định còn chờ.')


def main():
    sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments/akt')]
    import torch
    from knowledge_tracing.akt.comparison_contract import TRAINING_FIELDS,require_matched_candidate
    torch.set_num_threads(1)
    complete=read(RUN/'COMPLETE.json')
    stage=read(RUN/'stage-result.json')
    remote=read(RUN/'remote-inventory.json')
    guard=read(RUN/'app-budget-guard.json')
    terminal=read(LOGICAL/'selected-terminal.json')
    assert complete['status']==stage['status']=='LOCAL_ARTIFACTS_VERIFIED_GPU_STOPPED'
    assert guard['stop_acknowledged'] is True and complete['files']==len(remote['files'])
    assert stage['worker_status']==terminal['status']==remote['status']=='JUNYI_A2_SELECTED_ONLY_COMPLETE'
    assert terminal==remote['worker_result']['terminal']
    assert terminal['full_role_coverage'] and terminal['comparison_population_matched']
    assert terminal['complete_epochs']==12 and terminal['selected_epoch']==9
    assert terminal['optimizer_steps']==12*1818 and terminal['trained_targets']==12*13347331
    checkpoint=LOGICAL/'checkpoints/epoch-009/state.pt'
    metadata=read(checkpoint.parent/'metadata.json')
    assert sha(checkpoint)==terminal['checkpoint_sha256']==metadata['checkpoint_sha256']
    payload=torch.load(checkpoint,map_location='cpu',weights_only=True)
    assert payload['progress']['epoch']==9 and payload['progress']['validation_complete'] is True
    assert payload['identity']==metadata['identity']
    assert all(torch.isfinite(value).all().item() for value in payload['model_state_dict'].values())
    assert payload['optimizer_state_dict']['state'] and len(payload['cuda_rng'])==1
    assert all(key in payload for key in ('python_rng','numpy_rng','torch_rng'))
    del payload
    request=read(ROOT/'artifacts/akt/staged/junyi-a2-expert-20261114-03/project/gpu-stage-request.json')
    reference=read(ROOT/request['comparison_reference_file'])['reference']
    admission=read(next(LOGICAL.glob('comparison-admission-*.json')))
    candidate=dict(admission['candidate'],observed_selection_population_sha256=terminal['validation']['population_sha256'])
    require_matched_candidate(reference,candidate,observed=True)
    peers=[]
    for folder in ('model-export-a0-batch128-20261112-01','model-export-a1-batch128-20261113-01'):
        peer=read(ROOT/'experiments/akt/results'/folder/'MODEL_INDEX.json')
        identity=peer['metadata']['identity']
        assert all(identity['config'][key]==metadata['identity']['config'][key] for key in TRAINING_FIELDS)
        assert identity['inputs']==metadata['identity']['inputs']
        assert identity['encoding']==metadata['identity']['encoding']
        assert peer['selection_metrics']['population_sha256']==terminal['validation']['population_sha256']
        peers.append(dict(model=peer['model'],selected_epoch=peer['selected_epoch'],
            complete_epochs=peer['complete_epochs'],native_bce=peer['selection_metrics']['native_bce']))
    assert reference['initial_backbone_sha256']==terminal['initial_backbone_sha256']
    predictions=LOGICAL/terminal['predictions_file']
    assert sha(predictions)==terminal['predictions_sha256']
    metrics=score_predictions(predictions,terminal)
    write(HERE/'a2-selection-metrics.json',metrics)
    comparison=dict(status='MATCHED_DEVELOPMENT_SELECTION_INDEPENDENT_EVALUATION_PENDING',
        training_fields_matched=list(TRAINING_FIELDS),rows=1600343,initial_backbone_matched=True,
        models=peers+[dict(model='A2_EXPERT',selected_epoch=9,complete_epochs=12,
            native_bce=terminal['validation']['native_bce'])],
        a0_full_epoch_choice_replayed_batch128=False,
        limits_vi='A0 chọn epoch bằng batch1, riêng epoch9 đã replay batch128. A1/A2 dùng batch128. Các điểm selection chưa đủ kết luận hơn kém hoặc nhân quả.')
    write(HERE/'a2-comparison-audit.json',comparison)
    acceptance=dict(status='PASS_A2_SELECTED_FIT80_ARTIFACT_AND_PREDICTION_CONTRACT',
        selected_epoch=9,complete_epochs=12,train_targets_per_epoch=13347331,
        selection_targets=1600343,checkpoint_sha256=sha(checkpoint),
        probability_sha256=terminal['validation']['probability_sha256'],
        predictions_sha256=sha(predictions),archive_sha256=complete['archive_sha256'],
        archive_files=complete['files'],optimizer_rng_verified=True,
        checkpoint_tensors_finite=True,chronology_verified=True,model_comparison_boundary_verified=True,
        refit_completed=False,calibration_completed=False,independent_evaluation_completed=False,gpu_stopped=True)
    write(HERE/'a2-final-acceptance.json',acceptance)
    sources={'source.zip':ROOT/'artifacts/akt/modal/junyi-a2-a3-final-20261114-03/source.zip',
        'encoding.json':ROOT/request['inputs']['encoding_file'],
        'encoding-receipt.json':ROOT/request['inputs']['encoding_receipt'],
        'graph.json':ROOT/request['graph_file'],'roles.json':ROOT/request['inputs']['roles_path'],
        'confidence.json':ROOT/request['confidence_file'],
        'confidence-fit-manifest.json':ROOT/request['confidence_fit_artifact'],
        'selected-request.json':ROOT/'artifacts/akt/staged/junyi-a2-expert-20261114-03/project/gpu-stage-request.json',
        'execution-controller.py':ROOT/'experiments/akt/modal_junyi_staged.py',
        'execution-artifact-io.py':ROOT/'experiments/akt/junyi_staged_io.py',
        'execution-controller-tests.py':ROOT/'tests/akt/test_junyi_staged_local.py',
        'execution-controller-tests.log':HERE/'staged-resume-regression13.log',
        'execution-resource-choice.json':HERE/'a2-resume-resource-choice10.json',
        'runtime-linux-cuda.lock.txt':ROOT/request['runtime_lock_file'],
        'runtime-cuda.json':RUN/'files/outputs/modal-junyi-a2-staged-h100-20261114-10-operation/runtime.json',
        'upstream-identity.json':HERE/'upstream-portable-inventory.json',
        'upstream-LICENSE':ROOT/'artifacts/akt/staged/junyi-a2-expert-20261114-03/project/artifacts/akt/dependencies/upstream/LICENSE',
        'comparison-audit.json':HERE/'a2-comparison-audit.json','selection-metrics.json':HERE/'a2-selection-metrics.json',
        'acceptance.json':HERE/'a2-final-acceptance.json'}
    pins={name:dict(source=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,sha256=sha(path))
          for name,path in sources.items()}
    assert pins['confidence.json']['sha256']==request['confidence_sha256']
    assert not EXPORT.exists() and EXPORT.resolve().drive.upper()=='D:'
    write(HERE/'a2-export-plan.json',dict(source_checkpoint=checkpoint.relative_to(ROOT).as_posix(),
        checkpoint_sha256=sha(checkpoint),destination=str(EXPORT),support_inputs=pins))
    staging=EXPORT.with_name(EXPORT.name+'.building')
    staging.mkdir(exist_ok=False)
    temporary=staging/'A2_JUNYI_SELECTED.pt.partial'
    with checkpoint.open('rb') as original,temporary.open('xb') as target:
        shutil.copyfileobj(original,target,1024*1024)
        target.flush()
        os.fsync(target.fileno())
    assert sha(temporary)==terminal['checkpoint_sha256']
    temporary.rename(staging/'A2_JUNYI_SELECTED.pt')
    with zipfile.ZipFile(staging/'SUPPORT.zip','x',zipfile.ZIP_DEFLATED) as saved:
        for name,path in sources.items():
            assert sha(path)==pins[name]['sha256']
            saved.write(path,name)
    with zipfile.ZipFile(staging/'SUPPORT.zip') as saved:
        assert set(saved.namelist())==set(pins)
        assert all(hashlib.sha256(saved.read(name)).hexdigest()==pin['sha256'] for name,pin in pins.items())
    index=dict(model='A2_EXPERT',dataset='Junyi',phase='selected_fit80',batch_size=128,
        selected_epoch=9,complete_epochs=12,checkpoint_file='A2_JUNYI_SELECTED.pt',
        checkpoint_sha256=sha(checkpoint),checkpoint_bytes=checkpoint.stat().st_size,metadata=metadata,
        selection_metrics=terminal['validation'],standard_selection_metrics=metrics,
        model_class='knowledge_tracing.akt.research_junyi_graph_model.JunyiGraphAKTAdapter',
        variant='A2',graph_enabled=True,compact_context=True,graph_condition_sha256=terminal['graph_condition_sha256'],
        support_sha256=sha(staging/'SUPPORT.zip'),support_inventory=pins,comparison_audit=comparison,
        source_checkpoint=checkpoint.relative_to(ROOT).as_posix(),refit_completed=False,
        calibration_completed=False,independent_evaluation_completed=False)
    write(staging/'MODEL_INDEX.json',index)
    (staging/'README.md').write_text('''# A2 Junyi đã chọn checkpoint

A2 dùng backbone AKT NonRasch và đồ thị có trọng số độ tin cậy cho từng cạnh, fit từ TRAIN80. Đã học 12 epoch trên 13.347.331 tương tác mỗi epoch, chọn epoch 9 theo min_delta 0,0001 và patience 3. Seed 42, batch train/selection 128, vocabulary 717 bài tập.

`A2_JUNYI_SELECTED.pt` giữ nguyên model, Adam, RNG và tiến độ. `MODEL_INDEX.json` giữ cấu hình và phạm vi. `SUPPORT.zip` giữ source numerical, encoding, graph, confidence cùng provenance và controller ngoài image. Checkpoint/predictions/logs trung gian nằm ở output theo run.

Pipeline đã nạp lại checkpoint và xuất đủ 1.600.343 dự đoán selection khớp lượt chọn epoch, 0 OOV. Refit, calibration và đánh giá độc lập còn chờ. Gói đã kiểm tải/nạp tensor trên CPU, API inference độc lập từ riêng gói export còn chờ kiểm.
''',encoding='utf-8')
    assert {path.name for path in staging.iterdir()}=={'A2_JUNYI_SELECTED.pt','MODEL_INDEX.json','SUPPORT.zip','README.md'}
    staging.rename(EXPORT)
    write(HERE/'a2-export-result.json',dict(status='EXPORTED_A2_SELECTED_ON_D',output=str(EXPORT),
        checkpoint_sha256=sha(EXPORT/'A2_JUNYI_SELECTED.pt'),files=sorted(path.name for path in EXPORT.iterdir())))
    ledger_path=ROOT/'research_tracking/COMPUTE_BUDGET.json'
    ledger=read(ledger_path)
    allocation='junyi-a2-staged-h100-20261114-10'
    assert len(ledger['new_allocations'])==1 and ledger['new_allocations'][0]['id']==allocation
    seconds=max(event['elapsed_seconds'] for event in guard['events'])+60
    upper=seconds*.00133472
    assert upper<=2.6
    settlement=dict(id=allocation,status='SELECTED_COMPLETE_ARTIFACTS_VERIFIED_APP_STOPPED',
        elapsed_upper_seconds=seconds,reserved_upper_closed_usd=upper,actual_isolated_cost_usd=None,
        stop_acknowledged=True)
    ledger['closed_reservations'].append(settlement)
    ledger['historical_usage_reserved_upper_usd']+=upper
    ledger['new_allocations']=[]
    assert ledger['historical_usage_reserved_upper_usd']+ledger['safety_and_final_inference_reserve_usd']<=30
    ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    write(HERE/'a2-tranche10-settlement.json',settlement)
    print(json.dumps(dict(status=acceptance['status'],export=str(EXPORT),metrics=metrics['metrics'])),flush=True)


if __name__=='__main__':
    main()
