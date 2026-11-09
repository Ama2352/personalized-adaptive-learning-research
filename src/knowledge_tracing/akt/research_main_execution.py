"""Main A0-A3 selected-only guard; old A0 lifecycle permission is not reused.

No fit/CLI/auth-file creation. Only actual closed on-disk authorization plus
current native runtime/Gate/source/public-corpus/graph inputs can produce the
execution object. MainStage and SHA-shaped claims alone never grant execution.
"""
from dataclasses import asdict,dataclass,field,fields
import hashlib
import json
import math
import os
from pathlib import Path,PurePosixPath
import re
import shutil
import sys
import time

from . import research_execution as old
from .config import ResearchCUDAExecutionProfile
from .research_main_stage import MainSelectedStageSpec,PROTOCOL22,ACCOUNTING23
from ..research_admission import PROTOCOL21,RECIPE26,ALLOCATION
from ..simulator_bridge import identity_hash
from ..simulator_corpus_reader import CorpusReadLimits,read_public_research_corpus

SCOPE='simulator-research-main-selected-only-v1'
PHASES=('select_train80','raw_selection10')
DOCS=(('docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md',PROTOCOL21),
      ('docs/thesis_recovery/22_A0_RESEARCH_LIFECYCLE_CONTRACT.md',PROTOCOL22),
      ('docs/thesis_recovery/23_TRAINING_MATRIX_ACCOUNTING_V1.md',ACCOUNTING23),
      ('docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md',RECIPE26),
      ('docs/thesis_recovery/EXPERIMENT_ALLOCATION_V1.json',ALLOCATION))
GIT_EXE_SHA='4ab2b391de7fb5eb3afb34b5bd19ee7f71d0450bf7e4c207b201a0392e3825ae'
EOL_PROOF='artifacts/akt/local-tests/akt-research-runner-20261108-01/upstream_git_eol_preflight01.json'
EOL_SHA='a0307845fbd04ff1b7e52dea821ed9159462005876c4facfdd18be62c40ca6fd'
WINDOWS_UPSTREAM_FILES=(('LICENSE','891133edce0d8693f5b916d4257ce70b71a02aa110cb02cc5d47326544ea4522'),
    ('README.md','df8eea9919dcdb343f3a841540af18e2039b8b0c33af449ca9c752d11f56ee8b'),
    ('akt.py','be2788c20cac602e86ef3a51e5294b37dd7b200f818be4e173dbd69069a3ec6d'))
# Prospective CRLF-to-LF hashes of the pinned Windows bytes, not a Linux receipt.
LINUX_UPSTREAM_FILES=(('LICENSE','50a2c2d2521182935c537a56220083c7a4194abdfbd459b6c682fae32cceb4cf'),
    ('README.md','bec19014f10f469002e46f53175a1599b1be9b2d3fc9fe184129e6da1efd442b'),
    ('akt.py','ace9e4486ea6d8f8c52310a8ddf27212022136eda719c12d8204fab1bfcfdc67'))
UPSTREAM_TREE='904863502337ef2eefd1769d14836b62e3c3804a'
GATE_WRITER='scripts/akt/refresh_gate2.py'
CUDA_RECIPE_PATH='docs/thesis_recovery/28_CUDA_EXECUTION_PROFILE_V1.md'
CUDA_RECIPE_SHA256='57940d5991f90c9c306c2ab442729766489513703153407fe26646b21d963dd0'


def need(ok,message):
    if not ok:raise ValueError(message)


def canonical(value):return old._jsonable(value)


