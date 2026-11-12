"""Protocol batch128 có identity riêng, giữ quy tắc batch4 lịch sử."""
from dataclasses import replace
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from knowledge_tracing.akt.config import AKTConfig, ResearchCUDAExecutionProfile, validate_config


def config():
    run = 'unit-junyi-batch128'
    default = AKTConfig()
    return replace(default,phase='junyi-research',run_id=run,
        output_dir=default.project_root/'experiments/akt/results'/run,
        device='cuda',outer_fold=4,max_train_users=126774,max_val_users=15847,
        max_targets_per_side=13347331,max_total_targets=266946620,max_steps=36360,
        max_seconds=1500,max_wall_seconds=1600,max_rss_bytes=8*1024**3,
        min_available_ram_bytes=256*1024**2)


def test_batch128_requires_separate_protocol():
    profile = ResearchCUDAExecutionProfile(16*1024**3,recipe_id='cgakt-cuda-fp32-batch128-v2')
    validate_config(config(),cuda_profile=ResearchCUDAExecutionProfile(2*1024**3))
    with pytest.raises(ValueError):
        validate_config(replace(config(),batch_size=128),cuda_profile=profile)
    validate_config(replace(config(),batch_size=128,
        protocol_version='akt-nr-exercise-v2-batch128'),cuda_profile=profile)


@pytest.mark.parametrize('batch',[4,32,64,True])
def test_batch128_protocol_rejects_other_batch_sizes(batch):
    with pytest.raises(ValueError):
        validate_config(replace(config(),batch_size=batch,
            protocol_version='akt-nr-exercise-v2-batch128'),
            cuda_profile=ResearchCUDAExecutionProfile(16*1024**3,recipe_id='cgakt-cuda-fp32-batch128-v2'))


def test_batch128_protocol_rejects_simulator_scope():
    with pytest.raises(ValueError):
        validate_config(replace(config(),phase='simulator-research',outer_fold=0,
            batch_size=128,protocol_version='akt-nr-exercise-v2-batch128'),
            cuda_profile=ResearchCUDAExecutionProfile(16*1024**3,recipe_id='cgakt-cuda-fp32-batch128-v2'))


def test_legacy_vram_bound_and_recipe_binding_are_preserved():
    with pytest.raises(ValueError):
        ResearchCUDAExecutionProfile(16*1024**3)
    with pytest.raises(ValueError):
        ResearchCUDAExecutionProfile(16*1024**3+1,recipe_id='cgakt-cuda-fp32-batch128-v2')
    with pytest.raises(ValueError):
        validate_config(config(),cuda_profile=ResearchCUDAExecutionProfile(
            16*1024**3,recipe_id='cgakt-cuda-fp32-batch128-v2'))
    with pytest.raises(ValueError):
        validate_config(replace(config(),batch_size=128,
            protocol_version='akt-nr-exercise-v2-batch128'),
            cuda_profile=ResearchCUDAExecutionProfile(2*1024**3))
