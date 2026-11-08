"""Archive toy Graph-GAM evidence đã chạy; không model/test/data/network rerun."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT=Path.cwd().resolve()
assert Path(sys.prefix).resolve()==ROOT/'.venv'
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle

count=int(os.environ.get('GIT_CONFIG_COUNT','0'))
os.environ[f'GIT_CONFIG_KEY_{count}']='safe.directory'
os.environ[f'GIT_CONFIG_VALUE_{count}']=ROOT.as_posix()
os.environ['GIT_CONFIG_COUNT']=str(count+1)
RUN='graph-gam-variant-engineering-20261108-01'
TEST='artifacts/akt/local-tests/parallel-graph-gam-variant-20261108-01/'
PRE='artifacts/akt/local-tests/graph-gam-pretest-review-20261108-01/'
REPORT='research_tracking/reports/graph_gam_variant_readiness_20261108.md'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

run=json.loads((ROOT/(TEST+'run.json')).read_text(encoding='utf-8'))
assert run['returncode']==0 and run['all_sources_unchanged'] and run['elapsed_seconds']<60
assert run['source_sha256_before']==run['source_sha256_after']
for name,digest in run['source_sha256_before'].items():assert sha(ROOT/name)==digest,name
suites=ET.parse(ROOT/(TEST+'pytest.xml')).getroot().findall('testsuite')
counts={key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ('tests','failures','errors','skipped')}
assert counts=={'tests':38,'failures':0,'errors':0,'skipped':0}
ledger=json.loads((ROOT/(TEST+'toy_update_ledger.json')).read_text())
assert ledger['actual_native_update_calls']==len(ledger['calls'])==97<=512
assert ledger['optimizer_steps']==ledger['global_fit_calls']==0
notebook=next(name for name in run['source_sha256_before'] if name.endswith('.ipynb'))
cell=''.join(json.loads((ROOT/notebook).read_text(encoding='utf-8'))['cells'][11]['source']).encode()
cell_sha=hashlib.sha256(cell).hexdigest()
assert cell_sha=='5fc0adbf8fcb454b73bbdd3294bb20e17c2a08ec9eb496b7383677f38b04a5fc'
pairs=[
 ('src/knowledge_tracing/gam_kt/variant_factory.py','variant_factory.py'),
 ('tests/gam_kt/test_variant_factory.py','test_variant_factory.py'),
 (REPORT,'readiness_report.md'),
 ('src/knowledge_tracing/gam_kt/original_junyi.py','native_original_junyi.py'),
 ('src/knowledge_tracing/gam_kt/replay.py','native_replay.py'),
 ('src/knowledge_tracing/gam_kt/model.py','existing_graph_free_factory.py'),
 ('src/knowledge_tracing/evidence.py','evidence_helper_source.py'),
 (str(Path(__file__).resolve().relative_to(ROOT).as_posix()),'pack_evidence.py'),
 (TEST+'pytest.log','targeted-pytest.log'),(TEST+'pytest.xml','targeted-pytest.xml'),
 (TEST+'run.json','test_run.json'),(TEST+'toy_update_ledger.json','toy_update_ledger.json'),
 (TEST+'source_inventory_before.json','targeted_sources_before.json'),
 (PRE+'factory_before_review.py','pretest_factory.py'),
 (PRE+'tests_before_review.py','pretest_tests.py'),
 (PRE+'inventory_before.json','pretest_copy_before.json'),
 (PRE+'inventory_after.json','pretest_copy_after.json'),
 (PRE+'review.json','pretest_static_review.json')]
before=[{'source':name,'copy':alias,'sha256_before_copy':sha(ROOT/name)} for name,alias in pairs]
sources=sorted({ROOT/name for name,_ in pairs}|{ROOT/name for name in run['source_sha256_before']})
metadata={'kind':'GRAPH_GAM_ISOLATED_VARIANT_TOY_ENGINEERING',
 'role':'synthetic_online_state_engineering_only','research_fitted_model':False,
 'test_counts':counts,'native_update_calls_in_targeted_suite':97,
 'native_update_call_budget':512,'max_interactions_per_session':32,'max_exercise_nodes':16,'max_edges':64,
 'optimizer_steps':0,'global_fit_calls':0,'new_test_or_model_calls_during_archive':0,
 'test_controller_elapsed_seconds':run['elapsed_seconds'],'test_timeout_seconds':60,
 'source_files_verified_before_after_test':len(run['source_sha256_before']),
 'reference_cell_sha256':cell_sha,'existing_runner_still_graph_free':True,
 'scope_vi':'Source/variant isolation parity trên toy, không CV/selected-fit/OnlineSession/calibration/RQ efficacy.'}
note='''# Graph-GAM isolated variant factory — toy engineering 08/11/2026

Bundle giữ3canonical files mới và bằng chứng đã chạy.38targeted cases pass1.41s,
controller2.114884s<60;97native online-update calls gồm source reference/candidate,
dưới cap512, tối đa32/session;0optimizer/globalfit. Không rerun ở bước archive.
Source factory/test đã frozen; core/native/model/runner/evaluation/simulator wrappers
giữ nguyên. Parent xử lý root tracking/Git, không tự nâng readiness toàn mô hình.

Factory compile/exec nguyên trusted original_junyi.py trong namespace riêng; private
metadata/cache và freshlearner. Native adaptation vẫn coupling parent+local, empty
graph adaptation có thể khác alloff.6fixture recipes bao phủ cả4flag combinations
và empty/nonempty controls, không scientific defaults hoặc selected configuration.
Predict nguồn lazily tạo prior states; không pure/transactional query claim.
Wrapper nhận toy known exercises/nonempty bounded metadata/chronological events;
đó là accepted subset, không thay toàn bộ native/Junyi input range.

Reference source: paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/
source/junyi_cycle_corrected_ablation_confirmation.ipynb, cell11. source_provenance.json
giữ whole notebook SHA, exact cellSHA và mappings; reference_cell11.py.txt chỉ là
definition text, không preprocessing/dataset loader hoặc notebook toàn bộ được chạy.

Pretest review P2 phát hiện graph declaration hash chưa bind actual mutable parents.
Snapshot2files/reviewnote được giữ trước fix (0test/0update, không giả redtest).
Final graph frozen + materialized parent mapping hash có deterministic tamper test;
source/metadata/recipe guards và source-cell parity đã qua suite mới. Không có failed
targeted test invocation trong batch này; static finding không bị gọi failed test.

Không realdata/Holdout/CV, source notebook edit, fit/training model toàn cục,
GPU/cloud/network/install hoặc fitted/shared OnlineSession promotion. S04/S05,
train-only graph/difficulty artifacts, graph-enabled runner, export/resume,
mastery calibration và efficacy/inference vẫn pending. Snapshot report giữ links
canonical repository gốc; archive không standalone runtime/checkpoint bundle.

copy_inventory_before.json ghi trước18copies, copy_inventory.json đối chiếu bytes/SHA;
sources_sha256 manifest giữ provenance. record_evidence_run/verify_evidence_bundle
đóng/kiểm integrity rồi chỉ đọc. git_ignore_check.json dùng path argv tường minh,
không stdin; force_add_paths.txt là danh sách chính xác bị ignore. Git chỉ đọc;
safe.directory chỉ process, không add/commit/push/globalconfig/index/state.
'''
with record_evidence_run(ROOT,RUN,metadata=metadata,sources=sources,note=note) as directory:
    (directory/'copy_inventory_before.json').write_text(json.dumps(before,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    after=[]
    for row in before:
        source=ROOT/row['source'];assert sha(source)==row['sha256_before_copy']
        target=directory/row['copy']
        with target.open('xb') as stream:stream.write(source.read_bytes())
        record={**row,'sha256_after_copy':sha(target)}
        assert record['sha256_before_copy']==record['sha256_after_copy'];after.append(record)
    (directory/'copy_inventory.json').write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (directory/'reference_cell11.py.txt').write_bytes(cell)
    provenance={'native_source':'src/knowledge_tracing/gam_kt/original_junyi.py',
        'native_source_sha256':run['source_sha256_before']['src/knowledge_tracing/gam_kt/original_junyi.py'],
        'reference_notebook':notebook,'reference_notebook_sha256':run['source_sha256_before'][notebook],
        'reference_cell':11,'reference_cell_sha256':cell_sha,
        'reference_execution_scope':'only cell11 definitions; no preprocessing or dataset IO',
        'original_sources_unchanged':run['source_sha256_before'],
        'fixture_role':'manually seeded synthetic states; not fitted research or educational outcome'}
    (directory/'source_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    review={'reviewer':'rq12_evidence_synthesis','phase':'static review before first suite',
        'status':'FIX_REVIEW_PASS','reviewed_source_sha256':run['source_sha256_before']['src/knowledge_tracing/gam_kt/variant_factory.py'],
        'reviewed_test_sha256':run['source_sha256_before']['tests/gam_kt/test_variant_factory.py'],
        'finding_fixed':'frozen graph and actual materialized node/ordered-parent mapping bound in identity',
        'remaining_scope':'metadata accepted toy subset; no selected-fit/OnlineSession/S04S05/RQ efficacy',
        'reviewer_model_or_test_execution':False,'numerical_results_source':'targeted-pytest.log/xml and test_run.json, not static verdict'}
    (directory/'static_fix_review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
    planned={'manifest.json','README.md','execution.log','copy_inventory_before.json','copy_inventory.json',
             'reference_cell11.py.txt','source_provenance.json','static_fix_review.json',
             'git_ignore_check.json','force_add_paths.txt',*(alias for _,alias in pairs)}
    checks=[];force=[]
    for name in sorted(planned):
        path=(directory/name).relative_to(ROOT).as_posix()
        command=['git','check-ignore','--no-index','--verbose','--',path]
        result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,timeout=10)
        assert result.returncode in (0,1),(command,result.stderr)
        ignored=result.returncode==0
        checks.append({'path':path,'argv':command,'ignored':ignored,'returncode':result.returncode,
                       'stdout':result.stdout.strip(),'stderr':result.stderr.strip(),'stdin_used':False})
        if ignored:force.append(path)
    assert force==[f'research_tracking/runs/{RUN}/execution.log',f'research_tracking/runs/{RUN}/targeted-pytest.log']
    (directory/'git_ignore_check.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
    (directory/'force_add_paths.txt').write_text('\n'.join(force)+'\n',encoding='utf-8')
    assert {p.name for p in directory.iterdir()}==planned
verified=verify_evidence_bundle(directory)
manifest=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
assert {p.name for p in directory.iterdir()}=={'manifest.json',*manifest['outputs_sha256']}
for row in after:assert sha(ROOT/row['source'])==sha(directory/row['copy'])==row['sha256_before_copy']
links=[]
for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)',(ROOT/REPORT).read_text(encoding='utf-8')):
    assert not link.startswith(('http:','https:'))
    target=(ROOT/REPORT).parent/link
    assert target.is_file(),link
    links.append(link)
print(json.dumps({'bundle':directory.relative_to(ROOT).as_posix(),'verified':verified,
 'exact_copy_pairs':len(after),'canonical_report_links_checked':len(links),
 'manifest_sha256':sha(directory/'manifest.json'),'force_add_paths':force},indent=2))
