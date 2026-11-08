"""Đóng evidence viewer; chỉ đọc/copy/hash, không app/test/model/replay."""
from pathlib import Path
import hashlib,json,os,struct,subprocess,sys,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[5]
assert Path(sys.prefix).resolve()==ROOT/'.venv'
sys.path.insert(0,str(ROOT))
from src.knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
from src.research_demo.evidence import PINS,CLOSED_RUN,CLOSED_MANIFEST_SHA,CLOSED_PINS
PREP=Path(__file__).resolve().parent;BASE=PREP.parent
RUN='demo-closed-loop-engineering-20261108-01';DEST=ROOT/'research_tracking/runs'/RUN
assert not DEST.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
receipt=read(BASE/'c14-t2/run.json');first=read(BASE/'c14-t1/run.json')
assert receipt['counts']=={'tests':83,'failures':0,'errors':0,'skipped':0}
assert receipt['source_sha256_before']==receipt['source_sha256_after']
assert receipt['cumulative_all_attempts_seconds']<=60
assert first['counts']=={'tests':83,'failures':36,'errors':0,'skipped':0}
for relative,digest in receipt['source_sha256_before'].items():assert sha(ROOT/relative)==digest
for trial,expected in [('c14-t1',(83,36,0,0)),('c14-t2',(83,0,0,0))]:
 suite=ET.parse(BASE/trial/'pytest.xml').getroot().find('testsuite')
 assert tuple(int(suite.attrib[k]) for k in ('tests','failures','errors','skipped'))==expected
 if trial=='c14-t1':assert all('WinError 10013' in f.text for f in suite.findall('testcase/failure'))
full=read(PREP/'ui02-full-firstbreak.json');empty=read(PREP/'ui02-empty-negative.json')
membership=read(PREP/'ui02-membership-firstbreak.json');mobile=read(PREP/'ui02-mobile-geometry.json')
back=read(PREP/'ui02-back-fixed.json')
assert full['step']==61 and full['probabilityMatches'] and full['conceptMatches'] and full['conceptRows']==28 and full['routeEntries']==62 and full['rankingRows']==10 and full['noVisibleError']
assert all(d['status']==200 for d in full['sources'])
assert empty['jumpDisabled'] and empty['noVisibleError'] and 'negative case' in empty['prefix']
assert membership['step']=='27' and 'membership đổi' in membership['ranking'] and membership['noVisibleError']
assert mobile['width']==390 and mobile['height']==844 and mobile['noPageOverflow']
assert back['mode']=='fixed_preview' and back['closedHidden'] and back['noVisibleError']
assert 'Errors: 0, Warnings: 0' in (PREP/'ui02-console-errors.txt').read_text()
assert read(PREP/'preview-shutdown.json')['source_unchanged']
shutdown=read(PREP/'preview-shutdown02.json');assert shutdown['stop_marker'] and shutdown['source_unchanged']
png_dims=lambda p:struct.unpack('>II',p.read_bytes()[16:24])
assert png_dims(PREP/'ui02-desktop1366.png')==(1037,683)
assert png_dims(PREP/'ui02-mobile390.png')==(390,844)

mapping={}
def add(p,name):
 assert p.is_file() and not p.is_symlink() and name not in mapping
 assert p.suffix not in ('.pt','.parquet','.zip')
 mapping[name]=p
for relative in receipt['source_sha256_before']:add(ROOT/relative,'source__'+relative.replace('/','__'))
for relative in ('src/research_demo/__init__.py','src/research_demo/static/style.css','src/knowledge_tracing/evidence.py'):
 p=ROOT/relative
 if p.is_file():add(p,'dependency__'+relative.replace('/','__'))
report=ROOT/'research_tracking/reports/demo_closed_loop_readiness_20261108.md'
add(report,'report__'+report.name)
for p in sorted(PREP.iterdir()):
 if p.is_file():add(p,'prep__'+p.name)
for trial in ('c14-t1','c14-t2'):
 for p in sorted((BASE/trial).iterdir()):
  if p.is_file():add(p,trial+'__'+p.name)

inputs={}
def bind(p,digest):
 assert sha(p)==digest
 inputs[p.relative_to(ROOT).as_posix()]={'sha256':digest,'bytes':p.stat().st_size,'role':'EXISTING_COMMITTED_SELECTED_EVIDENCE_NO_NEW_REPLAY'}
for run,manifest_digest,name,digest in PINS:
 d=ROOT/'research_tracking/runs'/run;bind(d/'manifest.json',manifest_digest);bind(d/name,digest)
