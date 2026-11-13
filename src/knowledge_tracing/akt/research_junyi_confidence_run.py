"""Spool TRAIN80 trên D và công bố confidence sau đủ child đã fit.

SQLite commit cùng vị trí đọc, mỗi child là checkpoint riêng. Dùng lại
feature, solver, crossfit và bootstrap đã nghiệm thu của Method24.
"""
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import time

from ..edge_confidence import EdgeConfidenceRecipe, EdgeRuntimeBinding, EdgeSummary
from .research_junyi_confidence import (
    FEATURE_RECIPE, FOLD_RECIPE, JunyiSurrogateRow, fit_child_confidence,
    iter_surrogate_rows,
)
from .research_junyi_confidence_binding import binding_from_child_results, save_binding


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def write_closed(path, value):
    """Công bố marker cuối, giữ file đang ghi nếu bị ngắt."""
    path = Path(path)
    raw = (canonical(value) + '\n').encode()
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('Artifact cũ khác byte, giữ lại để điều tra')
        return
    temporary = path.with_suffix(path.suffix + '.writing-' + str(time.time_ns()))
    with temporary.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        import os
        os.fsync(stream.fileno())
    temporary.rename(path)


def approved_recipe():
    return EdgeConfidenceRecipe('train-lagged-edge-confidence-v1', 42, 3, 1., 5.,
                                1., 1e-6, 200, 1e-6, 200, 20)


def source_pins():
    here = Path(__file__).resolve().parent
    paths = [here / name for name in ('research_junyi_confidence_run.py',
        'research_junyi_confidence.py', 'research_junyi_confidence_binding.py',
        'research_junyi_graph.py', 'research_junyi_data.py',
        'research_junyi_window_cache.py', 'windows.py')]
    paths.append(here.parent / 'edge_confidence.py')
    paths.append(here.parents[2] / 'scripts/akt/fit_junyi_confidence.py')
    return {path.name: sha(path) for path in paths}


def run_identity(condition, window_manifest_sha256, runtime):
    if not condition.encoding.fit_view.full_role_coverage:
        raise ValueError('Confidence chính yêu cầu đầy đủ TRAIN80 đã frozen')
    return dict(train_view_identity=condition.encoding.fit_view.identity,
        encoding_identity=condition.encoding.identity,
        topology_source_sha256=condition.topology_source_sha256,
        recipe_identity=approved_recipe().identity,
        window_manifest_sha256=window_manifest_sha256,
        runtime=asdict(runtime), sources=source_pins())


def open_spool(directory, identity):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    write_closed(directory / 'IDENTITY.json', identity)
    connection = sqlite3.connect(directory / 'rows.sqlite', timeout=30)
    connection.execute('PRAGMA cache_size=-8192')
    connection.execute('PRAGMA journal_mode=DELETE')
    connection.execute('PRAGMA synchronous=FULL')
    connection.execute('CREATE TABLE IF NOT EXISTS rows '
                       '(child TEXT, ordinal INTEGER, payload TEXT, PRIMARY KEY(child, ordinal)) WITHOUT ROWID')
    connection.execute('CREATE TABLE IF NOT EXISTS progress (id INTEGER PRIMARY KEY, payload TEXT)')
    connection.commit()
    return connection


