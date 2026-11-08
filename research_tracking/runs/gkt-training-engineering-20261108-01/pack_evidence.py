"""Đóng GKT train-batch engineering sau actual parent review; không model rerun."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = Path.cwd().resolve()
assert Path(sys.prefix).resolve() == ROOT / '.venv'
PREP = ROOT / 'artifacts/akt/local-tests/gkt03-training-preparation-20261108-01'
TRIAL = ROOT / 'artifacts/akt/local-tests/parallel-gkt-training-20261108-01'
FAIL = ROOT / 'artifacts/akt/local-tests/parallel-gkt-training-20261108-controller00'
REPORT = ROOT / 'research_tracking/reports/gkt_training_readiness_20261108.md'
RUN = 'gkt-training-engineering-20261108-01'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
expected = {'src/knowledge_tracing/gkt/training.py': '6def666d82cf02dfefcf8980c2670ac24f3a137a86e9093e66cb87bc2cabc4e5',
            'tests/gkt/test_training.py': '1d4a9869d6b167e972c719df637b593171343e6d93fd55395925c7e0268392e0'}
assert all(sha(ROOT / n) == h for n, h in expected.items())
review = read(PREP / 'parent_review.json')
assert review['status'] == 'PARENT_ACTUAL_SOURCE_TEST_AND_RECEIPT_REVIEW_ACCEPTED_ENGINEERING_CONTRACT'
assert review['accepted_source_sha256'] == expected
assert sha(TRIAL / 'run.json') == 'aa48d1b448e989b9440688fec4553ece1437abee679528daa45693634aa407cc'
trial = read(TRIAL / 'run.json')
assert trial['exit_code'] == 0 and not trial['timed_out'] and trial['resource_accepted']
assert trial['sources_unchanged'] and trial['source_before'] == trial['source_after']
assert trial['controller_elapsed_seconds'] + 1 < 60 and trial['controller_wall_seconds'] + 1 < 60
assert all(sha(ROOT / n) == h for n, h in trial['source_before'].items())
for n, h in trial['source_before'].items():
    assert sha(TRIAL / (n.replace('/', '__') + '.before')) == h
    assert sha(TRIAL / (n.replace('/', '__') + '.after')) == h
assert all(sha(TRIAL / n) == h for n, h in trial['log_sha256'].items())
suites = list(ET.parse(TRIAL / 'pytest.xml').iter('testsuite'))
counts = {key: sum(int(s.attrib.get(key, 0)) for s in suites)
          for key in ('tests', 'failures', 'errors', 'skipped')}
assert counts == dict(tests=45, failures=0, errors=0, skipped=0)
ledger = [json.loads(line) for line in (TRIAL / 'optimizer-updates.jsonl').read_text().splitlines()]
assert trial['optimizer_updates'] == len(ledger) == 4 and [x['update'] for x in ledger] == [1, 2, 3, 4]
failure = read(FAIL / 'failure.json')
assert failure['optimizer_updates'] == 0 and not failure['full_controller_preexecution_snapshot_available']
pairs = [(p, 'trial01__' + p.name) for p in sorted(TRIAL.iterdir()) if p.is_file()]
pairs += [(FAIL / name, 'controller00__' + name) for name in ('failure.json', 'stderr.log')]
pairs += [(PREP / name, name) for name in ('PLAN.md', 'parent_review.json', 'pack_evidence.py')]
pairs += [(ROOT / n, 'final__' + n.replace('/', '__')) for n in expected]
pairs += [(REPORT, 'gkt_training_readiness_20261108.md'),
          (ROOT / 'src/knowledge_tracing/gkt/__init__.py', 'gkt_package_init.py'),
          (ROOT / 'src/knowledge_tracing/evidence.py', 'evidence_helper.py')]
assert len({name for _, name in pairs}) == len(pairs)
before = [dict(source=p.relative_to(ROOT).as_posix(), copy=alias, bytes=p.stat().st_size,
               sha256_before_copy=sha(p)) for p, alias in pairs]
acceptance = dict(kind='SYNTHETIC_GKT_ONE_TRAIN_BATCH_ENGINEERING_ONLY', recipe_id='gkt_static_recurrent_convention_v1',
    actual_tests=counts, actual_optimizer_updates=4, max_actual_updates=8,
    controller_elapsed_seconds=trial['controller_elapsed_seconds'], pytest_reported_seconds=8.21,
    cumulative_controller_seconds_conservative=trial['controller_elapsed_seconds'] + 1,
    cumulative_limit_seconds=60, controller_compile_failure_retained=True,
    controller_compile_failure_model_test_updates=0, full_failed_controller_snapshot_available=False,
    review='PARENT_ACTUAL_REVIEW; no independent reviewer agent',
    trained_weight_role='synthetic_trained_engineering_only',
    checkpoint_resume_epoch_corpus_adapter=False, scientific_S04_S05_adoption=False,
    data_GPU_network_install_calls=0, model_test_reruns_during_archive=0,
    limitations_vi=['Caller-owned budget/state/source identity cooperative, không nonresettable authorization hoặc origin attestation.',
        'Final state detached và bind weights trước update; không stale carry/TBPTT/resume.',
        'Exception sau update không hứa rollback hoặc checkpoint; không fitted research baseline.'])
# Per-process exact trusted repository directory only; no Git configuration writes.
count = int(os.environ.get('GIT_CONFIG_COUNT', '0'))
os.environ[f'GIT_CONFIG_KEY_{count}'] = 'safe.directory'
os.environ[f'GIT_CONFIG_VALUE_{count}'] = str(ROOT)
os.environ['GIT_CONFIG_COUNT'] = str(count + 1)
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
sources = sorted({p for p, _ in pairs} | {ROOT / n for n in trial['source_before']})
note = '''# GKT train-batch engineering — 08/11/2026

45/45 CPU tests,4 actual Adam updates, controller9,844604giây; conservative cumulative10,844604/60giây gồm1giây dự trữ cho controller00 compilation failure trước import/test/model. Không corpus/data/GPU hoặc checkpoint/resume/epoch/adapter/S05 adoption. Parent đã review source/tests/actual receipts; không dựng independent reviewer agent. Plan, final source/test,10 trước/sau snapshots, raw logs/JUnit/ledger và failure quan trọng được copy byte-exact, kiểm SHA trước/sau. Full failed controller source không có, giới hạn này được ghi rõ.

`frozen_acceptance.json` ghi scope; `copy_inventory_before.json` và `copy_inventory.json` ghi input/output. `manifest.json` hash toàn bộ output. `force_add_paths.txt` liệt kê toàn bộ bundle paths để parent có thể force-add các tệp ignored khi commit; không Git writes từ archiver. Không sửa bundle sau closure.
'''
with record_evidence_run(ROOT, RUN, metadata={'kind': acceptance['kind'], 'acceptance': acceptance}, sources=sources, note=note) as directory:
    for p, alias in pairs:
        shutil.copyfile(p, directory / alias)
    after = []
    for row in before:
        h = sha(directory / row['copy'])
        assert h == row['sha256_before_copy'] == sha(ROOT / row['source'])
        after.append({**row, 'sha256_after_copy': h, 'exact_match': True})
    def write(name, value):
        with (directory / name).open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')
    write('copy_inventory_before.json', before)
    write('copy_inventory.json', after)
    write('frozen_acceptance.json', acceptance)
    names = {alias for _, alias in pairs} | {'README.md', 'execution.log', 'copy_inventory_before.json',
            'copy_inventory.json', 'frozen_acceptance.json', 'force_add_paths.txt'}
    with (directory / 'force_add_paths.txt').open('x', encoding='utf-8') as stream:
        stream.write(''.join((directory / n).relative_to(ROOT).as_posix() + '\n'
                             for n in sorted(names | {'manifest.json'})))
verified = verify_evidence_bundle(directory)
assert {p.name for p in directory.iterdir()} == names | {'manifest.json'}
manifest = read(directory / 'manifest.json')
assert set(manifest['outputs_sha256']) == names and verified['artifacts'] == len(names)
assert all(sha(ROOT / n) == h for n, h in expected.items())
for link in re.findall(r'\]\(([^)]+)\)', REPORT.read_text(encoding='utf-8')):
    assert (REPORT.parent / link).resolve().exists(), link
print(json.dumps({**verified, 'manifest_sha256': sha(directory / 'manifest.json'),
    'report_sha256': sha(REPORT), 'copy_pairs': len(pairs), 'all_files_including_manifest': len(names) + 1,
    'source_sha256': expected, 'force_add_list': str(directory / 'force_add_paths.txt')}, ensure_ascii=False))
