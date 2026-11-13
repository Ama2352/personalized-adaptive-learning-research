"""Validation batch được bind vào grant, checkpoint identity và export."""
import io
import json
from dataclasses import replace

import numpy as np
import pytest
import torch

from test_junyi_selected_runner import harness
from test_prediction_batch import FakeAdapter,learner
from knowledge_tracing.akt import research_junyi_selection as selected
from test_junyi_graph_model import setup
from test_junyi_comparison_admission import matched


def test_evaluation_batch128_keeps_metrics_population_and_export():
    students=[learner(f'u{index:03d}',['A','B','OOV','A'] if index==1 else ['A','B'],
        start_row=index*10+1) for index in range(131)]
    total=sum(len(student.events) for student in students)
    old_output,new_output=io.StringIO(),io.StringIO()
    expected=selected._evaluate(FakeAdapter(batch_size=128),iter(students),total,output=old_output)
    adapter=FakeAdapter(batch_size=128)
    actual=selected._evaluate(adapter,iter(students),total,output=new_output,batch_size=128)
    assert actual==expected
    assert new_output.getvalue()==old_output.getvalue()
    records=[json.loads(line) for line in new_output.getvalue().splitlines()]
    assert len(records)==total and actual['oov']==1
    assert all(row['global_rank'] in range(4) for row in records)
    assert max(map(len,adapter.calls))==128


def test_selected_runner_uses_same_batch_for_validation_and_best_export(harness):
    result=harness.run(validation_batch_size=4)
    assert result['validation_batch_size']==4
    assert result['prediction_implementation']=='batched_windows_v1_batch4'
    assert harness.control['validation_batches']==[4]*6
    identity=json.loads((harness.config.output_dir/'run-manifest.json').read_text())
    assert identity['validation_batch_size']==4
    assert identity['prediction_implementation']==result['prediction_implementation']


def test_validation_batch_requires_matching_grant(harness):
    with pytest.raises(PermissionError,match='grant mismatch'):
        harness.run(validation_batch_size=4,bind_validation_batch=False)
    assert not harness.control['models'] and not harness.control['train_calls']


def test_batched_execution_rejects_legacy_comparison_reference(matched):
    harness=matched.harness
    with pytest.raises(ValueError,match='batching differs'):
        harness.run(comparison_reference=matched.reference_path,encoding_args=matched.encoding_args,
            validation_batch_size=4)
    assert not harness.control['models'] and not harness.control['train_calls']


def test_batched_execution_can_bind_its_own_verified_reference(matched):
    reference=dict(matched.reference,prediction_implementation='batched_windows_v1_batch4')
    matched.write_reference(reference)
    terminal=matched.harness.run(comparison_reference=matched.reference_path,
        encoding_args=matched.encoding_args,validation_batch_size=4)
    assert terminal['comparison_population_matched'] is True
    assert terminal['validation_batch_size']==4


@pytest.mark.parametrize('batch',[True,0,-1,5,129,1.5])
def test_invalid_validation_batch_stops_before_model(harness,batch):
    with pytest.raises(ValueError,match='Validation batch'):
        harness.run(validation_batch_size=batch)
    assert not harness.control['models']


def test_switching_batch_method_during_resume_is_rejected(harness):
    harness.control['fail_validation_epoch']=1
    with pytest.raises(RuntimeError,match='interruption'):
        harness.run()
    checkpoint=harness.config.output_dir/'checkpoints/train-epoch-001/state.pt'
    with pytest.raises(ValueError,match='identical unfinished logical run'):
        harness.run(resume=checkpoint,validation_batch_size=4)
    assert harness.control['train_calls']==[1]


@pytest.mark.parametrize('graph',[False,True])
def test_native_predictions_preserve_metadata_state_and_causality(setup,graph):
    from knowledge_tracing.akt.model import AKTAdapter
    from knowledge_tracing.akt.prediction import iter_predictions
    from knowledge_tracing.akt.prediction_batch import iter_predictions_batched
    from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView
    from knowledge_tracing.akt.research_junyi_graph import JunyiGraphPhaseSession
    from knowledge_tracing.akt.research_junyi_graph_model import JunyiGraphAKTAdapter
    from knowledge_tracing.akt.types import KTEvent,LearnerEvents
    condition=setup['condition']()
    roles=setup['train'].roles
    view=JunyiPhaseView(roles,'raw_selection10',roles.selection_users,roles.identity)
    config=replace(setup['config'],batch_size=128)
    torch.manual_seed(42)
    if graph:
        adapter=JunyiGraphAKTAdapter(config=config,encoding=setup['encoding'],condition=condition,
            phase=JunyiGraphPhaseSession(condition,view))
        with torch.no_grad():
            adapter.native.alpha.fill_(1.)
    else:
        adapter=AKTAdapter(config,setup['encoding'].native)
    adapter.checkpoint_id='native-validation-parity-fixture'
    students=[]
    for index,(user,size) in enumerate(zip(view.users,(1,101,205,7))):
        events=tuple(KTEvent(user,'OOV' if index==2 and rank==17 else ('A','C')[rank%2],
            rank+1,index*1000+rank+1,rank%2,0,0) for rank in range(size))
        students.append(LearnerEvents(user,0,events))
    state={name:value.clone() for name,value in adapter.native.state_dict().items()}
    rng=torch.get_rng_state().clone()
    before=list(iter_predictions(adapter,students))
    after=list(iter_predictions_batched(adapter,students,batch_size=128))
    assert [replace(row,prediction=None) for row in before]==[replace(row,prediction=None) for row in after]
    np.testing.assert_allclose([row.prediction for row in before if row.prediction is not None],
        [row.prediction for row in after if row.prediction is not None],atol=1e-6,rtol=1e-6)
    assert all(torch.equal(value,adapter.native.state_dict()[name]) for name,value in state.items())
    assert torch.equal(rng,torch.get_rng_state())
    changed=[]
    for student in students:
        changed.append(replace(student,events=tuple(replace(event,correct=1-event.correct)
            if index>=50 else event for index,event in enumerate(student.events))))
    perturbed=list(iter_predictions_batched(adapter,changed,batch_size=128))
    ranks={}
    for original,altered in zip(after,perturbed):
        rank=ranks.get(original.user_id,0)
        ranks[original.user_id]=rank+1
        if rank<=50:
            assert original.prediction==altered.prediction