def decode(text):
    need(type(text) is str and len(text.encode())<=65536,'bounded JSON parameter object')
    def pairs(rows):
        result={}
        for key,value in rows:
            need(key not in result,'duplicate parameter JSON key');result[key]=value
        return result
    value=json.loads(text,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
    need(type(value) is dict,'parameter JSON object required');canonical(value)
    return value


@dataclass(frozen=True)
class MainGitProfile:
    """One reviewed Windows process-only profile; no Linux profile promotion."""
    mode: str
    executable: str
    executable_sha256: str
    source_root: str
    eol_proof_file: str
    eol_proof_sha256: str
    upstream_files_sha256: tuple[tuple[str,str],...]

    def __post_init__(self):
        need(self.mode=='windows-native03-v1','separate Linux LF provenance adapter is not implemented')
        need(type(self.executable) is str and self.executable.replace('\\','/').lower()=='c:/program files/git/cmd/git.exe'
             and self.executable_sha256==GIT_EXE_SHA,'reviewed Windows Git binary required')
        old._text(self.source_root)
        need(self.eol_proof_file==EOL_PROOF and self.eol_proof_sha256==EOL_SHA
             and self.upstream_files_sha256==WINDOWS_UPSTREAM_FILES,'actual reviewed Windows EOL/source profile required')


def _linux_absolute(value):
    need(type(value) is str and '\\' not in value and ':' not in value,'absolute POSIX profile path required')
    path=PurePosixPath(value)
    need(path.is_absolute() and path.anchor=='/' and path.as_posix()==value and '..' not in path.parts,
         'canonical absolute POSIX profile path required')
    return path


@dataclass(frozen=True)
class MainLinuxGitProfile:
    """Declared Linux metadata; actual source/runtime/Gate proof is still required."""
    mode: str
    executable: str
    executable_sha256: str
    source_root: str
    proof_file: str
    proof_sha256: str
    upstream_files_sha256: tuple[tuple[str,str],...]

    def __post_init__(self):
        need(self.mode in ('linux-cpu-lf-v1','linux-cuda-lf-v1'),'unsupported Linux Git profile')
        _linux_absolute(self.executable);_linux_absolute(self.source_root)
        old._sha(self.executable_sha256);old._sha(self.proof_sha256)
        need(type(self.proof_file) is str and '\\' not in self.proof_file and ':' not in self.proof_file,
             'relative Linux source proof required')
        proof=PurePosixPath(self.proof_file)
        need(not proof.is_absolute() and proof.as_posix()==self.proof_file and '..' not in proof.parts
             and proof.parts[:2]==('artifacts','akt') and len(proof.parts)>2,'root-bound Linux source proof required')
        need(self.upstream_files_sha256==LINUX_UPSTREAM_FILES,'prospective pinned Linux LF hashes required')


def _git_environment(profile,source_root,platform_name):
    """Pure metadata profile, NOT actual Git/runtime verification."""
    if type(profile) is MainLinuxGitProfile:
        profile.__post_init__()
        need(platform_name=='linux','Linux profile cannot attest another platform')
        need(profile.source_root==source_root.as_posix(),'safe.directory must equal exact native source root')
        return dict(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_COUNT='3',
            GIT_CONFIG_KEY_0='core.fsmonitor',GIT_CONFIG_VALUE_0='false',
            GIT_CONFIG_KEY_1='safe.directory',GIT_CONFIG_VALUE_1=source_root.as_posix(),
            GIT_CONFIG_KEY_2='core.autocrlf',GIT_CONFIG_VALUE_2='false',
            GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__')
    need(type(profile) is MainGitProfile,'concrete Git profile required');profile.__post_init__()
    need(platform_name=='win32','Windows reviewed profile cannot attest Linux LF runtime')
    need(profile.source_root.replace('\\','/')==source_root.as_posix(),'safe.directory must equal exact native source root')
    return dict(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='nul',GIT_CONFIG_COUNT='3',
        GIT_CONFIG_KEY_0='core.fsmonitor',GIT_CONFIG_VALUE_0='false',
        GIT_CONFIG_KEY_1='safe.directory',GIT_CONFIG_VALUE_1=source_root.as_posix(),
        GIT_CONFIG_KEY_2='core.autocrlf',GIT_CONFIG_VALUE_2='true',
        GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__')


def _validate_git_environment(profile,source_root,platform_name,environment):
    """Validate caller metadata only; does not execute/attest Git or Gate."""
    expected=_git_environment(profile,source_root,platform_name)
    actual={k:v for k,v in environment.items() if k.startswith(('GIT_','GH_'))}
    need(actual==expected,'extra/missing Git/credential/transport process config rejected')
    return expected


def _validate_linux_source_proof(profile,config,evidence,proof):
    """Proof metadata consistency only; actual file/Git/runtime checks are separate."""
    root=config.project_root
    need(config.device in ('cpu','cuda') and profile.mode=='linux-'+config.device+'-lf-v1',
         'Linux source profile must match the requested execution device')
    fields={'schema_version','kind','platform_id','project_root','python','python_prefix','source_root','git',
            'git_environment','source','source_before','source_after','runtime_report_sha256','lock_sha256'}
    need(set(proof)==fields and type(proof['schema_version']) is int and proof['schema_version']==1
         and proof['kind']=='MAIN_LINUX_'+config.device.upper()+'_SOURCE_PROVENANCE_V1',
         'actual closed Linux source provenance proof required')
    need(proof['platform_id']=='linux' and proof['project_root']==str(root) and proof['python']==sys.executable
         and proof['python_prefix']==sys.prefix and proof['source_root']==str(config.source_root),
         'Linux proof actual host/interpreter/root binding')
    need(proof['git']==dict(executable=profile.executable,executable_sha256=profile.executable_sha256)
         and proof['git_environment']==_git_environment(profile,config.source_root,'linux'),
         'Linux proof Git binary/process environment binding')
    expected=dict(commit=config.source_commit,tree=UPSTREAM_TREE,remote='https://github.com/arghosh/AKT.git',
                  files=dict(LINUX_UPSTREAM_FILES))
    need(proof['source']==expected and proof['source_before']==proof['source_after']==expected['files']
         and proof['runtime_report_sha256']==evidence.runtime_report_sha256 and proof['lock_sha256']==evidence.lock_sha256,
         'Linux proof original source/runtime/lock binding')


def _linux_source_proof(profile,config,evidence,cap):
    """Read an externally pinned actual proof; never manufacture one from metadata."""
    root=config.project_root
    executable=shutil.which('git')
    need(executable is not None,'actual Linux Git executable required')
    binary=Path(executable);declared=Path(profile.executable)
    need(binary.is_absolute() and binary.resolve()==declared and declared.resolve()==declared
         and old._hash_file(declared,cap=16*1024**2)[0]==profile.executable_sha256,
         'actual physical Linux Git executable/origin/hash')
    for directory in (root,Path(sys.executable).parent,Path(sys._base_executable).parent):
        need(not (directory/'git').exists() and not (directory/'git').is_symlink(),'shadow Linux Git executable rejected')
    proof,pin,_=old._read_json(old._path(root,profile.proof_file),cap)
    need(pin==profile.proof_sha256,'actual Linux source proof SHA mismatch')
    _validate_linux_source_proof(profile,config,evidence,proof)
    for name,digest in LINUX_UPSTREAM_FILES:
        need(old._hash_file(old._path(root,'artifacts/akt/dependencies/upstream/'+name),cap=cap)[0]==digest,
             'actual Linux raw LF source drift')
    return proof


def _linux_gate_profile(config,evidence,runtime,gate,build_hashes,cap):
    """Additional Linux provenance after the unchanged genuine public readers."""
    root=config.project_root
    relative=Path(gate['evidence_path']).relative_to(root).as_posix()
    report,digest,_=old._read_json(old._path(root,relative),cap)
    need(digest==gate['report_sha256']==evidence.gate_report_sha256,'Linux Gate report changed after public reader')
    profile=report.get('execution_profile')
    fields={'schema_version','platform_id','project_root','python','python_prefix','writer_sha256'}
    need(type(profile) is dict and set(profile)==fields and type(profile['schema_version']) is int
         and profile['schema_version']==1,'closed actual Linux Gate execution profile required')
    writer=old._hash_file(old._path(root,GATE_WRITER),cap=cap)[0]
    expected=dict(schema_version=1,platform_id='linux',project_root=str(root),python=sys.executable,
                  python_prefix=sys.prefix,writer_sha256=writer)
    need(profile==expected and build_hashes.get(GATE_WRITER)==writer
         and report.get('build_hashes')==build_hashes,'Linux Gate actual process/writer/current build binding')
    actual=runtime['runtime']
    need(actual.get('platform_id')=='linux' and actual.get('project_root')==profile['project_root']
         and actual.get('python')==profile['python'] and actual.get('python_prefix')==profile['python_prefix'],
         'Linux Gate/runtime process binding')


def _main_native_evidence(spec,evidence):
    """Same genuine native validators; only process-profile admission differs.

    No stripping/restoring env, Git override, filters bypass or global config.
    preflight still executes original verify_upstream commands/PIN/remote/bytes.
    """
    research=spec.research;c=research.native_config;root=c.project_root;cap=research.budget.max_input_bytes
    _validate_git_environment(spec.git_profile,c.source_root,sys.platform,os.environ)
    linux=type(spec.git_profile) is MainLinuxGitProfile
    if linux:
        proof=_linux_source_proof(spec.git_profile,c,evidence,cap)
    else:
        executable=shutil.which('git')
        need(executable is not None and os.path.normcase(os.path.abspath(executable))==os.path.normcase(os.path.abspath(spec.git_profile.executable))
             and old._hash_file(Path(executable),cap=16*1024**2)[0]==GIT_EXE_SHA,'actual Git executable/origin/hash')
        for directory in (root,Path(sys.executable).parent,Path(sys._base_executable).parent):
            need(not any((directory/name).exists() for name in ('git.exe','git.com','git.cmd','git.bat')),'shadow Git executable rejected')
        proof,pin,_=old._read_json(old._path(root,EOL_PROOF),cap)
        need(pin==EOL_SHA and proof['raw_sha256']==dict(WINDOWS_UPSTREAM_FILES)['akt.py']
             and proof['config_autocrlf']['returncode']==0 and proof['config_autocrlf']['stdout'].endswith('\ttrue')
             and proof['normal_hash']['returncode']==proof['isolated_hash']['returncode']==0,
             'reviewed actual EOL comparison proof required, not fabricated normalization')
        for name,pin in WINDOWS_UPSTREAM_FILES:need(old._hash_file(c.source_root/name,cap=cap)[0]==pin,'physical upstream profile drift')
    paths={name:old._path(root,getattr(evidence,name)) for name in ('runtime_report','lock_file','gate_pointer')}
    preflight=root/'artifacts/akt/preflight'
    need(paths['runtime_report'].parent==preflight and paths['gate_pointer'].parent==preflight,'native preflight paths')
    lock=paths['lock_file']
    need((lock.parent==root and re.fullmatch('requirements-akt[^/]*[.]txt',lock.name)) or lock.is_relative_to(root/'artifacts/akt'),'native lock path')
    for name,field_name in (('runtime_report','runtime_report_sha256'),('lock_file','lock_sha256'),('gate_pointer','gate_pointer_sha256')):
        need(old._hash_file(paths[name],cap=cap)[0]==getattr(evidence,field_name),'actual runtime/lock/Gate input bytes')
    venv=root/'.venv'
    need(venv.is_dir() and not venv.is_symlink() and not getattr(venv,'is_junction',lambda:False)()
         and venv.resolve()==venv.absolute(),'physical same-root environment')
    if spec.cuda_profile is None:
        need(os.environ.get('CUDA_VISIBLE_DEVICES','') in ('','-1') and os.environ.get('NVIDIA_VISIBLE_DEVICES','') in ('','none','void'),'CPU main must hide CUDA')
    preflight_args=dict(project_root=root,runtime_report_path=paths['runtime_report'],lock_file=lock)
    if spec.cuda_profile is not None:
        preflight_args['cuda_profile']=spec.cuda_profile
    runtime=old.native_auth.preflight(c,**preflight_args)
    gate=old.native_auth.require_gate2_evidence(c,project_root=root,gate2_report=paths['gate_pointer'],lock_file=lock)
    need(runtime['runtime'].get('runtime_schema_version')==2 and runtime['runtime'].get('device')==c.device
         and runtime['runtime'].get('cuda_available') is (spec.cuda_profile is not None),
         'actual schema2 runtime must match the CPU/CUDA execution profile')
    need(runtime['runtime_report_sha256']==evidence.runtime_report_sha256 and runtime['lock_sha256']==evidence.lock_sha256
         and gate['pointer_sha256']==evidence.gate_pointer_sha256 and gate['report_sha256']==evidence.gate_report_sha256
         and gate['test_log_sha256']==evidence.gate_log_sha256,'genuine runtime/Gate/source/elapsed checks remain mandatory')
    build_hashes=old.native_auth.gate2_build_hashes(root)
    if linux:
        need(runtime['source']==proof['source'],'genuine Linux source verification differs from pinned proof')
        _linux_gate_profile(c,evidence,runtime,gate,build_hashes,cap)
        need(_linux_source_proof(spec.git_profile,c,evidence,cap)==proof,'Linux source proof changed during preflight')
    return dict(runtime=runtime,gate=gate,build_hashes=build_hashes)


@dataclass(frozen=True)
class MainGraphInput:
    topology_file: str | None
    topology_file_sha256: str | None
    method24_reference_json: str | None
    method24_training_json: str | None
    method24_limits_json: str | None
    expected_scores_sha256: str | None
    implementation_condition_sha256: str

    def __post_init__(self):
        old._sha(self.implementation_condition_sha256)
        if self.topology_file is not None:
            old._text(self.topology_file);old._sha(self.topology_file_sha256)
        else:need(self.topology_file_sha256 is None,'topology SHA without file')
        values=(self.method24_reference_json,self.method24_training_json,self.method24_limits_json,self.expected_scores_sha256)
        need(all(v is None for v in values) or all(v is not None for v in values),'complete Method24 request or none')
        if self.method24_reference_json is not None:
            for text in values[:3]:decode(text)
            old._sha(self.expected_scores_sha256)


@dataclass(frozen=True)
class MainSelectedExecutionSpec:
    research: old.SimulatorResearchSpec
    stage: MainSelectedStageSpec
    read_limits: CorpusReadLimits
    graph_input: MainGraphInput
    context_limits_json: str
    checkpoint_limits_json: str
    max_graph_input_bytes: int
    max_output_bytes: int
    cpu_threads: int
    git_profile: MainGitProfile | MainLinuxGitProfile
    cuda_profile: ResearchCUDAExecutionProfile | None = field(default=None,kw_only=True)

    def __post_init__(self):
        need(type(self.research) is old.SimulatorResearchSpec and type(self.stage) is MainSelectedStageSpec,'exact research/stage spec required')
        self.stage.validate()
        # Reject unsupported real environment/family before source/data/model work.
        need(self.stage.context.environment_id=='grade10_simulator','Junyi main producer is not implemented')
        need(self.stage.candidate_id=='A0' or self.stage.candidate_id.startswith(('A1_','A2_','A3_')),
             'SAKT/GKT selected producers pending; required matrix is not waived')
        need(type(self.read_limits) is CorpusReadLimits and type(self.graph_input) is MainGraphInput,'typed data/graph inputs required')
        need(type(self.git_profile) in (MainGitProfile,MainLinuxGitProfile),'typed process-only Git profile required');self.git_profile.__post_init__()
        profile_platform='linux' if type(self.git_profile) is MainLinuxGitProfile else 'win32'
        _git_environment(self.git_profile,self.research.native_config.source_root,profile_platform)
        old.SimulatorResearchSpec(**{f.name:getattr(self.research,f.name) for f in fields(self.research)},
                                  cuda_profile=self.cuda_profile)
        if self.cuda_profile is not None:
            need(type(self.cuda_profile) is ResearchCUDAExecutionProfile,'exact main CUDA profile required')
            self.cuda_profile.__post_init__()
        self.read_limits.__post_init__();self.graph_input.__post_init__()
        for name in ('max_graph_input_bytes','max_output_bytes'):old._positive(getattr(self,name))
        need(type(self.cpu_threads) is int and 1<=self.cpu_threads<=8,'explicit bounded CPU thread profile')
        decode(self.context_limits_json);decode(self.checkpoint_limits_json)
        c,b=self.research.native_config,self.research.budget
        need(c.source_root==c.project_root/'artifacts/akt/dependencies/upstream','main source root must be exact same-root upstream')
        need(old._path(c.project_root,'artifacts/akt/dependencies/upstream')==c.source_root,'physical root-bound upstream path')
        need(c.device==('cpu' if self.cuda_profile is None else 'cuda')
             and self.research.expected_protocol_sha256==PROTOCOL21,'frozen Grade10 device/profile/protocol required')
        if type(self.git_profile) is MainLinuxGitProfile:
            need(self.git_profile.mode=='linux-'+c.device+'-lf-v1','Linux Git profile/device mismatch')
        need(self.stage.config_sha256==old.native_auth.config_hash(c),'stage/native config binding')
        need(self.read_limits.max_total_bytes<=b.max_input_bytes and self.read_limits.max_wall_seconds<=b.max_wall_seconds
             and self.read_limits.max_events_per_learner<=b.max_events_per_learner
             and self.read_limits.max_total_events<=b.train_targets+b.selection_targets+b.calibration_targets
             and self.read_limits.max_trajectories_per_role<=b.train_learners,'read limits exceed declared budget')
        if self.stage.candidate_id=='A0':
            need(self.graph_input.topology_file is None and self.graph_input.method24_reference_json is None,'independent graph-free A0 needs no graph/Method24 artifact')
        else:need(self.graph_input.topology_file is not None,'graph variant requires actual pinned topology file')
        requires_scores=self.stage.candidate_variant in ('A2','A3') or self.stage.estimator_graph=='learned'
        need((self.graph_input.method24_reference_json is not None)==requires_scores,'actual Method24 evidence required exactly for confidence/learned topology')

    @property
    def identity(self):return identity_hash(self.metadata())

    def metadata(self):
        value=asdict(self)
        if self.cuda_profile is None:
            value.pop('cuda_profile')
        return canonical(value)


def _resource(spec,started,training_seconds=0.):
    from .resources import memory_snapshot
    b=spec.research.budget;elapsed=max(time.perf_counter()-started[0],time.time()-started[1])
    need(type(training_seconds) in (int,float) and math.isfinite(training_seconds) and 0<=training_seconds<=b.max_training_seconds,
         'cumulative selected training time cap')
    need(math.isfinite(elapsed) and 0<=elapsed<=b.max_wall_seconds,'cumulative selected wall cap')
    memory=memory_snapshot()
    if max(memory['process_rss_bytes'],memory.get('process_peak_rss_bytes') or 0)>b.max_rss_bytes or memory['system_available_ram_bytes']<b.min_available_ram_bytes:
        raise MemoryError('main selected-only RAM cap/floor')
    return elapsed


def _metadata(spec,evidence):
    need(type(spec) is MainSelectedExecutionSpec and type(evidence) is old.ResearchRuntimeEvidence,'exact main spec/runtime types required')
    spec.__post_init__();r=spec.research;root=r.native_config.project_root
    for name,pin in DOCS:need(old._hash_file(old._path(root,name),cap=r.budget.max_input_bytes)[0]==pin,'actual adopted document/allocation bytes')
    if spec.cuda_profile is not None:
        need(old._hash_file(old._path(root,CUDA_RECIPE_PATH),cap=r.budget.max_input_bytes)[0]==CUDA_RECIPE_SHA256,
             'actual adopted CUDA recipe28 bytes required')
    native=_main_native_evidence(spec,evidence);corpus=old._corpus(r,native)
    sources=native['build_hashes']
    need(spec.stage.sources_sha256==identity_hash(sources) and spec.stage.runtime_sha256==evidence.runtime_report_sha256,
         'stage current source/runtime identity')
    context=spec.stage.context
    need(context.domain_sha256==corpus['domain_sha256'] and context.bank_sha256==corpus['files_sha256']['bank.json']
         and context.split_sha256==corpus['research_plan_sha256'],'actual domain/bank bytes/split identity')
    result=dict(schema_version=1,scope=SCOPE,spec_sha256=spec.identity,stage_spec_sha256=spec.stage.identity,
        config_sha256=old.native_auth.config_hash(r.native_config),native_evidence=native,corpus=corpus,
        input_domain='grade10_simulator',requested_phases=PHASES,graph_input=asdict(spec.graph_input),
        context_limits=decode(spec.context_limits_json),checkpoint_limits=decode(spec.checkpoint_limits_json),
        max_graph_input_bytes=spec.max_graph_input_bytes,max_output_bytes=spec.max_output_bytes,
        cpu_threads=spec.cpu_threads,git_profile=asdict(spec.git_profile),
        matrix_candidate_count=9,external_freeze_authority=False,refit_allowed=False,calibration_allowed=False)
    if spec.cuda_profile is not None:
        result.update(schema_version=2,cuda_execution_profile=asdict(spec.cuda_profile),cuda_recipe_sha256=CUDA_RECIPE_SHA256)
    return canonical(result)


def _auth(spec,evidence,path,pin):
    root=spec.research.native_config.project_root;old._sha(pin)
    authpath=old._path(root,path)
    need(authpath.is_relative_to(root/'experiments/akt/authorizations') or authpath.is_relative_to(root/'artifacts/akt'),'main authorization path')
    value,digest,_=old._read_json(authpath,spec.research.budget.max_input_bytes)
    fields={'schema_version','scope','decision','run_id','config_sha256','execution_spec_sha256','stage_spec_sha256',
            'identity','caps','requested_phases','approval_reference'}
    need(digest==pin and set(value)==fields and type(value['schema_version']) is int and value['schema_version']==1
         and value['scope']==SCOPE and value['decision']=='AUTHORIZE_BOUNDED_MAIN_SELECTED_ONLY','actual closed main authorization required; old pilot is not main permission')
    c=spec.research.native_config
    need(c.execution_enabled is True and value['run_id']==c.run_id and value['config_sha256']==old.native_auth.config_hash(c)
         and value['execution_spec_sha256']==spec.identity and value['stage_spec_sha256']==spec.stage.identity
         and value['requested_phases']==list(PHASES),'actual main authorization stage/config/phases')
    old._text(value['approval_reference']);need(len(value['approval_reference'])<=256,'bounded approval reference')
    caps=dict(research_budget=asdict(spec.research.budget),read_limits=asdict(spec.read_limits),
              context_limits=decode(spec.context_limits_json),checkpoint_limits=decode(spec.checkpoint_limits_json),
              max_graph_input_bytes=spec.max_graph_input_bytes,max_output_bytes=spec.max_output_bytes)
    caps['cpu_threads']=spec.cpu_threads
    caps['git_profile']=asdict(spec.git_profile)
    if spec.cuda_profile is not None:
        caps['cuda_execution_profile']=asdict(spec.cuda_profile)
    need(old._same_json(value['caps'],caps),'actual main caps differ')
    identity=_metadata(spec,evidence)
    need(old._same_json(value['identity'],identity),'actual source/runtime/Gate/data/graph spec drift')
    return value,identity


def _actual_condition(spec,corpus,metadata):
    from . import research_graph_condition as conditions
    from ..shared_kt import PrerequisiteGraph
    r=spec.research;g=spec.graph_input;root=r.native_config.project_root
    roles={name:corpus.role_data(name) for name in ('train','selection','calibration')}
    train=roles['train'];context=spec.stage.context
    need(train.audit['audit']['shard_sha256']==context.train_role_sha256
         and roles['selection'].audit['audit']['shard_sha256']==context.selection_role_sha256,'actual audited role SHA, not raw JSONL SHA')
    binding=conditions.GraphTrain80Binding(r.corpus_id,r.expected_corpus_sha256,corpus.done_sha256,corpus.plan.identity,
        train.provenance.identity,metadata['corpus']['files_sha256']['train.jsonl'],identity_hash(corpus.bank.identity),
        *(roles[name].audit['audit']['shard_sha256'] for name in ('train','selection','calibration')))
    files={};nodes=edges=();topology_source=None;loaded=expected=None
    mode={'disabled':'none','expert':'expert_declared','learned':'method24_learned'}[spec.stage.estimator_graph]
    if g.topology_file is not None:
        path=old._path(root,g.topology_file)
        need(path.is_relative_to(root/'artifacts/akt'),'pinned topology input must be under AKT artifacts')
        topology,digest,_=old._read_json(path,spec.max_graph_input_bytes)
        need(digest==g.topology_file_sha256,'actual topology bytes SHA')
        need(type(topology.get('nodes')) is list and type(topology.get('edges')) is list
             and all(type(n) is str for n in topology['nodes'])
             and all(type(e) is list and len(e)==2 and all(type(n) is str for n in e) for e in topology['edges']),
             'actual topology nodes/edges schema')
        graph=PrerequisiteGraph.from_edges(topology['nodes'],topology['edges']);nodes,edges=graph.nodes,graph.edges
        files[g.topology_file]=digest;topology_source=digest
    if g.method24_reference_json is not None:
        from ..edge_confidence_artifact import Method24ArtifactRef,Method24TrainingBinding,Method24ReadLimits,load_method24_scores
        ref=Method24ArtifactRef(**decode(g.method24_reference_json))
        values=decode(g.method24_training_json)
        for field_name in ('public_files_sha256','source_files_sha256','runtime_files_sha256'):
            values[field_name]=tuple(tuple(row) for row in values[field_name])
        expected=Method24TrainingBinding(**values);limits=Method24ReadLimits(**decode(g.method24_limits_json))
        need(limits.max_read_bytes<=spec.max_graph_input_bytes and limits.max_wall_seconds<=r.budget.max_wall_seconds,'Method24 loader exceeds authorized input/time caps')
        loaded=load_method24_scores(ref,expected_training=expected,bank=corpus.bank,declared_graph=graph,
            graph_binding='method24_learned' if mode=='method24_learned' else 'declared',limits=limits)
        need(loaded.identity==g.expected_scores_sha256,'actual Method24 semantic identity')
        files.update(dict(loaded.artifacts_sha256))
        if mode=='method24_learned':topology_source=loaded.exported_graph_sha256
    condition=conditions.prepare_research_graph_condition(variant=spec.stage.candidate_variant,graph_mode=mode,
        bank=corpus.bank,nodes=nodes,edges=edges,train80=binding,expected_sources=conditions.source_inventory(),
        topology_source_sha256=topology_source,loaded_scores=loaded,expected_method24_training=expected,
        expected_scores_sha256=None if loaded is None else loaded.identity)
    need(condition.identity==g.implementation_condition_sha256,'actual implementation condition binding')
    need(spec.stage.graph_condition_sha256==(None if spec.stage.candidate_id=='A0' else condition.identity),
         'A0 internal empty condition is separate from estimator condition; graph candidate must bind exact condition')
    return condition,tuple(sorted(files.items()))


@dataclass(frozen=True,init=False)
class MainSelectedExecution:
    spec: MainSelectedExecutionSpec
    evidence: old.ResearchRuntimeEvidence
    authorization_file: str
    authorization_sha256: str
    identity_json: str
    started: tuple[float,float]
    _corpus: object=field(repr=False,compare=False)
    _condition: object=field(repr=False,compare=False)
    _graph_files: tuple=field(repr=False)

    def __init__(self,*args,**kwargs):raise TypeError('use require_main_selected_authorization with actual closed files')

    def revalidate(self,training_seconds=0.):
        elapsed=_resource(self.spec,self.started,training_seconds)
        _,identity=_auth(self.spec,self.evidence,self.authorization_file,self.authorization_sha256)
        need(old._same_json(identity,json.loads(self.identity_json)),'main bound identity changed')
        self._corpus.assert_integrity();self._condition.assert_integrity()
        root=self.spec.research.native_config.project_root
        for name,pin in self._graph_files:
            need(old._hash_file(old._path(root,name),cap=self.spec.max_graph_input_bytes)[0]==pin,'actual graph input drift')
        _resource(self.spec,self.started,training_seconds)
        return identity


def require_main_selected_authorization(spec,evidence,*,authorization_file,expected_authorization_sha256):
    need(type(spec) is MainSelectedExecutionSpec and type(evidence) is old.ResearchRuntimeEvidence,'concrete main execution guard types required')
    spec.__post_init__();started=(time.perf_counter(),time.time());_resource(spec,started)
    _,identity=_auth(spec,evidence,authorization_file,expected_authorization_sha256)
    output=spec.research.native_config.output_dir
    need(not output.exists(),'fresh main output only, no retry/resume/pilot promotion')
    _resource(spec,started)
    corpus=read_public_research_corpus(spec.research.corpus_id,expected_corpus_sha256=spec.research.expected_corpus_sha256,
        expected_done_sha256=identity['corpus']['done_sha256'],limits=spec.read_limits)
    corpus.assert_integrity()
    need(dict((n,h) for n,h,_ in corpus.files_sha256)==identity['corpus']['files_sha256']
         and corpus.plan.identity==spec.stage.context.split_sha256,'actual public reader/input binding')
    from ..response_calibration import reference_bank_v1
    reference_bank_v1(corpus.bank)
    b=spec.research.budget
    for role in ('train','selection','calibration'):
        value=corpus.role_data(role)
        need(len(value.trajectories)==getattr(b,role+'_learners') and value.audit['audit']['targets']==getattr(b,role+'_targets')
             and value.reference_complete,'actual frozen role counts/reference coverage')
    _resource(spec,started)
    condition,files=_actual_condition(spec,corpus,identity)
    result=object.__new__(MainSelectedExecution)
    for n,v in dict(spec=spec,evidence=evidence,authorization_file=authorization_file,authorization_sha256=expected_authorization_sha256,
                    identity_json=json.dumps(identity,sort_keys=True,separators=(',',':'),allow_nan=False),started=started,
                    _corpus=corpus,_condition=condition,_graph_files=files).items():object.__setattr__(result,n,v)
    result.revalidate()
    return result
