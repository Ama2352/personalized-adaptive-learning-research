"""ROOT-only dry inventory/closure cho nguồn177 và collection10/Gate04."""
from pathlib import Path
import argparse
from collections import Counter
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN_ID = 'akt-windows-gate-current177-20261109-01'
OLD = ROOT/'research_tracking/runs/akt-windows-gate-readiness-20261109-01/manifest.json'
OLD_SHA = 'f53291c057515f1159e1d520065e3d46744307511c428383cab8494ea5160d26'
COLLECTION = PREP/'gate-collection10-outer/final.json'
COLLECTION_SHA = 'f7a79a34809d777854724e0fac5f637379fec42c1bfed1adadf64315fb2157fa'
GATE = PREP/'win-current-gate-20261109-04-outer/result.json'
GATE_SHA = '12e9418c43045e48d0bead6c3be0b8cfd3a4733379c23c01ac91b30c6326639b'
FOCUSED_SHA = '4f7b109e7b927116d78fd7293b2528366796f0f58f44cbdbe6ad7e4e553b15a7'
REPAIR = {'scripts/akt/refresh_gate2.py':'8689c5b4737f4eae00459f4a3bc85c22206f58974274304fa4411e36f9acc055',
          'tests/akt/test_gate2_refresh.py':'268ace8716285c35db15caaae1efc819776795e3ef931f2e14f41b9cbe2a1e3c'}


def need(ok, reason):
    if not ok: raise ValueError(reason)


def safe(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and '..' not in path.parts,'absolute fixed ROOT path')
    cursor = ROOT
    for part in (None,*path.relative_to(ROOT).parts):
        if part is not None: cursor /= part
        need(not cursor.is_symlink() and not cursor.is_junction(),'physical evidence path')
    need(path.is_file(),'existing regular evidence')
    return path


def digest(raw): return hashlib.sha256(raw).hexdigest()


