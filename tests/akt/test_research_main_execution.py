"""Main execution metadata/file mocks only; never actual runtime/Gate/fit proof."""
from dataclasses import asdict,replace
import json
from pathlib import Path,PurePosixPath
from types import SimpleNamespace
import pytest

from knowledge_tracing.akt import config as cfg,research_execution as old,research_main_execution as main
from knowledge_tracing.akt.research_main_stage import MainSelectedStageSpec,PROTOCOL22,ACCOUNTING23
from knowledge_tracing.research_admission import MainSelectionContext,PROTOCOL21,RECIPE26,ALLOCATION

H='a'*64


def cuda_case(tmp_path,monkeypatch):
    """Manufactured typed spec only; never an actual CUDA permission."""
    case=make_case(tmp_path,monkeypatch)
    profile=cfg.ResearchCUDAExecutionProfile(128*1024**2)
    old_spec=case.spec.research;config=replace(old_spec.native_config,device='cuda')
    research=old.SimulatorResearchSpec(config,old_spec.corpus_id,old_spec.expected_corpus_sha256,
        old_spec.expected_protocol_sha256,old_spec.budget,cuda_profile=profile)
    stage=replace(case.spec.stage,config_sha256=old.native_auth.config_hash(config))
    case.spec=replace(case.spec,research=research,stage=stage,cuda_profile=profile)
    return case


def test_cpu_main_spec_wire_omits_optional_profile_and_matches_legacy_hash(tmp_path,monkeypatch):
    case=make_case(tmp_path,monkeypatch)
    legacy=asdict(case.spec);legacy.pop('cuda_profile')
    assert set(legacy)=={'research','stage','read_limits','graph_input','context_limits_json',
        'checkpoint_limits_json','max_graph_input_bytes','max_output_bytes','cpu_threads','git_profile'}
    assert case.spec.metadata()==main.canonical(legacy)
    assert case.spec.identity==main.identity_hash(main.canonical(legacy))
    assert 'cuda_profile' not in case.spec.metadata()['research']


def test_cuda_main_spec_retains_profile_but_creates_no_execution(tmp_path,monkeypatch):
    case=cuda_case(tmp_path,monkeypatch)
    assert case.spec.metadata()['cuda_profile']==asdict(case.spec.cuda_profile)
    assert 'cuda_profile' not in case.spec.metadata()['research']
    assert case.spec.research.native_config.device=='cuda'
    assert not isinstance(case.spec,main.MainSelectedExecution)
    assert replace(case.spec,cuda_profile=replace(case.spec.cuda_profile,max_vram_bytes=256*1024**2)).identity!=case.spec.identity
    with pytest.raises(ValueError):replace(case.spec,cuda_profile=None)
    with pytest.raises(ValueError):replace(case.spec,cuda_profile=True)
    cpu=make_case(tmp_path,monkeypatch)
    with pytest.raises(ValueError):replace(cpu.spec,cuda_profile=case.spec.cuda_profile)


def test_cuda_recipe_is_checked_before_native_or_corpus_work(tmp_path,monkeypatch):
    case=cuda_case(tmp_path,monkeypatch)
    monkeypatch.setattr(main,'DOCS',())
    monkeypatch.setattr(old,'_hash_file',lambda *a,**k:('f'*64,0))
    monkeypatch.setattr(main,'_main_native_evidence',lambda *a:pytest.fail('bad recipe must stop before runtime'))
    monkeypatch.setattr(old,'_corpus',lambda *a:pytest.fail('bad recipe must stop before corpus'))
    with pytest.raises(ValueError,match='recipe28'):main._metadata(case.spec,case.evidence)


def test_cuda_metadata_binds_recipe_profile_and_current_sources_without_grant(tmp_path,monkeypatch):
    case=cuda_case(tmp_path,monkeypatch);builds={'manufactured-source':H}
    case.spec=replace(case.spec,stage=replace(case.spec.stage,sources_sha256=main.identity_hash(builds)))
    monkeypatch.setattr(main,'DOCS',())
    monkeypatch.setattr(old,'_hash_file',lambda *a,**k:(main.CUDA_RECIPE_SHA256,1))
    monkeypatch.setattr(main,'_main_native_evidence',lambda *a:dict(build_hashes=builds))
    monkeypatch.setattr(old,'_corpus',lambda *a:dict(domain_sha256=case.spec.stage.context.domain_sha256,
        files_sha256={'bank.json':case.spec.stage.context.bank_sha256},
        research_plan_sha256=case.spec.stage.context.split_sha256))
    metadata=main._metadata(case.spec,case.evidence)
    assert metadata['schema_version']==2 and metadata['cuda_execution_profile']==asdict(case.spec.cuda_profile)
    assert metadata['cuda_recipe_sha256']==main.CUDA_RECIPE_SHA256
    assert metadata['external_freeze_authority'] is metadata['refit_allowed'] is metadata['calibration_allowed'] is False
    assert not isinstance(metadata,main.MainSelectedExecution)


