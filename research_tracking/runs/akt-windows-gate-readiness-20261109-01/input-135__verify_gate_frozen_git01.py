"""Kiểm source freeze154 qua raw Git để tránh nhân bản source trong bundle."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
packet_path = PREP/'gate_collection01_packet.ROOT.json'
packet_raw = packet_path.read_bytes()
assert hashlib.sha256(packet_raw).hexdigest() == 'bacc6e49d14d244396b7be03cf68c62daefa8c14adf056b1f0c5cde8b8f1ed90'
sources = json.loads(packet_raw)['gate_build_hashes']
assert len(sources) == 154
request = ''.join('2c337d4:'+name+'\n' for name in sources).encode()
child = subprocess.run(['git','cat-file','--batch'],cwd=ROOT,input=request,
                       capture_output=True,timeout=20,check=True)
assert not child.stderr
raw = child.stdout
offset = 0
for name,digest in sources.items():
    end = raw.index(b'\n',offset);header = raw[offset:end].split()
    assert len(header) == 3 and header[1] == b'blob',name
    size = int(header[2]);offset = end+1
    blob = raw[offset:offset+size];offset += size
    assert raw[offset:offset+1] == b'\n';offset += 1
    assert hashlib.sha256(blob).hexdigest() == digest,name
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest,name
assert offset == len(raw)
result = dict(status='FROZEN154_RAW_GIT_AND_WORKTREE_VERIFIED',commit='2c337d4',
              packet_sha256=hashlib.sha256(packet_raw).hexdigest(),source_count=len(sources),
              source_sha256=sources,source_files_copied=0,
              scope_vi='Giữ Git commit và SHA nguồn thay vì nhân bản154files; không thực thi source hoặc mô hình.')
with (PREP/'gate_frozen154_raw_git01.json').open('x',encoding='utf-8') as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps(dict(status=result['status'],commit=result['commit'],source_count=len(sources),source_files_copied=0)))
