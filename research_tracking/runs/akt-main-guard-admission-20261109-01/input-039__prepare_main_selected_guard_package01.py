"""SOURCE-ONLY. ROOT-owned metadata proposal/materialization; no fit entrypoint.

prepare-dry audits real public10 and genuine main._metadata before writing only
one wrapped proposal under P. Materialization is a separate exact-dry reviewed
operation. Neither mode invokes require_main_selected_authorization or runner.
"""
import time
START = time.perf_counter()
from pathlib import Path
import argparse
from dataclasses import asdict
import hashlib
import json
import os
import platform
import subprocess
import sys
import threading

R = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
OWNED = P/'main-guard-package01-owned'
OUT = P/'main-guard-package01'
DRY = P/'main_guard_package01_dry.json'
RUN_ID = 'main-a0-guard-only-20261109-01'
CONFIG = R/'experiments/akt/configs'/(RUN_ID+'.json')
AUTH = R/'experiments/akt/authorizations'/(RUN_ID+'.json')
REQUEST = P/'main_selected_actual_guard01_request.ROOT.json'
RUNTIME = R/'artifacts/akt/preflight/runtime-schema2-main177-20261109-01.json'
RUNTIME_SHA = '3fdddca8d9a39cf80e597cb6dd02701a3c619d64fc0f7ddadb1b6fb885ecd20b'
INDEX = R/'artifacts/akt/preflight/gate2-main177-win-current-gate-20261109-05.json'
INDEX_SHA = 'e8162f6efce3ca0a443f6c40f69308b06b610e95d5a02504ba146e92b6f87366'
BENCH = R/'research_tracking/runs/cgakt-context-api-cost-benchmark-20261109-01/attempt02__config.json'
BENCH_SHA = 'c5cc433a4368e9e13fea354b608172bdfc06684be7de8bb4f59f3d35d8265ba3'
CORPUS_ID = 'grade10-development-lifecycle01-20261108'
PUBLIC = R/'artifacts/simulator/corpora'/CORPUS_ID
FORBIDDEN_MODULES = {'torch','pandas','sklearn','scipy','joblib','pyBKT','modal','boto3'}


def need(ok, why):
    if not ok:
        raise ValueError(why)


def deadline():
    need(0 <= time.perf_counter()-START < 50, 'metadata worker50s, no reset')


def sha(path):
    deadline()
    need(path.is_relative_to(R) and path.is_file(), 'same-root regular input')
    cursor = R
    for part in path.relative_to(R).parts:
        cursor /= part
        need(not cursor.is_symlink() and not cursor.is_junction(), 'physical input')
    count = 0
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(65536):
            deadline(); count += len(block)
            need(count <= 32*1024**2, 'per-input32MiB cap')
            digest.update(block)
    return digest.hexdigest()


