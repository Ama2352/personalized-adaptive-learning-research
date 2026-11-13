"""Đối chiếu từng target selection bằng SQL và digest, không fit mô hình."""
import argparse
import hashlib
import json
from pathlib import Path
import threading
import time

ROOT=Path(__file__).resolve().parents[2]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    output=args.output.resolve()
    if not output.is_relative_to(ROOT/'research_tracking/runs') or output.exists():
        parser.error('Output JSON mới trong research_tracking/runs')
    request=json.loads((ROOT/'research_tracking/runs/junyi-a0-h100-batch128-20261112-01/request.json').read_text())
    inputs=request['inputs']
    cache_root=ROOT/inputs['selected_cache_root']
    manifest=cache_root/'manifest.json'
    roles_path=ROOT/inputs['roles_path']
    if sha(manifest)!=inputs['selected_cache_manifest_sha256'] or sha(roles_path)!=inputs['roles_sha256']:
        raise ValueError('Frozen cache/roles changed')
    metadata=json.loads(manifest.read_text())
    for name,record in metadata['outputs'].items():
        if sha(cache_root/name)!=record['sha256']:
            raise ValueError('Frozen data cache changed')
    roles=json.loads(roles_path.read_text())
    encoding_path=ROOT/inputs['encoding_file']
    if sha(encoding_path)!=inputs['encoding_sha256']:
        raise ValueError('Frozen encoding changed')
    vocabulary=set(json.loads(encoding_path.read_text())['values'])
    reference=json.loads((ROOT/'research_tracking/runs/junyi-comparison-preflight-20261113-01/data-audit.json').read_text())['reference']
    import duckdb
    temp=ROOT/'artifacts/akt/tmp'/output.parent.name
    temp.mkdir(parents=True,exist_ok=True)
    connection=duckdb.connect(config=dict(memory_limit='256MB',threads='1',temp_directory=str(temp)))
    timer=threading.Timer(90,connection.interrupt)
    timer.daemon=True
    started=time.monotonic()
    digest=hashlib.sha256()
    count=unseen=0
    learners=set()
    previous=None
    try:
        timer.start()
        connection.execute('CREATE TEMP TABLE selection_users(user_id VARCHAR PRIMARY KEY)')
        connection.executemany('INSERT INTO selection_users VALUES (?)',[(user,) for user in roles['selection_users']])
        cursor=connection.execute('''SELECT c.source_row,c.user_id,c.exercise,c.time_done,c.correct,c.suggested,a.fold
            FROM read_parquet(?) c JOIN read_parquet(?) a USING(user_id)
            JOIN selection_users s USING(user_id)
            WHERE a.partition='development'
            ORDER BY c.user_id,c.time_done,c.source_row''',
            [str(cache_root/'canonical.parquet'),str(cache_root/'assignments.parquet')])
        while True:
            rows=cursor.fetchmany(5000)
            if not rows:
                break
            for row in rows:
                source,user,exercise,timestamp,correct,suggested,fold=row
                key=(user,timestamp,source)
                if (type(user) is not str or type(source) is not int or source<=0
                        or type(timestamp) is not int or timestamp<0 or correct not in (0,1)
                        or suggested not in (0,1) or fold not in (0,1,2,3)
                        or (previous is not None and key<=previous)):
                    raise ValueError('Target schema, chronology or duplicate mismatch')
                previous=key
                digest.update(json.dumps(row,separators=(',',':')).encode()+b'\n')
                count+=1
                unseen+=exercise not in vocabulary
                learners.add(user)
    finally:
        timer.cancel()
        timer.join()
        connection.close()
    if (count!=reference['selection_targets'] or learners!=set(roles['selection_users'])
            or unseen!=0 or digest.hexdigest()!=reference['selection_population_sha256']):
        raise ValueError('Independent selection target population differs from A0')
    for name,record in metadata['outputs'].items():
        if sha(cache_root/name)!=record['sha256']:
            raise ValueError('Data cache changed during audit')
    report=dict(status='PASS_INDEPENDENT_SELECTION_TARGET_POPULATION',targets=count,learners=len(learners),
        oov=unseen,population_sha256=digest.hexdigest(),reference_candidate='A0_H100_BATCH128',
        comparison_fields=['source_row','user_id','exercise','time_done','correct','suggested','fold'],
        chronological_order=['user_id','time_done','source_row'],seconds=time.monotonic()-started,
        model_fit=False,holdout_rows_read=False,calibration_rows_read=False,
        limits_vi='Kiểm toàn bộ selection10 của cache đã ghim. Chưa kiểm dự báo A1–A3 trên dữ liệu này.')
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':
    main()
