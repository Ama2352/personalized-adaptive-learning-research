"""Wrapper mỏng quanh AKT upstream đã pin, không sửa thuật toán gốc."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType

import torch

from .config import AKTConfig, SOURCE_COMMIT
from .provenance import verify_upstream

_process_device: str | None = None


def load_upstream(root: Path, *, device: str) -> ModuleType:
    global _process_device
    if device not in {'cpu', 'cuda'}:
        raise ValueError('unsupported device')
    if _process_device is not None and _process_device != device:
        raise ValueError('only one device is supported per process')
    if device == 'cuda' and not torch.cuda.is_available():
        raise ValueError('CUDA unavailable')
    root = root.resolve()
    verify_upstream(root, SOURCE_COMMIT)
    spec = importlib.util.spec_from_file_location('akt_upstream_reference', root / 'akt.py')
    if spec is None or spec.loader is None:
        raise ValueError('upstream module cannot be loaded')
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    module.device = torch.device(device)
    _process_device = device
    return module


def build_native(config: AKTConfig, *, n_items: int) -> torch.nn.Module:
    if (n_items <= 0 or config.d_model % config.heads or config.n_pid != 0
            or config.graph or config.separate_qa):
        raise ValueError('invalid graph-free NonRasch model configuration')
    module = load_upstream(config.source_root, device=config.device)
    model = module.AKT(n_question=n_items, n_pid=0, d_model=config.d_model,
                       n_blocks=config.blocks, kq_same=config.kq_same,
                       dropout=config.dropout, model_type='akt',
                       final_fc_dim=config.final_fc, n_heads=config.heads,
                       d_ff=config.d_ff, separate_qa=False)
    return model.to(torch.device(config.device))
