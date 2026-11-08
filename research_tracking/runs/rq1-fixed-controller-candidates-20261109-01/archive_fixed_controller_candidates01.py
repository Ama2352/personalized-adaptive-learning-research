"""ROOT dry/closure only; không chạy analyzer/tests hoặc copy lại cache/production sources."""
from pathlib import Path
import re
import archive_edge_artifact_cross_ready01 as base

ROOT,PREP=base.ROOT,base.PREP
RUN_ID='rq1-fixed-controller-candidates-20261109-01'
REPORT=ROOT/'research_tracking/reports/rq1_fixed_controller_candidates_20261109.md'
DATA=PREP/'fixed-controller-candidates-attempt02'
FINAL_SHA='4808c8261094353ac5496bd37ae6353568a93542f05af2040f6157a753e88427'
PURE_SHA='941efc0b6c00feae6c0f0d2978e5d6f1d103684d20df4450ed50f46c5864d603'
OUTPUTS={'summary.json':'b74ed4cddc318053ebf4219ba2fae4ce39080c4ebe93750a06d68aa3ae9aeb57',
         'validation.json':'dc71a69af1c703295a2db2791c3a78cde6c476b6165277916a21b43dafd861b9',
         'event_flags.json':'1cf3ba08a6d5aff1f25d1cdd91f1aefa5fdd9578a3c1c17c7625fe7a0097942b',
         'result.json':'29c032854fb0e0d9b6f92d6272a991bbc7f4361a5c50132aa24419c8b58a5711'}


