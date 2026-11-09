"""ROOT-only inventory/closure của actual runtime schema2 và Gate index."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN_ID = 'akt-windows-runtime-gate-index-20261109-01'
REPORT = ROOT/'research_tracking/reports/akt_windows_runtime_gate_index_20261109.md'
RUNTIME_SHA = '3fdddca8d9a39cf80e597cb6dd02701a3c619d64fc0f7ddadb1b6fb885ecd20b'
RUNTIME_FINAL_SHA = 'a5fb17e05ad07b0562ceb05045a8f9f8a2d749490efd18ce465308aa18c37fe6'
INDEX_SHA = 'e8162f6efce3ca0a443f6c40f69308b06b610e95d5a02504ba146e92b6f87366'
INDEX_FINAL_SHA = '718ae04bf5d8ad8c717be08f7de8803576db317f6f39235642d38e674eca09d7'
GLOBAL_SHA = '9e768aadcf084482a2eeb9be814fc399100dd1a507eaa89afbbae87100365cd6'
LEGACY_SHA = '259c171fe63e39a14d9bdf42793bd854a5be73ded19a7a800a2e8a982906f1b4'
GATE_OUTER_SHA = '9e61948b93e5f52de248cf076cd6225dc5253f48db949dd40c2a706f4e23d69e'
GATE_REPORT_SHA = '9dfc6f8592ef1d90b7430c06dbcbc96a92808f810c503043b5045c5560850afe'
GATE_LOG_SHA = 'cbc97aad1e5f28aedc173e6a9c5e0c1b5ee44d92226a97e450191b5b8b8b8eec'


def need(ok, message):
    if not ok: raise ValueError(message)


def safe(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and '..' not in path.parts,'absolute fixed project path')
    cursor = ROOT
    for part in (None,*path.relative_to(ROOT).parts):
        if part is not None: cursor /= part
        need(not cursor.is_symlink() and not cursor.is_junction(),'physical evidence path')
    need(path.is_file(),'existing regular evidence')
    return path


def sha(path):
    with safe(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def digest(raw): return hashlib.sha256(raw).hexdigest()


def write(path, value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False); stream.write('\n')


def gather(report_sha):
    payloads, references = {},{}
    def read(path):
        safe(path)
        if path not in payloads:
            need(path.suffix in ('.py','.json','.md','.log','.bytes'),'small textual evidence only')
            raw = path.read_bytes(); need(len(raw) <= 1024**2,'per-file1MiB cap')
            payloads[path] = raw
            need(sum(map(len,payloads.values())) <= 4*1024**2,'compact4MiB total cap')
        return payloads[path]
    def load(path): return json.loads(read(path))
    def reference(path, expected, scope):
        need(sha(path) == expected,'unchanged referenced evidence/source bytes')
        name = path.relative_to(ROOT).as_posix()
        row = dict(sha256=expected,bytes=path.stat().st_size,scope=scope,copy=False)
        if name in references: need(references[name]['sha256'] == expected,'reference identity collision')
        references[name] = row
    def flat(folder):
        need(folder.is_dir() and not folder.is_symlink() and not folder.is_junction(),'actual terminal folder')
        for path in sorted(folder.iterdir()):
            if path.name == 'runtime-temp': continue
            need(path.is_file(),'flat small terminal evidence')
            read(path)
    need(digest(read(REPORT)) == report_sha,'ROOT-reviewed canonical report bytes')
    runtime_final = load(PREP/'runtime-schema2-main177-01-owned/final.json')
    runtime_child = load(PREP/'runtime-schema2-main177-01/result.json')
    index_final = load(PREP/'gate05-main-index-publication01-owned/final.json')
    index_child = load(PREP/'gate05-main-index-publication01/result.json')
    runtime_path = ROOT/'artifacts/akt/preflight/runtime-schema2-main177-20261109-01.json'
    index_path = ROOT/'artifacts/akt/preflight/gate2-main177-win-current-gate-20261109-05.json'
    runtime = load(runtime_path); index = load(index_path)
    need(digest(read(PREP/'runtime-schema2-main177-01-owned/final.json')) == RUNTIME_FINAL_SHA
         and digest(read(PREP/'gate05-main-index-publication01-owned/final.json')) == INDEX_FINAL_SHA
         and digest(read(runtime_path)) == RUNTIME_SHA and digest(read(index_path)) == INDEX_SHA,'actual accepted stage SHA bindings')
    need(runtime_final['status'] == 'ACCEPTED_NATIVE_SCHEMA2_CPU_RUNTIME_ONLY' and runtime_final['accepted'] is True
         and runtime_final['errors'] == [] and runtime_final['worker_result'] == runtime_child
         and runtime_final['runtime_sha256'] == RUNTIME_SHA and 0 < runtime_final['elapsed_seconds'] < 60,'actual native runtime acceptance')
    need(runtime_child['status'] == 'NATIVE_SCHEMA2_RUNTIME_PENDING_OUTER' and runtime_child['accepted'] is True
         and runtime_child['errors'] == runtime_child['forbidden'] == [] and not any(runtime_child['counters'].values())
         and runtime_child['source_before'] == runtime_child['source_after'] == runtime_final['source_pins']
         and len(runtime_child['git_commands']) == 10 and len(runtime_child['availability_queries']) == 2
         and all(row['returned'] is True and row['value'] is False for row in runtime_child['availability_queries']),
         'real CLI source/call observer evidence')
    for name in ('profiler_restored','argv_restored','path_restored','environment_restored','temp_cache_restored',
                 'bytecode_setting_restored','monitor_stopped','global_pointer_unchanged','legacy_runtime_unchanged'):
        need(runtime_child[name] is True,'native observer/restoration boundaries')
    need(runtime['runtime_schema_version'] == 2 and runtime['device'] == 'cpu' and runtime['cuda_available'] is False
         and runtime == runtime_child['report'] and runtime['torch_version'] == '2.7.1+cpu'
         and runtime['numpy_version'] == '2.5.4' and runtime_child['cpu_library_observation']['cuda_build'] is None
         and runtime_child['cpu_library_observation']['cuda_initialized'] is False,'actual isolated CPU schema2 metadata')
    for phase in (runtime_final,index_final):
        receipt = phase['owned_receipt']
        need(receipt['accepted'] is True and receipt['returncode'] == 0 and receipt['cleanup_accepted'] is True
             and receipt['job_active_after_cleanup'] == 0 and receipt['popen_handle_closed'] is True
             and receipt['actual_worker_in_job_before_GO'] is True and receipt['cleanup_errors'] == [],'actual owned Job0 receipts')
    need(index_final['status'] == 'ACCEPTED_GENUINE_GATE05_MAIN_INDEX_ONLY' and index_final['accepted'] is True
         and index_final['errors'] == index_final['resource_errors'] == [] and index_final['worker_result'] == index_child
         and index_final['index_sha256'] == INDEX_SHA and index_final['environment_restored'] is True
         and index_final['global_pointer_before_sha256'] == index_final['global_pointer_after_sha256'] == GLOBAL_SHA
         and index_final['excluded_inherited_display_variable_names'] == ['GH_PAGER','GIT_PAGER']
         and 0 < index_final['elapsed_seconds'] < 30,'actual publisher acceptance and environment setup')
    need(index_child['status'] == 'PUBLISHED_GENUINE_GATE05_INDEX_ONLY' and index_child['accepted'] is True
         and index_child['errors'] == index_child['forbidden_attempts'] == [] and index_child['environment_unchanged'] is True
         and len(index_child['actual_git_commands']) == 10 and index_child['execution_authority'] is False
         and index_final['outer_public_reader'] == index_child['public_index_reader'],'actual original public preflight/readers')
    reader = index_child['public_index_reader']
    need(reader['status'] == 'PASS' and reader['pointer_sha256'] == INDEX_SHA
         and reader['report_sha256'] == GATE_REPORT_SHA and reader['test_log_sha256'] == GATE_LOG_SHA
         and index_child['runtime_preflight']['runtime_report_sha256'] == RUNTIME_SHA,'explicit index/report/runtime bindings')
    need(set(index) == {'schema_version','evidence_file','evidence_sha256','test_log_file','test_log_sha256'}
         and index['schema_version'] == 1 and index['evidence_sha256'] == GATE_REPORT_SHA
         and index['test_log_sha256'] == GATE_LOG_SHA,'native five-field index format')
    profile = load(PREP/'runtime-schema2-profile-launch01/result.json')
    reservation = load(PREP/'runtime-schema2-profile-launch01/reservation.json')
    allocation = load(PREP/'runtime_schema2_main177_01_packet.json')
    need(profile['returncode'] == 0 and profile['parent_environment_unchanged'] is True
         and profile['excluded_inherited_display_variable_names'] == ['GH_PAGER','GIT_PAGER']
         and reservation['child_git_environment'] == allocation['git_environment']
         and index_final['reviewed_temporary_git_profile'] == allocation['git_environment'],'actual two distinct environment setups')
    resources = runtime_child['resources']
    need(resources['samples'] > 0 and resources['peak_rss_bytes'] <= 1024**3
         and resources['minimum_available_ram_bytes'] >= 2*1024**3,'runtime observed resources')
    family = index_final['resources']
    need(family['samples'] > 0 and family['minimum_available_ram_bytes'] >= 2*1024**3
         and all(row['observed_peak_bytes'] <= 1024**3 for row in family['processes'].values()),'publisher observed per-process resources')
    for folder in ('runtime-schema2-main177-01','runtime-schema2-main177-01-owned',
                   'gate05-main-index-publication01','gate05-main-index-publication01-owned'):
        need(not any((PREP/folder/name).exists() for name in ('postwrite-rejection.json','resource-failure.json','call-guard-failure.json')),
             'no late/resource/call rejection')
        flat(PREP/folder)
    flat(PREP/'runtime-schema2-profile-launch01')
    for name in ('check_runtime_schema2_main177_01.py','run_runtime_schema2_main177_01.py',
                 'runtime_schema2_main177_01_packet.json','launch_runtime_schema2_profile01.py',
                 'publish_gate05_main_index01.py','run_publish_gate05_main_index01.py',
                 'ROOT_RUNTIME_SCHEMA2_REVIEW01.md','ROOT_GATE05_INDEX_PUBLICATION_REVIEW01.md',
                 'RUNTIME_SCHEMA2_MAIN177_PLAN01.md','GATE05_INDEX_PUBLISHER_HANDOFF01.md','GATE_GENUINE_ADMISSION_ROUTE01.md',
                 'upstream_verify_process_eol03.json','upstream_git_eol_preflight01.json'):
        read(PREP/name)
    read(ROOT/'scripts/akt/check_runtime.py'); read(Path(__file__).resolve())
    for folder,stage in (('runtime-schema2-main177-01-owned',runtime_final),('gate05-main-index-publication01-owned',index_final)):
        for name,expected in stage['owned_receipt']['output_sha256'].items():
            need(digest(read(PREP/folder/name)) == expected,'raw owned stream SHA')
    for name,expected in runtime_final['source_pins'].items(): reference(ROOT/name,expected,'executed_runtime_source_lock_upstream')
    reference(ROOT/'artifacts/akt/preflight/gate2-current.json',GLOBAL_SHA,'preserved_global_index')
    reference(ROOT/'artifacts/akt/preflight/runtime-v2.json',LEGACY_SHA,'preserved_legacy_report_without_schema2')
    legacy = json.loads((ROOT/'artifacts/akt/preflight/runtime-v2.json').read_bytes())
    need('runtime_schema_version' not in legacy,'legacy basename v2 is not schema2')
    for name,row in runtime_child['package_entries_before'].items():
        reference(Path(row['path']),row['sha256'],'runtime_package_entry_origin_before_after')
    for name,row in index_final['source_input_pins'].items():
        reference(ROOT/row['path'],row['sha256'],'publisher_actual_input_'+name)
    gate_path = PREP/'win-current-gate-20261109-05-outer/result.json'
    reference(gate_path,GATE_OUTER_SHA,'actual_accepted_Gate05_outer')
    gate = json.loads(gate_path.read_bytes())
    need(gate['status'] == 'ACCEPTED_WINDOWS_CPU_SOFTWARE_GATE_ONLY' and gate['run_accepted'] is True
         and gate['errors'] == [] and gate['owned_receipt']['cleanup_accepted'] is True,'actual Gate05 prerequisite')
    for name,row in gate['outputs'].items(): reference(ROOT/name,row['sha256'],'Gate05_raw_artifact_reference_only')
    native_path = ROOT/'artifacts/akt/preflight'/index['evidence_file']
    native = json.loads(native_path.read_bytes())
    need(native['test_result'] == dict(passed=1748,failed=0,errors=0,skipped=0)
         and len(native['build_hashes']) == 177 and len(native['test_module_sha256']) == 81,'native Gate05 scope')
    for name,value in native['build_hashes'].items(): reference(ROOT/name,value,'current_Gate05_source_reference_only')
    summary = dict(kind='ACTUAL_WINDOWS_CPU_RUNTIME_SCHEMA2_AND_GENUINE_GATE_INDEX',
        runtime=dict(status=runtime_final['status'],report_sha256=RUNTIME_SHA,outer_seconds=runtime_final['elapsed_seconds'],
                     worker_seconds=runtime_child['elapsed_seconds'],resources=runtime_child['resources'],
                     actual_git_commands=10,actual_false_availability_queries=2,body_counters=runtime_child['counters']),
        publication=dict(status=index_final['status'],index_sha256=INDEX_SHA,outer_seconds=index_final['elapsed_seconds'],
                         worker_seconds=index_child['elapsed_seconds'],resources=index_final['resources'],
                         actual_git_commands=10,excluded_display_variables=index_final['excluded_inherited_display_variable_names']),
        legacy_runtime_sha256=LEGACY_SHA,global_pointer_sha256=GLOBAL_SHA,gate_outer_sha256=GATE_OUTER_SHA,
        execution_authority=False,actual_main_selected_fit=False,scope_vi='Runtime/index engineering, source and metadata reads. Actual main A0 remains a separate gated stage.')
    return payloads,references,summary


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare-dry',action='store_true'); mode.add_argument('--close',action='store_true')
    parser.add_argument('--report-sha256',required=True)
    parser.add_argument('--inventory',type=Path,required=True)
    parser.add_argument('--inventory-sha256')
    parser.add_argument('--review-reference')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT/'.venv','repository .venv')
    need(args.inventory.parent == PREP and not args.inventory.is_symlink() and not args.inventory.is_junction(),'inventory within existing prep')
    payloads,references,summary = gather(args.report_sha256)
    inputs = [dict(source=path.relative_to(ROOT).as_posix(),bytes=len(raw),sha256_before_copy=digest(raw))
              for path,raw in sorted(payloads.items())]
    inventory = dict(run_id=RUN_ID,inputs=inputs,references=references,summary=summary,
        input_occurrences=len(inputs),unique_copies=len({row['sha256_before_copy'] for row in inputs}),
        total_copy_bytes=sum(len(raw) for raw in payloads.values()))
    if args.prepare_dry:
        write(args.inventory,inventory)
        print(json.dumps(dict(status='DRY_INVENTORY_READY',sha256=sha(args.inventory),inputs=len(inputs),unique_copies=inventory['unique_copies']))); return
    need(args.review_reference and args.inventory_sha256 and sha(args.inventory) == args.inventory_sha256
         and json.loads(args.inventory.read_bytes()) == inventory,'exact ROOT-reviewed inventory and closure reference')
    destination = ROOT/'research_tracking/runs'/RUN_ID
    need(not destination.exists(),'exclusive immutable bundle')
    for row in inputs: need(sha(ROOT/row['source']) == row['sha256_before_copy'],'precopy input SHA')
    sys.path.insert(0,str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    note = '''# Runtime schema2 và index Gate Windows ngày09/11/2026

Hai actual stages đã ACCEPTED. RuntimeCLI có0NNbody,10Git và2availabilityFalse.
Publisher có publicpreflight10Git, publicreaders và index mới e816.
Legacy259c và globalpointer9e768 được kiểm tra nguyên bytes.
Profile Win03 được setup rõ ràng. Runtime dùng child environment riêng,
publisher tạm cấu hình caller rồi restore. Chỉ hai PAGER đã review bị loại.
copy_inventory.json giữ SHA trước/sau và aliases dedup theo bytes.
references.json dẫn Gate05 JUnit/log/report và dependencies bằng SHA.
Không có kết quả actual main fit/CUDA hoặc hiệu quả nghiên cứu trong bundle.
'''
    sources = sorted(set(payloads) | {ROOT/name for name in references})
    with record_evidence_run(ROOT,RUN_ID,metadata=dict(kind=summary['kind'],closure_review=args.review_reference),
                             sources=sources,note=note) as out:
        copies = {}
        for row in inputs:
            source = ROOT/row['source']; raw = payloads[source]; value = row['sha256_before_copy']
            if value not in copies:
                target = out/f'input-{len(copies):03d}__{source.name}'
                with target.open('xb') as stream: stream.write(raw)
                copies[value] = target
            target = copies[value]
            need(target.read_bytes() == raw and sha(source) == value,'copy equality/source posthash')
            row.update(copy=target.name,sha256_after_copy=sha(target),source_sha256_after_copy=value)
        write(out/'copy_inventory.json',inputs)
        write(out/'references.json',references)
        write(out/'validated_summary.json',summary)
        write(out/'closure_review.json',dict(reference=args.review_reference,reviewed_inventory_sha256=args.inventory_sha256))
    verification = verify_evidence_bundle(destination)
    for row in inputs: need(sha(ROOT/row['source']) == row['sha256_before_copy'],'final source byte integrity')
    force = PREP/'windows_runtime_gate_index_force_paths01.txt'
    with force.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write('\n'.join(path.relative_to(ROOT).as_posix() for path in sorted(destination.iterdir()))+'\n')
    print(json.dumps(dict(status='CLOSED_BY_ROOT_METADATA_EXECUTION',verification=verification,
        manifest_sha256=sha(destination/'manifest.json'),files_including_manifest=len(list(destination.iterdir())),force_paths=str(force))))


if __name__ == '__main__': main()
