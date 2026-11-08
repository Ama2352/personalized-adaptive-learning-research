"""Metadata/hash closure only; không chạy lại process, tests hoặc model."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_bytes())
def dump(path,value):
    with path.open('x',encoding='utf-8') as handle:
        json.dump(value,handle,ensure_ascii=False,indent=2);handle.write('\n')

if __name__=='__main__':
    run=load(PREP/'trial01/run.json')
    assert (run['tests'],run['failures'],run['errors'],run['skipped'])==(6,0,0,0)
    assert run['status']=='PASS_PURE_WINDOWS_OWNED_JOB_TESTS'
    assert run['source_before_sha256']==run['source_after_sha256']
    assert run['cumulative_seconds']==run['elapsed_seconds']<=20
    for path,digest in run['source_before_sha256'].items():
        assert sha(ROOT/path)==digest
        assert sha(PREP/'trial01/source-before'/Path(path).name)==digest
    assert 'Ran 6 tests in 1.849s' in (PREP/'trial01/unittest.log').read_text()
    outcomes=[]
    for mode in ('normal','descendant','timeout'):
        receipt=load(PREP/f'receipt-{mode}.json');folder=PREP/f'actual-{mode}'
        launch,ready,go=(load(folder/name) for name in ('launch.json','ready.json','GO.json'))
        assert receipt['cleanup_accepted'] is True and receipt['cleanup_errors']==[]
        assert receipt['popen_handle_closed'] is True and receipt['job_active_after_cleanup']==0
        assert receipt['GO_released'] is True and receipt['actual_worker_in_job_before_GO'] is True
        assert ready['worker']==go['worker']==receipt['actual_worker']
        assert launch['nonce']==ready['nonce']==go['nonce'] and launch['job_name']==go['job_name']==receipt['job_name']
        assert sha(folder/'ready.json')==go['ready_sha256']
        assert launch['parent']==receipt['parent']
        assert sha(PREP/'synthetic_worker.py')==ready['worker_sha256']==receipt['worker_sha256']
        assert ready['helper_sha256']==receipt['helper_sha256']==sha(ROOT/'scripts/research/windows_owned_worker.py')
        assert ready['forbidden_imports']==[] and Path(ready['prefix'])==ROOT/'.venv'
        assert Path(ready['entry'])==ROOT/'.venv/Scripts/python.exe'
        for name,digest in receipt['output_sha256'].items():assert sha(folder/name)==digest
        assert receipt['elapsed_seconds']<=receipt['max_seconds']
        if mode=='timeout':
            assert receipt['accepted'] is False and receipt['returncode']!=0
            assert not (folder/'body.json').exists()
            assert any(error['type']=='TimeoutError' for error in receipt['errors'])
        else:
            assert receipt['accepted'] is True and receipt['worker_returncode_before_cleanup']==0
            body=load(folder/'body.json')
            assert body['forbidden']==[] and body['gate']['worker']==receipt['actual_worker']
            assert body['gate']['ready_sha256']==go['ready_sha256']
            if mode=='descendant':
                assert body['descendant_in_job'] is True and receipt['job_active_before_cleanup']>0
        outcomes.append(dict(mode=mode,accepted=receipt['accepted'],elapsed_seconds=receipt['elapsed_seconds'],
            actual_worker_in_job_before_GO=True,cleanup_accepted=True,job_active_after_cleanup=0,popen_handle_closed=True))
    prior=ROOT/'research_tracking/runs/rq1-history-availability-20261108-01'
    prior_sha=sha(prior/'manifest.json')
    assert prior_sha=='e34307cbf499b8639412cb4c0375e36d8a6f996ad46aa6d075e5c6d8dc24ac77'
    reference=dict(existing_bundle=prior.relative_to(ROOT).as_posix(),manifest_sha256=prior_sha,
        parent_verified_git_commit='d7d7ec8',original_outcome=load(prior/'outcome.json'),
        policy='Reference existing immutable negatives; do not duplicate or rewrite old raw data.')
    dump(PREP/'prior-negative-reference.json',reference)
    proof=dict(status='VERIFIED_PURE_WINDOWS_JOB_PROCESS_EVIDENCE_NOT_NATIVE_PROOF',tests=6,failures=0,errors=0,skips=0,
        unittest_seconds=1.849,controller_seconds=run['elapsed_seconds'],cumulative_seconds=run['cumulative_seconds'],
        cap_seconds=20,source_sha256=run['source_before_sha256'],actual_process_modes=outcomes,
        native_model_collector_gpu_remote_calls=0,generic_caller_max_seconds=600,startup_gate_max_seconds=10,
        long120_or600_runtime_tested=False,old_failures_referenced_not_relabelled=True)
    dump(PREP/'final-verification.json',proof)
    selected=[ROOT/'scripts/research/windows_owned_worker.py',
        ROOT/'research_tracking/reports/windows_owned_worker_readiness_20261108.md',PREP/'test_launcher.py',
        PREP/'run_tests.py',PREP/'synthetic_worker.py',Path(__file__),PREP/'prior-negative-reference.json',PREP/'final-verification.json']
    selected.extend(PREP/'trial01'/name for name in ('reservation.json','run.json','unittest.log'))
    selected.extend(sorted((PREP/'trial01/source-before').iterdir()))
    for mode in ('normal','descendant','timeout'):
        selected.append(PREP/f'receipt-{mode}.json')
        selected.extend(sorted((PREP/f'actual-{mode}').iterdir()))
    assert all(p.is_file() and not p.is_symlink() for p in selected)
    inventory=[dict(source=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256_before_copy=sha(p)) for p in selected]
    dump(PREP/'copy-inventory-before.json',dict(inputs=inventory))
    os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=str(ROOT))
    with record_evidence_run(ROOT,'windows-owned-worker-engineering-20261108-01',
        metadata=dict(kind='actual-windows-pure-synthetic-job-ownership-engineering',tests_passed=6,failures=0,errors=0,skips=0,
            controller_seconds=run['elapsed_seconds'],cumulative_budget_seconds=20,native_model_collector_remote_calls=0,
            actual_process_modes=outcomes,prior_negative_manifest_sha256=prior_sha,
            generic_max600_not_runtime_tested=True,short_gate_max_seconds=10),
        sources=[*selected,prior/'manifest.json'],
        note='''# Windows owned worker — pure process proof

Một lượt root đã chạy:6methods PASS,0fail/error/skip; controller2,1453567s/20s. Normal và sleeping-descendant/rootRC0 được accepted; timeout sauGO được rejected như thiết kế nhưng owned Jobempty/handlesclosed. Không native/model/collector/Torch/GPU/remote hoặc actual120/600runtime. Generic600/shortgate10 chỉ là interface bounds, không execution authority.

Giữ source/test/controller/READY/GO/body/logs/receipts và SHA trước=sau copy. Unknown provisional PID/ancestry đóng handle, không terminate unrelated PID. Actual worker được xác minh exact Job trướcGO; cleanup cả khi shimRC0. Receipt accepted chỉ process ownership, không scientific acceptance.

Hai negatives trước (availability01FAILED_PRE_NATIVE +probeUNKNOWN) giữ tại rq1-history-availability-20261108-01, manifest e34307cbf499b8639412cb4c0375e36d8a6f996ad46aa6d075e5c6d8dc24ac77, rootcommitd7d7ec8; không copy lại hoặc relabel. prior-negative-reference.json ghi exactbindings. Không sửa science worker/outer/reader hoặc sharedtracking/Git. Caller vẫn kiểm source/plan/outputs/resource authority và final elapsed khi integrate native; timer/cooperative deadline không hardOSquota attestation.
''') as target:
        copied={}
        for index,(source,row) in enumerate(zip(selected,inventory),1):
            digest=row['sha256_before_copy']
            if digest not in copied:
                destination=target/f'input-{index:02d}__{source.name}'
                with destination.open('xb') as handle:handle.write(source.read_bytes())
                copied[digest]=destination
            destination=copied[digest]
            row.update(destination=destination.name,sha256_after_copy=sha(destination),source_sha256_after_copy=sha(source))
            assert row['sha256_before_copy']==row['sha256_after_copy']==row['source_sha256_after_copy']
            assert row['bytes']==destination.stat().st_size
        with (target/'copy-inventory.json').open('x',encoding='utf-8') as handle:
            json.dump(dict(input_aliases=len(inventory),unique_copies=len(copied),copies=inventory),handle,ensure_ascii=False,indent=2)
            handle.write('\n')
    result=dict(**verify_evidence_bundle(target),manifest_sha256=sha(target/'manifest.json'),
        physical_files=len(list(target.iterdir())),input_aliases=len(inventory),unique_copies=len(copied),
        helper_sha256=sha(ROOT/'scripts/research/windows_owned_worker.py'),
        report_sha256=sha(ROOT/'research_tracking/reports/windows_owned_worker_readiness_20261108.md'))
    dump(PREP/'closure.json',result)
    print(json.dumps(result))
