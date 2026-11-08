"""Chuẩn bị dry/đóng evidence cache; ROOT review và phê duyệt riêng trước chạy.

Không chạy analyzer/test/policy/model; không copy gzip gốc hoặc sửa report.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = ROOT/'artifacts/akt/local-tests/rq1-observability-preparation-20261108-01'
OLD = ROOT/'research_tracking/runs/rq1-closed-loop-reconstruction-20261108-02'
RUN_ID = 'rq1-ready-set-exposure-20261108-01'
REPORT = ROOT/'research_tracking/reports/rq1_ready_set_exposure_results_20261108.md'
INNER = PREP/'ready-exposure-attempt01'
OWNED = PREP/'ready-exposure-owned-attempt01'
PINS = {
    'manifest.json':'c8bd8f387e5101fca641098257dd5a99d67d2f838cefc3b53b7d9d55248bcb16',
    'accepted_fast__observed_metadata.jsonl.gz':'1ab8dcd5c5521c1f4055887f8d53032592a74e71949e9caaed83898c6efeb5ce',
    'simulator_input__edges.csv':'ecd910d8df52f8790997391de657ea0f9e8357446212c168b73e500d0facc2fb',
    'prep__closed_loop_native_source_snapshot.json':'a080cd079742d83dfef6a78f807d17c62f58dcdff9f8b36e38cc13f4ca428ec8',
}
SOURCE_SHA = '2eb46e0a2e35fa95c796c11150fa1fe66dc98e1d107b6e41fe5435a8c667c11b'
PLAN_SHA = '53414badb767d26608c3387386998b66fe2e12eb3efa901dd2fe660f198cb774'
HELPER_SHA = '414e3d834c46d081c7d9c05beff17a3e2d9c479a0e121394aabe321929235e49'
GENERATED = ('README.md','execution.log','source_references.json','copy_inventory_before.json',
             'copy_inventory.json','frozen_acceptance.json','closure_review.json','raw_log_paths.txt')


def need(ok, message):
    if not ok:raise ValueError(message)


def sha(path):
    need(path.is_file() and not path.is_symlink() and not getattr(path,'is_junction',lambda:False)(), 'regular source required')
    need(path.stat().st_size <= 4*1024**2, 'small evidence/source only')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def digest_arg(value):
    need(type(value) is str and len(value)==64 and all(c in '0123456789abcdef' for c in value), 'explicit SHA64 lowercase')
    return value


def physical(path):
    absolute = path.absolute()
    need(absolute.is_relative_to(ROOT), 'workspace-only path')
    current=ROOT
    for part in absolute.relative_to(ROOT).parts:
        current/=part
        need(not current.is_symlink() and not getattr(current,'is_junction',lambda:False)(), 'source/path alias rejected')
    need(absolute.resolve()==absolute, 'physical path required')
    return absolute


def verify_acceptance(expected_report_sha):
    digest_arg(expected_report_sha)
    need(sha(REPORT)==expected_report_sha, 'report changed: ROOT must review new report/dry pins')
    need(sha(PREP/'analyze_ready_set_exposure.py')==SOURCE_SHA, 'analyzer changed')
    need(sha(ROOT/'research_tracking/reports/rq1_ready_set_exposure_plan_20261108.md')==PLAN_SHA, 'plan changed')
    need(sha(ROOT/'src/knowledge_tracing/evidence.py')==HELPER_SHA, 'evidence helper changed')
    for name,pin in PINS.items():need(sha(physical(OLD/name))==pin, 'immutable reference changed: '+name)
    old_manifest=read(OLD/'manifest.json')
    need(old_manifest['status']=='completed' and len(old_manifest['outputs_sha256'])==125, 'accepted original125 outputs required')
    for name,pin in PINS.items():
        if name!='manifest.json':need(old_manifest['outputs_sha256'].get(name)==pin,'reference selected-output binding')
    freeze=read(PREP/'ready_set_exposure_freeze01.json')
    need(freeze['source_sha256']==SOURCE_SHA and freeze['plan_sha256']==PLAN_SHA
         and freeze['owned_max_seconds']==10 and freeze['cleanup_reserve_seconds']==2,'reviewed freeze binding/caps')
    need(sha(ROOT/'scripts/research/windows_owned_worker.py')==freeze['helper_sha256']
         =='0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1','executed owned-helper source drift')
    validation=read(INNER/'validation.json'); result=read(INNER/'result.json')
    owner=read(OWNED/'receipt.json'); final=read(OWNED/'final.json')
    need(not (INNER/'failure.json').exists() and not (OWNED/'postwrite_rejection.json').exists(), 'failure/postwrite rejection exists')
    need({p.name for p in INNER.iterdir()}=={'summary.json','event_membership_flags.csv','validation.json','result.json'},'unexpected inner file/failure')
    need(validation['status']=='ALL3240_SOURCE_READY_SETS_ORDER_EXACT'
         and validation['rows']==validation['ready_order_exact']==validation['served_in_B_subset_C_exact']==3240
         and validation['trajectories']==27 and validation['steps_each']==120
         and validation['strict_class_partition_concept_events']==90720 and validation['groups']==40
         and validation['concept_cells_including_zeros']==4480,'exact validation population required')
    need(validation['inputs_sha256']==PINS and validation['source_sha256']==SOURCE_SHA
         and validation['plan_sha256']==PLAN_SHA and validation['source_inputs_before_after_equal'] is True,'validation source/input binding')
    need(result['status']=='INNER_COMPLETE_PENDING_OWNED_OUTER_ACCEPTANCE'
         and type(result['worker_seconds']) in (int,float) and 0<=result['worker_seconds']<=7,'inner clock/status')
    need(result['worker_cap_seconds']==7 and result['no_retry'] is True,'inner fixed allocation')
    for name,pin in result['outputs_sha256'].items():
        need(name in ('summary.json','event_membership_flags.csv','validation.json') and sha(INNER/name)==pin,'inner output changed')
    need(set(result['outputs_sha256'])=={'summary.json','event_membership_flags.csv','validation.json'},'exact inner output vector')
    need(owner['accepted'] is True and owner['cleanup_accepted'] is True and owner['job_active_after_cleanup']==0
         and owner['popen_handle_closed'] is True and owner['returncode']==0 and not owner['errors']
         and owner['actual_worker_in_job_before_GO'] is True,'actual owned acceptance/cleanup required')
    need(owner['worker_sha256']==SOURCE_SHA and owner['helper_sha256']==freeze['helper_sha256']
         and type(owner['elapsed_seconds']) in (int,float) and 0<=owner['elapsed_seconds']<=10
         and owner['max_seconds']==10 and owner['cleanup_reserve_seconds']==2,'owned source/time binding')
    for name,pin in owner['output_sha256'].items():
        need(name in ('stdout.log','stderr.log') and sha(OWNED/name)==pin,'owned log drift')
    need(final['status']=='ACCEPTED_CACHED_SOURCE_LOCAL_DESCRIPTION'
         and type(final['elapsed_seconds']) in (int,float) and 0<=final['elapsed_seconds']<=10
         and final['cap_seconds']==10 and final['owned_cleanup'] is True and final['rows']==3240,'caller acceptance required')
    need(all(type(final[k]) is int and final[k]==0 for k in ('new_independent_N','actual_model_calls','optimizer_steps','actual_simulator_calls'))
         and all(type(validation[k]) is int and validation[k]==0 for k in ('actual_model_calls','optimizer_steps','network_calls','child_process_calls')),'scope counters must remain0')
    return dict(kind='POST_HOC_CACHED_SOURCE_LOCAL_READY_EXPOSURE_NOT_POLICY_INTERVENTION',
        rows=3240,trajectories=27,ready_order_exact=3240,concept_events=90720,groups=40,concept_cells=4480,
        source_sha256=SOURCE_SHA,plan_sha256=PLAN_SHA,report_sha256=expected_report_sha,
        original_bundle_relative=OLD.relative_to(ROOT).as_posix(),original_manifest_sha256=PINS['manifest.json'],
        caller_elapsed_seconds=final['elapsed_seconds'],caller_cap_seconds=10,owned_cleanup=True,job_active_after_cleanup=0,
        new_independent_N=0,actual_model_calls=0,optimizer_steps=0,actual_simulator_calls=0,
        not_calibration_or_learning_effect=True,original_a585_recovered=False,
        optional_independent_review_verdict='NOT_INFERRED_FROM_OPTIONAL_FILE_PRESENCE')


def inventory(args):
    acceptance=verify_acceptance(args.expected_report_sha256)
    pairs=[(ROOT/'research_tracking/reports/rq1_ready_set_exposure_plan_20261108.md','plan.md'),
        (REPORT,'report_snapshot.md'),(PREP/'analyze_ready_set_exposure.py','analyze_ready_set_exposure.py'),
        (PREP/'ready_set_exposure_freeze01.json','freeze.json'),(PREP/'run_ready_exposure01.py','root_outer.py'),
        (ROOT/'src/knowledge_tracing/evidence.py','evidence_helper.py'),
        (ROOT/'scripts/research/windows_owned_worker.py','windows_owned_worker.py'),
        (Path(__file__).resolve(),'pack_ready_set_exposure.py')]
    pairs += [(INNER/name,name) for name in ('summary.json','event_membership_flags.csv','validation.json','result.json')]
    pairs += [(OWNED/name,'owned__'+name) for name in ('final.json','GO.json','launch.json','ready.json','receipt.json','stdout.log','stderr.log')]
    for i,path in enumerate(args.optional_review_file,1):
        path=physical(path)
        need(path.parent==PREP and path.suffix in ('.json','.py','.log','.txt'), 'optional review file: direct prep/small text only')
        pairs.append((path,f'optional_review_{i:02d}__'+path.name))
    rows=[]
    for source,alias in pairs:
        source=physical(source)
        need(not any(c in alias for c in '\\/:\t\r\n') and alias not in GENERATED and alias!='manifest.json','safe copy alias')
        rows.append(dict(source=source.relative_to(ROOT).as_posix(),copy=alias,sha256=sha(source),bytes=source.stat().st_size))
    need(len({v['copy'] for v in rows})==len(rows),'duplicate copy alias')
    need(sum(v['bytes'] for v in rows)<=4*1024**2,'small evidence total cap')
    sources={v['source']:v['sha256'] for v in rows}
    sources.update({(OLD/name).relative_to(ROOT).as_posix():pin for name,pin in PINS.items()})
    return dict(status='DRY_ONLY_NO_BUNDLE',run_id=RUN_ID,acceptance=acceptance,copy_pairs=rows,
        selected_bytes=sum(v['bytes'] for v in rows),sources_sha256=sources,
        expected_generated_outputs=list(GENERATED),expected_output_count=len(rows)+1+len(GENERATED),
        original_gzip_copy=False,optional_files_are_opaque_not_scientific_acceptance=True)


def close(args,dry):
    need(args.approval_reference and args.approval_reference.strip(),'explicit ROOT closure reference')
    need(sha(args.inventory_output)==digest_arg(args.approved_dry_sha256) and read(args.inventory_output)==dry,'approved dry changed')
    destination=physical(ROOT/'research_tracking/runs'/RUN_ID)
    need(not destination.exists(),'immutable destination already exists; no retry/overwrite')
    sys.path.insert(0,str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    original_before=verify_evidence_bundle(OLD)  # Hash outputs only, never execute/decompress historical artifacts.
    need(original_before['artifacts']==125,'original125 output integrity')
    pairs=[(ROOT/v['source'],v['copy']) for v in dry['copy_pairs']]+[(args.inventory_output,'approved_dry_inventory.json')]
    before=[dict(source=p.relative_to(ROOT).as_posix(),copy=alias,sha256_before_copy=sha(p),bytes=p.stat().st_size) for p,alias in pairs]
    sources=sorted({ROOT/p for p in dry['sources_sha256']}|{args.inventory_output})
    note='''# RQ1 — footprint của ngoại lệ exposure trong ready set\n\nHậu kiểm cache đã nghiệm thu riêng:3240rows/27trajectories, exactR order,0native/model/optimizer/newN. Không causal mediation, calibration, policy intervention hoặc lợi ích học tập.\n\n[Summary](summary.json), [event flags](event_membership_flags.csv), [validation](validation.json), [caller terminal](owned__final.json), [receipt](owned__receipt.json), [plan](plan.md). `report_snapshot.md` giữ nguyên bytes bản report tại closure; original relative links của snapshot thuộc vị trí canonical report, không bị viết lại để giả provenance. Xem báo cáo canonical ở ../../reports/rq1_ready_set_exposure_results_20261108.md.\n\nBốn inputs gốc tham chiếu trong source_references.json thuộc ../rq1-closed-loop-reconstruction-20261108-02/. Không nhân đôi gzip/source snapshot/edges; toàn125outputs của bundle nguồn được hash-verify trước/sau copy. Optional review files chỉ được copy opaque; sự có mặt không tự là peer-review PASS.\n\n500root events tách khỏi prerequisite denominator;2740nonroot=2041exposure+699strict. Các con số mô tả quỹ đạo đã phân kỳ, không paired effects. Originala585missing, current-source reconstruction.\n\nexecution.log là log đóng gói, không nguyên log analyzer. owned__stdout/stderr và source root_outer.py giữ riêng proof execution. Không chép .pt/Parquet/privateRPC/base64/ZIP/dataset; không rerun. Helper chuẩn ghi Git HEAD bằng read-only rev-parse khi closure, không add/commit/push.\n'''
    with record_evidence_run(ROOT,RUN_ID,metadata={**dry['acceptance'],'closure_approval_reference':args.approval_reference,
            'approved_dry_sha256':args.approved_dry_sha256},sources=sources,note=note) as directory:
        def write(name,value):
            with (directory/name).open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
        write('copy_inventory_before.json',before)
        for row,(source,alias) in zip(before,pairs):
            need(sha(source)==row['sha256_before_copy'],'source changed immediately before copy')
            with source.open('rb') as src,(directory/alias).open('xb') as dst:shutil.copyfileobj(src,dst)
        after=[]
        for row,(source,alias) in zip(before,pairs):
            copied=sha(directory/alias)
            need(copied==sha(source)==row['sha256_before_copy'] and (directory/alias).stat().st_size==row['bytes'],'copy byte/SHA drift')
            after.append({**row,'sha256_after_copy':copied,'exact_match':True})
        need(verify_evidence_bundle(OLD)==original_before,'original bundle postcopy integrity')
        need(verify_acceptance(args.expected_report_sha256)==dry['acceptance'],'acceptance/source changed during copy')
        write('copy_inventory.json',after)
        write('frozen_acceptance.json',dry['acceptance'])
        write('source_references.json',dict(original_bundle=OLD.relative_to(ROOT).as_posix(),manifest_sha256=PINS['manifest.json'],
            selected_inputs_sha256=PINS,original_outputs_verified_before_after=125,original_gzip_copied=False,
            independent_optional_review_verdict='NOT_INFERRED',optional_files=[v['source'] for v in dry['copy_pairs'] if v['copy'].startswith('optional_review_')]))
        write('closure_review.json',dict(approval_reference=args.approval_reference,approved_dry_sha256=args.approved_dry_sha256,
            approved_report_sha256=args.expected_report_sha256,new_independent_N=0,source_calls_rerun=0))
        names={v['copy'] for v in before}|set(GENERATED)
        with (directory/'raw_log_paths.txt').open('x',encoding='utf-8') as stream:
            stream.write(''.join((directory/name).relative_to(ROOT).as_posix()+'\n' for name in sorted(names) if name.endswith('.log')))
        need({p.name for p in directory.iterdir()}==names|{'manifest.json'},'exact selected output inventory')
    verified=verify_evidence_bundle(directory)
    need(verified['artifacts']==dry['expected_output_count'],'closed output count')
    print(json.dumps(dict(**verified,run_id=RUN_ID,manifest_sha256=sha(directory/'manifest.json'),
        copy_pairs=len(before),source_count=len(sources),raw_log_paths_file=(directory/'raw_log_paths.txt').relative_to(ROOT).as_posix())))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('dry','close'))
    parser.add_argument('--inventory-output',type=Path,required=True)
    parser.add_argument('--expected-report-sha256',required=True)
    parser.add_argument('--optional-review-file',type=Path,action='append',default=[])
    parser.add_argument('--approved-dry-sha256')
    parser.add_argument('--approval-reference')
    args=parser.parse_args();args.inventory_output=physical(args.inventory_output)
    need(args.inventory_output.parent==PREP and args.inventory_output.suffix=='.json','direct prep dry JSON path')
    dry=inventory(args)
    if args.mode=='dry':
        with args.inventory_output.open('x',encoding='utf-8') as stream:json.dump(dry,stream,ensure_ascii=False,indent=2);stream.write('\n')
        print(json.dumps(dict(status='DRY_ONLY_NO_BUNDLE',dry_sha256=sha(args.inventory_output),copy_pairs=len(dry['copy_pairs']),
            expected_output_count=dry['expected_output_count'],report_sha256=args.expected_report_sha256)))
    else:close(args,dry)


if __name__=='__main__':main()
