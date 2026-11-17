"""CPU probe duy nhất, đọc count từ bản sao DB/WAL, không mở DB đang ghi."""
import os,json,warnings
from pathlib import Path
ROOT=Path.cwd()
os.environ['MODAL_CONFIG_PATH']=str(ROOT/'artifacts/akt/private/modal2016.toml')
os.environ['MODAL_PROFILE']='kltn2016'
warnings.filterwarnings('ignore',message=r'Your Modal token .*')
import modal
app=modal.App('kltn-a0-audit-snapshot-readonly')
volume=modal.Volume.from_name('kltn-junyi-calibration-artifacts-v1',environment_name='main')

@app.function(image=modal.Image.from_id('im-FLsPV1Te1DGul7RBdUy5HH'),cpu=1,memory=512,timeout=60,
    startup_timeout=60,max_containers=1,retries=0,scaledown_window=2,serialized=True,
    single_use_containers=True,volumes={'/artifacts':volume},routing_region='ap-south')
def observe():
    import datetime,json,shutil,subprocess,tempfile,time
    from pathlib import Path
    base=Path('/artifacts').resolve(strict=True)/'junyi-calibration-real-20261117-01'
    raw=base/'a0-raw-calibration-a0-join-20261117-01/payloads/raw'
    database=raw/'.audit.tmp.duckdb'
    files=[path for path in (database,raw/'.audit.tmp.duckdb.wal') if path.is_file()]
    def info():
        return {path.name:dict(bytes=path.stat().st_size,mtime_ns=path.stat().st_mtime_ns) for path in files}
    before=info()
    result=dict(observed=datetime.datetime.now(datetime.timezone.utc).isoformat(),gpu=False,
        raw_complete=(raw.parent/'COMPLETE.json').is_file(),original_files=before)
    if not files:
        result['status']='NO_AUDIT_FILE_CURRENTLY_PRESENT'
        return result
    if sum(pin['bytes'] for pin in before.values())>256*1024**2:
        result['status']='SNAPSHOT_EXCEEDS_256MIB_CAP'
        return result
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='kltn-a0-audit-') as temporary:
        target=Path(temporary)/'snapshot.duckdb'
        for original in files:
            destination=target if original==database else Path(str(target)+'.wal')
            shutil.copyfile(original,destination)
        result['original_files_after_copy']=info()
        result['unchanged_during_copy']=before==result['original_files_after_copy']
        code=('import duckdb,json,sys; '
            'c=duckdb.connect(sys.argv[1],config={"threads":"1","memory_limit":"128MB","temp_directory":""}); '
            'r=c.execute("SELECT count(*),min(source_row),max(source_row) FROM expected").fetchone(); '
            'print(json.dumps({"expected_rows":r[0],"min_source_row":r[1],"max_source_row":r[2],"duckdb":duckdb.__version__})); c.close()')
        checked=subprocess.run(['/opt/kltn/.venv/bin/python','-B','-c',code,str(target)],
            capture_output=True,text=True,timeout=35)
        result['query_returncode']=checked.returncode
        if checked.returncode==0:
            result['snapshot']=json.loads(checked.stdout)
            result['status']='COPIED_AUDIT_SNAPSHOT_COUNTED'
        else:
            result['status']='COPIED_SNAPSHOT_QUERY_FAILED'
            result['stderr_tail']=checked.stderr[-1200:]
    result['probe_seconds']=time.monotonic()-started
    return result

with modal.enable_output(),app.run(environment_name='main'):
    result=observe.remote()
    (ROOT/'research_tracking/runs/junyi-calibration-real-20261117-01/A0_AUDIT_SNAPSHOT_COUNT01.json').write_text(
        json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2),flush=True)
