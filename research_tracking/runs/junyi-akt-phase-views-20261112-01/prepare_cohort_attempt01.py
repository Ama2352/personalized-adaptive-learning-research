"""Cache một cohort Junyi nhỏ để kiểm pipeline CUDA, không fit model."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.akt.config import DataPaths
from knowledge_tracing.akt.research_junyi_roles import JunyiResearchRoles
from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView,iter_junyi_phase_learners


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--role-root',type=Path,default=ROOT/'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01')
    parser.add_argument('--train-users',type=int,required=True)
    parser.add_argument('--selection-users',type=int,required=True)
    parser.add_argument('--calibration-users',type=int,required=True)
    parser.add_argument('--max-events-per-user',type=int,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    counts=dict(train=args.train_users,selection=args.selection_users,calibration=args.calibration_users)
    if min(counts.values())<1 or sum(counts.values())>32 or not 1<=args.max_events_per_user<=300:
        raise ValueError('Bounded engineering cache supports at most32learners and300events each')
    output=args.output_dir.resolve()
    allowed=(ROOT/'artifacts/akt/junyi-cohorts').resolve()
    if output==allowed or not output.is_relative_to(allowed):
        raise ValueError('Unique output under artifacts/akt/junyi-cohorts required')
    role_root=args.role_root.resolve()
    if not role_root.is_relative_to(ROOT/'artifacts/akt/junyi-roles'):
        raise ValueError('Frozen Junyi research roles required')
    role_manifest=json.loads((role_root/'manifest.json').read_text())
    if sha(role_root/'roles.json')!=role_manifest['outputs_sha256']['roles.json']:
        raise ValueError('Role artifact digest mismatch')
    payload=json.loads((role_root/'roles.json').read_text())
    for name in ('train_users','selection_users','calibration_users','outer_validation_users'):
        payload[name]=tuple(payload[name])
    roles=JunyiResearchRoles(**payload)
    if roles.identity!=role_manifest['identity']:
        raise ValueError('Frozen role identity mismatch')
    paths=DataPaths(ROOT/'artifacts/bkt_baseline/derived/canonical',
        ROOT/'artifacts/bkt_baseline/splits/assignments.parquet',
        ROOT/'artifacts/bkt_baseline/derived/manifest.json',ROOT/'artifacts/bkt_baseline/splits/manifest.json')
    assignments_sha=sha(paths.assignments)
    if assignments_sha!=role_manifest['source_sha256']['artifacts/bkt_baseline/splits/assignments.parquet']:
        raise ValueError('Canonical outer assignments changed')
    pinned_sources=[paths.assignments,paths.canonical_manifest,paths.split_manifest,
        role_root/'roles.json',role_root/'manifest.json',Path(__file__).resolve(),
        ROOT/'src/knowledge_tracing/akt/research_junyi_data.py',
        ROOT/'src/knowledge_tracing/akt/research_junyi_roles.py']
    source_hashes={str(path.relative_to(ROOT)).replace('\\','/'):sha(path) for path in pinned_sources}
    output.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    manifest=dict(status='PREPARING',purpose='BOUNDED_JUNYI_CUDA_ENGINEERING_COHORT',
        roles_identity=roles.identity,outer_fold=4,seed=42,max_events_per_user=args.max_events_per_user,
        source_sha256=source_hashes,roles={},training_performed=False,
        full_junyi_benchmark=False,holdout_events_read=False,label_based_sampling=False)
    try:
        scopes=dict(train='select_train80',selection='raw_selection10',calibration='calibration_predict')
        for role,count in counts.items():
            candidates=getattr(roles,role+'_users')
            ranked=sorted(candidates,key=lambda user:(hashlib.sha256(
                f'junyi-akt-engineering-cohort-v1|42|{role}|{user}'.encode()).hexdigest(),user))
            users=tuple(sorted(ranked[:count]))
            view=JunyiPhaseView(roles,scopes[role],users,roles.identity)
            loaded=retained=truncated=0
            stats={}
            with (output/(role+'.jsonl')).open('x',encoding='utf-8') as stream:
                for learner in iter_junyi_phase_learners(paths,view,fetch_rows=4096,stats=stats):
                    if time.monotonic()-started>180:
                        raise TimeoutError('Bounded metadata/data cache preparation exceeded180seconds')
                    events=learner.events[:args.max_events_per_user]
                    record=dict(user_id=learner.user_id,fold=learner.fold,original_events=len(learner.events),
                        events=[dict(exercise=event.exercise,time_done=event.time_done,source_row=event.source_row,
                                     correct=event.correct,suggested=event.suggested) for event in events])
                    stream.write(json.dumps(record,ensure_ascii=False,separators=(',',':'))+'\n')
                    loaded+=len(learner.events);retained+=len(events);truncated+=len(events)<len(learner.events)
            manifest['roles'][role]=dict(users=list(users),phase_identity=view.identity,full_role_coverage=view.full_role_coverage,
                learners=len(users),loaded_events=loaded,retained_events=retained,truncated_learners=truncated,reader_stats=stats)
        for name,expected in source_hashes.items():
            if sha(ROOT/name)!=expected:
                raise ValueError('Inputs changed during cache preparation')
        manifest.update(status='BOUNDED_COHORT_PREPARED_NOT_TRAINED',elapsed_seconds=time.monotonic()-started,
            outputs_sha256={role+'.jsonl':sha(output/(role+'.jsonl')) for role in counts})
    except BaseException as error:
        manifest.update(status='FAILED',error_type=type(error).__name__,error=str(error))
        raise
    finally:
        (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:value for key,value in manifest.items() if key not in ('source_sha256','roles')},ensure_ascii=False))
    print(json.dumps({role:{key:value for key,value in details.items() if key not in ('users','reader_stats')} for role,details in manifest['roles'].items()},ensure_ascii=False))


if __name__=='__main__':
    main()
