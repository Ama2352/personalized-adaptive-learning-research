"""Kiểm metadata Development và tạo hợp đồng so sánh từ A0 H100 đã chạy."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from knowledge_tracing.akt.comparison_contract import TRAINING_FIELDS, require_matched_candidate
from knowledge_tracing.akt.research_junyi_roles import make_junyi_research_roles


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4*1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--observed', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT/'research_tracking/runs') or output.exists():
        parser.error('Dùng output JSON mới trong research_tracking/runs')
    bundle = ROOT/'research_tracking/runs/junyi-a0-h100-batch128-20261112-01'
    request = read(bundle/'request.json')
    pins = request['inputs']
    pinned_files = dict(roles=(pins['roles_path'], pins['roles_sha256']),
        encoding=(pins['encoding_file'], pins['encoding_sha256']),
        encoding_receipt=(pins['encoding_receipt'], pins['encoding_receipt_sha256']),
        selected_manifest=(pins['selected_cache_root']+'/manifest.json', pins['selected_cache_manifest_sha256']),
        window_manifest=(pins['train_window_cache']+'/manifest.json', pins['train_window_manifest_sha256']))
    checks = {}
    for key, (relative, expected) in pinned_files.items():
        if sha(ROOT/relative) != expected:
            raise ValueError(f'A0 input changed: {key}')
        checks[key] = expected
    roles_payload = read(ROOT/pins['roles_path'])
    cache = read(ROOT/pins['selected_cache_root']/'manifest.json')
    if any(cache[key] is not False for key in ('calibration_events_included',
            'outer_validation_events_included', 'holdout_events_included')):
        raise ValueError('Forbidden phase in selected cache')
    for name, entry in cache['outputs'].items():
        path = ROOT/pins['selected_cache_root']/name
        if path.stat().st_size != entry['bytes'] or sha(path) != entry['sha256']:
            raise ValueError(f'Selected cache changed: {name}')
    assignment = ROOT/'artifacts/bkt_baseline/splits/assignments.parquet'
    assignment_sha = sha(assignment)
    expected_assignment = cache['source_sha256']['artifacts/bkt_baseline/splits/assignments.parquet']
    gam = read(ROOT/'experiments/gam_kt/results/wsl_cpp/cv/cv.json')
    if assignment_sha != expected_assignment or assignment_sha != gam['protocol']['assignments_sha256']:
        raise ValueError('BKT/GAM/AKT frozen assignments mismatch')
    import duckdb
    connection = duckdb.connect()
    try:
        connection.execute("SET memory_limit='256MB'")
        connection.execute('SET threads=1')
        rows = connection.execute("SELECT user_id, fold, partition FROM read_parquet(?) "
            "WHERE partition='development' ORDER BY user_id", [str(assignment)]).fetchall()
    finally:
        connection.close()
    expected_roles = make_junyi_research_roles(rows)
    for field in ('train_users','selection_users','calibration_users','outer_validation_users'):
        if tuple(roles_payload[field]) != getattr(expected_roles, field):
            raise ValueError(f'Frozen assignment/role mismatch: {field}')
    if cache['roles_identity'] != expected_roles.identity:
        raise ValueError('Roles digest mismatch')
    window = read(ROOT/pins['train_window_cache']/'manifest.json')
    receipt = read(ROOT/pins['encoding_receipt'])
    encoding = read(ROOT/pins['encoding_file'])
    if not (window['key']['encoding_identity'] == receipt['encoding_identity']
            and window['key']['phase_view_identity'] == receipt['fit_view_identity']
            and receipt['phase_scope'] == window['key']['phase_scope'] == 'select_train80'
            and receipt['source_data_sha256'] == window['key']['source_data_sha256']):
        raise ValueError('Vocabulary or window phase lineage mismatch')
    archive = ROOT/'experiments/akt/results/modal-junyi-a0-b128-h100-20261112-03/artifacts.zip'
    verification = read(bundle/'modal-junyi-a0-b128-h100-20261112-03-verification.json')
    with zipfile.ZipFile(archive) as stream:
        member = 'experiments/akt/results/modal-junyi-a0-b128-h100-20261112-01/'
        actual = json.loads(stream.read(member+'run-manifest.json'))
        initial = json.loads(stream.read(member+'initial-backbone.json'))
    population = {row['validation']['population_sha256'] for row in verification['history']}
    if len(population) != 1:
        raise ValueError('A0 selection population changed across epochs')
    reference = dict(candidate_id='A0', data_pins=checks, roles_identity=expected_roles.identity,
        encoding_identity=receipt['encoding_identity'], train_view_identity=receipt['fit_view_identity'],
        train_targets=request['train_targets'], selection_targets=request['selection_targets'],
        training_config={key: actual['config'][key] for key in TRAINING_FIELDS},
        numeric_profile=actual['profile'], initial_backbone_sha256=initial['sha256'],
        prediction_implementation=actual['prediction_implementation'],
        selection_population_sha256=population.pop())
    # Hợp đồng A0 phải tự nhất quán trước khi dùng chặn candidate khác.
    require_matched_candidate(reference, dict(reference,
        observed_selection_population_sha256=reference['selection_population_sha256']), observed=True)
    candidate_status = 'NOT_SUPPLIED_NOT_APPROVED_FOR_TRAINING'
    if args.candidate:
        require_matched_candidate(reference, read(args.candidate), observed=args.observed)
        candidate_status = 'OBSERVED_MATCH' if args.observed else 'SPECIFICATION_MATCH_PENDING_RUNTIME'
    result = dict(status='PASS_A0_DATA_LINEAGE_CANDIDATES_PENDING', reference=reference,
        candidate_status=candidate_status, bkt_gam_assignments_sha256=assignment_sha,
        role_counts={field:len(getattr(expected_roles,field)) for field in
            ('train_users','selection_users','calibration_users','outer_validation_users')},
        development_learners=len(rows), vocabulary_size=len(encoding['values']),
        window_summary=window['summary'], cache_output_sha256={name:entry['sha256'] for name,entry in cache['outputs'].items()},
        limits_vi='Kiểm metadata và hash cache. Chưa replay toàn bộ target, chưa CUDA A1–A3, chưa chứng minh không có mọi dạng leakage. BKT/GAM lịch sử fit outer-train khác AKT train80. Hợp đồng chưa được nối bắt buộc vào mọi launcher.')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({key:result[key] for key in ('status','candidate_status','role_counts','vocabulary_size')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
