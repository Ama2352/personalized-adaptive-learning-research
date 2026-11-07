"""Archive validation RQ2 đã chạy; không chạy lại analysis/tests hoặc mở raw data."""
from pathlib import Path
import hashlib,json,os,sys,xml.etree.ElementTree as ET
ROOT=Path.cwd().resolve()
if Path(sys.prefix).resolve()!=ROOT/'.venv':
    raise ValueError('Chỉ dùng project .venv')
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
BASE='artifacts/akt/local-tests/parallel-rq2-controls-20261108-01/'
PRIMARY='research_tracking/runs/rq2-conditions-evidence-20261108-01/'
RUN='rq2-conditions-validation-20261108-01'
PAIRS=[
 ('scripts/research/analyze_rq2_controls.py','analysis_source.py'),
 ('tests/shared_kt/test_rq2_controls.py','test_source.py'),
 ('research_tracking/reports/rq2_conditions_evidence_20261108.md','rq2_conditions_report.md'),
 ('src/knowledge_tracing/evidence.py','evidence_helper_source.py'),
 (BASE+'pytest.log','synthetic_tests.log'),
 (BASE+'pytest.xml','synthetic_tests.xml'),
 (BASE+'run.json','synthetic_test_run.json'),
 (BASE+'analysis-01.log','primary_analysis.log'),
 (BASE+'analysis-01-run.json','primary_analysis_run.json'),
 (BASE+'reproduce.log','reproduction.log'),
 (BASE+'reproduce-run.json','reproduction_run.json'),
 (BASE+'reproduced_conditions.json','reproduced_conditions.json'),
 (PRIMARY+'conditions.json','primary_conditions.json'),
 (PRIMARY+'manifest.json','primary_analysis_manifest.json'),
 (PRIMARY+'copy_inventory.json','primary_source_copy_inventory.json'),
]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inventory=[{'source':a,'archived_as':b,'sha256_before_copy':sha(ROOT/a)} for a,b in PAIRS]
suites=ET.parse(ROOT/(BASE+'pytest.xml')).getroot().findall('testsuite')
counts={k:sum(int(s.attrib.get(k,0)) for s in suites) for k in ('tests','failures','errors','skipped')}
assert counts=={'tests':27,'failures':0,'errors':0,'skipped':0}
test_run=json.loads((ROOT/(BASE+'run.json')).read_text(encoding='utf-8'))
assert test_run['exit_code']==0 and test_run['sources_unchanged'] is True
for a in ['analysis-01-run.json','reproduce-run.json']:
    assert json.loads((ROOT/(BASE+a)).read_text(encoding='utf-8'))['exit_code']==0
assert sha(ROOT/(PRIMARY+'conditions.json'))==sha(ROOT/(BASE+'reproduced_conditions.json'))
primary_integrity=verify_evidence_bundle(ROOT/PRIMARY)
result=json.loads((ROOT/(PRIMARY+'conditions.json')).read_text(encoding='utf-8'))
assert len(result['input_sha256'])==13
for name,digest in result['input_sha256'].items():
    assert sha(ROOT/name)==digest,name
source_text=os.environ.get('KLTN_RQ2_VALIDATION_SOURCE')
if source_text is None:source_text=Path(__file__).read_text(encoding='utf-8')
source_bytes=source_text.encode('utf-8')
force=[f'research_tracking/runs/{RUN}/'+name for name in ['execution.log','synthetic_tests.log','primary_analysis.log','reproduction.log']]
metadata={'kind':'RQ2_STORED_ANALYSIS_VALIDATION_ARCHIVE','rq':['RQ2'],
 'purpose_vi':'Giữ source/report/log/JUnit và exact reproduction; không new experiment.',
 'new_raw_queries':0,'new_model_simulator_runs':0,'new_graph_generation':0,
 'primary_analysis_run':'rq2-conditions-evidence-20261108-01',
 'primary_analysis_integrity':primary_integrity,
 'synthetic_test_counts':counts,
 'selected_input_hashes_verified':13,
 'primary_reproduction_sha256':sha(ROOT/(PRIMARY+'conditions.json')),
 'pack_source_sha256':hashlib.sha256(source_bytes).hexdigest(),
 'scope_vi':'Descriptive/exploratory aggregate reanalysis; không efficacy, causal ability effect, equivalence hoặc formal CI.'}
note='''# RQ2: validation và report snapshot — 08/11/2026

Archive nhỏ giữ source/report và các kiểm đã chạy. Primary analysis run
rq2-conditions-evidence-20261108-01 bất biến, verified6outputs. Không chạy lại
model/simulator/tests/analysis ở archive này; không raw Junyi/correctness/Holdout,
outcomes/traces hoặc graph generation. Không thêm independent empirical samples.

27 synthetic tests pass0.37s. Primary arithmetic0.129116s đọc13selectedinputs có
SHA đối chiếu selected manifests. Reproduction PYTHONHASHSEED17 khớp rawbytes/SHA.
Run/control receipts ghi commands/timeouts60s; không có failed targeted attempt
trong workflow đã lưu. Source snapshots pre/post tests giống nhau, copies exact.

Findings mới: paired profile moderation PYH-PY có5seed dương/5âm và LOO đổi dấu,
không causal ability effect. Junyi removed/added/shared decomposition tách đúng
corrected976edges/raw979edges và same-learner exposure; pooledrate của control2
tăng dù numerator giảm do denominator giảm. Fixed/common learner estimands và
attrition khác; không quality/equivalence/instructional-effect inference.

archive_copy_inventory_before.json lập trước copy; archive_copy_inventory.json
đối chiếu source/destination SHA. Report/script snapshots giữ links repository
gốc; inventory chỉ rõ mapping, không giả bundle là standalone runtime.
record_evidence_run/verify_evidence_bundle đóng và kiểm output hashes; từ closure
chỉ đọc. *.log cần force-add theo force_add_paths.txt. Không sửa rootindex/state
hoặc Git. Đây là validation của một stored reanalysis, không thí nghiệm thứ hai.
'''
with record_evidence_run(ROOT,RUN,metadata=metadata,sources=[ROOT/a for a,b in PAIRS],note=note) as directory:
    (directory/'pack_evidence.py').write_bytes(source_bytes)
    (directory/'archive_copy_inventory_before.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    after=[]
    for item in inventory:
        assert sha(ROOT/item['source'])==item['sha256_before_copy']
        target=directory/item['archived_as'];target.write_bytes((ROOT/item['source']).read_bytes())
        row={**item,'sha256_after_copy':sha(target)}
        row['exact_match']=row['sha256_before_copy']==row['sha256_after_copy']
        assert row['exact_match']
        after.append(row)
    (directory/'archive_copy_inventory.json').write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (directory/'force_add_paths.txt').write_text('\n'.join(force)+'\n',encoding='utf-8')
# Chỉ đọc sau closure.
verified=verify_evidence_bundle(directory)
manifest=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
assert {p.name for p in directory.iterdir()}=={'manifest.json',*manifest['outputs_sha256']}
print(json.dumps({'bundle':str(directory.relative_to(ROOT)),'verified':verified,'copies_exact':len(after),
 'input_hashes_verified':13,'manifest_sha256':sha(directory/'manifest.json'),'force_add_paths':force},ensure_ascii=False,indent=2))