def verify():
    need,read,sha=base.need,base.read,base.sha
    need(sha(Path(base.__file__))=='188f96e30cf2434b1b7a32dea6dbd66da61bdaa3b3d1e0a15108d42425f86db7','reviewed common archiver')
    final_path=PREP/'fixed-controller-cached02-outer/final.json';pure_path=PREP/'fixed-controller-pure18-capture02/final.json'
    need(sha(final_path)==FINAL_SHA and sha(pure_path)==PURE_SHA,'actual ROOT terminal receipt pins')
    final,pure=read(final_path),read(pure_path)
    need(final['status']=='ACCEPTED_CACHED_SOURCE_RECONSTRUCTED_CONTROLLER_CID' and final['errors']==[]
         and base.finite(final['elapsed_before_receipt_seconds'],10) and final['cap_seconds']==10,'cached02 acceptance')
    need(pure['status']=='ACCEPTED_18_PURE_CONTROLLER_RULE_FIXTURES' and pure['errors']==[]
         and pure['counts']==dict(tests=18,failures=0,errors=0,skipped=0)
         and pure['source_before']==pure['source_after']==pure['source_expected'],'pure18 exact source-bound regression')
    for name,pin in pure['source_expected'].items():
        need(sha(PREP/name)==pin,'executed02 source drift')
    need(sha(PREP/'run_fixed_controller_cached02.py')==final['controller_sha256']
         and sha(PREP/'run_fixed_controller_pure18_02.py')==pure['controller_sha256'],'executed ROOT controllers')
    for folder in ('fixed-controller-pure18-capture02','fixed-controller-cached02-outer'):
        need(not (PREP/folder/'postwrite_rejection.json').exists(),'late ROOT rejection override')
    need({p.name for p in DATA.iterdir()}==set(OUTPUTS),'exact4 cached outputs/no failure')
    for name,pin in OUTPUTS.items():
        need(sha(DATA/name)==pin==final['artifacts'][name]['sha256'] and (DATA/name).stat().st_size==final['artifacts'][name]['bytes'],'output SHA/size')
    validation,summary,result=(read(DATA/n) for n in ('validation.json','summary.json','result.json'))
    need(validation==final['validation'] and validation['paired_snapshots']==1080 and validation['source_R_membership_exact']==2160
         and validation['source_CID_exact']==2160 and validation['old_groups_reconciled']==16
         and validation['joint_cells']==512 and validation['B_CID_cells']==64,'all2160 parity/allgroups')
    need(sha(PREP/'analyze_fixed_controller_candidates02.py')==validation['source_sha256']==final['source_sha256']
         and sha(PREP/'rq1_fixed_controller_candidates_contract02_20261109.md')==validation['contract_sha256']==final['contract_sha256'],
         'actual analyzer/contract chain')
    need(validation['native_model_simulator_calls']==validation['new_independent_N']==0
         and final['native_model_simulator_calls']==final['new_independent_N']==0,'no extra model/native/N')
    need(result['outputs_sha256']=={n:h for n,h in OUTPUTS.items() if n!='result.json'},'inner output vector')
    need(final['input_before']==final['input_after']==validation['inputs_sha256'],'fixed input identities')
    for name,pin in validation['inputs_sha256'].items():
        need(sha(ROOT/name)==pin,'referenced source/cache drift; never regenerate pins')
    pooled=summary['groups'][0]
    need(len(summary['groups'])==16 and {c['signature']:c['count'] for c in pooled['joint_MRCBcid'] if c['count']}==
         {'00000':973,'00001':17,'10000':30,'11100':4,'11110':51,'11111':5},'reviewed all-row mechanical pattern')
    coverage=validation['chapter_coverage']
    need(coverage==summary['chapter_coverage'] and coverage['node_count']==28 and coverage['input_chapter_rows']==36
         and len(coverage['extra_unused_chapter_ids'])==8 and coverage['missing_required_node_ids']==coverage['duplicate_chapter_ids']==[],
         'native chapter coverage, no fabricated/default chapter')
    for stem in ('fixed-controller-pure18-owned02','fixed-controller-cached02-owned'):
        base.owned(PREP/stem)
    need(sha(PREP/'fixed-controller-cached02-owned/receipt.json')==final['owned_receipt_sha256']
         and sha(PREP/'fixed-controller-pure18-owned02/receipt.json')==pure['owned_receipt_sha256'],'ROOT/owned receipts chain')
    old=read(PREP/'fixed-controller-cached01-outer/final.json')
    need(old['status']=='REJECTED_KEEP_PARTIAL_CACHED_CONTROLLER' and not (PREP/'fixed-controller-candidates-attempt01').exists(),
         'original admission failure preserved before outputs')
    failed=read(PREP/'fixed-controller-cached01-owned/receipt.json')
    need(failed['returncode']==1 and failed['accepted'] is False and failed['cleanup_accepted'] is True
         and failed['job_active_after_cleanup']==0 and failed['popen_handle_closed'] is True,'failure01 owned cleanup')
    for name,pin in failed['output_sha256'].items():
        need(name in ('stdout.log','stderr.log') and sha(PREP/'fixed-controller-cached01-owned'/name)==pin,'failure01 raw log identity')
    old14=read(PREP/'fixed-controller-pure14-capture01/final.json')
    need(old14['status']=='ACCEPTED_14_PURE_CONTROLLER_RULE_FIXTURES' and old14['counts']==dict(tests=14,failures=0,errors=0,skipped=0),
         'historical old14, not applied to source02')
    need(old14['source_before']==old14['source_after']==old14['source_expected'],'historical14 source chain')
    for name,pin in old14['source_expected'].items():
        need(sha(PREP/name)==pin,'historical01 source unchanged')
    base.owned(PREP/'fixed-controller-pure14-owned01')
    direct=read(PREP/'fixed_controller_candidates_pure01.json')
    direct_log=(PREP/'fixed_controller_candidates_pure01.log').read_text(encoding='utf-8')
    need(direct['returncode']==0 and base.finite(direct['elapsed_seconds'],10)
         and re.search(r'(?m)^Ran 14 tests in [0-9.]+s\s*$',direct_log) and re.search(r'(?m)^OK\s*$',direct_log),'standalone old14 receipt/log')
    need(sha(PREP/'pre-fixed-controller-chapter-coverage-fix01/inventory-before-and-copy-verification.json')==
         '42673927227f80b2e8160f0864e239228370662ca2f78cfb533ba506bacb7898','before/copy source preservation')
    need(sha(PREP/'pre-fixed-controller-chapter-coverage-fix01/post-preparation-verification02.json')==
         'c612cf89de05cb867112dd250d856e13ea85e06b44b17905d7f97c220bff08f1','post-preparation preservation proof')
    return dict(kind='POST_HOC_FIXED_CONTROLLER_SOURCE_RECONSTRUCTION_NOT_MEDIATION',paired_snapshots=1080,
        source_R_membership_exact=2160,source_CID_exact=2160,groups=16,new_independent_N=0,native_calls=0,
        balance_filtered_membership=4,changed_B_common_CID=51,same_B_changed_CID=17,
        failed01_admission_preserved=True,pure18_cases_are_software_not_scientific_N=True,
        cached02_prewrite_seconds=final['elapsed_before_receipt_seconds']),dict(validation['inputs_sha256'])


