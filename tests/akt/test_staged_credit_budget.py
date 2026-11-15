"""Đúng đơn vị credit, vẫn giữ hard cap và hành vi ledger gross cũ."""
from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'experiments/akt'))
from modal_junyi_staged import validate_stage_project_budget


@pytest.fixture
def billing():
    return dict(billing=dict(metered_cost='29.05668106', billed_cost='0',
        adjustments={'Credits': '-28.88', 'Free Storage': '-0.17607560',
                     'Network Egress Allowance': '-0.00060546', 'Plan Cost': '0'}))


def capture_amount(ledger, request, value):
    return dict(provider_metered_usd=value, test_amount=value)


def test_existing_gross_ledger_keeps_original_amount_and_result(billing):
    before = deepcopy(billing)
    result = validate_stage_project_budget({}, {}, billing, capture_amount)
    assert result == dict(provider_metered_usd=29.05668106, test_amount=29.05668106)
    assert billing == before


def test_credit_ledger_excludes_free_allowances_and_adds_rounding_margin(billing):
    result = validate_stage_project_budget(dict(provider_cost_basis='free_credit_consumption_v1'),
        {}, billing, capture_amount)
    assert result['test_amount'] == pytest.approx(28.89)
    assert result['provider_metered_gross_usd'] == 29.05668106
    assert 'provider_metered_usd' not in result


def test_credit_ledger_keeps_higher_reported_credit_consumption(billing):
    billing['billing']['adjustments']['Credits'] = '-28.90'
    result = validate_stage_project_budget(dict(provider_cost_basis='free_credit_consumption_v1'),
        {}, billing, capture_amount)
    assert result['test_amount'] == pytest.approx(28.91)


@pytest.mark.parametrize('field,value', [('metered_cost', 'NaN'), ('metered_cost', '-1'),
    ('billed_cost', 'Infinity'), ('billed_cost', '.01')])
def test_credit_ledger_rejects_invalid_or_paid_amounts(billing, field, value):
    billing['billing'][field] = value
    with pytest.raises((ValueError, PermissionError)):
        validate_stage_project_budget(dict(provider_cost_basis='free_credit_consumption_v1'),
            {}, billing, capture_amount)


def test_unknown_basis_cannot_silently_reduce_budget_amount(billing):
    with pytest.raises(ValueError):
        validate_stage_project_budget(dict(provider_cost_basis='unknown'), {}, billing, capture_amount)


def test_credit_normalization_preserves_validator_cap_rejection(billing):
    def exhausted(ledger, request, value):
        assert value == pytest.approx(28.89)
        raise PermissionError('Total cap exhausted')
    with pytest.raises(PermissionError, match='Total cap exhausted'):
        validate_stage_project_budget(dict(provider_cost_basis='free_credit_consumption_v1'),
            {}, billing, exhausted)
