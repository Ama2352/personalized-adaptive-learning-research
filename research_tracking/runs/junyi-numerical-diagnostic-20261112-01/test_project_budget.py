"""Kiểm admission toàn KLTN bằng ledger giả, không gọi cloud."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location('numerical_budget_unit',ROOT/'experiments/akt/modal_junyi_numerical_probe.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def ledger():
    return dict(status='USER_PREAPPROVED_BOUNDED_TRANCHES_TOTAL_PROJECT_CAP',extra_payment_allowed=False,
        automatic_monthly_budget_reset=False,total_project_credit_ceiling_usd=30,
        historical_usage_reserved_upper_usd=2,safety_and_final_inference_reserve_usd=3,
        new_allocations=[dict(id='diagnostic',cap_usd=.2,status='PREPARED_NOT_DISPATCHED')])


def request():
    return dict(allocation_id='diagnostic',authorized_batch_usd=.2,reserved_usd_per_run=.2)


def test_old_billing_delta_does_not_restrict_new_project_allocation():
    value = request()
    value['baseline_metered_usd'] = .56
    decision = MODULE.validate_project_budget(ledger(),value,1.)
    assert decision['conservative_project_envelope_usd']==5.2


def test_provider_metered_above_historical_upper_is_reserved():
    decision = MODULE.validate_project_budget(ledger(),request(),4.)
    assert decision['conservative_project_envelope_usd']==7.2


def test_allocation_caps_and_safety_reject_budget_exhaustion():
    value = ledger()
    value['new_allocations'].append(dict(id='other',cap_usd=25,status='RESERVED'))
    with pytest.raises(PermissionError,match='exhausted'):
        MODULE.validate_project_budget(value,request(),1.)


def test_exact_total_project_ceiling_is_supported_with_decimal_arithmetic():
    value = ledger()
    value['new_allocations'].append(dict(id='other',cap_usd=24.8,status='RESERVED'))
    assert MODULE.validate_project_budget(value,request(),1.)['conservative_project_envelope_usd']==30


@pytest.mark.parametrize('field,value',[('reserved_usd_per_run',.21),('authorized_batch_usd',.21)])
def test_per_run_cap_is_enforced_independently(field,value):
    query = request()
    query[field] = value
    with pytest.raises(PermissionError,match='explicit'):
        MODULE.validate_project_budget(ledger(),query,1.)


def test_missing_or_duplicate_allocation_is_rejected():
    value = ledger()
    value['new_allocations'].append(deepcopy(value['new_allocations'][0]))
    with pytest.raises(ValueError,match='Unique'):
        MODULE.validate_project_budget(value,request(),1.)
    query = request()
    query['allocation_id'] = 'missing'
    with pytest.raises(ValueError,match='Unique'):
        MODULE.validate_project_budget(ledger(),query,1.)


def test_monthly_reset_cannot_expand_project_cap():
    value = ledger()
    value['automatic_monthly_budget_reset'] = True
    with pytest.raises(PermissionError,match='total-project'):
        MODULE.validate_project_budget(value,request(),1.)
