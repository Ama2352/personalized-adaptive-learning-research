"""ROOT dry/closure of accepted manufacturedobserver benchmark; no rerun/native."""
from pathlib import Path
import math
import archive_edge_artifact_cross_ready01 as base

ROOT,PREP=base.ROOT,base.PREP
RUN_ID='mastery-observer-cost-engineering-20261109-01'
REPORT=ROOT/'research_tracking/reports/mastery_observer_cost_microbenchmark_20261109.md'
DATA=PREP/'mastery-observer-microbenchmark-attempt01'
SOURCE='benchmark_mastery_observer_overhead01.py'
PLAN='mastery_observer_microbenchmark_plan01.json'
SCHEMA='mastery_observer_microbenchmark_schema01.json'
PINS={SOURCE:'9e54b86078b5150c565f43d3f30447ecfae2999a3287f381cf3ed6326875f00c',
    PLAN:'6a1fa43169547f35e62000e7cdd8ed50d3cbbf01cbe2c84a16e8d9668424c97a',
    SCHEMA:'6b3010b7bb37c9969ea98f4695d2b3c9afb553cf221e8fe35533aa33ecddc847'}
FINAL_SHA='1764df8da9487d8d225a72c3865ba70981a8aae671794a6da590fa5d6abc178c'
RESULT_SHA='4cd0b7a20f212e2a94f4b60c0f8815a3831f36e5fa5b9ed46977cb18792e02dc'


def verify():
    need,read,sha=base.need,base.read,base.sha
    need(sha(Path(base.__file__))=='188f96e30cf2434b1b7a32dea6dbd66da61bdaa3b3d1e0a15108d42425f86db7','common archivehelper')
    need(all(sha(PREP/n)==h for n,h in PINS.items()),'exact executed source/plan/schema')
    need(sha(DATA/'final.json')==FINAL_SHA and sha(DATA/'worker_result.json')==RESULT_SHA,'actual final/result source-bound')
    final,result,plan,schema=(read(p) for p in (DATA/'final.json',DATA/'worker_result.json',PREP/PLAN,PREP/SCHEMA))
    need(final['status']=='ACCEPTED_MANUFACTURED_OBSERVER_COST_ONLY' and final['error'] is None
         and base.finite(final['elapsed_before_receipt_seconds'],5) and final['cap_seconds']==5,'actual ROOT operationalacceptance')
    need(result['status']=='OPERATIONAL_MANUFACTURED_BENCHMARK_PENDING_ROOT_POSTWRITE' and result['error'] is None
         and result['profiler_restored'] is True and result['shape']==[28,38] and result['memory_dtype']=='float32'
         and result['memory_bytes_per_concept']==152 and result['native_schema_coverage_claimed'] is False,'manufactured geometry/limits')
    need(final['plan_sha256']==result['plan_sha256']==PINS[PLAN]
         and final['source_sha256']==result['source_sha256']==plan['worker_sha256']==PINS[SOURCE]
         and plan['schema_mapping_sha256']==PINS[SCHEMA],'sourcechain')
    need(all(result[k]==0 for k in ('model_calls','teacher_calls','rng_calls','actual_data_reads','new_independent_N'))
         and result['prior_native60_allocation_reopened'] is False and final['prior_native_allocation_reopened'] is False
         and final['prior_native_charged_seconds']==plan['prior_native_60_charged_seconds']==56.3709122,'separate allocation/no science')
    need(plan['representation_iterations']==64 and plan['dummy_iterations']==4000 and plan['whole_seconds']==5
         and plan['native_retry_authorized'] is False,'finite originalplan')
    r=result['results'];proof=r['fixtures']
    need(proof['equal_state'] is True and proof['mutation_count']==len(proof['mutation_cases'])==19
         and all(c['legacy_detected'] is True and c['view_detected'] is True for c in proof['mutation_cases'])
         and proof['native_schema_coverage_claimed'] is False,'19mutations onlyfabricatedcoverage')
    for name in ('original_4jsonsha','immutable_4views'):
        t=r[name];need(t['iterations']==64 and t['full_state_representation_calls']==256 and t['equalities']==64
             and base.finite(t['seconds'],5) and t['seconds']>0,'equal fixed256representations')
    need(r['original_over_view_seconds_ratio']==r['original_4jsonsha']['seconds']/r['immutable_4views']['seconds'],'actual ratio algebra')
    for name in ('global_profile','direct_ledger'):
        t=r[name];need(t['iterations']==4000 and t['dummy_calls']==t['dummy_returns']==dict(branch=4000,leaf=8000)
             and t['checksum']==16008000 and t['profiler_restored'] is True and 0<t['seconds']<5,'same12k dummycalls/checksum')
    need(r['global_over_direct_seconds_ratio']==r['global_profile']['seconds']/r['direct_ledger']['seconds']
         and r['ratio_scope']=='THIS_FIXED_MANUFACTURED_OBSERVER_WORKLOAD_ONLY_NOT_NATIVE_RUNTIME_OR_COVERAGE','ratio scope restricted')
    owned=base.owned(DATA/'owned')
    need(sha(DATA/'owned/receipt.json')==final['owned_receipt_sha256'] and sha(DATA/'worker_result.json')==final['result_sha256'],
         'ROOT/owned/result identity')
    need(not any((DATA/n).exists() for n in ('postwrite_rejection.json','worker_postwrite_rejection.json','worker_failure.log','outer_failure.log')),
         'no late rejection overrides')
    expected={'dispatch.json','worker_result.json','final.json'}|{'owned/'+n for n in ('GO.json','launch.json','ready.json','receipt.json','stderr.log','stdout.log')}
    need({p.relative_to(DATA).as_posix() for p in DATA.rglob('*') if p.is_file()}==expected,'exact9 rawfiles')
    need(set(final['artifacts_sha256'])==expected-{'final.json'},'all8 priorrawhashes')
    for name,pin in final['artifacts_sha256'].items():need(sha(DATA/name)==pin,'rawoutputhash')
    need(schema['runtime_source_artifact_reads'] is False and schema['native_coverage_or_speed_forecast_claimed'] is False
         and schema['geometry']['memory_length']==38 and schema['geometry']['native_initial_dtype']=='np.float32'
         and len(schema['memory_state_fields'])==10,'sourcefieldmapping explicitlynotnativecoverage')
    old=plan['failure_archive_unchanged_refs']
    need(sha(ROOT/old['archiver_path'])==old['archiver_sha256'] and sha(ROOT/old['report_path'])==old['report_sha256'],'old63 failure batch frozen')
    source=schema['original_memory_state_source'];geometry=schema['geometry_source']
    pointers={source['path']:source['sha256'],geometry['loader']:geometry['loader_sha256'],
        'scripts/research/windows_owned_worker.py':plan['owned_helper_sha256'],
        old['archiver_path']:old['archiver_sha256'],old['report_path']:old['report_sha256']}
    need(all(sha(ROOT/n)==h for n,h in pointers.items()),'source-only references unchanged')
    return dict(kind='ACCEPTED_OPERATIONAL_MANUFACTURED_OBSERVER_MICROBENCHMARK_NOT_NATIVE_GAM',
        cap_seconds=5,caller_prewrite_seconds=final['elapsed_before_receipt_seconds'],
        root_terminal_observed_seconds=1.2128429,root_terminal_timing_source='ROOT_MESSAGE_OBSERVATION_NOT_WORKER_GENERATED',
        manufactured_states=28,manufactured_memory_length=38,manufactured_memory_dtype='float32',mutation_fixtures=19,
        json_seconds=r['original_4jsonsha']['seconds'],view_seconds=r['immutable_4views']['seconds'],
        json_over_view_ratio=r['original_over_view_seconds_ratio'],profile_seconds=r['global_profile']['seconds'],
        direct_seconds=r['direct_ledger']['seconds'],profile_over_direct_ratio=r['global_over_direct_seconds_ratio'],
        ratios_scope='FIXED_FABRICATED_WORKLOAD_ONLY_NO_NATIVE_FORECAST',native_schema_coverage_certified=False,
        native_model_calls=0,teacher_calls=0,research_rng_draws=0,data_reads=0,new_independent_N=0,
        old_native_charged_seconds=56.3709122,old_native_batch_reopened=False),pointers


