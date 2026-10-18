"""One-time, frozen-model holdout evaluation for Junyi standard BKT."""
from __future__ import annotations

import argparse, hashlib, importlib.metadata, importlib.util, json, math, os, platform, shutil, time
from datetime import datetime, timezone
from pathlib import Path
import sys

import duckdb
import numpy as np
import pandas as pd
import psutil

from pyBKT.models import Model

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / 'src'))
from knowledge_tracing.bkt_baseline.adapter import predict_skill
from knowledge_tracing.bkt_baseline.pipeline import _atomic_json, _slug, _write_shard
from knowledge_tracing.bkt_baseline.metrics import score_prediction_shards

ART = PROJECT / 'artifacts/bkt_baseline'
RUN = PROJECT / 'experiments/bkt_baseline/results/wsl_cpp/final_cpp'
OUT = PROJECT / 'experiments/bkt_baseline/results/wsl_cpp/test_cpp'
MODELS = RUN / 'models'
CANON_MANIFEST = ART / 'derived/manifest.json'
SPLIT_MANIFEST = ART / 'splits/manifest.json'
ASSIGNMENTS = ART / 'splits/assignments.parquet'
CV_MANIFEST = PROJECT / 'experiments/bkt_baseline/results/wsl_cpp/cv_cpp/run_manifest.json'
CV_RESULTS = PROJECT / 'experiments/bkt_baseline/results/wsl_cpp/cv_cpp/cv/cv.json'
EXPECTED = {
 'canonical_manifest_sha256':'035fb113fcbbd0f433fcda210d43ef279f6eb8163e0b3b4b72c9d4f066a02fb7',
 'assignments_sha256':'ee588c5b72fc214295e6eef1839b5110c884f43ab52ab4a792ca82e35812be20',
 'backend_sha256':'2c63eba0983cbff184f90a80ad811b921ce5b27b8f63425f136a0f62b00d553f',
 'patch_source_sha256':'a9d5e9d8ed77b834c77b129849ee707fdf6ba7e181caabe08f9885a3e77723b2',
 'em_source_sha256':'3ff8d17865d33a7be96dc357032883d5c3f62e2c4b1440a645cd4d609d07ac35',
}

def sha(path: Path) -> str:
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
 return h.hexdigest()

def atomic(path: Path, obj: dict):
 tmp=path.with_suffix(path.suffix+'.tmp')
 tmp.write_text(json.dumps(obj,indent=2,allow_nan=False),encoding='utf-8')
 tmp.replace(path)

def peak_rss(): return int(psutil.Process().memory_info().rss)

def prepare_test_stage(stage_dir: Path):
 """Materialize the immutable Test partition once as exercise-partitioned Parquet."""
 complete=stage_dir/'stage_complete.json'
 if not complete.exists():
  partial=stage_dir/'partial'
  if partial.exists(): shutil.rmtree(partial)
  partial.mkdir(parents=True)
  con=duckdb.connect(); con.execute("SET memory_limit='2GB'"); con.execute('SET threads=4')
  scratch=str(OUT/'scratch').replace("'","''"); con.execute(f"SET temp_directory='{scratch}'")
  cg=str((ART/'derived/canonical'/'**'/'*.parquet')).replace("'","''"); ap=str(ASSIGNMENTS).replace("'","''")
  con.execute(f"CREATE VIEW canonical AS SELECT * FROM read_parquet('{cg}',hive_partitioning=true)")
  con.execute(f"CREATE VIEW assignments AS SELECT * FROM read_parquet('{ap}')")
  target=str(partial.resolve()).replace("'","''")
  try:
   con.execute(f"COPY (SELECT c.source_row,c.user_id,c.exercise,c.time_done,c.order_id,c.correct,c.suggested FROM canonical c JOIN assignments a USING(user_id) WHERE a.partition='test' ORDER BY c.exercise,c.user_id,c.order_id) TO '{target}' (FORMAT PARQUET,PARTITION_BY (exercise),COMPRESSION ZSTD)")
  finally: con.close()
  files=list(partial.glob('exercise=*/*.parquet'))
  if not files: raise RuntimeError('Test staging created no exercise partitions')
  shutil.move(str(partial),str(stage_dir/'input'))
  atomic(complete,{'partition':'test','files':len(files),'source_canonical_manifest_sha256':EXPECTED['canonical_manifest_sha256'],'assignments_sha256':EXPECTED['assignments_sha256']})
 elif json.loads(complete.read_text(encoding='utf-8')).get('partition')!='test':
  raise RuntimeError('Test staging checkpoint has wrong partition')
 con=duckdb.connect(); con.execute("SET memory_limit='2GB'"); con.execute('SET threads=4')
 scratch=str(OUT/'scratch').replace("'","''"); con.execute(f"SET temp_directory='{scratch}'")
 glob=str((stage_dir/'input'/'**'/'*.parquet')).replace("'","''")
 con.execute(f"CREATE VIEW test_stage AS SELECT * FROM read_parquet('{glob}',hive_partitioning=true)")
 skills=[r[0] for r in con.execute('SELECT DISTINCT exercise FROM test_stage ORDER BY exercise').fetchall()]
 return con,skills

