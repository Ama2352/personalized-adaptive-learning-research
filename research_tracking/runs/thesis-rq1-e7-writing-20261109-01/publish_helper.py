"""Chuẩn bị hoặc publish đúng cặp E7 đã review, không chạy phân tích/model/Git."""
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
CANDIDATE = PREP/'thesis_rq1_e7_candidate01.md'
SOURCE_MAP = PREP/'thesis_rq1_e7_candidate01.sources.json'
TARGET = ROOT/'research_tracking/reports/THESIS_RQ1_MECHANISMS_DRAFT_20261109.md'
TARGET_MAP = TARGET.with_suffix('.sources.json')
BUNDLE = ROOT/'research_tracking/runs/rq1-mastery-ready-masking-20261109-01'
REPORT = ROOT/'research_tracking/reports/rq1_mastery_ready_masking_20261109.md'
OUT = PREP/'thesis-rq1-e7-publication01'
PINS = {
    CANDIDATE: '590227b64bc6f5ff156bd717bafc37beaa90cc29c26fba14b1a7f43c92576d5f',
    SOURCE_MAP: '6da8354dbaeb9248bbb13fbd4c16651a8dacb273b1fcaab88450623541cff100',
    TARGET: '59228c370e519770c74cb442dd7e1833e53df6b490d76b8febc1987221335fa0',
    TARGET_MAP: 'ea446f94ac906fe0674ea133935d6730fc32635fce9463779228d3f0bb0478b3',
}
MANIFEST_SHA = '9cbb7a276b750bf079f544ba69a4d0cf1ea28b89140707957630630a20aa9a4b'
REPORT_SHA = 'ab9ee901c703d9c319d80d97534253219c065d2be62b89f489a7a701d195539d'
PENDING = ('Manifest của bundle masking đang chờ Root đóng và cung cấp, nên bản ứng viên này chưa gán run ID hoặc SHA closure.')
PUBLISHED = ('Bằng chứng E7 đã được đóng trong [bundle masking](../runs/rq1-mastery-ready-masking-20261109-01/README.md). '
    'Có thể đối chiếu [báo cáo chuyên đề](rq1_mastery_ready_masking_20261109.md) và '
    '[bản đếm lại độc lập](../runs/rq1-mastery-ready-masking-20261109-01/masking_independent_native_recount02.json). '
    'Manifest hoàn tất và SHA của các file này được ghi trong source map.')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def physical(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve() == path, 'physical workspace path')
    cursor = ROOT
    for part in path.relative_to(ROOT).parts:
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'no path aliases')
    return path


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    physical(path)
    need(path.is_file() and path.stat().st_size <= 4*1024**2, 'bounded regular evidence file')
    raw = path.read_bytes()
    need(len(raw) == path.stat().st_size, 'stable file bytes')
    return raw


def parse(path):
    return json.loads(read(path))


def write(path, raw):
    physical(path)
    with path.open('xb') as stream:
        need(stream.write(raw) == len(raw), 'complete exclusive write')
        stream.flush()
        os.fsync(stream.fileno())
    need(read(path) == raw, 'write readback exact')


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')


def replace_value(text, key, value):
    """Chỉ đổi field tường minh, giữ nguyên các bytes E4–E6 khác của JSON."""
    matches = list(re.finditer(r'(?m)^  '+re.escape(json.dumps(key))+':', text))
    need(len(matches) == 1, 'unique top-level replacement key '+key)
    start = matches[0].end()
    while text[start].isspace():
        start += 1
    _, end = json.JSONDecoder().raw_decode(text, start)
    return text[:start]+json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+text[end:]


def validate_sources(mapping):
    refs = mapping['sources_sha256']
    need(mapping['source_count'] == len(refs) == 80, 'exact eighty frozen candidate references')
    stale = [name for name, pin in refs.items() if digest(read(ROOT/name)) != pin]
    need(not stale, 'candidate references changed, no automatic rebase '+repr(stale))
    evidence = mapping['e7_evidence']
    need(evidence['raw_input_count'] == len(evidence['raw_input_sha256']) == 40, 'forty raw proof inputs')
    assertions = evidence['numeric_assertions']
    need(len(assertions) == 18, 'eighteen exact numeric pointers')
    for row in assertions:
        value = parse(ROOT/row['source_path'])
        for part in row['json_pointer'].lstrip('/').split('/'):
            key = part.replace('~1', '/').replace('~0', '~')
            value = value[int(key)] if isinstance(value, list) else value[key]
        need(type(value) is type(row['value']) and value == row['value'], 'numeric source pointer '+row['json_pointer'])


