"""Small CPU engineering fixtures only: <=2learners/12steps/4nodes, 0optimizer."""
from dataclasses import replace
import inspect

import pytest
import torch

from knowledge_tracing.gkt import GKTBinding,GKTKernelConfig
from knowledge_tracing.gkt.recurrent import (
    ChoResetBeforeGRU,EVIDENCE_ROLE,GRU_VARIANT,RECIPE_ID,
    GKTRecurrentState,GKTStaticRecurrentCandidate,
)

DTYPE=torch.float64


@pytest.fixture(autouse=True)
def bounded_cpu():
    threads=torch.get_num_threads();torch.set_num_threads(2)
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(42)
        yield
    torch.set_num_threads(threads)


def make(*,nodes=3,width=2,embedding=2,adjacency=None,dtype=DTYPE,**overrides):
    config=GKTKernelConfig(nodes,width,embedding,width,'static','concept',True,True)
    binding=GKTBinding('synthetic-recurrent-fixture','a'*64,tuple('ABCD'[:nodes]),'concept')
    if adjacency is None:
        adjacency=torch.full((nodes,nodes),1/(nodes-1),dtype=dtype,device='cpu');adjacency.fill_diagonal_(0)
    recipe=dict(recipe_id=RECIPE_ID,mlp_hidden_dim=3,normalization='none',dropout=0,
                initial_state_policy='zeros',gru_variant=GRU_VARIANT)
    recipe.update(overrides)
    return GKTStaticRecurrentCandidate(config,binding,adjacency,**recipe)


def bound(model):return dict(binding=model.binding,graph_sha256=model.graph_sha256)
def state(model,batch=1):return model.initial_state(batch,**bound(model))
def events(batch=2,steps=4):
    ids=torch.tensor([[0,1,2,0,1,2,0,1,2,0,1,2],[2,0,1,2,0,1,2,0,1,2,0,1]],device='cpu')[:batch,:steps]
    answers=torch.tensor([[0,1,1,0,1,0,1,0,1,0,0,1],[1,0,1,0,0,1,0,1,0,1,1,0]],device='cpu')[:batch,:steps]
    return ids,answers,torch.ones_like(ids,dtype=torch.bool)
def run(model,ids,answers,mask,initial=None):
    return model(ids,answers,mask,initial_state=initial,**bound(model))


def test_every_required_recipe_is_explicit_registered_and_not_fitted():
    model=make();parameters=dict(model.named_parameters());keys=set(model.state_dict())
    assert len(parameters)==26 and 'adjacency' in keys
    assert all(name in keys for name in parameters)
    for prefix in ('concept_embedding','interaction_embedding','self_mlp','out_mlp','in_mlp','erase','add','gru'):
        assert any(name.startswith(prefix+'.') for name in parameters)
    assert not any(isinstance(m,(torch.nn.BatchNorm1d,torch.nn.Dropout)) for m in model.modules())
    output=model.predict(state(model),torch.tensor([0]),**bound(model))
    assert output.evidence_role==EVIDENCE_ROLE and not hasattr(model,'fit')
    assert 'responses' not in inspect.signature(model.predict).parameters
    with pytest.raises(TypeError):GKTStaticRecurrentCandidate(model.config,model.binding,model.adjacency)


@pytest.mark.parametrize('changes',[{'recipe_id':'author-exact'}, {'normalization':'batchnorm'}, {'dropout':.5},
    {'dropout':True},{'initial_state_policy':'learned'}, {'gru_variant':'torch-reset-after'},
    {'mlp_hidden_dim':True},{'mlp_hidden_dim':0}])
def test_unapproved_recipe_rejected(changes):
    with pytest.raises(ValueError):make(**changes)


def test_message_state_dimension_must_match():
    model=make()
    with pytest.raises(ValueError,match='message_dim'):
        GKTStaticRecurrentCandidate(replace(model.config,message_dim=1),model.binding,model.adjacency,
            recipe_id=RECIPE_ID,mlp_hidden_dim=3,normalization='none',dropout=0,
            initial_state_policy='zeros',gru_variant=GRU_VARIANT)


def test_unary_erase_add_known_answer():
    model=make()
    with torch.no_grad():
        model.erase.weight.zero_();model.erase.bias.zero_();model.add.weight.zero_()
        model.add.bias.copy_(torch.tensor([.25,-.25],dtype=DTYPE))
    message=torch.tensor([[2.,-1.]],dtype=DTYPE)
    expected=message*.5+torch.tanh(torch.tensor([[.25,-.25]],dtype=DTYPE))
    torch.testing.assert_close(model.erase_add(message),expected,rtol=1e-12,atol=1e-12)


