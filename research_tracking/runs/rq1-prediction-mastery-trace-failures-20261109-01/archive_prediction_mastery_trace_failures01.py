"""ROOT dry/close only. Archives two REJECTED native attempts; never runs them.

Small rawfailure snapshots, cached3240/production source pointers only; no science
on partialgzip, no retry and no retrospective metadata/result reconstruction.
"""
from pathlib import Path
import re
import archive_edge_artifact_cross_ready01 as base

ROOT,PREP = base.ROOT,base.PREP
RUN_ID = 'rq1-prediction-mastery-trace-failures-20261109-01'
REPORT = ROOT/'research_tracking/reports/rq1_prediction_mastery_trace_failures_20261109.md'
FREEZE = PREP/'prediction_mastery_failed_attempts_frozen01.json'
FREEZE_SHA = 'e4e0ecc9b1284e142382b091ab535f92e8fe5a557dd161798e753a9ca704c040'
BASE_SHA = '188f96e30cf2434b1b7a32dea6dbd66da61bdaa3b3d1e0a15108d42425f86db7'
PLAN_SHAS = ('b8587f7493bf62d9f63a3f45fa5cc0db718c4cd42b99b6bc2ed3be69c7ed70e1',
             '4a0f72a0dcb72e64cf8e997db9eb38854e0b0bc9ded69441b6a26c5a6aed3cef')


