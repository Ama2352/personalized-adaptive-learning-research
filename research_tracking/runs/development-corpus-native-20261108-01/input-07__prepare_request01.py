"""Freeze request bằng source bytes; không import collector hoặc sinh dữ liệu."""
import hashlib
import importlib.util
import json
from pathlib import Path

root=Path.cwd()
spec=importlib.util.spec_from_file_location('reviewed_corpus_metadata',root/'scripts/research/collect_development_corpus.py')
driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
request=dict(schema_version=1,purpose='first_development_corpus_lifecycle_pilot',
 approval_reference='root-reviewed-local-corpus01-12600-attempts-cumulative120-20261108',
 config_sha256=driver.CONFIG_SHA,plan_sha256=driver.PLAN_SHA,
 collection_sources={name:sha(root/name) for name in driver.COLLECTION_SOURCES},
 extra_sources={name:sha(root/name) for name in driver.EXTRA_SOURCES},
 output_relative='artifacts/akt/local-tests/development-corpus-20261108-01/native01')
relative='artifacts/akt/local-tests/development-corpus-20261108-01/request01.json'
with (root/relative).open('x',encoding='utf-8') as stream:
 json.dump(request,stream,ensure_ascii=False,indent=2);stream.write('\n')
expected=sha(root/relative)
verified,config=driver.validate_request(relative,expected)
assert verified==request and config['expected_events']['total']==12600
receipt=dict(status='METADATA_REQUEST_FROZEN_NOT_DISPATCHED',request_relative=relative,request_sha256=expected,
 source_sha256={**request['collection_sources'],**request['extra_sources']},
 planned_teacher_attempts=12600,actual_teacher_calls=0,final_events=0,neural_calls=0)
with (root/'artifacts/akt/local-tests/development-corpus-20261108-01/request01_metadata_check.json').open('x',encoding='utf-8') as stream:
 json.dump(receipt,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='source_sha256'}))
