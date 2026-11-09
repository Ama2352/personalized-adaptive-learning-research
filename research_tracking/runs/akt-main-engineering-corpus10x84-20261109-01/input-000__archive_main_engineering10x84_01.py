"""ROOT-only metadata inventory/closure; không collect/fit hoặc parse oracle."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN_ID = 'akt-main-engineering-corpus10x84-20261109-01'
REPORT = ROOT/'research_tracking/reports/akt_main_engineering_corpus10x84_20261109.md'
CORPUS = ROOT/'artifacts/simulator/corpora/grade10-main-lifecycle-engineering10x84-20261109-01'
OUT = PREP/'main-engineering10x84-01'
PURE = PREP/'main-engineering10x84-pure01'
PUBLIC10 = {'corpus.json','bank.json','plan.json','train.jsonl','train.manifest.json',
            'selection.jsonl','selection.manifest.json','calibration.jsonl','calibration.manifest.json','DONE.json'}
ORACLE7 = {'oracle/'+role+suffix for role in ('train','selection','calibration') for suffix in ('.json','.collection.json')}
ORACLE7.add('oracle/publication-inventory.json')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def safe(path):
    need(path.is_absolute() and path.is_relative_to(ROOT) and '..' not in path.parts, 'fixed project path')
    cursor = ROOT
    for part in (None, *path.relative_to(ROOT).parts):
        if part is not None:
            cursor /= part
        need(not cursor.is_symlink() and not cursor.is_junction(), 'physical evidence path')
    need(path.is_file(), 'regular evidence input')
    return path


def sha(path):
    with safe(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False); stream.write('\n')


def owned_ok(receipt):
    need(receipt['accepted'] is True and receipt['returncode'] == 0 and receipt['cleanup_accepted'] is True
         and receipt['actual_worker_in_job_before_GO'] is True and receipt['job_active_after_cleanup'] == 0
         and receipt['popen_handle_closed'] is True and receipt['errors'] == receipt['cleanup_errors'] == [], 'actual owned Job0/cleanup')


def gather(report_sha):
    payloads, references = {}, {}
    def read(path):
        safe(path)
        need(not path.is_relative_to(CORPUS), 'canonical corpus reference only, no copy or JSON parse')
        if path not in payloads:
            need(path.suffix in ('.py','.md','.json','.log'), 'small textual evidence')
            payload = path.read_bytes(); need(len(payload) <= 1024**2, 'per-file1MiB')
            payloads[path] = payload; need(sum(map(len, payloads.values())) <= 4*1024**2, 'compact4MiB total')
        return payloads[path]
    def load(path):
        return json.loads(read(path))
    def reference(path, pin, scope):
        need(sha(path) == pin, 'referenced bytes unchanged')
        name = path.relative_to(ROOT).as_posix()
        if name in references:
            need(references[name]['sha256'] == pin, 'reference identity collision')
        references[name] = dict(sha256=pin, bytes=path.stat().st_size, scope=scope, copy=False)
    def flat(folder):
        need(folder.is_dir() and not folder.is_symlink() and not folder.is_junction(), 'actual terminal evidence folder')
        for path in sorted(folder.iterdir()):
            if path.name == 'runtime-temp':
                continue
            need(path.is_file(), 'flat terminal evidence only')
            read(path)
    need(digest(read(REPORT)) == report_sha, 'exact ROOT-reviewed report')
    final = load(OUT/'outer-final.json'); worker = load(OUT/'worker_result.json')
    receipt = load(PREP/'main-engineering10x84-01-owned/receipt.json')
    request_path = PREP/'main_engineering10x84_request01.ROOT.json'; request = load(request_path)
    need(digest(read(OUT/'outer-final.json')) == 'e1745fc0423fd9660218d49a51a57126ac74d40810a2f6c58c8f776bd554c127'
         and digest(read(request_path)) == 'b99e6825b2b0c03316b6e4c167c682f820432c3b01a611c2199270e848eabe60', 'actual outer/request pins')
    need(final['status'] == 'ACCEPTED_GENUINE_ENGINEERING10X84_ONLY' and final['error'] is None
         and final['worker_result'] == worker and final['owned_receipt'] == receipt
         and final['environment_restored'] is True and final['canonical60_modified'] is False
         and final['research_allocation_changed'] is False and final['research_fit'] is False
         and 0 < final['elapsed_seconds'] < 70, 'actual engineering-only acceptance')
    owned_ok(receipt)
    sources = request['collection_sources'] | request['extra_sources']
    need(len(request['collection_sources']) == 13 and len(request['extra_sources']) == 6
         and len(sources) == 19 and worker['source_before'] == worker['source_after'] == sources
         and worker['request_sha256'] == final['request_sha256'] == digest(read(request_path)), 'actual source/request bindings')
    need(worker['status'] == 'GENUINE_ENGINEERING_CORPUS_PENDING_OUTER' and worker['denied'] == []
         and worker['reserved_teacher_attempts'] == worker['interact_attempts'] == worker['interact_returns'] == 840
         and worker['role_attempts'] == dict(train=672, selection=84, calibration=84)
         and worker['final_events'] == worker['model_calls'] == worker['optimizer_calls'] == 0
         and len(worker['git_calls']) == 10 and 0 < worker['elapsed_seconds'] < 60, 'actual genuine840/native0model')
    for role, learners, targets in (('train',8,672),('selection',1,84),('calibration',1,84)):
        role_result = load(OUT/(role+'.collection.json'))
        need(role_result['interact_attempts'] == role_result['interact_returns'] == targets
             and role_result['sources_before'] == role_result['sources_after'] == request['collection_sources'], 'genuine collector role receipts')
        need(len(worker['coverage_per_learner'][role]) == learners
             and set(worker['coverage_per_learner'][role].values()) == {84}
             and worker['role_audits'][role]['reference_complete'] is True
             and worker['role_audits'][role]['audit']['learners'] == learners
             and worker['role_audits'][role]['audit']['targets'] == targets
             and len(worker['role_audits'][role]['audit']['observed_items']) == 84
             and sum(worker['class_counts'][role]) == targets, 'actual restart/population/84reference coverage')
    resources = worker['resources']
    need(resources and all(type(row['process_rss_bytes']) is int and type(row['system_available_ram_bytes']) is int
         and max(row['process_rss_bytes'], row.get('process_peak_rss_bytes') or 0) <= 512*1024**2
         and row['system_available_ram_bytes'] >= 2*1024**3 for row in resources), 'actual sampled resources')
    publication = load(OUT/'publication.json')
    need(publication == worker['publication'] and publication['status'] == 'PUBLISHED_OBSERVABLE_CORPUS_NOT_MODEL_FITTED'
         and publication['corpus_path'] == CORPUS.relative_to(ROOT).as_posix()
         and publication['corpus_sha256'] == '78da1a4fd1708bb1efca723caed4976ed518687eb70b847fbdf780f111191151'
         and publication['done_sha256'] == '9b565431267a1e0e6f6fb4c05b42a989b2d533d2de98991e64927149b1c5b710'
         and worker['public_reader_identity'] == '03d168afdde03af27f322946c3655e75324bef235543624caf3d9372e2bd2683', 'actual publication/public restart identity')
    files = publication['files']
    need(len(files) == 17 and {name for name, pin, size in files} == PUBLIC10 | ORACLE7, 'exact17canonical files')
    need({path.relative_to(CORPUS).as_posix() for path in CORPUS.rglob('*') if path.is_file()} == PUBLIC10 | ORACLE7,
         'exact canonical population, no late failure file')
    for name, pin, size in files:
        path = CORPUS/name
        need(path.stat().st_size == size, 'canonical byte size')
        reference(path, pin, 'canonical_synthetic_opaque_hash_only_no_parse_no_copy')
    prerequisites = load(OUT/'prerequisites.json')
    need(prerequisites['runtime']['runtime_report_sha256'] == request['runtime_sha256']
         and prerequisites['runtime']['runtime']['runtime_schema_version'] == 2
         and prerequisites['gate']['pointer_sha256'] == request['gate_index_sha256']
         and len(prerequisites['git_calls']) == 10, 'actual genuine prerequisite validators')
    for path_field, pin_field in (('runtime_report','runtime_sha256'),('gate_index','gate_index_sha256')):
        reference(ROOT/request[path_field], request[pin_field], 'actual_explicit_runtime_Gate_reference_only')
    gate = prerequisites['gate']
    for path_field, pin_field in (('evidence_path','report_sha256'),('test_log_path','test_log_sha256')):
        reference(Path(gate[path_field]), gate[pin_field], 'native_Gate05_no_duplicate_logs_JUnit')
    for name, pin in sources.items():
        reference(ROOT/name, pin, 'executed_collection_source_pre_post')
    pure_final = load(PURE/'result.json'); pure_worker = load(PURE/'worker-result.json')
    pure_receipt = load(PREP/'main-engineering10x84-pure01-owned/receipt.json')
    need(digest(read(PURE/'result.json')) == '3ea41b137ec9672ce7e66f184a5c0409c575e16a63303461b25e33f35ab9261b'
         and pure_final['status'] == 'ACCEPTED_9_ENGINEERING10X84_CONTRACT_METHODS_ONLY'
         and pure_final['errors'] == [] and pure_final['worker_result'] == pure_worker
         and pure_final['owned_receipt'] == pure_receipt and pure_final['environment_restored'] is True
         and pure_final['counts'] == dict(tests=9, failures=0, errors=0, skipped=0, expected_failures=0, unexpected_successes=0)
         and 0 < pure_final['elapsed_seconds'] < 30, 'actual pure9 distinct acceptance')
    owned_ok(pure_receipt)
    packet = load(PREP/'main_engineering10x84_pure01_packet.json')
    need(pure_worker['calls'] == packet['expected_calls'] and len(pure_worker['subtests']) == 21
         and len(pure_worker['executed_test_methods']) == 9 and pure_worker['methods_restored'] is True
         and pure_worker['monitor_stopped'] is True and pure_worker['errors'] == pure_worker['forbidden']
         == pure_worker['heavy_modules'] == pure_worker['resource_errors'] == []
         and pure_worker['source_after'] == packet['source_sha256'] and pure_worker['runtime_after'] == packet['runtime_sha256'],
         'actual pure9 helper counts and no scientific imports/data')
    for name, pin in pure_final['runtime_sha256'].items():
        reference(ROOT/name, pin, 'runtime_entry_hash_only_no_dependency_copy')
    profile_folder = PREP/'engineering10x84-profile-launch01'
    profile = load(profile_folder/'result.json'); reservation = load(profile_folder/'reservation.json')
    need(profile['returncode'] == 0 and profile['parent_environment_unchanged'] is True
         and reservation['excluded_display_variable_names'] == ['GH_PAGER','GIT_PAGER'], 'actual child profile/parent unchanged')
    runtime_packet = load(PREP/'runtime_schema2_main177_01_packet.json')
    need(reservation['child_git_profile'] == runtime_packet['git_environment'], 'exact actual Win03 profile')
    for name in ('stdout','stderr'):
        need(digest(read(profile_folder/(name+'.log'))) == profile[name+'_sha256'], 'profile raw streams')
    for folder, value in ((PREP/'main-engineering10x84-01-owned',receipt), (PREP/'main-engineering10x84-pure01-owned',pure_receipt)):
        for name, pin in value['output_sha256'].items():
            need(digest(read(folder/name)) == pin, 'owned raw streams exact')
    for folder in (OUT, PURE):
        need(not any((folder/name).exists() for name in ('failure.json','failure.log','resource-failure.json',
             'postwrite-rejection.json','worker-postwrite-rejection.json')), 'no late failure override')
    for folder in (OUT, PREP/'main-engineering10x84-01-owned', PURE, PREP/'main-engineering10x84-pure01-owned', profile_folder):
        flat(folder)
    for name in ('collect_main_engineering10x84_01.py','run_main_engineering10x84_01.py',
                 'test_main_engineering10x84_contract01.py','main_engineering10x84_source_freeze01.json',
                 'check_main_engineering10x84_pure01.py','main_engineering10x84_pure01_packet.json',
                 'prepare_main_engineering10x84_request01.py','launch_engineering10x84_profile01.py',
                 'MAIN_ENGINEERING10X84_SOURCE_CONTRACT01.md','MAIN_ENGINEERING10X84_STATIC_REVIEW01.md',
                 'MAIN_ENGINEERING10X84_PURE_HANDOFF01.md','ROOT_ENGINEERING10X84_PURE_REVIEW01.md',
                 'ROOT_ENGINEERING10X84_COLLECTION_REVIEW01.md'):
        read(PREP/name)
    read(Path(__file__).resolve())
    summary = dict(kind='GENUINE_ENGINEERING10X84_COLLECT_PUBLISH_RESTART_NOT_FIT',
        pure=dict(tests=9, subtests=21, calls=pure_worker['calls'], outer_seconds=pure_final['elapsed_seconds']),
        native=dict(attempts=840, returns=840, roles=worker['role_attempts'], final_events=0, model_calls=0, optimizer_calls=0,
                    outer_seconds=final['elapsed_seconds'], worker_seconds=worker['elapsed_seconds'],
                    profile_seconds=profile['elapsed_seconds'], samples=len(resources),
                    peak_observed_bytes=max(max(row['process_rss_bytes'],row.get('process_peak_rss_bytes') or 0) for row in resources),
                    minimum_available_ram_bytes=min(row['system_available_ram_bytes'] for row in resources)),
        corpus=dict(id=publication['corpus_id'], sha256=publication['corpus_sha256'], done_sha256=publication['done_sha256'],
                    files=17, bytes=sum(row[2] for row in files), opaque_hash_only=True, parsed_oracle=False, copied_corpus=False),
        class_counts=worker['class_counts'], public_reader_identity=worker['public_reader_identity'], research_fit=False,
        limits_vi='EngineeringallPG/cyclic84 only; canonical60/allresearchcandidates/selectedfit/refit/calibration remain separate.')
    return payloads, references, summary


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare-dry', action='store_true'); mode.add_argument('--close', action='store_true')
    parser.add_argument('--report-sha256', required=True); parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--inventory-sha256'); parser.add_argument('--review-reference')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT/'.venv', 'repository .venv only')
    need(args.inventory.is_absolute() and args.inventory.parent == PREP and '..' not in args.inventory.parts
         and not args.inventory.is_symlink() and not args.inventory.is_junction(), 'fixed prep inventory path')
    payloads, references, summary = gather(args.report_sha256)
    inputs = [dict(source=path.relative_to(ROOT).as_posix(),bytes=len(raw),sha256_before_copy=digest(raw))
              for path, raw in sorted(payloads.items())]
    inventory = dict(run_id=RUN_ID,inputs=inputs,references=references,summary=summary,input_occurrences=len(inputs),
                     unique_copies=len({row['sha256_before_copy'] for row in inputs}),total_copy_bytes=sum(map(len,payloads.values())))
    if args.prepare_dry:
        write(args.inventory,inventory)
        print(json.dumps(dict(status='DRY_INVENTORY_READY',sha256=sha(args.inventory),inputs=len(inputs),unique_copies=inventory['unique_copies']))); return
    need(args.review_reference and args.inventory_sha256 and sha(args.inventory) == args.inventory_sha256
         and json.loads(args.inventory.read_bytes()) == inventory, 'exact ROOT-reviewed closure inventory')
    destination = ROOT/'research_tracking/runs'/RUN_ID
    need(not destination.exists(), 'exclusive immutable bundle')
    for row in inputs:
        need(sha(ROOT/row['source']) == row['sha256_before_copy'], 'source SHA before copy')
    sys.path.insert(0,str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    note = '''# Corpus engineering10×84 actual ngày09/11/2026

Pure9/21subtests và actual840teacher calls là hai allocations tách biệt.
Actualcollect→publish→publicreader accepted, Job0, nguồn trước/sau ổn định.
AllPG/cyclic84/seed42 là fixture riêng, không thay canonical60 hoặc nghiên cứu chính.
17canonical files chỉ được mở opaque để hash/size, không parse oracle/copycorpus.
Rawpublication/reader audits/ownedlogs và nguồn/request/reviews giữ exactbytes.
copy_inventory.json ghi SHA trước/sau với aliases dedup, references.json giữ corpus/runtime/Gate/deps.
Không selectedfit/checkpoint/refit/calibration/CUDA/cloud hoặc efficacy proof ở đây.
'''
    with record_evidence_run(ROOT,RUN_ID,metadata=dict(kind=summary['kind'],closure_review=args.review_reference),
            sources=sorted(set(payloads) | {ROOT/name for name in references}),note=note) as out:
        copies = {}
        for row in inputs:
            source = ROOT/row['source']; raw = payloads[source]; pin = row['sha256_before_copy']
            if pin not in copies:
                target = out/f'input-{len(copies):03d}__{source.name}'
                with target.open('xb') as stream:
                    stream.write(raw)
                copies[pin] = target
            target = copies[pin]
            need(target.read_bytes() == raw and sha(source) == pin, 'copy readback/source posthash')
            row.update(copy=target.name,sha256_after_copy=sha(target),source_sha256_after_copy=pin)
        write(out/'copy_inventory.json',inputs); write(out/'references.json',references)
        write(out/'validated_summary.json',summary)
        write(out/'closure_review.json',dict(reference=args.review_reference,inventory_sha256=args.inventory_sha256))
    verification = verify_evidence_bundle(destination)
    for row in inputs:
        need(sha(ROOT/row['source']) == row['sha256_before_copy'], 'final source byte integrity')
    force = PREP/'main_engineering10x84_force_paths01.txt'
    with force.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write('\n'.join(path.relative_to(ROOT).as_posix() for path in sorted(destination.iterdir()))+'\n')
    print(json.dumps(dict(status='CLOSED_BY_ROOT_METADATA_EXECUTION',verification=verification,
        manifest_sha256=sha(destination/'manifest.json'),files_including_manifest=len(list(destination.iterdir())),force_paths=str(force))))


if __name__ == '__main__':
    main()
