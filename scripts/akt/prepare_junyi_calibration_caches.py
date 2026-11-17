"""Chuẩn bị cache calibration CPU trên Volume, không nạp model hoặc Torch."""
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))


def _sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inspect_calibration_exports(export_indexes, *, run_id, budget):
    """Dựng bốn assets từ MODEL_INDEX/SUPPORT đã ghim, chưa nạp tensor."""
    from knowledge_tracing.akt.research_junyi_inference import inspect_cpu_refit_export
    if set(export_indexes) != {'A0', 'A1', 'A2', 'A3'}:
        raise ValueError('Four pinned portable export indexes required')
    result = {}
    for variant, entry in export_indexes.items():
        index = Path(entry['path'])
        if index.name != 'MODEL_INDEX.json':
            raise ValueError('Portable MODEL_INDEX.json required')
        assets = inspect_cpu_refit_export(index.parent, expected_index_sha256=entry['sha256'],
            output=ROOT/'experiments/akt/results'/(run_id+'-'+variant.lower()),
            run_id=run_id+'-'+variant.lower(), budget=budget)
        if assets['index']['identity']['variant'] != variant:
            raise ValueError('Portable export variant mismatch')
        result[variant] = assets
    return result


def prepare_calibration_caches(assets_by_variant, paths, source_pins, population, *,
        output_root, artifact_root, max_seconds, max_rss_bytes, volume_commit):
    """assets đến từ inspect_cpu_refit_export, chưa gọi builder weights.

    Return receipt nhỏ. Cùng window cache cho A0–A3, mỗi graph condition có
    SQLite riêng. GPU chỉ nhận cache/admission đã ghim và checkpoint.
    """
    import psutil
    from knowledge_tracing.akt.cache_artifacts import JunyiCacheArtifactRoot
    from knowledge_tracing.akt.research_junyi_data import iter_junyi_research_windows
    from knowledge_tracing.akt.research_junyi_graph import JunyiGraphPhaseSession
    from knowledge_tracing.akt.research_junyi_graph_cache import build_graph_context_cache, GraphContextCache
    from knowledge_tracing.akt.research_junyi_window_cache import (
        build_junyi_window_cache, JunyiWindowCacheSession, write_cpu_admission)

    if (type(artifact_root) is not JunyiCacheArtifactRoot or not callable(volume_commit)
            or set(assets_by_variant) != {'A0', 'A1', 'A2', 'A3'}
            or max_seconds <= 0 or max_rss_bytes <= 0):
        raise ValueError('Typed cloud root, four model metadata and CPU limits required')
    baseline = assets_by_variant['A0']
    view, encoding = baseline['calibration'], baseline['encoding']
    if (view.scope != 'calibration_predict' or not view.full_role_coverage
            or encoding.fit_view.scope != 'refit_union90'
            or any(asset['calibration'].identity != view.identity
                   or asset['encoding'].identity != encoding.identity for asset in assets_by_variant.values())):
        raise ValueError('Shared full calibration10/refit90 encoding required')
    if (population['source_pins'] != source_pins
            or any(_sha(getattr(paths, name)) != pin for name, pin in source_pins.items())):
        raise ValueError('Calibration source pins changed')
    population_payload = {key: value for key, value in population.items() if key != 'identity'}
    population_sha = hashlib.sha256(json.dumps(population_payload, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest()
    if (population_sha != population['identity'] or population['phase_identity'] != view.identity
            or population['roles_identity'] != view.roles.identity):
        raise ValueError('Calibration population identity/phase changed')
    manifest = json.loads(Path(paths.canonical_manifest).read_text(encoding='utf-8'))
    for name in ('canonical', 'assignments'):
        path = getattr(paths, name)
        pin = manifest['outputs'][path.name]
        if path.stat().st_size != pin['bytes'] or _sha(path) != pin['sha256']:
            raise ValueError('Calibration cache source bytes changed')
    expected = population['targets']
    dataset_sha = population['identity']
    source_sha = _sha(paths.canonical)
    root = artifact_root.validate(output_root)
    root.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    process = psutil.Process()
    def checked(records):
        for record in records:
            if time.monotonic() - started > max_seconds or process.memory_info().rss > max_rss_bytes:
                raise RuntimeError('CPU calibration cache budget exceeded')
            yield record
    def save(name, value):
        with (root / name).open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
        volume_commit()
    try:
        windows_root = root / 'windows'
        built = build_junyi_window_cache(windows_root, checked(iter_junyi_research_windows(paths, view, encoding)),
            view=view, encoding=encoding, source_data_sha256=source_sha,
            expected_target_rows=expected, artifact_root=artifact_root)
        if built['summary']['unseen_targets']:
            raise ValueError('Calibration cache has OOV; expected common fitted vocabulary')
        volume_commit()
        session = JunyiWindowCacheSession(windows_root, view, encoding, source_sha, expected,
            built['manifest_sha256'], artifact_root=artifact_root)
        admission = root / 'WINDOW_ADMISSION.json'
        write_cpu_admission(session, admission)
        volume_commit()
        graph_receipts = {}
        for variant in ('A1', 'A2', 'A3'):
            asset = assets_by_variant[variant]
            phase = JunyiGraphPhaseSession(asset['condition'], asset['calibration'])
            path = root / (variant + '.sqlite')
            graph = build_graph_context_cache(path, checked(session.iter_windows()), phase,
                dataset_sha256=dataset_sha, window_manifest_sha256=built['manifest_sha256'],
                expected_windows=built['summary']['windows'], expected_targets=expected,
                max_seconds=max(.001, max_seconds - (time.monotonic() - started)),
                max_rss_bytes=max_rss_bytes, artifact_root=artifact_root)
            opened = GraphContextCache.open(path, graph['cache_sha256'], phase,
                dataset_sha256=dataset_sha, window_manifest_sha256=built['manifest_sha256'],
                artifact_root=artifact_root)
            graph_receipts[variant] = dict(path=str(path), sha256=graph['cache_sha256'],
                binding=graph['binding'], windows=opened.windows, targets=opened.targets)
            save(variant + '_GRAPH_RECEIPT.json', graph_receipts[variant])
        result = dict(status='JUNYI_CALIBRATION_CPU_CACHES_COMPLETE', population=population,
            source_pins=source_pins, dataset_sha256=dataset_sha, source_data_sha256=source_sha,
            phase_identity=view.identity,
            encoding_identity=encoding.identity, windows=dict(path=str(windows_root),
                manifest_sha256=built['manifest_sha256'], summary=built['summary'],
                admission_path=str(admission), admission_sha256=_sha(admission)),
            graphs=graph_receipts, seconds=time.monotonic() - started,
            current_target_labels_in_gpu_windows=False, confidence_fitted_here=False)
        save('CACHE_RECEIPT.json', result)
        return result
    except BaseException as error:
        save('FAILURE.json', dict(type=type(error).__name__, message=str(error)))
        raise
