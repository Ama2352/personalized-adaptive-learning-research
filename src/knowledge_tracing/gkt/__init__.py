"""GKT static kernel và research data, neural exports được nạp khi sử dụng."""

from .config import GKTBinding, GKTKernelConfig

__all__ = ['GKTBinding', 'GKTKernelConfig', 'GKTMessages', 'GKTReadout',
           'StaticGKTKernel', 'adjacency_sha256', 'dense_adjacency']


def __getattr__(name):
    if name in ('GKTMessages', 'GKTReadout', 'StaticGKTKernel', 'adjacency_sha256', 'dense_adjacency'):
        from . import core
        value = getattr(core, name)
        globals()[name] = value
        return value
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
