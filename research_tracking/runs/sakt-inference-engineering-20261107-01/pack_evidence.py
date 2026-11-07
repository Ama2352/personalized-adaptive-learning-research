"""Đóng hồ sơ SAKT inference đã kiểm; không chạy lại tests hoặc model."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


ROOT = Path.cwd().resolve()
RUN_ID = 'sakt-inference-engineering-20261107-01'
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    if Path(sys.executable).resolve() != (ROOT / '.venv/Scripts/python.exe').resolve():
        raise RuntimeError('Chỉ dùng .venv repository')
    owned = [
        ('src/knowledge_tracing/sakt/adapter.py', 'final_adapter.py'),
        ('tests/sakt/test_adapter.py', 'final_test_adapter.py'),
        ('research_tracking/reports/sakt_adapter_readiness_20261107.md', 'sakt_adapter_readiness_report.md'),
    ]
    dependencies = [
        ('src/knowledge_tracing/sakt/__init__.py', 'source_sakt_init.py'),
        ('src/knowledge_tracing/sakt/config.py', 'source_sakt_config.py'),
        ('src/knowledge_tracing/sakt/model.py', 'source_sakt_model.py'),
        ('src/knowledge_tracing/sakt/tensors.py', 'source_sakt_tensors.py'),
        ('tests/sakt/__init__.py', 'tests_sakt_init.py'),
        ('tests/sakt/test_core.py', 'tests_sakt_core.py'),
        ('src/knowledge_tracing/shared_kt.py', 'shared_kt_source.py'),
        ('src/knowledge_tracing/simulator_bridge.py', 'simulator_bridge_source.py'),
        ('src/knowledge_tracing/evidence.py', 'evidence_helper_source.py'),
        ('research_tracking/runs/sakt-core-engineering-20261107-01/manifest.json', 'prior_core_manifest.json'),
        ('research_tracking/runs/sakt-core-engineering-20261107-01/primary_source_provenance.json', 'primary_source_provenance.json'),
    ]
    copies = owned + dependencies + [(str(Path(__file__).resolve().relative_to(ROOT)), 'pack_evidence.py')]
    trials = []
    checkpoint_inventory = []
    for ordinal, expected in [('01', 82), ('02', 87)]:
        relative = Path('artifacts/akt/local-tests') / ('parallel-sakt-adapter-20261107-' + ordinal)
        base = ROOT / relative
        for name in ('adapter_source.py', 'test_adapter_source.py', 'pytest.log', 'pytest.xml',
                     'run.json', 'source_before.json', 'source_after.json'):
            copies.append(((relative / name).as_posix(), 'trial' + ordinal + '_' + name))
        xml = ET.parse(base / 'pytest.xml').getroot()
        suites = xml.findall('.//testsuite')
        cases = xml.findall('.//testcase')
        counts = Counter(case.attrib['classname'] for case in cases)
        if (len(cases) != expected or not suites
                or any(int(suite.attrib[key]) for suite in suites for key in ('failures', 'errors', 'skipped'))):
            raise ValueError('Unexpected archived test result')
        before = json.loads((base / 'source_before.json').read_text(encoding='utf-8'))
        after = json.loads((base / 'source_after.json').read_text(encoding='utf-8'))
        if before != after:
            raise ValueError('Source changed during original targeted tests')
        for path, digest in before.items():
            if path not in ('src/knowledge_tracing/sakt/adapter.py', 'tests/sakt/test_adapter.py') and sha(ROOT / path) != digest:
                raise ValueError('Frozen dependency changed: ' + path)
        if (sha(base / 'adapter_source.py') != before['src/knowledge_tracing/sakt/adapter.py']
                or sha(base / 'test_adapter_source.py') != before['tests/sakt/test_adapter.py']):
            raise ValueError('Original source snapshot identity mismatch')
        run = json.loads((base / 'run.json').read_text(encoding='utf-8'))
        if run['exit_code'] != 0 or not run['sources_unchanged'] or run['elapsed_seconds'] > 120:
            raise ValueError('Original execution scope mismatch')
        trials.append({'run_id': relative.name, 'testcases': expected, 'by_class': dict(counts),
                       'junit_zero_failure_error_skip': True, 'run': run,
                       'original_sources_sha256': before,
                       'adapter_snapshot_equals_final': sha(base / 'adapter_source.py') == sha(ROOT / owned[0][0]),
                       'test_snapshot_equals_final': sha(base / 'test_adapter_source.py') == sha(ROOT / owned[1][0])})
        for path in sorted((base / 'tmp').rglob('*.pt')):
            checkpoint_inventory.append({'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size,
                'sha256': sha(path), 'role': 'random_weight_or_intentionally_invalid_unit_test_fixture',
                'selected_fitted_checkpoint': False, 'copied_into_bundle': False})
    if (trials[0]['by_class'].get('tests.sakt.test_adapter') != 45
            or trials[1]['by_class'].get('tests.sakt.test_adapter') != 50
            or not trials[1]['adapter_snapshot_equals_final'] or not trials[1]['test_snapshot_equals_final']):
        raise ValueError('Final source/test coverage binding mismatch')
    if len(checkpoint_inventory) != 95:
        raise ValueError('Unexpected fixture checkpoint inventory count')
    plans = [{'source': source, 'archived_as': target, 'bytes': (ROOT / source).stat().st_size,
              'pre_copy_sha256': sha(ROOT / source)} for source, target in copies]
    sources = list(dict.fromkeys([ROOT / item['source'] for item in plans]
                                + [ROOT / item['path'] for item in checkpoint_inventory]))
    note = """# SAKT frozen inference: kiểm kỹ thuật CPU — 07/11/2026

