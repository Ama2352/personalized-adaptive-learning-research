"""ROOT-only dry/close; preserves16mock cases and prior15/1, no executions."""
from pathlib import Path
import xml.etree.ElementTree as ET
import archive_edge_artifact_cross_ready01 as base

R,P=base.ROOT,base.PREP
RUN_ID='cgakt-main-selected-producer-engineering-20261109-01'
REPORT=R/'research_tracking/reports/cgakt_main_selected_producer_readiness_20261109.md'
SNAP=P/'pre-main-selected-wire-fix02'
SOURCES={
 'src/knowledge_tracing/akt/research_main_execution.py':'902018762fde6433a9bd9e33ce770df0057f6b0623327b8ff6b798e1faf4d881',
 'src/knowledge_tracing/akt/research_selected_runner.py':'fcaa0c1850a0de391e26d4b3eb915fc91b3848f1e8d834898fa7fb788e868e20',
 'tests/akt/test_research_main_execution.py':'9c102b3645528c5a2b7a4ca7830a68429f824ec0c3199b4d3ba587f88efcc0ce',
 'tests/akt/test_research_selected_runner.py':'05f85bd487e93fca925f568fdb326852dc9bcc07ef0d32f994e4051dd03fdeaa'}
PINS={
 'check_main_selected_producer01.py':'856ed83cc8e45b9ca3e29334f857c247fa3a1e212ebb7e5cf8d51204d5ed1c31',
 'check_main_selected_producer02.py':'bd1216a51b28e7c7f491851f5b61b8924352418998086afeaa1e9094ad810e59',
 'main_selected_producer_pure01_allocation.json':'4d3420f9056dea17193a217575870b0dbf096fcdc026f78b1b26b097b1b6b959',
 'main_selected_producer_pure02_allocation.json':'61d11680420a7de3357b3acf47a9ea7f894acfa8c011b77e2dde45bf57361f71',
 'pre-main-selected-wire-fix02/inventory-before.json':'8e18b9f3cbfbb33783e4b752b4a3b81b0cf9d0633abc129fcb3e736c2f9e680a',
 'pre-main-selected-wire-fix02/copy-verification.json':'2451540504c4b6d4b011a00a418d3d2926e15fe3f3d6267d24d0a8ec54f6d9bd',
 'main-selected-producer-pure01/final.json':'6dfb2d68e962ce2bc33f4383a2838fc9038302254f6ef6ee0f5cdfd09fcfb59a',
 'main-selected-producer-pure01/worker-result.json':'86718667a38ae5a562f7e81e444c306a72dbc4913dba5b20ad63e6a8c610d164',
 'main-selected-producer-pure01-owned/receipt.json':'4d107af50cefbd5205104ec78375b2454f3bba28c268e3aa4433b130f5d3ec1a',
 'main-selected-producer-pure02/final.json':'9a8ea24f34c1bdd74b287e75cecad4bf68ab6d976ab0c44dea7ca80a616bcb6f',
 'main-selected-producer-pure02/worker-result.json':'298c969419ad5845f8aea2412446f907a815541f40ecb7f129a5a09de90fb653',
 'main-selected-producer-pure02-owned/receipt.json':'718965c04c284b274075303f29c97049182bd7e70a3ed25601ea80ee933aa3a1'}
CAPTURE_FILES=('case-events.jsonl','cold-canary.json','collected.json','final.json','junit.xml','pytest.log','windows-metadata.json','worker-result.json')
OWNED_FILES=('GO.json','launch.json','ready.json','receipt.json','stdout.log','stderr.log')
OLD_TEST='tests/akt/test_research_main_execution.py'
OLD_TEST_SHA='fdeafb91ba738da2fd1ea7dbcb08a4658954079835d148a0d07785beef22e59d'