def selections():
    pairs=[(PREP/n,n) for n in PINS]
    pairs.extend((p,'raw__'+p.relative_to(DATA).as_posix().replace('/','__')) for p in sorted(DATA.rglob('*')) if p.is_file())
    pairs.append((Path(__file__).resolve(),Path(__file__).name))
    return pairs


def note():
    return '''# Chi phí observer trên state giả — engineering only

Accepted operational microbenchmark≤5s,19singlefieldmutations/equalstate/signedzero và12k dummycalls/ledgerchecksum mỗiarm. JSON/view ratio1.2684 vàglobalprofile/direct ratio8.9735 chỉ thuộcfixture cố định, không nóiGAM nhanh9lần hoặc JSONlàduynhất nguyênnhân timeout. Không NumPy/native/model/data/oracle/teacher/RNGnghiên cứu. Ownedlaunchnonce là entropy vận hành riêng, không experimentRNG.

Stategeometry map nguồn38float32/152B×28; fakebytes đãmaterialize, không đo NumPy.tobytes/Pandas/native-schema/type overhead. Nativecoverage=false; tươnglai phải source/schema review+all2160legacy/fullpreview+18initial/finalC13fingerprints trước diễn giải. Unknownframe early-return không được âmthầmbỏ RNGguard. Report trìnhbày đềxuất source-only, chưa sourcefix/native.

Originalnative60 vẫnclosed56.3709122/60; benchmark riêng không cấp quyềnretry. Gói failure63/report cũ nguyênbytes. Closure là integrity/archive của benchmarkengineering, không RQcomplete/calibration/modelbenefit/currentGate. CopySHApre/post+source refs; không copy lại notebooks/CSV/cache/154nguồn. Canonicalreport: ../../reports/mastery_observer_cost_microbenchmark_20261109.md.
'''


if __name__=='__main__':
    base.entry(RUN_ID,verify,selections,note,required_report=REPORT)
