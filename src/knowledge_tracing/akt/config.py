"""Cấu hình và giới hạn vùng ghi cho thí nghiệm AKT."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import math

SOURCE_COMMIT = '01b7e8d7d7c862cabc9467108e3e7f2555653a88'
PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class DataPaths:
    canonical: Path
    assignments: Path
    canonical_manifest: Path
    split_manifest: Path


@dataclass(frozen=True)
class RecoveryOptions:
    checkpoint_every_steps: int = 1
    source_envelope: Path | None = None
    source_sha256: str | None = None


@dataclass(frozen=True)
class AKTConfig:
    project_root: Path = PROJECT_ROOT
    output_dir: Path = PROJECT_ROOT / 'experiments/akt/results/preflight'
    phase: str = 'preflight'
    run_id: str = 'preflight'
    execution_enabled: bool = False
    partition: str = 'development'
    graph: bool = False
    source_commit: str = SOURCE_COMMIT
    source_root: Path = PROJECT_ROOT / 'artifacts/akt/dependencies/upstream'
    outer_fold: int = 0
    device: str = 'cpu'
    seed: int = 42
    context: int = 100
    target_block: int = 100
    max_length: int = 200
    d_model: int = 256
    heads: int = 8
    blocks: int = 1
    d_ff: int = 1024
    final_fc: int = 512
    dropout: float = 0.05
    kq_same: int = 1
    separate_qa: bool = False
    n_pid: int = 0
    batch_size: int = 4
    lr: float = 1e-4
    betas: tuple[float, float] = (0.9, 0.999)
    eps: float = 1e-8
    weight_decay: float = 0.0
    max_grad_norm: float = 1.0
    inner_val_fraction: float = 0.1
    min_delta: float = 0.0001
    patience: int = 3
    max_epochs: int = 20
    max_train_users: int | None = None
    max_val_users: int | None = None
    max_targets_per_side: int | None = None
    max_total_targets: int | None = None
    max_steps: int | None = None
    max_seconds: float | None = None
    max_wall_seconds: float | None = None
    max_rss_bytes: int | None = None
    min_available_ram_bytes: int | None = None
    protocol_version: str = 'akt-nr-exercise-v1'
    memory_mb: int = 512
    threads: int = 2
    fetch_rows: int = 50000
    recovery: RecoveryOptions | None = None


@dataclass(frozen=True)
class ResearchCUDAExecutionProfile:
    """Recipe28 metadata only; the caller must configure the actual CUDA process."""
    max_vram_bytes: int
    recipe_id: str = 'cgakt-cuda-fp32-v1'
    device: str = 'cuda:0'
    initialization: str = 'cpu-default-generator-42-then-device'
    dtype: str = 'float32'
    seed: int = 42
    foreach: bool = False
    fused: bool = False
    capturable: bool = False
    differentiable: bool = False
    amsgrad: bool = False
    maximize: bool = False
    decoupled_weight_decay: bool = False
    clip_foreach: str = 'native-default-None'
    deterministic_algorithms: bool = True
    deterministic_warn_only: bool = False
    matmul_allow_tf32: bool = False
    cudnn_allow_tf32: bool = False
    matmul_precision: str = 'highest'
    cudnn_benchmark: bool = False
    cublas_workspace_config: str = ':4096:8'

    def __post_init__(self):
        if type(self.max_vram_bytes) is not int or not 64*1024**2 <= self.max_vram_bytes <= 2*1024**3:
            raise ValueError('explicit CUDA allocator budget64MiB..2GiB required')
        fixed = dict(recipe_id='cgakt-cuda-fp32-v1',device='cuda:0',
            initialization='cpu-default-generator-42-then-device',dtype='float32',seed=42,
            foreach=False,fused=False,capturable=False,differentiable=False,amsgrad=False,
            maximize=False,decoupled_weight_decay=False,clip_foreach='native-default-None',
            deterministic_algorithms=True,deterministic_warn_only=False,matmul_allow_tf32=False,
            cudnn_allow_tf32=False,matmul_precision='highest',cudnn_benchmark=False,
            cublas_workspace_config=':4096:8')
        if any(type(getattr(self,name)) is not type(value) or getattr(self,name) != value
               for name,value in fixed.items()):
            raise ValueError('CUDA execution must match the adopted recipe28')


def validate_config(config: AKTConfig, *, cuda_profile: ResearchCUDAExecutionProfile | None = None) -> None:
    if cuda_profile is not None:
        if type(cuda_profile) is not ResearchCUDAExecutionProfile:
            raise ValueError('exact typed CUDA research profile required')
        cuda_profile.__post_init__()
        if config.phase not in {'simulator-research','junyi-research'} or config.device != 'cuda':
            raise ValueError('CUDA research profile requires explicit simulator-research CUDA config')
    if config.recovery is not None:
        from .recovery import validate_options
        validate_options(config)
    if config.project_root.resolve() != PROJECT_ROOT.resolve():
        raise ValueError('project root must be the trusted repository root')
    if config.phase not in {'preflight', 'smoke', 'cuda-smoke', 'pilot', 'fold-readiness', 'fold', 'simulator-research', 'junyi-research'}:
        raise ValueError('invalid phase')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,79}', config.run_id):
        raise ValueError('invalid run_id')
    if config.phase in {'smoke', 'cuda-smoke', 'pilot', 'fold'} and config.output_dir.name != config.run_id:
        raise ValueError('run_id must namespace the output directory')
    if config.phase == 'fold-readiness' and config.execution_enabled:
        raise ValueError('fold readiness cannot enable execution')
    if config.partition != 'development':
        raise ValueError('invalid partition')
    if config.graph or config.n_pid != 0:
        raise ValueError('graph and Rasch inputs are unavailable')
    if config.source_commit != SOURCE_COMMIT:
        raise ValueError('invalid source commit')
    if config.device not in {'cpu', 'cuda'} or config.outer_fold not in range(5):
        raise ValueError('invalid device or fold')
    if min(config.context, config.target_block, config.max_length, config.d_model,
           config.heads, config.blocks, config.batch_size, config.threads, config.fetch_rows) <= 0:
        raise ValueError('invalid positive configuration')
    if config.context + config.target_block > config.max_length or config.d_model % config.heads:
        raise ValueError('invalid window or model dimensions')
    if (config.lr <= 0 or config.eps <= 0 or config.max_grad_norm <= 0
            or len(config.betas) != 2 or not all(0 <= value < 1 for value in config.betas)
            or config.weight_decay < 0 or not 0 < config.inner_val_fraction < 1
            or config.patience <= 0 or config.max_epochs <= 0 or config.min_delta < 0
            or not 0 <= config.dropout < 1):
        raise ValueError('invalid training configuration')
    if config.inner_val_fraction != 0.1:
        raise ValueError('protocol v1 requires the frozen 10% inner learner split')
    for name in ('max_train_users', 'max_val_users', 'max_targets_per_side', 'max_total_targets',
                 'max_steps', 'max_seconds', 'max_wall_seconds', 'max_rss_bytes', 'min_available_ram_bytes'):
        value = getattr(config, name)
        if value is not None and (not math.isfinite(float(value)) or value <= 0):
            raise ValueError(f'invalid resource cap: {name}')
    if config.output_dir == Path('.'):
        raise ValueError('invalid output')
    root = config.project_root.resolve()
    output = config.output_dir.resolve()
    allowed = (root / 'experiments/akt/results', root / 'experiments/akt/readiness', root / 'artifacts/akt')
    protected = (root / 'dataset', root / 'artifacts/bkt_baseline', root / 'venv', root / '.wsl')
    if (any(output.is_relative_to(path.resolve()) for path in protected)
            or not any(output.is_relative_to(path.resolve()) and output != path.resolve() for path in allowed)):
        raise ValueError('protected output or output outside AKT directory')
    if config.phase == 'fold' and output.parent != (root / 'experiments/akt/results').resolve():
        raise ValueError('fold output must use a unique results run directory')
    if config.phase in {'smoke','cuda-smoke'}:
        required_device='cpu' if config.phase=='smoke' else 'cuda'
        if (config.device != required_device or config.context != 100 or config.target_block != 100
                or config.d_model != 32 or config.heads != 4 or config.blocks != 1
                or config.d_ff != 64 or config.final_fc != 32 or config.batch_size > 4
                or config.max_epochs != 1 or config.max_train_users is None or not 1 <= config.max_train_users <= 32
                or config.max_val_users is None or not 1 <= config.max_val_users <= 16
                or config.max_targets_per_side is None or not 1 <= config.max_targets_per_side <= 4096
                or (config.max_total_targets is not None and config.max_total_targets > 8192)
                or config.max_steps is None or config.max_steps > 20
                or config.max_seconds is None or config.max_seconds > 120
                or config.max_wall_seconds is None or config.max_wall_seconds > 300
                or config.max_rss_bytes is None or config.max_rss_bytes > 2 * 1024**3
                or config.min_available_ram_bytes is None or config.min_available_ram_bytes < 1024**3):
            raise ValueError('smoke cap or architecture exceeded')
    if config.phase == 'pilot':
        if (config.device != 'cpu' or config.context != 100 or config.target_block != 100
                or config.d_model != 256 or config.heads != 8 or config.blocks != 1 or config.d_ff != 1024
                or config.batch_size > 4 or config.max_epochs != 1
                or config.max_train_users is None or not 1 <= config.max_train_users <= 1024
                or config.max_val_users is None or not 1 <= config.max_val_users <= 256
                or config.max_total_targets is None or not 1 <= config.max_total_targets <= 100000
                or config.max_seconds is None or config.max_seconds > 900
                or config.max_wall_seconds is None or config.max_wall_seconds > 1200
                or config.max_rss_bytes is None or config.max_rss_bytes > 2 * 1024**3
                or config.min_available_ram_bytes is None or config.min_available_ram_bytes < 1024**3):
            raise ValueError('pilot cap or architecture exceeded')
    if config.phase in {'simulator-research','junyi-research'}:
        if config.phase=='junyi-research' and cuda_profile is None:
            raise ValueError('Junyi research requires an explicit typed CUDA profile')
        # New scope only; no dataclass/default/hash change for historical phases.
        frozen = {'device': 'cpu' if cuda_profile is None else 'cuda', 'seed': 42, 'context': 100, 'target_block': 100, 'max_length': 200,
                  'd_model': 256, 'heads': 8, 'blocks': 1, 'd_ff': 1024, 'final_fc': 512,
                  'dropout': 0.05, 'kq_same': 1, 'separate_qa': False, 'n_pid': 0, 'graph': False,
                  'batch_size': 4, 'lr': 1e-4, 'betas': (0.9, 0.999), 'eps': 1e-8,
                  'weight_decay': 0.0, 'max_grad_norm': 1.0, 'max_epochs': 20,
                  'patience': 3, 'min_delta': 0.0001, 'outer_fold': 4 if config.phase=='junyi-research' else 0}
        if (any(type(getattr(config, name)) is not type(value) or getattr(config, name) != value
                for name, value in frozen.items()) or config.recovery is not None
                or type(config.execution_enabled) is not bool):
            raise ValueError('simulator research requires frozen CPU A0 policy; no graph/recovery/fake fold')
        for name in ('max_train_users', 'max_val_users', 'max_targets_per_side', 'max_total_targets',
                     'max_steps', 'max_rss_bytes', 'min_available_ram_bytes'):
            if type(getattr(config, name)) is not int or getattr(config, name) <= 0:
                raise ValueError('simulator research requires every integer cap explicitly')
        for name in ('max_seconds', 'max_wall_seconds'):
            value = getattr(config, name)
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError('simulator research requires finite explicit time caps')
        if (config.max_seconds > config.max_wall_seconds or output.name != config.run_id
                or output.parent != (root / 'experiments/akt/results').resolve()):
            raise ValueError('simulator research requires bounded time and exclusive named results path')
    manifest = output / 'manifest.json'
    if manifest.is_file() and json.loads(manifest.read_text(encoding='utf-8')).get('status') == 'completed':
        raise ValueError('completed run cannot be overwritten')


def load_config(path: Path, *, cuda_profile: ResearchCUDAExecutionProfile | None = None) -> AKTConfig:
    data = json.loads(path.read_text(encoding='utf-8'))
    for key in ('project_root', 'output_dir', 'source_root'):
        if key in data:
            data[key] = Path(data[key])
            if not data[key].is_absolute():
                data[key] = PROJECT_ROOT / data[key]
    if 'betas' in data:
        data['betas'] = tuple(data['betas'])
    if data.get('recovery') is not None:
        options = data['recovery']
        if not isinstance(options, dict):
            raise ValueError('recovery must be an object or null')
        options = dict(options)
        if options.get('source_envelope') is not None:
            options['source_envelope'] = Path(options['source_envelope'])
            if not options['source_envelope'].is_absolute():
                options['source_envelope'] = PROJECT_ROOT / options['source_envelope']
        data['recovery'] = RecoveryOptions(**options)
    config = AKTConfig(**data)
    validate_config(config, cuda_profile=cuda_profile)
    return config