def junit(path,expected):
    root=ET.fromstring(base.physical(path).read_bytes());cases=list(root.iter('testcase'))
    counts={k:sum(int(s.get(k,'0')) for s in root.iter('testsuite')) for k in expected}
    base.need(counts==expected and len(cases)==16 and len({(c.get('classname'),c.get('name')) for c in cases})==16,'exact16unique JUnit cases')
    base.need(sum(c.get('classname')=='tests.akt.test_research_main_execution' for c in cases)==10
        and sum(c.get('classname')=='tests.akt.test_research_selected_runner' for c in cases)==6,'guard10/runner6 actual population')
    failures=[c for c in cases if c.find('failure') is not None]
    if expected['failures']:
        base.need(len(failures)==1 and failures[0].get('name')=='test_auth_consistency_only_with_explicit_metadata_mock_no_guard_grant'
            and 'Differing items' in failures[0].find('failure').get('message'),'preserved actual JSON assertion failure only')
    else:base.need(all(not list(c) for c in cases),'no failure/error/skip hidden in actual16')
    return counts


def verify():
    need,sha,read=base.need,base.sha,base.read
    need(sha(Path(base.__file__))=='188f96e30cf2434b1b7a32dea6dbd66da61bdaa3b3d1e0a15108d42425f86db7','shared archiver pin')
    for name,pin in SOURCES.items():need(sha(R/name)==pin,'final tested source drift')
    for name,pin in PINS.items():need(sha(P/name)==pin,'actual source/packet/raw pin drift')
    proof=read(SNAP/'copy-verification.json');before=read(SNAP/'inventory-before.json')
    need(proof['status']=='EXACT_PRE_FIX_COPIES_VERIFIED' and len(proof['copy_pairs'])==len(before['sources'])==9,'pre-fix source snapshots')
    for row in proof['copy_pairs']:
        need(sha(R/row['copy'])==row['sha256_before']==row['sha256_copy']==row['sha256_after']
             and (R/row['copy']).stat().st_size==row['bytes'],'pre/copy/post snapshot SHA')
    for row in before['raw01_immutable_references']:need(sha(R/row['path'])==row['sha256'],'raw01 retained unchanged')
    pointers={base.HELPER:sha(R/base.HELPER)};outcomes=[]
    def pointer(name,pin):
        need(name not in pointers or pointers[name]==pin,'conflicting logical source references');pointers[name]=pin
    for number in (1,2):
        tag=f'{number:02d}';capture=P/f'main-selected-producer-pure{tag}';owned=P/f'main-selected-producer-pure{tag}-owned'
        packet=read(P/f'main_selected_producer_pure{tag}_allocation.json')
        final,worker,canary,metadata=(read(capture/name) for name in ('final.json','worker-result.json','cold-canary.json','windows-metadata.json'))
        receipt=read(owned/'receipt.json');expected=dict(tests=16,failures=1 if number==1 else 0,errors=0,skipped=0)
        need({p.name for p in capture.iterdir()}==set(CAPTURE_FILES),'exact fixed capture files/no late failure')
        need({p.name for p in owned.iterdir() if p.is_file()}==set(OWNED_FILES),'exact owned top-level receipts/logs')
        junit(capture/'junit.xml',expected)
        need(worker['counts']==expected and worker['pytest_exit_code']==(1 if number==1 else 0)
            and worker['original_error'] is worker['junit_error'] is None,'actual worker16 counts/error status')
        need(packet['expected_tests']==16 and packet['whole_seconds']==60 and packet['worker_seconds']==50
            and packet['cleanup_seconds']==3 and packet['model_or_data_execution_authorized'] is False,'unchanged16 allocation/caps')
        sources,runtimes=packet['source_pins'],packet['runtime_pins']
        need(sources==final['source_before']==final['source_after']==worker['source_before']==worker['source_after']
            and runtimes==final['runtime_before']==final['runtime_after']==worker['runtime_before']==worker['runtime_after'],'executed source/runtime pre/post')
        for name,pin in sources.items():
            path=SNAP/'test_research_main_execution.py.before' if number==1 and name==OLD_TEST else R/name
            need(sha(path)==pin,'exact actual-tested source or historical snapshot')
            pointer(path.relative_to(R).as_posix(),pin)
        need(number!=1 or sources[OLD_TEST]==OLD_TEST_SHA,'old failed fixture provenance')
        need(final['allocation_sha256']==worker['allocation_sha256']==sha(P/f'main_selected_producer_pure{tag}_allocation.json'),'packet binding')
        need(receipt['cleanup_accepted'] is True and receipt['job_active_after_cleanup']==0
            and receipt['actual_worker_in_job_before_GO'] and receipt['popen_handle_closed'] and receipt['cleanup_errors']==[]
            and receipt['errors']==[] and receipt['returncode']==(1 if number==1 else 0),'actual Job cleanup even failed test')
        need(receipt['worker_sha256']==PINS[f'check_main_selected_producer{tag}.py'] and receipt['cleanup_reserve_seconds']==3
            and base.finite(receipt['elapsed_seconds'],60) and receipt['max_seconds']<=58,'exact owned controller/caps')
        need(sha(owned/'receipt.json')==final['owned_receipt_sha256'],'outer-owned receipt pin')
        for name,pin in final['output_sha256'].items():need(name in CAPTURE_FILES and sha(capture/name)==pin,'raw worker output hashes')
        for name,pin in receipt['output_sha256'].items():need(name in ('stdout.log','stderr.log') and sha(owned/name)==pin,'owned stdout/stderr hashes')
        need(worker['cold_import']==canary and canary['status']=='COLD_REAL_METADATA_MODULES_ONLY'
            and worker['cached_caller_class_identity'] and canary['same_execution_spec_class']
            and canary['scientific_modules_present']==[] and canary['guard_constructed'] is False
            and canary['actual_runtime_or_gate_validated'] is False,'real cached imports, no actual grant')
        need(worker['native_windows_metadata']==metadata and metadata['phase_closed'] and metadata['fixture_replaced'] is False
            and metadata['helper_calls']==len(metadata['commands'])==1 and metadata['outside_phase_popen_attempts']==0,'one honest Windows helper/no test Popen')
        need(worker['denied_attempts']==worker['scientific_modules_present']==worker['monitor_errors']==[]
            and worker['monitor_stopped'] and worker['environment_restored']
            and all(type(worker[k]) is int and worker[k]==0 for k in ('model_calls','optimizer_calls'))
            and worker['actual_guard_grant'] is False and worker['actual_gate_or_corpus_acceptance'] is False,'only mock scope')
        need(worker['resources']['observed_peak_rss_bytes']<=1024**3
            and worker['resources']['observed_minimum_available_ram_bytes']>=2*1024**3,'observed RAM limits')
        need(base.finite(worker['elapsed_seconds'],50) and base.finite(final['elapsed_before_receipt_seconds'],60)
            and final['cap_seconds']==60 and final['cleanup_reserve_seconds']==3,'stored global worker/outer bounds')
        if number==1:
            need(worker['status']=='REJECTED_KEEP_ALL' and final['status']=='REJECTED_KEEP_PARTIAL'
                and final['counts'] is None and receipt['accepted'] is False and len(final['errors'])==1
                and final['errors'][0]['message']=='actual owned Job/cleanup verdict','outer early rejection is not zero tests')
        else:
            need(worker['status']=='ACCEPTED_16_MOCKED_MAIN_PRODUCER_CASES_PENDING_OUTER'
                and final['status']=='ACCEPTED_16_MOCKED_MAIN_PRODUCER_ENGINEERING_ONLY' and final['counts']==expected
                and final['errors']==[] and receipt['accepted'] is True,'accepted16 not actual mainfit')
            need(final['prior_charged_seconds']==5.236512999981642 and final['total_allocation_ceiling_seconds']==65.23651299998164
                and base.finite(final['cumulative_elapsed_before_receipt_seconds'],65.23651299998164),'prior failed run ledger retained')
        outcomes.append(dict(attempt=tag,raw_counts=expected,passed=16-expected['failures'],outer_counts=final['counts'],
            worker_seconds=worker['elapsed_seconds'],outer_stored_seconds=final['elapsed_before_receipt_seconds'],
            owned_seconds=receipt['elapsed_seconds'],owned_cleanup=True,metadata_helper_calls=metadata['helper_calls']))
    return dict(kind='MODULES_IMPLEMENTED_ONLY_MOCK_ORCHESTRATION_VERIFIED',attempts=outcomes,final_tests=16,
        logical_test_partition=dict(guard=10,orchestration=6),actual_model_calls=0,actual_optimizer_calls=0,
        actual_corpus_or_runtime_gate_admission=False,actual_main_authorization=False,public_entry_success_path_tested=False,
        actual_selected_fit=False,all9_matrix=False,external_freeze=False,refit_calibration=False,lifecycle_resume=False,
        current_gate_checked_by_batch=False,git_profile_test_scope='METADATA_ONLY_NOT_ACTUAL_GIT_OR_PREFLIGHT',
        unchanged_production_sources={k:v for k,v in SOURCES.items() if k.startswith('src/')},
        runtime_dependencies_copied=False,corpus_copied=False,closure_does_not_execute_tests=True),pointers


