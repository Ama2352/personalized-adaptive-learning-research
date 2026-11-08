"""Pure metadata child; không import nguồn nghiên cứu/Torch hoặc spawn tiếp."""
import time
START=time.perf_counter()
import argparse
import json
import os
from pathlib import Path
import sys

parser=argparse.ArgumentParser()
parser.add_argument('--outer-pid',type=int,required=True)
parser.add_argument('--outer-create-time',type=float,required=True)
parser.add_argument('--release-file',required=True)
args=parser.parse_args()
record=dict(pid=os.getpid(),ppid=os.getppid(),executable=sys.executable,prefix=sys.prefix,
            base_executable=getattr(sys,'_base_executable',None),base_prefix=sys.base_prefix,
            platform=sys.platform,expected_outer_pid=args.outer_pid,
            expected_outer_create_time=args.outer_create_time,ancestors=[])
try:
    import psutil
    record['psutil_version']=psutil.__version__
    process=psutil.Process(os.getpid())
    for _ in range(8):
        row=dict(pid=process.pid,ppid=process.ppid(),exe=process.exe(),create_time=process.create_time())
        record['ancestors'].append(row)
        if process.pid==args.outer_pid:
            break
        process=process.parent()
        if process is None:
            break
except Exception as error:
    record['psutil_error_type']=type(error).__name__
record['forbidden_modules_loaded']=[name for name in ('torch','numpy','pandas','knowledge_tracing') if name in sys.modules]
assert not record['forbidden_modules_loaded']
payload=json.dumps(record,sort_keys=True,allow_nan=False)
assert len(payload.encode('utf-8'))+1<=16384
print(payload,flush=True)
release=Path(args.release_file)
while time.perf_counter()-START<6:
    if release.is_file():
        assert release.read_bytes()==b'RELEASE\n'
        sys.exit(0)
    time.sleep(.005)
raise TimeoutError('pure child release deadline; no native work')
