"""Pure stubs/temporary metadata only; không actual preflight/corpus/NN/Adam."""
from dataclasses import dataclass, replace
import builtins
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import sys
from types import SimpleNamespace as NS

import pytest

from knowledge_tracing.akt import research_runner as runner
from knowledge_tracing.akt.config import AKTConfig, PROJECT_ROOT
from knowledge_tracing.akt.research_execution import (AuthorizedResearchExecution,ResearchResourceBudget,
    SimulatorResearchSpec)
from knowledge_tracing.akt.research_lifecycle import LifecycleInvocation,LifecycleLedger,PURPOSE
from knowledge_tracing.simulator_bridge import ItemQuery,Observation,SimulatorBank,SimulatorItem,identity_hash
from knowledge_tracing.simulator_research_data import ResearchSplitPlan,SelectionFreeze
from knowledge_tracing.simulator_corpus_reader import CorpusReadLimits

SHA='a'*64
_PROCESS_GUARD={'active':False}


def _test_process_audit(event,args):
    # Không đổi class Popen/không đọc argv hoặc environment của audit event.
    if _PROCESS_GUARD['active'] and event=='subprocess.Popen':
        raise AssertionError('no subprocess permitted during pure runner fixture')


sys.addaudithook(_test_process_audit)


@pytest.fixture(autouse=True)
def no_neural_import_or_process(monkeypatch):
    assert 'torch' not in sys.modules
    original=builtins.__import__
    def checked(name,*args,**kwargs):
        if name=='torch' or name.startswith('torch.') or name in (
                'knowledge_tracing.akt.model','knowledge_tracing.akt.training','knowledge_tracing.akt.checkpoint'):
            raise AssertionError('no neural imports/constructors/optimizer in pure runner tests')
        return original(name,*args,**kwargs)
    monkeypatch.setattr(builtins,'__import__',checked)
    _PROCESS_GUARD['active']=True
    try:
        yield
    finally:
        _PROCESS_GUARD['active']=False
    assert 'torch' not in sys.modules


@pytest.fixture
def spec():
    b=ResearchResourceBudget(8,1,1,16,2,2,2,8,100,10.,20.,2*1024**3,1024**3,
        1024**2,1024**2,4*1024**2)
    c=AKTConfig(phase='simulator-research',run_id='unit-runner',execution_enabled=True,
        output_dir=PROJECT_ROOT/'experiments/akt/results/unit-runner',max_train_users=9,max_val_users=1,
        max_targets_per_side=18,max_total_targets=20,max_steps=8,max_seconds=10.,max_wall_seconds=20.,
        max_rss_bytes=2*1024**3,min_available_ram_bytes=1024**3)
    return SimulatorResearchSpec(c,'unit-metadata-not-corpus',SHA,SHA,b)


@pytest.fixture
def token(spec):
    return AuthorizedResearchExecution(spec,None,'artifacts/akt/unit-not-authorized.json',SHA,'UNIT_NOT_REAL_AUTH','{}')


def forbidden(*args,**kwargs):
    pytest.fail('lazy neural API must not be reached')


def test_invalid_auth_stops_before_reader_memory_or_lazy(monkeypatch,token):
    calls=[]
    def reject(*args,**kwargs):
        calls.append('auth');raise ValueError('actual closed auth rejected')
    monkeypatch.setattr(runner,'require_research_authorization',reject)
    monkeypatch.setattr(runner,'read_public_research_corpus',forbidden)
    monkeypatch.setattr(runner,'_memory',forbidden);monkeypatch.setattr(runner,'_lazy',forbidden)
    with pytest.raises(ValueError,match='closed auth'):
        runner.run_a0_research_lifecycle(token,read_limits=CorpusReadLimits(1024,4096,512,8,2,20,10.))
    assert calls==['auth']


def test_forged_token_field_mismatch_rejected_before_reader(monkeypatch,token):
    monkeypatch.setattr(runner,'require_research_authorization',lambda *a,**kw:replace(token,approval_reference='DIFFERENT_DISK_VALUE'))
    monkeypatch.setattr(runner,'read_public_research_corpus',forbidden)
    with pytest.raises(ValueError,match='disk artifact'):
        runner._admit(token,CorpusReadLimits(1024,4096,512,8,2,20,10.))


