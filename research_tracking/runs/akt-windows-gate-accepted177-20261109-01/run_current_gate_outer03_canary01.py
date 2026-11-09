"""ROOT chạy sáu kiểm tra bộ đọc JUnit và giữ raw output trong lượt hữu hạn."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[4]
P=Path(__file__).resolve().parent
TEST=P/'test_current_gate_outer03_junit.py'
OUT=P/'current-gate-outer03-canary01'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    started=time.perf_counter()
    assert Path(sys.prefix).resolve()==ROOT/'.venv'
    assert not OUT.exists()
    pins={TEST:'ab63b7c740216341a70412ffc91ed8c749046509e1b3489cffcd63fe73f2327d',
      P/'windows_current_gate_outer03.py':'4722088dadf1dc3e45203bb29c242e22d5d54bd66b4141f46b2ab8df28f64f3e',
      ROOT/'scripts/akt/refresh_gate2.py':'8689c5b4737f4eae00459f4a3bc85c22206f58974274304fa4411e36f9acc055'}
    assert all(sha(path)==h for path,h in pins.items())
    OUT.mkdir()
    command=[str(ROOT/'.venv/Scripts/python.exe'),'-B',str(TEST)]
    before={str(path.relative_to(ROOT)):h for path,h in pins.items()}
    with (OUT/'reservation.json').open('x',encoding='utf-8') as f:
        json.dump(dict(command=command,child_timeout_seconds=15,whole_seconds=30,
            expected_unittest_methods=6,maximum_read_junit_calls=14,source_before=before,
            scope_vi='Ba XML lịch sử và các XML nhỏ trong bộ nhớ, kiểm bộ đọc mới trước fullGate.'),f,ensure_ascii=False,indent=2)
    result=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=15,check=False)
    for name,raw in (('stdout.log',result.stdout),('stderr.log',result.stderr)):
        assert len(raw)<65536
        with (OUT/name).open('xb') as f:f.write(raw)
    after={str(path.relative_to(ROOT)):sha(path) for path in pins}
    accepted=(result.returncode==0 and b'Ran 6 tests' in result.stderr
       and b'\nOK\n' in result.stderr and before==after and time.perf_counter()-started<30)
    value=dict(status='ACCEPTED_SIX_OUTER_READER_CANARIES_ONLY' if accepted else 'REJECTED_READER_CANARY',
       returncode=result.returncode,source_before=before,source_after=after,
       elapsed_seconds=time.perf_counter()-started,child_timeout_seconds=15,whole_seconds=30,
       stdout_sha256=sha(OUT/'stdout.log'),stderr_sha256=sha(OUT/'stderr.log'),
       historical_gate04_accepted=False,current_gate_pass=False,
       scope_vi='Đã chạy sáu unittest. Chỉ kiểm parser và định danh trên XML cũ và dữ liệu dựng sẵn.')
    with (OUT/'result.json').open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(value,ensure_ascii=False))
    raise SystemExit(0 if accepted else 1)

if __name__=='__main__':main()
