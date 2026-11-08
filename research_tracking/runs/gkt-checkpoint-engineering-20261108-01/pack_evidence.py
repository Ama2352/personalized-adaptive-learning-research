"""Dry inventory trước parent closure approval; không test/model/Git writes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = Path.cwd().resolve()
PREP = ROOT / 'artifacts/akt/local-tests/gkt04-checkpoint-preparation-20261108-01'
REPORT = ROOT / 'research_tracking/reports/gkt_checkpoint_readiness_20261108.md'
RUN = 'gkt-checkpoint-engineering-20261108-01'
EXPECTED = {'src/knowledge_tracing/gkt/training_checkpoint.py': '5ddfea74c17cddf8f3ba72e60dcde1f2d36c6950ad2b22f7d2d55361ed2a89d8',
            'tests/gkt/test_training_checkpoint.py': '494ea9e719898a5d4c5deda50bc280fa0f2ff8d569b6934b34145281fc0d692e'}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
assert Path(sys.prefix).resolve() == ROOT / '.venv'
assert all(sha(ROOT / n) == h for n, h in EXPECTED.items())
acceptance = read(PREP / 'acceptance.json')
assert sha(PREP / 'acceptance.json') == 'f9e8e0443c97d7acc3db9c7d5bd49a8b1c6e372a1202cf074fc5cf9f8f211971'
assert acceptance['actual_updates'] == 2 and acceptance['max_actual_updates'] == 4
assert acceptance['cumulative_conservative_seconds'] <= 60
review = read(PREP / 'parent_source_review.json')
assert review['source_sha256'] == EXPECTED
raw_review = read(PREP / 'parent-review.json')
assert raw_review['status'] == 'PASS_PARENT_STATIC_AND_RAW_REVIEW_NOT_MODEL_RERUN'
assert raw_review['acceptance_sha256'] == sha(PREP / 'acceptance.json')
assert raw_review['final_tests'] == 40 and raw_review['actual_updates_across_trials'] == 2
pairs = []
current_dependencies = set()
for label, expected_counts, exitcode in [('01', (40, 0, 39, 0), 1), ('02', (40, 0, 0, 0), 0)]:
    d = ROOT / f'artifacts/akt/local-tests/parallel-gkt-checkpoint-20261108-{label}'
    trial = read(d / 'run.json')
    assert trial['exit_code'] == exitcode and trial['resource_accepted'] and trial['sources_unchanged']
    assert trial['source_before'] == trial['source_after']
    for name, h in trial['source_before'].items():
        current_dependencies.add(ROOT / name)
        assert sha(ROOT / name) == h
        assert all(sha(d / (name.replace('/', '__') + '.' + phase)) == h for phase in ('before', 'after'))
    assert all(sha(d / n) == h for n, h in trial['log_sha256'].items())
    suites = list(ET.parse(d / 'pytest.xml').iter('testsuite'))
    counts = tuple(sum(int(s.attrib.get(k, 0)) for s in suites) for k in ('tests', 'failures', 'errors', 'skipped'))
    assert counts == expected_counts
    pairs += [(p, 'trial' + label + '__' + p.name) for p in sorted(d.iterdir()) if p.is_file()]
assert len((PREP / 'actual-optimizer-updates.jsonl').read_text().splitlines()) == 2
for name in ('CONTRACT.md', 'acceptance.json', 'parent_source_review.json', 'link_control.py',
             'actual-optimizer-updates.jsonl', 'pack_evidence.py', 'parent_review.py', 'parent-review.json'):
    pairs.append((PREP / name, name))
for label, status in [('01', 'HARDLINK_FAILED'), ('02', 'HARDLINK_CREATED_EXACT')]:
    p = PREP / f'link-control-{label}/result.json'
    assert read(p)['status'] == status and read(p)['model_optimizer_calls'] == 0
    pairs.append((p, 'control' + label + '__result.json'))
for row in acceptance['selected_metadata']:
    p = ROOT / row['path']
    assert sha(p) == row['sha256'] and p.stat().st_size == row['bytes']
    pairs.append((p, 'successful_checkpoint__' + p.name))
for row in acceptance['selected_binary_inventory_no_copy']:
    p = ROOT / row['path']
    assert sha(p) == row['sha256'] and p.stat().st_size == row['bytes']
assert all('.pt' not in alias and not p.name.endswith('.pt') for p, alias in pairs)
pairs += [(ROOT / n, 'final__' + n.replace('/', '__')) for n in EXPECTED]
pairs += [(REPORT, 'gkt_checkpoint_readiness_20261108.md'),
          (ROOT / 'src/knowledge_tracing/gkt/__init__.py', 'gkt_package_init.py'),
          (ROOT / 'src/knowledge_tracing/evidence.py', 'evidence_helper.py')]
assert len(pairs) == len({alias for _, alias in pairs})
rows = [dict(source=p.relative_to(ROOT).as_posix(), copy=alias, bytes=p.stat().st_size,
             sha256_before_copy=sha(p)) for p, alias in pairs]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('operation', choices=('dry-run', 'close'))
parser.add_argument('--approved-report-sha256')
parser.add_argument('--approved-inventory-sha256')
parser.add_argument('--approval-reference')
args = parser.parse_args()
inventory_path = PREP / 'dry_inventory02.json'
if args.operation == 'dry-run':
    inventory = dict(status='DRY_INPUT_INVENTORY_NOT_CLOSED', run_id=RUN,
        report_sha256=sha(REPORT), source_sha256=EXPECTED, copy_pairs=len(rows), inputs=rows,
        selected_binary_references_not_copied=acceptance['selected_binary_inventory_no_copy'],
        planned_output_count=len(rows) + 6, planned_total_files=len(rows) + 7,
        tests_model_optimizer_reruns=0, closure_authorized=False)
    with inventory_path.open('x', encoding='utf-8') as stream:
        json.dump(inventory, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps(dict(status=inventory['status'], copy_pairs=len(rows),
        planned_outputs=inventory['planned_output_count'], report_sha256=sha(REPORT),
        dry_inventory_sha256=sha(inventory_path), source_sha256=EXPECTED)))
    raise SystemExit(0)
# Invocation only after the parent explicitly approves report + this exact dry inventory.
assert args.approval_reference and args.approval_reference.strip()
assert args.approved_report_sha256 == sha(REPORT)
assert args.approved_inventory_sha256 == sha(inventory_path)
inventory = read(inventory_path)
assert inventory['inputs'] == rows and inventory['report_sha256'] == sha(REPORT)
count = int(os.environ.get('GIT_CONFIG_COUNT', '0'))
os.environ[f'GIT_CONFIG_KEY_{count}'] = 'safe.directory'
os.environ[f'GIT_CONFIG_VALUE_{count}'] = str(ROOT)
os.environ['GIT_CONFIG_COUNT'] = str(count + 1)
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
metadata = dict(kind='GKT_WEIGHTS_ONLY_CHECKPOINT_ENGINEERING_NOT_RESUME', actual_trials=acceptance['trials'],
    actual_optimizer_updates=2, optimizer_limit=4, cumulative_conservative_seconds=acceptance['cumulative_conservative_seconds'],
    cumulative_limit_seconds=60, source_sha256=EXPECTED, approved_report_sha256=sha(REPORT),
    approved_dry_inventory_sha256=sha(inventory_path), closure_approval_reference=args.approval_reference,
    review='Parent actual source/tests/receipts/report/inventory review; no independent reviewer agent claimed',
    checkpoint_resume_fitted_flags=dict(weights_only=True, optimizer_saved=False, rng_saved=False,
        hidden_state_saved=False, resume_supported=False, fitted_research_model=False, completion_unit='train_step'),
    binary_references_not_copied=acceptance['selected_binary_inventory_no_copy'],
    scientific_adoption=False, model_test_optimizer_reruns_during_archive=0)
note = '''# GKT weights-only checkpoint engineering — 08/11/2026

Trial02:40PASS,1new Adam update; trial01:1PASS/39fixtureERROR vì hard-link WinError5,1update. Default/escalated owned-file controls phân biệt execution permission, không source bugfix. Giữ nguyên source/test hai lượt,24 snapshots, raw logs/JUnit/ledgers, contract và successful metadata. Tổng2/4updates, conservative24,609858/60giây. Parent actual review, không dựng independent-agent verdict. Không optimizer/RNG/hidden-state restore/resume/fitted research/epoch/corpus/adapter/S04S05 adoption. Binaries giữ ở artifact paths, bundle chỉ SHA/size references. Không sửa sau closure.
'''
sources = sorted({p for p, _ in pairs} | current_dependencies | {inventory_path})
with record_evidence_run(ROOT, RUN, metadata=metadata, sources=sources, note=note) as directory:
    for p, alias in pairs:
        shutil.copyfile(p, directory / alias)
    after = []
    for row in rows:
        h = sha(directory / row['copy'])
        assert h == row['sha256_before_copy'] == sha(ROOT / row['source'])
        after.append({**row, 'sha256_after_copy': h, 'exact_match': True})
    def write(name, value):
        with (directory / name).open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')
    write('copy_inventory_before.json', rows)
    write('copy_inventory.json', after)
    write('frozen_acceptance.json', {**metadata, 'input_receipt_sha256': sha(PREP / 'acceptance.json')})
    names = {alias for _, alias in pairs} | {'README.md', 'execution.log', 'copy_inventory_before.json',
            'copy_inventory.json', 'frozen_acceptance.json', 'force_add_paths.txt'}
    with (directory / 'force_add_paths.txt').open('x', encoding='utf-8') as stream:
        stream.write(''.join((directory / name).relative_to(ROOT).as_posix() + '\n'
                             for name in sorted(names | {'manifest.json'})))
verified = verify_evidence_bundle(directory)
manifest = read(directory / 'manifest.json')
assert set(manifest['outputs_sha256']) == names
assert {p.name for p in directory.iterdir()} == names | {'manifest.json'}
assert all(sha(ROOT / n) == h for n, h in EXPECTED.items())
for link in re.findall(r'\]\(([^)]+)\)', REPORT.read_text(encoding='utf-8')):
    assert (REPORT.parent / link).resolve().exists(), link
print(json.dumps({**verified, 'manifest_sha256': sha(directory / 'manifest.json'),
    'report_sha256': sha(REPORT), 'copy_pairs': len(rows), 'all_files_including_manifest': len(names) + 1,
    'force_add_list': str(directory / 'force_add_paths.txt')}))
