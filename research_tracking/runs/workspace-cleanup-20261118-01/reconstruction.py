"""Kiểm toàn snapshot bằng ánh xạ phục hồi và một phục hồi hardlink thật."""
from pathlib import Path
import json,hashlib,collections,os,concurrent.futures
from prepare import ROOT,B,WORK,sha

def main():
    plan=json.loads((B/'STAGING_PLAN.json').read_text(encoding='utf-8'))
    by_manifest=collections.defaultdict(dict)
    for row in plan['files']:by_manifest[row['snapshot_manifest']][row['snapshot_member']]=row
    reports=[];extra_checks=[]
    for name,removed in by_manifest.items():
        manifest=ROOT/name;data=json.loads(manifest.read_text(encoding='utf-8'))
        count=0
        for relative,pin in data['files'].items():
            if relative in removed:
                row=removed[relative]
                assert row['sha256']==pin['sha256'] and row['bytes']==pin['bytes']
                assert (ROOT/row['keeper']).is_file()
            else:
                path=manifest.parent/'project'/relative
                extra_checks.append((path,pin))
            count+=1
        reports.append(dict(manifest=name,manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),members=count,relocated_members=len(removed)))
    def check(item):
        path,pin=item;digest,st=sha(path)
        assert digest==pin['sha256'] and st.st_size==pin['bytes'],str(path)
        return True
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        count=sum(pool.map(check,extra_checks))
    # Một snapshot dựng lại toàn bộ bằng hardlink trong vùng thử riêng.
    sample=min(reports,key=lambda r:r['members']);manifest=ROOT/sample['manifest']
    data=json.loads(manifest.read_text(encoding='utf-8'));removed=by_manifest[sample['manifest']]
    probe=WORK/'reconstruction-probe';probe.mkdir(exist_ok=False)
    probe_inventory=[]
    for relative,pin in data['files'].items():
        source=ROOT/removed[relative]['keeper'] if relative in removed else manifest.parent/'project'/relative
        target=probe/relative
        assert target.resolve().is_relative_to(probe.resolve())
        target.parent.mkdir(parents=True,exist_ok=True);os.link(source,target)
        digest,st=sha(target);assert digest==pin['sha256'] and st.st_size==pin['bytes']
        probe_inventory.append(dict(path=target.relative_to(ROOT).as_posix(),bytes=st.st_size,sha256=digest,mtime_ns=st.st_mtime_ns,file_id=st.st_ino,nlink=st.st_nlink))
    result=dict(status='ALL_SNAPSHOT_RECONSTRUCTION_SOURCES_VERIFIED',snapshots=reports,
                relocated_members=sum(r['relocated_members'] for r in reports),unchanged_members_verified=count,
                physical_probe=dict(snapshot=sample['manifest'],files=len(probe_inventory),files_verified=probe_inventory))
    (B/'RECONSTRUCTION_ACCEPTANCE.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('RECONSTRUCTION',len(reports),'snapshots',result['relocated_members'],'relocated',count,'unchanged',len(probe_inventory),'physical probe files',flush=True)

if __name__=='__main__':main()