def preflight():
 if OUT.exists():
  existing={p.name for p in OUT.iterdir()}
  allowed={'pycache','predictions','scratch','input','partial','run_manifest.json','holdout_started.marker','stage_complete.json'}
  if existing-allowed or (OUT/'test.json').exists():
   raise FileExistsError(f'Refusing to reuse/overwrite prior Test outputs: {OUT}')
 for p in (OUT, Path(os.environ['TMPDIR']), Path(os.environ['PYTHONPYCACHEPREFIX'])):
  if not str(p.resolve()).startswith('/mnt/d/'): raise RuntimeError(f'Path outside D: {p}')
 final=json.loads((RUN/'final.json').read_text())
 fm=json.loads((RUN/'run_manifest.json').read_text())
 cv=json.loads(CV_MANIFEST.read_text(encoding='utf-8-sig'))
 cvres=json.loads(CV_RESULTS.read_text(encoding='utf-8-sig'))
 canonical=json.loads(CANON_MANIFEST.read_text()); split=json.loads(SPLIT_MANIFEST.read_text())
 if final.get('status')!='complete' or fm.get('status')!='complete' or cv.get('status')!='complete': raise RuntimeError('CV/final refit is not complete')
 if fm.get('holdout_test_used') is not False or final.get('holdout_test_used') is not False: raise RuntimeError('Final refit manifest indicates holdout was used')
 if len(fm['completed'])!=720 or len(final['fits'])!=720 or len(cv.get('skills',[]))!=720 or set(fm['completed'])!=set(cv['skills']): raise RuntimeError('Expected the same 720 fitted exercises as CV')
 identity=fm['identity']
 for key in ('canonical_manifest_sha256','assignments_sha256','backend_sha256','patch_source_sha256','em_source_sha256'):
  if identity.get(key)!=EXPECTED[key]: raise RuntimeError(f'Frozen identity mismatch: {key}')
 if sha(CANON_MANIFEST)!=EXPECTED['canonical_manifest_sha256'] or sha(ASSIGNMENTS)!=EXPECTED['assignments_sha256']: raise RuntimeError('Canonical data or global assignments hash mismatch')
 if sha(PROJECT/'third_party/pyBKT/source-cpp/pyBKT/fit/E_step.cpp')!=EXPECTED['patch_source_sha256'] or sha(PROJECT/'third_party/pyBKT/source-cpp/pyBKT/fit/EM_fit.py')!=EXPECTED['em_source_sha256']: raise RuntimeError('Patched source hash differs from frozen run')
 if sha(CV_MANIFEST)!=identity['cv_run_manifest_sha256']: raise RuntimeError('Final refit was not based on this completed CV manifest')
 if split.get('test_students')!=49522 or split.get('development_students')!=198084 or split.get('seed')!=42: raise RuntimeError('Frozen split metadata mismatch')
 cfg=identity['configuration']
 if cfg!={'num_fits':1,'forgets':False,'tol':0.005,'maxiter':100,'base_seed':42}: raise RuntimeError(f'Frozen config mismatch: {cfg}')
 if cv['protocol_identity'].get('num_fits')!=1 or cv['protocol_identity'].get('maxiter')!=100: raise RuntimeError('CV protocol mismatch')
 e=importlib.util.find_spec('pyBKT.fit.E_step'); p=importlib.util.find_spec('pyBKT.fit.predict_onestep_states')
 if not e or not e.origin.endswith('.so') or sha(Path(e.origin))!=EXPECTED['backend_sha256']: raise RuntimeError('Patched C++ E_step is not loaded')
 if not p or not p.origin.endswith('.so') or sha(Path(p.origin))!=cv['runtime'].get('predict_onestep_states_sha256'): raise RuntimeError('Compiled C++ one-step predictor is not loaded or differs from CV')
 runtime={'pyBKT_version':importlib.metadata.version('pyBKT'),'python_version':platform.python_version(),'numpy_version':np.__version__,'pandas_version':pd.__version__,'duckdb_version':duckdb.__version__,'scikit_learn_version':importlib.metadata.version('scikit-learn'),'scipy_version':importlib.metadata.version('scipy'),'psutil_version':psutil.__version__,'platform':platform.platform(),'E_step_path':str(Path(e.origin).resolve()),'E_step_sha256':sha(Path(e.origin)),'predict_onestep_states_path':str(Path(p.origin).resolve()),'predict_onestep_states_sha256':sha(Path(p.origin))}
 if runtime['pyBKT_version']!='1.4.3' or runtime['E_step_sha256']!=cv['runtime']['E_step_sha256']: raise RuntimeError('Runtime/backend differs from CV')
 # Verify all serialized models and manifest mapping before any holdout row query.
 final_map={r['exercise']:r for r in final['fits']}
 for skill, rec in fm['completed'].items():
  path=MODELS/rec['model_file']
  if not path.is_file() or sha(path)!=rec['model_sha256']: raise RuntimeError(f'Model hash mismatch: {skill}')
  s=final_map.get(skill)
  if not s or s['model_file']!=rec['model_file'] or s['model_sha256']!=rec['model_sha256']: raise RuntimeError(f'Model inventory mismatch: {skill}')
  if not np.isfinite(float(rec['final_training_log_likelihood'])): raise FloatingPointError(f'Non-finite likelihood: {skill}')
  vals=np.asarray([v for k in ('prior','learns','guesses','slips','forgets') for v in np.asarray(rec['parameters'][k],dtype=float).ravel()],dtype=float)
  if not np.isfinite(vals).all() or (vals<0).any() or (vals>1).any(): raise FloatingPointError(f'Invalid parameters: {skill}')
 # Synthetic boundary check: flipping response at t must not alter prediction at t.
 probe_skill=sorted(fm['completed'])[0]; probe_rec=fm['completed'][probe_skill]
 probe_model=Model(seed=42,num_fits=1,parallel=False); probe_model.load(str(MODELS/probe_rec['model_file']))
 base=pd.DataFrame({'user_id':['semantics-probe','semantics-probe'],'skill_name':[probe_skill,probe_skill],'correct':[0,1],'order_id':[1,2],'source_row':[-1000001,-1000002]})
 changed=base.copy(); changed.loc[0,'correct']=1
 out0=predict_skill(probe_model,base); out1=predict_skill(probe_model,changed)
 p0=out0.loc[out0.source_row==-1000001,'prediction'].iloc[0]; p1=out1.loc[out1.source_row==-1000001,'prediction'].iloc[0]
 if not math.isclose(float(p0),float(p1),rel_tol=0,abs_tol=1e-12): raise RuntimeError('Current response leaked into its own one-step prediction')
 # Assignment-only verification is safe before the Test marker; no outcomes are read.
 con=duckdb.connect()
 try:
  ap=str(ASSIGNMENTS).replace("'","''")
  count,users,overlap=con.execute(f"SELECT COUNT(*) FILTER(WHERE t.partition='test'),COUNT(DISTINCT t.user_id) FILTER(WHERE t.partition='test'),COUNT(DISTINCT t.user_id) FILTER(WHERE t.partition='test' AND d.partition='development') FROM read_parquet('{ap}') t LEFT JOIN read_parquet('{ap}') d ON t.user_id=d.user_id AND d.partition='development'").fetchone()
 finally: con.close()
 if count!=49522 or users!=49522 or overlap!=0: raise RuntimeError(f'Expected 49,522 unique, disjoint Test assignments; got rows={count}, students={users}, overlap={overlap}')
 runtime['synthetic_predict_before_update_check']='passed: changing response at t left prediction at t unchanged'
 return fm,final,cv,cvres,runtime

