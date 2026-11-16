"""Đối chiếu role metadata với export A0–A3, không đọc event/prediction/model."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView, JunyiResearchEncoding
from knowledge_tracing.akt.encoding import load_encoding
from knowledge_tracing.akt.research_junyi_roles import JunyiResearchRoles

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
REFIT=ROOT/'research_tracking/runs/junyi-refit-pipeline-20261114-01'
ROLE_NAMES=('train_users','selection_users','calibration_users','outer_validation_users')


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(payload):
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()


role_path=ROOT/'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01/roles.json'
payload=load(role_path)
for name in ROLE_NAMES:
    payload[name]=tuple(payload[name])
roles=JunyiResearchRoles(**payload)
groups={name:set(getattr(roles,name)) for name in ROLE_NAMES}
assert sum(map(len,groups.values()))==len(set().union(*groups.values()))
assert all(len(groups[name])==len(getattr(roles,name)) for name in ROLE_NAMES)
plan=load(REFIT/'epoch-plan.json')
assert plan['identity']==identity({k:v for k,v in plan.items() if k!='identity'})
assert roles.identity==plan['roles_identity']
refit=JunyiPhaseView(roles,'refit_union90',tuple(sorted((*roles.train_users,*roles.selection_users))),roles.identity)
calibration=JunyiPhaseView(roles,'calibration_predict',roles.calibration_users,roles.identity)
outer=JunyiPhaseView(roles,'outer_evaluation',roles.outer_validation_users,roles.identity)
encoding_receipt_path=ROOT/'artifacts/akt/window-cache/full-refit90-20261114-01.encoding.receipt.json'
encoding_receipt=load(encoding_receipt_path)
assert encoding_receipt['fit_view_identity']==refit.identity
assert encoding_receipt['phase_scope']=='refit_union90'
assert encoding_receipt['epoch_plan_identity']==plan['identity']
encoding_path=ROOT/'artifacts/akt/window-cache/full-refit90-20261114-01.encoding.json'
assert sha(encoding_path)==encoding_receipt['encoding_file_sha256']
encoding=JunyiResearchEncoding(load_encoding(encoding_path),refit)
assert encoding.identity==encoding_receipt['encoding_identity']
encoding.assert_for(calibration)
encoding.assert_for(outer)
cache_path=ROOT/'artifacts/akt/junyi-cohorts/outer4-selected-full-20261112-03/manifest.json'
cache=load(cache_path)
assert cache['roles_identity']==roles.identity and cache['full_role_coverage'] is True
assert all(cache[key] is False for key in ('calibration_events_included','outer_validation_events_included','holdout_events_included'))
counts={row['role']:row for row in cache['counts']}
train=JunyiPhaseView(roles,'select_train80',roles.train_users,roles.identity)
selection=JunyiPhaseView(roles,'raw_selection10',roles.selection_users,roles.identity)
source_identity=identity(dict(cache=sha(cache_path),roles=sha(role_path)))
selected_identity=identity(dict(source=source_identity,train=train.identity,selection=selection.identity,
    train_targets=counts['train']['targets'],selection_targets=counts['selection']['targets']))
assert selected_identity==plan['selected_inputs_identity']
targets=counts['train']['targets']+counts['selection']['targets']
refit_input_identity=identity(dict(view=refit.identity,targets=targets,source=source_identity,
                                  selected_inputs=selected_identity))
models={}
for variant in ('a0','a1','a2','a3'):
    index_path=ROOT/f'experiments/akt/results/model-export-{variant}-refit-20261114-01/MODEL_INDEX.json'
    index=load(index_path)
    stage=load(REFIT/f'stage-inputs-{variant}.json')
    pinned=stage['local_files'][role_path.relative_to(ROOT).as_posix()]
    assert pinned['sha256']==sha(role_path)
    assert index['identity']['plan_sha256']==plan['identity']
    assert index['identity']['encoding']==encoding_receipt['encoding_identity']
    assert index['identity']['inputs']==refit_input_identity
    assert stage['local_files'][cache_path.relative_to(ROOT).as_posix()]['sha256']==sha(cache_path)
    assert index['phase']=='refit90' and index['epochs']==plan['candidates'][variant.upper()]['epochs']
    models[variant]=dict(index_path=index_path.relative_to(ROOT).as_posix(),index_file_sha256=sha(index_path),
                        trained_checkpoint_sha256=index['checkpoint_sha256'],
                        shared_inputs_identity=index['identity']['inputs'],
                        calibration_completed=index['calibration_completed'],
                        independent_evaluation_completed=index['independent_evaluation_completed'])
assert len({row['shared_inputs_identity'] for row in models.values()})==1
result=dict(status='ROLE_METADATA_AND_REFIT_LINEAGE_VERIFIED',role_file_sha256=sha(role_path),
            role_identity=roles.identity,plan_identity=plan['identity'],counts={k:len(v) for k,v in groups.items()},
            pairwise_role_intersections=0,refit90_learners=len(refit.users),
            refit_input_identity=refit_input_identity,refit_targets=targets,
            selected_cache_manifest_sha256=sha(cache_path),refit_encoding_sha256=sha(encoding_path),
            refit_calibration_overlap=len(set(refit.users)&set(calibration.users)),
            refit_outer_overlap=len(set(refit.users)&set(outer.users)),
            calibration_outer_overlap=len(set(calibration.users)&set(outer.users)),
            views=dict(refit90=refit.identity,calibration=calibration.identity,outer=outer.identity),models=models,
            limits_vi=['Chỉ kiểm role metadata và binding trong export/stage, không mở checkpoint hoặc đọc events.',
                       'Chưa đối chiếu từng learner với assignments.parquet gốc, chưa tái kiểm source event/cache.',
                       'Bằng chứng này không tự cấp quyền evaluation hoặc xác nhận training đã đọc đúng mọi event.'])
(HERE/'ROLE_LINEAGE.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('models','views')},ensure_ascii=False))
