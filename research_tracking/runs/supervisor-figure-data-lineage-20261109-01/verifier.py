"""ROOT kiểm lineage/SVG bằng stdlib; không thực thi builder hoặc dựng lại hình."""
import time
PERF, WALL, MONO = time.perf_counter, time.time, time.monotonic
START = PERF(), WALL(), MONO()
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
LINEAGE = PREP / 'FIGURE_DATA_LINEAGE_DRAFT01.json'
LINEAGE_SHA = 'bf2128507f850d6d33177814af148fc63132e6594187c875d99da8f80eb5a775'
FIGURES = ROOT / 'research_tracking/runs/supervisor-figures-20261109-01'
FIGURE_MANIFEST_SHA = '9fff53c809e47f890caf8b2b491c8c37452ee74d6f9d17a04af54dcde6594758'
OUT = PREP / 'figure-data-lineage-verification01'
CAP_SECONDS = 20
TOTAL_READ_BYTES = 20 * 1024**2
MAX_FILE_BYTES = 2 * 1024**2


def need(condition, message):
    if not condition:
        raise ValueError(message)


def elapsed():
    return max(PERF() - START[0], WALL() - START[1], MONO() - START[2])


def check():
    need(elapsed() < CAP_SECONDS, 'same cooperative twenty-second metadata deadline')


def physical(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve() == path, 'physical ROOT path')
    cursor = ROOT
    for part in ('', *path.relative_to(ROOT).parts):
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'no input/output alias')


def source_path(relative):
    need(type(relative) is str and ':' not in relative and '\\' not in relative, 'relative POSIX source path')
    parsed = PurePosixPath(relative)
    need(not parsed.is_absolute() and '..' not in parsed.parts and parsed.as_posix() == relative, 'safe source path')
    path = ROOT / relative
    roots = (ROOT / 'research_tracking/runs', PREP,
             ROOT / 'artifacts/akt/local-tests/development-corpus-20261108-01')
    legacy = ROOT / 'research_tracking/reports/THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.sources.json'
    need(path == legacy or any(path.is_relative_to(root) for root in roots), 'closed metadata-only source population')
    need(path.suffix in ('.json', '.py', '.ipynb', '.html', '.svg'), 'source metadata extension only')
    physical(path)
    return path


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def decode(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('nonfinite JSON constant ' + value)
    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)


def same(left, right):
    return json.dumps(left, sort_keys=True, allow_nan=False, separators=(',', ':')) == json.dumps(
        right, sort_keys=True, allow_nan=False, separators=(',', ':'))


def pointer(value, location):
    need(type(location) is str and (location == '' or location.startswith('/')), 'JSON pointer syntax')
    if location:
        for part in location[1:].split('/'):
            need(not re.search(r'~(?![01])', part), 'JSON pointer escape')
            part = part.replace('~1', '/').replace('~0', '~')
            if type(value) is list:
                need(re.fullmatch('0|[1-9][0-9]*', part) and int(part) < len(value), 'array pointer range')
                value = value[int(part)]
            else:
                need(type(value) is dict and part in value, 'object pointer member')
                value = value[part]
    return value


class Inputs:
    def __init__(self):
        self.raw = {}
        self.json = {}
        self.bytes_read = 0

    def disk(self, path):
        check()
        physical(path)
        need(path.is_file() and path.stat().st_size <= MAX_FILE_BYTES, 'bounded regular source')
        raw = path.read_bytes()
        self.bytes_read += len(raw)
        need(len(raw) == path.stat().st_size and self.bytes_read <= TOTAL_READ_BYTES, 'stable size/total read-byte cap')
        check()
        return raw

    def get(self, path):
        if path not in self.raw:
            self.raw[path] = self.disk(path)
        return self.raw[path]

    def object(self, path):
        if path not in self.json:
            self.json[path] = decode(self.get(path))
        return self.json[path]


