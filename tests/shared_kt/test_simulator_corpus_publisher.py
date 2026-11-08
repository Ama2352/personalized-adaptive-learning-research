"""Typed hand-built observations only; không gọi native teacher/model/collector."""
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import inspect
import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

from knowledge_tracing import simulator_corpus_publisher as pub
from knowledge_tracing import simulator_research_collection as collection
from knowledge_tracing.simulator_bridge import ItemQuery, Observation, SimulatorBank, SimulatorItem, identity_hash
from knowledge_tracing.simulator_data import ObservableTrajectory
from knowledge_tracing.simulator_research_data import (ResearchSplitPlan, ResearchProvenance,
    ShardLimits, audit_research_shard)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope='module')
def template(tmp_path_factory):
    root=tmp_path_factory.mktemp('publisher-workspace')
    names=[collection.PROTOCOL_PATH,collection.COLLECTOR_PATH]+[f'fixture/source-{i}.txt' for i in range(11)]
    for name in [*names,pub.PUBLISHER_PATH]:
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text('SYNTHETIC_SOURCE_FIXTURE_NOT_ACTUAL_PROVENANCE '+name,encoding='utf-8')
    sources={name:digest(root/name) for name in names}
    plan=ResearchSplitPlan('publisher-engineering-fixture',42,10,1,sources[collection.PROTOCOL_PATH])
    bank=SimulatorBank('synthetic-publisher-bank-not-research-data',tuple(
        SimulatorItem(f'C{c}-d{d}',f'C{c}',d) for c in range(28) for d in (1050,1200,1350)))
    recipe=collection.ResearchCollectionRecipe('cyclic_items_seeded_offset',84,1000,60)
    collector_limits=collection.ResearchCollectionLimits(8,84,672,30,256*1024**2,1024**3)
    semantics={'fixture':'declared fake world, never native execution'}
    graph='d'*64
    all_assignments=plan.split_plan.assignments()
    ordinal={a.learner_id:i for i,a in enumerate(all_assignments)}
    results={}
    for role,profile in zip(pub.DEVELOPMENT_ROLES,('PG','PY','PYH')):
        assignments=[a for a in all_assignments if a.role==role]
        profiles={a.learner_id:profile for a in assignments}
        composite=identity_hash(dict(recipe=asdict(recipe),recipe_sha256=recipe.identity,
                                    profile_metadata_sha256=identity_hash(profiles)))
        provenance=ResearchProvenance(role,plan.identity,plan.split_plan.identity,identity_hash(bank.identity),graph,
            (('collector',sources[collection.COLLECTOR_PATH]),('environment',identity_hash(semantics)),
             ('source_inventory',identity_hash(sources))),composite,
            collection.COLLECTOR_VERSION+':'+recipe.policy,'unix_seconds_utc','UTC',False)
        trajectories=[];oracle={}
        for assignment in assignments:
            observations=tuple(Observation(ItemQuery(item.item_id,1000+(rank+1)*60,
                ordinal[assignment.learner_id]*collection.EVENT_STRIDE+rank+1),rank%2)
                for rank,item in enumerate(bank.items))
            trajectories.append(ObservableTrajectory(assignment.learner_id,plan.split_plan.identity,
                identity_hash(bank.identity),provenance.collection_policy_id,observations))
            oracle[assignment.learner_id]=dict(profile=profile,assignment=asdict(assignment),
                initial_state={'theta':999.},events=[dict(query=asdict(o.query),oracle_result={'y':o.correct},
                outcome_uniform=.123,learning_uniform=.456) for o in observations],final_snapshot={'theta':1001.})
        trajectories=tuple(trajectories)
        audit=audit_research_shard(trajectories,plan=plan,bank=bank,role=role,provenance=provenance,
            expected_provenance_sha256=provenance.identity,limits=collector_limits.shard_limits(),reference_items=bank.item_ids)
        sidecar=dict(scope='oracle evaluation only; forbidden as model features',learners=oracle)
        targets=sum(len(t.observations) for t in trajectories)
        manifest=dict(schema_version=1,status='COMPLETE_REQUESTED_ROLE_NOT_MODEL_FITTED',
            collector_version=collection.COLLECTOR_VERSION,role=role,plan_sha256=plan.identity,
            recipe=asdict(recipe),recipe_sha256=composite,limits=asdict(collector_limits),domain=bank.identity,
            environment_semantics=semantics,environment_graph_sha256=graph,provenance=asdict(provenance),
            provenance_sha256=provenance.identity,sources_before=sources,sources_after=sources,
            logging_policy_oracle_access=False,profile_metadata_sha256=identity_hash(profiles),
            source_row_formula='global_plan_learner_ordinal*1000000+rank+1',
            clock={'unit':'unix_seconds_utc','timezone':'UTC','first_event':'start+gap'},
            rng_namespace='FIXTURE_NO_RANDOM_DRAWS',numpy_version='FIXTURE',pandas_version='FIXTURE',
            audit=audit,oracle_sidecar_sha256=identity_hash(sidecar),interact_attempts=targets,
            interact_returns=targets,completed_events=targets,completed_learners=len(assignments),
            elapsed_seconds=0.,scope='HAND_BUILT_FIXTURE_NOT_COLLECTED')
        results[role]=collection.ResearchCollectionResult(bank,trajectories,provenance,sidecar,manifest)
    return root,sources,plan,results


