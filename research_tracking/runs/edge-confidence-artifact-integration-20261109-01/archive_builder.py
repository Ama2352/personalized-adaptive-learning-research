"""Chuẩn bị dry/closure riêng; không gọi loader, pytest, solver hoặc corpus reader.

Chỉ ROOT chạy sau review. Các exports lớn giữ nguyên tại producer; builder không
mở chúng và không mở actual corpus, kể cả bank. DONE/14SHA đã được integration03
kiểm thật; archive dùng receipt đó và producer bundle đã đóng làm tham chiếu.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN_ID = 'edge-confidence-artifact-integration-20261109-01'
HELPER = ROOT/'src/knowledge_tracing/evidence.py'
HELPER_SHA = '414e3d834c46d081c7d9c05beff17a3e2d9c479a0e121394aabe321929235e49'
CURRENT = {
    'src/knowledge_tracing/edge_confidence_artifact.py': 'ecc313c5a52c3fbb56e06e84bbd1c0808191b956a35bad1ffced200728e01746',
    'tests/shared_kt/test_edge_confidence_artifact.py': 'f02fcb9e26585b015584ca2e0f95b76a4cd1b423868439ad07a6d9f78e92fe78',
}
VERSIONS = {
    'ee272b14e82224cb15fc68b857d439b5962d287f4ffb201e7599969a2aa7e62b': PREP/'pre-edge-resource-snapshot-fix01/edge_confidence_artifact.py.before',
    '1d50cd6fec3568676dcc39a4dc3a0080c672fd04e12837a86ceb37425e487c7e': PREP/'pre-edge-resource-snapshot-fix01/test_edge_confidence_artifact.py.before',
    '85c98c6e3c9fa203c1ffa7c7050fcc900bdce26aed243dfbcc54e1640c1c1626': PREP/'pre-edge-uint64-seed-fix01/edge_confidence_artifact.py.before',
    '9885dee184e3c3bab113af92de1795dbfeb72c853368ac0c41162b3f9a3581bf': PREP/'pre-edge-uint64-seed-fix01/test_edge_confidence_artifact.py.before',
}
REFERENCE = {
    'historical60': ('edge-artifact-cross-ready-engineering-20261109-01', 47),
    'producer': ('edge-confidence-windows-bootstrap-20261108-01', 113),
}
GENERATED = {'README.md', 'execution.log', 'copy_inventory_before.json', 'copy_inventory.json',
             'frozen_acceptance.json', 'resource_seed_compatibility.json', 'reference_inventory.json',
             'raw_log_paths.txt', 'closure_review.json'}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def physical(path):
    path = path.absolute()
    need(path.is_relative_to(ROOT) and ROOT.resolve() == ROOT.absolute(), 'fixed physical workspace only')
    cursor = ROOT
    for part in path.relative_to(ROOT).parts:
        cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'path alias')
    need(path.resolve() == path, 'physical path required')
    return path


def sha(path):
    path = physical(path)
    need(path.is_file() and path.stat().st_size <= 1024**2, 'small regular evidence only; no large exports')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    sha(path)
    return json.loads(path.read_text(encoding='utf-8-sig'))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def dump(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')


def inventory():
    need(sha(HELPER) == HELPER_SHA, 'evidence helper pin')
    for name, pin in CURRENT.items():
        need(sha(ROOT/name) == pin, 'current consumer source drift: '+name)
    rows = {}; names = set()
    def add(path, alias, role):
        path = physical(path); relative = path.relative_to(ROOT).as_posix()
        if relative in rows:
            return rows[relative]['copy']
        need(alias not in names and '/' not in alias and '\\' not in alias, 'unique flat output alias')
        rows[relative] = dict(source=relative, copy=alias, sha256=sha(path), bytes=path.stat().st_size, role=role)
        names.add(alias)
        return alias
    add(Path(__file__).resolve(), 'archive_builder.py', 'archive code; not experimental execution')
    add(HELPER, 'evidence_helper.py', 'immutable evidence helper')
    for name in CURRENT:
        add(ROOT/name, 'current__'+Path(name).name, 'current consumer implementation/test')
    for folder in ('edge-artifact-pre-clock-fixture-fix01', 'pre-edge-resource-snapshot-fix01', 'pre-edge-uint64-seed-fix01'):
        for path in sorted((PREP/folder).iterdir()):
            need(path.is_file(), 'snapshot directory contains unexpected subdirectory')
            add(path, folder+'__'+path.name, 'historical exact source/test bytes; never relabel as current')
    facts = dict(kind='READ_ONLY_METHOD24_ARTIFACT_CONSUMER_ENGINEERING_NOT_MODEL_FIT',
                 pure_trials={}, actual_readonly_trials={}, new_model_calls=0, new_solver_calls=0,
                 oracle_reads=0, original_producer_solver_calls=2352,
                 historical60_referenced_not_added_as_independent_cases=True,
                 no_independent_greedy_recomputation=True, no_edge_truth_probability_claim=True)
    for label, count in (('03', 58), ('04', 66)):
        folder = PREP/('edge-artifact-cross-ready'+label)
        owned = PREP/(folder.name+'-owned')
        final, result, receipt = (read(owned/'final.json'), read(folder/'result.json'), read(owned/'receipt.json'))
        need(final['status'] == f'ACCEPTED_{count}_DATA_ONLY_FIXTURES'
             and final['counts'] == dict(tests=count, failures=0, errors=0, skipped=0)
             and 0 <= final['elapsed_seconds'] < 150, 'pure accepted count/resource verdict')
        need(not (owned/'postwrite_rejection.json').exists(), 'pure postpublication rejection')
        tree = ET.parse(folder/'junit.xml').getroot()
        actual = {k: sum(int(x.get(k, '0')) for x in tree.iter('testsuite')) for k in ('tests', 'failures', 'errors', 'skipped')}
        need(actual == final['counts'] and result['source_before'] == result['source_after'], 'pure XML/source bindings')
        need(receipt['accepted'] and receipt['cleanup_accepted'] and receipt['job_active_after_cleanup'] == 0
             and receipt['popen_handle_closed'] and receipt['returncode'] == 0, 'pure owned cleanup')
        bindings = []
        for logical, digest in result['source_before'].items():
            actual_path = VERSIONS.get(digest, ROOT/logical)
            need(sha(actual_path) == digest, 'version-specific tested dependency: '+logical)
            bindings.append(dict(logical_source=logical, exact_source=actual_path.relative_to(ROOT).as_posix(), sha256=digest))
        facts['pure_trials'][label] = dict(tests=count, elapsed_seconds=final['elapsed_seconds'], cap_seconds=150,
            counts=actual, tested_sources=bindings, actual_data_reads=0, model_calls=0, solver_fits=0)
        for directory in (folder, owned):
            for path in sorted(directory.iterdir()):
                need(path.is_file() and path.suffix in ('.json', '.jsonl', '.xml', '.log'), 'pure file allowlist')
                add(path, directory.name+'__'+path.name, 'actual pure receipt/log/JUnit')
        for name in ('check_edge_artifact_cross_ready'+label+'.py', 'run_edge_artifact_cross_ready'+label+'.py',
                     'edge_artifact_cross_ready'+label+'_allocation.json'):
            add(PREP/name, name, 'exact pure controller/allocation')
    for label, accepted in (('01', False), ('02', False), ('03', True)):
        folder = PREP/('edge-artifact-native'+label); owned = PREP/(folder.name+'-owned')
        packet = read(PREP/('edge_artifact_native'+label+'_expectation.json'))
        final, result, receipt = read(owned/'final.json'), read(folder/'result.json'), read(owned/'receipt.json')
        packet_sha = sha(PREP/('edge_artifact_native'+label+'_expectation.json'))
        need(final['expectation_sha256'] == result['expectation_sha256'] == packet_sha
             and 0 <= final['elapsed_seconds'] < 30 and final['model_calls'] == final['new_solver_calls'] == 0,
             'actual readonly packet/time/scope')
        need(receipt['cleanup_accepted'] and receipt['job_active_after_cleanup'] == 0 and receipt['popen_handle_closed'],
             'actual readonly owned cleanup')
        need(result['source_before'] == packet['source_pins'], 'actual readonly before-source binding')
        if accepted:
            need(final['status'] == 'ACCEPTED_ACTUAL_ARTIFACT_READ_ONLY_NOT_MODEL_EFFICACY'
                 and result['status'] == 'READ_ONLY_COMPLETE_PENDING_OUTER' and receipt['accepted']
                 and receipt['returncode'] == 0 and final['score_count'] == 31
                 and result['source_before'] == result['source_after'], 'actual03 accepted scope')
            need(sha(folder/'result.json') == '0b5de848f8f50b214cf5038641d2d71c9c5b21ba96c3409bcdbe3dfcf21089f6'
                 and sha(folder/'output-manifest.json') == 'f10a60f68d72712f02ee81fd74b7ecf300cc084b7ec761fcb940785c673db328', 'ROOT terminal03 pins')
            summary = read(folder/'summary.json')
            need(len(summary['scores']) == 31 and all(x['supported'] and x['score'] is not None for x in summary['scores'])
                 and summary['semantics'] == 'conditional_predictive_stability_not_edge_truth_probability', 'typed score semantics')
        else:
            need(final['status'] == 'REJECTED_ACTUAL_ARTIFACT_READ_ONLY' and receipt['returncode'] == 1
                 and result['error']['message'] == ('producer RAM verdict' if label == '01' else 'integer/count required'),
                 'historical actual failure remains a failure')
        need(not (folder/'postbudget_failure.json').exists() and not (folder/'resource-failure.json').exists(), 'actual resource rejection marker')
        for logical, digest in packet['source_pins'].items():
            exact = VERSIONS.get(digest, ROOT/logical)
            need(sha(exact) == digest, 'historical actual source drift: '+logical)
        files = read(folder/'output-manifest.json')
        need(files['expectation_sha256'] == packet_sha
             and all(sha(folder/n) == h for n, h in files['files_sha256'].items()), 'actual small-output manifest')
        facts['actual_readonly_trials'][label] = dict(status=final['status'], elapsed_seconds=final['elapsed_seconds'],
            error=result['error'], source_after=result['source_after'], score_count=final['score_count'],
            expectation_sha256=packet_sha, model_calls=0, new_solver_calls=0)
        for directory in (folder, owned):
            for path in sorted(directory.iterdir()):
                need(path.is_file() and path.suffix in ('.json', '.log'), 'actual small file allowlist')
                add(path, directory.name+'__'+path.name, 'actual readonly receipt/log/output; failure preserved')
        for name in ('check_edge_artifact_native'+label+'.py', 'run_edge_artifact_native'+label+'.py',
                     'edge_artifact_native'+label+'_expectation.json', 'edge_artifact_native'+label+'_root_review.json'):
            add(PREP/name, name, 'exact readonly controller/packet/ROOT predispatch review')
        if label != '01':
            name = 'edge_artifact_native'+label+'_preparation_inventory.json'
            add(PREP/name, name, 'historical controller pre-edit inventory')
    references = {}
    for kind, (run_id, count) in REFERENCE.items():
        path = ROOT/'research_tracking/runs'/run_id/'manifest.json'; value = read(path)
        need(value['status'] == 'completed' and len(value['outputs_sha256']) == count, 'closed referenced bundle')
        references[kind] = dict(path=path.relative_to(ROOT).as_posix(), sha256=sha(path), output_count=count,
            scope_vi='Tham chiếu manifest đã đóng; không copy cả bundle, không fresh-rehash các exports lớn')
        add(path, 'reference__'+kind+'__manifest.json', 'closed prior bundle manifest reference only')
    producer = ROOT/'research_tracking/runs'/REFERENCE['producer'][0]
    resources = read(producer/'native__resources.json'); worker = read(producer/'native__worker_result.json')
    folds = read(producer/'native__folds.json')
    packet = read(PREP/'edge_artifact_native03_expectation.json')
    need(sha(producer/'manifest.json') == packet['accepted_bundle']['sha256'], 'producer bundle external pin')
    for name in ('native__resources.json', 'native__worker_result.json', 'native__folds.json'):
        manifest = read(producer/'manifest.json')
        need(sha(producer/name) == manifest['outputs_sha256'][name], 'producer small proof pin')
        add(producer/name, 'producer_proof__'+name, 'small pinned producer metadata; no corpus/event file')
    concepts = tuple(packet['declared_graph']['nodes']); parent, child = concepts[1], concepts[0]
    config = read(PREP/'method24_config01.json')
    need(sha(PREP/'method24_config01.json') == packet['artifact']['config_sha256'], 'proof recipe config pin')
    add(PREP/'method24_config01.json', 'producer_config_proof.json', 'pinned seed recipe context only')
    seed_payload = [config['recipe']['method_id'], 'learner-bootstrap', config['recipe']['seed'],
                    packet['expected_training']['plan_sha256'], folds['learner_ids'], parent, child]
    seed = int(hashlib.sha256(canonical(seed_payload)).hexdigest()[:16], 16)
    need(seed == 10342883151489376549 and 2**63 <= seed < 2**64, 'real first unsigned64 seed provenance')
    proof = dict(earlier_resources=resources, later_resources=worker['resources'],
        snapshots_are_cumulative_not_equal=resources != worker['resources'],
        observed_samples=[resources['samples'], worker['resources']['samples']],
        first_producer_edge=dict(parent_id=parent, child_id=child, bootstrap_seed=seed, signed63_overflow=True),
        seed_derivation='int(SHA256(canonical([method,learner-bootstrap,recipe_seed,logical_plan,sorted_train_ids,parent,child]))[:16],16)',
        formula_source_sha256=packet['expected_training']['method_source_sha256'],
        seed_recomputed_from_pinned_exported_metadata=True, large_edges_file_opened_by_archiver=False,
        actual03_loaded_all_summaries=True, independent_greedy_recomputation=False,
        scope_vi='Đối chiếu arithmetic/hash metadata, không fit/bootstrap lại hoặc đọc OOF/labels/oracle.')
    facts['current_sources'] = CURRENT
    facts['reference_bundles'] = references
    return dict(schema_version=1, run_id=RUN_ID, copies=sorted(rows.values(), key=lambda x: x['copy']),
                facts=facts, references=references, compatibility_proof=proof,
                generated_outputs=sorted(GENERATED), expected_output_count=len(rows)+len(GENERATED))


NOTE = """# Loader artifact Method24: kiểm thu read-only

