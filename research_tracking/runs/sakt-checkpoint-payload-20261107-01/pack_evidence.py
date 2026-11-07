"""Archive P2 checkpoint payload regression; không thực thi model/tests mới."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path.cwd().resolve()
RUN_ID = 'sakt-checkpoint-payload-20261107-01'
PREVIOUS = 'research_tracking/runs/sakt-inference-engineering-20261107-01'
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    if Path(sys.executable).resolve() != (ROOT / '.venv/Scripts/python.exe').resolve():
        raise RuntimeError('Chỉ .venv repository được dùng')
    previous_integrity = verify_evidence_bundle(ROOT / PREVIOUS)
    previous_manifest_sha = sha(ROOT / PREVIOUS / 'manifest.json')
    copies = [
        ('src/knowledge_tracing/sakt/adapter.py', 'final_adapter.py'),
        ('tests/sakt/test_adapter.py', 'final_test_adapter.py'),
        ('research_tracking/reports/sakt_adapter_readiness_20261107.md', 'sakt_adapter_readiness_with_P2_addendum.md'),
        ('src/knowledge_tracing/sakt/config.py', 'source_sakt_config.py'),
        ('src/knowledge_tracing/sakt/model.py', 'source_sakt_model.py'),
        ('src/knowledge_tracing/sakt/tensors.py', 'source_sakt_tensors.py'),
        ('src/knowledge_tracing/sakt/__init__.py', 'source_sakt_init.py'),
        ('tests/sakt/test_core.py', 'tests_sakt_core.py'),
        ('src/knowledge_tracing/shared_kt.py', 'shared_kt_source.py'),
        ('src/knowledge_tracing/simulator_bridge.py', 'simulator_bridge_source.py'),
        ('src/knowledge_tracing/evidence.py', 'evidence_helper_source.py'),
        (PREVIOUS + '/manifest.json', 'previous_37output_manifest.json'),
        (PREVIOUS + '/README.md', 'previous_archive_README.md'),
        (PREVIOUS + '/primary_source_provenance.json', 'primary_source_provenance.json'),
        (str(Path(__file__).resolve().relative_to(ROOT)), 'pack_evidence.py'),
    ]
    trials, checkpoints = [], []
    for suffix, expected_tests, expected_failures in [('01-before', 2, 2), ('02-after', 89, 0)]:
        relative = Path('artifacts/akt/local-tests') / ('parallel-sakt-payload-20261107-' + suffix)
        base = ROOT / relative
        for name in ('adapter_source.py', 'test_adapter_source.py', 'pytest.log', 'pytest.xml',
                     'run.json', 'source_before.json', 'source_after.json'):
            copies.append(((relative / name).as_posix(), suffix + '_' + name))
        xml = ET.parse(base / 'pytest.xml').getroot()
        cases = xml.findall('.//testcase')
        failures = [case for case in cases if case.find('failure') is not None]
        errors = [case for case in cases if case.find('error') is not None]
        skipped = [case for case in cases if case.find('skipped') is not None]
        if len(cases) != expected_tests or len(failures) != expected_failures or errors or skipped:
            raise ValueError('Unexpected regression result')
        before = json.loads((base / 'source_before.json').read_text(encoding='utf-8'))
        after = json.loads((base / 'source_after.json').read_text(encoding='utf-8'))
        if before != after:
            raise ValueError('Original test sources changed during execution')
        if (sha(base / 'adapter_source.py') != before['src/knowledge_tracing/sakt/adapter.py']
                or sha(base / 'test_adapter_source.py') != before['tests/sakt/test_adapter.py']):
            raise ValueError('Original source snapshots mismatch')
        for path, digest in before.items():
            if path not in ('src/knowledge_tracing/sakt/adapter.py', 'tests/sakt/test_adapter.py') and sha(ROOT / path) != digest:
                raise ValueError('Frozen dependency changed')
        run = json.loads((base / 'run.json').read_text(encoding='utf-8'))
        if (run['exit_code'] != (1 if expected_failures else 0)
                or not run['sources_unchanged'] or run['elapsed_seconds'] > 120
                or run['optimizer_steps'] != 0 or run['GPU_calls'] != 0):
            raise ValueError('Original execution scope mismatch')
        trials.append({'run_id': relative.name, 'tests': len(cases), 'failures': len(failures),
            'errors': 0, 'skipped': 0, 'by_class': dict(Counter(c.attrib['classname'] for c in cases)),
            'run': run, 'source_sha256': before,
            'failure_messages': [{'test': c.attrib['name'], 'message': c.find('failure').attrib.get('message', '')}
                                 for c in failures]})
        for path in sorted((base / 'tmp').rglob('*.pt')):
            checkpoints.append({'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size,
                'sha256': sha(path), 'role': 'random_or_intentionally_invalid_loader_fixture',
                'selected_fitted': False, 'copied_binary': False})
    if (trials[1]['by_class'] != {'tests.sakt.test_adapter': 52, 'tests.sakt.test_core': 37}
            or len(checkpoints) != 54):
        raise ValueError('Final coverage or checkpoint inventory mismatch')
    final = ROOT / 'artifacts/akt/local-tests/parallel-sakt-payload-20261107-02-after'
    if (sha(final / 'adapter_source.py') != sha(ROOT / copies[0][0])
            or sha(final / 'test_adapter_source.py') != sha(ROOT / copies[1][0])):
        raise ValueError('Final source no longer matches tested source')
    plans = [{'source': source, 'archived_as': archived, 'bytes': (ROOT / source).stat().st_size,
              'pre_copy_sha256': sha(ROOT / source)} for source, archived in copies]
    sources = list(dict.fromkeys([ROOT / p['source'] for p in plans] + [ROOT / p['path'] for p in checkpoints]))
    note = """# P2 SAKT checkpoint: bind đúng payload deserialize — 08/11/2026

