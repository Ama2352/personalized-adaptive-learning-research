"""Archive native context evidence đã freeze; không import Torch hoặc rerun tests/model."""

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import unquote
import xml.etree.ElementTree as ET

from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle

ROOT = Path(__file__).resolve().parents[4]
RUN_ID = 'cpu-worker-context-20261108-01'
LOCAL = ROOT / 'artifacts/akt/local-tests'
REAL = LOCAL / 'context-real-cpu-20261108-01'
PREPARED = ROOT / 'artifacts/akt/synthetic/ctx0801'
GATE = ROOT / 'artifacts/akt/preflight'
EXPECTED_GATE_SHA = '8d51380ed58b104aea0c0de37bdeb097d12e45071252ec973a696dc1fc7ac66d'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024**2), b''):
            h.update(chunk)
    return h.hexdigest()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def xml_counts(path):
    node = ET.parse(path).getroot()
    suites = list(node) if node.tag == 'testsuites' else [node]
    return {**{key: sum(int(s.attrib.get(key, 0)) for s in suites)
               for key in ('tests', 'failures', 'errors', 'skipped')},
            'junit_seconds': sum(float(s.attrib.get('time', 0)) for s in suites)}


def select_files():
    selected = {}

    def add(name, path):
        path = Path(path)
        if name in selected or not path.is_file() or path.suffix.lower() in {'.pt', '.parquet'}:
            raise ValueError(f'unsafe, missing or duplicate selected file: {name}')
        selected[name] = path

    changed = ['context', 'device_budget', 'config', 'authorization', 'watchdog', 'runner']
    for name in changed:
        add(f'current_akt_{name}.py', ROOT / f'src/knowledge_tracing/akt/{name}.py')
    add('current_prepare_synthetic_context.py', ROOT / 'scripts/akt/prepare_synthetic_context.py')
    for name in ['context', 'cuda_budget', 'context_recovery', 'synthetic_context_builder']:
        add(f'current_test_{name}.py', ROOT / f'tests/akt/test_{name}.py')
    for name in ['akt_worker_context_readiness_20261108', 'gpu07_adversarial_review_20261108']:
        add(name + '.md', ROOT / f'research_tracking/reports/{name}.md')
    add('contract20_snapshot.md', ROOT / 'docs/thesis_recovery/20_LINUX_CUDA_WORKER_CONTRACT.md')
    for name in ['gate2-evidence-20261108-context-18.json', 'gate2-current.json',
                 'gate2-tests-20261108-context-18.log', 'gate2-tests-20261108-context-18.xml', 'runtime-v2.json']:
        add('gate18__' + name, GATE / name)
    add('runtime_requirements_akt_lock.txt', ROOT / 'requirements-akt.lock.txt')
    for path in sorted(REAL.iterdir()):
        if path.is_file():
            add('actual_cpu__' + path.name, path)
    heavy = ROOT / 'experiments/akt/results/ctx0801'
    for path in sorted(heavy.iterdir()):
        if path.is_file() and path.suffix.lower() in {'.json', '.log'}:
            add('ctx0801__' + path.name, path)
    add('ctx0801_predictions_manifest.json', heavy / 'predictions/manifest.json')
    for i in (1, 2, 3):
        for suffix in ('log', 'xml'):
            path = LOCAL / f'context-20261108-0{i}.{suffix}'
            add(f'context0{i}__pytest.{suffix}', path)
    for folder, prefix in [('context03-postfailure-source', 'context03_snapshot'),
                           ('context-20261108-04', 'context04'), ('context-20261108-05', 'context05'),
                           ('parallel-context-recovery-20261108-01', 'context_recovery'),
                           ('parallel-synthetic-context-20261108-01', 'builder01'),
                           ('parallel-synthetic-context-20261108-02', 'builder02'),
                           ('parallel-synthetic-context-20261108-03-prepare', 'builder03_prepare')]:
        directory = LOCAL / folder
        # Không recurse pytest temp/data. Chỉ top-level files theo yêu cầu.
        for path in sorted(directory.iterdir()):
            if path.is_file():
                add(prefix + '__' + path.name, path)
        if prefix in {'builder01', 'builder02'}:
            # Đây là exact two source snapshots đã được handoff inventory ghi rõ.
            for sub in ['scripts/akt/prepare_synthetic_context.py', 'tests/akt/test_synthetic_context_builder.py']:
                add(prefix + '__source__' + sub.replace('/', '--'), directory / 'source' / sub)
    for path in sorted(PREPARED.iterdir()):
        if path.is_file() and path.suffix == '.json':
            add('prepared_ctx0801__' + path.name, path)
    for name in ['run_context_checks.py', 'run_real_context_cpu.py',
                 'verify_real_context_alignment.py', 'verify_real_context_alignment_attempt01.py']:
        add('helper__' + name, LOCAL / name)
    add('archive_pack_source.py', Path(__file__).resolve())
    add('evidence_helper.py', ROOT / 'src/knowledge_tracing/evidence.py')
    return selected


