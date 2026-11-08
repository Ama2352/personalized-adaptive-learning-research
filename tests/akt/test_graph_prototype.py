"""Pinned native A0–A3 toy forward/backward; zero optimizer steps or model fit."""
from dataclasses import replace
import hashlib

import numpy as np
import pytest
import torch
from torch import nn

from knowledge_tracing.akt.config import PROJECT_ROOT, load_config
from knowledge_tracing.akt.model import AKTAdapter
from knowledge_tracing.akt import graph_prototype as graph_proto
from knowledge_tracing.graph_context import EdgeConfidence
from knowledge_tracing.akt.simulator_data import SimulatorShard,fit_simulator_encoding
from knowledge_tracing.shared_kt import PrerequisiteGraph
from knowledge_tracing.simulator_bridge import SimulatorBank,SimulatorItem,ItemQuery,Observation,identity_hash
from knowledge_tracing.simulator_data import SimulatorSplitPlan,ROLES,ObservableTrajectory


class CountingLinear(nn.Linear):
    def __init__(self):
        super().__init__(1,2)
        self.calls=0
        with torch.no_grad():
            self.weight.copy_(torch.tensor([[.25],[-.125]]))
            self.bias.copy_(torch.tensor([.1,-.1]))

    def forward(self,value):
        self.calls+=1
        return super().forward(value)


def toy(rename=None):
    rename=rename or {"A":"A","B":"B","C":"C"}
    bank=SimulatorBank("synthetic-akt-graph-engineering-toy-v1",tuple(
        SimulatorItem(i,rename[c],0.) for i,c in (("a","A"),("b","B"),("c","C"),("z","C"))))
    plan=SimulatorSplitPlan("graph-prototype-handmade-only",42,tuple((r,2 if r=="train" else 1) for r in ROLES))
    def shard(role,sequences):
        trajectories=[]
        for user,(assignment,items) in enumerate(zip(plan.assignments(role),sequences,strict=True)):
            observations=tuple(Observation(ItemQuery(item,rank+1,100*(1+user)+(1000 if role!="train" else 0)+rank),
                                           (rank+user)%2) for rank,item in enumerate(items))
            trajectories.append(ObservableTrajectory(assignment.learner_id,plan.identity,identity_hash(bank.identity),
                                "handmade-graph-engineering-only",observations))
        return SimulatorShard(plan,bank,role,12,tuple(trajectories))
    train=shard("train",("abacbc","baac"))
    selection=shard("selection",("abczac",))
    graph=PrerequisiteGraph.from_edges(list(rename.values()),[(rename["A"],rename["C"]),(rename["B"],rename["C"])])
    cfg=replace(load_config(PROJECT_ROOT/"experiments/akt/configs/smoke.json"),batch_size=4,threads=2)
    return cfg,train,selection,fit_simulator_encoding(train),graph


def build(cfg,train,encoding,graph,variant="A1"):
    with torch.random.fork_rng(devices=[]):
        with torch.device("cpu"):
            message=CountingLinear() if variant=="A1" else None
            readout=nn.Parameter(torch.tensor([.7,-.4])) if variant=="A1" else None
        torch.manual_seed(42)
        # Real prototype constructor must override ambient meta before native allocation.
        with torch.device("meta"):
            result=graph_proto.GraphAKTPrototype(config=cfg,train=train,encoding=encoding,graph=graph,
                spec=graph_proto.GraphPrototypeSpec(variant,graph_proto.RECIPE,"Parent approved A0/A1 toy engineering 20261108","effective_window"),
                message_module=message,readout=readout)
            assert torch.empty(1).device.type=="meta"
            assert all(p.device.type=="cpu" for p in result.parameters())
        return result


def labels(batch,shard):
    lookup={(t.learner_id,o.query.source_row):o.correct for t in shard.trajectories for o in t.observations}
    result=torch.full(batch.base.q_data.shape,-1.,dtype=torch.float32,device="cpu")
    for b,row in enumerate(batch.contexts):
        for local,q in enumerate(row):
            if q is not None:result[b,local]=lookup[q.learner_id,q.source_row]
    return result


