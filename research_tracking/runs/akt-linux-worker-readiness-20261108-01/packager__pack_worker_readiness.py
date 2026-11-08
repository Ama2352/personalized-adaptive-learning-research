"""Đóng bằng chứng đã nhận; mặc định chỉ inventory, không thực thi workload."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
WORK = Path(__file__).resolve().parent
RUN_ID = 'akt-linux-worker-readiness-20261108-01'
REPORT = ROOT / 'research_tracking/reports/akt_linux_worker_readiness_20261108.md'
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle

RAW_GROUPS = ('received', 'received-upstream-evidence02', 'received-linux-runtime02',
              'received-linux-gate02-failure', 'received-graph-fallback01',
              'received-loader-evidence02-transfer02', 'received-loader-evidence02-transfer03',
              'received-source-delta01')
SOURCES = ('build_exact_source_kit.py', 'source-manifest.json', 'build-verification.json',
           'upstream_checkout01.py', 'post_checkout_audit01.py',
           'linux_cpu_validation_driver02.py', 'graph_fallback_diagnostic01.py',
           'prepare_linux_cpu_validation_request02.py', 'test_linux_cpu_validation_driver02_env.py',
           'materialize_cached_upstream_loader01.py', 'materialize_upstream_loader03.py',
           'materialize_upstream_loader04.py', 'upstream-loader-profile01.json',
           'apply_source_delta01.py', 'linux_cpu_gate24_driver01.py',
           'prepare_source_delta_gate24_request01.py', 'prepare_source_delta_gate24_request02.py',
           'test_source_delta_gate24.py', 'test_gate24_producer02_cli.py',
           'test_loader_cache01.py', 'test_loader_transfer03.py', 'test_loader_transfer04.py',
           'SOURCE_DELTA_GATE24_SPEC01.md', 'GATE24_PRODUCER02_CLI_REVIEW.md',
           'gate24-independent-readonly-check01.json',
           'linux_cpu_dummy_worker_driver02.py', 'test_cpu_dummy_worker_driver02.py',
           'CPU_DUMMY_WORKER_NATIVE_CONTRACT_REVIEW01.md',
           'cpu-dummy-worker02-independent-review01.json', 'cpu-dummy-worker02-independent-review02.json',
           'parent_cpu_worker_review01.py', 'parent-cpu-worker-review01.json',
           'verify_worker_received01.py', 'verify_worker_received01-pre-review01.py',
           'worker-readonly-pre-review01-copy.json', 'worker-independent-readonly-check01.log',
           'worker-independent-readonly-check02.json', 'worker-independent-readonly-check02.log',
           'cpu_worker_binary_preservation01.py', 'cpu_worker_binary_chunk02.py',
           'verify_worker_durability01.py', 'worker-durability-independent-check01.json',
           'worker-durability-independent-check01.log',
           'binary01-transport-failure-normalized.json', 'record_binary01_transport_failure.py',
           'worker-transport-failure-independent-check01.json', 'parent-cpu-durability-review02.json',
           'materialize-upstream-loader03-independent-review.json',
           'materialize-upstream-loader04-independent-review.json')
LOCAL_DIRS = ('upstream-checkout01-local-validation', 'upstream-checkout01-local-validation02',
              'post-checkout-audit01-validation', 'post-checkout-audit01-validation02',
              'linux-cpu-validation02-offline-tests', 'source-delta-gate24-offline-tests01',
              'source-delta-gate24-offline-tests02', 'gate24-producer02-cli-check01')
LOCAL_TEST_DIRS = ('parallel-graph-fallback-20261108-01', 'parallel-graph-fallback-20261108-02',
                   'upstream-loader-cache01-offline-20261108-01',
                   'upstream-loader-transfer03-offline-20261108-01',
                   'upstream-loader-transfer04-offline-20261108-01')
ALLOWED = {'.json', '.py', '.md', '.log', '.xml', '.stdout', '.stderr', '.before', '.final', '.diff', '.snapshot', '.txt'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def checked_path(base, name):
    p = base / name
    if p.is_symlink() or not p.resolve().is_relative_to(base.resolve()) or not p.is_file():
        raise ValueError(f'unsafe/missing input: {p}')
    return p


def verified_receipt_entries(base, receipt):
    data = load(receipt)
    entries = data.get('copies')
    if entries is None and receipt.name in {'manifest.json', 'copy-inventory.json'}:
        entries = data.get('files')
    if isinstance(entries, dict):
        entries = [dict(value, path=name) for name, value in entries.items()]
    out = []
    for entry in entries or []:
        p = checked_path(base, entry['path'])
        expected = entry.get('sha256', entry.get('sha256_before_copy'))
        actual = digest(p)
        if actual != expected or actual != entry.get('sha256_after_copy', actual):
            raise ValueError(f'received SHA mismatch: {p}')
        if p.stat().st_size != entry['bytes']:
            raise ValueError(f'received size mismatch: {p}')
        out.append(p)
    return out


def collect(args):
    candidates, exclusions, receipts, missing = [], [], [], []

    def add(group, base, path):
        relative = path.relative_to(base).as_posix()
        parts = path.relative_to(base).parts
        if (path.is_symlink() or not path.is_file() or any(x in {'tmp', '__pycache__', '.pytest_cache'} for x in parts)
                or path.suffix.lower() not in ALLOWED or path.name == 'export-stdout.json'
                or any(x in path.name.lower() for x in ('private', 'base64', 'rpc-response', 'request-body'))):
            exclusions.append({'group': group, 'path': relative, 'reason': 'not selected text evidence'})
            return
        path.read_bytes().decode('utf-8-sig')  # Fail closed on binary data, no lossy conversion.
        candidates.append((group, relative, path))

    for name in RAW_GROUPS:
        base = WORK / name
        if not base.is_dir():
            raise ValueError(f'missing required received group: {base}')
        receipt_name = 'acceptance.json' if (base / 'acceptance.json').is_file() else (
            'manifest.json' if (base / 'manifest.json').is_file() else 'copy-inventory.json')
        receipt = checked_path(base, receipt_name)
        verified = verified_receipt_entries(base, receipt)
        # Base receipt has no copies list; verify its explicit receipt SHA separately.
        if name == 'received':
            p = checked_path(base, 'materialization-receipt.json')
            if digest(p) != load(receipt)['materialization_receipt_sha256']:
                raise ValueError('base materialization SHA mismatch')
            verified += [p, checked_path(base, 'post-checkout-audit01-result.json')]
        for p in [receipt, *verified]:
            add(name, base, p)
        receipts.append({'group': name, 'receipt_sha256': digest(receipt), 'verified_entries': len(verified)})
    for name in SOURCES:
        add('operation', WORK, checked_path(WORK, name))
    for name in LOCAL_DIRS:
        base = WORK / name
        if not base.is_dir():
            missing.append(name)
            continue
        for p in sorted(base.rglob('*')):
            if p.is_file():
                add(name, base, p)
    for name in LOCAL_TEST_DIRS:
        base = ROOT / 'artifacts/akt/local-tests' / name
        if not base.is_dir():
            raise ValueError(f'missing local check group: {base}')
        for p in sorted(base.iterdir()):
            if p.is_file():
                add(name, base, p)
    for group, base in [('gate24', args.gate24_root), ('worker', args.worker_root)]:
        if base is None:
            missing.append(f'{group} raw root not supplied; outcome not established by this packager')
            continue
        base = base.resolve()
        if not base.is_dir():
            raise ValueError(f'missing optional actual raw root: {base}')
        # Actual transferred roots must have a verification manifest/acceptance receipt.
        rs = [base / x for x in ('acceptance.json', 'manifest.json', 'copy-inventory.json') if (base / x).is_file()]
        if not rs:
            raise ValueError(f'no transfer receipt supplied for {group}')
        for receipt in rs:
            verified_receipt_entries(base, receipt)
        for p in sorted(base.rglob('*')):
            if p.is_file():
                add(group, base, p)
    if args.durability_receipt is not None:
        receipt = args.durability_receipt.resolve()
        data = load(receipt)
        if data['status'] != 'PRESERVED_EXACT_CPU_COLAB_DUMMY_ARTIFACT_BYTES' or data['binary_files'] != 4:
            raise ValueError('unexpected binary durability receipt')
        for entry in data['copies']:
            p = checked_path(ROOT, entry['local_destination'])
            if (digest(p) != entry['sha256_before_copy'] or digest(p) != entry['sha256_after_copy']
                    or p.stat().st_size != entry['bytes']):
                raise ValueError(f'durable bytes mismatch: {p}')
        before = checked_path(WORK, 'cpu-worker-binary-preservation01-before.json')
        if digest(before) != data['before_inventory_sha256']:
            raise ValueError('durability before inventory SHA mismatch')
        add('durability', receipt.parent, receipt)
        add('durability-before', WORK, before)
        transfer = WORK / 'transfer-cpu-worker-binary02'
        for name in ('acceptance.json', 'plan.json', 'first-receipt.json',
                     *(f'chunk-{i:04d}.receipt.json' for i in range(8))):
            add('binary-transfer-metadata', transfer, checked_path(transfer, name))
    delta_names = ('inventory_before.json', 'inventory_after.json',
                   'test_graph_prototype.before.py', 'test_graph_prototype.after.py')
    if args.gate24_root is None or not all((args.gate24_root / 'source-delta01' / n).is_file() for n in delta_names):
        missing.append('Delta backup/before-after inventories not supplied as raw copies')
    candidates += [('packager', Path(__file__).name, Path(__file__)),
                   ('report', REPORT.name, REPORT),
                   ('evidence-helper', 'evidence.py', ROOT / 'src/knowledge_tracing/evidence.py')]
    unique, occurrences = {}, []
    for group, relative, path in candidates:
        sha = digest(path)
        alias = f'{group}__{relative.replace("/", "__")}'
        if sha not in unique:
            unique[sha] = (alias, path)
        occurrences.append({'group': group, 'path': relative, 'source': path.relative_to(ROOT).as_posix(),
                            'bytes': path.stat().st_size, 'sha256_before_copy': sha,
                            'archive_name': unique[sha][0]})
    binary_omissions = []
    if args.worker_root is not None and (args.worker_root / 'acceptance.json').is_file():
        binary_omissions = load(args.worker_root / 'acceptance.json').get('binary_omissions', [])
    return unique, {'kind': 'LINUX_WORKER_READINESS_INPUT_INVENTORY', 'occurrences': occurrences,
                    'unique_sha_count': len(unique), 'received_receipts': receipts,
                    'gaps': missing, 'gaps_scope': 'Missing selected text groups only; binary omission ledger is separate.',
                    'worker_text_export_binary_omissions': binary_omissions, 'exclusions': exclusions,
                    'gate24_raw_supplied': args.gate24_root is not None,
                    'worker_raw_supplied': args.worker_root is not None,
                    'durability_receipt_supplied': args.durability_receipt is not None,
                    'scope': 'Hash integrity only; stage outcome/scientific validity require independent review.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gate24-root', type=Path)
    parser.add_argument('--worker-root', type=Path)
    parser.add_argument('--durability-receipt', type=Path)
    parser.add_argument('--inventory-output', type=Path, required=True)
    parser.add_argument('--close-after-parent-review', action='store_true')
    parser.add_argument('--reviewed-report-sha256')
    args = parser.parse_args()
    unique, inventory = collect(args)
    args.inventory_output.parent.mkdir(parents=True, exist_ok=True)
    with args.inventory_output.open('x', encoding='utf-8') as f:
        json.dump(inventory, f, ensure_ascii=False, indent=2)
        f.write('\n')
    if not args.close_after_parent_review:
        print(json.dumps({'status': 'PREPARATION_ONLY_NO_BUNDLE_CREATED', 'unique': len(unique),
                          'occurrences': len(inventory['occurrences']), 'gaps': inventory['gaps']}))
        return
    if args.gate24_root is None or digest(REPORT) != args.reviewed_report_sha256:
        raise ValueError('closure requires actual Gate24 raw root and exact parent-reviewed report SHA')
    if args.worker_root is not None and args.durability_receipt is None:
        raise ValueError('worker closure requires independent local binary durability receipt')
    sources = list(dict.fromkeys(path for _, path in unique.values()))
    with record_evidence_run(ROOT, RUN_ID, metadata={'kind': 'LINUX_CPU_WORKER_ENGINEERING_INVESTIGATION',
            'input_unique_sha_count': len(unique), 'worker_raw_supplied': args.worker_root is not None},
            sources=sources, note='# Hồ sơ kỹ thuật Linux CPU\n\nGiữ failure lịch sử; xem report snapshot và aliases trong inventory.\nKhông chứng minh CUDA/image/cost forecast hoặc hiệu quả học tập.\nReceipt durability transport_sha256 là hash envelope được lắp local, không phải raw MCP response; frame/archive proofs ở metadata transfer02.\nKhông lưu ZIP/wheels/venv/private MCP/base64/envelope/checkpoint/Parquet trong bundle này.\n') as out:
        for sha, (alias, path) in unique.items():
            payload = path.read_bytes()
            if hashlib.sha256(payload).hexdigest() != sha:
                raise ValueError(f'input changed before copy: {path}')
            target = out / alias
            with target.open('xb') as f:
                f.write(payload)
            if digest(target) != sha or digest(path) != sha:
                raise ValueError(f'copy/source SHA drift: {path}')
        inventory['sha256_after_copy'] = {name: digest(out / name) for name, _ in unique.values()}
        (out / 'copy-inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(verify_evidence_bundle(ROOT / 'research_tracking/runs' / RUN_ID)))


if __name__ == '__main__':
    main()
