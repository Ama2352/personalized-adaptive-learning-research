"""Inventory bản project dựng thử đã nghiệm thu; chỉ ghi allowlist file."""
from pathlib import Path
import json,hashlib,concurrent.futures,os
ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
NORMAL_TARGET=ROOT/'artifacts/akt/runtime/project-transfer-20261118-01/cold-project'
TARGET=Path('\\\\?\\'+str(NORMAL_TARGET.resolve()))
TRANSFER=ROOT/'research_tracking/runs/full-project-transfer-20261118-01'

def main():
    marker=json.loads((TARGET/'.cold-owned.json').read_text(encoding='utf-8'))
    assert marker['owner']=='full-project-transfer-20261118-01' and Path(marker['source']).resolve()==ROOT.resolve()
    acceptance=json.loads((TRANSFER/'COLD_RESTORE_ACCEPTANCE01.json').read_text(encoding='utf-8'))
    assert acceptance['required_input_files']==790 and acceptance['primary_akt_models']==15
    git=json.loads((TRANSFER/'COLD_GIT_ACCEPTANCE01.json').read_text(encoding='utf-8'))
    assert git['status']=='ALL_TRACKED_SOURCE_AND_GIT_RESTORE_VERIFIED'
    paths=[]
    for directory,dirs,files in os.walk(TARGET,followlinks=False):
        for name in dirs:
            p=Path(directory)/name
            assert not p.is_symlink() and not p.is_junction()
        for name in files:
            p=Path(directory)/name
            assert p.resolve().is_relative_to(TARGET.resolve()) and not p.is_symlink()
            paths.append(p)
    def pin(p):
        before=p.stat()
        with p.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        st=p.stat();assert before.st_mtime_ns==st.st_mtime_ns and before.st_size==st.st_size
        normal=NORMAL_TARGET/p.relative_to(TARGET)
        return dict(path=normal.relative_to(ROOT).as_posix(),bytes=st.st_size,sha256=digest,mtime_ns=st.st_mtime_ns,file_id=st.st_ino,nlink=st.st_nlink)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(pin,paths))
    (B/'COLD_COPY_INVENTORY.json').write_text(json.dumps(dict(status='OWN_COMPLETED_RESTORE_FIXTURE_INVENTORIED',files=rows,bytes=sum(r['bytes'] for r in rows),acceptance_sources=['COLD_RESTORE_ACCEPTANCE01.json','COLD_GIT_ACCEPTANCE01.json']),ensure_ascii=False,indent=2),encoding='utf-8')
    print('COLD_COPY',len(rows),sum(r['bytes'] for r in rows),'bytes; completed fixture',flush=True)

if __name__=='__main__':main()
