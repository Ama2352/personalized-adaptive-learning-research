"""Hậu kiểm toàn population JUnit bị fail, không giả native report PASS hoặc rerun."""
from collections import Counter
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
packet_path = PREP/'windows_current_gate_packet02.ROOT.json'
raw = packet_path.read_bytes()
assert hashlib.sha256(raw).hexdigest() == 'd9adeadd0904d29c0c40781bb1ad942493d637e0093ae74eacbc460131ca40c8'
packet = json.loads(raw)
groups = []
total = dict(tests=0,failures=0,errors=0,skipped=0)
for name in ('stdlib','no-torch','remaining'):
    path = ROOT/f'artifacts/akt/preflight/gate2-tests-win-current-gate-20261109-02-{name}.xml'
    blob = path.read_bytes()
    tree = ET.fromstring(blob)
    cases = list(tree.iter('testcase'))
    actual = [(case.get('classname'),case.get('name')) for case in cases]
    expected = [(case['classname'],case['name']) for case in packet['expected_JUnit_ids'][name]]
    assert len(actual) == len(set(actual)) and Counter(actual) == Counter(expected)
    counts = {k:sum(int(s.get(k,'0')) for s in tree.iter('testsuite')) for k in total}
    assert counts['tests'] == len(cases)
    failures = [dict(classname=c.get('classname'),name=c.get('name'),outcome=tag)
                for c in cases for tag in ('failure','error','skipped') if c.find(tag) is not None]
    assert {tag:sum(f['outcome']==tag for f in failures) for tag in ('failure','error','skipped')} == {
        'failure':counts['failures'],'error':counts['errors'],'skipped':counts['skipped']}
    for key in total:
        total[key] += counts[key]
    groups.append(dict(group=name,counts=counts,exact_expected_identities=True,
                       failures=failures,xml_sha256=hashlib.sha256(blob).hexdigest()))
assert total == dict(tests=1418,failures=3,errors=0,skipped=0)
result = dict(status='COMPLETE_TEST_POPULATION_WITH_FAILURES_NOT_GATE_PASS',
              total=total,passed=1415,groups=groups,merged_native_junit_created=False,
              scope_vi='Hậu kiểm3JUnitgroups có sẵn; không chạy tests, không tạo native PASS hoặc mergedXML giả.')
with (PREP/'windows_current_gate02_population_postmortem.json').open('x',encoding='utf-8') as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
state_path = ROOT/'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = json.loads(state_path.read_text(encoding='utf-8'))
native = state['engineering_checkpoint_20261109']['native_gate02']
native.update(last_verified_state='TERMINAL_REJECTED_COMPLETE_POPULATION_3_FAILURES',
              terminal_exit_code=1,seconds=291.5909478000249,counts=total,passed=1415,
              failure_population_proof='artifacts/akt/local-tests/akt-research-runner-20261108-01/windows_current_gate02_population_postmortem.json',
              notes_vi='Ba DuckDB COPY paths dài262/264 ký tự; parent tồn tại. Đang sửa scratchlayout, không tự replay cùngsource.')
state['current_next_step_20261109'] = 'No live sessions. Close/commit SAKT31 and cachedRQ1source-controller evidence; validate revised Gate scratch path fix then freshfreeze/collection before anynew fullGate. HTML09candidate needsvisualQA+closebrowser. NoModal/Holdout/fullCV.'
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=result['status'],total=total,passed=1415)))