def selections():
    pairs=[(R/name,'final__'+Path(name).name) for name in SOURCES]
    for name in ('check_main_selected_producer01.py','check_main_selected_producer02.py',
        'main_selected_producer_pure01_allocation.json','main_selected_producer_pure02_allocation.json',
        'MAIN_SELECTED_PRODUCER_PATCH_PLAN01.md','MAIN_SELECTED_PRODUCER_HANDOFF01.md',
        'MAIN_SELECTED_PRODUCER_WIRE_FIX02.md','main_selected_producer_source01.json'):
        pairs.append((P/name,name))
    for number in (1,2):
        tag=f'{number:02d}'
        pairs.extend((P/f'main-selected-producer-pure{tag}'/name,f'trial{tag}__'+name) for name in CAPTURE_FILES)
        pairs.extend((P/f'main-selected-producer-pure{tag}-owned'/name,f'owned{tag}__'+name) for name in OWNED_FILES)
    pairs.extend((SNAP/name,'pre-wire-fix__'+name) for name in ('inventory-before.json','copy-verification.json'))
    pairs.extend((R/row['copy'],'pre-wire-fix__'+Path(row['copy']).name) for row in base.read(SNAP/'copy-verification.json')['copy_pairs'])
    pairs.append((Path(__file__).resolve(),Path(__file__).name));return pairs


