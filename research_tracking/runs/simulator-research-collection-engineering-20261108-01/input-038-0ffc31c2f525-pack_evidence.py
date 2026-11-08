"""Immutable collector bundle: mock failure/PASS and native12 separated, no rerun."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys,xml.etree.ElementTree as ET
ROOT=Path.cwd().resolve();assert Path(sys.prefix).resolve()==ROOT/'.venv'
sys.path.insert(0,str(ROOT))
from src.knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
PREP=Path(__file__).resolve().parent;RUN='simulator-research-collection-engineering-20261108-01'
DEST=ROOT/'research_tracking/runs'/RUN;assert not DEST.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
native=read(PREP/'native01/run.json');mock1=read(PREP/'mock01/run.json');mock2=read(PREP/'mock02/run.json')
assert native['status']=='ACCEPTED_NATIVE12_REQUESTED_ROLE_SMOKE_NOT_RESEARCH_READY'
assert native['counts']=={'reservations':12,'native_attempts':12,'native_returns':12}
assert native['controller_seconds']<30 and not native['research_corpus_ready']
assert mock1['counts']=={'tests':43,'failures':1,'errors':0,'skipped':0}
assert mock2['counts']=={'tests':45,'failures':0,'errors':0,'skipped':0}
assert mock2['cumulative_all_attempts_seconds']<=60
assert mock2['source_sha256_before']==mock2['source_sha256_after']
for p,digest in mock2['source_sha256_after'].items():assert sha(ROOT/p)==digest
for attempt,counts in [('mock01',(43,1,0,0)),('mock02',(45,0,0,0))]:
 suite=ET.parse(PREP/attempt/'pytest.xml').getroot().find('testsuite')
 assert tuple(int(suite.attrib[k]) for k in ('tests','failures','errors','skipped'))==counts
assert all(sha(PREP/'native01'/name)==s for name,s in native['outputs_sha256'].items())
assert native['source_before']==native['source_after']==read(PREP/'native01_expected_sources.json')
verification=read(PREP/'native01_readonly_verification.json')
assert verification['status']=='VERIFIED_NATIVE_SMOKE_ARTIFACTS_NO_RERUN'
assert verification['native_run_sha256']==sha(PREP/'native01/run.json')
mapping={};by_sha={};aliases={}
def add(p,preferred=None):
 assert p.is_file() and not p.is_symlink() and p.suffix not in ('.pt','.parquet','.zip')
 assert p.stat().st_size<=2*1024**2
 relative=p.relative_to(ROOT).as_posix();digest=sha(p)
 if relative in aliases:return
 if digest in by_sha:
  name=by_sha[digest]
 else:
  name=preferred or f'input-{len(mapping):03}-{digest[:12]}-{p.name[:60]}'
  assert name not in mapping and not any(c in name for c in '\t\r\n')
  mapping[name]=p;by_sha[digest]=name
 aliases[relative]=name
# Durable report links resolve to these exact native file names.
for p in sorted((PREP/'native01').iterdir()):
 if p.is_file():add(p,'native__'+p.name)
for directory in ('mock01','mock02'):
 for name in ('pytest.log','pytest.xml','run.json'):add(PREP/directory/name,directory+'__'+name)
for relative in sorted(native['source_before']):
 add(ROOT/relative,'source__'+Path(relative).name)
add(ROOT/'tests/shared_kt/test_simulator_research_collection.py','source__test_simulator_research_collection.py')
add(ROOT/'src/knowledge_tracing/evidence.py','dependency__evidence.py')
report=ROOT/'research_tracking/reports/simulator_research_collection_readiness_20261108.md'
add(report,'report__'+report.name)
for p in sorted(PREP.iterdir()):
 if p.is_file():add(p)
for directory in ('mock01','mock02'):
 for p in sorted((PREP/directory).iterdir()):
  if p.is_file():add(p)
source_before={p:{'sha256':sha(ROOT/p),'bytes':(ROOT/p).stat().st_size,'copy':name} for p,name in aliases.items()}
copy_before={name:{'source':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for name,p in mapping.items()}
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
note='''# Research role collector — mock guards + native12 smoke, 08/11/2026

Collector riêng cho requested train/selection/calibration; final events forbidden.
Giữ fixture2x12/source/native/validators cũ. Không NN/optimizer/realdata/remote.
Mock01 actual42PASS/1FAIL do pandas unsigned timestamp wrap; sourcefix upperUTC
bound và mock02 final45PASS. Cumulative5.8013762s<=60; actual environment0 trongmocks.
Native01 do root review/dispatch:12reservations/attempts/returns,1.3233694s<=30,
RSS512MiB/freeRAM1GiB cooperative guards. Train8/selection2/calibration2events;
missing reference items76/82/82, tất cả NOTresearchready;0NN/final calls.
Ledger instrumentation trước original interact, không extra environment/RNG calls.

Raw observables và oracle sidecars táchfile native__<role>.*; sidecar cấm modelinputs.
Native runSHA df02590f5bc1e849694ae83ab699f41de258c0d70be63abfcca0dd268afdb799.
Readonly verifier hash/schema only, không replay. Initial tuple/list equality
failure giữ normalizedreceipt+oldsource, không fake rawstderr/nativefailure.
Preexecution driverpostguard revision giữ riêng; không actualfailure giả.

SHA-identical sourcecopies archive1lần+mọipathaliases trongcopy_inventory.json;
copy/source prepost exact; không pytest t/temp/private/modelbinary/Parquet/ZIP.
Source notebook/CSV chỉ simulator input metadata, không Junyi/rawlearner/Holdout.
Source/hash/provenance consistency không chống source A→B→A đồngthời/callerforgery.
Caps là cooperative không hardkill; actual12records không diversity/calibration/
training-readiness/RQcompletion/CUDA hoặc paid authorization proof.
Canonical report ../../reports/simulator_research_collection_readiness_20261108.md
Bundle immutable sauclosure; không test/model/native rerun khiđónggói.
'''
metadata={'kind':'RESEARCH_ROLE_COLLECTOR_MOCK_AND_NATIVE12_ENGINEERING_NOT_CORPUS_READY',
 'mock01_counts':mock1['counts'],'mock02_counts':mock2['counts'],
 'mock_cumulative_seconds':mock2['cumulative_all_attempts_seconds'],'mock_cap_seconds':60,
 'native_counts':native['counts'],'native_seconds':native['controller_seconds'],'native_cap_seconds':30,
 'native_model_optimizer_final_calls':0,'research_corpus_ready':False,'unique_copies':len(mapping),
 'input_aliases':len(aliases),'native_run_sha256':sha(PREP/'native01/run.json')}
with record_evidence_run(ROOT,RUN,metadata=metadata,sources=sorted(ROOT/p for p in aliases),note=note) as out:
 for name,p in mapping.items():
  with (out/name).open('xb') as f:f.write(p.read_bytes())
  assert sha(out/name)==copy_before[name]['sha256']
 after={p:sha(ROOT/p) for p in aliases}
 assert all(after[p]==item['sha256'] for p,item in source_before.items())
 inventory={'source_inventory_before':source_before,'source_sha256_after':after,
  'copy_pairs_before':copy_before,'copied_output_sha256':{name:sha(out/name) for name in mapping},
  'path_aliases':aliases,'source_prepost_exact':True,'all_copy_pairs_exact':True,
  'deduplication':'same SHA bytes copied once, all original paths retained; no raw content normalization',
  'excluded':'pytest temp dirs, no .pt/Parquet/ZIP/private/raw-learner artifacts'}
 (out/'copy_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 extras=['README.md','execution.log','copy_inventory.json','check_ignore.json','stage-paths.txt','files-to-force-add.txt','manifest.json']
 paths=sorted(f'research_tracking/runs/{RUN}/{name}' for name in [*mapping,*extras])
 checked=subprocess.run(['git','check-ignore','--',*paths],cwd=ROOT,text=True,capture_output=True)
 assert checked.returncode in (0,1),(checked.returncode,checked.stderr)
 ignored=checked.stdout.splitlines();assert set(ignored)<=set(paths)
 (out/'check_ignore.json').write_text(json.dumps({'argv':['git','check-ignore','--',*paths],
  'returncode':checked.returncode,'ignored_paths':ignored,'stdout':checked.stdout,'stderr':checked.stderr},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (out/'stage-paths.txt').write_text(''.join(p+'\n' for p in paths),encoding='utf-8')
 (out/'files-to-force-add.txt').write_text(''.join(p+'\n' for p in ignored),encoding='utf-8')
verified=verify_evidence_bundle(DEST);manifest=read(DEST/'manifest.json')
assert set(p.name for p in DEST.iterdir())==set(manifest['outputs_sha256'])|{'manifest.json'}
assert all(sha(ROOT/p)==s for p,s in manifest['sources_sha256'].items())
assert all((report.parent/link).resolve().is_file() for link in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')))
raw_whitespace={}
for name in manifest['outputs_sha256']:
 p=DEST/name
 try:lines=p.read_text(encoding='utf-8').splitlines()
 except UnicodeError:continue
 bad=[i for i,line in enumerate(lines,1) if line.endswith((' ','\t'))]
 if bad:raw_whitespace[p.relative_to(ROOT).as_posix()]=bad
result={**verified,'manifest_sha256':sha(DEST/'manifest.json'),'unique_copies':len(mapping),
 'input_aliases':len(aliases),'sources':len(manifest['sources_sha256']),'report_sha256':sha(report),
 'all_copy_source_prepost_sha_verified':True,'all_native_original_SHA_unchanged':True,
 'all_report_links_exist':True,'raw_whitespace_paths_lines':raw_whitespace,'ignored_paths':ignored,
 'bundle_bytes':sum(p.stat().st_size for p in DEST.iterdir()),'no_tests_native_or_models_rerun':True}
with (PREP/'closure_verification.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
