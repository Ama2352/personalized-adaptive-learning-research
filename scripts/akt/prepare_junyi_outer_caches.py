"""CPUouter-onlyParquet → nativewindowcache/3graphcaches, ngoài nguồn KT.

NguồnParquetphái sinh dùngchung4model phải được nghiệm thu trước. Không chạy
nguồn Junyi gốc, không fit graph/confidence/model và không tạo cloudcontainer.
Caller khởi động process với source7c/src đứng đầu sys.path trước importKT.
"""
import hashlib
import json
import math
from pathlib import Path
import re
import time


def _sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prepare_outer_caches(assets_by_variant, paths, *, source_pins, cache_tag, receipt_path,
        disk_budget_root, max_disk_bytes, max_seconds, max_rss_bytes):
    """GenericAPIgiữnguyênfullrank/OOV, graphcachechỉknownWindowInputs."""
    import psutil
    from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView, iter_junyi_research_windows
    from knowledge_tracing.akt.research_junyi_graph import JunyiGraphPhaseSession
    from knowledge_tracing.akt import research_junyi_window_cache as windows
    from knowledge_tracing.akt import research_junyi_graph_cache as graphs
    from knowledge_tracing.akt.types import WindowInputs

    if (set(assets_by_variant) != {'A0', 'A1', 'A2', 'A3'}
            or not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,63}', cache_tag)
            or type(max_seconds) not in (int,float) or not math.isfinite(max_seconds)
            or not 0 < max_seconds <= 7200 or max_rss_bytes <= 0 or not 0 < max_disk_bytes <= 4*1024**3):
        raise ValueError('Four variants, bounded new cache tag and explicit CPU limits required')
    receipt_path, disk_budget_root = Path(receipt_path), Path(disk_budget_root)
    if (receipt_path.exists() or not disk_budget_root.is_absolute() or not disk_budget_root.is_dir()
            or disk_budget_root.resolve() != disk_budget_root or disk_budget_root.is_symlink()):
        raise ValueError('New receipt and physical existing disk budget root required')
    baseline = assets_by_variant['A0']
    encoding = baseline['encoding']
    roles = encoding.fit_view.roles
    view = JunyiPhaseView(roles, 'outer_evaluation', roles.outer_validation_users, roles.identity)
    if encoding.fit_view.scope != 'refit_union90' or not encoding.fit_view.full_role_coverage or any(
            asset['encoding'].identity != encoding.identity for asset in assets_by_variant.values()):
        raise ValueError('Shared frozen refit90 encoding required')
    if set(source_pins) != {'canonical_manifest', 'split_manifest'} or any(
            _sha(getattr(paths, name)) != expected for name, expected in source_pins.items()):
        raise ValueError('Outer source metadata pins changed')
    manifest = json.loads(Path(paths.canonical_manifest).read_text(encoding='utf-8'))
    if (manifest.get('status') != 'FULL_OUTER_SOURCE_PREPARED'
            or manifest.get('purpose') != 'JUNYI_REFIT90_OUTER_EVALUATION_SOURCE'
            or manifest.get('phase_identity') != view.identity
            or manifest.get('roles_identity') != roles.identity
            or manifest.get('encoding_identity') != encoding.identity
            or manifest['counts']['learners'] != len(view.users)):
        raise ValueError('Full outer-only source/refit90 manifest required')
    for name in ('canonical', 'assignments'):
        path = getattr(paths, name)
        pin = manifest['outputs'][path.name]
        if not path.is_file() or path.stat().st_size != pin['bytes'] or _sha(path) != pin['sha256']:
            raise ValueError('Outer source bytes changed')
    expected = manifest['counts']['targets']
    expected_oov = manifest['counts']['oov_targets']
    if type(expected) is not int or type(expected_oov) is not int or not 0 <= expected_oov < expected:
        raise ValueError('Exact positive target count and nonnegative OOV count required')
    source_sha = _sha(paths.canonical)
    dataset_sha = _sha(paths.canonical_manifest)
    started = time.monotonic()
    process = psutil.Process()
    disk = dict(last_scan=-math.inf, bytes=0)
    def check(*, force_disk=False):
        now = time.monotonic()
        if now-started > max_seconds or process.memory_info().rss > max_rss_bytes:
            raise RuntimeError('Outer CPU cache budget exceeded')
        if force_disk or now-disk['last_scan'] >= 30:
            disk['bytes'] = sum(path.stat().st_size for path in disk_budget_root.rglob('*') if path.is_file())
            disk['last_scan'] = time.monotonic()
        if disk['bytes'] > max_disk_bytes:
            raise RuntimeError('Outer CPU cache disk budget exceeded')
    def checked(records):
        for index, record in enumerate(records):
            if index % 512 == 0:
                check()
            yield record
        check(force_disk=True)
    check(force_disk=True)
    window_root = windows.CACHE_BASE/cache_tag
    graph_root = graphs.CACHE_ROOT/cache_tag
    if not window_root.is_relative_to(disk_budget_root) or not graph_root.is_relative_to(disk_budget_root):
        raise ValueError('Window/graph caches must stay in bounded local cache root')
    built = windows.build_junyi_window_cache(window_root,
        checked(iter_junyi_research_windows(paths, view, encoding)), view=view, encoding=encoding,
        source_data_sha256=source_sha, expected_target_rows=expected)
    if built['summary']['unseen_targets'] != expected_oov:
        raise ValueError('Outer OOV recount differs from prepared source')
    session = windows.JunyiWindowCacheSession(window_root, view, encoding, source_sha,
        expected, built['manifest_sha256'])
    admission = window_root/'WINDOW_ADMISSION.json'
    windows.write_cpu_admission(session, admission)
    receipts = {}
    for variant in ('A1', 'A2', 'A3'):
        phase = JunyiGraphPhaseSession(assets_by_variant[variant]['condition'], view)
        path = graph_root/(variant+'.sqlite')
        known = (record for record in checked(session.iter_windows()) if type(record) is WindowInputs)
        graph = graphs.build_graph_context_cache(path, known, phase, dataset_sha256=dataset_sha,
            window_manifest_sha256=built['manifest_sha256'], expected_windows=built['summary']['windows'],
            expected_targets=expected-expected_oov,
            max_seconds=max(.001, max_seconds-(time.monotonic()-started)), max_rss_bytes=max_rss_bytes)
        opened = graphs.GraphContextCache.open(path, graph['cache_sha256'], phase,
            dataset_sha256=dataset_sha, window_manifest_sha256=built['manifest_sha256'])
        receipts[variant] = dict(path=str(path), sha256=graph['cache_sha256'],
            windows=opened.windows, targets=opened.targets, binding=graph['binding'])
        check(force_disk=True)
    check(force_disk=True)
    if any(_sha(getattr(paths, name)) != expected_pin for name, expected_pin in source_pins.items()):
        raise ValueError('Source metadata changed during preparation')
    if any(_sha(getattr(paths, name)) != manifest['outputs'][getattr(paths, name).name]['sha256']
           for name in ('canonical', 'assignments')):
        raise ValueError('Source data changed during preparation')
    result = dict(status='JUNYI_OUTER_CPU_CACHES_COMPLETE', phase='outer_evaluation',
        phase_identity=view.identity, roles_identity=roles.identity, encoding_identity=encoding.identity,
        source_pins=source_pins, source_data_sha256=source_sha, dataset_sha256=dataset_sha,
        windows=dict(path=str(window_root), summary=built['summary'], manifest_sha256=built['manifest_sha256'],
            admission_path=str(admission), admission_sha256=_sha(admission)), graphs=receipts,
        oov_targets_recounted=expected_oov, seconds=time.monotonic()-started,
        graph_or_confidence_fitted=False, labels_in_gpu_windows=False)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    with receipt_path.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return result
