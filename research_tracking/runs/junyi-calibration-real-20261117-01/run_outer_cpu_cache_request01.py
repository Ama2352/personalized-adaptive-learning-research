"""EntryCPUlocal/Colab cho requestouterprepared, không tự chạy dữ liệu gốc."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts/akt'/f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', type=Path, required=True)
    options = parser.parse_args()
    request = json.loads(options.request.read_text(encoding='utf-8'))
    if request.get('status') != 'READY_OUTER_PREPARED_SOURCE_REQUEST':
        raise ValueError('Prepared source request required; draft cannot execute')
    source = Path(request['source_root'])
    sys.path.insert(0, str(source/'src'))
    from knowledge_tracing.akt.config import PROJECT_ROOT, DataPaths
    from knowledge_tracing.akt.research_junyi_inference import (
        inspect_cpu_refit_export, JunyiCPUInferenceBudget)
    from knowledge_tracing.akt.research_junyi_calibration import inference_source_identity
    if PROJECT_ROOT != source or inference_source_identity() != request['inference_source_sha256']:
        raise ValueError('Actual new source packet differs from request')
    compatibility = load_script('free_outer_evaluation')
    if inference_source_identity() != compatibility.NEW_SOURCE:
        raise ValueError('Only approved guard release is accepted')
    budget = JunyiCPUInferenceBudget(**request['inspection_budget'])
    assets = {}
    if set(request['export_indexes']) != {'A0', 'A1', 'A2', 'A3'}:
        raise ValueError('Four pinned model export indexes required')
    for variant, entry in request['export_indexes'].items():
        path = Path(entry['path'])
        assets[variant] = inspect_cpu_refit_export(path.parent,
            expected_index_sha256=entry['sha256'],
            output=source/'experiments/akt/results'/(request['cache_tag']+'-'+variant.lower()),
            run_id=request['cache_tag']+'-'+variant.lower(), budget=budget)
        if assets[variant]['index']['identity']['variant'] != variant:
            raise ValueError('Variant mapping differs')
    paths = DataPaths(**{name:Path(value) for name,value in request['data_paths'].items()})
    helper = load_script('prepare_junyi_outer_caches')
    result = helper.prepare_outer_caches(assets, paths, source_pins=request['source_pins'],
        cache_tag=request['cache_tag'], receipt_path=Path(request['receipt_path']),
        disk_budget_root=Path(request['disk_budget_root']), **request['cache_budget'])
    if 'torch' in sys.modules:
        raise ValueError('CPU preparation must not import Torch')
    receipt = Path(request['receipt_path'])
    print(json.dumps(dict(status=result['status'], receipt_path=str(receipt),
        receipt_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),
        counts=result['windows']['summary'], oov=result['oov_targets_recounted'], torch_imported=False)))


if __name__ == '__main__':
    main()
