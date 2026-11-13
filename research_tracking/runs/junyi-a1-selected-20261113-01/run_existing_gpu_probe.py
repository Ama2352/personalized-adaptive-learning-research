"""Chạy phép đối chiếu nhỏ trong container đang cấp, tách nguồn khỏi training."""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zlib

ROOT=Path(__file__).resolve().parents[3]
BUNDLE=Path(__file__).resolve().parent
RUN='modal-junyi-a1-b128-h100-20261113-04'
os.environ['MODAL_CONFIG_PATH']=str(ROOT/'artifacts/akt/private/modal.toml')
os.environ['MODAL_PROFILE']='kltn'
os.environ['TEMP']=os.environ['TMP']=str(ROOT/'artifacts/akt/runtime/modal-client-temp')
cli=[sys.executable,'-B','-m','modal']
dispatch=json.loads((ROOT/'experiments/akt/results'/RUN/'dispatch.json').read_text())
containers=json.loads(subprocess.run(cli+['container','list','--json'],check=True,capture_output=True,text=True,timeout=25).stdout)
owned=[row for row in containers if row['app_id']==dispatch['app_id']]
assert len(owned)==1, 'Chỉ dùng container đã cấp của A1'
container=owned[0]['container_id']
prefix=cli+['container','exec','--no-pty',container,'--','/opt/kltn/.venv/bin/python','-B']
inputs=[(ROOT/'src/knowledge_tracing/akt/research_graph_model.py','/opt/kltn-checks/src/knowledge_tracing/akt/research_graph_model.py'),
        (BUNDLE/'probe_gpu_vector_parity.py','/opt/kltn-checks/probe_gpu_vector_parity.py')]
for source,destination in inputs:
    raw=source.read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    code='from pathlib import Path; import base64,hashlib,zlib; p=Path('+repr(destination)+'); p.parent.mkdir(parents=True,exist_ok=True); raw=zlib.decompress(base64.b64decode('+repr(base64.b64encode(zlib.compress(raw)).decode())+')); assert hashlib.sha256(raw).hexdigest()=='+repr(digest)+'; p.write_bytes(raw); print('+repr(digest)+')'
    subprocess.run(prefix+['-c',code],check=True,capture_output=True,text=True,timeout=25)
result=subprocess.run(prefix+['/opt/kltn-checks/probe_gpu_vector_parity.py','--root','/opt/kltn',
    '--new-native',inputs[0][1],'--output','/opt/kltn-checks/vector-parity-03'],
    capture_output=True,text=True,timeout=105)
(BUNDLE/'vector-gpu-probe03.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
code="from pathlib import Path; import hashlib,json,base64; raw=Path('/opt/kltn-checks/vector-parity-03/result.json').read_bytes(); print(json.dumps(dict(sha256=hashlib.sha256(raw).hexdigest(),data=base64.b64encode(raw).decode())))"
receipt=json.loads(subprocess.run(prefix+['-c',code],check=True,capture_output=True,text=True,timeout=25).stdout)
raw=base64.b64decode(receipt['data'],validate=True)
assert hashlib.sha256(raw).hexdigest()==receipt['sha256']
(BUNDLE/'vector-gpu-result03.json').write_bytes(raw)
print(json.dumps(dict(returncode=result.returncode,status=json.loads(raw)['status'],result_sha256=receipt['sha256'])))
raise SystemExit(0 if result.returncode == 0 and json.loads(raw)['status']=='PASS_H100_A1_SCALAR_VECTOR_PARITY' else 1)