def test_literal_cho_gru_non_diagonal_reset_known_answer():
    gru=ChoResetBeforeGRU(2,dtype=DTYPE)
    matrices={
        'W_r':[[.2,-.1],[.3,.4]],'U_r':[[.5,.1],[-.2,.6]],
        'W_z':[[.1,.2],[-.4,.3]],'U_z':[[.2,-.3],[.1,.5]],
        'W_n':[[.7,-.2],[.4,.3]],'U_n':[[.2,.8],[-.6,.1]],
    }
    with torch.no_grad():
        for name,matrix in matrices.items():getattr(gru,name).weight.copy_(torch.tensor(matrix,dtype=DTYPE))
    x=torch.tensor([[.5,-.25]],dtype=DTYPE);h=torch.tensor([[.4,-.3]],dtype=DTYPE)
    # Scalar arithmetic independent of module.forward and matrix broadcasting.
    def mv(matrix,vector):return [sum(a*b for a,b in zip(row,vector)) for row in matrix]
    import math
    xv=x[0].tolist();hv=h[0].tolist()
    r=[1/(1+math.exp(-v)) for v in [a+b for a,b in zip(mv(matrices['W_r'],xv),mv(matrices['U_r'],hv))]]
    z=[1/(1+math.exp(-v)) for v in [a+b for a,b in zip(mv(matrices['W_z'],xv),mv(matrices['U_z'],hv))]]
    candidate=[math.tanh(a+b) for a,b in zip(mv(matrices['W_n'],xv),mv(matrices['U_n'],[a*b for a,b in zip(r,hv)]))]
    expected=torch.tensor([[a*b+(1-a)*c for a,b,c in zip(z,hv,candidate)]],dtype=DTYPE)
    torch.testing.assert_close(gru(x,h),expected,rtol=1e-12,atol=1e-12)
    reset_after=torch.tanh(gru.W_n(x)+torch.tensor([r],dtype=DTYPE)*gru.U_n(h))
    wrong=torch.tensor([z],dtype=DTYPE)*h+(1-torch.tensor([z],dtype=DTYPE))*reset_after
    assert not torch.allclose(expected,wrong,rtol=1e-4,atol=1e-4)
    assert all(layer.bias is None for layer in gru.children())


def test_full_network_asymmetric_messages_and_post_gru_disconnected_mask():
    adjacency=torch.tensor([[0,.2,0,0],[.7,0,.4,0],[0,.3,0,0],[0,0,0,0]],dtype=DTYPE)
    model=make(nodes=4,width=1,embedding=1,adjacency=adjacency)
    with torch.no_grad():
        for mlp,value in ((model.self_mlp,5),(model.out_mlp,10),(model.in_mlp,100)):
            mlp[0].weight.zero_();mlp[0].bias.zero_();mlp[2].weight.zero_();mlp[2].bias.fill_(value)
        model.add.weight.zero_();model.add.bias.fill_(.7)
        for layer in model.gru.children():layer.weight.fill_(.4)
    previous=state(model);values=previous.values.clone();values[0,3,0]=.75;previous=replace(previous,values=values)
    seen=[];hook=model.erase.register_forward_pre_hook(lambda module,args:seen.append(args[0].detach().clone()))
    try:updated=model.observe(previous,torch.tensor([1]),torch.tensor([1]),torch.tensor([True]),**bound(model))
    finally:hook.remove()
    torch.testing.assert_close(seen[0],torch.tensor([[[27.],[5.],[34.],[0.]]],dtype=DTYPE))
    assert torch.equal(updated.values[:,3],previous.values[:,3])
    direct=model.gru(model.erase_add(torch.zeros((1,1),dtype=DTYPE)),previous.values[:,3])
    assert not torch.allclose(direct,previous.values[:,3])  # Biased add would drift without AFTER-GRU mask.
    assert not torch.equal(updated.values[:,:3],previous.values[:,:3])


def test_empty_graph_updates_answered_only():
    model=make(adjacency=torch.zeros((3,3),dtype=DTYPE));previous=state(model)
    updated=model.observe(previous,torch.tensor([1]),torch.tensor([0]),torch.tensor([True]),**bound(model))
    assert torch.equal(updated.values[:,[0,2]],previous.values[:,[0,2]])
    assert not torch.equal(updated.values[:,1],previous.values[:,1])


