"""Chạy một điều kiện đồ thị Main60 trong allocation sáu lượt đã được duyệt."""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent.parent.parent
BUNDLE = ROOT / 'research_tracking/runs/modal-akt-graph-selected-20261112-01'
os.environ['MODAL_CONFIG_PATH'] = str(ROOT / 'artifacts/akt/private/modal.toml')
os.environ['MODAL_PROFILE'] = 'kltn'
import modal
from modal_a0_gpu_pilot import remote_train, sha


async def read_billing():
    from modal.client import _Client
    from modal_proto import api_pb2
    from google.protobuf.timestamp_pb2 import Timestamp
    from google.protobuf.json_format import MessageToDict
    client = await _Client.from_env()
    try:
        start = Timestamp()
        start.FromDatetime(datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0))
        response = await asyncio.wait_for(client._stub.WorkspaceBillingSummary(
            api_pb2.WorkspaceBillingSummaryRequest(start_timestamp=start)), 15)
        return dict(observed_at_utc=datetime.now(timezone.utc).isoformat(),
                    billing=MessageToDict(response, preserving_proto_field_name=True))
    finally:
        await client._close()


def prepare(candidate_id):
    allocation = json.loads((BUNDLE / 'allocation.json').read_text())
    assert allocation['status'] == 'USER_APPROVED'
    assert allocation['conservative_six_run_compute_usd'] < allocation['authorized_batch_usd'] <= 2.5
    request_path = BUNDLE / allocation['candidate_requests'][candidate_id]
    request = json.loads(request_path.read_text())
    assert request['candidate_id'] == candidate_id
    assert sha(BUNDLE / 'gpu_graph_worker.py') == request['worker_sha256'] == allocation['worker_sha256']
    assert sha(ROOT / request['condition_file']) == request['condition_sha256']
    inputs = {
        '/opt/gpu_a0_lifecycle_worker.py': BUNDLE / 'gpu_graph_worker.py',
        '/opt/candidate-request.json': request_path,
        '/opt/checkpoint_sync.py': ROOT / 'experiments/akt/modal_artifact_sync.py',
        '/opt/cpu-gate.zip': ROOT / 'experiments/akt/results/modal-cpu-preflight-20261112-04/artifacts.zip',
        '/opt/public-corpus.zip': ROOT / 'artifacts/akt/modal/main60-akt-inputs-20261112-01/research-inputs.zip',
    }
    assert sha(inputs['/opt/public-corpus.zip']) == allocation['research_inputs_sha256']
    verified = json.loads((ROOT / 'research_tracking/runs/modal-akt-recovery-20261112-01/main60-a0-verification.json').read_text())
    assert verified['status'] == 'VERIFIED_MAIN60_A0_CUDA_SELECTED'
    return allocation, request, inputs


