"""Driver orchestration only: fake classes/results,0native/NumPy/Pandas/model."""
import builtins
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest

ROOT=Path(__file__).resolve().parents[2]
DRIVER=ROOT/'scripts/research/collect_development_corpus.py'
CONFIG=ROOT/'experiments/akt/configs/simulator-research-corpus01.json'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def case(tmp_path_factory,monkeypatch):
    spec=importlib.util.spec_from_file_location('isolated_development_worker',DRIVER)
    driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
    # Short per-case ordinal avoids Windows MAX_PATH with exact native source filenames.
    root=tmp_path_factory.mktemp('c')/'workspace';root.mkdir()
    config_bytes=CONFIG.read_bytes()
    assert hashlib.sha256(config_bytes).hexdigest()==driver.CONFIG_SHA
    config_path=root/driver.CONFIG;config_path.parent.mkdir(parents=True);config_path.write_bytes(config_bytes)
    config=json.loads(config_bytes)
    sources={}
    for name in (*driver.COLLECTION_SOURCES,*driver.EXTRA_SOURCES):
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(('SYNTHETIC_SOURCE_BINDING_NOT_NATIVE '+name).encode())
        sources[name]=sha(path)
    request_relative='artifacts/akt/local-tests/development-corpus-20261108-01/mock-request.json'
    request=dict(schema_version=1,purpose='first_development_corpus_lifecycle_pilot',approval_reference='MOCK_NOT_EXECUTION_AUTHORITY',
        config_sha256=driver.CONFIG_SHA,plan_sha256=driver.PLAN_SHA,
        collection_sources={p:sources[p] for p in driver.COLLECTION_SOURCES},
        extra_sources={p:sources[p] for p in driver.EXTRA_SOURCES},
        output_relative='artifacts/akt/local-tests/development-corpus-20261108-01/mock-output')
    request_path=root/request_relative;request_path.parent.mkdir(parents=True,exist_ok=True)
    monkeypatch.setattr(driver,'ROOT',root)
    original_sys_path=list(sys.path);monkeypatch.setattr(sys,'path',list(original_sys_path))
    state=SimpleNamespace(imports=[],calls=[],phase='start',ram_failure=None,results={},plan=None,
        missing_reference=False,reader_mismatch=False,drift_after_reader=False,fail_after_result=False,
        successful_result_written=False,memory_checks=[])
    def memory_snapshot():
        stage=('after_result' if state.successful_result_written else 'after_reader' if state.phase=='reader_returned'
               else 'after_heavy' if 'knowledge_tracing.simulator_corpus_reader' in state.imports else 'before_heavy')
        state.memory_checks.append(stage)
        bad=state.ram_failure==stage or (state.fail_after_result and stage=='after_result')
        return dict(process_rss_bytes=64*1024**2,process_peak_rss_bytes=None,
                    system_available_ram_bytes=0 if bad else 4*1024**3)
    class FakePlan:
        def __init__(self,**recipe):
            assert recipe==config['plan_recipe'];state.calls.append(('plan',));state.plan=self
            self.identity=driver.PLAN_SHA;self.protocol_sha256=recipe['protocol_sha256']
            self.split_plan=SimpleNamespace(assignments=self.assignments)
        def assignments(self,role):
            assert role in ('train','selection','calibration'),'final identities/events requested'
            return tuple(SimpleNamespace(learner_id=f'MOCK-{role}-{i:03}') for i in range(config['role_counts'][role]))
        def manifest(self):return dict(scope='MOCK_PLAN_NOT_ACTUAL_SPLIT_ATTESTATION',role_counts=config['role_counts'])
    class RecordArgs:
        def __init__(self,*args,**kwargs):self.args=args;self.kwargs=kwargs
    def collect(plan,*,role,profiles,recipe,limits,expected_sources):
        assert role in ('train','selection','calibration') and plan is state.plan
        assert expected_sources==request['collection_sources']
        count=config['role_counts'][role]
        assert len(profiles)==count and limits.args[0:3]==(count,210,count*210)
        expected={a.learner_id:('PG','PY','PYH')[i%3] for i,a in enumerate(plan.assignments(role))}
        assert profiles==expected
        state.calls.append(('collect',role,deepcopy(profiles)))
        result=SimpleNamespace(manifest=dict(interact_attempts=count*210,interact_returns=count*210,
            audit=dict(reference_complete=not state.missing_reference),scope='MOCK_COUNTS_NO_TEACHER_CALLS'),
            trajectories=tuple(reversed(plan.assignments(role))))
        state.results[role]=result
        return result
    class FakePublication:
        corpus_sha256='d'*64;done_sha256='e'*64
        def payload(self):return dict(scope='MOCK_PUBLICATION_NOT_PUBLISHED',corpus_sha256=self.corpus_sha256,done_sha256=self.done_sha256)
    def publish(plan,results,**kwargs):
        state.calls.append(('publish',))
        assert set(results)=={'train','selection','calibration'} and plan is state.plan
        assert kwargs['corpus_id']==config['corpus_id'] and kwargs['expected_protocol_sha256']==plan.protocol_sha256
        return FakePublication()
    def reader(corpus_id,**kwargs):
        state.calls.append(('reader',));state.phase='reader_returned'
        assert corpus_id==config['corpus_id'] and kwargs['expected_corpus_sha256']=='d'*64
        assert kwargs['expected_done_sha256']=='e'*64
        if state.drift_after_reader:
            (root/driver.EXTRA_SOURCES[-1]).write_bytes(b'changed after reader')
        def role_data(role):
            assert role in state.results
            trajectories=tuple(sorted(state.results[role].trajectories,key=lambda row:row.learner_id))
            if state.reader_mismatch:trajectories=trajectories[:-1]
            return SimpleNamespace(trajectories=trajectories,reference_complete=True,audit={'scope':'MOCK'},class_counts={'MOCK':1})
        return SimpleNamespace(plan=state.plan,identity='f'*64,input_bytes=123,role_data=role_data)
    modules={}
    for name in ('knowledge_tracing','knowledge_tracing.akt'):
        package=ModuleType(name);package.__path__=[];modules[name]=package
    attrs={
        'knowledge_tracing.akt.resources':dict(memory_snapshot=memory_snapshot),
        'knowledge_tracing.simulator_research_data':dict(ResearchSplitPlan=FakePlan,ShardLimits=RecordArgs),
        'knowledge_tracing.simulator_research_collection':dict(ResearchCollectionRecipe=RecordArgs,
            ResearchCollectionLimits=RecordArgs,collect_research_role=collect,
            source_inventory=lambda:dict(request['collection_sources'])),
        'knowledge_tracing.simulator_corpus_publisher':dict(CorpusPublicationLimits=RecordArgs,publish_research_corpus=publish),
        'knowledge_tracing.simulator_corpus_reader':dict(CorpusReadLimits=RecordArgs,read_public_research_corpus=reader),
    }
    for name,values in attrs.items():
        module=ModuleType(name);module.__dict__.update(values);modules[name]=module
    for name,module in modules.items():monkeypatch.setitem(sys.modules,name,module)
    real_import=builtins.__import__
    def block_heavy(name,*args,**kwargs):
        if name.split('.')[0] in ('numpy','pandas','torch'):
            raise AssertionError('actual heavy/native import forbidden in orchestration tests: '+name)
        if name.startswith('knowledge_tracing'):
            assert name in modules,'unexpected real repository import: '+name
            state.imports.append(name)
        return real_import(name,*args,**kwargs)
    monkeypatch.setattr(builtins,'__import__',block_heavy)
    original_write=driver.write_json
    def write(directory,name,value):
        original_write(directory,name,value)
        if name=='worker_result.json':state.successful_result_written=True
    monkeypatch.setattr(driver,'write_json',write)
    value=SimpleNamespace(driver=driver,root=root,config=config,request=request,request_path=request_path,
        request_relative=request_relative,state=state,output=root/request['output_relative'],
        corpus=root/'artifacts/simulator/corpora'/config['corpus_id'],
        owner=dict(status='OWNED_JOB_GATE_PASSED_NOT_SCIENTIFIC_ACCEPTANCE',worker=dict(pid=os.getpid())))
    def save_request():
        request_path.write_text(json.dumps(request,sort_keys=True),encoding='utf-8')
        return sha(request_path)
    value.save_request=save_request
    value.request_sha=save_request()
    yield value
    assert not any(n in sys.modules for n in ('numpy','pandas','torch'))


