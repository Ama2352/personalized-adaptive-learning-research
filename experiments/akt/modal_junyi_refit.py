"""Modal refit dùng lại image CPU, budget guard, stop barrier và artifact IO."""
import argparse
import json
import os
from pathlib import Path

from modal_junyi_staged import ROOT, run, validate_resource_budget


def validate_refit_execution(request, worker):
    if (worker.get('purpose') != 'refit90' or worker.get('variant') not in ('A0', 'A1', 'A2', 'A3')
            or worker['config']['phase'] != 'junyi-research' or worker['config']['batch_size'] != 128
            or worker['config']['seed'] != 42 or type(worker.get('frozen_epochs')) is not int
            or not 1 <= worker['frozen_epochs'] <= 20
            or not isinstance(worker.get('refit_request'), dict)):
        raise ValueError('Pinned A0–A3 refit90 worker and frozen epoch budget required')
    return validate_resource_budget(request, worker)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if not args.run:
        print(json.dumps(dict(status='NO_CLOUD_ACTION', snapshot=str(args.snapshot))))
        return
    temporary = ROOT / 'artifacts/akt/runtime/modal-client-temp'
    temporary.mkdir(parents=True, exist_ok=True)
    os.environ.update(TEMP=str(temporary), TMP=str(temporary), TMPDIR=str(temporary),
        MODAL_CONFIG_PATH=str(ROOT / 'artifacts/akt/private/modal.toml'), MODAL_PROFILE='kltn')
    import tempfile
    tempfile.tempdir = str(temporary)
    print(json.dumps(run(args.snapshot, json.loads(args.request.read_text()),
        worker_entrypoint='run_junyi_refit_gpu_stage.py', execution_validator=validate_refit_execution)))


if __name__ == '__main__':
    main()
