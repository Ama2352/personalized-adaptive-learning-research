"""Main execution metadata/file mocks only; never actual runtime/Gate/fit proof."""
from dataclasses import asdict,replace
import json
from pathlib import Path
from types import SimpleNamespace
import pytest

from knowledge_tracing.akt import config as cfg,research_execution as old,research_main_execution as main
from knowledge_tracing.akt.research_main_stage import MainSelectedStageSpec,PROTOCOL22,ACCOUNTING23
from knowledge_tracing.research_admission import MainSelectionContext,PROTOCOL21,RECIPE26,ALLOCATION

H='a'*64


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
