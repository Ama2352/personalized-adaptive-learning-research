"""ROOT dry/close only: GRAPH13 manufactured selection kernel, no tests/model/data execution."""
from pathlib import Path
import re
import archive_edge_artifact_cross_ready01 as base

ROOT,PREP=base.ROOT,base.PREP
RUN_ID='research-selection-kernel-engineering-20261109-01'
REPORT=ROOT/'research_tracking/reports/research_selection_kernel_readiness_20261109.md'
SNAP=PREP/'pre-research-selection-quantile-exit-fix01'
BASE_SHA='188f96e30cf2434b1b7a32dea6dbd66da61bdaa3b3d1e0a15108d42425f86db7'
KERNEL='src/knowledge_tracing/research_selection.py'
TEST='tests/shared_kt/test_research_selection.py'
KERNEL_SHA='0e3cf12d15626a76000c6cdc04779ac769806aae2a5e52f769d4c70f3580a348'
TEST01_SHA='3aad1836195b65824d342a766673ab664e584f0fd6328468bb4098487e191839'
TEST02_SHA='c2b0de6fa3af4a4c50944c3d15a0b686e068f920c5839565aa9149b5022d6ad6'
FINAL_SHA={'01':'bb98b10fe627c1d2082be57d8deee3ed377dc35454ad868cadbe1c3ed4a76d09',
           '02':'5d2542100251547c68e1b61c3af64db0c3a76231d731515dee04f29517cbd00e'}
CONTROLLER_SHA={'01':'728437890245e8828a01bb3606282a8b899d3da75e067e14b76a1a8309e03997',
                '02':'b24629bfa4d5141a2130514fdd1a995d060ad6513b5aee0a1b516c297a3fa020'}
CAPTURE_FILES=('before.json','cold-canary.json','worker-result.json','final.json')
OWNED_FILES=('GO.json','launch.json','ready.json','receipt.json','stdout.log','stderr.log')
PARITY_SHA='110d998297ac96e37e2c0bba03053085eee52ea3e5e6508b31d824f24d712e5f'
PARITY_SOURCE_SHA='9cffe96ca2595ce557e5e8b5df7b331e08684fa3fe82f4ca3f0ef6400be9c9e1'
PARITY_OUTER_SHA='ad63782fb668887a6692aeb3c9736c635dc2dcd3afd7c4e8782e07a9ff8e1bb0'


