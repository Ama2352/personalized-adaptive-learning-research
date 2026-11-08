"""Dry inventory mặc định; closure chỉ sau root duyệt exact report+inventory SHA."""
import argparse
import hashlib
import json
from pathlib import Path

W = Path(__file__).resolve().parent
ROOT = W.parents[3]
RUN = 'akt-gpu-host-preparation-20261108-01'
REPORT = ROOT / 'research_tracking/reports/akt_gpu_host_preparation_20261108.md'


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def selected():
    # Explicit phase roots; no traversal of private RPC/temp/venv/transport folders.
    rows = []
    for phase in ('gpu10-hidden-audit01', 'gpu10-host-discovery01', 'gpu10-cold-bootstrap01', 'gpu10-cold-installer01'):
        directory = W / phase
        for path in sorted(directory.rglob('*')):
            if not path.is_file(): continue
            relative = path.relative_to(directory)
            if '__pycache__' in relative.parts: raise ValueError('unexpected bytecode in selected prep')
            # Repeated freeze indexes add no distinct source/attempt evidence; run receipts carry pre/post pins.
            if path.name.startswith('freeze-inventory'): continue
            rows.append((phase + '-' + '-'.join(relative.parts[:-1]), path))
    for name in ('GPU_HOST_HIDDEN_AUDIT_CONTRACT01.md', 'GPU_HOST_HIDDEN_AUDIT_CONTRACT01_ADDENDUM.md',
                 'COLD_GPU_HOST_PREPARATION_CONTRACT01.md', 'gpu-host-preparation-public-facts01.json',
                 'normalize_gpu_host_preparation_facts01.py', 'actual-startup-facts02.json',
                 'actual-startup-facts03.json', 'actual-startup-facts02-provenance.json',
                 'actual-startup-facts03-provenance.json', 'startup-facts01-cell.py',
                 'startup-facts02-cell.py', 'startup-facts03-cell.py'):
        rows.append(('contract-public-facts', W / name))
    # Small reused source/profile/metadata inputs, not a copy of historical CPU bundles.
    for name in ('discovery02.py', 'discovery_profile01.json'):
        rows.append(('reused-discovery-input', W / 't4-discovery01' / name))
    old = W.parent / 'gpu08-linux-20261108-01/received/resolution-attempt01'
    for name in ('pip-report.json', 'candidate-linux-cuda.lock.txt', 'resolution.json'):
        rows.append(('reused-metadata-input', old / name))
    rows.extend([('report', REPORT), ('packager', Path(__file__)),
                 ('evidence-helper', ROOT / 'src/knowledge_tracing/evidence.py')])
    return rows


def inventory():
    unique = {}; occurrences = []; total = 0
    for group, path in selected():
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(ROOT):
            raise ValueError('unsafe/missing selected text input: ' + str(path))
        body = path.read_bytes()
        if len(body) > 2 * 1024**2: raise ValueError('per-input2MiB bound')
        body.decode('utf-8-sig')
        sha = hashlib.sha256(body).hexdigest()
        alias = group.rstrip('-') + '__' + path.name
        if sha not in unique: unique[sha] = (alias, path); total += len(body)
        occurrences.append(dict(source_path=path.relative_to(ROOT).as_posix(), bytes=len(body),
            sha256_before_copy=sha, archive_name=unique[sha][0]))
    if total > 5 * 1024**2: raise ValueError('selected unique text total5MiB bound')
    value = dict(kind='GPU_HOST_PREPARATION_ONLY_DRY_COPY_INVENTORY', run_id=RUN,
        occurrences=occurrences, input_occurrences=len(occurrences), unique_sha_inputs=len(unique),
        unique_input_bytes=total, scope_vi='Local mocks/source review + stored CPU startup facts, không actual GPU host/bootstrap/install/audit.',
        exclusions=['raw private RPC/tracebacks', 'encoded request/cell transport payloads', 'ZIP/wheels/venv/cache',
                    'model/checkpoint/prediction/realdata binaries', 'whole historical CPU bundles', 'unrelated graph lifecycle trials'])
    return unique, value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory-output', type=Path)
    parser.add_argument('--close-after-root-review', action='store_true')
    parser.add_argument('--reviewed-report-sha256')
    parser.add_argument('--approved-inventory', type=Path)
    parser.add_argument('--approved-inventory-sha256')
    args = parser.parse_args()
    unique, value = inventory()
    if not args.close_after_root_review:
        if args.inventory_output is None: parser.error('--inventory-output required for dry mode')
        raw = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
        with args.inventory_output.open('xb') as stream: stream.write(raw)
        print(json.dumps(dict(status='DRY_INVENTORY_ONLY_BUNDLE_NOT_CREATED',
            occurrences=len(value['occurrences']), unique_inputs=len(unique), bytes=value['unique_input_bytes'],
            inventory_sha256=hashlib.sha256(raw).hexdigest(), report_sha256=digest(REPORT))))
        return
    if digest(REPORT) != args.reviewed_report_sha256 or args.approved_inventory is None:
        raise ValueError('exact root-reviewed report/inventory required')
    if digest(args.approved_inventory) != args.approved_inventory_sha256:
        raise ValueError('approved dry inventory bytes mismatch')
    if json.loads(args.approved_inventory.read_bytes()) != value:
        raise ValueError('sources changed since approved dry inventory')
    import sys
    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    note = ('# Chuẩn bị GPU-host, chưa actual GPU readiness\n\n'
        'Local mocks/AST/metadata cho warm20/generic9/cold24/packet41; stored CPU startup facts chỉ là baseline. '
        'Không hardware change/remote/GPU/model/optimizer/install trong các phase chuẩn bị. '
        'Giữ cold17methods16PASS1FAIL→17PASS→24PASS và packet39methods28PASS7FAIL4ERROR→39PASS→41PASS; '
        'static findings không bị relabel fabricated RED. Xem report snapshot và full478row engineering metadata ledger.\n\n'
        'Mọi source/text copies SHA trước=sau, SHA trùng chỉ archive một lần và giữ aliases trong copy inventory. '
        'Không private RPC/request encoded payload/ZIP/wheel/venv/binary hoặc toàn historical bundles. '
        'Metadata/receipt compatibility không attestation fresh host/tags/wheel bytes/runtime/install; '
        'old CPU-v3 guards unchanged. Warm persistence chưa proven; cold descriptor/pip/startup/tags còn pending. '
        'Closure chỉ integrity archive, không execution authority hoặc scientific/GPU PASS.\n')
    with record_evidence_run(ROOT, RUN, metadata=dict(kind='GPU_HOST_PREPARATION_LOCAL_ENGINEERING_ONLY',
        unique_inputs=len(unique), actual_fresh_GPU_host=False, actual_GPU_bootstrap_audit_install=False,
        model_optimizer_steps=0, reviewed_report_sha256=args.reviewed_report_sha256,
        approved_dry_inventory_sha256=args.approved_inventory_sha256),
        sources=[p for _, p in unique.values()], note=note) as out:
        for expected, (alias, path) in unique.items():
            body = path.read_bytes()
            if hashlib.sha256(body).hexdigest() != expected: raise ValueError('input drift before copy')
            with (out / alias).open('xb') as stream: stream.write(body)
            if digest(out / alias) != expected or digest(path) != expected:
                raise ValueError('source/copy SHA mismatch')
        value['sha256_after_copy'] = {alias: digest(out / alias) for alias, _ in unique.values()}
        with (out / 'copy-inventory.json').open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps(verify_evidence_bundle(ROOT / 'research_tracking/runs' / RUN)))


if __name__ == '__main__': main()