@pytest.fixture
def case(template,monkeypatch,request):
    root,sources,plan,results=template
    monkeypatch.setattr(pub,'ROOT',root)
    monkeypatch.setattr(pub,'source_inventory',lambda:{name:digest(root/name) for name in sources})
    monkeypatch.setattr(pub,'memory_snapshot',lambda:dict(process_rss_bytes=64*1024**2,
        process_peak_rss_bytes=None,system_available_ram_bytes=4*1024**3))
    def forbidden(*args,**kwargs):
        raise AssertionError('native/model collection forbidden in publisher tests')
    monkeypatch.setattr(collection,'load_reference',forbidden)
    assert 'torch' not in sys.modules
    name=request.node.name.replace('[','-').replace(']','').replace('_','-')
    name='case-'+hashlib.sha256(name.encode()).hexdigest()[:16]
    value=SimpleNamespace(root=root,sources=dict(sources),plan=deepcopy(plan),results=deepcopy(results),corpus_id=name,
        limits=pub.CorpusPublicationLimits(2*1024**2,8*1024**2,4*1024**2,ShardLimits(8,84,840),
                                           30,512*1024**2,1024**3))
    value.base=root/'artifacts/simulator/corpora'/name
    yield value
    assert 'torch' not in sys.modules


def publish(case,**kwargs):
    options=dict(corpus_id=case.corpus_id,expected_sources=case.sources,
                 expected_protocol_sha256=case.plan.protocol_sha256,limits=case.limits)
    options.update(kwargs)
    return pub.publish_research_corpus(case.plan,case.results,**options)


def rejects_before_write(case,match):
    with pytest.raises(pub.CorpusPublicationFailure,match=match) as error:
        publish(case)
    assert error.value.receipt['owned_directory'] is False
    assert not case.base.exists()


def reseal(case,role):
    result=case.results[role]
    result.manifest['provenance']=asdict(result.provenance)
    result.manifest['provenance_sha256']=result.provenance.identity
    result.manifest['oracle_sidecar_sha256']=identity_hash(result.oracle_sidecar)
    result.manifest['audit']=audit_research_shard(result.trajectories,plan=case.plan,bank=result.bank,
        role=role,provenance=result.provenance,expected_provenance_sha256=result.provenance.identity,
        limits=collection.ResearchCollectionLimits(**result.manifest['limits']).shard_limits(),
        reference_items=result.bank.item_ids)


def read_guard_metadata(case,expected_sha):
    from knowledge_tracing.akt import research_execution as guard
    counts=dict(case.plan.split_plan.role_counts)
    budget=SimpleNamespace(max_input_bytes=case.limits.max_total_bytes,max_events_per_learner=84,
        **{r+'_learners':counts[r] for r in pub.DEVELOPMENT_ROLES},
        **{r+'_targets':counts[r]*84 for r in pub.DEVELOPMENT_ROLES})
    spec=SimpleNamespace(native_config=SimpleNamespace(project_root=case.root),corpus_id=case.corpus_id,
                         expected_corpus_sha256=expected_sha,expected_protocol_sha256=case.plan.protocol_sha256,budget=budget)
    # Metadata reader only: this does not invoke native preflight or grant execution.
    return guard._corpus(spec,{'build_hashes':case.sources})


