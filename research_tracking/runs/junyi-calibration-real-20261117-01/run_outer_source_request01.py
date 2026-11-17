"""EntryCPUsourceouter; chỉ chạy khi root đổi requestdraft thànhREADY đã kiểmquota."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', required=True, type=Path)
    args = parser.parse_args()
    request = json.loads(args.request.read_text(encoding='utf-8'))
    if request.get('status') != 'READY_OUTER_SOURCE_PREPARATION':
        raise ValueError('Root-reviewed READY source request required')
    source = Path(request['source_root'])
    sys.path.insert(0, str(source/'src'))
    from knowledge_tracing.akt.config import PROJECT_ROOT, DataPaths
    from knowledge_tracing.akt.research_junyi_calibration import inference_source_identity
    from knowledge_tracing.akt.research_junyi_inference import inspect_cpu_refit_export, JunyiCPUInferenceBudget
    if (PROJECT_ROOT != source or inference_source_identity() != request['inference_source_sha256']
            or inference_source_identity() != '7c72414eedf9507d514430aed4734f0a192ab14914a4984b17fdfcbfebd39123'):
        raise ValueError('Actual approved guard-release source required')
    budget = JunyiCPUInferenceBudget(**request['inspection_budget'])
    if set(request['export_indexes']) != {'A0','A1','A2','A3'}:
        raise ValueError('Four pinned portable export indexes required')
    assets = {}
    for variant, entry in request['export_indexes'].items():
        path = Path(entry['path'])
        asset = inspect_cpu_refit_export(path.parent, expected_index_sha256=entry['sha256'],
            output=source/'experiments/akt/results'/('outer-source-'+variant.lower()),
            run_id='outer-source-'+variant.lower(), budget=budget)
        if asset['index']['identity']['variant'] != variant:
            raise ValueError('Export variant mapping mismatch')
        assets[variant] = asset
    spec = importlib.util.spec_from_file_location('outer_source_operational',
        ROOT/'scripts/akt/prepare_junyi_outer_source.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module._sha(Path(module.__file__)) != request['source_writer_sha256']:
        raise ValueError('Root-reviewed source writer pin changed')
    paths = DataPaths(**{name:Path(value) for name,value in request['raw_data_paths'].items()})
    result = module.prepare_outer_source(assets, paths,
        source_repo_root=Path(request['original_repo_root']),
        inventory_path=Path(request['source_inventory']['path']),
        inventory_sha256=request['source_inventory']['sha256'],
        output_root=Path(request['output_root']), disk_budget_root=Path(request['disk_budget_root']),
        **request['expected_counts'], **request['source_budget'])
    if 'torch' in sys.modules:
        raise ValueError('Source CPU worker must not import Torch')
    manifest = Path(request['output_root'])/'manifest.json'
    print(json.dumps(dict(status=result['status'], manifest_path=str(manifest),
        manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
        source_pins=dict(canonical_manifest=hashlib.sha256(manifest.read_bytes()).hexdigest(),
            split_manifest=hashlib.sha256(paths.split_manifest.read_bytes()).hexdigest()),
        counts=result['counts'], data_paths=result['data_paths'], torch_imported=False)))


if __name__ == '__main__':
    main()
