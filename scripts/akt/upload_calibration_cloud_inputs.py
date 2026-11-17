"""Chuyển gói input đã pin lên Drive Sang, giữ tiến độ upload riêng trên D."""
import json
from pathlib import Path

import drive_resumable_upload as core

ROOT=Path(__file__).resolve().parents[2]
RUN='cloud-calibration-input-upload-20261117-01'
EVIDENCE=ROOT/'research_tracking/runs'/RUN
PRIVATE=ROOT/'artifacts/akt/private'/RUN


def main():
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    receipt_path=ROOT/'research_tracking/runs/cloud-calibration-inputs-20261117-01/INPUT_ARCHIVE04.json'
    receipt=core.read_json(receipt_path)
    source=(ROOT/receipt['path']).resolve()
    allowed=(ROOT/'artifacts/akt/runtime/calibration-cloud-inputs').resolve()
    if not source.is_relative_to(allowed) or source.name!='input04.zip':
        raise ValueError('Gói input cần đúng vùng staging đã pin.')
    pin=core.hashes(source)
    if pin['bytes']!=receipt['bytes'] or pin['sha256']!=receipt['sha256'] or pin['bytes']>160*1024**2:
        raise ValueError('Input ZIP khác pin hoặc vượt160MiB.')
    plan=dict(source=str(source.parent),files=[dict(path=source.name,**pin)],bytes=pin['bytes'],
        folder_name='junyi-calibration-inputs-20261117-01',
        parent_id='1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7',account='honguyenminhsang2005@gmail.com')
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    PRIVATE.mkdir(parents=True,exist_ok=True)
    plan_path=EVIDENCE/'UPLOAD_PLAN.json'
    if plan_path.exists() and core.read_json(plan_path)!=plan:
        raise RuntimeError('Input upload plan đã đổi, giữ state cũ để rà.')
    if not plan_path.exists():
        core.atomic_json(plan_path,plan)
    credentials=Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))
    with core.single_writer(PRIVATE/'upload.lock'),AuthorizedSession(credentials) as session:
        uploader=core.Uploader(session,plan,PRIVATE/'state.json',EVIDENCE,
                               chunk_bytes=32*1024**2,retries=6)
        uploader.run()
        entry=uploader.state['files'][source.name]
        metadata=uploader.metadata(entry['remote_id'])
        parent=uploader.state['folders']['.']
        if not uploader.matches(metadata,plan['files'][0],parent) or metadata.get('sha256Checksum')!=pin['sha256']:
            raise RuntimeError('Drive SHA-256 readback chưa đạt.')
        result=dict(status='INPUT_ZIP_DRIVE_SHA256_VERIFIED',account=plan['account'],
            file_id=metadata['id'],folder_id=parent,bytes=pin['bytes'],sha256=pin['sha256'],
            input_plan_sha256=receipt['plan_sha256'],source_deleted=False,
            research_outputs_downloaded=False,verified_at=core.now())
        core.atomic_json(EVIDENCE/'STRICT_ACCEPTANCE.json',result)
        print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        print('Input upload dừng do '+type(error).__name__+'; giữ state riêng để tiếp tục.')
        raise SystemExit(1)