def test_bad_corpus_stops_before_lazy_or_output(monkeypatch,token):
    monkeypatch.setattr(runner,'require_research_authorization',lambda *a,**kw:token)
    monkeypatch.setattr(AuthorizedResearchExecution,'revalidate',lambda self:dict(corpus=dict(done_sha256=SHA)))
    def reject(*args,**kwargs):raise ValueError('public corpus digest mismatch')
    monkeypatch.setattr(runner,'read_public_research_corpus',reject)
    monkeypatch.setattr(runner,'_lazy',forbidden);monkeypatch.setattr(runner,'_data',forbidden)
    with pytest.raises(ValueError,match='public corpus'):
        runner.run_a0_research_lifecycle(token,read_limits=CorpusReadLimits(1024,4096,512,8,2,20,10.))


def test_read_caps_cannot_widen_authorized_limits(monkeypatch,token):
    monkeypatch.setattr(runner,'require_research_authorization',lambda *a,**kw:token)
    monkeypatch.setattr(AuthorizedResearchExecution,'revalidate',lambda self:dict(corpus=dict(done_sha256=SHA)))
    monkeypatch.setattr(runner,'read_public_research_corpus',forbidden)
    with pytest.raises(ValueError,match='read limits'):
        runner._admit(token,CorpusReadLimits(1024,4096,512,8,3,20,10.))


def test_population_binding_reuses_shard_seal_without_prefix_arithmetic():
    t=NS(learner_id='u',observations=(Observation(ItemQuery('i',1,1),0),))
    key=runner._public_population((t,),(('selection',SHA),))
    assert key!=runner._public_population((t,),(('selection','b'*64),))
    changed=NS(learner_id='u',observations=(Observation(ItemQuery('i',2,1),0),))
    assert key!=runner._public_population((changed,),(('selection',SHA),))


@pytest.fixture
def runtime(tmp_path,monkeypatch,token):
    execution=NS(spec=token.spec,authorization_sha256=SHA)
    run=runner._Run(execution,{},NS(bank=object(),plan=object()),0.,0.)
    run.output=tmp_path
    inv=LifecycleInvocation(token.spec,SHA,SHA,SHA,SHA,
        (('train','b'*64),('selection','c'*64),('calibration','d'*64)),SHA,SHA,SHA,PURPOSE)
    run.head=LifecycleLedger.begin(inv)
    monkeypatch.setattr(run,'clocks',lambda:dict(wall_seconds=1.,training_seconds=.5))
    monkeypatch.setattr(run,'guard',lambda:None)
    return run


class Hook:
    def __init__(self,callbacks,callback):self.callbacks,self.callback=callbacks,callback
    def remove(self):self.callbacks.remove(self.callback)


class FakeAdam:
    """Không Adam/model thật; chỉ mô phỏng thứ tự hook trước/body-return."""
    def __init__(self,parameters):
        self.param_groups=[dict(params=list(parameters))];self.pre=[];self.post=[]
    def register_step_pre_hook(self,callback):self.pre.append(callback);return Hook(self.pre,callback)
    def register_step_post_hook(self,callback):self.post.append(callback);return Hook(self.post,callback)
    def declared_stub_step(self):
        for callback in self.pre:callback(self,(),{})
        for callback in self.post:callback(self,(),{})


@dataclass
class StubStats:
    complete: bool
    valid_targets: int
    optimizer_steps: int


class Mask:
    def __init__(self,n):self.n=n
    def sum(self):return self.n