def test_exact_schema_done_inventory_and_restart_roundtrip_without_oracle(case):
    receipt=publish(case)
    assert receipt.status=='PUBLISHED_OBSERVABLE_CORPUS_NOT_MODEL_FITTED'
    done=json.loads((case.base/'DONE.json').read_bytes())
    assert set(done)=={'schema_version','status','corpus_sha256','files_sha256'}
    assert set(done['files_sha256'])==set(pub.INPUT_NAMES)
    assert done['corpus_sha256']==receipt.corpus_sha256==digest(case.base/'corpus.json')
    assert receipt.done_sha256==digest(case.base/'DONE.json')
    assert all(digest(case.base/name)==sha for name,sha in done['files_sha256'].items())
    assert all(digest(case.base/name)==sha and (case.base/name).stat().st_size==size for name,sha,size in receipt.files)
    plan_disk=json.loads((case.base/'plan.json').read_bytes())
    assert set(plan_disk)=={'schema_version','recipe','manifest'}
    reconstructed=ResearchSplitPlan(**plan_disk['recipe'])
    assert identity_hash(reconstructed.manifest())==identity_hash(plan_disk['manifest'])==identity_hash(case.plan.manifest())
    bank_disk=json.loads((case.base/'bank.json').read_bytes())
    bank=SimulatorBank(bank_disk['environment_id'],tuple(SimulatorItem(**r) for r in bank_disk['items']))
    raw_recipes=set()
    for role in pub.DEVELOPMENT_ROLES:
        manifest=json.loads((case.base/(role+'.manifest.json')).read_bytes())
        assert len(manifest)==16
        payload=manifest['provenance'];payload['source_bindings']=tuple(tuple(x) for x in payload['source_bindings'])
        provenance=ResearchProvenance(**payload)
        assert provenance.identity==manifest['provenance_sha256']
        trajectories=tuple(ObservableTrajectory.from_payload(json.loads(line)) for line in (case.base/(role+'.jsonl')).read_bytes().splitlines())
        audited=audit_research_shard(trajectories,plan=reconstructed,bank=bank,role=role,
            provenance=provenance,expected_provenance_sha256=manifest['provenance_sha256'],
            limits=case.limits.shard_limits,reference_items=bank.item_ids)
        assert audited['reference_complete']
        text=(case.base/(role+'.jsonl')).read_text()
        assert not any(word in text for word in ('theta','oracle_result','uniform','profile'))
        raw_recipes.add(case.results[role].manifest['recipe_sha256'])
    assert len(raw_recipes)==3  # Role profile metadata differs; normalized recipe is shared.
    assert 'theta' in (case.base/'oracle/train.json').read_text()


def test_done_is_last_after_all_data_oracle_fsync_and_readback(case,monkeypatch):
    writes=[];reads=[]
    original_write,original_read=pub._write_file,pub._readback
    def write(path,payload):
        if path.name=='DONE.json':
            assert len(writes)==16 and not (case.base/'DONE.json').exists()
            assert set(writes)<=set(reads)
        original_write(path,payload);writes.append(path.relative_to(case.base).as_posix())
    def read(path,payload):
        original_read(path,payload);reads.append(path.relative_to(case.base).as_posix())
    monkeypatch.setattr(pub,'_write_file',write);monkeypatch.setattr(pub,'_readback',read)
    publish(case)
    assert writes[-1]=='DONE.json' and len(writes)==17


def test_real_guard_reader_accepts_published_metadata_without_opening_oracle(case,monkeypatch):
    receipt=publish(case)
    original=Path.open;opened=[]
    def forbid(path,*args,**kwargs):
        assert not path.is_relative_to(case.base/'oracle'), 'guard accessed privileged oracle'
        opened.append(path)
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'open',forbid)
    evidence=read_guard_metadata(case,receipt.corpus_sha256)
    assert evidence['done_sha256']==receipt.done_sha256 and set(evidence['files_sha256'])==set(pub.INPUT_NAMES)
    assert evidence['oracle_files_opened'] is False and evidence['final_event_files_opened'] is False
    assert evidence['actual_observable_schema_reaudit_required_before_model'] is True
    assert opened and all(p.parent==case.base for p in opened)


def test_no_overwrite_even_existing_partial_and_no_failure_in_old_directory(case):
    case.base.mkdir(parents=True)
    marker=case.base/'preserved.txt';marker.write_bytes(b'old-owned-elsewhere')
    with pytest.raises(pub.CorpusPublicationFailure,match='existing corpus'):
        publish(case)
    assert marker.read_bytes()==b'old-owned-elsewhere' and not (case.base/'failure.json').exists()