@pytest.mark.parametrize('dtype',[torch.float32,torch.float64])
def test_sequence_matches_manual_steps_and_continuation(dtype):
    model=make(dtype=dtype);ids,answers,mask=events();output=run(model,ids,answers,mask)
    previous=state(model,2);scores=[]
    for time in range(ids.shape[1]):
        scores.append(model.predict(previous,ids[:,time],**bound(model)).logits)
        previous=model.observe(previous,ids[:,time],answers[:,time],mask[:,time],**bound(model))
    torch.testing.assert_close(output.logits,torch.stack(scores,1))
    torch.testing.assert_close(output.final_state.values,previous.values)
    assert output.history_counts.tolist()==[[0,1,2,3],[0,1,2,3]]
    prefix=run(model,ids[:,:2],answers[:,:2],mask[:,:2])
    tail=run(model,ids[:,2:],answers[:,2:],mask[:,2:],prefix.final_state)
    torch.testing.assert_close(tail.logits,output.logits[:,2:])
    torch.testing.assert_close(tail.final_state.values,output.final_state.values)


def test_current_and_future_answers_never_change_current_or_past_scores():
    model=make();ids,answers,mask=events(steps=12);baseline=run(model,ids,answers,mask)
    for time in range(12):
        changed=answers.clone();changed[:,time:]=1-changed[:,time:]
        actual=run(model,ids,changed,mask)
        torch.testing.assert_close(actual.logits[:,:time+1],baseline.logits[:,:time+1],rtol=0,atol=0)
    changed=answers.clone();changed[:,0]=1-changed[:,0]
    actual=run(model,ids,changed,mask)
    assert torch.max(torch.abs(actual.logits[:,1:]-baseline.logits[:,1:])).item()>1e-8


def test_learner_peers_permutation_and_fresh_state_are_independent():
    model=make();ids,answers,mask=events();baseline=run(model,ids,answers,mask)
    for learner in range(2):
        single=run(model,ids[learner:learner+1],answers[learner:learner+1],mask[learner:learner+1])
        torch.testing.assert_close(single.logits,baseline.logits[learner:learner+1],rtol=1e-12,atol=1e-12)
    changed=answers.clone();changed[1]=1-changed[1]
    torch.testing.assert_close(run(model,ids,changed,mask).logits[0],baseline.logits[0],rtol=0,atol=0)
    reverse=run(model,ids.flip(0),answers.flip(0),mask.flip(0))
    torch.testing.assert_close(reverse.logits.flip(0),baseline.logits)
    fresh1=state(model);fresh2=state(model)
    assert fresh1.values.data_ptr()!=fresh2.values.data_ptr()


def test_padding_noop_finite_first_target_and_empty_sequence():
    model=make();ids=torch.tensor([[999,0,-1,1],[2,999,0,-8]])
    answers=torch.tensor([[-99,1,-1,0],[0,-99,1,888]])
    mask=torch.tensor([[False,True,False,True],[True,False,True,False]])
    output=run(model,ids,answers,mask)
    assert torch.all(output.logits[~mask]==0) and torch.all(output.probabilities[~mask]==0)
    assert torch.isfinite(output.logits).all() and torch.isfinite(output.final_state.values).all()
    assert output.history_counts.tolist()==[[0,0,1,1],[0,1,1,2]]
    assert output.final_state.history_counts.tolist()==[2,2]
    torch.testing.assert_close(output.probabilities[torch.tensor([0,1]),torch.tensor([1,0])],torch.tensor([.5,.5],dtype=DTYPE))
    all_padding=run(model,ids,answers,torch.zeros_like(mask))
    assert torch.equal(all_padding.final_state.values,state(model,2).values)
    empty=run(model,ids[:,:0],answers[:,:0],mask[:,:0])
    assert empty.logits.shape==(2,0) and empty.final_state.history_counts.tolist()==[0,0]


