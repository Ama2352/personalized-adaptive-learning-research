"""Inventory/closure riêng cho Gate05 accepted; không chạy test/model/Gate/Git."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
RUN = 'akt-windows-gate-accepted177-20261109-01'
REPORT = ROOT/'research_tracking/reports/akt_windows_gate_accepted_20261109.md'
DRY = P/'accepted_windows_gate05_dry01.json'
FINAL_SHA = '9e61948b93e5f52de248cf076cd6225dc5253f48db949dd40c2a706f4e23d69e'
COLLECT_SHA = 'e341841155d426fc404d5d6fe88584dc3a4de8372c865531be35d1c747d6c914'
RECONCILE_SHA = 'ad956d7f9d205ac243f84a39efffa4d74f67e0b13010f4ffa42a015d4df7a61a'
GENERATED = ('README.md','execution.log','copy_inventory.json','reference_inputs.json',
             'source_binding.json','scope.json','closure_review.json','reviewed_dry.json')


def need(ok, why):
    if not ok:
        raise ValueError(why)


def safe(path):
    need(path.is_absolute() and path.is_relative_to(ROOT), 'repository path')
    cursor = ROOT
    for part in path.relative_to(ROOT).parts:
        cursor /= part
        need(not cursor.is_symlink() and not cursor.is_junction(), 'physical path')
    need(path.resolve() == path and path.is_file(), 'regular selected file')
    return path


def sha(path):
    safe(path)
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):
    safe(path)
    need(path.stat().st_size <= 2*1024**2, 'bounded JSON')
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n')


def ref(path):
    return dict(sha256=sha(path),bytes=path.stat().st_size)


def gather(report_sha):
    need(sha(REPORT) == report_sha, 'reviewed report bytes')
    final_path = P/'win-current-gate-20261109-05-outer/result.json'
    final = read(final_path)
    need(sha(final_path) == FINAL_SHA and final['status'] == 'ACCEPTED_WINDOWS_CPU_SOFTWARE_GATE_ONLY'
         and final['run_accepted'] is True and final['errors'] == []
         and 0 <= final['elapsed_seconds'] <= 630 and final['publication_requested'] is False
         and final['pointer_changed'] is False, 'actual accepted Gate05, no publication')
    owner = final['owned_receipt']
    need(owner['accepted'] is True and owner['cleanup_accepted'] is True
         and owner['job_active_after_cleanup'] == 0 and owner['returncode'] == 0,
         'actual owned cleanup')
    collection_path = P/'gate-collection11-outer/final.json'
    collection = read(collection_path)
    need(sha(collection_path) == COLLECT_SHA
         and collection['status'] == 'ACCEPTED_COLLECTION_ONLY_NOT_GATE_PASS'
         and collection['collected_count'] == 1748 and collection['errors'] == []
         and collection['environment_restored'] is True
         and collection['source_before'] == collection['source_after']
         and collection['elapsed_seconds'] <= 60, 'actual collection11 exact population')
    packet_path = P/'windows_current_gate_packet05.ROOT.json'
    packet = read(packet_path)
    need(sha(packet_path) == final['external_collection_packet_sha256']
         and packet['collection_result']['sha256'] == COLLECT_SHA,
         'external collection packet exact bytes')
    inputs_path = ROOT/packet['collection_input']['path']
    inputs = read(inputs_path)
    need(sha(inputs_path) == packet['collection_input']['sha256'] == collection['packet_sha256']
         and inputs['gate_build_hashes'] == collection['source_before']['gate_build_hashes']
         and len(inputs['gate_build_hashes']) == 177 and len(inputs['test_module_sha256']) == 81,
         '177/81 source identity')
    expected = dict(stdlib=19, **{'no-torch':271}, remaining=1458, merged=1748)
    need(packet['expected_native_counts'] == expected, 'actual collected counts')
    native_path = ROOT/'artifacts/akt/preflight/gate2-evidence-win-current-gate-20261109-05.json'
    native = read(native_path)
    need(native['status'] == 'PASS' and native['test_result'] == dict(passed=1748,failed=0,errors=0,skipped=0)
         and native['build_hashes'] == inputs['gate_build_hashes']
         and native['test_module_sha256'] == inputs['test_module_sha256']
         and 0 <= native['elapsed_seconds'] <= native['timeout_seconds'] == 580
         and final['readiness']['runtime_report_sha256'] == packet['runtime_report']['sha256']
         == '259c171fe63e39a14d9bdf42793bd854a5be73ded19a7a800a2e8a982906f1b4',
         'native full Gate and historical runtime identity')
    for name,count in expected.items():
        verified = final['verified_JUnit'][name]
        need(verified['counts'] == dict(tests=count,failures=0,errors=0,skipped=0)
             and len(verified['identities']) == count, 'outer physical item accounting')
    paths = {}
    references = {}

    def add(alias,path):
        safe(path)
        need(alias not in paths and Path(alias).name == alias and path.stat().st_size <= 2*1024**2,
             'bounded unique flat copy')
        paths[alias] = path

    def reference(path):
        references[path.relative_to(ROOT).as_posix()] = ref(path)

    for name in ('gate_source_snapshot06.json','prepare_current_freeze06.py','gate_collection_worker11.py',
                 'run_gate_collection11.py','gate05_collection11_source_preparation01.json',
                 'windows_current_gate_outer03.py','windows_current_gate_worker02.py',
                 'prepare_windows_current_gate_packet04.py','windows_current_gate_packet05.ROOT.json',
                 'test_current_gate_outer03_junit.py','run_current_gate_outer03_canary01.py',
                 'current_gate_outer03_canary01_reconciliation.json','ROOT_CURRENT_COLLECTION_REVIEW06.md',
                 'ROOT_CURRENT_FULL_GATE_REVIEW05.md','CURRENT_GATE_DERIVATIVE05.md'):
        add(name,P/name)
    add('collection_input.json',inputs_path)
    add('report.md',REPORT)
    add(Path(__file__).name,Path(__file__).resolve())
    for label,directory in (('canary','current-gate-outer03-canary01'),
                            ('collection_outer','gate-collection11-outer'),
                            ('native_child','win-current-gate-20261109-05-child'),
                            ('native_outer','win-current-gate-20261109-05-outer')):
        for path in sorted((P/directory).iterdir()):
            if path.is_file():
                need(path.suffix in ('.json','.log','.bytes'), 'selected raw text only')
                add(label+'__'+path.name,path)
    for stage in collection['stages']:
        name = stage['group']
        child_path = ROOT/stage['child_result_relative']
        child = read(child_path)
        need(sha(child_path) == stage['child_result_sha256']
             and child['source_before'] == child['source_after'] == inputs['gate_build_hashes']
             and len(child['nodeids']) == expected[name]
             and not any(child['zero_body_counters'].values()), 'collection child source/zero-body receipt')
        need(stage['owned_receipt']['accepted'] is True
             and stage['owned_receipt']['cleanup_accepted'] is True
             and stage['owned_receipt']['job_active_after_cleanup'] == 0, 'collection group cleanup')
        add('collection_'+name+'__result.json',child_path)
        for filename in ('receipt.json','stdout.log','stderr.log'):
            add('collection_'+name+'__owned_'+filename,P/'gate-collection11-outer'/(name+'-owned')/filename)
    for name,row in final['outputs'].items():
        path = ROOT/name
        need(ref(path) == row, 'accepted native outputs full SHA/size')
        add(path.name,path)
        if path.suffix == '.xml':
            tree = ET.fromstring(path.read_bytes())
            cases = [(c.get('classname'),c.get('name')) for c in tree.iter('testcase')]
            group = 'merged' if path.name.endswith('-05.xml') else path.stem.rsplit('-',1)[-1]
            if path.name.endswith('-no-torch.xml'):
                group = 'no-torch'
            need(not any(list(tree.iter(tag)) for tag in ('failure','error','skipped'))
                 and len(cases) == len(set(cases)) == expected[group]
                 and Counter(cases) == Counter(tuple(v) for v in final['verified_JUnit'][group]['identities'])
                 and Counter(cases) == Counter((v['classname'],v['name']) for v in packet['expected_JUnit_ids'][group]),
                 'exact executed XML identities and no FES')
    before = P/'win-current-gate-20261109-05-outer/pointer-before.bytes'
    after = P/'win-current-gate-20261109-05-outer/pointer-after.bytes'
    need(before.read_bytes() == after.read_bytes() and sha(before) == final['pointer_before_sha256'],
         'original global pointer unchanged during Gate05')
    for directory in ('win-current-gate-20261109-05-outer','win-current-gate-20261109-05-child','gate-collection11-outer'):
        need(not (P/directory/'postwrite-rejection.json').exists(), 'no late rejection')
    reconciliation = read(P/'current_gate_outer03_canary01_reconciliation.json')
    old_canary = read(P/'current-gate-outer03-canary01/result.json')
    stderr = (P/'current-gate-outer03-canary01/stderr.log').read_bytes()
    need(sha(P/'current_gate_outer03_canary01_reconciliation.json') == RECONCILE_SHA
         and old_canary['status'] == 'REJECTED_READER_CANARY' and old_canary['returncode'] == 0
         and old_canary['source_before'] == old_canary['source_after']
         and 0 <= old_canary['elapsed_seconds'] <= old_canary['whole_seconds'] == 30
         and reconciliation['status'] == 'SIX_TEST_METHODS_PASSED_OUTER_REJECTED_CRLF_PATTERN'
         and reconciliation['additional_test_executions'] == 0
         and reconciliation['original_result_sha256'] == sha(P/'current-gate-outer03-canary01/result.json')
         and reconciliation['raw_stderr_sha256'] == hashlib.sha256(stderr).hexdigest()
         and b'OK' in stderr.splitlines() and any(line.startswith(b'Ran 6 tests') for line in stderr.splitlines()),
         'raw canary false reject and reconciliation kept separately')
    for name,digest in inputs['gate_build_hashes'].items():
        need(sha(ROOT/name) == digest, 'current source177 drift')
        reference(ROOT/name)
    for name,digest in inputs['support_document_sha256'].items():
        need(sha(ROOT/name) == digest, 'support source drift')
        reference(ROOT/name)
    for name,digest in final['controller_source_pins'].items():
        need(sha(ROOT/name) == digest, 'actual controller/runtime source drift')
        reference(ROOT/name)
    for row in read(P/'gate_source_snapshot06.json')['source_revision_provenance']['evidence_refs']:
        need(sha(ROOT/row['path']) == row['sha256'], 'historical source proof unchanged')
        reference(ROOT/row['path'])
    reference(ROOT/'research_tracking/runs/akt-windows-gate-current177-20261109-01/manifest.json')
    reference(ROOT/packet['runtime_report']['path'])
    reference(ROOT/inputs['lock_file'])
    inventory = [dict(copy=alias,source=path.relative_to(ROOT).as_posix(),**ref(path))
                 for alias,path in sorted(paths.items())]
    need(sum(row['bytes'] for row in inventory) <= 8*1024**2, 'compact copied evidence <=8MiB')
    return inventory,references,final,native,collection


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report-sha256',required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare-dry',action='store_true')
    mode.add_argument('--check-dry',action='store_true')
    mode.add_argument('--close',action='store_true')
    parser.add_argument('--expected-dry-sha256')
    parser.add_argument('--review-reference')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT/'.venv', 'repository .venv only')
    destination = ROOT/'research_tracking/runs'/RUN
    need(not destination.exists(), 'immutable destination absent')
    inventory,refs,final,native,collection = gather(args.report_sha256)
    dry = dict(run_id=RUN,report_sha256=args.report_sha256,copies=inventory,reference_inputs=refs,
               generated_outputs=list(GENERATED),expected_output_count=len(inventory)+len(GENERATED),
               accepted_outer_sha256=FINAL_SHA,collection_sha256=COLLECT_SHA,
               canary_reconciliation_sha256=RECONCILE_SHA)
    if args.prepare_dry:
        write(DRY,dry)
        print(json.dumps(dict(status='DRY_PREPARED_NOT_CLOSED',dry_sha256=sha(DRY),copies=len(inventory),
                              outputs=dry['expected_output_count'])))
        return
    need(read(DRY) == dry, 'exact reviewed/current dry bytes')
    if args.check_dry:
        print(json.dumps(dict(status='DRY_MATCH_NOT_CLOSED',outputs=dry['expected_output_count'])))
        return
    need(args.expected_dry_sha256 == sha(DRY) and args.review_reference, 'ROOT exact-dry closure review')
    sys.path.insert(0,str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    note = ('# Gate05 Windows CPU accepted\n\n1.748 physical items,0FES;177source/81modules. '
            'Collection11 trước chạy, exact JUnit IDs, owned cleanup/Job0, globalpointer unchanged. '
            'Giữ canary CRLF false reject và reconciliation. Gate04 vẫn REJECTED và chỉ reference bundle cũ. '
            'Software evidence, không fit nghiên cứu/GPU hoặc grant execution. '
            'Runtime schema2/index sau Gate05 có hồ sơ riêng. '
            'Báo cáo tại ../../reports/akt_windows_gate_accepted_20261109.md.\n')
    sources = list(dict.fromkeys([ROOT/row['source'] for row in inventory]+[ROOT/name for name in refs]+[DRY]))
    with record_evidence_run(ROOT,RUN,metadata=dict(kind='ACTUAL_WINDOWS_CPU_SOFTWARE_GATE_ACCEPTED',
            physical_tests=1748,failures=0,errors=0,skipped=0,global_pointer_published=False,
            research_fit_claim=False,gpu_readiness_claim=False),sources=sources,note=note) as out:
        copied = []
        for row in inventory:
            source = ROOT/row['source']
            need(ref(source) == dict(sha256=row['sha256'],bytes=row['bytes']), 'source before copy')
            (out/row['copy']).write_bytes(source.read_bytes())
            need(sha(source) == sha(out/row['copy']) == row['sha256'], 'before/copy/after SHA')
            copied.append(dict(**row,input_sha256_after=sha(source),copied_sha256=sha(out/row['copy'])))
        write(out/'copy_inventory.json',copied)
        write(out/'reference_inputs.json',refs)
        write(out/'source_binding.json',dict(gate_build_hashes=collection['source_before']['gate_build_hashes'],
              test_module_sha256=native['test_module_sha256'],
              old_gate04_bundle_referenced_not_duplicated=True,source177_not_duplicated=True,
              historical_gate_runtime_sha256=final['readiness']['runtime_report_sha256']))
        write(out/'scope.json',dict(status='ACCEPTED_ACTUAL_SOFTWARE_GATE_ONLY',physical_tests=1748,
              groups=dict(stdlib=19,**{'no-torch':271},remaining=1458),
              native_elapsed_seconds=native['elapsed_seconds'],native_cap_seconds=580,
              outer_elapsed_seconds=final['elapsed_seconds'],outer_cap_seconds=630,
              root_terminal_printed_seconds=480.8569538,root_printed_value_is_separate_observation=True,
              collection_seconds=collection['elapsed_seconds'],collection_cap_seconds=60,
              old_gate04='REJECTED',canary_child='SIX_METHODS_PASSED',canary_original_outer='REJECTED_CRLF_PATTERN',
              research_fit_claim=False,gpu_readiness_claim=False,all_nine_models_completed=False,
              later_schema2_runtime_and_index_archived_separately=True))
        write(out/'closure_review.json',dict(reference=args.review_reference,
              dry_sha256=args.expected_dry_sha256,report_sha256=args.report_sha256,no_reexecution=True))
        (out/'reviewed_dry.json').write_bytes(DRY.read_bytes())
        need(sha(out/'reviewed_dry.json') == args.expected_dry_sha256, 'dry copy')
        need({path.name for path in out.iterdir() if path.name != 'manifest.json'}
             == set(GENERATED)|{row['copy'] for row in inventory}, 'exact declared outputs')
        need(all(sha(ROOT/row['source']) == row['sha256'] for row in inventory)
             and all(ref(ROOT/name) == row for name,row in refs.items()), 'all inputs postcopy exact')
    verified = verify_evidence_bundle(destination)
    need(verified['artifacts'] == dry['expected_output_count'], 'all closed outputs verified')
    print(json.dumps(dict(**verified,manifest_sha256=sha(destination/'manifest.json'))))


if __name__ == '__main__':
    main()
