"""Lưu publication E7 đã nghiệm thu, không chạy lại phân tích hoặc sửa canonical."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PUB = PREP/'thesis-rq1-e7-publication01'
BUNDLE = ROOT/'research_tracking/runs/rq1-mastery-ready-masking-20261109-01'
RUN = 'thesis-rq1-e7-writing-20261109-01'
MANIFEST_SHA = '9cbb7a276b750bf079f544ba69a4d0cf1ea28b89140707957630630a20aa9a4b'
FILES = (
    ('before.md', PUB/'before.md', '59228c370e519770c74cb442dd7e1833e53df6b490d76b8febc1987221335fa0'),
    ('before.sources.json', PUB/'before.sources.json', 'ea446f94ac906fe0674ea133935d6730fc32635fce9463779228d3f0bb0478b3'),
    ('published.md', ROOT/'research_tracking/reports/THESIS_RQ1_MECHANISMS_DRAFT_20261109.md', 'f44318746bd77f6d5a10e3a8acd2a3899249245823ec96065c8f31c55f39d02f'),
    ('published.sources.json', ROOT/'research_tracking/reports/THESIS_RQ1_MECHANISMS_DRAFT_20261109.sources.json', '09c6165d731448d84f2863e36a67d945c431aed6549cacf4b47da90290af85fc'),
    ('plan.json', PUB/'plan.json', 'ef39a0b920daaf2a78a71378d7548e180011b6985db438d83131045423c03344'),
    ('publication.json', PUB/'publication.json', '424841ac89fd66bbbf6d2723e617fc86ff0e3d0d0ff1f00f68fb378178da2aca'),
    ('publish_helper.py', PREP/'publish_thesis_rq1_e7_01.py', '8aa9ca1d8a5afd456a9774d3764c6c45d3ec5fdf8c49402cea547096d24505f6'),
    ('candidate.md', PREP/'thesis_rq1_e7_candidate01.md', '590227b64bc6f5ff156bd717bafc37beaa90cc29c26fba14b1a7f43c92576d5f'),
    ('candidate.sources.json', PREP/'thesis_rq1_e7_candidate01.sources.json', '6da8354dbaeb9248bbb13fbd4c16651a8dacb273b1fcaab88450623541cff100'),
    ('supervisor_insert_draft.md', PREP/'SUPERVISOR_MASKING_INSERT_DRAFT01.md', 'fbd33dfb07dbbdca7de3a98fa8b551fe12ecc4db8bff5df373ecda22c209c294'),
)
GENERATED = ('README.md', 'execution.log', 'copy_inventory.json', 'reference_sources.json')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve() == path, 'physical workspace file')
    cursor = ROOT
    for part in path.relative_to(ROOT).parts:
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'no file aliases')
    need(path.is_file() and path.stat().st_size <= 4*1024**2, 'bounded evidence file')
    raw = path.read_bytes()
    need(len(raw) == path.stat().st_size, 'stable input bytes')
    return raw


def sha(path):
    return hashlib.sha256(read(path)).hexdigest()


def parse(path):
    return json.loads(read(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry', action='store_true')
    mode.add_argument('--close', action='store_true')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT/'.venv', 'repository .venv only')
    destination = ROOT/'research_tracking/runs'/RUN
    need(not destination.exists(), 'exclusive writing bundle, no mutation of closed evidence')
    copies = {alias: (path, pin) for alias, path, pin in FILES}
    copies['archiver.py'] = (Path(__file__).resolve(), sha(Path(__file__)))
    inventory = {}
    for alias, (path, pin) in copies.items():
        need(sha(path) == pin, 'publication/candidate source SHA '+alias)
        inventory[alias] = dict(source=path.relative_to(ROOT).as_posix(), sha256=pin, bytes=path.stat().st_size)
    plan, receipt = parse(PUB/'plan.json'), parse(PUB/'publication.json')
    need(receipt['status'] == 'PUBLISHED_E7_PAIR' and receipt['plan_sha256'] == FILES[4][2]
         and receipt['manifest_sha256'] == plan['manifest_sha256'] == MANIFEST_SHA
         and receipt['tests_or_model_or_git_run'] is False and receipt['historical_candidates_unchanged'] is True,
         'actual successful publication receipt, not prepare intention')
    expected_pair = {path.relative_to(ROOT).as_posix(): pin for _, path, pin in FILES[2:4]}
    need(receipt['published_sha256'] == expected_pair and receipt['replacements'] == list(expected_pair), 'exact published pair')
    for alias, _, pin in FILES[2:4]:
        need(sha(PUB/alias) == plan['prepared_sha256'][alias] == pin, 'prepared pair equals actual canonical publication')
    old = read(PUB/'before.md')
    need(len(old) == plan['prior_markdown_prefix_bytes'] == 28517
         and read(FILES[2][1])[:len(old)] == read(FILES[7][1])[:len(old)] == old, 'exact E4–E6/whole prior prefix')
    mapping = parse(FILES[3][1])
    need(mapping['draft_sha256'] == FILES[2][2] and mapping['source_count'] == len(mapping['sources_sha256']) == 80,
         'eighty original refs and current published draft identity')
    references = dict(mapping['sources_sha256'])
    references.update({(BUNDLE/'manifest.json').relative_to(ROOT).as_posix(): MANIFEST_SHA,
        'src/knowledge_tracing/evidence.py': '414e3d834c46d081c7d9c05beff17a3e2d9c479a0e121394aabe321929235e49'})
    references.update({(PUB/name).relative_to(ROOT).as_posix(): plan['prepared_sha256'][name]
                       for name in ('published.md', 'published.sources.json')})
    for relative, pin in references.items():
        need(sha(ROOT/relative) == pin, 'original reference changed '+relative)
    evidence = mapping['e7_evidence']
    need(evidence['manifest_sha256'] == MANIFEST_SHA and evidence['manifest_pending_root'] is False,
         'actual closed masking binding')
    manifest = parse(BUNDLE/'manifest.json')
    need(manifest['status'] == 'completed' and len(manifest['outputs_sha256']) == 44, 'closed forty-four-output scientific bundle')
    assertions = evidence['durable_numeric_assertions']
    need(len(assertions) == len(evidence['numeric_assertions']) == plan['numeric_pointers'] == 18, 'eighteen original/durable pointers')
    for original, durable in zip(evidence['numeric_assertions'], assertions, strict=True):
        need(durable['source_path'] == evidence['durable_source_aliases'][original['source_path']]
             and durable['json_pointer'] == original['json_pointer'] and durable['value'] == original['value'], 'exact source alias, no numeric rewrite')
        path = ROOT/durable['source_path']
        need(path.parent == BUNDLE and manifest['outputs_sha256'][path.name] == sha(path)
             == references[original['source_path']], 'durable numeric source bound to actual manifest')
        value = parse(path)
        for part in durable['json_pointer'].lstrip('/').split('/'):
            key = part.replace('~1', '/').replace('~0', '~')
            value = value[int(key)] if isinstance(value, list) else value[key]
        need(type(value) is type(durable['value']) and value == durable['value'], 'actual durable numeric pointer')
    outputs = sorted((*copies, *GENERATED))
    need(len(outputs) == len(set(outputs)) == 15, 'fifteen writing outputs excluding manifest')
    dry = dict(status='VERIFIED_PUBLICATION_WRITING_INPUTS_NOT_NEW_ANALYSIS', run_id=RUN,
        copies=inventory, references=references, outputs=outputs, outputs_excluding_manifest=15,
        source_references=80, durable_numeric_pointers=18, masking_manifest_sha256=MANIFEST_SHA)
    if args.dry:
        print(json.dumps(dry, ensure_ascii=False, indent=2))
        return
    with (PREP/'thesis_rq1_e7_copy_inventory_before01.json').open('x', encoding='utf-8') as stream:
        json.dump(dry, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    sources = list(dict.fromkeys([path for path, _ in copies.values()]+[ROOT/name for name in references]))
    note = ('# Bổ sung E7 vào bản thảo RQ1\n\n'
        'Giữ cặp trước/sau, candidate, plan và receipt publication thật. '
        'Nội dung cũ28517bytes được bảo toàn,80nguồn và18numeric pointers được đối chiếu. '
        'Nguồn nghiên cứu là bundle masking44 đã đóng, không copy lại gzip hoặc toàn bộ bundle. '
        'Phân loại30snapshot là18khôngchild+8childMkhôngexposure+4đồngthời, không attribution duy nhất. '
        'R là tập ban đầu, chưa là hardpermission hoặc bài phục vụ. Không chạy lại phân tích, model hoặc mô phỏng.\n')
    with record_evidence_run(ROOT, RUN, metadata=dict(kind='THESIS_RQ1_E7_WRITING_PUBLICATION',
        source_references=80, durable_numeric_pointers=18, prior_prefix_bytes=28517,
        analysis_rerun=False, new_independent_N=0, research_RQ_completion=False), sources=sources, note=note) as directory:
        checked = {}
        for alias, (path, pin) in copies.items():
            raw = read(path)
            need(hashlib.sha256(raw).hexdigest() == pin, 'source before copy')
            with (directory/alias).open('xb') as stream:
                stream.write(raw)
            need(sha(directory/alias) == sha(path) == pin and len(raw) == inventory[alias]['bytes'], 'copy/source after SHA')
            checked[alias] = dict(inventory[alias], copied_sha256=pin, source_after_sha256=sha(path))
        for name, pin in references.items():
            need(sha(ROOT/name) == pin, 'reference post-copy SHA')
        (directory/'copy_inventory.json').write_text(json.dumps(checked, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        (directory/'reference_sources.json').write_text(json.dumps(references, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        need(sorted(p.name for p in directory.iterdir() if p.name != 'manifest.json') == outputs, 'exact writing output set')
    verified = verify_evidence_bundle(destination)
    need(verified['artifacts'] == 15, 'exact closed writing count')
    print(json.dumps(dict(verification=verified, manifest_sha256=sha(destination/'manifest.json'))))


if __name__ == '__main__':
    main()
