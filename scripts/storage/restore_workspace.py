"""Phục hồi đúng một đường dẫn từ file/gói đã tải Drive; kiểm SHA, không ghi đè khác nội dung."""
from pathlib import Path
import argparse,gzip,hashlib,json,os,tempfile,zipfile

def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def safe_path(root,relative):
    if not isinstance(relative,str) or not relative or '\\' in relative or ':' in relative:
        raise ValueError('Đường dẫn tương đối không hợp lệ')
    parts=relative.split('/')
    if any(p in ('','.','..') or p.endswith((' ','.')) for p in parts):raise ValueError('Đường dẫn không an toàn')
    reserved={'CON','PRN','AUX','NUL'}|{prefix+str(i) for prefix in ('COM','LPT') for i in range(1,10)}
    if any(p.split('.')[0].upper() in reserved for p in parts):raise ValueError('Tên thiết bị Windows không hợp lệ')
    root=Path(root).resolve();target=root.joinpath(*parts)
    if not target.resolve().is_relative_to(root):raise ValueError('Đường dẫn vượt thư mục đích')
    current=root
    for part in parts:
        current=current/part
        if current.is_symlink() or current.is_junction():raise ValueError('Không phục hồi qua symlink/junction')
    return target

def find_download(downloads,meta):
    downloads=Path(downloads).resolve();name=meta['name'];file_id=meta['id']
    candidates=[downloads/(file_id+'--'+name),downloads/file_id,downloads/name]
    candidates.extend(downloads.rglob(name))
    for p in dict.fromkeys(candidates):
        if p.is_file() and p.resolve().is_relative_to(downloads) and not p.is_symlink():
            if p.stat().st_size==int(meta['size']) and digest(p)==meta['sha256Checksum']:return p
    raise FileNotFoundError('Thiếu bản tải đúng SHA: '+file_id+'--'+name)

def restore_one(manifest,relative,downloads,root):
    row=next((r for r in manifest['files'] if r['path']==relative),None)
    if row is None:raise ValueError('Đường dẫn không có trong chỉ mục')
    target=safe_path(root,relative)
    if target.exists():
        if not target.is_file() or target.stat().st_size!=row['bytes'] or digest(target)!=row['sha256']:
            raise ValueError('Đích đã có nội dung khác; giữ nguyên')
        return False
    ref=row.get('storage') or manifest['contents'][row['sha256']]['storage']
    drive=manifest['drive_files']
    ids=ref.get('file_ids') or [ref['file_id']]
    sources=[find_download(downloads,drive[file_id]) for file_id in ids]
    target.parent.mkdir(parents=True,exist_ok=True)
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent,prefix='.storage-restore-',delete=False) as output:
            temporary=Path(output.name);combined=hashlib.sha256();total=0
            def copy(stream):
                nonlocal total
                for block in iter(lambda:stream.read(1024**2),b''):
                    if total+len(block)>row['bytes']:raise ValueError('Dữ liệu vượt kích thước đã pin')
                    output.write(block);combined.update(block);total+=len(block)
            if ref['kind'] in ('bulk_member','dedup_member'):
                with zipfile.ZipFile(sources[0]) as archive:
                    with archive.open(ref['member']) as stream:copy(stream)
            elif ref['kind'] in ('drive_file','drive_multipart'):
                for source in sources:
                    with source.open('rb') as stream:copy(stream)
            else:raise ValueError('Loại lưu trữ chưa được hỗ trợ')
            output.flush();os.fsync(output.fileno())
        if total!=row['bytes'] or combined.hexdigest()!=row['sha256']:raise ValueError('Nội dung phục hồi không khớp SHA/kích thước')
        if row.get('mtime_ns') is not None:os.utime(temporary,ns=(row['mtime_ns'],row['mtime_ns']))
        # Hardlink công bố nguyên tử và từ chối ghi đè nếu có race với người dùng.
        os.link(temporary,target)
        return True
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True,help='STORAGE_INDEX.json.gz hoặc relocation JSON')
    p.add_argument('--path',required=True,help='Đường dẫn tương đối chính xác cần phục hồi')
    p.add_argument('--downloads',type=Path,help='Thư mục giữ file tải từ Drive')
    p.add_argument('--root',type=Path,help='Thư mục project đích; nên thử ở thư mục mới trước')
    args=p.parse_args()
    opener=gzip.open if args.manifest.suffix=='.gz' else open
    with opener(args.manifest,'rt',encoding='utf-8') as stream:manifest=json.load(stream)
    row=next((r for r in manifest['files'] if r['path']==args.path),None)
    if row is None:p.error('Đường dẫn không có trong chỉ mục')
    ref=row.get('storage') or manifest['contents'][row['sha256']]['storage']
    ids=ref.get('file_ids') or [ref['file_id']]
    if args.root is None:
        for file_id in ids:
            meta=manifest['drive_files'][file_id]
            print(json.dumps(dict(file_id=file_id,name=meta['name'],sha256=meta['sha256Checksum'],bytes=int(meta['size']),url=meta.get('webViewLink')),ensure_ascii=False))
        return
    if args.downloads is None:p.error('Cần --downloads khi phục hồi')
    restored=restore_one(manifest,args.path,args.downloads,args.root)
    print('RESTORED_SHA256_VERIFIED' if restored else 'ALREADY_PRESENT_SHA256_VERIFIED',args.path)

if __name__=='__main__':main()
