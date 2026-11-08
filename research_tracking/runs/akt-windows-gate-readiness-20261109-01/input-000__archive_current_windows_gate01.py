"""ROOT-only dry inventory/one closure; existing receipts only, no tests/native."""
from pathlib import Path
import argparse
from collections import Counter
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN_ID = 'akt-windows-gate-readiness-20261109-01'
REPORT = ROOT/'research_tracking/reports/akt_windows_gate_readiness_20261109.md'
OLD = ROOT/'research_tracking/runs/gate-collection-engineering-20261109-01/manifest.json'
OLD_SHA = 'aa3d46e5bc6898480503c90cc07a7e027e7735d616284ddafd4c91111c901d7d'
FINAL_SHA = 'fef18bdbd45ccb9eb6a42f11da0c26bc50fc54ab4d503edbf13024562accb45e'
CURRENT = {'scripts/akt/refresh_gate2.py':'9608ddfe1450b2d78699d5ec95d26b8cd65d4439fcc7bda209f698b2e4a7f9ef',
           'tests/akt/test_gate2_refresh.py':'255c07a3a1af2d458c8586bd206a3151baadeae76d1fa0a2ce3362409da8d5df'}


def need(ok,reason):
    if not ok: raise ValueError(reason)


def safe(path):
    need(path.is_absolute() and '..' not in path.parts and path.is_relative_to(ROOT),'fixed ROOT path')
    cursor = ROOT
    for part in (None,*path.relative_to(ROOT).parts):
        if part is not None: cursor /= part
        need(not cursor.is_symlink() and not cursor.is_junction(),'archive path alias')
    need(path.is_file(),'regular existing evidence file')
    return path


def digest(raw): return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with safe(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False); stream.write('\n')