def verify():
    need,read,sha = base.need,base.read,base.sha
    need(sha(Path(base.__file__)) == BASE_SHA and sha(FREEZE) == FREEZE_SHA,'reviewed archive/failurefreeze')
    freeze=read(FREEZE)
    need(freeze['status']=='FAILED_ATTEMPTS01_02_FROZEN_READONLY_INVENTORY_NO_RETRY'
         and freeze['file_count']==len(freeze['files'])==51 and freeze['research_acceptance'] is False,
         'all51 raw/source files frozen, no research admission')
    rows=freeze['files'];need(len({r['source'] for r in rows})==51,'unique actual frozenfile list')
    for row in rows:
        p=base.physical(ROOT/row['source'])
        need(p.is_relative_to(PREP) and p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],'preserved raw/source bytes')
    pointers={r['source']:r['sha256'] for r in rows}  # Includes partialgzip SHA reference only.
    for number,pin in enumerate(PLAN_SHAS,1):
        path=PREP/f'prediction_mastery_trace_plan0{number}.json'
        need(sha(path)==pin,'exact executed plan')
        plan=read(path)
        for name,h in {**plan['inputs_sha256'],**plan['source_sha256']}.items():
            need(sha(ROOT/name)==h,'all immutable source/cache references; do not refresh drift')
            if name in pointers:need(pointers[name]==h,'shared reference identity')
            pointers[name]=h
        pointers[path.relative_to(ROOT).as_posix()]=pin
    for folder,count in (('prediction-mastery-pure12-attempt01',12),('prediction-mastery-pure14-attempt02',14)):
        directory=PREP/folder; r=read(directory/'final.json')
        need(r['status']==f'ACCEPTED_{count}_SYNTHETIC_TRACE_FIXTURES' and r['errors']==[]
             and r['counts']==dict(tests=count,failures=0,errors=0,skipped=0)
             and r['source_before']==r['source_after'],'pure12/14 source-bound distinct actual invocations')
        receipt=base.owned(directory/'owned')
        need(sha(directory/'owned/receipt.json')==r['owned_receipt_sha256'],'pure receipt chain')
        log=(directory/'owned/stderr.log').read_text(encoding='utf-8')
        need(re.search(r'Ran '+str(count)+r' tests in [0-9.]+s',log) and log.rstrip().endswith('OK'),'actual unittest totals')
        need(not (directory/'postwrite_rejection.json').exists(),'pure no late rejection')
    for number in (1,2):
        directory=PREP/f'prediction-mastery-native-outer0{number}'
        r=read(directory/'final.json');owned=read(directory/'owned/receipt.json')
        need(r['status']=='REJECTED_KEEP_ALL_NO_RETRY' and r['errors'] and r['counts'] is None
             and r['source_before']==r['source_after'],'native remains REJECTED, stable source only')
        need(owned['accepted'] is False and owned['cleanup_accepted'] is True and owned['job_active_after_cleanup']==0
             and owned['popen_handle_closed'] is True and owned['cleanup_errors']==[]
             and owned['actual_worker_in_job_before_GO'] is True,'rejected native with owned cleanup accepted')
        for name,pin in owned['output_sha256'].items():
            need(name in ('stdout.log','stderr.log') and sha(directory/'owned'/name)==pin,'actual owned logsha')
    first=PREP/'prediction-mastery-trace-attempt01'
    need({p.name for p in first.iterdir()}=={'dispatch.json','failure.log','worker_run.json'},'first fail before reservation/policy')
    r=read(first/'worker_run.json')
    need(r['status']=='REJECTED_RETAIN_NO_PARTIAL_INTERPRETATION' and r['direct_attempts']==r['native_attempts']=={}
         and r['completed_trajectories']==[] and r['node_order']==[],'native01 zero policy/update before Paper2')
    message=(first/'failure.log').read_text(encoding='utf-8')
    need('pandas' in message and 'socket.gethostname' in message and 'no child/network during trace' in message,
         'actual local-metadata setup failure, not fabricated model mismatch')
    second=PREP/'prediction-mastery-trace-attempt02'
    need({p.name for p in second.iterdir()}=={'dispatch.json','reservation.json','trace.jsonl.gz','trajectory-1.json','trajectory-2.json'},
         'exact partial second stream, no terminal/failure/metadata receipt invented')
    owned=read(PREP/'prediction-mastery-native-outer02/owned/receipt.json')
    need(any(e['type']=='TimeoutError' and e['message']=='active deadline preserves cleanup reserve' for e in owned['errors']),
         'actual owned deadline reason; no research acceptance')
    reservation=read(second/'reservation.json')
    need(reservation['direct_reservations']['update']==2160 and reservation['native_caps']['predict']==6480
         and reservation['hardkill_actual_counts']=='UNKNOWN_LE_RESERVED; no reset/retry','durable full caps before work')
    a,b=read(second/'trajectory-1.json'),read(second/'trajectory-2.json')
    need((a['seed'],a['profile'],a['variant'])==(20000,'PG','graph_package')
         and (b['seed'],b['profile'],b['variant'])==(20000,'PG','empty_graph_package')
         and a['exact_legacy_rows']==a['full_preview_exact']==b['exact_legacy_rows']==b['full_preview_exact']==120
         and a['cumulative_direct_attempts']['update']==120 and b['cumulative_direct_attempts']['update']==240
         and a['cumulative_native_attempts']['predict']==360 and b['cumulative_native_attempts']['predict']==720,
         'progress-only lowerbounds, never total or full admission')
    parity=read(ROOT/'research_tracking/runs/rq1-fixed-edge-set-contrast-20261108-01/parity.json')
    saved=next(r for r in parity['observed']['profile_state_rng_fingerprints'] if r['seed']==20000 and r['profile']=='PG')
    for row in (a,b):
        need(row['initial_sha256']==saved['initial_policy_sha256'][row['variant']]
             and row['final_sha256']==saved['final_policy_sha256'][row['variant']],'two persisted endpoint parity only')
    need(freeze['conservative_charged_seconds']==56.3709122 and freeze['remaining_seconds']==3.6290878
         and freeze['native02_total_actual_updates']=='UNKNOWN_IN_CLOSED_INTERVAL_240_2160'
         and freeze['partial_gzip_crc']=='UNKNOWN_UNCLOSED_HARDKILL_NOT_PARSED','stopped cumulativeledger/unknownpartial')
    return dict(kind='REJECTED_NATIVE_MASTERY_TRACE_OPERATIONAL_FAILURES_NOT_RESEARCH_RESULT',
        research_status='NO_ALL2160_PARITY_NO_MASTERYSCORE_FINDING',native01='PRE_POLICY_LOCAL_METADATA_SETUP_REJECTED',
        native02='OWNED_ACTIVE_TIMEOUT_PARTIAL_UNINTERPRETABLE',pure01_cases=12,pure02_cases=14,
        pure_case_scope='old12 subset ofnew14, not26scientificsamples',original_cap_seconds=60,
        conservative_charged_seconds=56.3709122,remaining_seconds=3.6290878,retry_allowed=False,
        completed_updates_lower_bound=240,actual_updates_total=None,actual_updates_upper_bound=2160,
        predict_lower_bound=720,predict_total=None,predict_upper_bound=6480,partial_gzip_crc_verified=False,
        metadata02_terminal_receipt_available=False,new_independent_N=0,all_owned_cleanup_accepted=True,
        closure_scope='Operational archive only; partialstream remains opaque bytes'),pointers


