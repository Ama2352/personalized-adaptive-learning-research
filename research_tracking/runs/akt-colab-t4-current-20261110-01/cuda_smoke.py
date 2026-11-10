"""Kiểm CUDA bốn biến thể, mỗi biến thể 48 target giả và hai bước Adam."""
from dataclasses import replace, asdict
import gc
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback

ROOT = Path('/content/kltn-current-t4-20261110-01')
OUT = ROOT/'experiments/akt/results/current-t4-four-variant-smoke-20261110-01'
OUT.mkdir(parents=True, exist_ok=False)
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests/akt')]
started = time.monotonic()
result = dict(status='FAILED', scope='CUDA smoke on handmade fixtures, not fitted research evidence',
    model_checkpoint_generated=False, main_training=False, modal_spend_usd=0, variants=[])


def state_hash(module):
    digest = hashlib.sha256()
    for name, tensor in module.state_dict().items():
        digest.update(name.encode())
        digest.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


try:
    import torch
    import numpy as np
    import psutil
    import test_research_graph_model as fixture
    from knowledge_tracing.akt.config import ResearchCUDAExecutionProfile
    from knowledge_tracing.akt import research_graph_condition as conditions
    from knowledge_tracing.akt import research_graph_context as contexts
    from knowledge_tracing.akt import research_graph_model as models
    from knowledge_tracing.akt.research_simulator_data import iter_research_windows

    assert os.environ['CUBLAS_WORKSPACE_CONFIG'] == ':4096:8'
    assert torch.__version__ == '2.7.1+cu126'
    assert torch.cuda.is_available() and torch.cuda.device_count() == 1
    assert torch.cuda.get_device_name(0) == 'Tesla T4'
    profile = ResearchCUDAExecutionProfile(2*1024**3)
    total = torch.cuda.get_device_properties(0).total_memory
    torch.cuda.set_per_process_memory_fraction(profile.max_vram_bytes/total, 0)
    torch.use_deterministic_algorithms(True, warn_only=False)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.set_float32_matmul_precision('highest')
    torch.set_num_threads(2)
    before_sources = models.source_inventory()
    initial_hashes = []
    for variant in ('A0', 'A1', 'A2', 'A3'):
        assert time.monotonic()-started < 180
        assert psutil.virtual_memory().available >= 2*1024**3
        torch.manual_seed(42)
        case = fixture.handmade()
        existing = case['condition']
        arguments = dict(variant=variant, graph_mode='none' if variant == 'A0' else 'expert_declared',
            bank=case['bank'], nodes=() if variant == 'A0' else existing.nodes,
            edges=() if variant == 'A0' else existing.edges, train80=existing.train80,
            expected_sources=conditions.source_inventory())
        if variant != 'A0':
            arguments['topology_source_sha256'] = existing.topology_source_sha256
        if variant in ('A2', 'A3'):
            scores = existing.method24_scores
            arguments.update(loaded_scores=scores, expected_method24_training=scores.training,
                expected_scores_sha256=scores.identity)
        condition = conditions.prepare_research_graph_condition(**arguments)
        config = replace(case['config'], device='cuda', max_steps=2)
        index = contexts.prepare_research_graph_context(case['train'], case['encoding'], condition,
            limits=case['index'].limits, fit80_encoding_sha256=case['encoding'].identity,
            context=100, target_block=100)
        adapter = models.ResearchGraphAKTAdapter(config=config, encoding=case['encoding'],
            index=index, condition=condition, cuda_profile=profile)
        initial = state_hash(adapter.native.backbone)
        initial_hashes.append(initial)
        optimizer = torch.optim.Adam(adapter.native.parameters(), lr=config.lr,
            betas=config.betas, eps=config.eps, weight_decay=config.weight_decay,
            foreach=False, fused=False)
        updates = []
        for offset in (0, 4):
            entries = case['entries'][offset:offset+4]
            batch = adapter.collate_training(entries)
            update = adapter.step(batch, optimizer)
            assert update['stepped'] and update['valid_targets'] == 24
            assert update['parameter_updated'] and np.isfinite(update['mean_loss'])
            updates.append(update)
        assert all(torch.isfinite(p).all() for p in adapter.native.parameters())
        for state in optimizer.state.values():
            assert all(torch.isfinite(v).all() for v in state.values() if torch.is_tensor(v))
        prediction_index = contexts.prepare_research_graph_context(case['prediction'], case['encoding'], condition,
            limits=case['index'].limits, fit80_encoding_sha256=case['encoding'].identity,
            context=100, target_block=100)
        adapter.set_context_index(prediction_index)
        windows = tuple(iter_research_windows(case['prediction'], case['encoding'],
            context=100, target_block=100, training=False))
        predictions = adapter.predict_windows(windows)
        assert sum(len(p) for p in predictions) == 6
        assert all(np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all() for p in predictions)
        torch.cuda.synchronize()
        row = dict(variant=variant, initial_backbone_sha256=initial,
            final_backbone_sha256=state_hash(adapter.native.backbone), updates=updates,
            optimized_targets=48, prediction_count=6, predictions=[p.tolist() for p in predictions],
            alpha=None if adapter.native.alpha is None else adapter.native.alpha.item(),
            gate=None if adapter.native.gate is None else dict(
                weight=adapter.native.gate.weight.detach().cpu().tolist(),
                bias=adapter.native.gate.bias.detach().cpu().tolist()),
            peak_vram_allocated_bytes=torch.cuda.max_memory_allocated(),
            peak_vram_reserved_bytes=torch.cuda.max_memory_reserved())
        assert row['final_backbone_sha256'] != initial
        result['variants'].append(row)
        (OUT/'progress.json').write_text(json.dumps(result, indent=2)+'\n')
        del optimizer, adapter, batch, entries
        gc.collect()
        torch.cuda.empty_cache()
    assert len(set(initial_hashes)) == 1
    assert models.source_inventory() == before_sources
    result.update(status='CUDA_FOUR_VARIANT_SMOKE_PASS', gpu_name=torch.cuda.get_device_name(0),
        torch_version=torch.__version__, execution_profile=asdict(profile),
        total_optimizer_updates=8, total_optimized_targets=192, total_predictions=24,
        same_initial_backbone=True, source_unchanged=True)
except BaseException as error:
    result.update(error_type=type(error).__name__, error=str(error))
    (OUT/'failure.log').write_text(traceback.format_exc())
finally:
    result['elapsed_seconds'] = time.monotonic()-started
    (OUT/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'variants'}), flush=True)
sys.exit(0 if result['status'] == 'CUDA_FOUR_VARIANT_SMOKE_PASS' else 1)