def raw(value):
    return (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()


def read(path):
    need(path.stat().st_size <= 2*1024**2, 'small JSON')
    return json.loads(path.read_bytes())


def emit(path, payload):
    deadline(); need(len(payload) <= 2*1024**2, 'small exclusive output')
    with path.open('xb') as stream:
        stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    need(path.read_bytes() == payload, 'output readback exact')


def proposal(approval, public_pins):
    # Actual classes from frozen production; no SimpleNamespace or fake corpus.
    from knowledge_tracing.akt.config import AKTConfig,validate_config
    from knowledge_tracing.akt import research_execution as old,research_main_execution as main
    from knowledge_tracing.akt.research_main_stage import MainSelectedStageSpec,PROTOCOL22,ACCOUNTING23
    from knowledge_tracing.research_admission import MainSelectionContext,PROTOCOL21,RECIPE26,ALLOCATION
    from knowledge_tracing.simulator_corpus_reader import CorpusReadLimits,read_public_research_corpus
    from knowledge_tracing.akt.research_graph_condition import (
        GraphTrain80Binding,prepare_research_graph_condition,source_inventory)
    from knowledge_tracing.simulator_bridge import identity_hash
    need(sha(RUNTIME) == RUNTIME_SHA and sha(INDEX) == INDEX_SHA, 'actual schema2/index pins')
    index = read(INDEX)
    gate_path = INDEX.parent/index['evidence_file']
    need(gate_path.parent == INDEX.parent and sha(gate_path) == index['evidence_sha256'], 'real Gate report')
    gate = read(gate_path)
    need(gate['status'] == 'PASS' and len(gate['build_hashes']) == 177, 'actual current Gate177')
    source_pins = dict(gate['build_hashes'])
    for name,pin in source_pins.items():
        need(sha(R/name) == pin, 'actual source177 unchanged')
    budget = old.ResearchResourceBudget(48,6,6,10080,1260,1260,210,1,1,1.,45.,
                                        1024**3,2*1024**3,64*1024**2,8*1024**2,32*1024**2)
    config = AKTConfig(project_root=R,output_dir=R/'experiments/akt/results'/RUN_ID,
        phase='simulator-research',run_id=RUN_ID,execution_enabled=True,
        max_train_users=54,max_val_users=6,max_targets_per_side=11340,max_total_targets=12600,
        max_steps=1,max_seconds=1.,max_wall_seconds=45.,max_rss_bytes=1024**3,min_available_ram_bytes=2*1024**3)
    validate_config(config)
    need(config.max_epochs == 20 and config.patience == 3 and config.dropout == .05
         and config.context == config.target_block == 100 and config.seed == 42,
         'frozen scientific recipe; no tiny-hyperparameter override')
    need(not config.output_dir.exists(), 'fit directory must remain absent')
    research = old.SimulatorResearchSpec(config,CORPUS_ID,public_pins['corpus.json'],PROTOCOL21,budget)
    limits = CorpusReadLimits(8*1024**2,16*1024**2,262144,48,210,12600,15.)
    corpus = read_public_research_corpus(CORPUS_ID,expected_corpus_sha256=public_pins['corpus.json'],
        expected_done_sha256=public_pins['DONE.json'],limits=limits)
    corpus.assert_integrity()
    roles = {name:corpus.role_data(name) for name in ('train','selection','calibration')}
    for name,learners,targets in (('train',48,10080),('selection',6,1260),('calibration',6,1260)):
        need(len(roles[name].trajectories) == learners and roles[name].audit['audit']['targets'] == targets
             and roles[name].reference_complete, 'complete genuine public role')
    shard = {name:role.audit['audit']['shard_sha256'] for name,role in roles.items()}
    train_binding = GraphTrain80Binding(CORPUS_ID,public_pins['corpus.json'],corpus.done_sha256,
        corpus.plan.identity,roles['train'].provenance.identity,public_pins['train.jsonl'],
        identity_hash(corpus.bank.identity),shard['train'],shard['selection'],shard['calibration'])
    condition = prepare_research_graph_condition(variant='A0',graph_mode='none',bank=corpus.bank,
        nodes=(),edges=(),train80=train_binding,expected_sources=source_inventory())
    context = MainSelectionContext('grade10_simulator',PROTOCOL21,RECIPE26,ALLOCATION,
        identity_hash(corpus.bank.identity),public_pins['bank.json'],corpus.plan.identity,
        shard['train'],shard['selection'])
    stage = MainSelectedStageSpec('A0',context,PROTOCOL22,ACCOUNTING23,
        old.native_auth.config_hash(config),identity_hash(source_pins),RUNTIME_SHA,None,None)
    graph = main.MainGraphInput(None,None,None,None,None,None,condition.identity)
    # These are inert authorized upper limits; context/checkpoint modules and
    # neural constructors are deliberately not imported by this metadata phase.
    context_limits = dict(max_total_events=12600,max_events_per_learner=210,max_targets=12600,
        max_windows=180,max_window_tokens=200,max_parent_records=340200,max_observed_rows=2507400,
        max_cache_bytes=64*1024**2,max_seconds=40.)
    cp_limits = dict(max_checkpoint_bytes=64*1024**2,max_metadata_bytes=1024**2,max_tensor_bytes=64*1024**2)
    git = main.MainGitProfile('windows-native03-v1','C:/Program Files/Git/cmd/git.exe',main.GIT_EXE_SHA,
        config.source_root.as_posix(),main.EOL_PROOF,main.EOL_SHA,main.WINDOWS_UPSTREAM_FILES)
    spec = main.MainSelectedExecutionSpec(research,stage,limits,graph,json.dumps(context_limits),
        json.dumps(cp_limits),8*1024**2,16*1024**2,2,git)
    lock = R/'requirements-akt.lock.txt'
    evidence = old.ResearchRuntimeEvidence(RUNTIME.relative_to(R).as_posix(),RUNTIME_SHA,
        lock.relative_to(R).as_posix(),sha(lock),INDEX.relative_to(R).as_posix(),INDEX_SHA,
        index['evidence_sha256'],index['test_log_sha256'])
    # Genuine private planning dependency, NOT mocked and NOT an execution grant.
    # Runs original native preflight/Gate/source checks and public metadata audit.
    identity = main._metadata(spec,evidence)
    need(identity['native_evidence']['build_hashes'] == source_pins, 'actual metadata source identity')
    for name,pin in main.DOCS:
        need(sha(R/name) == pin, 'adopted document source pin')
        source_pins[name] = pin
    for path in (Path(__file__).resolve(),P/'run_prepare_main_selected_guard_package01.py',
                 P/'check_main_selected_guard01.py',P/'run_main_selected_guard01.py',
                 R/'scripts/research/windows_owned_worker.py'):
        source_pins[path.relative_to(R).as_posix()] = sha(path)
    auth = dict(schema_version=1,scope=main.SCOPE,decision='AUTHORIZE_BOUNDED_MAIN_SELECTED_ONLY',
        run_id=RUN_ID,config_sha256=old.native_auth.config_hash(config),execution_spec_sha256=spec.identity,
        stage_spec_sha256=stage.identity,identity=identity,
        caps=dict(research_budget=asdict(budget),read_limits=asdict(limits),context_limits=context_limits,
            checkpoint_limits=cp_limits,max_graph_input_bytes=spec.max_graph_input_bytes,
            max_output_bytes=spec.max_output_bytes,cpu_threads=2,git_profile=asdict(git)),
        requested_phases=list(main.PHASES),approval_reference=approval)
    config_wire = main.canonical(asdict(config))
    auth_wire = main.canonical(auth)
    parameters = main.canonical(asdict(spec))
    parameters['research'].pop('native_config')
    request = dict(schema_version=1,kind='ROOT_REVIEWED_ACTUAL_MAIN_GUARD_ONLY',source_pins=source_pins,
        native_config_file=CONFIG.relative_to(R).as_posix(),native_config_sha256=hashlib.sha256(raw(config_wire)).hexdigest(),
        main_parameters=parameters,runtime_evidence=asdict(evidence),authorization_file=AUTH.relative_to(R).as_posix(),
        authorization_sha256=hashlib.sha256(raw(auth_wire)).hexdigest(),approval_reference=approval)
    return dict(config=config_wire,authorization=auth_wire,request=request)


def main(args):
    global OUT,OWNED
    if args.materialize:
        OUT = P/'main-guard-package01-materialize'
        OWNED = P/'main-guard-package01-materialize-owned'
    sys.path.insert(0,str(R/'scripts/research'))
    from windows_owned_worker import worker_gate
    owner = worker_gate()  # Always before domain/heavy imports or public reads.
    runtime_temp = OWNED/'runtime-temp'
    runtime_temp.mkdir(exist_ok=False)
    os.environ.update(TEMP=str(runtime_temp),TMP=str(runtime_temp),TMPDIR=str(runtime_temp))
    need(not OUT.exists(), 'exclusive preparation attempt')
    OUT.mkdir()
    need(args.approval_reference.strip(), 'ROOT operation reference')
    need(not any(n.split('.')[0] in FORBIDDEN_MODULES|{'numpy'} for n in sys.modules), 'cold metadata worker')
    need(sha(BENCH) == BENCH_SHA, 'committed public corpus reference')
    public_pins = read(BENCH)['public_inputs_sha256']
    need(len(public_pins) == 10, 'exact nine public files plus DONE')
    phase = ['metadata']; denied = []; metadata_calls = []; git_calls = []
    upstream = R/'artifacts/akt/dependencies/upstream'
    tails = [('rev-parse','HEAD'),('status','--porcelain','--untracked-files=all'),('remote','get-url','origin')]
    for name in ('akt.py','README.md','LICENSE'):
        tails += [('hash-object',name),('rev-parse','HEAD:'+name)]
    tails += [('rev-parse','HEAD^{tree}')]
    expected_git = [subprocess.list2cmdline(['git','-C',str(upstream),*tail]) for tail in tails]
    cmd = os.path.normcase(os.path.abspath(str(Path(os.environ['SystemRoot'])/'System32/cmd.exe')))
    def audit(event,values):
        if event == 'import' and (str(values[0]).split('.')[0] in FORBIDDEN_MODULES
                or str(values[0]) in {'knowledge_tracing.paper2_reference','knowledge_tracing.simulator_research_collection',
                                    'knowledge_tracing.akt.research_selected_runner'}):
            denied.append(event+':'+str(values[0])); raise RuntimeError('metadata only, model/teacher imports denied')
        if event == 'subprocess.Popen':
            if phase[0] == 'metadata' and len(metadata_calls) < 3 and type(values[0]) is str and type(values[1]) is str:
                allowed = {cmd.casefold()+' /c "ver"','"'+cmd.casefold()+'" /c "ver"'}
                if os.path.normcase(os.path.abspath(values[0])) == cmd and values[1].strip().casefold() in allowed:
                    metadata_calls.append(values[1]); return
            if phase[0] == 'proposal' and len(git_calls) < 10 and values[0] in (None,'git') and values[1] == expected_git[len(git_calls)]:
                git_calls.append(values[1]); return
            denied.append(event); raise RuntimeError('only exact metadata/Git provenance child allowed')
        if event == 'os.system' or event.startswith(('os.spawn','os.posix_spawn')) or event.startswith('socket.') and not (phase[0]=='metadata' and event=='socket.gethostname'):
            denied.append(event); raise RuntimeError('network or undeclared child denied')
        if event in ('open','os.listdir','os.scandir') and values and isinstance(values[0],(str,bytes,os.PathLike)):
            path = Path(os.path.abspath(os.fsdecode(values[0])))
            if path.is_relative_to(R/'artifacts/simulator/corpora') and path not in {PUBLIC/name for name in public_pins}:
                denied.append('nonpublic_corpus'); raise RuntimeError('only exact public10, never oracle/final')
            if any(path == R/name or path.is_relative_to(R/name) for name in ('dataset','artifacts/bkt_baseline','venv','.wsl')):
                denied.append('protected'); raise RuntimeError('protected input denied')
    sys.addaudithook(audit)
    error = None; prepared = None; metadata = None
    stop = threading.Event(); monitor_errors = []; monitor = None
    resources = dict(samples=0,peak_rss_bytes=0,min_available_ram_bytes=None)
    try:
        try:
            native = platform.uname(); processor = platform.processor()
            metadata = dict(system=native.system,release=native.release,version=native.version,machine=native.machine,
                processor_cache_warmed=type(processor) is str,commands=metadata_calls,fixture_replaced=False)
            need(native.system == 'Windows', 'actual Windows metadata')
        finally:
            phase[0] = 'closed_metadata'
        emit(OUT/'windows-metadata.json',raw(metadata))
        import psutil
        proc = psutil.Process()
        def memory():
            deadline(); info = proc.memory_info(); peak = max(info.rss,getattr(info,'peak_wset',0)); free = int(psutil.virtual_memory().available)
            resources['samples'] += 1; resources['peak_rss_bytes'] = max(resources['peak_rss_bytes'],peak)
            old = resources['min_available_ram_bytes']; resources['min_available_ram_bytes'] = free if old is None else min(old,free)
            need(peak <= 1024**3 and free >= 2*1024**3, 'metadata RSS1GiB/free2GiB')
        memory()
        def watch():
            while not stop.wait(.1):
                try:
                    memory()
                except BaseException as exc:
                    monitor_errors.append(str(exc)); os._exit(125)
        monitor = threading.Thread(target=watch,daemon=True); monitor.start()
        before = {name:sha(PUBLIC/name) for name in public_pins}
        need(before == public_pins, 'actual public10 exact bytes')
        need(not any(path.exists() for path in (CONFIG,AUTH,REQUEST)), 'all three final paths absent before any write')
        phase[0] = 'proposal'
        sys.path.insert(0,str(R/'src'))
        prepared = proposal(args.approval_reference,public_pins)
        phase[0] = 'post_proposal'; memory()
        need(len(git_calls) == 10 and not denied and not monitor_errors, 'genuine ten Git commands; no hidden denied attempts')
        wrapped = dict(kind='PROPOSED_MAIN_A0_GUARD_ONLY_PACKAGE_NOT_AUTHORIZATION',execution_authority=False,
            approval_reference=args.approval_reference,proposal=prepared,public_inputs_sha256=public_pins,
            runtime_sha256=RUNTIME_SHA,index_sha256=INDEX_SHA,source_pins=prepared['request']['source_pins'])
        if args.prepare_dry:
            emit(DRY,raw(wrapped))
        else:
            need(args.expected_dry_sha256 and args.review_reference, 'separate exact ROOT dry review')
            need(sha(DRY) == args.expected_dry_sha256 and read(DRY) == wrapped, 'unchanged reviewed dry')
            # Materialization alone is not actual guard admission. All paths
            # are checked absent above; failure keeps partial bytes, no retry.
            for path,value in ((CONFIG,prepared['config']),(AUTH,prepared['authorization']),(REQUEST,prepared['request'])):
                need(path.parent.is_dir(), 'existing reviewed output directory required')
                emit(path,raw(value))
        need({name:sha(PUBLIC/name) for name in public_pins} == before, 'public10 postcheck')
        need(all(sha(R/name) == pin for name,pin in wrapped['source_pins'].items()), 'all source pins postcheck')
        need(sha(RUNTIME) == RUNTIME_SHA and sha(INDEX) == INDEX_SHA, 'runtime/index postcheck')
        memory()
    except BaseException as exc:
        error = dict(type=type(exc).__name__,message=str(exc))
    finally:
        phase[0] = 'closed'; stop.set()
        if monitor is not None:
            monitor.join(timeout=.5)
    accepted = error is None and not denied and not monitor_errors and time.perf_counter()-START < 50
    result = dict(status='METADATA_PACKAGE_PENDING_OUTER' if accepted else 'REJECTED_KEEP_PARTIAL',error=error,
        mode='prepare-dry' if args.prepare_dry else 'materialize',owner=owner,metadata=metadata,
        git_calls=git_calls,denied=denied,resources=resources,monitor_errors=monitor_errors,
        monitor_stopped=monitor is None or not monitor.is_alive(),elapsed_seconds=time.perf_counter()-START,
        model_calls=0,optimizer_calls=0,teacher_calls=0,actual_guard_created=False,actual_selected_fit=False,
        output_sha256={path.relative_to(R).as_posix():sha(path) for path in
            ((DRY,) if args.prepare_dry else (CONFIG,AUTH,REQUEST)) if path.exists()})
    emit(OUT/'result.json',raw(result))
    need(not denied and not monitor_errors, 'final late attempt check')
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare-dry',action='store_true'); mode.add_argument('--materialize',action='store_true')
    parser.add_argument('--approval-reference',required=True)
    parser.add_argument('--expected-dry-sha256'); parser.add_argument('--review-reference')
    main(parser.parse_args())
