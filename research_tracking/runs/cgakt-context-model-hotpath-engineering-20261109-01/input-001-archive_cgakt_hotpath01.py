"""ROOT dry/close hotpath160cases theo hai scope; không rerun test/model."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN_ID = 'cgakt-context-model-hotpath-engineering-20261109-01'
CANDIDATE = PREP/'cgakt_hotpath_integrity_20261109.candidate.md'
CANONICAL = ROOT/'research_tracking/reports/cgakt_hotpath_integrity_20261109.md'
CANDIDATE_SHA = 'd29fa49a55009393758550338a8a3c18a2189dc71a4e2ea415b09b04c0f2ae0a'
PINS = {
    'run_graph_context_hotpath_pure04.py': 'b814fcdc5cc38b8beba2fd107ae9f39fe0e474dc2385e05c6c0833a683f22cd0',
    'check_cgakt_research_hotpath04.py': '34b68e699b654dff05f1b8152deb5058753b01f0f712505f2ef289f1e02706aa',
    'run_cgakt_research_hotpath04.py': '9d5a1de7b167fe042421047e92ae8c3867fff4dc228ccdf057ef43323a013675',
    'cgakt_research_hotpath04_allocation.json': '2ac8712184fdf2f1c2e233db8a8559983a80eb712bd76c1760abb12656874401',
}
NEW_SOURCES = {
    'src/knowledge_tracing/akt/research_graph_context.py': '8bfe0dca095d1de6c898fd849be6c5d1ee7033dffc13c20b24c7857de92bb029',
    'tests/akt/test_research_graph_context.py': 'd54b188ce56fa913551ce54c33209151a1b9456fac0031c541930370471299a8',
    'src/knowledge_tracing/akt/research_graph_model.py': '77e365e4ffc6861f34a9ae05cbca947f057be967389f74f75bf5caacc7ee2397',
    'tests/akt/test_research_graph_model.py': '579359ff7b8ac64a75f9a343200724091d0d5b78af9a87e3d33ad023f1742ffc',
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')


def safe(path, *, existing=True):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts and path.is_relative_to(ROOT), 'fixed project path required')
    cursor = ROOT
    for part in (None, *path.relative_to(ROOT).parts):
        if part is not None:
            cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'path alias rejected')
    need(path.resolve().is_relative_to(ROOT.resolve()), 'physical project path required')
    if existing:
        need(path.is_file(), 'regular input required')
    return path


def xml_counts(raw):
    tree = ET.fromstring(raw)
    counts = {k: sum(int(s.get(k, '0')) for s in tree.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
    cases = list(tree.iter('testcase'))
    need(len(cases) == counts['tests'], 'JUnit testcase count')
    return counts, cases


def gather(report):
    payloads = {}
    def read(path):
        path = safe(path)
        if path not in payloads:
            need(path.stat().st_size <= 2*1024**2, 'input2MiB cap')
            raw = path.read_bytes(); need(len(raw) <= 2*1024**2, 'readback2MiB cap')
            payloads[path] = raw
            need(sum(map(len, payloads.values())) <= 5*1024**2, 'total5MiB cap')
        return payloads[path]
    load = lambda path: json.loads(read(path))
    for name, digest in PINS.items():
        need(sha(read(PREP/name)) == digest, 'frozen controller changed:'+name)
    need(report in (CANDIDATE, CANONICAL) and sha(read(report)) == CANDIDATE_SHA, 'reviewed report bytes/path')
    pure_path = PREP/'graph-context-hotpath-pure04'
    pure = load(pure_path/'result.json')
    pure_counts, pure_cases = xml_counts(read(pure_path/'junit.xml'))
    need(pure['status'] == 'ACCEPTED_135_CONDITION_CONTEXT_HOTPATH_CASES_NOT_MODEL' and pure['returncode'] == 0
         and pure['error'] is None and pure_counts == pure['counts'] == dict(tests=135, failures=0, errors=0, skipped=0), 'actual pure135')
    groups = {name: sum(case.get('classname', '').endswith('test_research_graph_'+name) for case in pure_cases)
              for name in ('condition','context')}
    need(groups == pure['expected_case_groups'] == dict(condition=66, context=69), 'separate actual case classes')
    need(pure['seconds'] < pure['cap_seconds'] == 90 and pure['source_before'] == pure['source_after'], 'pure source/time bound')
    need(pure['actual_neural_model_calls'] == pure['actual_optimizer_calls'] == pure['actual_teacher_calls'] == 0
         and pure['actual_artifact_or_corpus_parsed'] is False, 'declared pure workload scope')
    need(pure['cold_import_canaries'] == [
        dict(module='knowledge_tracing.akt.research_graph_condition', numpy_loaded=False, torch_loaded=False, accepted=True),
        dict(module='knowledge_tracing.akt.research_graph_context', numpy_loaded=True, torch_loaded=False, accepted=True)], 'actual cold import records')
    for name in ('result.json','junit.xml','pytest.log','research_graph_condition-cold.stdout.log',
                 'research_graph_condition-cold.stderr.log','research_graph_context-cold.stdout.log','research_graph_context-cold.stderr.log'):
        read(pure_path/name)
    for module, canary in zip(('research_graph_condition','research_graph_context'), pure['cold_import_canaries']):
        need(json.loads(read(pure_path/(module+'-cold.stdout.log'))) == canary
             and read(pure_path/(module+'-cold.stderr.log')) == b'', 'raw cold canaries')

    label = 'cgakt-research-hotpath04'
    child = load(PREP/label/'result.json'); final = load(PREP/(label+'-owned')/'final.json')
    owned = load(PREP/(label+'-owned')/'receipt.json'); packet = load(PREP/'cgakt_research_hotpath04_allocation.json')
    counts, cases = xml_counts(read(PREP/label/'junit.xml'))
    need(counts == child['counts'] == final['counts'] == dict(tests=25, failures=0, errors=0, skipped=0), 'actual native25')
    names = [c.get('name') for c in cases]
    need(len(set(names)) == 25 and set(names) == set(packet['expected_test_names']), 'actual25case identities')
    need(final['status'] == 'ACCEPTED_CGAKT_RESEARCH_HOTPATH_ENGINEERING_ONLY' and child['pytest_exit_code'] == 0
         and owned['accepted'] is True and owned['returncode'] == 0 and owned['cleanup_accepted'] is True
         and owned['job_active_after_cleanup'] == 0 and owned['popen_handle_closed'] is True
         and owned['actual_worker_in_job_before_GO'] is True, 'actual native verdict/owned cleanup')
    need(child['native_started'] == child['native_body_returned'] == packet['expected_native_counts'], 'native8/5/0 exact')
    need(child['source_before'] == child['source_after'] == final['source_after'] == packet['source_pins']
         and child['methods_restored'] and child['runtime_restored'] and child['environment_restored']
         and child['monitor_stopped'] and child['monitor_errors'] == [] and child['forbidden_attempts'] == [], 'source/restoration guards')
    observer = child['full_cache_observation']; boundary = child['whole_inference_boundary']
    need(observer['full_payload_started'] == observer['full_payload_returned'] == 61 and observer['hotpath_attempts'] == []
         and observer['region_calls'] == dict(collate=20, step=11, native=10, inference=7)
         and child['remaining_hot_regions'] == [], 'actual cache observer distinct from Architecture8')
    need(all(boundary[k] == 1 for k in ('before_started','before_returned','after_started','after_returned'))
         and boundary['before_identity'] == boundary['after_identity'] and boundary['errors'] == [], 'whole inference full audits')
    need(child['resources']['observed_peak_rss_bytes'] == 278994944
         and child['resources']['observed_minimum_available_ram_bytes'] == 4623921152
         and child['elapsed_seconds'] < 80 and final['elapsed_seconds'] < 90, 'actual resource scope')
    need(child['upstream_cuda_availability'] == [dict(phase='local_git_provenance', result=False)]
         and child['torch_profile']['cuda_initialized_after'] is False, 'actual CPU availability/init')
    git = child['local_git_provenance']
    need(len(git['commands']) == 10 and git['original_loader_used'] and git['cached_module_used'] is False
         and git['process_environment_actual'] == packet['local_git_provenance']['process_config'], 'normal source provenance')
    for name, row in final['output_inventory'].items():
        need(name in ('case_events.jsonl','junit.xml','pytest.log','reservation.json','result.json')
             and sha(read(PREP/label/name)) == row['sha256'] and len(read(PREP/label/name)) == row['bytes'], 'child exact byte binding')
    need(sha(read(PREP/(label+'-owned')/'receipt.json')) == final['owned_receipt_sha256'], 'outer-owned receipt binding')
    for name, digest in owned['output_sha256'].items():
        need(name in ('stdout.log','stderr.log') and sha(read(PREP/(label+'-owned')/name)) == digest, 'owned raw logs')
    for name in ('result.json','reservation.json','junit.xml','pytest.log','case_events.jsonl'):
        read(PREP/label/name)
    for name in ('final.json','receipt.json','ready.json','GO.json','launch.json','stdout.log','stderr.log'):
        read(PREP/(label+'-owned')/name)

    checked = dict(pure['source_before'])
    for name, digest in packet['source_pins'].items():
        need(name not in checked or checked[name] == digest, 'cross-scope source binding')
        checked[name] = digest
    for name, digest in checked.items():
        path = safe(ROOT/name)
        need(path.stat().st_size <= 262144 and sha(path.read_bytes()) == digest, 'current frozen source drift:'+name)
    for name, digest in NEW_SOURCES.items():
        need(checked[name] == digest and sha(read(ROOT/name)) == digest, 'four new sources')
    before = PREP/'graph-context-hotpath-before01'
    rows = load(before/'inventory-before.json'); verify = load(before/'copy-verification.json')
    need(len(rows) == len(verify) == 2, 'context before2source inventory')
    for row, after in zip(rows, verify):
        need(row['source'] == after['source'] and row['copy'] == after['copy']
             and row['before'] == after['copy_sha256'] == after['after'] and after['equal'] is True
             and sha(read(ROOT/row['copy'])) == row['before'], 'context pre/post copy bytes')
    before = PREP/'pre-cgakt-model-hotpath01'
    rows = load(before/'inventory.json')['copies']
    need(len(rows) == 2, 'model before2source inventory')
    for row in rows:
        need(sha(read(before/row['snapshot'])) == row['sha256_before_copy'] == row['sha256_after_copy']
             == row['source_sha256_after_copy'], 'model pre/post copy bytes')
    erratum = load(PREP/'cgakt_hotpath04_basetemp_handoff_erratum.json')
    need(erratum['kind'] == 'PROSE_HANDOFF_CORRECTION_NOT_EXECUTION_FAILURE'
         and erratum['actual_frozen_worker_value'] == 'artifacts/akt/local-tests/cgm01'
         and "base_temp = R/'artifacts/akt/local-tests/cgm01'" in read(PREP/'check_cgakt_research_hotpath04.py').decode('utf-8'), 'literal actual basetemp/prose correction')
    references = []
    for old, count in (('cgakt-research-context-engineering-20261109-01',52), ('cgakt-research-core-engineering-20261109-01',74)):
        path = ROOT/'research_tracking/runs'/old/'manifest.json'; manifest = load(path)
        need(manifest['status'] == 'completed' and len(manifest['outputs_sha256']) == count, 'immutable old bundle reference')
        references.append(dict(run_id=old, manifest_sha256=sha(read(path)), outputs=count, copied_whole_bundle=False))
    read(Path(__file__))
    aliases, by_sha = [], {}
    for path, raw in sorted(payloads.items()):
        digest = sha(raw)
        if digest not in by_sha:
            by_sha[digest] = f'input-{len(by_sha)+1:03d}-'+path.name
        aliases.append(dict(source=path.relative_to(ROOT).as_posix(), bytes=len(raw), sha256_before_copy=digest,
                            archived_as=by_sha[digest]))
    summary = dict(pure=dict(counts=pure_counts, case_groups=groups, stored_seconds=pure['seconds'], model_calls=0),
        native=dict(counts=counts, counters=child['native_body_returned'], stored_child_seconds=child['elapsed_seconds'],
            stored_outer_seconds=final['elapsed_seconds'], resources=child['resources'], cache_observer=observer,
            whole_inference_boundary=boundary, owned_cleanup=True), total_software_cases=160,
        scope_vi='135data+25nativecases distinct; Architecture8 != native-region10; nobenchmark/maintraining/fit.')
    return dict(schema_version=1, run_id=RUN_ID, report_source=report.relative_to(ROOT).as_posix(),
        input_aliases=aliases, unique_input_copies=len(by_sha), checked_source_bindings=checked,
        outcomes=summary, old_bundle_references=references), payloads


def recheck(inventory):
    for row in inventory['input_aliases']:
        need(sha(safe(ROOT/row['source']).read_bytes()) == row['sha256_before_copy'], 'evidence input changed')
    for name, digest in inventory['checked_source_bindings'].items():
        need(sha(safe(ROOT/name).read_bytes()) == digest, 'frozen dependency changed')


def main():
    need(os.path.normcase(os.path.abspath(sys.executable)) == os.path.normcase(str(ROOT/'.venv/Scripts/python.exe'))
         and Path(sys.prefix).resolve() == ROOT/'.venv', 'repository .venv only')
    parser = argparse.ArgumentParser(description='ROOT metadata-only dry/close, không chạy test/model')
    parser.add_argument('--report', type=Path, default=CANDIDATE)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--close', action='store_true')
    parser.add_argument('--expected-inventory-sha256')
    args = parser.parse_args(); report = safe(args.report.absolute())
    inventory_path = safe(args.inventory.absolute(), existing=args.close)
    need(inventory_path.parent == PREP and inventory_path.suffix == '.json', 'exclusive prep inventory only')
    need(not (ROOT/'research_tracking/runs'/RUN_ID).exists(), 'immutable run exists')
    inventory, payloads = gather(report); raw_inventory = canonical(inventory); recheck(inventory)
    if not args.close:
        need(not inventory_path.exists() and args.expected_inventory_sha256 is None, 'exclusive dry inventory')
        with inventory_path.open('xb') as handle:
            handle.write(raw_inventory); handle.flush(); os.fsync(handle.fileno())
        print(json.dumps(dict(status='DRY_ONLY_NOT_CLOSED', inventory_sha256=sha(raw_inventory),
            aliases=len(inventory['input_aliases']), unique_copies=inventory['unique_input_copies'], outcomes=inventory['outcomes'])))
        return
    need(args.expected_inventory_sha256 == sha(inventory_path.read_bytes()) == sha(raw_inventory), 'external reviewed same dry inventory required')
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    note = '''# CG-AKT hotpath integrity — engineering09/11/2026

Hai scope:135data/condition/context cases và25native model cases, đều0FES.
Actualnative1backbone/1wrapper/1gate,8Architecture.forward/5logicalbackward/0Adam.
Regioncalls native10 gồm negativeprehooks; không đồng nhất với8Architecture.
61fullpayloadcalls ngoài hotregions;0hotattempts; fullbefore/afterwholeinference1each.
Four before/after sources+rawlogs/canaries/receipts giữbytes vàSHA. Old52/74 chỉ
tham chiếu manifest, không copy toàn bundle. cgm01 là basetemp actual, cgh04 là
message typo đã đính chính, không executionfailure/acceptancerepair.
Không rerun/test/model khi archive. Không actualcorpus/fitted/maintraining/CUDA/
costbenchmark; O(W)lookup giữ nguyên, representative benchmark phải có receipt riêng.
Pureordinarysubprocess scope khácnativeownedJob/observedRSS; không gộp claims.
'''
    git_before = {k:v for k,v in os.environ.items() if k.startswith('GIT_')}
    try:
        for key in list(git_before): os.environ.pop(key, None)
        os.environ.update(GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='safe.directory', GIT_CONFIG_VALUE_0=ROOT.as_posix())
        sources = sorted(set(payloads) | {ROOT/name for name in inventory['checked_source_bindings']} | {inventory_path})
        with record_evidence_run(ROOT, RUN_ID, metadata=dict(kind='CGAKT_HOTPATH_160_SOFTWARE_CASES_NOT_MAIN_TRAINING',
                outcomes=inventory['outcomes'], source_bindings=inventory['checked_source_bindings'],
                old_bundle_references=inventory['old_bundle_references']), sources=sources, note=note) as directory:
            with (directory/'inventory-before.json').open('xb') as handle: handle.write(raw_inventory)
            copied = {}
            for row in inventory['input_aliases']:
                if row['archived_as'] not in copied:
                    target = directory/row['archived_as']
                    with target.open('xb') as handle:
                        handle.write(payloads[ROOT/row['source']]); handle.flush(); os.fsync(handle.fileno())
                    copied[row['archived_as']] = sha(target.read_bytes())
                    need(copied[row['archived_as']] == row['sha256_before_copy'], 'archive copy SHA mismatch')
            recheck(inventory)
            verification = dict(status='VERIFIED_BYTE_COPIES_NOT_TEST_RERUN', inventory_sha256=sha(raw_inventory),
                copied_sha256=copied, sources_after={r['source']: sha(safe(ROOT/r['source']).read_bytes()) for r in inventory['input_aliases']})
            with (directory/'copy-verification.json').open('xb') as handle: handle.write(canonical(verification))
            names = [*copied, 'README.md','execution.log','inventory-before.json','copy-verification.json','force-add-files.txt','manifest.json']
            force = [(directory/name).relative_to(ROOT).as_posix() for name in names] + list(NEW_SOURCES)
            if report == CANONICAL: force.append(report.relative_to(ROOT).as_posix())
            with (directory/'force-add-files.txt').open('x', encoding='utf-8', newline='\n') as handle: handle.write('\n'.join(force)+'\n')
    finally:
        for key in list(os.environ):
            if key.startswith('GIT_'): os.environ.pop(key, None)
        os.environ.update(git_before)
    verified = verify_evidence_bundle(directory); recheck(inventory)
    print(json.dumps(dict(verified=verified, manifest_sha256=sha((directory/'manifest.json').read_bytes()),
        force_add_list=(directory/'force-add-files.txt').relative_to(ROOT).as_posix())))


if __name__ == '__main__':
    main()
