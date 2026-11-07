"""Fixture subprocess riêng cho test, không phải entrypoint thực nghiệm.

Chỉ thay nguồn dữ liệu/Gate1/Gate2 bằng fixture tổng hợp. Authorization/caps,
CLI parser, watchdog process, optimizer, checkpoint, export chạy mã thật.
"""

from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    from knowledge_tracing.akt import config as config_module, runner, watchdog, authorization
    from knowledge_tracing.akt import training, prediction
    from knowledge_tracing.akt.types import KTEvent, LearnerEvents
    from knowledge_tracing.akt.splits import InnerSplit

    root = Path(os.environ['AKT_TEST_FIXTURE_ROOT']).resolve()
    config_module.PROJECT_ROOT = root
    runner.PROJECT_ROOT = root
    prediction.PROJECT_ROOT = root
    report = {'source': {'commit': config_module.SOURCE_COMMIT}, 'lock_sha256': 'fixture-lock',
              'runtime_report_sha256': 'fixture-runtime'}

    def identity(config):
        return {**report, 'config_sha256': authorization.config_hash(config),
                'build_hashes': {'fixture': 'same-source'}, 'assignments_sha256': 'fixture-assignments'}

    # Giữ actual require_authorization, chỉ cô lập external provenance fixtures.
    watchdog.require_authorization = lambda config, approval: authorization.require_authorization(
        config, approval, identity_fn=identity)
    runner._authorization_identity = identity
    runner._require_gate2_evidence = lambda config: {'status': 'PASS_CPU', 'fixture': True}
    runner.preflight = lambda config: report
    snapshot = lambda: {'pid': os.getpid(), 'process_rss_bytes': 128 * 1024**2,
        'process_peak_rss_bytes': 128 * 1024**2, 'system_available_ram_bytes': 4 * 1024**3,
        'system_total_ram_bytes': 8 * 1024**3}
    watchdog.memory_snapshot = runner.memory_snapshot = training.memory_snapshot = snapshot

    def load(config, **unused):
        train = tuple(LearnerEvents(f'train-{n}', 1, tuple(
            KTEvent(f'train-{n}', 'A', i, n*100+i, (i+n) % 2, 0, 1) for i in range(17))) for n in range(5))
        val = (LearnerEvents('val', 2, tuple(KTEvent('val', 'A' if i != 3 else 'OOV', i,
            i+1000, i % 2, 0, 2) for i in range(9))),)
        split = InnerSplit(tuple(item.user_id for item in train), ('val',), 0, 'fixture-split')
        return {**report, 'config_sha256': authorization.config_hash(config)}, split, train, val
    runner._load_phase_inputs = load

    original_write = runner._write_json
    interrupt = os.environ.get('AKT_TEST_INTERRUPT', '')

    def write(path, value):
        original_write(path, value)
        if (interrupt == 'batch-exit' and path.name == 'recovery-progress.json'
                and 'epoch-1-step-2-' in value['checkpoint']):
            os._exit(23)  # Không chạy worker exception/finally, parent phải giữ snapshot đã commit.
    runner._write_json = write
    export = runner.export_predictions

    def fail_export(*args, **kwargs):
        if interrupt == 'export':
            raise InterruptedError('fixture export failure after selection')
        return export(*args, **kwargs)
    runner.export_predictions = fail_export

    popen = subprocess.Popen

    def spawn(command, **kwargs):
        if command[1:3] == ['-m', 'knowledge_tracing.akt.cli']:
            command = [command[0], str(Path(__file__).resolve()), *command[3:]]
        return popen(command, **kwargs)
    watchdog.subprocess.Popen = spawn
    return watchdog.main(sys.argv[1:])


if __name__ == '__main__':
    raise SystemExit(main())
