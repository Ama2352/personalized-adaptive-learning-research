"""Đóng hai bundle metadata hữu hạn; không chạy test, Torch, model hoặc solver."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
INVENTORIES = {
    'main60': 'main60_graph_binding_archive_inputs01.json',
    'sakt': 'sakt_selected_archive_inputs01.json',
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', choices=INVENTORIES, required=True)
    parser.add_argument('--inventory-sha256', required=True)
    parser.add_argument('--dry', action='store_true')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT/'.venv', 'repository venv only')
    inventory_path = PREP/INVENTORIES[args.bundle]
    need(sha(inventory_path) == args.inventory_sha256, 'external exact input inventory')
    inventory = json.loads(inventory_path.read_bytes())
    destination = ROOT/'research_tracking/runs'/inventory['run_id']
    need(not destination.exists(), 'exclusive new bundle')
    copies = dict(inventory['copies'])
    copies['input_inventory.json'] = dict(path=inventory_path.relative_to(ROOT).as_posix(), sha256=sha(inventory_path), bytes=inventory_path.stat().st_size)
    copies['archiver.py'] = dict(path=Path(__file__).resolve().relative_to(ROOT).as_posix(), sha256=sha(Path(__file__)), bytes=Path(__file__).stat().st_size)
    need(len(copies) == len(set(copies)) and all('/' not in name and '\\' not in name for name in copies), 'unique flat aliases')
    before = {}
    for alias, record in copies.items():
        path = ROOT/record['path']
        need(path.is_file() and not path.is_symlink() and not getattr(path,'is_junction',lambda:False)(), 'physical small source')
        need(path.stat().st_size == record['bytes'] <= 2**20 and sha(path) == record['sha256'], 'source bytes/hash '+alias)
        before[alias] = dict(record)
    need(sum(v['bytes'] for v in copies.values()) <= 8*2**20, 'compact bundle copy budget8MiB')
    for name, digest in inventory['references_sha256'].items():
        need(sha(ROOT/name) == digest, 'closed/reference SHA '+name)
    for ref in inventory['native_references']:
        path = ROOT/ref['path']
        need(path.is_file() and path.stat().st_size == ref['bytes'], 'native reference physical size')
        if ref['verify_sha_at_archive']:
            need(sha(path) == ref['sha256'], 'native checkpoint physical SHA')
    # Revalidate actual small terminal admission, never infer acceptance from intent.
    actual = json.loads((ROOT/inventory['accepted_outer']).read_bytes())
    need(actual['status'] == inventory['accepted_status'] and actual['errors'] == [], 'actual accepted terminal')
    receipt = actual['owned_receipt']
    need(receipt['accepted'] is True and receipt['returncode'] == 0 and receipt['cleanup_accepted'] is True
         and receipt['job_active_after_cleanup'] == 0, 'actual owned cleanup')
    outputs = sorted([*copies, 'README.md', 'execution.log', 'copy_inventory.json', 'reference_sources.json'])
    dry = dict(status='DRY_VERIFIED_NOT_CLOSED', run_id=inventory['run_id'], outputs_excluding_manifest=len(outputs),
        copies=len(copies), copy_bytes=sum(v['bytes'] for v in copies.values()), outputs=outputs,
        input_inventory_sha256=args.inventory_sha256, new_training_or_test_calls=0)
    if args.dry:
        print(json.dumps(dry, ensure_ascii=False, indent=2)); return
    before_path = PREP/(args.bundle+'_selected_archive_before01.json')
    with before_path.open('x', encoding='utf-8') as stream:
        json.dump(dict(dry=dry, inventory_before_copy=before), stream, ensure_ascii=False, indent=2); stream.write('\n')
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    sources = list(dict.fromkeys([ROOT/v['path'] for v in copies.values()]+[ROOT/n for n in inventory['references_sha256']]))
    with record_evidence_run(ROOT, inventory['run_id'], metadata=inventory['metadata'], sources=sources, note=inventory['readme_vi']) as directory:
        checked = {}
        for alias, record in copies.items():
            path = ROOT/record['path']; raw = path.read_bytes()
            need(hashlib.sha256(raw).hexdigest() == record['sha256'], 'source changed before copy')
            with (directory/alias).open('xb') as stream: stream.write(raw)
            need(sha(directory/alias) == sha(path) == record['sha256'], 'source/copy after SHA')
            checked[alias] = dict(record, copy_sha256=sha(directory/alias), source_after_sha256=sha(path))
        refs = dict(references_sha256=inventory['references_sha256'], native_references=inventory['native_references'],
            original_source_inventory=inventory['original_source_inventory'], limitation_vi=inventory['reference_limit_vi'])
        (directory/'copy_inventory.json').write_bytes((json.dumps(checked, ensure_ascii=False, indent=2)+'\n').encode())
        (directory/'reference_sources.json').write_bytes((json.dumps(refs, ensure_ascii=False, indent=2)+'\n').encode())
        for name, digest in inventory['references_sha256'].items(): need(sha(ROOT/name) == digest, 'reference after SHA')
        for ref in inventory['native_references']:
            path = ROOT/ref['path']; need(path.stat().st_size == ref['bytes'], 'native reference after size')
            if ref['verify_sha_at_archive']: need(sha(path) == ref['sha256'], 'native checkpoint after SHA')
        need(sorted(f.name for f in directory.iterdir() if f.name != 'manifest.json') == outputs, 'exact complete output population')
    verification = verify_evidence_bundle(destination)
    need(verification['artifacts'] == len(outputs), 'exact closed count')
    print(json.dumps(dict(run_id=inventory['run_id'], verification=verification,
        manifest_sha256=sha(destination/'manifest.json'), copy_bytes=dry['copy_bytes'], new_training_or_test_calls=0)))


if __name__ == '__main__':
    main()
