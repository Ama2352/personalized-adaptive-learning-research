"""Kiểm kê metadata dung lượng AKT hiện tại, không đọc nội dung hoặc xóa file."""
from collections import defaultdict
import json
import os
from pathlib import Path
import shutil
import time

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
started=time.monotonic();rows=[];unique={}
for relative in ('artifacts/akt','experiments/akt'):
    base=ROOT/relative
    groups=defaultdict(lambda:dict(files=0,logical_bytes=0,hardlinked_files=0))
    largest=[]
    for directory,subdirs,names in os.walk(base,followlinks=False):
        subdirs[:]=[name for name in subdirs if not (Path(directory)/name).is_symlink()
            and not getattr(Path(directory)/name,'is_junction',lambda:False)()]
        for name in names:
            path=Path(directory)/name
            if path.is_symlink():
                continue
            stat=path.stat()
            key=path.relative_to(base).parts[0] if len(path.relative_to(base).parts)>1 else '(files)'
            item=groups[key];item['files']+=1;item['logical_bytes']+=stat.st_size
            item['hardlinked_files']+=int(stat.st_nlink>1)
            unique.setdefault((stat.st_dev,stat.st_ino),stat.st_size)
            largest.append((stat.st_size,str(path.relative_to(ROOT)),stat.st_nlink))
    rows.append(dict(root=relative,children=[dict(name=name,**item) for name,item in
        sorted(groups.items(),key=lambda x:x[1]['logical_bytes'],reverse=True)],
        largest_files=[dict(bytes=size,path=path,links=links) for size,path,links in sorted(largest,reverse=True)[:20]]))
disk=shutil.disk_usage(ROOT)
result=dict(status='METADATA_ONLY_NO_DELETE',seconds=time.monotonic()-started,roots=rows,
    unique_file_logical_bytes_across_both=sum(unique.values()),disk_free_bytes=disk.free,
    note='Logical bytes tính theo đường dẫn. Unique file bytes khử hardlink theo file ID; chưa đo NTFS allocation/compression.')
(B/'STORAGE_TOPLEVEL01.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for row in rows:
    print(row['root'],[(r['name'],round(r['logical_bytes']/1024**3,2),r['files']) for r in row['children'][:12]])
print('D_FREE_GIB',round(disk.free/1024**3,2),'SECONDS',round(result['seconds'],2),flush=True)
