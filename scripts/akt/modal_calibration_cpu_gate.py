"""Kiểm Linux CPU tổng hợp và lưu log trực tiếp Drive trước inference thật."""
import os
from pathlib import Path
import warnings

ROOT=Path(__file__).resolve().parents[2] if os.name=='nt' else Path('/opt/kltn')
if os.name=='nt':
    os.environ['MODAL_CONFIG_PATH']=str(ROOT/'artifacts/akt/private/modal2016.toml')
    os.environ['MODAL_PROFILE']='kltn2016'
warnings.filterwarnings('ignore',message=r'Your Modal token .*')
import modal

volume=modal.Volume.from_name('kltn-junyi-calibration-artifacts-v1',environment_name='main')
image=(modal.Image.debian_slim(python_version='3.13')
    .pip_install('numpy==2.5.4','pandas==3.0.6','duckdb==1.5.6','psutil==7.2.2',
                 'pytest==9.1.1','requests==2.34.2','google-auth==2.62.1',
                 'scikit-learn==1.9.1','scipy==1.18.1','pyarrow==26.0.1')
    .add_local_dir(str(ROOT/'src/knowledge_tracing'),'/opt/kltn/src/knowledge_tracing',
                   ignore=['**/__pycache__/**','**/*.pyc'])
    .add_local_file(str(ROOT/'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md'),
                    '/opt/kltn/docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md')
    .add_local_file(str(ROOT/'artifacts/akt/dependencies/upstream/akt.py'),
                    '/opt/kltn/artifacts/akt/dependencies/upstream/akt.py'))
for name in ['test_cloud_calibration_fit.py','test_junyi_calibration_producer.py','test_drive_artifact_sink.py',
             'test_research_junyi_numeric_predictions.py']:
    image=image.add_local_file(str(ROOT/'tests/akt'/name),'/opt/kltn/tests/akt/'+name)
for name in ['drive_artifact_sink.py','drive_resumable_upload.py']:
    image=image.add_local_file(str(ROOT/'scripts/akt'/name),'/opt/kltn/scripts/akt/'+name)
app=modal.App('kltn-calibration-linux-cpu-gate')


@app.function(image=image,cpu=1,memory=2048,timeout=900,startup_timeout=180,
              max_containers=1,scaledown_window=2,retries=0,single_use_containers=True,
              routing_region='ap-south',
              volumes={'/artifacts':volume},
              secrets=[modal.Secret.from_name('kltn-drive-artifacts-sang2005-20261117',
                       environment_name='main',required_keys=['KLTN_DRIVE_OAUTH_JSON'])])
def gate():
    import json
    import subprocess
    import sys
    import time
    sys.path.insert(0,'/opt/kltn/scripts/akt')
    import drive_artifact_sink as sink
    volume.reload()
    sink.CLOUD_ROOT=Path('/artifacts').resolve(strict=True)
    run_id='cloud-calibration-linux-20261117-01'
    tranche_id='cpu-tests03'
    output=sink.CLOUD_ROOT/run_id/tranche_id/'payloads'
    output.mkdir(parents=True,exist_ok=False)
    command=[sys.executable,'-B','-m','pytest','/opt/kltn/tests/akt/test_cloud_calibration_fit.py',
        '/opt/kltn/tests/akt/test_junyi_calibration_producer.py',
        '/opt/kltn/tests/akt/test_drive_artifact_sink.py',
        '/opt/kltn/tests/akt/test_research_junyi_numeric_predictions.py','-q','-p','no:cacheprovider',
        '--basetemp=/tmp/kltn-calibration-tests']
    import hashlib
    import importlib.metadata
    pins={path.relative_to(ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest()
          for directory in ['src','tests','scripts'] for path in (ROOT/directory).rglob('*.py')}
    versions={name:importlib.metadata.version(name) for name in
              ['numpy','pandas','duckdb','psutil','pytest','scikit-learn','scipy','pyarrow']}
    (output/'config.json').write_text(json.dumps(dict(command=command,synthetic=True,gpu=False,
        source_sha256=pins,versions=versions),ensure_ascii=False,indent=2))
    env=dict(os.environ,PYTHONPATH='/opt/kltn/src',PYTHONDONTWRITEBYTECODE='1')
    started=time.monotonic()
    with (output/'tests.txt').open('w') as log:
        result=subprocess.run(command,cwd='/opt/kltn',env=env,stdout=log,stderr=subprocess.STDOUT,
                              timeout=120,check=False)
    (output/'result.json').write_text(json.dumps(dict(exit_code=result.returncode,
        seconds=time.monotonic()-started,gpu_called=False,synthetic_only=True)))
    volume.commit()
    receipt=sink.publish_from_environment(source_root=output,
        files=['config.json','tests.txt','result.json'],run_id=run_id,tranche_id=tranche_id,
        volume_commit=volume.commit,max_total_bytes=1024**2,retries=2)
    return dict(exit_code=result.returncode,receipt=receipt,
                test_summary=(output/'tests.txt').read_text()[-3000:])


if __name__=='__main__':
    import json
    destination=ROOT/'research_tracking/runs/cloud-calibration-fit-20261117-01/LINUX_CPU_GATE03.json'
    if destination.exists():
        raise SystemExit('Đã có receipt, kiểm trạng thái trước khi chạy lại.')
    with modal.enable_output(),app.run(environment_name='main'):
        result=gate.remote()
    destination.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
    raise SystemExit(result['exit_code'])
