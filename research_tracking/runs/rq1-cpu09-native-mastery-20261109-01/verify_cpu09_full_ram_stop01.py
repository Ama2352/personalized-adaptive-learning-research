"""Kiểm hậu kỳ lượt dừng RAM, không import replay hoặc mô hình."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
contract_path = PREP / 'rq1_cpu09_targeted_full_contract01.json'
assert hashlib.sha256(contract_path.read_bytes()).hexdigest() == '6cfd2cfbe6d3398ea96128c2dcf72a1cad9da052c82b1289a9f6527afc6822d8'
contract = json.loads(contract_path.read_bytes())
outer = json.loads((PREP / contract['outer_name'] / 'final.json').read_bytes())
assert outer['status'] == 'REJECTED_KEEP_NEW_FULL_OPERATION_NO_RETRY'
assert outer['receipt']['cleanup_accepted'] is True and outer['receipt']['job_active_after_cleanup'] == 0
assert outer['environment_restored'] is True and outer['resources']['monitor_stopped'] is True
assert outer['resources']['terminated_owned_job'] is True
assert outer['resources']['observed_minimum_available_ram_bytes'] < contract['limits']['min_available_ram_bytes']
assert outer['validation'] is None and outer['source_input_after'] == {}
records = {}
for name, expected in (contract['bindings'] | contract['historical_reference_inputs']).items():
    path = ROOT / name
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected['sha256'], name
    if 'bytes' in expected:
        assert len(raw) == expected['bytes'], name
    records[name] = dict(bytes=len(raw), sha256=expected['sha256'])
inner = ROOT / contract['output_relative']
files = {path.name: dict(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
         for path in inner.iterdir()}
assert set(files) == {'native_metadata.json', 'pure_checks.json', 'reservation.json'}
proof = dict(status='VERIFIED_SOURCE_INTEGRITY_AFTER_RAM_TERMINATION_NOT_REPLAY_ACCEPTANCE',
             source_files_checked=len(records), source_after=records, actual_worker_outputs=files,
             full_parity_completed=False, truth_evaluation_completed=False,
             actual_constructor_and_update_counts='UNKNOWN_AFTER_HARD_TERMINATION',
             reservation_upper_bounds=contract['direct_call_caps'],
             job_active_after_cleanup=0, environment_restored=True, monitor_stopped=True,
             minimum_available_ram_bytes=outer['resources']['observed_minimum_available_ram_bytes'],
             elapsed_before_final_seconds=outer['elapsed_before_receipt_seconds'])
with (PREP / 'cpu09_full_ram_stop_postcheck01.json').open('x', encoding='utf-8') as stream:
    json.dump(proof, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({key: value for key, value in proof.items() if key not in ('source_after', 'actual_worker_outputs')}))
