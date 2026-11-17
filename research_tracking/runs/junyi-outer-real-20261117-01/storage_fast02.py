"""Kiểm dung lượng logic bằng metadata directory entry, không hash và không xóa."""
from collections import defaultdict
import heapq
import json
import os
from pathlib import Path
import shutil
import time

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
started=time.monotonic();results=[]
for relative in ('artifacts/akt','experiments/akt'):
    base=ROOT/relative
    groups=defaultdict(lambda:dict(files=0,logical_bytes=0))
    stack=[(str(base),None)];largest=[]
    while stack:
        directory,group=stack.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_symlink() or getattr(entry,'is_junction',lambda:False)():
                    continue
                first=entry.name if group is None else group
                if entry.is_dir(follow_symlinks=False):
                    stack.append((entry.path,first))
                elif entry.is_file(follow_symlinks=False):
                    stat=entry.stat(follow_symlinks=False)
                    key='(files)' if group is None else group
                    groups[key]['files']+=1;groups[key]['logical_bytes']+=stat.st_size
                    row=(stat.st_size,entry.path)
                    if len(largest)<20:
                        heapq.heappush(largest,row)
                    elif row>largest[0]:
                        heapq.heapreplace(largest,row)
    result=dict(root=relative,children=[dict(name=name,**value) for name,value in
        sorted(groups.items(),key=lambda x:x[1]['logical_bytes'],reverse=True)],
        largest_files=[dict(bytes=size,path=str(Path(path).relative_to(ROOT))) for size,path in sorted(largest,reverse=True)])
    results.append(result)
    print(relative,[(v['name'],round(v['logical_bytes']/1024**3,2),v['files']) for v in result['children'][:12]],flush=True)
disk=shutil.disk_usage(ROOT)
(B/'STORAGE_TOPLEVEL02.json').write_text(json.dumps(dict(status='LOGICAL_METADATA_ONLY_NO_DELETE',
    roots=results,disk_free_bytes=disk.free,seconds=time.monotonic()-started,
    note='Tổng theo đường dẫn, chưa khử hardlink và chưa đo NTFS allocation/compression.'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('D_FREE_GIB',round(disk.free/1024**3,2),'SECONDS',round(time.monotonic()-started,2),flush=True)
