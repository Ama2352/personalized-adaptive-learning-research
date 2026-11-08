"""Đối chiếu JUnit, nguồn trước/sau và snapshot; không chạy lại test/model."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from run_boundary import FILES, PREP, ROOT, dump, snapshot

after = snapshot(PREP / 'after')
initial = json.loads((PREP / 'before/inventory.json').read_text(encoding='utf-8'))
trials = []
for name, expected_tests, expected_failures in [('trial01-red', 4, 4), ('trial02-green', 67, 0)]:
    folder = PREP / name
    run = json.loads((folder / 'run.json').read_text(encoding='utf-8'))
    suite = ET.parse(folder / 'pytest.xml').getroot().find('testsuite')
    counts = {key: int(suite.attrib[key]) for key in ('tests', 'failures', 'errors', 'skipped')}
    assert counts == dict(tests=expected_tests, failures=expected_failures, errors=0, skipped=0)
    assert run['sources_unchanged'] and run['source_before'] == run['source_after']
    for path, metadata in run['source_before'].items():
        payload = (folder / 'source-before' / path.replace('/', '__')).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == metadata['sha256']
    trials.append(dict(trial=name, counts=counts, junit_seconds=float(suite.attrib['time']),
                       controller_seconds=run['controller_seconds'], returncode=run['returncode']))
for name in FILES[2:]:
    assert initial[name] == after[name]
assert after == json.loads((PREP/'trial02-green/run.json').read_text())['source_after']
cumulative = sum(t['controller_seconds'] for t in trials)
assert cumulative <= 30
receipt = dict(status='VERIFIED_LOCAL_SYNTHETIC_BOUNDARY_RED_GREEN_NOT_RESEARCH_EVALUATION',
    trials=trials, cumulative_controller_seconds=cumulative, budget_seconds=30,
    source_before=initial, source_after=after,
    changed_paths=[p for p in FILES if initial[p] != after[p]],
    preserved_controller_and_bridge_and_protocol=True, neural_network_calls=0,
    optimizer_steps=0, remote_calls=0,
    limits_vi='Fixture scalar tổng hợp; không attestation nguồn train/refit/partition thực tế, không corpus hay RQ hoàn tất.')
dump(PREP/'final-verification.json', receipt)
print(json.dumps(dict(status=receipt['status'], trials=trials, cumulative_seconds=cumulative)))