def junit(raw):
    root = ET.fromstring(raw)
    cases = list(root.iter('testcase'))
    counts = {k:sum(int(s.get(k,'0')) for s in root.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
    need(len(cases)==counts['tests'],'XML count population')
    return counts,[(v.get('classname'),v.get('name')) for v in cases]


def collect(report_sha):
    payloads = {}
    def read(path):
        safe(path)
        if path not in payloads:
            need(path.suffix in ('.py','.json','.xml','.log','.md','.before','.bytes'),'small text evidence only')
            need(path.suffix!='.bytes' or path.name in ('pointer-before.bytes','pointer-after.bytes'),'pointer bytes only')
            raw = path.read_bytes(); need(len(raw)<=4*1024**2,'per-file4MiB cap')
            payloads[path]=raw
            need(sum(map(len,payloads.values()))<=32*1024**2,'total32MiB cap')
        return payloads[path]
    def load(path): return json.loads(read(path))
    def tree(folder):
        need(folder.is_dir() and not folder.is_symlink() and not folder.is_junction(),'required phase folder')
        for path in sorted(folder.rglob('*')):
            if path.is_file(): read(path)

    need(digest(read(REPORT))==report_sha,'ROOT-reviewed canonical report pin')
    need(file_sha(OLD)==OLD_SHA,'old01–05 bundle unchanged, reference only')
    external = [dict(path=OLD.relative_to(ROOT).as_posix(),sha256=OLD_SHA,copy=False)]
    for i in ('06','07','08','09'):
        tree(PREP/f'gate-collection{i}'); tree(PREP/f'gate-collection{i}-outer')
        for name in (f'gate_collection_worker{i}.py',f'run_gate_collection{i}.py',f'gate_collection{i}_root_review.json'): read(PREP/name)
    for i in ('01','02'):
        tree(PREP/f'gate-basetemp-fix{i}'); tree(PREP/f'gate-basetemp-fix{i}-owned')
        for name in (f'check_gate_basetemp_fix{i}.py',f'run_gate_basetemp_fix{i}.py'): read(PREP/name)
    for i in ('01','02','03'):
        tree(PREP/f'win-current-gate-20261109-{i}-child'); tree(PREP/f'win-current-gate-20261109-{i}-outer')
        read(PREP/f'windows_current_gate_root_dispatch{i}.json')
        for path in sorted((ROOT/'artifacts/akt/preflight').glob(f'gate2-*-win-current-gate-20261109-{i}*')):
            if path.is_file(): read(path)
    for folder in ('pre-gate-basetemp-root-fix01','pre-gate-scratch-layout-fix01'): tree(PREP/folder)
    for name in ('inspect_pywin32_namespace01.py','pywin32_namespace_record01.json','test_collection_namespace06.py',
        'collection_namespace06_pure.json','collection_namespace06_pure.log','prepare_current_freeze02.py','prepare_current_freeze03.py',
        'gate_collection02_packet.ROOT.json','gate_collection03_packet.ROOT.json','gate_frozen154_raw_git01.json','verify_gate_frozen_git01.py',
        'windows_current_gate_worker01.py','windows_current_gate_outer01.py','prepare_windows_current_gate_packet01.py','prepare_windows_current_gate_packet02.py',
        'windows_current_gate_packet.ROOT.json','windows_current_gate_packet02.ROOT.json','windows_current_gate_packet03.ROOT.json',
        'fullgate_memory_admission02.json','fullgate_memory_admission03.json','summarize_failed_gate02_population.py',
        'windows_current_gate02_population_postmortem.json'):
        read(PREP/name)
    read(Path(__file__))
    for name,digest_expected in CURRENT.items(): need(digest(read(ROOT/name))==digest_expected,'current source2overlay')

    # Preserve installed namespace provenance as receipts/hashes, not .venv copies.
    pywin = load(PREP/'pywin32_namespace_record01.json')
    need(pywin['status']=='INSTALLED_PYWIN32_RECORD_MATCHED_NOT_WHEEL_ATTESTATION'
         and len(pywin['file_sha256'])==15 and pywin['script_count']==12 and pywin['no_scripts_executed'] is True,'namespace provenance scope')
    collections = []
    for i,expected in (('06',None),('07',1417),('08',1418),('09',1418)):
        final = load(PREP/f'gate-collection{i}-outer/final.json')
        if expected is None:
            need(final['status']=='REJECTED_COLLECTION','06 rejection preserved')
        else:
            need(final['status']=='ACCEPTED_COLLECTION_ONLY_NOT_GATE_PASS' and final['collected_count']==expected
                 and final['source_before']==final['source_after'] and final['module_count']==69 and final['errors']==[],'accepted collection')
            union=[]
            for stage in final['stages']:
                child=load(ROOT/stage['child_result_relative']); owned=stage['owned_receipt']
                need(digest(read(ROOT/stage['child_result_relative']))==stage['child_result_sha256'],'collection child identity')
                need(owned['accepted'] is True and owned['cleanup_accepted'] is True and owned['job_active_after_cleanup']==0
                     and child['forbidden_attempts']==child['failures']==child['collection_reports']==[]
                     and not any(child['zero_body_counters'].values()),'collection guards/Job0')
                union.extend(child['nodeids'])
            need(union==final['nodeids'] and len(union)==len(set(union))==expected,'exact collected union')
        collections.append(dict(phase=i,status=final['status'],node_count=final['collected_count'],stored_outer_seconds=final['elapsed_seconds']))
    focus=[]
    for i in ('01','02'):
        final=load(PREP/f'gate-basetemp-fix{i}-owned/final.json')
        counts,_=junit(read(PREP/f'gate-basetemp-fix{i}/junit.xml'))
        need(final['status']=='ACCEPTED_GATE_BASETEMP_FIX_FIXTURES_ONLY' and counts==final['counts']==dict(tests=77,failures=0,errors=0,skipped=0),'actual focused77')
        need(final['owned_receipt']['cleanup_accepted'] is True and final['owned_receipt']['job_active_after_cleanup']==0,'focused cleanup')
        focus.append(dict(revision=i,counts=counts,stored_outer_seconds=final['elapsed_seconds']))

    first=load(PREP/'win-current-gate-20261109-01-outer/result.json')
    second=load(PREP/'win-current-gate-20261109-02-outer/result.json')
    final_path=PREP/'win-current-gate-20261109-03-outer/result.json'
    final=load(final_path)
    need(digest(read(final_path))==FINAL_SHA,'ROOT reviewed actual03 outer receipt')
    need(first['status']==second['status']=='REJECTED_WINDOWS_CPU_GATE','keep native01/02 failures')
    counts,_=junit(read(ROOT/'artifacts/akt/preflight/gate2-tests-win-current-gate-20261109-01-stdlib.xml'))
    need(counts==dict(tests=19,failures=0,errors=19,skipped=0),'01 actual setup errors')
    postmortem=load(PREP/'windows_current_gate02_population_postmortem.json')
    need(postmortem['status']=='COMPLETE_TEST_POPULATION_WITH_FAILURES_NOT_GATE_PASS'
         and postmortem['total']==dict(tests=1418,failures=3,errors=0,skipped=0)
         and postmortem['passed']==1415 and postmortem['merged_native_junit_created'] is False,'02 population postmortem')
    for group in postmortem['groups']:
        path=ROOT/f'artifacts/akt/preflight/gate2-tests-win-current-gate-20261109-02-{group["group"]}.xml'
        actual,_=junit(read(path)); need(actual==group['counts'] and digest(read(path))==group['xml_sha256'],'02 XML rawcounts')
    packet=load(PREP/'windows_current_gate_packet03.ROOT.json')
    inputs=load(ROOT/packet['collection_input']['path'])
    need(digest(read(ROOT/packet['collection_input']['path']))==packet['collection_input']['sha256'],'final sourcefreeze input')
    native_path=ROOT/'artifacts/akt/preflight/gate2-evidence-win-current-gate-20261109-03.json'
    native=load(native_path)
    need(final['status']=='ACCEPTED_WINDOWS_CPU_SOFTWARE_GATE_ONLY' and final['run_accepted'] is True
         and final['publication_requested'] is False and final['pointer_changed'] is False and final['errors']==[],'actual03 accepted/no promotion')
    owned=final['owned_receipt']
    need(owned['accepted'] is True and owned['cleanup_accepted'] is True and owned['job_active_after_cleanup']==0
         and owned['actual_worker_in_job_before_GO'] is True and owned['popen_handle_closed'] is True,'03 actual Job0')
    need(native['status']=='PASS' and native['build_hashes']==inputs['gate_build_hashes']
         and len(native['build_hashes'])==154 and len(native['test_module_sha256'])==69
         and native['test_result']==dict(passed=1418,failed=0,errors=0,skipped=0)
         and native['timeout_seconds']==580 and 0<native['elapsed_seconds']<580 and 0<final['elapsed_seconds']<630,'native03 source/time/population')
    for group in ('stdlib','no-torch','remaining','merged'):
        path=ROOT/('artifacts/akt/preflight/gate2-tests-win-current-gate-20261109-03'+('' if group=='merged' else '-'+group)+'.xml')
        counts,actual=junit(read(path))
        expected=[(v['classname'],v['name']) for v in packet['expected_JUnit_ids'][group]]
        need(len(actual)==len(set(actual)) and Counter(actual)==Counter(expected)
             and counts==dict(tests=len(expected),failures=0,errors=0,skipped=0),'03 exact actual JUnit IDs')
    for name,item in final['outputs'].items(): need(digest(read(ROOT/name))==item['sha256'],'03 output byte binding')
    for name,expected in native['build_hashes'].items(): need(file_sha(ROOT/name)==expected,'154 actual current source bindings, no copies')
    for name,expected in packet['controller_source_pins'].items(): need(file_sha(ROOT/name)==expected,'dispatched additional source pins')
    runtime_path=ROOT/packet['runtime_report']['path']; need(digest(read(runtime_path))==packet['runtime_report']['sha256'],'runtime exact bytes')
    lock=ROOT/'requirements-akt.lock.txt'; need(file_sha(lock)==native['lock_sha256'],'current lock binding')
    base=load(PREP/'gate_frozen154_raw_git01.json')
    need(base['commit']=='2c337d4' and len(base['source_sha256'])==154
         and set(base['source_sha256'])==set(native['build_hashes'])
         and {n:v for n,v in native['build_hashes'].items() if v!=base['source_sha256'][n]}==CURRENT,'baseGit154 plus exactlytwo overlays')
    for folder,expected in (('pre-gate-basetemp-root-fix01',base['source_sha256']),
                            ('pre-gate-scratch-layout-fix01',load(PREP/'gate_collection02_packet.ROOT.json')['gate_build_hashes'])):
        for source in CURRENT:
            need(digest(read(PREP/folder/(Path(source).name+'.before')))==expected[source],'preserved before source snapshots')
    resources=final['worker_result']['resources']
    summary=dict(kind='WINDOWS_CURRENT_SOFTWARE_GATE_INVESTIGATION_EXISTING_RAW_ONLY',collections=collections,focused=focus,
        native01=dict(status=first['status'],stored_outer_seconds=first['elapsed_seconds'],tests=19,errors=19),
        native02=dict(status=second['status'],stored_outer_seconds=second['elapsed_seconds'],tests=1418,passed=1415,failures=3),
        native03=dict(status=final['status'],stored_outer_seconds=final['elapsed_seconds'],native_seconds=native['elapsed_seconds'],
            tests=1418,failures=0,errors=0,skipped=0,peak_observed_bytes=max(v['observed_peak_bytes'] for v in resources['workers'].values()),
            minimum_available_bytes=resources['observed_minimum_available_ram_bytes'],samples=resources['samples'],
            source_files=154,test_modules=69,pointer_changed=False,published_current=False),
        current_overlay=CURRENT,base_git='2c337d4',base_git_proof_does_not_certify_current_uncommitted_overlay=True,
        external_references=external,scope_vi='Không chạy lại tests/model hoặc promote pointer khi archive; Windows synthetic software, không Linux/CUDA/research proof.')
    return payloads,summary,native['build_hashes']


def main():
    parser=argparse.ArgumentParser()
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--dry-run',action='store_true'); modes.add_argument('--close',action='store_true')
    parser.add_argument('--report-sha256',required=True)
    parser.add_argument('--inventory',type=Path,required=True)
    parser.add_argument('--inventory-sha256')
    args=parser.parse_args()
    need(Path(sys.prefix).resolve()==ROOT/'.venv','repository .venv only')
    payloads,summary,source_map=collect(args.report_sha256)
    inputs=[dict(source=p.relative_to(ROOT).as_posix(),bytes=len(raw),sha256_before_copy=digest(raw)) for p,raw in sorted(payloads.items())]
    inventory=dict(run_id=RUN_ID,inputs=inputs,unique_copies=len({v['sha256_before_copy'] for v in inputs}),
        input_occurrences=len(inputs),total_source_bytes=sum(len(v) for v in payloads.values()),summary=summary)
    need(args.inventory.parent==PREP and not args.inventory.is_symlink() and not args.inventory.is_junction(),'inventory in existing prep')
    if args.dry_run:
        write(args.inventory,inventory)
        print(json.dumps(dict(status='DRY_INVENTORY_ONLY_NOT_CLOSED',path=str(args.inventory),sha256=file_sha(args.inventory),
            input_occurrences=len(inputs),unique_copies=inventory['unique_copies'],report_sha256=args.report_sha256)));return
    need(args.inventory_sha256 and file_sha(args.inventory)==args.inventory_sha256,'ROOT-reviewed exact dry inventory pin')
    need(json.loads(args.inventory.read_bytes())==inventory,'sources/scope changed after dry review')
    need(not (ROOT/'research_tracking/runs'/RUN_ID).exists(),'exclusive new bundle; no overwrite')
    for item in inputs: need(file_sha(ROOT/item['source'])==item['sha256_before_copy'],'precopy source drift')
    sys.path.insert(0,str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    note='''# Windows current software Gate — 09/11/2026

Actual03:1418PASS/0failure/error/skip, exact collected identities,154sources/69modules,
Windows CPU only. Native355,0576142s/580; outer358,7608751s/630; Job0, noPublish,
pointer unchanged. Giữ06failure,07–09collections, native01/02failures, focused77
hai revisions, current03accepted. Không relabel collection/focused thành fullGate.

copy_inventory.json giữ sourcepath/SHA trước=saucopy và aliases dedup nguyên byte.
validated_summary.json phân biệt stages; current_source_bindings.json giữ154SHA
không154copies. Hai canonicalsource files có threeversion overlays/before snapshots;
Git2c337d4 proof chỉ nền152unchanged+old2, không currentpostcommit proof.
Report Việt đi kèm là input nguyên byte. Old01–05bundle chỉ reference manifestSHA.

Không chạy lại test/model/teacher, không read realJunyi/Holdout/corpus, không
Linux/CUDA/fulltraining/RQefficacy proof. Logs native giả lập và actual fixtures
giữ scope; resource poll không hardOSquota/wholehost attestation. No pointerpromotion.
'''
    sources=sorted(set(payloads) | {ROOT/name for name in source_map} | {OLD})
    with record_evidence_run(ROOT,RUN_ID,metadata=dict(kind=summary['kind'],validated_summary=summary),
            sources=sources,note=note) as out:
        copies={}
        for item in inputs:
            path=ROOT/item['source']; raw=payloads[path]; sha=item['sha256_before_copy']
            if sha not in copies:
                target=out/f'input-{len(copies):03d}__{path.name}'
                with target.open('xb') as stream: stream.write(raw)
                copies[sha]=target
            target=copies[sha]
            need(target.read_bytes()==raw and file_sha(path)==sha,'byte-exact source/copy postcheck')
            item.update(copy=target.name,sha256_after_copy=file_sha(target),source_sha256_after_copy=sha)
        write(out/'copy_inventory.json',inputs)
        write(out/'validated_summary.json',summary)
        write(out/'current_source_bindings.json',dict(build_hashes=source_map,current_overlay=CURRENT,external_references=summary['external_references']))
    directory=ROOT/'research_tracking/runs'/RUN_ID
    verified=verify_evidence_bundle(directory)
    for item in inputs: need(file_sha(ROOT/item['source'])==item['sha256_before_copy'],'source changed after closure')
    force=PREP/'current_windows_gate_force_paths01.txt'
    with force.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write('\n'.join(p.relative_to(ROOT).as_posix() for p in sorted(directory.iterdir()))+'\n')
    print(json.dumps(dict(status='CLOSED_VERIFIED_BY_ROOT_METADATA_EXECUTION',verification=verified,
        manifest_sha256=file_sha(directory/'manifest.json'),files_including_manifest=len(list(directory.iterdir())),
        force_paths=force.relative_to(ROOT).as_posix(),input_occurrences=len(inputs),unique_copies=len(copies))))


if __name__=='__main__': main()
