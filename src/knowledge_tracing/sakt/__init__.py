"""Lõi SAKT theo phương trình bài gốc; chưa là adapter/trainer benchmark."""

from .config import SAKTConfig

__all__ = ['SAKTConfig', 'SAKTCore', 'SAKTOutput', 'SAKTInputs', 'collate_sequences']


def __getattr__(name):
    # Data-only imports không kéo Torch; giữ nguyên public model/tensor exports.
    if name in ('SAKTCore', 'SAKTOutput'):
        from . import model
        value = getattr(model, name)
    elif name in ('SAKTInputs', 'collate_sequences'):
        from . import tensors
        value = getattr(tensors, name)
    else:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    globals()[name] = value
    return value