def preflight(selected):
    total = sum(p.stat().st_size for p in selected.values())
    if total > 4 * 1024**2:
        raise ValueError('selected archive inputs exceed 4MiB')
    gate_path = GATE / 'gate2-evidence-20261108-context-18.json'
    assert sha(gate_path) == EXPECTED_GATE_SHA
    gate, pointer = read(gate_path), read(GATE / 'gate2-current.json')
    assert gate['status'] == 'PASS' and gate['test_result'] == dict(passed=661, failed=0, errors=0, skipped=0)
    assert pointer['evidence_file'] == gate_path.name and pointer['evidence_sha256'] == EXPECTED_GATE_SHA
    assert sha(GATE / pointer['test_log_file']) == pointer['test_log_sha256'] == gate['test_log_sha256']
    assert sha(GATE / 'gate2-tests-20261108-context-18.xml') == gate['junit_sha256']
    gate_xml = xml_counts(GATE / 'gate2-tests-20261108-context-18.xml')
    assert {k: gate_xml[k] for k in ('tests', 'failures', 'errors', 'skipped')} == dict(tests=661, failures=0, errors=0, skipped=0)
    for name, path in selected.items():
        if name.startswith('current_'):
            assert sha(path) == gate['build_hashes'][rel(path)], name
    acceptance, alignment = read(REAL / 'acceptance.json'), read(REAL / 'alignment.json')
    assert acceptance['status'] == alignment['status'] == 'PASS'
    assert acceptance['actual_cuda'] is False and acceptance['research_model_evidence'] is False
    assert acceptance['input_hashes_unchanged'] is True and acceptance['predictions_rows'] == 8
    training = acceptance['summary']['training']
    assert training['optimizer_steps'] == 2 and training['optimized_target_rows'] == 48
    assert acceptance['summary']['checkpoint_reload_state_exact'] is True
    assert alignment['training_targets'] == 48 and alignment['validation_targets'] == 8
    assert alignment['alignment_matches_original_toy_labels'] and alignment['history_counts_exact_0_to_7']
    assert sha(REAL / 'toy_predictions.csv') == alignment['prediction_csv_sha256']
    original_outputs = []
    for path, expected in acceptance['output_hashes'].items():
        p = ROOT / path
        assert p.resolve().is_relative_to((ROOT / 'experiments/akt/results/ctx0801').resolve())
        actual = sha(p)
        assert actual == expected, path
        original_outputs.append(dict(path=path, bytes=p.stat().st_size,
                                     expected_sha256=expected, actual_sha256=actual,
                                     match=True, copied= p.suffix.lower() not in {'.pt', '.parquet'}))
    input_checks = []
    for path, expected in read(REAL / 'planned-run.json')['input_hashes'].items():
        p = ROOT / path
        assert p.resolve().is_relative_to(PREPARED.resolve()) and sha(p) == expected
        input_checks.append(dict(path=path, sha256=expected, match=True,
                                 copied=p.suffix.lower() != '.parquet'))
    # Gate identity thật của authorization và acceptance phải khớp report hiện tại.
    approval = read(REAL / 'authorization.json')
    for identity in (approval['identity'], acceptance['identity']):
        assert identity['gate2_report_sha256'] == EXPECTED_GATE_SHA
        assert identity['gate2_test_log_sha256'] == gate['test_log_sha256']
        assert identity['gate2_pointer_sha256'] == sha(GATE / 'gate2-current.json')
    xml_summary = {}
    for name, path in selected.items():
        if path.suffix == '.xml':
            xml_summary[name] = xml_counts(path)
    assert xml_summary['context03__pytest.xml']['failures'] == 1
    assert xml_summary['builder01__tests.xml']['failures'] == 1
    assert xml_summary['context05__pytest.xml']['tests'] == 78
    assert xml_summary['builder02__tests.xml']['tests'] == 53
    assert xml_summary['context_recovery__pytest.xml']['tests'] == 11
    return total, gate_xml, xml_summary, original_outputs, input_checks


