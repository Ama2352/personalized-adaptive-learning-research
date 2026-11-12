"""Hợp đồng workload Junyi trước khi có Torch/GPU."""
from dataclasses import replace
import json

import pytest

from knowledge_tracing.akt.config import ResearchCUDAExecutionProfile, validate_config
from knowledge_tracing.akt.research_junyi_engineering import engineering_config, file_sha, prepare_inputs, write_json


def test_one_epoch_config_retains_architecture_and_protocol():
    config = engineering_config('junyi-engineering-unit')
    validate_config(config, cuda_profile=ResearchCUDAExecutionProfile(2*1024**3))
    assert config.max_steps == 79
    assert config.max_epochs == 20
    assert config.outer_fold == 4
    assert config.max_total_targets == 13363


def test_output_json_exclusive_and_finite(tmp_path):
    path = tmp_path/'record.json'
    write_json(path, dict(complete=True))
    assert json.loads(path.read_text()) == dict(complete=True)
    with pytest.raises(FileExistsError):
        write_json(path, {})


def test_pinned_roles_checked_before_data(tmp_path):
    roles = tmp_path/'roles.json'
    roles.write_text('{}')
    with pytest.raises(ValueError, match='Pinned'):
        prepare_inputs(tmp_path, roles, cohort_sha256='0'*64, roles_sha256='0'*64)


def test_pinned_cohort_checked_before_parse(tmp_path):
    roles = tmp_path/'roles.json'
    roles.write_text('{}')
    (tmp_path/'manifest.json').write_text('{}')
    with pytest.raises(ValueError, match='Pinned'):
        prepare_inputs(tmp_path, roles, cohort_sha256='0'*64, roles_sha256=file_sha(roles))
