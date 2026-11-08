"""Close readout counterexample, no analyzer/teacher/model rerun or history edits."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys
ROOT=Path.cwd().resolve();assert Path(sys.prefix).resolve()==ROOT/'.venv'
sys.path.insert(0,str(ROOT))
from src.knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
PREP=Path(__file__).resolve().parent;RUN='rq2-retention-readout-separation-20261108-01'
DEST=ROOT/'research_tracking/runs'/RUN;assert not DEST.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
receipt=read(PREP/'run.json');plan=read(PREP/'plan.json');values=read(PREP/'analysis01/readouts.json')
assert receipt['status']=='COMPLETED_FIXED_STATE_ARITHMETIC' and receipt['returncode']==0
assert receipt['controller_seconds']<=10 and receipt['environment_model_teacher_trajectory_calls']==0
assert receipt['source_before']==receipt['source_after'] and values['soft_gain_order_reversal']
assert all(sha(ROOT/path)==digest for path,digest in receipt['source_after'].items())
assert all(sha(PREP/path)==digest for path,digest in receipt['outputs_sha256'].items())
assert values['orderings']['T']['native_hard_mastery_count']=='tie_within_1e-12'
assert values['orderings']['D14']['native_hard_mastery_count']=='A>B'
mapping={}
def add(path,name):
 assert path.is_file() and not path.is_symlink() and name not in mapping
 mapping[name]=path
for name in ('analyze_readouts.py','plan.json','run.json','stdout.log','stderr.log','source_metric_locations.json','pack_evidence.py'):
 add(PREP/name,name)
for name in ('readouts.json','source_excerpts.json'):add(PREP/'analysis01'/name,name)
add(ROOT/plan['legacy_retention'],'legacy_C08_retention.json')
report=ROOT/'research_tracking/reports/rq2_retention_metric_separation_20261108.md'
add(report,'report__rq2_retention_metric_separation_20261108.md')
add(ROOT/'src/knowledge_tracing/evidence.py','dependency__evidence.py')
before={name:{'source':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size}
        for name,path in mapping.items()}
sources=set(mapping.values())|{ROOT/plan['notebook']}
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
note='''# Retention readout separation — source-level RQ2 diagnostic, 08/11/2026

ONE predeclared constructed state fixture, stdlib arithmetic0.1298041s<=10,
no teacher/environment/model/trajectory/RNG/search, no empirical learner N.
Shared28base=(850,1200,26x1000); A gains(0,250,zeros),B(450,0,zeros).
Alltheta<=1600 is a domain bound, not reachablepersona/policy/trajectory proof.

Netmean theta retention still exp(-.84)xfinal, C08unchanged. Native SOFTgain
B>A atT, A>B at14d; HARDcount ties1/28 thenA1/28>B0: notstrict hardreversal.
Readout counterexample doesnot prove retentionbenefit/edgeeffect/independence.
This is native true-state soft/hard readout, not modelmastery/calibrated P(K).

readouts.json allraw states/values+negativecontrols; source_excerpts.json and
source_metric_locations.json preserve exact AST snippets/pins, no nativeexec.
legacy_C08_retention.json is unchanged historical copy. Originalnotebook only
path/SHA referenced, not copied with unrelated outputs. run.json preserves
original workdir output paths; copy_inventory.json maps to flat bundle names.
stdout/stderr are actual single analyzer subprocess logs. No failedrun invented.
report__ snapshot includes derivation; canonical ../../reports/rq2_retention_metric_separation_20261108.md
Archive uses pre/post exact SHA, no raw normalization or research rerun.
No C08/thesisdraft/history/tracking/state/Git changes; bundle immutable afterclosure.
'''
metadata={'kind':'SOURCE_RETENTION_READOUT_CONSTRUCTED_COUNTEREXAMPLE_NOT_POLICY_EXPERIMENT',
 'rq':['RQ2'],'constructed_states':2,'empirical_learning_effect':False,'statistical_inference':False,
 'native_environment_model_trajectory_calls':0,'parameter_search':False,
 'arithmetic_controller_seconds':receipt['controller_seconds'],'arithmetic_cap_seconds':10,
 'soft_readout_order_reversal':True,'hard_strict_order_reversal':False,
 'legacy_C08_sha256':plan['legacy_retention_sha256'],'notebook_sha256':plan['notebook_sha256']}
with record_evidence_run(ROOT,RUN,metadata=metadata,sources=sorted(sources),note=note) as out:
 for name,path in mapping.items():
  with (out/name).open('xb') as f:f.write(path.read_bytes())
  assert sha(out/name)==before[name]['sha256']
 after={name:sha(path) for name,path in mapping.items()}
 assert all(after[name]==item['sha256'] for name,item in before.items())
 assert sha(ROOT/plan['notebook'])==plan['notebook_sha256']
 inventory={'source_inventory_before':before,'source_sha256_after':after,
  'copied_output_sha256':{name:sha(out/name) for name in mapping},'exact_copy_identity':True,
  'pre_post_source_identity':True,'original_workdir_aliases':{p.relative_to(PREP).as_posix():name for name,p in mapping.items() if p.is_relative_to(PREP)},
  'uncopied_primary_source':{'path':plan['notebook'],'sha256':plan['notebook_sha256'],'reason':'existing source; exact selected AST snippets copied, unrelated notebook outputs omitted'}}
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
verification=verify_evidence_bundle(DEST);manifest=read(DEST/'manifest.json')
assert set(p.name for p in DEST.iterdir())==set(manifest['outputs_sha256'])|{'manifest.json'}
assert all(sha(ROOT/p)==digest for p,digest in manifest['sources_sha256'].items())
assert all((report.parent/target).resolve().is_file() for target in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')))
whitespace={}
for name in manifest['outputs_sha256']:
 lines=(DEST/name).read_text(encoding='utf-8').splitlines()
 bad=[i for i,line in enumerate(lines,1) if line.endswith((' ','\t'))]
 if bad:whitespace[name]=bad
result={**verification,'manifest_sha256':sha(DEST/'manifest.json'),'exact_copies':len(mapping),
 'source_bindings':len(manifest['sources_sha256']),'all_source_copy_prepost_sha_exact':True,
 'C08_original_sha_unchanged':sha(ROOT/plan['legacy_retention'])==plan['legacy_retention_sha256'],
 'report_sha256':sha(report),'all_public_links_exist':True,'ignored_paths':ignored,
 'raw_whitespace_paths_lines':whitespace,'bundle_bytes':sum(p.stat().st_size for p in DEST.iterdir()),
 'native_environment_model_rng_analyzer_rerun_during_closure':False}
with (PREP/'closure_verification.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
