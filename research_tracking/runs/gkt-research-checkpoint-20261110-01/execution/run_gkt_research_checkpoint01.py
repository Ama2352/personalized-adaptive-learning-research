"""ROOT-only28fixtures,120whole/116owned/110worker; model11 actual phải đạt trước."""
import time
PERF,WALL,MONO=time.perf_counter,time.time,time.monotonic
START,START_WALL,START_MONO=PERF(),WALL(),MONO()
import hashlib
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
WORKER=PREP/'check_gkt_research_checkpoint01.py'
PACKET=PREP/'gkt_research_checkpoint01_packet.json'
OUT=PREP/'gkt-research-checkpoint01-owned'
CHILD=PREP/'gkt-research-checkpoint01'


def need(value,message):
    if not value:raise ValueError(message)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def elapsed():return max(PERF()-START,WALL()-START_WALL,MONO()-START_MONO)


def read_json(path):
    need(path.is_file() and path.stat().st_size<=1024**2,'bounded regular JSON')
    return json.loads(path.read_bytes())


def write(name,value):
    encoded=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    need(len(encoded.encode('utf-8'))<=2*1024**2,'bounded outer receipt')
    with (OUT/name).open('x',encoding='utf-8') as stream:
        stream.write(encoded);stream.flush();os.fsync(stream.fileno())


need(len(sys.argv)==4,'ROOT packet SHA, actual model11 outer SHA and actual trainer8 outer SHA')
sys.path.insert(0,str(ROOT/'scripts/research'))
from windows_owned_worker import entry,safe,run_owned
entry()
for path in (WORKER,OUT,CHILD,PACKET):safe(path)
need(not OUT.exists() and not CHILD.exists() and not safe(ROOT/'artifacts/akt/local-tests/gcp01').exists(),
     'fresh trainer01 namespaces, no automatic retry')
need(sha(PACKET)==sys.argv[1],'reviewed packet')
packet=read_json(PACKET);pins=packet['source_pins'];runtime=packet['runtime_pins']
need(packet['limits']==dict(whole_seconds=120,owned_seconds=116,worker_seconds=110,cleanup_reserve_seconds=3,
    outer_reserve_seconds=4,max_family_rss_bytes=1024**3,max_worker_highwater_bytes=1024**3,
    minimum_available_ram_bytes=2*1024**3,prelaunch_minimum_available_ram_bytes=4*1024**3,cpu_threads=2,
    metadata_file_bytes=1024**2,child_total_bytes=8*1024**2,stdout_stderr_bytes=65536),'exact reviewed finite caps')
before={n:sha(safe(ROOT/n)) for n in pins};r_before={n:sha(Path(n)) for n in runtime}
need(before==pins and r_before==runtime,'actual applied trainer04/model02/test04 source/runtime pins')
model11_path=safe(ROOT/packet['required_model11']['path'])
need(model11_path.is_file() and sha(model11_path)==sys.argv[2],'actual external model11 SHA before any launch')
model11=read_json(model11_path)
need(model11['status']=='ACCEPTED_GKT11_CPU_COMPUTE_NOT_FITTED' and model11['errors']==[]
    and model11['counts']==dict(tests=11,failures=0,errors=0,skipped=0)
    and model11['owned_receipt']['accepted'] is True and model11['owned_receipt']['cleanup_accepted'] is True
    and model11['owned_receipt']['job_active_after_cleanup']==0 and model11['elapsed_seconds']<60
    and not (model11_path.parent/'postwrite_rejection.json').exists(),
    'actual model11 prerequisite, not metadata probe')
for name in ('src/knowledge_tracing/gkt/research_model.py','tests/gkt/test_research_model.py'):
    need(model11['source_before'][name]==model11['source_after'][name]==pins[name],'exact model11 source binding')
trainer8_path=safe(ROOT/packet['required_trainer8']['path'])
need(trainer8_path.is_file() and trainer8_path.stat().st_size<=2*1024**2
    and sha(trainer8_path)==sys.argv[3]==packet['required_trainer8']['sha256']
    and sys.argv[2]==packet['required_model11']['sha256'],'external exact prerequisite SHAs')
trainer8=json.loads(trainer8_path.read_bytes())
need(trainer8['status']=='ACCEPTED_GKT8_TRAINER_CPU_COMPUTE_NOT_FITTED' and trainer8['errors']==[]
    and trainer8['counts']==dict(tests=8,failures=0,errors=0,skipped=0)
    and trainer8['owned_receipt']['accepted'] is True and trainer8['owned_receipt']['returncode']==0
    and trainer8['owned_receipt']['cleanup_accepted'] is True
    and trainer8['owned_receipt']['job_active_after_cleanup']==0 and trainer8['elapsed_seconds']<90
    and not (trainer8_path.parent/'postwrite_rejection.json').exists(),'genuine current trainer8 acceptance')
