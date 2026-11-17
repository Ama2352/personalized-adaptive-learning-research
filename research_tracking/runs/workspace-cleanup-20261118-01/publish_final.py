"""Xuất source/commit cuối và manifest bàn giao mới, giữ bản cũ ở kho lịch sử."""
from pathlib import Path
from contextlib import redirect_stdout
import subprocess,json,hashlib,zipfile,sys,html,shutil,os
ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
TRANSFER=ROOT/'research_tracking/runs/full-project-transfer-20261118-01'
WORK=ROOT/'artifacts/akt/runtime/workspace-cleanup-20261118-01/publication'
sys.path.insert(0,str(ROOT/'scripts/akt'))
API='https://www.googleapis.com/drive/v3'
FIELDS='id,name,mimeType,size,sha256Checksum,parents,trashed,webViewLink,owners(emailAddress)'

def sha(path):
    path=Path(path);absolute=str(path.absolute())
    if os.name=='nt' and len(absolute)>=235 and not absolute.startswith('\\\\?\\'):path=Path('\\\\?\\'+absolute)
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def write_once(path,data):
    if isinstance(data,str):data=data.encode('utf-8')
    if path.exists():assert path.read_bytes()==data,'Nội dung gói đã tạo khác lần trước; giữ nguyên để rà'
    else:path.write_bytes(data)

def source_allowed(relative,tracked,size):
    if relative.startswith(('dataset/','.venv/','venv/','.wsl/','.git/')):return False
    if 'private' in Path(relative).parts or Path(relative).name.startswith('.env'):return False
    if relative.startswith('artifacts/'):
        return tracked and size<=10*1024**2 and relative.startswith(('artifacts/simulator/corpora/','artifacts/akt/local-tests/akt-research-runner-20261108-01/'))
    return True