def native_hash(native):
    return {k:hashlib.sha256(v.detach().cpu().numpy().tobytes()).hexdigest() for k,v in native.state_dict().items()}


@pytest.fixture(scope="module")
def bundle():
    cfg,train,selection,encoding,graph=toy()
    with torch.random.fork_rng(devices=[]),torch.device("cpu"):
        torch.manual_seed(42)
        baseline=AKTAdapter(cfg,encoding.exercise_encoding()).native
    proto=build(cfg,train,encoding,graph)
    batch=graph_proto.prepare_graph_batch(train,encoding,config=cfg,graph=graph)
    return cfg,train,selection,encoding,graph,baseline,proto,batch


def test_fresh_backbone_initialization_identity_and_thin_visible_output_parity(bundle):
    _,train,_,_,_,baseline,proto,batch=bundle
    assert native_hash(proto.native)==native_hash(baseline)
    target=labels(batch,train)
    result=baseline(batch.base.q_data,batch.base.qa_data,target)
    h,z=proto._features(batch.base.q_data,batch.base.qa_data)
    assert h.shape==(*batch.base.q_data.shape,32) and z.shape==(batch.base.q_data.numel(),)
    assert h.requires_grad and z.requires_grad
    assert torch.equal(torch.sigmoid(z),result[1])
    mask=target.reshape(-1)>-.9
    loss=nn.BCEWithLogitsLoss(reduction="none")(z[mask],target.reshape(-1)[mask]).sum()+0.
    assert torch.equal(loss,result[0]) and int(result[2])==10
    # h/z are inspected for shape/source contract; native does not return them.


def test_disabled_exact_native_outputs_and_backbone_gradients(bundle):
    _,train,_,_,_,baseline,proto,batch=bundle
    baseline.zero_grad(set_to_none=True);proto.zero_grad(set_to_none=True)
    before=proto.message_module.calls
    target=labels(batch,train)
    expected=baseline(batch.base.q_data,batch.base.qa_data,target)
    actual=proto(batch,target,enabled=False)
    assert all(torch.equal(a,b) for a,b in zip(actual,expected,strict=True))
    expected[0].backward();actual[0].backward()
    for (_,left),(_,right) in zip(baseline.named_parameters(),proto.native.named_parameters(),strict=True):
        assert (left.grad is None)==(right.grad is None)
        if left.grad is not None:assert torch.equal(left.grad,right.grad)
    assert proto.message_module.calls==before and proto.readout.grad is None
    assert all(p.grad is None for p in proto.message_module.parameters())


def test_active_joint_gradients_and_same_forward_mixed_inactive_probabilities(bundle):
    _,train,_,_,_,_,proto,batch=bundle
    proto.zero_grad(set_to_none=True)
    state=native_hash(proto.native)
    details=proto.forward_details(batch,labels(batch,train))
    assert details.applied_mask.any() and (~details.applied_mask).any()
    assert torch.equal(details.native_result[1][~details.applied_mask],details.base_probabilities[~details.applied_mask])
    assert torch.any(details.native_result[1][details.applied_mask]!=details.base_probabilities[details.applied_mask])
    details.native_result[0].backward()
    assert any(p.grad is not None and torch.any(p.grad!=0) for p in proto.native.parameters())
    assert all(p.grad is not None and torch.isfinite(p.grad).all() and torch.any(p.grad!=0) for p in proto.message_module.parameters())
    assert proto.readout.grad is not None and torch.isfinite(proto.readout.grad).all() and torch.any(proto.readout.grad!=0)
    assert all(p.grad is None or torch.isfinite(p.grad).all() for p in proto.parameters())
    assert native_hash(proto.native)==state  # backward only, no optimizer


