"""Archive portability evidence đã có; không rerun tests/model/cloud."""
import ast
import base64
import hashlib
import io
import json
import math
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path.cwd().resolve()
if Path(sys.prefix).resolve() != ROOT / '.venv':
    raise ValueError('Chỉ project .venv từ repository root')
sys.path.insert(0, str(ROOT/'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
RUN_ID='cpu-portability-gate-20261107-01'
L='artifacts/akt/local-tests/'
P='artifacts/akt/preflight/'
C='artifacts/akt/colab/'
R='research_tracking/reports/'
PAIRS=[]
for trial in ('01','02','03'):
    for extension, original in (('log','pytest.log'),('xml','pytest.xml')):
        PAIRS.append((L+'parallel-platform-20261107-'+trial+'/'+original, 'platform-trial'+trial+'.'+extension))
PAIRS += [
    ('tests/akt/test_runner.py','test_runner_source.py'),
    ('tests/akt/test_runtime.py','test_runtime_source.py'),
    ('src/knowledge_tracing/akt/runner.py','runner_source.py'),
    ('scripts/akt/check_runtime.py','check_runtime_source.py'),
    (R+'colab_platform_fixtures_20261107.md','platform_fixtures_report.md'),
    (P+'gate2-evidence-20261107-parallel-portability-15.json','gate15_report.json'),
    (P+'gate2-tests-20261107-parallel-portability-15.log','gate15_tests.log'),
    (P+'gate2-tests-20261107-parallel-portability-15.xml','gate15_tests.xml'),
    (P+'gate2-pointer-before-20261107-parallel-portability-15.json','gate15_pointer_before.json'),
    (P+'gate2-current.json','gate_current_at_archive.json'),
    (L+'vscode-notebook-v12-verification.json','v12_harness_verification.json'),
    (L+'vscode-notebook-v12-verification.log','v12_harness_verification.log'),
    (L+'verify_vscode_colab_notebook_v12.py','verify_vscode_colab_notebook_v12.py'),
    (L+'colab-dependency-pin-v12-verification.json','v12_dependency_pin_verification.json'),
    (L+'check_colab_dependency_pin_v12.py','check_colab_dependency_pin_v12.py'),
    (C+'duckdb-api-contrast-20261107.json','duckdb_actual_version_contrast.json'),
    (C+'duckdb-api-contrast-receipt.json','duckdb_actual_raw_receipt.json'),
    (C+'requests/add-duckdb-api-probe.json','duckdb_probe_code_request.json'),
    (C+'requests/run-duckdb-api-probe.json','duckdb_probe_run_request.json'),
    (L+'duckdb-copy-api-local-20261107.json','duckdb_local_api_proof.json'),
    ('notebooks/akt_colab_synthetic.ipynb','akt_colab_synthetic_v12_snapshot.ipynb'),
    (R+'rq12_evidence_synthesis_20261107.md','rq12_synthesis_snapshot.md'),
    (R+'rq12_evidence_synthesis_20261107.json','rq12_synthesis_snapshot.json'),
    ('src/knowledge_tracing/evidence.py','evidence_helper_source.py'),
]

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path): return json.loads((ROOT/path).read_text(encoding='utf-8'))
def close(a,b): assert abs(a-b)<=1e-12,(a,b)
def counts(path):
    suites=ET.parse(ROOT/path).getroot().findall('testsuite')
    return {key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ('tests','failures','errors','skipped')}

# Inventory được tính trước mọi copy, bao gồm receipts chỉ định; không credentials/private config.
inventory=[{'source':s,'archived_as':d,'sha256_before_copy':digest(ROOT/s)} for s,d in PAIRS]
platform_counts={trial:counts(L+'parallel-platform-20261107-'+trial+'/pytest.xml') for trial in ('01','02','03')}
assert platform_counts['01']=={'tests':1,'failures':0,'errors':1,'skipped':0}
for trial in ('02','03'):
    assert platform_counts[trial]=={'tests':21,'failures':0,'errors':0,'skipped':0}
gate=load(P+'gate2-evidence-20261107-parallel-portability-15.json')
gate_digest=digest(ROOT/(P+'gate2-evidence-20261107-parallel-portability-15.json'))
assert gate_digest=='7e15832f72632dd07f676ef277a8ad49d3f4a71ef35c8f40099492f5b9071f16'
assert gate['test_result']=={'passed':462,'failed':0,'errors':0,'skipped':0}
assert counts(P+'gate2-tests-20261107-parallel-portability-15.xml')=={'tests':462,'failures':0,'errors':0,'skipped':0}
assert digest(ROOT/(P+'gate2-tests-20261107-parallel-portability-15.log'))==gate['test_log_sha256']
assert digest(ROOT/(P+'gate2-tests-20261107-parallel-portability-15.xml'))==gate['junit_sha256']
assert '462 passed in 294.17s' in (ROOT/(P+'gate2-tests-20261107-parallel-portability-15.log')).read_text(encoding='utf-8')
pointer=load(P+'gate2-current.json')
assert pointer['evidence_sha256']==gate_digest and pointer['test_log_sha256']==gate['test_log_sha256']
assert pointer['evidence_file']=='gate2-evidence-20261107-parallel-portability-15.json'
source_checks={}
for path in ('tests/akt/test_runner.py','tests/akt/test_runtime.py','src/knowledge_tracing/akt/runner.py','scripts/akt/check_runtime.py'):
    source_checks[path]=digest(ROOT/path)
    assert source_checks[path]==gate['build_hashes'][path]
expected_tests={'tests/akt/test_runner.py':'a2523287d0576b648139c6a4d589b3e80b773404bae6824c2b34752fdccc0386',
                'tests/akt/test_runtime.py':'5df59d195bc2f895451488a2d41cba6a77a4f834e801e4a2b970fc2a0c9fec3a'}
for path,value in expected_tests.items():assert source_checks[path]==value

harness=load(L+'vscode-notebook-v12-verification.json')
assert harness['status']=='PASS' and harness['case_count']==len(harness['cases'])==20
assert all(case['status']=='PASS' for case in harness['cases'])
notebook=load('notebooks/akt_colab_synthetic.ipynb')
notebook_sha=digest(ROOT/'notebooks/akt_colab_synthetic.ipynb')
assert notebook_sha==harness['notebook_sha256']=='e75004d19a500ad562d7e7a11656158fae4cb74c8fc74c8fd389214e566616a7'
code_cells=[cell for cell in notebook['cells'] if cell['cell_type']=='code']
assert len(code_cells)==harness['code_cells_ast_valid']==7
assert all(not c.get('outputs') and c.get('execution_count') is None for c in code_cells)
bootstrap=next(''.join(c['source']) for c in code_cells if c['id']=='akt-bootstrap')
assignments={node.targets[0].id:node.value for node in ast.parse(bootstrap).body
             if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name)}
