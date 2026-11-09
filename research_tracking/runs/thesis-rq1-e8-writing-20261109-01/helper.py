"""ROOT chuẩn bị, xuất bản cặp E8 rồi lưu hồ sơ viết nhỏ; không chạy nghiên cứu."""
from copy import deepcopy
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OUT = PREP/'thesis-rq1-e8-publication01'
TARGET = ROOT/'research_tracking/reports/THESIS_RQ1_MECHANISMS_DRAFT_20261109.md'
TARGET_MAP = TARGET.with_suffix('.sources.json')
CANDIDATE = PREP/'THESIS_RQ1_MECHANISMS_DRAFT_20261109.e8_candidate01.md'
SOURCE_MAP = PREP/'THESIS_RQ1_MECHANISMS_DRAFT_20261109.e8_candidate01.sources.json'
APPEND = PREP/'THESIS_RQ1_E8_APPEND_CANDIDATE01.md'
PREPARATION = PREP/'thesis-e8-source-preparation01.json'
RUN = 'thesis-rq1-e8-writing-20261109-01'
DESTINATION = ROOT/'research_tracking/runs'/RUN
OLD = {TARGET: 'f44318746bd77f6d5a10e3a8acd2a3899249245823ec96065c8f31c55f39d02f',
       TARGET_MAP: '09c6165d731448d84f2863e36a67d945c431aed6549cacf4b47da90290af85fc'}
PINS = {CANDIDATE: 'd329b198aeb6eebeb39c6ee201ba0fa0d60466b8f11334dd72515e5e6cc45982',
        SOURCE_MAP: 'fd37a0d9a1804f49da77a095ed2ae170fa061023222f88d8720ec6f71c567a50',
        APPEND: '20a1d77262e7efd5ae430930d572c73b108b112a27ab791cc6bfda581b75ed06',
        PREPARATION: '9bc5237085138ea25a13778a6cab7f34566575b3f7b19afed5d020c25e9b3a3f'}
SCIENTIFIC = {
    'research_tracking/runs/paper1-concept-local-invariance-20261109-01':
        ('e4176e08eb84d91c07351a073beca2305e18f028774ffe21f11cfe8a196ad191', 17),
    'research_tracking/runs/paper1-seeded-domain-smoke-engineering-20261109-01':
        ('a12e409be45a3c900154b2f7f1d1118bd2e3cda59a66476d6cb32b886da85131', 28),
}
EVIDENCE_WRITER_SHA = '414e3d834c46d081c7d9c05beff17a3e2d9c479a0e121394aabe321929235e49'
GENERATED = ('README.md', 'execution.log', 'copy_inventory.json', 'reference_sources.json',
             'reviewed_archive_dry.json', 'closure_review.json')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def physical(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve() == path, 'Physical workspace path')
    cursor = ROOT
    for part in path.relative_to(ROOT).parts:
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'Không alias')
    return path


def read(path):
    physical(path)
    need(path.is_file() and path.stat().st_size <= 8*1024**2, 'File metadata/source≤8MiB')
    raw = path.read_bytes()
    need(len(raw) == path.stat().st_size, 'Stable read size')
    return raw


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(path):
    return digest(read(path))


def parse(path):
    return json.loads(read(path))


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')


def write(path, raw):
    physical(path)
    need(len(raw) <= 2*1024**2, 'Small writing output≤2MiB')
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def pointer(value, path):
    for token in path.lstrip('/').split('/'):
        token = token.replace('~1', '/').replace('~0', '~')
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def replace_value(text, key, value):
    matches = list(re.finditer(r'(?m)^  '+re.escape(json.dumps(key))+':', text))
    need(len(matches) == 1, 'Unique top-level publication key '+key)
    start = matches[0].end()
    while text[start].isspace():
        start += 1
    _, end = json.JSONDecoder().raw_decode(text, start)
    return text[:start]+json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+text[end:]


