"""Đọc summary/model index hiện có, giữ nguyên model và dữ liệu gốc."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent

def load(relative):
    return json.loads((ROOT/relative).read_text(encoding='utf-8'))

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def tree_stats(relative):
    base=ROOT/relative;files=0;size=0;extensions=Counter()
    for directory,subdirs,names in os.walk(base,followlinks=False):
        subdirs[:]=[n for n in subdirs if n not in ('__pycache__','pycache','tmp','scratch')]
        for name in names:
            path=Path(directory)/name
            if path.is_symlink() or path.suffix=='.pyc':
                continue
            files+=1;size+=path.stat().st_size;extensions[path.suffix]+=1
    return dict(path=relative,files=files,bytes=size,extensions=dict(extensions))

def main():
    bkt=load('experiments/bkt_baseline/results/wsl_cpp/cv_cpp/cv/cv.json')
    final=load('experiments/bkt_baseline/results/wsl_cpp/final_cpp/final.json')
    gam=load('experiments/gam_kt/results/wsl_cpp/cv/cv.json')
    result=dict(as_of='2026-11-17',source_commit='d2ab9380',groups={})
    result['groups']['BKT']=dict(dataset='Junyi',phase='historical frozen CV5 + Development final refit + completed Test evaluation',
        cv_exercise_fit_instances=len(bkt['fit_log']),cv_instances_by_fold=dict(Counter(str(row['fold']) for row in bkt['fit_log'])),
        cv_parameter_location='cv_cpp/cv/cv.json:fit_log[].coefficients',cv_metrics=bkt['aggregate'],
        final_exercise_models=final['totals']['trained_exercises'],final_pkl_files=len(list((ROOT/'experiments/bkt_baseline/results/wsl_cpp/final_cpp/models').glob('*.pkl'))),
        final_training_interactions=final['totals']['training_interactions'],final_training_users=final['inputs']['development_students'],
        final_convergence=final['totals'],evidence=['docs/bkt-baseline-results.md','experiments/bkt_baseline/results/wsl_cpp/cv_cpp/cv/cv.json','experiments/bkt_baseline/results/wsl_cpp/final_cpp/final.json'],
        limitations=['Pilot num_fits used Developmentfold0 before historical CV; document selection-bias limitation','Historical Test already evaluated; preserve artifacts verbatim'],
        storage=tree_stats('experiments/bkt_baseline/results/wsl_cpp'))
    banks=[]
    for fold in range(5):
        path=f'experiments/gam_kt/results/wsl_cpp/cv/fold={fold}/difficulty.json'
        metadata=load(path);banks.append(dict(fold=fold,**metadata))
    result['groups']['GAM_KT']=dict(dataset='Junyi',phase='historical graph-free CV5',difficulty_banks=banks,
        cv_supported_metrics=gam['aggregate_mean_sample_sd']['supported']['overall'],
        cv_native_metrics=gam['aggregate_mean_sample_sd']['native']['overall'],coverage=gam['aggregate_mean_sample_sd']['coverage'],
        holdout_evaluation=bool(gam['holdout_test_used']),wall_seconds=gam['total_wall_seconds'],
        evidence=['experiments/gam_kt/results/wsl_cpp/cv/cv.json','experiments/gam_kt/results/wsl_cpp/cv/report_vi.md'],
        storage=tree_stats('experiments/gam_kt/results/wsl_cpp/cv'))
    selected=[];refits=[]
    for variant in ('a0','a1','a2','a3'):
        for phase,pattern,target in [('selected',f'model-export-{variant}-batch128-*',selected),('refit',f'model-export-{variant}-refit-20261114-01',refits)]:
            paths=list((ROOT/'experiments/akt/results').glob(pattern+'/MODEL_INDEX.json'))
            assert len(paths)==1
            index=paths[0];metadata=json.loads(index.read_text())
            checkpoint=index.parent/metadata['checkpoint_file']
            assert checkpoint.stat().st_size==metadata['checkpoint_bytes'] and sha(checkpoint)==metadata['checkpoint_sha256']
            target.append(dict(model=metadata['model'],phase=metadata['phase'],
                selected_epoch=metadata.get('selected_epoch'),complete_epochs=metadata.get('complete_epochs',metadata.get('epochs')),
                model_index=str(index.relative_to(ROOT)),checkpoint=str(checkpoint.relative_to(ROOT)),
                bytes=checkpoint.stat().st_size,sha256=metadata['checkpoint_sha256']))
    result['groups']['AKT_JUNYI']=dict(dataset='Junyi',phase='selected-fit80/refit90/calibration10/outerfold4 complete',
        selected=selected,refits=refits,selected_total_executed_epochs=sum(e['complete_epochs'] for e in selected),
        refit_total_epochs=sum(e['complete_epochs'] for e in refits),
        outer=load('research_tracking/runs/junyi-outer-real-20261117-01/OUTER_COMPARISON01.json'),
        drive_evaluation=load('research_tracking/runs/junyi-outer-real-20261117-01/DRIVE_FINAL_ARCHIVE_ACCEPTANCE01.json'))
    exported=load('experiments/akt/results/model-export-20261112-01/MODEL_INDEX.json')
    grade=[];legacy=[]
    for row in exported['entries']:
        path=ROOT/'experiments/akt/results/model-export-20261112-01'/row['destination']
        assert path.stat().st_size==row['bytes'] and sha(path)==row['sha256']
        entry={name:row.get(name) for name in ('model','dataset','phase','epoch','bytes','sha256','source_archive','source_member')}
        entry['checkpoint']=str(path.relative_to(ROOT))
        (grade if row['dataset']=='Grade10' else legacy).append(entry)
    assert len(grade)==7
    result['groups']['AKT_GRADE10']=dict(dataset='Grade10',phase='selected-fit only',models=grade,
        remaining=['refit90','calibration10','independent prediction/closed-loop/noise/ablation evaluation'],
        drive_model_index='research_tracking/runs/junyi-calibration-real-20261117-01/MODEL_DRIVE_COVERAGE03.json')
    result['groups']['AKT_LEGACY_EXPORTED']=dict(models=legacy,phase='historical engineering/archive, superseded by current Junyi exports')
    small=load('research_tracking/runs/baseline-evaluation-readiness-20261117-01/EXISTING_ARTIFACTS.json')
    for row in small:
        checkpoint=ROOT/row['checkpoint']['path']
        assert sha(checkpoint)==row['checkpoint']['sha256']
        terminal=load(row['directory']+'/selected-terminal.json')
        result['groups'][row['model']]=dict(**row,terminal=terminal,
            storage=tree_stats('experiments/'+row['model'].lower()+'/results'),
            research_status='engineering cohort only; main Grade10/Junyi lifecycle pending')
    result['groups']['GRAPH_GAM_KT']=dict(phase='legacy Paper2 online experiments and frozen results; modern matched lifecycle needs verification',
        source='paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20',
        current_diagnostic_outputs=tree_stats('experiments/gam_kt/results'),
        note='Online state and graph-package contrasts are not counted as standalone offline checkpoint exports')
    result['groups']['PAPER1']=dict(phase='legacy concept-Elo simulator, source/notebook and published paper',
        source='paper1/AdaptiveEngineSimulation_Enhanced.ipynb',authoritative='paper1/Paper1_RIVF_2026_Graph_vs_Policy_Adaptive_Sequencing.pdf')
    (B/'TRAINING_OUTPUTS_CATALOG_DRAFT01.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('ALL_MODEL_METADATA_CATALOG_BUILT',list(result['groups']),flush=True)
    print('BKT_CV_FITS',len(bkt['fit_log']),'BKT_FINAL',final['totals']['trained_exercises'],
        'AKT_SELECTED_EPOCHS',sum(e['complete_epochs'] for e in selected),'AKT_REFIT_EPOCHS',sum(e['complete_epochs'] for e in refits),flush=True)

if __name__=='__main__':
    main()