Archive hai targeted trials đã chạy, không thực thi thêm tests/model/trainer,
optimizer, GPU, realdata/Holdout, cloud hoặc Git mutation. Trial01 có82pass
(37core+45adapter), trial02 có87pass (37core+50adapter); cả hai khôngfail/error/skip,
dưới120s. Exact adapter/test snapshots và run/log/JUnit được giữ riêng từng lượt,
không gán final test source cho trial01. Final source/tests/report và dependencies
nhỏ được snapshot; không sửa shared/core/config/tensors/__init__ trong gói.

Random weights chỉ là engineering fixtures. Own typed scores có provenance,
không OnlineScore fitted. fit và complete OnlineSession backend từ chối vì chưa
trainer/selected-fit provenance. Caller phải khai báo cold policy/geometry;
không adoption S04/S05/mastery/calibration hoặc nghiệm thu fitted baseline.
Metadata equality/hash không xác thực training/split hoặc origin của từng input.

checkpoint_inventory.json giữ đường dẫn/size/SHA của95 .pt random/negative-control
fixtures, không copy checkpoint binaries. Không checkpoint nào là selected fitted
model. Bản kê không giả mọi negative fixture là loadable/finite. Không xóa nguồn
tmp trong lúc còn cần truy vết/resume. Bundle không là standalone full runtime.

archive_copy_inventory_before.json được lập trước copy; archive_copy_inventory.json
ghi source pre/post và destination SHA. Manifest ghi sources/outputs. pack_evidence.py
là đúng mã đóng gói được chạy; source→archived_as cho phép tra các đường dẫn repo
còn nằm trong script/report snapshots. Tái chạy tests cần project .venv/dependencies
và output ID mới theo run.json; không chạy lại packer vào bundle đã đóng.

Gate16 native AKT/shared đang được xử lý riêng, không dùng nó nghiệm thu SAKT.
Actual CUDA của AKT không nghiệm thu adapter CPU mới; không Gate4/full training/RQ
efficacy từ87cases. Không thay indexes/state/tasks/Git. Sau closure chỉ gọi helper
verify_evidence_bundle để kiểm output SHA, không ghi thêm output vào bundle.
"""
    with record_evidence_run(ROOT, RUN_ID, metadata={
        'kind': 'SAKT_FROZEN_INFERENCE_CPU_ENGINEERING_ARCHIVE',
        'purpose_vi': 'Archive hash-bound random-weight inference adapter, chưa trainer/fitted OnlineSession backend.',
        'archived_trial_counts': {'trial01': 82, 'trial02': 87, 'core_final': 37, 'adapter_final': 50},
        'new_test_executions': 0, 'new_model_steps': 0, 'archived_optimizer_steps': 0,
        'gpu_cloud_calls': 0, 'raw_realdata_or_holdout_queries': 0,
        'fitted_online_backend_complete': False, 's04_s05_adopted': False,
        'weight_roles': ['random_fixture', 'unverified_state'],
        'gate16_includes_this_sakt_acceptance': False,
        'scope_vi': 'CPU FP32; own typed scores; strict raw state_dict SHA/config/vocab/domain/spec, không fitted efficacy.',
    }, sources=sources, note=note) as directory:
        write(directory / 'archive_copy_inventory_before.json', {'copies': plans})
        observed = []
        for item in plans:
            source, target = ROOT / item['source'], directory / item['archived_as']
            target.write_bytes(source.read_bytes())
            record = {**item, 'source_post_sha256': sha(source), 'destination_sha256': sha(target)}
            record['all_equal'] = record['pre_copy_sha256'] == record['source_post_sha256'] == record['destination_sha256']
            if not record['all_equal']:
                raise ValueError('Archive copy SHA mismatch')
            observed.append(record)
        write(directory / 'archive_copy_inventory.json', {'copies': observed, 'all_equal': True})
        write(directory / 'checkpoint_inventory.json', {'checkpoints': checkpoint_inventory,
            'files': len(checkpoint_inventory), 'bytes': sum(item['bytes'] for item in checkpoint_inventory),
            'copied_binaries': 0, 'scope_vi': 'Hash inventory random/invalid test fixtures; không fitted/checkpoint efficacy.'})
        write(directory / 'archive_validation.json', {'status': 'passed_archive_validation', 'trials': trials,
            'copy_count': len(observed), 'all_copy_sha_match': True,
            'checkpoint_inventory_files': len(checkpoint_inventory), 'checkpoint_binaries_copied': 0,
            'new_test_or_model_executions': 0,
            'limitations_vi': ['Own typed provenance scores, không fitted OnlineScore hoặc complete bridge.',
                               'Caller cold/window conventions chưa là frozen research protocol.',
                               'CPU synthetic; không CUDA/Gate16/SAKT baseline hoặc efficacy acceptance.']})
        (directory / 'validation.log').write_text(
            'PASS: archived82/87 cases,37core+45/50adapter; JUnit zero failures/errors/skips.\n'
            'PASS: final source matches trial02; unchanged frozen dependencies; all pre/copy/post SHA equal.\n'
            'PASS: checkpoint binaries inventory only;0new model/test executions; no fitted efficacy.\n', encoding='utf-8')
        ignored = subprocess.run(['git', 'check-ignore', '--',
            *[str(path.relative_to(ROOT)) for path in directory.iterdir()]], cwd=ROOT,
            capture_output=True, text=True, check=False).stdout
        (directory / 'force_add_paths.txt').write_text(ignored, encoding='utf-8')
    result = verify_evidence_bundle(ROOT / 'research_tracking/runs' / RUN_ID)
    print(json.dumps({'run_id': RUN_ID, **result, 'copied_files': len(plans),
                      'checkpoint_inventory_files': len(checkpoint_inventory)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
