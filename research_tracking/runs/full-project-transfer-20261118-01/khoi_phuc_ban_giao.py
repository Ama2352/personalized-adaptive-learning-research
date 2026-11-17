"""Tải tiếp tục, kiểm SHA và khôi phục KLTN vào thư mục mới. Python stdlib đủ cho verify/extract."""
from pathlib import Path,PurePosixPath
import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import time
import zipfile


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def local_path(root,name):
    posix=PurePosixPath(name)
    if posix.is_absolute() or '..' in posix.parts or '\\' in name or ':' in name:
        raise ValueError('Đường dẫn archive không an toàn.')
    path=root.joinpath(*posix.parts)
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Đường dẫn thoát thư mục đích.')
    # Dùng extended-length path cho Win32, giữ nguyên cấu hình global của máy.
    absolute=str(path.absolute())
    if os.name=='nt' and len(absolute)>=235 and not absolute.startswith('\\\\?\\'):
        path=Path('\\\\?\\'+absolute)
    return path


def selected(asset,tier):
    if tier=='archive':
        return True
    if asset['tier']=='archive':
        return False
    return tier!='core' or asset['role'] not in {'RAW_DATA','READY_CACHE','CONFIDENCE_REPLAY_CACHE'}


def obtain(session,asset,path):
    if path.exists():
        if path.stat().st_size!=asset['bytes'] or digest(path)!=asset['sha256']:
            raise ValueError('File đã có khác SHA, giữ nguyên để rà: '+str(path))
        return
    path.parent.mkdir(parents=True,exist_ok=True)
    part=path.with_name(path.name+'.part')
    api='https://www.googleapis.com/drive/v3/files/'+asset['file_id']
    meta=session.get(api,params={'fields':'id,size,sha256Checksum,trashed'},timeout=90)
    meta.raise_for_status();meta=meta.json()
    if meta.get('trashed') or int(meta['size'])!=asset['bytes'] or meta.get('sha256Checksum')!=asset['sha256']:
        raise ValueError('Drive metadata đã khác manifest.')
    for attempt in range(6):
        offset=part.stat().st_size if part.exists() else 0
        if offset>asset['bytes']:
            raise ValueError('File .part lớn hơn kế hoạch.')
        if offset==asset['bytes']:
            break
        try:
            headers={'Range':f'bytes={offset}-'} if offset else {}
            with session.get(api,params={'alt':'media'},headers=headers,stream=True,timeout=(30,180)) as response:
                response.raise_for_status()
                if offset and response.status_code==200:
                    offset=0 # Server trả toàn file, chỉ dựng lại file .part do tool tạo.
                if offset and (response.status_code!=206 or not response.headers.get('Content-Range','').startswith(f'bytes {offset}-')):
                    raise ValueError('Range download chưa khớp byte đã nhận.')
                with part.open('ab' if offset else 'wb') as stream:
                    for block in response.iter_content(1024*1024):
                        stream.write(block)
                        if stream.tell()>asset['bytes']:
                            raise ValueError('Download vượt kích thước kế hoạch.')
            if part.stat().st_size==asset['bytes']:
                break
        except ValueError:
            raise
        except Exception:
            if attempt==5:
                raise RuntimeError('Mạng/Drive gián đoạn; giữ .part, chạy lại cùng lệnh để tiếp tục.') from None
            time.sleep(min(30,2**attempt))
    if part.stat().st_size!=asset['bytes'] or digest(part)!=asset['sha256']:
        raise ValueError('Download chưa đạt SHA; giữ .part để kiểm.')
    part.replace(path)


def inventory(archive):
    for name in ('HANDOFF_INVENTORY.json','HANDOFF_MEMBER_INVENTORY.json','GRADE10_SUPPORT_INVENTORY.json','METHOD24_INPUT_INVENTORY.json','PACKAGE_MANIFEST.json','INVENTORY.json','SHA256.json'):
        if name not in archive.namelist():
            continue
        data=json.loads(archive.read(name))
        if isinstance(data,dict) and isinstance(data.get('files'),list):
            return name,{r['path']:r for r in data['files']}
        if isinstance(data,dict) and isinstance(data.get('files'),dict):
            return name,data['files']
        if isinstance(data,list) and all(isinstance(r,dict) and 'path' in r for r in data):
            return name,{r['path']:r for r in data}
        if isinstance(data,dict):
            return name,{key:(dict(sha256=value) if isinstance(value,str) else value) for key,value in data.items()}
    return None,{}


