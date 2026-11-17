"""Probe CPU metadata tối đa30giây, chỉ đọc snapshot A0 trên Volume."""
import os
from pathlib import Path
import json
import warnings
ROOT=Path.cwd()
os.environ['MODAL_CONFIG_PATH']=str(ROOT/'artifacts/akt/private/modal2016.toml')
os.environ['MODAL_PROFILE']='kltn2016'
warnings.filterwarnings('ignore',message=r'Your Modal token .*')
import modal
app=modal.App('kltn-a0-cpu-progress-readonly')
volume=modal.Volume.from_name('kltn-junyi-calibration-artifacts-v1',environment_name='main')

@app.function(image=modal.Image.from_id('im-FLsPV1Te1DGul7RBdUy5HH'),cpu=.25,memory=256,timeout=30,
    startup_timeout=60,max_containers=1,retries=0,scaledown_window=2,serialized=True,
    single_use_containers=True,volumes={'/artifacts':volume},routing_region='ap-south')
def observe():
    import datetime,json
    from pathlib import Path
    root=Path('/artifacts').resolve(strict=True)/'junyi-calibration-real-20261117-01'
    attempt='calibration-a0-join-20261117-01'
    result=dict(observed=datetime.datetime.now(datetime.timezone.utc).isoformat(),gpu=False)
    raw=root/('a0-raw-'+attempt)/'payloads/raw'
    manifest=raw/'manifest.json'
    if manifest.is_file():
        if manifest.stat().st_size>2*1024**2:raise ValueError('manifest exceeds metadata cap')
        value=json.loads(manifest.read_text())
        result['raw']=dict(status=value['status'],prediction_rows=value['prediction_rows'],
            expected_rows=value.get('expected_rows'),shards=len(value['shards']),
            completed_users=len(value['completed_users']),modified_utc=datetime.datetime.fromtimestamp(
                manifest.stat().st_mtime,datetime.timezone.utc).isoformat())
    for name,path in [('raw_complete',raw.parent/'COMPLETE.json'),
        ('fit_complete',root/('a0-fit-'+attempt)/'payloads/COMPLETE.json'),
        ('temperature',root/('a0-fit-'+attempt)/'payloads/fit/temperature.json')]:
        result[name]=dict(exists=path.is_file(),bytes=path.stat().st_size if path.is_file() else 0)
    for name,path in [('audit',raw/'.audit.tmp.duckdb'),('audit_wal',raw/'.audit.tmp.duckdb.wal')]:
        result[name]=dict(exists=path.is_file(),bytes=path.stat().st_size if path.is_file() else 0,
            modified_utc=datetime.datetime.fromtimestamp(path.stat().st_mtime,datetime.timezone.utc).isoformat()
            if path.is_file() else None)
    return result

with modal.enable_output(),app.run(environment_name='main'):
    result=observe.remote()
    (ROOT/'research_tracking/runs/junyi-calibration-real-20261117-01/A0_CPU_PROGRESS_PROBE01.json').write_text(
        json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2),flush=True)
