"""Đếm quy mô train/selection Junyi từ ID, không đọc correctness hoặc Holdout."""
import hashlib
import json
from pathlib import Path
import time

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).parent
roles_path = ROOT/'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01/roles.json'
roles = json.loads(roles_path.read_text())
selected = pd.DataFrame([(user, role) for role in ('train', 'selection')
                         for user in roles[role+'_users']], columns=['user_id','role'])
temp = ROOT/'artifacts/akt/tmp/junyi-population-count-20261112-01'
temp.mkdir(parents=True, exist_ok=False)
started = time.monotonic()
con = duckdb.connect(config=dict(memory_limit='256MB', threads='1', temp_directory=str(temp)))
try:
    con.register('requested_development_roles', selected)
    rows = con.execute("""
        SELECT role, COUNT(*) learners, SUM(n) targets, MIN(n) minimum_events,
               MAX(n) maximum_events, SUM(CEIL(n/100.0)) minimum_windows_without_oov
        FROM (SELECT r.role,c.user_id,COUNT(*) n
              FROM read_parquet(?,hive_partitioning=true) c
              JOIN requested_development_roles r ON c.user_id=r.user_id
              GROUP BY r.role,c.user_id)
        GROUP BY role ORDER BY role
    """, [str(ROOT/'artifacts/bkt_baseline/derived/canonical/**/*.parquet')]).df().to_dict('records')
finally:
    con.close()
result = dict(status='DEVELOPMENT_TRAIN_SELECTION_TARGET_COUNTS', counts=rows,
    roles_sha256=hashlib.sha256(roles_path.read_bytes()).hexdigest(),
    projected_canonical_columns=['user_id'], correctness_read=False, calibration_events_read=False,
    holdout_events_read=False, training_performed=False, elapsed_seconds=time.monotonic()-started,
    limitation='Windows là cận dưới trước OOV barriers; chưa đo throughput fullJunyi.')
with (BUNDLE/'development-population-counts.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
print(json.dumps(result, ensure_ascii=False))
