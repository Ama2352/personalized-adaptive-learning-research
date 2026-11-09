"""Inventory A1 accepted đã có, không chạy model/test hoặc load checkpoint."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
OUTPUT=PREP/'a1_expert_selected_archive_inputs01.json'


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):return json.loads(path.read_bytes())


def main():
    final=read(PREP/'a1-expert-engineering03/outer-final.json');worker=final['worker_result']
    request=read(PREP/'a1_expert_engineering03_request.ROOT.json')
    assert final['status']=='ACCEPTED_ACTUAL_A1_EXPERT_SELECTED_ONLY_ENGINEERING' and final['error']is None
    assert final['owned_receipt']['returncode']==0 and final['owned_receipt']['cleanup_accepted']is True and final['owned_receipt']['job_active_after_cleanup']==0
    assert worker['source_before']==worker['source_after']==request['source_pins']
    assert worker['observer_restored']is True and worker['job_query_handle_closed']is True and worker['monitor_stopped']is True
    assert worker['monitor_errors']==worker['denied']==[]
    for name,digest in request['source_pins'].items():assert sha(ROOT/name)==digest,name
    config_path=ROOT/request['native_config_file'];auth=ROOT/request['authorization_file']
    assert sha(config_path)==request['native_config_sha256'] and sha(auth)==request['authorization_sha256']
    config=read(config_path);native=Path(config['output_dir'])
    terminal=read(native/'selected-terminal.json');claim=read(native/'selected-claim.json')
    assert terminal['complete_fit_epochs']==7 and terminal['selected_epoch']==4
    assert claim['candidate_id']=='A1_EXPERT' and claim['full_targets']==claim['supported_targets']==84
    assert claim['initial_backbone_sha256']=='d80de4e015d4673a714be76468078de4f168709fb2aa41bc5c6771f78af2bf63'
    assert claim['graph_condition_sha256']=='2555ffbc1657f37d27aae331f99e4575869e952c0c307a111f0909e60385c744'
    assert terminal['counters']['complete']==terminal['counters']['body_returned']==14
    assert terminal['counters']['complete_targets']==4704
    assert len(worker['git_calls'])==530
    expected=dict(model_constructor=2,adam_constructor=2,adapter_step=14,selection_pass=8,native_forward=22,
        checkpoint_save=4,checkpoint_inspect=2,checkpoint_restore=1,metadata=51,revalidate=50)
    for key,count in expected.items():assert worker['observer']['counts'][key]==dict(started=count,returned=count,exceptions=0)
    copies={}
    def add(alias,path):
        assert alias not in copies and path.is_file() and path.stat().st_size<=2**20,alias
        copies[alias]=dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size)
    def flat(name,alias):
        for path in sorted((PREP/name).iterdir()):
            if path.is_file():add(alias+'__'+path.name,path)
    for name in ['A1_EXPERT_SELECTED_ENGINEERING_REPORT01.md','prepare_a1_archive_inventory01.py',
        'prepare_a1_expert_engineering_package01.py','run_prepare_a1_expert_engineering_package01.py',
        'check_a1_expert_engineering03.py','run_a1_expert_engineering03.py','prepare_a1_operational_request03.py',
        'launch_a1_expert_engineering_profile03.py','a1_expert_engineering03_request.ROOT.json',
        'a1_expert_engineering_package01_dry.json','ROOT_A1_EXPERT_OPERATIONAL_RETRY03_REVIEW.md',
        'ROOT_A1_EXPERT_OPERATIONAL_RETRY03_ACTUAL_FIT_REVIEW.md','a1_light_admission03.py','a1_light_admission04.py',
        'a1-light-admission03.json','a1-light-admission04.json']:
        add(name,PREP/name)
    for name,alias in [('a1-expert-engineering03','accepted'),('a1-expert-engineering03-owned','owned'),
        ('a1-expert-engineering-profile-fit03','profile'),('a1-expert-operational-request03','request'),
        ('a1-expert-engineering-package01','dry'),('a1-expert-engineering-package01-owned','dry_owned'),
        ('a1-expert-engineering-package01-materialize','materialize'),('a1-expert-engineering-package01-materialize-owned','materialize_owned')]:
        flat(name,alias)
    add('scientific_config.json',config_path);add('scientific_authorization.json',auth)
    refs=[]
    for name,row in worker['native_outputs'].items():
        path=ROOT/name;assert path.is_relative_to(native) and path.stat().st_size==row['bytes']
        if path.suffix=='.pt':
            refs.append(dict(path=name,bytes=row['bytes'],sha256=row['sha256'],verify_sha_at_archive=True,copied=False,deserialized=False))
        else:
            assert path.suffix in {'.json','.jsonl','.csv'},path
            add('native__'+path.relative_to(native).as_posix().replace('/','__'),path)
    assert len(refs)==4
    reference_names=['research_tracking/runs/owned-job-resource-exit-guard-20261110-01/manifest.json',
        'research_tracking/runs/main60-graph-condition-binding-20261110-01/manifest.json',
        'src/knowledge_tracing/evidence.py']
    evidence=request['runtime_evidence']
    reference_names += [evidence['runtime_report'],evidence['gate_pointer'],evidence['lock_file']]
    for path in [PREP/'graph29-a0-continuous01/outer-final.json',
        ROOT/'experiments/akt/results/main-a0-graph29-continuous-engineering10x84-20261110-01/selected-claim.json']:
        reference_names.append(path.relative_to(ROOT).as_posix())
    reference={name:sha(ROOT/name) for name in reference_names}
    assert reference[evidence['runtime_report']]==evidence['runtime_report_sha256']
    assert reference[evidence['gate_pointer']]==evidence['gate_pointer_sha256']
    assert sha(ROOT/'research_tracking/runs/owned-job-resource-exit-guard-20261110-01/manifest.json')=='46e9b64d1066667e9ac974db8d5236dc67934df0050f5b37e58fb69f6ba8cff7'
    value=dict(run_id='a1-expert-selected-engineering-20261110-01',copies=copies,references_sha256=reference,
        native_references=refs,original_source_inventory=request['source_pins'],
        accepted_outer=(PREP/'a1-expert-engineering03/outer-final.json').relative_to(ROOT).as_posix(),accepted_status=final['status'],
        reference_limit_vi='Guard58 chỉ tham chiếu, không duplicate failure/probes/canaries. Worker03 được lưu riêng như accepted producer source. Bốn checkpoint chỉ physical SHA/size refs, không copy hoặc deserialize.',
        metadata=dict(kind='A1_EXPERT_ENGINEERING_SELECTED_ONLY_PUBLIC_PRODUCER',epochs=7,selected_epoch=4,
            optimizer_steps=14,train_target_exposures=4704,selection_passes=8,full_selection_targets=84,
            initial_backbone_matches_A0=True,graph_confidence='fixed_uniform',graph_fit_scope='train8_public_expert',
            actual_whole_seconds=final['elapsed_seconds'],prior_failed_attempt_NN_updates=0,
            new_independent_N=0,full_main_matrix=False,refit=False,calibration=False,CUDA=False),
        readme_vi='# A1 expert selected-only engineering đã nghiệm thu\n\nActual7epochs/best4/14updates4704train targets/full84rawselection,freshinitialbackbonekhớpA0,source/runtime/Job0 đạt. Hai-threadCPU/cùng numericalconfig; publicexpert28/31unitconfidence boundtrain8,khôngMethod24train48. Guard58 historicalfailure/probes/canariesrefs only.4checkpointnativeSHArefs,khôngTorchload. Xem A1_EXPERT_SELECTED_ENGINEERING_REPORT01.md. Không graph efficacy/mainmatrix/refit/calibration/CUDAclaim.\n')
    with OUTPUT.open('xb') as stream:stream.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
    print(json.dumps(dict(inventory_sha256=sha(OUTPUT),copies=len(copies),copy_bytes=sum(v['bytes'] for v in copies.values()),native_binary_refs=len(refs))))


if __name__=='__main__':main()
