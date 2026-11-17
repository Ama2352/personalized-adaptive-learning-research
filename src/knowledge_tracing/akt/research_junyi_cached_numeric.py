"""Inference số từ cache đã nghiệm thu CPU; không encode hoặc join nhãn.

Core dùng callback telemetry để kiểm tổng hợp nhẹ. Wrapper CUDA kiểm backend thật
và builder native riêng, không tự cấu hình flags hoặc fallback CPU.
"""
from dataclasses import asdict, dataclass
import json
import math
import os
from pathlib import Path
import time

from .research_junyi_numeric_predictions import (
    NumericWindow, _hash, _root, _sha, write_numeric_shard,
)
from .filesystem import publish_new_file
from .types import UnseenTarget, WindowInputs


@dataclass(frozen=True)
class CachedNumericBudget:
    max_seconds: float
    max_rss_bytes: int
    max_vram_bytes: int
    expected_records: int
    expected_windows: int
    expected_targets: int
    expected_oov_targets: int
    batch_size: int = 128

    def __post_init__(self):
        if type(self.max_seconds) not in (int, float) or not math.isfinite(self.max_seconds) or self.max_seconds <= 0:
            raise ValueError('positive finite wall cap required')
        for name, value in asdict(self).items():
            if name != 'max_seconds' and (type(value) is not int or value < 0):
                raise ValueError('integer nonnegative numeric budget required')
        if (not 1 <= self.batch_size <= 128 or not self.max_rss_bytes or not self.max_vram_bytes
                or self.expected_windows > self.expected_records
                or self.expected_oov_targets > self.expected_targets):
            raise ValueError('invalid cached inference budget')


