"""Chỉ đếm Development fold4 bằng user/exercise, không đọc correctness."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def worker():
    import duckdb
    started=time.monotonic()
    canonical=ROOT/'artifacts/bkt_baseline/derived/canonical'
    assignments=ROOT/'artifacts/bkt_baseline/splits/assignments.parquet'
    roles_path=ROOT/'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01/roles.json'
    encoding_path=ROOT/'artifacts/akt/window-cache/full-refit90-20261114-01.encoding.json'
    metadata=[assignments,roles_path,encoding_path,ROOT/'artifacts/bkt_baseline/splits/manifest.json',
        ROOT/'artifacts/bkt_baseline/derived/manifest.json']
    pins={path.relative_to(ROOT).as_posix():dict(bytes=path.stat().st_size,sha256=digest(path)) for path in metadata}
    roles=json.loads(roles_path.read_text(encoding='utf-8'))
    encoding=json.loads(encoding_path.read_text(encoding='utf-8'))
    vocab=encoding['values']
    files=sorted(canonical.rglob('*.parquet'))
    def fingerprint():
        rows=[(p.relative_to(ROOT).as_posix(),p.stat().st_size,p.stat().st_mtime_ns) for p in files]
        return hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()
    before=fingerprint()
    con=duckdb.connect(config={'memory_limit':'128MB','threads':'1','temp_directory':'',
                              'preserve_insertion_order':'false'})
    try:
        con.execute("CREATE TEMP TABLE outer_users AS SELECT CAST(user_id AS VARCHAR) user_id FROM read_parquet(?) WHERE partition='development' AND fold=4",[str(assignments)])
        users={row[0] for row in con.execute('SELECT user_id FROM outer_users').fetchall()}
        if users!=set(roles['outer_validation_users']) or len(users)!=39616:
            raise ValueError('Outer assignments/roles coverage mismatch')
        con.execute('CREATE TEMP TABLE vocabulary(exercise VARCHAR PRIMARY KEY)')
        con.executemany('INSERT INTO vocabulary VALUES (?)',[(value,) for value in vocab])
        pattern=str(canonical/'**/*.parquet')
        query="""WITH per_user AS (
          SELECT u.user_id,COUNT(*) targets,COUNT(*) FILTER(WHERE v.exercise IS NULL) oov
          FROM read_parquet(?,hive_partitioning=true) c
          JOIN outer_users u ON CAST(c.user_id AS VARCHAR)=u.user_id
          LEFT JOIN vocabulary v ON c.exercise=v.exercise GROUP BY u.user_id)
          SELECT COUNT(*),SUM(targets),SUM(oov),MAX(targets),COUNT(*) FILTER(WHERE oov>0) FROM per_user"""
        learners,targets,oov,max_history,users_oov=con.execute(query,[pattern]).fetchone()
        by_exercise=con.execute("""SELECT c.exercise,COUNT(*) FROM read_parquet(?,hive_partitioning=true) c
          JOIN outer_users u ON CAST(c.user_id AS VARCHAR)=u.user_id
          LEFT JOIN vocabulary v ON c.exercise=v.exercise WHERE v.exercise IS NULL GROUP BY c.exercise ORDER BY c.exercise""",[pattern]).fetchall()
    finally:con.close()
    if before!=fingerprint() or any(digest(ROOT/name)!=pin['sha256'] for name,pin in pins.items()):
        raise ValueError('Source metadata/fingerprints changed')
    if learners!=39616 or targets!=4137050 or sum(row[1] for row in by_exercise)!=oov:
        raise ValueError('Count does not match frozen outer population')
    result=dict(status='READONLY_OUTER_METADATA_COUNTS_COMPLETE',phase='outer_evaluation',partition='development',fold=4,
        learners=learners,targets=targets,fitted_targets=targets-oov,oov_targets=oov,
        vocabulary=len(vocab),max_learner_events=max_history,learners_with_oov=users_oov,
        oov_exercises=[dict(exercise=name,targets=count) for name,count in by_exercise],
        source_pins=pins,canonical_files=len(files),canonical_bytes=sum(p.stat().st_size for p in files),
        canonical_metadata_fingerprint_before_after=before,duckdb=duckdb.__version__,seconds=time.monotonic()-started,
        columns_requested=['user_id','exercise','partition','fold'],correctness_requested=False,holdout_selected=False,
        limits_vi='Chỉ aggregate counts. Không đọc correct/suggested/time/order hoặc predictions. '
        'Canonical files kiểm size/mtime ổn định, không rehash payload Parquet trong lượt này.')
    with (HERE/'COUNTS01.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False))


def guarded():
    import psutil
    started=time.monotonic();peak=0;reason=None
    with (HERE/'count-worker01.log').open('x',encoding='utf-8') as stream:
        process=subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),'--worker'],cwd=ROOT,
            stdout=stream,stderr=subprocess.STDOUT)
        try:
            while process.poll() is None:
                try:
                    parent=psutil.Process(process.pid)
                    rss=sum(p.memory_info().rss for p in (parent,*parent.children(recursive=True)) if p.is_running())
                    peak=max(peak,rss)
                except psutil.NoSuchProcess:continue
                if time.monotonic()-started>90:reason='wall90s'
                elif rss>256*1024**2:reason='rss256MiB'
                if reason:
                    for child in reversed(parent.children(recursive=True)):
                        try:child.kill()
                        except psutil.NoSuchProcess:pass
                    process.kill();process.wait();break
                time.sleep(.1)
        finally:
            if process.poll() is None:process.kill();process.wait()
    result=dict(status='COMPLETE' if process.returncode==0 and reason is None else 'STOPPED',returncode=process.returncode,
        stop_reason=reason,wall_seconds=time.monotonic()-started,peak_process_tree_rss_bytes=peak,
        max_seconds=90,max_rss_bytes=256*1024**2)
    with (HERE/'COUNT_RESOURCES01.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps(result))
    if result['status']!='COMPLETE':raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',action='store_true')
    args=parser.parse_args()
    worker() if args.worker else guarded()
