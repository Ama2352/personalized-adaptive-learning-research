"""Kiểm hậu kỳ launcher kết thúc đột ngột, không chạy model hoặc đọc cache contents."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
contract_path = PREP / 'rq1_cpu09_targeted_full_contract02.json'
assert hashlib.sha256(contract_path.read_bytes()).hexdigest() == 'd45e81f581f7305bb06829f2c36796f58fa0133a7a33e444c2901d4f7c4128aa'
contract = json.loads(contract_path.read_bytes())
outer_path = PREP / contract['outer_name'] / 'final.json'
outer = json.loads(outer_path.read_bytes())
receipt = outer['receipt']
assert outer['status'] == 'REJECTED_KEEP_NEW_FULL_OPERATION_NO_RETRY'
assert receipt['returncode'] == receipt['worker_returncode_before_cleanup'] == 3221225786
assert receipt['GO_released'] is True and receipt['accepted'] is False
assert receipt['cleanup_accepted'] is True and receipt['job_active_after_cleanup'] == 0
assert receipt['job_active_before_cleanup'] == 0 and receipt['errors'] == receipt['cleanup_errors'] == []
assert outer['environment_restored'] is True and outer['resources']['monitor_stopped'] is True
assert outer['resources']['terminated_owned_job'] is False and outer['resources']['errors'] == []
records = {}
for name, expected in (contract['bindings'] | contract['historical_reference_inputs']).items():
    path = ROOT / name
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected['sha256'] and len(raw) == expected['bytes'], name
    records[name] = dict(bytes=len(raw), sha256=expected['sha256'])
inner = ROOT / contract['output_relative']
files = {path.name: dict(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
         for path in inner.iterdir()}
assert set(files) == {'native_metadata.json', 'pure_checks.json'}
metadata = json.loads((inner / 'native_metadata.json').read_bytes())
assert metadata['phase_closed'] is True and metadata['blocked_bootstrap_attempts'] == 0
proof = dict(status='VERIFIED57_SOURCE_INPUTS_AND_UNEXPECTED_LAUNCHER_EXIT_NOT_REPLAY_ACCEPTANCE',
             source_files_checked=len(records), source_after=records, actual_worker_outputs=files,
             launcher_returncode=3221225786, launcher_returncode_hex='0xC000013A',
             native_worker_direct_exit_code_recorded=False, cause='UNKNOWN',
             full_parity_completed=False, truth_evaluation_completed=False,
             actual_constructor_and_update_counts='UNKNOWN_WITHOUT_TERMINAL_NATIVE_RECEIPT',
             metadata_phase_closed=True, job_active_before_cleanup=0, job_active_after_cleanup=0,
             environment_restored=True, monitor_stopped=True, resource_monitor_errors=[],
             minimum_available_ram_bytes=outer['resources']['observed_minimum_available_ram_bytes'],
             observed_family_peak_rss_bytes=outer['resources']['observed_family_peak_rss_bytes'],
             outer_terminal_sha256=hashlib.sha256(outer_path.read_bytes()).hexdigest(),
             elapsed_before_final_seconds=outer['elapsed_before_receipt_seconds'])
assert proof['source_files_checked'] == 57
with (PREP / 'cpu09_full02_terminal_postcheck01.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(proof, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({key: value for key, value in proof.items() if key not in ('source_after', 'actual_worker_outputs')}))