@pytest.mark.parametrize("mode",["A0","empty","no_parent_support"])
@pytest.mark.parametrize("ambient_threads",[1,2])
def test_whole_batch_native_bypass_for_each_supported_fallback(bundle,mode,ambient_threads):
    cfg,train,selection,encoding,graph,baseline,proto,_=bundle
    previous_threads=torch.get_num_threads()
    hooks=[]
    try:
        torch.set_num_threads(ambient_threads)
        if mode=="A0":
            model=build(cfg,train,encoding,graph,"A0")
            shard=train
        elif mode=="empty":
            graph=PrerequisiteGraph.from_edges(graph.nodes,[])
            model=build(cfg,train,encoding,graph)
            shard=train
        else:
            trajectory=selection.trajectories[0]
            shard=replace(selection,trajectories=(replace(trajectory,observations=tuple(
                replace(o,query=replace(o.query,item_id="c")) for o in trajectory.observations)),))
            model=proto
        batch=graph_proto.prepare_graph_batch(shard,encoding,config=cfg,graph=graph)
        before=model.message_module.calls if model.message_module is not None else 0
        target=labels(batch,shard)
        native_threads=[]
        control_threads=[]
        hooks.append(model.native.register_forward_pre_hook(
            lambda module,args:native_threads.append(torch.get_num_threads())))
        hooks.append(baseline.register_forward_pre_hook(
            lambda module,args:control_threads.append(torch.get_num_threads())))
        actual=model.forward_details(batch,target)
        assert torch.get_num_threads()==ambient_threads
        # The wrapper scopes CPU threads; exact control uses the same thread contract.
        try:
            torch.set_num_threads(cfg.threads)
            with torch.device("cpu"):
                expected=baseline(batch.base.q_data,batch.base.qa_data,target)
        finally:
            torch.set_num_threads(ambient_threads)
        assert torch.get_num_threads()==ambient_threads
        assert native_threads==control_threads==[cfg.threads]
        assert all(torch.equal(a,b) for a,b in zip(actual.native_result,expected,strict=True))
        assert actual.hidden is None and not actual.applied_mask.any()
        if model.message_module is not None:assert model.message_module.calls==before
    finally:
        for hook in hooks:hook.remove()
        torch.set_num_threads(previous_threads)


def test_current_future_label_perturbations_no_current_probability_leak_and_past_positive_control(bundle):
    cfg,_,selection,encoding,graph,_,proto,_=bundle
    # Known item sequence without OOV keeps direct target-to-source comparison simple.
    t=selection.trajectories[0]
    t=replace(t,observations=tuple(replace(o,query=replace(o.query,item_id=i)) for o,i in zip(t.observations,"abacbc",strict=True)))
    original=replace(selection,trajectories=(t,))
    changed=replace(original,trajectories=(replace(t,observations=tuple(
        replace(o,correct=1-o.correct) if rank>=3 else o for rank,o in enumerate(t.observations))),))
    first=graph_proto.prepare_graph_batch(original,encoding,config=cfg,graph=graph)
    second=graph_proto.prepare_graph_batch(changed,encoding,config=cfg,graph=graph)
    p=proto(first)[1];q=proto(second)[1]
    assert torch.equal(p[:4],q[:4])
    # Explicit current loss label changes only loss, never current predictions.
    target=labels(first,original)
    assert torch.equal(proto(first,target)[1],proto(first,1-target)[1])
    past=replace(original,trajectories=(replace(t,observations=(replace(t.observations[0],correct=1-t.observations[0].correct),*t.observations[1:])),))
    third=graph_proto.prepare_graph_batch(past,encoding,config=cfg,graph=graph)
    assert torch.any(proto(third)[1][1:]!=p[1:])


def test_batch_padding_peer_independence_and_permuted_windows(bundle):
    cfg,train,_,encoding,graph,_,proto,batch=bundle
    together=proto(batch)[1].reshape(batch.base.q_data.shape)
    for row,window in enumerate(batch.window_ids):
        single=graph_proto.prepare_graph_batch(train,encoding,config=cfg,graph=graph,window_ids=(window,))
        count=int(single.base.valid_mask.sum())
        assert torch.allclose(proto(single)[1][:count],together[row,:count],atol=1e-7,rtol=0)
    reverse=graph_proto.prepare_graph_batch(train,encoding,config=cfg,graph=graph,window_ids=tuple(reversed(batch.window_ids)))
    assert torch.equal(proto(reverse)[1].reshape(reverse.base.q_data.shape).flip(0),together)


