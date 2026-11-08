"""Archive same-pilot observability evidence only; không rerun model/RNG/tests."""
from collections import Counter
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT=Path.cwd().resolve();assert Path(sys.prefix).resolve()==ROOT/'.venv'
PREP=Path(__file__).resolve().parent;ATTEMPT=PREP/'attempt01';DATA=ATTEMPT/'replay'
OLD=ROOT/'research_tracking/runs/cpu-rq12-20261107-03'
RUN='rq1-query-observability-reproduction-20261108-01'
REPORT=ROOT/'research_tracking/reports/rq1_query_observability_reproduction_20261108.md'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
old_manifest=read(OLD/'manifest.json');historical_before={name:sha(OLD/name) for name in old_manifest['outputs_sha256']}
assert historical_before==old_manifest['outputs_sha256']
run=read(ATTEMPT/'run.json');parity=read(DATA/'parity.json');analysis=read(ATTEMPT/'sidecar_analysis.json')
assert run['status']=='PASS' and run['controller_elapsed_seconds']<=120 and run['optimizer_steps']==0
assert run['source_unchanged'] and run['source_sha256_before']==run['source_sha256_after']
assert all(sha(PREP/name)==h for name,h in run['source_sha256_before'].items())
assert parity['status']=='PASS_EXACT_LEGACY_PARITY_NEW_OBSERVATIONS_ONLY' and parity['variant_rows']==3240 and parity['logical_event_keys']==1080
assert parity['optimizer_steps']==parity['new_independent_N']==0 and parity['historical_metadata_backfilled'] is False
assert analysis['status']=='PASS_STORED_OBSERVABILITY_ANALYSIS_NO_MODEL_RERUN'
assert all(sha(PREP/name)==h for name,h in analysis['input_sha256_before_after'].items())
assert parity['control']['profile_state_rng_fingerprints']==parity['observed']['profile_state_rng_fingerprints']
assert parity['control']['policy_headers']==parity['observed']['policy_headers']
assert sha(DATA/'historical_runner.py')=='402dca905694d850f126e41f3b5dcc91b327e986ae2cfbb240dda739eed8dd45'
suites=list(ET.parse(ATTEMPT/'pytest.xml').getroot().iter('testsuite'))
assert sum(int(s.attrib.get('tests',0)) for s in suites)==12
assert all(sum(int(s.attrib.get(key,0)) for s in suites)==0 for key in ('failures','errors','skipped'))
flags=list(csv.DictReader((ATTEMPT/'sidecar_event_flags.csv').open(encoding='utf-8',newline='')));assert len(flags)==2160
for summary in analysis['counts']:
    if summary['group'] not in ('pooled','PG','PY','PYH'):continue
    selected=[row for row in flags if row['candidate']==summary['candidate'] and (summary['group']=='pooled' or row['profile']==summary['group'])]
    assert len(selected)==summary['pairs']
    for column,key in [('A_concept_changed','concept_changed'),('A_full_tuple_changed','full_tuple_changed'),('A_question_changed','question_changed'),('A_difficulty_changed','difficulty_changed')]:
        assert sum(int(row[column]) for row in selected)==summary[key]
    assert sum(int(row['P_same']) and int(row['A_full_tuple_changed']) for row in selected)==summary['same_P_full_tuple_changed']
for name in ('control_legacy.jsonl.gz','observed_legacy.jsonl.gz','observed_query_sidecar.jsonl.gz'):
    with gzip.open(DATA/name,'rt',encoding='utf-8') as stream:assert sum(1 for _ in stream)==3240
pairs=[]
for name in ['observer.py','test_observer.py','run_reproduction.py','run_bounded_attempt.py','analyze_sidecar.py','INSPECTION_NOTE.md','inspection_sources.json']:
    pairs.append((PREP/name,name))
for path in sorted(ATTEMPT.glob('source__*')):pairs.append((path,'attempt01__'+path.name))
assert len(list(ATTEMPT.glob('source__*')))==6
for name in ('run.json','pytest.log','pytest.xml','reproduction.log','sidecar_analysis.json','sidecar_event_flags.csv'):
    pairs.append((ATTEMPT/name,'attempt01__'+name))
for name in ('historical_runner.py','control_legacy.jsonl.gz','control_query_sidecar.jsonl.gz','observed_legacy.jsonl.gz','observed_query_sidecar.jsonl.gz','parity.json'):
    pairs.append((DATA/name,name))
for name in ('manifest.json','source_provenance.json','comparisons.json','traces.jsonl.gz'):
    pairs.append((OLD/name,'historical__'+name))
pairs.extend([(REPORT,'rq1_query_observability_reproduction.md'),(Path(__file__).resolve(),'pack_observability.py'),
              (ROOT/'src/knowledge_tracing/evidence.py','evidence_helper.py')])
