"""Persist authorized pure engineering metadata analysis; no tests or target calls."""
import hashlib
import importlib.util
import json
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent


def digest(raw): return hashlib.sha256(raw).hexdigest()


def main():
    start = time.monotonic()
    ledger_path = HERE / 'pure-test-ledger01.json'
    ledger = json.loads(ledger_path.read_bytes())
    if ledger['cumulative_seconds'] >= 30: raise RuntimeError('same30s pure budget exhausted')
    output = HERE / 'compatibility-engineering-summary01.json'
    receipt_path = HERE / 'compatibility-engineering-summary01-receipt.json'
    if output.exists() or receipt_path.exists(): raise FileExistsError('exclusive analysis evidence')
    names = ('packet_validator01.py', 'test_packet_validator01.py', 'write_compatibility_summary01.py')
    before = {name: digest((HERE / name).read_bytes()) for name in names}
    spec = importlib.util.spec_from_file_location('engineering_fixture_source', HERE / 'test_packet_validator01.py')
    tests = importlib.util.module_from_spec(spec); spec.loader.exec_module(tests)
    _, blobs, _ = tests.fixture()  # In-memory, engineering-only; NO unittest methods are invoked.
    v = tests.v
    if digest(blobs['selected_report']) != v.REPORT_SHA or digest(blobs['linux_lock']) != v.LOCK_SHA:
        raise ValueError('immutable metadata input pin mismatch')
    target = json.loads(blobs['target_compatibility'])['facts']
    result = v.evaluate_compatibility(json.loads(blobs['selected_report']), blobs['linux_lock'], target,
                                      expected_bindings=target['bindings'])
    value = dict(role='ENGINEERING_STORED_METADATA_EVALUATION_NOT_ACTUAL_TARGET',
        target_marker_origin='HISTORICAL_CPU_LINUX_RESOLVER_ENVIRONMENT_NOT_FRESH_GPU_HOST',
        tag_origin='SYNTHETIC_UNION_OF_SELECTED_WHEEL_TAGS_NOT_MEASURED_HOST_TAGS',
        source_sha256=before['packet_validator01.py'], selected_report_sha256=v.REPORT_SHA,
        lock_sha256=v.LOCK_SHA, marker_environment=target['marker_environment'], fixture_tags=target['tags'],
        dependency_ledger_canonical_sha256=digest(v.canonical(result['dependency_rows'])), evaluation=result,
        execution_authorized=False, target_processes=0, pip_network_GPU_model_calls=0,
        limitation_vi='Kết quả semantics metadata thuần; không fresh ABI/tags, wheel bytes, install hoặc CUDA proof.')
    raw = json.dumps(value, indent=2, allow_nan=False).encode() + b'\n'
    if len(raw) > 2 * 1024**2: raise ValueError('bounded analysis output')
    with output.open('xb') as stream: stream.write(raw)
    after = {name: digest((HERE / name).read_bytes()) for name in names}
    elapsed = time.monotonic() - start
    ledger['cumulative_seconds'] += elapsed
    receipt = dict(role=value['role'], before=before, after=after, source_unchanged=before == after,
        output=dict(path=output.name, bytes=len(raw), sha256=digest(raw)), analysis_seconds=elapsed,
        cumulative_pure_seconds=ledger['cumulative_seconds'], cumulative_cap_seconds=30,
        test_methods_invoked=0, actual_target_processes=0, pip_network_GPU_model_calls=0)
    ledger['attempts'].append(dict(path=output.name, kind='PURE_METADATA_ANALYSIS_NOT_TEST',
        returncode=0 if before == after and ledger['cumulative_seconds'] <= 30 else 1,
        controller_posthash_seconds=elapsed))
    with receipt_path.open('x', encoding='utf-8') as stream: json.dump(receipt, stream, indent=2)
    ledger_path.write_text(json.dumps(ledger, indent=2) + '\n')
    print(json.dumps(receipt))
    return 0 if before == after and ledger['cumulative_seconds'] <= 30 else 1


if __name__ == '__main__': raise SystemExit(main())
