"""Fixture CUDA A0/A3, so sánh hai epoch liên tục với save rồi fresh-process restore."""
import argparse
from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time
import traceback

ROOT = Path('/content/kltn-current-t4-20261110-01')
BASE = ROOT/'experiments/akt/results/t4-checkpoint-recovery-20261110-01'
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests/akt')]
parser = argparse.ArgumentParser()
parser.add_argument('--variant', choices=('A0', 'A3'), required=True)
parser.add_argument('--phase', choices=('continuous', 'interrupted', 'resumed'), required=True)
args = parser.parse_args()
OUT = BASE/args.variant/args.phase
OUT.mkdir(parents=True, exist_ok=False)
started = time.monotonic()
result = dict(status='FAILED', variant=args.variant, phase=args.phase,
    scope='Handmade complete-epoch CUDA checkpoint check, not research fit or lifecycle recovery',
    main_training=False, modal_spend_usd=0)


def events(value):
    with (OUT/'events.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(value, sort_keys=True)+'\n')
        stream.flush()
        os.fsync(stream.fileno())


try:
    import numpy as np
    import torch
    import test_research_graph_model as fixture
    from knowledge_tracing.akt import research_graph_checkpoint as checkpoint
    from knowledge_tracing.akt import research_graph_condition as conditions
    from knowledge_tracing.akt import research_graph_context as contexts
    from knowledge_tracing.akt import research_graph_model as models
    from knowledge_tracing.akt.config import ResearchCUDAExecutionProfile
    from knowledge_tracing.akt.training import train_epoch
    from knowledge_tracing.akt.research_simulator_data import iter_research_windows

    def rng_hashes():
        state = checkpoint._rng(cuda_profile=cuda)
        return dict(python=hashlib.sha256(json.dumps(state['python']).encode()).hexdigest(),
            numpy=hashlib.sha256(json.dumps(state['numpy']).encode()).hexdigest(),
            cpu=hashlib.sha256(state['torch'].numpy().tobytes()).hexdigest(),
            cuda=hashlib.sha256(state['cuda']['state'].numpy().tobytes()).hexdigest())

    assert os.environ['CUBLAS_WORKSPACE_CONFIG'] == ':4096:8'
    assert torch.__version__ == '2.7.1+cu126' and torch.cuda.device_count() == 1
    assert torch.cuda.get_device_name(0) == 'Tesla T4'
    cuda = ResearchCUDAExecutionProfile(2*1024**3)
    torch.cuda.set_per_process_memory_fraction(cuda.max_vram_bytes/torch.cuda.get_device_properties(0).total_memory, 0)
    torch.use_deterministic_algorithms(True, warn_only=False)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.set_float32_matmul_precision('highest')
    torch.set_num_threads(2)
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    source_before = checkpoint.source_inventory()
    case = fixture.handmade()
    setup = case['condition']
    if args.variant == 'A0':
        setup = conditions.prepare_research_graph_condition(variant='A0', graph_mode='none',
            bank=case['bank'], nodes=(), edges=(), train80=setup.train80,
            expected_sources=conditions.source_inventory())
    config = replace(case['config'], device='cuda', max_steps=4,
        run_id='t4-checkpoint-'+args.variant.lower()+'-'+args.phase, output_dir=OUT)
    index = contexts.prepare_research_graph_context(case['train'], case['encoding'], setup,
        limits=case['index'].limits, fit80_encoding_sha256=case['encoding'].identity,
        context=100, target_block=100)
    adapter = models.ResearchGraphAKTAdapter(config=config, encoding=case['encoding'],
        index=index, condition=setup, cuda_profile=cuda)
    optimizer = torch.optim.Adam(adapter.native.parameters(), lr=config.lr,
        betas=config.betas, eps=config.eps, weight_decay=config.weight_decay,
        foreach=False, fused=False)
    tracker = checkpoint.GraphAdamParticipation(adapter, optimizer, event_sink=events)
    placeholder = 'a'*64
    profile = checkpoint.GraphCheckpointProfile(
        hashlib.sha256((ROOT/checkpoint.PROTOCOL21_PATH).read_bytes()).hexdigest(),
        checkpoint.RECIPE_SHA256, placeholder, placeholder, tracker.initial_backbone_sha256,
        placeholder, 'selected_fit_candidate', None)
    identity = checkpoint.graph_checkpoint_identity(config=config, encoding=case['encoding'],
        condition=setup, index=index, profile=profile, cuda_profile=cuda)
    limits = checkpoint.GraphCheckpointLimits(64*1024**2, 1024**2, 64*1024**2)
    (OUT/'identity.json').write_text(json.dumps(identity, indent=2)+'\n')
    first_epoch = 1
    if args.phase == 'resumed':
        tracker.close()
        prior = json.loads((BASE/args.variant/'interrupted/result.json').read_text())
        assert prior['status'] == 'CHECKPOINT_SAVED_AT_EPOCH1'
        reference = prior['checkpoint']
        directory = ROOT/reference['directory']
        inspected = checkpoint.inspect_graph_epoch_state(directory, expected_identity=identity,
            expected_complete_sha256=reference['complete_sha256'], limits=limits)
        random.seed(901)
        np.random.seed(902)
        torch.manual_seed(903)
        tracker = checkpoint.restore_graph_epoch_state(inspected, fresh_adapter=adapter,
            fresh_owned_optimizer=optimizer, expected_identity=identity,
            profile=profile, limits=limits, event_sink=events)
        assert rng_hashes() == prior['rng_hashes']
        assert tracker.completed_epochs == 1 and tracker.returned == 2 and tracker.optimized_targets == 48
        first_epoch = 2
    last_epoch = 1 if args.phase == 'interrupted' else 2
    receipts = []
    for epoch in range(first_epoch, last_epoch+1):
        assert time.monotonic()-started < 75
        tracker.begin_epoch(epoch)
        stats = train_epoch(adapter, lambda: iter(case['entries']), optimizer=optimizer, epoch=epoch,
            budget=dict(max_steps=2, max_targets=48, max_seconds=45., max_rss_bytes=2*1024**3,
                min_available_ram_bytes=2*1024**3), batch_factory=tracker.collate,
            progress_callback=tracker.progress)
        assert stats.complete and stats.valid_targets == 48 and stats.optimizer_steps == 2
        receipt = tracker.finish_epoch(stats)
        receipts.append(asdict(receipt))
    before_save = rng_hashes()
    if args.phase != 'continuous':
        saved = checkpoint.save_graph_epoch_state(OUT/'checkpoint', adapter=adapter,
            optimizer=optimizer, participation=tracker, epoch_receipt=receipt,
            expected_identity=identity, profile=profile, limits=limits)
        assert rng_hashes() == before_save
        result['checkpoint'] = dict(directory=saved.directory.relative_to(ROOT).as_posix(),
            checkpoint_sha256=saved.checkpoint_sha256, complete_sha256=saved.complete_sha256)
    result.update(rng_hashes=before_save, receipts=receipts,
        completed_epochs=tracker.completed_epochs, optimized_targets=tracker.optimized_targets,
        optimizer_steps=tracker.returned, initial_backbone_sha256=tracker.initial_backbone_sha256,
        model_sha256=receipt.model_sha256, optimizer_sha256=receipt.optimizer_sha256,
        participation=dict(tracker.counts))
    prediction_index = contexts.prepare_research_graph_context(case['prediction'], case['encoding'], setup,
        limits=case['index'].limits, fit80_encoding_sha256=case['encoding'].identity,
        context=100, target_block=100)
    adapter.set_context_index(prediction_index)
    windows = tuple(iter_research_windows(case['prediction'], case['encoding'],
        context=100, target_block=100, training=False))
    predictions = adapter.predict_windows(windows)
    assert sum(map(len, predictions)) == 6 and all(np.isfinite(p).all() for p in predictions)
    result['predictions'] = [p.tolist() for p in predictions]
    assert checkpoint.source_inventory() == source_before
    result['source_unchanged'] = True
    if args.phase == 'resumed':
        control = json.loads((BASE/args.variant/'continuous/result.json').read_text())
        for field in ('model_sha256', 'optimizer_sha256', 'rng_hashes', 'participation',
                'completed_epochs', 'optimized_targets', 'optimizer_steps', 'predictions'):
            assert result[field] == control[field], field
        result['continuous_resumed_exact'] = True
    result.update(status='CHECKPOINT_SAVED_AT_EPOCH1' if args.phase == 'interrupted' else 'COMPLETE',
        gpu_name=torch.cuda.get_device_name(0), peak_vram_allocated_bytes=torch.cuda.max_memory_allocated(),
        pid=os.getpid(), actual_cuda_profile=asdict(cuda))
    tracker.close()
except BaseException as error:
    result.update(error_type=type(error).__name__, error=str(error))
    (OUT/'failure.log').write_text(traceback.format_exc())
finally:
    result['elapsed_seconds'] = time.monotonic()-started
    (OUT/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('receipts', 'participation')}), flush=True)
sys.exit(0 if result['status'] in ('COMPLETE', 'CHECKPOINT_SAVED_AT_EPOCH1') else 1)
