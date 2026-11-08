"""ROOT dry/close only: accepted native03+cachedanalysis, no replay/calculation.

Small complete18gzip retained once; oldcache/failed63/benchmark24 referencedonly.
"""
from pathlib import Path
import re
import archive_edge_artifact_cross_ready01 as base

ROOT,PREP=base.ROOT,base.PREP
RUN_ID='rq1-prediction-mastery-trace-20261109-01'
REPORT=ROOT/'research_tracking/reports/rq1_native_mastery_reference_diagnostic_20261109.md'
DATA=PREP/'prediction-mastery-trace-attempt03'
ANALYSIS=PREP/'prediction-mastery-analysis-attempt01'
OUTER_SHA='81cf9dd9df724338d6c8d57e01be16b5d2120d27b9730c186b5eb539803e4594'
WORKER_SHA='891a69a3546599782e530d04c3fa29b53fd832f130399404fe159a5fcab2b178'
ANALYSIS_FINAL_SHA='b19806f8cc23c14c342b40eea18a69e42fe2ab69aae104bca5e6d8002de6c935'
PURE8_SHA='8ac3cc4dcda1f353833be580999f86abd2b90604f1ca81b834a56a8bf0877a6c'
OUTPUTS={'summary.json':'625095a6421b050f0592e9aecfa4767690ed863d3a5489a414a7b614fb3dde38',
    'event_flags.json':'7ed456f1da83c10012ff2cd7edc2973355d6d75c8df04ef0dd5e413caad98e8f',
    'validation.json':'13c90b544299362e56bbd7035c83063e12796d46679a4bbab62a6cdd8ca81f02',
    'result.json':'df0bdf446bc4e2418bd8cd614c1c9a3be777d4b3746613b1372f790b022b6fec'}
SOURCES=('prediction_mastery_trace_worker03.py','test_prediction_mastery_trace03.py',
    'run_prediction_mastery_trace03.py','prediction_mastery_trace_plan03.json','PREDICTION_MASTERY_TRACE_CONTRACT03.md',
    'prediction_mastery_revision03_budget.json','prediction_mastery_v03_source_equivalence01.json',
    'analyze_prediction_mastery_trace01.py','test_prediction_mastery_analysis01.py','prediction_mastery_analysis_plan01.json',
    'run_mastery_analysis01.py','crosscheck_native_mastery_gates01.py','native_mastery_gates_crosscheck01.json')
PROOF_PINS={'crosscheck_native_mastery_gates01.py':'c0ab73c965d67e4c8319ff04297187659a6c24235e1b6897e68daa4b5d01b8db',
    'native_mastery_gates_crosscheck01.json':'ca428a9c466a3e2a41700383e754e45e4494bbd5b90e7521dc891c69797cc573'}
PRIOR={'research_tracking/runs/rq1-prediction-mastery-trace-failures-20261109-01/manifest.json':'c36bf066b57fb6d38693628665db93533414651e5a03c38bc315253c242e88c5',
    'research_tracking/runs/mastery-observer-cost-engineering-20261109-01/manifest.json':'79dfecb73afd93677fc3ad42fee0a2ea5ea080f8b8f3b9c3ca7e7ae8bd7139e9'}


