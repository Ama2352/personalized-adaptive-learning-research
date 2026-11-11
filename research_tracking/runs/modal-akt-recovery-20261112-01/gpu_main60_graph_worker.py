"""Selected A1/A2/A3 trên Main60, topology/confidence đã ghim từ TRAIN48."""
from dataclasses import asdict
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback
import zipfile

ROOT = Path('/opt/kltn')
REQUEST = json.loads(Path('/opt/candidate-request.json').read_text())
CANDIDATE = REQUEST['candidate_id']
assert CANDIDATE in ('A1_EXPERT','A1_LEARNED','A2_EXPERT','A2_LEARNED','A3_EXPERT','A3_LEARNED')
RUN = REQUEST['run_id']
assert re.fullmatch('modal-main60-'+CANDIDATE.lower().replace('_','-')+'-selected-[0-9]{8}-[0-9]{2}', RUN)
CORPUS = 'grade10-development-lifecycle01-20261108'
OUT = ROOT / 'experiments/akt/results' / (RUN + '-operation')
OUT.mkdir(exist_ok=False)
started = time.monotonic()
result = dict(status='FAILED', research_matrix_completed=False, gpu_requested=True,
              cohort='Main60x210', main60_training=True)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, default=str, allow_nan=False)
        stream.write('\n')


