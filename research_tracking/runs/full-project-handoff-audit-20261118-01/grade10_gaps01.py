"""Giữ hồ sơ selected Grade10 còn trong archive local, tái dùng model đã sao lưu."""
from pathlib import Path
import hashlib
import io
import json
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def prepare():
    index=json.loads((ROOT/'experiments/akt/results/model-export-20261112-01/MODEL_INDEX.json').read_text())
    history=json.loads((ROOT/'research_tracking/runs/drive-history-upload-20261116-01/READBACK_ACCEPTANCE.json').read_text())
    names={Path(row['path']).name:row for row in history['files']}
    models=[];members=[];buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as output:
        for row in index['entries']:
            if row['dataset']!='Grade10':
                continue
            path=ROOT/row['source_archive'];key=path.parent.name+'__'+path.name
            model=dict(model=row['model'],checkpoint_epoch=row['epoch'],
                original_checkpoint=row['source_member'],compact_checkpoint='experiments/akt/results/model-export-20261112-01/'+row['destination'],
                checkpoint_sha256=row['sha256'],source_archive=row['source_archive'])
            if key in names:
                model.update(archive_status='VERIFIED_DRIVE_HISTORY_ARCHIVE',drive=names[key])
                models.append(model);continue
            assert path.is_file(), str(path)
            archive_sha=sha(path)
            before=path.stat()
            model.update(archive_status='LOCAL_ARCHIVE_WITHOUT_ACCEPTED_HISTORY_RECEIPT',
                         bytes=before.st_size,sha256=archive_sha)
            with zipfile.ZipFile(path) as source:
                for info in source.infolist():
                    name=info.filename;relative=Path(name)
                    assert not relative.is_absolute() and '..' not in relative.parts
                    if info.is_dir() or relative.suffix not in {'.json','.jsonl','.csv','.txt','.log'}:
                        continue
                    assert info.file_size<=4*1024**2
                    raw=source.read(info)
                    destination=name if name.startswith(('experiments/','artifacts/')) else 'archive-metadata/'+row['model']+'/'+name
                    members.append(dict(model=row['model'],path=destination,original_member=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
                        source_archive=row['source_archive'],source_archive_sha256=archive_sha))
                    target=zipfile.ZipInfo(destination,(1980,1,1,0,0,0));target.compress_type=zipfile.ZIP_DEFLATED
                    output.writestr(target,raw)
            assert path.stat().st_size==before.st_size and sha(path)==archive_sha
            models.append(model)
        manifest=dict(status='FIVE_LOCAL_SELECTED_RUN_SUPPORT_PACKAGED_WITH_MODEL_RELOCATION',models=models,files=members,
            limits=['Archive gốc giữ nguyên. Gói này giữ terminal, selection predictions/targets/coverage, epoch logs và checkpoint metadata.',
                    'Model best đã có trong Grade10 export trên Drive; phục hồi về original_checkpoint sau kiểm SHA khi consumer yêu cầu đường dẫn cũ.',
                    'Các checkpoint epoch trung gian còn trong archive gốc; chưa cần cho refit fresh theo epoch đã chọn.',
                    'Chưa nghiệm thu cold restore toàn pipeline trên máy người nhận.'])
        output.writestr('GRADE10_SUPPORT_INVENTORY.json',json.dumps(manifest,ensure_ascii=False,indent=2).encode())
    raw=buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        assert len(archive.namelist())==len(set(archive.namelist()))
        assert archive.testzip() is None
        for row in members:
            assert hashlib.sha256(archive.read(row['path'])).hexdigest()==row['sha256']
    (B/'GRADE10_SUPPORT01.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('GRADE10_SUPPORT_VERIFIED',len(models),'models',len(members),'members',len(raw),'ZIPbytes',flush=True)
    return raw


def main():
    raw=prepare()
    if '--upload' not in sys.argv:
        return
    sys.path.insert(0,str(ROOT/'research_tracking/runs/report-drive-snapshot-20261117-01'))
    sys.path.insert(0,str(ROOT/'scripts/akt'))
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    import publish_snapshot as pub
    from drive_stream_upload import upload_stream
    pub.NAME='project-handoff-readiness-20261118-01';pub.LIMIT=16*1024**2
    with AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as session:
        folder=pub.folder(session)
        (B/'DRIVE_FOLDER01.json').write_text(json.dumps(folder,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        plan=dict(folder_id=folder['id'],name='GRADE10_SELECTION_SUPPORT01.zip',total_bytes=len(raw),
                  source_plan_sha256=sha(B/'GRADE10_SUPPORT01.json'))
        def chunks():
            for offset in range(0,len(raw),8*1024**2):
                yield raw[offset:offset+8*1024**2]
        receipt=upload_stream(session,plan,chunks,ROOT/'artifacts/akt/private/drive-upload/project-handoff-readiness-20261118-01/grade-support-state.json',max_total_bytes=16*1024**2)
        readback=pub.readback(session,receipt['file_id'],len(raw),hashlib.sha256(raw).hexdigest())
        (B/'GRADE10_SUPPORT_DRIVE01.json').write_text(json.dumps(readback,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('GRADE10_SUPPORT_DRIVE_ACCEPTED',readback['url'],flush=True)


if __name__=='__main__':
    main()