def build_source_zip(source,root,head,paths):
    source=Path(source);root=Path(root).resolve()
    if source.exists():
        with zipfile.ZipFile(source) as archive:saved=json.loads(archive.read('PACKAGE_MANIFEST.json'))
        assert saved['source_head']==head,'Gói nguồn thuộc commit khác; giữ nguyên để rà'
        pins=saved['files']
        for pin in pins:assert sha(root/pin['path'])==pin['sha256'],'Nguồn đã đổi sau đóng gói'
        return pins
    partial=source.with_name(source.name+'.partial')
    if partial.exists():
        digest=sha(partial);failed=source.with_name(source.name+'.failed-'+digest[:12])
        assert partial.resolve().parent==source.resolve().parent==failed.resolve().parent
        note=source.with_name(source.name+'.failures.json')
        records=json.loads(note.read_text(encoding='utf-8')) if note.exists() else []
        records.append(dict(path=str(partial),retained_as=str(failed),bytes=partial.stat().st_size,sha256=digest))
        note.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
        if failed.exists():
            assert sha(failed)==digest;partial.unlink()
        else:partial.rename(failed)
        assert sha(failed)==digest
    pins=[]
    with zipfile.ZipFile(partial,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as archive:
        for path in sorted(paths):
            path=Path(path);assert path.resolve().is_relative_to(root) and not path.is_symlink()
            relative=path.relative_to(root).as_posix();digest=sha(path);stat=path.stat()
            archive.write(path,relative);pins.append(dict(path=relative,bytes=stat.st_size,sha256=digest))
        archive.writestr('PACKAGE_MANIFEST.json',json.dumps(dict(source_head=head,files=pins),ensure_ascii=False,separators=(',',':')))
    with zipfile.ZipFile(partial) as archive:
        for pin in pins:
            with archive.open(pin['path']) as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==pin['sha256']
    os.link(partial,source);partial.unlink()
    return pins

def cleanup_publisher_work(result,head):
    target=WORK/'source-check';owned=target/'.publisher-owned.json'
    if target.exists():
        assert target.resolve().is_relative_to(WORK.resolve()) and target.name=='source-check'
        assert owned.is_file() and json.loads(owned.read_text(encoding='utf-8'))['commit']==head
        native=Path('\\\\?\\'+str(target.resolve())) if os.name=='nt' else target
        shutil.rmtree(native)
    for key in ('source','git_bundle'):
        meta=result[key];path=WORK/meta['name']
        assert path.resolve().parent==WORK.resolve() and not path.is_symlink()
        if path.exists():
            assert sha(path)==meta['sha256Checksum'];path.unlink()
    result['local_transport_and_source_probe_removed']=True

def main():
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    from drive_resumable_upload import Uploader,atomic_json
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    assert not subprocess.check_output(['git','-c','core.excludesFile='+str(ROOT/'.git/info/exclude'),'status','--porcelain'],cwd=ROOT,text=True).strip(),'Commit xong và workingtree sạch trước xuất bản'
    completed=B/'FINAL_PUBLICATION_RECEIPT.json';cold_check=B/'final_publication/SOURCE_RESTORE_ACCEPTANCE.json'
    if completed.exists() and cold_check.exists():
        prior=json.loads(completed.read_text(encoding='utf-8'));checked=json.loads(cold_check.read_text(encoding='utf-8'))
        if prior['commit']==checked['commit']==head:
            with AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as s:
                for row in prior['checks']:
                    response=s.get(API+'/files/'+row['file_id'],params={'fields':'id,sha256Checksum,trashed'},timeout=60);response.raise_for_status();meta=response.json()
                    assert not meta['trashed'] and meta['sha256Checksum']==row['sha256']
            cleanup_publisher_work(prior,head);atomic_json(completed,prior)
            print('ALREADY_PUBLISHED_AND_DRIVE_REVERIFIED',head,flush=True);return
    WORK.mkdir(parents=True,exist_ok=True)
    source=WORK/'01_SOURCE_KLTN_FINAL.zip';bundle=WORK/'13_KLTN_GIT_FINAL.bundle'
    tracked=[p for p in subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0') if p]
    paths={ROOT/p for p in tracked}
    previous_source=json.loads((TRANSFER/'01_SOURCE_VA_HO_SO_NGHIEN_CUU.zip.manifest.json').read_text(encoding='utf-8'))
    # Giữ cả nguồn/hồ sơ an toàn đã được bàn giao trước nhưng chủ đích không theo dõi Git.
    for row in previous_source['member_inventory']:
        path=ROOT/row['path']
        if path.is_file() and source_allowed(row['path'],row['path'] in tracked,path.stat().st_size):paths.add(path)
    for relative in ('paper1','paper2','ref-papers'):
        paths.update(p for p in (ROOT/relative).rglob('*') if p.is_file() and not any(x in p.parts for x in ('.git','__pycache__')))
    for path in paths:assert source_allowed(path.relative_to(ROOT).as_posix(),path.relative_to(ROOT).as_posix() in tracked,path.stat().st_size)
    pins=build_source_zip(source,ROOT,head,paths)
    if not bundle.exists():subprocess.run(['git','bundle','create',str(bundle),'HEAD'],cwd=ROOT,check=True,capture_output=True)
    subprocess.run(['git','bundle','verify',str(bundle)],cwd=ROOT,check=True,capture_output=True)
    assert (head+' HEAD') in subprocess.check_output(['git','bundle','list-heads',str(bundle)],cwd=ROOT,text=True)
    separation=json.loads((B/'DRIVE_SEPARATION.json').read_text(encoding='utf-8'))
    original=json.loads((TRANSFER/'MANIFEST_BAN_GIAO.json').read_text(encoding='utf-8'))
    ready=separation['ready_assets'];handoff=separation['handoff_folder'];cold=separation['archive_folder']
    original_source=next(r for r in ready if r['role']=='SOURCE')
    private=ROOT/'artifacts/akt/private/drive-upload/workspace-cleanup-20261118-01/publication';private.mkdir(parents=True,exist_ok=True)
    evidence=B/'final_publication';evidence.mkdir(exist_ok=True)
    with AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as session:
        def api(method,path,**kwargs):
            response=session.request(method,API+path,timeout=90,**kwargs)
            if response.status_code not in (200,201):raise RuntimeError('DriveHTTP'+str(response.status_code))
            return response.json()
        def meta(file_id):return api('GET','/files/'+file_id,params={'fields':FIELDS})
        def folder(parent,name):
            result=api('GET','/files',params={'q':"'%s' in parents and name='%s' and trashed=false"%(parent,name),'fields':'files('+FIELDS+')'})['files']
            assert len(result)<=1
            return result[0] if result else api('POST','/files',json={'name':name,'mimeType':'application/vnd.google-apps.folder','parents':[parent]},params={'fields':FIELDS})
        def upload(path,parent,folder_name):
            stat=path.stat();digest=sha(path)
            plan=dict(source=str(path.parent.resolve()),parent_id=parent,account='honguyenminhsang2005@gmail.com',folder_name=folder_name,bytes=stat.st_size,
                      files=[dict(path=path.name,bytes=stat.st_size,sha256=digest,mtime_ns=stat.st_mtime_ns)])
            log=evidence/path.stem;log.mkdir(exist_ok=True)
            with (log/'console.log').open('a',encoding='utf-8') as output,redirect_stdout(output):
                Uploader(session,plan,private/(path.name+'.state.json'),log,chunk_bytes=64*1024**2,retries=5).run()
            receipt=json.loads((log/'RECEIPTS.json').read_text(encoding='utf-8'))[0];actual=meta(receipt['file_id'])
            assert not actual['trashed'] and actual['sha256Checksum']==digest and int(actual['size'])==stat.st_size
            return actual
        # Root của Uploader luôn là folder con: dùng parent KLTN và tên master để không tạo tầng thừa.
        source_meta=upload(source,handoff['id'],'01_SOURCE')
        bundle_meta=upload(bundle,handoff['id'],'01_SOURCE')
        source_asset=dict(file_id=source_meta['id'],name=source.name,bytes=int(source_meta['size']),sha256=source_meta['sha256Checksum'],url=source_meta['webViewLink'],drive_path='01_SOURCE/'+source.name,role='SOURCE',tier='ready',restore_mode='root',restore_order=0)
        bundle_asset=dict(file_id=bundle_meta['id'],name=bundle.name,bytes=int(bundle_meta['size']),sha256=bundle_meta['sha256Checksum'],url=bundle_meta['webViewLink'],drive_path='01_SOURCE/'+bundle.name,role='PROJECT_GIT_BUNDLE',tier='ready',restore_mode='none',restore_order=10)
        retired=[r for r in ready if r['role'] in {'SOURCE','PROJECT_GIT_BUNDLE','TRACKED_SOURCE_SUPPLEMENT'}]
        old_folder=folder(cold['id'],'00_NGUON_BAN_GIAO_CU')
        for row in retired:
            before=meta(row['file_id']);assert before['sha256Checksum']==row['sha256']
            after=before if old_folder['id'] in before['parents'] else api('PATCH','/files/'+row['file_id'],params={'addParents':old_folder['id'],'removeParents':','.join(before['parents']),'fields':FIELDS},json={})
            assert after['sha256Checksum']==row['sha256'] and after['size']==before['size']
        assets=[r for r in ready if r not in retired]+[source_asset,bundle_asset]
        final=dict(original)
        final.update(schema='KLTN_HANDOFF_FINAL_20261118',assets=assets,source_snapshot=dict(source_head=head,source_modified=[]),master_folder=handoff,
                     separate_archive_folder=cold,totals=dict(files=len(assets),bytes=sum(r['bytes'] for r in assets),ready_files=len(assets),ready_bytes=sum(r['bytes'] for r in assets)),
                     preserved_originals='Bản cũ lưu trong kho lịch sử; local payload có thể đã chuyển lạnh đúng SHA; xem STORAGE_INDEX.',interpretation='Bộ file để tiếp tục KLTN, không chứng nhận đã hoàn tất nghiên cứu hoặc runtime máy người nhận.')
        manifest=WORK/'MANIFEST_BAN_GIAO_FINAL.json';write_once(manifest,json.dumps(final,ensure_ascii=False,indent=2))
        # Helper đã có kiểm hồi quy và hỗ trợ đường dẫn dài/Git bundle/upstream.
        helper=WORK/'khoi_phuc_ban_giao.py';write_once(helper,(TRANSFER/'khoi_phuc_ban_giao.py').read_bytes())
        requirements=WORK/'requirements-tai-goi.txt';write_once(requirements,(TRANSFER/'requirements-tai-goi.txt').read_bytes())
        requirement_extra=WORK/'requirements-local-bo-sung.txt';write_once(requirement_extra,(TRANSFER/'requirements-local-bo-sung.txt').read_bytes())
        guide=WORK/'BAT_DAU_TAI_DAY_FINAL.md'
        guide_text=f'''# Tiếp quản KLTN — bản cuối18/11/2026

Source đã commit tại `{head}`. Bộ bàn giao có{len(assets)}file dữ liệu/gói, tổng{sum(r['bytes'] for r in assets)/1e9:.3f}GB. Kho lịch sử tách riêng: {cold['webViewLink']}.

## Bắt đầu

1. Tải MANIFEST_BAN_GIAO_FINAL.json, khoi_phuc_ban_giao.py, hai requirements và SHA256SUMS_FINAL.txt ở gốc. Kiểm SHA theo bảng.
2. Tải các gói giữ nguyên đường dẫn01_SOURCE/02_DU_LIEU/03_ARTIFACTS_VA_KET_QUA. `core` bỏ CSV gốc/cache tăng tốc, `ready` giữ đủ cả; không cần tải kho lịch sử để bắt đầu.
3. Dùng Python3.13 và Git. Tạo .venv trong project mới rồi kiểm/khôi phục bằng lệnh bên dưới. Người nhận tự đăng nhập Drive/OAuth nếu dùng downloader; không nhận token của chủ repo.

```powershell
py -3.13 -m venv D:/Nhan_KLTN/project/.venv
D:/Nhan_KLTN/project/.venv/Scripts/python.exe D:/Nhan_KLTN/khoi_phuc_ban_giao.py --manifest D:/Nhan_KLTN/MANIFEST_BAN_GIAO_FINAL.json --downloads D:/Nhan_KLTN/goi --tier ready --extract --root D:/Nhan_KLTN/project
```

Lượt khôi phục đầu cần project mới/trống, có thể có .venv. Helper kiểm SHA từng gói/member, ghép parts, khôi phục15model, AKT upstream đúng commit và Git HEAD của source. Không tự training.

Sau khôi phục, cài requirements của môi trường phù hợp rồi đọc README.md, docs/REPOSITORY_MAP.md, docs/operations/STORAGE_AND_HANDOFF.md và báo cáo GVHD hiện hành. Kiểm import/smoke trên máy mới trước chạy nghiên cứu. Linux/CUDA dùng lock/runbook của run, không trộn wheel Windows.

## Công việc còn lại

Junyi A0–A3 expert đã đủ selection/refit/calibration/outer fold4. Tiếp tục lifecycle Grade10 và comparator, đánh giá mastery/controller/vòng kín, graph noise/history/profile và đối chứng thứ tự Junyi, rồi tổng hợp nhận định RQ, demo và luận văn. Chấp nhận kết quả âm hoặc bất định; không tối ưu số liệu để buộc model thắng.

Catalog research_tracking/storage/20261118_STORAGE_INDEX.json.gz và scripts/storage/restore_workspace.py tra file cũ đã chuyển lạnh. Kho lịch sử và hồ sơ dọn được giữ riêng, không thay frozen manifests. Quyền truy cập tài khoản người nhận và runtime mới phải được chủ thư mục/người nhận kiểm riêng.
'''
        write_once(guide,guide_text)
        web=WORK/'BAT_DAU_TAI_DAY_FINAL.html';write_once(web,'<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Tiếp quản KLTN</title><style>body{max-width:960px;margin:40px auto;padding:0 20px;font:16px/1.6 system-ui}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><pre>'+html.escape(guide_text)+'</pre></html>')
        sums=WORK/'SHA256SUMS_FINAL.txt'
        docs=[manifest,helper,requirements,requirement_extra,guide,web]
        write_once(sums,'\n'.join(sha(p)+'  '+p.name for p in docs)+'\n')
        published=[]
        for path in docs+[sums]:published.append(upload(path,handoff['parents'][0],handoff['name']))
        # Đọc lại toàn bộ133asset, kiểm từng SHA và ancestry dưới master mới.
        cache={};checks=[]
        def beneath(file_id):
            if file_id==handoff['id']:return True
            if file_id in cache:return cache[file_id]
            data=meta(file_id);value=any(beneath(p) for p in data.get('parents',[]));cache[file_id]=value;return value
        for row in assets:
            actual=meta(row['file_id'])
            assert not actual['trashed'] and actual['sha256Checksum']==row['sha256'] and int(actual['size'])==row['bytes'] and beneath(row['file_id'])
            checks.append(dict(file_id=row['file_id'],sha256=row['sha256'],passed=True))
        result=dict(status='FINAL_SOURCE_COMMIT_AND_ALL_HANDOFF_ASSETS_DRIVE_VERIFIED',commit=head,handoff_folder=handoff,archive_folder=cold,assets=len(assets),bytes=sum(r['bytes'] for r in assets),source_files=len(pins),source=source_meta,git_bundle=bundle_meta,root_documents=published,retired_assets=retired,checks=checks,local_manifest=manifest.relative_to(ROOT).as_posix())
        atomic_json(B/'FINAL_PUBLICATION_RECEIPT.json',result)
    # Kiểm source thật từ gói cuối trong thư mục mới, không tạo bản môi trường/dataset mới.
    sys.path.insert(0,str(TRANSFER));from khoi_phuc_ban_giao import extract
    target=WORK/'source-check';owned=target/'.publisher-owned.json'
    if target.exists():assert owned.is_file() and json.loads(owned.read_text(encoding='utf-8'))['commit']==head
    else:
        target.mkdir();owned.write_text(json.dumps(dict(commit=head)),encoding='utf-8')
    extract(source,target)
    for pin in pins:assert sha(target/pin['path'])==pin['sha256']
    subprocess.run([str(ROOT/'.venv/Scripts/python.exe'),'-B','-m','unittest','discover','-s',str(target/'tests'),'-p','test_storage_restore.py','-v'],cwd=target,check=True,capture_output=True)
    subprocess.run([str(ROOT/'.venv/Scripts/python.exe'),'-B','-m','unittest','discover','-s',str(target/'tests'),'-p','test_handoff_source_package.py','-v'],cwd=target,check=True,capture_output=True)
    atomic_json(B/'final_publication/SOURCE_RESTORE_ACCEPTANCE.json',dict(status='FINAL_SOURCE_ARCHIVE_ALL_MEMBERS_AND_RESTORE_TESTS_VERIFIED',commit=head,files=len(pins),storage_restore_tests=8,source_package_tests=2,source_sha256=sha(source),bundle_sha256=sha(bundle)))
    # Bản thử và gói vận chuyển của chính publisher đã có SHA/Drive proof, không giữ thêm bản nặng local.
    cleanup_publisher_work(result,head)
    atomic_json(B/'FINAL_PUBLICATION_RECEIPT.json',result)
    print('FINAL_PUBLICATION_VERIFIED',head,len(assets),sum(r['bytes'] for r in assets),handoff['webViewLink'],flush=True)

if __name__=='__main__':main()