def test_inputs_and_caller_adjacency_immutable():
    original=torch.tensor([[0,.5,.5],[.5,0,.5],[.5,.5,0]],dtype=DTYPE)
    model=make(adjacency=original);ids,answers,mask=events();previous=state(model,2)
    snapshots=[x.clone() for x in (original,ids,answers,mask,previous.values,previous.history_counts)]
    run(model,ids,answers,mask,previous)
    assert all(torch.equal(x,y) for x,y in zip((original,ids,answers,mask,previous.values,previous.history_counts),snapshots))
    original.fill_(0)
    assert torch.any(model.adjacency!=0)


@pytest.mark.parametrize('case',['domain','vocab','nodes','unit','graph','state_graph','state_recipe','state_domain','internal_graph','internal_kernel_graph','recipe'])
def test_domain_node_graph_recipe_mismatch_rejected(case):
    model=make();previous=state(model);kwargs=bound(model)
    if case=='domain':kwargs['binding']=replace(model.binding,domain='other')
    elif case=='vocab':kwargs['binding']=replace(model.binding,vocabulary_sha256='b'*64)
    elif case=='nodes':kwargs['binding']=replace(model.binding,node_ids=('C','B','A'))
    elif case=='unit':kwargs['binding']=replace(model.binding,node_unit='exercise_tag')
    elif case=='graph':kwargs['graph_sha256']='b'*64
    elif case=='state_graph':previous=replace(previous,graph_sha256='b'*64)
    elif case=='state_recipe':previous=replace(previous,recipe_sha256='b'*64)
    elif case=='state_domain':previous=replace(previous,binding=replace(model.binding,domain='other'))
    elif case=='internal_graph':model.adjacency[0,1]=.9
    elif case=='internal_kernel_graph':model._kernel._adjacency[0,1]=.9
    elif case=='recipe':model.normalization='other'
    with pytest.raises(ValueError):model.predict(previous,torch.tensor([0]),**kwargs)


@pytest.mark.parametrize('case',['unknown','negative','float_ids','float_response','nonbinary','float_mask','bad_batch','nonfinite_state','negative_count','nonfinite_parameter'])
def test_invalid_inputs_rejected(case):
    model=make();ids,answers,mask=events();previous=state(model,2)
    if case=='unknown':ids=ids.clone();ids[0,0]=3
    elif case=='negative':ids=ids.clone();ids[0,0]=-1
    elif case=='float_ids':ids=ids.double()
    elif case=='float_response':answers=answers.double()
    elif case=='nonbinary':answers=answers.clone();answers[0,0]=2
    elif case=='float_mask':mask=mask.double()
    elif case=='bad_batch':previous=state(model,1)
    elif case=='nonfinite_state':previous.values[0,0,0]=float('nan')
    elif case=='negative_count':previous.history_counts[0]=-1
    elif case=='nonfinite_parameter':
        with torch.no_grad():model.add.bias[0]=float('inf')
    with pytest.raises(ValueError):run(model,ids,answers,mask,previous)


def test_every_registered_parameter_path_has_finite_nonzero_gradients():
    model=make();ids,answers,mask=events(steps=6);result=run(model,ids,answers,mask)
    loss=result.logits.square().sum()+result.final_state.values.square().sum()
    loss.backward()
    for name,parameter in model.named_parameters():
        assert parameter.grad is not None,name
        assert torch.isfinite(parameter.grad).all(),name
        assert parameter.grad.abs().sum().item()>0,name
    assert not model.adjacency.requires_grad and model.adjacency.grad is None


def test_active_counter_overflow_rejected_and_padding_counter_unchanged():
    model=make();previous=state(model)
    previous.history_counts[0]=torch.iinfo(torch.long).max
    with pytest.raises(ValueError,match='counter'):
        model.observe(previous,torch.tensor([0]),torch.tensor([1]),torch.tensor([True]),**bound(model))
    updated=model.observe(previous,torch.tensor([-1]),torch.tensor([-1]),torch.tensor([False]),**bound(model))
    assert torch.equal(updated.values,previous.values)
    assert torch.equal(updated.history_counts,previous.history_counts)


def test_cpu_constructor_and_kernel_helpers_ignore_meta_default_device():
    old=torch.get_default_device()
    try:
        torch.set_default_device('meta')
        model=make();previous=state(model)
        ids=torch.tensor([0],device='cpu');answers=torch.tensor([1],device='cpu');valid=torch.tensor([True],device='cpu')
        output=model.predict(previous,ids,**bound(model))
        updated=model.observe(previous,ids,answers,valid,**bound(model))
        assert output.logits.device.type==updated.values.device.type=='cpu'
    finally:torch.set_default_device(old)
