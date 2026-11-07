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


def validate_config(config: AKTConfig) -> None:
    if config.recovery is not None:
        from .recovery import validate_options
        validate_options(config)
    if config.project_root.resolve() != PROJECT_ROOT.resolve():
        raise ValueError('project root must be the trusted repository root')
    if config.phase not in {'preflight', 'smoke', 'pilot', 'fold-readiness', 'fold'}:
        raise ValueError('invalid phase')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,79}', config.run_id):
        raise ValueError('invalid run_id')
    if config.phase in {'smoke', 'pilot', 'fold'} and config.output_dir.name != config.run_id:
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
    if config.phase == 'smoke':
        if (config.device != 'cpu' or config.context != 100 or config.target_block != 100
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
    manifest = output / 'manifest.json'
    if manifest.is_file() and json.loads(manifest.read_text(encoding='utf-8')).get('status') == 'completed':
        raise ValueError('completed run cannot be overwritten')


def load_config(path: Path) -> AKTConfig:
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
    validate_config(config)
    return config
