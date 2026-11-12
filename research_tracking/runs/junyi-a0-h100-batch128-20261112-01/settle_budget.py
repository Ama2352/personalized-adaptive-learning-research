"""Đóng các khoản dự phòng đã hết lượt để tránh cộng trùng với usage đã đo."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BUNDLE=Path(__file__).resolve().parent
ledger_path=ROOT/'research_tracking/COMPUTE_BUDGET.json'
original=ledger_path.read_bytes()
ledger=json.loads(original)
stop=json.loads((BUNDLE/'stop-confirmation-final.json').read_text())
assert stop['all_owned_stopped'] is True and stop['containers']==[]
assert ledger['total_project_credit_ceiling_usd']==30
assert ledger['extra_payment_allowed'] is False
anchor=json.loads((ROOT/'experiments/akt/results/modal-junyi-a0-b128-h100-20261112-01/billing-before.json').read_text())
final=json.loads((BUNDLE/'billing-final.json').read_text())
rate=.001097+4*.0000131+12*.00000222
bounds=[]
for sequence in (1,2,3):
    execution=f'modal-junyi-a0-b128-h100-20261112-{sequence:02d}'
    native=ROOT/'experiments/akt/results'/execution
    receipt=json.loads((native/'receipt.json').read_text())
    guard=json.loads((native/'app-budget-guard.json').read_text())
    assert receipt['download_inventory_verified'] and guard['stop_acknowledged']
    assert receipt['worker_result']['gpu']=='NVIDIA H100 80GB HBM3'
    acknowledgement=next(row for row in guard['events'] if row['event']=='stop_acknowledged')
    # Timer bắt đầu trước khi tạoApp/GPU. Thêm60s cho biên dừng container.
    seconds=acknowledgement['elapsed_seconds']+60
    upper=seconds*rate
    assert upper<=3
    bounds.append(dict(execution=execution,guard_elapsed_plus60_seconds=seconds,
        rate_upper_usd_per_second=rate,compute_upper_usd=upper))
anchored_upper=float(anchor['billing']['metered_cost'])+sum(row['compute_upper_usd'] for row in bounds)
historical_upper=max(anchored_upper,float(final['billing']['metered_cost']))
snapshot=BUNDLE/'compute-budget-before-settlement.json'
with snapshot.open('xb') as stream:
    stream.write(original)
closed=ledger.setdefault('closed_reservations',[])
for allocation in ledger['new_allocations']:
    row=dict(allocation)
    row['financial_record_status']='CLOSED_AFTER_ALL_OWNED_APPS_STOPPED'
    row['settlement_note_vi']='Mức dự phòng ban đầu được giữ trong hồ sơ. Chi đã phát sinh nằm trong anchor và cận H100; phần chưa dùng được giải phóng. Trạng thái nghiên cứu gốc giữ nguyên.'
    closed.append(row)
ledger['new_allocations']=[]
ledger['historical_usage_reserved_upper_usd']=historical_upper
ledger['a0_h100_settlement']=dict(anchor_metered_usd=float(anchor['billing']['metered_cost']),
    anchor_file='experiments/akt/results/modal-junyi-a0-b128-h100-20261112-01/billing-before.json',
    anchor_note_vi='Usage trước H100 đã bao các lượt cũ. Các App cũ và CPU Gate đã dừng trước khi chạy H100. Khoản dự phòng chưa chạy được đóng theo ưu tiên A0, không bỏ nhiệm vụ nghiên cứu.',
    h100_bounds=bounds,historical_upper_usd=historical_upper,
    metered_snapshot_usd=float(final['billing']['metered_cost']),
    provider_credits_used_usd=abs(float(final['billing']['adjustments']['Credits'])),
    safety_reserve_usd=ledger['safety_and_final_inference_reserve_usd'],
    prior_ledger_sha256=hashlib.sha256(original).hexdigest(),
    evidence='research_tracking/runs/junyi-a0-h100-batch128-20261112-01/stop-confirmation-final.json')
assert historical_upper+ledger['safety_and_final_inference_reserve_usd']<30
ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(BUNDLE/'budget-settlement.json').write_text(json.dumps(ledger['a0_h100_settlement'],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='CLOSED_RESERVATIONS_WITHOUT_DOUBLE_COUNTING',historical_upper_usd=historical_upper,
    credits_remaining_snapshot=30-abs(float(final['billing']['adjustments']['Credits'])),
    preserved_reservation_records=len(closed),active_reservations=0)))
