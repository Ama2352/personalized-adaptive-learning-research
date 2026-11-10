"""Kiểm độc lập archive đã tải về, không import Torch hoặc chạy huấn luyện."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import runpy
import sys
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NATIVE = ROOT/'experiments/akt/results/colab-isolated-cpu-20261110-01'
sys.path.insert(0, str(ROOT/'src'))
from knowledge_tracing.akt.authorization import gate2_build_hashes


def checked_archive(label):
    metadata = json.loads((HERE/(label+'-export-metadata.json')).read_bytes())
    raw = (NATIVE/(label+'-logs.zip')).read_bytes()
    assert len(raw) == metadata['bytes']
    assert hashlib.sha256(raw).hexdigest() == metadata['sha256']
    archive = zipfile.ZipFile(io.BytesIO(raw))
    assert archive.testzip() is None
    inventory = json.loads(archive.read('SHA256.json'))
    assert len(archive.namelist()) == len(set(archive.namelist())) == len(inventory)+1
    assert set(archive.namelist()) == set(inventory) | {'SHA256.json'}
    for name, digest in inventory.items():
        path = PurePosixPath(name)
        assert not path.is_absolute() and '..' not in path.parts and '\\' not in name
        assert hashlib.sha256(archive.read(name)).hexdigest() == digest
    return archive, metadata


installed_archive, _ = checked_archive('install')
archive, metadata = checked_archive('final')
prefix = 'artifacts/akt/runtime/isolated-install01/'
installed = json.loads(archive.read(prefix+'result.json'))
assert installed == json.loads(installed_archive.read(prefix+'result.json'))
assert installed['status'] == 'ISOLATED_LINUX_CPU_READY_NOT_CUDA'
assert installed['installed_packages'] == 44 and installed['base_pip_unchanged'] is True
assert installed['elapsed_seconds'] <= 600 and installed['peak_workspace_bytes'] <= 20*1024**3
assert archive.read(prefix+'base-pip-before.stdout') == archive.read(prefix+'base-pip-after.stdout')
audit = installed['installed_origins']
assert audit['package_count'] == 44 and audit['external_distribution_origins'] == 0
assert audit['torch_build'] == '2.7.1+cu126' and audit['cuda_initialized'] is False
assert audit['gpu_model_steps'] == audit['optimizer_steps'] == 0
report = json.loads(archive.read(prefix+'pip-install-report.json'))
expected = json.loads((HERE/'expected44.json').read_bytes())
actual = {
    item['metadata']['name'].lower().replace('_', '-').replace('.', '-'): dict(
        version=item['metadata']['version'], url=item['download_info']['url'],
        sha256=item['download_info']['archive_info']['hashes']['sha256'])
    for item in report['install']
}
assert len(report['install']) == 44 and actual == expected

preflight = 'artifacts/akt/preflight/'
report_name = 'gate2-evidence-colab-isolated198-20261110-01.json'
gate = json.loads(archive.read(preflight+report_name))
pointer = json.loads(archive.read(preflight+'gate2-current.json'))
assert pointer['evidence_file'] == report_name
assert hashlib.sha256(archive.read(preflight+report_name)).hexdigest() == pointer['evidence_sha256']
assert gate['status'] == 'PASS' and gate['test_result'] == dict(passed=1993, failed=0, errors=0, skipped=0)
assert gate['elapsed_seconds'] <= 600
assert gate['lock_sha256'] == installed['lock_sha256']
assert hashlib.sha256(archive.read(preflight+pointer['test_log_file'])).hexdigest() == gate['test_log_sha256']

contents, transforms = runpy.run_path(str(ROOT/'scripts/akt/build_colab_bundle.py'))['bundle_contents']()
current = gate2_build_hashes(ROOT)
expected_build = {name: hashlib.sha256(contents[name]).hexdigest() for name in current}
assert len(current) == 198 and gate['build_hashes'] == expected_build
differences = {name for name in current if current[name] != expected_build[name]}
assert differences <= set(transforms)
for name in differences:
    assert current[name] == transforms[name]['original_sha256']
assert sum(len(group['modules']) for group in gate['process_groups']) == 92
identifiers = []
for group in gate['process_groups']:
    data = archive.read(preflight+Path(group['junit_path']).name)
    assert hashlib.sha256(data).hexdigest() == group['junit_sha256']
    cases = list(ET.fromstring(data).iter('testcase'))
    assert len(cases) == group['test_result']['passed']
    assert all(case.find(tag) is None for case in cases for tag in ('failure', 'error', 'skipped'))
    identifiers.extend((case.get('classname'), case.get('name')) for case in cases)
assert len(identifiers) == len(set(identifiers)) == 1993
combined = archive.read(preflight+Path(pointer['test_log_file']).with_suffix('.xml').name)
assert hashlib.sha256(combined).hexdigest() == gate['junit_sha256']
assert len(list(ET.fromstring(combined).iter('testcase'))) == 1993
runtime = json.loads(archive.read('artifacts/akt/runtime/isolated-gate198-01/runtime.json'))
assert runtime['device'] == 'cpu' and runtime['cuda_available'] is False
assert runtime['torch_version'] == '2.7.1+cu126' and runtime['numpy_version'] == '2.5.4'
assert runtime['lock_sha256'] == installed['lock_sha256']
assert runtime['available_ram_bytes'] >= 4*1024**3
proof = dict(status='FULL_ISOLATED_CPU_GATE_VERIFIED', passed=1993, failed=0, errors=0,
    skipped=0, deselected=0, source_files=198, test_modules=92, packages_verified=44,
    notebook_copies_outputs_stripped=len(differences), model_and_tests_match_local=True,
    gate_elapsed_seconds=gate['elapsed_seconds'], installation_elapsed_seconds=installed['elapsed_seconds'],
    archive_sha256=metadata['sha256'], archive_bytes=metadata['bytes'],
    gate_report_sha256=pointer['evidence_sha256'], cuda_verified=False,
    main_training_completed=False, modal_spend_usd=0)
(HERE/'verification.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='utf-8')
(NATIVE/'final-receipt.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='utf-8')
print(json.dumps(proof))