def train_stubs(runtime,*,post_failure=False,complete=True):
    parameter=object();adapter=NS(native=NS(parameters=lambda:iter([parameter])),encoding=NS(vocabulary=NS(values=('i',))))
    optimizer=FakeAdam([parameter])
    phase=NS(scope='select_train80',shards=(NS(audit={'audit':{'targets':16}}),))
    entry=NS(window=NS(target_mask=Mask(16)),targets=(0,1)*8)
    tools=NS(collate_windows=lambda *a,**kw:NS())
    def train_epoch(actual,factory,**kwargs):
        assert not hasattr(runtime,'corpus')
        assert not any(hasattr(value,'role_data') or hasattr(value,'trajectories') for value in vars(runtime).values())
        assert actual is adapter and kwargs['optimizer'] is optimizer and kwargs['recovery'] is None
        assert list(factory())==[entry]
        kwargs['batch_factory']((entry,))
        optimizer.declared_stub_step()
        if post_failure:raise RuntimeError('injected after stub body return')
        kwargs['progress_callback']({'training':{'optimizer_steps':1}})
        return StubStats(complete,16,1)
    tools.train_epoch=train_epoch
    data=NS(iter_research_windows=lambda *a,**kw:iter([entry]))
    return tools,data,adapter,optimizer,phase


def test_train_epoch_reuses_native_primitive_and_global_hooks(runtime):
    tools,data,adapter,opt,phase=train_stubs(runtime)
    stats=runner._train_epoch(runtime,tools,data,adapter,opt,phase,None,1)
    assert stats.complete and (runtime.head.reserved_steps,runtime.head.body_returned_steps,runtime.head.completed_steps)==(1,1,1)
    assert runtime.head.completed_targets==16 and runtime.head.pending is None
    assert not opt.pre and not opt.post
    events=[json.loads(x) for x in (runtime.output/'events.jsonl').read_text().splitlines()]
    assert [e['event'] for e in events]==['epoch_started','optimizer_reserved','optimizer_body_returned','batch_complete']


def test_post_body_failure_keeps_pending_return_not_rollback(runtime):
    tools,data,adapter,opt,phase=train_stubs(runtime,post_failure=True)
    with pytest.raises(RuntimeError,match='body return'):
        runner._train_epoch(runtime,tools,data,adapter,opt,phase,None,1)
    assert runtime.head.reserved_steps==runtime.head.body_returned_steps==1
    assert runtime.head.completed_steps==0 and runtime.head.pending_body_returned
    assert not opt.pre and not opt.post


def test_partial_native_epoch_never_selects(runtime):
    tools,data,adapter,opt,phase=train_stubs(runtime,complete=False)
    with pytest.raises(ValueError,match='partial optimization'):
        runner._train_epoch(runtime,tools,data,adapter,opt,phase,None,1)
    assert runtime.head.reserved_steps==1  # Work retained, not a successful epoch.


def test_foreign_or_duplicate_optimizer_parameters_rejected_before_forward(runtime):
    tools,data,adapter,opt,phase=train_stubs(runtime)
    opt.param_groups[0]['params']*=2
    tools.train_epoch=forbidden
    with pytest.raises(ValueError,match='ownership'):
        runner._train_epoch(runtime,tools,data,adapter,opt,phase,None,1)


def test_global_cap_not_reset_after_prior_work(runtime):
    tools,data,adapter,opt,phase=train_stubs(runtime)
    runtime.head=replace(runtime.head,reserved_steps=runtime.budget.max_optimizer_steps)
    tools.train_epoch=forbidden
    with pytest.raises(ValueError,match='remaining optimization'):
        runner._train_epoch(runtime,tools,data,adapter,opt,phase,None,1)
    assert runtime.head.reserved_steps==runtime.budget.max_optimizer_steps


def test_late_body_return_keeps_failed_ledger_and_durable_event(runtime,monkeypatch):
    tools,data,adapter,opt,phase=train_stubs(runtime)
    calls=iter([dict(wall_seconds=1.,training_seconds=.5),dict(wall_seconds=1.,training_seconds=.5),
                dict(wall_seconds=1.,training_seconds=.5),dict(wall_seconds=21.,training_seconds=2.)])
    # start_epoch, remainingbudget, reserve, body_return; finally uses last clock.
    last={'wall_seconds':1.,'training_seconds':.5}
    def clocks():
        nonlocal last
        last=next(calls,last);return last
    monkeypatch.setattr(runtime,'clocks',clocks)
    with pytest.raises(runner.LifecycleBudgetExceeded):
        runner._train_epoch(runtime,tools,data,adapter,opt,phase,None,1)
    assert runtime.head.phase=='failed' and runtime.head.body_returned_steps==1
    assert runtime.head.completed_steps==0
    assert 'REJECTED_TIME_BUDGET' in (runtime.output/'events.jsonl').read_text()