def main():
 parser=argparse.ArgumentParser(); parser.add_argument('--preflight-only',action='store_true'); parser.add_argument('--diagnose-skill'); parser.add_argument('--render-report-only',action='store_true'); parser.add_argument('--verify-output-only',action='store_true'); args=parser.parse_args()
 if args.verify_output_only:
  manifest=json.loads((OUT/'run_manifest.json').read_text(encoding='utf-8')); result=json.loads((OUT/'test.json').read_text(encoding='utf-8'))
  if manifest.get('status')!='complete' or manifest.get('report_status')!='complete': raise RuntimeError('Test run/report is not complete')
  if manifest.get('holdout_test_used_for_fit_or_tuning') is not False: raise RuntimeError('Test used for fitting/tuning')
  outputs=manifest.get('output_files',{}); expected_outputs={'test.json','results_vi.md'}|{f'predictions/{_slug(s)}.parquet' for s in manifest['completed_skills']}
  if set(outputs)!=expected_outputs or len(manifest['completed_skills'])!=711: raise RuntimeError('Output inventory mismatch')
  for rel,digest in outputs.items():
   if sha(OUT/rel)!=digest: raise RuntimeError(f'Output hash mismatch: {rel}')
  for skill,rec in manifest['completed_skills'].items():
   if outputs.get(f"predictions/{_slug(skill)}.parquet")!=rec['prediction_sha256']: raise RuntimeError(f'Shard manifest identity mismatch: {skill}')
  fm=json.loads((RUN/'run_manifest.json').read_text(encoding='utf-8')); cv=json.loads(CV_MANIFEST.read_text(encoding='utf-8-sig'))
  if sha(CV_MANIFEST)!=manifest['identity']['cv_manifest_sha256'] or cv.get('status')!='complete': raise RuntimeError('CV identity/status mismatch')
  model_files=0
  for skill,rec in fm['completed'].items():
   if sha(MODELS/rec['model_file'])!=rec['model_sha256']: raise RuntimeError(f'Model file hash mismatch: {skill}')
   model_files+=1
  integ=result['integrity']; overall=result['overall']
  if model_files!=720 or integ['rows']!=5218345 or integ['unique_source_rows']!=5218345 or integ['test_students_with_interactions']!=49522 or integ['unseen_rows_with_prediction']!=0 or integ['invalid_fitted_predictions']!=0 or integ['invalid_binary_values']!=0: raise RuntimeError('Final integrity summary mismatch')
  if overall['scored_rows']+overall['unseen_rows']!=5218345 or result['total_test_exercises']!=711: raise RuntimeError('Coverage or exercise total mismatch')
  print(json.dumps({'verification':'passed','verified_model_hashes':model_files,'verified_output_hashes':len(outputs),'prediction_shards':len(manifest['completed_skills']),'rows':integ['rows'],'unique_source_rows':integ['unique_source_rows'],'students':integ['test_students_with_interactions'],'unseen_rows':overall['unseen_rows'],'invalid_predictions':integ['invalid_fitted_predictions'],'train_test_overlap':integ['train_test_assignment_overlap'],'report_sha256':outputs['results_vi.md']},indent=2)); return
 if args.render_report_only:
  report_data=json.loads((OUT/'test.json').read_text(encoding='utf-8'))
  write_report(report_data,OUT/'results_vi.md')
  saved=json.loads((OUT/'run_manifest.json').read_text(encoding='utf-8'))
  saved.setdefault('output_files',{})['results_vi.md']=sha(OUT/'results_vi.md')
  saved['report_status']='complete'
  atomic(OUT/'run_manifest.json',saved)
  print(json.dumps({'report':'written','path':str(OUT/'results_vi.md'),'sha256':saved['output_files']['results_vi.md']},indent=2)); return
 start=time.perf_counter(); fm,final,cv,cvres,runtime=preflight()
 if args.preflight_only:
  print(json.dumps({'preflight':'passed','verified_models':len(fm['completed']),'runtime':runtime},indent=2)); return
 if args.diagnose_skill:
  skill=args.diagnose_skill; con,skills=prepare_test_stage(OUT)
  try:
   data=con.execute('SELECT *,exercise AS skill_name FROM test_stage WHERE exercise=? ORDER BY user_id,order_id',[skill]).df()
   if skill not in fm['completed']: raise RuntimeError(f'Unseen exercise {skill}')
   rec=fm['completed'][skill]; model=Model(seed=42,num_fits=1,parallel=False); model.load(str(MODELS/rec['model_file']))
   pred=predict_skill(model,data)
   bad=pred[~np.isfinite(pd.to_numeric(pred.prediction,errors='coerce'))]
   joined=data.merge(pred,on='source_row',validate='one_to_one')
   bad_rows=joined[joined.source_row.isin(bad.source_row)]
   pv=pd.to_numeric(pred.prediction,errors='coerce'); outside=pred[(pv<0)|(pv>1)]
   details={'exercise':skill,'rows':len(data),'prediction_rows':len(pred),'non_finite_predictions':len(bad),'nan_count':int(pv.isna().sum()),'below_zero':int((pv<0).sum()),'above_one':int((pv>1).sum()),'minimum':float(pv.min()),'maximum':float(pv.max()),'out_of_range_rows':outside.head(30).to_dict(orient='records'),'bad_prediction_rows':bad_rows.head(30).to_dict(orient='records'),'coefficients':{k:np.asarray(v).tolist() for k,v in model.coef_[skill].items()},'fit_record':{'em_iterations':rec['em_iterations'],'stopped_by_tol':rec['stopped_by_tol'],'hit_maxiter':rec['hit_maxiter'],'training_log_likelihood':rec['final_training_log_likelihood']}}
   print(json.dumps(details,indent=2,allow_nan=True,default=str))
  finally: con.close()
  return
 OUT.mkdir(parents=True,exist_ok=True); (OUT/'predictions').mkdir(exist_ok=True); (OUT/'scratch').mkdir(exist_ok=True)
 identity={**EXPECTED,'final_manifest_sha256':sha(RUN/'run_manifest.json'),'final_json_sha256':sha(RUN/'final.json'),'cv_manifest_sha256':sha(CV_MANIFEST),'cv_results_sha256':sha(CV_RESULTS),'configuration':fm['identity']['configuration']}
 if (OUT/'holdout_started.marker').exists():
  manifest=json.loads((OUT/'run_manifest.json').read_text(encoding='utf-8'))
  if manifest.get('status')!='running' or manifest.get('identity')!=identity: raise RuntimeError('Existing Test checkpoint identity/status mismatch')
  for skill,rec in manifest.get('completed_skills',{}).items():
   shard=OUT/'predictions'/f'{_slug(skill)}.parquet'
   if not shard.is_file() or sha(shard)!=rec['prediction_sha256']: raise RuntimeError(f'Existing prediction checkpoint failed hash: {skill}')
  manifest['attempts']=manifest.get('attempts',[])+[{'resumed_utc':datetime.now(timezone.utc).isoformat(),'note':'Resumed same holdout evaluation from hash-verified exercise checkpoints; frozen models/protocol unchanged.'}]
 else:
  (OUT/'holdout_started.marker').write_text(datetime.now(timezone.utc).isoformat()+'\n',encoding='utf-8')
  manifest={'status':'running','started_utc':datetime.now(timezone.utc).isoformat(),'scope':'holdout Test only','holdout_test_used_for_fit_or_tuning':False,'identity':identity,'runtime':runtime,'protocol':{'partition':'test','expected_students':49522,'ordering':['user_id','exercise','time_done','source_row'],'prediction':'pyBKT sequential one-step-ahead; each outcome updates only subsequent state','ece_bins':15,'accuracy_threshold':0.5,'unseen_policy':'null prediction; excluded from fitted BKT metric denominators','probability_roundoff':'clip only representational violations within 1e-12; larger violations abort'},'verified_model_count':720,'completed_skills':{},'probability_roundoff_corrections':0,'max_probability_roundoff_adjustment':0.0,'peak_rss_bytes_start':peak_rss(),'attempts':[]}
 atomic(OUT/'run_manifest.json',manifest)
 store,skills=prepare_test_stage(OUT)
 try:
  model_skills=set(fm['completed']); total=sum(int(r['rows']) for r in manifest['completed_skills'].values())
  if not skills: raise RuntimeError('No holdout exercises found')
  manifest['test_exercises']=len(skills); atomic(OUT/'run_manifest.json',manifest)
  for i,skill in enumerate(skills,1):
   if skill in manifest['completed_skills']:
    if i%25==0 or i==len(skills): print(f'Test resume {i}/{len(skills)} exercises; verified checkpoint reused',flush=True)
    continue
   data=store.execute('SELECT *,exercise AS skill_name FROM test_stage WHERE exercise=? ORDER BY user_id,order_id',[skill]).df()
   if data.empty: raise RuntimeError(f'Empty Test exercise query: {skill}')
   if set(data['exercise'])!={skill} or data['source_row'].duplicated().any(): raise RuntimeError(f'Exercise/row identity issue: {skill}')
   if not data['correct'].isin([0,1]).all() or not data['suggested'].isin([0,1]).all(): raise RuntimeError(f'Non-binary labels: {skill}')
   # Guard chronology and strict within-user history boundary.
   if data.duplicated(['user_id','order_id']).any(): raise RuntimeError(f'Tied/duplicate order_id within user for {skill}')
   if not data.groupby('user_id',sort=False)['order_id'].apply(lambda x:x.is_monotonic_increasing).all(): raise RuntimeError(f'Non-chronological input: {skill}')
   support=int(fm['completed'][skill]['development_students']) if skill in model_skills else 0
   if support:
    rec=fm['completed'][skill]; model=Model(seed=42,num_fits=1,parallel=False); model.load(str(MODELS/rec['model_file']))
    if skill not in model.coef_: raise RuntimeError(f'Loaded model skill mismatch: {skill}')
    pred=predict_skill(model,data)
    if len(pred)!=len(data) or pred['source_row'].duplicated().any() or set(pred.source_row)!=set(data.source_row): raise RuntimeError(f'Prediction alignment failure: {skill}')
    raw_p=pd.to_numeric(pred['prediction'],errors='coerce').to_numpy(dtype=np.float64)
    if not np.isfinite(raw_p).all(): raise FloatingPointError(f'Non-finite fitted predictions: {skill}')
    if (raw_p < -1e-12).any() or (raw_p > 1+1e-12).any(): raise FloatingPointError(f'Prediction outside [0,1] beyond roundoff tolerance: {skill}')
    roundoff_count=int(((raw_p<0)|(raw_p>1)).sum())
    roundoff_adjustment=float(np.max(np.maximum(-raw_p,raw_p-1).clip(min=0))) if roundoff_count else 0.0
    pred['prediction']=np.clip(raw_p,0.0,1.0)
    merged=data.merge(pred,on='source_row',how='left',validate='one_to_one',sort=False)
    if merged.prediction.isna().any() or not np.isfinite(merged.prediction).all() or not merged.prediction.between(0,1).all(): raise FloatingPointError(f'Invalid prediction after roundoff validation: {skill}')
   else:
    roundoff_count=0; roundoff_adjustment=0.0
    merged=data.copy(); merged['prediction']=np.nan
   out=merged.loc[:,['source_row','user_id','exercise','order_id','correct','suggested','prediction']]
   dest=OUT/'predictions'/f'{_slug(skill)}.parquet'; _write_shard(out,dest,support)
   manifest['completed_skills'][skill]={'rows':len(out),'support_students':support,'model_sha256':fm['completed'][skill]['model_sha256'] if support else None,'prediction_sha256':sha(dest),'scored_rows':len(out) if support else 0,'unseen_rows':0 if support else len(out),'probability_roundoff_corrections':roundoff_count,'max_probability_roundoff_adjustment':roundoff_adjustment}
   manifest['probability_roundoff_corrections']=sum(int(r.get('probability_roundoff_corrections',0)) for r in manifest['completed_skills'].values())
   manifest['max_probability_roundoff_adjustment']=max([float(r.get('max_probability_roundoff_adjustment',0)) for r in manifest['completed_skills'].values()] or [0.0])
   total+=len(out); atomic(OUT/'run_manifest.json',manifest)
   if i%25==0 or i==len(skills): print(f'Test progress {i}/{len(skills)} exercises; {total:,} rows; RSS {peak_rss()/1024**3:.2f} GiB',flush=True)
 finally: store.close()
 # Evaluate saved prediction shards, then add exact prevalence and denominators.
 metrics=score_prediction_shards(OUT/'predictions/*.parquet')
 con=duckdb.connect()
 try:
  pat=str(OUT/'predictions/*.parquet').replace("'","''"); con.execute(f"CREATE VIEW p AS SELECT * FROM read_parquet('{pat}')")
  def prevalence(where):
   return con.execute(f"SELECT COUNT(*),COUNT(*) FILTER(WHERE train_skill_students>0),COUNT(*) FILTER(WHERE train_skill_students=0),SUM(correct),SUM(correct) FILTER(WHERE train_skill_students>0),SUM(correct) FILTER(WHERE train_skill_students=0),COUNT(*) FILTER(WHERE suggested=1),COUNT(*) FILTER(WHERE suggested=0) FROM p WHERE {where}").fetchone()
  for label,where in [('overall','TRUE'),('suggested','suggested=1'),('non_suggested','suggested=0')]:
   n,sc,un,ys,ysc,yun,_,_=prevalence(where); block=metrics['overall'] if label=='overall' else metrics['suggested'][label]
   block['class_counts']={'correct_1_all_rows':int(ys or 0),'correct_0_all_rows':int(n-(ys or 0)),'correct_1_scored_rows':int(ysc or 0),'correct_0_scored_rows':int(sc-(ysc or 0)),'correct_1_unseen_rows':int(yun or 0),'correct_0_unseen_rows':int(un-(yun or 0))}
   block['class_prevalence_all_rows']=float(ys/n) if n else None
   block['class_prevalence_scored_rows']=float(ysc/sc) if sc else None
   block['metric_denominators']={'auc_roc_observations':int(sc) if block['metrics']['auc'] is not None else None,'auc_positive_negative_pairs':int((ysc or 0)*(sc-(ysc or 0))) if block['metrics']['auc'] is not None else None,'log_loss':int(sc),'brier':int(sc),'ece':int(sc),'accuracy':int(sc)}
   block['excluded_unseen_rows']=int(un)
  integrity=con.execute("SELECT COUNT(*),COUNT(DISTINCT source_row),COUNT(DISTINCT user_id),COUNT(*) FILTER(WHERE prediction IS NOT NULL AND train_skill_students=0),COUNT(*) FILTER(WHERE train_skill_students>0 AND (prediction IS NULL OR NOT isfinite(prediction) OR prediction<0 OR prediction>1)),COUNT(DISTINCT user_id) FILTER(WHERE train_skill_students>0 AND prediction IS NOT NULL),COUNT(*) FILTER(WHERE correct NOT IN (0,1) OR suggested NOT IN (0,1)) FROM p").fetchone()
 finally: con.close()
 if integrity[0]!=integrity[1] or integrity[2]!=49522 or integrity[3] or integrity[4] or integrity[6]: raise RuntimeError(f'Final integrity check failed: {integrity}')
 if integrity[0]!=sum(x['rows'] for x in manifest['completed_skills'].values()): raise RuntimeError('Output interaction count mismatch')
 metrics['integrity']={'rows':integrity[0],'unique_source_rows':integrity[1],'test_students_with_interactions':integrity[2],'unseen_rows_with_prediction':integrity[3],'invalid_fitted_predictions':integrity[4],'invalid_binary_values':integrity[6],'row_alignment':'one output row per canonical source_row','student_partition':'all rows joined only to partition=test','train_test_assignment_overlap':0,'prediction_semantics':'pyBKT sequential one-step-ahead: response at t excluded from prediction at t and updates state only for subsequent interaction'}
 metrics['trained_exercises']=sum(1 for x in manifest['completed_skills'].values() if x['support_students']>0)
 metrics['unseen_exercise_names']=[s for s in skills if s not in model_skills]
 metrics['total_test_exercises']=len(skills); metrics['prediction_coverage']=metrics['overall']['coverage']
 metrics['total_test_interactions']=int(integrity[0]); metrics['test_students']=int(integrity[2])
 metrics['holdout_test_used_for_fit_or_tuning']=False
 metrics['development_cv_aggregate']=cvres['aggregate']
 metrics['timing_wall_seconds']=(datetime.now(timezone.utc)-datetime.fromisoformat(manifest['started_utc'])).total_seconds(); metrics['resumed_attempt_active_wall_seconds']=time.perf_counter()-start; metrics['peak_rss_bytes']=peak_rss()
 metrics['warnings']={'final_models_hit_maxiter':int(final['totals']['hit_maxiter']),'retained_by_frozen_decision':True}
 metrics['probability_roundoff_corrections']={'rows':sum(int(r.get('probability_roundoff_corrections',0)) for r in manifest['completed_skills'].values()),'max_adjustment':max([float(r.get('max_probability_roundoff_adjustment',0)) for r in manifest['completed_skills'].values()] or [0.0]),'tolerance':1e-12,'policy':'Only floating-point excursions within 1e-12 were clipped to [0,1]; larger excursions stop the run.'}
 atomic(OUT/'test.json',metrics)
 manifest.update({'status':'complete','completed_utc':datetime.now(timezone.utc).isoformat(),'wall_seconds':metrics['timing_wall_seconds'],'resumed_attempt_active_wall_seconds':metrics['resumed_attempt_active_wall_seconds'],'peak_rss_bytes':metrics['peak_rss_bytes'],'total_test_interactions':int(integrity[0]),'test_students_with_interactions':int(integrity[2]),'unseen_exercises':len(metrics['unseen_exercise_names']),'unseen_rows':metrics['overall']['unseen_rows'],'scored_rows':metrics['overall']['scored_rows'],'output_files':{str(p.relative_to(OUT)):sha(p) for p in [OUT/'test.json']+sorted((OUT/'predictions').glob('*.parquet'))}})
 atomic(OUT/'run_manifest.json',manifest)
 write_report(metrics,OUT/'results_vi.md')
 print(json.dumps({'status':'complete','rows':metrics['total_test_interactions'],'test_students':metrics['test_students'],'overall':metrics['overall'],'suggested':metrics['suggested'],'unseen_exercises':metrics['unseen_exercises'],'wall_seconds':metrics['timing_wall_seconds'],'peak_rss_bytes':metrics['peak_rss_bytes'],'output':str(OUT)},ensure_ascii=False,indent=2),flush=True)

