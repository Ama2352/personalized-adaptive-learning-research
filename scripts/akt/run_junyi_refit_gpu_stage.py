"""Numerical refit worker trong image đã kiểm, cùng budget/stop barrier selected."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from run_junyi_gpu_stage import prepare_runtime_report
from run_junyi_refit import pinned, prepare_inputs, configure_cuda
from knowledge_tracing.akt.research_junyi_engineering import file_sha, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--execution', type=Path, required=True)
    args = parser.parse_args()
    worker = json.loads(args.request.read_text())
    execution = json.loads(args.execution.read_text())
    operation = ROOT / 'experiments/akt/results' / (execution['execution_id'] + '-operation')
    if not operation.is_dir() or file_sha(args.request) != execution['worker_request_sha256']:
        raise ValueError('Owned controller operation and pinned worker request required')
    started = time.monotonic()
    result = dict(status='FAILED', refit_completed=False, calibration_completed=False)
    try:
        if worker['purpose'] != 'refit90' or not execution.get('approval_reference'):
            raise PermissionError('Authorized refit execution required')
        os.environ.update(GIT_CONFIG_COUNT='3', GIT_CONFIG_KEY_0='core.fsmonitor', GIT_CONFIG_VALUE_0='false',
            GIT_CONFIG_KEY_1='safe.directory', GIT_CONFIG_VALUE_1=str(ROOT / 'artifacts/akt/dependencies/upstream'),
            GIT_CONFIG_KEY_2='core.autocrlf', GIT_CONFIG_VALUE_2='false', GIT_OPTIONAL_LOCKS='0',
            GIT_TERMINAL_PROMPT='0', PYTHONDONTWRITEBYTECODE='1')
        request = json.loads(pinned(worker['refit_request']).read_text())
        if (request['variant'] != worker['variant'] or request['phase'] != 'junyi_refit90'
                or json.loads(pinned(request['config']).read_text()) != worker['config']
                or json.loads(pinned(request['cuda_profile']).read_text()) != worker['profile']):
            raise ValueError('Worker and prepared refit inputs differ')
        context = prepare_inputs(request)
        config, profile = context['config'], context['profile']
        if config.run_id != worker['logical_run_id'] or context['plan']['candidates'][worker['variant']]['epochs'] != worker['frozen_epochs']:
            raise ValueError('Logical run or frozen epoch mismatch')
        configure_cuda(profile, config.threads)
        import torch
        if execution['gpu'] not in torch.cuda.get_device_name(0):
            raise ValueError('Actual GPU differs from execution resource')
        from knowledge_tracing.akt.authorization import require_gate2_evidence, GATE2_CURRENT
        from knowledge_tracing.akt.research_junyi_refit import refit_grant_binding, run_junyi_refit
        lock = pinned(request['lock_file'])
        runtime = prepare_runtime_report(ROOT, operation, config.source_root, lock, 'cuda')
        gate = require_gate2_evidence(config, lock_file=lock)
        binding = refit_grant_binding(config=config, inputs=context['inputs'], encoding=context['encoding'],
            variant=context['variant'], plan=context['plan'], window_cache=context['window_cache'],
            gate_sha256=gate['report_sha256'], runtime_sha256=file_sha(runtime),
            graph_condition=context['graph_condition'], graph_cache=context['graph_cache'])
        grant = dict(status='USER_APPROVED', approval_reference=execution['approval_reference'], binding=binding)
        write_json(operation / 'authorization.json', grant)
        if execution.get('resume_checkpoint') is not None:
            resume = ROOT / execution['resume_checkpoint']
            if not resume.resolve().is_relative_to((config.output_dir / 'checkpoints').resolve()):
                raise ValueError('Resume outside logical refit output')
            context.update(resume=resume, expected_resume_sha256=execution['resume_sha256'])
        terminal = run_junyi_refit(**context, grant=grant, runtime_report=runtime, lock_file=lock,
                                    gate2_report=GATE2_CURRENT)
        result.update(status=terminal['status'], terminal=terminal,
            refit_completed=terminal['status'] == 'JUNYI_REFIT90_COMPLETE', gpu=torch.cuda.get_device_name(0))
    except BaseException:
        (operation / 'failure.log').write_text(traceback.format_exc(), encoding='utf-8')
        raise
    finally:
        result['wall_seconds'] = time.monotonic() - started
        write_json(operation / 'result.json', result)


if __name__ == '__main__':
    main()
