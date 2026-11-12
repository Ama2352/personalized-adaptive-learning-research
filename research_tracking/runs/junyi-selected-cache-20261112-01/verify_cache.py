"""Đối chiếu cache đầy đủ và reader trên cohort kỹ thuật đã có."""
import hashlib
import json
from pathlib import Path
import sys

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.akt.config import DataPaths
from knowledge_tracing.akt.data import iter_development_learners

BUNDLE = Path(__file__).parent
cache = ROOT/'artifacts/akt/junyi-cohorts/outer4-selected-full-20261112-03'
manifest = json.loads((cache/'manifest.json').read_text())
assert manifest['status']=='FULL_TRAIN_SELECTION_CACHE_VERIFIED_NOT_TRAINED'
for name,entry in manifest['outputs'].items():
    with (cache/name).open('rb') as stream:
        assert hashlib.file_digest(stream,'sha256').hexdigest()==entry['sha256']
cohort = json.loads((ROOT/'artifacts/akt/junyi-cohorts/cuda-engineering320x300-20261112-01/manifest.json').read_text())
users = tuple(sorted(cohort['roles']['train']['users']+cohort['roles']['selection']['users']))
original = DataPaths(ROOT/'artifacts/bkt_baseline/derived/canonical',
    ROOT/'artifacts/bkt_baseline/splits/assignments.parquet',
    ROOT/'artifacts/bkt_baseline/derived/manifest.json',ROOT/'artifacts/bkt_baseline/splits/manifest.json')
cached = DataPaths(cache/'canonical.parquet',cache/'assignments.parquet',original.canonical_manifest,original.split_manifest)
before = tuple(iter_development_learners(original,user_ids=users,allowed_folds=(0,1,2,3),preserve_user_order=True))
after = tuple(iter_development_learners(cached,user_ids=users,allowed_folds=(0,1,2,3),preserve_user_order=True))
assert before==after
roles = json.loads((ROOT/'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01/roles.json').read_text())
role_frame = pd.DataFrame([(user,role) for role in ('train','selection') for user in roles[role+'_users']],
                          columns=['user_id','role'])
with duckdb.connect(config=dict(memory_limit='256MB',threads='1',temp_directory='')) as con:
    con.register('roles',role_frame)
    support = con.execute("""SELECT c.exercise,COUNT(DISTINCT c.user_id) learners
        FROM read_parquet(?) c JOIN roles r ON c.user_id=r.user_id
        WHERE r.role='train' GROUP BY c.exercise ORDER BY c.exercise""",[str(cache/'canonical.parquet')]).df()
    con.register('train_exercises',support[['exercise']])
    coverage = con.execute("""SELECT COUNT(*) total,COUNT(v.exercise) supported
        FROM read_parquet(?) c JOIN roles r ON c.user_id=r.user_id
        LEFT JOIN train_exercises v ON c.exercise=v.exercise
        WHERE r.role='selection'""",[str(cache/'canonical.parquet')]).fetchone()
support.to_csv(BUNDLE/'train-exercise-support.csv',index=False)
result = dict(status='VERIFIED_FULL_CACHE_AND_NATIVE_READER_EQUIVALENCE',
    cache=str(cache.relative_to(ROOT)).replace('\\','/'),counts=manifest['counts'],
    exact_reader_learners=len(before),exact_reader_events=sum(len(x.events) for x in before),
    vocabulary_exercises=len(support),selection_targets=coverage[0],selection_supported=coverage[1],
    selection_oov=coverage[0]-coverage[1],full_training_performed=False,
    limits='Reader equality kiểm288learner. Counts/SHA toàncache; khôngclaim đãfitmodel hoặc fullNN validation.')
(BUNDLE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
