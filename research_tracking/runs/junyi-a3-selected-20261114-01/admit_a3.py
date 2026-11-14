"""Kiểm checkout, đối soát dự phòng cũ và phân bổ A3 trong trần30USD."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRIOR = ROOT / 'research_tracking/runs/junyi-confidence-completion-20261114-01'
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'experiments/akt')]
from junyi_staged_io import verify_project, sha, write_new
from knowledge_tracing.akt.provenance import verify_upstream
from modal_junyi_main_selected import validate_project_budget


def main():
    snapshot = ROOT / 'artifacts/akt/staged/junyi-a3-expert-20261114-03'
    inventory = verify_project(snapshot)
    upstream = snapshot / 'project/artifacts/akt/dependencies/upstream'
    os.environ.update(GIT_OPTIONAL_LOCKS='0', GIT_CONFIG_COUNT='3',
                      GIT_CONFIG_KEY_0='core.fsmonitor', GIT_CONFIG_VALUE_0='false',
                      GIT_CONFIG_KEY_1='safe.directory', GIT_CONFIG_VALUE_1=str(upstream),
                      GIT_CONFIG_KEY_2='core.autocrlf', GIT_CONFIG_VALUE_2='false')
    identity = verify_upstream(upstream, '01b7e8d7d7c862cabc9467108e3e7f2555653a88')
    assert identity == json.loads((PRIOR / 'upstream-portable-inventory.json').read_text())['identity']
    toplevel = subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', '--show-toplevel'], text=True).strip()
    assert Path(toplevel).resolve() == upstream.resolve()
    write_new(HERE / 'snapshot-dependency-verification.json', dict(
        status='PASS_SNAPSHOT_DEPENDENCY_AND_INVENTORY', variant='A3',
        files=len(inventory['files']), dependency=identity, inputs_sha256=sha(snapshot / 'INPUTS.json')))
    assert json.loads((HERE / 'containers-before.json').read_text()) == []
    ledger_path = ROOT / 'research_tracking/COMPUTE_BUDGET.json'
    original = ledger_path.read_bytes()
    ledger = json.loads(original)
    assert ledger['new_allocations'] == []
    anchor = ledger['last_a1_compact_accounting_snapshot']
    old_upper = anchor['historical_upper_usd']
    anchor_metered = float(anchor['provider_snapshot']['billing']['metered_cost'])
    later_upper = ledger['historical_usage_reserved_upper_usd'] - old_upper
    current = json.loads((HERE / 'billing-before.json').read_text())
    metered = float(current['billing']['metered_cost'])
    assert float(current['billing']['billed_cost']) == 0
    # Duy trì toàn bộ cận tài nguyên sau mốc A1 và thêm1USD cho điều chỉnh trễ.
    # Không dùng số metering hiện tại như hóa đơn đã khóa sổ.
    revised_upper = max(anchor_metered + later_upper, metered) + 1.0
    assert revised_upper < ledger['historical_usage_reserved_upper_usd']
    reconciliation = dict(status='RECONCILED_OLD_RESERVATION_WITH_DELAY_MARGIN',
        previous_ledger_sha256=hashlib.sha256(original).hexdigest(),
        old_historical_upper_usd=ledger['historical_usage_reserved_upper_usd'],
        old_a1_anchor_upper_usd=old_upper, old_a1_anchor_metered_usd=anchor_metered,
        later_resource_upper_preserved_usd=later_upper,
        fresh_metered_usd=metered, latency_adjustment_margin_usd=1.0,
        revised_historical_upper_usd=revised_upper, containers_empty=True,
        safety_and_final_inference_reserve_usd=ledger['safety_and_final_inference_reserve_usd'],
        reason_vi='Mốc billing sau A1 đã được kiểm lại sau gần19giờ, mọi container đã dừng. '
        'Giải phóng phần cận A1 chưa dùng, giữ toàn bộ cận các lượt sau đó và thêm1USD '
        'dự phòng billing trễ. Trần30USD và dự phòng cuối3USD giữ trong ledger.')
    write_new(HERE / 'budget-reconciliation.json', reconciliation)
    ledger.setdefault('reservation_reconciliations', []).append(dict(
        evidence=str((HERE / 'budget-reconciliation.json').relative_to(ROOT)).replace('\\', '/'),
        previous_historical_upper_usd=ledger['historical_usage_reserved_upper_usd'],
        revised_historical_upper_usd=revised_upper))
    ledger['historical_usage_reserved_upper_usd'] = revised_upper
    execution = json.loads((HERE / 'a3-training-request01.json').read_text())
    ledger['new_allocations'] = [dict(id=execution['allocation_id'], cap_usd=2.6,
        purpose_vi='A3 selected-fit Junyi, một H100 tối đa30phút, checkpoint và stop barrier.')]
    admission = validate_project_budget(ledger, execution, metered)
    write_new(HERE / 'budget-admission-local.json', admission)
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    state = json.loads((HERE / 'STATE.json').read_text())
    state.update(status='A3_LOCAL_ADMITTED_WAITING_PROVIDER_CHECK', token_refresh_required=False,
                 budget_admission='budget-admission-local.json', snapshot_verified=True)
    (HERE / 'STATE.json').write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=state['status'], budget=admission)))


if __name__ == '__main__':
    main()
