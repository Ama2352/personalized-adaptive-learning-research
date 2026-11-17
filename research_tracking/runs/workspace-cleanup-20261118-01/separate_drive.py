"""Tách bản sao lịch sử khỏi bộ bàn giao, giữ bytes/ID và ghi relocation mới."""
from pathlib import Path
import json,threading,concurrent.futures
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
TRANSFER=ROOT/'research_tracking/runs/full-project-transfer-20261118-01'
API='https://www.googleapis.com/drive/v3'
FIELDS='id,name,mimeType,size,sha256Checksum,parents,trashed,webViewLink'

def main():
    master=json.loads((TRANSFER/'MANIFEST_BAN_GIAO.json').read_text(encoding='utf-8'))
    dedup=json.loads((B/'DRIVE_ACCEPTANCE.json').read_text(encoding='utf-8'))
    changes=[]
    with AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as s:
        def api(method,path,**kwargs):
            r=s.request(method,API+path,timeout=60,**kwargs)
            if r.status_code not in (200,201):raise RuntimeError('DriveHTTP'+str(r.status_code))
            return r.json()
        def meta(file_id):return api('GET','/files/'+file_id,params={'fields':FIELDS})
        def children(parent):
            rows=[];token=None
            while True:
                params={'q':"'%s' in parents and trashed=false"%parent,'pageSize':1000,'fields':'nextPageToken,files('+FIELDS+')'}
                if token:params['pageToken']=token
                data=api('GET','/files',params=params);rows.extend(data.get('files',[]));token=data.get('nextPageToken')
                if not token:return rows
        def folder(parent,name):
            found=[r for r in children(parent) if r['name']==name]
            assert len(found)<=1
            return found[0] if found else api('POST','/files',json={'name':name,'mimeType':'application/vnd.google-apps.folder','parents':[parent]},params={'fields':FIELDS})
        def move(file_id,parent,expected_sha=None):
            before=meta(file_id);assert not before['trashed']
            if expected_sha:assert before['sha256Checksum']==expected_sha
            if parent not in before.get('parents',[]):
                after=api('PATCH','/files/'+file_id,params={'addParents':parent,'removeParents':','.join(before.get('parents',[])),'fields':FIELDS},json={})
            else:after=before
            assert parent in after['parents'] and not after['trashed']
            if expected_sha:assert after['sha256Checksum']==expected_sha and after['size']==before['size']
            changes.append(dict(before=before,after=after))
            (B/'DRIVE_MOVE_PROGRESS.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
            return after
        handoff=meta(master['master_folder']['id'])
        archive=folder(handoff['parents'][0],'KLTN_LUU_TRU_LICH_SU_20261118')
        old_guides=folder(archive['id'],'00_HUONG_DAN_VA_MANIFEST_CU')
        # Hai archive Grade10 cần chạy tiếp được giữ ở bộ bàn giao trước khi chuyển cây lịch sử.
        support=next(r for r in master['assets'] if r['role']=='GRADE10_SUPPORT_OR_CONFIDENCE')
        grade_parent=meta(support['file_id'])['parents'][0]
        for row in master['assets']:
            if row['role']=='COLD_HISTORY' and row['tier']=='ready':
                move(row['file_id'],grade_parent,row['sha256'])
                row['drive_path']='03_ARTIFACTS_VA_KET_QUA/Grade10/'+row['name']
        # Tách35archive lịch sử còn lại bằng cách đổi parent của cây gốc, không copy payload.
        root_history=[r for r in children(handoff['id']) if r['name']=='04_LICH_SU_AUDIT']
        if root_history:move(root_history[0]['id'],archive['id'])
        move(dedup['folder']['id'],archive['id'])
        for row in master['assets']:
            if row['tier']=='archive' and row['role']!='COLD_HISTORY':
                parent=archive['id']
                for segment in row['drive_path'].split('/')[:-1]:parent=folder(parent,segment)['id']
                move(row['file_id'],parent,row['sha256'])
        # Hướng dẫn/manifest cũ được giữ nguyên bytes ở kho lịch sử, tránh dùng nhầm bản cũ.
        for row in children(handoff['id']):
            if row['mimeType']!='application/vnd.google-apps.folder':move(row['id'],old_guides['id'],row.get('sha256Checksum'))
        ready=[r for r in master['assets'] if r['tier']=='ready']
        historical=[r for r in master['assets'] if r['tier']=='archive']
        result=dict(status='HANDOFF_AND_NONHANDOFF_ARCHIVES_SEPARATED',handoff_folder=handoff,archive_folder=archive,
                    ready_assets=ready,historical_assets=historical,dedup_archive=meta(dedup['file']['id']),changes=changes,
                    original_manifest_preserved='research_tracking/runs/full-project-transfer-20261118-01/MANIFEST_BAN_GIAO.json')
        (B/'DRIVE_SEPARATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print('DRIVE_SEPARATED',len(ready),'handoff',len(historical),'archive',archive['webViewLink'],flush=True)

if __name__=='__main__':main()
