"""ROOT-only GKT11,60whole/56owned/50worker,4GiB admission; no fit authority."""
import time
PERF,WALL,MONO=time.perf_counter,time.time,time.monotonic
START,START_WALL,START_MONO=PERF(),WALL(),MONO()
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
WORKER=PREP/'check_gkt_research_model02.py'
PACKET=PREP/'gkt_research_model02_packet.json'
OUT=PREP/'gkt-research-model02-owned'
CHILD=PREP/'gkt-research-model02'


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
need(not OUT.exists() and not CHILD.exists() and not safe(ROOT/'artifacts/akt/local-tests/grm02').exists(),'fresh GKT02 namespace')
need(sha(PACKET)==sys.argv[1],'reviewed packet')
packet=json.loads(PACKET.read_bytes());pins=packet['source_pins'];runtime=packet['runtime_pins']
before={n:sha(safe(ROOT/n)) for n in pins};r_before={n:sha(Path(n)) for n in runtime}
need(before==pins and r_before==runtime,'canonical exact model02/test02 must be applied before launch')
import psutil
available=int(psutil.virtual_memory().available)
if available<4*1024**3:
    OUT.mkdir();write('final.json',dict(status='NO_GO_GKT_RAM_BEFORE_OWNED_LAUNCH',available_ram_bytes=available,
        required_available_ram_bytes=4*1024**3,owned_launch_started=False,actual_native_counters=None,automatic_retry=False))
    raise SystemExit(1)
seconds=min(56.,60.-elapsed()-4.)
need(seconds>3,'same whole budget cleanup reserve')
receipt=run_owned(WORKER,[sys.argv[1]],OUT,expected_worker_sha256=pins[WORKER.relative_to(ROOT).as_posix()],
    approval_reference='ROOT_REVIEW_REQUIRED_GKT11_COMPUTE_2BACKWARD_ZERO_OPTIMIZER',
    max_seconds=seconds,cleanup_reserve_seconds=3,max_output_bytes=65536)
errors=[];child=None;actual_counts=None
if not OUT.exists():OUT.mkdir()
write('receipt.json',receipt)
try:
    need(receipt['accepted'] is True and receipt['returncode']==0 and receipt['cleanup_accepted'] is True
        and receipt['job_active_after_cleanup']==0 and receipt['actual_worker_in_job_before_GO'] is True
        and receipt['popen_handle_closed'] is True and receipt['errors']==receipt['cleanup_errors']==[],'actual owned terminal/cleanup')
    child=json.loads((CHILD/'result.json').read_bytes())
    cases=list(ET.parse(CHILD/'junit.xml').iter('testcase'))
    actual_counts=dict(tests=len(cases),failures=sum(len(list(c.iter('failure'))) for c in cases),
        errors=sum(len(list(c.iter('error'))) for c in cases),skipped=sum(len(list(c.iter('skipped'))) for c in cases))
    ids=[(c.get('classname'),c.get('name')) for c in cases]
    need(len(set(ids))==11 and ids==[('tests.gkt.test_research_model',n.split('::',1)[1]) for n in packet['expected_nodeids']], 'exact11 physical JUnit IDs')
    need(child['status']=='ACCEPTED_GKT11_CPU_COMPUTE_PENDING_OUTER' and child['pytest_exit_code']==0
        and child['counts']==actual_counts==dict(tests=11,failures=0,errors=0,skipped=0)
        and child['error'] is None and child['junit_error'] is None and child['forbidden']==[],'actual11 cases/0FES')
    need(child['counters']==packet['expected_counters'] and len(child['negative_ctor_proofs'])==9
        and all(r['parameter_registrations_before']==r['after'] for r in child['negative_ctor_proofs'])
        and len(child['gradient_proofs'])==2,'exact finite work and real negative/gradient proofs')
    need(any(p['kind']=='full_model' and len(p['gradient_names'])==32 and 'gru.W_n.weight' in p['nonzero_names']
         for p in child['gradient_proofs'][-1]),'finite32 full-model gradients/nonzero GRU')
    need(child['source_before']==child['source_after']==pins and child['runtime_before']==child['runtime_after']==runtime
        and child['nodeids']==packet['expected_nodeids'],'actual source/runtime/collection bindings')
    need(child['method_restoration']['accepted'] is True and child['environment_restored'] is True
        and child['job_query_handle_closed'] is True and child['monitor_stopped'] is True and child['monitor_errors']==[],'restoration and monitor closure')
    memory=child['resources']
    need(memory['samples']>0 and memory['peak_worker_rss_bytes']<=1024**3 and memory['peak_family_rss_bytes']<=1024**3
        and memory['minimum_available_ram_bytes']>=2*1024**3 and memory['maximum_job_processes']>=1,'sampled family/worker1GiB/free2GiB')
    need(child['torch_profile']['cuda_build'] is None and child['torch_profile']['cuda_initialized_after'] is False
        and all(q['value'] is False for q in child['cuda_false_queries']),'genuine CPU/CUDA metadata')
    need(child['elapsed_seconds']<50 and not any((CHILD/n).exists() for n in ('resource-failure.json','postwrite_rejection.json')),'worker deadline/resources')
except BaseException as exc:errors.append(dict(type=type(exc).__name__,message=str(exc)))
after={n:sha(safe(ROOT/n)) for n in pins};r_after={n:sha(Path(n)) for n in runtime}
accepted=not errors and after==before and r_after==r_before and sha(PACKET)==sys.argv[1] and elapsed()<60
outputs={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in CHILD.iterdir() if p.is_file()} if CHILD.exists() else {}
write('final.json',dict(status='ACCEPTED_GKT11_CPU_COMPUTE_NOT_FITTED' if accepted else 'REJECTED_GKT_KEEP_ALL',
    errors=errors,counts=actual_counts,child_result=child,owned_receipt=receipt,source_before=before,source_after=after,
    runtime_before=r_before,runtime_after=r_after,packet_sha256=sys.argv[1],outputs=outputs,elapsed_seconds=elapsed(),cap_seconds=60,
    prelaunch_available_ram_bytes=available,owned_allocated_seconds=seconds,automatic_retry=False,
    actual_corpus_fit=False,actual_cuda_proof=False,actual_optimizer_body_proof=False))
if elapsed()>=60:write('postwrite_rejection.json',dict(elapsed_seconds=elapsed()));accepted=False
print(json.dumps(dict(accepted=accepted,counts=actual_counts,elapsed_seconds=elapsed())))
raise SystemExit(0 if accepted else 1)