def selections():
    rows=base.read(FREEZE)['files']
    pairs=[]
    oldnames={'prediction_mastery_trace_worker01.py','test_prediction_mastery_trace01.py','run_prediction_mastery_trace01.py',
        'PREDICTION_MASTERY_TRACE_CONTRACT01.md','prediction_mastery_trace_plan01.json'}
    for row in rows:
        original=ROOT/row['source'];relative=original.relative_to(PREP)
        if relative.as_posix()=='prediction-mastery-trace-attempt02/trace.jsonl.gz':
            continue  # Only51-file frozeninventory+SHA pointer; keep partialraw inplace, no gzip parse/copy.
        source=PREP/'pre-prediction-mastery-metadata-fix01'/relative if relative.as_posix() in oldnames else original
        base.need(base.sha(source)==row['sha256'],'before-source snapshot must equal executed01 bytes')
        pairs.append((source,'raw__'+relative.as_posix().replace('/','__')))
    pairs.extend([(FREEZE,FREEZE.name),(Path(__file__).resolve(),Path(__file__).name)])
    return pairs


def note():
    return '''# RQ1 — hai native trace attempts chưa nghiệm thu

Native01 local Windows metadata setupfailure trước policy/update. Native02 owned active deadline hardtimeout; cleanup Job0 accepted nhưng research bị từ chối. Pure12/14 softwarefixtures không là26researchsamples. Chỉ2/18trajectory receipts hoàn tất, nên actualupdate total UNKNOWN trong[240,2160], predict UNKNOWN trong[720,6480]. Reservation/caps không là actualtotal. Không giải nén/phân tích/repair partialgzip, CRC chưa nghiệm thu; chỉ giữSHA/reference trong inventory, raw gốc nguyênvị trí.

Original60s charged56.3709122 còn3.6290878; batchSTOP, không retry/reset. Không có findings θ/pi/calibration hoặc causal/newN từ partial. Metadata02 fields/helpercounts không persist trước hardkill nên unavailable; không tự điền0. Report snapshot phân biệt source-overhead hypotheses với measurement, và đề nghị operational microbenchmark chưa chạy.

Archive completed/verify chỉ xác nhận đóng gói failure bytes; không là native scientificPASS/currentGate/benchmark. Không copy lại cached3240gzip/notebooks/CSV/Gate154: source_references.json giữexactSHA vào immutablebundles/nguồn. Ownpartialgzip không copy vào bundle; SHA/size/path giữ trong frozeninventory vàsource_references, raw gốc vẫn nguyên vị trí. Copyinventory trước/sau + sourceprepost giữ nguồn đã chạy. Canonical report: ../../reports/rq1_prediction_mastery_trace_failures_20261109.md.
'''


if __name__=='__main__':
    base.entry(RUN_ID,verify,selections,note,required_report=REPORT)

