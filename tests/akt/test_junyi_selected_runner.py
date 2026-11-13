"""Orchestration Junyi với model CPU nhỏ; CUDA/runtime được mock rõ phạm vi.

Chỉ chạy trong Gate Linux đủ RAM. Checkpoint/model/Adam/RNG dùng hàm native.
train_epoch và evaluation được thay bằng thao tác xác định để kiểm state machine.
"""
from dataclasses import asdict
import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from knowledge_tracing.akt import authorization, checkpoint, model, research_graph_model, training
from knowledge_tracing.akt import research_junyi_selection as selected
from knowledge_tracing.akt.config import AKTConfig, DataPaths, ResearchCUDAExecutionProfile
from knowledge_tracing.akt.encoding import ExerciseEncoding
from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView, JunyiResearchEncoding
from knowledge_tracing.akt.research_junyi_roles import make_junyi_research_roles
from knowledge_tracing.akt.research_runner import _state_hash
from knowledge_tracing.akt.types import KTEvent, LearnerEvents
from knowledge_tracing.shared_kt import StableVocabulary


def test_selection_uses_legacy_prediction_path(monkeypatch):
    from knowledge_tracing.akt import prediction, prediction_batch
    from knowledge_tracing.akt.types import PredictionRecord
    records = [PredictionRecord(1,'u','A',1,1,0,4,.75,'fitted',False,
                                1,0,0,False,'window','checkpoint')]
    calls = []

    def legacy(adapter, learners):
        calls.append((adapter, learners))
        return iter(records)

    def forbidden(*args, **kwargs):
        raise AssertionError('Unadmitted batched path used for selection')

    monkeypatch.setattr(prediction,'iter_predictions',legacy)
    monkeypatch.setattr(prediction_batch,'iter_predictions_batched',forbidden)
    adapter, learners = object(), object()
    actual = selected._evaluate(adapter,learners,1)
    assert calls == [(adapter,learners)]
    assert actual['targets']==actual['supported']==1
    assert actual['oov']==0
    assert actual['native_bce']==pytest.approx(-math.log(.75))


