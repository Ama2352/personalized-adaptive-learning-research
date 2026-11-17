"""Upload bằng CPU local, kiểm lại byte trên Volume; không cấp GPU."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import warnings
from concurrent.futures import ThreadPoolExecutor
import sys

ROOT = Path(__file__).resolve().parents[3]
B = Path(__file__).resolve().parent
os.environ['MODAL_CONFIG_PATH']=str(ROOT/'artifacts/akt/private/modal2016.toml')
os.environ['MODAL_PROFILE']='kltn2016'
warnings.filterwarnings('ignore',message=r'Your Modal token .*')

async def verify_account():
    import modal
    from modal.client import _Client
    from modal_proto import api_pb2
    client = await _Client.from_env()
    info = await client._stub.TokenInfoGet(api_pb2.TokenInfoGetRequest())
    assert info.workspace_name=='honguyenminhsang2016'
    await client._close()
    return info.workspace_name

def main():
    import modal
    workspace=asyncio.run(verify_account())
    # AppGetObjects endpoint của phiên này trả UnimplementedError. Giữ lỗi
    # trong log01, dùng log build/run đã đạt và kiểm77file trước CUDA ở worker.
    log = ROOT/'research_tracking/runs/junyi-calibration-real-20261117-01/a1-a3-gpu01.log'
    body = log.read_text(encoding='utf-8')
    assert 'im-ifzJuCpP1yGdoDMSVIVgZz' in body and 'A1_A2_A3_GPU_COMPLETE_NO_MORE_INPUTS_APP_STOPPING' in body
    (B/'RUNTIME_IMAGE_LOG_EVIDENCE01.json').write_text(json.dumps(dict(
        status='PRIOR_SUCCESS_LOG_IMAGE_WITH_ACTUAL_RUNTIME_GATE_REQUIRED',
        image_id='im-ifzJuCpP1yGdoDMSVIVgZz',source_log=str(log.relative_to(ROOT)),
        log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),api_confirmation=False),indent=2)+'\n')
    volume = modal.Volume.from_name('kltn-junyi-calibration-artifacts-v1',environment_name='main')
    inventory = json.loads((B/'HANDOFF_INVENTORY01.json').read_text())
    physical = '/__modal/volumes/vo-dv1975utRQbmagCjA0brSe'
    if '--verify-only' not in sys.argv:
        with volume.batch_upload(force=False) as batch:
            for entry in inventory['files']:
                batch.put_file(entry['local_path'],entry['remote_path'].removeprefix(physical))
    print('INPUT_UPLOAD_COMPLETE_READING_BACK',flush=True)
    def verify(entry):
        digest = hashlib.sha256()
        count = 0
        for chunk in volume.read_file(entry['remote_path'].removeprefix(physical)):
            digest.update(chunk)
            count += len(chunk)
        assert count==entry['bytes'] and digest.hexdigest()==entry['sha256'],entry['remote_path']
        return dict(path=entry['remote_path'],bytes=count,sha256=digest.hexdigest())
    accepted=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for verified in pool.map(verify,inventory['files']):
            accepted.append(verified)
            if len(accepted)%25==0:
                print('REMOTE_SHA_VERIFIED',len(accepted),flush=True)
    (B/'MODAL_STAGING_ACCEPTANCE01.json').write_text(json.dumps(dict(
        status='ALL_REMOTE_INPUT_BYTES_SHA256_VERIFIED',workspace=workspace,files=accepted,
        gpu_started=False),indent=2)+'\n')
    print('STAGING_ACCEPTED',len(accepted),flush=True)

if __name__=='__main__':
    main()
