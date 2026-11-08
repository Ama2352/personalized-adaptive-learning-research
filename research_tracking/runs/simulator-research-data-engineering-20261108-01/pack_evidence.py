"""Small immutable data-contract evidence; no test/model/generator execution."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,xml.etree.ElementTree as ET
ROOT=Path.cwd().resolve();assert Path(sys.prefix).resolve()==ROOT/'.venv'
sys.path.insert(0,str(ROOT))
from src.knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
PREP=Path(__file__).resolve().parent;TRIAL=PREP/'trial01'
RUN='simulator-research-data-engineering-20261108-01'
DEST=ROOT/'research_tracking/runs'/RUN;assert not DEST.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
receipt=read(TRIAL/'run.json');assert receipt['status']=='PASS_PURE_SYNTHETIC_RESEARCH_DATA_CONTRACT'
assert receipt['counts']=={'tests':76,'failures':0,'errors':0,'skipped':0}
assert receipt['controller_seconds']<=60 and receipt['source_sha256_before']==receipt['source_sha256_after']
for p,digest in receipt['source_sha256_after'].items():assert sha(ROOT/p)==digest
suite=ET.parse(TRIAL/'pytest.xml').getroot().find('testsuite')
assert tuple(int(suite.attrib[k]) for k in ('tests','failures','errors','skipped'))==(76,0,0,0)
assert len([t for t in suite.findall('testcase') if t.attrib['classname'].endswith('test_simulator_research_data')])==51
mapping={}
def add(p,name):
 assert p.is_file() and not p.is_symlink() and name not in mapping
 assert p.suffix not in ('.pt','.parquet','.zip')
 mapping[name]=p
for relative in receipt['source_sha256_after']:
 add(ROOT/relative,'source__'+relative.replace('/','__'))
for p in sorted(TRIAL.iterdir()):
 if p.is_file():add(p,'trial01__'+p.name)
add(ROOT/'research_tracking/reports/simulator_research_data_contract_20261108.md','report__simulator_research_data_contract_20261108.md')
add(Path(__file__),'pack_evidence.py')
add(ROOT/'src/knowledge_tracing/evidence.py','dependency__evidence.py')
before={name:{'source':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for name,p in mapping.items()}
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
note='''# Research-mode simulator input contract — 08/11/2026

Engineering deliverable trực tiếp cho corpus role-aware, không corpus generated.
Additive exact80/10/10 plan + final metadata, explicit source/policy/clock binding,
28x3reference support, train-only vocabulary và90% refit view với selectionfreeze.
Không sửa oldvalidators/collector/history/native/tracking/state/tasks/Git.

Actual76PASS=51new+25frozen schema cases;0fail/error/skip,controller1.0936313s
trong60s cumulative. Manual synthetic observations only,0environment/generation/
model/optimizer calls. Không fabricate failed trial hoặc rerun để đóng bundle.
Sources8 trước/sau PASS giữ nguyên; copy_inventory.json ghi pre/post exact SHA.
Final events bị reject trước iterate; final IDs/seedmetadata không empirical
independence. Provenance/freeze SHA là caller declaration, không attestation.
Missing reference coverage báo rõ,>=1learner/item không adequate calibration.

Collector research generation/real source policy execution/actual corpus/fit/
calibration/controller vẫn missing, cần nextobjective riêng; không nới fixture2x12.
Metadata plan ceiling10.000 không là scientific corpus default. Không dataset,
Holdout/private/model binaries/pytest temp data hoặc remote/cloud/spend.
Report canonical: ../../reports/simulator_research_data_contract_20261108.md
Bundle bất biến sau closure; source snapshots không entrypoint hiện hành.
'''
metadata={'kind':'RESEARCH_SIMULATOR_INPUT_CONTRACT_ENGINEERING_ONLY','targeted_tests':receipt['counts'],
 'new_contract_tests':51,'frozen_schema_tests':25,'cumulative_test_seconds':receipt['controller_seconds'],
 'test_cap_seconds':60,'research_corpus_generated':False,'model_optimizer_environment_generation_calls':0,
 'declared_provenance_not_execution_attestation':True,'source_before_after_sha_exact':True}
with record_evidence_run(ROOT,RUN,metadata=metadata,sources=sorted(set(mapping.values())),note=note) as bundle:
 for name,p in mapping.items():
  with (bundle/name).open('xb') as f:f.write(p.read_bytes())
  assert sha(bundle/name)==before[name]['sha256']
 after={name:sha(p) for name,p in mapping.items()}
 assert all(after[name]==item['sha256'] for name,item in before.items())
 inventory={'source_inventory_before':before,'source_sha256_after':after,
  'copied_output_sha256':{name:sha(bundle/name) for name in mapping},
  'exact_copy_identity':True,'pre_post_source_identity':True,'sources_before_after_tests':receipt['source_sha256_after'],
  'excluded':'all pytest t/temp folders; no model/checkpoint/Parquet/private/raw-data/remote evidence'}
 (bundle/'copy_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 extras=['README.md','execution.log','copy_inventory.json','stage-paths.txt','files-to-force-add.txt','check_ignore.json','manifest.json']
 paths=sorted(f'research_tracking/runs/{RUN}/{name}' for name in [*mapping,*extras])
 assert not any(any(c in p for c in '\r\n\t') for p in paths)
 ignored=subprocess.run(['git','check-ignore','--',*paths],cwd=ROOT,text=True,capture_output=True)
 assert ignored.returncode in (0,1),(ignored.returncode,ignored.stderr)
 ignored_paths=ignored.stdout.splitlines();assert set(ignored_paths)<=set(paths)
 (bundle/'check_ignore.json').write_text(json.dumps({'argv':['git','check-ignore','--',*paths],
  'returncode':ignored.returncode,'ignored_paths':ignored_paths,'stdout':ignored.stdout,'stderr':ignored.stderr,
  'path_tab_LF_CR_absent':True},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (bundle/'stage-paths.txt').write_text(''.join(p+'\n' for p in paths),encoding='utf-8')
 (bundle/'files-to-force-add.txt').write_text(''.join(p+'\n' for p in ignored_paths),encoding='utf-8')
verification=verify_evidence_bundle(DEST);manifest=read(DEST/'manifest.json')
assert set(p.name for p in DEST.iterdir())==set(manifest['outputs_sha256'])|{'manifest.json'}
assert set((DEST/'stage-paths.txt').read_text().splitlines())==set(p.relative_to(ROOT).as_posix() for p in DEST.iterdir())
assert all(sha(ROOT/p)==digest for p,digest in manifest['sources_sha256'].items())
report=ROOT/'research_tracking/reports/simulator_research_data_contract_20261108.md'
import re
links=re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8'))
assert all((report.parent/link).resolve().is_file() for link in links)
result={**verification,'manifest_sha256':sha(DEST/'manifest.json'),'exact_copy_pairs':len(mapping),
 'source_bindings':len(manifest['sources_sha256']),'report_sha256':sha(report),'all_source_output_sha_verified':True,
 'all_copy_sha_before_after_exact':True,'all_public_report_links_exist':len(links),
 'ignored_paths':ignored_paths,'source_test_frozen':True,'no_rerun_model_or_tests':True}
with (PREP/'closure_verification.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
