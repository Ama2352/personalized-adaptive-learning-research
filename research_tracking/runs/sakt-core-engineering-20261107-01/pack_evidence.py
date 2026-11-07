"""Đóng bundle SAKT đã kiểm; không chạy lại model/tests hoặc thay scientific protocol."""
import hashlib
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path.cwd().resolve()
if Path(sys.prefix).resolve() != ROOT / '.venv':
    raise ValueError('Chỉ dùng project .venv từ repository root')
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle

RUN_ID = 'sakt-core-engineering-20261107-01'
BASE = 'artifacts/akt/local-tests/'
TRIAL01 = BASE + 'parallel-sakt-20261107-01/'
TRIAL02 = BASE + 'parallel-sakt-20261107-02/'
PAIRS = [
    ('src/knowledge_tracing/sakt/__init__.py', 'source_sakt_init.py'),
    ('src/knowledge_tracing/sakt/config.py', 'source_sakt_config.py'),
    ('src/knowledge_tracing/sakt/model.py', 'source_sakt_model.py'),
    ('src/knowledge_tracing/sakt/tensors.py', 'source_sakt_tensors.py'),
    ('tests/sakt/__init__.py', 'tests_sakt_init.py'),
    ('tests/sakt/test_core.py', 'tests_sakt_core.py'),
    ('research_tracking/reports/sakt_core_readiness_20261107.md', 'sakt_core_readiness_report.md'),
    (TRIAL02 + 'primary-source-provenance.json', 'primary_source_provenance.json'),
    (TRIAL02 + 'source-and-evidence-sha256.json', 'original_source_and_evidence_sha256.json'),
    (TRIAL01 + 'pytest.log', 'intermediate_35pass.log'),
    (TRIAL01 + 'pytest.xml', 'intermediate_35pass.xml'),
    (TRIAL02 + 'pytest.log', 'final_37pass.log'),
    (TRIAL02 + 'pytest.xml', 'final_37pass.xml'),
    ('src/knowledge_tracing/evidence.py', 'evidence_helper_source.py'),
    ('src/knowledge_tracing/shared_kt.py', 'shared_kt_source.py'),
    ('docs/thesis_recovery/02_RESEARCH_TRACEABILITY.md', 'input_research_traceability.md'),
    ('docs/thesis_recovery/18_SIMULATOR_KT_INTERFACE.md', 'input_simulator_kt_interface.md'),
    ('docs/REPOSITORY_MAP.md', 'input_REPOSITORY_MAP.md'),
    ('requirements-akt.lock.txt', 'requirements-akt.lock.txt'),
    ('artifacts/akt/preflight/gate2-current.json', 'gate15_pointer_snapshot.json'),
    ('artifacts/akt/preflight/gate2-evidence-20261107-parallel-portability-15.json', 'gate15_evidence_snapshot.json'),
]
KIT = ROOT / 'artifacts/akt/colab/akt-synthetic-20261107-v12.zip'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def junit_counts(path):
    suites = ET.parse(path).getroot().findall('testsuite')
    return {key: sum(int(suite.attrib.get(key, 0)) for suite in suites)
            for key in ('tests', 'failures', 'errors', 'skipped')}

# Inventory hoàn tất trước khi copy bất kỳ source/evidence artifact nào.
before = [{'source': source, 'archived_as': target, 'sha256_before_copy': digest(ROOT/source)}
          for source, target in PAIRS]
handoff = json.loads((ROOT/(TRIAL02 + 'source-and-evidence-sha256.json')).read_text(encoding='utf-8'))
original_rows = handoff['sources_and_inputs'] + handoff['outputs']
for item in original_rows:
    assert digest(ROOT/item['path']) == item['sha256'], item['path']
first = junit_counts(ROOT/(TRIAL01 + 'pytest.xml'))
final = junit_counts(ROOT/(TRIAL02 + 'pytest.xml'))
assert first == {'tests': 35, 'failures': 0, 'errors': 0, 'skipped': 0}
assert final == {'tests': 37, 'failures': 0, 'errors': 0, 'skipped': 0}
assert digest(ROOT/'research_tracking/reports/sakt_core_readiness_20261107.md') == '951ef1df8d19b0c9f79ae422a60b2c8825eb193ab6d11f8a5d3bde32809a79aa'
pointer = json.loads((ROOT/'artifacts/akt/preflight/gate2-current.json').read_text(encoding='utf-8'))
assert pointer['evidence_file'] == 'gate2-evidence-20261107-parallel-portability-15.json'
gate_path = ROOT/'artifacts/akt/preflight'/pointer['evidence_file']
assert digest(gate_path) == pointer['evidence_sha256']
gate = json.loads(gate_path.read_text(encoding='utf-8'))
assert gate['test_result'] == {'passed': 462, 'failed': 0, 'errors': 0, 'skipped': 0}
assert 'tests/sakt' not in gate['command'] and 'sakt' not in json.dumps(gate).lower()
kit_hash_before = digest(KIT)
with zipfile.ZipFile(KIT) as archive:
    kit_entries = archive.namelist()
    assert not any('/sakt/' in entry.replace('\\', '/') for entry in kit_entries)
    kit_manifest_bytes = archive.read('BUNDLE_MANIFEST.json')
