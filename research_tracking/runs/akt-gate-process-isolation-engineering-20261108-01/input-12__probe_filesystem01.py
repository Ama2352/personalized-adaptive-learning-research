"""Đo tối đa8file tự dựng; không pytest, model, source mutation hoặc dataset."""
from pathlib import Path
import sys,time,json,importlib.util,os
R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts/research'))
from windows_owned_worker import worker_gate
worker_gate()
start=time.perf_counter()
spec=importlib.util.spec_from_file_location('method24_fs_definition_only',P/'method24_worker01.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
base=P/'filesystem_probe01';base.mkdir(exist_ok=False)
synthetic=base/'tree';synthetic.mkdir();w.ROOT=synthetic
rows=[]
def event(value):
    rows.append(value)
    with (base/'progress.jsonl').open('a',encoding='utf-8') as h:
        h.write(json.dumps(value,ensure_ascii=False)+'\n');h.flush();os.fsync(h.fileno())
for i in range(8):
    if time.perf_counter()-start>8:
        event({'status':'STOP_BEFORE_NEXT_FILE','completed_files':i});break
    relative=f'fixture/a/b/c/d/{i:02d}.json';f=synthetic/relative
    t=time.perf_counter();f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b'{"manufactured":true}\n');created=time.perf_counter()-t
    t=time.perf_counter();digest=w.hash_file(relative);hashed=time.perf_counter()-t
    event(dict(index=i,create_seconds=created,safe_hash_seconds=hashed,sha256=digest))
elapsed=time.perf_counter()-start
assert all(name not in sys.modules for name in ('torch','numpy','pandas','sklearn'))
with (base/'result.json').open('x',encoding='utf-8') as h:json.dump({'status':'COMPLETE_BOUNDED_FILESYSTEM_PROBE','files':len([r for r in rows if 'index' in r]),'rows':rows,'elapsed_seconds':elapsed,'scope_vi':'Source-safe/hash trên8file tự dựng, không đại diện toànpytest/fit/ổđĩa hay chứng minh nguyênnhân timeout.'},h,ensure_ascii=False,indent=2);h.write('\n')
print('SYNTHETIC_FILESYSTEM_PROBE_COMPLETE')
