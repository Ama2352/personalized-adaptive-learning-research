"""SOURCE-ONLY. Fresh tiny-A0 metadata proposal/materialization; no fit invocation.

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
OWNED = P/'graph29-a0-resume-package01-owned'
OUT = P/'graph29-a0-resume-package01'
DRY = P/'graph29_a0_resume_package01_dry.json'
RUN_ID = 'main-a0-graph29-resume-engineering10x84-20261110-01'
CONFIG = R/'experiments/akt/configs'/(RUN_ID+'.json')
AUTH = R/'experiments/akt/authorizations'/(RUN_ID+'.json')
REQUEST = P/'graph29_a0_resume01_request.ROOT.json'
RUNTIME = R/'artifacts/akt/preflight/runtime-schema2-main177-20261109-01.json'
RUNTIME_SHA = '3fdddca8d9a39cf80e597cb6dd02701a3c619d64fc0f7ddadb1b6fb885ecd20b'
INDEX = R/'artifacts/akt/preflight/gate2-main183-win-current-gate-20261110-07.json'
INDEX_SHA = 'dd8bd24f6a71e57e6206e56dc9c101648558e8dc7b5779abe015c221ea828fd0'
BENCH = P/'main-engineering10x84-01/outer-final.json'
BENCH_SHA = 'e1745fc0423fd9660218d49a51a57126ac74d40810a2f6c58c8f776bd554c127'
CORPUS_ID = 'grade10-main-lifecycle-engineering10x84-20261109-01'
PUBLIC = R/'artifacts/simulator/corpora'/CORPUS_ID
FORBIDDEN_MODULES = {'torch','pandas','sklearn','scipy','joblib','pyBKT','modal','boto3'}
CONTROL = {
    'outer': (P/'graph29-a0-continuous01/outer-final.json',
              'f796d0cdfb08effe22e36e77630dea986595843de063952bb4da1db2a3f3a14f'),
    'check': (P/'graph29-a0-continuous01/actual-completion-check.json',
              '9d6c259554004ac7b025d221719ee09d3fe659c0f6fe5a91661de4acc06bd065'),
    'request': (P/'graph29_a0_continuous01_request.ROOT.json',
                '5c77bd7ba189dce4606bf0bcc2f9f6e197da50008cfbbfce2df38e6b29792a68'),
    'history': (R/'experiments/akt/results/main-a0-graph29-continuous-engineering10x84-20261110-01/fit80/epochs.json',
                '1e525917180a5e7444e6402c6f88c92c280f3b02b354372b806408d316cde38e'),
}
PARENT_EXPECTED = dict(
    outer='06b12918cdaae355048650948d72bbfda513e060101ac7aa62114732a2cd87ad',
    terminal='68a741ab3b835e60ee85c0da4afd28d1cac19ce4bd4ef8e8e8eff00e00bdc5f3',
    owned='7447ecd57d97f997bd4e49dfb5a78886b60a1e606d1f20d402bf7edda090aba5',
    request='46f38b0439ef1536c624c8056c06d2e7c5683e3dbad9bdc6c840a82266b31bce',
    spec='27fc1fbf1f232cf5a23c4144df4f39bb4d99cd467f2ba1c3728a62e8dfb4534b')


def need(ok, why):
    if not ok:
        raise ValueError(why)


def deadline():
    need(0 <= time.perf_counter()-START < 50, 'metadata worker50s, no reset')


def sha(path, cap=32*1024**2):
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
            need(count <= cap, 'bounded input bytes')
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


def parent_metadata(spec, args):
    """Raw immutable lineage only. Full canonical inspector remains native-only."""
    from knowledge_tracing.akt import research_selected_resume as resume
    need(all(getattr(args,'parent_'+name+'_sha256') == pin for name,pin in PARENT_EXPECTED.items()),
         'external ROOT pins must match actual accepted parent02, not failed01')
    parent = R/'experiments/akt/results/main-a0-graph29-pause5-engineering10x84-20261110-02'
    owned_dir = P/'graph29-a0-pause5-02-owned'
    references = {
        'outer': (P/'graph29-a0-pause5-02/outer-final.json', args.parent_outer_sha256),
        'terminal': (owned_dir/'sealed-parent-terminal.json', args.parent_terminal_sha256),
        'owned': (owned_dir/'receipt.json', args.parent_owned_sha256),
        'request': (P/'graph29_a0_pause5_02_request.ROOT.json', args.parent_request_sha256),
    }
    for file, pin in references.values():
        need(type(pin) is str and len(pin) == 64 and sha(file) == pin, 'external actual parent SHA required')
    outer, terminal, owned, parent_request = (read(references[name][0]) for name in ('outer','terminal','owned','request'))
    need(outer['status'] == 'ACCEPTED_ACTUAL_GRAPH29_PARENT_PAUSE5_SEALED' and outer['error'] is None
         and outer['environment_restored'] is True and outer['owned_receipt'] == owned
         and outer['request_sha256'] == args.parent_request_sha256
         and outer['sealed_parent_file'] == references['terminal'][0].relative_to(R).as_posix()
         and outer['sealed_parent_sha256'] == args.parent_terminal_sha256,
         'actual accepted parent outer correspondence')
    need(terminal['status'] == resume.TERMINAL_STATUS and terminal['schema_version'] == 1
         and terminal['parent_directory'] == parent.relative_to(R).as_posix()
         and terminal['owned_receipt_file'] == references['owned'][0].relative_to(R).as_posix()
         and terminal['owned_receipt_sha256'] == args.parent_owned_sha256
         and terminal['attempt'] == 1 and terminal['charged_wall_seconds'] == 180.
         and terminal['constructors'] == dict(model=1,adam=1), 'actual sealed first attempt, charge180')
    need(owned['accepted'] is True and owned['returncode'] == 0 and owned['cleanup_accepted'] is True
         and owned['job_active_after_cleanup'] == 0 and owned['actual_worker_in_job_before_GO'] is True
         and owned['popen_handle_closed'] is True and owned['errors'] == owned['cleanup_errors'] == []
         and not (owned_dir/'postwrite_rejection.json').exists(), 'genuine cleaned parent, no rejection override')
    parent_worker = P/'check_graph29_a0_pause5_02.py'
    parent_worker_sha = sha(parent_worker)
    need(parent_worker_sha == '1a01f445690ad5f41573df3faaf92d5a9856985f4e97755762d6b5a6908b4664'
         and parent_request['kind'] == 'ROOT_REVIEWED_ACTUAL_MAIN_GRAPH29_PAUSE5_A0_ONLY', 'frozen reviewed parent02')
    proof = terminal['launch_proof']
    resume._launch_proof(spec,parent,references['owned'][0],owned,proof,
        expected_worker_sha256=parent_worker_sha,expected_request_sha256=args.parent_request_sha256,
        expected_spec_sha256=args.parent_spec_sha256)
    outputs = terminal['outputs']
    need(type(outputs) is dict and 0 < len(outputs) <= 256, 'bounded sealed parent output inventory')
    actual = set(); pending = [parent]; directories = 0; retained = 0
    while pending:
        directory = pending.pop(); directories += 1
        need(directories <= 128, 'bounded parent directory traversal')
        for file in directory.iterdir():
            need(not file.is_symlink() and not file.is_junction(), 'physical parent outputs')
            if file.is_dir():
                pending.append(file)
            else:
                actual.add(file.relative_to(parent).as_posix())
                need(len(actual) <= 256, 'bounded parent files')
    need(actual == set(outputs) and not any(Path(name).name in ('failure.json','postwrite_rejection.json')
         for name in actual), 'exact clean parent population')
    for name, row in outputs.items():
        need(set(row) == {'sha256','bytes'} and type(row['bytes']) is int and row['bytes'] >= 0,
             'closed raw output record')
        file = parent/name
        need('..' not in Path(name).parts and not Path(name).is_absolute()
             and sha(file,64*1024**2) == row['sha256'] and file.stat().st_size == row['bytes'], 'sealed raw parent bytes')
        retained += row['bytes']
        need(retained <= spec.max_output_bytes, 'retained parent bytes share child quota')
    marker_path = R/terminal['marker_file']
    need(marker_path == parent/'selected-pause/epoch-5/COMPLETE.json'
         and sha(marker_path) == terminal['marker_sha256'], 'actual complete epoch5 marker')
    marker = read(marker_path)
    need(marker['status'] == resume.PAUSE_STATUS and marker['epoch'] == 5
         and set(marker['files_sha256']) == {'state.json','history.json','accounting.json'}, 'closed sidecars')
    for name, pin in marker['files_sha256'].items():
        need(sha(marker_path.parent/name) == pin, 'actual sidecar SHA')
    state = read(marker_path.parent/'state.json'); history = read(marker_path.parent/'history.json')['epochs']
    accounting = read(marker_path.parent/'accounting.json')
    need(state['epoch'] == 5 and state['next_epoch'] == 6 and state['best_epoch'] == 4
         and state['stopper']['last_epoch'] == 5 and state['stopper']['stale_epochs'] == 1
         and state['stopper']['best_epoch'] == 4 and state['semantic_spec'] == resume.semantic_spec(spec),
         'latest5/best4 continuing semantic identity')
    resume.validate_history(history,state,672)
    need(accounting['steps'] == dict(reserved=10,returned=10,complete=10)
         and accounting['targets'] == dict(reserved=3360,returned=3360,complete=3360)
         and accounting['constructors'] == dict(model=1,adam=1) and accounting['attempt'] == 1
         and type(accounting['training_seconds']) in (int,float)
         and 0 <= accounting['training_seconds'] < 300.
         and accounting['training_seconds'] == terminal['charged_training_seconds'], 'parent physical work retained')
    need(sha(parent/'events.jsonl') == accounting['journal_sha256']
         and (parent/'events.jsonl').stat().st_size == accounting['journal_bytes'], 'no post-boundary journal activity')
    for ref,epoch in ((state['latest'],5),(state['best'],4)):
        directory = Path(ref['directory'])
        need(directory == parent/'checkpoints'/('epoch-'+str(epoch)), 'exact parent latest/best directory')
        for name,key in (('COMPLETE.json','complete_sha256'),('metadata.json','metadata_sha256'),('state.pt','checkpoint_sha256')):
            need(sha(directory/name,64*1024**2) == ref[key], 'opaque checkpoint bytes, no torch.load')
        need(read(directory/'metadata.json')['receipt']['completed_epochs'] == epoch, 'checkpoint epoch metadata')
    request = resume.SelectedResumeRequest(parent.relative_to(R).as_posix(),terminal['marker_sha256'],
        references['terminal'][0].relative_to(R).as_posix(),args.parent_terminal_sha256,parent_worker_sha,
        args.parent_request_sha256,args.parent_spec_sha256,spec.stage.context.allocation_sha256,2,2,3,spec.max_output_bytes)
    refs = {name:dict(path=file.relative_to(R).as_posix(),sha256=pin) for name,(file,pin) in references.items()}
    # Seal all lightweight launch inputs in the child's immutable request sources.
    extra = {file.relative_to(R).as_posix():pin for file,pin in references.values()}
    extra[parent_worker.relative_to(R).as_posix()] = parent_worker_sha
    for name,pin in terminal['launch_proof']['protocol_sha256'].items():
        extra[(owned_dir/name).relative_to(R).as_posix()] = pin
    for field in ('worker_result_file','authorization_file'):
        extra[proof[field]] = proof[field.replace('_file','_sha256')]
    for name,pin in marker['files_sha256'].items():
        extra[(marker_path.parent/name).relative_to(R).as_posix()] = pin
    extra[terminal['marker_file']] = terminal['marker_sha256']
    control_claim = read(CONTROL['check'][0])['claim']
    for name,field in (('predictions.csv','raw_predictions'),('targets.csv','targets'),('coverage.json','coverage')):
        control_export = R/'experiments/akt/results/main-a0-graph29-continuous-engineering10x84-20261110-01/selection'/name
        need(sha(control_export) == control_claim[field]['sha256']
             and control_export.stat().st_size == control_claim[field]['size_bytes'], 'original accepted control export claim')
        extra[control_export.relative_to(R).as_posix()] = control_claim[field]['sha256']
    need('torch' not in sys.modules, 'raw metadata validation must not import canonical full inspector')
    return request,dict(references=refs,outputs=outputs,retained_bytes=retained,
        validation_scope='RAW_BYTES_AND_LAUNCH_BINDINGS_ONLY_CANONICAL_INSPECTION_PENDING_NATIVE'),extra


def proposal(approval, public_pins, args):
    # Actual classes from frozen production; no SimpleNamespace or fake corpus.
    from knowledge_tracing.akt.config import AKTConfig,validate_config
    from knowledge_tracing.akt import research_execution as old,research_main_execution as main
    from knowledge_tracing.akt.research_main_stage import MainSelectedStageSpec,PROTOCOL22,ACCOUNTING23
    from knowledge_tracing.research_admission import MainSelectionContext,PROTOCOL21,RECIPE26,ALLOCATION
    from knowledge_tracing.simulator_corpus_reader import CorpusReadLimits,read_public_research_corpus
    from knowledge_tracing.akt.research_graph_condition import (
        GraphTrain80Binding,prepare_research_graph_condition,source_inventory)
    from knowledge_tracing.simulator_bridge import identity_hash
    from knowledge_tracing.akt.research_selected_resume import control_binding, semantic_spec, _semantic_metadata
    need(sha(RUNTIME) == RUNTIME_SHA and sha(INDEX) == INDEX_SHA, 'actual schema2/index pins')
    index = read(INDEX)
    gate_path = INDEX.parent/index['evidence_file']
    need(gate_path.parent == INDEX.parent and sha(gate_path) == index['evidence_sha256'], 'real Gate report')
    gate = read(gate_path)
    need(gate['status'] == 'PASS' and len(gate['build_hashes']) == 183, 'actual current Gate183')
    source_pins = dict(gate['build_hashes'])
    for name,pin in source_pins.items():
        need(sha(R/name) == pin, 'actual source183 unchanged')
    budget = old.ResearchResourceBudget(8,1,1,672,84,84,84,40,13440,300.,540.,
                                        1024**3,2*1024**3,64*1024**2,4*1024**2,32*1024**2)
    config = AKTConfig(project_root=R,output_dir=R/'experiments/akt/results'/RUN_ID,
        phase='simulator-research',run_id=RUN_ID,execution_enabled=True,
        max_train_users=9,max_val_users=1,max_targets_per_side=756,max_total_targets=840,
        max_steps=40,max_seconds=300.,max_wall_seconds=540.,max_rss_bytes=1024**3,min_available_ram_bytes=2*1024**3)
    validate_config(config)
    need(config.max_epochs == 20 and config.patience == 3 and config.dropout == .05
         and config.context == config.target_block == 100 and config.seed == 42,
         'frozen scientific recipe; no tiny-hyperparameter override')
    need(not config.output_dir.exists(), 'fit directory must remain absent')
    research = old.SimulatorResearchSpec(config,CORPUS_ID,public_pins['corpus.json'],PROTOCOL21,budget)
    limits = CorpusReadLimits(8*1024**2,16*1024**2,262144,8,84,840,15.)
    corpus = read_public_research_corpus(CORPUS_ID,expected_corpus_sha256=public_pins['corpus.json'],
        expected_done_sha256=public_pins['DONE.json'],limits=limits)
    corpus.assert_integrity()
    roles = {name:corpus.role_data(name) for name in ('train','selection','calibration')}
    for name,learners,targets in (('train',8,672),('selection',1,84),('calibration',1,84)):
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
    context_limits = dict(max_total_events=840,max_events_per_learner=84,max_targets=840,
        max_windows=10,max_window_tokens=200,max_parent_records=23520,max_observed_rows=1975680,
        max_cache_bytes=64*1024**2,max_seconds=40.)
    cp_limits = dict(max_checkpoint_bytes=64*1024**2,max_metadata_bytes=1024**2,max_tensor_bytes=64*1024**2)
    git = main.MainGitProfile('windows-native03-v1','C:/Program Files/Git/cmd/git.exe',main.GIT_EXE_SHA,
        config.source_root.as_posix(),main.EOL_PROOF,main.EOL_SHA,main.WINDOWS_UPSTREAM_FILES)
    spec = main.MainSelectedExecutionSpec(research,stage,limits,graph,json.dumps(context_limits),
        json.dumps(cp_limits),8*1024**2,1536*1024**2,2,git)
    for control_path, control_sha in CONTROL.values():
        need(sha(control_path) == control_sha, 'actual continuous control bytes required')
    control_outer, control_check, control_request, control_history = (
        read(CONTROL[name][0]) for name in ('outer','check','request','history'))
    receipt = control_outer['owned_receipt']
    need(control_outer['status'] == 'ACCEPTED_ACTUAL_TINY_A0_SELECTED_ONLY_ENGINEERING'
         and control_outer['error'] is None and control_outer['environment_restored'] is True
         and receipt['accepted'] is True and receipt['cleanup_accepted'] is True
         and receipt['returncode'] == 0 and receipt['job_active_after_cleanup'] == 0,
         'actual completed control and owned cleanup required')
    need(control_check['epochs'] == len(control_history) == 7 and control_check['selected_epoch'] == 4
         and control_check['best_saves'] == 4
         and [row['epoch'] for row in control_history] == list(range(1,8))
         and next(row['epoch'] for row in control_history if row['selected_epoch'] != row['epoch']) == 5
         and control_history[4]['selected_epoch'] == 4, 'first continuing nonbest epoch is actual E5')
    observed = control_check['observed']
    need(observed['training_targets'] == 4704 and observed['selection_targets'] == 672
         and all(observed['counts'][name] == dict(started=count,returned=count,exceptions=0)
                 for name,count in dict(model_constructor=2,adam_constructor=2,adapter_step=14,
                    selection_pass=8,native_forward=22,checkpoint_save=4,checkpoint_restore=1).items()),
         'actual control counters, never hypothetical workload')
    control_config_path = R/control_request['native_config_file']
    need(sha(control_config_path) == control_request['native_config_sha256'], 'actual control configuration')
    control_metadata = dict(control_request['main_parameters'])
    control_metadata['research'] = dict(control_metadata['research'], native_config=read(control_config_path))
    if control_metadata.get('cuda_profile') is None:
        control_metadata.pop('cuda_profile', None)
    need(semantic_spec(spec) == _semantic_metadata(control_metadata), 'parent changes only run/output paths and derived config SHA')
    resume_request, parent_reference, parent_pins = parent_metadata(spec,args)
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
    for path in (Path(__file__).resolve(),P/'run_prepare_graph29_a0_resume_package01.py',
                 P/'check_graph29_a0_resume01.py',P/'run_graph29_a0_resume01.py',
                 R/'scripts/research/windows_owned_worker.py'):
        source_pins[path.relative_to(R).as_posix()] = sha(path)
    control_reference = {name:dict(path=path.relative_to(R).as_posix(),sha256=pin) for name,(path,pin) in CONTROL.items()}
    for path,pin in CONTROL.values():
        source_pins[path.relative_to(R).as_posix()] = pin
    source_pins[control_config_path.relative_to(R).as_posix()] = control_request['native_config_sha256']
    source_pins.update(parent_pins)
    auth = dict(schema_version=1,scope=main.SCOPE,decision='AUTHORIZE_BOUNDED_MAIN_SELECTED_COMPLETE_EPOCH_RESUME',
        run_id=RUN_ID,config_sha256=old.native_auth.config_hash(config),execution_spec_sha256=spec.identity,
        stage_spec_sha256=stage.identity,identity=identity,
        caps=dict(research_budget=asdict(budget),read_limits=asdict(limits),context_limits=context_limits,
            checkpoint_limits=cp_limits,max_graph_input_bytes=spec.max_graph_input_bytes,
            max_output_bytes=spec.max_output_bytes,cpu_threads=2,git_profile=asdict(git)),
        requested_phases=list(main.PHASES),approval_reference=approval,
        resume=control_binding(spec,(None,resume_request)))
    config_wire = main.canonical(asdict(config))
    auth_wire = main.canonical(auth)
    parameters = main.canonical(asdict(spec))
    parameters['research'].pop('native_config')
    request = dict(schema_version=1,kind='ROOT_REVIEWED_ACTUAL_MAIN_GRAPH29_RESUME_A0_ONLY',source_pins=source_pins,
        native_config_file=CONFIG.relative_to(R).as_posix(),native_config_sha256=hashlib.sha256(raw(config_wire)).hexdigest(),
        main_parameters=parameters,runtime_evidence=asdict(evidence),authorization_file=AUTH.relative_to(R).as_posix(),
        authorization_sha256=hashlib.sha256(raw(auth_wire)).hexdigest(),approval_reference=approval,
        resume_request=asdict(resume_request),parent_reference=parent_reference,control_reference=control_reference)
    return dict(config=config_wire,authorization=auth_wire,request=request)


def main(args):
    global OUT,OWNED
    if args.materialize:
        OUT = P/'graph29-a0-resume-package01-materialize'
        OWNED = P/'graph29-a0-resume-package01-materialize-owned'
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
    accepted = read(BENCH)
    need(accepted['status']=='ACCEPTED_GENUINE_ENGINEERING10X84_ONLY'
         and accepted['error'] is None, 'actual distinct engineering corpus acceptance')
    publication = accepted['worker_result']['publication']
    need(publication['corpus_id']==CORPUS_ID and len(publication['files'])==17
         and publication['corpus_sha256']=='78da1a4fd1708bb1efca723caed4976ed518687eb70b847fbdf780f111191151'
         and publication['done_sha256']=='9b565431267a1e0e6f6fb4c05b42a989b2d533d2de98991e64927149b1c5b710',
         'actual corpus/DONE, not canonical60 or manufactured collection')
    public_names={'corpus.json','bank.json','plan.json','train.jsonl','train.manifest.json',
        'selection.jsonl','selection.manifest.json','calibration.jsonl','calibration.manifest.json','DONE.json'}
    public_pins={name:digest for name,digest,size in publication['files'] if name in public_names}
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
        prepared = proposal(args.approval_reference,public_pins,args)
        phase[0] = 'post_proposal'; memory()
        need(len(git_calls) == 10 and not denied and not monitor_errors, 'genuine ten Git commands; no hidden denied attempts')
        wrapped = dict(kind='PROPOSED_MAIN_GRAPH29_RESUME_A0_PACKAGE_NOT_AUTHORIZATION',execution_authority=False,
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
        parent = R/prepared['request']['resume_request']['parent_directory']
        for name,row in prepared['request']['parent_reference']['outputs'].items():
            need(sha(parent/name,64*1024**2) == row['sha256']
                 and (parent/name).stat().st_size == row['bytes'], 'parent opaque postcheck after package writes')
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
    for field in ('outer','terminal','owned','request','spec'):
        parser.add_argument('--parent-'+field+'-sha256',required=True)
    main(parser.parse_args())
