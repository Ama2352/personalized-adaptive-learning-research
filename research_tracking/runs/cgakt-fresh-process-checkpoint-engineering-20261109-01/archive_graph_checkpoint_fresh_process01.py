"""ROOT dry/close GRAPH19; chỉ metadata/hash/copy, không Torch hoặc rerun."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

R=Path(__file__).resolve().parents[4]
P=Path(__file__).resolve().parent
RUN='cgakt-fresh-process-checkpoint-engineering-20261109-01'
DRY=P/'graph_checkpoint_fresh_process_archive_dry01.json'
REPORT=P/'cgakt_fresh_process_checkpoint_readiness_20261109.candidate.md'
BASE=R/'research_tracking/runs/cgakt-research-checkpoint-engineering-20261109-01'
BASE_SHA='95769b7b1ee8c2c927f0cb6ed1ff7c308458629703bd63e3c6081c0bafa15307'
GENERATED=tuple(sorted(('README.md','execution.log','copy_inventory.json','binary_reference.json',
    'source_binding.json','scope.json','timing_scope.json','closure_review.json','raw_log_paths.txt')))


def need(ok,message):
    if not ok:raise ValueError(message)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(path):
    need(path.is_absolute() and path.is_relative_to(R) and '..' not in path.parts,'fixed project input')
    cursor=R
    for part in ('',*path.relative_to(R).parts):
        if part:cursor/=part
        need(not cursor.is_symlink() and not getattr(cursor,'is_junction',lambda:False)(),'no input alias')
    need(path.resolve()==path and path.is_file(),'physical regular input')
    return path


def write(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')


def binary_sha(path,size):
    safe(path);before=path.stat();need(before.st_size==size and 0<size<=64*1024**2,'exact bounded checkpoint size')
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        while chunk:=stream.read(1024**2):digest.update(chunk)
    after=path.stat()
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)
        ==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'binary changed while stream hashing')
    return digest.hexdigest()


def gather(expected_final_sha,expected_report_sha):
    paths={}
    def add(alias,path):
        safe(path);need(alias not in paths and path.stat().st_size<=2*1024**2,'unique smallselected input')
        paths[alias]=path
    def read(path):
        safe(path);need(path.stat().st_size<=2*1024**2,'small JSON');return json.loads(path.read_bytes())
    parent=P/'graph19-fresh-parent01'
    need(sha(safe(parent/'final.json'))==expected_final_sha,'external actual parentfinal SHA')
    need(sha(safe(REPORT))==expected_report_sha,'reviewed report bytes')
    final=read(parent/'final.json');cross=read(parent/'cross_process_proof.json');handoff=read(parent/'handoff.json')
    packet=read(P/'graph_checkpoint_fresh_process01_allocation.json')
    need(final['status']=='ACCEPTED_GRAPH19_TRUE_FRESH_OS_PROCESS_TRAINING_STATE_NOT_LIFECYCLE'
        and final['errors']==[] and final['elapsed_seconds']<150,'actual final accepted not intent')
    need(cross['status']=='ACCEPTED_TRUE_FRESH_OS_PROCESS_STATE_PARITY'
        and cross['producer_reaped_before_consumer'] is True and cross['actual_optimizer_bodies']==6
        and cross['actual_optimization_targets']==144 and cross['three_rng_and_modes_restored'] is True
        and cross['full_epoch2_population_and_order_exact'] is True,'actual cross-process proof')
    need(final['packet_sha256']==sha(P/'graph_checkpoint_fresh_process01_allocation.json')
        and final['handoff_sha256']==sha(parent/'handoff.json'),'external packet/handoff identities')
    rows={}
    for role in ('producer','consumer'):
        child=read(P/f'graph19-fresh-{role}01/result.json');owned=read(parent/f'{role}_owned_receipt.json')
        need(child['status']==f'ACCEPTED_GRAPH19_{role.upper()}_PENDING_PARENT'
            and child['native_started']==child['native_body_returned']==packet['allocation']['roles'][role]['counter_caps'],
            'exact actual physicalrole workload:'+role)
        need(owned['accepted'] is True and owned['cleanup_accepted'] is True and owned['returncode']==0
            and owned['job_active_after_cleanup']==0 and owned['popen_handle_closed'] is True and owned['cleanup_errors']==[]
            and owned['actual_worker_in_job_before_GO'] is True and child['owner']['worker']==owned['actual_worker'],
            'kernel worker token/cleanup:'+role)
        need(child['source_before']==child['source_after']==final['source_before']==final['source_after']==packet['source_pins']
            and child['runtime_before']==child['runtime_after']==packet['runtime_pins'],'executed source/runtime vectors')
        need(child['method_restoration']['accepted'] is True and child['forbidden_attempts']==[] and child['original_error'] is None
            and child['monitor_errors']==[] and child['monitor_stopped'] is True and child['environment_restored'] is True,
            'scope/method/environment guards')
        need(child['elapsed_seconds']<53 and child['native_work_seconds']<45
            and child['resources']['observed_peak_rss_bytes']<=1024**3
            and child['resources']['observed_minimum_available_ram_bytes']>=2*1024**3,'actual per-role resource bounds')
        need(child['cuda_false_queries']['true_results']==0 and child['torch_profile']['cuda_initialized_after'] is False
            and len(child['local_git_calls'])==10 and len(child['original_loaders'])==1
            and child['original_loaders'][0]['original'] is True and child['original_loaders'][0]['cached'] is False,
            'actual CPU/original upstream scope')
        need(sha(P/f'graph19-fresh-{role}01/result.json')==final['roles'][role]['result_sha256'],'independent result byteSHA')
        rows[role]=(child,owned)
    prod,cons=rows['producer'][0]['proof'],rows['consumer'][0]['proof']
    a,b=rows['producer'][1]['actual_worker'],rows['consumer'][1]['actual_worker']
    need(a['pid']!=b['pid'] and int(a['created_filetime_100ns'])<int(b['created_filetime_100ns'])
        and cross['producer']==a and cross['consumer']==b,'distinct actual OS processes/creation tokens')
    for key in ('plan','profile','identity','checkpoint','e1_rng_digests','e1_module_modes','e1_counters','full_epoch2',
        'final_model_sha256','final_adam_sha256','final_rng_digests','final_module_modes','readout'):
        need(prod[key]==cons[key],'full state/input/sample parity:'+key)
    e2=prod['full_epoch2']
    need(e2['complete'] is True and e2['epoch_windows']==8 and e2['epoch_targets']==48
        and e2['epoch_optimizer_steps']==2 and e2['completed_epochs']==2 and e2['sampler_seed']==44
        and len({w for row in e2['actual_ordered_inputs'] for w in row['window_ids']})==8,'complete next epoch unique8windows')
    need({w for row in e2['actual_ordered_inputs'] for w in row['window_ids']}==set(prod['plan']['full_window_ids'])
        and len(e2['actual_ordered_inputs'])==2 and all(row['reserved']==row['returned']==24 for row in e2['actual_ordered_inputs']),
        'full same population each ordered numerical batch, not merely8otherwindows')
    need(prod['physical_optimizer_bodies']==4 and cons['physical_optimizer_bodies']==2
        and prod['tracker_cumulative_bodies']==cons['tracker_cumulative_bodies']==4
        and cons['immediate_three_rng_modes_restored'] is True,'physical6 vs history4+4; actual restored RNG/modes')
    need(handoff['producer_result_sha256']==final['roles']['producer']['result_sha256']
        and handoff['producer_receipt_sha256']==sha(parent/'producer_owned_receipt.json')
        and handoff['producer_actual_worker']==a and handoff['producer_reaped_job_empty'] is True,'trusted owned external handoff')
    ref=prod['checkpoint'];base=R/ref['directory']
    need(base==R/'experiments/akt/results/graph19-fresh-producer-20261109-01/checkpoints/epoch-1','fixed checkpoint directory')
    safe(base/'metadata.json')
    need({f.name for f in base.iterdir()}=={'state.pt','metadata.json','COMPLETE.json'},'exact fresh checkpoint files')
    need(sha(safe(base/'metadata.json'))==ref['metadata_sha256'] and sha(safe(base/'COMPLETE.json'))==ref['complete_sha256'],
        'physical metadata/COMPLETE byteSHA')
    need(binary_sha(base/'state.pt',ref['checkpoint_bytes'])==ref['checkpoint_sha256'],'physical binarySHA before copies')
    meta=read(base/'metadata.json');complete=read(base/'COMPLETE.json')
    need(complete['status']=='COMPLETE_CGAKT_EPOCH_TRAINING_STATE' and complete['metadata_sha256']==ref['metadata_sha256']
        and complete['checkpoint_sha256']==ref['checkpoint_sha256'] and meta['identity']==prod['identity'], 'physical COMPLETE/context identity')
    need(meta['receipt']['windows_sha256']==e2['windows_sha256'] and meta['receipt']['targets_sha256']==e2['targets_sha256']
        and meta['receipt']['epoch_targets']==48 and meta['receipt']['epoch_steps']==2
        and meta['receipt']['model_sha256']==prod['e1_counters']['model_sha256']
        and meta['receipt']['optimizer_sha256']==prod['e1_counters']['adam_sha256'],'same E1/E2 target population and saved E1 trainingstate')
    binary=dict(source=(base/'state.pt').relative_to(R).as_posix(),bytes=ref['checkpoint_bytes'],sha256=ref['checkpoint_sha256'],
        copied=False,torch_load_by_archiver=False,producer_result_sha256=final['roles']['producer']['result_sha256'])
    for name in ('check_graph_checkpoint_fresh_process01.py','run_graph_checkpoint_fresh_process01.py',
        'graph_checkpoint_fresh_process01_allocation.json'):
        add(name,P/name);need(sha(P/name)==packet['source_pins'].get((P/name).relative_to(R).as_posix(),sha(P/name)), 'executed driverbytes')
    add('archive_graph_checkpoint_fresh_process01.py',Path(__file__).resolve())
    add('report__cgakt_fresh_process_checkpoint_readiness.md',REPORT)
    add('reference__CP119_manifest.json',BASE/'manifest.json');need(sha(BASE/'manifest.json')==BASE_SHA,'immutable119 manifestref')
    add('checkpoint__metadata.json',base/'metadata.json');add('checkpoint__COMPLETE.json',base/'COMPLETE.json')
    add('writer__evidence.py',R/'src/knowledge_tracing/evidence.py')
    for path in sorted((P/'graph19-source-only-partial-before01').iterdir()):
        need(path.is_file(),'flat unexecuted sourcehistory');add('history__'+path.name,path)
    for label,folder in [('parent',parent),('producer',P/'graph19-fresh-producer01'),('producer_owned',P/'graph19-fresh-producer01-owned'),
        ('consumer',P/'graph19-fresh-consumer01'),('consumer_owned',P/'graph19-fresh-consumer01-owned')]:
        for path in sorted(folder.iterdir()):
            need(path.is_file(),'flat terminal raw outputs only');add(label+'__'+path.name,path)
    inventory=[dict(copy=alias,source=path.relative_to(R).as_posix(),sha256=sha(path),bytes=path.stat().st_size) for alias,path in sorted(paths.items())]
    need(sum(row['bytes'] for row in inventory)<=5*1024**2,'compact selected evidence5MiB cap')
    return inventory,binary,final,rows,cross


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare-dry',action='store_true');parser.add_argument('--check-dry',action='store_true')
    parser.add_argument('--parent-final-sha',required=True);parser.add_argument('--report-sha',required=True)
    parser.add_argument('--close',action='store_true');parser.add_argument('--expected-dry-sha');parser.add_argument('--review-reference')
    args=parser.parse_args();need(Path(sys.prefix).resolve()==R/'.venv','repository .venv only')
    need(not(R/'research_tracking/runs'/RUN).exists(),'immutable destination absent')
    inventory,binary,final,rows,cross=gather(args.parent_final_sha,args.report_sha)
    dry=dict(run_id=RUN,copies=inventory,binary_reference=binary,parent_final_sha256=args.parent_final_sha,
        report_sha256=args.report_sha,generated_outputs=GENERATED,expected_output_count=len(inventory)+len(GENERATED))
    # JSON normalisation also makes tuple/list admission deterministic.
    dry=json.loads(json.dumps(dry,allow_nan=False))
    if args.prepare_dry:
        write(DRY,dry);print(json.dumps(dict(dry_sha256=sha(DRY),copies=len(inventory),outputs=dry['expected_output_count'])));return
    need(json.loads(DRY.read_bytes())==dry,'exact reviewed dry/current inputs match')
    if args.check_dry:print(json.dumps(dict(status='DRY_MATCH_NOT_CLOSED',outputs=dry['expected_output_count'])));return
    need(args.close and sha(DRY)==args.expected_dry_sha and args.review_reference,'explicit Root closure approval required')
    sys.path.insert(0,str(R/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    note='# CG-AKT — fresh OS process training-state proof\n\nHandmade CPU, fullE1→checkpoint→fullE2 state/sample parity in two distinct reaped OSworkers. Not lifecycle/main/fitted/GPU. CP119 referenced, one binary SHA/size only, no duplicate historicalmodels.\n'
    with record_evidence_run(R,RUN,metadata=dict(kind='CGAKT_TRUE_FRESH_OS_PROCESS_STATE_SAMPLE_ENGINEERING_ONLY',
        actual_optimizer_bodies=6,actual_training_target_exposures=144,actual_forward_calls=8),
        sources=[R/row['source'] for row in inventory],note=note) as out:
        copied=[]
        for row in inventory:
            source=R/row['source'];need(sha(source)==row['sha256'],'precopy sourceSHA')
            (out/row['copy']).write_bytes(source.read_bytes())
            need(sha(source)==sha(out/row['copy'])==row['sha256'],'source/copy/postcopySHA')
            copied.append(dict(**row,source_sha256_after_copy=sha(source),copy_sha256=sha(out/row['copy'])))
        write(out/'copy_inventory.json',copied);write(out/'binary_reference.json',binary)
        write(out/'source_binding.json',dict(historical_executed_sources=final['source_before'],runtime_bytes=final['runtime_before'],
            reference_CP119_manifest_sha256=BASE_SHA,partial_proposal_unexecuted=True))
        write(out/'scope.json',dict(actual_os_processes=2,actual_optimizer_bodies=6,actual_training_target_exposures=144,
            epoch_boundary_state_and_full_next_epoch_verified=True,fitted_research_model=False,lifecycle_resume_supported=False,
            mid_epoch_cursor_resume_supported=False,actual_corpus_fit=False,CUDA_or_cloud_execution=False))
        write(out/'timing_scope.json',dict(whole_seconds=final['elapsed_seconds'],cap_seconds=150,
            roles={role:dict(worker_seconds=row[0]['elapsed_seconds'],native_seconds=row[0]['native_work_seconds'],
                resources=row[0]['resources'],raw_timings=row[0]['timings']) for role,row in rows.items()},
            overlap='state_validation nested inside post; no sum of nested scopes; no fullcorpus/GPU throughput inference'))
        write(out/'closure_review.json',dict(reference=args.review_reference,dry_sha256=args.expected_dry_sha,no_reruns=True))
        (out/'raw_log_paths.txt').write_text('\n'.join(row['source'] for row in inventory if row['source'].endswith(('.log','.jsonl')))+'\n',encoding='utf-8')
        need({p.name for p in out.iterdir() if p.name!='manifest.json'}==set(GENERATED)|{row['copy'] for row in inventory},'exact outputs')
        need(all(sha(R/row['source'])==row['sha256'] for row in inventory),'all selected inputSHA aftercopy')
        need(binary_sha(R/binary['source'],binary['bytes'])==binary['sha256'],'physical binary unchanged after copies; not loaded/copied')
    directory=R/'research_tracking/runs'/RUN;verified=verify_evidence_bundle(directory)
    need(verified['artifacts']==dry['expected_output_count'],'exact closed count')
    print(json.dumps(dict(**verified,manifest_sha256=sha(directory/'manifest.json'))))


if __name__=='__main__':main()