def validate_sources(mapping):
    refs = mapping['sources_sha256']
    need(mapping['source_count'] == len(refs) == 94, 'Exact94source references')
    need(sum((ROOT/name).stat().st_size for name in refs) <= 256*1024**2, 'Total reference bytes≤256MiB')
    for name, pin in refs.items():
        need(re.fullmatch('[a-f0-9]{64}', pin) and sha(ROOT/name) == pin, 'Reference SHA '+name)
    assertions = mapping['e8_evidence']['numeric_assertions']
    need(len(assertions) == 22, '22E8 exact source pointers')
    for row in assertions:
        value = pointer(parse(ROOT/row['source_path']), row['json_pointer'])
        need(type(value) is type(row['value']) and value == row['value'], 'Exact pointer '+row['json_pointer'])
    locations = mapping['e8_evidence']['code_locations']
    need(len(locations) == 11, '11durable source ranges')
    for row in locations:
        lines = read(ROOT/row['source_path']).decode('utf-8').splitlines()
        need(1 <= row['line_start'] <= row['line_end'] <= len(lines), 'Bounded actual code location')
    for folder, (pin, count) in SCIENTIFIC.items():
        directory = ROOT/folder
        need(sha(directory/'manifest.json') == pin, 'Actual scientific manifest pin')
        manifest = parse(directory/'manifest.json')
        need(manifest['status'] == 'completed' and len(manifest['outputs_sha256']) == count, 'Closed scientific scope/count')
        for name, expected in manifest['outputs_sha256'].items():
            need(Path(name).name == name and sha(directory/name) == expected, 'Closed scientific output '+name)
    proof = ROOT/'research_tracking/runs/paper1-concept-local-invariance-20261109-01'
    result = parse(proof/'result.json')
    observed = result['counts']
    need(result['status'] == 'ACCEPTED91_PAPER1_CASES_WITH6_LOCAL_INVARIANCE_FIXTURES'
         and result['returncode'] == 0 and result['timed_out'] is False
         and observed['accepted'] is True and observed['counts'] == dict(tests=91, failures=0, errors=0,
             skipped=0, expected_failures=0, unexpected_successes=0), 'Named fixture suite actually accepted')
    need(len(set(observed['collected_ids'])) == 91
         and observed['collected_ids'] == observed['started_ids'] == observed['completed_ids']
         and len(observed['new_ids']) == 6 and all(name in observed['completed_ids'] for name in observed['new_ids'])
         and result['source_before'] == result['source_after'], '91exact IDs and source equality')
    expected_test = 'test_concept_local_invariance.ConceptLocalInvarianceTests.test_capped_latent_can_change_aggregate_gain_at_same_horizon'
    need(expected_test in observed['new_ids'], 'Cap fixture is named PASS, not only a code literal')
    code = read(proof/'test_concept_local_invariance.py').decode('utf-8').splitlines()
    need('(2., 12.)' in code[117] and 'aggregate_latent_gain' in code[117], 'Exact code assertion at118')
    need(result['static_new_fixture_upper_bounds'] == dict(episode_calls=13, feedback_horizon_sum=464,
         extra_ready_only_controllers=1), 'Static bounds retained without measured-ledger promotion')


def links(raw):
    result = []
    for target in re.findall(r'\]\(([^)]+)\)', raw.decode('utf-8')):
        if target.startswith(('http://', 'https://', '#')):
            continue
        path = physical((TARGET.parent/target).resolve())
        need(path.is_file(), 'Published-position link exists '+target)
        result.append(target)
    need(len(result) == 23, 'Exact23existing links')
    return result


