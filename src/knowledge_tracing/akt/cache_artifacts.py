"""Root cache cloud khai báo rõ, mặc định cache local không đổi."""
from dataclasses import dataclass
from pathlib import Path

CLOUD_CACHE_ROOT = Path('/artifacts')


@dataclass(frozen=True)
class JunyiCacheArtifactRoot:
    root: Path

    def validate(self, path):
        expected = CLOUD_CACHE_ROOT.resolve(strict=True)
        root = Path(self.root)
        if not root.is_absolute() or root != expected or not root.is_dir() or root.is_symlink():
            raise ValueError('Physical mounted Junyi cache root required')
        path = Path(path).absolute()
        if path == root or not path.is_relative_to(root):
            raise ValueError('Cache outside mounted artifact root')
        for component in (path, *path.parents):
            if component == root:
                break
            if component.is_symlink() or getattr(component, 'is_junction', lambda: False)():
                raise ValueError('Cache artifact alias rejected')
        if path.resolve() != path:
            raise ValueError('Physical cache artifact path required')
        return path