try:
    for archive_name, destination in [('/opt/kltn-input.zip', ROOT),
                                     ('/opt/public-corpus.zip', ROOT)]:
        with zipfile.ZipFile(archive_name) as saved:
            manifest = json.loads(saved.read('MANIFEST.json'))
            pins = manifest.get('files', manifest)
            for name, expected in pins.items():
                assert not Path(name).is_absolute() and '..' not in Path(name).parts
                digest = expected if isinstance(expected, str) else expected['sha256']
                assert hashlib.sha256(saved.read(name)).hexdigest() == digest
                path = destination / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(saved.read(name))
    preflight = ROOT / 'artifacts/akt/preflight'
    preflight.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile('/opt/cpu-gate.zip') as saved:
        inventory = json.loads(saved.read('SHA256.json'))
        for name, expected in inventory.items():
            raw = saved.read(name)
            assert hashlib.sha256(raw).hexdigest() == expected['sha256']
            if name.startswith('gate2-'):
                assert Path(name).name == name
                (preflight / name).write_bytes(raw)
    lock = ROOT / 'artifacts/akt/runtime/modal-linux-cuda.lock.txt'
    shutil.copyfile('/opt/locked-cu126.txt', lock)
    upstream = ROOT / 'artifacts/akt/dependencies/upstream'
    git = str(Path(shutil.which('git')).resolve())
    git_environment = dict(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_COUNT='3',
        GIT_CONFIG_KEY_0='core.fsmonitor', GIT_CONFIG_VALUE_0='false',
        GIT_CONFIG_KEY_1='safe.directory', GIT_CONFIG_VALUE_1=upstream.as_posix(),
        GIT_CONFIG_KEY_2='core.autocrlf', GIT_CONFIG_VALUE_2='false',
        GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0', GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__')
    assert not {k for k in os.environ if k.startswith(('GIT_', 'GH_'))}
    os.environ.update(git_environment, CUDA_VISIBLE_DEVICES='0', CUBLAS_WORKSPACE_CONFIG=':4096:8',
                      OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
                      PYTHONDONTWRITEBYTECODE='1')
    runtime_file = preflight / (RUN + '-runtime.json')
    subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'scripts/akt/check_runtime.py'),
                    '--upstream', str(upstream), '--device', 'cuda', '--lock-file', str(lock),
                    '--output', str(runtime_file)], check=True, timeout=30)
    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.akt.config import AKTConfig, ResearchCUDAExecutionProfile
    from knowledge_tracing.akt import research_execution as old
    from knowledge_tracing.akt import research_main_execution as main
    from knowledge_tracing.akt.research_main_stage import MainSelectedStageSpec, PROTOCOL22, ACCOUNTING23
    from knowledge_tracing.akt.research_selected_runner import run_main_selected_candidate
    from knowledge_tracing.research_admission import MainSelectionContext, PROTOCOL21, RECIPE26, ALLOCATION
    from knowledge_tracing.simulator_corpus_reader import CorpusReadLimits, read_public_research_corpus
    from knowledge_tracing.akt.research_graph_condition import GraphTrain80Binding
    from knowledge_tracing.simulator_bridge import identity_hash

    import torch
    cuda = ResearchCUDAExecutionProfile(2*1024**3)
    torch.cuda.set_per_process_memory_fraction(cuda.max_vram_bytes/torch.cuda.get_device_properties(0).total_memory, 0)
    torch.use_deterministic_algorithms(True, warn_only=False)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.set_float32_matmul_precision('highest')
    torch.set_num_threads(2)
    result.update(candidate_id=CANDIDATE, gpu_name=torch.cuda.get_device_name(0),
                  compute_capability=list(torch.cuda.get_device_capability(0)), torch_version=torch.__version__)
    budget = old.ResearchResourceBudget(48, 6, 6, 10080, 1260, 1260, 210, 720, 201600,
                                      600., 750., 6*1024**3, 2*1024**3,
                                      64*1024**2, 4*1024**2, 32*1024**2)
    config = AKTConfig(device='cuda', phase='simulator-research', run_id=RUN,
        output_dir=ROOT / 'experiments/akt/results' / RUN, execution_enabled=True,
        max_train_users=54, max_val_users=6, max_targets_per_side=11340, max_total_targets=12600,
        max_steps=720, max_seconds=600., max_wall_seconds=750.,
        max_rss_bytes=6*1024**3, min_available_ram_bytes=2*1024**3)
    corpus_root = ROOT / 'artifacts/simulator/corpora' / CORPUS
    limits = CorpusReadLimits(8*1024**2, 16*1024**2, 262144, 48, 210, 12600, 15.)
    corpus = read_public_research_corpus(CORPUS, expected_corpus_sha256=sha(corpus_root/'corpus.json'),
        expected_done_sha256=sha(corpus_root/'DONE.json'), limits=limits)
    roles = {role: corpus.role_data(role) for role in ('train', 'selection', 'calibration')}
    shards = {role: value.audit['audit']['shard_sha256'] for role, value in roles.items()}
    train_binding = GraphTrain80Binding(CORPUS, sha(corpus_root/'corpus.json'), corpus.done_sha256,
        corpus.plan.identity, roles['train'].provenance.identity, sha(corpus_root/'train.jsonl'),
        identity_hash(corpus.bank.identity), shards['train'], shards['selection'], shards['calibration'])
    condition_path = ROOT/REQUEST['condition_file']
    assert condition_path.is_relative_to(ROOT/'research_tracking/runs/main60-graph-condition-binding-20261110-01')
    assert sha(condition_path) == REQUEST['condition_sha256']
    bound = json.loads(condition_path.read_text())
    assert bound['train80'] == asdict(train_binding)
    graph_input = main.MainGraphInput(**bound['main_graph_input'])
    pointer_path = preflight / 'gate2-current.json'
    pointer = json.loads(pointer_path.read_text())
    gate = json.loads((preflight / pointer['evidence_file']).read_text())
    evidence = old.ResearchRuntimeEvidence(runtime_file.relative_to(ROOT).as_posix(), sha(runtime_file),
        lock.relative_to(ROOT).as_posix(), sha(lock), pointer_path.relative_to(ROOT).as_posix(),
        sha(pointer_path), pointer['evidence_sha256'], pointer['test_log_sha256'])
    source = dict(commit=config.source_commit, tree=subprocess.check_output(
        [git, '-C', str(upstream), 'rev-parse', 'HEAD^{tree}'], text=True).strip(),
        remote=subprocess.check_output([git, '-C', str(upstream), 'remote', 'get-url', 'origin'], text=True).strip(),
        files={name: sha(upstream/name) for name, _ in main.LINUX_UPSTREAM_FILES})
    proof_file = ROOT / 'artifacts/akt/runtime' / (RUN + '-linux-source.json')
    write(proof_file, dict(schema_version=1, kind='MAIN_LINUX_CUDA_SOURCE_PROVENANCE_V1',
        platform_id=sys.platform, project_root=str(ROOT), python=sys.executable, python_prefix=sys.prefix,
        source_root=str(upstream), git=dict(executable=git, executable_sha256=sha(Path(git))),
        git_environment=git_environment, source=source, source_before=source['files'],
        source_after={name: sha(upstream/name) for name, _ in main.LINUX_UPSTREAM_FILES},
        runtime_report_sha256=sha(runtime_file), lock_sha256=sha(lock)))
    git_profile = main.MainLinuxGitProfile('linux-cuda-lf-v1', git, sha(Path(git)), str(upstream),
        proof_file.relative_to(ROOT).as_posix(), sha(proof_file), main.LINUX_UPSTREAM_FILES)
    context = MainSelectionContext('grade10_simulator', PROTOCOL21, RECIPE26, ALLOCATION,
        identity_hash(corpus.bank.identity), sha(corpus_root/'bank.json'), corpus.plan.identity,
        shards['train'], shards['selection'])
    stage = MainSelectedStageSpec(CANDIDATE, context, PROTOCOL22, ACCOUNTING23,
        old.native_auth.config_hash(config), identity_hash(gate['build_hashes']), sha(runtime_file), graph_input.implementation_condition_sha256, shards['train'])
    context_limits = dict(max_total_events=12600, max_events_per_learner=210, max_targets=12600,
        max_windows=180, max_window_tokens=200, max_parent_records=352800, max_observed_rows=35280000,
        max_cache_bytes=64*1024**2, max_seconds=40.)
    checkpoint_limits = dict(max_checkpoint_bytes=64*1024**2, max_metadata_bytes=1024**2, max_tensor_bytes=64*1024**2)
    spec = main.MainSelectedExecutionSpec(
        old.SimulatorResearchSpec(config, CORPUS, sha(corpus_root/'corpus.json'), PROTOCOL21, budget, cuda_profile=cuda),
        stage, limits, graph_input,
        json.dumps(context_limits), json.dumps(checkpoint_limits), 160*1024**2, 1536*1024**2, 2, git_profile, cuda_profile=cuda)
    identity = main._metadata(spec, evidence)
    authorization = dict(schema_version=1, scope=main.SCOPE, decision='AUTHORIZE_BOUNDED_MAIN_SELECTED_ONLY',
        run_id=RUN, config_sha256=old.native_auth.config_hash(config), execution_spec_sha256=spec.identity,
        stage_spec_sha256=stage.identity, identity=identity,
        caps=dict(research_budget=asdict(budget), read_limits=asdict(limits), context_limits=context_limits,
            checkpoint_limits=checkpoint_limits, max_graph_input_bytes=spec.max_graph_input_bytes,
            max_output_bytes=spec.max_output_bytes, cpu_threads=2, git_profile=asdict(git_profile), cuda_execution_profile=asdict(cuda)),
        requested_phases=list(main.PHASES),
        approval_reference='User20261112: continue AKT setup/training; Main60 graph selected GPU; separate approved batch allocation required')
    authorization_file = ROOT / 'artifacts/akt/runtime' / (RUN + '-authorization.json')
    write(authorization_file, authorization)
    write(OUT/'config.json', asdict(config))
    claim = run_main_selected_candidate(spec, evidence,
        authorization_file=authorization_file.relative_to(ROOT).as_posix(),
        expected_authorization_sha256=sha(authorization_file))
    result.update(status='ACTUAL_GRAPH_CUDA_SELECTED_MAIN60_COMPLETE', claim=asdict(claim))
except BaseException as error:
    result.update(error_type=type(error).__name__, error=str(error))
    (OUT/'failure.log').write_text(traceback.format_exc())
finally:
    result['elapsed_seconds'] = time.monotonic() - started
    write(OUT/'result.json', result)
    print(json.dumps(result), flush=True)
raise SystemExit(0 if result['status']=='ACTUAL_GRAPH_CUDA_SELECTED_MAIN60_COMPLETE' else 1)