for accepted in (model11,trainer8):
    for name,digest in accepted['source_before'].items():
        need(accepted['source_after'][name]==digest==pins[name],'all prerequisite source bindings')
    for name,digest in accepted['runtime_before'].items():
        need(accepted['runtime_after'][name]==digest==runtime[name],'all prerequisite runtime bindings')
probe_ref=packet['required_job_query_proof'];probe_path=safe(ROOT/probe_ref['path'])
need(sha(probe_path)==probe_ref['sha256'],'actual Job API receipt pin')
probe=read_json(probe_path)
need(probe['status']=='ACCEPTED_JOB_QUERY_METADATA_NOT_NATIVE' and probe['error'] is None
    and len(probe['child']['samples'])==6 and probe['child']['handle_closed'] is True
    and probe['receipt']['accepted'] is True and probe['receipt']['cleanup_accepted'] is True
    and probe['receipt']['job_active_after_cleanup']==0,'Kernel query proof does not substitute native model11')
import psutil
available=int(psutil.virtual_memory().available)
if available<4*1024**3:
    OUT.mkdir();write('final.json',dict(status='NO_GO_GKT_RAM_BEFORE_OWNED_LAUNCH',available_ram_bytes=available,
        required_available_ram_bytes=4*1024**3,owned_launch_started=False,actual_native_counters=None,
        packet_sha256=sys.argv[1],model11_result_sha256=sys.argv[2],automatic_retry=False))
    raise SystemExit(1)
seconds=min(116.,120.-elapsed()-4.)
need(seconds>3,'same whole120 with cleanup3/finalreserve4')
receipt=run_owned(WORKER,[sys.argv[1],sys.argv[2],sys.argv[3]],OUT,
    expected_worker_sha256=pins[WORKER.relative_to(ROOT).as_posix()],
    approval_reference='ROOT_REVIEW_REQUIRED_GKT28_CPU_CHECKPOINT_MAX6_ADAM_NOT_FIT_AUTHORITY',
    max_seconds=seconds,cleanup_reserve_seconds=3,max_output_bytes=65536)
errors=[];child=None;actual_counts=None;outputs={}
if not OUT.exists():OUT.mkdir()
write('receipt.json',receipt)
# Preserve any actual partial child result/counts even when the owned launch fails.
try:
    if (CHILD/'result.json').exists():child=read_json(CHILD/'result.json')
    if (CHILD/'junit.xml').exists():
        need((CHILD/'junit.xml').stat().st_size<=1024**2,'bounded actual JUnit')
        cases=list(ET.parse(CHILD/'junit.xml').iter('testcase'))
        actual_counts=dict(tests=len(cases),failures=sum(len(list(c.iter('failure'))) for c in cases),
            errors=sum(len(list(c.iter('error'))) for c in cases),skipped=sum(len(list(c.iter('skipped'))) for c in cases))
    need(receipt['accepted'] is True and receipt['returncode']==0 and receipt['cleanup_accepted'] is True
        and receipt['job_active_after_cleanup']==0 and receipt['actual_worker_in_job_before_GO'] is True
        and receipt['popen_handle_closed'] is True and receipt['errors']==receipt['cleanup_errors']==[],'owned terminal/cleanup')
    need(child is not None and actual_counts is not None,'actual child result and JUnit required')
    ids=[(c.get('classname'),c.get('name')) for c in cases]
    need(len(ids)==len(set(ids))==28
        and ids==[('tests.gkt.test_research_checkpoint',n.split('::',1)[1]) for n in packet['expected_nodeids']],
        'exact28physicalJUnit identities in source order')
    need(child['status']=='ACCEPTED_GKT28_CHECKPOINT_CPU_PENDING_OUTER' and child['pytest_exit_code']==0
        and child['counts']==actual_counts==dict(tests=28,failures=0,errors=0,skipped=0)
        and child['error'] is None and child['junit_error'] is None and child['forbidden']==[],'actual28cases/0FES')
    need(child['counters']==packet['expected_counters'] and len(child['shape_proofs'])==2
        and len(child['gradient_proofs'])==len(child['clip_proofs'])==len(child['step_proofs'])==6,
        'exact two model/six optimizer/serialization workload')
    need(all(row['elements']==24700 and row['named_parameters']==32 and row['registration_delta']==38
             for row in child['shape_proofs']),'registered GKT geometry')
    need(all(row['names'] and row['nonzero_names'] for row in child['gradient_proofs'])
        and all(0<=row['actual_postclip_l2']<=1.00001 for row in child['clip_proofs'])
        and all(row['targets']==16 and row['changed_names'] for row in child['step_proofs']),
        'actual participating gradients/clipping/six parameter updates96targets')
    phases=child['phase_proofs']
    need(len(phases)==3 and all(row['api']=='train_research_epoch' and row['complete'] is True for row in phases)
        and sum(row['deltas']['adam_returned'] for row in phases)==6
        and sum(row['deltas']['optimized_targets'] for row in phases)==96
        and sum(row['deltas']['input_targets'] for row in phases)==96
        and sum(row['deltas']['input_prefix_events'] for row in phases)==144,
        'full E1/control E2/restored E2 scopes')
    need(phases[0]['cumulative_counters']['complete_train_epochs']==1
        and phases[1]['cumulative_counters']['complete_train_epochs']==phases[2]['cumulative_counters']['complete_train_epochs']==2
        and all(phases[1][k]==phases[2][k] for k in
                ('model_state_after','adam_sha256','owned_rng_sha256','normalization_after')),
        'exact same-process E2 control/restored state parity')
    need(child['source_before']==child['source_after']==pins and child['runtime_before']==child['runtime_after']==runtime
        and child['nodeids']==packet['expected_nodeids'] and child['model11_result_sha256']==sys.argv[2]
        and child['trainer8_result_sha256']==sys.argv[3]
        and child['job_query_proof_sha256']==probe_ref['sha256'],'actual bindings')
    need(child['method_restoration']['accepted'] is True and child['environment_restored'] is True
        and child['job_query_handle_closed'] is True and child['monitor_stopped'] is True
        and child['trainer_clock_restored'] is True and child['monitor_errors']==[],'restore/clock/monitor closure')
    memory=child['resources']
    need(memory['samples']>0 and memory['peak_worker_rss_bytes']<=1024**3 and memory['peak_family_rss_bytes']<=1024**3
        and memory['minimum_available_ram_bytes']>=2*1024**3 and memory['maximum_job_processes']>=1,
        'sampled exact Job family and worker1GiB/free2GiB')
    need(child['torch_profile']['cuda_build'] is None and child['torch_profile']['cuda_initialized_after'] is False
        and all(q['value'] is False for q in child['cuda_false_queries']),'genuine CPU metadata')
    need(child['elapsed_seconds']<110 and not any((CHILD/n).exists()
        for n in ('resource-failure.json','postwrite_rejection.json')),'worker110/resource deadline')
    need(all(read_json(CHILD/'cold_canary.json')['absent_before_native'].values()),'actual cold import record')
