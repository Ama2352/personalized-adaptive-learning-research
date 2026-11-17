"""Kiểm kê dung lượng local trước dọn; không theo junction, không xóa."""
from pathlib import Path
from collections import defaultdict
import os,json,shutil,time
ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
groups=defaultdict(lambda:dict(files=0,bytes=0));errors=[];large=[];start=time.monotonic()
for relative in ('artifacts/akt','experiments/akt','artifacts/gkt','artifacts/simulator','experiments/sakt','experiments/gkt'):
    stack=[ROOT/relative]
    while stack:
        directory=stack.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if entry.is_symlink() or getattr(entry,'is_junction',lambda:False)():continue
                    if entry.is_dir(follow_symlinks=False):stack.append(Path(entry.path))
                    elif entry.is_file(follow_symlinks=False):
                        p=Path(entry.path);s=entry.stat(follow_symlinks=False);rel=p.relative_to(ROOT).as_posix()
                        pieces=rel.split('/');key='/'.join(pieces[:4 if pieces[1]=='akt' and pieces[2] in ('results','runtime') else 3])
                        groups[key]['files']+=1;groups[key]['bytes']+=s.st_size
                        if s.st_size>100*1024**2:large.append(dict(path=rel,bytes=s.st_size,mtime_ns=s.st_mtime_ns))
        except (PermissionError,FileNotFoundError) as e:errors.append(dict(path=str(directory),error=type(e).__name__))
report=dict(groups=[dict(path=k,**v) for k,v in sorted(groups.items(),key=lambda x:-x[1]['bytes'])],large=sorted(large,key=lambda r:-r['bytes']),errors=errors,free_bytes=shutil.disk_usage(ROOT).free,seconds=time.monotonic()-start)
(B/'SCAN_BEFORE.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(top=report['groups'][:30],free_bytes=report['free_bytes'],errors=errors,seconds=report['seconds']),ensure_ascii=False,indent=2))
