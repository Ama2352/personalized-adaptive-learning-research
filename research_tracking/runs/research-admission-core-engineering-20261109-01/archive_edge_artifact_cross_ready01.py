"""Dry/closure do ROOT dispatch; không chạy tests, loader hoặc analyzer."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN_ID = 'edge-artifact-cross-ready-engineering-20261109-01'
GENERATED = ('README.md', 'execution.log', 'copy_inventory_before.json', 'copy_inventory.json',
             'frozen_acceptance.json', 'source_references.json', 'closure_review.json', 'raw_log_paths.txt')
HELPER = 'src/knowledge_tracing/evidence.py'
OWNED_FILES = ('final.json', 'GO.json', 'launch.json', 'ready.json', 'receipt.json', 'stdout.log', 'stderr.log')
SNAP = PREP/'pre-edge-resource-snapshot-fix01'
REMAP = {'src/knowledge_tracing/edge_confidence_artifact.py': SNAP/'edge_confidence_artifact.py.before',
         'tests/shared_kt/test_edge_confidence_artifact.py': SNAP/'test_edge_confidence_artifact.py.before'}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def physical(path):
    p = Path(path).absolute()
    need(p.is_relative_to(ROOT), 'workspace path only')
    cursor = ROOT
    for part in p.relative_to(ROOT).parts:
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'path alias')
    need(p.resolve() == p, 'physical path required')
    return p


def sha(path):
    p = physical(path)
    need(p.is_file() and p.stat().st_size <= 8*1024**2, 'bounded regular evidence file')
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(path):
    return json.loads(physical(path).read_bytes())


def finite(value, cap):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= cap


def owned(directory):
    r = read(directory/'receipt.json')
    need(r['accepted'] is True and r['cleanup_accepted'] is True and r['job_active_after_cleanup'] == 0
         and r['popen_handle_closed'] is True and r['actual_worker_in_job_before_GO'] is True
         and r['returncode'] == 0 and not r['errors'], 'owned acceptance/cleanup')
    for name, pin in r['output_sha256'].items():
        need(name in ('stdout.log', 'stderr.log') and sha(directory/name) == pin, 'owned log drift')
    return r


def verify():
    a = read(PREP/'edge_artifact_cross_ready02_allocation.json')
    r = read(PREP/'edge-artifact-cross-ready02/result.json')
    f = read(PREP/'edge-artifact-cross-ready02-owned/final.json')
    first = read(PREP/'edge-artifact-cross-ready01-owned/final.json')
    need(first['status'] == 'REJECTED_DATA_ONLY_FIXTURES' and first['counts'] is None,
         'preserve failed startup, not failed tests')
    need(f['status'] == 'ACCEPTED_60_DATA_ONLY_FIXTURES' and f['counts'] ==
         dict(tests=60, failures=0, errors=0, skipped=0) and finite(f['elapsed_seconds'], 150), 'pure60 terminal')
    need(r['pytest_exit_code'] == 0 and r['counts'] == f['counts'] and r['error'] is None
         and r['source_before'] == r['source_after'] == a['source_pins'] and r['source_unchanged'] is True
         and r['environment_restored'] is True and r['monitor_stopped'] is True and not r['monitor_errors']
         and not r['forbidden_attempts'] and not r['unexpected_heavy_modules'], 'pure result/source/resources')
    need(all(type(r[k]) is int and r[k] == 0 for k in ('model_calls', 'solver_fits', 'actual_corpus_reads')), 'pure scope')
    need(a['expected_cases'] == 60 and a['partition_expected'] == dict(edge_artifact=51, cross_ready=9), 'case partition')
    need(sha(SNAP/'inventory-before.json') == '750ded8de7049d945507360c429b1f4d596712cf6413342a004ad58a2400ca91'
         and sha(SNAP/'copy-verification.json') == '1e3bb39ca680c2dbaf104f0d3df0d6e163a3f3462fe58b22ee90a97eda13e289',
         'historical tested source relocation receipts')
    for name, pin in a['source_pins'].items():
        need(sha(REMAP.get(name, ROOT/name)) == pin, 'executed source/snapshot drift: '+name)
    proof_rows = read(SNAP/'copy-verification.json')
    need(len(proof_rows) == 2 and {r['source'] for r in proof_rows} == set(REMAP), 'exact2 historical tested snapshots')
    for row in proof_rows:
        need(ROOT/row['copy'] == REMAP[row['source']] and row['sha256_before'] == row['sha256_copy'] ==
             row['sha256_after'] == a['source_pins'][row['source']], 'historical before/copy/after SHA')
    need(sha(PREP/'check_edge_artifact_cross_ready02.py') == a['worker_sha256'], 'pure worker pin')
    tree = ET.fromstring((PREP/'edge-artifact-cross-ready02/junit.xml').read_bytes())
    cases = list(tree.iter('testcase'))
    need(len(cases) == 60 and not any(list(c) for c in cases), 'JUnit60 no failure/error/skip children')
    receipt = owned(PREP/'edge-artifact-cross-ready02-owned')
    need(receipt['worker_sha256'] == a['worker_sha256'] and receipt['max_seconds'] == 147
         and receipt['cleanup_reserve_seconds'] == 3 and finite(receipt['elapsed_seconds'], 147), 'pure owned allocation')
    need(not (PREP/'edge-artifact-cross-ready02-owned/postwrite_rejection.json').exists(), 'late rejection')
    before = PREP/'edge-artifact-pre-clock-fixture-fix01'
    proof = read(before/'copy-verification.json')
    need(proof['verified'] is True and proof['source_sha256_before'] == proof['copy_sha256'] ==
         proof['source_sha256_after'] == sha(before/'test_edge_confidence_artifact.py.before'), 'pre-fixture snapshot')
    paths = {HELPER: sha(ROOT/HELPER), **{REMAP.get(n, ROOT/n).relative_to(ROOT).as_posix():h for n,h in a['source_pins'].items()}}
    acceptance = dict(kind='SOFTWARE_DATA_ONLY_FIXTURES_NOT_RESEARCH_EFFICACY', tests=60,
        loader_cases=51, cross_ready_cases=9, failed_startup_preserved=True, actual_data_reads=0,
        model_calls=0, solver_fits=0, caller_prewrite_elapsed_seconds=f['elapsed_seconds'],
        cap_seconds=150, numpy_allowed_for_shared_graph_types=True, actual_loader_acceptance=False,
        tested_logical_source_sha256=a['source_pins'],
        historical_source_remaps={n:p.relative_to(ROOT).as_posix() for n,p in REMAP.items()},
        tested_loader_superseded_after_actual_resource_snapshot_incompatibility=True)
    return acceptance, paths


def selections():
    pairs = [(REMAP.get(name, ROOT/name), 'source__'+name.replace('/', '__')) for name in (
        'src/knowledge_tracing/edge_confidence_artifact.py', 'tests/shared_kt/test_edge_confidence_artifact.py',
        'scripts/research/analyze_rq1_cross_ready.py', 'tests/shared_kt/test_rq1_cross_ready.py', HELPER,
        'scripts/research/windows_owned_worker.py')]
    for name in ('check_edge_artifact_cross_ready01.py', 'run_edge_artifact_cross_ready01.py',
                 'check_edge_artifact_cross_ready02.py', 'run_edge_artifact_cross_ready02.py',
                 'edge_artifact_cross_ready01_allocation.json', 'edge_artifact_cross_ready02_allocation.json'):
        pairs.append((PREP/name, name))
    groups = {
        'edge-artifact-cross-ready01': ('source_before.json',),
        'edge-artifact-cross-ready02': ('source_before.json', 'result.json', 'junit.xml', 'case_events.jsonl', 'pytest.log'),
        'edge-artifact-cross-ready01-owned': OWNED_FILES,
        'edge-artifact-cross-ready02-owned': OWNED_FILES,
        'edge-artifact-pre-clock-fixture-fix01': ('inventory-before.json', 'copy-verification.json', 'test_edge_confidence_artifact.py.before'),
        'pre-edge-resource-snapshot-fix01': ('inventory-before.json', 'copy-verification.json'),
    }
    for folder, names in groups.items():
        pairs.extend((PREP/folder/n, folder+'__'+n) for n in names)
    return pairs


def note():
    return '''# Kiểm kỹ thuật bộ đọc edge confidence và hậu kiểm ready membership

51cases bộ đọc +9cases pure join/set arithmetic =60PASS, không actual loader trên dữ liệu nghiên cứu, không analyzer trên cache, không fit/model/teacher. NumPy chỉ phục vụ shared graph types; metadata Windows là quan sát OS thật của controller, không giả OS.

Giữ failed startup01 (thiếu src trong sys.path, trước collection; không gọi đó là failed scientific result) và accepted02 riêng. Snapshot trước sửa fixture clock giữ bytes gốc. 60PASS không trả lời RQ hoặc chứng minh graph/model efficacy.

Nguồn loader ee272/test1d50 ở đây là bản đã chạy60purecases, được copy từ pre-edge-resource-snapshot-fix01 với before/copy/afterSHA. Bản này đã được thay thế sau khi actual producer resource snapshots có2582/2584samples và cùng extrema bị điều kiện equality cũ từ chối.60PASS không chứng nhận tương thích actualproducer; lỗi tích hợp và nguồn sửa mới thuộc archive riêng. Không gắn PASS cũ với code mới.

copy_inventory_before.json/copy_inventory.json giữ SHA trước/sau; source_references.json giữ nguồn dùng để đối chiếu, không copy corpus/Method24 output lớn. execution.log là log đóng gói, các stdout/stderr/JUnit gốc nằm riêng. Không có .pt/Parquet/CSV nghiên cứu hay secret. Helper chuẩn chỉ read-only Git HEAD, không add/commit/push.
'''


def build_spec(run_id, verify_fn, selection_fn, note_fn, args):
    acceptance, pointers = verify_fn()
    pairs = selection_fn()+[(Path(__file__).resolve(), 'archive_edge_artifact_cross_ready01.py')]
    if args.report is not None:
        need(sha(args.report) == args.expected_report_sha256, 'reviewed report pin')
        pairs.append((physical(args.report), 'report_snapshot.md'))
    for i, p in enumerate(args.optional_review_file, 1):
        p = physical(p)
        need(p.parent == PREP and p.suffix in ('.py', '.json', '.log', '.txt'), 'direct prep optional review')
        pairs.append((p, f'optional_review_{i:02d}__'+p.name))
    rows = []
    for path, alias in pairs:
        need(alias and not any(c in alias for c in '/\\:\t\r\n') and alias not in GENERATED, 'safe unique alias')
        path = physical(path)
        rows.append(dict(source=path.relative_to(ROOT).as_posix(), copy=alias, sha256=sha(path), bytes=path.stat().st_size))
    need(len({v['copy'] for v in rows}) == len(rows) and sum(v['bytes'] for v in rows) <= 8*1024**2, 'unique small copy inventory')
    pointers.update({v['source']: v['sha256'] for v in rows})
    return dict(status='DRY_ONLY_NO_BUNDLE', run_id=run_id, acceptance=acceptance, copy_pairs=rows,
        sources_sha256=pointers, selected_bytes=sum(v['bytes'] for v in rows),
        expected_output_count=len(rows)+1+len(GENERATED), original_compressed_inputs_copied=False)


def entry(run_id=RUN_ID, verify_fn=verify, selection_fn=selections, note_fn=note, *, required_report=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=('dry', 'close')); p.add_argument('--inventory-output', type=Path, required=True)
    p.add_argument('--report', type=Path); p.add_argument('--expected-report-sha256')
    p.add_argument('--optional-review-file', type=Path, action='append', default=[])
    p.add_argument('--approved-dry-sha256'); p.add_argument('--approval-reference')
    args = p.parse_args(); args.inventory_output = physical(args.inventory_output)
    if required_report is not None:
        need(args.report is not None and physical(args.report) == required_report and args.expected_report_sha256,
             'exact canonical report and reviewed SHA required')
    need(args.inventory_output.parent == PREP and args.inventory_output.suffix == '.json', 'direct prep dry path')
    dry = build_spec(run_id, verify_fn, selection_fn, note_fn, args)
    if args.mode == 'dry':
        with args.inventory_output.open('x', encoding='utf-8') as f:
            json.dump(dry, f, ensure_ascii=False, indent=2); f.write('\n')
        print(json.dumps(dict(status=dry['status'], sha256=sha(args.inventory_output), outputs=dry['expected_output_count'])))
        return
    need(args.approval_reference and sha(args.inventory_output) == args.approved_dry_sha256
         and read(args.inventory_output) == dry, 'ROOT exact approved dry/closure reference')
    need(not (ROOT/'research_tracking/runs'/run_id).exists(), 'no overwrite/retry')
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    pairs = dry['copy_pairs']+[dict(source=args.inventory_output.relative_to(ROOT).as_posix(),
        copy='approved_dry_inventory.json', sha256=sha(args.inventory_output), bytes=args.inventory_output.stat().st_size)]
    before = [{**v, 'sha256_before_copy': v['sha256']} for v in pairs]
    sources = sorted({ROOT/n for n in dry['sources_sha256']}|{args.inventory_output})
    def dump(directory, name, value):
        with (directory/name).open('x', encoding='utf-8') as f:
            json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False); f.write('\n')
    with record_evidence_run(ROOT, run_id, metadata={**dry['acceptance'], 'closure_approval_reference': args.approval_reference,
            'approved_dry_sha256': args.approved_dry_sha256}, sources=sources, note=note_fn()) as directory:
        dump(directory, 'copy_inventory_before.json', before)
        for v in pairs:
            source = ROOT/v['source']
            need(sha(source) == v['sha256'], 'precopy source drift')
            with source.open('rb') as src, (directory/v['copy']).open('xb') as dst:
                shutil.copyfileobj(src, dst)
        after = []
        for v in pairs:
            need(sha(ROOT/v['source']) == sha(directory/v['copy']) == v['sha256']
                 and (directory/v['copy']).stat().st_size == v['bytes'], 'postcopy byte/SHA drift')
            after.append({**v, 'sha256_after_copy': v['sha256'], 'exact_match': True})
        acceptance_after, _ = verify_fn()
        need(acceptance_after == dry['acceptance'], 'postcopy acceptance')
        for name, pin in dry['sources_sha256'].items():
            need(sha(ROOT/name) == pin, 'source/reference postcopy drift')
        dump(directory, 'copy_inventory.json', after)
        dump(directory, 'frozen_acceptance.json', dry['acceptance'])
        dump(directory, 'source_references.json', dict(sources_sha256=dry['sources_sha256'], original_compressed_inputs_copied=False))
        dump(directory, 'closure_review.json', dict(approval_reference=args.approval_reference, approved_dry_sha256=args.approved_dry_sha256))
        with (directory/'raw_log_paths.txt').open('x', encoding='utf-8') as f:
            log_names = sorted({'execution.log'}|{v['copy'] for v in pairs if v['copy'].endswith('.log')})
            f.write(''.join((directory/name).relative_to(ROOT).as_posix()+'\n' for name in log_names))
        need({v.name for v in directory.iterdir()} == {v['copy'] for v in pairs}|set(GENERATED)|{'manifest.json'}, 'exact outputs')
    verified = verify_evidence_bundle(directory)
    need(verified['artifacts'] == dry['expected_output_count'], 'closed count')
    print(json.dumps(dict(**verified, manifest_sha256=sha(directory/'manifest.json'), run_id=run_id)))


if __name__ == '__main__':
    entry()
