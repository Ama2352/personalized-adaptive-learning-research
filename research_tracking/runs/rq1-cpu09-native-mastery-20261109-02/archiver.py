"""Root dry/closure failure02; không replay, import model hoặc decode cache."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
RUN_ID='rq1-cpu09-native-mastery-20261109-02'
REPORT=PREP/'CPU09_TARGETED_FULL_REPORT_DRAFT02.md'
DRY=PREP/'cpu09_targeted_full_archive_dry02.json'
CONTRACT=PREP/'rq1_cpu09_targeted_full_contract02.json'
OUTER=PREP/'rq1-cpu09-targeted-full-native02-outer'
OWNED=PREP/'rq1-cpu09-targeted-full-native02-owned'
INNER=ROOT/'experiments/gam_kt/results'/RUN_ID
FINAL_SHA='9327a58214dab1574516a539d422d9337db85e4bfd06ada8d4f72f2f63360ebe'
D41='docs/thesis_recovery/09_DECISION_REGISTER.md'
D41_SHA='366e0faeef6c312a483f447f360c83207a7bea7443634dd0b0c8a5d0903b8bb9'
PINS={
    'worker_rq1_cpu09_targeted_full02.py':'9db2ffb509a58267d875360262d6deaeaf704f2a8348e116e978e70cfa03fee6',
    'run_rq1_cpu09_targeted_full02.py':'19a0a5b8d6d320f9a1371ba5efaba13de45475fc6f98f2c19b89d2d0c3ed4c7c',
    'rq1_cpu09_targeted_full_contract02.json':'d45e81f581f7305bb06829f2c36796f58fa0133a7a33e444c2901d4f7c4128aa',
    'CPU09_TARGETED_FULL_ROOT_REVIEW02.md':'2e68b845f6a2c3373feb28acfc82883ebee087e166d99f9bf934969df90141c1',
    'verify_cpu09_full02_terminal01.py':'b42952a0899e929b56853550547d1e0bf39d342e8275439b2c40f4d264ad551a',
    'cpu09_full02_terminal_postcheck01.json':'3a603fb78477388b779cd9f4af1b5b57d8fd1aeefd25f06b580577adef05b8f2',
}
GENERATED=('README.md','execution.log','copy_inventory.json','reference_inputs.json',
           'scope.json','timing_scope.json','closure_review.json','reviewed_dry.json','raw_log_paths.txt')


def need(ok,message):
    if not ok:raise ValueError(message)


def payload(path,cap=4*1024**2):
    need(path.is_absolute() and path.is_relative_to(ROOT) and path.resolve()==path,'physical ROOT-bound path')
    cursor=ROOT
    need(ROOT.is_dir() and not ROOT.is_symlink() and not getattr(ROOT,'is_junction',lambda:False)(),'physical ROOT')
    for part in path.relative_to(ROOT).parts:
        cursor/=part
        need(not cursor.is_symlink() and not getattr(cursor,'is_junction',lambda:False)(),'no aliases')
    need(path.is_file() and path.stat().st_size<=cap,'bounded regular evidence input')
    with path.open('rb') as stream:raw=stream.read(cap+1)
    need(len(raw)<=cap and len(raw)==path.stat().st_size,'stable bounded bytes')
    return raw


def sha(path,cap=4*1024**2):return hashlib.sha256(payload(path,cap)).hexdigest()


def read(path,pin=None):
    raw=payload(path,1024**2)
    need(pin is None or hashlib.sha256(raw).hexdigest()==pin,'same-payload hash before JSON parse')
    return json.loads(raw)


def write(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')


def gather(args):
    need(re.fullmatch('[a-f0-9]{64}',args.report_sha256) and args.outer_sha256==FINAL_SHA,'Root actual/report SHA inputs')
    need(sha(REPORT)==args.report_sha256,'exact reviewed report')
    for name,pin in PINS.items():need(sha(PREP/name)==pin,'frozen executed source/review/postcheck')
    terminal=read(OUTER/'final.json',args.outer_sha256)
    contract=read(CONTRACT,PINS[CONTRACT.name])
    receipt=terminal['receipt'];resources=terminal['resources']
    need(terminal['status']=='REJECTED_KEEP_NEW_FULL_OPERATION_NO_RETRY'
         and terminal['errors']==[dict(type='ValueError',message='actual clean owned terminal')]
         and terminal['whole_cap_seconds']==300 and terminal['automatic_retry'] is False
         and terminal['old_five_attempt_lane_reopened'] is False,'actual rejected02, no retry or relabel')
    need(terminal['validation'] is None and terminal['outputs']=={} and terminal['source_input_after']=={},
         'native terminal/postchecks absent; external proof stays separate')
    need(receipt['returncode']==receipt['worker_returncode_before_cleanup']==3221225786
         and receipt['accepted'] is False and receipt['GO_released'] is True
         and receipt['actual_worker_in_job_before_GO'] is True
         and receipt['cleanup_accepted'] is True and receipt['job_active_before_cleanup']==receipt['job_active_after_cleanup']==0
         and receipt['cleanup_errors']==receipt['errors']==[] and receipt['popen_handle_closed'] is True,
         'shim failure before successful owned cleanup')
    need(receipt['popen']['pid']==45776 and receipt['actual_worker']['pid']==14104
         and receipt['popen']['pid']!=receipt['actual_worker']['pid'],'actual shim/worker distinction')
    need(terminal['environment_restored'] is True and resources['monitor_stopped'] is True
         and resources['terminated_owned_job'] is False and resources['errors']==[]
         and resources['observed_family_peak_rss_bytes']==126898176
         and resources['observed_minimum_available_ram_bytes']==2556096512,'observed resources, not a proved exit origin')
    proof=read(PREP/'cpu09_full02_terminal_postcheck01.json',PINS['cpu09_full02_terminal_postcheck01.json'])
    refs=contract['bindings']|contract['historical_reference_inputs']
    need(len(refs)==57 and proof['source_files_checked']==57 and proof['source_after']==refs
         and proof['status']=='VERIFIED57_SOURCE_INPUTS_AND_UNEXPECTED_LAUNCHER_EXIT_NOT_REPLAY_ACCEPTANCE'
         and proof['outer_terminal_sha256']==args.outer_sha256 and proof['cause']=='UNKNOWN'
         and proof['native_worker_direct_exit_code_recorded'] is False
         and proof['actual_constructor_and_update_counts']=='UNKNOWN_WITHOUT_TERMINAL_NATIVE_RECEIPT'
         and proof['full_parity_completed'] is proof['truth_evaluation_completed'] is False,'external57 integrity only')
    expected_inner={'native_metadata.json','pure_checks.json'}
    expected_outer={'admission.json','final.json','memory.jsonl'}
    expected_owned={'GO.json','launch.json','ready.json','receipt.json','stderr.log','stdout.log'}
    need({p.name for p in INNER.iterdir()}==set(proof['actual_worker_outputs'])==expected_inner
         and {p.name for p in OUTER.iterdir()}==expected_outer
         and {p.name for p in OWNED.iterdir()}==expected_owned,'exact11 actual raw files')
    need(read(OWNED/'receipt.json')==receipt,'owned/embedded receipt exact')
    for name,item in proof['actual_worker_outputs'].items():
        need(sha(INNER/name)==item['sha256'] and (INNER/name).stat().st_size==item['bytes'],'postcheck inner bytes')
    pure=read(INNER/'pure_checks.json');metadata=read(INNER/'native_metadata.json')
    need(pure['manufactured_checks']==5 and pure['native_calls']==0,'five manufactured checks only')
    need(metadata['phase_closed'] is True and metadata['helper_calls']==1
         and metadata['blocked_bootstrap_attempts']==metadata['outside_phase_popen_attempts']==metadata['outside_phase_socket_attempts']==0,
         'actual metadata completed, no inferred signal source')
    need((OWNED/'stdout.log').stat().st_size==(OWNED/'stderr.log').stat().st_size==0,'empty captured streams preserved')
    copies={};references={}
    def add(alias,path):
        need(alias not in copies and Path(alias).name==alias,'unique flat alias')
        payload(path,1024**2);copies[alias]=path
    for name in PINS:add(name,PREP/name)
    add('report.md',REPORT);add('archiver.py',Path(__file__).resolve())
    for prefix,directory in (('worker',INNER),('outer',OUTER),('owned',OWNED)):
        for path in sorted(directory.iterdir()):add(prefix+'__'+path.name,path)
    for name,item in refs.items():
        path=ROOT/name
        need(sha(path)==item['sha256'] and path.stat().st_size==item['bytes'],'archive-time57 source/input bindings')
        references[name]=dict(**item,copied=False,role='BOUND_SOURCE_INPUT_REFERENCE_OPAQUE_HASH_ONLY')
    need(sha(ROOT/D41)==D41_SHA and '## D41 —' in payload(ROOT/D41).decode('utf-8'),'reviewed D41 reference version')
    references[D41]=dict(sha256=D41_SHA,bytes=(ROOT/D41).stat().st_size,copied=False,role='D41_ALLOCATION_REFERENCE')
    inventory=[dict(copy=alias,source=path.relative_to(ROOT).as_posix(),sha256=sha(path,1024**2),bytes=path.stat().st_size)
               for alias,path in sorted(copies.items())]
    need(len(inventory)==19 and sum(row['bytes'] for row in inventory)<=1024**2,'exact compact19copies')
    return inventory,references,terminal


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--report-sha256',required=True);parser.add_argument('--outer-sha256',required=True)
    action=parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--prepare-dry',action='store_true');action.add_argument('--check-dry',action='store_true')
    action.add_argument('--close',action='store_true')
    parser.add_argument('--expected-dry-sha256');parser.add_argument('--review-reference')
    args=parser.parse_args()
    need(Path(sys.prefix).resolve()==ROOT/'.venv','repository .venv only')
    destination=ROOT/'research_tracking/runs'/RUN_ID
    need(not destination.exists() and destination.resolve()==destination,'exclusive new bundle')
    inventory,refs,terminal=gather(args)
    dry=dict(run_id=RUN_ID,report_sha256=args.report_sha256,outer_sha256=args.outer_sha256,
        native_accepted=False,actual_terminal_status=terminal['status'],copies=inventory,reference_inputs=refs,
        generated_outputs=list(GENERATED),expected_output_count=28)
    if args.prepare_dry:
        write(DRY,dry);print(json.dumps(dict(status='DRY_PREPARED_NOT_CLOSED',dry_sha256=sha(DRY),outputs=28)));return
    need(read(DRY)==dry,'current bytes equal reviewed dry')
    if args.check_dry:
        print(json.dumps(dict(status='DRY_MATCH_NOT_CLOSED',outputs=28)));return
    need(args.expected_dry_sha256==sha(DRY) and args.review_reference,'Root exact-dry closure review')
    sys.path.insert(0,str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    note=('# Full CPU09 lượt02 — hồ sơ launcher dừng đột ngột\n\n'
        'Native verdict REJECTED giữ nguyên. Shim C000013A; actual worker direct exit code và nguyên nhân UNKNOWN. '
        'Giữ11raw files, source/review/postcheck57; không copy hoặc decode cache. '
        'Metadata Windows đã đóng sạch và5helper checks không thay terminal replay. '
        'Không reservation/parity/truth mới hoặc native call-count receipt. '
        'Archive completed chỉ là bảo toàn failure, không cấp authority hoặc RQ claim. '
        'Đọc [report.md](report.md) và scope.json.\n')
    sources=list(dict.fromkeys([ROOT/r['source'] for r in inventory]+[ROOT/n for n in refs]+[DRY]))
    with record_evidence_run(ROOT,RUN_ID,metadata=dict(kind='CPU09_UNEXPECTED_LAUNCHER_EXIT_FAILURE02',
        actual_terminal_verdict=terminal['status'],native_accepted=False,cause='UNKNOWN',new_independent_N=0),
        sources=sources,note=note) as out:
        copied=[]
        for row in inventory:
            source=ROOT/row['source'];need(sha(source,1024**2)==row['sha256'],'source beforecopy')
            with (out/row['copy']).open('xb') as stream:stream.write(payload(source,1024**2))
            need(sha(source,1024**2)==sha(out/row['copy'],1024**2)==row['sha256'],'source/copy/source-after SHA equality')
            copied.append(dict(**row,source_sha256_after_copy=sha(source,1024**2),copy_sha256=sha(out/row['copy'],1024**2)))
        write(out/'copy_inventory.json',copied);write(out/'reference_inputs.json',refs)
        write(out/'scope.json',dict(native_accepted=False,shim_pid=45776,shim_returncode=3221225786,
            status_name='STATUS_CONTROL_C_EXIT',classification_source='https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/596a1078-e883-4972-9bbc-49e60bebca55',
            actual_worker_pid=14104,actual_worker_exit_code=None,cause='UNKNOWN',
            no_resource_failure_observed=True,resource_observation='SAMPLED_NOT_CONTINUOUS_PROOF',
            actual_constructor_and_update_counts='UNKNOWN_WITHOUT_TERMINAL_NATIVE_RECEIPT',
            reservation_present=False,full_parity_completed=False,truth_evaluation_completed=False,
            external_postcheck_source_count=57,external_postcheck_is_native_admission=False,
            no_rerun_at_closure=True,archive_completion_does_not_promote_rejected_native=True))
        write(out/'timing_scope.json',dict(outer_elapsed_before_receipt_seconds=terminal['elapsed_before_receipt_seconds'],
            owned_helper_elapsed_seconds=terminal['receipt']['elapsed_seconds'],whole_cap_seconds=300,
            owned_cap_seconds=285,worker_cap_seconds=270,cleanup_reserve_seconds=5,
            resource_receipt=terminal['resources'],nested_times_not_summed=True))
        write(out/'closure_review.json',dict(reference=args.review_reference,dry_sha256=args.expected_dry_sha256,
            report_sha256=args.report_sha256,outer_sha256=args.outer_sha256))
        with (out/'reviewed_dry.json').open('xb') as stream:stream.write(payload(DRY))
        need(sha(out/'reviewed_dry.json')==args.expected_dry_sha256,'exact reviewed dry copy')
        (out/'raw_log_paths.txt').write_text('\n'.join(row['source'] for row in inventory
            if row['copy'].startswith(('worker__','outer__','owned__')))+'\n',encoding='utf-8')
        need({p.name for p in out.iterdir() if p.name!='manifest.json'}==set(GENERATED)|{r['copy'] for r in inventory},'exact28outputs')
        need(all(sha(ROOT/r['source'],1024**2)==r['sha256'] for r in inventory),'all copied sources stable')
        need(all(sha(ROOT/n)==r['sha256'] for n,r in refs.items()),'all57inputs and D41 unchanged')
    verified=verify_evidence_bundle(destination);need(verified['artifacts']==28,'verified28outputs')
    print(json.dumps(dict(status='CLOSED_FAILURE_EVIDENCE_NOT_REPLAY_ACCEPTANCE',verification=verified,
        manifest_sha256=sha(destination/'manifest.json'),outputs=28,files_including_manifest=29)))


if __name__=='__main__':main()
