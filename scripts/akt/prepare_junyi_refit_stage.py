"""Kiểm và đóng snapshot refit90 trên CPU trước khi cấp GPU."""
import argparse
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'experiments/akt')]


def validate_worker(worker, request):
    """Khóa cầu nối vào request đã ghim, tránh thay cấu hình khi đóng gói."""
    from run_junyi_refit import pinned
    if (worker.get('purpose') != 'refit90' or request.get('phase') != 'junyi_refit90'
            or worker.get('variant') != request.get('variant')
            or worker.get('variant') not in ('A0', 'A1', 'A2', 'A3')):
        raise ValueError('Explicit matching A0–A3 refit worker required')
    if (worker['config'] != json.loads(pinned(request['config']).read_text())
            or worker['profile'] != json.loads(pinned(request['cuda_profile']).read_text())):
        raise ValueError('Inline worker differs from pinned config/profile')
    plan = json.loads(pinned(request['epoch_plan']).read_text())
    if (type(worker.get('frozen_epochs')) is not int
            or worker['frozen_epochs'] != plan['candidates'][worker['variant']]['epochs']
            or worker['logical_run_id'] != worker['config']['run_id']):
        raise ValueError('Frozen epoch count or logical run differs')


def prepare(request, destination):
    from junyi_staged_io import prepare_project, sha, write_new, verify_project
    from run_junyi_refit import pinned, prepare_inputs
    from knowledge_tracing.akt.authorization import require_gate2_evidence
    worker = request['worker']
    refit = json.loads(pinned(worker['refit_request']).read_text())
    validate_worker(worker, refit)
    inputs = prepare_inputs(refit)
    prepare_project(ROOT, request, destination)
    project = destination.resolve() / 'project'
    # Kiểm đúng byte nguồn và mọi asset đã sao chép trước khi nghiệm thu snapshot.
    verify_project(destination)
    gate = require_gate2_evidence(SimpleNamespace(source_commit=worker['config']['source_commit']),
        project_root=project, gate2_report=project / 'artifacts/akt/preflight/gate2-current.json',
        lock_file=project / refit['lock_file']['path'])
    if sha(project / refit['lock_file']['path']) != refit['lock_file']['sha256']:
        raise ValueError('Snapshot runtime lock differs')
    checked = dict(status='PASS_LOCAL_STAGE_INPUTS', phase='junyi_refit90', variant=worker['variant'],
        targets=inputs['inputs'].targets, frozen_epochs=worker['frozen_epochs'],
        plan_identity=inputs['plan']['identity'], encoding_identity=inputs['encoding'].identity,
        gate_report_sha256=gate['report_sha256'], inputs_sha256=sha(destination / 'INPUTS.json'),
        worker_request_sha256=sha(project / 'gpu-stage-request.json'), gpu_started=False)
    write_new(destination / 'CPU_CHECK.json', checked)
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(json.loads(args.request.read_text(encoding='utf-8')), args.snapshot),
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
