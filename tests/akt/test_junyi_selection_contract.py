"""Selected-only giữ split và nguồn; grant không mở refit/calibration."""
from dataclasses import replace
import json

import pytest

from knowledge_tracing.akt.config import DataPaths, ResearchCUDAExecutionProfile, load_config
from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView
from knowledge_tracing.akt.research_junyi_engineering import engineering_config
from knowledge_tracing.akt.research_junyi_roles import make_junyi_research_roles
from knowledge_tracing.akt.research_junyi_selection import JunyiSelectedInputs,validate_selected_grant


@pytest.fixture
def inputs(tmp_path):
    roles = make_junyi_research_roles([(str(i),i%5,'development') for i in range(100)])
    train = JunyiPhaseView(roles,'select_train80',roles.train_users,roles.identity)
    selection = JunyiPhaseView(roles,'raw_selection10',roles.selection_users,roles.identity)
    return JunyiSelectedInputs(DataPaths(*(tmp_path/name for name in ('canonical','assignments','manifest','split'))),
        train,selection,1000,100,'a'*64)


def grant(inputs):
    return dict(status='USER_APPROVED',approval_reference='test-fixture',purpose='main_selected',workload_epochs=20,
        binding=dict(candidate_id='A0',phase='junyi_selected_only',config_sha256='b'*64,
            inputs_identity=inputs.identity,gate_sha256='c'*64,runtime_sha256='d'*64))


def validate(inputs,receipt):
    validate_selected_grant(engineering_config('junyi-contract-unit'),inputs,receipt,
        config_sha256='b'*64,gate_sha256='c'*64,runtime_sha256='d'*64)


def test_grant_fixed_train_selection(inputs):
    validate(inputs,grant(inputs))


@pytest.mark.parametrize('field,value',[('status','PASS'),('purpose','refit90'),('workload_epochs',21),
    ('workload_epochs',True),('workload_epochs',0),('approval_reference','')])
def test_foreign_or_unbounded_grant_rejected(inputs,field,value):
    receipt=grant(inputs);receipt[field]=value
    with pytest.raises(PermissionError):
        validate(inputs,receipt)


@pytest.mark.parametrize('field',['candidate_id','phase','config_sha256','inputs_identity','gate_sha256','runtime_sha256'])
def test_binding_change_rejected(inputs,field):
    receipt=grant(inputs);receipt['binding'][field]='foreign'
    with pytest.raises(PermissionError):
        validate(inputs,receipt)


def test_main_cannot_end_at_one_epoch(inputs):
    receipt=grant(inputs);receipt['workload_epochs']=1
    with pytest.raises(PermissionError):
        validate(inputs,receipt)
    receipt['purpose']='bounded_engineering'
    validate(inputs,receipt)


def test_main_requires_full_roles(inputs):
    smaller=replace(inputs,train=JunyiPhaseView(inputs.train.roles,'select_train80',inputs.train.users[:2],inputs.train.roles.identity))
    with pytest.raises(PermissionError):
        validate(smaller,grant(smaller))


def test_role_phase_mismatch(inputs):
    with pytest.raises(ValueError):
        replace(inputs,selection=inputs.train)


def test_cuda_profile_config_loader(tmp_path):
    from dataclasses import asdict
    config=engineering_config('junyi-config-loader')
    path=tmp_path/'config.json';path.write_text(json.dumps(asdict(config),default=str))
    assert load_config(path,cuda_profile=ResearchCUDAExecutionProfile(2*1024**3))==config
    with pytest.raises(ValueError):
        load_config(path)
