"""Probe CPU duy nhất, metadata admission A0/A1, không đọc Parquet/DB."""
import os,json,warnings
from pathlib import Path
ROOT=Path.cwd()
os.environ['MODAL_CONFIG_PATH']=str(ROOT/'artifacts/akt/private/modal2016.toml')
os.environ['MODAL_PROFILE']='kltn2016'
warnings.filterwarnings('ignore',message=r'Your Modal token .*')
import modal
app=modal.App('kltn-cpu-raw-recovery-admission-readonly')
volume=modal.Volume.from_name('kltn-junyi-calibration-artifacts-v1',environment_name='main')

@app.function(image=modal.Image.from_id('im-FLsPV1Te1DGul7RBdUy5HH'),cpu=.5,memory=256,timeout=45,
    startup_timeout=60,max_containers=1,retries=0,scaledown_window=2,serialized=True,
    single_use_containers=True,volumes={'/artifacts':volume},routing_region='ap-south')
def observe():
    import datetime,hashlib,json
    from pathlib import Path
    root=Path('/artifacts').resolve(strict=True)/'junyi-calibration-real-20261117-01'
    result=dict(observed=datetime.datetime.now(datetime.timezone.utc).isoformat(),gpu=False,variants={})
    for variant in ('a0','a1'):
        attempt='calibration-'+variant+'-join-20261117-01'
        raw=root/(variant+'-raw-'+attempt)/'payloads/raw'
        operation=root/(variant+'-cpu-join-operation-'+attempt)/'payloads'
        row=dict(raw_exists=raw.is_dir(),operation_exists=operation.is_dir())
        manifest=raw/'manifest.json'
        if manifest.is_file():
            if manifest.stat().st_size>2*1024**2:raise ValueError('metadata cap exceeded')
            data=manifest.read_bytes();value=json.loads(data)
            names=sorted(path.name for path in raw.iterdir() if path.is_file() and path.name.endswith('.parquet'))
            row['raw']=dict(status=value['status'],prediction_rows=value['prediction_rows'],
                expected_rows=value.get('expected_rows'),shards=len(value['shards']),
                completed_users=len(value['completed_users']),manifest_sha256=hashlib.sha256(data).hexdigest(),
                parquet_files=len(names),last_parquet=names[-1] if names else None,
                last_parquet_modified_utc=datetime.datetime.fromtimestamp((raw/names[-1]).stat().st_mtime,
                    datetime.timezone.utc).isoformat() if names else None)
        configuration=operation/'config.json'
        if configuration.is_file():
            data=configuration.read_bytes();config=json.loads(data)
            row['operation']=dict(config_sha256=hashlib.sha256(data).hexdigest(),
                authorization=config['authorization'],complete=(operation/'COMPLETE.json').is_file(),
                failed=(operation/'FAILED.json').is_file())
        row['raw_complete']=(raw.parent/'COMPLETE.json').is_file()
        fit=root/(variant+'-fit-'+attempt)/'payloads'
        row['fit_complete']=(fit/'COMPLETE.json').is_file()
        for name in ('.audit.tmp.duckdb','.audit.tmp.duckdb.wal'):
            path=raw/name
            if path.is_file():row[name]=dict(bytes=path.stat().st_size,
                modified_utc=datetime.datetime.fromtimestamp(path.stat().st_mtime,datetime.timezone.utc).isoformat())
        result['variants'][variant]=row
    return result

with modal.enable_output(),app.run(environment_name='main'):
    result=observe.remote()
    (ROOT/'research_tracking/runs/junyi-calibration-real-20261117-01/RAW_RECOVERY_ADMISSION01.json').write_text(
        json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2),flush=True)
