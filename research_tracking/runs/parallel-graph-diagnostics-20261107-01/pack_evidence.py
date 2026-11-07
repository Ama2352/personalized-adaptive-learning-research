"""Đóng gói evidence đã chạy; không chạy lại model/tests/simulator."""
import hashlib
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path.cwd().resolve()
if Path(sys.prefix).resolve() != ROOT / '.venv':
    raise ValueError('Chỉ dùng project .venv từ repository root')
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle

RUN_ID = 'parallel-graph-diagnostics-20261107-01'
G = 'artifacts/akt/local-tests/parallel-graph-20261107-prototype-'
F = 'artifacts/akt/local-tests/parallel-factorial-analysis-20261107-01/'
R = 'research_tracking/reports/'
PAIRS = [
    (G+'01/pytest.log', 'graph-trial01-collection-failure.log'),
    (G+'01/junit.xml', 'graph-trial01-collection-failure.xml'),
    (G+'02/pytest.log', 'graph-trial02-pass.log'),
    (G+'02/junit.xml', 'graph-trial02-pass.xml'),
    ('src/knowledge_tracing/graph_augmentation.py', 'graph_augmentation_source.py'),
    ('src/knowledge_tracing/graph_context.py', 'graph_context_source.py'),
    ('tests/shared_kt/test_graph_augmentation.py', 'test_graph_augmentation_source.py'),
    ('tests/shared_kt/test_graph_context.py', 'test_graph_context_source.py'),
    (R+'graph_gate_prototype_20261107.md', 'graph_gate_prototype_report.md'),
    (F+'analyze_factorial_uncertainty.py', 'analyze_factorial_uncertainty.py'),
    (F+'analyze_factorial_uncertainty_failed01.py', 'analyze_factorial_uncertainty_failed01.py'),
    (F+'analysis.log', 'factorial-trial01-metadata-key-failure.log'),
    (F+'analysis-02.log', 'factorial-trial02-pass.log'),
    (F+'reproduce.log', 'factorial-reproduce-pass.log'),
    (F+'reproduced.json', 'factorial_reproduced.json'),
    (F+'handoff_inventory.json', 'factorial_original_handoff_inventory.json'),
    (R+'factorial_pilot_uncertainty_20261107.md', 'factorial_uncertainty_report.md'),
    (R+'factorial_pilot_uncertainty_20261107.json', 'factorial_uncertainty.json'),
    ('research_tracking/runs/cpu-factorial-20261107-01/contrasts.json', 'input_factorial_contrasts.json'),
    ('research_tracking/runs/cpu-factorial-20261107-01/summary.json', 'input_factorial_summary.json'),
    (R+'cpu_pilot_followup_20261107.json', 'input_mechanism_followup.json'),
    (R+'rq12_evidence_synthesis_20261107.md', 'input_rq12_synthesis.md'),
    (R+'rq12_evidence_synthesis_20261107.json', 'input_rq12_synthesis.json'),
    (R+'cpu_pilots_20261107.md', 'input_cpu_pilots_report.md'),
    ('research_tracking/runs/cpu-factorial-20261107-01/README.md', 'input_factorial_run_README.md'),
    ('src/knowledge_tracing/evidence.py', 'evidence_helper_source.py'),
]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def counts(path):
    suites = ET.parse(path).getroot().findall('testsuite')
    return {key: sum(int(suite.attrib.get(key, 0)) for suite in suites)
            for key in ('tests', 'failures', 'errors', 'skipped')}

# Inventory có trước mọi copy. Không sửa/move/delete nguồn hoặc run cũ.
inventory = [{'source': source, 'archived_as': dest, 'sha256_before_copy': digest(ROOT/source)}
             for source, dest in PAIRS]
expected_graph = {
    'src/knowledge_tracing/graph_augmentation.py': '105aa918f1dc5d8fcfae22c9d8e7d2e13c1832b71d8b6a7ce8deed67d443ff08',
    'tests/shared_kt/test_graph_augmentation.py': '98d11d01cdf1e3e0412fa8f29c7d07b04be0db40e0975a0f49b33e1ace1cfc82',
    'src/knowledge_tracing/graph_context.py': '3db94ec43271d336898f61f81f12aeb569c6de52219eeed535af709711c97264',
}
for name, expected in expected_graph.items():
    assert digest(ROOT/name) == expected