embedded=base64.b64decode(ast.literal_eval(assignments['BUNDLE_BASE64']),validate=True)
embedded_sha=hashlib.sha256(embedded).hexdigest()
assert embedded_sha==harness['embedded_bundle_sha256']==digest(ROOT/(C+'akt-synthetic-20261107-v12.zip'))
with zipfile.ZipFile(io.BytesIO(embedded)) as archive:
    embedded_manifest=json.loads(archive.read('BUNDLE_MANIFEST.json'))
    assert len(embedded_manifest['files'])==139
    assert set(archive.namelist())=={'BUNDLE_MANIFEST.json',*embedded_manifest['files']}
    for path,expected in embedded_manifest['files'].items():
        assert hashlib.sha256(archive.read(path)).hexdigest()==expected
pin=load(L+'colab-dependency-pin-v12-verification.json')
assert pin['status']=='PASS' and len(pin['cases'])==4 and all(c['status']=='PASS' for c in pin['cases'])
assert pin['venv_before_install_guard'] and pin['wheel_only_and_install_report']
contrast=load(C+'duckdb-api-contrast-20261107.json')
assert contrast['status']=='DUCKDB_API_VERSION_CONTRAST_PASS'
assert contrast['before']['version']=='1.3.2' and contrast['before']['status']=='ERROR'
assert contrast['after']['version']=='1.5.6' and contrast['after']['status']=='PASS' and contrast['after']['rows']==[[1,1]]
receipt=load(C+'duckdb-api-contrast-receipt.json')
receipt_text=''.join(receipt['structured_content']['outputs'][0]['text'])
assert json.loads(receipt_text)==contrast
assert not receipt.get('is_error',False)
local=load(L+'duckdb-copy-api-local-20261107.json')
assert local['status']=='PASS' and local['duckdb']=='1.5.6' and local['rows_roundtrip']==[[1,1]]

