"""Sao chép server-side đúng13backup sang owner Sang, không tải payload."""
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
API = 'https://www.googleapis.com/drive/v3'
ACCOUNT = 'honguyenminhsang2005@gmail.com'
PARENT = '1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7'
FOLDER_NAME = 'verified-model-backups-sang-20261117-01'
FOLDER = 'application/vnd.google-apps.folder'
FIELDS = 'id,name,mimeType,owners(emailAddress),parents,size,sha256Checksum,trashed,capabilities(canCopy),appProperties'
STATE = HERE/'MODEL_BACKUP_COPY_STATE01.json'


def stamp():
    return datetime.now(timezone.utc).isoformat()


def save(state):
    temporary = STATE.with_suffix('.json.tmp')
    with temporary.open('w',encoding='utf-8') as stream:
        json.dump(state,stream,ensure_ascii=False,indent=2)
        stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,STATE)


def checked(response):
    if response.status_code not in (200,201):
        raise RuntimeError('Drive request HTTP'+str(response.status_code))
    return response.json()


def get(session,path,params):
    import requests
    for attempt in range(2):
        try:
            response=session.get(API+path,params=params,timeout=45,allow_redirects=False)
            if response.status_code in (429,500,502,503,504) and attempt==0:
                time.sleep(1)
                continue
            return checked(response)
        except requests.RequestException:
            if attempt:
                raise RuntimeError('Drive metadata network unavailable') from None
            time.sleep(1)


def children(session,parent,name):
    escaped=name.replace('\\','\\\\').replace("'","\\'")
    result=[]
    token=None
    while True:
        params=dict(q=f"'{parent}' in parents and name = '{escaped}' and trashed = false",
            fields='nextPageToken,files('+FIELDS+')',pageSize=100)
        if token:params['pageToken']=token
        payload=get(session,'/files',params)
        result.extend(payload.get('files',[]))
        token=payload.get('nextPageToken')
        if not token:return result


def owned(meta):
    return ACCOUNT in [row.get('emailAddress','').lower() for row in meta.get('owners',[])]


def matching(meta,row,parent):
    return (not meta.get('trashed') and meta.get('name')==row['name']
        and parent in meta.get('parents',[]) and owned(meta)
        and int(meta.get('size',-1))==row['bytes'] and meta.get('sha256Checksum')==row['sha256'])


def execute(session,inventory):
    if (len(inventory)!=13 or len({row['id'] for row in inventory})!=13
            or len({row['name'] for row in inventory})!=13 or sum(row['bytes'] for row in inventory)>500*1024**2):
        raise ValueError('Exactly13 fixed files within500MiB required')
    state=json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else dict(
        status='PREFLIGHT',started_at=stamp(),account=ACCOUNT,parent_id=PARENT,source_files=inventory,copies=[])
    if state['source_files']!=inventory:
        raise ValueError('Immutable copy inventory changed')
    about=get(session,'/about',{'fields':'user(emailAddress),storageQuota'})
    if about['user']['emailAddress'].lower()!=ACCOUNT:
        raise ValueError('Drive account mismatch')
    quota=about.get('storageQuota',{})
    total=sum(row['bytes'] for row in inventory)
    for row in inventory:
        meta=get(session,'/files/'+row['id'],{'fields':FIELDS})
        if (meta.get('trashed') or meta.get('sha256Checksum')!=row['sha256']
                or int(meta.get('size',-1))!=row['bytes'] or not meta.get('capabilities',{}).get('canCopy')):
            state.update(status='BLOCKED_SOURCE_METADATA_OR_COPY_CAPABILITY',blocked_source_id=row['id'],at=stamp())
            save(state)
            raise ValueError('Source metadata mismatch or canCopyFalse')
    folders=children(session,PARENT,FOLDER_NAME)
    if folders:
        if len(folders)!=1 or folders[0]['mimeType']!=FOLDER or not owned(folders[0]):
            raise ValueError('Destination folder ambiguous or not owned by Sang')
        folder=folders[0]
    else:
        # Folder creation is not automatically retried after uncertain POST.
        folder=checked(session.post(API+'/files',params={'fields':FIELDS},json={
            'name':FOLDER_NAME,'mimeType':FOLDER,'parents':[PARENT]},timeout=45,allow_redirects=False))
        if not owned(folder) or PARENT not in folder.get('parents',[]):
            raise ValueError('Created folder owner/parent mismatch')
    parent=folder['id']
    existing={row['name']:children(session,parent,row['name']) for row in inventory}
    copy_bytes=sum(row['bytes'] for row in inventory if not any(matching(meta,row,parent)
                   for meta in existing[row['name']]))
    if 'limit' in quota and int(quota['limit'])-int(quota.get('usage',0))<copy_bytes:
        state.update(status='BLOCKED_DRIVE_QUOTA',required_new_bytes=copy_bytes,at=stamp())
        save(state)
        raise ValueError('Insufficient Sang Drive quota for bounded copy')
    state.update(status='COPYING',folder_id=parent,folder_url='https://drive.google.com/drive/folders/'+parent,
                 source_preflight_verified=True,total_source_bytes=total,at=stamp())
    save(state)
    for row in inventory:
        candidates=existing[row['name']]
        matches=[meta for meta in candidates if matching(meta,row,parent)]
        if matches:
            copied=sorted(matches,key=lambda value:value['id'])[0]
            mode='REUSED_VERIFIED_COPY'
        else:
            if candidates:
                raise ValueError('Destination name has conflicting content')
            try:
                response=session.post(API+'/files/'+row['id']+'/copy',params={'fields':FIELDS},
                    json=dict(name=row['name'],parents=[parent],appProperties={'kltn_source_file_id':row['id'],
                        'kltn_source_sha256':row['sha256']}),timeout=90,allow_redirects=False)
                copied=checked(response)
            except Exception:
                # A timeout may have already created a server copy. Reconcile
                # before stopping, never repeat an uncertain copy POST.
                matches=[meta for meta in children(session,parent,row['name']) if matching(meta,row,parent)]
                if not matches:
                    state.update(status='COPY_ACK_UNCERTAIN_STOPPED',uncertain_source_id=row['id'],at=stamp())
                    save(state)
                    raise RuntimeError('Copy acknowledgement uncertain; inspect saved state') from None
                copied=matches[0]
            mode='SERVER_SIDE_COPY'
        fresh=get(session,'/files/'+copied['id'],{'fields':FIELDS})
        if not matching(fresh,row,parent):
            raise ValueError('Copied file SHA/byte/owner/parent mismatch')
        receipt=dict(source_id=row['id'],source_name=row['name'],destination_id=fresh['id'],
            destination_url='https://drive.google.com/file/d/'+fresh['id']+'/view',bytes=row['bytes'],sha256=row['sha256'],
            owners=[owner.get('emailAddress') for owner in fresh['owners']],parent_id=parent,mode=mode,verified_at=stamp())
        state['copies']=[entry for entry in state['copies'] if entry['source_id']!=row['id']]+[receipt]
        save(state)
        print(json.dumps(dict(status='SERVER_COPY_VERIFIED',name=row['name'],bytes=row['bytes'],owner_sang=True)),flush=True)
    state.update(status='COMPLETE_THIRTEEN_SERVER_COPIES_SHA_OWNER_VERIFIED',finished_at=stamp(),
                 original_files_deleted=False,permissions_changed=False,payload_downloaded=False,modal_called=False)
    save(state)
    return state