def test_oov_barrier_preserves_global_rank_and_history_window_without_graph_rescue(bundle):
    cfg,_,selection,encoding,graph,_,proto,_=bundle
    batch=graph_proto.prepare_graph_batch(selection,encoding,config=cfg,graph=graph)
    assert [u[2] for u in batch.unseen_targets]==[3]
    assert all(query.evidence.target_fitted for row in batch.contexts for query in row if query)
    later=[query for row in batch.contexts for query in row if query and query.global_rank>=4]
    assert [query.global_rank for query in later]==[4,5]
    assert all(query.evidence.effective_start==4 for query in later)
    assert later[-1].evidence.observed_rows==(later[0].source_row,)
    assert torch.isfinite(proto(batch)[1]).all()


def test_neutral_zero_readout_is_allowed_not_a_positive_effect_requirement(bundle):
    _,_,_,_,_,_,proto,batch=bundle
    saved=proto.readout.detach().clone()
    try:
        with torch.no_grad():proto.readout.zero_()
        details=proto.forward_details(batch)
        assert torch.equal(details.native_result[1],details.base_probabilities)
    finally:
        with torch.no_grad():proto.readout.copy_(saved)


def test_concept_renaming_equivariance_uses_explicit_bank_mapping_not_numeric_transfer(bundle):
    _,_,_,_,_,_,proto,batch=bundle
    cfg,train,_,encoding,graph=toy({"A":"Y","B":"X","C":"Z"})
    renamed=build(cfg,train,encoding,graph)
    changed=graph_proto.prepare_graph_batch(train,encoding,config=cfg,graph=graph)
    assert torch.equal(proto(batch)[1],renamed(changed)[1])
    with pytest.raises(ValueError,match="binding"):
        proto(changed)


@pytest.mark.parametrize("case",["tensor","context","graph","vocab","oracle"])
def test_batch_identity_drift_and_cross_domain_confidence_guards(bundle,case):
    _,_,_,_,_,_,proto,batch=bundle
    if case=="tensor":
        base=replace(batch.base,q_data=batch.base.q_data.clone())
        base.q_data[0,0]=2
        changed=replace(batch,base=base)
    elif case in {"graph","vocab"}:
        changed=replace(batch,model_binding="wrong-"+case)
    else:
        rows=[list(r) for r in batch.contexts]
        old=rows[0][0]
        evidence=replace(old.evidence,confidence_kind="oracle_label") if case=="oracle" else replace(old.evidence,effective_start=99)
        rows[0][0]=replace(old,evidence=evidence)
        changed=replace(batch,contexts=tuple(tuple(r) for r in rows))
    with pytest.raises(ValueError):proto(changed)


def test_unknown_variant_and_implicit_gate_recipe_are_rejected():
    with pytest.raises(ValueError,match="unknown variant"):
        graph_proto.GraphPrototypeSpec("unknown",graph_proto.RECIPE,"engineering","effective_window")
    with pytest.raises(ValueError,match="explicit engineering gate"):
        graph_proto.GraphPrototypeSpec("A3",graph_proto.RECIPE,"engineering","effective_window")


def test_scope_limits_and_no_full_history_or_junyi_domain(bundle):
    cfg,train,_,encoding,graph,_,_,_=bundle
    with pytest.raises(ValueError,match="matched-window"):
        graph_proto.GraphPrototypeSpec("A1",graph_proto.RECIPE,"engineering","full_history")
    for altered in (replace(cfg,dropout=.1),replace(cfg,context=1),replace(cfg,device="cuda")):
        with pytest.raises(ValueError):graph_proto.prepare_graph_batch(train,encoding,config=altered,graph=graph)
    alien=replace(train.bank,environment_id="Junyi-not-Grade10")
    with pytest.raises(ValueError):
        changed=replace(train,bank=alien)
        graph_proto.prepare_graph_batch(changed,encoding,config=cfg,graph=graph)