# Chỉ selected immutable outputs: không rehash/assert42mutable indexes của inventory lịch sử.
synthesis=load(R+'rq12_evidence_synthesis_20261107.json')
assert len(synthesis['input_inventory'])==42
selected=synthesis['selected_output_hash_checks']
assert len(selected)==synthesis['hash_checks_count']==synthesis['hash_checks_passed']==21
selected_checks=[]
for item in selected:
    actual=digest(ROOT/item['path'])
    assert item['match'] and actual==item['sha256']==item['manifest_expected_sha256']
    selected_checks.append({'path':item['path'],'sha256':actual,'matches_recorded_manifest':True})
comparison=load('research_tracking/runs/cpu-rq12-20261107-03/comparisons.json')
for candidate,stored in synthesis['chain'].items():
    rows=[r for r in comparison if r['candidate']==candidate]
    assert len(rows)==9
    for key,value in stored.items():
        if key.startswith('threshold_local_rows_'):
            side=key.removeprefix('threshold_local_rows_')
            computed=sum(r['threshold_local_calibration'][side]['rows'] for r in rows)
        else:computed=sum(r[key] for r in rows)
        assert computed==value,(candidate,key)
factorial=load('research_tracking/runs/cpu-factorial-20261107-01/contrasts.json')
summary=load('research_tracking/runs/cpu-factorial-20261107-01/summary.json')
for profile in ('PG','PY','PYH'):
    rows=[r for r in factorial if r['profile']==profile]
    assert len(rows)==10 and len({r['seed'] for r in rows})==10
    for r in rows:close(r['graph_effect_mechanism_on']-r['graph_effect_mechanism_off'],r['interaction_contrast'])
    value=math.fsum(r['interaction_contrast'] for r in rows)/10
    close(value,summary[profile]['mean_interaction']);close(value,synthesis['factorial'][profile]['mean_interaction'])
followup=load(R+'cpu_pilot_followup_20261107.json')
assert synthesis['factorial_mechanism_coverage']==followup['mechanism_coverage']
assert synthesis['factorial_initial_min_ability']==followup['initial_min_ability_in_pilot']
closed=load('research_tracking/runs/cpu-closedloop-20261107-01/closed_loop_outcomes.json')
assert len(closed)==synthesis['closed_loop']['trajectories']==27
assert sum(len(r['actions']) for r in closed)==synthesis['closed_loop']['events']==3240
factor=math.exp(-.06*14)
close(factor,synthesis['retention_source_fixture']['scaling_factor'])
retention_error=max(abs(r['retained_mean_theta_gain']-factor*r['net_mean_theta_gain']) for r in closed)
close(retention_error,synthesis['closed_loop']['max_retention_identity_absolute_error'])
for profile,stored in synthesis['closed_loop']['profiles'].items():
    rows={(r['seed'],r['variant']):r for r in closed if r['profile']==profile}
    seeds=sorted({key[0] for key in rows})
    assert len(seeds)==stored['paired_seeds']==3
    mean=math.fsum(rows[s,'graph_package']['net_mean_theta_gain']-rows[s,'graph_free']['net_mean_theta_gain'] for s in seeds)/3
    close(mean,stored['mean_graph_package_minus_graph_free_net_gain'])
    disagreement=sum(a!=b for s in seeds for a,b in zip(rows[s,'graph_package']['actions'],rows[s,'graph_free']['actions'],strict=True))
    assert disagreement==stored['actual_action_disagreement']
    assert sum(len(rows[s,'graph_free']['actions']) for s in seeds)==stored['paired_steps']
common=load('research_tracking/runs/cpu-junyi-common-20261107-01/common_population.json')
for row,stored in zip(common['comparisons'],synthesis['junyi_common']['comparisons'],strict=True):
    assert row['seed']==stored['seed']
    contrast_row=row['contrast'];all_fixed=contrast_row['all_fixed_opportunities'];subset=contrast_row['common_coobserved_opportunities']
    for key in ('eligible_learners','fixed_child_opportunities','changed_parent_child_opportunities'):
        assert contrast_row[key]==stored[key]
    assert subset['learners']==stored['common_learners']
    assert contrast_row['common_coobserved_child_opportunities']==stored['common_opportunities']
    close(stored['common_opportunity_retained_fraction'],stored['common_opportunities']/stored['fixed_child_opportunities'])
    close(stored['prior_fraction_control_minus_base'],all_fixed['paired_control_minus_base']['observed_prior_fraction']['mean'])
    close(stored['common_prior_fraction_control_minus_base'],subset['paired_control_minus_base']['observed_prior_fraction']['mean'])
    prior=all_fixed['paired_control_minus_base']['observed_prior_fraction']
    assert prior['positive_learners']+prior['negative_learners']==stored['changed_prior_learners']