Run ID giữ ngày07/11 của batch. Đây là follow-up engineering, không sửa bundle
sakt-inference-engineering-20261107-01 (37outputs/source87snapshot). Review trước
chỉ static đã phát hiện stat/hashpath/loadpath/posthash có thể đọc A→B→A.

Giữ2regressions fail-before/7,88s và full89pass-after/7,33s (37core+52adapter),
exact source/test snapshots/logs/XML/run/pre-postSHA của từng attempt. Không
collection errors/skips; mọi invocation dưới120s,0optimizer/GPU/realdata/cloud.
Archive không chạy lại tests/model. Final adapter chỉ đổi bounded singlepayload
maxbytes+1, SHA payload, torch.load(BytesIO(payload),weights_only=True,map_location=cpu).
Bounded postpath guard là consistency check, không security basis cho A→B→A.

Rawstate_dict/config/vocab/domain/frozen conventions giữ; random/unverified scores
không thành fitted/OnlineSession/trainer/calibration. Byte cap là serialized bytes,
không peakRAM/decompression attestation. Negative-control fixtures không mặc nhiên
loadable/finite.54 .pt files chỉ inventory/hash, không copy binaries.

Platform agent đã review read-only patch/tests/logs, không rerun/edit và không
còn blocking issue trong phạm vi P2. reviewer_note.json ghi đúng giới hạn đó;
không là scientific approval/Gate16/SAKT efficacy. Core/shared/AKT không sửa.

