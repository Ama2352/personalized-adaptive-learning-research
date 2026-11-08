"""GRAPH19 ROOT-only: hai owned OSworkers nối tiếp, whole150s, không Torch ở parent."""
import time
START,WALL=time.perf_counter(),time.time()
import hashlib
import json
import os
from pathlib import Path
import sys
import threading

R=Path(__file__).resolve().parents[4]
P=Path(__file__).resolve().parent
PACKET=P/'graph_checkpoint_fresh_process01_allocation.json'
WORKER=P/'check_graph_checkpoint_fresh_process01.py'
OUT=P/'graph19-fresh-parent01'
sys.path.insert(0,str(R/'scripts/research'))
from windows_owned_worker import entry,safe,run_owned


def need(ok,message):
    if not ok:raise ValueError(message)


def elapsed():return max(time.perf_counter()-START,time.time()-WALL)


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def file_sha(path,cap=2*1024**2):
    if path.is_relative_to(R):safe(path)
    else:
        need(path in {Path(name) for name in packet['runtime_pins']},'only exact reviewed external runtime origin')
        cursor=Path(path.anchor)
        for part in path.parts[1:]:
            cursor/=part
            need(not cursor.is_symlink() and not getattr(cursor,'is_junction',lambda:False)(),'external runtime alias rejected')
        need(path.resolve()==path,'physical runtime origin required')
    before=path.stat();need(path.is_file() and before.st_size<=cap,'bounded regular input')
    value=hashlib.sha256()
    with path.open('rb') as stream:
        while chunk:=stream.read(1024**2):value.update(chunk)
    after=path.stat()
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'input changed during hash')
    return value.hexdigest()


def write(name,value):
    with (OUT/name).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())


entry()
need(len(sys.argv)==2 and not OUT.exists(),'one exclusive reviewed packetSHA invocation')
raw=PACKET.read_bytes();need(len(raw)<=131072 and hashlib.sha256(raw).hexdigest()==sys.argv[1],'reviewed sourcepacket bytes')
packet=json.loads(raw);pins=packet['source_pins'];allocation=packet['allocation']
need(allocation['producer_run_id']=='graph19-fresh-producer-20261109-01'
    and allocation['consumer_run_id']=='graph19-fresh-consumer-20261109-01','fixed namespace scope')
need(allocation['whole_seconds']==150 and allocation['owned_role_seconds']==60 and allocation['cleanup_seconds']==3
    and allocation['worker_timer_seconds']==53 and allocation['native_work_seconds']==45,'explicit reviewed cumulative budgets')
need(allocation['effective_training_budget']==dict(max_steps=2,max_targets=48,max_seconds=45.,max_rss_bytes=1024**3,min_available_ram_bytes=2*1024**3),'matching inner/outer RAM budget')
need(not any(n in sys.modules for n in ('torch','numpy','knowledge_tracing')),'parent has no framework/domain imports')
for name,digest in pins.items():need(file_sha(R/name)==digest,'source before drift:'+name)
for name,digest in packet['runtime_pins'].items():need(file_sha(Path(name),cap=16*1024**2)==digest,'runtime before drift')
checkpoint_root=R/allocation['producer_checkpoint_directory']
need(checkpoint_root==R/'experiments/akt/results'/allocation['producer_run_id']/'checkpoints/epoch-1','fixed producer checkpoint scope')
need(not (R/'experiments/akt/results'/allocation['producer_run_id']).exists()
    and not (R/'experiments/akt/results'/allocation['consumer_run_id']).exists(),'fresh owned run namespaces only')
for role in ('producer','consumer'):
    need(not (P/('graph19-fresh-'+role+'01')).exists() and not (P/('graph19-fresh-'+role+'01-owned')).exists(),'no stage retry/overwrite')