def test_fixed_root_api_has_no_project_root_override(case):
    assert 'project_root' not in inspect.signature(pub.publish_research_corpus).parameters
    with pytest.raises(TypeError,match='project_root'):
        publish(case,project_root=case.root/'dataset')
    assert not case.base.exists()


@pytest.mark.parametrize('corpus_id',('../dataset','x/y','/absolute','a\\b',''))
def test_rejects_unsafe_ids_before_write(case,corpus_id):
    with pytest.raises(pub.CorpusPublicationFailure,match='safe corpus ID'):
        publish(case,corpus_id=corpus_id)
    assert not case.base.exists()


def test_path_alias_rejected_before_write(case,monkeypatch):
    original=pub._alias
    monkeypatch.setattr(pub,'_alias',lambda p:p==case.root/'artifacts/simulator' or original(p))
    rejects_before_write(case,'alias forbidden')


@pytest.mark.parametrize('field',('graph','recipe','bank','source','oracle_flag'))
def test_cross_role_provenance_and_world_mismatch_before_mkdir(case,field):
    result=case.results['calibration']
    if field=='graph':
        result.manifest['environment_graph_sha256']='e'*64
        case.results['calibration']=replace(result,provenance=replace(result.provenance,environment_graph_sha256='e'*64))
        result=case.results['calibration']
        result.manifest['provenance']=asdict(result.provenance);result.manifest['provenance_sha256']=result.provenance.identity
        match='cross-role'
    elif field=='recipe':
        result.manifest['recipe']['gap_seconds']=61;match='cross-role'
    elif field=='bank':
        bank=SimulatorBank('different-fixture-world',result.bank.items)
        case.results['calibration']=replace(result,bank=bank)
        result.manifest['domain']=bank.identity;match='cross-role'
    elif field=='source':
        result.manifest['sources_after']={**case.sources,'extra.txt':'0'*64};match='source inventory'
    else:
        object.__setattr__(result.provenance,'logging_policy_oracle_access',True)
        reseal(case,'calibration')
        match='oracle-free'
    rejects_before_write(case,match)


def test_actual_pinned_source_drift_before_write(case):
    path=case.root/'fixture/source-0.txt';before=path.read_bytes()
    try:
        path.write_bytes(before+b' changed')
        rejects_before_write(case,'source/protocol drift')
    finally:
        path.write_bytes(before)


def test_plan_seed_assignment_drift_before_write(case):
    object.__setattr__(case.plan.split_plan,'root_seed',99)
    rejects_before_write(case,'plan/seed assignment drift')


def test_final_role_rejected_without_iterating_it(case):
    class Forbidden:
        def __iter__(self):raise AssertionError('final accessed')
    case.results['final']=Forbidden()
    rejects_before_write(case,'exact three development roles')


def test_source_row_clock_and_sidecar_query_must_match(case):
    result=case.results['calibration'];trajectory=result.trajectories[0]
    first=trajectory.observations[0]
    changed=replace(first,query=replace(first.query,source_row=first.query.source_row+1))
    case.results['calibration']=replace(result,trajectories=(replace(trajectory,observations=(changed,*trajectory.observations[1:])),))
    result.oracle_sidecar['learners'][trajectory.learner_id]['events'][0]['query']=asdict(changed.query)
    result.manifest['oracle_sidecar_sha256']=identity_hash(result.oracle_sidecar)
    rejects_before_write(case,'clock/source-row drift')


def test_missing_reference_coverage_not_rescued_or_published(case):
    result=case.results['calibration'];trajectory=result.trajectories[0]
    last=trajectory.observations[-1]
    changed=replace(last,query=replace(last.query,item_id=trajectory.observations[0].query.item_id))
    case.results['calibration']=replace(result,trajectories=(replace(trajectory,observations=(*trajectory.observations[:-1],changed)),))
    result.oracle_sidecar['learners'][trajectory.learner_id]['events'][-1]['query']=asdict(changed.query)
    reseal(case,'calibration')
    rejects_before_write(case,'complete reference coverage')


def test_oracle_current_outcome_mismatch_is_failure_not_feature(case):
    result=case.results['selection'];learner=result.trajectories[0].learner_id
    detail=result.oracle_sidecar['learners'][learner]['events'][0]
    detail['oracle_result']['y']=1-detail['oracle_result']['y']
    result.manifest['oracle_sidecar_sha256']=identity_hash(result.oracle_sidecar)
    rejects_before_write(case,'query/outcome mismatch')