archive_copy_inventory_before.json lập trước copy; archive_copy_inventory.json
đối chiếu source pre/post/destination. Previous37output manifest+README được
snapshot và verify output-only trước/sau closure. Parent cần review/index/Git
riêng; không sửa shared indexes/state/tasks hoặc chạy paid/fullCV trong gói.
Report/script còn dùng repository paths gốc; bundle không là standalone runtime.
Không thêm/sửa outputs sau closure; helper verify chỉ đọc SHA outputs.
"""
    with record_evidence_run(ROOT, RUN_ID, metadata={
        'kind': 'SAKT_CHECKPOINT_SINGLE_PAYLOAD_CPU_REGRESSION_ARCHIVE',
        'previous_run_id': Path(PREVIOUS).name, 'previous_manifest_sha256': previous_manifest_sha,
        'previous_run_outputs': previous_integrity['artifacts'],
        'regression_before': {'tests': 2, 'failures': 2, 'errors': 0, 'skipped': 0},
        'regression_after': {'tests': 89, 'failures': 0, 'errors': 0, 'skipped': 0},
        'new_test_runs_in_archive': 0, 'optimizer_steps': 0, 'gpu_cloud_calls': 0,
        'realdata_holdout_queries': 0, 'fitted_online_backend_complete': False,
        'scope_vi': 'Loader single bounded payload identity, không trainer/Gate16/efficacy hoặc scientific protocol adoption.',
    }, sources=sources, note=note) as directory:
        save(directory / 'archive_copy_inventory_before.json', {'copies': plans})
        observed = []
        for record in plans:
            source, destination = ROOT / record['source'], directory / record['archived_as']
            destination.write_bytes(source.read_bytes())
            value = {**record, 'source_post_sha256': sha(source), 'destination_sha256': sha(destination)}
            value['all_equal'] = value['pre_copy_sha256'] == value['source_post_sha256'] == value['destination_sha256']
            if not value['all_equal']:
                raise ValueError('Copy integrity mismatch')
            observed.append(value)
        save(directory / 'archive_copy_inventory.json', {'copies': observed, 'all_equal': True})
        save(directory / 'checkpoint_inventory.json', {'files': len(checkpoints), 'checkpoints': checkpoints,
            'bytes': sum(c['bytes'] for c in checkpoints), 'copied_binaries': 0})
        save(directory / 'reviewer_note.json', {'reviewer_task': '/root/platform_fixture_compat',
            'review_mode': 'read_only_static_source_tests_and_existing_logs', 'review_verdict': 'PASS_WITHIN_P2_SCOPE',
            'rerun_or_source_edits_by_reviewer': False,
            'findings_vi': 'Kiểm actual payload length/hash bounded rồi deserialize BytesIO ngăn load unhashedB; bounded postpath không đổi payload; strict CPU FP32/state_dict/identity/frozen guards giữ.',
            'limit_vi': 'Serialized byte cap không là peakRAM/decompression attestation; không efficacy/protocol approval.'})
        save(directory / 'archive_validation.json', {'status': 'passed_archive_validation', 'trials': trials,
            'copies_verified': len(observed), 'all_copy_sha_match': True, 'checkpoints_inventory_only': 54,
            'previous_bundle_integrity': previous_integrity, 'previous_manifest_sha256': previous_manifest_sha,
            'new_test_model_runs': 0, 'fitted_or_gate16_acceptance': False})
        (directory / 'validation.log').write_text(
            'PASS archive:2fail-before/89pass-after; unchanged-source during both executions.\n'
            'PASS pre/copy/post SHA, frozen dependencies,54checkpoint fixtures inventory only.\n'
            'PASS prior37output bundle still verified;0new tests/model/training/GPU in archive.\n', encoding='utf-8')
        ignored = subprocess.run(['git', 'check-ignore', '--', *[str(p.relative_to(ROOT)) for p in directory.iterdir()]],
                                 cwd=ROOT, text=True, capture_output=True, check=False).stdout
        (directory / 'force_add_paths.txt').write_text(ignored, encoding='utf-8')
    verified = verify_evidence_bundle(ROOT / 'research_tracking/runs' / RUN_ID)
    old = verify_evidence_bundle(ROOT / PREVIOUS)
    if sha(ROOT / PREVIOUS / 'manifest.json') != previous_manifest_sha:
        raise ValueError('Previous immutable bundle changed')
    print(json.dumps({'run_id': RUN_ID, **verified, 'previous_bundle': old,
                      'copied_files': len(plans), 'checkpoint_inventory_files': len(checkpoints)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
