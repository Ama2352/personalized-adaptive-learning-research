from pathlib import Path
import hashlib,json,re,time
import duckdb
root=Path.cwd()
run=root/'artifacts/akt/local-tests/parallel-worker-path-20261108-01'
run.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
log=root/'artifacts/akt/preflight/gate2-tests-20261107-linux-worker-16.log'
failed=re.search(r'Cannot open file "([^"]+)"',log.read_text(encoding='utf-8')).group(1)
failed_path=Path(failed)
failed_base=next(p for p in failed_path.parents if p.name.startswith('gate2-20261107-linux-worker-16-'))
# Root mới có cùng độ dài chính xác; không ghi vào failed Gate basetemp.
control_base=root/'artifacts/akt/local-tests'/('gate2-20261107-linux-worker-pc-'+'0'*32)
assert len(str(control_base))==len(str(failed_base))
long_path=control_base/failed_path.relative_to(failed_base)
short_name=long_path.with_name('a.parquet.tmp')
compact_path=control_base/'wk0/p/experiments/akt/results/synthetic-worker/predictions/.pending'/failed_path.name
baseline=run/'baseline.parquet'
cases=[]
for label,path in [('baseline',baseline),('same_parent_short_filename',short_name),
                   ('same_depth_original_filename_length',long_path),('compact_fixture_full_filename',compact_path)]:
    path.parent.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    result={'case':label,'path':str(path),'path_characters':len(str(path)),'parent_characters':len(str(path.parent))}
    con=duckdb.connect()
    try:
        con.execute('COPY (SELECT 1::INTEGER AS synthetic_row) TO ? (FORMAT PARQUET)',[str(path)])
        assert con.execute('SELECT * FROM read_parquet(?)',[str(path)]).fetchall()==[(1,)]
        result.update(status='PASS')
    except Exception as error:
        result.update(status='ERROR',error_type=type(error).__name__,error=str(error))
    finally:con.close()
    result['elapsed_seconds']=time.monotonic()-started;cases.append(result)
assert cases[0]['status']==cases[1]['status']==cases[3]['status']=='PASS'
assert cases[2]['status']=='ERROR'
source=root/'tests/akt/test_worker_lifecycle.py'
source_before=sha(source)
assert source_before=='734f28bd0aea487a67b364a83e3def69a3ca1cd34e3c658583055c5f8ec28b47'
inventory={'source':source.relative_to(root).as_posix(),'source_sha256_before_copy':source_before}
(run/'source_inventory_before_copy.json').write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
snapshot=run/'test_worker_lifecycle_gate16_failed_source.py'
snapshot.write_bytes(source.read_bytes());assert sha(snapshot)==source_before
receipt={'scope':'Cheap one-row DuckDB COPY path-length diagnostic only; no model/dataset/GPU',
         'duckdb':duckdb.__version__,'actual_gate16_failed_path':failed,
         'actual_failed_path_characters':len(failed),'gate16_log_sha256':sha(log),
         'gate16_junit_sha256':sha(root/'artifacts/akt/preflight/gate2-tests-20261107-linux-worker-16.xml'),
         'parent_failure_receipt_sha256':sha(root/'artifacts/akt/local-tests/linux-gate16-failure-receipt.json'),
         'control_root_length_matches_gate16':True,'cases':cases,
         'source_snapshot_sha256':source_before,
         'interpretation_vi':'Long filename ở deep parent fail, cùng parent short filename và compact root full filename pass. Phù hợp Windows/DuckDB path-length limitation; không graph/model failure.'}
(run/'path_control.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