safe(OUT);OUT.mkdir()
write('reservation.json',dict(kind=packet['kind'],packet_sha256=sys.argv[1],source_before=pins,
    allocation=allocation,actual_counts_unknown_until_terminal=True,permission_scope='HANDMADE_LOCAL_ENGINEERING_ONLY_NOT_SCIENTIFIC_FIT_AUTHORITY'))
timer=threading.Timer(max(.01,147-elapsed()),lambda:os._exit(124));timer.daemon=True;timer.start()
import psutil
roles={};errors=[];handoff_sha=None;producer_done_at=None
worker_sha=pins[WORKER.relative_to(R).as_posix()]


def stage(role,handoff_argument):
    need(elapsed()<140,'global final10s reserve before stage')
    if role=='producer':need(150-elapsed()>=130,'leave complete consumer60+handoff/final reserve before firstGO')
    else:need(150-elapsed()>=70,'leave consumer60+final10 before secondGO')
    available=int(psutil.virtual_memory().available);need(available>=2*1024**3,'current free2GiB before each modelworker')
    for name,digest in pins.items():need(file_sha(R/name)==digest,'prestage component drift')
    maximum=min(60.,150-elapsed()-10.)
    owned=P/('graph19-fresh-'+role+'01-owned');child=P/('graph19-fresh-'+role+'01')
    began=elapsed()
    receipt=run_owned(WORKER,[sys.argv[1],role,handoff_argument],owned,expected_worker_sha256=worker_sha,
        approval_reference='ROOT_REVIEW_REQUIRED_GRAPH19_TWO_FRESH_OS_PROCESSES_HANDMADE_STATE_ONLY',
        max_seconds=maximum,cleanup_reserve_seconds=3,max_output_bytes=32768)
    write(role+'_owned_receipt.json',receipt)
    row=dict(role=role,started_at_parent_seconds=began,returned_at_parent_seconds=elapsed(),owned_max_seconds=maximum,
        preflight_available_ram_bytes=available,receipt=receipt,result=None,result_sha256=None)
    roles[role]=row
    result_path=child/'result.json'
    if result_path.is_file():
        digest=file_sha(result_path);result=json.loads(result_path.read_bytes())
        row.update(result=result,result_sha256=digest)  # Preserve failed/partial counters too, never infer0.
    need(receipt['accepted'] is True and receipt['cleanup_accepted'] is True and receipt['returncode']==0
        and receipt['actual_worker_in_job_before_GO'] is True and receipt['job_active_after_cleanup']==0
        and receipt['popen_handle_closed'] is True and receipt['cleanup_errors']==[],'owned stage terminalRC0+reapedJob0:'+role)
    need(row['result'] is not None,'actual terminal child result required')
    result=row['result'];digest=row['result_sha256']
    need(result['status']=='ACCEPTED_GRAPH19_'+role.upper()+'_PENDING_PARENT'
        and result['original_error'] is None,'actual child stage accepted:'+role)
    need(result['owner']['worker']==receipt['actual_worker'] and result['owner']['parent_owner']==receipt['parent'],
        'actual worker kernel token, not venv shim/selfreportedPID')
    need(result['native_started']==result['native_body_returned']==allocation['roles'][role]['counter_caps'],'exact role physical counts')
    need(result['source_before']==result['source_after']==pins and result['runtime_before']==result['runtime_after']==packet['runtime_pins']
        and result['packet_sha256']==result['packet_sha256_after']==sys.argv[1],'stage input/source/runtime identity')
    need(result['method_restoration']['accepted'] is True and result['forbidden_attempts']==[]
        and result['monitor_errors']==[] and result['monitor_stopped'] is True and result['environment_restored'] is True,'stage scope/restoration')
    need(result['resources']['observed_peak_rss_bytes']<=1024**3 and result['resources']['observed_minimum_available_ram_bytes']>=2*1024**3
        and result['elapsed_seconds']<53 and result['native_work_seconds']<45,'stage observed resources/deadline')
    need(not any((child/name).exists() for name in ('resource-failure.json','postwrite_rejection.json')),'stage latefailure marker')
    need(len(result['local_git_calls'])==10 and len(result['original_loaders'])==1
        and result['original_loaders'][0]['original'] is True and result['original_loaders'][0]['cached'] is False,
        'genuine one upstream loader per distinct process')
    row.update(result=result,result_sha256=digest)
    write(role+'_accepted.json',dict(role=role,result_sha256=digest,actual_worker=receipt['actual_worker'],
        owned_receipt_sha256=file_sha(OUT/(role+'_owned_receipt.json')),parent_elapsed_seconds=elapsed()))
    return row