def run(case):return case.driver.run(case.request_relative,case.save_request(),case.owner)


@pytest.mark.parametrize('mapping',('collection_sources','extra_sources'))
def test_protected_source_rejected_before_any_protected_open(case,monkeypatch,mapping):
    victim=next(iter(case.request[mapping]));case.request[mapping].pop(victim)
    case.request[mapping]['dataset/forbidden.parquet']='a'*64
    request_sha=case.save_request();opened=[];original=Path.open
    def spy(path,*args,**kwargs):
        assert not path.is_relative_to(case.root/'dataset'),'protected data opened'
        opened.append(path)
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'open',spy)
    with pytest.raises(ValueError,match='exact .*source'):
        case.driver.validate_request(case.request_relative,request_sha)
    assert opened and not case.state.imports and not case.output.exists() and not case.state.calls


def test_frozen_config_profile_sha_cannot_be_changed(case):
    path=case.root/case.driver.CONFIG
    profile=json.loads(path.read_bytes());profile['collection_recipe']['policy']='changed'
    path.write_text(json.dumps(profile),encoding='utf-8')
    with pytest.raises(ValueError,match='config SHA mismatch'):
        run(case)
    assert not case.output.exists() and not case.state.calls


def test_allowlisted_source_byte_drift_rejected_before_generation(case):
    (case.root/case.driver.COLLECTION_SOURCES[-1]).write_bytes(b'drift')
    with pytest.raises(ValueError,match='source drift'):
        run(case)
    assert not case.output.exists() and not case.state.calls


