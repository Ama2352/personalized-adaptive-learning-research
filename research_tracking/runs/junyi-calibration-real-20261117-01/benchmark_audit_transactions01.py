"""Đo audit synthetic401rows/condition, giữ nguyên _expected_insert hiện hành."""
import hashlib
import json
from pathlib import Path
import time

import duckdb
from knowledge_tracing.akt.prediction import _expected_insert
from knowledge_tracing.akt.types import KTEvent,LearnerEvents

ROOT=Path.cwd()
OUTPUT=ROOT/'artifacts/akt/runtime/audit-transaction-bench-20261117-01'
OUTPUT.mkdir(parents=True,exist_ok=False)
learners=tuple(LearnerEvents(f'user-{user:02d}',user%4,tuple(
    KTEvent(f'user-{user:02d}','item-'+str(index%3),100+index,user*100+index+1,index%2,0,user%4)
    for index in range(50))) for user in range(8))
with duckdb.connect() as warmup:
    _expected_insert(warmup,lambda:iter((LearnerEvents('warmup',0,(KTEvent('warmup','i',0,1,0,0,0),)),)))
results=[]
for transaction in (False,True):
    path=OUTPUT/('transaction.duckdb' if transaction else 'autocommit.duckdb')
    con=duckdb.connect(str(path),config={'threads':'1','memory_limit':'128MB','temp_directory':''})
    started=time.perf_counter()
    if transaction:con.execute('BEGIN TRANSACTION')
    count=_expected_insert(con,lambda:iter(learners))
    if transaction:con.execute('COMMIT')
    seconds=time.perf_counter()-started
    rows=con.execute('SELECT * FROM expected ORDER BY source_row').fetchall()
    digest=hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()
    wal=path.with_suffix(path.suffix+'.wal')
    row=dict(transaction=transaction,rows=count,seconds=seconds,logical_rows_sha256=digest,
        database_bytes_before_close=path.stat().st_size,wal_bytes_before_close=wal.stat().st_size if wal.exists() else 0)
    con.close()
    row['database_bytes_after_close']=path.stat().st_size
    results.append(row)
assert results[0]['rows']==results[1]['rows']==400
assert results[0]['logical_rows_sha256']==results[1]['logical_rows_sha256']
result=dict(status='SYNTHETIC_AUDIT_TRANSACTION_IDENTICAL_ROWS',rows_per_condition=400,
    total_synthetic_rows=801,duckdb=duckdb.__version__,results=results,
    speedup=results[0]['seconds']/results[1]['seconds'],
    limits='Local disk synthetic, not measured fullcohort or ModalVolume; unchanged _expected_insert body')
(ROOT/'research_tracking/runs/junyi-calibration-real-20261117-01/AUDIT_TRANSACTION_BENCH01.json').write_text(
    json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2),flush=True)
