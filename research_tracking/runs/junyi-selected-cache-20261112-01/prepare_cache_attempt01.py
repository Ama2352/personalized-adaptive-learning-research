"""Tạo cache parquet train80/selection10 đầy đủ, không training hoặc đọc Holdout."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from knowledge_tracing.akt.config import DataPaths
from knowledge_tracing.akt.data import read_development_assignments
from knowledge_tracing.akt.research_junyi_roles import JunyiResearchRoles


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prepare_cache(output, role_root, *, canonical, assignments, canonical_manifest, split_manifest):
    """Nguồn gốc giữ nguyên; cache chỉ chứa learner train và selection đã ghim."""
    import duckdb
    import pandas as pd
    allowed = (ROOT/'artifacts/akt/junyi-cohorts').resolve()
    output = output.resolve()
    if output == allowed or not output.is_relative_to(allowed):
        raise ValueError('Owned Junyi cache output required')
    role_manifest = json.loads((role_root/'manifest.json').read_text(encoding='utf-8'))
    payload = json.loads((role_root/'roles.json').read_text(encoding='utf-8'))
    if sha(role_root/'roles.json') != role_manifest['outputs_sha256']['roles.json']:
        raise ValueError('Frozen role file changed')
    for key in ('train_users','selection_users','calibration_users','outer_validation_users'):
        payload[key] = tuple(payload[key])
    roles = JunyiResearchRoles(**payload)
    if roles.identity != role_manifest['identity'] or roles.outer_fold != 4:
        raise ValueError('Frozen Junyi role identity required')
    if sha(assignments) != role_manifest['source_sha256']['artifacts/bkt_baseline/splits/assignments.parquet']:
        raise ValueError('Frozen assignments changed')
    source_paths = [assignments, canonical_manifest, split_manifest,
                    role_root/'roles.json', role_root/'manifest.json', Path(__file__).resolve()]
    source_paths += sorted(canonical.rglob('*.parquet'))
    source_hashes = {str(path.relative_to(ROOT)).replace('\\','/'):sha(path) for path in source_paths}
    paths = DataPaths(canonical, assignments, canonical_manifest, split_manifest)
    development = read_development_assignments(paths)
    requested = pd.DataFrame([(user,role) for role in ('train','selection')
                              for user in getattr(roles,role+'_users')], columns=['user_id','role'])
    selected = requested.merge(development, on='user_id', how='left', validate='one_to_one')
    if selected.fold.isna().any() or not selected.fold.isin([0,1,2,3]).all():
        raise ValueError('Train/selection learner boundary mismatch')
    output.mkdir(parents=True, exist_ok=False)
    temp = ROOT/'artifacts/akt/tmp'/output.name
    temp.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    manifest = dict(status='PREPARING', purpose='FULL_JUNYI_TRAIN80_SELECTION10_CACHE',
        roles_identity=roles.identity, full_role_coverage=True, training_performed=False,
        calibration_events_included=False, outer_validation_events_included=False,
        holdout_events_included=False, source_sha256=source_hashes,
        chronological_reader='data.iter_development_learners ORDER BY user_id,time_done,source_row')
    con = duckdb.connect(config=dict(memory_limit='256MB', threads='1', temp_directory=str(temp)))
    try:
        con.register('requested_development_users', selected)
        target = output/'canonical.parquet'
        # COPY thuần projection/join; native reader vẫn quyết định timeline khi đọc.
        con.execute("""COPY (
            SELECT c.user_id,c.exercise,c.time_done,c.source_row,c.correct,c.suggested
            FROM read_parquet(?,hive_partitioning=true) c
            JOIN requested_development_users u ON c.user_id=u.user_id
        ) TO ? (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000)""",
            [str(canonical/'**/*.parquet'),str(target)])
        assignments_copy = output/'assignments.parquet'
        con.execute("""COPY (
            SELECT user_id,CAST(fold AS INTEGER) fold,'development' partition
            FROM requested_development_users
        ) TO ? (FORMAT PARQUET, COMPRESSION ZSTD)""", [str(assignments_copy)])
        counts = con.execute("""SELECT u.role,COUNT(*) targets,COUNT(DISTINCT c.user_id) learners
            FROM read_parquet(?) c JOIN requested_development_users u ON c.user_id=u.user_id
            GROUP BY u.role ORDER BY u.role""",[str(target)]).df().to_dict('records')
        actual = {row['role']:(int(row['learners']),int(row['targets'])) for row in counts}
        if actual != dict(train=(126774,13347331),selection=(15847,1600343)):
            raise ValueError('Full selected cache target population differs from frozen role audit')
        if any(sha(ROOT/name) != digest for name,digest in source_hashes.items()):
            raise ValueError('Source changed while preparing cache')
        manifest.update(status='FULL_TRAIN_SELECTION_CACHE_VERIFIED_NOT_TRAINED',counts=counts,
            outputs={path.name:dict(bytes=path.stat().st_size,sha256=sha(path))
                     for path in (target,assignments_copy)},
            data_paths=dict(canonical=str(target.relative_to(ROOT)),assignments=str(assignments_copy.relative_to(ROOT)),
                            canonical_manifest=str(canonical_manifest.relative_to(ROOT)),
                            split_manifest=str(split_manifest.relative_to(ROOT))))
    except BaseException as error:
        manifest.update(status='FAILED_PRESERVED',error_type=type(error).__name__,error=str(error))
        raise
    finally:
        con.close()
        manifest['elapsed_seconds'] = time.monotonic()-started
        with (output/'manifest.json').open('x',encoding='utf-8') as stream:
            json.dump(manifest,stream,ensure_ascii=False,indent=2)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    root = ROOT/'artifacts/bkt_baseline'
    manifest = prepare_cache(args.output,ROOT/'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01',
        canonical=root/'derived/canonical',assignments=root/'splits/assignments.parquet',
        canonical_manifest=root/'derived/manifest.json',split_manifest=root/'splits/manifest.json')
    print(json.dumps({key:value for key,value in manifest.items() if key!='source_sha256'},ensure_ascii=False))


if __name__ == '__main__':
    main()