except BaseException as exc:errors.append(dict(type=type(exc).__name__,message=str(exc)))
after={n:sha(safe(ROOT/n)) for n in pins};r_after={n:sha(Path(n)) for n in runtime}
try:
    files=[p for p in CHILD.iterdir() if p.is_file()] if CHILD.exists() else []
    need(len(files)<=12 and all(p.stat().st_size<=1024**2 for p in files)
        and sum(p.stat().st_size for p in files)<=8*1024**2,'bounded direct child outputs')
    outputs={p.name:dict(bytes=p.stat().st_size,sha256=sha(safe(p))) for p in files}
except BaseException as exc:errors.append(dict(type=type(exc).__name__,message=str(exc)))
artifact_references={}
try:
    base=safe(ROOT/'artifacts/akt/local-tests/gcp01')
    artifacts=[path for path in base.rglob('*') if path.is_file()] if base.exists() else []
    need(len(artifacts)<=96 and sum(path.stat().st_size for path in artifacts)<=32*1024**2,
         'bounded owned fixture binary/reference inventory')
    for path in artifacts:
        need(path.stat().st_size<=8*1024**2,'fixture leaf byte cap')
        artifact_references[path.relative_to(ROOT).as_posix()]=dict(bytes=path.stat().st_size,sha256=sha(safe(path)))
    need(bool(artifacts) or errors,'actual checkpoint files required on acceptance')
except BaseException as exc:errors.append(dict(type=type(exc).__name__,message=str(exc)))
accepted=(not errors and after==before and r_after==r_before and sha(PACKET)==sys.argv[1]
    and sha(model11_path)==sys.argv[2] and sha(trainer8_path)==sys.argv[3] and sha(probe_path)==probe_ref['sha256'] and elapsed()<120)
write('final.json',dict(status='ACCEPTED_GKT28_CPU_EPOCH_CHECKPOINT_NOT_LIFECYCLE_FIT' if accepted else 'REJECTED_GKT_KEEP_ALL',
    errors=errors,counts=actual_counts,child_result=child,owned_receipt=receipt,source_before=before,source_after=after,
    runtime_before=r_before,runtime_after=r_after,packet_sha256=sys.argv[1],model11_result_sha256=sys.argv[2],trainer8_result_sha256=sys.argv[3],
    job_query_proof_sha256=probe_ref['sha256'],outputs=outputs,artifact_references=artifact_references,elapsed_seconds=elapsed(),cap_seconds=120,
    prelaunch_available_ram_bytes=available,owned_allocated_seconds=seconds,automatic_retry=False,
    actual_corpus_fit=False,actual_cuda_proof=False,actual_optimizer_body_verified=accepted))
if elapsed()>=120:write('postwrite_rejection.json',dict(elapsed_seconds=elapsed()));accepted=False
print(json.dumps(dict(accepted=accepted,counts=actual_counts,elapsed_seconds=elapsed())))
raise SystemExit(0 if accepted else 1)
