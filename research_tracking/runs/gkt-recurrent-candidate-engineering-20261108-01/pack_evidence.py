"""Đóng engineering bundle sau independent review; không rerun tests/model."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT=Path.cwd().resolve()
assert Path(sys.prefix).resolve()==ROOT/'.venv'
PREP=ROOT/'artifacts/akt/local-tests/parallel-gkt-recurrent-20261108-preparation'
RUN='gkt-recurrent-candidate-engineering-20261108-01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
report=ROOT/'research_tracking/reports/gkt_recurrent_candidate_readiness_20261108.md'
review=read(PREP/'independent_review.json')
assert review['status']=='PASS_SCOPED_ENGINEERING_CANDIDATE_ONLY'
expected={'src/knowledge_tracing/gkt/recurrent.py':'510195d71c1ddb743f747e78d7d874c04bb809931c5ec24ae6fe907fe53ec072',
          'tests/gkt/test_recurrent.py':'bb173f7dd9b7b8cf14dbe00dd5fc75097dc87c9f5a794d90e29fd670d26afdce'}
assert review['source_sha256']==expected and all(sha(ROOT/name)==h for name,h in expected.items())
pairs=[];summaries=[];all_trial_sources=[]
for trial,expected_count in [('01',86),('02',87),('03',88)]:
    directory=ROOT/f'artifacts/akt/local-tests/parallel-gkt-recurrent-20261108-{trial}'
    run=read(directory/'run.json');assert run['returncode']==0 and run['error'] is None and run['optimizer_steps']==0
    assert run['sources_unchanged'] and run['source_sha256_before']==run['source_sha256_after']
    assert run['counts']=={'tests':expected_count,'failures':0,'errors':0,'skipped':0}
    suites=list(ET.parse(directory/'pytest.xml').getroot().iter('testsuite'))
    assert sum(int(s.attrib.get('tests',0)) for s in suites)==expected_count
    assert all(sum(int(s.attrib.get(key,0)) for s in suites)==0 for key in ('failures','errors','skipped'))
    for row in run['copies']:
        path=directory/row['copy'];assert sha(path)==row['sha256_before_copy']==row['sha256_after_copy']==run['source_sha256_before'][row['source']]
        if trial=='03':assert sha(ROOT/row['source'])==sha(path)
        pairs.append((path,'trial'+trial+'__'+path.name));all_trial_sources.append(ROOT/row['source'])
    assert len(run['copies'])==8
    for name in ('pytest.log','pytest.xml','run.json'):pairs.append((directory/name,'trial'+trial+'__'+name))
    summaries.append({'trial':trial,'passed':expected_count,'failures':0,'errors':0,'skipped':0,
        'controller_elapsed_seconds':run['controller_elapsed_seconds'],'junit_seconds':sum(float(s.attrib.get('time',0)) for s in suites),
        'optimizer_steps':0,'source_sha256':run['source_sha256_before'],'log_sha256':sha(directory/'pytest.log'),'junit_sha256':sha(directory/'pytest.xml')})
budget=read(PREP/'budget.json')
assert budget['optimizer_steps']==0 and len(budget['attempts'])==3
assert abs(sum(row['controller_elapsed_seconds'] for row in summaries)-budget['elapsed_seconds'])<1e-8 and budget['elapsed_seconds']<=120
for name in ('implementation_note.json','budget.json','run_targeted.py','independent_review.json'):
    pairs.append((PREP/name,name))
pairs.extend([(report,'gkt_recurrent_candidate_readiness.md'),(Path(__file__).resolve(),'pack_evidence.py'),
              (ROOT/'src/knowledge_tracing/evidence.py','evidence_helper.py')])
assert len(pairs)==40 and len({name for _,name in pairs})==40
before=[{'source':p.relative_to(ROOT).as_posix(),'copy':alias,'bytes':p.stat().st_size,'sha256_before_copy':sha(p)} for p,alias in pairs]
count=int(os.environ.get('GIT_CONFIG_COUNT','0'))
os.environ[f'GIT_CONFIG_KEY_{count}']='safe.directory';os.environ[f'GIT_CONFIG_VALUE_{count}']=str(ROOT);os.environ['GIT_CONFIG_COUNT']=str(count+1)
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
sources=sorted({p for p,_ in pairs}|set(all_trial_sources))
acceptance={'recipe_id':'gkt_static_recurrent_convention_v1','evidence_role':'engineering_convention_unfitted',
 'final_tests':88,'kernel_cases':43,'new_cases':45,'registered_parameter_paths_nonzero_finite_gradient_tested':26,
 'actual_trials':summaries,'cumulative_controller_seconds':budget['elapsed_seconds'],'cap_seconds':120,
 'optimizer_steps':0,'training_calls':0,'model_test_reruns_during_archive':0,'dataset_GPU_network_install_calls':0,
 'independent_review':'PASS_SCOPED_ENGINEERING_CANDIDATE_ONLY','author_parity':False,'final_S05_adoption':False,
 'trainer_fitted_adapter_graph_fit':False,'primary_external_byte_hash_claimed':False,
 'trial02_difference':'active counteroverflow guard/regression fromstaticselfreview; nofail-beforeinvocation wasrun',
 'trial03_difference':'Dense/default-meta CPU constructor fix fromindependentstaticreview; nofail-beforeinvocation wasrun'}
note='# GKT recurrent engineering candidate — 08/11/2026\n\nFull recurrent network theo recipe convention, chưa final baseline/S05/author parity. Giữ86/87historical và88final PASS, 24trialsource snapshots, 0optimizer. Không trainer/fitted adapter/learnedgraph/data/GPU. Independent review chỉ trong phạm vi engineering. SHA inventories trước/sau copy; không sửa bundle cũ.\n'
with record_evidence_run(ROOT,RUN,metadata={'kind':'GKT_RECURRENT_ENGINEERING_CONVENTION_ONLY','acceptance':acceptance},sources=sources,note=note) as directory:
    for path,alias in pairs:shutil.copyfile(path,directory/alias)
    after=[]
    for row in before:
        copied=sha(directory/row['copy']);assert copied==row['sha256_before_copy']==sha(ROOT/row['source'])
        after.append({**row,'sha256_after_copy':copied,'exact_match':True})
    def write(name,value):(directory/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    write('copy_inventory_before.json',before);write('copy_inventory.json',after);write('frozen_acceptance.json',acceptance)
    names={alias for _,alias in pairs}|{'README.md','execution.log','copy_inventory_before.json','copy_inventory.json','frozen_acceptance.json','git_ignore_check.json','force_add_paths.txt'}
    checks=[];force=[]
    for name in sorted(names|{'manifest.json'}):
        relative=(directory/name).relative_to(ROOT).as_posix()
        checked=subprocess.run(['git','check-ignore','--no-index','--verbose','--',relative],cwd=ROOT,capture_output=True,text=True)
        assert checked.returncode in (0,1)
        checks.append({'path':relative,'ignored':checked.returncode==0,'rule':checked.stdout.strip()})
        if checked.returncode==0:force.append(relative)
    write('git_ignore_check.json',checks);(directory/'force_add_paths.txt').write_text(''.join(n+'\n' for n in force),encoding='utf-8')
verified=verify_evidence_bundle(directory)
assert verified['artifacts']==47 and {p.name for p in directory.iterdir()}==names|{'manifest.json'}
assert all(sha(ROOT/name)==h for name,h in expected.items())
print(json.dumps({**verified,'copy_pairs':40,'manifest_sha256':sha(directory/'manifest.json'),'report_sha256':sha(report),
                  'source_sha256':expected,'force_add_paths':force},ensure_ascii=False))