Đây là bằng chứng tích hợp phần mềm trên artifact Method24 thật đã được ROOT chấp nhận; không phải một lần fit mới hoặc kết quả CG-AKT fitted. API `load_method24_scores` yêu cầu caller cấp typed external artifact/training/source/runtime/bank pins và giới hạn đọc. Kết quả immutable giữ nguyên score0 khác null thiếu support và lý do. Scores biểu thị conditional predictive stability, không phải xác suất cạnh là prerequisite thật; không có converter tự động sang legacy `EdgeConfidence` hoặc adoption recipe graph neural.

Hai revision pure được lưu riêng: trial03 có58cases và trial04 có66cases. Không cộng chúng thành independent observations. PURE60 lịch sử (loader51+cross-ready9) được tham chiếu bằng manifest47outputs riêng, không gắn PASS đó vào source hiện tại.

Integration read-only01 bị từ chối vì consumer từng yêu cầu hai cumulative RAM snapshots bằng nhau: producer ghi samples2582 rồi2584, cùng peak263442432bytes và minimum-free1599983616bytes. Sửa contract kiểm cả hai closed schemas/types/caps/cùngscope; samples/peak chỉ tăng hoặc bằng, minimum-free chỉ giảm hoặc bằng. Integration02 vẫn bị từ chối vì bootstrap seed10342883151489376549 thuộc unsigned64 và vượt signed63 của count validator. Sửa riêng seed thành `type int, 0<=seed<2**64`, không nới count bounds. Raw failures và source đúng từng revision được giữ nguyên.

