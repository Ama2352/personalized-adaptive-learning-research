"""GKT06 dry inventory; explicit exact-report/inventory approval required to close."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = Path.cwd().resolve(); PREP = Path(__file__).resolve().parent
REPORT = ROOT / 'research_tracking/reports/gkt_epoch_pipeline_readiness_20261108.md'
RUN = 'gkt-epoch-pipeline-engineering-20261108-01'
MODEL = PREP.parent / 'parallel-gkt-pipeline-20261108-model01'; OUTPUT = MODEL / 'output'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
EXPECTED = read(PREP / 'pre_update_freeze.json')['source_sha256']
assert Path(sys.prefix).resolve() == ROOT / '.venv'
assert all(sha(ROOT / n) == h for n, h in EXPECTED.items())
assert sha(PREP / 'acceptance.json') == '9f99136cfe1ba4cd6bf9cdedb177ce15b70c7fc0e23939e646cb5451600cf3e7'
acceptance = read(PREP / 'acceptance.json'); budget = read(PREP / 'budget.json')
review = read(PREP / 'parent-review.json')
assert review['status'] == 'PASS_PARENT_SOURCE_AND_RAW_GKT06_REVIEW'
assert review['acceptance_sha256'] == sha(PREP / 'acceptance.json')
assert review['optimizer_reservations'] == review['optimizer_body_returns'] == review['complete_batches'] == 2
assert budget['actual_controller_seconds'] + budget['reserved_static_seconds'] <= 60
assert budget['optimizer_updates'] == 2 and len(budget['attempts']) == 2
pairs = []; dependencies = set(); sources = []
for phase in ('pure01', 'model01'):
    d = PREP.parent / ('parallel-gkt-pipeline-20261108-' + phase); receipt = read(d / 'run.json')
    assert receipt['returncode'] == 0 and receipt['resource_accepted'] and not receipt['timeout']
    assert receipt['source_before'] == receipt['source_after'] and len(receipt['source_before']) == 13
    sources.append(receipt['source_before'])
    for name, h in receipt['source_before'].items():
        dependencies.add(ROOT / name); assert sha(ROOT / name) == h
        assert all(sha(d / (name.replace('/', '__') + '.' + suffix)) == h for suffix in ('before', 'after'))
    if phase == 'pure01':
        suites = list(ET.parse(d / 'pytest.xml').iter('testsuite'))
        counts = {k: sum(int(s.attrib.get(k, 0)) for s in suites) for k in ('tests', 'failures', 'errors', 'skipped')}
        assert counts == dict(tests=38, failures=0, errors=0, skipped=0)
        assert receipt['reserved_updates'] == receipt['returned_updates'] == 0
    else:
        assert receipt['reserved_updates'] == receipt['returned_updates'] == 2
    pairs += [(p, phase + '__' + p.name) for p in sorted(d.iterdir()) if p.is_file()]
assert sources[0] == sources[1]
freeze = read(PREP / 'pre_update_freeze.json')
assert all(sha(PREP / n) == h for n, h in freeze['helper_sha256'].items())
assert all(sha(ROOT / n) == h for n, h in acceptance['raw_hashes'].items())
actual = read(MODEL / 'result.json'); manifest = read(OUTPUT / 'run.json'); marker = read(OUTPUT / 'COMPLETE.json')
assert actual['completed_epochs'] == actual['optimizer_step_returns'] == actual['optimizer_step_started'] == 2
assert actual['caller_flags_and_rng_preserved'] and actual['owned_step_hooks_removed']
assert actual['max_optimizer_parameter_step'] == 2 and actual['parameter_delta_present']
assert marker['run_manifest_sha256'] == actual['run_manifest_sha256'] == sha(OUTPUT / 'run.json')
assert marker['selected_prediction_sha256'] == actual['selected_prediction_sha256'] == sha(OUTPUT / 'selected_predictions.csv')
assert not (OUTPUT / 'failure.json').exists()
events = [json.loads(line) for line in (OUTPUT / 'optimizer_events.jsonl').read_text().splitlines()]
assert [x['event'] for x in events] == ['step_started', 'step_returned', 'step_started', 'step_returned']
assert manifest['optimizer_counters'] == dict(started_steps=2, returned_steps=2, started_targets=12, returned_targets=12)
binaries = []
for epoch in (1, 2):
    d = OUTPUT / f'epoch-{epoch:03d}'; receipt = read(d / 'epoch.json'); cpdir = d / 'weights'
    assert receipt['complete_epoch'] and receipt['optimizer_steps'] == 1
    assert sorted(receipt['optimized_source_rows']) == [1, 2, 3, 11, 12, 13]
    complete = read(cpdir / 'COMPLETE.json')
    for n, row in complete['files'].items():
        assert sha(cpdir / n) == row['sha256'] and (cpdir / n).stat().st_size == row['bytes']
    with (d / 'selection.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert [int(r['source_row']) for r in rows] == [101, 102, 103, 104]
    assert [int(r['global_rank']) for r in rows] == [0, 1, 2, 3]
    assert [r['support_reason'] for r in rows] == ['cold_query_only', 'known_history', 'oov_item', 'unsupported_history']
    assert sum(r['probability'] != '' for r in rows) == 2 and all(r['research_fitted'] == 'False' for r in rows)
    assert all(r['checkpoint_manifest_sha256'] == receipt['checkpoint_manifest_sha256'] for r in rows)
    assert sha(d / 'selection.csv') == receipt['selection_csv_sha256']
    p = cpdir / 'weights.pt'
    binaries.append(dict(path=p.relative_to(ROOT).as_posix(), bytes=p.stat().st_size, sha256=sha(p)))
assert manifest['selected_epoch'] == review['selected_epoch'] == 2
assert (OUTPUT / 'selected_predictions.csv').read_bytes() == (OUTPUT / 'epoch-002/selection.csv').read_bytes()
assert manifest['training_mapping_usage_verified'] and manifest['fitted_research_model'] is False
assert manifest['adapter_mapping_provenance'] == 'caller_declared_inference_mapping_NOT_training_attested'
for used in manifest['mapping_usage']:
    assert used['completed']['optimizer_steps'] == 1
    assert used['prepared']['mapping_sha256'] == manifest['training_encoding']['mapping_sha256']
    assert len(used['prepared']['source_rows']) == len(used['prepared']['mapped_node_indices']) == 6
for p in sorted(OUTPUT.rglob('*')):
    if p.is_file() and p.suffix != '.pt':
        assert not p.is_symlink() and p.suffix in ('.json', '.jsonl', '.csv', '.pending')
        pairs.append((p, 'output__' + p.relative_to(OUTPUT).as_posix().replace('/', '__')))
for name in ('acceptance.json', 'budget.json', 'pre_update_contract.json', 'pre_update_freeze.json',
             'run_targeted.py', 'model_phase.py', 'parent_review.py', 'parent-review.json', 'pack_evidence.py'):
    pairs.append((PREP / name, name))
pairs += [(ROOT / name, 'final__' + name.replace('/', '__')) for name in EXPECTED]
pairs += [(REPORT, 'gkt_epoch_pipeline_readiness_20261108.md'),
          (ROOT / 'src/knowledge_tracing/evidence.py', 'evidence_helper.py')]
assert len(pairs) == len({alias for _, alias in pairs}) and all(not p.name.endswith('.pt') for p, _ in pairs)
rows = [dict(source=p.relative_to(ROOT).as_posix(), copy=alias, bytes=p.stat().st_size,
             sha256_before_copy=sha(p)) for p, alias in pairs]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('operation', choices=('dry-run', 'close'))
parser.add_argument('--approved-report-sha256'); parser.add_argument('--approved-inventory-sha256')
parser.add_argument('--approval-reference')
args = parser.parse_args(); inventory_path = PREP / 'dry_inventory.json'
if args.operation == 'dry-run':
    inventory = dict(status='DRY_INPUT_INVENTORY_NOT_CLOSED', run_id=RUN, report_sha256=sha(REPORT),
        source_sha256=EXPECTED, copy_pairs=len(rows), inputs=rows, binary_references_not_copied=binaries,
        planned_outputs=len(rows) + 6, planned_total_files=len(rows) + 7, model_test_optimizer_reruns=0,
        closure_authorized=False)
    with inventory_path.open('x', encoding='utf-8') as stream:
        json.dump(inventory, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps(dict(status=inventory['status'], copy_pairs=len(rows), planned_outputs=len(rows) + 6,
        report_sha256=sha(REPORT), dry_inventory_sha256=sha(inventory_path), source_sha256=EXPECTED)))
    raise SystemExit(0)
assert args.approval_reference and args.approval_reference.strip()
assert args.approved_report_sha256 == sha(REPORT) and args.approved_inventory_sha256 == sha(inventory_path)
assert read(inventory_path)['inputs'] == rows and read(inventory_path)['binary_references_not_copied'] == binaries
count = int(os.environ.get('GIT_CONFIG_COUNT', '0'))
os.environ[f'GIT_CONFIG_KEY_{count}'] = 'safe.directory'; os.environ[f'GIT_CONFIG_VALUE_{count}'] = str(ROOT)
os.environ['GIT_CONFIG_COUNT'] = str(count + 1)
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
metadata = dict(kind='GKT_ROLE_BOUND_EPOCH_PIPELINE_ENGINEERING_NOT_RESEARCH_FIT', pure_tests=38,
    actual_completed_epochs=2, optimizer_reservations=2, optimizer_body_returns=2, complete_gkt_batches=2,
    train_targets_each_epoch=6, selection_population=actual['selection_population'], selected_epoch=2,
    favorable_metric_improvement_required=False, actual_failed_trials=[],
    cumulative_conservative_seconds=acceptance['cumulative_conservative_seconds'], cumulative_cap_seconds=60,
    source_sha256=EXPECTED, approved_report_sha256=sha(REPORT), approved_inventory_sha256=sha(inventory_path),
    closure_approval_reference=args.approval_reference, parent_review_sha256=sha(PREP / 'parent-review.json'),
    review='Parent actual source/raw review; no independent reviewer agent claimed',
    mapping_usage_verified=True, semantic_mapping_attested=False,
    initialization_provenance=manifest['initialization_provenance'],
    binary_references_not_copied=binaries, resume_supported=False, fitted_research_model=False,
    scientific_S04_S05_adoption=False, model_test_optimizer_reruns_during_archive=0)
note = '''# GKT role-bound epoch pipeline engineering — 08/11/2026

38 pure cases trước parent review, sau đó một actual2epoch toy run:2reservations/2Adam body returns/2complete GKT batches,6train targets mỗi epoch; selection4=2scored+2unsupported/0research_fitted. Selected epoch2 là criterion fixture explicit, không positive efficacy acceptance. Cumulative conservative31,254267/60s.52source snapshots, exact fullCSV/checkpoint metadata/run/event lineage;2model binaries chỉ SHA references tại output gốc. Mapping usage mechanical verified, semantic map/initial fitted origin không attested. Không corpus/final scientific fit/refit/resume/OnlineSession/S04S05 adoption. Parent actual review, không invented independent-agent verdict/failure. Copy/hash only; không sửa sau closure.
'''
guard_sources = sorted({p for p, _ in pairs} | dependencies | {inventory_path} | {ROOT / x['path'] for x in binaries})
with record_evidence_run(ROOT, RUN, metadata=metadata, sources=guard_sources, note=note) as directory:
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
        stream.write(''.join((directory / n).relative_to(ROOT).as_posix() + '\n' for n in sorted(names | {'manifest.json'})))
verified = verify_evidence_bundle(directory)
assert set(read(directory / 'manifest.json')['outputs_sha256']) == names
assert {p.name for p in directory.iterdir()} == names | {'manifest.json'}
assert all(sha(ROOT / n) == h for n, h in EXPECTED.items())
for link in re.findall(r'\]\(([^)]+)\)', REPORT.read_text(encoding='utf-8')):
    assert (REPORT.parent / link).resolve().exists(), link
print(json.dumps({**verified, 'manifest_sha256': sha(directory / 'manifest.json'), 'report_sha256': sha(REPORT),
    'copy_pairs': len(rows), 'all_files_including_manifest': len(names) + 1,
    'force_add_list': str(directory / 'force_add_paths.txt')}))