def spool_windows(directory, *, windows, session, identity, expected_targets,
                  expected_records, max_seconds, commit_windows=256):
    """Commit dữ liệu và offset cùng transaction, resume không nhân đôi target."""
    directory = Path(directory)
    connection = open_spool(directory, identity)
    started = time.monotonic()
    children = {child for _, child in session.condition.graph.edges}
    try:
        saved = connection.execute('SELECT payload FROM progress WHERE id=1').fetchone()
        progress = json.loads(saved[0]) if saved else dict(records=0, targets=0, stored_rows=0)
        original_records = progress['records']
        if (directory / 'SPOOL_COMPLETE.json').exists():
            complete = json.loads((directory / 'SPOOL_COMPLETE.json').read_text())
            if sha(directory / 'rows.sqlite') != complete['database_sha256']:
                raise ValueError('Spool đã đóng bị thay đổi')
            return complete

        def checkpoint():
            connection.execute('INSERT OR REPLACE INTO progress VALUES (1, ?)', (canonical(progress),))
            connection.commit()

        def remaining():
            for index, record in enumerate(windows):
                if index < original_records:
                    continue
                yield record
                progress['records'] = index + 1
                if progress['records'] % commit_windows == 0:
                    checkpoint()
                    if time.monotonic() - started >= max_seconds:
                        raise TimeoutError('Hết tranche CPU spool, tiếp tục từ progress đã commit')

        for row in iter_surrogate_rows(remaining(), session, max_targets=expected_targets,
                max_windows=expected_records, max_seconds=max_seconds + 120):
            progress['targets'] += 1
            if row.child_id in children:
                connection.execute('INSERT INTO rows VALUES (?, ?, ?)',
                    (row.child_id, progress['targets'], canonical(
                        {name: getattr(row, name) for name in JunyiSurrogateRow.__dataclass_fields__})))
                progress['stored_rows'] += 1
        if progress['targets'] != expected_targets or progress['records'] != expected_records:
            raise ValueError('Spool thiếu TRAIN80 target hoặc record, không công bố COMPLETE')
        checkpoint()
        session.assert_boundary()
        if identity['sources'] != source_pins():
            raise ValueError('Nguồn thay đổi khi spool')
        counts = dict(connection.execute('SELECT child, COUNT(*) FROM rows GROUP BY child'))
        connection.close()
        connection = None
        complete = dict(status='SPOOL_TRAIN80_COMPLETE', **progress, child_counts=counts,
            database_sha256=sha(directory / 'rows.sqlite'), identity_sha256=sha(directory / 'IDENTITY.json'))
        write_closed(directory / 'SPOOL_COMPLETE.json', complete)
        return complete
    finally:
        if connection is not None:
            connection.rollback()
            connection.close()


def rows_for_child(database, child):
    connection = sqlite3.connect(f'file:{Path(database).resolve().as_posix()}?mode=ro', uri=True)
    connection.execute('PRAGMA cache_size=-4096')
    try:
        for payload, in connection.execute('SELECT payload FROM rows WHERE child=? ORDER BY ordinal', (child,)):
            fields = json.loads(payload)
            fields['base'] = tuple(fields['base'])
            fields['parents'] = tuple(tuple(value) for value in fields['parents'])
            yield JunyiSurrogateRow(**fields)
    finally:
        connection.close()


def empty_child(child, parents, view, recipe):
    edges = tuple(EdgeSummary(parent, child, 0, 0, 0, 0, (0, 0), False,
        tuple((fold, 0, 0, 0) for fold in range(recipe.folds)), False,
        'CHILD_HAS_NO_TRAIN80_TARGETS', (), None, 0, None,
        recipe.bootstrap_replicates, None) for parent in parents)
    return dict(feature_recipe=FEATURE_RECIPE, fold_recipe=FOLD_RECIPE,
        train_view_identity=view.identity, recipe_identity=recipe.identity,
        child=child, edges=edges, oof=(), fit_ledger=())


def fit_one_child(directory, *, condition, runtime, child, max_rows, max_seconds):
    directory = Path(directory)
    identity = json.loads((directory / 'IDENTITY.json').read_text())
    expected = run_identity(condition, identity['window_manifest_sha256'], runtime)
    if identity != expected:
        raise ValueError('Nguồn, runtime hoặc TRAIN80 khác spool')
    complete = json.loads((directory / 'SPOOL_COMPLETE.json').read_text())
    parents = tuple(parent for parent, target in condition.graph.edges if target == child)
    if not parents:
        raise ValueError('Child phải thuộc topology đã chốt')
    result_dir = directory / 'children' / hashlib.sha256(child.encode()).hexdigest()
    result_dir.mkdir(parents=True, exist_ok=True)
    marker = result_dir / 'COMPLETE.json'
    if marker.exists():
        pins = json.loads(marker.read_text())
        if any(sha(result_dir / name) != pin for name, pin in pins['files'].items()):
            raise ValueError('Checkpoint child đã đóng bị thay đổi')
        return json.loads((result_dir / 'summary.json').read_text())
    if (result_dir / 'summary.json').exists():
        summary = json.loads((result_dir / 'summary.json').read_text())
        if sha(result_dir / summary['oof_path']) != summary['oof_sha256']:
            raise ValueError('OOF của child ghi dở khác byte đã công bố')
        write_closed(marker, dict(child=child, files={'summary.json': sha(result_dir / 'summary.json'),
            summary['oof_path']: summary['oof_sha256']}))
        return summary
    # File dở giữ nguyên. Lượt retry có thư mục attempt riêng.
    attempt = result_dir / ('attempt-' + str(time.time_ns()))
    attempt.mkdir()
    recipe = approved_recipe()
    count = complete['child_counts'].get(child, 0)
    if count > max_rows:
        raise MemoryError('Child vượt cap RAM/rows, cần tranche tài nguyên phù hợp')
    started = time.monotonic()
    result = fit_child_confidence(rows_for_child(directory / 'rows.sqlite', child), child=child,
        parents=parents, view=condition.encoding.fit_view, recipe=recipe, runtime=runtime,
        max_rows=max_rows, max_fits=recipe.folds * (1 + len(parents)), max_seconds=max_seconds
    ) if count else empty_child(child, parents, condition.encoding.fit_view, recipe)
    with gzip.open(attempt / 'oof.jsonl.gz', 'wt', encoding='utf-8') as output:
        for row in result['oof']:
            output.write(canonical(asdict(row)) + '\n')
    summary = {key: value for key, value in result.items() if key != 'oof'}
    summary['edges'] = [asdict(edge) for edge in result['edges']]
    summary.update(targets=count, oof_rows=len(result['oof']), wall_seconds=time.monotonic() - started,
                   oof_path=(attempt / 'oof.jsonl.gz').relative_to(result_dir).as_posix(),
                   oof_sha256=sha(attempt / 'oof.jsonl.gz'))
    write_closed(result_dir / 'summary.json', summary)
    write_closed(marker, dict(child=child, files={'summary.json': sha(result_dir / 'summary.json'),
        summary['oof_path']: sha(attempt / 'oof.jsonl.gz')}))
    return json.loads((result_dir / 'summary.json').read_text())