def test_cpu_context_under_meta_and_mocked_cuda_rejection(bundle,monkeypatch):
    cfg,train,_,encoding,graph,_,proto,_=bundle
    with torch.device("meta"):
        batch=graph_proto.prepare_graph_batch(train,encoding,config=cfg,graph=graph)
        output=proto(batch)
        assert torch.empty(1).device.type=="meta" and output[1].device.type=="cpu"
    monkeypatch.setattr(torch.cuda,"is_available",lambda:True)
    with pytest.raises(RuntimeError,match="CUDA hidden"):
        graph_proto.prepare_graph_batch(train,encoding,config=cfg,graph=graph)
    with pytest.raises(RuntimeError,match="CUDA hidden"):
        proto(batch)


def test_actual_source_dependency_inventory_and_simulated_drift_reject_before_forward(bundle,monkeypatch):
    cfg,_,_,_,_,_,proto,batch=bundle
    before=graph_proto._source_inventory(cfg)
    required={"src/knowledge_tracing/graph_context.py","src/knowledge_tracing/graph_augmentation.py",
              "src/knowledge_tracing/simulator_bridge.py","src/knowledge_tracing/simulator_data.py",
              "src/knowledge_tracing/shared_kt.py","src/knowledge_tracing/akt/encoding.py",
              "src/knowledge_tracing/akt/online.py","src/knowledge_tracing/akt/windows.py",
              "src/knowledge_tracing/akt/tensors.py","artifacts/akt/dependencies/upstream/akt.py"}
    assert required<=before.keys()
    assert not any(key.startswith("tests/") for key in before)
    original=graph_proto._source_inventory
    monkeypatch.setattr(graph_proto,"_source_inventory",lambda config:{**original(config),"src/knowledge_tracing/akt/resources.py":"0"*64})
    calls=proto.message_module.calls
    with pytest.raises(ValueError,match="source drift"):
        proto(batch)
    assert proto.message_module.calls==calls


def test_a0_cannot_register_unvalidated_branch_parameters(bundle):
    cfg,train,_,encoding,graph,_,_,_=bundle
    spec=graph_proto.GraphPrototypeSpec("A0",graph_proto.RECIPE,"engineering","effective_window")
    with pytest.raises(ValueError,match="A0 requires no"):
        graph_proto.GraphAKTPrototype(config=cfg,train=train,encoding=encoding,graph=graph,spec=spec,
                                      message_module=CountingLinear(),readout=nn.Parameter(torch.ones(2)))


def weighted_bundle(variant="A2", values=(.25,.75), kind="structural_score"):
    cfg,train,selection,encoding,graph=toy()
    confidence=EdgeConfidence(kind,tuple((p,c,v) for (p,c),v in zip(graph.edges,values,strict=True)),
        identity_hash({"role":"handmade-engineering-not-fitted-not-calibrated","values":values}),
        "train" if kind=="estimated_probability" else None)
    recipe=graph_proto.GATE_RECIPE if variant=="A3" else None
    with torch.random.fork_rng(devices=[]),torch.device("cpu"):
        message=CountingLinear();readout=nn.Parameter(torch.tensor([.7,-.4]))
        gate=nn.Linear(4,1) if variant=="A3" else None
        if gate is not None:
            with torch.no_grad():gate.weight.fill_(.2);gate.bias.fill_(-.1)
        torch.manual_seed(42)
        model=graph_proto.GraphAKTPrototype(config=cfg,train=train,encoding=encoding,graph=graph,
            spec=graph_proto.GraphPrototypeSpec(variant,graph_proto.RECIPE,"user sustained engineering; toy only",
                "effective_window",gate_feature_recipe=recipe),message_module=message,readout=readout,
            confidence=confidence,gate_module=gate)
    batch=graph_proto.prepare_graph_batch(train,encoding,config=cfg,graph=graph,confidence=confidence,
                                         gate_feature_recipe=recipe)
    return cfg,train,selection,encoding,graph,confidence,model,batch


