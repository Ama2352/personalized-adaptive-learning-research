"""Chỉ cho phép gỡ bản trùng đã hash và có bản phục hồi; không xóa."""
from pathlib import Path
import json,hashlib,os
from prepare import ROOT,B,OLD,WORK,sha

def main():
    remote=json.loads((B/'DRIVE_ACCEPTANCE.json').read_text(encoding='utf-8'))
    assert remote['status']=='REMOTE_ARCHIVE_SHA256_SIZE_OWNER_PARENT_VERIFIED'
    package=json.loads((B/'DEDUP_PACKAGE.json').read_text(encoding='utf-8'))
    assert remote['file']['sha256Checksum']==package['sha256']
    recon=json.loads((B/'RECONSTRUCTION_ACCEPTANCE.json').read_text(encoding='utf-8'))
    assert recon['status']=='ALL_SNAPSHOT_RECONSTRUCTION_SOURCES_VERIFIED'
    staging=json.loads((B/'STAGING_PLAN.json').read_text(encoding='utf-8'))
    assert not staging['failed']
    content={r['sha256'] for r in package['members']}
    protected=json.loads((B/'PROTECTED_BEFORE.json').read_text(encoding='utf-8'))
    protected_paths={r['path'].lower() for r in protected['files']}
    files=[];relocation=[]
    for row in staging['files']:
        assert row['sha256'] in content and row['path'].lower() not in protected_paths
        source=ROOT/row['path'];keeper=ROOT/row['keeper']
        st=source.stat();ks=keeper.stat()
        assert st.st_size==ks.st_size==row['bytes'] and st.st_mtime_ns==row['mtime_ns'] and ks.st_mtime_ns==row['keeper_mtime_ns']
        files.append(dict(**row,category='STAGING_DUPLICATE'))
        relocation.append(dict(path=row['path'],sha256=row['sha256'],bytes=row['bytes'],keeper=row['keeper'],drive_archive_id=remote['file']['id'],reconstruction='Dùng keeper đúngSHA hoặc CONTENT/<SHA> trong archive; đặt lại vào path gốc theo snapshot_manifest.',snapshot_manifest=row['snapshot_manifest']))
    # CONTENT chỉ là hardlink/bản sao phụ; manifest và metadata tại root vẫn giữ local.
    old=json.loads((OLD/'MANIFEST.json').read_text(encoding='utf-8'))
    for row in old['content_files']:
        source=(OLD/row['path']).resolve();keeper=(ROOT/row['keeper']).resolve()
        assert source.is_relative_to((OLD/'CONTENT').resolve()) and keeper.is_relative_to(ROOT)
        a,st=sha(source);b,ks=sha(keeper)
        assert a==b==row['sha256'] and st.st_size==ks.st_size==row['bytes'] and a in content
        files.append(dict(path=source.relative_to(ROOT).as_posix(),keeper=row['keeper'],bytes=st.st_size,sha256=a,mtime_ns=st.st_mtime_ns,file_id=st.st_ino,nlink=st.st_nlink,category='DEDUP_SECONDARY_CONTENT'))
    # Các hardlink trong lượt kiểm phục hồi là fixture của chính run này.
    for row in recon['physical_probe']['files_verified']:
        files.append(dict(**row,category='OWN_RECONSTRUCTION_PROBE'))
    # ZIP cục bộ vừa upload chỉ là gói vận chuyển; bản gốc và bản Drive vẫn giữ.
    source=ROOT/package['path'];digest,st=sha(source)
    assert digest==remote['file']['sha256Checksum']
    files.append(dict(path=package['path'],bytes=st.st_size,sha256=digest,mtime_ns=st.st_mtime_ns,file_id=st.st_ino,nlink=st.st_nlink,category='UPLOADED_TRANSPORT_ZIP'))
    package_copies=B/'PACKAGE_COPIES_VERIFIED.json'
    if package_copies.exists():
        for row in json.loads(package_copies.read_text(encoding='utf-8'))['files']:
            assert row['passed'] and row['sha256']==row['drive']['sha256Checksum']
            files.append({k:v for k,v in row.items() if k not in ('drive','passed')}|dict(category='UPLOADED_HANDOFF_TRANSPORT_COPY'))
    cold=B/'COLD_COPY_INVENTORY.json'
    if cold.exists():
        fixture=json.loads(cold.read_text(encoding='utf-8'))
        assert fixture['status']=='OWN_COMPLETED_RESTORE_FIXTURE_INVENTORIED'
        for row in fixture['files']:files.append(dict(**row,category='COMPLETED_COLD_RESTORE_FIXTURE'))
    allow=[ROOT/'artifacts/akt/staged',OLD/'CONTENT',WORK/'reconstruction-probe',WORK,ROOT/'artifacts/akt/runtime/project-transfer-20261118-01/packages',ROOT/'artifacts/akt/runtime/project-transfer-20261118-01/cold-project']
    seen=set()
    for row in files:
        p=(ROOT/row['path']).resolve()
        assert p.is_relative_to(ROOT) and any(p.is_relative_to(a.resolve()) for a in allow)
        assert row['path'] not in seen and row['path'].lower() not in protected_paths
        seen.add(row['path'])
    forbidden=['dataset/','artifacts/bkt_baseline/','venv/','.venv/','.wsl/','.git/','research_tracking/','src/','scripts/','tests/','third_party/']
    assert not any(any(r['path'].lower().startswith(f) for f in forbidden) for r in files)
    plan=dict(status='READY_FOR_AUTHORIZED_DUPLICATE_UNLINK',root=str(ROOT.resolve()),allowed_roots=[str(p.resolve()) for p in allow],files=files,logical_bytes=sum(r['bytes'] for r in files),remote_backup=remote['file'])
    (B/'DELETE_PLAN.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    (B/'RELOCATION.json').write_text(json.dumps(dict(status='RELOCATION_PENDING_UNLINK',files=relocation,archive=remote['file'],original_manifests_unchanged=True),ensure_ascii=False,indent=2),encoding='utf-8')
    print('DELETE_PLAN',len(files),plan['logical_bytes'],'bytes; original manifests/models/results protected',flush=True)

if __name__=='__main__':main()
