"""Cold metadata/joins only. Canonical imports after ROOT-reviewed application.

No live accepted authorization is fabricated. The synthetic two-row result is
only a join fixture, not a model/corpus/checkpoint or a fitted prediction claim.
"""
from dataclasses import asdict, replace
import hashlib
import json
from types import SimpleNamespace

import pytest

from knowledge_tracing.gkt import research_execution as ex, research_runner as runner
from knowledge_tracing.research_admission import MainSelectionContext, PROTOCOL21, RECIPE26, ALLOCATION
from knowledge_tracing.simulator_bridge import ItemQuery, identity_hash

H = 'a'*64


def declared_spec():
    context=MainSelectionContext('grade10_simulator',PROTOCOL21,RECIPE26,ALLOCATION,H,'b'*64,'c'*64,'d'*64,'e'*64)
    sources=dict.fromkeys(ex.SOURCE_NAMES,H)
    sources.update({ex.RECIPE_PATH:ex.RECIPE_SHA256,
        'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md':PROTOCOL21,
        'docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md':RECIPE26,
        'docs/thesis_recovery/EXPERIMENT_ALLOCATION_V1.json':ALLOCATION})
    budget=ex.GKTSelectedBudget(train_learners=8,selection_learners=1,calibration_learners=1,
        train_targets=32,selection_targets=4,calibration_targets=4,max_optimizer_steps=100,
        max_optimized_targets=1600,max_prediction_targets=204,max_training_prefix_events=2400,
        max_prediction_prefix_events=306,max_model_calls=202,max_training_seconds=60.,max_wall_seconds=120.,
        max_worker_rss_bytes=2**30,min_available_ram_bytes=2*2**30,prelaunch_available_ram_bytes=4*2**30,
        max_metadata_bytes=2**18,max_source_file_bytes=8*2**20,max_checkpoint_bytes=8*2**20,
        max_tensor_bytes=8*2**20,max_output_bytes=512*2**20,cpu_threads=2)
    limits=ex.public_reader.CorpusReadLimits(2**20,8*2**20,2**16,8,4,40,10.)
    return ex.GKTSelectedExecutionSpec('metadata-only',context,ex.GKTSelectedRecipe(),'not-published',H,'b'*64,
        ex.FilePin('artifacts/akt/declared-expert.json','f'*64),json.dumps(asdict(limits)),tuple(sorted(sources.items())),budget)


def declared_evidence():
    def pin(name):
        return ex.FilePin('artifacts/akt/'+name,H)
    components=tuple(ex.GKTComponentAcceptance(kind,pin(kind+'/final.json'),pin(kind+'/child.json'),
        pin(kind+'/owned.json'),pin(kind+'/junit.xml')) for kind in ('model11','trainer8','checkpoint28'))
    return ex.GKTSelectedEvidence(pin('runtime.json'),pin('gate.json'),ex.FilePin('requirements-akt.lock.txt',H),
        components,tuple(ex.FilePin('.venv/'+name,H) for name in ('python','cfg','torch','numpy')))


def joined_fixture():
    queries=(ItemQuery('i0',10,1),ItemQuery('unseen',11,2))
    truth=tuple(SimpleNamespace(learner_id='L',query=q,correct=i,global_rank=i,origin_role='selection',
        phase_scope='raw_selection10',phase_sha256=H,encoding_sha256='b'*64,trained_item=i==0,
        history_sha256=str(i+1)*64,history_hash_scheme='observable-prefix-chain-v1') for i,q in enumerate(queries))
    predictions=tuple(dict(learner_id='L',query=asdict(q),global_rank=i,origin_role='selection',
        history_sha256=str(i+1)*64,history_hash_scheme='observable-prefix-chain-v1',
        support_reason='cold_query_only' if i==0 else 'oov_item',probability=.3 if i==0 else None,
        prediction_status='scored' if i==0 else 'unsupported') for i,q in enumerate(queries))
    result=dict(status='complete',complete=True,stop_reason='raw_prediction_complete',
        role='gkt_research_compute_only_no_fit_attestation',resume_supported=False,fitted_research_model=False,
        pending_batch_keys=(),cleanup_errors=[],model_state_before=H,model_state_after=H,
        normalization_before={'self':0},normalization_after={'self':0},predictions=predictions,
        raw_predictions_sha256=identity_hash(predictions))
    return result,truth