@pytest.mark.parametrize("variant",["A2","A3"])
def test_weighted_and_gated_gradients_with_independent_signed_residual_formula(variant):
    _,train,_,_,_,_,model,batch=weighted_bundle(variant)
    before=native_hash(model.native)
    detail=model.forward_details(batch,labels(batch,train))
    assert detail.applied_mask.any() and (~detail.applied_mask).any()
    flat=[q for row in batch.contexts for q in row]
    for i,query in enumerate(flat):
        if not detail.applied_mask[i]:
            assert torch.equal(detail.native_result[1][i],detail.base_probabilities[i])
            continue
        parents=query.evidence.parents
        # Explicit arithmetic, independent of apply_graph_residual/feature helper.
        residual=0.
        for p in parents:
            if p.support:
                x=p.mean_observed_correctness
                residual+=p.confidence*(.7*(.25*x+.1)-.4*(-.125*x-.1))
        mass=sum(p.confidence for p in parents if p.support)
        residual=residual/max(1.,mass)*float(detail.gate_values[i])
        assert float(detail.augmented_logits[i]-detail.base_logits[i])==pytest.approx(residual,abs=1e-7)
        assert detail.confidence_mass[i]==mass
    detail.native_result[0].backward()
    for module in (model.native,model.message_module,model.gate_module):
        if module is not None:
            assert any(p.grad is not None and torch.any(p.grad!=0) for p in module.parameters())
            assert all(p.grad is None or torch.isfinite(p.grad).all() for p in module.parameters())
    assert model.readout.grad is not None and torch.any(model.readout.grad!=0)
    assert native_hash(model.native)==before  # No optimizer or fitting.


def test_uniform_a2_matches_a1_without_changing_backbone_or_branch_weights(bundle):
    _,train,_,_,_,_,fixed,fixed_batch=bundle
    _,_,_,_,_,_,weighted,weighted_batch=weighted_bundle("A2",(1.,1.),"fixed_uniform")
    assert native_hash(fixed.native)==native_hash(weighted.native)
    assert all(torch.equal(a,b) for a,b in zip(fixed(fixed_batch,labels(fixed_batch,train)),
                                              weighted(weighted_batch,labels(weighted_batch,train)),strict=True))


@pytest.mark.parametrize("variant",["A2","A3"])
@pytest.mark.parametrize("disable",[True,False])
@pytest.mark.parametrize("ambient_threads",[1,2])
def test_weighted_disable_or_all_zero_confidence_exact_native_tuple_and_gradients(variant,disable,ambient_threads):
    cfg,train,_,_,_,_,model,batch=weighted_bundle(variant,(.25,.75) if disable else (0.,0.))
    previous=torch.get_num_threads()
    try:
        target=labels(batch,train)
        torch.set_num_threads(cfg.threads)
        expected=model.native(batch.base.q_data,batch.base.qa_data,target)
        expected[0].backward()
        gradients={k:None if p.grad is None else p.grad.clone() for k,p in model.native.named_parameters()}
        model.zero_grad(set_to_none=True)
        calls=model.message_module.calls
        torch.set_num_threads(ambient_threads)
        actual=model.forward_details(batch,target,enabled=not disable)
        assert torch.get_num_threads()==ambient_threads
        assert all(torch.equal(a,b) for a,b in zip(actual.native_result,expected,strict=True))
        assert actual.hidden is None and actual.gate_values is None and not actual.applied_mask.any()
        torch.set_num_threads(cfg.threads)
        actual.native_result[0].backward()
        for k,p in model.native.named_parameters():
            assert (p.grad is None)==(gradients[k] is None)
            if p.grad is not None:assert torch.equal(p.grad,gradients[k])
        assert model.message_module.calls==calls and model.readout.grad is None
        assert all(p.grad is None for module in (model.message_module,model.gate_module) if module is not None
                   for p in module.parameters())
    finally:
        torch.set_num_threads(previous)


def test_engineering_gate_feature_population_and_normalization_are_explicit():
    _,_,_,_,_,_,model,batch=weighted_bundle("A3")
    query=next(q for row in batch.contexts for q in row if q is not None and any(p.support for p in q.evidence.parents))
    parents=query.evidence.parents;support=sum(p.support for p in parents)
    expected=(support/(1+support),.5,.0625,sum(p.support>0 for p in parents)/2)
    assert graph_proto.gate_features(query.evidence)==expected
    detail=model.forward_details(batch)
    for i,q in enumerate(q for row in batch.contexts for q in row):
        if detail.applied_mask[i]:
            x=graph_proto.gate_features(q.evidence)
            expected_gate=1/(1+np.exp(-(.2*sum(x)-.1)))
            assert float(detail.gate_values[i])==pytest.approx(expected_gate,abs=1e-7)


