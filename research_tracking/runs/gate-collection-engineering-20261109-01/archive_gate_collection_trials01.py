"""Archiver vận hành: ROOT review dry rồi đóng finaltrialset; không chạy collection.

Chỉ copy/hash nguồn và raw evidence đã terminal. Không import worker hoặc pytest,
không tạo Gate PASS, không sửa current pointer. Final trialset01–05 do ROOT chốt.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PACKET = PREP/'gate_collection01_packet.ROOT.json'
PACKET_SHA = 'bacc6e49d14d244396b7be03cf68c62daefa8c14adf056b1f0c5cde8b8f1ed90'
HELPER_SHA = '0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'
SOURCE_MAP = {
    '01': ('1010dadc9310506cc6687b165082d3938a30069da7b4429ebbb3db75c2334c84',
           'a9e695e7521e1c4c2764034bb924a96cededfa548217864998b779583f7fb820'),
    '02': ('ee7bb38a8d979eb37fdf7e74b23f45f367d85b23b092857838653675eca89179',
           'f5953fb59a2b4cf75619ac374d36646fe2cd78a327cbd9941a1d06e373323fc9'),
    '03': ('cfc9fbf52acc340acc375b7f20eaddbc2f3284218939d06ad34447a81e737037',
           '44d22781f95119212d7b4463a2c253425780f5c30fba69f6a3afcb0fbb8d4cdc'),
    '04': ('274b368e353647e73b34c9b0158e0501d530de137f21f7082b5171cb96ac78a7',
           '0f96446aa27fcbb201df94af42dc129a6e65270843cd594cc2c9f5baabe181c7'),
    '05': ('9a4588d04e9f02164d7e4925ef2347e8fba08e8cd69a0d5a531d8f227a738f5c',
           'c0c83cbca3fc89aeab6fcdfcca15ebf5ebc6663ad5c3b0dce9b33e8ad96e0306'),
}
GROUPS = ('stdlib', 'no-torch', 'remaining')
CHILD_NAMES = {'collection.log','import-time-inventory.json','result.json','shim-ancestry-observation.json',
               'resource-failure.json','call-guard-failure.json','postwrite-rejection.json',
               'scripts-namespace-before.json','scripts-namespace-after.json'}
OWNER_NAMES = {'GO.json','launch.json','ready.json','receipt.json','stdout.log','stderr.log','postwrite_rejection.json'}
GENERATED = {'README.md','execution.log','copy_inventory_before.json','copy_inventory.json',
             'trial_summary.json','historical_source_bindings.json','closure_review.json','raw_log_paths.txt'}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def physical(path):
    p = Path(path).absolute()
    need(p.is_relative_to(ROOT), 'workspace-only physical path')
    cursor = ROOT
    for part in p.relative_to(ROOT).parts:
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor,'is_junction',lambda:False)(), 'path alias')
    need(p.resolve() == p, 'path traversal/canonical mismatch')
    return p


def sha(path):
    p = physical(path)
    need(p.is_file() and p.stat().st_size <= 2*1024**2, 'bounded regular text/source file')
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(path):
    sha(path)
    return json.loads(Path(path).read_bytes())


def finite(value, cap):
    return type(value) in (int,float) and math.isfinite(value) and 0 <= value <= cap


def collect(args):
    need(tuple(args.trials) == ('01','02','03','04','05'), 'ROOT final explicit trialset01–05; no omission or new retry')
    need(sha(PACKET) == PACKET_SHA, 'original frozen packet unchanged')
    packet = read(PACKET)
    need(packet['kind'] == 'ROOT_FROZEN_GATE2_COLLECTION_INPUT' and len(packet['gate_build_hashes']) == 154
         and len(packet['test_module_sha256']) == 69, 'original154 sources/69 modules')
    pairs = [(PACKET, 'packet.ROOT.json'),
             (PREP/'gate_collection01_packet.template.json','packet.template.json'),
             (PREP/'GATE_COLLECTION01_REVIEW.md','GATE_COLLECTION01_REVIEW.md'),
             (PREP/'GATE_COLLECTION03_FIX.md','GATE_COLLECTION03_FIX.md'),
             (PREP/'test_gate_collection_shim03.py','test_gate_collection_shim03.py'),
             (PREP/'verify_gate_frozen_git01.py','verify_gate_frozen_git01.py'),
             (PREP/'gate_frozen154_raw_git01.json','gate_frozen154_raw_git01.json'),
             (Path(__file__).resolve(),'archive_gate_collection_trials01.py'),
             (args.report,'report_snapshot.md')]
    need(sha(args.report) == args.expected_report_sha256, 'ROOT reviewed report snapshot')
    # ROOT already verified raw Git blobs and current bytes; consume this proof, never rerun it.
    need(sha(PREP/'verify_gate_frozen_git01.py') == '0bf0d01fd100579efbcf649c69db45478077c8745444d440eed52e16d61bd589'
         and sha(PREP/'gate_frozen154_raw_git01.json') == 'b940fadffb25a4f93bc6733c23ae9005aeb68f1caa16c0410a0253367feba833',
         'ROOT frozen154 raw Git proof pins')
    proof = read(PREP/'gate_frozen154_raw_git01.json')
    need(proof['status'] == 'FROZEN154_RAW_GIT_AND_WORKTREE_VERIFIED' and proof['commit'] == '2c337d4'
         and proof['packet_sha256'] == PACKET_SHA and proof['source_count'] == 154
         and proof['source_sha256'] == packet['gate_build_hashes'] and proof['source_files_copied'] == 0,
         'exact154 committed source bindings, no copied production sources')
    need(packet['gate_build_hashes'].get('scripts/research/windows_owned_worker.py') == HELPER_SHA,
         'unchanged owned helper')
    need(set(packet['upstream_file_sha256']) == {'akt.py','README.md','LICENSE','load_data.py'},'exact4 upstream hash pointers')
    need(sha(ROOT/'src/knowledge_tracing/evidence.py') == packet['gate_build_hashes']['src/knowledge_tracing/evidence.py'],
         'closure helper source matches frozen committed helper')
    summaries = []
    for trial in args.trials:
        worker = PREP/f'gate_collection_worker{trial}.py'
        outer = PREP/f'run_gate_collection{trial}.py'
        review_path = PREP/f'gate_collection{trial}_root_review.json'
        review = read(review_path)
        worker_sha, outer_sha = SOURCE_MAP[trial]
        need(review['packet_sha256'] == PACKET_SHA,'ROOT reviewed packet')
        if trial == '01':
            need(review['controller_pins'][worker.name] == worker_sha and review['controller_pins'][outer.name] == outer_sha,
                 'ROOT initial controller review')
        else:
            need(review['worker_sha256'] == worker_sha and review['outer_sha256'] == outer_sha,'ROOT revision controller review')
        need(sha(worker) == worker_sha and sha(outer) == outer_sha, 'reviewed worker/controller bytes')
        pairs.extend(((worker,worker.name),(outer,outer.name),(review_path,review_path.name)))
        if trial == '04':
            pairs.append((PREP/'GATE_COLLECTION04_REPORTING_HYPOTHESIS.md','GATE_COLLECTION04_REPORTING_HYPOTHESIS.md'))
        if trial == '05':
            pairs.append((PREP/'GATE_COLLECTION05_ROOT_PATH.md','GATE_COLLECTION05_ROOT_PATH.md'))
        child = PREP/f'gate-collection{trial}'; operation = PREP/f'gate-collection{trial}-outer'
        final = read(operation/'final.json'); before = read(operation/'before.json')
        need(final['status'] == 'REJECTED_COLLECTION'
             and final['gate_pass'] is False and final['test_bodies_executed'] is False
             and final['automatic_retry'] is False and final['environment_restored'] is True,
             'terminal collection-only scope, never GatePASS')
        need(final['packet_sha256'] == PACKET_SHA and final['worker_sha256'] == worker_sha
             and final['helper_sha256'] == HELPER_SHA and final['source_before'] == final['source_after']
             and final['source_before']['gate_build_hashes'] == packet['gate_build_hashes'], 'terminal source/packet identity')
        need(before['packet_sha256'] == PACKET_SHA and before['source'] == final['source_before'], 'original before receipt binding')
        need(final['cap_seconds'] == 60 and finite(final['elapsed_seconds'],60), 'native cumulative60s cap not reset')
        need(final['module_count'] == 69 and len(final['nodeids']) == final['collected_count']
             and len(set(final['nodeids'])) == len(final['nodeids']), 'inventory counts, not testPASS')
        need({p.name for p in operation.iterdir()} <= {'before.json','final.json','postwrite-rejection.json',
             *(g+'-owned' for g in GROUPS)}, 'outer known raw population')
        for name in ('before.json','final.json','postwrite-rejection.json'):
            if (operation/name).exists():
                pairs.append((operation/name,f'trial{trial}__outer__'+name))
        groups = []
        for group in GROUPS:
            directory = child/group; owned = operation/(group+'-owned')
            if directory.exists():
                need(directory.is_dir() and {p.name for p in directory.iterdir()} <= CHILD_NAMES, 'child allowlisted files only')
                for p in sorted(directory.iterdir()):
                    pairs.append((p,f'trial{trial}__{group}__'+p.name))
            if not owned.exists():
                need(not directory.exists() or not list(directory.iterdir()), 'child evidence without owned attempt')
                groups.append(dict(group=group,status='NOT_DISPATCHED_OR_NO_OUTPUT'))
                continue
            need({p.name for p in owned.iterdir()} <= OWNER_NAMES, 'owned allowlisted files only')
            for p in sorted(owned.iterdir()):
                pairs.append((p,f'trial{trial}__{group}__owned__'+p.name))
            receipt = read(owned/'receipt.json')
            for name,pin in receipt['output_sha256'].items():
                need(name in ('stdout.log','stderr.log') and sha(owned/name) == pin, 'original owned log SHA')
            need(receipt['worker_sha256'] == worker_sha and receipt['helper_sha256'] == HELPER_SHA
                 and receipt['cleanup_accepted'] is True and receipt['job_active_after_cleanup'] == 0
                 and receipt['popen_handle_closed'] is True, 'owned source/cleanup proof')
            result_path = directory/'result.json'
            item = dict(group=group,worker_returncode=receipt['returncode'],owned_accepted=receipt['accepted'],
                cleanup_accepted=receipt['cleanup_accepted'],job_active_after_cleanup=0,
                result_present=result_path.exists(),collected_count=None,body_or_fit_count_not_inferred_from_missing_result=True)
            if result_path.exists():
                result = read(result_path)
                need(result['group'] == group and result['source_before'] == packet['gate_build_hashes'], 'group before-source identity')
                if result['status'] == 'COLLECTED_ONLY_PENDING_OUTER':
                    need(result['packet_sha256'] == PACKET_SHA and result['source_before'] == result['source_after'],
                         'completed group packet/post-source identity')
                else:
                    need(result['status'] == 'REJECTED_COLLECTION' and result['failures'], 'preserve genuine rejected child schema')
                    # Rejected04/05 lack packet/post-source fields; outer binds packet and posthash.
                    # Do not invent missing child telemetry to make the envelope look complete.
                item.update(status=result['status'],collected_count=result['collected_count'],
                    pytest_exit_code=result['pytest_exit_code'],zero_body_counters=result['zero_body_counters'],
                    child_source_after_present='source_after' in result,collection_reports=result['collection_reports'],
                    failures=result['failures'],profiler_restored=result['profiler_restored'],monitor_stopped=result['monitor_stopped'])
            groups.append(item)
        summaries.append(dict(trial=trial,status=final['status'],stored_prewrite_elapsed_seconds=final['elapsed_seconds'],
            cap_seconds=60,gate_pass=False,collected_count=final['collected_count'],groups=groups,
            root_observed_pure8='ROOT_TERMINAL_OBSERVATION_ONLY_NO_RAW_XML' if trial == '03' else None,
            errors=final['errors'],source_before_after_equal=True))
    for i,path in enumerate(args.optional_review_file,1):
        path = physical(path)
        need(path.parent == PREP and path.suffix in ('.json','.py','.md','.log','.txt'), 'opaque direct-prep optional review')
        pairs.append((path,f'optional_review_{i:02d}__'+path.name))
    rows = []
    for source,alias in pairs:
        need(alias not in GENERATED and not any(c in alias for c in '/\\:\t\r\n'), 'safe copy alias')
        source = physical(source)
        rows.append(dict(source=source.relative_to(ROOT).as_posix(),copy=alias,sha256=sha(source),bytes=source.stat().st_size))
    need(len({r['copy'] for r in rows}) == len(rows) and sum(r['bytes'] for r in rows) <= 8*1024**2, 'small unique archive population')
    return dict(status='DRY_OPERATIONAL_COLLECTION_ONLY_ROOT_REVIEW_REQUIRED',run_id=args.run_id,trials=args.trials,
        trial_summary=summaries,copy_pairs=rows,selected_bytes=sum(r['bytes'] for r in rows),
        packet_sha256=PACKET_SHA,historical_gate_source_sha256=packet['gate_build_hashes'],
        historical_source_commit='2c337d4',production_source_files_copied=0,
        lock_sha256=packet['lock_sha256'],upstream_file_sha256=packet['upstream_file_sha256'],
        full_gate_or_current_pointer_accepted=False,scientific_N_not_defined=True,expected_output_count=len(rows)+1+len(GENERATED))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('dry','close'));p.add_argument('--trials',nargs='+',required=True)
    p.add_argument('--run-id',default='gate-collection-engineering-20261109-01')
    p.add_argument('--report',type=Path,required=True);p.add_argument('--expected-report-sha256',required=True)
    p.add_argument('--inventory-output',type=Path,required=True)
    p.add_argument('--optional-review-file',type=Path,action='append',default=[])
    p.add_argument('--approved-dry-sha256');p.add_argument('--closure-reference')
    args = p.parse_args();args.report = physical(args.report);args.inventory_output = physical(args.inventory_output)
    need(args.inventory_output.parent == PREP and args.inventory_output.suffix == '.json','direct prep exclusive dry JSON')
    need(args.run_id.startswith('gate-collection-') and all(c.isalnum() or c in '-_' for c in args.run_id),'collection role run ID')
    dry = collect(args)
    if args.mode == 'dry':
        with args.inventory_output.open('x',encoding='utf-8') as f:
            json.dump(dry,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
        print(json.dumps(dict(status=dry['status'],dry_sha256=sha(args.inventory_output),expected_outputs=dry['expected_output_count'])))
        return
    need(args.closure_reference and sha(args.inventory_output) == args.approved_dry_sha256
         and read(args.inventory_output) == dry,'explicit ROOT reviewed exact final trialset/report/dry')
    destination = ROOT/'research_tracking/runs'/args.run_id
    need(not destination.exists(),'immutable no overwrite/retry')
    sys.path.insert(0,str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    pairs = dry['copy_pairs']+[dict(source=args.inventory_output.relative_to(ROOT).as_posix(),copy='approved_dry_inventory.json',
        sha256=sha(args.inventory_output),bytes=args.inventory_output.stat().st_size)]
    sources = sorted({ROOT/r['source'] for r in pairs})
    note = '''# Collection trên ba nhóm process, không phải full Gate

Giữ final trialset01–05 ROOT chọn explicit trong approved_dry_inventory.json; không thêm retry, không cộng số node đã collect thành testPASS hoặc mẫu nghiên cứu. Trial01/02 bị từ chối trước pytest;03 đã thu inventory19stdlib+271no-torch, remainingRC124, toàn trial vẫn rejected.04remaining984nodes có3importerrors, vẫn rejected.05normal imports của scripts.akt/research đúngROOT, nhưng guard parentnamespace-exclusive từ chối vì parent scripts còn path win32/scripts;0collected. Tất cả05trials rejected, không fullGate/currentPASS. Collection imports có chạy module tops nhưng không dispatch test bodies; không training/model/teacher/fullCV.03remaining không có result/counters cuối; không suy missingtelemetry thành0.

154source files và69module bindings thuộc packet lịch sử và commit2c337d4, được ROOT rawGit+worktree verify qua gate_frozen154_raw_git01.json; không copy lại production sources/notebooks/upstream. Không chứng nhận runtime/currentGate hôm nay. Có8pure shim checks được ROOT quan sát terminal, không tạo XML/log giả nếu không có raw. Giữ query handles/Jobcleanup trong nguyên receipts; tên file nhỏ không là scientificN. Không có lời giải cho nguyên nhân remaining timeout chỉ từ RC124.

copy_inventory_before.json/copy_inventory.json giữ SHA và size trước/sau của scratchcontrollers/reviews/rawoutcomes. Lock/upstream hashes giữ trong packet, không chép lại dependency hoặc notebooks. RawGit verifier được copy như source proof, archiver không chạy lại nó. README/execution.log thuộc archiver; collection.log/stdout/stderr/raw controllers được giữ riêng. Không Gitmutation/currentpointer edit; helper chuẩn chỉ đọc Git HEAD. Báo cáo freeze trướcclosure; actualmanifest xác nhận operationalarchive integrity, không đổi cả5trialrejected thành collection/fullGate acceptance.
'''
    def dump(directory,name,value):
        with (directory/name).open('x',encoding='utf-8') as f:
            json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    with record_evidence_run(ROOT,args.run_id,metadata=dict(kind='GATE_COLLECTION_OPERATIONAL_EVIDENCE_NOT_FULL_GATE',
            trials=args.trials,closure_reference=args.closure_reference,approved_dry_sha256=args.approved_dry_sha256,
            gate_pass=False,scientific_N_not_defined=True),sources=sources,note=note) as directory:
        dump(directory,'copy_inventory_before.json',pairs)
        for row in pairs:
            need(sha(ROOT/row['source']) == row['sha256'],'source changed immediately before copy')
            with (ROOT/row['source']).open('rb') as src,(directory/row['copy']).open('xb') as dst:
                shutil.copyfileobj(src,dst)
        after=[]
        for row in pairs:
            need(sha(ROOT/row['source']) == sha(directory/row['copy']) == row['sha256']
                 and (directory/row['copy']).stat().st_size == row['bytes'],'source/copy postSHA drift')
            after.append({**row,'sha256_before_copy':row['sha256'],'sha256_after_copy':row['sha256'],'exact_match':True})
        need(collect(args) == dry,'postcopy full raw/source inventory changed')
        dump(directory,'copy_inventory.json',after);dump(directory,'trial_summary.json',dry['trial_summary'])
        dump(directory,'historical_source_bindings.json',dict(packet_sha256=PACKET_SHA,
            commit='2c337d4',gate_source_sha256=dry['historical_gate_source_sha256'],source_files_copied=0,
            lock_sha256=dry['lock_sha256'],upstream_file_sha256=dry['upstream_file_sha256'],
            raw_git_proof_sha256='b940fadffb25a4f93bc6733c23ae9005aeb68f1caa16c0410a0253367feba833',
            scope='Historical packet+ROOT raw Git proof, not currentGate acceptance'))
        dump(directory,'closure_review.json',dict(reference=args.closure_reference,approved_dry_sha256=args.approved_dry_sha256,
            trials=args.trials,full_gate_pass=False,scientific_N_not_defined=True))
        logs=sorted({'execution.log'}|{r['copy'] for r in pairs if r['copy'].endswith('.log')})
        with (directory/'raw_log_paths.txt').open('x',encoding='utf-8') as f:
            f.write(''.join((directory/n).relative_to(ROOT).as_posix()+'\n' for n in logs))
        need({p.name for p in directory.iterdir()} == {r['copy'] for r in pairs}|GENERATED|{'manifest.json'},'exact output population')
    verified=verify_evidence_bundle(directory)
    need(verified['artifacts'] == dry['expected_output_count'],'closed output count')
    print(json.dumps(dict(**verified,manifest_sha256=sha(directory/'manifest.json'))))


if __name__ == '__main__':
    main()