def write_report(m,out):
 def f(v): return 'không xác định' if v is None else f'{v:.6f}'
 overall=m['overall']; den=overall['metric_denominators']; counts=overall['class_counts']
 unseen_names=', '.join(m['unseen_exercise_names']) if m['unseen_exercise_names'] else 'không có'
 lines=['# Đánh giá holdout Test — standard BKT','',f"- Dữ liệu: {m['test_students']:,} sinh viên, {m['total_test_interactions']:,} tương tác; {m['total_test_exercises']} exercise, trong đó {m['trained_exercises']} có model Development. Prediction fitted: {overall['scored_rows']:,}/{overall['total_rows']:,} ({overall['coverage']:.6%}).",f"- Exercise unseen: {len(m['unseen_exercise_names'])} — {unseen_names}; loại {overall['unseen_rows']:,} tương tác khỏi metric BKT, không dùng fallback.",f"- Prevalence correct: {counts['correct_1_all_rows']:,}/{overall['total_rows']:,} = {overall['class_prevalence_all_rows']:.6%} trên toàn Test; {counts['correct_1_scored_rows']:,}/{overall['scored_rows']:,} = {overall['class_prevalence_scored_rows']:.6%} trên phần scored.",'','## Overall metrics','','| Metric | Holdout Test | Development CV mean ± sample SD |','|---|---:|---:|']
 for k,name in [('auc','AUC-ROC'),('log_loss','Log Loss'),('brier','Brier'),('ece','ECE'),('accuracy','Accuracy')]:
  cv=m['development_cv_aggregate'][k]; lines.append(f"| {name} | {f(m['overall']['metrics'][k])} | {cv['mean']:.6f} ± {cv['sd']:.6f} |")
 lines+=['','## Suggested / non-suggested','','| Nhóm | N tổng | N scored | Coverage | Prevalence | AUC | Log Loss | Brier | ECE | Accuracy |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for label,title in [('suggested','Suggested'),('non_suggested','Non-suggested')]:
  b=m['suggested'][label]; lines.append(f"| {title} | {b['total_rows']:,} | {b['scored_rows']:,} | {b['coverage']:.4%} | {b['class_prevalence_all_rows']:.4%} | {f(b['metrics']['auc'])} | {f(b['metrics']['log_loss'])} | {f(b['metrics']['brier'])} | {f(b['metrics']['ece'])} | {f(b['metrics']['accuracy'])} |")
 lines.append(f"- Suggested denominator: N={m['suggested']['suggested']['scored_rows']:,}; AUC positive/negative pairs={m['suggested']['suggested']['metric_denominators']['auc_positive_negative_pairs']:,} ({m['suggested']['suggested']['class_counts']['correct_1_scored_rows']:,} positive, {m['suggested']['suggested']['class_counts']['correct_0_scored_rows']:,} negative).")
 lines.append(f"- Non-suggested denominator: N={m['suggested']['non_suggested']['scored_rows']:,}; AUC positive/negative pairs={m['suggested']['non_suggested']['metric_denominators']['auc_positive_negative_pairs']:,} ({m['suggested']['non_suggested']['class_counts']['correct_1_scored_rows']:,} positive, {m['suggested']['non_suggested']['class_counts']['correct_0_scored_rows']:,} negative).")
 lines.append('- Suggested subgroup rất lệch lớp: chỉ 4 trường hợp incorrect trên 1,069,815 dòng; AUC và ECE cần được diễn giải trong bối cảnh này.')
 lines+=['','## Mẫu số và coverage','',f"- Overall: Log Loss/Brier/ECE/Accuracy mỗi metric dùng N={den['log_loss']:,}; AUC dùng N={den['auc_roc_observations']:,}, gồm {counts['correct_1_scored_rows']:,} dương và {counts['correct_0_scored_rows']:,} âm ({den['auc_positive_negative_pairs']:,} cặp dương–âm).",'- Mẫu số chính xác từng subgroup nằm trong `suggested.*.metric_denominators` của `test.json`.','','| Support sinh viên exercise trong Development | Tổng dòng Test | Scored | Coverage |','|---|---:|---:|---:|']
 for band in ('unseen','1-9','10-49','50-99','100-999','>=1000'):
  b=m['rarity'][band]; lines.append(f"| {band} | {b['total_rows']:,} | {b['scored_rows']:,} | {f(b['coverage'] or 0)} |")
 lines+=['',f"- Wall time end-to-end thực tế: {m['timing_wall_seconds']/3600:.2f} giờ; attempt resumed chạy {m['resumed_attempt_active_wall_seconds']/3600:.2f} giờ; peak RSS {m['peak_rss_bytes']/1024**3:.2f} GiB.",f"- Giữ nguyên 720 model; {m['warnings']['final_models_hit_maxiter']} model đạt maxiter=100 theo quyết định đã đóng băng.",f"- Sai số số học ở biên: {m['probability_roundoff_corrections']['rows']} prediction được kẹp trong [0,1]; chỉnh tối đa {m['probability_roundoff_corrections']['max_adjustment']:.3g} (ngưỡng 1e-12); vi phạm lớn hơn sẽ làm run dừng.",'- ECE dùng 15 bin độ rộng bằng nhau; Accuracy dùng threshold 0.5. Suggested chỉ dùng phân tầng đánh giá, không phải predictor.','- Test chỉ dùng cho đánh giá cuối, không fit/tune. Chênh lệch với CV mô tả holdout performance và không dùng để chỉnh baseline.','']
 out.write_text('\n'.join(lines),encoding='utf-8')

if __name__=='__main__': main()
