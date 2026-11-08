"""Archive approved cached arithmetic only; no model/analyzer rerun."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys
ROOT=Path.cwd().resolve();assert Path(sys.prefix).resolve()==ROOT/'.venv'
sys.path.insert(0,str(ROOT))
from src.knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
PREP=Path(__file__).resolve().parent;RUN='rq1-fixed-edge-set-contrast-20261108-01'
DEST=ROOT/'research_tracking/runs'/RUN;assert not DEST.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
plan=read(PREP/'full_empty_plan.json');receipt=read(PREP/'full-empty-execution01/run.json')
summary=read(PREP/'full-empty-analysis01/summary.json');BASE=ROOT/plan['bundle']
assert receipt['status']=='PASS_CACHED_ANALYSIS' and receipt['returncode']==0
assert receipt['elapsed_seconds']<=10 and receipt['before_sha256']==receipt['after_sha256']
assert all(sha(ROOT/name)==digest for name,digest in receipt['after_sha256'].items())
assert all(sha(ROOT/name)==item['sha256'] for name,item in receipt['outputs'].items())
assert summary['population_keys']==1080 and len(summary['groups'])==16
assert summary['GF_decomposition_eligible'] and len(summary['historical_metric_checks'])==36
c13=read(BASE/'manifest.json');assert all(sha(BASE/name)==digest for name,digest in c13['outputs_sha256'].items())
report=ROOT/'research_tracking/reports/rq1_fixed_edge_set_contrast_20261108.md'
assert sha(report)=='2e8c0b64838edaf81d80a5fc068c0aeedba5690ed941dd34e0e3eb9af7442b65'
mapping={}
def add(path,name):
 assert path.is_file() and not path.is_symlink() and name not in mapping
 mapping[name]=path
for original,name in [('analyze_full_empty_fixed.py','analyze_full_empty_fixed.py'),
 ('full_empty_plan.json','plan.json'),('RQ1_NEXT_CONTRAST_REVIEW.md','source_review.md'),
 ('full_empty_source_excerpts.json','source_excerpts.json'),('pack_full_empty.py','pack_full_empty.py')]:add(PREP/original,name)
for name in ('summary.json','event_flags.json'):add(PREP/'full-empty-analysis01'/name,name)
for name in ('run.json','stdout.log','stderr.log'):add(PREP/'full-empty-execution01'/name,name)
for name in ('observed_legacy.jsonl.gz','observed_query_sidecar.jsonl.gz','control_legacy.jsonl.gz',
 'historical__traces.jsonl.gz','historical__comparisons.json','historical_runner.py','parity.json','observer.py'):
 add(BASE/name,name)
add(BASE/'manifest.json','C13_manifest.json')
add(report,'report__rq1_fixed_edge_set_contrast_20261108.md')
for name in ('diagnostics.py','paper2_reference.py','evidence.py'):add(ROOT/'src/knowledge_tracing'/name,'source__'+name)
before={name:{'source':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size}
 for name,path in mapping.items()}
sources=set(mapping.values())|{ROOT/path for path in plan['inputs_sha256']}
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
note='''# RQ1 fixed-stream edge-set contrast — 08/11/2026

Cached arithmetic only, ONE actual PASS0.6813872s<=10,0model/teacher/RNG/replay.
All1080targets,3reused seed families/3profiles/120steps,16groups,36oldmetricchecks.
Full/empty both enabled Graph-GAM package: estimator edges differ; controller
and environment graphs remain full. Edge-dependent updates/local downstream
states included; not direct-logit-only/individual-edgequality/causal benefit.
NEW963Pchanges/943samepreview distinct from historical full-GF964/944.
Pooled LL/Brier favors full, all3PG trajectories opposite; allgroups retained.
A is deepcopy preview, NOTserved; S uncalibrated, M storedboolean.
GF algebra same1080rows/order-dependent, not mediation or contributionfraction.
new independent N=0; no p/CI/calibrator/thresholdsearch; C13/C14 unchanged.

summary.json retains16groups/all4P-previewcells; event_flags.json1080records.
plan/analyzer before quantities; run.json actual command/log/sourceprepost.
Original receipt source paths retained; copy_inventory maps flat archive names.
Source notebook only exactSHA+selectedcells; historical C13 originals unchanged.
Canonical report ../../reports/rq1_fixed_edge_set_contrast_20261108.md.
This bundle is new descriptive RQ1 evidence, not finalRQcompletion or fittedNN.
'''
with record_evidence_run(ROOT,RUN,metadata={'kind':'CACHED_FIXED_STREAM_CONDITIONAL_ESTIMATOR_EDGE_SET_CONTRAST',
 'rq':['RQ1'],'new_independent_N':0,'models_teacher_rng_replay_calls':0,'paired_targets':1080,
 'groups':16,'historical_metric_checks':36,'statistical_inference':False,
 'arithmetic_elapsed_seconds':receipt['elapsed_seconds'],'arithmetic_cap_seconds':10,
 'candidate':'graph_package','reference':'empty_graph_package','both_package_enabled':True,
 'scientific_scope':'conditional edge-set input including downstream states; not causal teaching benefit'},
 sources=sorted(sources),note=note) as out:
 for name,path in mapping.items():
  with (out/name).open('xb') as f:f.write(path.read_bytes())
  assert sha(out/name)==before[name]['sha256']
 after={name:sha(path) for name,path in mapping.items()}
 assert all(after[name]==item['sha256'] for name,item in before.items())
 inventory={'source_inventory_before':before,'source_sha256_after':after,
  'copied_output_sha256':{name:sha(out/name) for name in mapping},'exact_copy_identity':True,
  'pre_post_source_identity':True,'C13_all40_outputs_sha_unchanged':True,
  'uncopied_notebook':{path:digest for path,digest in plan['inputs_sha256'].items() if path.endswith('.ipynb')}}
 (out/'copy_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
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
assert all(sha(BASE/name)==digest for name,digest in c13['outputs_sha256'].items())
assert all((report.parent/target).resolve().is_file() for target in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')))
whitespace={}
for name in manifest['outputs_sha256']:
 if name.endswith('.gz'):continue
 bad=[i for i,line in enumerate((DEST/name).read_text(encoding='utf-8').splitlines(),1) if line.endswith((' ','\t'))]
 if bad:whitespace[name]=bad
result={**verified,'manifest_sha256':sha(DEST/'manifest.json'),'exact_copies':len(mapping),
 'source_bindings':len(manifest['sources_sha256']),'all_source_copy_prepost_sha_exact':True,
 'C13_all40_output_sha_unchanged':True,'report_sha256':sha(report),'all_public_links_exist':True,
 'ignored_paths':ignored,'raw_whitespace_paths_lines':whitespace,
 'bundle_bytes':sum(p.stat().st_size for p in DEST.iterdir()),'analyzer_model_replay_during_closure':False}
with (PREP/'full_empty_closure_verification.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
