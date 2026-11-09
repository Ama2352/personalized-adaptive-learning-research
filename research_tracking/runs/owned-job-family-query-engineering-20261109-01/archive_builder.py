"""Đóng bằng chứng metadata Jobquery, giữ scope riêng với simulator/nativeNN."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN = 'owned-job-family-query-engineering-20261109-01'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

outer = PREP / 'owned-job-query-metadata01-owned/final.json'
assert sha(outer) == 'e4ce1c58a29a3f91192abde66203ebe778093c9c4112a6988c590a30d36347e7'
result = json.loads(outer.read_bytes())
child, owned = result['child'], result['receipt']
assert result['status'] == 'ACCEPTED_JOB_QUERY_METADATA_NOT_NATIVE'
assert result['source_before'] == result['source_after']
assert child['status'] == 'ACCEPTED_JOB_QUERY_METADATA_CHILD' and child['handle_closed']
assert len(child['samples']) == 6 and child['scientific_modules_absent']
assert owned['accepted'] and owned['returncode'] == 0 and owned['job_active_after_cleanup'] == 0
assert owned['cleanup_accepted'] and owned['popen_handle_closed']
assert all(len(row['owned_job_members_outside_worker_descendants']) == 1 for row in child['samples'])
files = {}
for folder in ('owned-job-query-metadata01', 'owned-job-query-metadata01-owned'):
    for path in (PREP / folder).iterdir():
        assert path.is_file() and not path.is_symlink()
        files[folder + '__' + path.name] = path
for name in ('check_owned_job_query_metadata01.py', 'run_owned_job_query_metadata01.py'):
    files[name] = PREP / name
files['windows_owned_worker.py'] = ROOT / 'scripts/research/windows_owned_worker.py'
files['archive_builder.py'] = Path(__file__).resolve()
inventory = [dict(copy=name, source=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size,
                  sha256=sha(path)) for name, path in files.items()]
save(PREP / 'owned_job_query_inventory_before01.json', inventory)
review = dict(status='ROOT_VERIFIED_SIX_METADATA_SAMPLES',
    outer_sha256=sha(outer), samples=6,
    sampled_family_peak_bytes=max(s['family_rss_bytes'] for s in child['samples']),
    worker_highwater_bytes=max(s['worker_highwater_bytes'] for s in child['samples']),
    observed_minimum_available_bytes=min(s['available_bytes'] for s in child['samples']),
    handle_closed=True, job_active_after_cleanup=0,
    scope='Six sampled exact ownedJob queries, worker highwater and metadata-only128MiB/free1GiB/admission1280MiB.',
    empirical_finding='Eachsample has one owned Job member outside worker descendants.',
    scientific_new_N=0, new_model_calls=0, inference_of_old_full_family_peak=False)
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
note = ('# Đo RAM theo named owned Job\n\n'
    'Root đã chạy6metadata samples trong owned Job, actual terminal0 và cleanupJob0. '
    'Mỗi sample thấy một Job member ngoài worker descendants. Sampled family peak43.454.464B, '
    'worker highwater24.276.992B và free tối thiểu2.095.341.568B. '
    'Đã đóng query handles, không import Torch/NumPy/Pandas/KT hoặc gọi model/world. '
    'Đây là probe hữu hạn của query API, chưa là hard memory quota hoặc fulltraining readiness. '
    'Telemetry cũ ghi family từ worker+descendants cần đọc đúng scope, chưa chứng minh wholeJob peak. '
    'Raw khoa học cũ được giữ nguyên. Pilot fresh02 dùng fullJob query trong allocation riêng.\n')
with record_evidence_run(ROOT, RUN, sources=[*files.values(), PREP / 'owned_job_query_inventory_before01.json'],
        metadata=dict(kind='OWNED_JOB_FAMILY_METADATA_ENGINEERING', model_calls=0, scientific_new_N=0), note=note) as out:
    for row in inventory:
        source = ROOT / row['source']
        assert sha(source) == row['sha256']
        (out / row['copy']).write_bytes(source.read_bytes())
        assert sha(source) == sha(out / row['copy']) == row['sha256']
    save(out / 'copy_inventory.json', inventory)
    save(out / 'root_review.json', review)
verified = verify_evidence_bundle(ROOT / 'research_tracking/runs' / RUN)
print(json.dumps(dict(status='CLOSED_METADATA_QUERY_ONLY', outputs=verified['artifacts'],
    manifest_sha256=sha(ROOT / 'research_tracking/runs' / RUN / 'manifest.json'))))
