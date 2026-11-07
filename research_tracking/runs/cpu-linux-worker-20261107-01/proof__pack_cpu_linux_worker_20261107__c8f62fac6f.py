"""Archive combined sau parent xác nhận Gate17; không poll/run Gate hoặc model."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle

RUN = 'cpu-linux-worker-20261107-01'
L = 'artifacts/akt/local-tests/'
P = 'artifacts/akt/preflight/'
R = 'research_tracking/reports/'
FINAL = 'fd583722bc3f3b97e990cfde83715601b49d4daae793c587603305dbc79ab225'
FAILED = '734f28bd0aea487a67b364a83e3def69a3ca1cd34e3c658583055c5f8ec28b47'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8-sig'))


def counts(path):
    suites = ET.parse(path).getroot().findall('testsuite')
    return {k: sum(int(s.get(k, 0)) for s in suites) for k in ('tests', 'failures', 'errors', 'skipped')}


def main(expected_report_sha):
    assert Path(sys.prefix).resolve() == ROOT / '.venv'
    gate_name = P + 'gate2-evidence-20261107-linux-worker-17.json'
    gate = load(gate_name)
    assert sha(ROOT / gate_name) == expected_report_sha
    assert gate['status'] == 'PASS' and gate['test_result'] == {'passed': 513, 'failed': 0, 'errors': 0, 'skipped': 0}
    log = P + 'gate2-tests-20261107-linux-worker-17.log'
    xml = P + 'gate2-tests-20261107-linux-worker-17.xml'
    assert sha(ROOT / log) == gate['test_log_sha256']
    assert sha(ROOT / xml) == gate['junit_sha256']
    assert counts(ROOT / xml) == {'tests': 513, 'failures': 0, 'errors': 0, 'skipped': 0}
    assert '513 passed in 269.98s' in (ROOT / log).read_text(encoding='utf-8')
    pointer = load(P + 'gate2-current.json')
    assert pointer['evidence_sha256'] == expected_report_sha and pointer['test_log_sha256'] == gate['test_log_sha256']
    for name, expected in gate['build_hashes'].items():
        assert sha(ROOT / name) == expected, name
    assert sha(ROOT / 'tests/akt/test_worker_lifecycle.py') == FINAL
    failure = load(L + 'linux-gate16-failure-receipt.json')
    assert failure['passed'] == 512 and failure['failed'] == 1 and failure['test_worker_source_sha256'] == FAILED
    assert counts(ROOT / (P + 'gate2-tests-20261107-linux-worker-16.xml')) == {'tests': 513, 'failures': 1, 'errors': 0, 'skipped': 0}

    selected = {}

    def add(name, category):
        path = ROOT / name
        assert path.is_file() and path.suffix not in {'.pt', '.parquet', '.zip'}
        selected.setdefault(name, category)

    handoff_name = L + 'parallel-linux-runtime-20261107-03/handoff-inventory.json'
    runtime_handoff = load(handoff_name)
    for item in runtime_handoff['source_inputs'] + runtime_handoff['outputs']:
        assert sha(ROOT / item['path']) == item['sha256'], item['path']
        add(item['path'], 'runtime')
    add(handoff_name, 'runtime')
    for trial in ('01', '02', '03'):
        for p in (ROOT / (L + 'parallel-linux-runtime-20261107-' + trial)).glob('*'):
            if p.is_file():
                add(p.relative_to(ROOT).as_posix(), 'runtime' + trial)
    for label in ('20261107-01', '20261107-02', '20261107-03', '20261108-04'):
        directory = ROOT / (L + 'parallel-worker-' + label)
        for p in directory.rglob('*'):
            if p.is_file() and p.suffix in {'.json', '.log', '.xml', '.py', '.txt', '.diff'}:
                add(p.relative_to(ROOT).as_posix(), 'worker' + label[-2:])
    for p in (ROOT / (L + 'parallel-worker-path-20261108-01')).glob('*'):
        if p.is_file() and p.suffix in {'.json', '.py', '.log', '.xml'}:
            add(p.relative_to(ROOT).as_posix(), 'path')
    path_control = load(L + 'parallel-worker-path-20261108-01/path_control.json')
    assert [r['path_characters'] for r in path_control['cases']] == [87, 227, 264, 220]
    assert [r['status'] for r in path_control['cases']] == ['PASS', 'PASS', 'ERROR', 'PASS']
    assert path_control['source_snapshot_sha256'] == FAILED
    deep = load(L + 'parallel-worker-20261108-04/deep_regression_handoff.json')
    assert deep['source_sha256'] == FINAL and deep['failed_gate16_source_sha256'] == FAILED
    for key in ('latest_acceptance', 'negative_acceptance'):
        assert sha(ROOT / deep[key + '_path']) == deep[key + '_sha256']
    deepbase = Path(deep['basetemp'])
    gatebase = Path(gate['command'][gate['command'].index('--basetemp') + 1])
    for label, base in (('deep', deepbase), ('gate17', gatebase)):
        for p in base.glob('wk*/p/**/*.json'):
            add(p.relative_to(ROOT).as_posix(), label)
    for item in ('worker-20261107-03', 'worker-20261108-04'):
        old_inventory = load(L + 'parallel-' + item + '/handoff_inventory.json')
        for entry in old_inventory['files']:
            assert sha(ROOT / entry['path']) == entry['sha256'], entry['path']
    for trial in ('01', '02'):
        for ext in ('log', 'xml'):
            add(L + 'linux-parent-fixture-20261107-' + trial + '.' + ext, 'parent' + trial)
    for name in (
        'src/knowledge_tracing/akt/authorization.py', 'scripts/akt/check_runtime.py',
        'tests/akt/test_runtime.py', 'tests/akt/test_runner.py', 'tests/akt/test_worker_lifecycle.py',
        'src/knowledge_tracing/evidence.py',
        'docs/thesis_recovery/20_LINUX_CUDA_WORKER_CONTRACT.md',
        R + 'akt_linux_runtime_contract_20261107.md', R + 'akt_main_worker_lifecycle_20261107.md',
        L + 'linux-gate16-failure-receipt.json',
        P + 'gate2-tests-20261107-linux-worker-16.log', P + 'gate2-tests-20261107-linux-worker-16.xml',
        gate_name, log, xml, P + 'gate2-pointer-before-20261107-linux-worker-17.json', P + 'gate2-current.json',
        Path(__file__).resolve().relative_to(ROOT).as_posix(),
    ):
        add(name, 'source' if name.startswith(('src/', 'scripts/', 'tests/')) else 'proof')
    inventory = []
    for name, category in selected.items():
        p = ROOT / name
        # Tên flat ngắn để chính archive không lặp lại lỗi deep path.
        alias = category + '__' + p.stem[:45] + '__' + hashlib.sha256(name.encode()).hexdigest()[:10] + p.suffix
        inventory.append({'source': name, 'archived_as': alias, 'sha256_before_copy': sha(p)})
    assert len({r['archived_as'] for r in inventory}) == len(inventory)
    accepted = load(deep['latest_acceptance_path'])
    assert (accepted['training_targets'], accepted['validation_targets'], accepted['fitted_predictions'], accepted['unseen_predictions']) == (8, 4, 3, 1)
    # Chỉ đọc4synthetic rows từ Parquet đã có handoffSHA; không execute model.
    import duckdb
    prediction_dir = (ROOT / deep['latest_acceptance_path']).parent / 'predictions'
    parquet = sorted(prediction_dir.glob('part-*.parquet'))
    old_inputs = load(L + 'parallel-worker-20261108-04/handoff_inventory.json')['files']
    recorded = {r['path']: r['sha256'] for r in old_inputs}
    for p in parquet:
        assert sha(p) == recorded[p.relative_to(ROOT).as_posix()]
    con = duckdb.connect()
    try:
        cur = con.execute('SELECT * FROM read_parquet(?) ORDER BY source_row', [[str(p) for p in parquet]])
        columns = [r[0] for r in cur.description]
        rows = cur.fetchall()
    finally:
        con.close()
    assert len(rows) == len({r[columns.index('source_row')] for r in rows}) == 4
    identities = [[r[columns.index(k)] for k in ('user_id', 'source_row', 'exercise', 'correct')] for r in rows]
    assert identities == accepted['prediction_target_identities']
    metadata = {'kind': 'WINDOWS_CPU_RUNTIME_CONTRACT_AND_SYNTHETIC_WORKER_ARCHIVE', 'schema_version': 1,
                'gate17': {'passed': 513, 'failed': 0, 'errors': 0, 'skipped': 0, 'pytest_seconds': 269.98, 'report_sha256': expected_report_sha},
                'gate16': {'passed': 512, 'failed': 1, 'pytest_seconds': 372.65, 'published': False, 'worker_source_sha256': FAILED},
                'final_worker_source_sha256': FINAL,
                'scope_vi': 'Actual Windows CPU integration, mocked platform/runtime negatives, metadata legacy Windows preflight. Không actual Linux/CUDA main-worker hoặc GPU/fulltrain/realdata/RQ efficacy.',
                'new_workload': {'tests': 0, 'model_steps': 0, 'gpu_cloud_calls': 0, 'dataset_queries': 0, 'synthetic_prediction_artifact_rows_read': 4},
                'limits_vi': ['Runtime trial01/02 sources là reconstruction không có pre-run SHA certificate.', 'Failed Gate16 build hashes chụp sau failure, không wrapper-issued PASS report.', 'Fixture shortening không sửa production DuckDB long-path risk.', 'Main runner Linux lock/report wiring và GPU07/08/09 vẫn pending; inherited Colab venv không được tự adopt.']}
    note = '''# Combined runtime/worker CPU acceptance — 07/11/2026

Bundle giữ runtime3attempts, worker4attempts, parent fixture2attempts, cheap path contrast, failed Gate16 và published Gate17. Đây là archive sau Gate17PASS513/0fail/error/skip269.98s; không rerun Gate/model/GPU hoặc đọc realdata. Runtime platform mocks không chứng minh actual Linux/CUDA worker. Parent20contract/report snapshots giữ rõ phần GPU06 còn pending và không tự thông qua GPU07/08/09/S04/S05.

Failed Gate16:512pass/1fail372.65s, no pointer publication, source worker734f28bd... được giữ riêng. Failure là DuckDB pending path264chars; cheap contrast cùng parent227charsPASS,264charsERROR và compact root/full filename220charsPASS. Final fixturefd583722... chỉ rút nesting ngay trong Gate basetemp; không đổi production exporter/guards/registry. Production root đủ dài vẫn là rủi ro riêng. Gate17source hashes/pointer/log/XML được đối chiếu, không sửa lịch sử.

Worker actual in-process main entry đọc syntheticParquet thật qua loader/split/caps:8train/1optimizerstep,4val gồm3known+1OOV, bestcheckpoint reload exact/export4targetidentities. Authorization/caps thật; external Gate/RAM fixtures có nhãn. Không gắn refit/watchdog/freshprocess claims cho newworker cases; historical recovery coverage được trỏ riêng. CSV4rows chỉ projection từ Parquet handoffSHA đã có, không dataset query/model inference. .pt/Parquet/ZIP không copy vào bundle.

Runtime3attempts giữ Git ownership failure, CLI sys.argv fixture failure và63pass final. Intermediate sources runtime01/02 là reconstruction từ patch đã biết, không pre-run SHA certificates; metadata/traceback crosschecks giữ nguyên. Parent fixture01 là pytest temp-folder error trước test body;02PASS, không production runtime failure. Legacy Windows preflight chỉ đọc metadata, không actual inherited Colab venv acceptance.

archive_copy_inventory.json map tên flat ngắn với nguồn và pre/post exactSHA. Helpers record/verify hash mọi output; source paths không phải yêu cầu force-add artifacts binaries hoặc ignored originals. force_add_paths.txt liệt kê logs trong bundle cần force-add. Không sửa bundle sau closure, indices/state/docs/Git/.gitattributes.
'''
    with record_evidence_run(ROOT, RUN, metadata=metadata, sources=[ROOT / n for n in selected] + parquet, note=note) as directory:
        for r in inventory:
            source = ROOT / r['source']
            assert sha(source) == r['sha256_before_copy']
            target = directory / r['archived_as']
            target.write_bytes(source.read_bytes())
            r['sha256_after_copy'] = sha(target)
            r['exact_match'] = r['sha256_before_copy'] == r['sha256_after_copy']
            assert r['exact_match']
        def put(name, value):
            (directory / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        put('archive_copy_inventory.json', inventory)
        put('archive_validation.json', {'copied_files': len(inventory), 'all_copy_sha_exact': True, 'gate17_report_log_xml_pointer_binding': True, 'current_gate17_build_hashes_verified': len(gate['build_hashes']), 'final_source_sha256': FINAL, 'failed_gate16_source_sha256': FAILED, 'runtime_handoff_hashes_verified': 21, 'path_control': path_control, 'worker_acceptance': accepted})
        with (directory / 'synthetic_worker_predictions.csv').open('x', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, lineterminator='\n')
            writer.writerow(columns)
            writer.writerows(rows)
        put('prediction_csv_derivation.json', {'rows': 4, 'inputs': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)} for p in parquet], 'csv_sha256': sha(directory / 'synthetic_worker_predictions.csv'), 'scope': 'Derived synthetic artifact only; no original binary copy/model execution'})
        force = [f'research_tracking/runs/{RUN}/execution.log'] + [f'research_tracking/runs/{RUN}/' + r['archived_as'] for r in inventory if r['archived_as'].endswith('.log')]
        (directory / 'force_add_paths.txt').write_text('\n'.join(force) + '\n', encoding='utf-8')
    verified = verify_evidence_bundle(directory)
    closed = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
    assert {p.name for p in directory.iterdir()} == {'manifest.json', *closed['outputs_sha256']}
    assert all(sha(directory / n) == v for n, v in closed['outputs_sha256'].items())
    print(json.dumps({'run': directory.relative_to(ROOT).as_posix(), 'integrity': verified, 'copied_files': len(inventory), 'all_output_sha_exact': len(closed['outputs_sha256']), 'manifest_sha256': sha(directory / 'manifest.json'), 'force_add_paths': force}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--expected-report-sha256', required=True)
    main(parser.parse_args().expected_report_sha256)