try:
    producer=stage('producer','-')
    producer_done_at=elapsed()
    p=producer['result']['proof'];ref=p['checkpoint']
    need(p['e1_counters']['completed_epochs']==1 and p['e1_counters']['body_returns']==2
        and p['e1_counters']['optimized_targets']==48 and p['full_epoch2']['complete'] is True
        and p['full_epoch2']['epoch_windows']==8 and p['full_epoch2']['epoch_targets']==48
        and p['full_epoch2']['epoch_optimizer_steps']==2,'actual completeE1 and complete controlE2')
    need(ref['directory']==allocation['producer_checkpoint_directory'],'fixed externally handed checkpoint')
    expected={'COMPLETE.json':ref['complete_sha256'],'metadata.json':ref['metadata_sha256'],'state.pt':ref['checkpoint_sha256']}
    safe(checkpoint_root)
    need({f.name for f in checkpoint_root.iterdir()}==set(expected),'complete exact three-file E1 artifact, no pending/failure')
    for name,digest in expected.items():need(file_sha(checkpoint_root/name,cap=64*1024**2)==digest,'parent physical checkpoint byteSHA:'+name)
    need((checkpoint_root/'state.pt').stat().st_size==ref['checkpoint_bytes'],'parent exact checkpoint size')
    complete=json.loads((checkpoint_root/'COMPLETE.json').read_bytes());meta=json.loads((checkpoint_root/'metadata.json').read_bytes())
    need(complete['status']=='COMPLETE_CGAKT_EPOCH_TRAINING_STATE' and complete['metadata_sha256']==ref['metadata_sha256']
        and complete['checkpoint_sha256']==ref['checkpoint_sha256'] and meta['identity']==p['identity'],'actual COMPLETE/metadata/source identity')
    need(meta['receipt']['model_sha256']==p['e1_counters']['model_sha256'] and meta['receipt']['optimizer_sha256']==p['e1_counters']['adam_sha256'],
        'E1 checkpoint state/progress agrees producer receipt')
    handoff=dict(kind='TRUSTED_OWNED_PARENT_HANDOFF_NOT_EXECUTION_OR_SELECTION_AUTHORITY',packet_sha256=sys.argv[1],
        producer_result_sha256=producer['result_sha256'],producer_receipt_sha256=file_sha(OUT/'producer_owned_receipt.json'),
        producer_actual_worker=producer['receipt']['actual_worker'],producer_reaped_job_empty=True,
        producer_finished_at_parent_seconds=producer_done_at,checkpoint=ref)
    write('handoff.json',handoff);handoff_sha=file_sha(OUT/'handoff.json')
    consumer=stage('consumer',handoff_sha)
    a,b=producer['receipt']['actual_worker'],consumer['receipt']['actual_worker']
    need(a['pid']!=b['pid'] and int(a['created_filetime_100ns'])<int(b['created_filetime_100ns'])
        and producer['receipt']['job_name']!=consumer['receipt']['job_name'],'two distinct actual OS processes/creationtokens/jobs')
    need(consumer['started_at_parent_seconds']>producer_done_at and producer['receipt']['parent']==consumer['receipt']['parent'],
        'same supervisor starts consumer only after producer fully reaped')
    c=consumer['result']['proof']
    for key in ('plan','identity','profile','checkpoint','e1_rng_digests','e1_module_modes','e1_counters',
        'full_epoch2','final_model_sha256','final_adam_sha256','final_rng_digests','final_module_modes','readout'):
        need(p[key]==c[key],'independent parent exact cross-process comparison:'+key)
    need(c['immediate_three_rng_modes_restored'] is True and consumer['result']['handoff_sha256']==handoff_sha,'actual post-perturbation restore+handevidence')
    need(p['tracker_cumulative_bodies']==c['tracker_cumulative_bodies']==4
        and p['physical_optimizer_bodies']==4 and c['physical_optimizer_bodies']==2,'six physical updates, not cumulative4+4 doubled')
    need(p['full_epoch2']['windows_sha256']==meta['receipt']['windows_sha256']
        and p['full_epoch2']['targets_sha256']==meta['receipt']['targets_sha256'], 'same fullphase population, not dropped/duplicated samples')
    write('cross_process_proof.json',dict(status='ACCEPTED_TRUE_FRESH_OS_PROCESS_STATE_PARITY',producer=a,consumer=b,
        producer_reaped_before_consumer=True,model_sha256=c['final_model_sha256'],adam_sha256=c['final_adam_sha256'],
        readout=c['readout'],three_rng_and_modes_restored=True,full_epoch2_population_and_order_exact=True,
        full_epoch2_ledger=c['full_epoch2'],actual_optimizer_bodies=6,actual_optimization_targets=144,
        fitted_research_model=False,lifecycle_resume_supported=False,sampler_resume_supported=False))
