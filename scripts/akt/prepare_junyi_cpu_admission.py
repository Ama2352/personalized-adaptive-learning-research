"""Kiểm train window cache trên CPU trước cấp GPU và xuất handoff có SHA."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-seconds', type=int, default=360)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    assert 1 <= args.max_seconds <= 600
    destination = args.output.resolve()
    assert destination.is_relative_to(ROOT / 'artifacts/akt') and not destination.exists()
    if not args.worker:
        subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()), '--request', str(args.request),
                        '--output', str(destination), '--max-seconds', str(args.max_seconds), '--worker'],
                       check=True, timeout=args.max_seconds, cwd=ROOT)
        return
    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.akt.research_junyi_selection import load_full_selected_cache
    from knowledge_tracing.akt.research_junyi_engineering import file_sha
    from knowledge_tracing.akt.research_junyi_data import load_prepared_junyi_encoding
    from knowledge_tracing.akt.research_junyi_window_cache import JunyiWindowCacheSession, write_cpu_admission
    request = json.loads(args.request.read_text(encoding='utf-8'))
    data = request['inputs']
    # Chỉ các cache phái sinh đã được duyệt. Không đọc dataset gốc hoặc Holdout.
    paths = {}
    for name in ('selected_cache_root', 'roles_path', 'encoding_file', 'encoding_receipt', 'train_window_cache'):
        relative = Path(data[name])
        assert not relative.is_absolute() and '..' not in relative.parts
        paths[name] = (ROOT / relative).resolve()
        assert paths[name].is_relative_to(ROOT / 'artifacts/akt')
    started = time.monotonic()
    inputs = load_full_selected_cache(paths['selected_cache_root'], paths['roles_path'],
        expected_manifest_sha256=data['selected_cache_manifest_sha256'], expected_roles_sha256=data['roles_sha256'])
    view, targets = inputs.train, inputs.train_targets
    if request.get('phase') == 'junyi_refit90':
        from knowledge_tracing.akt.research_junyi_refit import refit_view
        plan_pin = request['epoch_plan']
        plan_path = ROOT / plan_pin['path']
        assert file_sha(plan_path) == plan_pin['sha256']
        plan = json.loads(plan_path.read_text(encoding='utf-8'))
        assert plan['selected_inputs_identity'] == inputs.identity
        assert plan['roles_identity'] == inputs.train.roles.identity
        refit = refit_view(inputs)
        view, targets = refit.view, refit.targets
    encoding = load_prepared_junyi_encoding(paths['encoding_file'], paths['encoding_receipt'],
        view=view, source_data_sha256=inputs.source_identity,
        expected_file_sha256=data['encoding_sha256'], expected_receipt_sha256=data['encoding_receipt_sha256'])
    session = JunyiWindowCacheSession(paths['train_window_cache'], view, encoding, inputs.source_identity,
        targets, data['train_window_manifest_sha256'])
    destination.parent.mkdir(parents=True, exist_ok=True)
    write_cpu_admission(session, destination)
    result = dict(status='CPU_STRICT_ADMISSION_COMPLETE', output=str(destination),
                  sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
                  train_targets=targets, phase_scope=view.scope, records=session.strict_records_verified,
                  wall_seconds=time.monotonic()-started, gpu_used=False)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