def verify():
    need,read,sha=base.need,base.read,base.sha
    need(sha(Path(base.__file__))==BASE_SHA,'common archiver source pin')
    need(sha(ROOT/KERNEL)==KERNEL_SHA and sha(ROOT/TEST)==TEST02_SHA,'executed current kernel/test pins')
    need(sha(SNAP/'test_research_selection.py.before')==TEST01_SHA,'failed01 exact test snapshot')
    pointers={KERNEL:KERNEL_SHA,TEST:TEST02_SHA}
    finals={}
    for trial in ('01','02'):
        capture=PREP/f'research-selection-pure-capture{trial}'
        owned=PREP/f'research-selection-pure-owned{trial}'
        need({p.name for p in capture.iterdir()}==set(CAPTURE_FILES),'exact closed pure capture; no hidden failure')
        need({p.name for p in owned.iterdir()}==set(OWNED_FILES),'exact owned raw files')
        need(sha(capture/'final.json')==FINAL_SHA[trial],'executed final receipt pin')
        final,worker,canary=(read(capture/name) for name in ('final.json','worker-result.json','cold-canary.json'))
        finals[trial]=final
        need(final['controller_sha256']==CONTROLLER_SHA[trial]
             and sha(PREP/f'check_research_selection{trial}.py')==CONTROLLER_SHA[trial],'executed controller identity')
        need(final['source_before']==final['source_expected']==worker['source_after'],'worker source-after admission')
        for name,pin in final['source_expected'].items():
            path=SNAP/'test_research_selection.py.before' if trial=='01' and name==TEST else ROOT/name
            need(sha(path)==pin,'tested source historical/current binding: '+name)
            pointers[path.relative_to(ROOT).as_posix()]=pin
        need(worker['denied_attempts']==worker['scientific_modules_present']==[]
             and all(type(worker[k]) is int and worker[k]==0 for k in ('model_calls','optimizer_calls','real_data_rows_opened')),
             'manufactured kernel-only scope')
        need(canary['status']=='STDLIB_KERNEL_COLD_IMPORT_ONLY' and canary['scientific_modules_present']==[]
             and canary['replicates']==2000 and canary['seed']==42 and canary['external_freeze_authority'] is False,
             'cold canary not main-selection authority')
        need(sha(owned/'receipt.json')==final['owned_receipt_sha256'],'owned receipt hash')
        receipt=read(owned/'receipt.json')
        need(receipt['cleanup_accepted'] is True and receipt['job_active_after_cleanup']==0
             and receipt['popen_handle_closed'] is True and receipt['actual_worker_in_job_before_GO'] is True
             and not receipt['errors'] and base.finite(receipt['elapsed_seconds'],30),'actual owned cleanup even failed01')
        for name,pin in receipt['output_sha256'].items():
            need(name in ('stdout.log','stderr.log') and sha(owned/name)==pin,'owned log original SHA')
        for name,pin in final['output_sha256'].items():need(sha(capture/name)==pin,'pure output SHA')
        stderr=(owned/'stderr.log').read_text(encoding='utf-8')
        need(len(re.findall(r'(?m)^Ran 8 tests in [0-9.]+s\s*$',stderr))==1,'actual8 unittest log')
        case_lines=[line for line in stderr.splitlines() if line.startswith('test_') and ' ... ' in line]
        need(len(case_lines)==8,'all8 case start/terminal lines')
        if trial=='01':
            need(final['status']=='REJECTED_KEEP_PARTIAL_KERNEL_FIXTURES' and final['counts'] is None
                 and worker['unittest_returncode']==1 and receipt['returncode']==1 and receipt['accepted'] is False,
                 'failed01 retained, not changed to PASS')
            need(sum(line.endswith('... ok') for line in case_lines)==7
                 and sum(line.endswith('... FAIL') for line in case_lines)==1
                 and next(line for line in case_lines if line.endswith('... FAIL')).startswith('test_loss_formula_known_answers_and_type7')
                 and 'AssertionError: 0.7500000000000001 != 0.75' in stderr and 'FAILED (failures=1)' in stderr,
                 'single exact quantile rounding failure, no inferred exit-bool failure')
        else:
            base.owned(owned)
            need(final['status']=='ACCEPTED_8_MANUFACTURED_SELECTION_KERNEL_FIXTURES'
                 and final['errors']==[] and final['counts']==dict(tests=8,failures=0,errors=0,skipped=0)
                 and final['source_after']==final['source_before'] and base.finite(final['elapsed_before_receipt_seconds'],30)
                 and worker['unittest_returncode']==0 and worker['unittest_raw_exit_type']=='int'
                 and type(worker['unittest_raw_exit_value']) is int and worker['unittest_raw_exit_value']==0
                 and all(line.endswith('... ok') for line in case_lines) and re.search(r'(?m)^OK\s*$',stderr),
                 'actual02 int0 and8PASS, not hypothetical bool-success observation')
            need(final['prior_charged_seconds']==.8424742 and final['total_allocation_ceiling_seconds']==30.8424742,
                 'retained prior resource ledger; no reset')
    proof=read(SNAP/'copy-verification.json')
    need(len(proof)==2,'exact two pre-edit source copies')
    for row in proof:
        need(row['source_before_sha256']==row['copy_sha256']==row['source_after_sha256']==sha(ROOT/row['copy']),
             'pre-edit before/copy/after provenance')
    inventory=read(SNAP/'inventory-before.json')
    for row in inventory['raw01_preserved']:
        need(sha(Path(row['path']))==row['sha256'],'all historical01 raw bytes unchanged')
    need(inventory['kernel_sha256']==KERNEL_SHA,'kernel unchanged across fixture/controller correction')
    need(sha(PREP/'reporting-loss-parity01.json')==PARITY_SHA
         and sha(PREP/'check_reporting_loss_parity01.py')==PARITY_SOURCE_SHA
         and sha(PREP/'reporting-loss-parity01-owned/result.json')==PARITY_OUTER_SHA,'ROOT actual formula parity source/receipts')
    parity=read(PREP/'reporting-loss-parity01.json')
    outer=read(PREP/'reporting-loss-parity01-owned/result.json')
    need(parity['status']=='ACCEPTED_SIX_MANUFACTURED_REPORTING_LL_PARITY_FIXTURES_NOT_SELECTOR'
         and len(parity['fixtures'])==6 and parity['absolute_tolerance']==1e-12 and parity['relative_tolerance']==0.
         and all(base.finite(row['absolute_difference'],1e-12) for row in parity['fixtures']),
         'six formula fixtures, no recalculation/execution')
    need(outer['accepted'] is True and outer['returncode']==0 and base.finite(outer['seconds'],10)
         and outer['source_sha256']==PARITY_SOURCE_SHA and outer['whole_cap_seconds']==10,
         'regular subprocess parity accepted; NOT ownedJob certificate')
    evaluator='src/knowledge_tracing/gam_kt/evaluation.py'
    need(sha(ROOT/evaluator)==parity['source_sha256'],'formula evaluator source reference, no dependency copies')
    pointers[evaluator]=parity['source_sha256']
    pointers['scripts/research/windows_owned_worker.py']='0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1'
    pointers[base.HELPER]=sha(ROOT/base.HELPER)
    for name,pin in pointers.items():need(sha(ROOT/name)==pin,'all current/reference pins before copy')
    return dict(kind='MANUFACTURED_RESPONSE_POOLED_SELECTION_STATISTICAL_KERNEL_ONLY',
        accepted_unittest_cases=8,failed01_cases_run=8,failed01_passed=7,failed01_failures=1,
        failure01_reason='EXACT_TYPE7_FLOAT_ROUNDING_ASSERTION_NOT_KERNEL_MATH',
        kernel_unchanged_across_attempts=True,actual02_raw_exit_type='int',actual02_raw_exit_value=0,
        bool_exit_compatibility_fix_observed_as_bool_success=False,
        actual_formula_parity_fixtures=6,formula_absolute_tolerance=1e-12,formula_relative_tolerance=0.,
        formula_parity_regular_subprocess_only=True,pure02_owned_job_cleanup_accepted=True,
        accepted02_stored_prewrite_seconds=finals['02']['elapsed_before_receipt_seconds'],
        prior01_charged_seconds=.8424742,total_pure_allocation_ceiling_seconds=30.8424742,
        bootstrap_replicates=2000,bootstrap_seed=42,eligibility_epsilon=0.,
        actual_research_selection=False,nine_candidate_admission=False,external_freeze_authority=False,
        model_fits=0,optimizer_steps=0,actual_corpus_reads=0,research_efficacy_claimed=False),pointers


