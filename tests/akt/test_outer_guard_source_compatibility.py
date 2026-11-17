"""Chỉ chấp nhận release guard cụ thể, không nới source checks chung."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def helper():
    spec = importlib.util.spec_from_file_location('outer_guard_compatibility',
        ROOT/'scripts/akt/free_outer_evaluation.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def release():
    value = json.loads((ROOT/'research_tracking/runs/junyi-outer-cache-release-20261117-01/SOURCE_DELTA01.json').read_text())
    return value['frozen_files'], value['proposed_frozen_plus_one_guard_files']


def test_missing_variant_pins_produces_draft_only(helper, release):
    before, after = release
    receipt = helper.build_compatibility_receipt(before, after)
    assert receipt['status'] == 'DRAFT_MISSING_VARIANT_PINS'
    with pytest.raises(ValueError, match='complete compatibility'):
        helper.validate_compatibility(receipt, checkpoint_sha256='a'*64,
            calibration_identity='b'*64, calibrated_source=helper.OLD_SOURCE,
            current_source=helper.NEW_SOURCE)


def test_valid_release_full_maps_and_exact_patch(helper, release, monkeypatch):
    before, after = release
    receipt = helper.build_compatibility_receipt(before, after,
        checkpoint_sha256='a'*64, calibration_identity='b'*64)
    monkeypatch.setattr(helper, 'runtime_source_files', lambda: dict(after))
    result = helper.validate_compatibility(receipt, checkpoint_sha256='a'*64,
        calibration_identity='b'*64, calibrated_source=helper.OLD_SOURCE,
        current_source=helper.NEW_SOURCE)
    assert result['calibration_source_sha256'] == helper.OLD_SOURCE
    assert result['inference_source_sha256'] == helper.NEW_SOURCE
    assert len(receipt['old_files']) == len(receipt['new_files']) == 77


@pytest.mark.parametrize('damage', ['source', 'extra_delta', 'checkpoint', 'calibrator', 'runtime'])
def test_any_mismatch_rejects(helper, release, monkeypatch, damage):
    before, after = release
    receipt = helper.build_compatibility_receipt(before, after,
        checkpoint_sha256='a'*64, calibration_identity='b'*64)
    runtime = dict(after)
    args = dict(checkpoint_sha256='a'*64, calibration_identity='b'*64,
                calibrated_source=helper.OLD_SOURCE, current_source=helper.NEW_SOURCE)
    if damage == 'source':
        args['current_source'] = '9'*64
    if damage == 'extra_delta':
        receipt = copy.deepcopy(receipt)
        receipt['new_files']['src/knowledge_tracing/akt/model.py'] = '9'*64
    if damage == 'checkpoint':
        args['checkpoint_sha256'] = '9'*64
    if damage == 'calibrator':
        args['calibration_identity'] = '9'*64
    if damage == 'runtime':
        runtime['src/knowledge_tracing/akt/model.py'] = '9'*64
    monkeypatch.setattr(helper, 'runtime_source_files', lambda: runtime)
    with pytest.raises(ValueError):
        helper.validate_compatibility(receipt, **args)


def test_builder_refuses_checkout_crlf_upstream_delta(helper, release):
    before, after = release
    after = dict(after)
    after['artifacts/akt/dependencies/upstream/akt.py'] = 'be2788c20cac602e86ef3a51e5294b37dd7b200f818be4e173dbd69069a3ec6d'
    with pytest.raises(ValueError):
        helper.build_compatibility_receipt(before, after)
