"""ROOT-owned metadata worker tạo index native Gate05 cho explicit main evidence."""
import time
START, WALL = time.perf_counter(), time.time()
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PREFLIGHT = ROOT/'artifacts/akt/preflight'
OUT = PREP/'gate05-main-index-publication01'
INDEX = PREFLIGHT/'gate2-main177-win-current-gate-20261109-05.json'
GLOBAL = PREFLIGHT/'gate2-current.json'
HELPER = ROOT/'scripts/research/windows_owned_worker.py'
HELPER_SHA = '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'
SOURCE_ROOT = ROOT/'artifacts/akt/dependencies/upstream'
GIT = Path('C:/Program Files/Git/cmd/git.exe')
GIT_SHA = '4ab2b391de7fb5eb3afb34b5bd19ee7f71d0450bf7e4c207b201a0392e3825ae'
PROOF = PREP/'upstream_verify_process_eol03.json'
PROOF_SHA = 'cac0e916a29f81f8f716aad5d9df05ea5c9e13c591f000fee0a130d02a499361'
EOL = PREP/'upstream_git_eol_preflight01.json'
EOL_SHA = 'a0307845fbd04ff1b7e52dea821ed9159462005876c4facfdd18be62c40ca6fd'
FIXED = dict(outer_receipt=PREP/'win-current-gate-20261109-05-outer/result.json',
    report=PREFLIGHT/'gate2-evidence-win-current-gate-20261109-05.json',
    log=PREFLIGHT/'gate2-tests-win-current-gate-20261109-05.log',
    packet=PREP/'windows_current_gate_packet05.ROOT.json',
    worker=PREP/'windows_current_gate_worker02.py',
    controller=PREP/'windows_current_gate_outer03.py',
    runtime=PREFLIGHT/'runtime-schema2-main177-20261109-01.json',lock=ROOT/'requirements-akt.lock.txt')


def need(ok, message):
    if not ok: raise ValueError(message)


def elapsed(): return max(time.perf_counter()-START,time.time()-WALL)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def info(path, cap=32*1024**2):
    if path != GIT: safe(path)
    need(path.is_file() and not path.is_symlink() and not path.is_junction(),'physical bounded file')
    count = 0
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(65536):
            count += len(block); need(count <= cap,'metadata/source byte cap'); digest.update(block)
    return dict(bytes=count,sha256=digest.hexdigest())


def raw_json(path):
    safe(path)
    with path.open('rb') as stream: raw = stream.read(8*1024**2+1)
    need(len(raw) <= 8*1024**2,'bounded JSON bytes')
    return json.loads(raw),sha(raw)


def write(path, raw):
    with safe(path).open('xb') as stream:
        need(stream.write(raw) == len(raw),'short metadata write'); stream.flush(); os.fsync(stream.fileno())