d=ROOT/'research_tracking/runs'/CLOSED_RUN;bind(d/'manifest.json',CLOSED_MANIFEST_SHA)
assert read(d/'manifest.json')['status']=='completed'
for name,digest,_ in CLOSED_PINS:bind(d/name,digest)
before={n:{'source':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for n,p in mapping.items()}
sources=sorted(set(mapping.values())|{ROOT/p for p in inputs})
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
note='''# Demo closed-loop — kiểm kỹ thuật E11 một phần, 08/11/2026

Trình xem cùng trang cho artifact GAM/Paper2 đã committed; không chạy model,
optimizer, policy, simulator/replay, GPU/cloud hoặc đọc raw/Test. Native B-score
không calibrated mastery. Source-local CID ranking là POST-HOC, new N=0,
không qid/difficulty/causal/edge-only benefit. P served item sau select.
Sau histories divergence không paired ΔP/loss. Giữ bảy negative comparisons.

Trial01 47pass/36fail: HTTP connect WinError10013; giữ nguyên failure log/XML.
Trial02 cùng source83PASS/0fail/error/skip,8.0692843s controller;
cumulative36.1590131s<=60s có reserve1s. Kiểm phần mềm không RQ completion.
QA01 server hết cap180s -> Failed to fetch; QA02 hoàn tất, server/tab riêng đóng.
Screenshot tên desktop1366 thực tế1037x683; mobile390x844, không pageoverflow.
Ảnh viewport đã đọc, không exhaustive accessibility/browser certification.

Report canonical: ../../reports/demo_closed_loop_readiness_20261108.md
report__ snapshot giữ nguyên byte; snapshots không phải entrypoint hiện hành.
Inputs khoa học đã committed chỉ inventory/path/SHA, không duplicate gzip lớn.
Không copy pytest t/temp, private MCP, checkpoint, Parquet, credentials.
copy_inventory.json ghi nguồn trước/sau và exactcopies; manifest hash mọi output.
Bundle bất biến sau closure. Không rootindex/state/Git mutation.
'''
metadata={'kind':'READONLY_CLOSED_LOOP_VIEWER_ENGINEERING_PARTIAL_E11','rq':['RQ1','RQ2'],'model_optimizer_research_replay_calls':0,'new_independent_N':0,'scientific_inference':'SOURCE_LOCAL_POSTHOC_STORED_ONLY','targeted_tests':receipt['counts'],'cumulative_test_seconds':receipt['cumulative_all_attempts_seconds'],'test_cap_seconds':60,'selected_inputs':inputs,'source_revision':receipt['source_sha256_before']}
with record_evidence_run(ROOT,RUN,metadata=metadata,sources=sources,note=note) as out:
 for name,p in mapping.items():
  with (out/name).open('xb') as f:f.write(p.read_bytes())
  assert sha(out/name)==before[name]['sha256']
 after={name:sha(p) for name,p in mapping.items()}
 assert all(after[n]==i['sha256'] for n,i in before.items())
 assert all(sha(ROOT/p)==i['sha256'] for p,i in inputs.items())
 inventory={'source_inventory_before':before,'source_sha256_after':after,'copied_output_sha256':{n:sha(out/n) for n in mapping},'exact_copy_identity':True,'pre_post_source_identity':True,'referenced_committed_inputs':inputs,'no_source_overwrites':True,'excluded':'pytest temp folders/private MCP/checkpoint/Parquet; no dataset/realdata/Test','screenshots_actual_dimensions':{'prep__ui02-desktop1366.png':[1037,683],'prep__ui02-mobile390.png':[390,844]}}
 (out/'copy_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 extras=['README.md','execution.log','copy_inventory.json','check_ignore.json','files-to-force-add.txt','stage-paths.txt','manifest.json']
 paths=sorted(f'research_tracking/runs/{RUN}/{n}' for n in [*mapping,*extras])
 assert all(not any(c in p for c in '\t\r\n') for p in paths)
 checked=subprocess.run(['git','check-ignore','--',*paths],cwd=ROOT,text=True,capture_output=True)
 assert checked.returncode in (0,1),(checked.returncode,checked.stderr)
 ignored=checked.stdout.splitlines();assert set(ignored)<=set(paths)
 (out/'check_ignore.json').write_text(json.dumps({'argv':['git','check-ignore','--',*paths],'returncode':checked.returncode,'stdout':checked.stdout,'stderr':checked.stderr,'ignored_paths':ignored,'path_tab_LF_CR_absent':True},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (out/'files-to-force-add.txt').write_text(''.join(p+'\n' for p in ignored),encoding='utf-8')
 (out/'stage-paths.txt').write_text(''.join(p+'\n' for p in paths),encoding='utf-8')
verification=verify_evidence_bundle(DEST)
manifest=read(DEST/'manifest.json')
assert set(p.name for p in DEST.iterdir())==set(manifest['outputs_sha256'])|{'manifest.json'}
assert set((DEST/'stage-paths.txt').read_text().splitlines())==set(p.relative_to(ROOT).as_posix() for p in DEST.iterdir())
assert all(sha(ROOT/p)==i['sha256'] for p,i in inputs.items())
result={**verification,'manifest_sha256':sha(DEST/'manifest.json'),'report_sha256':sha(report),'exact_copy_pairs':len(mapping),'source_bindings':len(manifest['sources_sha256']),'selected_committed_inputs':len(inputs),'all_source_prepost_and_copy_sha':True,'all_outputs_exact':True,'ignored_paths':len(ignored),'sources_frozen':receipt['source_sha256_before'],'no_model_tests_or_replay_during_pack':True}
with (PREP/'closure_verification.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