def test_cuda_auth_requires_exact_backend_caps_not_only_a_spec_hash(tmp_path,monkeypatch):
    case=cuda_case(tmp_path,monkeypatch);identity={'manufactured_metadata_not_permission':True}
    value=auth_value(case,identity)
    value['caps']['cuda_execution_profile']=asdict(case.spec.cuda_profile)
    monkeypatch.setattr(main,'_metadata',lambda *a:identity)
    relative,pin=put_auth(case,value)
    got,_=main._auth(case.spec,case.evidence,relative,pin)
    assert got['caps']['cuda_execution_profile']==asdict(case.spec.cuda_profile)
    assert not isinstance(got,main.MainSelectedExecution)
    value['caps']['cuda_execution_profile']['foreach']=True
    relative,pin=put_auth(case,value)
    with pytest.raises(ValueError,match='caps'):main._auth(case.spec,case.evidence,relative,pin)
    value['caps'].pop('cuda_execution_profile')
    relative,pin=put_auth(case,value)
    with pytest.raises(ValueError,match='caps'):main._auth(case.spec,case.evidence,relative,pin)


def test_linux_cuda_source_proof_cannot_reuse_cpu_kind_mode_or_runtime(monkeypatch):
    case=linux_metadata(monkeypatch)
    case.config.device='cuda'
    profile=replace(case.profile,mode='linux-cuda-lf-v1')
    proof=case.proof|{'kind':'MAIN_LINUX_CUDA_SOURCE_PROVENANCE_V1','runtime_report_sha256':'d'*64}
    evidence=SimpleNamespace(runtime_report_sha256='d'*64,lock_sha256=case.evidence.lock_sha256)
    main._validate_linux_source_proof(profile,case.config,evidence,proof)
    with pytest.raises(ValueError,match='profile'):
        main._validate_linux_source_proof(case.profile,case.config,evidence,proof)
    with pytest.raises(ValueError,match='proof'):
        main._validate_linux_source_proof(profile,case.config,evidence,proof|{'kind':case.proof['kind']})
    with pytest.raises(ValueError,match='runtime'):
        main._validate_linux_source_proof(profile,case.config,evidence,
            proof|{'runtime_report_sha256':case.proof['runtime_report_sha256']})


def make_case(tmp_path,monkeypatch):
    root=tmp_path/'fixture-main';root.mkdir(exist_ok=True)
    monkeypatch.setattr(cfg,'PROJECT_ROOT',root);monkeypatch.setattr(old,'PROJECT_ROOT',root)
    b=old.ResearchResourceBudget(8,1,1,24,3,3,3,8,192,10.,20.,1024**3,1024**3,8*1024**2,1024**2,4*1024**2)
    c=cfg.AKTConfig(project_root=root,output_dir=root/'experiments/akt/results/unit-main',run_id='unit-main',
        phase='simulator-research',execution_enabled=True,source_root=root/'artifacts/akt/dependencies/upstream',
        max_train_users=9,max_val_users=1,max_targets_per_side=27,max_total_targets=30,max_steps=8,
        max_seconds=10.,max_wall_seconds=20.,max_rss_bytes=1024**3,min_available_ram_bytes=1024**3)
    research=old.SimulatorResearchSpec(c,'manufactured',H,PROTOCOL21,b)
    context=MainSelectionContext('grade10_simulator',PROTOCOL21,RECIPE26,ALLOCATION,H,H,H,'b'*64,'c'*64)
    stage=MainSelectedStageSpec('A0',context,PROTOCOL22,ACCOUNTING23,old.native_auth.config_hash(c),H,H,None,None)
    read=main.CorpusReadLimits(1024**2,4*1024**2,65536,8,3,30,10.)
    graph=main.MainGraphInput(None,None,None,None,None,None,H)
    context_limits=json.dumps(dict(max_total_events=30,max_events_per_learner=3,max_targets=30,max_windows=30,
        max_window_tokens=200,max_parent_records=100,max_observed_rows=1000,max_cache_bytes=1024**2,max_seconds=5.))
    checkpoint_limits=json.dumps(dict(max_checkpoint_bytes=8*1024**2,max_metadata_bytes=1024**2,max_tensor_bytes=8*1024**2))
    profile=main.MainGitProfile('windows-native03-v1','C:/Program Files/Git/cmd/git.exe',main.GIT_EXE_SHA,
        c.source_root.as_posix(),main.EOL_PROOF,main.EOL_SHA,main.WINDOWS_UPSTREAM_FILES)
    spec=main.MainSelectedExecutionSpec(research,stage,read,graph,context_limits,checkpoint_limits,4*1024**2,64*1024**2,2,profile)
    evidence=old.ResearchRuntimeEvidence('artifacts/akt/preflight/runtime.json',H,'requirements-akt.lock.txt',H,
        'artifacts/akt/preflight/gate2-current.json',H,H,H)
    return SimpleNamespace(root=root,spec=spec,evidence=evidence)