def ignored_explicit(paths):
    ignored = []
    for start in range(0, len(paths), 24):
        process = subprocess.run(['git', '-c', 'core.quotepath=false', 'check-ignore', '--no-index', '--',
                                  *paths[start:start+24]], cwd=ROOT, capture_output=True, text=True)
        assert process.returncode in (0, 1), process.stderr
        ignored.extend(process.stdout.splitlines())
    return sorted(set(ignored))


def main():
    selected = select_files()
    total, gate_xml, xml_summary, original_outputs, input_checks = preflight(selected)
    before = [dict(source=rel(path), destination=name, bytes=path.stat().st_size,
                   source_sha256=sha(path)) for name, path in selected.items()]
    extra_sources = [ROOT / item['path'] for item in original_outputs + input_checks]
    sources = list(dict.fromkeys([*selected.values(), *extra_sources]))
    note = '''# Context worker và bounded phase CUDA — 08/11/2026

Run cpu-worker-context-20261108-01 là archive phần mềm/operational evidence.
Gate18 PASS661/177,08s và actual Windows CPU watchdog→child→real guards với
input dummy:48train targets/2updates/8validation predictions/checkpoint reload.
Không research efficacy, actual new-worker CUDA, full outer refit/fullCV,
realdata/Holdout/Modal, paid spend hoặc S04/S05 adoption.

## Bằng chứng được giữ

- Reports parent/review/contract20 là snapshots; canonical references còn cần repo.
- Current6AKTmodules, builder và4tests đều khớp Gate18 build hashes.
- Context trials01–03 root logs/XML; postfailure03 source;04/05 chỉ files top-level.
- Recovery receipt/log/XML/source; builder01FAIL/02PASS/03prepare cùng exact
  source snapshots. Không copy pytest t/temporary fixture trees hoặc Parquet.
- Actual CPU acceptance/alignment/execution/planned/config/auth/stdout/stderr
  và8dummy-row CSV. Authorization là historical exact-run evidence, không
  cấp quyền reuse/research/GPU. Toy AUC/loss không được dùng làm efficacy.
- Preparedctx config/context/inventory/marker/manifests, không Parquet.
- Original checkpoint/prediction shard chỉ hash/verify theo acceptance;
  .pt/Parquet vẫn nằm ở experiments hoặc prepared synthetic root, không copy.
- Alignment attempt01 KeyError chỉ được thuật lại trong parent report và giữ
  source verifier attempt01; không có raw stderr log, không tạo log giả.

## Đọc và kiểm

[Parent report](akt_worker_context_readiness_20261108.md),
[review](gpu07_adversarial_review_20261108.md),
[verification](archive_verification.json),
[copy before](archive_copy_inventory_before.json),
[copy after](archive_copy_inventory.json),
[source provenance](source_provenance.json),
[raw whitespace](raw_whitespace_inventory.json),
[ignored paths](force_add_paths.json).

Archive không rerun tests/models hoặc load checkpoint. Helper verify kiểm output
integrity, không scientific validity. Child/worker/controller/JUnit/pytest timing
giữ riêng từ receipts, không ép các wall measures thành cùng một phép đo.
Trial03 postfailure snapshot không được gọi exact prelaunch snapshot; root
trial01/02 không có source snapshots độc lập thì không dựng lịch sử giả.

Input hashes không là atomic DuckDB snapshot khi có concurrent writers; actual
dummy run dùng input giữ bất biến. VRAM cap chỉ PyTorch allocator, chưa actual
GPU07 phase hardware proof; Linux lock/image/new-worker CUDA vẫn còn thiếu.
Runtime hiện có là Windows CPU; không claim môi trường Linux/Modal equivalence.

Raw failure logs/XML giữ byte-exact kể cả trailing whitespace; parent có exact
paths/line inventory để xử lý .gitattributes nếu cần, archive không sửa whitespace.
Canonical report snapshot relative links có thể không resolve từ vị trí flat
archive; selected_links.json kiểm từ canonical source directory, không rewrite
nội dung cũ hoặc gọi archive là standalone executable kit.

Không sửa index/state/tasks/Git/source sauGate. Không thêm/sửa bundle sau closure.
'''
    with record_evidence_run(ROOT, RUN_ID, metadata={
        'kind': 'AKT_GPU07_WORKER_CONTEXT_WINDOWS_CPU_ENGINEERING_ARCHIVE',
        'scope_vi': 'Source-bound Gate18 + actual real-guard dummy CPU lifecycle; CUDA phase chỉ mocked/spec, không efficacy.',
        'gate18': {'passed': 661, 'failed': 0, 'errors': 0, 'skipped': 0,
                   'report_sha256': EXPECTED_GATE_SHA, 'junit_seconds': gate_xml['junit_seconds']},
        'actual_cpu': {'status': 'PASS', 'optimizer_steps_reused': 2, 'train_targets': 48,
                       'validation_predictions': 8, 'real_guards': True, 'dummy_only': True},
        'new_training_or_test_runs_in_archive': 0,
        'new_optimizer_steps_in_archive': 0,
        'actual_new_worker_cuda': False, 'realdata_holdout_queries': 0,
        'gpu_cloud_calls': 0, 'fitted_research_efficacy': False,
        'selected_copy_input_bytes': total,
    }, sources=sources, note=note) as out:
        dump(out / 'archive_copy_inventory_before.json', before)
        after = []
        for item in before:
            path = ROOT / item['source']
            destination = out / item['destination']
            shutil.copyfile(path, destination)
            actual, copied = sha(path), sha(destination)
            assert actual == copied == item['source_sha256']
            after.append({**item, 'source_after_sha256': actual, 'copied_sha256': copied, 'exact_match': True})
        dump(out / 'archive_copy_inventory.json', after)
        # Reverify original binaries/shards and inputs after copies; no torch/DuckDB import.
        for item in original_outputs:
            item['after_copy_sha256'] = sha(ROOT / item['path'])
            assert item['after_copy_sha256'] == item['expected_sha256']
        for item in input_checks:
            item['after_copy_sha256'] = sha(ROOT / item['path'])
            assert item['after_copy_sha256'] == item['sha256']
        dump(out / 'archive_verification.json', {
            'scope_vi': 'Hash/XML/copy-only verification; không model/training hoặc synthetic corpus generation mới.',
            'current_source_gate18_bindings': {rel(p): sha(p) for n, p in selected.items() if n.startswith('current_')},
            'xml_readouts': xml_summary,
            'original_actual_output_hash_checks': original_outputs,
            'original_synthetic_input_hash_checks': input_checks,
            'alignment_original_csv_sha256': sha(REAL / 'toy_predictions.csv'),
            'new_test_or_model_runs': 0,
        })
        links = []
        for name in ['akt_worker_context_readiness_20261108.md', 'gpu07_adversarial_review_20261108.md', 'contract20_snapshot.md']:
            original = selected[name]
            for target in re.findall(r'\]\(([^)]+)\)', original.read_text(encoding='utf-8')):
                if '://' in target:
                    continue
                path = (original.parent / unquote(target.split('#')[0])).resolve()
                assert path.is_relative_to(ROOT) and path.exists(), target
                links.append(dict(source=rel(original), target=target, resolved=rel(path), exists=True))
        dump(out / 'selected_links.json', {'scope_vi': 'Canonical source directory, local locators only.', 'count': len(links), 'links': links})
        whitespace = []
        for name, path in selected.items():
            # splitlines bỏ CRLF để không gọi line ending là trailing spaces.
            lines = path.read_bytes().splitlines()
            numbers = [i for i, line in enumerate(lines, 1) if re.search(rb'[ \t]+$', line)]
            trailing_blank = 0
            for line in reversed(lines):
                if line.strip():break
                trailing_blank += 1
            if numbers or trailing_blank > 0:
                whitespace.append(dict(source=rel(path), bundle_path=rel(out / name),
                                       trailing_space_lines=numbers, trailing_blank_lines=trailing_blank,
                                       raw_failure_or_execution_log=path.suffix in {'.log', '.xml'},
                                       bytes_preserved=True))
        dump(out / 'raw_whitespace_inventory.json', {
            'scope_vi': 'Không sửa raw bytes. Exact paths cho parent .gitattributes nếu diff-check flag; CRLF không tính là trailing space.',
            'files': whitespace,
        })
        dump(out / 'source_provenance.json', {
            'source_commit_upstream': read(GATE / 'gate2-evidence-20261108-context-18.json')['source'],
            'gate18_report_sha256': EXPECTED_GATE_SHA,
            'gate18_build_hashes': read(GATE / 'gate2-evidence-20261108-context-18.json')['build_hashes'],
            'copied_current_sources_match_gate18': True,
            'historical_trials_not_relabelled_as_current_source': True,
            'missing_alignment_attempt01_raw_log': True,
            'alignment_attempt01_evidence_vi': 'Parent report narrative + verifier source snapshot only; no fabricated raw log.',
            'native_upstream_source_modified': False,
            'archive_copies_no_pt_or_parquet': True,
            'S04_S05_adopted': False,
        })
        # Explicit argument list tránh newline translation của check-ignore stdin trên Windows.
        paths = [rel(p) for p in out.iterdir()] + [rel(out / 'force_add_paths.json')]
        ignored = ignored_explicit(paths)
        dump(out / 'force_add_paths.json', {
            'scope_vi': 'git check-ignore --no-index bằng exact argv; không git add/commit.',
            'ignored_paths_requiring_force_add': ignored,
            'raw_canonical_helpers_not_required_to_add': 'Đã snapshot vào bundle; originals trong artifacts/akt vẫn ignored.',
        })
    verified = verify_evidence_bundle(ROOT / 'research_tracking/runs' / RUN_ID)
    manifest = ROOT / 'research_tracking/runs' / RUN_ID / 'manifest.json'
    print(json.dumps({**verified, 'run_id': RUN_ID, 'manifest_sha256': sha(manifest),
                      'copies': len(after), 'sources': len(sources), 'copy_bytes': total,
                      'bundle_bytes': sum(p.stat().st_size for p in manifest.parent.iterdir()),
                      'original_output_checks': len(original_outputs),
                      'synthetic_input_checks': len(input_checks), 'links': len(links),
                      'ignored_logs': ignored,
                      'raw_whitespace_paths': [x['bundle_path'] for x in whitespace]}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