except BaseException as error:
    errors.append(dict(type=type(error).__name__,message=str(error)))
source_after=runtime_after={}
try:
    source_after={name:file_sha(R/name) for name in pins}
    runtime_after={name:file_sha(Path(name),cap=16*1024**2) for name in packet['runtime_pins']}
except BaseException as error:errors.append(dict(type=type(error).__name__,message=str(error)))
accepted=not errors and len(roles)==2 and source_after==pins and runtime_after==packet['runtime_pins'] and elapsed()<150
need(not any(n in sys.modules for n in ('torch','numpy','knowledge_tracing')),'no model/runtime import in supervisor')
final=dict(status='ACCEPTED_GRAPH19_TRUE_FRESH_OS_PROCESS_TRAINING_STATE_NOT_LIFECYCLE' if accepted else 'REJECTED_GRAPH19_KEEP_ALL',
    errors=errors,roles={name:dict(actual_worker=row['receipt'].get('actual_worker'),owned_cleanup_accepted=row['receipt']['cleanup_accepted'],
        physical_counts=None if row['result'] is None else row['result'].get('native_body_returned'),result_sha256=row['result_sha256']) for name,row in roles.items()},
    source_before=pins,source_after=source_after,runtime_before=packet['runtime_pins'],runtime_after=runtime_after,
    packet_sha256=sys.argv[1],handoff_sha256=handoff_sha,elapsed_seconds=elapsed(),whole_cap_seconds=150,
    child_owned_cap_seconds=60,each_cleanup_reserve_seconds=3,actual_corpus_fit=False,lifecycle_resume_supported=False,
    scope_vi='Two sequential owned OSprocesses, handmadeE1 state transfer+fullE2 state/sample/order/readout parity. No corpus/teacher/final/GPU/currentGate/mainselection/midcursor/lifecycle resume.')
write('final.json',final)
if elapsed()>=150:
    write('postwrite_rejection.json',dict(status='REJECTED_PARENT_POSTWRITE_TIME',elapsed_seconds=elapsed()));accepted=False
timer.cancel()
print(json.dumps(dict(status=final['status'] if accepted else 'REJECTED_GRAPH19_KEEP_ALL',elapsed_seconds=elapsed(),roles=final['roles'])))
raise SystemExit(0 if accepted else 1)
