"""Kiểm closure toàn bộ file nguồn, Git restore và metadata Drive ở đúng masterfolder."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
TARGET=ROOT/'artifacts/akt/runtime/project-transfer-20261118-01/cold-project'
sys.path.insert(0,str(B))
from khoi_phuc_ban_giao import extract,digest,selected,local_path


def main():
    master=json.loads((B/'MANIFEST_BAN_GIAO.json').read_text(encoding='utf-8'))
    assert len(master['primary_akt_models'])==15 and len(master['assets'])==176
    assert len({r['file_id'] for r in master['assets']})==len(master['assets'])
    assert len({r['drive_path'] for r in master['assets']})==len(master['assets'])
    coverage=json.loads((B/'TRACKED_COVERAGE01.json').read_text(encoding='utf-8'))
    assert coverage['missing_after_supplement']==[]
    output=ROOT/'artifacts/akt/runtime/project-transfer-20261118-01/packages'
    extract(output/'14_GIT_TRACKED_BO_SUNG.zip',TARGET)
    if not (TARGET/'.git').exists():
        subprocess.run(['git','init',str(TARGET)],check=True)
        subprocess.run(['git','-C',str(TARGET),'config','core.longpaths','true'],check=True)
        subprocess.run(['git','-C',str(TARGET),'symbolic-ref','HEAD','refs/heads/main'],check=True)
        subprocess.run(['git','-C',str(TARGET),'fetch',str(output/'13_KLTN_GIT.bundle'),'HEAD'],check=True)
        subprocess.run(['git','-C',str(TARGET),'reset','--mixed',master['source_snapshot']['source_head']],check=True)
    subprocess.run(['git','-C',str(TARGET),'config','core.longpaths','true'],check=True)
    modified=subprocess.check_output(['git','-C',str(TARGET),'diff','--name-only'],text=True).splitlines()
    assert modified==master['source_snapshot']['source_modified'],modified[:10]
    tracked=subprocess.check_output(['git','-C',str(TARGET),'ls-files','-z']).decode().split('\0')
    missing=[p for p in tracked if p and not local_path(TARGET,p).is_file()]
    assert not missing,missing[:10]
    local_result=dict(status='ALL_TRACKED_SOURCE_AND_GIT_RESTORE_VERIFIED',tracked_files=len(tracked)-1,
        preserved_working_changes=modified,source_head=master['source_snapshot']['source_head'])
    (B/'COLD_GIT_ACCEPTANCE01.json').write_text(json.dumps(local_result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    sys.path.insert(0,str(ROOT/'research_tracking/runs/report-drive-snapshot-20261117-01'))
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    import publish_snapshot as pub
    with AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as session:
        folders={master['master_folder']['id']:True};count=0
        def inside(folder):
            if folder in folders:return folders[folder]
            data=pub.checked(session.get(pub.API+'/files/'+folder,params={'fields':'id,parents,trashed'},timeout=90))
            valid=not data.get('trashed') and any(inside(p) for p in data.get('parents',[]))
            folders[folder]=valid;return valid
        for row in master['assets']:
            data=pub.checked(session.get(pub.API+'/files/'+row['file_id'],params={'fields':'id,name,size,sha256Checksum,parents,owners(emailAddress),trashed'},timeout=120))
            assert not data['trashed'] and data['owners'][0]['emailAddress']=='honguyenminhsang2005@gmail.com'
            assert int(data['size'])==row['bytes'] and data['sha256Checksum']==row['sha256'] and data['name']==row['name']
            assert len(data['parents'])==1 and inside(data['parents'][0])
            count+=1
            if count%25==0:print('FINAL_DRIVE_METADATA_PASS',count,flush=True)
        result=dict(status='ALL_MASTER_ASSETS_SHA256_OWNER_AND_ANCESTRY_VERIFIED',files=count,bytes=master['totals']['bytes'],
            ready_bytes=sum(a['bytes'] for a in master['assets'] if selected(a,'ready')),
            core_bytes=sum(a['bytes'] for a in master['assets'] if selected(a,'core')),
            master_folder=master['master_folder'],checks='SHA server và size từng asset; mọi parent nằm dưới master; Git/corpus/input/checkpoint đã kiểm cold restore riêng.')
        (B/'FINAL_ACCEPTANCE01.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('FINAL_HANDOFF_ACCEPTANCE_PASS',count,flush=True)


if __name__=='__main__':main()
