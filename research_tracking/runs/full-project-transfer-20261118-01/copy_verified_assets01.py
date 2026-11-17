"""Sao chép phía Drive các model/evidence đã kiểm để bộ bàn giao dùng một quyền thư mục."""
from pathlib import Path
import json
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'research_tracking/runs/report-drive-snapshot-20261117-01'))
import publish_snapshot as pub
NAME='KLTN_BAN_GIAO_DAY_DU_20261118'
FIELDS='id,name,mimeType,size,sha256Checksum,parents,owners(emailAddress),trashed,webViewLink'


def write(name,value):
    (B/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


class Drive:
    def __init__(self,session):
        self.session=session

    def get(self,route,**kwargs):
        for attempt in range(3):
            response=self.session.get(pub.API+route,timeout=120,**kwargs)
            if response.status_code not in (429,500,502,503,504):
                return pub.checked(response)
            time.sleep(attempt+1)
        raise RuntimeError('Drive read hết số lần thử lại.')

    def meta(self,file_id):
        return self.get('/files/'+file_id,params={'fields':FIELDS})

    def children(self,folder):
        rows=[];token=None
        while True:
            params=dict(q=f"'{folder}' in parents and trashed=false",pageSize=1000,fields='nextPageToken,files('+FIELDS+')')
            if token:
                params['pageToken']=token
            data=self.get('/files',params=params);rows.extend(data.get('files',[]));token=data.get('nextPageToken')
            if not token:
                return rows

    def folder(self,parent,name):
        matches=[r for r in self.children(parent) if r['name']==name]
        assert len(matches)<=1,'Trùng tên thư mục đích'
        if matches:
            row=matches[0];assert row['mimeType']=='application/vnd.google-apps.folder';return row
        return pub.checked(self.session.post(pub.API+'/files',json=dict(name=name,mimeType='application/vnd.google-apps.folder',parents=[parent]),params={'fields':FIELDS},timeout=120))

    def target_folder(self,root,relative):
        parent=root
        for name in Path(relative).parts:
            parent=self.folder(parent,name)['id']
        return parent


def collect(drive):
    assets=[];seen=set()
    def add(file_id,target,role,expected=None):
        if file_id in seen:
            return
        meta=drive.meta(file_id)
        assert not meta['trashed'] and meta['owners'][0]['emailAddress']=='honguyenminhsang2005@gmail.com'
        assert meta['mimeType']!='application/vnd.google-apps.folder' and meta.get('sha256Checksum')
        if expected:
            assert meta['sha256Checksum']==expected['sha256'] and int(meta['size'])==expected['bytes']
        assert meta['name'].lower() not in {'token.json','client_secret.json','modal.toml','.env'}
        assets.append(dict(source=meta,target_folder=target,role=role));seen.add(file_id)
    def tree(folder,target,role):
        for item in drive.children(folder):
            if item['mimeType']=='application/vnd.google-apps.folder':
                tree(item['id'],target+'/'+item['name'],role)
            else:
                add(item['id'],target,role)
    for name in ('NEW_ARCHIVES_DRIVE01.json','CONFIDENCE_ARCHIVES_DRIVE01.json'):
        data=json.loads((ROOT/'research_tracking/runs/training-handoff-20261117-01'/name).read_text())
        for row in data['files']:
            add(row['id'],'03_ARTIFACTS_VA_KET_QUA/Training_outputs','TRAINING_OUTPUT',dict(bytes=int(row['size']),sha256=row['sha256Checksum']))
    tree('1--Q-yO2ja7q2RwWWfyv6nDtw80PDrnyZ','03_ARTIFACTS_VA_KET_QUA/AKT_models','MODEL_OR_AUDIT')
    outer=json.loads((ROOT/'research_tracking/runs/junyi-outer-real-20261117-01/DRIVE_FINAL_ARCHIVE_ACCEPTANCE01.json').read_text())
    for row in outer['archives']:
        add(row['file_id'],'03_ARTIFACTS_VA_KET_QUA/Junyi_outer','OUTER_EVALUATION',row)
    row=json.loads((ROOT/'research_tracking/runs/junyi-outer-real-20261117-01/EVIDENCE_DRIVE01.json').read_text())
    add(row['file_id'],'03_ARTIFACTS_VA_KET_QUA/Junyi_outer','FROZEN_SOURCE_AND_FIGURES',row)
    history=json.loads((ROOT/'research_tracking/runs/drive-history-upload-20261116-01/READBACK_ACCEPTANCE.json').read_text())
    for row in history['files']:
        parent=Path(row['path']).parent.as_posix()
        add(row['id'],'04_LICH_SU_AUDIT'+('/'+parent if parent!='.' else ''),'COLD_HISTORY',dict(bytes=row['bytes'],sha256=row['local_sha256']))
    for name in ('GRADE10_SUPPORT_DRIVE01.json','METHOD24_DRIVE02.json'):
        row=json.loads((ROOT/'research_tracking/runs/full-project-handoff-audit-20261118-01'/name).read_text())
        add(row['file_id'],'03_ARTIFACTS_VA_KET_QUA/Grade10','GRADE10_SUPPORT_OR_CONFIDENCE',row)
    # Toàn cây calibration đã dùng; không tải các binary này về máy.
    for folder,label in (('1VF23RDlVmsXEbbcWl6xTtXQ7yz0WjQ0H','Cloud_lifecycle'),
                         ('1tUKMQF8TDnFj8LY_KJjH6wC9DH5-bB-Z','Numeric_backups'),
                         ('1eHoAwpISsYHmonVEkBns_16dY-YCcHV2','Local_A2_fit'),
                         ('1FtAAZJdXQ7MAGCc0OwOE8jwwt9Tk5Yxs','Local_A3_fit')):
        tree(folder,'03_ARTIFACTS_VA_KET_QUA/Junyi_calibration/'+label,'CALIBRATION')
    return assets


def main():
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    pub.NAME=NAME
    with AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as session:
        master=pub.folder(session);write('DRIVE_MASTER01.json',master)
        drive=Drive(session)
        plan_path=B/'COPY_PLAN01.json'
        if plan_path.exists():
            assets=json.loads(plan_path.read_text())['assets']
        else:
            assets=collect(drive);write('COPY_PLAN01.json',dict(assets=assets,bytes=sum(int(a['source']['size']) for a in assets),
                reason='Sao chép phía server để người nhận chỉ cần quyền thư mục bàn giao mới; nguyên bản Drive và local giữ nguyên.'))
        print('COPY_PLAN',len(assets),sum(int(a['source']['size']) for a in assets),'bytes',flush=True)
        records=[]
        for number,asset in enumerate(assets,1):
            original=asset['source'];parent=drive.target_folder(master['id'],asset['target_folder'])
            candidates=[r for r in drive.children(parent) if r['name']==original['name']]
            assert len(candidates)<=1,'Có file copy trùng tên'
            if candidates:
                copied=candidates[0]
            else:
                # Nếu POST hết phiên giữa chừng, lần chạy tiếp dò theo tên+SHA trước khi copy.
                copied=pub.checked(session.post(pub.API+'/files/'+original['id']+'/copy',
                    json=dict(name=original['name'],parents=[parent]),params={'fields':FIELDS},timeout=180))
            copied=drive.meta(copied['id']);current_source=drive.meta(original['id'])
            for item in (copied,current_source):
                assert item.get('sha256Checksum')==original['sha256Checksum'] and item['size']==original['size']
                assert item['owners'][0]['emailAddress']=='honguyenminhsang2005@gmail.com' and not item['trashed']
            assert copied['parents']==[parent] and current_source['parents']==original['parents']
            records.append(dict(source_id=original['id'],destination=copied,role=asset['role'],
                drive_path=asset['target_folder']+'/'+original['name'],source_parents_unchanged=True))
            write('COPIED_ASSETS01.json',dict(status='COPYING',master=master,files=records))
            print('COPIED_VERIFIED',number,'/',len(assets),asset['role'],original['name'],flush=True)
        write('COPIED_ASSETS01.json',dict(status='ALL_SERVER_COPIES_SOURCE_AND_DESTINATION_SHA256_VERIFIED',master=master,files=records))
        print('SERVER_COPIES_COMPLETE',len(records),master['webViewLink'],flush=True)


if __name__=='__main__':
    main()
