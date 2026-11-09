"""ROOT-only pure8 local inventory; whole60/owned57/cleanup3/worker53, no ZIP."""
import time
START,WALL=time.perf_counter(),time.time()
from pathlib import Path
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

R=Path(__file__).resolve().parents[4]
P=Path(__file__).resolve().parent
WORKER=P/'check_colab_contract_inventory04.py'
PACKET=P/'colab_contract_inventory04_allocation.json'
OUT=P/'colab-contract-inventory04-owned'
CHILD=P/'colab-contract-inventory04'
TMP=R/'artifacts/akt/local-tests/cbd04'


def need(ok,message):
    if not ok:raise ValueError(message)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def elapsed():return max(time.perf_counter()-START,time.time()-WALL)


def write(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n');stream.flush()


need(len(sys.argv)==2 and not OUT.exists() and not CHILD.exists() and not TMP.exists(),'exclusive reviewed attempt')
raw=PACKET.read_bytes()
need(len(raw)<=65536 and hashlib.sha256(raw).hexdigest()==sys.argv[1],'ROOT packet SHA')
packet=json.loads(raw);pins,inputs,runtimes=packet['source_pins'],packet['fixture_input_pins'],packet['runtime_pins']
need(all(sha(R/n)==h for n,h in pins.items()) and all(sha(R/n)==h for n,h in inputs.items())
     and all(sha(Path(n))==h for n,h in runtimes.items()),'source/fixture/runtime preflight')
need(packet['expected_tests']==8 and packet['outer_seconds']==60 and packet['owned_seconds']==57
     and packet['worker_seconds']==53 and packet['cleanup_seconds']==3 and packet['zip_write_cap']==0,
     'exact8 metadata-only allocation')
sys.path.insert(0,str(R/'scripts/research'))
from windows_owned_worker import entry,run_owned,safe
entry();safe(WORKER);safe(OUT);safe(CHILD);safe(TMP)
need(pins['scripts/research/windows_owned_worker.py']=='0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1','unchanged owned helper')
import psutil
need(Path(psutil.__file__).resolve()==Path(packet['runtime_origins']['psutil']).resolve(),'actual psutil origin')
available=int(psutil.virtual_memory().available)
need(available>=2*1024**3,'fresh2GiB free admission')
owned_seconds=min(57.,60.-elapsed()-3.)
need(owned_seconds>3,'insufficient whole60 remaining; no retry')
receipt=run_owned(WORKER,[sys.argv[1]],OUT,expected_worker_sha256=pins[WORKER.relative_to(R).as_posix()],
    approval_reference='ROOT_REVIEW_REQUIRED_LOCAL_BUNDLE_INVENTORY_PURE8_NO_ZIP_OR_EXPORT',
    max_seconds=owned_seconds,cleanup_reserve_seconds=3,max_output_bytes=32768)
write(OUT/'receipt.json',receipt)
errors=[];counts=child=None
try:
    child=json.loads((CHILD/'result.json').read_bytes());tree=ET.parse(CHILD/'junit.xml').getroot()
    counts={k:sum(int(s.get(k,'0')) for s in tree.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
    need(len(list(tree.iter('testcase')))==counts['tests'],'exact JUnit count')
    need(receipt['accepted'] and receipt['cleanup_accepted'] and receipt['actual_worker_in_job_before_GO']
         and receipt['job_active_after_cleanup']==0 and receipt['popen_handle_closed'] and receipt['cleanup_errors']==[]
         and receipt['returncode']==0,'owned Job cleanup')
    need(counts==dict(tests=8,failures=0,errors=0,skipped=0) and child['counts']==counts
         and child['status']=='ACCEPTED_8_LOCAL_INVENTORY_CASES_PENDING_OUTER' and child['pytest_exit_code']==0,
         'actual8 source/inventory fixtures')
    need(child['source_before']==child['source_after']==pins and child['fixture_inputs_before']==child['fixture_inputs_after']==inputs
         and child['runtime_before']==child['runtime_after']==runtimes and child['allocation_sha256']==sys.argv[1],
         'selected source/fixture/runtime stability')
    need(child['zip_observer_counts']['write_attempts']==0 and child['zip_observer_intact_before_restore']
         and child['zip_method_restored'] and child['global_source_inventory_stability_claim'] is False,
         'actual no-ZIP-writer observer and no global WIP stability claim')
    need(child['metadata_phase_closed'] and child['native_windows_metadata']['fixture_replaced'] is False
         and child['forbidden_attempts']==[] and child['scientific_modules_present']==[] and child['monitor_errors']==[]
         and child['monitor_stopped'] and child['environment_restored'] and child['original_error'] is None
         and child['junit_error'] is None,'purity/restoration/error guards')
    need(len(child['allowed_metadata_devnull_events'])<=3 and child['blocked_write_details']==[],
         'scoped exact NUL stdio only; no source writes')
    need(child['runtime_temp']['path']==child['runtime_temp']['actual_gettempdir']==str(CHILD/'runtime-temp')
         and child['runtime_temp']['separate_from_pytest_basetemp'] is True
         and child['runtime_temp']['cache_restored'] is True,'owned stdlib temp/cache restored, pytest temp separate')
    need(child['resources']['observed_peak_rss_bytes']<=1024**3
         and child['resources']['observed_minimum_available_ram_bytes']>=2*1024**3
         and child['elapsed_seconds']<53 and not any((CHILD/n).exists() for n in ('resource-failure.json','postwrite_rejection.json')),
         'actual resource/time bounds')
except BaseException as error:errors.append(dict(type=type(error).__name__,message=str(error)))
after={n:sha(R/n) for n in pins};inputs_after={n:sha(R/n) for n in inputs};runtime_after={n:sha(Path(n)) for n in runtimes}
outputs={path.name:dict(bytes=path.stat().st_size,sha256=sha(path)) for path in CHILD.iterdir() if path.is_file()} if CHILD.is_dir() else {}
accepted=not errors and after==pins and inputs_after==inputs and runtime_after==runtimes and sha(PACKET)==sys.argv[1] and elapsed()<60
result=dict(status='ACCEPTED_8_LOCAL_SOURCE_INVENTORY_CASES_NO_ZIP_EXPORT' if accepted else 'REJECTED_KEEP_ALL_LOCAL_INVENTORY',
    counts=counts,errors=errors,source_before=pins,source_after=after,fixture_inputs_before=inputs,fixture_inputs_after=inputs_after,
    runtime_before=runtimes,runtime_after=runtime_after,allocation_sha256=sys.argv[1],preflight_available_ram_bytes=available,
    output_inventory=outputs,owned_receipt_sha256=sha(OUT/'receipt.json'),owned_allocated_seconds=owned_seconds,
    elapsed_seconds=elapsed(),cap_seconds=60,worker_seconds=53,cleanup_seconds=3,
    zip_observer_counts=None if child is None else child['zip_observer_counts'],global_source_inventory_stability_claim=False,
    scope_vi='Local in-memory inventory + synthetictmpFS only. Fixed dependencies pinned; incidentalWIP source not globalGatefreeze. No ZIP creation/sourceexport/remote/training/authorization.')
write(OUT/'final.json',result)
if elapsed()>=60:write(OUT/'postwrite_rejection.json',dict(status='REJECTED_OUTER_POSTWRITE_TIME',seconds=elapsed()));accepted=False
print(json.dumps(dict(status=result['status'] if accepted else 'REJECTED_KEEP_ALL_LOCAL_INVENTORY',counts=counts,seconds=elapsed())))
raise SystemExit(0 if accepted else 1)
