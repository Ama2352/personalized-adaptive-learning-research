"""Đo toàn repo bằng metadata, giữ giới hạn quyền và tách vùng bảo vệ."""
from pathlib import Path
import os,json,collections,shutil,sys
ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
groups=collections.defaultdict(lambda:dict(files=0,bytes=0));errors=[]
stack=[ROOT]
while stack:
    directory=stack.pop()
    try:
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_symlink() or getattr(entry,'is_junction',lambda:False)():continue
                p=Path(entry.path)
                if entry.is_dir(follow_symlinks=False):stack.append(p)
                elif entry.is_file(follow_symlinks=False):
                    rel=p.relative_to(ROOT).parts
                    key='/'.join(rel[:2]) if rel[0] in ('artifacts','experiments') else rel[0] if len(rel)>1 else '[root files]'
                    st=entry.stat(follow_symlinks=False);groups[key]['files']+=1;groups[key]['bytes']+=st.st_size
    except (PermissionError,FileNotFoundError,OSError) as e:errors.append(dict(path=directory.relative_to(ROOT).as_posix(),error=type(e).__name__))
result=dict(groups=[dict(path=k,**v) for k,v in sorted(groups.items(),key=lambda p:-p[1]['bytes'])],logical_bytes=sum(v['bytes'] for v in groups.values()),free_bytes=shutil.disk_usage(ROOT).free,errors=errors,note='Tổng logic theo đường dẫn; có thể cộng lặp hardlink. Không đổi nội dung/ACL.')
name='REPO_FINAL_SIZE.json' if '--final' in sys.argv else 'REPO_INTERMEDIATE_SIZE.json'
(B/name).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(groups=result['groups'][:20],logical_bytes=result['logical_bytes'],errors=len(errors),free_bytes=result['free_bytes']),ensure_ascii=False,indent=2))