def selections():
    pairs=[(Path(__file__).resolve(),'archive_fixed_controller_candidates01.py')]
    for name in ('analyze_fixed_controller_candidates01.py','test_fixed_controller_candidates01.py',
        'rq1_fixed_controller_candidates_contract_20261109.md','run_fixed_controller_pure14_01.py','run_fixed_controller_cached01.py',
        'analyze_fixed_controller_candidates02.py','test_fixed_controller_candidates02.py',
        'rq1_fixed_controller_candidates_contract02_20261109.md','run_fixed_controller_pure18_02.py','run_fixed_controller_cached02.py',
        'fixed_controller_candidates_pure01.json','fixed_controller_candidates_pure01.log'):
        pairs.append((PREP/name,name))
    allowed={'before.json','final.json','GO.json','launch.json','ready.json','receipt.json','stdout.log','stderr.log','postwrite_rejection.json'}
    for folder in ('fixed-controller-pure14-capture01','fixed-controller-pure14-owned01',
        'fixed-controller-cached01-outer','fixed-controller-cached01-owned',
        'fixed-controller-pure18-capture02','fixed-controller-pure18-owned02',
        'fixed-controller-cached02-outer','fixed-controller-cached02-owned'):
        directory=PREP/folder
        base.need({p.name for p in directory.iterdir()}<=allowed,'explicit source/receipt raw files only')
        pairs.extend((p,folder+'__'+p.name) for p in sorted(directory.iterdir()))
    directory=PREP/'pre-fixed-controller-chapter-coverage-fix01'
    base.need({p.name for p in directory.iterdir()}=={
        'inventory-before-and-copy-verification.json','post-preparation-verification02.json',
        'analyze_fixed_controller_candidates01.py.before','test_fixed_controller_candidates01.py.before',
        'rq1_fixed_controller_candidates_contract_20261109.md.before','run_fixed_controller_pure14_01.py.before',
        'run_fixed_controller_cached01.py.before'},'exact chapter-correction preservation')
    pairs.extend((p,'chapter_correction__'+p.name) for p in sorted(directory.iterdir()))
    pairs.extend((DATA/n,n) for n in OUTPUTS)
    return pairs


def note():
    return '''# RQ1 — source-reconstructed C/B và khóa chọn CID

1080fixed snapshot pairs,2160ready memberships+CID exact;16groups giữ zero cells.4C-differences bị visits-balance loại khỏi B;51B khác/cùngCID;17cùngB/khácCID. Đây là source-local mechanical explanation, không directlylogged C/B, không calibration/causalmediation/learningbenefit hoặc independentN mới. Summary/eventflags giữ allcases/profiles/seeds, không chỉ favourable examples.

Giữ failed01admission+standalone14/owned14 trênsource01,18regression trênsource02 vàcached02 riêng. Nativechaptermap có28requirednodes/36entries/8unusedextra/0missing; strictkeysetanalysisguard cũ quá chặt, không phải datachapterbug. Không sửa bất kỳ nguyên source/input/rawfailure cũ. Unitcases không researchsamples; hai old14runs không28unique scientificcases.

Tham chiếu frozen source/cache theo SHA trong source_references.json, thuộc các immutablebundles trước; không copy lại gzip/notebooks/CSV/sharedproductioncode. Sourcefixedrunner đã recovered Git e4e6a262bddcdd3b6b6de8c1115ef0eb54b3240a; không gắn missingrunner của closedloop khác sang đây. report_snapshot.md giữ canonicalreport bytes; xem ../../reports/rq1_fixed_controller_candidates_20261109.md.

copy_inventory_before.json/copy_inventory.json kiểm source+copy trước/sau, verify_evidence_bundle chỉ integrity. execution.log là log archiver; unittest stdout/stderr,owned receipts vàrootcontrollers là rawexecution riêng. Closure không rerunanalysis/tests/native hoặc sửapublishedHTML/currentGate. Optionalreviewfiles chỉ copyopaque, không suy PASS từ sự có mặt.
'''


if __name__=='__main__':
    base.entry(RUN_ID,verify,selections,note,required_report=REPORT)
