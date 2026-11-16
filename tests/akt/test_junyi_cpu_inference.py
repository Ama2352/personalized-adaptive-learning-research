"""Admission CPU inference mới, metadata builder, giữ chặn research training."""
from dataclasses import asdict,replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import zipfile

import pytest

from knowledge_tracing.akt.config import AKTConfig,PROJECT_ROOT,validate_config
from knowledge_tracing.akt.research_junyi_inference import (
    JunyiCPUInferenceBudget,inspect_cpu_refit_export,_identity)
from knowledge_tracing.akt.research_junyi_roles import make_junyi_research_roles
from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView,JunyiResearchEncoding
from knowledge_tracing.akt.encoding import ExerciseEncoding
from knowledge_tracing.shared_kt import StableVocabulary


def config():
    return AKTConfig(phase='junyi-inference',device='cpu',outer_fold=4,batch_size=128,
        protocol_version='akt-nr-exercise-v2-batch128',run_id='cpu-inference-test',
        output_dir=PROJECT_ROOT/'experiments/akt/results/cpu-inference-test',execution_enabled=True,
        max_train_users=1,max_val_users=1,max_targets_per_side=128,max_total_targets=128,max_steps=2,
        max_seconds=120.,max_wall_seconds=120.,max_rss_bytes=2*1024**3,min_available_ram_bytes=256*1024**2)


def budget():
    return JunyiCPUInferenceBudget(128,128,1,120.,2*1024**3,256*1024**2,128)


def test_cpu_inference_accepts_frozen_batch128_without_cuda_profile():
    validate_config(config())


@pytest.mark.parametrize('field,value',[('device','cuda'),('batch_size',4),('d_model',32),
    ('outer_fold',0),('seed',43),('n_pid',1),('graph',True),('lr',.001)])
def test_cpu_inference_does_not_relax_architecture_or_domain(field,value):
    with pytest.raises(ValueError):
        validate_config(replace(config(),**{field:value}))


def test_research_training_phase_still_requires_cuda_profile():
    with pytest.raises(ValueError,match='typed CUDA'):
        validate_config(replace(config(),phase='junyi-research'))


@pytest.mark.parametrize('field,value',[('max_targets',True),('max_users',0),
    ('max_seconds',float('inf')),('prediction_batch_size',129)])
def test_cpu_budget_rejects_invalid_or_unbounded_values(field,value):
    with pytest.raises(ValueError):
        replace(budget(),**{field:value})


@pytest.fixture
def portable(tmp_path):
    roles=make_junyi_research_roles([(str(i),i%5,'development') for i in range(20)])
    train=JunyiPhaseView(roles,'select_train80',roles.train_users,roles.identity)
    refit=JunyiPhaseView(roles,'refit_union90',tuple(sorted((*roles.train_users,*roles.selection_users))),roles.identity)
    encoding={scope:JunyiResearchEncoding(ExerciseEncoding(StableVocabulary(('A','B')),dict(A=2,B=2)),view)
              for scope,view in [('80',train),('90',refit)]}
    members={'inputs/config.json':json.loads(json.dumps(asdict(replace(config(),phase='junyi-research',device='cuda')),default=str)),
             'inputs/roles.json':asdict(roles),'inputs/epoch_plan.json':dict(roles_identity=roles.identity,identity='a'*64)}
    for scope,view in [('80',train),('90',refit)]:
        name='inputs/encoding'+scope+'.json'
        members[name]=dict(schema_version=1,values=['A','B'],train_support_students=dict(A=2,B=2))
        raw=json.dumps(members[name]).encode()
        members['inputs/encoding'+scope+'_receipt.json']=dict(status='JUNYI_TRAIN_ENCODING_FITTED',
            phase_scope=view.scope,fit_view_identity=view.identity,encoding_identity=encoding[scope].identity,
            encoding_file_sha256=hashlib.sha256(raw).hexdigest())
    index=dict(model='A0_JUNYI_REFIT',phase='refit90',identity=dict(phase='junyi_refit90',variant='A0',
        encoding=encoding['90'].identity,condition=None,plan_sha256='a'*64))
    def write():
        inventory={}
        with zipfile.ZipFile(tmp_path/'SUPPORT.zip','w') as archive:
            for name,value in members.items():
                raw=json.dumps(value).encode();archive.writestr(name,raw)
                inventory[name]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            archive.writestr('INVENTORY.json',json.dumps(inventory))
        index['support_sha256']=hashlib.sha256((tmp_path/'SUPPORT.zip').read_bytes()).hexdigest()
        (tmp_path/'MODEL_INDEX.json').write_text(json.dumps(index))
        return hashlib.sha256((tmp_path/'MODEL_INDEX.json').read_bytes()).hexdigest()
    return tmp_path,members,index,write


def test_metadata_builder_reuses_encoding_and_preserves_training_fields(portable):
    path,members,index,write=portable
    pin=write()
    assets=inspect_cpu_refit_export(path,expected_index_sha256=pin,output=config().output_dir,
        run_id=config().run_id,budget=budget())
    assert assets['config'].phase=='junyi-inference' and assets['config'].device=='cpu'
    assert assets['config'].batch_size==members['inputs/config.json']['batch_size']==128
    assert assets['encoding'].identity==index['identity']['encoding']
    assert assets['origin'].fit_view.scope=='select_train80'
    assert not any(p.suffix=='.pt' for p in path.iterdir())


@pytest.mark.parametrize('field',['roles','encoding','plan'])
def test_metadata_builder_rejects_wrong_lineage(portable,field):
    path,members,index,write=portable
    if field=='roles':members['inputs/epoch_plan.json']['roles_identity']='0'*64
    if field=='encoding':members['inputs/encoding90_receipt.json']['encoding_identity']='0'*64
    if field=='plan':index['identity']['plan_sha256']='0'*64
    pin=write()
    with pytest.raises(ValueError):
        inspect_cpu_refit_export(path,expected_index_sha256=pin,output=config().output_dir,
            run_id=config().run_id,budget=budget())


def test_normal_optimizer_entrypoints_reject_inference_only_config():
    import psutil
    import sys
    if 'torch' not in sys.modules and psutil.virtual_memory().available<640*1024**2:
        pytest.skip('Torch import requires bounded startup headroom')
    from knowledge_tracing.akt.model import AKTAdapter
    from knowledge_tracing.akt.research_junyi_graph_model import JunyiGraphAKTAdapter
    fake=SimpleNamespace(config=config())
    for method in (AKTAdapter.step,AKTAdapter.fit,JunyiGraphAKTAdapter.step):
        with pytest.raises(ValueError,match='inference-only'):
            method(fake,None,None)
    with pytest.raises(ValueError,match='inference-only'):
        JunyiGraphAKTAdapter.collate_training(fake,[])


@pytest.mark.parametrize("operation", ["export", "fit"])
def test_local_cli_rejects_full_outputs_before_loading_weights_or_creating_files(operation):
    import importlib.util
    from pathlib import Path

    launcher = Path(__file__).resolve().parents[2] / "scripts/akt/run_junyi_calibration.py"
    spec = importlib.util.spec_from_file_location("junyi_calibration_local_cli", launcher)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises(ValueError, match="cloud-first artifact sink"):
        module.execute({"operation": operation})
