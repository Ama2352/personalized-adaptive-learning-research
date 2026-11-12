"""Ghi derivative inner-role Junyi từ metadata Development, không đọc events."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.akt.research_junyi_roles import make_junyi_research_roles


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    allowed = (ROOT / 'artifacts/akt/junyi-roles').resolve()
    if not output.is_relative_to(allowed) or output == allowed:
        raise ValueError('Unique derivative output under artifacts/akt/junyi-roles required')
    assignments = ROOT / 'artifacts/bkt_baseline/splits/assignments.parquet'
    split_manifest = ROOT / 'artifacts/bkt_baseline/splits/manifest.json'
    sources = {str(path.relative_to(ROOT)).replace('\\', '/'): sha(path)
               for path in (assignments, split_manifest, Path(__file__).resolve(),
                            ROOT / 'src/knowledge_tracing/akt/research_junyi_roles.py',
                            ROOT / 'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md')}
    import duckdb
    with duckdb.connect(config={'memory_limit': '128MB', 'threads': '1'}) as connection:
        rows = connection.execute(
            "SELECT user_id, fold, partition FROM read_parquet(?) WHERE partition='development'",
            [str(assignments)]).fetchall()
    roles = make_junyi_research_roles(rows)
    original = json.loads(split_manifest.read_text(encoding='utf-8'))
    counts = {name: len(getattr(roles, name)) for name in
              ('train_users', 'selection_users', 'calibration_users', 'outer_validation_users')}
    assert sum(counts.values()) == original['development_students']
    assert counts['outer_validation_users'] == original['development_fold_students']['4']
    for relative, expected in sources.items():
        assert sha(ROOT / relative) == expected, 'Source changed during metadata preparation'
    output.mkdir(parents=True, exist_ok=False)
    payload = output / 'roles.json'
    payload.write_text(json.dumps(asdict(roles), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    manifest = dict(status='DEVELOPMENT_METADATA_ROLES_PREPARED', identity=roles.identity,
        counts=counts, source_sha256=sources, outputs_sha256={'roles.json': sha(payload)},
        events_read=False, correctness_read=False, holdout_events_read=False,
        training_performed=False, producer_integration_complete=False,
        limits='Derivative role manifest theo Protocol21. Chưa là input Junyi producer đã nghiệm thu hoặc lượt training.')
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == '__main__':
    main()