def verify():
    need,read,sha=base.need,base.read,base.sha
    need(sha(Path(base.__file__))=='188f96e30cf2434b1b7a32dea6dbd66da61bdaa3b3d1e0a15108d42425f86db7','commonarchiverpin')
    outer_path=PREP/'prediction-mastery-native-outer03/final.json'
    need(sha(outer_path)==OUTER_SHA and sha(DATA/'worker_run.json')==WORKER_SHA,'actualall2160acceptednative')
    outer,run=read(outer_path),read(DATA/'worker_run.json')
    need(outer['status']=='ACCEPTED_FIXED_HISTORY_MASTERY_TRACE_ONLY' and outer['errors']==[]
         and outer['source_before']==outer['source_after'] and outer['new_explicit_allocation_seconds']==300
         and base.finite(outer['elapsed_before_receipt_seconds'],290),'new300allocationacceptedallornothing')
    need(run['status']=='INNER_ALL2160_LEGACY_AND18_FINAL_FINGERPRINTS_EXACT_PENDING_ROOT' and run['errors']==[]
         and run['legacy_rows_exact']==2160 and run['profiler_restored'] is True
         and run['source_input_before']==run['source_input_after']==outer['source_before'],'workeradmission/sourceprepost')
    need(run['direct_attempts']==run['direct_returns'] and run['native_attempts']==run['native_returns']
         and all(run['native_attempts'][k]==n for k,n in dict(predict=6480,update=2160,select=2160,ready_set=4320,mastery_score=67060,is_mastered=284290).items())
         and run['direct_attempts']['constructor']==18,'actualcompletednativecounts,notreservations')
    expected={'dispatch.json','reservation.json','native_metadata.json','worker_run.json'}|{f'trace-{i:02d}.jsonl.gz' for i in range(1,19)}|{f'trajectory-{i}.json' for i in range(1,19)}
    need({p.name for p in DATA.iterdir()}==expected and len(expected)==40,'exact40complete nativefiles')
    need(set(run['outputs_sha256'])==expected-{'dispatch.json','worker_run.json'},'closednativehashvector')
    for n,pin in run['outputs_sha256'].items():need(sha(DATA/n)==pin,'nativeoutSHA')
    need(read(DATA/'native_metadata.json')==run['native_windows_metadata'] and run['native_windows_metadata']['phase_closed'] is True,'durablemetadataexactterminal')
    pointers=dict(outer['source_before'])
    for n,pin in pointers.items():need(sha(ROOT/n)==pin,'frozennativesource/inputreference')
    parity=read(ROOT/'research_tracking/runs/rq1-fixed-edge-set-contrast-20261108-01/parity.json')
    for i,row in enumerate(run['completed_trajectories'],1):
        need(row==read(DATA/f'trajectory-{i}.json') and row['trace_file']==f'trace-{i:02d}.jsonl.gz'
             and row['gzip_closed'] is True and row['trace_records']==row['exact_legacy_rows']==row['full_preview_exact']==120
             and sha(DATA/row['trace_file'])==row['trace_sha256'] and (DATA/row['trace_file']).stat().st_size==row['trace_bytes'],'18closedstreamprogress/hash/120admission')
        saved=next(r for r in parity['observed']['profile_state_rng_fingerprints'] if r['seed']==row['seed'] and r['profile']==row['profile'])
        need(row['initial_sha256']==saved['initial_policy_sha256'][row['variant']] and row['final_sha256']==saved['final_policy_sha256'][row['variant']],'18C13endpointparity')
    need(len(run['completed_trajectories'])==18,'all18notpartial')
    for folder in ('prediction-mastery-native-outer03','prediction-mastery-pure14-attempt03'):
        directory=PREP/folder
        need(not any((directory/n).exists() for n in ('failure.log','postwrite_rejection.json')),'noROOTlatefailure')
        receipt=base.owned(directory/'owned')
        need(sha(directory/'owned/receipt.json')==read(directory/'final.json')['owned_receipt_sha256'],'native/pureownedchain')
    p14=read(PREP/'prediction-mastery-pure14-attempt03/final.json')
    need(p14['status']=='ACCEPTED_14_SYNTHETIC_TRACE_FIXTURES' and p14['errors']==[]
         and p14['counts']==dict(tests=14,failures=0,errors=0,skipped=0),'actualsource03pure14notresearchN')
    need(sha(PREP/'mastery-analysis-pure01/result.json')==PURE8_SHA,'pure8receiptpin')
    pure=read(PREP/'mastery-analysis-pure01/result.json')
    need(pure['status']=='ACCEPTED_8_BOOLEAN_ANALYSIS_FIXTURES_NOT_SCIENCE' and pure['returncode']==0
         and pure['source_before']==pure['source_after'] and sha(PREP/'mastery-analysis-pure01/unittest.log')==pure['log_sha256'],'pure8source/log')
    need(re.search(r'Ran 8 tests in [0-9.]+s',(PREP/'mastery-analysis-pure01/unittest.log').read_text()) is not None,'real8lognotfabricatedowned')
    for n,pin in pure['source_before'].items():need(sha(PREP/n)==pin,'pure8boundsource')
    finalpath=PREP/'mastery-analysis-owned01/final.json';need(sha(finalpath)==ANALYSIS_FINAL_SHA,'actualanalysisouter')
    final=read(finalpath);base.owned(PREP/'mastery-analysis-owned01')
    need(final['status']=='ACCEPTED_CACHED_NATIVE_MASTERY_DIAGNOSTIC_NOT_CALIBRATION' and final['error'] is None
         and final['outputs_sha256']==OUTPUTS and final['accepted_trace_outer_sha256']==OUTER_SHA
         and base.finite(final['seconds'],10) and final['native_calls']==final['new_independent_N']==0,'cachedanalysisaccepted')
    need(not (PREP/'mastery-analysis-owned01/postwrite-rejection.json').exists(),'noanalysislatefailure')
    need({p.name for p in ANALYSIS.iterdir()}==set(OUTPUTS),'exact4analysisoutputs')
    for n,pin in OUTPUTS.items():need(sha(ANALYSIS/n)==pin,'analysisrawSHA')
    summary,valid,result=(read(ANALYSIS/n) for n in ('summary.json','validation.json','result.json'))
    need(result['outputs_sha256']=={n:h for n,h in OUTPUTS.items() if n!='result.json'},'inneranalysishashvector')
    need(valid['paired_events']==1080 and valid['arm_rows']==2160 and valid['paired_concept_snapshots']==30240
         and valid['groups']==16 and valid['per_concept_rows']==28 and valid['all18CRC'] is True
         and valid['all2160legacy_admission'] is True and valid['no_rows_dropped'] is True
         and valid['outer_sha256']==OUTER_SHA and valid['worker_run_sha256']==WORKER_SHA,'allanalysisdenominators/admission')
    for n,pin in valid['inputs_sha256'].items():need(sha(ROOT/n)==pin,'analysisinput/sourcepostbinding');pointers[n]=pin
    need(len(summary['groups'])==16 and len(summary['per_concept_pooled'])==28,'allgroups/conceptsretained')
    pooled=summary['groups'][0]
    need({c['signature']:c['count'] for c in pooled['joint_predicate_change_cells']}==
         {'000':26722,'001':0,'010':3428,'011':0,'100':0,'101':90,'110':0,'111':0},'all8zerosandobservedcells')
    need(pooled['M_any_events']==90 and pooled['M_concept_crossings']==90
         and pooled['pi_gate_any_events']==880 and pooled['theta_gate_any_events']==90,'eventversusconceptunitsseparate')
    need(pooled['raw_theta_full_minus_empty']['numerically_changed']==pooled['raw_pi_full_minus_empty']['numerically_changed']==20319
         and [r['count'] for r in pooled['queried_nativeM_vs_raw_reference']]==[1748,253,0,159]
         and [r['count'] for r in pooled['paired_query_Mchange_vs_raw_criterion_change']]==[1053,22,5,0],'predefinedrawreadoutsnotaccuracy')
    for n,pin in PROOF_PINS.items():need(sha(PREP/n)==pin,'independentrawproof/scriptpins')
    cross=read(PREP/'native_mastery_gates_crosscheck01.json')
    need(cross['status']=='INDEPENDENT_RAW_BOOLEAN_MECHANISM_RECONCILED' and cross['cells']=={'000':26722,'010':3428,'101':90}
         and cross['directions']=={'pi_only_empty_pass':3428,'M_full_true':90} and cross['raw_gzip_crc_verified']==18
         and cross['native_model_calls']==cross['oracle_reads']==cross['new_independent_N']==0,'independent18CRC/directionsnotmodelrun')
    for n,pin in PRIOR.items():need(sha(ROOT/n)==pin and read(ROOT/n)['status']=='completed','oldfailure63/benchmark24closedimmutable');pointers[n]=pin
    return dict(kind='DESCRIPTIVE_NATIVE_MASTERY_BOOLEAN_AND_RAW_REFERENCE_DIAGNOSTIC_REUSED_FIXED_HISTORY',
        paired_events=1080,queried_arm_rows=2160,paired_concept_time_snapshots=30240,
        Mset_disagreement_events=90,M_concept_time_classification_disagreements=90,temporal_learning_transitions_claimed=False,
        joint_predicate_change_cells={'000':26722,'001':0,'010':3428,'011':0,'100':0,'101':90,'110':0,'111':0},
        raw_readout_disagreement_rows=253,raw_readout_is_accuracy_or_calibration=False,
        actual_predict_calls=6480,actual_update_calls=2160,actual_native_S_calls=67060,actual_native_M_calls=284290,
        source03_boolean_fixtures=14,cached_boolean_fixtures=8,all18CRC_and2160legacy_admitted=True,
        native_root_terminal_observed_seconds=200.3490072,native_stored_outer_prewrite_seconds=outer['elapsed_before_receipt_seconds'],
        root_terminal_timing_origin='ROOT_MESSAGE_OBSERVATION_NOT_WORKER_GENERATED',analysis_outer_seconds=final['seconds'],
        new_explicit_native_allocation_seconds=300,old60_allocation_reopened=False,new_independent_N=0,
        calibration_accuracy_or_learning_benefit_claimed=False,source_fixed_runner_provenance='RECOVERED_GIT_e4e6a262bddcdd3b6b6de8c1115ef0eb54b3240a'),pointers