def sha(path):
    with safe(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write(path, value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False); stream.write('\n')


def collect(report, report_sha, gate_sha):
    payloads = {}
    def read(path):
        safe(path)
        if path not in payloads:
            need(path.suffix in ('.py','.json','.xml','.log','.md','.bytes','.before'),'text evidence only')
            need(path.suffix != '.bytes' or path.name in ('pointer-before.bytes','pointer-after.bytes'),'pointer bytes only')
            need(path.stat().st_size <= 32*1024**2,'per-file32MiB cap')
            payloads[path] = path.read_bytes()
            need(sum(map(len,payloads.values())) <= 64*1024**2,'total64MiB cap')
        return payloads[path]
    def load(path): return json.loads(read(path))
    def tree(folder):
        need(folder.is_dir() and not folder.is_symlink() and not folder.is_junction(),'required actual evidence directory')
        for path in sorted(folder.rglob('*')):
            if path.is_file() and 'runtime-temp' not in path.relative_to(folder).parts:
                read(path)
    need(digest(read(report)) == report_sha,'ROOT-reviewed report bytes')
    need(sha(OLD) == OLD_SHA,'historical Gate154 manifest reference')
    names = ('prepare_current_freeze04.py','prepare_current_freeze05.py',
        'gate_source_snapshot04.json','gate_source_snapshot05.json','CURRENT_GATE_DERIVATIVE04.md','CURRENT_GATE_DERIVATIVE05.md',
        'root_gate_freeze04_metadata_diagnostic01.json','root_gate_freeze05_relative_path_failure01.json',
        'ROOT_CURRENT_COLLECTION_REVIEW04.md','ROOT_CURRENT_COLLECTION_REVIEW05.md','ROOT_CURRENT_FULL_GATE_REVIEW04.md',
        'gate_collection_worker10.py','run_gate_collection10.py','gate_collection05_packet.ROOT.json',
        'windows_current_gate_worker02.py','windows_current_gate_outer02.py','prepare_windows_current_gate_packet03.py',
        'windows_current_gate_packet04.ROOT.json','pywin32_namespace_record01.json')
    for name in names: read(PREP/name)
    read(Path(__file__))
    tree(PREP/'gate-collection10'); tree(PREP/'gate-collection10-outer')
    tree(PREP/'gate-junit-items01'); tree(PREP/'gate-junit-items01-owned')
    for name in ('check_gate_junit_items01.py','run_gate_junit_items01.py','gate_junit_items01_packet.json'):
        read(PREP/name)
    for name,value in REPAIR.items(): need(digest(read(ROOT/name)) == value,'current reviewed repair source2')
    focused = load(PREP/'gate-junit-items01-owned/final.json')
    focused_child = load(PREP/'gate-junit-items01/result.json')
    need(digest(read(PREP/'gate-junit-items01-owned/final.json')) == FOCUSED_SHA
         and focused['status'] == 'ACCEPTED_GATE_JUNIT_ITEM_FIXTURES_ONLY'
         and focused['counts'] == dict(tests=99,failures=0,errors=0,skipped=0)
         and focused['errors'] == [] and focused['source_pins'] == REPAIR
         and focused['owned_receipt']['accepted'] is True and focused['owned_receipt']['returncode'] == 0
         and focused['owned_receipt']['cleanup_accepted'] is True and focused['owned_receipt']['job_active_after_cleanup'] == 0
         and focused_child['source_before'] == focused_child['source_after'] == REPAIR
         and focused_child['temporary_cache_restored'] is True and focused_child['environment_restored'] is True
         and focused_child['errors'] == focused_child['forbidden_attempts'] == focused_child['heavy_modules_loaded'] == [],
         'actual focused99 source/resource/purity/cleanup evidence')
    focused_xml = ET.fromstring(read(PREP/'gate-junit-items01/junit.xml'))
    need(len(list(focused_xml.iter('testcase'))) == 99
         and not any(list(focused_xml.iter(tag)) for tag in ('failure','error','skipped')),'focused99 raw JUnit')
    inputs = load(PREP/'gate_collection05_packet.ROOT.json')
    final = load(COLLECTION)
    need(digest(read(COLLECTION)) == COLLECTION_SHA,'actual accepted collection identity')
    need(final['status'] == 'ACCEPTED_COLLECTION_ONLY_NOT_GATE_PASS' and final['gate_pass'] is False
         and final['errors'] == [] and final['environment_restored'] is True
         and final['source_before'] == final['source_after'] and final['collected_count'] == 1726
         and final['module_count'] == 81 and 0 < final['elapsed_seconds'] < 60,'actual collection scope/resources')
    need(digest(read(PREP/'gate_collection05_packet.ROOT.json')) == final['packet_sha256'],'actual finalized metadata packet')
    need(len(inputs['gate_build_hashes']) == 177 and len(inputs['test_module_sha256']) == 81
         and final['source_before']['gate_build_hashes'] == inputs['gate_build_hashes'],'exact source177/module81')
    joined, groups = [], []
    for expected, stage in zip(inputs['module_groups'],final['stages']):
        path = ROOT/stage['child_result_relative']
        child = load(path)
        owned = stage['owned_receipt']
        need(digest(read(path)) == stage['child_result_sha256'],'raw collection child hash')
        need(owned['accepted'] is True and owned['returncode'] == 0 and owned['cleanup_accepted'] is True
             and owned['job_active_after_cleanup'] == 0 and owned['popen_handle_closed'] is True
             and owned['actual_worker_in_job_before_GO'] is True,'actual collection Job0')
        need(child['status'] == 'COLLECTED_ONLY_PENDING_OUTER' and child['pytest_exit_code'] == 0
             and child['modules'] == expected['modules'] and stage['group'] == expected['name']
             and child['source_before'] == child['source_after'] == inputs['gate_build_hashes']
             and child['support_document_before'] == child['support_document_after'] == inputs['support_document_sha256']
             and child['failures'] == child['forbidden_attempts'] == child['collection_reports'] == []
             and not any(child['zero_body_counters'].values()) and child['temporary_environment_and_cache_restored'] is True,
             'actual collection source/purity/support/temp boundaries')
        need(child['resources']['observed_minimum_available_ram_bytes'] >= 1024**3
             and all(v['observed_peak_bytes'] <= 3*1024**3 for v in child['resources']['workers'].values()),'collection resource observations')
        joined.extend(child['nodeids'])
        groups.append(dict(group=stage['group'],collected=child['collected_count'],child_sha256=stage['child_result_sha256']))
    need([g['collected'] for g in groups] == [19,271,1436] and len(groups) == 3
         and joined == final['nodeids'] and len(joined) == len(set(joined)) == 1726,'exact actual collected identity union')
    diagnostic = load(PREP/'root_gate_freeze04_metadata_diagnostic01.json')
    relative = load(PREP/'root_gate_freeze05_relative_path_failure01.json')
    need(diagnostic['build_equal'] is True and diagnostic['groups_equal'] is False
         and type(diagnostic['prior_failure']) is dict,'ordering preparation failure and normalized tool capture retained')
    need(relative['exit_code'] == 1 and relative['packet_created'] is False
         and relative['collection_started'] is False and relative['canonical_groups_check_passed'] is True,'relative command failure scope')
    source_map = inputs['gate_build_hashes']
    external = [dict(path=OLD.relative_to(ROOT).as_posix(),sha256=OLD_SHA,copy=False)]
    preserved = {name:PREP/'pre-gate-junit-subtests-fix01'/(Path(name).name+'.before')
                 for name in ('scripts/akt/refresh_gate2.py','tests/akt/test_gate2_refresh.py')}
    for name,value in source_map.items():
        item = dict(path=name,sha256=value,copy=False)
        if name in preserved:
            need(digest(read(preserved[name])) == value,'exact original source2 bytes for failed Gate04')
            item['preserved_copy'] = preserved[name].relative_to(ROOT).as_posix()
        external.append(item)
    for name in ('inventory.json','report-helper-before-inventory.json',
                 'akt_windows_gate_current_20261109.candidate.md.before','archive_current_windows_gate02.py.before'):
        read(PREP/'pre-gate-junit-subtests-fix01'/name)
    external += [dict(path=name,sha256=value,copy=False) for name,value in inputs['support_document_sha256'].items()]
    external.append(dict(path=inputs['lock_file'],sha256=inputs['lock_sha256'],copy=False))
    external += [dict(path='artifacts/akt/dependencies/upstream/'+name,sha256=value,copy=False)
                 for name,value in inputs['upstream_file_sha256'].items()]
    namespace = load(PREP/'pywin32_namespace_record01.json')
    external += [dict(path=name,sha256=value,copy=False) for name,value in namespace['file_sha256'].items()]
    full = dict(status='PENDING_ROOT_TERMINAL_RECEIPT_AND_REVIEW')
    if gate_sha:
        gate = load(GATE)
        need(gate_sha == GATE_SHA and digest(read(GATE)) == gate_sha,'ROOT external actual Gate04 terminal receipt pin')
        need(gate['status'] == 'REJECTED_WINDOWS_CPU_GATE' and gate['run_accepted'] is False
             and gate['publication_requested'] is False and gate['owned_receipt']['returncode'] == 1
             and gate['owned_receipt']['cleanup_accepted'] is True
             and gate['owned_receipt']['job_active_after_cleanup'] == 0,'failed Gate04 retained with cleanup')
        for folder in ('win-current-gate-20261109-04-outer','win-current-gate-20261109-04-child'): tree(PREP/folder)
        packet = load(PREP/'windows_current_gate_packet04.ROOT.json')
        need(packet['collection_result']['sha256'] == COLLECTION_SHA
             and gate['external_collection_packet_sha256'] == digest(read(PREP/'windows_current_gate_packet04.ROOT.json')),
             'actual Gate bound to exact accepted collection')
        for name, expected in gate['outputs'].items():
            need(digest(read(ROOT/name)) == expected['sha256'],'actual native output binding')
        diagnostic04 = load(PREP/'root_gate04_junit_surplus_diagnostic01.json')
        need(diagnostic04['kind'] == 'POSTHOC_PHYSICAL_JUNIT_ID_DIAGNOSTIC_NOT_GATE_ACCEPTANCE'
             and diagnostic04['physical_total'] == 1726 and diagnostic04['raw_attribute_total'] == 1791
             and diagnostic04['current_gate_pass'] is False and diagnostic04['native_cli_failed'] is True,
             'preserved failed04 posthoc identity diagnostic')
        for group in diagnostic04['groups']:
            xml_path = ROOT/f'artifacts/akt/preflight/gate2-tests-win-current-gate-20261109-04-{group["group"]}.xml'
            raw = read(xml_path); xml = ET.fromstring(raw)
            cases = [(v.get('classname'),v.get('name')) for v in xml.iter('testcase')]
            expected_ids = [(v['classname'],v['name']) for v in packet['expected_JUnit_ids'][group['group']]]
            need(digest(raw) == group['sha256'] and len(cases) == len(set(cases)) == group['physical_cases']
                 and Counter(cases) == Counter(expected_ids)
                 and not any(list(xml.iter(tag)) for tag in ('failure','error','skipped')),'posthoc raw physical identity/FES evidence')
        runtime = ROOT/packet['runtime_report']['path']
        need(digest(read(runtime)) == packet['runtime_report']['sha256'],'actual runtime report identity')
        need(not (ROOT/'artifacts/akt/preflight/gate2-evidence-win-current-gate-20261109-04.json').exists(),
             'failed native04 did not publish a Gate evidence report')
        full = dict(status=gate['status'],run_accepted=gate['run_accepted'],outer_seconds=gate['elapsed_seconds'],
            actual_result_sha256=gate_sha,publication_requested=gate['publication_requested'],errors=gate['errors'],
            physical_junit_items=1726,raw_tests_attribute_sum=1791,posthoc_diagnostic_sha256=digest(read(PREP/'root_gate04_junit_surplus_diagnostic01.json')))
    for item in external:
        need(sha(ROOT/item.get('preserved_copy',item['path'])) == item['sha256'],'external source/dependency/reference drift')
    summary = dict(kind='WINDOWS_CURRENT177_GATE_FAILURE_AND_JUNIT_FIXTURES',
        source_files=177,test_modules=81,collected_cases=1726,collection_groups=groups,
        collection_seconds=final['elapsed_seconds'],collection_result_sha256=COLLECTION_SHA,
        metadata04_ordering_failure=True,metadata05_relative_command_failure=True,
        metadata04_failure_capture='NORMALIZED_PRIOR_FAILURE_FIELD_IN_ACTUAL_DIAGNOSTIC',
        full_gate=full,focused99=dict(status=focused['status'],counts=focused['counts'],outer_seconds=focused['elapsed_seconds'],
            actual_result_sha256=FOCUSED_SHA,repair_source_sha256=REPAIR),external_references=external)
    return payloads, summary


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run',action='store_true'); mode.add_argument('--close',action='store_true')
    parser.add_argument('--report',type=Path,required=True); parser.add_argument('--report-sha256',required=True)
    parser.add_argument('--gate-result-sha256')
    parser.add_argument('--inventory',type=Path,required=True); parser.add_argument('--inventory-sha256')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT/'.venv','repository .venv')
    need(args.report in (PREP/'akt_windows_gate_current_20261109.candidate.md',
                         ROOT/'research_tracking/reports/akt_windows_gate_current_20261109.md'),'designated report only')
    payloads, summary = collect(args.report,args.report_sha256,args.gate_result_sha256)
    entries = [dict(source=path.relative_to(ROOT).as_posix(),bytes=len(raw),sha256_before_copy=digest(raw))
               for path,raw in sorted(payloads.items())]
    inventory = dict(run_id=RUN_ID,inputs=entries,input_occurrences=len(entries),
        unique_copies=len({v['sha256_before_copy'] for v in entries}),summary=summary)
    need(args.inventory.parent == PREP and not args.inventory.is_symlink() and not args.inventory.is_junction(),'inventory within prep')
    if args.dry_run:
        write(args.inventory,inventory)
        print(json.dumps(dict(status='DRY_ONLY',inventory_sha256=sha(args.inventory),inputs=len(entries),unique_copies=inventory['unique_copies']))); return
    need(args.gate_result_sha256 and summary['full_gate']['status'] != 'PENDING_ROOT_TERMINAL_RECEIPT_AND_REVIEW',
         'ROOT actual terminal review required before closure')
    need(args.inventory_sha256 and sha(args.inventory) == args.inventory_sha256
         and json.loads(args.inventory.read_bytes()) == inventory,'exact ROOT-reviewed dry inventory')
    need(not (ROOT/'research_tracking/runs'/RUN_ID).exists(),'exclusive bundle')
    for item in entries: need(sha(ROOT/item['source']) == item['sha256_before_copy'],'before-copy input hashes')
    sys.path.insert(0,str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    note = '''# Gate Windows nguồn177 ngày09/11/2026

validated_summary.json phân biệt metadata failures, actual collection và terminal Gate.
Collection10 có1726nodeIDs,19/271/1436 trong ba fresh groups, zero test bodies theo guards.
Các failures metadata04/câu lệnh relative05 được giữ nguyên phạm vi preparation.
Raw streams/receipts/source snapshots được copy byte-exact và đối chiếu SHA trước/sau.
Nguồn177, supportdocs5, namespace15 và old Gate154 được ghi bằng references/hash.
Gate04 bị từ chối tại merger do report-count khác physicalitem-count.
Raw1726physicalitems khớp expectedIDs và0FES. Console ghi65passedsubtests.
Targeted99 của parser/merger sửa đã accepted trong allocation riêng.
Gate04 tiếp tục REJECTED. Gate mới cần nguồn và collection mới theo ROOT review.
Benchmark nghiên cứu, full corpus fit và CUDA cần bằng chứng của các stage riêng.
'''
    sources = sorted(set(payloads) | {ROOT/item.get('preserved_copy',item['path']) for item in summary['external_references']})
    with record_evidence_run(ROOT,RUN_ID,metadata=dict(kind=summary['kind']),sources=sources,note=note) as out:
        copies = {}
        for item in entries:
            raw = payloads[ROOT/item['source']]
            value = item['sha256_before_copy']
            if value not in copies:
                target = out/f'input-{len(copies):03d}__{Path(item["source"]).name}'
                with target.open('xb') as stream: stream.write(raw)
                copies[value] = target
            target = copies[value]
            need(target.read_bytes() == raw and sha(ROOT/item['source']) == value,'copy byte equality and source posthash')
            item.update(copy=target.name,sha256_after_copy=sha(target),source_sha256_after_copy=value)
        write(out/'copy_inventory.json',entries)
        write(out/'validated_summary.json',summary)
    directory = ROOT/'research_tracking/runs'/RUN_ID
    verified = verify_evidence_bundle(directory)
    for item in entries: need(sha(ROOT/item['source']) == item['sha256_before_copy'],'final source hashes')
    force = PREP/'current_windows_gate177_force_paths01.txt'
    with force.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write('\n'.join(path.relative_to(ROOT).as_posix() for path in sorted(directory.iterdir()))+'\n')
    print(json.dumps(dict(status='CLOSED_BY_ROOT_METADATA_EXECUTION',verification=verified,
        manifest_sha256=sha(directory/'manifest.json'),files_including_manifest=len(list(directory.iterdir())),force_paths=str(force))))


if __name__ == '__main__': main()