def encode(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n').encode()


def main():
    sys.path.insert(0,str(ROOT/'scripts/research'))
    global safe
    from windows_owned_worker import worker_gate,safe
    owner = worker_gate()
    parser = argparse.ArgumentParser(description=__doc__)
    for name in FIXED: parser.add_argument('--'+name.replace('_','-')+'-sha256',required=True)
    parser.add_argument('--self-sha256',required=True)
    parser.add_argument('--build-map-sha256',required=True)
    parser.add_argument('--global-pointer-sha256',required=True)
    parser.add_argument('--runtime-report',type=Path,required=True)
    parser.add_argument('--approval-reference',required=True)
    args = parser.parse_args()
    need(args.approval_reference.strip(),'ROOT metadata publication review')
    selected_runtime = safe(args.runtime_report)
    need(selected_runtime.parent == PREFLIGHT and selected_runtime.is_file(),'actual schema2 runtime in preflight')
    FIXED['runtime'] = selected_runtime
    need(sys.platform == 'win32' and Path(sys.prefix).resolve() == ROOT/'.venv'
         and os.path.normcase(sys.executable) == os.path.normcase(str(ROOT/'.venv/Scripts/python.exe')),
         'actual repository Windows .venv')
    need(not OUT.exists() and not INDEX.exists(),'exclusive metadata attempt and index')
    for value in [args.self_sha256,args.build_map_sha256,args.global_pointer_sha256,
                  *[getattr(args,name+'_sha256') for name in FIXED]]:
        need(len(value) == 64 and all(c in '0123456789abcdef' for c in value),'external SHA256 pins')
    need(info(Path(__file__).resolve())['sha256'] == args.self_sha256
         and info(HELPER)['sha256'] == HELPER_SHA,'publisher/helper source identity')
    before = {name:info(path) for name,path in FIXED.items()}
    need(all(row['sha256'] == getattr(args,name+'_sha256') for name,row in before.items()),'ROOT external actual input hashes')
    outer,outer_sha = raw_json(FIXED['outer_receipt'])
    native,native_sha = raw_json(FIXED['report'])
    packet,packet_sha = raw_json(FIXED['packet'])
    need((outer_sha,native_sha,packet_sha) == (args.outer_receipt_sha256,args.report_sha256,args.packet_sha256),
         'hash and parse the exact ROOT-pinned metadata bytes')
    gate_runtime_reference = packet['runtime_report']
    need(info(ROOT/gate_runtime_reference['path'])['sha256'] == gate_runtime_reference['sha256'],
         'accepted Gate original runtime reference remains exact')
    need(outer['status'] == 'ACCEPTED_WINDOWS_CPU_SOFTWARE_GATE_ONLY' and outer['run_accepted'] is True
         and outer['run_id'] == 'win-current-gate-20261109-05' and outer['errors'] == []
         and outer['publication_requested'] is False and outer['pointer_changed'] is False
         and 0 < outer['elapsed_seconds'] < 630,'actual fresh accepted no-publish Gate05')
    receipt = outer['owned_receipt']
    need(receipt['accepted'] is True and receipt['returncode'] == 0 and receipt['cleanup_accepted'] is True
         and receipt['job_active_after_cleanup'] == 0 and receipt['popen_handle_closed'] is True
         and receipt['actual_worker_in_job_before_GO'] is True,'actual Gate ownership and cleanup')
    need(outer['external_collection_packet_sha256'] == args.packet_sha256
         and outer['controller_source_pins'][FIXED['worker'].relative_to(ROOT).as_posix()] == args.worker_sha256
         and outer['controller_source_pins'][FIXED['controller'].relative_to(ROOT).as_posix()] == args.controller_sha256,
         'actual Gate worker/controller/packet bindings')
    build = native['build_hashes']
    build_raw = json.dumps(build,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
    need(sha(build_raw) == args.build_map_sha256 and len(build) == 177
         and len(native['test_module_sha256']) == 81 and native['status'] == 'PASS'
         and native['test_result'] == dict(passed=packet['expected_native_counts']['merged'],failed=0,errors=0,skipped=0)
         and native['lock_sha256'] == args.lock_sha256 and native['test_log_sha256'] == args.log_sha256,
         'ROOT-pinned actual build/native counts/lock/log')
    for name,row in outer['outputs'].items():
        need(info(ROOT/name) == row,'all accepted outer native artifacts remain exact')
    need(info(PROOF)['sha256'] == PROOF_SHA and info(EOL)['sha256'] == EOL_SHA,'actual reviewed Windows provenance proofs')
    proof,proof_sha = raw_json(PROOF)
    need(proof_sha == PROOF_SHA and proof['status'] == 'ORIGINAL_VERIFY_UPSTREAM_PASSED_WITH_EXPLICIT_INSTALLED_EOL_POLICY'
         and proof['process_config'] == dict(fsmonitor=False,safe_directory=SOURCE_ROOT.as_posix(),autocrlf=True),
         'actual Win03 proof scope')
    git_env = dict(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='nul',GIT_CONFIG_COUNT='3',
        GIT_CONFIG_KEY_0='core.fsmonitor',GIT_CONFIG_VALUE_0='false',
        GIT_CONFIG_KEY_1='safe.directory',GIT_CONFIG_VALUE_1=SOURCE_ROOT.as_posix(),
        GIT_CONFIG_KEY_2='core.autocrlf',GIT_CONFIG_VALUE_2='true',
        GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__')
    need({k:v for k,v in os.environ.items() if k.startswith(('GIT_','GH_'))} == git_env,
         'caller must supply exact reviewed process profile before launch')
    executable = shutil.which('git')
    need(executable and os.path.normcase(os.path.abspath(executable)) == os.path.normcase(str(GIT))
         and info(GIT)['sha256'] == GIT_SHA,'actual approved Git image/origin')
    for directory in (ROOT,Path(sys.executable).parent,Path(sys._base_executable).parent):
        need(not any((directory/name).exists() for name in ('git.exe','git.com','git.cmd','git.bat')),'shadow Git executable')
    environment = dict(os.environ)
    old_pointer = safe(GLOBAL).read_bytes()
    need(sha(old_pointer) == args.global_pointer_sha256,'ROOT external unchanged historical pointer identity')
    safe(OUT).mkdir()
    write(OUT/'global-pointer-before.bytes',old_pointer)
    commands, denied = [], []
    phase = ['metadata_no_subprocess']
    suffixes = [('rev-parse','HEAD'),('status','--porcelain','--untracked-files=all'),('remote','get-url','origin')]
    for name in ('akt.py','README.md','LICENSE'):
        suffixes.extend([('hash-object',name),('rev-parse','HEAD:'+name)])
    suffixes.append(('rev-parse','HEAD^{tree}'))
    expected_commands = [subprocess.list2cmdline(['git','-C',str(SOURCE_ROOT),*suffix]) for suffix in suffixes]
    def audit(event, values):
        if event == 'subprocess.Popen':
            if (phase[0] == 'PUBLIC_PREFLIGHT_LOCAL_GIT' and len(commands) < 10
                    and values[0] in (None,'git') and values[1] == expected_commands[len(commands)]):
                commands.append(dict(raw_executable=values[0],command=values[1],phase=phase[0])); return
            denied.append(event); raise RuntimeError('only exact ten original provenance Git commands')
        if event == 'os.system' or event.startswith('os.spawn') or event.startswith('socket.') and event != 'socket.gethostname':
            denied.append(event); raise RuntimeError('metadata process/network guard')
        if event == 'import' and str(values[0]).split('.')[0] in ('torch','numpy','pandas','sklearn','scipy','duckdb','modal','boto3','pyBKT'):
            denied.append('import:'+str(values[0])); raise RuntimeError('metadata-only import guard')
        if event in ('open','os.listdir','os.scandir') and values and isinstance(values[0],(str,bytes,os.PathLike)):
            actual = os.path.normcase(os.path.abspath(os.fsdecode(values[0])))
            for relative in ('dataset','artifacts/bkt_baseline','artifacts/simulator/corpora','experiments','venv','.wsl'):
                protected = os.path.normcase(str(ROOT/relative))
                if actual == protected or actual.startswith(protected+os.sep):
                    denied.append('protected_data'); raise RuntimeError('metadata publication forbids corpus/model inputs')
    sys.addaudithook(audit)
    timer = threading.Timer(max(.001,24.-elapsed()),lambda:os._exit(124)); timer.daemon=True; timer.start()
    errors, index_raw, validation, runtime = [],None,None,None
    try:
        sys.path.insert(0,str(ROOT/'src'))
        from knowledge_tracing.akt.authorization import gate2_build_hashes,preflight,require_gate2_evidence
        from knowledge_tracing.akt.config import AKTConfig
        need(gate2_build_hashes(ROOT) == build,'current entire native source map')
        config = AKTConfig()
        phase[0] = 'PUBLIC_PREFLIGHT_LOCAL_GIT'
        try:
            runtime = preflight(config,project_root=ROOT,runtime_report_path=FIXED['runtime'],lock_file=FIXED['lock'])
        finally:
            phase[0] = 'metadata_no_subprocess'
        need(len(commands) == 10 and runtime['source'] == native['source']
             and runtime['runtime_report_sha256'] == args.runtime_sha256 and runtime['lock_sha256'] == args.lock_sha256,
             'original public preflight accepts same runtime/native source')
        need(runtime['runtime'].get('runtime_schema_version') == 2 and runtime['runtime'].get('device') == 'cpu'
             and runtime['runtime'].get('cuda_available') is False,'genuine schema2 CPU report required for main metadata')
        index_raw = encode(dict(schema_version=1,evidence_file=FIXED['report'].name,evidence_sha256=args.report_sha256,
            test_log_file=FIXED['log'].name,test_log_sha256=args.log_sha256))
        write(INDEX,index_raw)
        validation = require_gate2_evidence(config,project_root=ROOT,gate2_report=INDEX,lock_file=FIXED['lock'])
        need(validation['pointer_sha256'] == sha(index_raw) and validation['report_sha256'] == args.report_sha256
             and validation['test_log_sha256'] == args.log_sha256,'public index reader acceptance')
        need({name:info(path) for name,path in FIXED.items()} == before and gate2_build_hashes(ROOT) == build,
             'actual input and entire source map posthash')
        need(INDEX.read_bytes() == index_raw and GLOBAL.read_bytes() == old_pointer,'index and global pointer bytes')
        need(require_gate2_evidence(config,project_root=ROOT,gate2_report=INDEX,lock_file=FIXED['lock']) == validation,
             'final genuine reader equality')
    except BaseException as error: errors.append(dict(type=type(error).__name__,message=str(error)))
    finally:
        timer.cancel()
        phase[0] = 'metadata_no_subprocess'
        after_pointer = GLOBAL.read_bytes()
        write(OUT/'global-pointer-after.bytes',after_pointer)
        unchanged_env = dict(os.environ) == environment
        accepted = (not errors and not denied and index_raw is not None and INDEX.exists()
                    and INDEX.read_bytes() == index_raw and old_pointer == after_pointer and unchanged_env and elapsed()<24)
        write(OUT/'result.json',encode(dict(status='PUBLISHED_GENUINE_GATE05_INDEX_ONLY' if accepted else 'REJECTED_RETAIN_INDEX_FOR_REVIEW',
            accepted=accepted,errors=errors,forbidden_attempts=denied,owner=owner,approval_reference=args.approval_reference,
            input_before=before,index_path=INDEX.relative_to(ROOT).as_posix(),
            index_sha256=info(INDEX)['sha256'] if INDEX.exists() else None,index_exists=INDEX.exists(),
            global_pointer_before_sha256=sha(old_pointer),global_pointer_after_sha256=sha(after_pointer),
            environment_unchanged=unchanged_env,actual_git_commands=commands,reviewed_git_environment=git_env,
            runtime_preflight=runtime,public_index_reader=validation,elapsed_seconds=elapsed(),worker_cap_seconds=24,
            selected_runtime_report=FIXED['runtime'].relative_to(ROOT).as_posix(),
            gate_original_runtime_reference=gate_runtime_reference,
            execution_authority=False)))
        if elapsed()>=24:
            write(OUT/'postwrite-rejection.json',encode(dict(elapsed_seconds=elapsed()))); accepted=False
    print(json.dumps(dict(accepted=accepted,result=str(OUT/'result.json'),elapsed_seconds=elapsed())))
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__': main()
