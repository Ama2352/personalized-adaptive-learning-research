"""CPUsourcewriterouter-only dùngchung4model, không đổi nguồn KT hoặc datasetgốc."""
import hashlib
import json
import math
from pathlib import Path
import threading
import time
import uuid

SELECT_SQL = """SELECT c.user_id,c.exercise,c.time_done,c.source_row,c.correct,c.suggested
 FROM read_parquet($source,hive_partitioning=true) c
 JOIN read_parquet($assignments) a ON c.user_id=a.user_id
 JOIN requested_outer_users u ON CAST(c.user_id AS VARCHAR)=u.user_id
 WHERE a.partition='development' AND a.fold=4"""


def _sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def prepare_outer_source(assets_by_variant, paths, *, source_repo_root, inventory_path,
        inventory_sha256, output_root, disk_budget_root, expected_targets, expected_learners,
        expected_oov_targets, max_seconds, max_rss_bytes, max_disk_bytes):
    """Nguyên bảnSQL/ordering như writercalibration, đổi explicitrole/purposeouter.

Expectedcounts là dự kiến cần xác minh, không phải bằng chứng đã có. Hashfull
inventorytrước/sau, SQLchỉtrảDevelopmentfold4. GuardRAM/disk/wallcooperative;
caller cần subprocess/watchdog ngoài cho tác vụ thật. Không tự phátGPU/Drive.
"""
    import duckdb
    import psutil
    from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView
    from knowledge_tracing.akt.research_junyi_calibration import inference_source_identity
    if set(assets_by_variant) != {'A0','A1','A2','A3'}:
        raise ValueError('Four frozen metadata exports required')
    encoding = assets_by_variant['A0']['encoding']
    roles = encoding.fit_view.roles
    view = JunyiPhaseView(roles, 'outer_evaluation', roles.outer_validation_users, roles.identity)
    if encoding.fit_view.scope != 'refit_union90' or not encoding.fit_view.full_role_coverage or any(
            asset['encoding'].identity != encoding.identity for asset in assets_by_variant.values()):
        raise ValueError('Shared full refit90 encoding required')
    export_pins = {variant:dict(index_sha256=asset['expected_index_sha256'],
        checkpoint_sha256=asset['index']['checkpoint_sha256'],
        condition_identity=asset['index']['identity']['condition'])
        for variant,asset in assets_by_variant.items()}
    if any(type(row[name]) is not str or len(row[name]) != 64
           or any(character not in '0123456789abcdef' for character in row[name])
           for row in export_pins.values() for name in ('index_sha256','checkpoint_sha256')):
        raise ValueError('Explicit portable model metadata pins required')
    if (any(type(value) is not int or value <= 0 for value in
            (expected_targets, expected_learners, max_rss_bytes, max_disk_bytes))
            or type(expected_oov_targets) is not int or not 0 <= expected_oov_targets < expected_targets
            or expected_learners != len(view.users) or not 0 < max_disk_bytes <= 4*1024**3
            or type(max_seconds) not in (int,float) or not math.isfinite(max_seconds)
            or not 0 < max_seconds <= 7200):
        raise ValueError('Explicit bounded counts and resource limits required')
    source_repo_root, inventory_path = Path(source_repo_root), Path(inventory_path)
    writer_sha256 = _sha(Path(__file__))
    output_root, disk_budget_root = Path(output_root), Path(disk_budget_root)
    if (not output_root.is_absolute() or output_root.resolve() != output_root
            or output_root.exists() or not disk_budget_root.is_dir()
            or disk_budget_root.resolve() != disk_budget_root
            or output_root == disk_budget_root or not output_root.is_relative_to(disk_budget_root)):
        raise ValueError('New physical output inside existing bounded cache required')
    if _sha(inventory_path) != inventory_sha256:
        raise ValueError('Frozen source inventory changed')
    source_inventory = json.loads(inventory_path.read_text(encoding='utf-8'))['source_sha256']
    canonical_files = sorted(paths.canonical.rglob('*.parquet')) if paths.canonical.is_dir() else [paths.canonical]
    required = canonical_files + [paths.assignments, paths.canonical_manifest, paths.split_manifest]
    if any(path.relative_to(source_repo_root).as_posix() not in source_inventory for path in required):
        raise ValueError('Canonical/assignments/manifests missing from source inventory')
    started = time.monotonic()
    process = psutil.Process()
    disk = dict(last_scan=-math.inf, bytes=0, scans=0)
    def check(*, force_disk=False):
        now = time.monotonic()
        if now-started > max_seconds or process.memory_info().rss > max_rss_bytes:
            raise RuntimeError('Outer source CPU budget exceeded')
        if force_disk or now-disk['last_scan'] >= 30:
            disk['bytes'] = sum(path.stat().st_size for path in disk_budget_root.rglob('*') if path.is_file())
            disk['last_scan'] = time.monotonic()
            disk['scans'] += 1
        if disk['bytes'] > max_disk_bytes:
            raise RuntimeError('Outer source disk budget exceeded')
    def verify_sources():
        if _sha(inventory_path) != inventory_sha256:
            raise ValueError('Source inventory changed during stage')
        for relative, expected in source_inventory.items():
            path = source_repo_root/relative
            if not path.resolve().is_relative_to(source_repo_root.resolve()) or _sha(path) != expected:
                raise ValueError('Original source bytes differ from frozen inventory')
            check()
    verify_sources()
    check(force_disk=True)
    output_reserve = min(160*1024**2, max_disk_bytes//4)
    spill_bytes = max_disk_bytes-disk['bytes']-output_reserve
    if spill_bytes <= 0:
        raise RuntimeError('Insufficient cache headroom after reserving prepared output')
    temporary = disk_budget_root/('outer-source-sql-'+uuid.uuid4().hex)
    temporary.mkdir()
    connection = duckdb.connect(config={'threads':'1', 'memory_limit':'256MB',
        'temp_directory':str(temporary), 'max_temp_directory_size':str(spill_bytes)+'B'})
    timer = threading.Timer(max(.01, max_seconds-(time.monotonic()-started)), connection.interrupt)
    timer.daemon = True
    timer.start()
    try:
        assigned = connection.execute("SELECT CAST(user_id AS VARCHAR) FROM read_parquet(?) "
            "WHERE partition='development' AND fold=4", [str(paths.assignments)]).fetchall()
        if len(assigned) != len(view.users) or {row[0] for row in assigned} != set(view.users):
            raise ValueError('Full outer assignment/fold role mismatch')
        connection.execute('BEGIN TRANSACTION')
        connection.execute('CREATE TEMP TABLE requested_outer_users(user_id VARCHAR PRIMARY KEY)')
        connection.executemany('INSERT INTO requested_outer_users VALUES(?)', [(user,) for user in view.users])
        connection.execute('CREATE TEMP TABLE refit_vocabulary(exercise VARCHAR PRIMARY KEY)')
        connection.executemany('INSERT INTO refit_vocabulary VALUES(?)',
                               [(value,) for value in encoding.native.vocabulary.values])
        connection.execute('COMMIT')
        pattern = str(paths.canonical/'**/*.parquet') if paths.canonical.is_dir() else str(paths.canonical)
        params = dict(source=pattern, assignments=str(paths.assignments))
        connection.sql(SELECT_SQL, params=params).create_view('outer_selected')
        stats = connection.execute("""SELECT COUNT(*),COUNT(DISTINCT c.user_id),
          COUNT(DISTINCT c.source_row),COUNT(*) FILTER(WHERE c.correct=1),
          COUNT(*) FILTER(WHERE c.correct=0),
          COUNT(*) FILTER(WHERE c.correct IS NULL OR c.correct NOT IN(0,1)
            OR c.suggested IS NULL OR c.suggested NOT IN(0,1) OR c.source_row IS NULL
            OR c.source_row<=0 OR c.time_done IS NULL OR c.time_done<0 OR c.exercise IS NULL OR c.exercise=''),
          COUNT(*) FILTER(WHERE v.exercise IS NULL)
          FROM outer_selected c LEFT JOIN refit_vocabulary v ON c.exercise=v.exercise""").fetchone()
        names = ('targets','learners','unique_source_rows','positive_labels','negative_labels','invalid_rows','oov_targets')
        counts = dict(zip(names, map(int, stats)))
        counts['max_learner_events'] = int(connection.execute(
            'SELECT MAX(n) FROM (SELECT user_id,COUNT(*) n FROM outer_selected GROUP BY user_id)').fetchone()[0] or 0)
        if (counts['invalid_rows'] or counts['targets'] != counts['unique_source_rows']
                or (counts['targets'],counts['learners'],counts['oov_targets'])
                != (expected_targets,expected_learners,expected_oov_targets)):
            raise ValueError('Invalid/duplicate outer rows or actual counts differ from expected')
        exercise_counts = [dict(exercise=row[0], targets=int(row[1]), supported=bool(row[2]))
            for row in connection.execute('SELECT c.exercise,COUNT(*),v.exercise IS NOT NULL '
                'FROM outer_selected c LEFT JOIN refit_vocabulary v ON c.exercise=v.exercise '
                'GROUP BY c.exercise,v.exercise ORDER BY c.exercise').fetchall()]
        check(force_disk=True)
        output_root.mkdir(parents=True, exist_ok=False)
        canonical, assignments = output_root/'canonical.parquet', output_root/'assignments.parquet'
        connection.execute('COPY (SELECT * FROM outer_selected ORDER BY user_id,time_done,source_row) '
            'TO $destination (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 50000)',
            dict(destination=str(canonical)))
        check(force_disk=True)
        if canonical.stat().st_size > output_reserve:
            raise RuntimeError('Prepared canonical exceeds reserved output budget')
        connection.execute("COPY (SELECT user_id,4::INTEGER fold,'development' AS partition "
            'FROM requested_outer_users ORDER BY user_id) TO $destination (FORMAT PARQUET, COMPRESSION ZSTD)',
            dict(destination=str(assignments)))
        check(force_disk=True)
        copied = connection.execute('SELECT COUNT(*),COUNT(DISTINCT source_row) FROM read_parquet(?)',
            [str(canonical)]).fetchone()
        if copied != (expected_targets, expected_targets):
            raise ValueError('Outer prepared output coverage differs')
        verify_sources()
        check(force_disk=True)
        if _sha(Path(__file__)) != writer_sha256:
            raise ValueError('Source writer changed during execution')
        result = dict(status='FULL_OUTER_SOURCE_PREPARED', purpose='JUNYI_REFIT90_OUTER_EVALUATION_SOURCE',
            writer_sha256=writer_sha256,
            phase_identity=view.identity, roles_identity=roles.identity, encoding_identity=encoding.identity,
            inference_source_sha256=inference_source_identity(), portable_export_pins=export_pins,
            counts=counts, exercise_counts=exercise_counts,
            known_oov_exercise_counts_sha256=_identity(exercise_counts),
            source_inventory_sha256=inventory_sha256, source_sha256=source_inventory,
            outputs={path.name:dict(bytes=path.stat().st_size,sha256=_sha(path)) for path in (canonical,assignments)},
            data_paths=dict(canonical=str(canonical), assignments=str(assignments),
                canonical_manifest=str(output_root/'manifest.json'), split_manifest=str(paths.split_manifest)),
            original_physical_source='exercise-partitioned mixed learners; explicit Development/fold4/fullroles SQL join',
            temporary_directory=str(temporary),
            resource_contract=dict(max_disk_bytes=max_disk_bytes, spill_cap_bytes=spill_bytes,
                output_reserved_bytes=output_reserve, disk_scan_interval_seconds=30,
                disk_scans=disk['scans'], disk_semantics='cooperative, forced at write/stage boundaries'),
            holdout_events_included=False, training_performed=False, calibration_fit_performed=False,
            graph_or_confidence_fitted=False, seconds=time.monotonic()-started)
        with (output_root/'manifest.json').open('x', encoding='utf-8') as stream:
            json.dump(result,stream,ensure_ascii=False,indent=2)
            stream.write('\n')
        return result
    finally:
        timer.cancel()
        connection.close()
