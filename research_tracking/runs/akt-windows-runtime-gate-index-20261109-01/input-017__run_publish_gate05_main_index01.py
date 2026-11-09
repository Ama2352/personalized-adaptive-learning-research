"""ROOT-only30s outer cho index publisher, temporary reviewed Git profile."""
import time
START, WALL = time.perf_counter(), time.time()
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys
import threading

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
WORKER = PREP/'publish_gate05_main_index01.py'
WORKER_SHA = '0365e7850af024e3bf99ec87afeaf55e8087822e38c64c26a82e515f1c345414'
OUT = PREP/'gate05-main-index-publication01-owned'
CHILD = PREP/'gate05-main-index-publication01'
INDEX = ROOT/'artifacts/akt/preflight/gate2-main177-win-current-gate-20261109-05.json'
GLOBAL = ROOT/'artifacts/akt/preflight/gate2-current.json'
RUNTIME_PACKET = PREP/'runtime_schema2_main177_01_packet.json'
RUNTIME_PACKET_SHA = 'e4d97a562f4140bfe7b3dbba8bdefda4746ef93d718b6586fc995ac6a31206a9'
RUNTIME_ACCEPTED = PREP/'runtime-schema2-main177-01-owned/final.json'
RUNTIME_ACCEPTED_SHA = 'a5fb17e05ad07b0562ceb05045a8f9f8a2d749490efd18ce465308aa18c37fe6'
GLOBAL_SHA = '9e768aadcf084482a2eeb9be814fc399100dd1a507eaa89afbbae87100365cd6'
BUILD_SHA = '49011f876058e926ffda8c915517b9a08624cd46a7b4cc62b05fae93b2e13c6e'
INPUTS = {
    'outer_receipt':(PREP/'win-current-gate-20261109-05-outer/result.json','9e61948b93e5f52de248cf076cd6225dc5253f48db949dd40c2a706f4e23d69e'),
    'report':(ROOT/'artifacts/akt/preflight/gate2-evidence-win-current-gate-20261109-05.json','9dfc6f8592ef1d90b7430c06dbcbc96a92808f810c503043b5045c5560850afe'),
    'log':(ROOT/'artifacts/akt/preflight/gate2-tests-win-current-gate-20261109-05.log','cbc97aad1e5f28aedc173e6a9c5e0c1b5ee44d92226a97e450191b5b8b8b8eec'),
    'packet':(PREP/'windows_current_gate_packet05.ROOT.json','eb2949554791e9b52c639e1b51d52dc82431be600e920083533869b179f031c4'),
    'worker':(PREP/'windows_current_gate_worker02.py','b59becc9c2af31d10cf20a4afc17a05946a1e9acdd989114d30bcbfb3dc3b374'),
    'controller':(PREP/'windows_current_gate_outer03.py','4722088dadf1dc3e45203bb29c242e22d5d54bd66b4141f46b2ab8df28f64f3e'),
    'runtime':(ROOT/'artifacts/akt/preflight/runtime-schema2-main177-20261109-01.json','3fdddca8d9a39cf80e597cb6dd02701a3c619d64fc0f7ddadb1b6fb885ecd20b'),
    'lock':(ROOT/'requirements-akt.lock.txt','3e721fdb49543ad0888cf02a863826ebc6144c0d1dd670f2490ebcc0d69b8c0a')}


def need(ok, message):
    if not ok: raise ValueError(message)


def elapsed(): return max(time.perf_counter()-START,time.time()-WALL)