def auth_value(case,identity):
    s=case.spec
    return dict(schema_version=1,scope=main.SCOPE,decision='AUTHORIZE_BOUNDED_MAIN_SELECTED_ONLY',run_id=s.research.native_config.run_id,
        config_sha256=old.native_auth.config_hash(s.research.native_config),execution_spec_sha256=s.identity,
        stage_spec_sha256=s.stage.identity,identity=identity,
        caps=dict(research_budget=asdict(s.research.budget),read_limits=asdict(s.read_limits),
            context_limits=main.decode(s.context_limits_json),checkpoint_limits=main.decode(s.checkpoint_limits_json),
            max_graph_input_bytes=s.max_graph_input_bytes,max_output_bytes=s.max_output_bytes,cpu_threads=s.cpu_threads,
            git_profile=asdict(s.git_profile)),
        requested_phases=list(main.PHASES),approval_reference='MANUFACTURED_UNIT_METADATA_NOT_EXECUTION')


def put_auth(case,value):
    relative='experiments/akt/authorizations/manufactured-main.json'
    path=case.root/relative;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value),encoding='utf-8')
    return relative,main.old._hash_file(path,cap=65536)[0]


def test_metadata_spec_keeps_frozen_config_and_explicit_caps(tmp_path,monkeypatch):
    c=make_case(tmp_path,monkeypatch)
    assert c.spec.research.native_config.max_epochs==20 and c.spec.research.native_config.dropout==.05
    assert main.PHASES==('select_train80','raw_selection10')
    assert c.spec.cpu_threads==2 and len(c.spec.identity)==64


def test_unsupported_environment_family_rejected_before_runtime_data(tmp_path,monkeypatch):
    c=make_case(tmp_path,monkeypatch)
    monkeypatch.setattr(main,'_main_native_evidence',lambda *a:pytest.fail('no runtime/data work for unsupported scope'))
    with pytest.raises(ValueError,match='Junyi'):
        replace(c.spec,stage=replace(c.spec.stage,context=replace(c.spec.stage.context,environment_id='junyi_development_outer_fold4')))
    for candidate in ('SAKT','GKT'):
        stage=replace(c.spec.stage,candidate_id=candidate,graph_condition_sha256=H if candidate=='GKT' else None,
            graph_train_role_sha256=c.spec.stage.context.train_role_sha256 if candidate=='GKT' else None)
        with pytest.raises(ValueError,match='SAKT/GKT'):replace(c.spec,stage=stage)


def test_wrong_pilot_or_refit_authorization_dies_before_metadata(tmp_path,monkeypatch):
    c=make_case(tmp_path,monkeypatch)
    monkeypatch.setattr(main,'_metadata',lambda *a:pytest.fail('bad authority must stop before runtime/data'))
    for changes in ({'scope':old.SCOPE},{'requested_phases':['selection_fit','refit90']},{'decision':'GatePASS'}):
        value=auth_value(c,{})|changes;relative,pin=put_auth(c,value)
        with pytest.raises(ValueError):main._auth(c.spec,c.evidence,relative,pin)


def test_actual_authorization_byte_pin_and_closed_schema(tmp_path,monkeypatch):
    c=make_case(tmp_path,monkeypatch);value=auth_value(c,{})
    monkeypatch.setattr(main,'_metadata',lambda *a:pytest.fail('invalid bytes/schema cannot reach metadata'))
    relative,pin=put_auth(c,value)
    with pytest.raises(ValueError):main._auth(c.spec,c.evidence,relative,'f'*64)
    relative,pin=put_auth(c,value|{'verified':True})
    with pytest.raises(ValueError):main._auth(c.spec,c.evidence,relative,pin)