def extract(archive_path,target):
    restored=0
    namespace=archive_path.name+'-'+digest(archive_path)[:12]
    with zipfile.ZipFile(archive_path) as archive:
        if len(archive.namelist())!=len(set(archive.namelist())):
            raise ValueError('ZIP có tên member trùng.')
        manifest,pins=inventory(archive)
        for info in archive.infolist():
            if info.is_dir():
                continue
            if stat.S_ISLNK(info.external_attr>>16):
                raise ValueError('ZIP chứa symlink.')
            if info.filename==manifest or info.filename in {'PACKAGE_MANIFEST.json','HUONG_DAN.md'}:
                # Manifest/hướng dẫn của từng archive giữ riêng, tránh ghi đè khi ghép bộ model.
                output=local_path(target,'handoff-reference/package-docs/'+namespace+'/'+info.filename)
            else:
                output=local_path(target,info.filename)
            expected=pins.get(info.filename,{})
            if output.exists():
                with archive.open(info) as saved:
                    source_sha=hashlib.file_digest(saved,'sha256').hexdigest()
                if output.stat().st_size!=info.file_size or digest(output)!=source_sha:
                    raise ValueError('File đích đã có khác nội dung, giữ nguyên: '+str(output))
                continue
            output.parent.mkdir(parents=True,exist_ok=True)
            temporary=output.with_name(output.name+'.handoff-part')
            sha=hashlib.sha256();count=0
            with archive.open(info) as source,temporary.open('wb') as stream:
                while block:=source.read(1024*1024):
                    stream.write(block);sha.update(block);count+=len(block)
            if count!=info.file_size or ('sha256' in expected and sha.hexdigest()!=expected['sha256']):
                raise ValueError('Member SHA/kích thước không khớp.')
            temporary.replace(output);restored+=1
    return restored


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--downloads',type=Path,required=True)
    parser.add_argument('--tier',choices=('core','ready','archive'),default='ready')
    parser.add_argument('--download',action='store_true')
    parser.add_argument('--client-secret',type=Path)
    parser.add_argument('--auth-dir',type=Path)
    parser.add_argument('--extract',action='store_true')
    parser.add_argument('--root',type=Path)
    args=parser.parse_args()
    plan=json.loads(args.manifest.read_text(encoding='utf-8-sig'))
    assets=[a for a in plan['assets'] if selected(a,args.tier)]
    args.downloads.mkdir(parents=True,exist_ok=True)
    if args.download:
        from google.auth.transport.requests import AuthorizedSession
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        if not args.auth_dir:
            raise ValueError('Cần --auth-dir riêng để giữ token cá nhân.')
        args.auth_dir.mkdir(parents=True,exist_ok=True);token=args.auth_dir/'token.json'
        scopes=['https://www.googleapis.com/auth/drive.readonly']
        if token.exists():
            credentials=Credentials.from_authorized_user_file(str(token),scopes)
        else:
            if not args.client_secret:
                raise ValueError('Cần OAuth Desktop client riêng của người nhận.')
            credentials=InstalledAppFlow.from_client_secrets_file(str(args.client_secret),scopes).run_local_server(port=0,access_type='offline')
        try:
            with AuthorizedSession(credentials) as session:
                for number,asset in enumerate(assets,1):
                    obtain(session,asset,local_path(args.downloads,asset['drive_path']))
                    print('Đã tải/kiểm',number,'/',len(assets),asset['drive_path'],flush=True)
        finally:
            token.write_text(credentials.to_json(),encoding='utf-8')
    for asset in assets:
        path=local_path(args.downloads,asset['drive_path'])
        if not path.is_file() or path.stat().st_size!=asset['bytes'] or digest(path)!=asset['sha256']:
            raise ValueError('Thiếu file hoặc SHA chưa khớp: '+str(path))
    print('TẤT CẢ FILE ĐÃ KHỚP SHA',len(assets),flush=True)
    if not args.extract:
        return
    if not args.root:
        raise ValueError('Cần --root để khôi phục.')
    root=args.root.resolve();root.mkdir(parents=True,exist_ok=True)
    marker=root/'.handoff-restore.json'
    if not marker.exists() and any(p.name!='.venv' for p in root.iterdir()):
        raise ValueError('Lượt khôi phục đầu cần thư mục mới/trống, có thể có .venv.')
    marker.write_text(json.dumps(dict(manifest=str(args.manifest.resolve()),status='RESTORING'),ensure_ascii=False),encoding='utf-8')
    restored=0
    for asset in sorted(assets,key=lambda a:a.get('restore_order',50)):
        if asset.get('restore_mode')=='copy_file':
            source=local_path(args.downloads,asset['drive_path']);target=local_path(root,asset['restore_file'])
            target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():
                if digest(target)!=asset['sha256']:
                    raise ValueError('File calibration đích đã có khác SHA.')
            else:
                shutil.copy2(source,target);restored+=1
            continue
        if asset.get('restore_mode')=='archive_and_root':
            source=local_path(args.downloads,asset['drive_path']);target=local_path(root,asset['restore_archive_file'])
            target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():
                if digest(target)!=asset['sha256']:
                    raise ValueError('Archive gốc đích đã có khác SHA.')
            else:
                shutil.copy2(source,target)
            restored+=extract(source,root)
            continue
        if asset.get('restore_mode') not in {'root','subdir'}:
            continue
        destination=root if asset['restore_mode']=='root' else local_path(root,asset['restore_subdir'])
        destination.mkdir(parents=True,exist_ok=True)
        restored+=extract(local_path(args.downloads,asset['drive_path']),destination)
    for group in plan.get('multipart_groups',[]):
        output=args.downloads/'assembled'/group['archive_name'];output.parent.mkdir(parents=True,exist_ok=True)
        if not output.exists():
            temporary=output.with_name(output.name+'.assembling')
            with temporary.open('wb') as stream:
                for name in group['parts']:
                    with local_path(args.downloads,name).open('rb') as source:
                        shutil.copyfileobj(source,stream,1024*1024)
            if digest(temporary)!=group['sha256']:
                raise ValueError('ZIP ghép phần chưa đúng SHA.')
            temporary.replace(output)
        if digest(output)!=group['sha256']:
            raise ValueError('ZIP ghép phần chưa đúng SHA.')
        restored+=extract(output,root)
    for model in plan.get('grade10_checkpoint_relocations',[]):
        source=local_path(root,model['compact_checkpoint']);target=local_path(root,model['original_checkpoint'])
        if digest(source)!=model['checkpoint_sha256']:
            raise ValueError('Grade10 best checkpoint chưa đúngSHA.')
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():
            if digest(target)!=model['checkpoint_sha256']:
                raise ValueError('Checkpoint tại đường dẫn cũ khác SHA.')
        else:
            shutil.copy2(source,target)
    bundle=next(a for a in assets if a['role']=='UPSTREAM_BUNDLE')
    upstream=root/'artifacts/akt/dependencies/upstream'
    if not upstream.exists():
        upstream.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run(['git','-c','core.autocrlf=false','clone',str(local_path(args.downloads,bundle['drive_path']).resolve()),str(upstream)],check=True)
        subprocess.run(['git','-C',str(upstream),'remote','set-url','origin','https://github.com/arghosh/AKT.git'],check=True)
    commit=subprocess.check_output(['git','-C',str(upstream),'rev-parse','HEAD'],text=True).strip()
    if commit!='01b7e8d7d7c862cabc9467108e3e7f2555653a88':
        raise ValueError('AKT upstream khác commit đã pin.')
    history=next((a for a in assets if a['role']=='PROJECT_GIT_BUNDLE'),None)
    if history and not (root/'.git').exists():
        subprocess.run(['git','init',str(root)],check=True)
        subprocess.run(['git','-C',str(root),'config','core.longpaths','true'],check=True)
        subprocess.run(['git','-C',str(root),'symbolic-ref','HEAD','refs/heads/main'],check=True)
        subprocess.run(['git','-C',str(root),'fetch',str(local_path(args.downloads,history['drive_path']).resolve()),'HEAD'],check=True)
        # --mixed chỉ phục hồi HEAD/index; giữ đúng bytes source snapshot và notebook đang sửa.
        subprocess.run(['git','-C',str(root),'reset','--mixed',plan['source_snapshot']['source_head']],check=True)
    for model in plan.get('primary_akt_models',[]):
        path=local_path(root,model['path'])
        if not path.is_file() or path.stat().st_size!=model['bytes'] or digest(path)!=model['sha256']:
            raise ValueError('Model chính chưa đủ hoặc saiSHA: '+model['path'])
    marker.write_text(json.dumps(dict(status='FILES_RESTORED_AND_SHA_VERIFIED',restored_files=restored,
        runtime_model_tests='Cần chạy preflight/import/test trong .venv sau cài dependency; chưa training.'),ensure_ascii=False,indent=2),encoding='utf-8')
    print('ĐÃ KHÔI PHỤC',restored,'file vào',root,flush=True)


if __name__=='__main__':
    main()