def selections():
    pairs=[(PREP/n,n) for n in SOURCES]
    pairs.extend((p,'native__'+p.name) for p in sorted(DATA.iterdir()))
    for folder,prefix in (('prediction-mastery-native-outer03','native_outer'),('prediction-mastery-pure14-attempt03','native_pure14'),('mastery-analysis-owned01','analysis_owned')):
        for p in sorted((PREP/folder).rglob('*')):
            if p.is_file():pairs.append((p,prefix+'__'+p.relative_to(PREP/folder).as_posix().replace('/','__')))
    pairs.extend((ANALYSIS/n,n) for n in OUTPUTS)
    pairs.extend((PREP/'mastery-analysis-pure01'/n,'analysis_pure8__'+n) for n in ('result.json','unittest.log'))
    pairs.append((Path(__file__).resolve(),Path(__file__).name))
    return pairs


def note():
    return '''# RQ1 — native mastery gates vàrawreference readouts, reusedhistory

Native03all2160legacy/fullpreview+18initial/finalC13fingerprints accepted;18closedgzip/120records mỗi stream vàindependentrawCRC18. Sourcefixedrunner recoveredGit e4e6a262…, không closedloop missingrunner branch. Same18policies/2160updates/6480predict,0teacher/newworld/NNoptimizer/oracle/newN. Actual14nativefixtures và8cachedbooleanfixtures giữriêng nhưsoftware, khôngresearchN.

30240cặpconcept–thờiđiểm:26722samegates,3428pi-gatedifference maskedbybothθbelow,90θ-gate/Mdifferences withbothpiPass.90Mseteventdisagreements và90concept-timedisagreements bằngnhauHERE, không90temporal learningtransitions; repeatedconceptdifference canpersist.000 khôngnumericstateequality.20319numericmarginals không chứngminhjointrecordidentity.253nativeM/rawcriteriondisagreements khôngaccuracy/calibration; queryM5/rawcriterion22 disjoint, khôngcùngbiếnpreview22. Fulltables16groups/28concepts preserved, no causal/benefit claim.

Oldfailed63/microbenchmark24 vàcached3240/notebook/Gate154 chỉsourceSHAreferences, khôngcopylạinguồn/historicaltraces. New18smallclosedgzip làacceptedtraceoutputs mới, giữmộtlần. NativeROOTterminal200.3490072s táchstoredprewrite200.0550102s; explicitnewallocation300 khônghiddenresetold60STOP56.3709122. Source/state/runtimeproofnoGPU/paid. Copyinventorypre/post+verifybundle làarchiveintegrity, khôngRQcomplete.

Report snapshot canonical ../../reports/rq1_native_mastery_reference_diagnostic_20261109.md; summary/validation/eventflags/independentcrosscheck giữexactbytes. execution.log làarchiver, rawowned/unittest/native/sourcefiles giữscope riêng. Khôngrerunmodel/analyzer/test khiđóngbundle.
'''


if __name__=='__main__':base.entry(RUN_ID,verify,selections,note,required_report=REPORT)