def test_auth_consistency_only_with_explicit_metadata_mock_no_guard_grant(tmp_path,monkeypatch):
    c=make_case(tmp_path,monkeypatch);identity={'MANUFACTURED_METADATA_NOT_RUNTIME_OR_GATE':True}
    value=auth_value(c,identity);relative,pin=put_auth(c,value)
    monkeypatch.setattr(main,'_metadata',lambda *a:identity)
    got,matched=main._auth(c.spec,c.evidence,relative,pin)
    # Auth is the actual JSON wire object: nested upstream tuples become lists.
    # Keep every field/cap strict instead of comparing decoded bytes to asdict.
    wire=json.loads((c.root/relative).read_bytes())
    assert got==wire==main.canonical(value)
    assert got['caps']==wire['caps']==main.canonical(value['caps'])
    assert matched==wire['identity']==identity
    assert not isinstance(got,main.MainSelectedExecution)  # Never pretend these mocks authorize model execution.
    value['caps']['max_output_bytes']+=1;relative,pin=put_auth(c,value)
    with pytest.raises(ValueError,match='caps'):main._auth(c.spec,c.evidence,relative,pin)


def test_missing_actual_auth_stops_before_public_reader(tmp_path,monkeypatch):
    c=make_case(tmp_path,monkeypatch)
    monkeypatch.setattr(main,'_resource',lambda *a:None)  # Resource operator not under test, no runtime certificate.
    monkeypatch.setattr(main,'read_public_research_corpus',lambda *a,**k:pytest.fail('no approved file; no corpus/model'))
    with pytest.raises((ValueError,FileNotFoundError)):
        main.require_main_selected_authorization(c.spec,c.evidence,authorization_file='artifacts/akt/missing.json',expected_authorization_sha256=H)


def test_execution_cannot_be_constructed_from_noauth_boolean():
    with pytest.raises(TypeError):main.MainSelectedExecution(True)
    assert main.SCOPE!=old.SCOPE and 'refit90' not in main.PHASES


def test_graph_and_parameter_requests_reject_partial_nonfinite_inputs(tmp_path,monkeypatch):
    c=make_case(tmp_path,monkeypatch)
    with pytest.raises(ValueError):replace(c.spec.graph_input,method24_reference_json='{}')
    with pytest.raises(ValueError):replace(c.spec.graph_input,topology_file_sha256=H)
    with pytest.raises(ValueError):main.decode('{"same":1,"same":2}')
    with pytest.raises(ValueError):main.decode('{"n":1e999}')
    with pytest.raises(ValueError):replace(c.spec,cpu_threads=True)


def test_reviewed_windows_profile_accepts_metadata_without_runtime_grant(tmp_path,monkeypatch):
    c=make_case(tmp_path,monkeypatch);profile=c.spec.git_profile;root=c.spec.research.native_config.source_root
    env=main._git_environment(profile,root,'win32')
    assert main._validate_git_environment(profile,root,'win32',env|{'PATH':'irrelevant-to-this-metadata-test'})==env
    assert env['GIT_CONFIG_VALUE_1']==root.as_posix() and env['GIT_CONFIG_VALUE_2']=='true'
    assert not isinstance(env,main.MainSelectedExecution)  # No actual Git/runtime/Gate call or PASS claim.
    with pytest.raises(ValueError):main._git_environment(profile,root,'linux')
    with pytest.raises(ValueError):replace(c.spec,git_profile=replace(profile,source_root=root.as_posix()+'/other'))


def test_git_extra_configuration_transport_or_wrong_safe_root_rejects_before_native(tmp_path,monkeypatch):
    c=make_case(tmp_path,monkeypatch);profile=c.spec.git_profile;root=c.spec.research.native_config.source_root
    env=main._git_environment(profile,root,'win32')
    monkeypatch.setattr(main.old.native_auth,'preflight',lambda *a,**k:pytest.fail('bad env cannot call native preflight'))
    for changes in ({'GIT_CONFIG_COUNT':'4'},{'GIT_CONFIG_KEY_3':'credential.helper'},{'GIT_SSH_COMMAND':'untrusted'},
                    {'GH_TOKEN':'untrusted'},{'GIT_CONFIG_VALUE_1':root.parent.as_posix()},{'GIT_ALLOW_PROTOCOL':'https'}):
        with pytest.raises(ValueError):main._validate_git_environment(profile,root,'win32',env|changes)