@pytest.mark.parametrize("variant",["A2","A3"])
def test_confidence_and_gate_identity_drift_fail_closed_even_when_disabled(variant):
    cfg,train,_,encoding,graph,confidence,model,_=weighted_bundle(variant)
    changed=replace(confidence,provenance_sha256="a"*64)
    batch=graph_proto.prepare_graph_batch(train,encoding,config=cfg,graph=graph,confidence=changed,
        gate_feature_recipe=graph_proto.GATE_RECIPE if variant=="A3" else None)
    with pytest.raises(ValueError,match="binding"):model(batch,enabled=False)
    oracle=EdgeConfidence("oracle_label",tuple((p,c,1.) for p,c in graph.edges),"b"*64)
    with pytest.raises(ValueError,match="nonoracle"):
        graph_proto.prepare_graph_batch(train,encoding,config=cfg,graph=graph,confidence=oracle)


@pytest.mark.parametrize("variant",["A2","A3"])
def test_weighted_gated_causal_prefix_isolation_and_oov_barrier(variant):
    cfg,train,selection,encoding,graph,confidence,model,batch=weighted_bundle(variant)
    recipe=graph_proto.GATE_RECIPE if variant=="A3" else None
    def prepare(shard,**kwargs):
        return graph_proto.prepare_graph_batch(shard,encoding,config=cfg,graph=graph,
            confidence=confidence,gate_feature_recipe=recipe,**kwargs)
    original=model(batch)[1].reshape(batch.base.q_data.shape)
    # Perturb disjoint selection histories; never rewrite the train shard bound to encoding.
    t=selection.trajectories[0]
    t=replace(t,observations=tuple(replace(o,query=replace(o.query,item_id=i))
        for o,i in zip(t.observations,"abacbc",strict=True)))
    reference=replace(selection,trajectories=(t,))
    changed=replace(reference,trajectories=(replace(t,observations=tuple(
        replace(o,correct=1-o.correct) if i>=3 else o for i,o in enumerate(t.observations))),))
    first=prepare(reference);second=prepare(changed)
    assert torch.equal(model(first)[1][:4],model(second)[1][:4])
    # Learner isolation/padding: peer in the full train batch cannot affect this window.
    single=prepare(train,window_ids=(batch.window_ids[0],));n=int(single.base.valid_mask.sum())
    assert torch.allclose(model(single)[1][:n],original[0,:n],atol=1e-7,rtol=0)
    barrier=prepare(selection)
    assert [u[2] for u in barrier.unseen_targets]==[3]
    later=[q for row in barrier.contexts for q in row if q and q.global_rank>=4]
    assert [q.global_rank for q in later]==[4,5] and all(q.evidence.effective_start==4 for q in later)
    assert torch.isfinite(model(barrier)[1]).all()


def test_a3_rejects_wrong_gate_output_geometry():
    _,_,_,_,_,_,model,batch=weighted_bundle("A3")
    model.gate_module=nn.Linear(4,2)
    with pytest.raises(ValueError,match="logits"):model(batch)


@pytest.mark.parametrize("variant",["A2","A3"])
def test_new_variants_do_not_silently_choose_uniform_confidence(variant):
    cfg,train,_,encoding,graph=toy()
    spec=graph_proto.GraphPrototypeSpec(variant,graph_proto.RECIPE,"engineering","effective_window",
        gate_feature_recipe=graph_proto.GATE_RECIPE if variant=="A3" else None)
    with pytest.raises(ValueError,match="caller-explicit"):
        graph_proto.GraphAKTPrototype(config=cfg,train=train,encoding=encoding,graph=graph,spec=spec,
            message_module=CountingLinear(),readout=nn.Parameter(torch.ones(2)),
            gate_module=nn.Linear(4,1) if variant=="A3" else None)
