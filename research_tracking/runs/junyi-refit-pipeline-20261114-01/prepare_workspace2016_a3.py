"""Đưa checkpoint Drive đã kiểm vào Volume mới trước cấp H100."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_new(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    assert os.environ['MODAL_PROFILE'] == 'kltn2016'
    assert Path(os.environ['MODAL_CONFIG_PATH']).resolve() == (ROOT / 'artifacts/akt/private/modal2016.toml').resolve()
    sys.path.insert(0, str(ROOT / 'experiments/akt'))
    from modal_junyi_refit import validate_refit_execution
    from modal_graph_selected import read_billing
    from modal_junyi_main_selected import validate_project_budget
    from modal_junyi_staged import validate_stage_project_budget
    import modal

    imported = ROOT / 'experiments/akt/results/colab-junyi-a3-refit-20261115-023-import'
    proof = read(imported / 'COMPLETE.json')
    assert proof['status'] == 'LOCAL_IMPORTED_CHECKPOINT_VERIFIED'
    assert proof['complete_epochs'] == 8 and proof['partial_optimizer_step'] == 1874
    previous = read(imported / 'remote-inventory.json')
    snapshot = ROOT / 'artifacts/akt/staged/junyi-a3-refit-short-20261115-01'
    worker = read(snapshot / 'project/gpu-stage-request.json')
    identifier = 'junyi-a3-refit-h100-ws2016-20261115-01'
    request = dict(status='USER_APPROVED',
        approval_reference='Người dùng15/11 cung cấp workspace2016/30USD và yêu cầu tiếp tục H100, checkpoint Drive023 đã kiểm trênD.',
        execution_id='modal-' + identifier, allocation_id=identifier, gpu='H100',
        image_id='im-ldjZsYO21pzaupmQXGLhnS', child_timeout_seconds=420,
        function_timeout_seconds=430, watchdog_seconds=900,
        authorized_batch_usd=.70, reserved_usd_per_run=.70,
        resume_checkpoint=proof['checkpoint'], resume_sha256=proof['checkpoint_sha256'],
        resume_inventory=(imported / 'remote-inventory.json').relative_to(ROOT).as_posix(),
        gpu_cpu_max=2, gpu_memory_max_mib=8192, active_function_budget=True,
        reuse_local_outputs=False, workspace_name='honguyenminhsang2016',
        project_budget_file='research_tracking/COMPUTE_BUDGET_WORKSPACE2016.json')
    resource = validate_refit_execution(request, worker)
    billing = asyncio.run(read_billing())
    assert billing['workspace_name'] == request['workspace_name']
    ledger_path = ROOT / request['project_budget_file']
    ledger = read(ledger_path)
    assert ledger['new_allocations'] == []
    ledger['new_allocations'] = [dict(id=identifier, cap_usd=.70, purpose='A3 refit từepoch9step1874 tới9epoch')]
    admission = validate_stage_project_budget(ledger, request, billing, validate_project_budget)
    write_new(HERE / 'workspace2016-budget-before-a3-01.json', dict(billing=billing, admission=admission, resource=resource))
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    write_new(HERE / 'a3-refit-workspace2016-execution01.json', request)
    volume = modal.Volume.from_name('kltn-staged-' + worker['logical_run_id'] + '-outputs', create_if_missing=True, version=2)
    selected = {name: pin for name, pin in previous['files'].items()
                if name.startswith('outputs/' + worker['logical_run_id'] + '/')}
    for name, pin in selected.items():
        path = imported / 'files' / name
        assert path.stat().st_size == pin['bytes'] and sha(path) == pin['sha256']
    with volume.batch_upload(force=False) as batch:
        for name in selected:
            batch.put_file(imported / 'files' / name, '/' + name)
    remote = 'outputs/' + proof['checkpoint'].removeprefix('experiments/akt/results/')
    digest = hashlib.sha256()
    size = 0
    for block in volume.read_file(remote):
        digest.update(block)
        size += len(block)
    assert digest.hexdigest() == proof['checkpoint_sha256']
    write_new(HERE / 'workspace2016-checkpoint-volume01.json', dict(status='PASS_CHECKPOINT_UPLOADED_BEFORE_GPU',
        workspace=request['workspace_name'], volume=volume.name, files=len(selected), checkpoint=remote,
        checkpoint_sha256=digest.hexdigest(), checkpoint_bytes=size, gpu_started=False))
    print(json.dumps(dict(status='READY_FOR_BOUNDED_H100', remaining_optimizer_steps=166,
                         request='a3-refit-workspace2016-execution01.json', reserved_usd=.70)))


if __name__ == '__main__':
    main()