for key,value in synthesis['junyi_common']['identity_all_category_mean_contrasts'].items():
    assert value==common['identity_negative_control']['all_fixed_opportunities']['paired_control_minus_base'][key]['mean']==0
source_text=os.environ.get('KLTN_PORTABILITY_PACK_SOURCE')
if source_text is None:source_text=Path(__file__).read_text(encoding='utf-8')
metadata={
 'kind':'CPU_PORTABILITY_AND_NOTEBOOK_HARNESS_EVIDENCE_ARCHIVE', 'schema_version':1,
 'purpose_vi':'Archive platform fixture trials, Gate15, v12 mocked harness/dependency probe và actual1row DuckDB contrast; không rerun workload.',
 'new_workload':{'test_runs':0,'model_training_steps':0,'simulator_events':0,'gpu_cloud_calls':0,'raw_or_holdout_queries':0},
 'gate15':{'report_sha256':gate_digest,'passed':462,'failures':0,'errors':0,'skipped':0,'pytest_seconds':294.17,'scope':'Windows local CPU synthetic/software acceptance; không actual Colab/CUDA acceptance'},
 'platform_junit':platform_counts,
 'v12':{'notebook_sha256':notebook_sha,'embedded_bundle_sha256':embedded_sha,'embedded_files_verified':139,'harness_cases':20,'dependency_mock_cases':4,'scope':'Local extraction/export thật; GPU/setup/CPU guards và dependency probe mocked'},
 'duckdb_vi':'Actual remote one-row API/version contrast1.3.2ERROR→1.5.6PASS trong isolatedvenv; local1.5.6APIproof; không model/realdata/full CPU suite.',
 'synthesis_vi':'Snapshot aggregate synthesis; tự kiểm21selected outputSHA và các bảng arithmetic đã liệt kê.42inputinventory là record lịch sử, không khẳng định current mutableindexes trùng hashes cũ.',
 'limits_vi':['Không standalone full runtime kit hoặc full source snapshot theo mọi Gate15buildhash.',
  'Snapshot current pointer tại archive, không promise pointer còn current sau này.',
  'Harness/dependency scripts snapshot tại archive; prior JSON chưa lưu executed-script SHA riêng.',
  'Software PASS không graph efficacy/trained RQ3/confirmatory inference hoặc GPU success.'],
 'pack_source_sha256':hashlib.sha256(source_text.encode()).hexdigest(),
}
note='''# Archive CPU portability, Gate15 và notebookv12 — 07/11/2026

Đây là evidence archive, không chạy lại Gate/model/tests/probes/cloud. Platform trial01 giữ collection failure thiếu PYTHONPATH; trial02 và03 đều21pass, trong đó02 có29deselected,03 chọn node IDs tường minh không deselect. Source test_runner/test_runtime snapshots khớp report và Gate15buildhash; production runner/check_runtime snapshots cũng khớp Gate15. Giữ nguyên failure/log/XML bytes.

Gate15 actual local Windows CPU462pass0fail/error/skip294.17s; reportsha7e15832f72632dd07f676ef277a8ad49d3f4a71ef35c8f40099492f5b9071f16. Report/log/XML/pointer-before/current-at-archive được snapshot; current pointer sau này có thể đổi. Không coi Gate15 là actual Linux/Colab/CUDA acceptance.

Notebookv12 snapshot khớp harness e75004d19a500ad562d7e7a11656158fae4cb74c8fc74c8fd389214e566616a7; embeddedZIPddb35b8e... và139source files được kiểm exacthash không execution. Notebook đã clear outputs. Harness20cases dùng local extraction/export thật nhưng GPU/setup/CPU guards mocked; dependency probe4cases cũng mocked. Không đọc log CONNECTED_GPU/MOCK_GPU như actual GPU. Snapshot scripts tại archive, prior resultJSON không bind scriptSHA riêng.

DuckDB actual rawconnector receipt khớp contrastJSON: cùngPython/source one-row COPY TO ? trong isolatedvenv,1.3.2ParserException và1.5.6PASS; localAPIproof1.5.6PASS. Scope chỉ one-row API compatibility, không đầy đủ model/realdata/Colab suite. Requestcode giữ cách chạy, không có credentials/private config trong allowlist archive.

RQ12synthesis là snapshot aggregate/descriptive evidence, không confirmatory graph benefit hoặc final efficacy. Tự kiểm21selectedoutputSHA; arithmetic bảng chain, closedloop gain/action disagreement/retention, factorial mean/contrast/coverage và common-population fractions/identity.42inputinventory giữ nguyên lịch sử, không rehash/assert currentmutable indexes hoặc nguồn runtime vẫn như lúc synthesis. Các giới hạn posthoc/pilot/lowcoverage trong reportJSON/MD giữ nguyên; không tự thông qua S04/S05.

archive_copy_inventory.json có SHA trước/sau từng copy. archive_validation.json ghi phạm vi kiểm; manifest hash mọi output và sources đã chọn. BUNDLE_MANIFEST_v12.json chỉ manifest lấy từ ZIP nhúng, không thêm ZIP trùng lặp. pack_evidence.py giữ đúng mã đóng gói dùng helpers có sẵn. Không sửa bundle sau closure. force_add_paths.txt liệt kê các logs bị ignore; không sửa .gitattributes hoặc Git/index/state/tasks trong gói này.
'''
source_paths=list(dict.fromkeys([s for s,_ in PAIRS]+[item['path'] for item in selected]+[
 'research_tracking/runs/cpu-factorial-20261107-01/summary.json',R+'cpu_pilot_followup_20261107.json',C+'akt-synthetic-20261107-v12.zip']))