def verify(inputs):
    raw = inputs.get(LINEAGE)
    need(digest(raw) == LINEAGE_SHA, 'ROOT-reviewed lineage bytes')
    lineage = decode(raw)
    registry = lineage['source_registry']
    need(lineage['schema_version'] == 1 and len(registry) == 27 and len(lineage['figures']) == 11
         and lineage['scientific_new_N'] == 0, 'reviewed lineage population/scope')
    paths = {}
    manifest_checks = 0
    for name, row in registry.items():
        path = source_path(row['path'])
        need(path not in paths.values(), 'unique registered source paths')
        payload = inputs.get(path)
        need(digest(payload) == row['sha256'] and len(payload) == row['bytes'], 'registered source SHA/size ' + name)
        paths[name] = path
        if 'manifest' in row:
            bound = row['manifest']
            manifest_path = source_path(bound['path'])
            manifest_raw = inputs.get(manifest_path)
            manifest = inputs.object(manifest_path)
            need(digest(manifest_raw) == bound['sha256'] and manifest['status'] == 'completed'
                 and pointer(manifest, bound['json_pointer']) == row['sha256'], 'closed output binding ' + name)
            manifest_checks += 1
    need(paths['figure_manifest'] == FIGURES / 'manifest.json'
         and digest(inputs.get(paths['figure_manifest'])) == FIGURE_MANIFEST_SHA, 'immutable figure bundle identity')
    manifest = inputs.object(paths['figure_manifest'])
    index = inputs.object(paths['figure_index'])
    html = inputs.get(paths['source_html'])
    need(index['source_html_sha256'] == digest(html) and len(index['figures']) == 11
         and manifest['status'] == 'completed' and len(manifest['outputs_sha256']) == 20, 'figure index/HTML/bundle scope')
    notebook = inputs.object(paths['notebook_snapshot'])
    record_ids = {row['id'] for row in inputs.object(paths['notebook_source_map'])['records']}
    ast_cache = {}
    svg_spans = list(re.finditer(rb'<svg\b.*?</svg>', html, re.DOTALL))
    captions = list(re.finditer(rb'<figcaption\b[^>]*>(.*?)</figcaption>', html, re.DOTALL))
    need(len(svg_spans) == len(captions) == 11, 'eleven raw HTML SVG/caption spans')
    seen_files = set()
    figure_checks = []
    point_checks = y_terms = denominator_checks = 0
    referenced_cells = set()
    for ordinal, figure in enumerate(lineage['figures'], 1):
        check()
        original = pointer(index, figure['figure_index_pointer'])
        name = figure['svg_file']
        need(figure['ordinal'] == original['ordinal'] == ordinal
             and name == original['file'] and Path(name).name == name and name.endswith('.svg')
             and name not in seen_files and figure['title'] == original['title']
             and figure['svg_sha256'] == original['svg_sha256'], 'unique ordered figure registry identity')
        seen_files.add(name)
        svg = inputs.get(FIGURES / name)
        start, end = original['source_start_byte'], original['source_end_byte']
        need(type(start) is int and type(end) is int and 0 <= start < end <= len(html)
             and (start, end) == svg_spans[ordinal - 1].span()
             and html[start:end] == svg and len(svg) == original['svg_bytes']
             and digest(svg) == figure['svg_sha256'] == manifest['outputs_sha256'][name], 'SVG/source slice/manifest exact bytes')
        need(original['source_line_1based'] == html[:start].count(b'\n') + 1, 'source line metadata')
        caption = captions[ordinal - 1]
        need(caption.span(1) == (original['figcaption_start_byte'], original['figcaption_end_byte'])
             and digest(caption.group(1)) == original['figcaption_sha256']
             and caption.group(1).decode('utf-8') == original['figcaption_html'], 'caption raw span identity')
        element = ET.fromstring(svg)
        namespace = '{http://www.w3.org/2000/svg}'
        need(element.tag == namespace + 'svg'
             and ''.join(element.find(namespace + 'title').itertext()).strip() == original['title']
             and ''.join(element.find(namespace + 'desc').itertext()).strip() == original['description']
             and [''.join(node.itertext()) for node in element.iter(namespace + 'text')] == original['original_text_labels'],
             'stored SVG title/description/text-label metadata')
        for builder in figure['builder_chain']:
            builder_id = builder['source_id']
            need(builder_id in paths and paths[builder_id].suffix == '.py', 'registered inert builder source')
            if builder_id not in ast_cache:
                ast_cache[builder_id] = ast.parse(inputs.get(paths[builder_id]), filename=str(paths[builder_id]))
            definitions = {node.name: node for node in ast.walk(ast_cache[builder_id]) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
            names = [builder['function']] if 'function' in builder else builder.get('functions', [])
            need(all(name in definitions for name in names), 'named builder function definitions exist')
            if 'function' in builder and 'line' in builder:
                need(definitions[builder['function']].lineno == builder['line'], 'named function source line')
            for record in builder.get('record_ids', [builder['record_id']] if 'record_id' in builder else []):
                need(record in record_ids, 'notebook source-map record ID exists')
            for key in ('cell_0based', 'notebook_cell_0based'):
                if key in builder:
                    cell = builder[key]
                    need(type(cell) is int and 0 <= cell < len(notebook['cells']), 'cached notebook cell range')
                    outputs = notebook['cells'][cell].get('outputs', [])
                    need(sum('image/svg+xml' in output.get('data', {}) for output in outputs) == 1, 'one cached SVG in referenced notebook cell')
                    referenced_cells.add(cell)
        for point in figure['numeric_points']:
            source_id = point['source_id']
            need(source_id in paths and paths[source_id].suffix == '.json', 'registered primary aggregate JSON')
            value = inputs.object(paths[source_id])
            need(same(pointer(value, point['json_pointer']), point['value']), 'exact JSON pointer/value ' + point['json_pointer'])
            point_checks += 1
            if 'denominator_pointer' in point:
                need(same(pointer(value, point['denominator_pointer']), point['denominator']), 'exact denominator pointer/value')
                denominator_checks += 1
            if 'Hpast' in point:
                parent = pointer(value, point['json_pointer'].rsplit('/', 1)[0])
                need(all(same(parent[key], point[key]) for key in
                     ('Hpast', 'available_length', 'nominal_window', 'context', 'same_target_pairs')), 'history alias/target context metadata')
            if 'primary_Y_terms' in point:
                outcomes = inputs.object(paths[figure['primary_Y_source_id']])
                need(len(point['primary_Y_terms']) == 4, 'four paired world endpoint terms')
                cells = set()
                weighted = []
                for term in point['primary_Y_terms']:
                    actual = pointer(outcomes, term['json_pointer'])
                    row = pointer(outcomes, term['json_pointer'].rsplit('/', 1)[0])
                    cell = (term['graph_on'], term['prerequisite_mechanism_on'])
                    need(all(type(flag) is bool for flag in cell) and cell not in cells
                         and type(term['coefficient']) is int and term['coefficient'] == (1 if cell[0] == cell[1] else -1)
                         and row['seed'] == point['seed'] and row['profile'] == point['profile']
                         and row['graph_on'] is cell[0] and row['prerequisite_mechanism_on'] is cell[1]
                         and same(actual, term['value']), 'exact paired Y pointer/value/key/coefficient')
                    cells.add(cell)
                    weighted.append(term['coefficient'] * actual)
                    y_terms += 1
                on = pointer(value, point['source_effect_on_pointer'])
                off = pointer(value, point['source_effect_off_pointer'])
                need(math.isclose(on - off, point['value'], rel_tol=0, abs_tol=1e-12)
                     and math.isclose(math.fsum(weighted), point['value'], rel_tol=0, abs_tol=1e-12), 'cached Psi arithmetic at fixed1e-12; not new simulation')
        need(figure['unknowns'] == ['UNKNOWN_EXACT_END_TO_END_REBUILD_BYTE_PARITY_WITH_EDITORIAL_TRANSFORMATIONS'], 'retain unmeasured rebuild limitation')
        figure_checks.append(dict(ordinal=ordinal, file=name, svg_sha256=digest(svg), exact_html_span=True,
            numeric_point_count=len(figure['numeric_points']), scope='STORED_BYTES_AND_STATIC_LINEAGE_NOT_REBUILD'))
    need(seen_files == {name for name in manifest['outputs_sha256'] if name.endswith('.svg')}
         and point_checks == 54 and y_terms == 36 and denominator_checks == 4, 'complete eleven-figure/pointer population')
    claims = inputs.object(paths['legacy_claim_map'])
    catalog = lineage['legacy_C01_C14_catalog']['claims']
    need(len(catalog) == 14, 'fourteen historical claim references')
    for claim in catalog:
        actual = pointer(claims, claim['claim_json_pointer'])
        need(claim['id'] == actual['id'] and claim['claim_vi'] == actual['claim_vi']
             and claim['evidence_count'] == len(actual['evidence']), 'historical claim catalog metadata only')
    need(lineage['rebuild_readiness']['reexecuted_figures'] is False
         and lineage['rebuild_readiness']['bitwise_rebuild'].startswith('UNKNOWN'), 'no rebuild promotion')
    return dict(registered_sources=27, closed_manifest_bindings=manifest_checks, stored_svgs=11,
        primary_pointer_value_checks=point_checks, denominator_pointer_checks=denominator_checks,
        primary_Y_pointer_checks=y_terms, cached_Psi_arithmetic_checks=9, legacy_claim_metadata_checks=14,
        builder_sources_AST_checked=len(ast_cache), cached_notebook_svg_cells=sorted(referenced_cells), figures=figure_checks,
        proposed_small_archive=dict(run_id='supervisor-figure-data-lineage-20261109-01',
            copies=['lineage draft', 'this verifier', 'actual result/stdout/stderr if ROOT captures them'],
            candidate_basis='Separate static manifest-output SHA search during source review; not recomputed by this verifier',
            builder_source_ids_without_matching_output_SHA_in_reviewed_run_manifests=
                ['html_builder', 'notebook_builder', 'process_builder', 'cross_builder', 'candidate_builder'],
            already_archived_builder=dict(source_id='masking_builder',
                path='research_tracking/runs/supervisor-masking-report-qa-20261109-01/publish_masking_supervisor01.py'),
            scope='Proposal only; no archive generated, no aggregate/HTML/notebook/SVG/runtime duplication'))


def write(path, value):
    physical(path)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lineage-sha256', required=True)
    parser.add_argument('--helper-sha256', required=True)
    parser.add_argument('--review-reference', required=True)
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT / '.venv' and sys.dont_write_bytecode is True, '.venv -B only')
    need(args.lineage_sha256 == LINEAGE_SHA and re.fullmatch('[a-f0-9]{64}', args.helper_sha256)
         and args.review_reference.strip(), 'ROOT explicit source review')
    physical(OUT)
    need(not OUT.exists(), 'exclusive verification attempt')
    OUT.mkdir()
    inputs = Inputs()
    result = {}
    error = None
    before = {}
    after = {}
    try:
        need(digest(inputs.get(Path(__file__).resolve())) == args.helper_sha256, 'actual verifier source SHA')
        need(not any(name.split('.')[0] in ('torch', 'numpy', 'pandas', 'sklearn') for name in sys.modules), 'fresh stdlib-only process')
        result = verify(inputs)
        before = {path.relative_to(ROOT).as_posix(): digest(raw) for path, raw in inputs.raw.items()}
        after = {path.relative_to(ROOT).as_posix(): digest(inputs.disk(path)) for path in inputs.raw}
        need(before == after and not any(name.split('.')[0] in ('torch', 'numpy', 'pandas', 'sklearn') for name in sys.modules), 'source stable and scientific modules absent')
        check()
    except BaseException as exc:
        error = dict(type=type(exc).__name__, message=str(exc))
    accepted = error is None and elapsed() < CAP_SECONDS
    receipt = dict(status='VERIFIED_FIGURE_DATA_LINEAGE_AND_STORED_SVG_BYTES_NOT_REBUILD' if accepted else 'REJECTED_LINEAGE_VERIFICATION_KEEP_OUTPUTS',
        accepted=accepted, error=error, review_reference=args.review_reference,
        lineage_sha256=args.lineage_sha256, helper_sha256=args.helper_sha256, result=result,
        source_before=before, source_after=after, disk_bytes_read=inputs.bytes_read,
        elapsed_seconds=elapsed(), cooperative_cap_seconds=CAP_SECONDS,
        scientific_new_N=0, builder_execution=False, render=False,
        scientific_modules_absent=not any(name.split('.')[0] in ('torch', 'numpy', 'pandas', 'sklearn') for name in sys.modules),
        end_to_end_rebuild='UNKNOWN_NOT_PERFORMED', automatic_retry=False,
        resource_scope='Cooperative elapsed/file-byte caps; no RSS monitor or hard OS quota in this standalone helper')
    write(OUT / 'result.json', receipt)
    if elapsed() >= CAP_SECONDS:
        write(OUT / 'postwrite_rejection.json', dict(status='REJECTED_POSTWRITE_BUDGET', elapsed_seconds=elapsed()))
        accepted = False
    print(json.dumps(dict(status=receipt['status'] if accepted else 'REJECTED_LINEAGE_VERIFICATION_KEEP_OUTPUTS',
          elapsed_seconds=elapsed(), result_sha256=digest((OUT / 'result.json').read_bytes()))))
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__':
    main()