def selections():
    pairs=[(ROOT/KERNEL,'source__research_selection.py'),(ROOT/TEST,'test__research_selection.py')]
    names=('check_research_selection01.py','check_research_selection02.py',
           'MAIN_SELECTOR_CONTRACT01.md','RESEARCH_SELECTION_KERNEL_PREP01.md','RESEARCH_SELECTION_KERNEL_PREP02.md',
           'research_selection_source_freeze01.json','research_selection_source_freeze02.json',
           'check_reporting_loss_parity01.py','reporting-loss-parity01.json')
    pairs.extend((PREP/name,name) for name in names)
    for trial in ('01','02'):
        for folder,files,alias in ((f'research-selection-pure-capture{trial}',CAPTURE_FILES,f'pure{trial}_capture'),
                                   (f'research-selection-pure-owned{trial}',OWNED_FILES,f'pure{trial}_owned')):
            pairs.extend((PREP/folder/name,alias+'__'+name) for name in files)
    pairs.extend((SNAP/name,'pre_fix__'+name) for name in ('inventory-before.json','copy-verification.json',
        'test_research_selection.py.before','check_research_selection01.py.before'))
    pairs.extend((PREP/'reporting-loss-parity01-owned'/name,'formula_parity_outer__'+name)
                 for name in ('result.json','stdout.log','stderr.log'))
    pairs.append((Path(__file__).resolve(),Path(__file__).name))
    return pairs


def note():
    return '''# GRAPH13 — kernel thống kê chọn ứng viên, dữ liệu chế tạo

Kernel response-pooled LL/common-U +2.000 shared learner draws seed42/type7/strictupper<0/stable-ID tie đã PASS8purecases revision02; không model/data/CSV selection/authority/mainrefit/efficacy. Caller vẫn phải chứng nhận đủ9selected-only candidates vàexternalfreeze trướcmainrefits. A2/SAKT/GKT không bị bỏ. Không biến manufacturedCI thành researchCI/N.

Giữ nguyên01:8run/7PASS/1FAIL vì exacttype7.025=.7500000000000001 so.75. Kernel không đổi; test02 chỉtolerance1e-14, stricteligibility/tinynegative khôngđổi. Raw02 actualSystemExit=int0. Normalizationbool/None làcompatibilityfix, khôngquan sátboolsuccess/khôngkếtluậnboolgâyfail01.01finalcountsnull vàworker_resultsourceafter giữexactbytes.

SáuROOTformulaParityfixtures dùngevaluator GAM/sklearn thật trên manufacturedarrays; regularsubprocess reaped/3.4976351s/10, khôngownedJob/RAMcertificate. Pure02 cóownedJobcleanup0. Nguồn/dependencyversion ghi trongparityreport; chỉSHAreference evaluator/ownedhelper, khôngcopyvenv/dependencies/corpus. LLperlearnerroundedaggregates cóthểkhácbitcuối allrowfsum, tolerancefixture1e-12 khôngeligibilityepsilon.

Cácstdout/stderr/ownedreceipts/coldcanary/sourcebeforeafter/snapshots đượcgiữriêng; execution.log chỉlàarchiver. Closure cócopyinventorytrướcsau+verifybundle, khôngruntest/model/actualselection. Snapshotreport chuẩn bịtrướcclosure; manifest xácnhậnarchiveintegrity, khôngruntime/fullGate/RQcomplete. Canonicalreport ../../reports/research_selection_kernel_readiness_20261109.md.
'''


if __name__=='__main__':base.entry(RUN_ID,verify,selections,note,required_report=REPORT)
