"""ROOT-only đóng bằng chứng GKT selected; đọc opaque hashes, không Torch/load/test."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
RUN_ID='gkt-selected-engineering-20261110-01'
DESTINATION=ROOT/'research_tracking/runs'/RUN_ID
TERMINAL=PREP/'gkt-selected-fit03/outer-final.json'
NATIVE=ROOT/'experiments/gkt/results/gkt-selected-engineering10x84-20261110-01'
FIXED=(
    'prepare_gkt_selected_positive01.py','run_prepare_gkt_selected_positive01.py',
    'materialize_gkt_selected_positive01.py','gkt_selected_positive01_packet.json',
    'prepare_gkt_selected_positive02.py','run_prepare_gkt_selected_positive02.py',
    'materialize_gkt_selected_positive02.py','gkt_selected_positive02_packet.json',
    'materialize_gkt_selected_positive03.py','prepare_gkt_operational_retry03.py',
    'check_gkt_selected_fit01.py','run_gkt_selected_fit01.py',
    'check_gkt_selected_fit02.py','run_gkt_selected_fit02.py',
    'check_gkt_selected_fit03.py','run_gkt_selected_fit03.py',
    'check_gkt_wrapper_restoration01.py','check_gkt_wrapper_restoration02.py','check_gkt_wrapper_restoration03.py',
    'gkt-wrapper-restoration-precheck02.json','gkt-wrapper-restoration-precheck03.json',
    'gkt_selected_fit02_request.ROOT.json','gkt_selected_fit03_request.ROOT.json',
    'gkt_native_positive_derivative_before01.json','gkt_native_positive_sources01.json',
    'gkt_native_positive_sources02.json','gkt_native02_before_operational03_inventory.json',
    'gkt_positive_derivative_sources_before01.json','gkt_positive_dry_source_inventory01.json',
    'gkt_positive_dry_source_inventory02.json','GKT_NATIVE_POSITIVE_HANDOFF02.md',
    'GKT_SELECTED_CANDIDATES_HANDOFF01.md','GKT_SELECTED_PRODUCER_SOURCE_PROPOSAL01.md',
    'ROOT_GKT_SELECTED_ENGINEERING02_ACTUAL_FIT_REVIEW.md','ROOT_GKT_OPERATIONAL_RETRY03_REVIEW.md',
    'gkt-role-parent-before01.json','gkt-materializer03-cli-startup01-note.json',
    'gkt_light_admission03.py','gkt_light_admission04.py','gkt_light_admission05.py',
    'gkt-light-admission03.json','gkt-light-admission04.json','gkt-light-admission05.json',
)
FLAT_DIRECTORIES=(
    'gkt-positive01-static-reject-before02','gkt-positive-packet-before-correction01',
    'gkt-native01-static-monitor-hold-before02',
    'gkt-selected-positive-package02','gkt-selected-positive-package02-owned',
    'gkt-selected-materialization03','gkt-operational-retry03-preparation',
    'gkt-wrapper-restoration-precheck02-dispatch','gkt-wrapper-restoration-precheck03-dispatch',
    'gkt-selected-fit02','gkt-selected-fit02-owned','gkt-selected-fit03','gkt-selected-fit03-owned',
)
SOURCE_FILES=(
    'src/knowledge_tracing/gkt/research_execution.py',
    'src/knowledge_tracing/gkt/research_runner.py','tests/gkt/test_research_selected.py',
    'docs/thesis_recovery/29_GKT_RESEARCH_NUMERICAL_RECIPE_V1.md',
)
REFERENCE_MANIFESTS=(
    'research_tracking/runs/gkt-research-model-trainer-20261110-01/manifest.json',
    'research_tracking/runs/gkt-research-checkpoint-20261110-01/manifest.json',
    'research_tracking/runs/sakt-selected-metadata-20261110-01/manifest.json',
    'research_tracking/runs/owned-job-resource-exit-guard-20261110-01/manifest.json',
    'research_tracking/runs/akt-current-gate183-20261110-01/manifest.json',
)


def need(ok,message):
    if not ok:raise ValueError(message)


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):
    need(path.is_file() and path.stat().st_size<=2**20,'bounded metadata')
    return json.loads(path.read_bytes())


def raw(value):
    return (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()


def physical(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and '..' not in path.parts,'workspace path')
    cursor=ROOT
    for part in path.relative_to(ROOT).parts:
        cursor/=part
        need(not cursor.is_symlink() and not getattr(cursor,'is_junction',lambda:False)(),'physical path')
    need(path.resolve()==path,'same physical path')
    return path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--terminal-sha256',required=True)
    parser.add_argument('--dry',action='store_true')
    args=parser.parse_args()
    need(Path(sys.prefix).resolve()==ROOT/'.venv','repository venv only')
    need(not DESTINATION.exists(),'exclusive new bundle')
    need(sha(physical(TERMINAL))==args.terminal_sha256,'Root external actual terminal SHA')
    terminal=read(TERMINAL)
    accepted=terminal['status']=='ACCEPTED_ACTUAL_GKT_SELECTED_ONLY_ENGINEERING'
    need(accepted or terminal['status']=='REJECTED_GKT_KEEP_PARTIAL','actual final status, never pending')
    receipt=terminal['owned_receipt']
    need(receipt is not None and receipt['cleanup_accepted'] is True
         and receipt['job_active_after_cleanup']==0,'actual terminal Job0')
    if accepted:
        need(terminal['errors']==[] and receipt['accepted'] is True and receipt['returncode']==0
             and terminal['environment_restored'] is True,'actual accepted native wrapper')
    request=read(PREP/'gkt_selected_fit03_request.ROOT.json')
    worker=read(PREP/'gkt-selected-fit03/result.json')
    need(terminal['request_sha256']==sha(PREP/'gkt_selected_fit03_request.ROOT.json')
         and terminal['worker_result']==worker,'actual request and child correspondence')
    prior=read(PREP/'gkt-selected-fit02/result.json')
    need(prior['error']['message']=='GKT preallocation RAM floor'
         and prior['observer']['installed_after_actual_lazy_tools'] is False
         and prior['observer']['training_targets']==0,'preserved preallocation failure02, not fitted')
    paths=[PREP/name for name in FIXED]+[ROOT/name for name in SOURCE_FILES]
    for name in FLAT_DIRECTORIES:
        directory=physical(PREP/name)
        need(directory.is_dir(),'required actual evidence directory '+name)
        paths.extend(sorted(path for path in directory.iterdir() if path.is_file()))
    # Reference-only the earlier cold62 proofs and all dependencies/runtime/corpus.
    # No recursive traversal of temp/cache, no opaque checkpoint deserialization.
    references={name:sha(physical(ROOT/name)) for name in REFERENCE_MANIFESTS}
    dependencies={}
    for field in ('source_pins','input_pins','runtime_pins'):
        dependencies[field]=dict(request[field])
        for name,digest in request[field].items():
            path=Path(name) if Path(name).is_absolute() else physical(ROOT/name)
            need(sha(path)==digest,'current source/input/runtime reference '+name)
    auth=physical(ROOT/request['authorization_file'])
    need(sha(auth)==request['authorization_sha256'],'unchanged genuine auth')
    paths.append(auth)
    native_references={}
    for name,record in worker['native_outputs'].items():
        path=physical(ROOT/name)
        need(path.is_relative_to(NATIVE) and path.stat().st_size==record['bytes']
             and sha(path)==record['sha256'],'actual opaque native output')
        native_references[name]=dict(record)
        if path.suffix!='.pt':paths.append(path)
    if accepted:
        need(native_references and not (NATIVE/'failure.json').exists(),'complete native output population')
        actual={p.relative_to(ROOT).as_posix() for p in NATIVE.rglob('*') if p.is_file()}
        need(actual==set(native_references),'exact accepted native file population')
    paths.append(Path(__file__).resolve())
    copies={}
    for path in dict.fromkeys(paths):
        physical(path)
        need(path.is_file() and path.stat().st_size<=2**20,'small source/raw log only')
        alias=(path.relative_to(PREP).as_posix() if path.is_relative_to(PREP)
               else path.relative_to(ROOT).as_posix()).replace('/','__')
        need(alias not in copies,'unique flat copy alias')
        copies[alias]=dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size)
    need(sum(row['bytes'] for row in copies.values())<=24*2**20,'compact24MiB bundle')
    facts=dict(status=terminal['status'],accepted=accepted,outer_seconds=terminal['elapsed_seconds'],
        worker_seconds=worker['elapsed_seconds'],resources=worker['resources'],observer=worker['observer'],
        prior02_error=prior['error'],prior02_resources=prior['resources'],
        corpus_fit_scope='8train672/selection84/calibration84metadata-only',
        full_main_matrix_completed=False,refit_or_calibration=False,cuda_verified=False)
    note=('# GKT selected engineering trên corpus10×84\n\n'
        +'Terminal thực tế '+terminal['status']+'.\n\n'
        +'Giữ dry02 thực, materialize03, precheck02/03 stdlib và failure02 trước NN. '
        +'Failure02 có primary RAM4GiB và secondary audit đọc pseudo-path <unknown> lúc định dạng traceback, '
        +'không nới read guard. Mẫu admission03 đạt ngưỡng ghi trong rawfile, admission04 không đạt headroom256MiB, '
        +'admission05 đạt. Raw03 ghi extra128MiB, cả ba giá trị thực vẫn trên4GiB+256MiB. '
        +'Các dấu admission là snapshot, không thay kiểm RAM thật ở normal entry.\n\n'
        +'Recipe29 giữ GKT concept28/expert31/width32/BN-D5/batch4 nguyên trajectory, seed42, '
        +'Adam0.001 và response-pooled binary64 log loss. Chỉ selected train80/raw selection10 trên engineering8/1/1. '
        +'Không đổi hyperparameters, không Main60/refit/calibration/Junyi/Holdout/CUDA/Modal.\n\n'
        +'Lỗi CLI ROOT thiếu --materialize và dry01 tuple-call bị bắt bằng review tĩnh được phân biệt với actual failure02. '
        +'Giữ raw receipt/source byte-exact và inventory trước/sau copy. Guard Win5 gốc chưa xác định nguyên nhân; '
        +'probe/canary nằm bundle tham chiếu, không nhân đôi. Checkpoint .pt chỉ tham chiếu SHA, không Torch.load. '
        +'Cold62/model11/trainer8/checkpoint28 và Gate183 giữ phạm vi bằng chứng riêng. '
        +'Xem acceptance.json để đọc actual counts, epochs, timings và tài nguyên của terminal này.\n')
    outputs=sorted([*copies,'README.md','execution.log','copy_inventory.json','reference_sources.json','acceptance.json'])
    summary=dict(status='DRY_VERIFIED_NOT_CLOSED',run_id=RUN_ID,outputs_excluding_manifest=len(outputs),
        copies=len(copies),copy_bytes=sum(r['bytes'] for r in copies.values()),
        actual_terminal_sha256=args.terminal_sha256,actual_native_accepted=accepted,new_training_or_test_calls=0)
    if args.dry:
        print(json.dumps(summary,ensure_ascii=False,indent=2));return
    inventory_path=PREP/'gkt_selected_archive_inventory_before01.json'
    with inventory_path.open('xb') as stream:stream.write(raw(dict(summary=summary,copies=copies,references=references)))
    sys.path.insert(0,str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
    sources=list(dict.fromkeys([ROOT/row['path'] for row in copies.values()]+[ROOT/n for n in references]))
    with record_evidence_run(ROOT,RUN_ID,metadata=dict(kind='GKT_selected_engineering',
            actual_native_accepted=accepted,scientific_main_matrix=False),sources=sources,note=note) as directory:
        checked={}
        for alias,row in copies.items():
            source=ROOT/row['path'];payload=source.read_bytes()
            need(hashlib.sha256(payload).hexdigest()==row['sha256'],'source changed before copy')
            with (directory/alias).open('xb') as stream:stream.write(payload)
            need(sha(directory/alias)==sha(source)==row['sha256'],'source/copy after SHA')
            checked[alias]=dict(row,source_after_sha256=sha(source),copy_sha256=sha(directory/alias))
        (directory/'copy_inventory.json').write_bytes(raw(checked))
        (directory/'reference_sources.json').write_bytes(raw(dict(closed_manifests=references,
            dependency_references=dependencies,native_artifacts=native_references)))
        (directory/'acceptance.json').write_bytes(raw(facts))
        need(sha(TERMINAL)==args.terminal_sha256,'terminal unchanged after copy')
        for name,digest in references.items():need(sha(ROOT/name)==digest,'reference unchanged')
        for name,row in native_references.items():need(sha(ROOT/name)==row['sha256'],'opaque native bytes unchanged')
        need(sorted(p.name for p in directory.iterdir() if p.name!='manifest.json')==outputs,'exact output population')
    verification=verify_evidence_bundle(DESTINATION)
    need(verification['artifacts']==len(outputs),'closed exact output count')
    print(json.dumps(dict(summary,verification=verification,manifest_sha256=sha(DESTINATION/'manifest.json'))))


if __name__=='__main__':
    main()