def restore_summary(payload):
    restored = dict(payload)
    edges = []
    for entry in payload['edges']:
        fields = dict(entry)
        for name in ('eligible_class_counts', 'fold_population', 'learner_deltas'):
            fields[name] = tuple(tuple(value) if isinstance(value, list) else value for value in fields[name])
        edges.append(EdgeSummary(**fields))
    restored['edges'] = tuple(edges)
    return restored


def finalize(directory, *, condition, runtime):
    directory = Path(directory)
    identity = json.loads((directory / 'IDENTITY.json').read_text())
    if identity != run_identity(condition, identity['window_manifest_sha256'], runtime):
        raise ValueError('Lineage source/runtime khác run')
    complete = json.loads((directory / 'SPOOL_COMPLETE.json').read_text())
    if sha(directory / 'rows.sqlite') != complete['database_sha256']:
        raise ValueError('Spool khác byte đã đóng')
    children = sorted({child for _, child in condition.graph.edges})
    results, pins = [], {}
    for child in children:
        folder = directory / 'children' / hashlib.sha256(child.encode()).hexdigest()
        marker = json.loads((folder / 'COMPLETE.json').read_text())
        if marker['child'] != child or any(sha(folder / name) != pin for name, pin in marker['files'].items()):
            raise ValueError('Child chưa hoàn tất hoặc khác SHA')
        results.append(restore_summary(json.loads((folder / 'summary.json').read_text())))
        pins[child] = sha(folder / 'COMPLETE.json')
    fit_manifest = dict(status='COMPLETE_FULL_TRAIN80_CONFIDENCE', **identity,
        all_train_targets_seen=complete['targets'], full_role_coverage=True,
        history_scope='effective_native_window_prefix',
        semantics='conditional_predictive_stability_not_edge_truth_probability', uses_oracle_labels=False,
        children=pins, spool_complete_sha256=sha(directory / 'SPOOL_COMPLETE.json'))
    path = directory / 'fit-manifest.json'
    write_closed(path, fit_manifest)
    binding = binding_from_child_results(results, condition=condition, recipe=approved_recipe(),
                                        fit_artifact_sha256=sha(path))
    target = directory / 'confidence.json'
    if not target.exists():
        save_binding(binding, target)
    from .research_junyi_confidence_binding import load_binding
    if load_binding(target, expected_sha256=sha(target)) != binding:
        raise ValueError('Binding đã lưu khác kết quả đủ child')
    receipt = dict(status='COMPLETE_FULL_TRAIN80_CONFIDENCE', confidence_sha256=sha(target),
        fit_artifact_sha256=sha(path), edges=len(binding.weights),
        supported_edges=sum(row.supported for row in binding.weights),
        unsupported_edges=sum(not row.supported for row in binding.weights))
    write_closed(directory / 'COMPLETE.json', receipt)
    return receipt
