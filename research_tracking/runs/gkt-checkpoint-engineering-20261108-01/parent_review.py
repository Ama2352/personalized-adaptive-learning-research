"""Parent kiểm actual receipts/XML/SHA, không load model hoặc chạy lại suite."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path.cwd()
base = root / 'artifacts/akt/local-tests'
prep = base / 'gkt04-checkpoint-preparation-20261108-01'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
accept = json.loads((prep / 'acceptance.json').read_text())
for relative, digest in accept['source_sha256'].items():
    assert sha(root / relative) == digest
for trial in accept['trials']:
    directory = base / ('parallel-gkt-checkpoint-20261108-' + trial['label'])
    assert sha(directory / 'run.json') == trial['run_sha256']
    assert sha(directory / 'pytest.xml') == trial['junit_sha256']
    suites = ET.parse(directory / 'pytest.xml').getroot().findall('testsuite')
    counts = {key: sum(int(s.get(key, 0)) for s in suites) for key in ('tests','failures','errors','skipped')}
    assert counts == trial['counts'], counts
    for relative, digest in accept['source_sha256'].items():
        prefix = relative.replace('/', '__')
        assert sha(directory / (prefix + '.before')) == digest
        assert sha(directory / (prefix + '.after')) == digest
    run = json.loads((directory / 'run.json').read_text())
    assert run['exit_code'] == trial['exit_code'] and run['timed_out'] is False
for row in accept['selected_binary_inventory_no_copy']:
    p = root / row['path']
    assert p.stat().st_size == row['bytes'] and sha(p) == row['sha256']
ledger = prep / 'actual-optimizer-updates.jsonl'
assert sha(ledger) == accept['global_update_ledger_sha256']
assert len(ledger.read_text().splitlines()) == accept['actual_updates'] == 2
assert accept['cumulative_conservative_seconds'] < accept['cap_seconds'] == 60
complete = base / 'parallel-gkt-checkpoint-20261108-02/tmp/weights0/completed'
metadata = json.loads((complete / 'metadata.json').read_bytes())
flags = metadata['identity']['flags']
assert flags == dict(optimizer_saved=False,rng_saved=False,hidden_state_saved=False,
    resume_supported=False,fitted_research_model=False,completion_unit='train_step')
manifest = json.loads((complete / 'COMPLETE.json').read_bytes())
for name, row in manifest['files'].items():
    assert sha(complete / name) == row['sha256']
    assert (complete / name).stat().st_size == row['bytes']
assert not (base / 'parallel-gkt-checkpoint-20261108-01/tmp/weights0/completed/COMPLETE.json').exists()
report = dict(status='PASS_PARENT_STATIC_AND_RAW_REVIEW_NOT_MODEL_RERUN',
    acceptance_sha256=sha(prep / 'acceptance.json'),
    review_scope='Đọc source/tests; kiểm raw XML/counts/source snapshots/model binary SHA/COMPLETE+metadata và cumulative ledger.',
    final_tests=40,failed_trial_retained=True,actual_updates_across_trials=2,
    model_loads=0,new_optimizer_updates=0,resume_proven=False,fitted_research_model=False,
    remaining='Weights-only engineering; không epoch/corpus/selectedfit/production adapter hoặc S05 adoption.')
with (prep / 'parent-review.json').open('x',encoding='utf-8') as stream:
    json.dump(report,stream,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False))