def verify_copies(session,state,source_owners):
    about=get(session,'/about',{'fields':'user(emailAddress)'})
    if about['user']['emailAddress'].lower()!=ACCOUNT:
        raise ValueError('Drive account mismatch')
    rows=[]
    copies={row['source_id']:row for row in state['copies']}
    if len(copies)!=13:
        raise ValueError('All13 copied receipts required')
    for source in state['source_files']:
        before=source_owners[source['id']]
        original=get(session,'/files/'+source['id'],{'fields':FIELDS})
        copy=copies[source['id']]
        fresh=get(session,'/files/'+copy['destination_id'],{'fields':FIELDS})
        owners=[row.get('emailAddress') for row in original['owners']]
        if (original.get('trashed') or int(original.get('size',-1))!=source['bytes']
                or original.get('sha256Checksum')!=source['sha256'] or owners!=before['owners']
                or not matching(fresh,source,state['folder_id'])):
            raise ValueError('Post-copy source or destination mismatch')
        rows.append(dict(source_id=source['id'],destination_id=copy['destination_id'],
            sha256=source['sha256'],bytes=source['bytes'],source_owners_unchanged=owners,
            destination_owned_by_sang=True))
    return dict(status='PASS_FRESH_SOURCE_AND_DESTINATION_POSTCOPY_METADATA',account=ACCOUNT,
        verified_at=stamp(),files=rows,source_files_preserved=True,payload_downloaded=False,modal_called=False)


def main():
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    parser=argparse.ArgumentParser()
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args()
    source=ROOT/'research_tracking/runs/artifact-retention-audit-20261116-01/DRIVE_UPLOAD_RECEIPT01.json'
    original=json.loads(source.read_text())
    inventory=[dict(id=row['id'],name=row['name'],bytes=row['bytes'],sha256=row['sha256']) for row in original['files']]
    credentials=Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'),
        ['https://www.googleapis.com/auth/drive'])
    with AuthorizedSession(credentials) as session:
        if args.verify_only:
            state=json.loads(STATE.read_text(encoding='utf-8'))
            before=json.loads((HERE/'MODEL_DRIVE_OWNERS01.json').read_text(encoding='utf-8'))
            result=verify_copies(session,state,{row['id']:row for row in before['files']})
            with (HERE/'MODEL_BACKUP_POSTCOPY_VERIFY01.json').open('x',encoding='utf-8') as stream:
                json.dump(result,stream,ensure_ascii=False,indent=2)
            print(json.dumps(dict(status=result['status'],files=len(result['files']),source_files_preserved=True)))
            return
        result=execute(session,inventory)
    print(json.dumps(dict(status=result['status'],files=len(result['copies']),bytes=result['total_source_bytes'],
                         folder_url=result['folder_url'])))


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        raise SystemExit('Server-side backup copy stopped: '+type(error).__name__) from None
