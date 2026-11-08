"""GKT05 dry inventory then explicit parent-approved closure; no model/test rerun."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = Path.cwd().resolve(); PREP = Path(__file__).resolve().parent
REPORT = ROOT / 'research_tracking/reports/gkt_adapter_readiness_20261108.md'
RUN = 'gkt-inference-adapter-engineering-20261108-01'
OLD_BUNDLE = ROOT / 'research_tracking/runs/gkt-checkpoint-engineering-20261108-01'
EXPECTED = {'src/knowledge_tracing/gkt/adapter.py': '2e6c4ed64433dac63f54344710303cf0908b0c66cc63735a71f3f6d23f42c0f4',
            'tests/gkt/test_adapter.py': '08b7dccd4b66278d47bf5508768d2bdb9cc3cacb92290c0acbbbffd56c947ba7'}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
assert Path(sys.prefix).resolve() == ROOT / '.venv'
assert all(sha(ROOT / n) == h for n, h in EXPECTED.items())
assert sha(PREP / 'acceptance.json') == '9f585832e32dc31950db7aeeddfa691158434d019499ca84c2bad6f5a3a95ccf'
acceptance = read(PREP / 'acceptance.json'); budget = read(PREP / 'budget.json')
assert budget['actual_controller_seconds'] + budget['reserved_pretest_static_seconds'] <= 60
assert acceptance['optimizer_updates'] == budget['optimizer_steps'] == 0
review = read(PREP / 'parent-review.json')
assert review['status'] == 'PASS_PARENT_SOURCE_AND_RAW_GKT05_REVIEW'
assert review['acceptance_sha256'] == sha(PREP / 'acceptance.json') and review['unit_cases'] == 32
pairs = []; dependencies = set(); trials = {}
for label in ('unit01', 'integration01'):
    directory = ROOT / ('artifacts/akt/local-tests/parallel-gkt-adapter-20261108-' + label)
    trial = read(directory / 'run.json'); trials[label] = trial
    assert trial['returncode'] == 0 and trial['resource_accepted'] and not trial['timeout'] and trial['optimizer_steps'] == 0
    assert trial['source_before'] == trial['source_after'] and trial['sources_unchanged']
    assert len(trial['source_before']) == 10
    for name, h in trial['source_before'].items():
        dependencies.add(ROOT / name)
        assert sha(ROOT / name) == h
        assert all(sha(directory / (name.replace('/', '__') + '.' + phase)) == h for phase in ('before', 'after'))
    if label == 'unit01':
        suites = list(ET.parse(directory / 'pytest.xml').iter('testsuite'))
        counts = {k: sum(int(s.attrib.get(k, 0)) for s in suites) for k in ('tests', 'failures', 'errors', 'skipped')}
        assert counts == dict(tests=32, failures=0, errors=0, skipped=0)
        assert sha(directory / 'run.json') == acceptance['unit']['run_sha256']
        assert sha(directory / 'pytest.xml') == acceptance['unit']['junit_sha256']
    else:
        assert sha(directory / 'run.json') == acceptance['actual_integration']['run_sha256']
        assert sha(directory / 'result.json') == acceptance['actual_integration']['result_sha256']
        actual = read(directory / 'result.json')
        assert actual['actual_torch_loads'] == 1 and actual['mock_loads'] == actual['optimizer_steps'] == 0
        assert actual['target_population'] == review['target_population'] == acceptance['actual_integration']['target_population']
        assert (actual['target_population']['expected_targets'], actual['target_population']['scored_targets'],
                actual['target_population']['unsupported_targets'], actual['target_population']['research_fitted_targets']) == (6, 2, 4, 0)
        assert [s['global_rank'] for s in actual['scores']] == list(range(6))
        assert all(sha(ROOT / n) == h for n, h in actual['input_sha256'].items())
        assert actual['inputs_unchanged'] and actual['fitted_online_promotion_rejected']
    pairs += [(p, label + '__' + p.name) for p in sorted(directory.iterdir()) if p.is_file()]
assert trials['unit01']['source_before'] == trials['integration01']['source_before']
assert all(sha(PREP / name) == h for name, h in acceptance['source_helpers_current_sha256'].items())
for name in ('acceptance.json', 'budget.json', 'run_targeted.py', 'actual_stored_integration.py',
             'parent_review.py', 'parent-review.json', 'pack_evidence.py'):
    pairs.append((PREP / name, name))
assert sha(OLD_BUNDLE / 'manifest.json') == '0e0f0a19e466fd9c334e7fc279a1ebe4669babd0c2b8dd000542c009207b4cac'
old_manifest = read(OLD_BUNDLE / 'manifest.json')
for name in ('manifest.json', 'acceptance.json', 'successful_checkpoint__metadata.json', 'successful_checkpoint__COMPLETE.json'):
    p = OLD_BUNDLE / name
    if name != 'manifest.json':
        assert sha(p) == old_manifest['outputs_sha256'][name]
    pairs.append((p, 'input_GKT04__' + name))
pairs += [(ROOT / name, 'final__' + name.replace('/', '__')) for name in EXPECTED]
pairs += [(REPORT, 'gkt_adapter_readiness_20261108.md'),
          (ROOT / 'src/knowledge_tracing/evidence.py', 'evidence_helper.py')]
assert len(pairs) == len({alias for _, alias in pairs})
assert all(not p.name.endswith('.pt') for p, _ in pairs)
rows = [dict(source=p.relative_to(ROOT).as_posix(), copy=alias, bytes=p.stat().st_size,
             sha256_before_copy=sha(p)) for p, alias in pairs]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('operation', choices=('dry-run', 'close'))
parser.add_argument('--approved-report-sha256'); parser.add_argument('--approved-inventory-sha256')
parser.add_argument('--approval-reference')
args = parser.parse_args(); inventory_path = PREP / 'dry_inventory.json'
if args.operation == 'dry-run':
    inventory = dict(status='DRY_INPUT_INVENTORY_NOT_CLOSED', run_id=RUN, report_sha256=sha(REPORT),
        source_sha256=EXPECTED, copy_pairs=len(rows), inputs=rows, exact_actual_input_hashes=actual['input_sha256'],
        binary_copied=False, planned_output_count=len(rows) + 6, planned_total_files=len(rows) + 7,
        tests_model_optimizer_reruns=0, closure_authorized=False)
    with inventory_path.open('x', encoding='utf-8') as stream:
        json.dump(inventory, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps(dict(status=inventory['status'], copy_pairs=len(rows), planned_outputs=len(rows) + 6,
        report_sha256=sha(REPORT), dry_inventory_sha256=sha(inventory_path), source_sha256=EXPECTED)))
    raise SystemExit(0)
assert args.approval_reference and args.approval_reference.strip()
assert args.approved_report_sha256 == sha(REPORT) and args.approved_inventory_sha256 == sha(inventory_path)
assert read(inventory_path)['inputs'] == rows
count = int(os.environ.get('GIT_CONFIG_COUNT', '0'))
os.environ[f'GIT_CONFIG_KEY_{count}'] = 'safe.directory'; os.environ[f'GIT_CONFIG_VALUE_{count}'] = str(ROOT)
os.environ['GIT_CONFIG_COUNT'] = str(count + 1)
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
metadata = dict(kind='GKT_FROZEN_INFERENCE_ENGINEERING_NOT_FITTED_SESSION',
    unit_tests=32, unit_role='unverified_fixture', default_unit_untracked_binary_dependency=False,
    actual_stored_checkpoint_loads=1, actual_integration_role='synthetic_trained_engineering_only',
    target_population=actual['target_population'], optimizer_updates=0,
    cumulative_conservative_seconds=acceptance['cumulative_conservative_seconds'], cumulative_cap_seconds=60,
    source_sha256=EXPECTED, approved_report_sha256=sha(REPORT), approved_inventory_sha256=sha(inventory_path),
    closure_approval_reference=args.approval_reference, parent_review_sha256=sha(PREP / 'parent-review.json'),
    review='Parent actual source/raw receipt review; no independent reviewer agent claimed',
    mapping_provenance='caller_declared_inference_mapping_NOT_training_attested',
    score_kind='uncalibrated_node_response_probability', fitted_online_promotion=False,
    checkpoint_binary_copied=False, exact_actual_input_hashes=actual['input_sha256'],
    scientific_S04_S05_adoption=False, model_test_optimizer_reruns_during_archive=0)
note = '''# GKT frozen engineering inference adapter — 08/11/2026

32 portable mock unit cases giữ unverified_fixture, tách một actual stored GKT04 checkpoint load. Integration6targets=2scored+4unsupported/0research_fitted,0optimizer; conservative51,662743/60giây. Giữ40source before/after snapshots và exact input lineage; model binary chỉ SHA reference tại artifact gốc. Mapping caller-declared NOT train-attested, full-prefix/cold/OOVunsupported_history explicit, không fitted OnlineSession hoặc final baseline/S04S05 promotion. Parent actual review; không fabricated independent-agent PASS. Pack chỉ copy/hash, không rerun model/tests. Không sửa sau closure.
'''
sources = sorted({p for p, _ in pairs} | dependencies | {inventory_path} | {ROOT / n for n in actual['input_sha256']})
with record_evidence_run(ROOT, RUN, metadata=metadata, sources=sources, note=note) as directory:
    for p, alias in pairs:
        shutil.copyfile(p, directory / alias)
    after = []
    for row in rows:
        h = sha(directory / row['copy']); assert h == row['sha256_before_copy'] == sha(ROOT / row['source'])
        after.append({**row, 'sha256_after_copy': h, 'exact_match': True})
    def write(name, value):
        with (directory / name).open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')
    write('copy_inventory_before.json', rows); write('copy_inventory.json', after)
    write('frozen_acceptance.json', {**metadata, 'input_acceptance_sha256': sha(PREP / 'acceptance.json')})
    names = {alias for _, alias in pairs} | {'README.md', 'execution.log', 'copy_inventory_before.json',
            'copy_inventory.json', 'frozen_acceptance.json', 'force_add_paths.txt'}
    with (directory / 'force_add_paths.txt').open('x', encoding='utf-8') as stream:
        stream.write(''.join((directory / name).relative_to(ROOT).as_posix() + '\n' for name in sorted(names | {'manifest.json'})))
verified = verify_evidence_bundle(directory)
assert set(read(directory / 'manifest.json')['outputs_sha256']) == names
assert {p.name for p in directory.iterdir()} == names | {'manifest.json'}
assert all(sha(ROOT / n) == h for n, h in EXPECTED.items())
for link in re.findall(r'\]\(([^)]+)\)', REPORT.read_text(encoding='utf-8')):
    assert (REPORT.parent / link).resolve().exists(), link
print(json.dumps({**verified, 'manifest_sha256': sha(directory / 'manifest.json'), 'report_sha256': sha(REPORT),
    'copy_pairs': len(rows), 'all_files_including_manifest': len(names) + 1,
    'force_add_list': str(directory / 'force_add_paths.txt')}))