def note():
    return '''# Main selected-only A0–A3: software orchestration09/11/2026

MODULES_IMPLEMENTED_ONLY_MOCK_ORCHESTRATION_VERIFIED. Actual02:16PASS0FES,
cold real cached metadata classes/import origins, no NumPy/Torch/model/corpus.
Actual01:16run15PASS1FAIL JSON tuple/list expected-wire test; outercountsNULL
because RC1 checked before reading counts, NOT0tests.01cleanup is accepted/Job0;
trial remains rejected. Test-only correction; productionguard9020/runnerfcaa
unchanged. Keep full wire/caps/identity assertions and cap-drift negative.

New concrete actual disk/runtime/Gate/source/publicdata/graph guard and conditional
selected-fit80/rawselection10 runner implemented;16mocks do NOT exercise complete
successful publicentry. No actual auth/Git/preflight/Gate/corpus admission/NNfit,
no all9/matrix/externalfreeze/refit/calibration/lifecycle-resume certificate.
Grade10CPU A* first; SAKT/GKT/Junyi remain mandatory pending producers.
Git profile tests metadata only; native Windows discovery honestly uses1literal
cmd-ver helper in each attempt, then process phase closed,0laterPopen attempts.
No blanket0process orOSsandbox claim. RSS1GiB/free2GiB observed checks; global
60s per attempt/cleanup3; prior01charge retained in02, no hidden reset.

Raw JUnit/logs/receipts and pre-fix snapshots preserve bytes, source/runtime hashes
before/after and copyinventory. No runtime/dependency/corpus copies. execution.log
is archive log, not test/native log. Archiving does not rerun tests or models.
README/report scope stays module/mock evidence; manifest confirms closure only.
Canonical report ../../reports/cgakt_main_selected_producer_readiness_20261109.md.
'''


if __name__=='__main__':base.entry(RUN_ID,verify,selections,note,required_report=REPORT)