def build(old_md, old_map):
    for path, pin in PINS.items():
        need(sha(path) == pin, 'Frozen candidate/preparation source '+path.name)
    need(digest(old_md) == OLD[TARGET] and digest(old_map) == OLD[TARGET_MAP] and len(old_md) == 35807,
         'Exact before pair/35807bytes')
    candidate = read(CANDIDATE)
    need(candidate[:len(old_md)] == old_md and candidate[len(old_md):] == read(APPEND), 'Whole E1–E7 exact prefix and E8 append')
    need(not any(char in read(APPEND).decode('utf-8') for char in ';:'), 'New prose has no semicolons/colon introductions')
    previous, mapping = json.loads(old_map), parse(SOURCE_MAP)
    need(mapping['draft_sha256'] == digest(candidate) and len(previous['sources_sha256']) == 80,
         'Candidate draft binding and80old sources')
    for name, pin in previous['sources_sha256'].items():
        need(mapping['sources_sha256'].get(name) == pin, 'All80old source entries retained')
    for key, value in previous.items():
        if key == 'sources_sha256' or key in ('status', 'draft_sha256', 'source_count'):
            continue
        if key == 'evidence_mapping':
            need(all(mapping[key].get(k) == v for k,v in value.items()), 'Old E1–E7 evidence mappings unchanged')
        else:
            need(mapping[key] == value, 'Historical source-map field retained '+key)
    validate_sources(mapping)
    checked_links = links(candidate)
    parent = mapping['e8_candidate_parent']
    need(parent['canonical_draft_bytes'] == 35807 and parent['canonical_draft_sha256'] == OLD[TARGET]
         and parent['canonical_sources_sha256'] == OLD[TARGET_MAP], 'Exact candidate lineage')
    published_e8 = deepcopy(mapping['e8_evidence'])
    published_e8['publication_status'] = 'PUBLISHED_CONDITIONAL_SOURCE_PROOF_AND_FIXTURES_NOT_FINAL_RQ'
    source_text = replace_value(read(SOURCE_MAP).decode('utf-8'), 'status', 'PUBLISHED_E8_THESIS_DRAFT_EVIDENCE_BOUND_NOT_FINAL_RQ')
    source_text = replace_value(source_text, 'e8_evidence', published_e8)
    published_map = source_text.encode('utf-8')
    parsed = json.loads(published_map)
    for key, value in mapping.items():
        need(parsed[key] == (published_e8 if key == 'e8_evidence' else
             'PUBLISHED_E8_THESIS_DRAFT_EVIDENCE_BOUND_NOT_FINAL_RQ' if key == 'status' else value), 'Status-only prepared-map derivation')
    pair = {'published.md': candidate, 'published.sources.json': published_map}
    plan = dict(kind='E8_PUBLICATION_PREPARED_NOT_PUBLISHED', helper_sha256=sha(Path(__file__).resolve()),
        canonical_before={p.relative_to(ROOT).as_posix():h for p,h in OLD.items()},
        candidate_pins={p.relative_to(ROOT).as_posix():h for p,h in PINS.items()},
        prepared_sha256={name:digest(raw) for name,raw in pair.items()}, source_references=94,
        E8_numeric_pointers=22, code_locations=11, canonical_relative_links=checked_links,
        prior_markdown_prefix_bytes=35807, prior_source_entries=80,
        scientific_manifests={name:dict(sha256=pin, outputs=count) for name,(pin,count) in SCIENTIFIC.items()},
        source_map_change='Only top-level status and E8 publication_status in prepared copy; frozen candidates unchanged.',
        two_file_atomicity=False, partial_failure_no_auto_rollback_or_retry=True)
    return pair, plan


def journal(event, **details):
    path = OUT/'publication.log'
    raw = (json.dumps(dict(event=event, **details), ensure_ascii=False, allow_nan=False)+'\n').encode('utf-8')
    need(path.stat().st_size+len(raw) <= 65536 if path.exists() else len(raw) <= 65536, 'Publication log≤64KiB')
    with path.open('ab') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def prepare():
    need(not OUT.exists() and not DESTINATION.exists(), 'Exclusive new preparation')
    pair, plan = build(read(TARGET), read(TARGET_MAP))
    OUT.mkdir()
    for path, alias in ((TARGET, 'before.md'), (TARGET_MAP, 'before.sources.json')):
        write(OUT/alias, read(path))
        need(sha(path) == sha(OUT/alias) == OLD[path], 'Before/copy/source-after SHA')
    for alias, value in pair.items():
        write(OUT/alias, value)
    _, checked = build(read(TARGET), read(TARGET_MAP))
    need(checked == plan, 'All publication inputs stable after preparation')
    write(OUT/'plan.json', encoded(plan))
    print(json.dumps(dict(status='PREPARED_NOT_PUBLISHED', plan_sha256=sha(OUT/'plan.json'), prepared_sha256=plan['prepared_sha256'])))


