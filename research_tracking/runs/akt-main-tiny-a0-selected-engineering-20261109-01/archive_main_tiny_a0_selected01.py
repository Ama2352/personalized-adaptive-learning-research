"""Dry/closure actual tiny A0 engineering; không chạy model/tests/Git/oracle parser."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
RUN='akt-main-tiny-a0-selected-engineering-20261109-01'
REPORT=R/'research_tracking/reports/akt_main_tiny_a0_selected_engineering_20261109.md'
DRY=P/'main_tiny_a0_selected_archive_dry01.json'
FINAL_SHA='15efa8880bd215649a22d360362930b6e2131a592b59b585f193f7eecf99d7e2'
CORPUS_OUTER_SHA='e1745fc0423fd9660218d49a51a57126ac74d40810a2f6c58c8f776bd554c127'
CORPUS_MANIFEST_SHA='9c90a35429503ab146711460a543fea2b61a2e06ddd2a0ad7d287394f1bc6bfc'
GENERATED=('README.md','execution.log','copy_inventory.json','reference_inputs.json','binary_references.json',
           'source_binding.json','scope.json','closure_review.json','reviewed_dry.json')


def need(ok,why):
    if not ok:raise ValueError(why)


def safe(path):
    need(path.is_absolute() and path.is_relative_to(R),'same-root path')
    cursor=R
    for part in path.relative_to(R).parts:
        cursor/=part;need(not cursor.is_symlink() and not cursor.is_junction(),'physical input')
    need(path.resolve()==path and path.is_file(),'regular selected input')
    return path


def sha(path):
    safe(path)
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path,cap=2*1024**2):
    safe(path);need(path.stat().st_size<=cap,'small JSON')
    return json.loads(path.read_bytes())


def row(path):return dict(sha256=sha(path),bytes=path.stat().st_size)


def write(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')


def gather(report_sha):
    need(sha(REPORT)==report_sha,'external reviewed report SHA')
    final_path=P/'main-tiny-selected-a0-01/outer-final.json'
    final=read(final_path);worker=final['worker_result'];owner=final['owned_receipt']
    need(sha(final_path)==FINAL_SHA and final['status']=='ACCEPTED_ACTUAL_TINY_A0_SELECTED_ONLY_ENGINEERING'
         and final['error'] is None and final['elapsed_seconds']<600 and final['environment_restored'] is True,
         'actual final02 acceptance')
    need(owner['accepted'] is True and owner['cleanup_accepted'] is True and owner['job_active_after_cleanup']==0
         and owner['returncode']==0 and owner['errors']==[] and owner['popen_handle_closed'] is True,'actual owned cleanup')
    need(worker['error'] is None and worker['source_before']==worker['source_after'] and worker['observer_restored'] is True
         and worker['denied']==worker['monitor_errors']==[] and worker['monitor_stopped'] is True
         and worker['elapsed_seconds']<560 and worker['cuda_initialized'] is False,'actual worker source/resource/scope')
    need(worker['resources']['peak_rss_bytes']<=1024**3
         and worker['resources']['min_available_ram_bytes']>=2*1024**3,'observed memory')
    request_path=P/'main_tiny_selected_a0_02_request.ROOT.json';request=read(request_path)
    need(sha(request_path)==final['request_sha256']==worker['request_sha256']
         == '2d5eb7463e834a453e2e0edf85544f47214cd062b43cfe59804602326e22d230','actual request02 bytes')
    config_path=R/request['native_config_file'];auth_path=R/request['authorization_file']
    need(sha(config_path)==request['native_config_sha256']=='f51560d8a50fa7866022fe4ece7bdaa367aa4fad28be14f6cb5bb2bf854bbcc8'
         and sha(auth_path)==request['authorization_sha256']=='fde4d2e08b03891b6e088ff6d83ac5d37fce0ceaab7e208acace0c341f94486b',
         'original materialized config/auth unchanged')
    config=read(config_path);base=Path(config['output_dir'])
    need(base==R/'experiments/akt/results/main-a0-tiny-selected-engineering10x84-20261109-01'
         and config['max_epochs']==20 and config['patience']==3 and config['max_steps']==40,'frozen recipe/run')
    terminal=read(base/'selected-terminal.json');complete=read(base/'COMPLETE.json');epochs=read(base/'fit80/epochs.json')
    need(terminal['status']=='SELECTED_ONLY_COMPLETE' and terminal['complete_fit_epochs']==7
         and terminal['selected_epoch']==4 and terminal['fresh_best_reload'] is True
         and complete['status']=='COMPLETE_MAIN_SELECTED_ONLY_CANDIDATE' and complete['main_matrix_complete'] is False,
         'actual selected-only completion')
    need(len(epochs)==7 and [r['epoch'] for r in epochs]==list(range(1,8))
         and all(r['training']['complete'] is True and r['training']['valid_targets']==672
                 and r['training']['optimizer_steps']==2 for r in epochs),'all complete actual epochs')
    counters=terminal['counters']
    need(counters['reserved']==counters['body_returned']==counters['complete']==14
         and counters['reserved_targets']==counters['body_returned_targets']==counters['complete_targets']==4704,
         'actual native tracker totals')
    observation=worker['observer'];expected=dict(revalidate=50,auth=51,metadata=51,native_evidence=51,corpus_hash_audit=51,
        lazy_tools=1,model_constructor=2,adam_constructor=2,adapter_step=14,selection_pass=8,native_forward=22,
        checkpoint_save=4,checkpoint_inspect=2,checkpoint_restore=1)
    need(observation['counts']=={key:dict(started=n,returned=n,exceptions=0) for key,n in expected.items()}
         and observation['training_targets']==4704 and observation['selection_targets']==672
         and observation['selection_windows']==8 and observation['forward_by_scope']==dict(training=14,selection=8)
         and observation['nested_times_must_not_be_summed'] is True and len(worker['git_calls'])==530,'actual observer scope')
    journal=[json.loads(line) for line in (base/'events.jsonl').read_text().splitlines()]
    kinds=Counter(r['kind'] for r in journal)
    need(kinds['tracker_optimizer_started']==kinds['tracker_optimizer_body_returned']==kinds['step_committed']==14,
         'original durable Adam events')
    selection=terminal['full_selection']
    need(selection['full_targets']==selection['supported_targets']==84 and selection['unsupported_targets']==0
         and selection['supported_metrics']['positive_count']==58 and selection['supported_metrics']['negative_count']==26,
         'raw selection population')
    need(not any((base/name).exists() for name in ('failure.json','refit90','calibration'))
         and not any((P/'main-tiny-selected-a0-01'/name).exists() for name in ('failure.log','resource-failure.json','postwrite-rejection.json')),
         'no late failure or forbidden phase output')
    paths={};refs={};binaries=[]
    def reference(path,expected=None,opaque=False):
        actual=row(path)
        if expected is not None:need(actual==expected,'reference SHA/size')
        refs[path.relative_to(R).as_posix()]=dict(**actual,copied=False,opaque_bytes_only=opaque)
    def add(alias,path):
        safe(path);need(Path(alias).name==alias and alias not in paths and path.stat().st_size<=2*1024**2,
                        'unique bounded flat copy')
        need(path.suffix.lower() not in ('.pt','.parquet','.dll','.pyd'),'binaries reference only')
        paths[alias]=path
    for name in ('prepare_main_tiny_a0_package01.py','run_prepare_main_tiny_a0_package01.py',
                 'check_main_tiny_selected_a0_01.py','run_main_tiny_selected_a0_01.py','run_main_tiny_selected_a0_02.py',
                 'prepare_tiny_disk_path_fix02.py','launch_tiny_a0_profile01.py','launch_tiny_a0_profile02.py',
                 'tiny_disk_path_fix02_inventory.json','main_tiny_a0_package01_dry.json',
                 'main_tiny_selected_a0_01_request.ROOT.json','main_tiny_selected_a0_02_request.ROOT.json',
                 'MAIN_TINY_A0_SELECTED_LIFECYCLE_CONTRACT01.md','MAIN_REVALIDATION_COST_SOURCE_AUDIT01.md',
                 'ROOT_MAIN_TINY_A0_REVIEW01.md','ROOT_MAIN_TINY_A0_DRY_REVIEW01.md',
                 'ROOT_MAIN_TINY_A0_ACTUAL_FIT_REVIEW01.md','ROOT_MAIN_TINY_A0_ACTUAL_FIT_REVIEW02.md'):
        add(name,P/name)
    add(Path(__file__).name,Path(__file__).resolve());add('report.md',REPORT)
    add('materialized_config.json',config_path);add('materialized_authorization.json',auth_path)
    for label,directory in (('metadata_prepare','main-tiny-a0-package01'),
            ('metadata_prepare_owned','main-tiny-a0-package01-owned'),
            ('metadata_materialize','main-tiny-a0-package01-materialize'),
            ('metadata_materialize_owned','main-tiny-a0-package01-materialize-owned'),
            ('fit','main-tiny-selected-a0-01'),('fit_owned','main-tiny-selected-a0-01-owned'),
            ('profile_prepare','tiny-a0-profile-prepare01'),('profile_materialize','tiny-a0-profile-materialize01'),
            ('profile_fit01','tiny-a0-profile-fit01'),('profile_fit02','tiny-a0-profile-fit02')):
        directory=P/directory
        for path in sorted(directory.iterdir()):
            if path.is_file():
                need(path.suffix in ('.json','.log'),'small original terminal text')
                add(label+'__'+path.name,path)
    for directory in ('main-tiny-a0-package01','main-tiny-a0-package01-materialize'):
        result=read(P/directory/'outer-final.json')
        need(result['status']=='ACCEPTED_METADATA_PACKAGE_ONLY' and result['error'] is None
             and result['elapsed_seconds']<60 and result['owned_receipt']['accepted'] is True
             and result['owned_receipt']['cleanup_accepted'] is True
             and result['owned_receipt']['job_active_after_cleanup']==0,'both actual metadata operations')
    failed=read(P/'tiny-a0-profile-fit01/result.json')
    stderr=(P/'tiny-a0-profile-fit01/stderr.log').read_text()
    fix=read(P/'tiny_disk_path_fix02_inventory.json')
    need(failed['returncode']==1 and failed['parent_environment_unchanged'] is True
         and 'TypeError: argument 1 must be str, not WindowsPath' in stderr
         and fix['native_worker_started_in_original_attempt'] is False and fix['config_and_authorization_unchanged'] is True,
         'actual prelaunch failure preserved, not a failed training epoch')
    old=(P/'run_main_tiny_selected_a0_01.py').read_bytes();new=(P/'run_main_tiny_selected_a0_02.py').read_bytes()
    need(new==old.replace(b'psutil.disk_usage(R)',b'psutil.disk_usage(str(R))')
         and sha(P/'run_main_tiny_selected_a0_02.py')==fix['derivative_outer_sha256'],'exact disk-path-only derivative')
    original_request=read(P/'main_tiny_selected_a0_01_request.ROOT.json')
    revised=json.loads(json.dumps(original_request));revised['source_pins']['artifacts/akt/local-tests/akt-research-runner-20261108-01/run_main_tiny_selected_a0_02.py']=fix['derivative_outer_sha256']
    need(revised==request,'only added derivative controller pin, unchanged actual auth/config/spec')
    need(set(worker['native_outputs'])=={p.relative_to(R).as_posix() for p in base.rglob('*') if p.is_file()},'all actual native artifacts')
    for name,expected_row in worker['native_outputs'].items():
        path=R/name;need(row(path)==expected_row,'actual native output inventory')
        if path.suffix=='.pt':
            reference(path,expected_row,opaque=True)
            binaries.append(dict(source=name,**expected_row,copied=False,model_loaded=False))
        else:add('native__'+path.relative_to(base).as_posix().replace('/','__'),path)
    need(len(binaries)==4 and all(r['bytes']==26949689 for r in binaries),'four actual payloads reference only')
    for name,pin in complete['outputs_sha256'].items():need(sha(base/name)==pin,'native COMPLETE file hashes')
    corpus_outer=P/'main-engineering10x84-01/outer-final.json'
    need(sha(corpus_outer)==CORPUS_OUTER_SHA,'actual previously accepted corpus')
    publication=read(corpus_outer)['worker_result']['publication']
    corpus=R/publication['corpus_path'];need(len(publication['files'])==17,'actual original corpus17')
    for name,digest,size in publication['files']:
        reference(corpus/name,dict(sha256=digest,bytes=size),opaque=True)  # Oracle bytes only hashed, never parsed.
    manifest=R/'research_tracking/runs/akt-main-engineering-corpus10x84-20261109-01/manifest.json'
    need(sha(manifest)==CORPUS_MANIFEST_SHA,'closed corpus bundle identity');reference(manifest)
    reference(corpus_outer)
    for name,pin in worker['source_before'].items():
        need(sha(R/name)==pin,'executed source bytes unchanged');reference(R/name)
    for name,field in (('runtime_report','runtime_report_sha256'),('lock_file','lock_sha256'),('gate_pointer','gate_pointer_sha256')):
        descriptor=request['runtime_evidence'];need(sha(R/descriptor[name])==descriptor[field],'actual runtime/Gate/lock identity')
        reference(R/descriptor[name])
    inventory=[dict(copy=alias,source=path.relative_to(R).as_posix(),**row(path)) for alias,path in sorted(paths.items())]
    need(sum(r['bytes'] for r in inventory)<=8*1024**2,'small copied evidence<=8MiB')
    return inventory,refs,binaries,final,terminal


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--report-sha256',required=True)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare-dry',action='store_true');mode.add_argument('--check-dry',action='store_true');mode.add_argument('--close',action='store_true')
    parser.add_argument('--expected-dry-sha256');parser.add_argument('--review-reference');args=parser.parse_args()
    need(Path(sys.prefix).resolve()==R/'.venv','repository .venv only')
    destination=R/'research_tracking/runs'/RUN;need(not destination.exists(),'immutable destination absent')
    inventory,refs,binaries,final,terminal=gather(args.report_sha256)
    dry=dict(run_id=RUN,report_sha256=args.report_sha256,copies=inventory,reference_inputs=refs,binary_references=binaries,
        generated_outputs=list(GENERATED),expected_output_count=len(inventory)+len(GENERATED),actual_outer_sha256=FINAL_SHA)
    if args.prepare_dry:
        write(DRY,dry);print(json.dumps(dict(status='DRY_PREPARED_NOT_CLOSED',dry_sha256=sha(DRY),copies=len(inventory),outputs=dry['expected_output_count'])));return
    need(read(DRY)==dry,'exact reviewed/current dry')
    if args.check_dry:
        print(json.dumps(dict(status='DRY_MATCH_NOT_CLOSED',outputs=dry['expected_output_count'])));return
    need(args.expected_dry_sha256==sha(DRY) and args.review_reference,'Root exact-dry closure review')
    sys.path.insert(0,str(R/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    note=('# Actual tiny A0 selected-only engineering\n\nGenuine10×84 input,7completeepochs/best4,14Adam/4704targets, '
          'freshbestreload/full84export,CPU ownedcleanup accepted. Giữ prelaunch01diskTypeError và derivative02. '
          'Metadata prepare/materialize riêng, không oldguardauthreuse. CP4/corpus17 SHA-reference only. '
          'Metrics thuộc integrationfixture; không efficacy/main9/refit/calibration/CUDA/resume. '
          'Báo cáo ../../reports/akt_main_tiny_a0_selected_engineering_20261109.md.\n')
    sources=list(dict.fromkeys([R/r['source'] for r in inventory]+[R/name for name in refs]+[DRY]))
    with record_evidence_run(R,RUN,metadata=dict(kind='ACTUAL_A0_SELECTED_ONLY_ENGINEERING_INTEGRATION',
            complete_epochs=7,selected_epoch=4,optimizer_steps=14,engineering_only=True,research_matrix_complete=False),sources=sources,note=note) as out:
        copied=[]
        for item in inventory:
            source=R/item['source'];need(row(source)==dict(sha256=item['sha256'],bytes=item['bytes']),'input before copy')
            (out/item['copy']).write_bytes(source.read_bytes())
            need(sha(source)==sha(out/item['copy'])==item['sha256'],'before/copy/after SHA')
            copied.append(dict(**item,input_sha256_after=sha(source),copied_sha256=sha(out/item['copy'])))
        write(out/'copy_inventory.json',copied);write(out/'reference_inputs.json',refs);write(out/'binary_references.json',binaries)
        write(out/'source_binding.json',dict(source_before=final['worker_result']['source_before'],
            source_after=final['worker_result']['source_after'],native_result_sha256=FINAL_SHA,
            original_config_auth_commit_reference='9871d61',commit_origin='ROOT_PROVIDED_NOT_GIT_REEXECUTED_BY_ARCHIVER',
            metadata_operations_separate=True,only_derivative_outer_disk_argument_and_added_request_pin=True,
            checkpoints_copied=False,corpus17_copied=False,oracle_parsed=False,oracle_hash_access='OPAQUE_BYTES_ONLY'))
        write(out/'scope.json',dict(kind='ENGINEERING_INTEGRATION_ONLY',epochs=7,selected_epoch=4,optimizer_steps=14,
            optimized_target_exposures=4704,unique_train_events=672,selection_passes=8,selection_target_exposures=672,
            unique_selection_events=84,selection_learners=1,best_saves=4,fresh_restore=True,metadata_dispatches=51,git_processes=530,
            worker_seconds=final['worker_result']['elapsed_seconds'],outer_seconds=final['elapsed_seconds'],
            profile_launcher_seconds=161.4746751000057,nested_times_must_not_be_summed=True,
            metrics_scope='RAW_SELECTION_USED_FOR_EPOCH_SELECTION_NOT_INDEPENDENT_TEST',
            supported_metrics=terminal['full_selection']['supported_metrics'],native_bce=terminal['full_selection']['native_bce_mean'],
            efficacy_claim=False,research_main_comparison=False,refit_calibration=False,resume_supported=False,cuda_readiness=False))
        write(out/'closure_review.json',dict(reference=args.review_reference,dry_sha256=args.expected_dry_sha256,
            report_sha256=args.report_sha256,root_closure_without_reexecution=True))
        (out/'reviewed_dry.json').write_bytes(DRY.read_bytes());need(sha(out/'reviewed_dry.json')==args.expected_dry_sha256,'reviewed dry copy')
        need({p.name for p in out.iterdir() if p.name!='manifest.json'}==set(GENERATED)|{r['copy'] for r in inventory},'exact declared outputs')
        need(all(sha(R/r['source'])==r['sha256'] for r in inventory)
             and all(row(R/name)==dict(sha256=r['sha256'],bytes=r['bytes']) for name,r in refs.items()),'all selected originals/reference SHA after copy')
    verified=verify_evidence_bundle(destination);need(verified['artifacts']==dry['expected_output_count'],'all outputs verified')
    print(json.dumps(dict(**verified,manifest_sha256=sha(destination/'manifest.json'))))


if __name__=='__main__':main()
