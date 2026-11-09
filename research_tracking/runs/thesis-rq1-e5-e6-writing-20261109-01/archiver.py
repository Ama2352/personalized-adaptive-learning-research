"""Đóng gói phần viết E5–E6 sau Root publication, không sửa canonical/source."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
WORK = Path(__file__).resolve().parent
RUN = 'thesis-rq1-e5-e6-writing-20261109-01'
BASE = 'THESIS_RQ1_MECHANISMS_DRAFT_20261109'
BEFORE = WORK/'thesis-rq1-e5e6-before01'
OLD_PINS = {
    'before_inventory.json': (BEFORE/'inventory_before.json', '34bed7dca564632c94ce99165bc38c65759c8bcca07cbf51112316ea63e4c015'),
    'before_draft.md': (BEFORE/(BASE+'.md'), '92500c9afe44c83f9df58614cf1a023d0660c1aaefbbd485268d9b3e68e422aa'),
    'before_sources.json': (BEFORE/(BASE+'.sources.json'), 'a15bea67fef44c8344ba6fd37b1d87fc78e6ad5c26d15e126130caa14405855b'),
    'addition_fragment.md': (WORK/'THESIS_RQ1_E5_E6_ADDITION01.md', 'e2fbb6a5e8c75205567863e2c4ba8040dad7c18c5c0295f4322d6d4cc9071103'),
}
GENERATED = ('README.md', 'execution.log', 'copy_inventory.json', 'reference_sources.json')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--draft-sha256', required=True)
    parser.add_argument('--sources-sha256', required=True)
    parser.add_argument('--proof-file', required=True, help='Tên JSON proof đã freeze trực tiếp trong prep')
    parser.add_argument('--proof-sha256', required=True)
    parser.add_argument('--dry', action='store_true')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT/'.venv', 'repository .venv required')
    need(all(re.fullmatch('[0-9a-f]{64}', value) for value in
             (args.draft_sha256, args.sources_sha256, args.proof_sha256)), 'external final SHA required')
    need(Path(args.proof_file).name == args.proof_file and args.proof_file.endswith('.json'), 'prep proof basename required')
    out = ROOT/'research_tracking/runs'/RUN
    need(not out.exists(), 'exclusive new writing bundle required')
    draft = ROOT/'research_tracking/reports'/(BASE+'.md')
    source_map = ROOT/'research_tracking/reports'/(BASE+'.sources.json')
    copies = dict(OLD_PINS)
    copies['draft.md'] = (draft, args.draft_sha256)
    copies['sources.json'] = (source_map, args.sources_sha256)
    copies['root_publication_proof.json'] = (WORK/args.proof_file, args.proof_sha256)
    copies['archiver.py'] = (Path(__file__).resolve(), sha(Path(__file__)))
    inventory = {}
    for alias, (path, expected) in copies.items():
        need(path.is_file() and not path.is_symlink() and sha(path) == expected, 'selected input SHA '+alias)
        inventory[alias] = dict(source=path.relative_to(ROOT).as_posix(), sha256=expected, bytes=path.stat().st_size)
    need(sha(WORK/(BASE+'.candidate03.md')) == args.draft_sha256, 'canonical text differs from reviewed candidate03')
    need(isinstance(json.loads((WORK/args.proof_file).read_text(encoding='utf-8')), dict), 'Root proof JSON object required')
    metadata = json.loads(source_map.read_text(encoding='utf-8'))
    references = metadata['sources_sha256']
    need(metadata['draft_sha256'] == args.draft_sha256 and metadata['source_count'] == len(references) == 29,
         'published draft/source-count binding required')
    for relative, expected in references.items():
        path = PurePosixPath(relative)
        need(not path.is_absolute() and path.as_posix() == relative and '..' not in path.parts
             and '\\' not in relative and ':' not in relative and re.fullmatch('[0-9a-f]{64}', expected),
             'canonical source reference required')
        need(sha(ROOT/relative) == expected, 'reference SHA '+relative)
    outputs = sorted((*copies, *GENERATED))
    dry = dict(status='DRY_VERIFIED_WRITING_INPUTS_NOT_CLOSED', run_id=RUN, copies=len(copies),
               outputs_excluding_manifest=len(outputs), outputs=outputs, inventory=inventory,
               reference_sources_sha256=references, new_independent_N=0, model_calls=0)
    if args.dry:
        print(json.dumps(dry, ensure_ascii=False, indent=2))
        return
    with (WORK/'thesis_rq1_e5e6_copy_inventory_before01.json').open('x', encoding='utf-8') as stream:
        json.dump(dry, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    sources = list(dict.fromkeys([path for path, _ in copies.values()]+[ROOT/name for name in references]))
    note = ('# Bổ sung phần viết E5–E6 cho bản thảo RQ1\n\n'
            'Giữ hai bản canonical đã được Root công bố, hai snapshot trước sửa, inventory, fragment và proof review/publication. '
            'Tham chiếu29nguồn theo SHA, không nhân đôi dữ liệu nghiên cứu. Không chạy lại thí nghiệm hoặc tạo mẫu độc lập mới. '
            'Draft chương luận văn không đồng nghĩa RQ1 hoàn tất; không có kết quả fitted CG-AKT hoặc lợi ích học tập mới.\n')
    with record_evidence_run(ROOT, RUN, metadata=dict(kind='THESIS_RQ1_E5_E6_WRITING_ONLY',
        new_independent_N=0, model_calls=0, canonical_draft_sha256=args.draft_sha256,
        canonical_sources_sha256=args.sources_sha256, publication_proof_sha256=args.proof_sha256),
        sources=sources, note=note) as directory:
        checked = {}
        for alias, (path, expected) in copies.items():
            raw = path.read_bytes()
            need(hashlib.sha256(raw).hexdigest() == expected, 'input drift before copy')
            with (directory/alias).open('xb') as stream:
                stream.write(raw)
            need(sha(directory/alias) == sha(path) == expected, 'copy/source post-SHA drift')
            need((directory/alias).stat().st_size == inventory[alias]['bytes'], 'copied byte count')
            checked[alias] = dict(inventory[alias], copy_sha256=expected, source_after_sha256=sha(path))
        for relative, expected in references.items():
            need(sha(ROOT/relative) == expected, 'reference changed during copying')
        (directory/'copy_inventory.json').write_text(json.dumps(checked, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        (directory/'reference_sources.json').write_text(json.dumps(references, indent=2)+'\n', encoding='utf-8')
        need(sorted(p.name for p in directory.iterdir() if p.name != 'manifest.json') == outputs, 'exact output membership')
    verification = verify_evidence_bundle(out)
    need(verification['artifacts'] == len(outputs), 'exact closed output count')
    print(json.dumps(dict(verification=verification, manifest_sha256=sha(out/'manifest.json'))))


if __name__ == '__main__':
    main()