@pytest.mark.parametrize('problem',['identity','metadata_cap','payload_cap','sha','epoch'])
def test_owned_checkpoint_rejects_before_restore_and_caps_before_load(runtime,problem):
    directory=runtime.output/'refit90';directory.mkdir()
    path=directory/'checkpoint.pt';path.write_bytes(b'NOT_PICKLE_SYNTHETIC_BYTES')
    identity=dict(weight_role='simulator_research_refit90')
    meta=dict(identity=identity,checkpoint_sha256=runner._sha(path),bytes=path.stat().st_size,epoch=1)
    meta_sha=runner._write_json(path.with_suffix('.json'),meta,runtime.budget.max_prediction_bytes)
    ref=dict(path='refit90/checkpoint.pt',**meta,metadata_sha256=meta_sha)
    tools=NS(load_checkpoint=forbidden,restore_checkpoint=forbidden)
    if problem=='identity':ref['identity']={'weight_role':'WRONG'}
    elif problem=='metadata_cap':runtime.budget=replace(runtime.budget,max_prediction_bytes=1)
    elif problem=='payload_cap':runtime.budget=replace(runtime.budget,max_checkpoint_bytes=1)
    elif problem=='sha':path.write_bytes(b'MUTATED')
    else:
        tools.load_checkpoint=lambda *a,**kw:{'progress':dict(epoch=2,role=identity['weight_role'])}
    with pytest.raises(ValueError):
        runner._restore_owned(runtime,tools,ref,None,None,identity)


def test_model_creation_seeds_and_constructs_new_instances_no_load(runtime):
    calls=[];parameter_sets=[]
    class Numpy:
        random=NS(seed=lambda seed:calls.append(('numpy',seed)))
    def ctor(config,encoding):
        parameters=[object()];parameter_sets.append(parameters)
        return NS(native=NS(parameters=lambda:iter(parameters)))
    tools=NS(np=Numpy,torch=NS(random=NS(default_generator=NS(manual_seed=lambda seed:calls.append(('torch_cpu',seed)))),
        optim=NS(Adam=lambda params,**kw:FakeAdam(params))),AKTAdapter=ctor)
    encoding=NS(exercise_encoding=lambda:object())
    first,opt1=runner._new_model(runtime,tools,encoding)
    second,opt2=runner._new_model(runtime,tools,encoding)
    assert first is not second and opt1 is not opt2 and parameter_sets[0][0] is not parameter_sets[1][0]
    assert calls==[('numpy',42),('torch_cpu',42),('numpy',42),('torch_cpu',42)]


def test_phase_selector_never_passes_calibration_to_train_or_refit(monkeypatch):
    calls=[]
    def shard(plan,bank,role,trajectories,*args):calls.append(role);return NS(role=role)
    data=NS(ResearchAKTShard=shard,prepare_research_phase=lambda scope,**kw:(scope,kw))
    corpus=NS(plan=object(),bank=object(),limits=NS(shard_limits=object()),
        role_data=lambda role:NS(trajectories=(),provenance=NS(identity=SHA)))
    assert runner._phase(data,corpus,'select_train80')[0]=='select_train80' and calls==['train']
    calls.clear();freeze=object()
    _,kwargs=runner._phase(data,corpus,'refit_union90',freeze)
    assert calls==['train','selection'] and kwargs['selection_freeze'] is freeze
    calls.clear();runner._phase(data,corpus,'raw_selection10')
    assert calls==['selection']


def test_output_no_clobber_and_prediction_byte_cap(runtime):
    runner._write_json(runtime.output/'one.json',{'x':1},100)
    with pytest.raises(FileExistsError):runner._write_json(runtime.output/'one.json',{'x':2},100)
    with pytest.raises(ValueError,match='byte cap'):
        runner._write_csv(runtime.output/'large.csv',[dict(x='a'*100)],10)
    assert not (runtime.output/'large.csv').exists()