def test_existing_corpus_rejected_before_generation_or_worker_writes(case):
    case.corpus.mkdir(parents=True)
    with pytest.raises(ValueError,match='fresh corpus destination'):
        run(case)
    assert not case.output.exists() and not case.state.calls and not case.state.imports


@pytest.mark.parametrize('which',('output','corpus','source'))
def test_alias_rejected_before_generation(case,monkeypatch,which):
    target=case.output if which=='output' else case.corpus if which=='corpus' else case.root/case.driver.COLLECTION_SOURCES[0]
    original=Path.is_symlink
    monkeypatch.setattr(Path,'is_symlink',lambda path:path==target or original(path))
    with pytest.raises(ValueError,match='path alias'):
        run(case)
    assert not case.output.exists() and not case.state.calls


@pytest.mark.parametrize('bad',('status','pid','missing'))
def test_wrong_owner_stops_before_validation_or_writes(case,monkeypatch,bad):
    owner=deepcopy(case.owner)
    if bad=='status':owner['status']='NOT_A_GATE_RECEIPT'
    elif bad=='pid':owner['worker']['pid']=os.getpid()+1
    else:owner.pop('worker')
    validate=monkeypatch.setattr(case.driver,'validate_request',lambda *a:pytest.fail('owner rejected too late'))
    with pytest.raises(ValueError,match='owned gate receipt'):
        case.driver.run(case.request_relative,case.request_sha,owner)
    assert not case.output.exists() and not case.state.calls


@pytest.mark.parametrize('point',('before_heavy','after_heavy','after_reader'))
def test_ram_guards_leave_no_success_receipt(case,point):
    case.state.ram_failure=point
    assert run(case)==1
    reservation=json.loads((case.output/'reservation.json').read_bytes())
    assert reservation['max_teacher_attempts']==12600 and reservation['actual_attempts'] is None
    assert (case.output/'failure.json').is_file() and not (case.output/'worker_result.json').exists()
    assert point in case.state.memory_checks
    if point=='before_heavy':
        assert case.state.imports==['knowledge_tracing.akt.resources'] and not case.state.calls
    elif point=='after_heavy':
        assert 'knowledge_tracing.simulator_corpus_reader' in case.state.imports and not case.state.calls
    else:
        assert ('reader',) in case.state.calls and ('publish',) in case.state.calls
        failure=json.loads((case.output/'failure.json').read_bytes())
        assert failure['published_but_not_accepted']['scope']=='MOCK_PUBLICATION_NOT_PUBLISHED'


def test_positive_mock_flow_is_pending_outer_not_actual_corpus_acceptance(case):
    assert run(case)==0
    reservation=json.loads((case.output/'reservation.json').read_bytes())
    assert reservation['status']=='RESERVED_NOT_ACTUAL_COUNTS' and reservation['actual_attempts'] is None
    assert reservation['max_teacher_attempts']==12600
    receipt=json.loads((case.output/'worker_result.json').read_bytes())
    assert receipt['status']=='WORKER_COMPLETE_PENDING_OUTER_ACCEPTANCE' and receipt['outer_acceptance_required'] is True
    assert receipt['interact_attempts']==receipt['interact_returns']==12600  # Manufactured stub counters, not teacher executions.
    assert receipt['final_events']==receipt['model_calls']==receipt['modal_spend_usd']==0
    assert receipt['publication']['scope']=='MOCK_PUBLICATION_NOT_PUBLISHED'
    assert not case.corpus.exists() and not (case.output/'failure.json').exists()
    roles=[row[1] for row in case.state.calls if row[0]=='collect']
    assert roles==['train','selection','calibration']
    profiles=json.loads((case.output/'profiles.json').read_bytes())
    assert Counter(profiles['train'].values())=={'PG':16,'PY':16,'PYH':16}
    assert all(Counter(profiles[r].values())=={'PG':2,'PY':2,'PYH':2} for r in ('selection','calibration'))
    assert 'final' not in profiles and len(case.state.memory_checks)>=3


def test_missing_role_support_stops_before_publish_reader(case):
    case.state.missing_reference=True
    assert run(case)==1
    assert not any(row[0] in ('publish','reader') for row in case.state.calls)
    assert not (case.output/'worker_result.json').exists()
    assert (case.output/'failure.json').is_file()


def test_reader_content_mismatch_is_failure_not_pending_success(case):
    case.state.reader_mismatch=True
    assert run(case)==1
    assert (case.output/'failure.json').is_file() and not (case.output/'worker_result.json').exists()


def test_extra_source_drift_after_reader_prevents_success(case):
    case.state.drift_after_reader=True
    assert run(case)==1
    assert (case.output/'failure.json').is_file() and not (case.output/'worker_result.json').exists()


def test_post_result_ram_failure_retains_failure_override_not_final_acceptance(case):
    case.state.fail_after_result=True
    assert run(case)==1
    assert (case.output/'failure.json').is_file()
    receipt=json.loads((case.output/'worker_result.json').read_bytes())
    assert receipt['status']=='WORKER_COMPLETE_PENDING_OUTER_ACCEPTANCE' and receipt['outer_acceptance_required'] is True
