"""ROOT-only dry/close: pure typed main9 core; no tests/data/model/selection execution."""
from pathlib import Path
import re
import archive_edge_artifact_cross_ready01 as base

ROOT,PREP=base.ROOT,base.PREP
RUN_ID='research-admission-core-engineering-20261109-01'
REPORT=ROOT/'research_tracking/reports/research_admission_core_readiness_20261109.md'
SOURCE='src/knowledge_tracing/research_admission.py'
TEST='tests/shared_kt/test_research_admission.py'
SOURCE_SHA='b8601da03a972834cfd2f5596ea6a6b9c5759437796b4f4b65720f7abc1a92f2'
TEST_SHA='d69dbf755a0f784a26b9eaf7cfc0b411ff035e191a8faecae770b4eb3bb4a2e3'
CONTROLLER_SHA='bc06608c53b401ad7a3172e9500ce1d255bb6e64e56143fcaa22506ee80ba327'
PACKET_SHA='654caf194c5fd838059b723dd53f4f0caeb30f9c7fa43ddfcc3851a4673eecda'
FINAL_SHA='9f5df5cc50f571d33ce9dac79d4c4283126f91c66460f51d863c64280e5b1485'
RECEIPT_SHA='da5bc00a1f3a7f46ad0614e7fa91ead6f9da50c4569245fd63888c246e7071a7'
PRIOR='research_tracking/runs/research-selection-kernel-engineering-20261109-01/manifest.json'
PRIOR_SHA='ac942db640bbcde951fb1b4398ac47bf8e7c1f609e694badaacf50640a800976'
CAPTURE=PREP/'research-admission-pure-capture01'
OWNED=PREP/'research-admission-pure-owned01'
CAPTURE_FILES=('before.json','cold-canary.json','worker-result.json','final.json')
OWNED_FILES=('GO.json','launch.json','ready.json','receipt.json','stdout.log','stderr.log')


def verify():
    need,sha,read=base.need,base.sha,base.read
    need(sha(Path(base.__file__))=='188f96e30cf2434b1b7a32dea6dbd66da61bdaa3b3d1e0a15108d42425f86db7','common archive helper pin')
    need(sha(ROOT/SOURCE)==SOURCE_SHA and sha(ROOT/TEST)==TEST_SHA,'actual tested new core/test source')
    need(sha(PREP/'check_research_admission01.py')==CONTROLLER_SHA
         and sha(PREP/'research_admission_pure_packet01.json')==PACKET_SHA,'reviewed controller/packet')
    need(sha(CAPTURE/'final.json')==FINAL_SHA and sha(OWNED/'receipt.json')==RECEIPT_SHA,'actual terminal/owned pins')
    need({p.name for p in CAPTURE.iterdir()}==set(CAPTURE_FILES)
         and {p.name for p in OWNED.iterdir()}==set(OWNED_FILES),'exact closed pure files/no postwrite failure')
    final,worker,canary=(read(CAPTURE/name) for name in ('final.json','worker-result.json','cold-canary.json'))
    receipt=base.owned(OWNED)
    need(final['status']=='ACCEPTED_8_MANUFACTURED_ADMISSION_CORE_FIXTURES' and final['errors']==[]
         and final['counts']==dict(tests=8,failures=0,errors=0,skipped=0)
         and final['source_before']==final['source_after']==final['source_expected']==worker['source_after']
         and final['controller_sha256']==CONTROLLER_SHA and final['owned_receipt_sha256']==RECEIPT_SHA
         and final['cap_seconds']==30 and base.finite(final['elapsed_before_receipt_seconds'],30),
         'actual8 complete/source stable/whole cap')
    need(worker['unittest_returncode']==0 and worker['unittest_raw_exit_type']=='int'
         and type(worker['unittest_raw_exit_value']) is int and worker['unittest_raw_exit_value']==0
         and worker['denied_attempts']==worker['scientific_modules_present']==[]
         and all(type(worker[k]) is int and worker[k]==0 for k in ('model_calls','optimizer_calls','real_data_rows_opened')),
         'actual raw exit and manufactured-only scope')
    need(canary['status']=='STDLIB_ADMISSION_COLD_IMPORT_ONLY' and canary['scientific_modules_present']==[]
         and canary['required_candidates']==9 and canary['common_models']==5
         and canary['nine_candidate_admission_performed'] is False and canary['external_freeze_authority'] is False
         and canary['population_scheme']=='model-neutral-selection-K-y-jsonl-v1'
         and Path(canary['prefix'])==ROOT/'.venv' and canary['python_implementation']=='cpython',
         'cold actual interpreter, no artifact admission/authority')
    need(receipt['worker_sha256']==CONTROLLER_SHA and receipt['cleanup_reserve_seconds']==2
         and base.finite(receipt['elapsed_seconds'],30),'exact owned source/allocation')
    for name,pin in final['output_sha256'].items():need(sha(CAPTURE/name)==pin,'worker outputs SHA')
    stderr=(OWNED/'stderr.log').read_text(encoding='utf-8')
    cases=[line for line in stderr.splitlines() if line.startswith('test_') and ' ... ' in line]
    need(len(cases)==8 and all(line.endswith('... ok') for line in cases)
         and len(re.findall(r'(?m)^Ran 8 tests in [0-9.]+s\s*$',stderr))==1
         and re.search(r'(?m)^OK\s*$',stderr) and '(skipped=' not in stderr,'actual8/no skip unittest')
    pointers={name:pin for name,pin in final['source_expected'].items()}
    packet=read(PREP/'research_admission_pure_packet01.json')
    need(packet['logical_unittest_methods']==8 and packet['whole_cap_seconds']==30
         and packet['candidate_count']==9 and packet['common_model_count']==5
         and packet['disk_terminal_verification_implemented'] is False
         and packet['external_freeze_implemented'] is False,'review packet pure-only missing producer explicit')
    for row in packet['source_files']:
        need(sha(ROOT/row['path'])==row['sha256'] and (ROOT/row['path']).stat().st_size==row['size_bytes'],'packet exact source SHA/size')
        pointers[row['path']]=row['sha256']
    for name,pin in pointers.items():need(sha(ROOT/name)==pin,'source reference pre-copy')
    need(sha(ROOT/PRIOR)==PRIOR_SHA and read(ROOT/PRIOR)['status']=='completed'
         and len(read(ROOT/PRIOR)['outputs_sha256'])==50,'closed existing statistical kernel referenced only')
    pointers[PRIOR]=PRIOR_SHA;pointers[base.HELPER]=sha(ROOT/base.HELPER)
    return dict(kind='PURE_TYPED_MAIN_NINE_CONSISTENCY_ACCUMULATOR_NOT_FILE_ADMISSION',
        tests=8,failures=0,errors=0,skipped=0,manufactured_fixture_keys=4,manufactured_fixture_learners=3,
        candidate_count=9,common_support_models=5,actual_model_calls=0,actual_optimizer_calls=0,actual_corpus_rows=0,
        sorted_K_is_statistical_view_not_logged_training_chronology=True,
        actual_nine_terminal_files_verified=False,actual_external_freeze=False,main_selected_only_producer_missing=True,
        selected_only_claim_kind_is_future_blueprint_not_pilot_compatibility=True,
        owned_cleanup_accepted=True,actual_raw_exit_type='int',actual_raw_exit_value=0,
        stored_prewrite_seconds=final['elapsed_before_receipt_seconds'],whole_cap_seconds=30,
        old_kernel_reexecuted=False,previous_kernel_manifest_sha256=PRIOR_SHA,
        current_runtime_fullGate_or_researchfit_granted=False),pointers