Integration03 được chấp nhận: một loader call đọc/hash14outputs thật, DONE bind13outputs khác; trả31scores có kiểu và lineage, không fit solver/NN, không đọc learner trajectories/labels/oracle. Graph `method24_learned` phải đúng declared31-edge DAG supported, acyclic, positive-supported pair population và edge budget. Chế độ declared graph giữ riêng, không biến learned graph thiếu budget thành supported. Offload/convert sang tensor hoặc train graph model nằm ngoài gói này.

Caller pins và kiểm in-process chỉ hỗ trợ provenance hợp tác, không chữ ký chống giả mạo hoặc runtime attestation hiện tại. Runtime/source receipts nói về producer lịch sử. Greedy ordering/cycle rejection fidelity được giao cho producer đã pin/review; consumer độc lập kiểm structure/population/budget, không replay greedy learner. Ngân sách RAM là telemetry polling cooperative, không hard OS quota. Owned Job cleanup và outer postpublication elapsed verdict được giữ riêng trong raw receipts.

`frozen_acceptance.json` ghi đúng số test/time/trạng thái từng trial. `resource_seed_compatibility.json` đối chiếu hai snapshots và derive unsigned64 seed từ exported metadata đã pin; không đọc large OOF hay fit ledger. `copy_inventory_before.json` và `copy_inventory.json` ghi SHA/size trước và sau copy. `reference_inventory.json` trỏ producer113 và PURE60/47; các exports khoảng69.5MB vẫn ở producer run gốc, không được copy hoặc fresh-hash lại bởi archive builder. Source/tests hiện tại và lịch sử có alias riêng. Không suy graph truth, lợi ích CG-AKT, current Gate hoặc kết luận RQ3 từ gói này.
"""


def main():
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--dry-json', type=Path)
    action.add_argument('--close', action='store_true')
    parser.add_argument('--expected-dry-sha256')
    parser.add_argument('--review-reference')
    args = parser.parse_args()
    current = inventory()
    if args.dry_json is not None:
        path = physical(args.dry_json)
        need(not path.exists() and path.parent == PREP, 'new prep-only dry inventory')
        dump(path, current)
        print(json.dumps(dict(dry=str(path.relative_to(ROOT)), sha256=sha(path),
                              copies=len(current['copies']), expected_outputs=current['expected_output_count'])))
        return
    need(type(args.review_reference) is str and bool(args.review_reference.strip()), 'ROOT concrete closure review reference required')
    dry = PREP/'edge_artifact_integration_archive_dry01.json'
    need(args.expected_dry_sha256 is not None and sha(dry) == args.expected_dry_sha256, 'reviewed exact dry SHA required')
    need(read(dry) == current, 'selected input/output/proof drift after dry review')
    spec = importlib.util.spec_from_file_location('reviewed_evidence_archive_helper', HELPER)
    evidence = importlib.util.module_from_spec(spec); spec.loader.exec_module(evidence)
    metadata = dict(current['facts'], closure_review_reference=args.review_reference,
                    approved_dry_sha256=args.expected_dry_sha256)
    source_paths = [ROOT/x['source'] for x in current['copies']] + [dry]
    with evidence.record_evidence_run(ROOT, RUN_ID, metadata=metadata, sources=source_paths, note=NOTE) as directory:
        dump(directory/'copy_inventory_before.json', current)
        copies = []
        for row in current['copies']:
            source = ROOT/row['source']; target = directory/row['copy']
            need(sha(source) == row['sha256'] and source.stat().st_size == row['bytes'], 'precopy source drift')
            with source.open('rb') as incoming, target.open('xb') as outgoing:
                shutil.copyfileobj(incoming, outgoing)
            need(sha(source) == sha(target) == row['sha256'] and target.stat().st_size == row['bytes'], 'copy SHA/size drift')
            copies.append(dict(row, source_sha256_after=sha(source), copy_sha256=sha(target)))
        dump(directory/'copy_inventory.json', copies)
        dump(directory/'frozen_acceptance.json', current['facts'])
        dump(directory/'resource_seed_compatibility.json', current['compatibility_proof'])
        dump(directory/'reference_inventory.json', current['references'])
        dump(directory/'closure_review.json', dict(reference=args.review_reference, approved_dry_sha256=args.expected_dry_sha256,
                                                  tests_rerun=False, loader_rerun=False, model_or_solver_calls=0))
        (directory/'raw_log_paths.txt').write_text('\n'.join(x['source'] for x in current['copies']
            if x['source'].endswith(('.log', '.xml', '.jsonl')))+'\n', encoding='utf-8')
        need({p.name for p in directory.iterdir()} == {x['copy'] for x in current['copies']} | GENERATED | {'manifest.json'}, 'exact closure output population')
    directory = ROOT/'research_tracking/runs'/RUN_ID
    verified = evidence.verify_evidence_bundle(directory)
    need(verified['artifacts'] == current['expected_output_count'], 'exact verified output count')
    print(json.dumps(dict(bundle=directory.relative_to(ROOT).as_posix(), manifest_sha256=sha(directory/'manifest.json'), **verified)))


if __name__ == '__main__':
    main()