@pytest.mark.parametrize('mode',('file','total','oracle','mutated_limit'))
def test_explicit_byte_caps_and_cap_drift_before_mkdir(case,mode):
    if mode=='file':
        case.limits=replace(case.limits,max_file_bytes=100)
    elif mode=='total':
        # Derive a cap above every large source payload but below their combined size.
        sizes=[len(json.dumps(value,sort_keys=True,separators=(',',':')).encode()) for result in case.results.values()
               for value in (result.oracle_sidecar,result.manifest)]
        cap=max(sizes)+4096
        case.limits=replace(case.limits,max_file_bytes=cap,max_total_bytes=cap,max_oracle_bytes=cap)
    elif mode=='oracle':
        case.limits=replace(case.limits,max_oracle_bytes=100)
    else:
        object.__setattr__(case.limits,'max_file_bytes',True)
    rejects_before_write(case,'total/oracle publication byte cap' if mode in ('total','oracle') else 'cap|positive')


def test_midwrite_failure_retains_owned_partial_failure_receipt_and_no_done(case,monkeypatch):
    original=pub._write_file
    def fail(path,payload):
        if path.name=='selection.jsonl':
            with path.open('xb') as handle:handle.write(payload[:37])
            raise OSError('injected midwrite failure')
        return original(path,payload)
    monkeypatch.setattr(pub,'_write_file',fail)
    with pytest.raises(pub.CorpusPublicationFailure,match='injected midwrite') as caught:
        publish(case)
    assert caught.value.receipt['owned_directory'] and caught.value.receipt['failure_receipt_persisted']
    assert (case.base/'train.jsonl').is_file() and (case.base/'failure.json').is_file()
    assert not (case.base/'DONE.json').exists()
    assert (case.base/'selection.jsonl').stat().st_size==37
    failure=json.loads((case.base/'failure.json').read_bytes())
    assert failure['status']=='FAILED_NO_USABLE_CORPUS' and failure['rollback'] is False and failure['automatic_retry'] is False
    assert failure['incomplete_or_unverified_file']=='selection.jsonl'


def test_readback_corruption_prevents_done(case,monkeypatch):
    original=pub._readback;triggered=False
    def corrupt(path,payload):
        nonlocal triggered
        if not triggered:
            triggered=True;path.write_bytes(b'corrupt')
        return original(path,payload)
    monkeypatch.setattr(pub,'_readback',corrupt)
    with pytest.raises(pub.CorpusPublicationFailure,match='readback SHA'):
        publish(case)
    assert (case.base/'failure.json').is_file() and not (case.base/'DONE.json').exists()


def test_source_drift_after_data_writes_prevents_done(case,monkeypatch):
    original=pub._write_file;source=case.root/'fixture/source-0.txt';before=source.read_bytes()
    def drift(path,payload):
        original(path,payload)
        if path.name=='publication-inventory.json':source.write_bytes(before+b' changed')
    monkeypatch.setattr(pub,'_write_file',drift)
    try:
        with pytest.raises(pub.CorpusPublicationFailure,match='source/protocol drift'):
            publish(case)
        assert (case.base/'failure.json').is_file() and not (case.base/'DONE.json').exists()
    finally:
        source.write_bytes(before)


def test_caller_mutation_after_seal_cannot_change_published_bytes(case,monkeypatch):
    original=pub._write_file;triggered=False
    expected=identity_hash(case.results['calibration'].oracle_sidecar)
    def mutate(path,payload):
        nonlocal triggered
        if not triggered:
            triggered=True;case.results['calibration'].oracle_sidecar['scope']='caller mutation after sealing'
        original(path,payload)
    monkeypatch.setattr(pub,'_write_file',mutate)
    publish(case)
    assert identity_hash(json.loads((case.base/'oracle/calibration.json').read_bytes()))==expected


def test_late_done_failure_keeps_failure_marker_and_truthful_done_presence(case,monkeypatch):
    original=pub._write_file
    def fail(path,payload):
        original(path,payload)
        if path.name=='DONE.json':raise OSError('injected after DONE fsync')
    monkeypatch.setattr(pub,'_write_file',fail)
    with pytest.raises(pub.CorpusPublicationFailure,match='after DONE') as caught:
        publish(case)
    assert caught.value.receipt['done_created'] is True
    assert (case.base/'DONE.json').is_file() and (case.base/'failure.json').is_file()
    with pytest.raises(ValueError,match='complete DONE and absence of failure'):
        read_guard_metadata(case,digest(case.base/'corpus.json'))
