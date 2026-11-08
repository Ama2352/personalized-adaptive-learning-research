"""Archive approved fixed bins; no native or analyzer rerun."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys
ROOT=Path.cwd().resolve();assert Path(sys.prefix).resolve()==ROOT/'.venv'
sys.path.insert(0,str(ROOT))
from src.knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
PREP=Path(__file__).resolve().parent;RUN='rq1-history-edge-contrast-20261108-01'
DEST=ROOT/'research_tracking/runs'/RUN;assert not DEST.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
plan=read(PREP/'history_contrast_plan.json');receipt=read(PREP/'history-contrast-execution01/run.json')
summary=read(PREP/'history-contrast-analysis01/summary.json');BASE=ROOT/plan['bundle']
assert receipt['status']=='PASS_CACHED_HISTORY_ANALYSIS' and receipt['returncode']==0
assert receipt['elapsed_seconds']<=10 and receipt['before_sha256']==receipt['after_sha256']
assert len(receipt['after_sha256'])==14
assert all(sha(ROOT/name)==digest for name,digest in receipt['after_sha256'].items())
assert all(sha(ROOT/name)==item['sha256'] for name,item in receipt['outputs'].items())
assert summary['paired_targets']==1080 and summary['summary_cells']==304
assert len(summary['groups'])==16 and len(summary['weighted_metric_reconstruction_checks'])==96
oldmanifest=read(BASE/'manifest.json')
assert all(sha(BASE/name)==digest for name,digest in oldmanifest['outputs_sha256'].items())
report=ROOT/'research_tracking/reports/rq1_history_stratified_edge_contrast_20261108.md'
assert sha(report)=='fce27768ea3e8290fab619296854b124e9cceb1af2ba5cc7dad9fc6c4330848b'
mapping={}
def add(path,name):
 assert path.is_file() and not path.is_symlink() and name not in mapping
 mapping[name]=path
for original,name in [('analyze_history_contrast.py','analyze_history_contrast.py'),
 ('history_contrast_plan.json','plan.json'),('RQ1_HISTORY_CONTRAST_PLAN.md','design.md'),
 ('pack_history_contrast.py','pack_history_contrast.py')]:add(PREP/original,name)
for name in ('summary.json','event_bins.json'):add(PREP/'history-contrast-analysis01'/name,name)
for name in ('run.json','stdout.log','stderr.log'):add(PREP/'history-contrast-execution01'/name,name)
for name in ('manifest.json','event_flags.json','summary.json','run.json','C13_manifest.json'):
 add(BASE/name,'input__'+name)
for name in ('observed_query_sidecar.jsonl.gz','observed_legacy.jsonl.gz','historical_runner.py'):add(BASE/name,name)
for name in ('21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md','05_EXPERIMENT_MATRIX.md','06_AKT_CGAKT_ARCHITECTURE_PLAN.md'):
 add(ROOT/'docs/thesis_recovery'/name,'source__'+name)
add(report,'report__rq1_history_stratified_edge_contrast_20261108.md')
add(ROOT/'src/knowledge_tracing/evidence.py','source__evidence.py')
before={name:{'source':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size}
 for name,path in mapping.items()}
sources=set(mapping.values())|{ROOT/name for name in plan['inputs_sha256']}
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
note='''# RQ1/RQ2 history stratification — cached descriptive evidence, 08/11/2026

ONE stdlib cached run PASS0.4277682s<=10;0native/model/teacher/RNG/replay,newN0.
All1080fixed query-labelpairs,16contexts,304cells including empty/null.
Hpast=event_id prior policyupdates, bins0/1-10/11-50/>50.
Ownconcept priorcount strictlybeforetarget bins0/1-5/>=6; NOTtrain support,
vocab coverage or all parent information. H exactly confounded with time/order.
Reuse frozenfull-empty LL/Brier/previewflags; no estimator/calibrator/p/CI.
Pooled/profile marginal+joint tables in report; ALLseed/trajectory cells JSON.
Emptycells notzeroeffects; H11-50/C>=6 only3targets/1seedfamily. PG and joint
PYHcounter-signs kept. Preview is NOTserved; no learning/ability/historycausalclaim.

run.json exactcommand,14beforeafterpins/logs. summary.json96weightedmetricchecks
plus exactpartition n/previewcounts. event_bins.json1080target memberships.
input__ files retain immutableoldcontrast contents; originalpath provenance
unchanged, copy_inventory maps flatnames. PriorC13/C14/contrast untouched.
Canonical ../../reports/rq1_history_stratified_edge_contrast_20261108.md.
Controlled available-history replay is a separate design, NOTexecutedhere.
'''
with record_evidence_run(ROOT,RUN,metadata={'kind':'CACHED_DESCRIPTIVE_HISTORY_STRATIFIED_EDGE_SET_CONTRAST',
 'rq':['RQ1','RQ2'],'paired_targets':1080,'contexts':16,'summary_cells':304,
 'weighted_metric_checks':96,'new_independent_N':0,'native_teacher_model_rng_replay_calls':0,
 'arithmetic_elapsed_seconds':receipt['elapsed_seconds'],'arithmetic_cap_seconds':10,
 'statistical_inference':False,'history_intervention':False,'train_support_analysis':False},
 sources=sorted(sources),note=note) as out:
 for name,path in mapping.items():
  with (out/name).open('xb') as f:f.write(path.read_bytes())
  assert sha(out/name)==before[name]['sha256']
 after={name:sha(path) for name,path in mapping.items()}
 assert all(after[name]==item['sha256'] for name,item in before.items())
 (out/'copy_inventory.json').write_text(json.dumps({'source_inventory_before':before,'source_sha256_after':after,
  'copied_output_sha256':{name:sha(out/name) for name in mapping},'exact_copy_identity':True,
  'pre_post_source_identity':True,'prior_full_empty_all29_outputs_unchanged':True},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 extras=['README.md','execution.log','copy_inventory.json','check_ignore.json','stage-paths.txt','files-to-force-add.txt','manifest.json']
 paths=sorted(f'research_tracking/runs/{RUN}/{name}' for name in [*mapping,*extras])
 assert all(not any(c in path for c in '\t\r\n') for path in paths)
 check=subprocess.run(['git','check-ignore','--',*paths],cwd=ROOT,text=True,capture_output=True)
 assert check.returncode in (0,1),(check.returncode,check.stderr)
 ignored=check.stdout.splitlines();assert set(ignored)<=set(paths)
 (out/'check_ignore.json').write_text(json.dumps({'argv':['git','check-ignore','--',*paths],
  'returncode':check.returncode,'ignored_paths':ignored,'stdout':check.stdout,'stderr':check.stderr},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (out/'stage-paths.txt').write_text(''.join(p+'\n' for p in paths),encoding='utf-8')
 (out/'files-to-force-add.txt').write_text(''.join(p+'\n' for p in ignored),encoding='utf-8')
verified=verify_evidence_bundle(DEST);manifest=read(DEST/'manifest.json')
assert set(p.name for p in DEST.iterdir())==set(manifest['outputs_sha256'])|{'manifest.json'}
assert all(sha(ROOT/name)==digest for name,digest in manifest['sources_sha256'].items())
assert all(sha(BASE/name)==digest for name,digest in oldmanifest['outputs_sha256'].items())
assert all((report.parent/target).resolve().is_file() for target in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')))
whitespace={}
for name in manifest['outputs_sha256']:
 if name.endswith('.gz'):continue
 bad=[i for i,line in enumerate((DEST/name).read_text(encoding='utf-8').splitlines(),1) if line.endswith((' ','\t'))]
 if bad:whitespace[name]=bad
result={**verified,'manifest_sha256':sha(DEST/'manifest.json'),'exact_copies':len(mapping),
 'source_bindings':len(manifest['sources_sha256']),'source_copy_prepost_sha_exact':True,
 'prior_full_empty_all29_outputs_unchanged':True,'report_sha256':sha(report),'all_public_links_exist':True,
 'ignored_paths':ignored,'raw_whitespace_paths_lines':whitespace,
 'bundle_bytes':sum(p.stat().st_size for p in DEST.iterdir()),'analyzer_model_replay_during_closure':False}
with (PREP/'history_contrast_closure_verification.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
