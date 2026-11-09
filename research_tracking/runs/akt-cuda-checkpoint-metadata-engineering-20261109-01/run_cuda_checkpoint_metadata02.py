"""ROOT-only current38 metadata,30whole/27owned/24worker; no NN/GPU proof."""
import time
PERF,WALL,MONO=time.perf_counter,time.time,time.monotonic
START,START_WALL,START_MONO=PERF(),WALL(),MONO()
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
PACKET=PREP/'cuda_checkpoint_metadata02_packet.json'
WORKER=PREP/'check_cuda_checkpoint_metadata02.py'
OUT=PREP/'cuda-checkpoint-metadata-tests02-owned'
CHILD=PREP/'cuda-checkpoint-metadata-tests02'


def need(value,message):
    if not value:raise ValueError(message)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def elapsed():return max(PERF()-START,WALL()-START_WALL,MONO()-START_MONO)


def write(name,value):
    with (OUT/name).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')


need(len(sys.argv)==2,'ROOT external packet SHA')
sys.path.insert(0,str(ROOT/'scripts/research'))
from windows_owned_worker import entry,safe,run_owned
entry()
for path in (WORKER,OUT,CHILD,PACKET):safe(path)
need(not OUT.exists() and not CHILD.exists() and not (ROOT/'artifacts/akt/local-tests/ccm02').exists(),'fresh metadata02 namespace')
need(sha(PACKET)==sys.argv[1],'reviewed packet')
packet=json.loads(PACKET.read_bytes());pins=packet['source_pins'];runtime=packet['runtime_pins']
before={n:sha(safe(ROOT/n)) for n in pins};r_before={n:sha(Path(n)) for n in runtime}
need(before==pins and r_before==runtime,'actual current source/runtime')
import psutil
available=int(psutil.virtual_memory().available)
if available<1280*1024**2:
    OUT.mkdir();write('final.json',dict(status='NO_GO_METADATA_RAM',available_ram_bytes=available,
        required_available_ram_bytes=1280*1024**2,owned_launch_started=False,automatic_retry=False))
    raise SystemExit(1)
receipt=run_owned(WORKER,[sys.argv[1]],OUT,expected_worker_sha256=pins[WORKER.relative_to(ROOT).as_posix()],
    approval_reference='ROOT_REVIEW_REQUIRED_CURRENT38_CHECKPOINT_METADATA_NO_NATIVE',
    max_seconds=min(27.,30.-elapsed()-3.),cleanup_reserve_seconds=3,max_output_bytes=65536)
errors=[];child=None
if not OUT.exists():OUT.mkdir()
write('receipt.json',receipt)
try:
    need(receipt['accepted'] is True and receipt['returncode']==0 and receipt['cleanup_accepted'] is True
        and receipt['job_active_after_cleanup']==0 and receipt['actual_worker_in_job_before_GO'] is True
        and receipt['popen_handle_closed'] is True and receipt['errors']==receipt['cleanup_errors']==[],'actual owned terminal/cleanup')
    child=json.loads((CHILD/'result.json').read_bytes())
    need(child['status']=='ACCEPTED_CURRENT38_CHECKPOINT_METADATA_CHILD' and child['pytest_exit_code']==0
        and child['counts']==dict(tests=38,failures=0,errors=0,skipped=0) and child['denied']==[] and child['error'] is None
        and child['scientific_modules_absent'] is True and child['environment_and_sys_restored'] is True
        and child['nodeids']==packet['expected_nodeids'],'actual current38 metadata only')
    need(child['source_before']==child['source_after']==pins and child['runtime_before']==child['runtime_after']==runtime,'child bindings stable')
    memory=child['resources']
    need(memory['samples']>0 and memory['observed_peak_rss_bytes']<=128*1024**2
        and memory['observed_minimum_available_ram_bytes']>=1024**3 and child['elapsed_seconds']<24
        and not (CHILD/'postwrite_rejection.json').exists(),'metadata resources/deadline')
except BaseException as exc:errors.append(dict(type=type(exc).__name__,message=str(exc)))
after={n:sha(safe(ROOT/n)) for n in pins};r_after={n:sha(Path(n)) for n in runtime}
accepted=not errors and after==before and r_after==r_before and sha(PACKET)==sys.argv[1] and elapsed()<30
outputs={path.name:dict(bytes=path.stat().st_size,sha256=sha(path)) for path in CHILD.iterdir() if path.is_file()} if CHILD.exists() else {}
write('final.json',dict(status='ACCEPTED_CURRENT38_CHECKPOINT_METADATA_NOT_NATIVE' if accepted else 'REJECTED_CURRENT38_METADATA_KEEP_ALL',
    errors=errors,child_result=child,owned_receipt=receipt,source_before=before,source_after=after,
    runtime_before=r_before,runtime_after=r_after,packet_sha256=sys.argv[1],outputs=outputs,elapsed_seconds=elapsed(),cap_seconds=30,
    prelaunch_available_ram_bytes=available,automatic_retry=False,actual_native_or_cuda_proof=False))
if elapsed()>=30:write('postwrite_rejection.json',dict(elapsed_seconds=elapsed()));accepted=False
print(json.dumps(dict(accepted=accepted,elapsed_seconds=elapsed())))
raise SystemExit(0 if accepted else 1)