def linux_metadata(monkeypatch):
    """Declared POSIX metadata only, never a host/runtime/Gate execution proof."""
    root=PurePosixPath('/fixture/project')
    config=SimpleNamespace(project_root=root,source_root=root/'artifacts/akt/dependencies/upstream',source_commit=cfg.SOURCE_COMMIT,device='cpu')
    profile=main.MainLinuxGitProfile('linux-cpu-lf-v1','/fixture/git',H,config.source_root.as_posix(),
        'artifacts/akt/manufactured-source-proof.json',H,main.LINUX_UPSTREAM_FILES)
    process=SimpleNamespace(platform='linux',executable=str(root/'.venv/bin/python'),prefix=str(root/'.venv'))
    monkeypatch.setattr(main,'sys',process)
    evidence=SimpleNamespace(runtime_report_sha256='b'*64,lock_sha256='c'*64)
    source=dict(commit=cfg.SOURCE_COMMIT,tree=main.UPSTREAM_TREE,remote='https://github.com/arghosh/AKT.git',
                files=dict(main.LINUX_UPSTREAM_FILES))
    proof=dict(schema_version=1,kind='MAIN_LINUX_CPU_SOURCE_PROVENANCE_V1',platform_id='linux',
        project_root=str(root),python=process.executable,python_prefix=process.prefix,source_root=str(config.source_root),
        git=dict(executable=profile.executable,executable_sha256=profile.executable_sha256),
        git_environment=main._git_environment(profile,config.source_root,'linux'),source=source,
        source_before=dict(source['files']),source_after=dict(source['files']),
        runtime_report_sha256=evidence.runtime_report_sha256,lock_sha256=evidence.lock_sha256)
    return SimpleNamespace(config=config,profile=profile,evidence=evidence,proof=proof)


def test_linux_profile_and_source_metadata_consistency_is_not_execution(monkeypatch):
    c=linux_metadata(monkeypatch)
    env=main._git_environment(c.profile,c.config.source_root,'linux')
    assert main._validate_git_environment(c.profile,c.config.source_root,'linux',env|{'PATH':'fixture'})==env
    assert env['GIT_CONFIG_GLOBAL']=='/dev/null' and env['GIT_CONFIG_VALUE_2']=='false'
    assert main._validate_linux_source_proof(c.profile,c.config,c.evidence,c.proof) is None
    assert not isinstance(c.profile,main.MainSelectedExecution)


@pytest.mark.parametrize('changes',[
    {'mode':'windows-native03-v1'},{'executable':'relative/git'},{'executable':'/fixture/../git'},
    {'executable':'//fixture/git'},{'executable':'/fixture/./git'},{'executable_sha256':'not-sha'},
    {'proof_file':'artifacts/akt/../proof.json'},{'proof_file':'/tmp/proof.json'},
    {'proof_file':'experiments/proof.json'},{'upstream_files_sha256':main.WINDOWS_UPSTREAM_FILES}])
def test_linux_profile_rejects_unsafe_or_windows_metadata(monkeypatch,changes):
    c=linux_metadata(monkeypatch)
    with pytest.raises(ValueError):replace(c.profile,**changes)


@pytest.mark.parametrize('changes',[
    {'GIT_CONFIG_GLOBAL':'nul'},{'GIT_CONFIG_VALUE_2':'true'},
    {'GIT_CONFIG_VALUE_1':'/different/source'},{'GIT_SSH_COMMAND':'fixture'},
    {'GH_TOKEN':'fixture'},{'GIT_ALLOW_PROTOCOL':'https'}])
def test_linux_environment_remains_closed(monkeypatch,changes):
    c=linux_metadata(monkeypatch);env=main._git_environment(c.profile,c.config.source_root,'linux')
    with pytest.raises(ValueError):main._validate_git_environment(c.profile,c.config.source_root,'linux',env|changes)
    with pytest.raises(ValueError):main._git_environment(c.profile,c.config.source_root,'win32')


@pytest.mark.parametrize('field,value',[
    ('schema_version',True),('platform_id','win32'),('project_root','/other'),('python','/usr/bin/python'),
    ('python_prefix','/usr'),('runtime_report_sha256','f'*64),('lock_sha256','f'*64),
    ('source_before',dict(main.WINDOWS_UPSTREAM_FILES)),('source_after',{}),('source',{}),
    ('git',{'executable':'/other/git','executable_sha256':H}),('git_environment',{})])