def publish(args):
    pair, plan = build(read(TARGET), read(TARGET_MAP))
    need(args.review_reference and args.expected_plan_sha256 == sha(OUT/'plan.json') and parse(OUT/'plan.json') == plan,
         'ROOT exact-plan review required')
    need(not (OUT/'publication.json').exists() and not (OUT/'failure.json').exists()
         and not (OUT/'publication.log').exists(), 'Single publication, no automatic retry')
    for target, alias in ((TARGET, 'before.md'), (TARGET_MAP, 'before.sources.json')):
        need(sha(OUT/alias) == sha(target) == OLD[target], 'Preserved original pair')
    for alias, value in pair.items():
        need(read(OUT/alias) == value, 'Exact prepared pair')
    done = []
    try:
        journal('PUBLICATION_STARTED', plan_sha256=args.expected_plan_sha256)
        for target, alias in ((TARGET, 'published.md'), (TARGET_MAP, 'published.sources.json')):
            pending = target.with_name(target.name+'.e8-publication01.pending')
            need(not physical(pending).exists(), 'Exclusive pending path')
            write(pending, pair[alias])
            need(sha(pending) == plan['prepared_sha256'][alias], 'Pending bytes before replacement')
        for target, alias in ((TARGET, 'published.md'), (TARGET_MAP, 'published.sources.json')):
            need(sha(target) == OLD[target], 'Concurrent canonical edit rejected')
            os.replace(target.with_name(target.name+'.e8-publication01.pending'), target)
            done.append(target.relative_to(ROOT).as_posix())
            need(read(target) == pair[alias], 'Actual published bytes')
            journal('FILE_REPLACED_AND_VERIFIED', path=done[-1], sha256=sha(target))
        validate_sources(parse(TARGET_MAP))
        links(read(TARGET))
        journal('PAIR_AND_REFERENCES_VERIFIED', sources=94, E8_numeric_pointers=22, prior_prefix_bytes=35807)
        write(OUT/'publication.json', encoded(dict(status='PUBLISHED_E8_PAIR_NOT_FINAL_RQ',
            review_reference=args.review_reference, plan_sha256=args.expected_plan_sha256, replacements=done,
            published_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in (TARGET, TARGET_MAP)},
            source_references=94, E8_numeric_pointers=22, prior_prefix_bytes=35807,
            publication_log_sha256=sha(OUT/'publication.log'), historical_candidates_unchanged=True,
            tests_or_native_or_Git_run_during_publication=False, two_file_atomicity=False)))
    except BaseException as error:
        write(OUT/'failure.json', encoded(dict(status='FAILED_OR_PARTIAL_PUBLICATION_KEEP_ALL', replacements=done,
            error_type=type(error).__name__, error=str(error), originals_preserved=True,
            rollback=False, automatic_retry=False)))
        raise
    print(json.dumps(dict(status='PUBLISHED_E8_PAIR_NOT_FINAL_RQ', publication_sha256=sha(OUT/'publication.json'))))


def archive_inputs(*, archive_in_progress=False):
    need((archive_in_progress or not DESTINATION.exists()) and not (OUT/'failure.json').exists(),
         'New archive requires actual successful publication')
    pair, plan = build(read(OUT/'before.md'), read(OUT/'before.sources.json'))
    need(parse(OUT/'plan.json') == plan, 'Unchanged prepared plan')
    receipt = parse(OUT/'publication.json')
    expected_pair = {TARGET.relative_to(ROOT).as_posix():digest(pair['published.md']),
                     TARGET_MAP.relative_to(ROOT).as_posix():digest(pair['published.sources.json'])}
    need(receipt['status'] == 'PUBLISHED_E8_PAIR_NOT_FINAL_RQ' and receipt['plan_sha256'] == sha(OUT/'plan.json')
         and receipt['published_sha256'] == expected_pair and receipt['replacements'] == list(expected_pair)
         and receipt['publication_log_sha256'] == sha(OUT/'publication.log'), 'Actual publication receipt/log')
    for target, alias in ((TARGET, 'published.md'), (TARGET_MAP, 'published.sources.json')):
        need(read(target) == read(OUT/alias) == pair[alias]
             and not target.with_name(target.name+'.e8-publication01.pending').exists(), 'Actual published pair, no pending')
    copies = {'before.md':OUT/'before.md', 'before.sources.json':OUT/'before.sources.json',
        'published.md':TARGET, 'published.sources.json':TARGET_MAP, 'candidate.md':CANDIDATE,
        'candidate.sources.json':SOURCE_MAP, 'append.md':APPEND, 'source_preparation.json':PREPARATION,
        'plan.json':OUT/'plan.json', 'publication.json':OUT/'publication.json',
        'publication.log':OUT/'publication.log', 'helper.py':Path(__file__).resolve()}
    inventory = {alias:dict(source=path.relative_to(ROOT).as_posix(), sha256=sha(path), bytes=len(read(path)))
                 for alias,path in copies.items()}
    need(len(inventory) == 12 and sum(row['bytes'] for row in inventory.values()) <= 2*1024**2, 'Twelve small copies≤2MiB')
    references = dict(parse(SOURCE_MAP)['sources_sha256'])
    references['src/knowledge_tracing/evidence.py'] = EVIDENCE_WRITER_SHA
    need(all(sha(ROOT/name) == pin for name,pin in references.items()), 'All references before archive')
    outputs = sorted((*copies, *GENERATED))
    need(len(outputs) == 18, '18writing outputs excluding manifest')
    dry = dict(kind='E8_ACTUAL_PUBLICATION_ARCHIVE_DRY', run_id=RUN, copies=inventory, references=references,
        outputs=outputs, output_count_excluding_manifest=18, publication_sha256=sha(OUT/'publication.json'),
        source_references=94, E8_numeric_pointers=22, prior_prefix_bytes=35807, no_analysis_rerun=True)
    return copies, dry