assert len(pairs)==32 and len({alias for _,alias in pairs})==32
before=[{'source':p.relative_to(ROOT).as_posix(),'copy':alias,'bytes':p.stat().st_size,'sha256_before_copy':sha(p)} for p,alias in pairs]
sources={p for p,_ in pairs}|{OLD/name for name in old_manifest['outputs_sha256']}|{
    ROOT/name for name in parity['source_input_sha256_before_after']}
count=int(os.environ.get('GIT_CONFIG_COUNT','0'));os.environ[f'GIT_CONFIG_KEY_{count}']='safe.directory';os.environ[f'GIT_CONFIG_VALUE_{count}']=str(ROOT);os.environ['GIT_CONFIG_COUNT']=str(count+1)
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
acceptance={'kind':'SAME_PILOT_REPRODUCTION_OBSERVABILITY_NOT_NEW_INDEPENDENT_SAMPLE','spy_tests':12,
 'legacy_rows_per_pass':3240,'comparisons_exact_per_pass':18,'logical_events':1080,'query_preview_tuples':3240,
 'controller_seconds':run['controller_elapsed_seconds'],'reproduction_seconds':parity['elapsed_seconds'],'cap_seconds':120,
 'native_prediction_update_calls_total':6480,'environment_interactions_total':2160,'optimizer_steps':0,'new_independent_N':0,
 'historical_metadata_backfilled':False,'preview_is_served':False,'new_graph_generation':False,
 'analysis_model_rng_calls':0,'archive_model_test_RNG_calls':0,'independent_analysis_review':'parent review before commit; not claimed complete here',
 'counts':[row for row in analysis['counts'] if row['group'] in ('pooled','PG','PY','PYH')]}
note='# RQ1: reproduction cùng pilot, thêm query/item observability — 08/11/2026\n\n12spytests PASS; control/observed exact3.240legacy rows+18comparisons mỗi pass,9state/RNG fingerprints khớp,3.240query/fullpreview captures. 1.080logical keys/cùng3seed families, không newindependentN. Fulltuplediff22=conceptdiff22, additional same-concept itemdiff0; sameP/fulltuplediff2/116. Không backfillhistorical metadata, preview không served, không causal/calibration/RQcompletion. Control querysidecar rỗng là chủ đích; control chỉ giữ legacy projection. SHA/copy/historical8preservation trước-sau; archive không rerun model/tests.\n'
with record_evidence_run(ROOT,RUN,metadata={'kind':'RQ1_FIXED_STREAM_OBSERVABILITY_REPRODUCTION_ONLY','acceptance':acceptance},sources=sorted(sources),note=note) as directory:
    for path,alias in pairs:shutil.copyfile(path,directory/alias)
    after=[]
    for row in before:
        copied=sha(directory/row['copy']);assert copied==row['sha256_before_copy']==sha(ROOT/row['source'])
        after.append({**row,'sha256_after_copy':copied,'exact_match':True})
    historical_after={name:sha(OLD/name) for name in old_manifest['outputs_sha256']};assert historical_before==historical_after
    def write(name,value):(directory/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    write('copy_inventory_before.json',before);write('copy_inventory.json',after);write('frozen_acceptance.json',acceptance)
    write('historical8_preservation.json',{'historical_run':'cpu-rq12-20261107-03','expected_from_manifest':old_manifest['outputs_sha256'],
        'actual_pre_archive':historical_before,'actual_post_copy':historical_after,'all8unchanged':True,
        'model_phase_check':'run_reproduction source-bound assertions checked all8 against historicalmanifest before and after bothpasses; actualPASS. Separate current8maps above are archive-phase measurements.'})
    names={alias for _,alias in pairs}|{'README.md','execution.log','copy_inventory_before.json','copy_inventory.json','frozen_acceptance.json','historical8_preservation.json','git_ignore_check.json','force_add_paths.txt'}
    checks=[];force=[]
    for name in sorted(names|{'manifest.json'}):
        relative=(directory/name).relative_to(ROOT).as_posix();checked=subprocess.run(['git','check-ignore','--no-index','--verbose','--',relative],cwd=ROOT,capture_output=True,text=True)
        assert checked.returncode in (0,1);checks.append({'path':relative,'ignored':checked.returncode==0,'rule':checked.stdout.strip()})
        if checked.returncode==0:force.append(relative)
    write('git_ignore_check.json',checks);(directory/'force_add_paths.txt').write_text(''.join(p+'\n' for p in force),encoding='utf-8')
verified=verify_evidence_bundle(directory);assert verified['artifacts']==40 and {p.name for p in directory.iterdir()}==names|{'manifest.json'}
print(json.dumps({**verified,'copy_pairs':32,'manifest_sha256':sha(directory/'manifest.json'),'report_sha256':sha(REPORT),'force_add_paths':force},ensure_ascii=False))
