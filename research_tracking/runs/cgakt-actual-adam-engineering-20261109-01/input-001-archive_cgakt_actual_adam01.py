"""ROOT dry/close GRAPH10: chỉ đọc/copy metadata, không chạy lại model/test."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
RUN_ID = 'cgakt-actual-adam-engineering-20261109-01'
CANDIDATE = P/'cgakt_actual_adam_20261109.candidate.md'
CANONICAL = ROOT/'research_tracking/reports/cgakt_actual_adam_20261109.md'
REPORT_SHA = 'c01779dfa9a7a821e31993bb3fed9b43f8e948e5abd5ae518ac9bbf3153c3bb0'
TEST = 'tests/akt/test_research_graph_optimizer.py'
TEST_SHA = '5bdc3e5373c04a8f0a6199628b00461039e51c35bbfab8186f46a2ce342f4afc'
PINS = {
    'check_cgakt_graph10_optimizer01.py': '88357c12c0d4ada6d6f048a2e904170936043045bac9197423ff22e9d2593a5d',
    'run_cgakt_graph10_optimizer01.py': '8cbba573a1619c19fddb3d71e5d39c171f93e45289c7ee87ff4eab1889ecfa54',
    'cgakt_graph10_optimizer01_allocation.json': 'a424c30c1b15bb9c56dbc8233e5658bb37faa19ef7edb171103415136cc0760a',
    'check_cgakt_graph10_optimizer02.py': 'b52ce13ac1537532fdc42d2ab20f188f513112ca7c2d17e888f4fa9cf04bd18e',
    'run_cgakt_graph10_optimizer02.py': '8049eeed3e4294913cf1364567fcb20c8bc28b83075de9ad52f85fea179713d2',
    'cgakt_graph10_optimizer02_allocation.json': '63ea4fd26f2f566f1d4b3a6113affa6aa25482e9280bd8fe8fb76efa1a2ef70f',
    'method_patch_observer02.py': '57a762f20e7147f7195ee6538fecdf960cd83d556a6ac4989656e2b7c1fed42b',
    'check_method_patch_observer02.py': 'fc09c7e2321215f376aba743adc91a87187f9556328c2863c474205b517610bf',
    'run_method_observer_pure02.py': '76d4a961d16bb5a35e5743b25c25fdb36343a2321c54dc837c430933e13a80b1',
    'CGAKT_ACTUAL_ADAM_CHECK_PLAN01.md': '1ed422550556e6cfcf31b89d711053e5ff56e9959218fa92f254274c7661ca76',
    'graph10_plan_cuda_query_erratum01.json': '40628cb8de2a005b4b674f6941fc7f09b8496a27f35f629ba536c0a76bbf3011',
}
COUNTS = dict(tests=1, failures=0, errors=0, skipped=0)
NATIVE = dict(adapter_constructors=1, backbone_constructors=1, wrapper_constructors=1,
    gate_constructors=1, forwards=3, logical_backwards=3, clip_calls=3,
    adam_constructors=1, adam_steps=3, adapter_steps=3)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')


def safe(path, existing=True):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts and path.is_relative_to(ROOT), 'fixed project path')
    cursor = ROOT
    for part in (None, *path.relative_to(ROOT).parts):
        if part is not None:
            cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'alias rejected')
    need(path.resolve().is_relative_to(ROOT.resolve()), 'physical project path')
    if existing:
        need(path.is_file(), 'regular input required')
    return path


def gather(report):
    payloads, checked, trials = {}, {}, {}
    def read(path):
        path = safe(path)
        if path not in payloads:
            need(path.stat().st_size <= 2*1024**2, 'input2MiB cap')
            raw = path.read_bytes()
            need(len(raw) <= 2*1024**2, 'read2MiB cap')
            payloads[path] = raw
            need(sum(map(len, payloads.values())) <= 5*1024**2, 'total5MiB cap')
        return payloads[path]
    load = lambda path: json.loads(read(path))
    for name, digest in PINS.items():
        need(sha(read(P/name)) == digest, 'pinned preparation drift:'+name)
    need(report in (CANDIDATE, CANONICAL) and sha(read(report)) == REPORT_SHA, 'reviewed report bytes')
    need(sha(read(ROOT/TEST)) == TEST_SHA, 'new test source')
    for number, expected_status, expected_final_sha in (
        ('01', 'REJECTED_GRAPH10_ACTUAL_ADAM_CHECK', '0f9d24e21949b397621e3a87bf199e86464dae53fa7a957e8db6caa8c7ee1fe6'),
        ('02', 'ACCEPTED_GRAPH10_ACTUAL_ADAM_ENGINEERING_ONLY', 'b21d17a98bcc91afb5580fdb96ae6abd31ef991b35f4c432db68bc8216c30534')):
        child_dir = P/('cgakt-graph10-optimizer'+number)
        owned_dir = P/(child_dir.name+'-owned')
        packet = load(P/('cgakt_graph10_optimizer'+number+'_allocation.json'))
        child = load(child_dir/'result.json'); final = load(owned_dir/'final.json')
        owned = load(owned_dir/'receipt.json')
        need(sha(read(owned_dir/'final.json')) == expected_final_sha and final['status'] == expected_status, 'actual terminal identity/status')
        tree = ET.fromstring(read(child_dir/'junit.xml'))
        counts = {k: sum(int(s.get(k, '0')) for s in tree.iter('testsuite')) for k in COUNTS}
        cases = list(tree.iter('testcase'))
        need(counts == COUNTS == child['counts'] == final['counts'] and len(cases) == 1
             and cases[0].get('name') == 'test_owned_adam_inactive_then_two_active_steps_have_live_updates_and_participation', 'actual one testcase, not three cases')
        need(child['native_started'] == child['native_body_returned'] == NATIVE == packet['expected_native_counts'], 'actual3updates even rejected01')
        need(child['source_before'] == child['source_after'] == packet['source_pins'] == final['source_after'], 'source before/after')
        for name, digest in packet['source_pins'].items():
            need(name not in checked or checked[name] == digest, 'cross-trial source disagreement')
            checked[name] = digest
        need(owned['cleanup_accepted'] and owned['job_active_after_cleanup'] == 0
             and owned['popen_handle_closed'] and owned['actual_worker_in_job_before_GO'], 'owned Job cleanup proof')
        # Lượt01 thật sự RC1/acceptedFalse; giữ verdict thất bại thay vì đòi
        # một worker thành công cho cả hai attempts khi đóng gói evidence.
        need(owned['accepted'] is (number == '02')
             and owned['returncode'] == (0 if number == '02' else 1), 'actual failed01 versus accepted02 worker verdict')
        need(child['runtime_restored'] and child['environment_restored'] and child['monitor_stopped']
             and child['monitor_errors'] == [] and child['forbidden_attempts'] == [], 'restoration and forbidden guards')
        need(child['methods_restored'] is (number == '02'), 'preserved observer failure01')
        if number == '02':
            restoration = child['method_restoration']
            need(restoration['accepted'] and restoration['patched_targets'] == 30
                 and len(restoration['final_checks']) == 30 and all(row['restored'] for row in restoration['final_checks'])
                 and restoration['restore_errors'] == [], 'actual all30 final checks')
            need(final['pure_allocation_charged_seconds'] == 5 and final['prior_actual_adam_steps'] == 3
                 and final['cumulative_adam_body_returned'] == 6 and final['cumulative_adam_started'] == 6
                 and final['cumulative_charged_seconds'] < final['cumulative_cap_seconds'] == 105.3190763, 'cumulative budget/counts')
        need(child['upstream_cuda_availability'] == [dict(phase='local_git_provenance', result=False)]
             and child['optimizer_cpu_availability'] == [] and child['torch_profile']['cuda_initialized_after'] is False, 'actual false query, not zero-query claim')
        need(len(child['local_git_provenance']['commands']) == 10 and child['local_git_provenance']['original_loader_used'], 'normal Git provenance')
        summary = child['test_globals_summary']
        need(summary['attempts'] == summary['ledger_rows'] == 3 and summary['valid_targets'] == [6,6,6]
             and summary['reservation']['planned_targets'] == 18, 'actual target visits/ledger')
        need(sha(read(child_dir/'test-globals.json')) == child['test_globals_sha256'], 'actual ledger bytes')
        for name, row in final['output_inventory'].items():
            need(name in ('case_events.jsonl','junit.xml','pytest.log','reservation.json','result.json','test-globals.json')
                 and sha(read(child_dir/name)) == row['sha256'] and len(read(child_dir/name)) == row['bytes'], 'child output binding')
        need(sha(read(owned_dir/'receipt.json')) == final['owned_receipt_sha256'], 'outer-owned binding')
        for name, digest in owned['output_sha256'].items():
            need(name in ('stdout.log','stderr.log') and sha(read(owned_dir/name)) == digest, 'raw stdout/stderr binding')
        for name in ('case_events.jsonl','junit.xml','pytest.log','reservation.json','result.json','test-globals.json'):
            read(child_dir/name)
        for name in ('final.json','GO.json','launch.json','ready.json','receipt.json','stderr.log','stdout.log'):
            read(owned_dir/name)
        trials[number] = dict(status=final['status'], junit=counts, native=child['native_body_returned'],
            child_seconds=child['elapsed_seconds'], native_seconds=child['native_work_seconds'],
            stored_outer_seconds=final['elapsed_seconds'], methods_restored=child['methods_restored'],
            resources=child['resources'], owned_cleanup=True, target_visits=18)
    pure_dir = P/'graph10-observer-pure02'; pure = load(pure_dir/'result.json')
    need(sha(read(pure_dir/'result.json')) == 'f9b6f4dee1d51f0b5f8bc50e1bfb38fc8587109dd5db938a49e979316ff48e24'
         and pure['status'] == 'ACCEPTED_FIVE_STDLIB_METHOD_OBSERVER_CASES_NOT_NATIVE' and pure['returncode'] == 0
         and pure['actual'] == dict(kind='STDLIB_OBSERVER_ONLY_NOT_NATIVE', tests=5, failures=0, errors=0, skipped=0)
         and pure['source_before'] == pure['source_after'] and pure['seconds'] < pure['whole_cap_seconds'] == 5, 'actual pure5')
    for name, digest in pure['source_before'].items():
        need(sha(read(P/name)) == digest, 'pure source binding')
    for name, digest in pure['output_sha256'].items():
        need(name in ('stdout.log','stderr.log') and sha(read(pure_dir/name)) == digest, 'pure raw logs')
    before = P/'graph10-observer-before02'; snap = load(before/'inventory.json')
    for row in snap['controller_copies']:
        need(sha(read(before/row['source'])) == row['sha256_before_copy'] == row['sha256_after_copy']
             == row['source_sha256_after_copy'] == sha(read(P/row['source'])), 'controller before-copy evidence')
    for row in snap['actual01_raw_before_after']:
        need(sha(read(P/row['source'])) == row['sha256'] and len(read(P/row['source'])) == row['bytes'], 'actual01 retained byte evidence')
    snap_dir = P/'graph10-optimizer-source01'; snap = load(snap_dir/'inventory.json')
    need(sha(read(snap_dir/snap['snapshot'])) == snap['sha256_before_copy'] == snap['sha256_after_copy']
         == snap['source_sha256_after_copy'] == TEST_SHA, 'new test snapshot')
    for name, digest in checked.items():
        need(sha(safe(ROOT/name).read_bytes()) == digest, 'current source/runtime drift:'+name)
    reference = ROOT/'research_tracking/runs/cgakt-context-model-hotpath-engineering-20261109-01/manifest.json'
    old = load(reference)
    need(old['status'] == 'completed' and len(old['outputs_sha256']) == 41
         and sha(read(reference)) == '38ce2196a3472a674dad94bef48f79b7a248f126729c85651d6dac8559dfd6ef', 'old41 manifest reference')
    read(Path(__file__).resolve())
    aliases, unique = [], {}
    for path, raw in sorted(payloads.items()):
        digest = sha(raw)
        unique.setdefault(digest, f'input-{len(unique)+1:03d}-'+path.name)
        aliases.append(dict(source=path.relative_to(ROOT).as_posix(), bytes=len(raw), sha256_before_copy=digest, archived_as=unique[digest]))
    return dict(schema_version=1, run_id=RUN_ID, report_source=report.relative_to(ROOT).as_posix(),
        input_aliases=aliases, unique_input_copies=len(unique), checked_source_bindings=checked,
        outcomes=dict(trials=trials, pure=pure['actual'], actual_total_adam_updates=6,
            cumulative_charged_seconds=final['cumulative_charged_seconds'], cumulative_cap_seconds=105.3190763,
            target_scope_vi='18processedvisits/12distincteventIDs perattempt; same fixture repeated, no independentN'),
        old_bundle_reference=dict(path=reference.relative_to(ROOT).as_posix(), sha256=sha(read(reference)), outputs=41, copied_whole_bundle=False)), payloads


def recheck(inventory):
    for row in inventory['input_aliases']:
        need(sha(safe(ROOT/row['source']).read_bytes()) == row['sha256_before_copy'], 'input drift')
    for name, digest in inventory['checked_source_bindings'].items():
        need(sha(safe(ROOT/name).read_bytes()) == digest, 'dependency drift')


def main():
    need(os.path.normcase(os.path.abspath(sys.executable)) == os.path.normcase(str(ROOT/'.venv/Scripts/python.exe'))
         and Path(sys.prefix).resolve() == ROOT/'.venv', 'repository .venv only')
    parser = argparse.ArgumentParser(description='ROOT metadata dry/close only; không rerun test/model')
    parser.add_argument('--report', type=Path, default=CANDIDATE)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--close', action='store_true')
    parser.add_argument('--expected-inventory-sha256')
    args = parser.parse_args(); report = safe(args.report.absolute())
    inventory_path = safe(args.inventory.absolute(), existing=args.close)
    need(inventory_path.parent == P and inventory_path.suffix == '.json', 'prep-only inventory')
    need(not (ROOT/'research_tracking/runs'/RUN_ID).exists(), 'immutable run already exists')
    inventory, payloads = gather(report); raw = encoded(inventory); recheck(inventory)
    if not args.close:
        need(not inventory_path.exists() and args.expected_inventory_sha256 is None, 'exclusive dry inventory')
        with inventory_path.open('xb') as handle:
            handle.write(raw); handle.flush(); os.fsync(handle.fileno())
        print(json.dumps(dict(status='DRY_ONLY_NOT_CLOSED', inventory_sha256=sha(raw),
            aliases=len(inventory['input_aliases']), unique_copies=inventory['unique_input_copies'], outcomes=inventory['outcomes'])))
        return
    need(args.expected_inventory_sha256 == sha(inventory_path.read_bytes()) == sha(raw), 'external reviewed dry SHA required')
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    note = '''# CG-AKT actual Adam — engineering09/11/2026

01 JUnit1PASS/3actualupdates nhưng overallREJECTED do methodobserver.02 JUnit1PASS/
3actualupdates được accepted, all30 finalmethodchecks. Tổng actual6updates trên
cùngfixture, không3nativecases/không18independentobservations. Pure5 là scope
stdlib riêng. Native3forward/3logicalbackward/3clip/3Adamsteps/18targetvisits mỗi
attempt. MissingAdamstate inactive và zeroTensorgrad active1 là hợp lệ.
Giữ rawlogs và snapshots tồn tại thực, SHA trước/saucopy. Oldhotpath41 chỉthamchiếu
manifest; khôngcopydeps/venv. Plan giữbytes; erratum sửa0CUDAquery thành1actualfalse
upstreamquery mỗiattempt,AdamExtra0,0init/allocation trong scope CPU đã đo.
Charged34.65431779999721 khác tổng roundedterminal; xem receipts từngclockpoint.
Khôngrerun khiarchive; không actualcorpus/checkpoint/resume/calibration/fitted/
maintraining/CUDA/throughput/cost/RQclaim. Monitorcooperative, không hardOSquota.
'''
    git_before = {k:v for k,v in os.environ.items() if k.startswith('GIT_')}
    try:
        for key in list(git_before): os.environ.pop(key, None)
        os.environ.update(GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='safe.directory', GIT_CONFIG_VALUE_0=ROOT.as_posix())
        sources = sorted(set(payloads) | {ROOT/name for name in inventory['checked_source_bindings']} | {inventory_path})
        with record_evidence_run(ROOT, RUN_ID, metadata=dict(kind='CGAKT_ACTUAL_ADAM_SYNTHETIC_ENGINEERING_ONLY',
                outcomes=inventory['outcomes'], source_bindings=inventory['checked_source_bindings'],
                old_bundle_reference=inventory['old_bundle_reference']), sources=sources, note=note) as directory:
            with (directory/'inventory-before.json').open('xb') as handle: handle.write(raw)
            copied = {}
            for row in inventory['input_aliases']:
                if row['archived_as'] in copied: continue
                target = directory/row['archived_as']
                with target.open('xb') as handle:
                    handle.write(payloads[ROOT/row['source']]); handle.flush(); os.fsync(handle.fileno())
                copied[row['archived_as']] = sha(target.read_bytes())
                need(copied[row['archived_as']] == row['sha256_before_copy'], 'copied bytes mismatch')
            recheck(inventory)
            verification = dict(status='VERIFIED_BYTE_COPIES_NOT_RERUN', inventory_sha256=sha(raw), copied_sha256=copied,
                sources_after={row['source']: sha(safe(ROOT/row['source']).read_bytes()) for row in inventory['input_aliases']})
            with (directory/'copy-verification.json').open('xb') as handle: handle.write(encoded(verification))
            names = [*copied, 'README.md','execution.log','inventory-before.json','copy-verification.json','force-add-files.txt','manifest.json']
            force = [(directory/name).relative_to(ROOT).as_posix() for name in names]+[TEST]
            if report == CANONICAL: force.append(report.relative_to(ROOT).as_posix())
            with (directory/'force-add-files.txt').open('x', encoding='utf-8', newline='\n') as handle:
                handle.write('\n'.join(force)+'\n')
    finally:
        for key in list(os.environ):
            if key.startswith('GIT_'): os.environ.pop(key, None)
        os.environ.update(git_before)
    verified = verify_evidence_bundle(directory); recheck(inventory)
    print(json.dumps(dict(verified=verified, manifest_sha256=sha((directory/'manifest.json').read_bytes()),
        force_add_list=(directory/'force-add-files.txt').relative_to(ROOT).as_posix())))


if __name__ == '__main__':
    main()
