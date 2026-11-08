"""Archive accepted native02 + ONE cached analysis, never rerun either phase."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys
ROOT=Path.cwd().resolve();PREP=Path(__file__).resolve().parent
assert Path(sys.prefix).resolve()==ROOT/'.venv'
sys.path.insert(0,str(ROOT))
from src.knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_bytes())
RUN='rq1-history-availability-20261108-02';DEST=ROOT/'research_tracking/runs'/RUN;assert not DEST.exists()
RAW=PREP/'availability-replay-attempt02';ANALYSIS=PREP/'availability-cached-analysis01'
native=read(RAW/'run.json');worker=read(RAW/'worker_run.json');numeric=read(PREP/'availability_analysis_verification02.json')
aplan=read(PREP/'availability_analysis_plan02.json');rawaudit=read(PREP/'availability_raw_verification02.json')
assert native['status']=='ACCEPTED_ONE_NATIVE_HISTORY_AVAILABILITY_REPLAY'
assert native['cumulative_seconds']<=60 and worker['completed_cases']==108 and worker['full_control_phase_passed']
assert rawaudit['full_prefix_arm_P_S_M_R_fulltuple_exact_checks']==54
assert numeric['status']=='PASS_INDEPENDENT_ALL_AVAILABILITY_NUMERIC_CELLS'
assert numeric['summary_rows_verified']==144 and numeric['summary_mean_numeric_checks']==1872
assert native['source_input_before_sha256']==native['source_input_after_sha256']
assert all(sha(ROOT/n)==d for n,d in native['source_input_after_sha256'].items())
assert all(sha(RAW/n)==d for n,d in native['outputs_sha256'].items())
assert all(sha(ROOT/n)==d for n,d in aplan['inputs_sha256'].items())
assert all(sha(ANALYSIS/n)==d for n,d in numeric['output_sha256'].items())
report=ROOT/'research_tracking/reports/rq1_history_availability_replay_20261108.md'
assert sha(report)=='b8adc20fd57db76b443ba60956d662081f28e86c5bebc3b80809706cf59cb28d'
mapping={}
def add(path,name):
 assert path.is_file() and not path.is_symlink() and name not in mapping
 mapping[name]=path
for path in sorted(RAW.rglob('*')):
 if path.is_file():add(path,'native__'+path.relative_to(RAW).as_posix().replace('/','__'))
for name in ('history_availability_worker02.py','run_history_availability02.py','history_availability_plan02.json',
 'history_availability_budget02.json','history_availability_preparation02.json','history_availability_proposed_cli02.json',
 'RQ1_CONTROLLED_HISTORY_REPLAY_DESIGN.md'):
 add(PREP/name,'source__'+name)
for name,alias in [('AVAILABILITY_CACHED_ANALYSIS_PLAN.md','analysis__recipe.md'),
 ('availability_analysis_plan02.json','analysis__plan.json'),('analyze_history_availability02.py','analysis__analyzer.py'),
 ('availability_analysis_root_dispatch01.json','analysis__root_tool_capture.json'),
 ('availability_raw_verification02.json','verification__raw.json'),('verify_availability_raw02.py','verification__raw_source.py'),
 ('availability_analysis_verification02.json','verification__numeric.json'),('verify_availability_analysis02.py','verification__numeric_source.py'),
 ('pack_availability_accepted02.py','pack_availability_accepted02.py')]:add(PREP/name,alias)
for name in ('summary.json','unique_pairs.json','nominal_aliases.json'):add(ANALYSIS/name,'analysis__'+name)
add(report,'report__rq1_history_availability_replay_20261108.md')
for run,alias in [('rq1-history-availability-20261108-01','prior_failure_manifest.json'),
 ('windows-owned-worker-engineering-20261108-01','helper_manifest.json'),
 ('rq1-fixed-edge-set-contrast-20261108-01','fixed_stream_manifest.json')]:
 add(ROOT/'research_tracking/runs'/run/'manifest.json',alias)
add(ROOT/'research_tracking/reports/windows_owned_worker_readiness_20261108.md','helper_readiness.md')
add(ROOT/'artifacts/akt/local-tests/windows-owned-launcher-20261108-01/trial01/run.json','helper_trial01.json')
add(ROOT/'scripts/research/windows_owned_worker.py','source__windows_owned_worker.py')
add(ROOT/'src/knowledge_tracing/evidence.py','evidence_helper.py')
before={n:{'source':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for n,p in mapping.items()}
sources=set(mapping.values())|{ROOT/n for n in native['source_input_after_sha256']}|{ROOT/n for n in aplan['inputs_sha256']}
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
note='''# Native whole-policy available-history replay — accepted revision02

Native02 ACCEPTED108arms/54full-prefix exactP/S28/M/R/fulltuple controls FIRST,
then54truncatedarms.27cachedtargets,54unique target-windowpairs;81nominalaliases
notnewN. Samecachedqueries/y/time; no newworld/teacher/RNGdraw/NNoptimizer.
Native modelSTATEupdates4140 are actualmodelcalls, not a cached-onlyphase.
WholepolicyINCLUDINGcontrollerbookkeeping, notKT-only/practicecausalbenefit.

Prior3.504370999943088s retained; nativeouter2.5932703018188477s,
cumulative6.097641301761936/60. Source/25pins/callledgers immutable. Ownedhelper
actualworker inexactJob beforeGO;cleanupaccepted/Job0/handlesclosed.
OldFAILED01/probeUNKNOWN archive untouched, prior_failure_manifest isreference,
notrelabeledPASS. Newacceptedrun doesnotrecover originalclosedlooprunner.

ONEstdlibcachedanalysis,rootobserved747ms/toolwall.5720696s<=10. Capturefile
analysis__root_tool_capture.json is TOOL_CAPTURE_NOT_RAW_STDOUT_BYTES; no fake
analysisstdout/stderrfile. Source/recipe freeze precededeffectestimates.
ALL144contexts/H/nominal summaries,54unique pairs and81aliases retained.
Independentnumeric702pair/1872mean/576countchecksPASS; readonly statehash equality
wasasserted inexecutedsource, no independent dualhiddenstate dumps exist.

NonmonotonicLL, contraryprofiles andboth-arm previewchanges preserved. NoCI/p,
calibrator/abilityclaim/edgequality/learningbenefit/RQcompletion;newN0.
raw native__* exactbytes; source__* exactexecuted/preparedsnapshots. Original
path/identity metadata unchanged; copy_inventory maps original→flatmember.
Canonical ../../reports/rq1_history_availability_replay_20261108.md.
No model/replay/analyzer rerun duringarchive, no oldbundle/index/state/Git edits.
'''
with record_evidence_run(ROOT,RUN,metadata={'kind':'CONTROLLED_NATIVE_WHOLE_POLICY_HISTORY_AVAILABILITY_AND_CACHED_ANALYSIS',
 'native_status':native['status'],'cached_analysis_status':'CACHED_CONTROLLED_ALGORITHMIC_AVAILABLE_HISTORY_CONTRAST',
 'native_endpoint_arms':108,'full_prefix_controls_exact':54,'unique_cached_targets':27,'unique_target_window_pairs':54,
 'nominal_pairs_with_aliases':81,'summary_rows':144,'whole_policy_including_controller_bookkeeping':True,
 'native_model_state_updates':4140,'teacher_world_rng_draw_nn_optimizer_calls':0,'new_independent_N':0,
 'native_prior_charged_seconds':native['prior_charged_seconds'],'native_revision_seconds':native['revision_elapsed_seconds'],
 'native_cumulative_seconds':native['cumulative_seconds'],'native_cap_seconds':60,'owned_cleanup_accepted':True,
 'cached_analysis_cap_seconds':10,'cached_capture_is_not_raw_stdout':True,'statistical_inference':False,
 'learning_outcome_or_instructional_causal_benefit':False},sources=sorted(sources),note=note) as out:
 for n,path in mapping.items():
  with (out/n).open('xb') as f:f.write(path.read_bytes())
  assert sha(out/n)==before[n]['sha256']
 after={n:sha(p) for n,p in mapping.items()}
 assert all(after[n]==v['sha256'] for n,v in before.items())
 (out/'copy_inventory.json').write_text(json.dumps({'source_inventory_before':before,'source_sha256_after':after,
  'copied_output_sha256':{n:sha(out/n) for n in mapping},'exact_copy_identity':True,'source_prepost_identity':True,
  'analysis_capture_kind':'ROOT_TOOL_CAPTURE_NOT_RAW_STDOUT_BYTES','prior_failure_not_overwritten':True},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 extras=['README.md','execution.log','copy_inventory.json','check_ignore.json','stage-paths.txt','files-to-force-add.txt','manifest.json']
 paths=sorted(f'research_tracking/runs/{RUN}/{n}' for n in [*mapping,*extras])
 assert all(not any(c in n for c in '\t\r\n') for n in paths)
 check=subprocess.run(['git','check-ignore','--',*paths],cwd=ROOT,text=True,capture_output=True)
 assert check.returncode in (0,1),(check.returncode,check.stderr)
 ignored=check.stdout.splitlines();assert set(ignored)<=set(paths)
 (out/'check_ignore.json').write_text(json.dumps({'argv':['git','check-ignore','--',*paths],
  'returncode':check.returncode,'ignored_paths':ignored,'stdout':check.stdout,'stderr':check.stderr},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (out/'stage-paths.txt').write_text(''.join(n+'\n' for n in paths),encoding='utf-8')
 (out/'files-to-force-add.txt').write_text(''.join(n+'\n' for n in ignored),encoding='utf-8')
verified=verify_evidence_bundle(DEST);manifest=read(DEST/'manifest.json')
assert set(p.name for p in DEST.iterdir())==set(manifest['outputs_sha256'])|{'manifest.json'}
assert all(sha(ROOT/n)==d for n,d in manifest['sources_sha256'].items())
assert all((report.parent/link).resolve().is_file() for link in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')))
whitespace={}
for n in manifest['outputs_sha256']:
 bad=[i for i,line in enumerate((DEST/n).read_text(encoding='utf-8').splitlines(),1) if line.endswith((' ','\t'))]
 if bad:whitespace[n]=bad
result={**verified,'manifest_sha256':sha(DEST/'manifest.json'),'copies':len(mapping),'source_bindings':len(manifest['sources_sha256']),
 'copy_source_prepost_sha_exact':True,'all_public_report_links_exist':True,'report_sha256':sha(report),
 'ignored_paths':ignored,'raw_whitespace_paths_lines':whitespace,'bundle_bytes':sum(p.stat().st_size for p in DEST.iterdir()),
 'native_or_cached_analyzer_rerun_during_archive':False}
with (PREP/'availability_accepted02_closure_verification.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
