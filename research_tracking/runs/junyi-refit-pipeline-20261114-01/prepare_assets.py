"""Lập yêu cầu CPU/cache và config refit từ model đã nghiệm thu."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'experiments/akt')]
from junyi_staged_io import sha, write_new


def pin(path):
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=sha(path))


def main():
    cache = ROOT / 'artifacts/akt/window-cache/full-refit90-20261114-01'
    manifest = json.loads((cache / 'manifest.json').read_text())
    assert json.loads((cache / 'COMPLETE.json').read_text())['manifest_sha256'] == sha(cache / 'manifest.json')
    assert manifest['summary']['target_rows'] == 14947674 and manifest['summary']['learners'] == 142621
    assert manifest['summary']['unseen_targets'] == 0
    previous = json.loads((ROOT / 'artifacts/akt/staged/junyi-a3-expert-20261114-03/project/gpu-stage-request.json').read_text())
    data = dict(previous['inputs'])
    encoding = ROOT / 'artifacts/akt/window-cache/full-refit90-20261114-01.encoding.json'
    receipt = encoding.with_suffix('.receipt.json')
    data.update(encoding_file=encoding.relative_to(ROOT).as_posix(), encoding_sha256=sha(encoding),
        encoding_receipt=receipt.relative_to(ROOT).as_posix(), encoding_receipt_sha256=sha(receipt),
        train_window_cache=cache.relative_to(ROOT).as_posix(), train_window_manifest_sha256=sha(cache / 'manifest.json'))
    plan = pin(HERE / 'epoch-plan.json')
    write_new(HERE / 'cpu-admission-request.json', dict(phase='junyi_refit90', epoch_plan=plan, inputs=data))
    profile = HERE / 'cuda-profile.json'
    write_new(profile, previous['profile'])
    for variant, folder in (
        ('A0', 'model-export-a0-batch128-20261112-01'), ('A1', 'model-export-a1-batch128-20261113-01'),
        ('A2', 'model-export-a2-batch128-20261114-01'), ('A3', 'model-export-a3-batch128-20261114-01')):
        index = ROOT / 'experiments/akt/results' / folder / 'MODEL_INDEX.json'
        config = json.loads(index.read_text())['metadata']['identity']['config']
        config.update(project_root='.', source_root='artifacts/akt/dependencies/upstream',
            run_id=f'junyi-{variant.lower()}-refit-20261114-01',
            output_dir=f'experiments/akt/results/junyi-{variant.lower()}-refit-20261114-01',
            max_train_users=142621, max_targets_per_side=14947674, max_total_targets=14947674 * 9)
        config_file = HERE / f'config-{variant.lower()}.json'
        write_new(config_file, config)
        if variant == 'A0':
            continue
        request = dict(phase_scope='refit_union90', variant=variant,
            selected_cache_root=data['selected_cache_root'], roles_file=data['roles_path'],
            selected_manifest_sha256=data['selected_cache_manifest_sha256'], roles_sha256=data['roles_sha256'],
            encoding_file=data['encoding_file'], encoding_receipt=data['encoding_receipt'],
            encoding_sha256=data['encoding_sha256'], encoding_receipt_sha256=data['encoding_receipt_sha256'],
            encoding80_file=previous['inputs']['encoding_file'], encoding80_receipt=previous['inputs']['encoding_receipt'],
            encoding80_sha256=previous['inputs']['encoding_sha256'],
            encoding80_receipt_sha256=previous['inputs']['encoding_receipt_sha256'],
            train_window_cache=data['train_window_cache'], train_window_manifest_sha256=data['train_window_manifest_sha256'],
            graph_file=previous['graph_file'], graph_sha256=previous['graph_sha256'],
            epoch_plan=plan, selected_index=pin(index),
            output_file=f'artifacts/akt/graph-context-cache/full-refit90-20261114-01/{variant.lower()}-train.sqlite',
            max_seconds=1200, max_rss_bytes=1536 * 1024**2)
        if variant != 'A1':
            request.update(confidence_file=previous['confidence_file'], confidence_sha256=previous['confidence_sha256'])
        write_new(HERE / f'graph-request-{variant.lower()}.json', request)
    write_new(HERE / 'assets-preparation.json', dict(status='CPU_ASSETS_REQUESTS_PREPARED',
        window_manifest=pin(cache / 'manifest.json'), encoding=pin(encoding), receipt=pin(receipt),
        source_targets=14947674, learners=142621, items=717, gpu_used=False))
    print(json.dumps(dict(status='CPU_ASSETS_REQUESTS_PREPARED')))


if __name__ == '__main__':
    main()