def main():
    from modal_budget_guard import (ModalAppBudgetGuard, ModalRunDeadline,
                                    PendingOwnedModalApp, stop_owned_app_cli)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', required=True,
                        choices=('A1_EXPERT', 'A1_LEARNED', 'A2_EXPERT', 'A2_LEARNED', 'A3_EXPERT', 'A3_LEARNED'))
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    allocation, request, inputs = prepare(args.candidate)
    run_id = request['run_id']
    pins = {name: sha(path) for name, path in inputs.items()}
    print(json.dumps(dict(candidate_id=args.candidate, run_id=run_id,
                         paid_execution_requested=args.run, input_hashes=pins)), flush=True)
    if not args.run:
        return
    lock_file = BUNDLE / 'active-run.lock'
    with lock_file.open('x', encoding='utf-8') as stream:
        json.dump(dict(run_id=run_id, candidate_id=args.candidate), stream)
    # Giữ lock nếu có lỗi để xác minh App/artifact trước khi mở lượt kế tiếp.
    billing = asyncio.run(read_billing())
    metered = float(billing['billing']['metered_cost'])
    assert metered + allocation['reserved_usd_per_run'] < allocation['workspace_monthly_free_credit_ceiling_usd']
    assert metered - allocation['baseline_metered_usd'] + allocation['reserved_usd_per_run'] < allocation['authorized_batch_usd']
    reservations = []
    for path in BUNDLE.glob('*-reservation.json'):
        reservation = json.loads(path.read_text())
        prior = ROOT / 'experiments/akt/results' / reservation['run_id'] / 'receipt.json'
        assert prior.exists(), 'Có lượt chưa đóng. Không mở thêm container.'
        assert json.loads(prior.read_text())['status'] == 'CUDA_GRAPH_SELECTED_MAIN60_COMPLETE', 'Dừng batch sau lỗi.'
        reservations.append(reservation)
    assert len(reservations) < allocation['max_approved_runs']
    assert (len(reservations) + 1) * allocation['reserved_usd_per_run'] < allocation['authorized_batch_usd']
    native = ROOT / 'experiments/akt/results' / run_id
    assert not native.exists() or {p.name for p in native.iterdir()} <= {'execution.log'}
    native.mkdir(exist_ok=True)
    (native / 'billing-before.json').write_text(json.dumps(billing, indent=2) + '\n')
    with (BUNDLE / (args.candidate.lower() + '-reservation.json')).open('x') as stream:
        json.dump(dict(run_id=run_id, candidate_id=args.candidate,
                       reserved_usd=allocation['reserved_usd_per_run'], inputs=pins,
                       created_at_utc=datetime.now(timezone.utc).isoformat()), stream, indent=2)
    deadline = ModalRunDeadline(800)
    image = modal.Image.from_id('im-ldjZsYO21pzaupmQXGLhnS')
    for name, path in inputs.items():
        image = image.add_local_file(path, name, copy=True)
    app = modal.App('kltn-akt-' + run_id)
    volume = modal.Volume.from_name('kltn-akt-' + run_id, create_if_missing=True, version=2)
    function = app.function(image=image, gpu=allocation['gpu_options'], cpu=(0.25, 2), memory=(4096, 8192),
                            timeout=840, startup_timeout=60, retries=0, max_containers=1,
                            volumes={'/durable': volume})(remote_train)
    binding = PendingOwnedModalApp(run_id, app.name, lambda: app.app_id)
    with ModalAppBudgetGuard(binding, deadline, stop_app=stop_owned_app_cli,
                             diagnostic_path=native/'app-budget-guard.json') as guard:
        with modal.enable_output(), app.run(environment_name='main'):
            guard.remaining()
            call = function.spawn(pins, run_id, True, args.candidate)
            (native / 'dispatch.json').write_text(json.dumps(dict(call_id=call.object_id)) + '\n')
            receipt = call.get(timeout=guard.remaining())
            (native / 'remote-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    archive = native / 'artifacts.zip'
    with archive.open('xb') as stream:
        for block in volume.read_file(run_id + '/artifacts.zip'):
            stream.write(block)
    assert archive.stat().st_size == receipt['archive_bytes'] and sha(archive) == receipt['archive_sha256']
    with zipfile.ZipFile(archive) as saved:
        assert saved.testzip() is None
        inventory = json.loads(saved.read('SHA256.json'))
        assert set(saved.namelist()) == set(inventory) | {'SHA256.json'}
        for name, expected in inventory.items():
            with saved.open(name) as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == expected['sha256']
    receipt['download_inventory_verified'] = True
    (native / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(dict(status=receipt['status'], candidate_id=args.candidate,
                         epochs=receipt.get('terminal', {}).get('complete_fit_epochs'),
                         selected_epoch=receipt.get('terminal', {}).get('selected_epoch'),
                         archive_bytes=receipt['archive_bytes'], downloaded_verified=True)), flush=True)
    assert receipt['status'] == 'CUDA_GRAPH_SELECTED_MAIN60_COMPLETE'
    lock_file.unlink()


if __name__ == '__main__':
    main()
