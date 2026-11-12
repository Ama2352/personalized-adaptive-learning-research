"""Junyi giữ recipe AKT, yêu cầu fold4 và typed CUDA profile tường minh."""
from dataclasses import replace
from pathlib import Path

import pytest

from knowledge_tracing.akt.config import AKTConfig,PROJECT_ROOT,ResearchCUDAExecutionProfile,validate_config


def config():
    return AKTConfig(phase='junyi-research',device='cuda',outer_fold=4,run_id='junyi-config-test',
        output_dir=PROJECT_ROOT/'experiments/akt/results/junyi-config-test',execution_enabled=True,
        max_train_users=256,max_val_users=32,max_targets_per_side=12000,max_total_targets=16000,
        max_steps=1580,max_seconds=600.,max_wall_seconds=750.,
        max_rss_bytes=6*1024**3,min_available_ram_bytes=2*1024**3)


def test_junyi_frozen_recipe_with_explicit_profile():
    validate_config(config(),cuda_profile=ResearchCUDAExecutionProfile(2*1024**3))


def test_junyi_requires_profile():
    with pytest.raises(ValueError,match='typed CUDA'):
        validate_config(config())


@pytest.mark.parametrize('field,value',[('outer_fold',0),('device','cpu'),('batch_size',8),
    ('d_model',32),('lr',.001),('n_pid',1),('graph',True),('seed',43)])
def test_wrong_domain_backend_or_recipe_rejected(field,value):
    with pytest.raises(ValueError):
        validate_config(replace(config(),**{field:value}),cuda_profile=ResearchCUDAExecutionProfile(2*1024**3))