@pytest.fixture
def harness(tmp_path, monkeypatch):
    roles = make_junyi_research_roles([(str(i),i%5,'development') for i in range(30)])
    train = JunyiPhaseView(roles,'select_train80',roles.train_users[:2],roles.identity)
    selection = JunyiPhaseView(roles,'raw_selection10',roles.selection_users[:1],roles.identity)
    paths = DataPaths(*(tmp_path/name for name in ('canonical','assignments','canonical.json','split.json')))
    inputs = selected.JunyiSelectedInputs(paths,train,selection,4,2,'a'*64)
    config = AKTConfig(phase='junyi-research',device='cuda',outer_fold=4,
        run_id='junyi-selected-unit',output_dir=tmp_path/'run',execution_enabled=True,
        max_train_users=2,max_val_users=1,max_targets_per_side=4,max_total_targets=1000,
        max_steps=100,max_seconds=60.,max_wall_seconds=120.,max_rss_bytes=2*1024**3,
        min_available_ram_bytes=1)
    profile = ResearchCUDAExecutionProfile(2*1024**3)
    native_encoding = ExerciseEncoding(StableVocabulary(('A',)),{'A':2})
    encoding = JunyiResearchEncoding(native_encoding,train)
    runtime = tmp_path/'runtime.json'
    runtime.write_text('{}')
    gate_file = tmp_path/'gate.json'
    gate_file.write_text(json.dumps(dict(build_hashes={'unit-source':'f'*64})))
    gate = dict(report_sha256=selected.file_sha(gate_file),evidence_path=str(gate_file))
    lock = tmp_path/'lock.txt'
    lock.write_text('unit fixture')
    control = dict(train_calls=[],evaluate_calls=[],partial_epoch=None,fail_validation_epoch=None,
                   population_change_epoch=None,models=[],grants=0)

    class TinyNative(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = torch.nn.Linear(1,1,device='cpu')
            self.register_buffer('epoch_marker',torch.tensor(0,dtype=torch.int64,device='cpu'))

        def forward(self, values):
            return self.linear(values)

        @property
        def backbone(self):
            return self

    class TinyAdapter:
        def __init__(self, actual_config, actual_encoding):
            self.config = actual_config
            self.encoding = actual_encoding
            self.native = TinyNative()
            control['models'].append(self)

    class TinyGraphAdapter(TinyAdapter):
        def set_phase(self,phase):
            self.phase=phase
            control.setdefault('graph_phases',[]).append(phase.view.scope)

        def collate_training(self,entries):
            raise AssertionError('Orchestration fixture replaces the training loop')

    native_load = checkpoint.load_checkpoint
    native_snapshot = checkpoint.load_training_snapshot
    monkeypatch.setattr(checkpoint,'load_checkpoint',lambda path,*,expected_identity,device:
        native_load(path,expected_identity=expected_identity,device='cpu'))
    monkeypatch.setattr(checkpoint,'load_training_snapshot',lambda path,*,expected_identity,device:
        native_snapshot(path,expected_identity=expected_identity,device='cpu'))
    monkeypatch.setattr(model,'AKTAdapter',TinyAdapter)
    monkeypatch.setattr(selected,'validate_config',lambda *args,**kwargs:None)
    monkeypatch.setattr(authorization,'require_gate2_evidence',lambda *args,**kwargs:gate)
    monkeypatch.setattr(authorization,'preflight',lambda *args,**kwargs:dict(status='unit-mocked'))
    monkeypatch.setattr(research_graph_model,'_cuda_execution_check',lambda *args,**kwargs:dict(unit_cpu=True))
    monkeypatch.setattr(selected,'fit_junyi_research_encoding',lambda *args,**kwargs:encoding)
    monkeypatch.setattr(selected,'iter_junyi_research_windows',lambda *args,**kwargs:iter(()))

    def learners(*args,**kwargs):
        return iter((LearnerEvents(selection.users[0],0,tuple(
            KTEvent(selection.users[0],'A',100+i,i+1,i%2,0,0) for i in range(2))),))

    monkeypatch.setattr(selected,'iter_junyi_phase_learners',learners)

    def stats_for(epoch, *, complete, steps):
        return training.EpochStats(loss_sum=float(epoch),valid_targets=steps*2,
            optimizer_steps=steps,complete=complete,resource={'wall_seconds':.01},
            nonzero_gradient_steps=steps,parameter_update_steps=steps,
            stop_reason='epoch_complete' if complete else 'time_budget')

    def train_epoch(adapter, windows_factory, *, optimizer, epoch, budget, progress_callback, recovery,
                    batch_factory=None):
        control['train_calls'].append(epoch)
        if batch_factory is not None:
            assert batch_factory.__self__ is adapter
            assert adapter.phase.view.scope=='select_train80'
            assert recovery['identity']['batch_factory']['condition_sha256']==adapter.phase.condition.identity
        assert recovery['checkpoint_every_steps']==1000
        assert callable(recovery['checkpoint_callback'])
        assert recovery['selection_state']['optimizer_steps']>=0
        done = 0
        if recovery['resume_checkpoint'] is not None:
            payload = checkpoint.load_recovery_checkpoint(recovery['resume_checkpoint'],
                expected_identity=recovery['identity'],device='cpu')
            state = checkpoint.restore_recovery_checkpoint(adapter,optimizer,payload)
            assert state['epoch']==epoch
            done = state['optimizer_steps']
        incomplete = control['partial_epoch']==epoch
        final_steps = 1 if incomplete else 2
        for _ in range(done,final_steps):
            optimizer.zero_grad(set_to_none=True)
            value = adapter.native(torch.tensor([[float(epoch)]],dtype=torch.float32,device='cpu'))
            value.square().sum().backward()
            optimizer.step()
        adapter.native.epoch_marker.fill_(epoch)
        stats = stats_for(epoch,complete=not incomplete,steps=final_steps)
        if incomplete:
            path = recovery['checkpoint_dir']/f'unit-epoch{epoch:03d}-step{final_steps:03d}.pt'
            checkpoint.save_recovery_checkpoint(path,adapter,optimizer,identity=recovery['identity'],
                resume_state=dict(schema_version=1,epoch=epoch,optimizer_steps=final_steps,
                    sampler_state={'unit_fake_cursor':True},trainer_state=dict(
                        stats=asdict(stats),selection_state=recovery['selection_state'])))
            recovery['checkpoint_callback'](path)
        progress_callback(dict(training=dict(optimizer_steps=final_steps),complete_epoch=not incomplete))
        return stats

    monkeypatch.setattr(training,'train_epoch',train_epoch)
    losses = {1:.5,2:.4,3:.40001,4:.40002,5:.40003}

    def evaluate(adapter, actual_learners, target_count, *, output=None):
        if isinstance(adapter,TinyGraphAdapter):
            assert adapter.phase.view.scope=='raw_selection10'
        assert target_count==2 and sum(len(learner.events) for learner in actual_learners)==2
        epoch = int(adapter.native.epoch_marker.item())
        control['evaluate_calls'].append((epoch,output is not None))
        prevalidation = config.output_dir/'checkpoints'/f'train-epoch-{epoch:03d}'
        assert (prevalidation/'COMPLETE.json').is_file()
        assert (prevalidation/'state.pt').is_file()
        if control['fail_validation_epoch']==epoch:
            raise RuntimeError('unit validation interruption after checkpoint')
        if output is not None:
            output.write(json.dumps(dict(unit=True,epoch=epoch))+'\n')
        return dict(targets=2,supported=2,oov=0,
            population_sha256=('c' if control['population_change_epoch']==epoch else 'b')*64,
            native_bce=losses[epoch],probability_sha256=_state_hash(adapter))

    monkeypatch.setattr(selected,'_evaluate',evaluate)

    def run(*, epochs=20,resume=None,graph_condition=None,wrong_graph_grant=False,
            comparison_reference=None,reference_pin=None,encoding_args=None,purpose='bounded_engineering'):
        control['grants'] += 1
        prepared = {} if resume is None else dict(resume_checkpoint_sha256=selected.file_sha(resume))
        if comparison_reference is not None:
            prepared['comparison_reference_sha256']=reference_pin or selected.file_sha(comparison_reference)
        if encoding_args:
            for source,target in (('expected_encoding_sha256','encoding_sha256'),
                    ('expected_encoding_receipt_sha256','encoding_receipt_sha256'),
                    ('expected_train_window_manifest_sha256','train_window_manifest_sha256')):
                prepared[target]=encoding_args[source]
        candidate_id='A0'
        if graph_condition is not None:
            from knowledge_tracing.akt.research_junyi_graph import JunyiGraphPhaseSession

            def make(config,profile,encoding,view,condition):
                assert encoding is condition.encoding
                adapter=TinyGraphAdapter(config,encoding.native)
                adapter.set_phase(JunyiGraphPhaseSession(condition,view))
                return adapter

            monkeypatch.setattr(selected,'_make_selected_adapter',make)
            if not wrong_graph_grant:
                prepared['graph_condition_sha256']=graph_condition.identity
                candidate_id='A1_EXPERT'
        grant = dict(status='USER_APPROVED',binding=dict(candidate_id=candidate_id,phase='junyi_selected_only',
            config_sha256=authorization.config_hash(config),inputs_identity=inputs.identity,
            gate_sha256=gate['report_sha256'],runtime_sha256=selected.file_sha(runtime)),
            prepared_inputs=prepared,approval_reference='unit-test-fixture-only',
            workload_epochs=epochs,purpose=purpose)
        authorization_file = tmp_path/f'authorization-{control["grants"]:02d}.json'
        authorization_file.write_text(json.dumps(grant))
        runner=selected.run_a0_junyi_selected if graph_condition is None else selected.run_junyi_selected
        extra={} if graph_condition is None else dict(graph_condition=graph_condition)
        extra.update(encoding_args or {})
        return runner(config,profile,inputs,
            authorization_file=authorization_file,expected_authorization_sha256=selected.file_sha(authorization_file),
            runtime_report=runtime,lock_file=lock,resume_checkpoint=resume,
            expected_resume_sha256=None if resume is None else selected.file_sha(resume),
            comparison_reference_file=comparison_reference,
            expected_comparison_reference_sha256=None if comparison_reference is None else (
                reference_pin or selected.file_sha(comparison_reference)),**extra)

    return SimpleNamespace(run=run,control=control,config=config,inputs=inputs,
                           native_load=native_load,native_snapshot=native_snapshot,encoding=encoding,profile=profile)


def graph_condition(harness):
    from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition
    from knowledge_tracing.shared_kt import PrerequisiteGraph
    return JunyiGraphCondition(harness.encoding,PrerequisiteGraph.from_edges(('A',),()),'a'*64)


def test_graph_selection_shares_stopping_checkpoint_and_export_protocol(harness):
    condition=graph_condition(harness)
    result=harness.run(graph_condition=condition)
    assert result['status']=='JUNYI_A1_SELECTED_ONLY_COMPLETE'
    assert result['complete_epochs']==5 and result['selected_epoch']==2
    assert harness.control['graph_phases'].count('raw_selection10')==6
    assert harness.control['evaluate_calls'][-1]==(2,True)
    identity=json.loads((harness.config.output_dir/'run-manifest.json').read_text())
    assert identity['candidate_id']=='A1_EXPERT'
    allocation=json.loads((selected.PROJECT_ROOT/'docs/thesis_recovery/EXPERIMENT_ALLOCATION_V1.json').read_text())
    assert identity['candidate_id'] in {entry['id'] for entry in allocation['conditions_per_environment']}
    assert result['candidate_id']==identity['candidate_id']
    assert result['graph_condition_sha256']==condition.identity
    assert identity['batch_factory']['condition_sha256']==condition.identity
    assert identity['batch_factory']['phase_sha256']==harness.inputs.train.identity


def test_graph_selection_resumes_before_validation_without_retraining(harness):
    condition=graph_condition(harness)
    harness.control['fail_validation_epoch']=1
    with pytest.raises(RuntimeError,match='validation interruption'):
        harness.run(graph_condition=condition)
    harness.control['fail_validation_epoch']=None
    path=harness.config.output_dir/'checkpoints/train-epoch-001/state.pt'
    result=harness.run(epochs=1,resume=path,graph_condition=condition)
    assert result['status']=='PARTIAL_SELECTED_ONLY_NOT_FINAL'
    assert harness.control['train_calls']==[1]
    assert result['history'][0]['epoch']==1


def test_graph_selection_rejects_a0_authorization(harness):
    with pytest.raises(PermissionError,match='grant mismatch'):
        harness.run(graph_condition=graph_condition(harness),wrong_graph_grant=True)
    assert harness.control['models']==[]


def test_early_stopping_reloads_best_complete_checkpoint(harness):
    result = harness.run()
    assert result['status']=='JUNYI_A0_SELECTED_ONLY_COMPLETE'
    assert result['complete_epochs']==5 and result['selected_epoch']==2
    assert result['optimizer_steps']==10 and result['trained_targets']==20
    assert harness.control['train_calls']==[1,2,3,4,5]
    assert harness.control['evaluate_calls'][-1]==(2,True)
    assert result['validation']==result['history'][1]['validation']
    assert result['external_freeze'] is False and result['refit_completed'] is False
    assert (harness.config.output_dir/'COMPLETE.json').is_file()


def test_epoch_checkpoint_published_before_validation_failure(harness):
    harness.control['fail_validation_epoch']=1
    with pytest.raises(RuntimeError,match='validation interruption'):
        harness.run()
    path = harness.config.output_dir/'checkpoints/train-epoch-001/state.pt'
    identity = json.loads((harness.config.output_dir/'run-manifest.json').read_text())
    payload = harness.native_load(path,expected_identity=identity,device='cpu')
    assert payload['progress']['validation_complete'] is False
    assert payload['progress']['epoch_stats']['optimizer_steps']==2
    assert payload['progress']['optimizer_steps']==0
    assert int(payload['model_state_dict']['epoch_marker'])==1
    assert not (harness.config.output_dir/'COMPLETE.json').exists()


def test_resume_prevalidation_checkpoint_skips_completed_training(harness):
    harness.control['fail_validation_epoch']=1
    with pytest.raises(RuntimeError):
        harness.run()
    harness.control['fail_validation_epoch']=None
    checkpoint_path = harness.config.output_dir/'checkpoints/train-epoch-001/state.pt'
    result = harness.run(epochs=1,resume=checkpoint_path)
    assert result['status']=='PARTIAL_SELECTED_ONLY_NOT_FINAL'
    assert result['optimizer_steps']==2 and result['trained_targets']==4
    assert harness.control['train_calls']==[1]
    assert len(result['history'])==1 and result['history'][0]['epoch']==1
    assert (harness.config.output_dir/'checkpoints/epoch-001/COMPLETE.json').is_file()


def test_resume_postvalidation_restores_history_and_stopper(harness):
    first = harness.run(epochs=2)
    assert first['status']=='PARTIAL_SELECTED_ONLY_NOT_FINAL'
    path = harness.config.output_dir/'checkpoints/epoch-002/state.pt'
    result = harness.run(resume=path)
    assert result['selected_epoch']==2 and result['complete_epochs']==5
    assert harness.control['train_calls']==[1,2,3,4,5]
    assert [row['epoch'] for row in result['history']]==[1,2,3,4,5]
    assert result['optimizer_steps']==10 and result['trained_targets']==20


def test_partial_epoch_is_recoverable_and_never_selected_final(harness):
    harness.control['partial_epoch']=1
    result = harness.run(epochs=1)
    assert result['status']=='PARTIAL_SELECTED_ONLY_NOT_FINAL'
    assert result['selected_epoch'] is None and result['history']==[]
    assert result['optimizer_steps']==1 and result['trained_targets']==2
    output = harness.config.output_dir
    assert not (output/'COMPLETE.json').exists()
    path = output/'batch-recovery/unit-epoch001-step001.pt'
    assert path.is_file()
    durable = output/'checkpoints/unit-epoch001-step001'
    assert (durable/'COMPLETE.json').is_file()
    assert selected.file_sha(path)==selected.file_sha(durable/'state.pt')
    harness.control['partial_epoch']=None
    resumed = harness.run(epochs=1,resume=path)
    assert resumed['status']=='PARTIAL_SELECTED_ONLY_NOT_FINAL'
    assert resumed['optimizer_steps']==2 and resumed['trained_targets']==4
    assert len(resumed['history'])==1


def test_selection_population_drift_fails_before_final(harness):
    harness.control['population_change_epoch']=2
    with pytest.raises(ValueError,match='Selection population changed'):
        harness.run()
    output = harness.config.output_dir
    assert (output/'checkpoints/train-epoch-002/COMPLETE.json').is_file()
    assert not (output/'COMPLETE.json').exists()


def test_completed_logical_run_cannot_resume(harness):
    harness.run()
    path = harness.config.output_dir/'checkpoints/epoch-005/state.pt'
    with pytest.raises(ValueError,match='unfinished logical run'):
        harness.run(resume=path)
