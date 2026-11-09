"""Schema2 metadata fixtures only; opaque bytes, no Torch/model/CUDA import."""
from dataclasses import asdict, fields
import copy
import hashlib

import pytest

from knowledge_tracing.akt import research_graph_checkpoint as cp
from knowledge_tracing.akt.config import ResearchCUDAExecutionProfile

H='a'*64
SOURCES=(('MANUFACTURED_METADATA_NOT_GPU_PROOF',H),)
LIMITS=cp.GraphCheckpointLimits(1024**2,65536,1024**2)


def identity(schema=2):
    profile=cp.GraphCheckpointProfile(H,cp.RECIPE_SHA256,H,H,H,H,'selected_fit_candidate',None)
    value=dict(schema_version=schema,role=cp.ROLE,recipe=cp.RECIPE,recipe_sha256=cp.RECIPE_SHA256,
        config=dict(phase='simulator-research',device='cpu' if schema==1 else 'cuda'),
        encoding={},encoding_sha256=H,condition={},condition_sha256=H,phase_index_sha256=H,phase_sha256=H,
        neural_binding=dict(phase_scope='select_train80'),profile=asdict(profile),sources=[list(row) for row in SOURCES],
        iterator_resume_supported=False,lifecycle_resume_supported=False,fitted_research_model=False,
        selection_state_saved=False,global_budget_saved=False)
    if schema==2:value['execution_profile']=asdict(ResearchCUDAExecutionProfile(1024**3))
    return value


def files(tmp_path_factory,monkeypatch,*,schema=2):
    root=tmp_path_factory.mktemp('cp')
    monkeypatch.setattr(cp,'ROOT',root)
    monkeypatch.setattr(cp,'source_inventory',lambda:SOURCES)
    monkeypatch.setattr(cp,'_torch',lambda *args,**kwargs:pytest.fail('metadata inspection cannot import/deserialise Torch'))
    directory=root/'experiments/akt/results/f/checkpoints/e1';directory.mkdir(parents=True)
    expected=identity(schema)
    raw=b'OPAQUE_SYNTHETIC_BYTES_NOT_TORCH_SAVE_OR_GPU_STATE'
    receipt=dict(completed_epochs=1,optimizer_body_returns=2,optimized_targets=48,
        parameter_participation=[['backbone.weight',2],['alpha',1]],phase_index_sha256=H,
        windows_sha256=H,targets_sha256=H,ordered_batches_sha256=H,epoch_steps=2,epoch_targets=48,
        model_sha256=H,optimizer_sha256=H)
    producer=dict(run_id='f',output_dir='manufactured',max_steps=2,max_seconds=30.,max_wall_seconds=30.,
        max_rss_bytes=1024**3,min_available_ram_bytes=1024**3)
    if schema==2:producer.update(expected['config'])
    meta=dict(schema_version=schema,role=cp.ROLE,identity=copy.deepcopy(expected),receipt=receipt,
        producer_config=producer,layout=[['backbone.weight','alpha']],
        state_representation=[['alpha','initialized'],['backbone.weight','initialized']],
        checkpoint_sha256=hashlib.sha256(raw).hexdigest(),checkpoint_bytes=len(raw),
        restore_scope='completed_epoch_boundary',iterator_resume_supported=False,lifecycle_resume_supported=False,
        fitted_research_model=False)
    def write(*,complete_schema=None):
        (directory/'state.pt').write_bytes(raw)
        encoded=cp._raw(meta);(directory/'metadata.json').write_bytes(encoded)
        complete=cp._raw(dict(schema_version=schema if complete_schema is None else complete_schema,status=cp.STATUS,
            metadata_sha256=hashlib.sha256(encoded).hexdigest(),checkpoint_sha256=hashlib.sha256(raw).hexdigest()))
        (directory/'COMPLETE.json').write_bytes(complete)
        return hashlib.sha256(complete).hexdigest()
    return directory,expected,meta,write


def inspect(directory,expected,pin):
    return cp.inspect_graph_epoch_state(directory,expected_identity=expected,expected_complete_sha256=pin,limits=LIMITS)


def test_eight_field_checkpoint_profile_stays_unchanged():
    assert tuple(item.name for item in fields(cp.GraphCheckpointProfile))==(
        'protocol21_sha256','protocol26_sha256','runtime_receipt_sha256','runtime_profile_sha256',
        'initial_backbone_sha256','candidate_allocation_sha256','purpose','external_system_freeze_sha256')


def test_cpu_identity_legacy_schema_has_no_execution_profile():
    value=identity(1)
    assert 'execution_profile' not in value and cp._identity_shape(value) is None
    assert cp._device(None)=='cpu' and cp._device(None,serialized=True)=='cpu'


def test_cuda_identity_profile_is_metadata_not_runtime_proof():
    profile=cp._identity_shape(identity())
    assert type(profile) is ResearchCUDAExecutionProfile
    assert cp._device(profile)=='cuda:0' and cp._device(profile,serialized=True)=='cpu'
    assert not isinstance(profile,cp.InspectedGraphCheckpoint)


