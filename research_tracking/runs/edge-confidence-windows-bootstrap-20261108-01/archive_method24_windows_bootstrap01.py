"""Dry/closure có ROOT approval; chỉ copy/hash, không rerun tests/solver/native.

Native attachment chỉ đọc khi caller cung cấp exact outer-run SHA sau terminal.
Giữ nguyên5exports lớn tại run gốc, lưu đủ14SHA/size pointers trước/sau.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[4]
PREP=ROOT/'artifacts/akt/local-tests/akt-research-runner-20261108-01'
RUN_ID='edge-confidence-windows-bootstrap-20261108-01'
HELPER=ROOT/'src/knowledge_tracing/evidence.py'
HELPER_SHA='414e3d834c46d081c7d9c05beff17a3e2d9c479a0e121394aabe321929235e49'
CURRENT={'method24_worker01.py':'ffb0c5307f5130164ac59f2e70959cf49505b3b59bc8e1afc29dca6f08126505',
 'run_method24_native01.py':'983aab01b53e05df14e814c742c303e2dbfee1dd6e6ced886ff4e2d699391993',
 'test_method24_native01.py':'e3b1cd60743a11d9f5221ced0e0b8a99c4e0de3a5dc1d05f64e345a008c5a409',
 'method24_config01.json':'d2a9d8d682c01fa423eade202655d9b2b5aa121bf69abc879de2ca050f3a440c',
 'method24_runtime_profile01.json':'c008d6a734c53152b33ad4b6a99a3657528c33c71606dd265dc4b61ef8387bc8'}
REQUEST_SHA='4f1b2dd69441eabd5995665e013cbefcc5378d3ab153ceb9581fd9757fbbfc42'
ROOT_REVIEW_SHA='8e10b8baccd07b826d69166afb9ed486d59373a2d506434f66c310b45d1e85e5'
TERMINAL_OBSERVATION_SHA='784984218a15ca81ce8ef0468db1d92526db4d679a223d7ac621d6ecc6d5e805'
SOURCE11=('method24_worker01.py','run_method24_native01.py')
PRODUCTION9=('scripts/research/windows_owned_worker.py','src/knowledge_tracing/__init__.py',
 'src/knowledge_tracing/akt/__init__.py','src/knowledge_tracing/akt/resources.py','src/knowledge_tracing/edge_confidence.py',
 'src/knowledge_tracing/simulator_bridge.py','src/knowledge_tracing/simulator_corpus_reader.py',
 'src/knowledge_tracing/simulator_data.py','src/knowledge_tracing/simulator_research_data.py')
LARGE=('fit-ledger.jsonl','baseline-oof.csv','edge-oof.csv','learner-deltas.csv','edges.jsonl')
NATIVE_SMALL=('reservation.json','runtime.json','resources.json','input-source-inventory.json','recipe.json',
 'folds.json','graph.json','worker_result.json','DONE.json')
GENERATED=('README.md','execution.log','copy_inventory_before.json','copy_inventory.json','frozen_acceptance.json',
 'native_artifact_inventory.json','closure_review.json','raw_log_paths.txt')


def need(ok,message):
    if not ok:raise ValueError(message)


def physical(path):
    path=path.absolute();need(path.is_relative_to(ROOT),'workspace only')
    current=ROOT
    for part in path.relative_to(ROOT).parts:
        current/=part
        need(not current.is_symlink() and not getattr(current,'is_junction',lambda:False)(),'path alias')
    need(path.resolve()==path,'physical path required')
    return path


def sha(path,cap=4*1024**2):
    path=physical(path);need(path.is_file() and path.stat().st_size<=cap,'bounded regular evidence file')
    h=hashlib.sha256();count=0
    with path.open('rb') as stream:
        while block:=stream.read(1024**2):
            count+=len(block);need(count<=cap,'stream byte cap');h.update(block)
    need(count==path.stat().st_size,'size drift')
    return h.hexdigest()


def read(path):return json.loads(path.read_bytes())


def valid_sha(value):
    need(type(value) is str and len(value)==64 and all(c in '0123456789abcdef' for c in value),'SHA64 required')
    return value


def native_terminal_inventory(expected_run_sha,terminal_receipt=None):
    """Chỉ gọi SAU ROOT xác nhận terminal; không đọc/parse5exports lớn."""
    if expected_run_sha is None:
        need(terminal_receipt is None,'native terminal receipt requires explicit runSHA')
        return dict(status='NOT_ATTACHED_NO_NATIVE_FILES_READ',artifacts=[]),[]
    expected_run_sha=valid_sha(expected_run_sha)
    need(sha(PREP/'method24_run01.json')==expected_run_sha,'native outer-run pin')
    need(sha(PREP/'method24_request01.json')==REQUEST_SHA and sha(PREP/'method24_root_dispatch_review01.json')==ROOT_REVIEW_SHA,'request/ROOT review pin')
    run=read(PREP/'method24_run01.json');request=read(PREP/'method24_request01.json');review=read(PREP/'method24_root_dispatch_review01.json')
    need(run['status']=='ACCEPTED_CONDITIONAL_TRAIN_SURROGATE_NOT_EDGE_TRUTH' and run['error'] is None
         and run['request_sha256']==REQUEST_SHA and run['actual_solver_calls']==run['reserved_solver_calls']==2352
         and run['owned_cleanup_accepted'] is True,'native outer accepted scope/counts')
    need(type(run['elapsed_before_receipt_seconds']) in (int,float) and math.isfinite(run['elapsed_before_receipt_seconds'])
         and 0<=run['elapsed_before_receipt_seconds']<=120,'pre-receipt clock only')
    need(not (PREP/'method24_postbudget_failure01.json').exists() and not (PREP/'method24_outer_failure01.log').exists(),'outer rejection override')
    source_paths={(PREP/n).relative_to(ROOT).as_posix() for n in SOURCE11}|set(PRODUCTION9)
    need(request['source_count']==11 and set(request['source_sha256'])==source_paths
         and review['source_sha256']==request['source_sha256'] and review['request_sha256']==REQUEST_SHA,'source11/review binding')
    for rel,pin in request['source_sha256'].items():need(sha(ROOT/rel)==pin,'source11 drift: '+rel)
    directory=physical(PREP/'method24-native01')
    names=set(NATIVE_SMALL)|set(LARGE)
    need({p.name for p in directory.iterdir()}==names and set(run['artifacts'])==names,'exact14native files; no failure/extra')
    done=read(directory/'DONE.json');result=read(directory/'worker_result.json');resources=read(directory/'resources.json')
    need(done['status']=='COMPLETE_METHOD24_PENDING_OUTER_ACCEPTANCE' and done['request_sha256']==REQUEST_SHA
         and set(done['files_sha256'])==names-{'DONE.json'},'DONE13 hashes')
    artifacts=[]
    for name in sorted(names):
        path=directory/name;expected=run['artifacts'][name]
        need(path.stat().st_size==expected['bytes'] and sha(path,100663296 if name=='edge-oof.csv' else 134217728)==expected['sha256'],'native artifact SHA/size: '+name)
        if name!='DONE.json':need(done['files_sha256'][name]==expected['sha256'],'DONE/outer artifact disagreement')
        artifacts.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=expected['sha256'],bytes=expected['bytes'],
            copied_to_bundle=name in NATIVE_SMALL,retained_original_ignored=name in LARGE))
    need(sum(v['bytes'] for v in artifacts)==69519761,'actual14total unchanged')
    need(result['processed_fit_slots']==result['actual_solver_calls']==2352 and result['oof_rows']==272160
         and result['edge_summaries']==result['supported_edges']==756 and result['graph_edges']==31
         and result['graph_status']=='SUPPORTED_DAG' and result['request_sha256']==REQUEST_SHA,'native counts/result scope')
    need(result['teacher_calls']==result['neural_optimizer_steps']==result['modal_spend_usd']==0,'no teacher/NN/spend')
    need(resources['observed_peak_rss_bytes']<=536870912 and resources['observed_minimum_available_ram_bytes']>=1073741824,'native resources')
    owner=read(PREP/'method24_owned_receipt01.json')
    need(owner['accepted'] is True and owner['cleanup_accepted'] is True and owner['job_active_after_cleanup']==0
         and owner['popen_handle_closed'] is True and owner['returncode']==owner['worker_returncode_before_cleanup']==0
         and owner['actual_worker_in_job_before_GO'] is True,'native ownedJob acceptance')
    need(result['owner']['worker']==owner['actual_worker'] and result['owner']['parent_owner']==owner['parent'],'native actual owner')
    runtime=read(directory/'runtime.json');m=runtime['native_windows_metadata'];counts=runtime['process_counts']
    need(m['phase_closed'] is True and m['outside_phase_popen_attempts']==m['blocked_bootstrap_attempts']==0
         and type(m['helper_calls']) is int and 0<=m['helper_calls']<=3,'OS metadata phase closure')
    need(counts==dict(metadata_bootstrap_helpers=m['helper_calls'],fit_phase_popen_attempts=0,
         outside_metadata_phase_popen_attempts=0,overall_permitted_worker_child_popen_events=m['helper_calls']),'honest worker Popen counts')
    need(runtime['profile_sha256']==CURRENT['method24_runtime_profile01.json'] and
         all(p['num_threads']==1 for p in runtime['threadpools']),'runtime profile/thread1')
    graph=read(directory/'graph.json')
    need(graph['status']=='SUPPORTED_DAG' and len(graph['edges'])==31,'actual learned graph output')
    info=dict(status='NATIVE_OUTER_ACCEPTED_RECEIPTS_HASH_VERIFIED',request_sha256=REQUEST_SHA,run_sha256=expected_run_sha,
        source11_sha256=request['source_sha256'],artifacts=artifacts,large_exports_copied=False,
        elapsed_before_receipt_seconds=run['elapsed_before_receipt_seconds'],
        elapsed_scope='native outer pre-receipt only; do not invent final45.169seconds from this field',
        observed_peak_rss_bytes=resources['observed_peak_rss_bytes'],observed_minimum_available_ram_bytes=resources['observed_minimum_available_ram_bytes'],
        actual_solver_calls=2352,processed_fit_slots=2352,oof_rows=272160,supported_edges=756,dag_edges=31,
        positive_supported_candidates=graph['considered_positive_supported'],cycle_rejections=len(graph['rejected_cycles']),
        metadata_helpers=m['helper_calls'],fit_phase_popen_attempts=0,teacher_calls=0,neural_optimizer_steps=0,
        root_terminal_receipt=None)
    extra=[]
    if terminal_receipt is not None:
        terminal_receipt=physical(terminal_receipt)
        need(terminal_receipt==PREP/'method24_terminal_observation01.json'
             and sha(terminal_receipt)==TERMINAL_OBSERVATION_SHA,'exact ROOT terminal observation path/pin')
        terminal=read(terminal_receipt)
        need(type(terminal) is dict and set(terminal)=={'kind','tool_session_id','observed_exit_code','stdout_json','scope_vi'}
             and terminal['kind']=='ROOT_OBSERVATION_OF_TOOL_TERMINAL_NOT_WORKER_GENERATED'
             and type(terminal['tool_session_id']) is int and terminal['tool_session_id']==51067
             and type(terminal['observed_exit_code']) is int and terminal['observed_exit_code']==0,
             'ROOT observed tool terminal schema/RC0; not worker-generated evidence')
        observed=terminal['stdout_json']
        need(type(observed) is dict and set(observed)=={'status','elapsed_seconds','error','run_sha256'}
             and observed['status']==run['status'] and observed['error'] is None
             and observed['run_sha256']==expected_run_sha and run['request_sha256']==REQUEST_SHA,
             'ROOT stdout outer-run binding; request identity comes from pinned outer run')
        elapsed=observed['elapsed_seconds']
        need(type(elapsed) in (int,float) and math.isfinite(elapsed)
             and run['elapsed_before_receipt_seconds']<=elapsed<=120,'ROOT observed final elapsed')
        info['root_terminal_receipt']=dict(path=terminal_receipt.relative_to(ROOT).as_posix(),sha256=sha(terminal_receipt),
            kind=terminal['kind'],tool_session_id=terminal['tool_session_id'],observed_exit_code=terminal['observed_exit_code'],
            observed_stdout_elapsed_seconds=elapsed,outer_run_sha256=expected_run_sha,
            request_sha256_from_pinned_outer=run['request_sha256'],worker_generated=False)
        extra.append((terminal_receipt,'native__root_terminal_receipt.json'))
    pairs=[(PREP/n,'native__'+n) for n in ('method24_run01.json','method24_owned_receipt01.json','method24_dispatch01.json')]
    pairs += [(directory/n,'native__'+n) for n in NATIVE_SMALL]
    pairs += [(PREP/'method24-owned01'/n,'native_owned__'+n) for n in ('GO.json','launch.json','ready.json','stdout.log','stderr.log')]
    pairs += [(ROOT/rel,'native_source__'+rel.replace('/','__')) for rel in sorted(source_paths) if ROOT/rel not in {PREP/n for n in SOURCE11}]
    return info,pairs+extra


def inventory(args):
    need(sha(HELPER)==HELPER_SHA,'evidence helper drift')
    for name,pin in CURRENT.items():need(sha(PREP/name)==pin,'final source/config/profile drift')
    pairs=[(PREP/n,'final__'+n) for n in CURRENT]
    pairs += [(Path(__file__).resolve(),'archive_method24_windows_bootstrap01.py'),(HELPER,'evidence_helper.py')]
    pairs += [(ROOT/'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md','protocol21_snapshot.md'),
        (ROOT/'research_tracking/reports/edge_confidence_method24_plan_20261108.md','method24_plan_snapshot.md'),
        (ROOT/'research_tracking/reports/edge_confidence_method24_plan_20261108.sources.json','method24_plan_sources.json')]
    acceptance={'kind':'WINDOWS_METADATA_BOOTSTRAP_ENGINEERING_WITH_OPTIONAL_NATIVE_TRAIN_SURROGATE',
        'pure_cases_separate':{},'smoke01_failed_preserved':True,'smoke02_actual_solver_fits':2,
        'new_neural_optimizer_steps':0,'scope_vi':'Không cộng43+45thànhindependent tests;2ABI fits khác2352nativefits; no RQ/causal/edge-truth/NN efficacy claim.'}
    for label,number,snapshot in [('03',43,'pre-late-counter-fix01'),('04',45,None)]:
        folder=PREP/('method24-pure'+label);owned=PREP/('method24-pure'+label+'-owned')
        final=read(owned/'final.json');result=read(folder/'result.json')
        need(final['status']=='ACCEPTED_PURE_ONLY_NOT_NATIVE_FIT' and final['counts']==dict(tests=number,failures=0,errors=0,skipped=0)
             and 0<=final['elapsed_seconds']<=150 and final['solver_fits']==final['model_calls']==0,'pure scope/count/cap')
        suite=ET.parse(folder/'junit.xml').getroot()
        need({k:sum(int(s.get(k,'0')) for s in suite.iter('testsuite')) for k in ('tests','failures','errors','skipped')}==final['counts'],'pure JUnit counts')
        need(result['source_before']==result['source_after'] and not result['actual_subprocess_attempts'] and not result['heavy_modules_loaded'],'pure source/purity')
        for name,pin in result['source_before'].items():
            path=PREP/snapshot/(name+'.before') if snapshot and name.endswith('.py') else PREP/name
            need(sha(path)==pin,'version-specific pure source binding')
        acceptance['pure_cases_separate'][label]=dict(tests=number,elapsed_seconds=final['elapsed_seconds'],cap_seconds=150,actual_solver_fits=0)
        for directory in (folder,owned):
            for file in sorted(directory.iterdir()):
                if file.is_file():pairs.append((file,directory.name+'__'+file.name))
        for name in ('check_method24_pure'+label+'.py','run_method24_pure'+label+'.py','method24_pure'+label+'_allocation.json'):
            pairs.append((PREP/name,name))
    failure=read(PREP/'method24-solver-smoke01/failure.json');smoke=read(PREP/'method24-solver-smoke02/result.json')
    need(failure['status']=='REJECTED_PUBLIC_SOLVER_SMOKE' and failure['fit_attempts']==failure['fit_completions']==0,'smoke01zero fits/failure')
    smoke_final=read(PREP/'method24-solver-smoke02-owned/final.json')
    need(smoke_final['status']=='ACCEPTED_MANUFACTURED_SOLVER_ABI_ONLY' and smoke_final['actual_fit_attempts']==2
         and smoke_final['actual_corpus_reads']==smoke_final['actual_neural_calls']==0 and 0<=smoke_final['elapsed_seconds']<=30,'smoke02 scope')
    need(smoke['fit_attempts']==smoke['fit_completions']==2 and not smoke['forbidden_attempts'],'smoke02 actual fits')
    need(smoke['source_before']==smoke['source_after'] and len(smoke['fit_results'])==2,'smoke02 source/fit population')
    for rel,pin in smoke['source_before'].items():
        source=ROOT/rel
        if source==PREP/'method24_worker01.py':source=PREP/'pre-method24-windows-metadata01/method24_worker01.py.before'
        need(sha(source)==pin,'smoke02 exact historical source binding')
    acceptance['smoke02_elapsed_seconds']=smoke_final['elapsed_seconds']
    acceptance['smoke02_actual_OS_metadata']=smoke['actual_os_metadata']
    for label in ('01','02'):
        for suffix in ('','-owned'):
            directory=PREP/('method24-solver-smoke'+label+suffix)
            for file in sorted(directory.iterdir()):
                if file.is_file():pairs.append((file,directory.name+'__'+file.name))
        for name in ('method24_solver_smoke'+label+'.py','run_method24_solver_smoke'+label+'.py','method24_solver_smoke'+label+'_allocation.json'):
            pairs.append((PREP/name,name))
    for name in ('pre-method24-windows-metadata01','pre-late-counter-fix01'):
        for path in sorted((PREP/name).iterdir()):
            if path.is_file():pairs.append((path,name+'__'+path.name))
    # Immutable request/review, not proof that preparing a request executed fits.
    pairs += [(PREP/n,n) for n in ('method24_request01.json','method24_root_dispatch_review01.json')]
    need(sha(PREP/'method24_request01.json')==REQUEST_SHA and sha(PREP/'method24_root_dispatch_review01.json')==ROOT_REVIEW_SHA,'reviewed request pins')
    native,native_pairs=native_terminal_inventory(args.native_run_sha256,args.terminal_receipt)
    acceptance['native']=native;pairs += native_pairs
    by_source={}
    for source,alias in pairs:
        source=physical(source);need(source.is_file() and source.stat().st_size<=512*1024,'small selected copy only')
        by_source.setdefault(source,alias)
    rows=[dict(source=p.relative_to(ROOT).as_posix(),copy=a,sha256=sha(p),bytes=p.stat().st_size) for p,a in sorted(by_source.items())]
    need(len({v['copy'] for v in rows})==len(rows) and sum(v['bytes'] for v in rows)<=4*1024**2,'bounded unambiguous copy inventory')
    return dict(status='DRY_NOT_CLOSED',run_id=RUN_ID,acceptance=acceptance,copy_pairs=rows,
        source_sha256={v['source']:v['sha256'] for v in rows},selected_bytes=sum(v['bytes'] for v in rows),
        expected_generated_outputs=list(GENERATED),expected_output_count=len(rows)+1+len(GENERATED))


def close(args,dry):
    need(args.approval_reference and sha(args.inventory_output)==valid_sha(args.approved_dry_sha256)
         and read(args.inventory_output)==dry,'ROOT approval/exact dry required')
    destination=physical(ROOT/'research_tracking/runs'/RUN_ID);need(not destination.exists(),'immutable bundle exists')
    sys.path.insert(0,str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    pairs=[(ROOT/r['source'],r['copy']) for r in dry['copy_pairs']]+[(args.inventory_output,'approved_dry_inventory.json')]
    before=[dict(source=p.relative_to(ROOT).as_posix(),copy=a,sha256_before_copy=sha(p),bytes=p.stat().st_size) for p,a in pairs]
    note='''# Method24 — Windows metadata bootstrap, pure tests, solver ABI và native receipt\n\n43PASS và45PASS là hai revisions/suites khác nhau, không88independent cases. Smoke01failed trước solver, rawouter countnull giữ nguyên; smoke02actual2publicfits/16manufactured rows, không corpus/NN. Native attachment nếu có chứa2352statistical TRAIN-only fits riêng, không gọi toànbatch0models hoặc researchNNfitted.\n\n[Acceptance](frozen_acceptance.json), [native14SHA/size pointers](native_artifact_inventory.json), [copy inventory](copy_inventory.json).5exports lớn giữ nguyên nơi gốc, không đưa Git/copybundle; pointers có full14hash trước/sau. No source/test/solver/model rerun.\n\nWindows OS fields lấyplatform.uname thật trongownedJob trước fitguard, không fakeversion; metadatahelperPopen có thểnonzero, fit-phasePopen0. Latecaughtattemptguard trước/sauDONE, failureoverrides pendingmarkers.\n\nConfidence là predictive stability của train-only surrogate; learnedgraph không tự là prerequisite truth, calibratededgeprobability, causalbenefit, NNperformance hoặc RQcompletion. Publicschema audit đọc9inputs+DONE; optimization chỉTRAIN48×210, không nóitrain-onlyfileaccess.\n\nexecution.log là archiver log, khôngnativeexecution trace. Native outer elapsed_before_receipt chỉpre-receipt, không lấy làm finalwall; nếu ROOTterminal receipt được cung cấp thì giữ riêng. record_evidence_run chỉ dùng read-onlyGitHEAD provenance, khôngadd/commit/push.\n'''
    with record_evidence_run(ROOT,RUN_ID,metadata={**dry['acceptance'],'root_closure_reference':args.approval_reference,
            'approved_dry_sha256':args.approved_dry_sha256},sources=sorted({p for p,_ in pairs}),note=note) as directory:
        def write(name,value):
            with (directory/name).open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
        write('copy_inventory_before.json',before)
        for row,(source,alias) in zip(before,pairs):
            need(sha(source)==row['sha256_before_copy'],'precopy drift')
            with source.open('rb') as src,(directory/alias).open('xb') as dst:shutil.copyfileobj(src,dst)
        after=[]
        for row,(source,alias) in zip(before,pairs):
            digest=sha(directory/alias);need(digest==sha(source)==row['sha256_before_copy'],'postcopy source/destination drift')
            after.append({**row,'sha256_after_copy':digest,'exact_match':True})
        native_after,_=native_terminal_inventory(args.native_run_sha256,args.terminal_receipt)
        need(native_after==dry['acceptance']['native'],'native14hash/source/rejections changed during copy')
        write('copy_inventory.json',after);write('frozen_acceptance.json',dry['acceptance'])
        write('native_artifact_inventory.json',dict(before=dry['acceptance']['native'],after=native_after,
            exact_match=True,large_exports_copied=False))
        write('closure_review.json',dict(approval_reference=args.approval_reference,approved_dry_sha256=args.approved_dry_sha256,
            no_tests_or_solver_rerun=True,native_time_scope='pre-receipt unless persisted ROOT terminal provided'))
        names={v['copy'] for v in before}|set(GENERATED)
        with (directory/'raw_log_paths.txt').open('x',encoding='utf-8') as stream:
            stream.write(''.join((directory/n).relative_to(ROOT).as_posix()+'\n' for n in sorted(names) if n.endswith('.log')))
        need({p.name for p in directory.iterdir()}==names|{'manifest.json'},'exact bundle file set')
    verified=verify_evidence_bundle(directory);need(verified['artifacts']==dry['expected_output_count'],'verified output count')
    print(json.dumps(dict(**verified,manifest_sha256=sha(directory/'manifest.json'),copy_pairs=len(before))))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('dry','close'));parser.add_argument('--inventory-output',type=Path,required=True)
    parser.add_argument('--native-run-sha256');parser.add_argument('--terminal-receipt',type=Path)
    parser.add_argument('--approved-dry-sha256');parser.add_argument('--approval-reference')
    args=parser.parse_args();args.inventory_output=physical(args.inventory_output)
    need(args.inventory_output.parent==PREP and args.inventory_output.suffix=='.json','direct prep dryJSON')
    dry=inventory(args)
    if args.mode=='dry':
        with args.inventory_output.open('x',encoding='utf-8') as stream:json.dump(dry,stream,ensure_ascii=False,indent=2);stream.write('\n')
        print(json.dumps(dict(status='DRY_ONLY_NO_BUNDLE_CREATED',dry_sha256=sha(args.inventory_output),
            copy_pairs=len(dry['copy_pairs']),expected_outputs=dry['expected_output_count'],native_attached=args.native_run_sha256 is not None)))
    else:close(args,dry)


if __name__=='__main__':main()
