"""Hợp đồng cache CPU bắt buộc trước function GPU staged A2/A3."""
from pathlib import PurePosixPath


CACHE_FIELDS = (
    ('train_graph', 'train_graph_context_cache', 'expected_train_graph_context_cache_sha256',
     'train_graph_context_cache_sha256'),
    ('selection_graph', 'selection_graph_context_cache', 'expected_selection_graph_context_cache_sha256',
     'selection_graph_context_cache_sha256'),
    ('selection_windows', 'selection_window_cache', 'expected_selection_cache_manifest_sha256',
     'selection_cache_manifest_sha256'),
    ('selection_join_admission', 'selection_cpu_admission_file', 'expected_selection_cpu_admission_sha256',
     'selection_cpu_admission_sha256'),
    ('selection_window_admission', 'selection_window_admission_file', 'expected_selection_window_admission_sha256',
     'selection_window_admission_sha256'),
)


def prepared_cache_options(worker, resolve):
    entries = worker.get('cpu_prepared')
    if type(entries) is not dict or set(entries) != {row[0] for row in CACHE_FIELDS}:
        raise ValueError('Staged GPU requires all train/selection CPU caches and admissions')
    options, pins = {}, {}
    for name, path_key, pin_key, grant_key in CACHE_FIELDS:
        entry = entries[name]
        if type(entry) is not dict or set(entry) != {'path', 'sha256'}:
            raise ValueError('CPU cache must have one path and external SHA256')
        value, digest = entry['path'], entry['sha256']
        if (type(value) is not str or not value or '\\' in value or ':' in value
                or PurePosixPath(value).is_absolute() or '..' in PurePosixPath(value).parts
                or PurePosixPath(value).as_posix() != value):
            raise ValueError('CPU cache path must be canonical and project-relative')
        if type(digest) is not str or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('CPU cache external SHA256 required')
        options[path_key] = resolve(value)
        options[pin_key] = digest
        pins[grant_key] = digest
    return options, pins