@pytest.mark.parametrize('schema',[1,2])
def test_both_wire_versions_inspect_opaque_bytes_without_torch(tmp_path_factory,monkeypatch,schema):
    directory,expected,meta,write=files(tmp_path_factory,monkeypatch,schema=schema)
    before={p.name:p.read_bytes() for p in directory.iterdir()}
    pin=write();published={p.name:p.read_bytes() for p in directory.iterdir()}
    result=inspect(directory,expected,pin)
    assert result.reference.directory==directory
    assert {p.name:p.read_bytes() for p in directory.iterdir()}==published
    assert before=={} and meta['schema_version']==schema


@pytest.mark.parametrize('change',[
    'missing_profile','extra_profile_cpu','cuda_in_schema1','cpu_in_schema2','boolean_version',
    'unsupported_version','extra_identity_field','prediction_phase','future_fitted_claim'])
def test_closed_schema_device_and_phase_reject_without_torch(change):
    value=identity(1 if change in ('extra_profile_cpu','cuda_in_schema1') else 2)
    if change=='missing_profile':value.pop('execution_profile')
    elif change=='extra_profile_cpu':value['execution_profile']=asdict(ResearchCUDAExecutionProfile(1024**3))
    elif change=='cuda_in_schema1':value['config']['device']='cuda'
    elif change=='cpu_in_schema2':value['config']['device']='cpu'
    elif change=='boolean_version':value['schema_version']=True
    elif change=='unsupported_version':value['schema_version']=3
    elif change=='extra_identity_field':value['verified_gpu']=True
    elif change=='prediction_phase':value['neural_binding']['phase_scope']='raw_selection10'
    else:value['fitted_research_model']=True
    with pytest.raises(ValueError):cp._identity_shape(value)


@pytest.mark.parametrize('field,value',[
    ('device','cuda:1'),('dtype','float16'),('seed',43),('foreach',True),('fused',True),
    ('capturable',True),('matmul_allow_tf32',True),('deterministic_warn_only',True),
    ('max_vram_bytes',0),('foreach',0)])
def test_cuda_recipe_drift_rejected_as_metadata(field,value):
    expected=identity();expected['execution_profile'][field]=value
    with pytest.raises(ValueError):cp._identity_shape(expected)


@pytest.mark.parametrize('change',['missing','extra'])
def test_cuda_execution_profile_requires_exact_field_population(change):
    expected=identity()
    if change=='missing':expected['execution_profile'].pop('max_vram_bytes')
    else:expected['execution_profile']['runtime_verified']=True
    with pytest.raises(ValueError):cp._identity_shape(expected)


@pytest.mark.parametrize('field',['runtime_receipt_sha256','runtime_profile_sha256'])
def test_expected_runtime_binding_drift_rejects_before_deserialization(tmp_path_factory,monkeypatch,field):
    directory,expected,meta,write=files(tmp_path_factory,monkeypatch)
    pin=write();changed=copy.deepcopy(expected);changed['profile'][field]='b'*64
    with pytest.raises(ValueError,match='identity/role/scope'):inspect(directory,changed,pin)
    assert meta['identity']==expected


@pytest.mark.parametrize('layer',['complete','metadata','metadata-boolean'])
def test_mixed_outer_schema_versions_reject(tmp_path_factory,monkeypatch,layer):
    directory,expected,meta,write=files(tmp_path_factory,monkeypatch)
    if layer.startswith('metadata'):meta['schema_version']=True if layer=='metadata-boolean' else 1
    pin=write(complete_schema=1 if layer=='complete' else None)
    with pytest.raises(ValueError):inspect(directory,expected,pin)


@pytest.mark.parametrize('change',['missing_device','cpu_device','missing_phase','wrong_phase'])
def test_cuda_producer_config_must_match_execution_identity(tmp_path_factory,monkeypatch,change):
    directory,expected,meta,write=files(tmp_path_factory,monkeypatch)
    config=meta['producer_config']
    if change=='missing_device':config.pop('device')
    elif change=='cpu_device':config['device']='cpu'
    elif change=='missing_phase':config.pop('phase')
    else:config['phase']='smoke'
    with pytest.raises(ValueError,match='producer/config'):inspect(directory,expected,write())


@pytest.mark.parametrize('extra',['failure.json','state.pt.pending'])
def test_schema2_partial_artifacts_remain_rejected(tmp_path_factory,monkeypatch,extra):
    directory,expected,_,write=files(tmp_path_factory,monkeypatch);pin=write()
    (directory/extra).write_bytes(b'partial retained')
    with pytest.raises(ValueError,match='partial/failed/extra'):inspect(directory,expected,pin)


def test_cuda_state_bytes_digest_is_checked_without_loading(tmp_path_factory,monkeypatch):
    directory,expected,_,write=files(tmp_path_factory,monkeypatch);pin=write()
    (directory/'state.pt').write_bytes(b'drift')
    with pytest.raises(ValueError,match='byte/SHA'):inspect(directory,expected,pin)
