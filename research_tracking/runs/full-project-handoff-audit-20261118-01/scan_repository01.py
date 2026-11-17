"""Kiểm kê metadata toàn repository, giữ nguyên dữ liệu/model và tách hardlink."""
from collections import defaultdict
from pathlib import Path
import json
import os
import time

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
DETAIL=ROOT/'artifacts/akt/runtime/project-handoff-20261118-01'


def main():
    DETAIL.mkdir(parents=True,exist_ok=True)
    output=DETAIL/'FILES.jsonl'
    totals=defaultdict(lambda:dict(files=0,bytes=0))
    identities={}; errors=[]; count=0;start=time.monotonic()
    skipped=[DETAIL, B]
    stack=[ROOT]
    with output.open('w',encoding='utf-8') as stream:
        while stack:
            directory=stack.pop()
            try:
                entries=list(os.scandir(directory))
            except OSError as error:
                errors.append(dict(path=str(directory.relative_to(ROOT)),error=type(error).__name__))
                continue
            for entry in entries:
                path=Path(entry.path)
                if path in skipped:
                    continue
                try:
                    if entry.is_symlink() or (hasattr(entry,'is_junction') and entry.is_junction()):
                        errors.append(dict(path=path.relative_to(ROOT).as_posix(),error='LINK_NOT_FOLLOWED'))
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(path);continue
                    if not entry.is_file(follow_symlinks=False):
                        continue
                    stat=entry.stat(follow_symlinks=False)
                except OSError as error:
                    errors.append(dict(path=path.relative_to(ROOT).as_posix(),error=type(error).__name__))
                    continue
                relative=path.relative_to(ROOT).as_posix();parts=relative.split('/')
                top=parts[0] if len(parts)>1 else '[root files]'
                keys=[top]
                if len(parts)>2:
                    keys.append('/'.join(parts[:2]))
                if relative.startswith(('artifacts/akt/','experiments/akt/')):
                    keys.extend('/'.join(parts[:depth]) for depth in (3,4) if len(parts)>depth)
                for key in set(keys):
                    totals[key]['files']+=1;totals[key]['bytes']+=stat.st_size
                identity=f'{stat.st_dev}:{stat.st_ino}'
                if stat.st_ino:
                    if identity not in identities:
                        identities[identity]=[stat.st_size,0,False]
                    identities[identity][1]+=1
                    if relative.startswith(('artifacts/akt/','experiments/akt/')):
                        identities[identity][2]=True
                row=dict(path=relative,bytes=stat.st_size,mtime_ns=stat.st_mtime_ns,
                         file_id=identity,hardlink_count=stat.st_nlink)
                # Credentials chỉ được đo dung lượng, đường dẫn chi tiết giữ ngoài inventory công khai.
                if '/private/' not in relative:
                    stream.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n')
                count+=1
                if count%50000==0:
                    print('SCANNED',count,round(time.monotonic()-start,1),'seconds',flush=True)
    result=dict(status='REPOSITORY_METADATA_INVENTORY_COMPLETE',scanned_files=count,
        seconds=time.monotonic()-start,groups=dict(sorted(totals.items())),
        unique_logical_bytes_by_file_id=sum(v[0] for v in identities.values()) if identities else None,
        unique_logical_akt_bytes_by_file_id=sum(v[0] for v in identities.values() if v[2]) if identities else None,
        errors=errors,detail=str(output.relative_to(ROOT)),
        limits=['Chỉ metadata; chưa hash toàn bộ binary.','FileID đo byte logic duy nhất, chưa đo NTFS allocation/compression.',
                'Không theo symlink/junction.','Loại hai thư mục output của lượt kiểm khỏi tự đếm.',
                'Nếu st_ino=0 thì chưa đo được hardlink; tổng byte theo đường dẫn.'])
    (B/'REPOSITORY_INVENTORY01.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('COMPLETE',count,'files',round(result['seconds'],1),'seconds','errors',len(errors),flush=True)
    for key,value in totals.items():
        if '/' not in key:
            print(key,value['files'],value['bytes'],flush=True)


if __name__=='__main__':
    main()