def test_native_objective_uses_same_float32_endpoints_without_reporting_clip():
    calls=[];dtype=object()
    def tensor(values,**kwargs):
        assert kwargs==dict(dtype=dtype,device='cpu');return list(values)
    def bce(probabilities,labels,**kwargs):
        calls.append((probabilities,labels,kwargs));return NS(item=lambda:.25)
    tools=NS(torch=NS(float32=dtype,tensor=tensor,nn=NS(functional=NS(binary_cross_entropy=bce))))
    assert runner._native_bce(tools,[0.,1.],[0,1])==.25
    assert calls==[([0.,1.],[0,1],dict(reduction='mean'))]


@pytest.fixture
def reporting_case():
    raw=[];truth=[];calibrated=[];calls=[]
    for i,(p,y) in enumerate(((.625,0),(.375,1),(None,0))):
        key=dict(learner_id='cal-u',item_id=f'i{i}',timestamp=i+1,source_row=i+1,global_rank=i,
            history_sha256=SHA,history_hash_scheme='observable-prefix-chain-v1',origin_role='calibration',
            phase_scope='calibration_predict',phase_sha256=SHA,encoding_sha256=SHA)
        row=dict(**key,probability=p,support_reason='supported' if p is not None else 'oov_item')
        raw.append(row);truth.append(dict(**key,correct=y))
        calibrated.append(dict(row,calibrated_probability=(0.,1.,None)[i]))
    summary=dict(full_targets=3,supported_targets=2,unsupported_targets=1,population_sha256=SHA,
        population_scheme=runner.POPULATION_SCHEME,native_bce_mean=.6,objective=runner.OBJECTIVE,
        supported_metrics={'raw_sentinel_not_calibrated':True},full_metrics=None)
    def metrics(frame):
        calls.append(frame);return {'canonical_sentinel':True}
    tools=NS(pd=NS(DataFrame=lambda frame:frame),_metrics=metrics)
    return NS(raw=raw,truth=truth,calibrated=calibrated,summary=summary,tools=tools,calls=calls)


def test_calibrated_reporting_identity_join_preserves_raw_nulls_and_evaluator(reporting_case):
    case=reporting_case
    before=json.dumps((case.raw,case.truth,case.calibrated,case.summary),sort_keys=True)
    result=runner._calibrated_reporting_metrics(case.tools,case.summary,case.raw,
        list(reversed(case.calibrated)),[case.truth[2],case.truth[0],case.truth[1]])
    assert case.calls==[dict(correct=[0,1],prediction=[0.,1.])]  # No extra clip or positional-label join.
    assert result['supported_metrics']=={'canonical_sentinel':True} and result['full_metrics'] is None
    assert (result['full_targets'],result['supported_targets'],result['unsupported_targets'])==(3,2,1)
    assert result['unsupported_counts']=={'oov_item':1}
    assert result['population_sha256']==case.summary['population_sha256']
    assert result['population_scheme']==runner.POPULATION_SCHEME and result['reporting_evaluator']==runner.METRICS
    assert result['evaluation_scope']=='in_sample_calibration_partition_not_external_quality'
    assert json.dumps((case.raw,case.truth,case.calibrated,case.summary),sort_keys=True)==before


@pytest.mark.parametrize('problem',['missing_truth','extra_truth','duplicate_truth','changed_history',
    'changed_raw_probability','null_to_probability','supported_to_null','nonfinite','missing_identity',
    'wrong_supported_count','bool_label','noncalibration_role'])