with record_evidence_run(ROOT,RUN_ID,metadata=metadata,sources=[ROOT/p for p in source_paths],note=note) as directory:
    (directory/'pack_evidence.py').write_bytes(source_text.encode('utf-8'))
    for item in inventory:
        source=ROOT/item['source']; assert digest(source)==item['sha256_before_copy']
        target=directory/item['archived_as'];target.write_bytes(source.read_bytes())
        item['sha256_after_copy']=digest(target);item['exact_match']=item['sha256_after_copy']==item['sha256_before_copy'];assert item['exact_match']
    (directory/'archive_copy_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (directory/'BUNDLE_MANIFEST_v12.json').write_text(json.dumps(embedded_manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (directory/'synthesis_recorded_42input_inventory.json').write_text(json.dumps({'status':'HISTORICAL_RECORD_ONLY_NOT_CURRENT_INPUT_REVALIDATION','recorded_inputs':synthesis['input_inventory']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    validation={'exact_copied_files':len(inventory),'all_pre_post_copy_sha_exact':True,'platform_junit':platform_counts,
      'gate15_report_log_junit_pointer_binding':True,'targeted_source_gate15_bindings':source_checks,
      'notebook_harness_hash_binding':True,'embedded_bundle_files_verified':139,'harness_pass_cases':20,'dependency_pass_mock_cases':4,
      'duckdb_raw_receipt_equals_actual_contrast_json':True,'duckdb_local_api_proof_checked':True,
      'synthesis_selected_output_sha_checks':selected_checks,'synthesis_recorded_input_inventory_count':42,
      'synthesis_arithmetic_checks':['chain_all_counts_and_local_band_denominators','closedloop_means_action_counts_retention','factorial_means_contrasts_and_coverage','common_population_fractions_and_identity'],
      'synthesis_scope_vi':synthesis['scope_vi'],'synthesis_review_note_vi':synthesis['review_note_vi'],
      'not_asserted_vi':'Không kiểm current42inputhashes/mutable indexes hoặc toàn bộ bundles/runtime; không scientific validation/efficacy/GPU proof.'}
    (directory/'archive_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    force_add=[f'research_tracking/runs/{RUN_ID}/'+n for n in ['execution.log']+[d for _,d in PAIRS if d.endswith('.log')]]
    (directory/'force_add_paths.txt').write_text('\n'.join(force_add)+'\n',encoding='utf-8')
# Sau closure chỉ đọc.
verified=verify_evidence_bundle(directory)
manifest=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
assert {p.name for p in directory.iterdir()}=={'manifest.json',*manifest['outputs_sha256']}
assert all(digest(directory/name)==value for name,value in manifest['outputs_sha256'].items())
print(json.dumps({'run':directory.relative_to(ROOT).as_posix(),'integrity':verified,'copied_files':len(inventory),'exact_output_sha_count':len(manifest['outputs_sha256']),'no_unlisted_files':True,'synthesis_selected_outputs_verified':len(selected_checks),'recorded_input_inventory':42,'manifest_sha256':digest(directory/'manifest.json'),'force_add_paths':force_add},ensure_ascii=False,indent=2))