def run_cached_numeric(predictor, cache, *, graph_cache, phase, binding, roles_sha256, dataset_sha256,
                       output_root, budget, snapshot, setup_seconds=0.0):
    """Core đọc cache hữu hạn → predict_windows → shard xác suất, không labels.

Caller cấp cache CPU-admitted và snapshot thật trong production. Kiểm giới hạn
trước/sau mỗi batch mang tính cooperative; controller vẫn cần timeout/watchdog.
"""
    if type(budget) is not CachedNumericBudget:
        raise ValueError('typed cached numeric budget required')
    if type(setup_seconds) not in (int, float) or not math.isfinite(setup_seconds) or setup_seconds < 0:
        raise ValueError('finite nonnegative setup duration required')
    binding.validate()
    if not _hash(roles_sha256) or not _hash(dataset_sha256):
        raise ValueError('roles and dataset identities required')
    root = _root(output_root)
    if root.exists():
        raise FileExistsError('numeric run root must be new')
    if (cache.admission_receipt is None or not _hash(cache.expected_admission_sha256)
            or not _hash(cache.source_data_sha256)
            or cache.expected_manifest_sha256 != binding.window_manifest_sha256
            or cache.view.identity != binding.phase_sha256
            or cache.encoding.identity != binding.encoding_sha256
            or cache.view.roles.identity != roles_sha256
            or cache.expected_target_rows != budget.expected_targets):
        raise ValueError('CPU admitted cache binding mismatch')
    if (predictor.binding.checkpoint_sha256 != binding.checkpoint_sha256
            or predictor.binding.model_id != binding.variant + '_JUNYI_REFIT'
            or predictor.binding.model_source_sha256 != binding.source_sha256
            or predictor.binding.split_sha256 != roles_sha256
            or predictor.binding.vocabulary_sha256 != binding.encoding_sha256
            or predictor.binding.domain_sha256 != cache.source_data_sha256
            or predictor.adapter.checkpoint_id != binding.checkpoint_id):
        raise ValueError('predictor numeric binding mismatch')
    if binding.variant == 'A0':
        if graph_cache is not None or phase is not None:
            raise ValueError('A0 cannot receive graph augmentation')
    else:
        if (graph_cache is None or phase is None or phase.condition.variant != binding.variant
                or phase.view.identity != binding.phase_sha256):
            raise ValueError('typed graph cache/phase required')
        graph_cache.assert_for(phase)
        graph_binding = json.loads(graph_cache.binding)
        if (graph_binding['dataset_sha256'] != dataset_sha256
                or graph_binding['window_manifest_sha256'] != binding.window_manifest_sha256):
            raise ValueError('graph cache dataset/window binding mismatch')
        if graph_cache.windows != budget.expected_windows or graph_cache.targets != budget.expected_targets - budget.expected_oov_targets:
            raise ValueError('graph cache coverage mismatch')
        predictor.adapter.set_phase(phase, context_cache=graph_cache)
    predictor.assert_boundary()
    cache.assert_boundary()
    if budget.batch_size > predictor.adapter.config.batch_size:
        raise ValueError('prediction batch exceeds frozen model configuration')
    started = time.monotonic()
    samples = []

    def check():
        value = snapshot()
        if (setup_seconds + time.monotonic() - started > budget.max_seconds
                or value['rss_bytes'] > budget.max_rss_bytes
                or value['vram_bytes'] > budget.max_vram_bytes):
            raise RuntimeError('cached numeric resource cap exceeded')
        if any(type(value[name]) is not int or value[name] < 0 for name in ('rss_bytes', 'vram_bytes')):
            raise ValueError('nonnegative actual memory telemetry required')
        samples.append(dict(wall_seconds=time.monotonic() - started, **value))

    check()
    root.mkdir(parents=True)
    shards, pending = [], []
    records = windows = targets = oov = 0
    inference_seconds = numeric_publish_seconds = 0.0

    def flush():
        nonlocal inference_seconds, numeric_publish_seconds
        if not pending:
            return
        check()
        batch_started = time.monotonic()
        probabilities = predictor.adapter.predict_windows(tuple(pending))
        check()
        inference_seconds += time.monotonic() - batch_started
        publish_started = time.monotonic()
        shard = write_numeric_shard(root, f'shard-{len(shards):06d}',
            tuple(NumericWindow.from_window(window) for window in pending), probabilities,
            binding=binding, shard_index=len(shards))
        shards.append(shard)
        pending.clear()
        numeric_publish_seconds += time.monotonic() - publish_started

    for record in cache.iter_windows():
        records += 1
        if type(record) is UnseenTarget:
            oov += 1
            targets += 1
        elif type(record) is WindowInputs:
            windows += 1
            targets += int(record.target_mask.sum())
            pending.append(record)
            if len(pending) == budget.batch_size:
                flush()
        else:
            raise ValueError('prediction cache must exclude training targets')
        if (records > budget.expected_records or windows > budget.expected_windows
                or targets > budget.expected_targets or oov > budget.expected_oov_targets):
            raise ValueError('cached numeric input exceeds coverage')
        if records % budget.batch_size == 0:
            check()
    flush()
    if (records, windows, targets, oov) != (budget.expected_records, budget.expected_windows,
                                           budget.expected_targets, budget.expected_oov_targets):
        raise ValueError('cached numeric full coverage mismatch')
    cache.assert_boundary()
    predictor.assert_boundary()
    if graph_cache is not None:
        graph_cache.assert_for(phase)
    check()
    payload = dict(kind='JUNYI_CACHED_NUMERIC_INFERENCE_V1', status='COMPLETE',
        binding=asdict(binding), roles_sha256=roles_sha256,
        source_data_sha256=cache.source_data_sha256,
        dataset_sha256=dataset_sha256,
        window_admission_sha256=cache.expected_admission_sha256,
        graph_cache_identity=None if graph_cache is None else graph_cache.identity,
        counts=dict(records=records, windows=windows, targets=targets,
                    fitted_targets=targets-oov, oov_targets=oov),
        shards=[dict(manifest_path=str(item.manifest_path), manifest_sha256=item.manifest_sha256) for item in shards],
        wall_seconds=setup_seconds+time.monotonic()-started,
        timings=dict(setup_seconds=setup_seconds, inference_seconds=inference_seconds,
                     numeric_publish_seconds=numeric_publish_seconds,
                     core_seconds=time.monotonic()-started,
                     volume_commit_seconds=None),
        telemetry=dict(samples=samples, peak_rss_bytes=max(row['rss_bytes'] for row in samples),
                       peak_vram_bytes=max(row['vram_bytes'] for row in samples)),
        resource_caps=asdict(budget), volume_commit_required=True)
    temporary, receipt = root/'receipt.partial', root/'RECEIPT.json'
    with temporary.open('x', encoding='utf-8') as stream:
        json.dump(payload, stream, sort_keys=True, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    publish_new_file(temporary, receipt)
    return dict(receipt_path=str(receipt), receipt_sha256=_sha(receipt), counts=payload['counts'])


def run_cuda_cached_numeric(assets, cache, *, graph_cache, phase, binding, dataset_sha256, output_root, budget):
    """CUDA admission thật rồi reuse core. CPU cache/admission phải có trước.

Builder hiện hữu kiểm SUPPORT.zip khi gắn weights; hot loop chỉ đọc input/context
cache và ghi numeric shards. Caller commit Volume rồi trả GPU ngay sau hàm.
"""
    setup_started = time.monotonic()
    from .config import ResearchCUDAExecutionProfile
    from .research_junyi_window_cache import JunyiWindowCacheSession
    from .research_junyi_graph_cache import GraphContextCache
    profile = assets.get('cuda_profile')
    if (type(budget) is not CachedNumericBudget
            or type(profile) is not ResearchCUDAExecutionProfile or assets['config'].device != 'cuda'
            or type(cache) is not JunyiWindowCacheSession
            or (graph_cache is not None and type(graph_cache) is not GraphContextCache)
            or budget.max_vram_bytes != profile.max_vram_bytes):
        raise ValueError('native CUDA profile/cache admission required')
    if cache.admission_receipt is None or not _hash(cache.expected_admission_sha256):
        raise ValueError('CPU admission required before loading CUDA model')
    from .research_junyi_inference import build_cuda_refit_predictor
    from .research_graph_model import _cuda_execution_check
    from .resources import memory_snapshot
    import torch
    _cuda_execution_check(profile, synchronize=True)
    predictor = build_cuda_refit_predictor(assets, domain_sha256=cache.source_data_sha256)

    def actual_snapshot():
        _cuda_execution_check(profile, synchronize=True)
        memory = memory_snapshot()
        return dict(rss_bytes=max(memory['process_rss_bytes'], memory['process_peak_rss_bytes'] or 0),
                    vram_bytes=int(torch.cuda.max_memory_reserved(0)))

    return run_cached_numeric(predictor, cache, graph_cache=graph_cache, phase=phase,
        binding=binding, roles_sha256=cache.view.roles.identity, output_root=output_root,
        dataset_sha256=dataset_sha256, budget=budget, snapshot=actual_snapshot,
        setup_seconds=time.monotonic()-setup_started)