def selections():
    pairs=[(ROOT/SOURCE,'source__research_admission.py'),(ROOT/TEST,'test__research_admission.py')]
    pairs.extend((PREP/name,name) for name in ('check_research_admission01.py','research_admission_pure_packet01.json','MAIN_NINE_ADMISSION_REVIEW01.md'))
    pairs.extend((CAPTURE/name,'capture__'+name) for name in CAPTURE_FILES)
    pairs.extend((OWNED/name,'owned__'+name) for name in OWNED_FILES)
    pairs.append((Path(__file__).resolve(),Path(__file__).name))
    return pairs


def note():
    return '''# GRAPH12/13 — main9 consistency core, pure manufactured evidence

Actual8PASS/0FES/coldstdlib+ownedJobcleanup0, noNumPy/Torch/model/optimizer/corpus/realexports. Sourceb860/testd69 only. Counter4keys/3learners/9candidateIDs làmanufacturedfixture, khôngresearchN. Existingkernel50/859617f chỉSHAreference, khôngrerun/copyoldbundle.

Core nhậncaller-providedtypedclaims vàsynchronized9K/yrows, kiểmcoveragefull/commonU5, giữall9comparisoncoverage vàperlearnercounts; buffer5losslistscurrentlearner→fsum→existingtypedstatistics. NOT_FILE_ADMISSION; filebytes/nineactualterminal/externalfreezeauthorityFalse. Missingmainselected-onlyproducer/trusteddiskdriver/externalfreeze rõràng; khôngpromoteoldA0pilot/graph-offA3/syntheticweights thànhfitted researchcertificate.

CanonicalKsort làstatisticalview, khôngchronologicaltraining. Rawexports giữloggedorder; futuredriverphảisortviewriêngvàverifyexpectedF/actualbytes/labels/source/phase/caps/authority trướcmainselection. Khôngrewriteprefix/trainingorder. ClaimSHA/status khônglàchứngthựcfile; no winner/refit/paid/GPU/RQcompletion.

Source/inputSHA trước/sau,coldcanary,8case stderr,ownedraw/controller/packet vàcopyinventory giữexactbytes. execution.log làarchiver; closureverify chỉarchiveintegrity. Khôngexecutetest/kernel/bootstrap/model khiarchive. Report ../../reports/research_admission_core_readiness_20261109.md đượcchuẩn bịtrướcclosure; actualmanifest/index xácnhậnclosure riêng.
'''


if __name__=='__main__':base.entry(RUN_ID,verify,selections,note,required_report=REPORT)
