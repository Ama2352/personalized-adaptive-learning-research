"""Ghép confidence thật và cấu hình frozen thành request CPU A2/A3, chưa dispatch."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CONFIDENCE = ROOT/'artifacts/akt/confidence/full-train80-20261114-02'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save_new(path, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('Request đã đóng khác byte, cần version mới')
        return
    with path.open('xb') as stream:
        stream.write(raw)


def main():
    complete = json.loads((CONFIDENCE/'COMPLETE.json').read_text())
    if complete['status'] != 'COMPLETE_FULL_TRAIN80_CONFIDENCE':
        raise ValueError('Cần confidence TRAIN80 hoàn chỉnh')
    if sha(CONFIDENCE/'confidence.json') != complete['confidence_sha256']:
        raise ValueError('Confidence khác byte đã đóng')
    if sha(CONFIDENCE/'fit-manifest.json') != complete['fit_artifact_sha256']:
        raise ValueError('Manifest fit khác byte đã đóng')
    for variant in ('A2', 'A3'):
        plan = json.loads((ROOT/'research_tracking/runs/junyi-a2-a3-preparation-20261113-01'/
                          (variant.lower()+'-preparation.json')).read_text())
        config = dict(plan['training_config'])
        run_id = 'junyi-'+variant.lower()+'-expert-selected-20261114-01'
        config.update(run_id=run_id, output_dir='/opt/kltn/experiments/akt/results/'+run_id,
                      execution_enabled=True)
        worker = dict(variant=variant, logical_run_id=run_id, config=config,
            profile=plan['numeric_profile'], inputs=plan['inputs'], purpose='main_selected',
            workload_epochs=config['max_epochs'], validation_batch_size=128,
            graph_file=plan['topology_file'], graph_sha256=plan['topology_sha256'],
            comparison_reference_file=plan['comparison_reference'].replace('\\', '/'),
            comparison_reference_sha256=plan['comparison_reference_sha256'],
            train_admission_file=plan['train_cpu_admission']['path'],
            train_admission_sha256=plan['train_cpu_admission']['sha256'],
            confidence_file=(CONFIDENCE/'confidence.json').relative_to(ROOT).as_posix(),
            confidence_sha256=complete['confidence_sha256'],
            confidence_fit_artifact=(CONFIDENCE/'fit-manifest.json').relative_to(ROOT).as_posix(),
            a0_model_index='experiments/akt/results/model-export-a0-batch128-20261112-01/MODEL_INDEX.json',
            a1_model_index='experiments/akt/results/model-export-a1-batch128-20261113-01/MODEL_INDEX.json',
            runtime_lock_file='artifacts/akt/runtime-locks/locked-cu126.txt',
            runtime_lock_sha256='60dad3de310562db4f775d1977e2097a6d1c8f57a22bfa4f7afc3ceab35cc45a')
        save_new(HERE/(variant.lower()+'-worker-base.json'), worker)
    print(json.dumps(dict(status='REAL_CONFIDENCE_WORKER_BASES_PREPARED', gpu_started=False)))


if __name__ == '__main__':
    main()
