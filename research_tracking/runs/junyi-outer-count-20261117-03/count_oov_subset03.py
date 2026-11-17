"""Đếm OOV trên đúng5partition nhỏ, Windows Job512MiB và timeout60s."""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
from urllib.parse import unquote

for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CAP=512*1024**2


def helper():
    spec=importlib.util.spec_from_file_location('owned_count_job',ROOT/'scripts/research/windows_owned_worker.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def worker():
    module=helper();api=module.Kernel()
    handle=api.check(api.k.OpenJobObjectW(0x0001|0x0004,False,os.environ['KLTN_OUTER_COUNT_JOB']))
    try:
        api.check(api.k.AssignProcessToJobObject(handle,api.k.GetCurrentProcess()))
        if not api.contains(api.k.GetCurrentProcess(),handle):raise ValueError('Worker Job membership missing')
    finally:api.close(handle)
    print('OWNED_JOB_ASSIGNED_BEFORE_DUCKDB',flush=True)
    import duckdb
    import psutil
    started=time.monotonic()
    source=ROOT/'artifacts/bkt_baseline/derived/canonical'
    assignment=ROOT/'artifacts/bkt_baseline/splits/assignments.parquet'
    encoding_path=ROOT/'artifacts/akt/window-cache/full-refit90-20261114-01.encoding.json'
    vocab=set(json.loads(encoding_path.read_text())['values'])
    files=sorted(p for p in source.rglob('*.parquet') if unquote(p.parent.name.split('=',1)[1]) not in vocab)
    if len(files)!=5 or sum(p.stat().st_size for p in files)!=7381:
        raise ValueError('Expected exact5small OOV partitions')
    con=duckdb.connect(config={'memory_limit':'32MB','threads':'1','temp_directory':'','preserve_insertion_order':'false'})
    try:
        paths=[str(path) for path in files]
        footer=con.execute('SELECT file_name,num_rows FROM parquet_file_metadata(?)', [paths]).fetchall()
        inventory=[dict(path=Path(name).relative_to(ROOT).as_posix(),rows=rows,
            bytes=Path(name).stat().st_size,sha256=sha(Path(name))) for name,rows in footer]
        with (HERE/'OOV_FILE_INVENTORY03.json').open('x',encoding='utf-8') as stream:json.dump(inventory,stream,indent=2)
        print('FIVE_FOOTERS_PINNED_BEFORE_OUTER_QUERY',flush=True)
        rows=con.execute("""SELECT c.exercise,COUNT(*),COUNT(DISTINCT c.user_id)
            FROM read_parquet(?,hive_partitioning=true) c
            JOIN read_parquet(?) a ON c.user_id=a.user_id
            WHERE a.partition='development' AND a.fold=4 GROUP BY c.exercise ORDER BY c.exercise""",
            [paths,str(assignment)]).fetchall()
    finally:con.close()
    memory=psutil.Process().memory_info()
    peak=getattr(memory,'peak_wset',memory.rss)
    if peak>CAP:raise MemoryError('Worker RSS exceeded512MiB')
    result=dict(status='READONLY_OUTER_OOV_SUBSET_COUNT_COMPLETE',phase='outer_evaluation',fold=4,partition='development',
        vocabulary=717,source_files=5,source_bytes=7381,source_footer_rows=sum(row['rows'] for row in inventory),
        oov_targets=sum(row[1] for row in rows),oov_exercises=[dict(exercise=name,targets=count,learners=learners)
            for name,count,learners in rows],peak_worker_rss_bytes=peak,seconds=time.monotonic()-started,
        metadata_pins={p.relative_to(ROOT).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in (assignment,encoding_path)},
        correctness_requested=False,holdout_selected=False,
        limits_vi='Chỉ targetcounts trên5exercise ngoài refit90vocab. Fulloutertargetcount còn lấy từ metadata BKT, '
        'chưa independentlyscan toànoutercohort hoặc biết maxhistory/windows.')
    with (HERE/'OOV_COUNTS03.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False))


def set_job_memory(api,job):
    class Basic(ctypes.Structure):
        _fields_=[('process_time',ctypes.c_longlong),('job_time',ctypes.c_longlong),('flags',wintypes.DWORD),
            ('min_ws',ctypes.c_size_t),('max_ws',ctypes.c_size_t),('active_limit',wintypes.DWORD),
            ('affinity',ctypes.c_size_t),('priority',wintypes.DWORD),('scheduling',wintypes.DWORD)]
    class IO(ctypes.Structure):
        _fields_=[(name,ctypes.c_ulonglong) for name in ('read_ops','write_ops','other_ops','read_bytes','write_bytes','other_bytes')]
    class Extended(ctypes.Structure):
        _fields_=[('basic',Basic),('io',IO),('process_limit',ctypes.c_size_t),('job_limit',ctypes.c_size_t),
            ('process_peak',ctypes.c_size_t),('job_peak',ctypes.c_size_t)]
    info=Extended();info.basic.flags=0x2000|0x8|0x200;info.basic.active_limit=16;info.job_limit=CAP
    api.check(api.k.SetInformationJobObject(job.handle,9,ctypes.byref(info),ctypes.sizeof(info)))


def guarded():
    module=helper();api=module.Kernel()
    name='Local\\KLTN-outer-count-'+uuid.uuid4().hex
    job=module.WindowsJob(api,name)
    started=time.monotonic();status='STOPPED';returncode=None;reason=None
    try:
        set_job_memory(api,job)
        environment=os.environ.copy();environment['KLTN_OUTER_COUNT_JOB']=name
        with (HERE/'oov-count-worker03.log').open('x',encoding='utf-8') as stream:
            try:
                completed=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--worker'],cwd=ROOT,
                    env=environment,stdout=stream,stderr=subprocess.STDOUT,timeout=60,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                returncode=completed.returncode
                status='COMPLETE' if returncode==0 else 'STOPPED'
            except subprocess.TimeoutExpired:reason='subprocess_timeout60s'
    finally:
        job.terminate()
        active_after=job.active()
        job.close()
    result=dict(status=status,returncode=returncode,stop_reason=reason,wall_seconds=time.monotonic()-started,
        subprocess_timeout_seconds=60,job_memory_limit_bytes=CAP,job_active_after_terminate=active_after)
    with (HERE/'OOV_COUNT_RESOURCES03.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps(result))
    if status!='COMPLETE':raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--worker',action='store_true')
    args=parser.parse_args();worker() if args.worker else guarded()