def archive(args):
    copies, dry = archive_inputs()
    dry_path = OUT/'archive_dry.json'
    if args.prepare_archive:
        write(dry_path, encoded(dry))
        print(json.dumps(dict(status='ARCHIVE_DRY_NOT_CLOSED', dry_sha256=sha(dry_path), copies=12, outputs=18)))
        return
    need(args.review_reference and args.expected_archive_dry_sha256 == sha(dry_path) and parse(dry_path) == dry,
         'ROOT exact archive-dry review')
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    sources = list(copies.values())+[ROOT/name for name in dry['references']]+[dry_path]
    note = ('# Nối E8 vào bản thảo RQ1\n\n'
            'Giữ35807byte E1–E7,80sourceentries cũ;94refs/22pointers/23links được kiểm. '
            'Proof concept-local có điều kiện cả hai branch complete và selected-only local updates. '
            'Fixture cap2/12 là tổng latent gain dựng tay, không học sinh thật. '
            'Witness US42domain28 và proof6fixtures/91tests là hai scopes riêng.\n\n'
            'Cặp trước/sau/candidates/plan/publication/log giữ đúng bytes. Pair replacement atomic từng file, '
            'không hứa transaction hai file. Frozen candidates nguyên vẹn; prepared map chỉ đổi publication status. '
            'Reference scientific bundles, không copy lại raw trajectories/data/figures hoặc chạy phân tích.\n')
    with record_evidence_run(ROOT, RUN, metadata=dict(kind='THESIS_RQ1_E8_WRITING_PUBLICATION', source_references=94,
            E8_numeric_pointers=22, prior_prefix_bytes=35807, analysis_rerun=False,
            new_independent_N=0, research_RQ_completion=False), sources=sources, note=note) as out:
        copied = {}
        for alias,path in copies.items():
            row = dry['copies'][alias]
            need(sha(path) == row['sha256'], 'Source before copy')
            write(out/alias, read(path))
            need(sha(path) == sha(out/alias) == row['sha256'], 'Source/copy/source-after SHA')
            copied[alias] = dict(row, copied_sha256=sha(out/alias), source_after_sha256=sha(path))
        write(out/'copy_inventory.json', encoded(dict(before=dry['copies'], after=copied, unchanged=True)))
        write(out/'reference_sources.json', encoded(dry['references']))
        write(out/'reviewed_archive_dry.json', read(dry_path))
        write(out/'closure_review.json', encoded(dict(review_reference=args.review_reference,
            dry_sha256=args.expected_archive_dry_sha256, publication_sha256=dry['publication_sha256'],
            scope='Writing archive only; evidence writer reads Git HEAD, no Git mutation or scientific rerun.')))
        _, after = archive_inputs(archive_in_progress=True)
        need(after == dry and sorted(p.name for p in out.iterdir() if p.name != 'manifest.json') == dry['outputs'],
             'All references/copies stable and exact18outputs')
    verified = verify_evidence_bundle(DESTINATION)
    need(verified['artifacts'] == 18, 'Closed18writing outputs')
    print(json.dumps(dict(verification=verified, manifest_sha256=sha(DESTINATION/'manifest.json'))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--prepare', action='store_true')
    modes.add_argument('--publish', action='store_true')
    modes.add_argument('--prepare-archive', action='store_true')
    modes.add_argument('--close-archive', action='store_true')
    parser.add_argument('--expected-plan-sha256')
    parser.add_argument('--expected-archive-dry-sha256')
    parser.add_argument('--review-reference')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT/'.venv', 'Repository .venv only')
    if args.prepare:
        prepare()
    elif args.publish:
        publish(args)
    else:
        archive(args)


if __name__ == '__main__':
    main()