original_handoff = json.loads((ROOT/(F+'handoff_inventory.json')).read_text(encoding='utf-8-sig'))
for item in original_handoff:
    assert digest(ROOT/item['path']) == item['sha256']
factorial = json.loads((ROOT/(R+'factorial_pilot_uncertainty_20261107.json')).read_text(encoding='utf-8'))
for item in factorial['input_inventory']:
    assert digest(ROOT/item['path']) == item['sha256']
assert digest(ROOT/(F+'reproduced.json')) == digest(ROOT/(R+'factorial_pilot_uncertainty_20261107.json'))
graph_failure = counts(ROOT/(G+'01/junit.xml'))
graph_pass = counts(ROOT/(G+'02/junit.xml'))
assert graph_failure == {'tests': 2, 'failures': 0, 'errors': 2, 'skipped': 0}
assert graph_pass == {'tests': 75, 'failures': 0, 'errors': 0, 'skipped': 0}
source_text = os.environ.get('KLTN_GRAPH_EVIDENCE_PACK_SOURCE')
if source_text is None:
    source_text = Path(__file__).read_text(encoding='utf-8')
source_bytes = source_text.encode('utf-8')
metadata = {
    'kind': 'MIXED_SOFTWARE_PROTOTYPE_AND_EXPLORATORY_AGGREGATE_ARCHIVE',
    'schema_version': 1,
    'purpose_vi': 'Giữ nguyên failure/pass và nguồn của hai gói song song; chỉ archive/verify, không thực thi nghiên cứu mới.',
    'evidence_classes': {
        'graph': 'Software-only isolated residual/gate contract, synthetic CPU forward/gradient; không trained CG-AKT/RQ3 result.',
        'factorial': 'EXPLORATORY POST-HOC uncertainty từ aggregates pilot đã lưu; không formal population CI/significance/final efficacy.'},
    'workload': {'new_test_executions': 0, 'new_simulator_events': 0, 'new_training_steps': 0,
                 'gpu_cloud_calls': 0, 'raw_or_holdout_queries': 0},
    'archived_graph_junit': {'trial01': graph_failure, 'trial02': graph_pass},
    'factorial': {'paired_seed_blocks': 10, 'profiles': ['PG','PY','PYH'], 'joint_block_draws': 10000,
                  'resampling_seed': 42, 'primary_reproduction_sha256': digest(ROOT/(F+'reproduced.json'))},
    'historical_trial_limits_vi': 'Graph trial01 source đúng thời điểm collection failure không có snapshot riêng; tests được thêm2cases trước trial02. Snapshot/hash graph trong bundle bind trial02, không gán ngược trial01.',
    'source_scope_vi': 'Snapshot targeted sources/tests và helper; không standalone full runtime/upstream kit. Native AKT integration, end-to-end leakage/cross-learner proof và system A0 selector ngoài scope.',
    'pack_source_sha256': hashlib.sha256(source_bytes).hexdigest(),
    'methodology_vi': 'Không adopt S04/S05 hoặc sửa confirmatory protocol; giữ3profile family, không chọn seeds/claim equivalence PG.',
}
note = '''# Archive graph prototype và factorial uncertainty — 07/11/2026

Hai loại bằng chứng riêng: graph là kiểm phần mềm synthetic CPU, còn factorial là exploratory post-hoc aggregate analysis. Đây là run đóng gói bằng chứng đã chạy, không thêm model fit, simulator event, GPU/cloud hoặc query raw/Holdout. Không coi status completed là trained CG-AKT/RQ3 hoặc kết luận efficacy.

Graph trial01 giữ nguyên collection failure vì thiếu PYTHONPATH=src; trial02 đạt75cases(42augmentation+33context), không fail/error/skip. Snapshot graph source/tests bind trial02 theo SHA đã handoff. Không có snapshot test source đúng thời điểm trial01; không tuyên bố trial01 dùng cùng source42cases. Graph kernel chưa chọn f/gate architecture, chưa hook native latent/logit, và caller-supplied tensors/session histories vẫn cần end-to-end provenance/isolation review.

Factorial giữ failure01 sai tên metadata key và source lỗi, script sửa, pass02, reproduction và output giống bytes.10seeds/profile,3profiles,10.000joint seed-block draws với seed42. Envelope empirical resampling không là formal population95%CI; không pvalues/significance/final efficacy. PG deficit0/2400 là mechanism không exposed, không proof of equivalence. Inputs chỉ contrasts/summary/coverage cùng báo cáo đã lưu, không reopen raw4cell outcomes/traces; pairing4cells kế thừa từ aggregates/hồ sơ nguồn.

archive_copy_inventory.json ghi SHA trước copy và đối chiếu exact sau copy; manifest ghi source/input và mọi output SHA. Bảy input snapshots giúp truy vết aggregates. Script factorial snapshot vẫn dùng layout repository gốc; bảng source→archived_as trong inventory chỉ rõ mapping, bundle không tự giả làm full standalone runtime. Graph/factorial reports trong bundle là snapshots nguyên bytes, có thể còn đường dẫn local/source lịch sử.

pack_evidence.py là chính mã đóng gói dùng helper record_evidence_run/verify_evidence_bundle hiện có; không sửa framework. Helper tự ghi manifest/README/execution.log và closure hashes. Không sửa bundle sau closure; verify chỉ đọc. *.log cần force-add theo force_add_paths.txt; không sửa .gitattributes để né whitespace ở traceback gốc. Không ghi Git/index/state/tasks trong gói này.
'''
with record_evidence_run(ROOT, RUN_ID, metadata=metadata,
                         sources=[ROOT/source for source, _ in PAIRS], note=note) as directory:
    (directory/'pack_evidence.py').write_bytes(source_bytes)
    for item in inventory:
        source = ROOT/item['source']
        assert digest(source) == item['sha256_before_copy']
        target = directory/item['archived_as']
        target.write_bytes(source.read_bytes())
        item['sha256_after_copy'] = digest(target)
        item['exact_match'] = item['sha256_after_copy'] == item['sha256_before_copy']
        assert item['exact_match']
    (directory/'archive_copy_inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (directory/'archive_validation.json').write_text(json.dumps({
        'source_copy_files': len(inventory), 'all_copy_sha256_exact': True,
        'factorial_original_handoff_hashes_verified': len(original_handoff),
        'factorial_input_hashes_verified': len(factorial['input_inventory']),
        'factorial_primary_reproduced_identical': True,
        'graph_pass_source_hashes_verified': expected_graph,
        'graph_failure_junit': graph_failure, 'graph_pass_junit': graph_pass,
        'validation_scope_vi': 'Chỉ hash/XML/metadata, không rerun tests/model/analysis.'},
        ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    force_add = [f'research_tracking/runs/{RUN_ID}/'+name for name in
                 ['execution.log']+[dest for _, dest in PAIRS if dest.endswith('.log')]]
    (directory/'force_add_paths.txt').write_text('\n'.join(force_add)+'\n', encoding='utf-8')
# Từ đây chỉ đọc; không thêm log/verification artifact sau closure.
verified = verify_evidence_bundle(directory)
manifest = json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
actual_files = {path.name for path in directory.iterdir() if path.is_file()}
assert actual_files == {'manifest.json', *manifest['outputs_sha256']}
assert all(digest(directory/name) == expected for name, expected in manifest['outputs_sha256'].items())
print(json.dumps({'run': directory.relative_to(ROOT).as_posix(), 'integrity': verified,
                  'exact_output_sha_count': len(manifest['outputs_sha256']),
                  'no_unlisted_files': True, 'manifest_sha256': digest(directory/'manifest.json'),
                  'force_add_paths': force_add}, ensure_ascii=False, indent=2))