def rows(result,truth):
    return runner.selection_rows(result,truth,phase_sha256=H,encoding_sha256='b'*64)


def reseal(result):
    result['raw_predictions_sha256']=identity_hash(result['predictions'])


def test_declared_spec_has_no_authority():
    spec=declared_spec()
    assert spec.recipe.batch_size==4 and spec.recipe.state_dim==32 and spec.recipe.max_epochs==50
    assert spec.output.parts[-3:]==('gkt','results','metadata-only')
    assert ex.OBJECTIVE=='gkt29_raw_response_pooled_binary64_log_loss_v1'
    assert not hasattr(spec,'guard') and not hasattr(spec,'revalidate')


@pytest.mark.parametrize('field,value',[('batch_size',128),('dropout',.2),('state_dim',200),('max_epochs',20),('seed',43)])
def test_wrong_recipe_is_rejected(field,value):
    with pytest.raises(ValueError):
        replace(ex.GKTSelectedRecipe(),**{field:value})


def test_source_is_mandatory():
    spec=declared_spec()
    for name in ('src/knowledge_tracing/gkt/research_model.py','src/knowledge_tracing/gam_kt/__init__.py'):
        sources=dict(spec.expected_sources)
        sources.pop(name)
        with pytest.raises(ValueError,match='all GKT/shared'):
            replace(spec,expected_sources=tuple(sorted(sources.items())))


def test_workload_counts_learner_batches_not_target_chunks():
    spec=declared_spec()
    with pytest.raises(ValueError,match='whole declared'):
        replace(spec,budget=replace(spec.budget,max_optimizer_steps=50))


def test_insufficient_model_calls_rejected():
    spec=declared_spec()
    with pytest.raises(ValueError,match='whole declared'):
        replace(spec,budget=replace(spec.budget,max_model_calls=201))


def test_foreign_environment_rejected():
    spec=declared_spec()
    with pytest.raises(ValueError,match='Grade10'):
        replace(spec,context=replace(spec.context,environment_id='junyi_development_outer_fold4'))


def test_topology_protected_path_rejected_before_inspection(monkeypatch):
    spec=declared_spec()
    def forbidden(*args,**kwargs):
        raise AssertionError('protected source path must not reach path inspection')
    monkeypatch.setattr(ex,'_path',forbidden)
    with pytest.raises(ValueError,match='topology metadata'):
        replace(spec,topology=ex.FilePin('dataset/expert.json',H))


def test_all_component_kinds_required():
    evidence=declared_evidence()
    with pytest.raises(ValueError,match='three GKT'):
        replace(evidence,components=evidence.components[:2])


def test_duplicate_component_not_a_substitute():
    evidence=declared_evidence()
    with pytest.raises(ValueError,match='three GKT'):
        replace(evidence,components=(evidence.components[0],)*3)


def test_component_requires_actual_junit_pin():
    evidence=declared_evidence()
    with pytest.raises(ValueError,match='typed actual'):
        replace(evidence.components[0],junit=None)


def test_artifact_read_rejects_wrong_sha(tmp_path,monkeypatch):
    monkeypatch.setattr(ex,'ROOT',tmp_path)
    directory=tmp_path/'artifacts/akt';directory.mkdir(parents=True)
    (directory/'wrong.json').write_text('{}',encoding='utf-8')
    with pytest.raises(ValueError,match='byte SHA mismatch'):
        ex._read(ex.FilePin('artifacts/akt/wrong.json',H),1024)