def sha(path):
    with safe(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write(path, value):
    with safe(path).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--controller-sha256',required=True)
    parser.add_argument('--approval-reference',required=True)
    args = parser.parse_args()
    sys.path.insert(0,str(ROOT/'scripts/research'))
    global safe
    from windows_owned_worker import entry,run_owned,safe
    entry()
    need(args.approval_reference.strip() and sha(Path(__file__).resolve()) == args.controller_sha256
         and sha(WORKER) == WORKER_SHA,'ROOT exact publisher/outer review')
    need(sha(ROOT/'scripts/research/windows_owned_worker.py') == '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1',
         'reviewed owned helper')
    need(not any(safe(path).exists() for path in (OUT,CHILD,INDEX)),'exclusive publication attempt/index')
    need(sha(RUNTIME_PACKET) == RUNTIME_PACKET_SHA and sha(RUNTIME_ACCEPTED) == RUNTIME_ACCEPTED_SHA,
         'actual accepted runtime and reviewed process profile')
    need(all(sha(path) == digest for path,digest in INPUTS.values()) and sha(GLOBAL) == GLOBAL_SHA,'actual ROOT input pins')
    runtime_receipt = json.loads(RUNTIME_ACCEPTED.read_bytes())
    need(runtime_receipt['status'] == 'ACCEPTED_NATIVE_SCHEMA2_CPU_RUNTIME_ONLY' and runtime_receipt['accepted'] is True
         and runtime_receipt['errors'] == [] and runtime_receipt['runtime_sha256'] == INPUTS['runtime'][1],
         'actual schema2 acceptance required')
    expected_git = json.loads(RUNTIME_PACKET.read_bytes())['git_environment']
    environment = dict(os.environ)
    inherited_git = {name:value for name,value in environment.items() if name.startswith(('GIT_','GH_'))}
    displays = {'GH_PAGER','GIT_PAGER'}
    need(all(name in displays or name in expected_git and value == expected_git[name]
             for name,value in inherited_git.items()),'unreviewed Git environment rejected')
    excluded = sorted(name for name in inherited_git if name in displays)
    pointer_before = GLOBAL.read_bytes()
    native = json.loads(INPUTS['report'][0].read_bytes())
    build = native['build_hashes']
    need(hashlib.sha256(json.dumps(build,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest() == BUILD_SHA,
         'external reviewed full current build identity')
    need(all(sha(ROOT/name) == digest for name,digest in build.items()),'current entire native build map')
    import psutil
    root_process = psutil.Process(); born = root_process.create_time()
    resources = dict(samples=0,minimum_available_ram_bytes=None,processes={})
    resource_errors = []
    sample_lock = threading.Lock()
    def sample():
        with sample_lock:
            need(root_process.create_time() == born,'owned outer PID/ctime')
            available = int(psutil.virtual_memory().available)
            previous = resources['minimum_available_ram_bytes']
            resources['minimum_available_ram_bytes'] = available if previous is None else min(previous,available)
            resources['samples'] += 1
            need(available >= 2*1024**3,'publication free2GiB floor')
            for process in [root_process,*root_process.children(recursive=True)]:
                try:
                    created = process.create_time(); need(created >= born,'descendant identity predates outer')
                    memory = process.memory_info(); peak = max(memory.rss,getattr(memory,'peak_wset',0))
                    key = str(process.pid)+':'+repr(created)
                    previous_peak = resources['processes'].get(key,{}).get('observed_peak_bytes',0)
                    resources['processes'][key] = dict(pid=process.pid,created=created,observed_peak_bytes=max(previous_peak,peak))
                    need(peak <= 1024**3,'publication family per-process RSS1GiB cap')
                except psutil.NoSuchProcess: pass
    sample()
    stop = threading.Event()
    def monitor():
        while not stop.wait(.1):
            try: sample()
            except BaseException as error:
                resource_errors.append(dict(type=type(error).__name__,message=str(error)))
                return  # Acceptance fails. Original owned27 deadline still cleans the whole Job.
    watcher = threading.Thread(target=monitor,daemon=True)
    errors, receipt, result, reader = [],None,None,None
    worker_args = []
    for name,(_,digest) in INPUTS.items(): worker_args.extend(['--'+name.replace('_','-')+'-sha256',digest])
    worker_args.extend(['--self-sha256',WORKER_SHA,'--build-map-sha256',BUILD_SHA,'--global-pointer-sha256',GLOBAL_SHA,
        '--runtime-report',str(INPUTS['runtime'][0]),'--approval-reference',args.approval_reference])
    allocation = None
    try:
        for name in displays: os.environ.pop(name,None)
        os.environ.update(expected_git)
        need({name:value for name,value in os.environ.items() if name.startswith(('GIT_','GH_'))} == expected_git,
             'temporary Win03 profile exact')
        watcher.start()
        allocation = min(27.,30.-elapsed()-1.)
        need(allocation > 25.,'setup left insufficient publication/cleanup allowance')
        receipt = run_owned(WORKER,worker_args,OUT,expected_worker_sha256=WORKER_SHA,
            approval_reference=args.approval_reference,max_seconds=allocation,cleanup_reserve_seconds=3,max_output_bytes=131072)
        write(OUT/'receipt.json',receipt)
        need(receipt['accepted'] is True and receipt['returncode'] == 0 and receipt['cleanup_accepted'] is True
             and receipt['job_active_after_cleanup'] == 0 and receipt['actual_worker_in_job_before_GO'] is True
             and receipt['popen_handle_closed'] is True and receipt['cleanup_errors'] == [],'actual publisher owned completion')
        result = json.loads((CHILD/'result.json').read_bytes())
        need(result['status'] == 'PUBLISHED_GENUINE_GATE05_INDEX_ONLY' and result['accepted'] is True
             and result['errors'] == result['forbidden_attempts'] == [] and result['environment_unchanged'] is True
             and result['execution_authority'] is False and result['elapsed_seconds'] < 24,'actual publisher metadata result')
        need(result['global_pointer_before_sha256'] == result['global_pointer_after_sha256'] == GLOBAL_SHA
             and result['selected_runtime_report'] == INPUTS['runtime'][0].relative_to(ROOT).as_posix(),
             'global pointer and schema2 selection identities')
        index_raw = INDEX.read_bytes()
        index = json.loads(index_raw)
        expected_index = dict(schema_version=1,evidence_file=INPUTS['report'][0].name,evidence_sha256=INPUTS['report'][1],
                              test_log_file=INPUTS['log'][0].name,test_log_sha256=INPUTS['log'][1])
        need(index == expected_index and hashlib.sha256(index_raw).hexdigest() == result['index_sha256'],
             'actual native-format index bytes')
        need(len(result['actual_git_commands']) == 10 and all(row['phase'] == 'PUBLIC_PREFLIGHT_LOCAL_GIT'
             for row in result['actual_git_commands']),'actual original ten Git commands')
        need(result['runtime_preflight']['runtime_report_sha256'] == INPUTS['runtime'][1]
             and result['runtime_preflight']['lock_sha256'] == INPUTS['lock'][1]
             and result['runtime_preflight']['source'] == native['source'],'actual public runtime preflight')
        sys.path.insert(0,str(ROOT/'src'))
        from knowledge_tracing.akt.authorization import require_gate2_evidence
        from knowledge_tracing.akt.config import AKTConfig
        reader = require_gate2_evidence(AKTConfig(),project_root=ROOT,gate2_report=INDEX,lock_file=INPUTS['lock'][0])
        need(reader == result['public_index_reader'] and reader['pointer_sha256'] == result['index_sha256']
             and reader['report_sha256'] == INPUTS['report'][1] and reader['test_log_sha256'] == INPUTS['log'][1],
             'independent outer public reader acceptance')
        need(not any((CHILD/name).exists() for name in ('postwrite-rejection.json','resource-failure.json')),
             'late publisher rejection absent')
        need(all(sha(OUT/name) == digest for name,digest in receipt['output_sha256'].items()),'raw publisher streams')
    except BaseException as error: errors.append(dict(type=type(error).__name__,message=str(error)))
    finally:
        stop.set()
        if watcher.ident is not None: watcher.join(timeout=.5)
        try: sample()
        except BaseException as error: resource_errors.append(dict(type=type(error).__name__,message=str(error)))
        os.environ.clear(); os.environ.update(environment)
    try:
        need(not resource_errors and not watcher.is_alive(),'live family resources/monitor completion')
        need(dict(os.environ) == environment and GLOBAL.read_bytes() == pointer_before,'exact caller environment/global pointer restoration')
        need(all(sha(path) == digest for path,digest in INPUTS.values()) and sha(WORKER) == WORKER_SHA
             and sha(RUNTIME_PACKET) == RUNTIME_PACKET_SHA and sha(RUNTIME_ACCEPTED) == RUNTIME_ACCEPTED_SHA
             and sha(Path(__file__).resolve()) == args.controller_sha256
             and all(sha(ROOT/name) == digest for name,digest in build.items()),'all actual inputs/current source posthash')
        need('torch' not in sys.modules and 'numpy' not in sys.modules,'outer remains metadata only')
    except BaseException as error: errors.append(dict(stage='postcheck',type=type(error).__name__,message=str(error)))
    if not OUT.exists(): safe(OUT).mkdir()
    accepted = not errors and elapsed()<30
    write(OUT/'final.json',dict(status='ACCEPTED_GENUINE_GATE05_MAIN_INDEX_ONLY' if accepted else 'REJECTED_INDEX_PUBLICATION_REVIEW_RETAINED_FILES',
        accepted=accepted,errors=errors,resource_errors=resource_errors,resources=resources,owned_receipt=receipt,
        worker_result=result,outer_public_reader=reader,excluded_inherited_display_variable_names=excluded,
        reviewed_temporary_git_profile=expected_git,environment_restored=dict(os.environ)==environment,
        global_pointer_before_sha256=hashlib.sha256(pointer_before).hexdigest(),global_pointer_after_sha256=sha(GLOBAL),
        worker_sha256=WORKER_SHA,controller_sha256=args.controller_sha256,runtime_acceptance_sha256=RUNTIME_ACCEPTED_SHA,
        source_input_pins={name:dict(path=path.relative_to(ROOT).as_posix(),sha256=digest) for name,(path,digest) in INPUTS.items()},
        index_path=INDEX.relative_to(ROOT).as_posix(),index_sha256=sha(INDEX) if INDEX.exists() else None,
        index_exists=INDEX.exists(),whole_cap_seconds=30,owned_allocated_seconds=allocation,worker_cap_seconds=24,
        elapsed_seconds=elapsed(),automatic_retry=False,execution_authority=False))
    if elapsed()>=30:
        write(OUT/'postwrite-rejection.json',dict(elapsed_seconds=elapsed())); accepted=False
    print(json.dumps(dict(accepted=accepted,elapsed_seconds=elapsed(),index_sha256=sha(INDEX) if INDEX.exists() else None)))
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__': main()
