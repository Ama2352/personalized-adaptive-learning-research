"""Entrypoint refit A0–A3; mặc định kiểm khai báo, --run cần grant/Gate/runtime."""
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.akt.research_junyi_engineering import file_sha


def pinned(entry):
    name = PurePosixPath(entry['path'])
    if (name.is_absolute() or '..' in name.parts or 'private' in name.parts
            or ':' in entry['path'] or '\\' in entry['path']):
        raise ValueError('Owned public project input required')
    path = ROOT.joinpath(*name.parts)
    if not path.resolve().is_relative_to(ROOT) or file_sha(path) != entry['sha256']:
        raise ValueError('Input path or SHA changed')
    return path


def execute(request):
    os.environ.update(CUBLAS_WORKSPACE_CONFIG=':4096:8', CUDA_VISIBLE_DEVICES='0',
        OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    from knowledge_tracing.akt.config import load_config, ResearchCUDAExecutionProfile
    from knowledge_tracing.akt.research_junyi_selection import load_full_selected_cache
    from knowledge_tracing.akt.research_junyi_refit import refit_view, run_junyi_refit
    from knowledge_tracing.akt.research_junyi_data import load_prepared_junyi_encoding
    from knowledge_tracing.akt.research_junyi_window_cache import JunyiWindowCacheSession
    from knowledge_tracing.akt.research_junyi_graph_cache import GraphContextCache
    from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition, JunyiGraphPhaseSession
    from knowledge_tracing.akt.research_junyi_confidence_binding import load_binding
    from knowledge_tracing.shared_kt import PrerequisiteGraph
    profile = ResearchCUDAExecutionProfile(**json.loads(pinned(request['cuda_profile']).read_text()))
    config = load_config(pinned(request['config']), cuda_profile=profile)
    import torch
    from knowledge_tracing.akt.device_budget import configure_cuda_budget
    torch.set_num_threads(config.threads)
    torch.set_default_dtype(torch.float32)
    torch.use_deterministic_algorithms(True, warn_only=False)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.set_float32_matmul_precision('highest')
    configure_cuda_budget(torch.cuda, max_vram_bytes=profile.max_vram_bytes)
    if config.output_dir.resolve().parent != ROOT / 'experiments/akt/results' or config.output_dir.name != config.run_id:
        raise ValueError('Exclusive owned logical refit output required')
    data = request['inputs']
    selected = load_full_selected_cache(ROOT / data['selected_cache_root'], pinned(data['roles']),
        expected_manifest_sha256=data['selected_cache_manifest_sha256'], expected_roles_sha256=data['roles']['sha256'])
    inputs = refit_view(selected)
    plan = json.loads(pinned(request['epoch_plan']).read_text())
    def encoding_for(prefix, view):
        return load_prepared_junyi_encoding(pinned(data[prefix]), pinned(data[prefix + '_receipt']),
            view=view, source_data_sha256=inputs.source_identity,
            expected_file_sha256=data[prefix]['sha256'], expected_receipt_sha256=data[prefix + '_receipt']['sha256'])
    encoding = encoding_for('encoding90', inputs.view)
    admission = data.get('window_admission')
    cache = JunyiWindowCacheSession(ROOT / data['window_cache90'], inputs.view, encoding,
        inputs.source_identity, inputs.targets, data['window_manifest_sha256'], prefetch=True,
        admission_receipt=None if admission is None else pinned(admission),
        expected_admission_sha256=None if admission is None else admission['sha256'])
    condition = graph_cache = None
    variant = request['variant']
    if variant != 'A0':
        origin = encoding_for('encoding80', selected.train)
        topology = json.loads(pinned(request['graph']).read_text())
        confidence = (None if variant == 'A1' else load_binding(pinned(request['confidence']),
            expected_sha256=request['confidence']['sha256']))
        condition = JunyiGraphCondition(encoding,
            PrerequisiteGraph.from_edges(topology['nodes'], topology['corrected_edges']),
            request['graph']['sha256'], variant=variant, confidence=confidence, train80_origin=origin)
        graph_cache = GraphContextCache.open(pinned(request['graph_context_cache90']),
            request['graph_context_cache90']['sha256'], JunyiGraphPhaseSession(condition, inputs.view),
            dataset_sha256=inputs.source_identity, window_manifest_sha256=data['window_manifest_sha256'])
    elif any(key in request for key in ('graph', 'confidence', 'graph_context_cache90')):
        raise ValueError('A0 requires graph-free inputs')
    resume_entry = request.get('resume_checkpoint')
    resume = None if resume_entry is None else pinned(resume_entry)
    if resume is not None and not resume.resolve().is_relative_to(config.output_dir / 'checkpoints'):
        raise ValueError('Resume must belong to the same logical refit')
    return run_junyi_refit(config, profile, inputs, encoding, variant=variant, plan=plan,
        expected_plan_sha256=plan['identity'], grant=json.loads(pinned(request['authorization']).read_text()),
        runtime_report=pinned(request['runtime_report']), lock_file=pinned(request['lock_file']),
        gate2_report=pinned(request['gate2_report']), window_cache=cache,
        graph_condition=condition, graph_cache=graph_cache, resume=resume,
        expected_resume_sha256=None if resume_entry is None else resume_entry['sha256'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--request-sha256')
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    request = json.loads(args.request.read_text(encoding='utf-8'))
    if request.get('phase') != 'junyi_refit90' or request.get('variant') not in ('A0', 'A1', 'A2', 'A3'):
        raise ValueError('Explicit Junyi A0–A3 refit request required')
    if not args.run:
        print(json.dumps(dict(status='REFIT_REQUEST_DECLARED_NOT_EXECUTED', variant=request['variant'],
                              request_sha256=file_sha(args.request))))
        return
    if file_sha(args.request) != args.request_sha256:
        raise ValueError('Pinned execution request required')
    print(json.dumps(execute(request)))


if __name__ == '__main__':
    main()