def test_sakt_authority_rejected_before_identity_inspection(tmp_path,monkeypatch):
    spec,evidence=declared_spec(),declared_evidence()
    monkeypatch.setattr(ex,'ROOT',tmp_path)
    directory=tmp_path/'artifacts/akt';directory.mkdir(parents=True)
    auth=dict(schema_version=1,scope='sakt_main_selected_only_v1',decision='AUTHORIZE_BOUNDED_SAKT_MAIN_SELECTED_ONLY',
        run_id=spec.run_id,spec_sha256=spec.identity,recipe_sha256=ex.RECIPE_SHA256,identity={},caps=asdict(spec.budget),
        requested_phases=list(ex.PHASES),approval_reference='NEGATIVE_ONLY_NOT_AUTHORIZATION')
    raw=json.dumps(auth).encode();(directory/'wrong-auth.json').write_bytes(raw)
    def forbidden(*args,**kwargs):
        raise AssertionError('wrong-family auth must fail before inspection or model')
    monkeypatch.setattr(ex,'_inspect',forbidden)
    with pytest.raises(ValueError,match='closed GKT authorization'):
        ex.require_gkt_selected_authorization(spec,evidence,authorization_file='artifacts/akt/wrong-auth.json',
            expected_authorization_sha256=hashlib.sha256(raw).hexdigest())


def test_supported_and_null_share_complete_population():
    result,truth=joined_fixture()
    actual,reasons=rows(result,truth)
    assert len(actual)==2 and [r.probability for r in actual]==[.3,None]
    assert [r.candidate_id for r in actual]==['GKT','GKT']
    assert len(reasons)==2 and actual[1].support_reason=='oov_item'
    assert runner.population(actual)['scheme']=='model-neutral-selection-K-y-jsonl-v1'


def test_duplicate_prediction_rejected_even_with_new_sha():
    result,truth=joined_fixture()
    result['predictions']=(result['predictions'][0],)*2;reseal(result)
    with pytest.raises(ValueError,match='key mismatch'):
        rows(result,truth)


def test_missing_prediction_rejected():
    result,truth=joined_fixture()
    result['predictions']=result['predictions'][:1];reseal(result)
    with pytest.raises(ValueError,match='full selection'):
        rows(result,truth)


def test_wrong_history_truth_rejected():
    result,truth=joined_fixture();truth[0].history_sha256='f'*64
    with pytest.raises(ValueError,match='truth join'):
        rows(result,truth)


def test_incomplete_row_cannot_be_exported_as_null():
    result,truth=joined_fixture();result['predictions'][1]['prediction_status']='unprocessed';reseal(result)
    with pytest.raises(ValueError,match='unprocessed'):
        rows(result,truth)


def test_prediction_payload_mutation_rejected():
    result,truth=joined_fixture();result['predictions'][0]['probability']=.4
    with pytest.raises(ValueError,match='frozen GKT'):
        rows(result,truth)


def test_bn_mutation_rejected():
    result,truth=joined_fixture();result['normalization_after']['self']=1
    with pytest.raises(ValueError,match='frozen GKT'):
        rows(result,truth)


@pytest.mark.parametrize('probability',[float('nan'),float('inf')])
def test_nonfinite_prediction_rejected(probability):
    result,truth=joined_fixture();result['predictions'][0]['probability']=probability
    # Canonical sealing itself rejects nonfinite JSON before export.
    with pytest.raises(ValueError):
        reseal(result);rows(result,truth)


def test_supported_status_cannot_hide_oov():
    result,truth=joined_fixture();result['predictions'][0]['support_reason']='oov_item';reseal(result)
    with pytest.raises(ValueError,match='null reason'):
        rows(result,truth)


def test_prediction_role_truth_cannot_train_or_export():
    result,truth=joined_fixture();truth[0].origin_role='calibration'
    with pytest.raises(ValueError,match='truth join'):
        rows(result,truth)
