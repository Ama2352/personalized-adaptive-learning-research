"""Đóng bằng chứng witness120, giữ failure và nguồn, chưa công bố báo cáo GVHD."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN = 'rq1-observer03-cached-truth-20261109-01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


packet = read(PREP / 'observer03_cached_truth02_packet.json')
outer = PREP / packet['phases']['cached']['owned'] / 'final.json'
assert sha(outer) == '32042e63144f36cec7acff18e30b62657fe528a4bbf137de608227cf0a25cebe'
accepted = read(outer)
assert accepted['status'] == 'ACCEPTED_OBSERVER03_CACHED120_LATENT_WITNESS'
assert accepted['receipt']['job_active_after_cleanup'] == 0 and not accepted['errors']
assert accepted['source_input_before'] == accepted['source_input_after']
summary = read(PREP / packet['phases']['cached']['child'] / 'summary.json')
assert summary['native_M_by_latent'] == summary['theta_gate_by_latent'] == dict.fromkeys(('00', '01', '10', '11'), 0) | {'01': 120}
crosscheck = read(PREP / 'observer03_truth120_independent_crosscheck01.json')
assert crosscheck['first_visit_analysis']['observed_concepts'] == crosscheck['first_visit_analysis']['latent_positive_first_visits'] == 22

files = {}
for number in ('01', '02'):
    prior = read(PREP / f'observer03_cached_truth{number}_packet.json')
    for phase, config in prior['phases'].items():
        for kind in ('child', 'owned'):
            folder = PREP / config[kind]
            for path in folder.iterdir():
                assert path.is_file() and not path.is_symlink()
                alias = f'{phase}{number}_{kind}__{path.name}'
                assert alias not in files
                files[alias] = path
names = (
    'analyze_observer03_cached_truth01.py', 'test_observer03_cached_truth01.py',
    'run_observer03_cached_truth01.py', 'run_observer03_cached_truth02.py',
    'observer03_cached_truth01_packet.json', 'observer03_cached_truth02_packet.json',
    'RQ1_OBSERVER03_CACHED_TRUTH_CONTRACT01.md',
    'RQ1_CACHED_NATIVE_TRUTH_JOIN_FEASIBILITY01.md',
    'ROOT_OBSERVER03_TRUTH_SOURCE_REVIEW01.md',
    'OBSERVER03_CACHED_TRUTH_SOURCE_HANDOFF01.md',
    'OBSERVER03_CACHED_TRUTH_INDEPENDENT_REVIEW01.md',
    'OBSERVER03_MONITOR_RESOURCE_ERRATUM01.md',
    'OBSERVER03_MONITOR_RESOURCE_REVIEW02.md',
    'OBSERVER03_CACHED120_SELECTION_INTERPRETATION_REVIEW01.md',
    'RQ1_OBSERVER03_TRUTH_WITNESS_REPORT_DRAFT01.md',
    'probe_observer03_monitor_type_cache01.py',
    'observer03_monitor_type_cache01_result.json',
    'prepare_and_probe_observer03_monitor02.py',
    'observer03_monitor_type_cache02_result.json',
    'crosscheck_observer03_truth120_root01.py',
    'crosscheck_observer03_truth120_before_bom_fix01.py',
    'observer03_truth120_independent_crosscheck01.json',
    'analyze_rq2_cached_mechanism01.py',
)
for name in names:
    files[name] = PREP / name
files['windows_owned_worker.py'] = ROOT / 'scripts/research/windows_owned_worker.py'
files['archive_builder.py'] = Path(__file__).resolve()
inventory = [dict(alias=name, source=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size,
                  sha256=sha(path)) for name, path in files.items()]
inventory_path = PREP / 'observer03_truth_witness_copy_inventory_before01.json'
assert not inventory_path.exists()
inventory_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
references = {**packet['source_pins'], **{name: row['sha256'] for name, row in packet['inputs'].items()}}
assert all(sha(ROOT / name) == digest for name, digest in references.items())

sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle

note = '''# RQ1 — đối chiếu trên120 câu do policy chọn

Đã ghép đúng120readouts của một history cũ21000/PG/S=Poff/Loff với cacheCPU09.
Controller vẫn giữ đồ thị tiên quyết. Cả120native theta dưới1250 trong khi tiêu chí
latent của queried concept đều đạt. Số lượt theta đạt để xét thêm pi bằng0.
22concept được phục vụ đều latent-positive từ first visit. Đây là mẫu on-policy,
không đại diện độ chính xác toàn bộ state, không graph comparison hoặc learning gain.
First-visit là kiểm cơ chế hậu nghiệm, không independent confirmation.

Gói giữ pure8 ở hai phiên bản, cached01 bị dừng do RAM bộ đo, cached02 accepted,
probe3calls phát hiện ctypes type retention và probe02 xác nhận cache ổn định.
Analyzer/tests không đổi khi sửa bộ đo, caps giữ nguyên. Crosscheck độc lập đã đạt,
giữ source trước sửa CSV BOM. Dataset và file lịch sử không đổi.

Chưa có model/world/RNG khoa học mới. Các raw inputs lớn tham chiếu qua SHA,
không nhân bản gzip. Bản nháp kỹ thuật giữ trong gói. Báo cáo canonical và hai file
GVHD còn cần xuất bản ở batch nối tiếp, chưa được bundle này coi là đã cập nhật.
'''
sources = {*(ROOT / row['source'] for row in inventory), *(ROOT / name for name in references), inventory_path}
with record_evidence_run(ROOT, RUN, sources=sorted(sources), note=note,
        metadata=dict(kind='cached_on_policy_native_mastery_latent_witness', queried_rows=120,
                      histories=1, observed_concepts=22, new_independent_N=0,
                      new_model_world_calls=0, full_RQDIAG23_complete=False,
                      human_report_publication_pending=True)) as output:
    for row in inventory:
        source = ROOT / row['source']
        assert sha(source) == row['sha256']
        (output / row['alias']).write_bytes(source.read_bytes())
        assert sha(source) == sha(output / row['alias']) == row['sha256']
    (output / 'copy_inventory.json').write_bytes(inventory_path.read_bytes())
    (output / 'reference_sources.json').write_text(json.dumps(references, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    failure = dict(kind='INDEPENDENT_CROSSCHECK_METADATA_ENCODING_FAILURE',
                   error='KeyError question_id vì CSV có UTF8 BOM, dừng trước đọc gzip.',
                   correction='Chỉ đổi encoding reader sang utf-8-sig; dữ liệu gốc không đổi.',
                   before_source='crosscheck_observer03_truth120_before_bom_fix01.py',
                   after_source='crosscheck_observer03_truth120_root01.py')
    (output / 'crosscheck_bom_failure_note.json').write_text(json.dumps(failure, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
result = verify_evidence_bundle(ROOT / 'research_tracking/runs' / RUN)
print(json.dumps(dict(status='CLOSED_WITNESS_EVIDENCE_PUBLICATION_PENDING', outputs=result['artifacts'],
                     manifest_sha256=sha(ROOT / 'research_tracking/runs' / RUN / 'manifest.json'))))