kit_manifest_hash = hashlib.sha256(kit_manifest_bytes).hexdigest()
before.append({'source_archive': KIT.relative_to(ROOT).as_posix(),
               'archive_entry': 'BUNDLE_MANIFEST.json',
               'source_archive_sha256_before_copy': kit_hash_before,
               'archived_as': 'kit_v12_bundle_manifest_snapshot.json',
               'sha256_before_copy': kit_manifest_hash})

source_text = os.environ.get('KLTN_SAKT_ARCHIVE_SOURCE')
if source_text is None:
    source_text = Path(__file__).read_text(encoding='utf-8')
source_bytes = source_text.encode('utf-8')
force_add = [f'research_tracking/runs/{RUN_ID}/{name}' for name in
             ('execution.log', 'intermediate_35pass.log', 'final_37pass.log')]
metadata = {
    'kind': 'SAKT_PAPER_EQUATION_CORE_CPU_ENGINEERING_ARCHIVE',
    'schema_version': 1,
    'purpose_vi': 'Archive bằng chứng kỹ thuật SAKT đã chạy; không trainer hoặc baseline evaluation.',
    'scope_vi': 'Paper-equation single-block core, CPU synthetic, 0 optimizer steps; conventions pending.',
    'workload': {'new_test_executions': 0, 'new_training_steps': 0, 'archived_optimizer_steps': 0,
                 'gpu_cloud_calls': 0, 'raw_holdout_development_benchmark_queries': 0},
    'archived_junit': {'intermediate_trial01': first, 'final_trial02': final},
    'final_source_binding_vi': 'Snapshot source/tests bind final37pass; không có snapshot riêng source35pass trung gian.',
    'provenance': {'paper': 'https://arxiv.org/pdf/1907.06837v1',
                   'author_repository_commit': '98510c58e49fc2cd8ae05412d1f3bb1b9b5053a0',
                   'author_code_or_checkpoint_parity_claimed': False},
    'pending_vi': ['Final variant/head width/norm/dropout/context/position geometry',
                   'First-target scoring policy và common target denominator',
                   'Trainer/epoch selection/refit/export/resume/calibration',
                   'SequenceKTModel và simulator adapter/domain/checkpoint binding'],
    'gate15_and_kit12_include_sakt': False,
    'gate15_test_result': gate['test_result'],
    'kit_v12_sha256': kit_hash_before,
    'pack_source_sha256': hashlib.sha256(source_bytes).hexdigest(),
    'research_limits_vi': 'Attention không tự là prerequisite graph; random-weight engineering không là fitted baseline hoặc apples-to-apples evaluation.',
}
note = '''# SAKT core: bundle kiểm kỹ thuật CPU — 07/11/2026

Bundle này archive kết quả đã chạy, không thực thi thêm model/tests, optimizer, trainer, realdata, Holdout, Development benchmark, GPU hoặc cloud. Scope là paper-equation SAKT một block, CPU synthetic, 0 optimizer steps. Weights ngẫu nhiên chỉ dùng kiểm phần mềm; status completed không là complete baseline evaluation, research efficacy, hoặc model fitted.

Nguồn chính: arXiv:1907.06837v1 và author repo shalini1194/SAKT commit98510c58e49fc2cd8ae05412d1f3bb1b9b5053a0. Có khác biệt paper/code; implementation theo phương trình bài báo, không claim parity TensorFlow/checkpoint của tác giả. Không vendor/execute code tác giả. Attention trên history không tự là prerequisite graph.

Intermediate trial01 có35pass/25.58s; final trial02 có37pass/3.30s; cả hai0failure/error/skipped. Source/tests snapshot bind final37cases. Hai kiểm order/all-padding-backward được thêm sau trial01; không có snapshot riêng của source35cases. Giữ cả logs/XML nguyên bytes. Report/source snapshots còn có đường dẫn repository gốc; inventory ánh xạ source→archived_as. Bundle không tự giả làm full standalone runtime/kit.

Conventions explicit nhưng pending protocol: head width/capacity, norm/dropout, canonical rank position trong window (khác absolute left-padded TF slots), context/window budget và first-target policy. Cold score query-only hữu hạn/has_history=false chưa được chốt tính metric. API chỉ nhận current item và shifted prior_responses, chưa là SequenceKTModel hoặc simulator adapter. Trainer/epoch selection/refit/export/resume/calibration/domain/checkpoint binding chưa triển khai; không ghép vào AKT training loop hoặc claim apples-to-apples comparison.

Gate15 hiện ghi462pass cho tests/akt và tests/shared_kt; KHÔNG gồm tests/sakt. Kitv12 KHÔNG chứa package/tests SAKT. gate15_evidence_snapshot.json và kit_v12_bundle_manifest_snapshot.json cùng membership check chỉ chứng minh phạm vi packaging hiện hành, không nghiệm thu SAKT trên Colab/Linux/CUDA. Parent đang xử lý GPU evidence riêng; bundle này không mở rộng scope đó.

archive_copy_inventory_before.json được lập trước copy; archive_copy_inventory.json lưu SHA trước/sau và exact_match. Original handoff inventory16files được kiểm lại. manifest.json và record_evidence_run ghi source/input/output SHA; verify_evidence_bundle chạy sau closure chỉ đọc. Không sửa bundle sau đóng; parent cần review/index/map/commit riêng. Force-add chỉ3logs liệt kê trong force_add_paths.txt; không ghi Git/index/state/tasks trong gói này.
'''
with record_evidence_run(ROOT, RUN_ID, metadata=metadata,
                         sources=[ROOT/source for source, _ in PAIRS] + [KIT], note=note) as directory:
    (directory/'pack_evidence.py').write_bytes(source_bytes)
    (directory/'archive_copy_inventory_before.json').write_text(
        json.dumps(before, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    after = []
    for item in before:
        row = dict(item)
        if 'source' in item:
            source = ROOT/item['source']
            assert digest(source) == item['sha256_before_copy']
            payload = source.read_bytes()
        else:
            assert digest(KIT) == kit_hash_before
            with zipfile.ZipFile(KIT) as archive:
                payload = archive.read(item['archive_entry'])
            assert hashlib.sha256(payload).hexdigest() == item['sha256_before_copy']
        destination = directory/item['archived_as']
        destination.write_bytes(payload)
        row['sha256_after_copy'] = digest(destination)
        row['exact_match'] = row['sha256_after_copy'] == row['sha256_before_copy']
        assert row['exact_match']
        after.append(row)
    assert digest(KIT) == kit_hash_before
    for item in original_rows:
        assert digest(ROOT/item['path']) == item['sha256']
    (directory/'archive_copy_inventory.json').write_text(
        json.dumps(after, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (directory/'archive_validation.json').write_text(json.dumps({
        'scope_vi': 'Chỉ hash/XML/membership; không rerun tests/model/trainer.',
        'copied_files_or_entries': len(after),
        'all_precopy_postcopy_sha256_exact': True,
        'original_handoff_hashes_verified': len(original_rows),
        'intermediate_junit': first, 'final_junit': final,
        'final_source_snapshot_only_vi': 'Snapshot37cases, không gán ngược source35cases.',
        'kit_zip_unchanged': True,
        'new_optimizer_steps': 0,
    }, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (directory/'gate15_kit12_membership_check.json').write_text(json.dumps({
        'gate15_sha256': digest(gate_path),
        'gate15_pointer_sha256': digest(ROOT/'artifacts/akt/preflight/gate2-current.json'),
        'gate15_command': gate['command'], 'gate15_test_result': gate['test_result'],
        'gate15_sakt_included': False,
        'kit_v12_zip_sha256': kit_hash_before,
        'kit_v12_entry_count': len(kit_entries),
        'kit_v12_manifest_sha256': kit_manifest_hash,
        'kit_v12_sakt_entries': [],
        'scope_vi': 'Không suy SAKT đã được Gate15/kitv12/Colab nghiệm thu.',
    }, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (directory/'force_add_paths.txt').write_text('\n'.join(force_add)+'\n', encoding='utf-8')
# Bundle đã đóng: chỉ đọc.
verified = verify_evidence_bundle(directory)
manifest = json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
assert {p.name for p in directory.iterdir()} == {'manifest.json', *manifest['outputs_sha256']}
assert all(digest(directory/name) == expected for name, expected in manifest['outputs_sha256'].items())
print(json.dumps({'bundle':directory.relative_to(ROOT).as_posix(),
                  'verified':verified, 'exact_copy_files_or_entries':len(after),
                  'original_handoff_hashes_verified':len(original_rows),
                  'no_unlisted_files':True,
                  'manifest_sha256':digest(directory/'manifest.json'),
                  'force_add_paths':force_add}, ensure_ascii=False, indent=2))