def test_linux_source_proof_rejects_stale_or_cross_host_metadata(monkeypatch,field,value):
    c=linux_metadata(monkeypatch);c.proof[field]=value
    with pytest.raises(ValueError):main._validate_linux_source_proof(c.profile,c.config,c.evidence,c.proof)


def test_linux_source_proof_requires_exact_schema(monkeypatch):
    c=linux_metadata(monkeypatch)
    for proof in (c.proof|{'verified':True},{k:v for k,v in c.proof.items() if k!='source_after'}):
        with pytest.raises(ValueError):main._validate_linux_source_proof(c.profile,c.config,c.evidence,proof)


def linux_gate_metadata(tmp_path,monkeypatch):
    """TmpFS reader-bound report fixture, not an actual Linux software Gate."""
    root=tmp_path/'g';root.mkdir()
    writer=root/main.GATE_WRITER;writer.parent.mkdir(parents=True);writer.write_bytes(b'MANUFACTURED WRITER\n')
    writer_sha=main.old._hash_file(writer,cap=65536)[0]
    process=SimpleNamespace(platform='linux',executable=str(root/'.venv/bin/python'),prefix=str(root/'.venv'))
    monkeypatch.setattr(main,'sys',process)
    profile=dict(schema_version=1,platform_id='linux',project_root=str(root),python=process.executable,
                 python_prefix=process.prefix,writer_sha256=writer_sha)
    builds={main.GATE_WRITER:writer_sha}
    report=root/'artifacts/akt/preflight/gate2-manufactured.json';report.parent.mkdir(parents=True)
    value=dict(build_hashes=builds,execution_profile=profile)
    runtime=dict(runtime=dict(platform_id='linux',project_root=str(root),python=process.executable,python_prefix=process.prefix))
    return SimpleNamespace(root=root,report=report,value=value,builds=builds,runtime=runtime)


def check_linux_gate_fixture(c,*,digest_override=None):
    c.report.write_text(json.dumps(c.value),encoding='utf-8')
    digest=main.old._hash_file(c.report,cap=65536)[0]
    evidence=SimpleNamespace(gate_report_sha256=digest)
    gate=dict(evidence_path=str(c.report),report_sha256=digest_override or digest)
    return main._linux_gate_profile(SimpleNamespace(project_root=c.root),evidence,c.runtime,gate,c.builds,65536)


def test_linux_gate_profile_checks_bound_report_without_grant(tmp_path,monkeypatch):
    c=linux_gate_metadata(tmp_path,monkeypatch)
    assert check_linux_gate_fixture(c) is None
    assert not isinstance(c.value,main.MainSelectedExecution)


@pytest.mark.parametrize('field,value',[
    ('schema_version',True),('platform_id','win32'),('project_root','/other'),('python','/other/python'),
    ('python_prefix','/other/venv'),('writer_sha256','f'*64),('extra','not-closed')])
def test_linux_gate_profile_rejects_stale_or_foreign_writer_process(tmp_path,monkeypatch,field,value):
    c=linux_gate_metadata(tmp_path,monkeypatch);c.value['execution_profile'][field]=value
    with pytest.raises(ValueError):check_linux_gate_fixture(c)


def test_linux_gate_rejects_legacy_windows_report_without_profile(tmp_path,monkeypatch):
    c=linux_gate_metadata(tmp_path,monkeypatch);c.value.pop('execution_profile')
    with pytest.raises(ValueError,match='execution profile'):check_linux_gate_fixture(c)


def test_linux_gate_rejects_report_reread_drift(tmp_path,monkeypatch):
    c=linux_gate_metadata(tmp_path,monkeypatch)
    with pytest.raises(ValueError,match='changed after public reader'):
        check_linux_gate_fixture(c,digest_override='f'*64)


def test_linux_gate_rejects_build_and_runtime_mismatch(tmp_path,monkeypatch):
    c=linux_gate_metadata(tmp_path,monkeypatch)
    c.runtime['runtime']['platform_id']='win32'
    with pytest.raises(ValueError,match='runtime'):check_linux_gate_fixture(c)
    c.runtime['runtime']['platform_id']='linux'
    c.builds.pop(main.GATE_WRITER)
    with pytest.raises(ValueError,match='current build'):check_linux_gate_fixture(c)