def test_calibrated_reporting_rejects_population_support_or_truth_drift(reporting_case,problem):
    case=reporting_case
    if problem=='missing_truth':case.truth.pop()
    elif problem=='extra_truth':case.truth.append(dict(case.truth[0],source_row=4,global_rank=3))
    elif problem=='duplicate_truth':case.truth.append(dict(case.truth[0]))
    elif problem=='changed_history':case.truth[0]['history_sha256']='b'*64
    elif problem=='changed_raw_probability':case.calibrated[0]['probability']=.7
    elif problem=='null_to_probability':case.calibrated[2]['calibrated_probability']=.5
    elif problem=='supported_to_null':case.calibrated[0]['calibrated_probability']=None
    elif problem=='nonfinite':case.calibrated[0]['calibrated_probability']=float('nan')
    elif problem=='missing_identity':del case.truth[0]['global_rank']
    elif problem=='wrong_supported_count':case.summary['supported_targets']=3
    elif problem=='bool_label':case.truth[0]['correct']=True
    elif problem=='noncalibration_role':
        for rows in (case.raw,case.calibrated,case.truth):
            for row in rows:row.update(origin_role='selection',phase_scope='raw_selection10')
    with pytest.raises(ValueError):
        runner._calibrated_reporting_metrics(case.tools,case.summary,case.raw,case.calibrated,case.truth)
    assert case.calls==[]  # Reject before canonical evaluator on a different population.


def test_prediction_joins_truth_after_forward_and_keeps_full_oov_population(runtime,monkeypatch):
    predicted=[False]
    queries=[ItemQuery('i0',1,1),ItemQuery('i1',2,2),ItemQuery('oov',3,3)]
    observations=tuple(Observation(q,y) for q,y in zip(queries,(0,1,0)))
    phase=NS(scope='raw_selection10',identity=SHA,assert_integrity=lambda:None,
        trajectories=(NS(learner_id='u',observations=observations),),
        shards=(NS(role='selection',audit={'audit':{'shard_sha256':SHA}}),))
    encoding=NS(identity=SHA,assert_integrity=lambda:None)
    window=NS(inputs=NS(item_ids=[0,1],user_ids=('u','u'),source_rows=[1,2]),target_mask=[True,True],
        global_ranks=[0,1],window_id='original-window',history_available=[0,1],history_used=[0,1],context_reset=[False,False])
    class Unseen:
        learner_id='u';query=queries[2];global_rank=2
    def predict(windows):
        assert windows==(window,);predicted[0]=True;return [[.625,.375]]
    def targets(*args):
        assert predicted[0], 'current labels must join only after complete prediction pass'
        return tuple(NS(learner_id='u',query=q,correct=y,global_rank=i,trained_item=i<2,
            history_sha256=SHA,history_hash_scheme='observable-prefix-chain-v1',origin_role='selection',
            phase_scope='raw_selection10',phase_sha256=SHA,encoding_sha256=SHA)
            for i,(q,y) in enumerate(zip(queries,(0,1,0))))
    data=NS(ResearchUnseenTarget=Unseen,iter_research_windows=lambda *a,**kw:iter((window,Unseen())),
            research_scoring_targets=targets)
    metric_inputs=[]
    tools=NS(np=NS(flatnonzero=lambda values:[i for i,v in enumerate(values) if v],
                   float32=lambda value:struct.unpack('f',struct.pack('f',value))[0]),
        pd=NS(DataFrame=lambda value:value),_metrics=lambda frame:metric_inputs.append(frame) or {'stub_metrics_only':True})
    monkeypatch.setattr(runner,'_state_hash',lambda adapter:SHA)
    def bce(actual,probabilities,labels):
        assert actual is tools and probabilities==[.625,.375] and labels==[0,1]
        return .7
    monkeypatch.setattr(runner,'_native_bce',bce)
    summary,rows,truth=runner._predict(runtime,tools,data,NS(predict_windows=predict),phase,encoding)
    assert (summary['full_targets'],summary['supported_targets'],summary['unsupported_targets'])==(3,2,1)
    assert summary['full_metrics'] is None and rows[2]['probability'] is None
    assert rows[2]['support_reason']=='oov_item' and rows[2]['window_id'] is None
    assert rows[0]['window_id']=='original-window' and rows[1]['history_used']==1
    assert [t['correct'] for t in truth]==[0,1,0] and len(rows)==len(truth)==3
    assert metric_inputs==[dict(correct=[0,1],prediction=[.625,.375])]


@dataclass
class StubEncoding:
    scope: str
    identity: str