def build(expected_manifest_sha):
    need(expected_manifest_sha == MANIFEST_SHA and digest(read(BUNDLE/'manifest.json')) == MANIFEST_SHA,
         'external ROOT pin of actual completed masking manifest')
    for path, pin in PINS.items():
        need(digest(read(path)) == pin, 'frozen candidate/canonical drift '+path.name)
    mapping = parse(SOURCE_MAP)
    validate_sources(mapping)
    old = read(TARGET)
    candidate = read(CANDIDATE)
    need(len(old) == 28517 and candidate[:len(old)] == old, 'entire canonical prefix, including E4–E6, unchanged')
    manifest = parse(BUNDLE/'manifest.json')
    outputs = manifest['outputs_sha256']
    need(manifest['status'] == 'completed' and manifest['kind'] == 'RQ1_CACHED_MASTERY_READY_PREDICATE_MASKING'
         and len(outputs) == 44 and manifest['new_independent_N'] == manifest['native_model_calls'] == 0,
         'actual forty-four-output completed scientific bundle')
    for name, pin in outputs.items():
        need(Path(name).name == name and digest(read(BUNDLE/name)) == pin, 'actual immutable bundle output '+name)
    need(digest(read(REPORT)) == REPORT_SHA == outputs['report_snapshot.md'], 'canonical technical report exact closed snapshot')
    for name, pin in mapping['e7_evidence']['raw_input_sha256'].items():
        need(manifest['sources_sha256'].get(name) == pin, 'bundle binds every original raw input '+name)
    aliases = {}
    for row in parse(BUNDLE/'copy_inventory.json'):
        need(row['sha256'] == row['source_sha256_after_copy'] == row['copied_sha256'] == outputs[row['copy']],
             'closed copy inventory identity')
        if mapping['sources_sha256'].get(row['source']) == row['sha256']:
            aliases[row['source']] = (BUNDLE/row['copy']).relative_to(ROOT).as_posix()
    durable_assertions = []
    for row in mapping['e7_evidence']['numeric_assertions']:
        need(row['source_path'] in aliases, 'primary E7 numbers require a durable copied source')
        durable_assertions.append(dict(row, source_path=aliases[row['source_path']]))
    text = candidate.decode('utf-8')
    need(text.count(PENDING) == 1, 'one explicit pending-closure sentence')
    published = text.replace(PENDING, PUBLISHED).encode('utf-8')
    need(published[:len(old)] == old, 'publication cannot rewrite the existing thesis sections')
    evidence = deepcopy(mapping['e7_evidence'])
    evidence.update(publication_status='CLOSED_RAW_E7_EVIDENCE_BOUND', manifest_path=(BUNDLE/'manifest.json').relative_to(ROOT).as_posix(),
        manifest_sha256=MANIFEST_SHA, manifest_pending_root=False, report_path=REPORT.relative_to(ROOT).as_posix(),
        report_sha256=REPORT_SHA, durable_source_aliases=aliases, durable_numeric_assertions=durable_assertions)
    unarchived = [name for name in mapping['sources_sha256'] if name.startswith(PREP.relative_to(ROOT).as_posix()+'/') and name not in aliases]
    evidence['unarchived_preparation_references'] = unarchived
    source_text = read(SOURCE_MAP).decode('utf-8')
    source_text = replace_value(source_text, 'status', 'PUBLISHED_E7_THESIS_DRAFT_EVIDENCE_BOUND_NOT_FINAL_RQ')
    source_text = replace_value(source_text, 'draft_sha256', digest(published))
    source_text = replace_value(source_text, 'e7_evidence', evidence)
    final_map = source_text.encode('utf-8')
    parsed = json.loads(final_map)
    need(parsed['sources_sha256'] == mapping['sources_sha256'], 'retain all eighty original source references')
    for key in ('e4_numeric_assertions', 'e4_report_provenance', 'reference_mixture_rows',
                'reference_mixture_unique_query_responses', 'reentry_mechanism_fixtures'):
        need(parsed[key] == mapping[key], 'prior E4–E6 metadata remains unchanged')
    return published, final_map, aliases, unarchived


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--publish', action='store_true')
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--expected-plan-sha256')
    parser.add_argument('--review-reference')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT/'.venv', 'repository .venv only')
    published, published_map, aliases, unarchived = build(args.manifest_sha256)
    physical(OUT)
    prepared = {'published.md': published, 'published.sources.json': published_map}
    plan = dict(kind='EXACT_E7_PUBLICATION_PLAN_NOT_PUBLICATION_PROOF', manifest_sha256=MANIFEST_SHA,
        canonical_before={path.relative_to(ROOT).as_posix(): pin for path, pin in PINS.items() if path in (TARGET, TARGET_MAP)},
        candidates={path.relative_to(ROOT).as_posix(): pin for path, pin in PINS.items() if path in (CANDIDATE, SOURCE_MAP)},
        prepared_sha256={name: digest(raw) for name, raw in prepared.items()}, source_references=80, numeric_pointers=18,
        prior_markdown_prefix_bytes=28517, helper_sha256=digest(read(Path(__file__))),
        durable_source_aliases=aliases, unarchived_preparation_references=unarchived,
        two_file_atomicity=False, partial_failure_no_rollback_or_automatic_retry=True)
    if args.prepare:
        need(not OUT.exists(), 'exclusive metadata preparation, no retry')
        OUT.mkdir()
        snapshots = ((TARGET, 'before.md'), (TARGET_MAP, 'before.sources.json'))
        for path, alias in snapshots:
            raw = read(path)
            need(digest(raw) == PINS[path], 'source before snapshot')
            write(OUT/alias, raw)
            need(digest(read(path)) == digest(read(OUT/alias)) == PINS[path], 'snapshot/source post-SHA')
        for name, raw in prepared.items():
            write(OUT/name, raw)
        build(args.manifest_sha256)  # All references and closure remain unchanged after copying.
        write(OUT/'plan.json', json_bytes(plan))
        print(json.dumps(dict(status='PREPARED_NOT_PUBLISHED', plan_sha256=digest(read(OUT/'plan.json')),
            prepared_sha256=plan['prepared_sha256'], unarchived_preparation_references=unarchived)))
        return
    need(args.review_reference and args.expected_plan_sha256 == digest(read(OUT/'plan.json'))
         and parse(OUT/'plan.json') == plan, 'ROOT exact prepared-plan review required')
    for path, alias in ((TARGET, 'before.md'), (TARGET_MAP, 'before.sources.json')):
        need(digest(read(path)) == digest(read(OUT/alias)) == PINS[path], 'canonical/snapshot still frozen')
    for name, raw in prepared.items():
        need(read(OUT/name) == raw, 'prepared bytes remain derived from the frozen candidate')
    need(not (OUT/'publication.json').exists() and not (OUT/'failure.json').exists(), 'one publication only')
    replacements = []
    try:
        for target, name in ((TARGET, 'published.md'), (TARGET_MAP, 'published.sources.json')):
            pending = target.with_name(target.name+'.e7-publication01.pending')
            need(not physical(pending).exists(), 'fresh exact pending path')
            write(pending, prepared[name])
        # The original pair is already durable in OUT. Pair replacement is sequential.
        for target, name in ((TARGET, 'published.md'), (TARGET_MAP, 'published.sources.json')):
            need(digest(read(target)) == PINS[target], 'concurrent canonical modification')
            os.replace(target.with_name(target.name+'.e7-publication01.pending'), target)
            replacements.append(target.relative_to(ROOT).as_posix())
            need(read(target) == prepared[name], 'published bytes after replacement')
        validate_sources(parse(SOURCE_MAP))
        need(digest(read(BUNDLE/'manifest.json')) == MANIFEST_SHA, 'bundle manifest after publication')
        write(OUT/'publication.json', json_bytes(dict(status='PUBLISHED_E7_PAIR', review_reference=args.review_reference,
            plan_sha256=args.expected_plan_sha256, manifest_sha256=MANIFEST_SHA, replacements=replacements,
            published_sha256={path.relative_to(ROOT).as_posix(): digest(read(path)) for path in (TARGET, TARGET_MAP)},
            tests_or_model_or_git_run=False, historical_candidates_unchanged=True)))
    except BaseException as error:
        write(OUT/'failure.json', json_bytes(dict(status='PARTIAL_OR_FAILED_PUBLICATION_KEEP_ALL',
            replacements=replacements, error_type=type(error).__name__, error=str(error),
            rollback=False, automatic_retry=False, snapshots_preserved=True)))
        raise
    print(json.dumps(dict(status='PUBLISHED_E7_PAIR', receipt_sha256=digest(read(OUT/'publication.json')))))


if __name__ == '__main__':
    main()
