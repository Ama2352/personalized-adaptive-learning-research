"""Đọc receipt/JUnit/snapshots; không thực thi lại publisher hoặc tests."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from run_pure import FILES, PREP, ROOT, dump, sha

trial=PREP/'trial01'
run=json.loads((trial/'run.json').read_bytes())
suite=ET.parse(trial/'pytest.xml').getroot().find('testsuite')
counts={k:int(suite.attrib[k]) for k in ('tests','failures','errors','skipped')}
assert counts==dict(tests=31,failures=0,errors=0,skipped=0)
assert run['returncode']==0 and not run['timed_out'] and run['sources_unchanged']
assert run['before']==run['after'] and run['cumulative_seconds']<=30
for name,row in run['before'].items():
    assert sha(trial/'source-before'/name.replace('/','__'))==row['sha256']
    assert sha(ROOT/name)==row['sha256']
before=json.loads((PREP/'roundtrip-amendment-before.json').read_text(encoding='utf-8-sig'))
assert sha(ROOT/before['snapshot'])==before['sha256_before_copy']==before['sha256_after_copy']
proof=dict(status='VERIFIED_SYNTHETIC_TMPFS_PUBLISHER_ENGINEERING_NOT_ACTUAL_CORPUS',
    junit_counts=counts,junit_seconds=float(suite.attrib['time']),controller_seconds=run['controller_seconds'],
    cumulative_seconds=run['cumulative_seconds'],budget_seconds=30,input_sources=run['before'],
    source_snapshot_copy_verified=len(run['before']),pretest_schema_snapshot_verified=True,
    fixture_development_learners=10,fixture_events_per_learner=84,
    actual_teacher_or_collector_calls=0,model_calls=0,optimizer_steps=0,remote_calls=0,
    actual_project_corpus_publications=0,
    limitations_vi='Fixture source/protocol/semantics là metadata dựng tay. Reader integration chỉ _corpus, không native preflight/Gate/runtime/authorization. Không corpus diversity, fitted model, actual collection hoặc hard crash transaction.')
dump(PREP/'final-verification.json',proof)
print(json.dumps({k:v for k,v in proof.items() if k!='input_sources'}))