@pytest.mark.parametrize('calibration_labels',[(0,1),(1,0)])
def test_orchestration_stubs_freeze_before_fresh_refit_and_calibration_never_selects(
        runtime,monkeypatch,calibration_labels):
    """Hai fake epoch events,0actual optimizer; scalar T thật trên2fake predictions."""
    calls=[]
    plan=ResearchSplitPlan('runner-stub-not-generated-corpus',42,10,1,SHA)
    bank=SimulatorBank('runner-stub-bank',tuple(SimulatorItem(f'c{c}-{d}',f'c{c}',d)
        for c in range(28) for d in (1050,1200,1350)))
    corpus=NS(plan=plan,bank=bank,assert_integrity=lambda:None,
              calibration_trajectories='FULL_CORPUS_ONLY_IN_TRUSTED_ORCHESTRATOR')
    runtime.plan=plan;runtime.bank=bank
    runtime.execution.revalidate=lambda:calls.append(('source_revalidate',))
    runtime.identity={'native_evidence':{'build_hashes':{'stub_source':SHA}}}
    runtime.head=LifecycleLedger.begin(replace(runtime.head.invocation,
        research_plan_sha256=plan.identity,bank_sha256=identity_hash(bank.identity)))
    for name in ('fit80','selection','refit90','calibration'):(runtime.output/name).mkdir()
    def phase(scope):
        roles={'select_train80':('train',),'raw_selection10':('selection',),
               'refit_union90':('train','selection'),'calibration_predict':('calibration',)}[scope]
        return NS(scope=scope,shards=tuple(NS(role=r,audit={'audit':{'shard_sha256':dict(
            train='b'*64,selection='c'*64,calibration='d'*64)[r]}}) for r in roles))
    train=phase('select_train80');selection=phase('raw_selection10');encoding=StubEncoding('select_train80',SHA)
    def make_phase(data,corpus,scope,freeze=None):
        assert freeze is not None and runtime.head.selection_freeze==freeze
        if scope=='calibration_predict':assert runtime.head.phase=='refit_complete'
        calls.append(('phase',scope));return phase(scope)
    monkeypatch.setattr(runner,'_phase',make_phase)
    data=NS(fit_research_encoding=lambda p:StubEncoding(p.scope,SHA))
    models=[]
    def new_model(run,tools,enc):
        parameter=object();model=NS(native=NS(parameters=lambda:iter([parameter])))
        models.append(model);calls.append(('new_model',enc.scope));return model,FakeAdam([parameter])
    monkeypatch.setattr(runner,'_new_model',new_model)
    monkeypatch.setattr(runner,'_checkpoint_identity',lambda run,tools,model,enc,role:
        dict(weight_role=role,vocabulary_sha256=SHA))
    def train_epoch(run,tools,data,model,opt,p,enc,epoch):
        assert not hasattr(run,'corpus') and not hasattr(run,'calibration_trajectories')
        assert not any(value is corpus or hasattr(value,'role_data') or hasattr(value,'trajectories')
                       for value in vars(run).values())
        calls.append(('stub_train',p.scope,tuple(s.role for s in p.shards)))
        assert p.scope in ('select_train80','refit_union90')
        run.head.inputs(p.scope);run.transition('start_epoch')
        n=16 if p.scope=='select_train80' else 18
        run.transition('reserve_step',n);run.transition('body_returned',run.head.pending)
        run.transition('complete_step',run.head.pending)
        return StubStats(True,n,1)
    monkeypatch.setattr(runner,'_train_epoch',train_epoch)
    observed=[]
    class Stopper:
        def __init__(self,patience,delta):
            assert (patience,delta)==(3,.0001);self.best_epoch=None
        def observe(self,epoch,loss):
            observed.append((epoch,loss));self.best_epoch=1;return True
    def predict(run,tools,data,model,p,enc):
        assert not hasattr(run,'corpus') and not hasattr(run,'calibration_trajectories')
        assert p.scope in ('raw_selection10','calibration_predict')
        calls.append(('predict',p.scope))
        role='selection' if p.scope=='raw_selection10' else 'calibration'
        learner=plan.split_plan.assignments(role)[0].learner_id
        keys=[dict(learner_id=learner,source_row=i+1,item_id=bank.item_ids[0],timestamp=i+1,global_rank=i,
            history_sha256=SHA,history_hash_scheme='observable-prefix-chain-v1',origin_role=role,
            phase_scope=p.scope,phase_sha256=SHA,encoding_sha256=enc.identity) for i in range(2)]
        rows=[dict(key,probability=v,support_reason='supported') for key,v in zip(keys,(.625,.375))]
        labels=(0,1) if role=='selection' else calibration_labels
        summary=dict(full_targets=2,supported_targets=2,population_sha256=SHA,population_scheme=runner.POPULATION_SCHEME,
                     native_bce_mean=.6,objective=runner.OBJECTIVE,supported_metrics={'raw_sentinel':True})
        return summary,rows,[dict(key,correct=y) for key,y in zip(keys,labels)]
    monkeypatch.setattr(runner,'_predict',predict)
    def save(run,tools,path,model,opt,identity,epoch):
        calls.append(('save',path.parent.name));return dict(path=path.relative_to(run.output).as_posix(),
            checkpoint_sha256=('1' if path.parent.name=='fit80' else '4')*64,epoch=epoch,identity=identity)
    monkeypatch.setattr(runner,'_save',save)
    monkeypatch.setattr(runner,'_restore_owned',lambda *a:calls.append(('restore',)))
    monkeypatch.setattr(runner,'_read_owned',lambda *a:calls.append(('read_payload_before_constructor',)) or {})
    monkeypatch.setattr(runner,'_restore_loaded',lambda *a:calls.append(('restore_loaded',)))
    def probe(run,tools,data,model,p,enc):
        assert p.scope=='refit_union90';calls.append(('probe',p.scope))
        return dict(scope='BOUNDED_FIRST_NATIVE_WINDOWS_NOT_FULL_REFIT',windows=1,targets=2,population_sha256=SHA)
    monkeypatch.setattr(runner,'_reload_probe',probe)
    canonical_calls=[]
    def canonical_metrics(frame):
        canonical_calls.append(frame);return {'canonical_calibrated_sentinel':True}
    tools=NS(EarlyStopping=Stopper,pd=NS(DataFrame=lambda frame:frame),_metrics=canonical_metrics)
    result=runner._execute_cpu(runtime,tools,data,train,selection,encoding,corpus)
    assert result['selected_epoch']==1 and observed==[(1,.6)]
    assert [call for call in calls if call[0]=='stub_train']==[
        ('stub_train','select_train80',('train',)),('stub_train','refit_union90',('train','selection'))]
    assert [call for call in calls if call[0]=='new_model']==[
        ('new_model','select_train80'),('new_model','refit_union90'),('new_model','refit_union90')]
    assert models[0] is not models[1] and models[1] is not models[2]
    assert calls.index(('read_payload_before_constructor',)) < max(i for i,c in enumerate(calls) if c[0]=='new_model')
    assert calls.index(('phase','refit_union90')) < calls.index(('phase','calibration_predict'))
    assert len([c for c in calls if c[0]=='probe'])==2
    assert runtime.head.phase=='complete' and runtime.head.completed_steps==2  # Stub events, no Adam execution.
    assert (runtime.output/'selection/freeze.json').is_file()
    assert (runtime.output/'calibration/calibrator.json').is_file()
    exported=json.loads((runtime.output/'calibration/export.json').read_text())
    assert exported['coverage']['supported_metrics']=={'raw_sentinel':True}
    assert exported['coverage']['objective']==runner.OBJECTIVE
    assert exported['calibrated_reporting']['supported_metrics']=={'canonical_calibrated_sentinel':True}
    assert exported['calibrated_reporting']['supported_targets']==2
    assert exported['temperature_fit_objective']['logit_clip']==1e-6
    assert exported['temperature_fit_objective']['scope']=='Tfit optimization objective; not canonical reportingLL'
    assert len(canonical_calls)==1 and canonical_calls[0]['correct']==list(calibration_labels)
    assert not (runtime.output/'COMPLETE.json').exists()  # Actual outer acceptance/publication not stubbed as success.
