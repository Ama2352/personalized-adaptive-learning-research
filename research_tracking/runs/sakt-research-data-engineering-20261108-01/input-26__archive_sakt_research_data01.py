"""ROOT đóng evidence SAKT đã chạy; không test/import model/đọc corpus lại."""
from pathlib import Path
import hashlib
import json
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUNNER = ROOT / 'artifacts/akt/local-tests/akt-research-runner-20261108-01'
RUN_ID = 'sakt-research-data-engineering-20261108-01'
FINAL_PINS = {
    'src/knowledge_tracing/sakt/__init__.py': '6b17674fb5d383be2823cfce897e447a523114d4c45a87d0c10291af7278ef0e',
    'src/knowledge_tracing/sakt/research_data.py': 'da64bc5bc4abb380c8d57fff4632afff0e88820c5533beeb2799089538b8c574',
    'tests/sakt/test_research_data.py': '005b531d7bc163329e4c8939bd787b046146a48691e9d0dbee58b0ee4933ccc7',
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and path.is_relative_to(ROOT), 'outside fixed ROOT')
    cursor = ROOT
    for part in (None, *path.relative_to(ROOT).parts):
        if part is not None:
            cursor /= part
        require(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'aliased input')
    require(path.is_file(), 'missing/nonregular input: ' + str(path))
    require(path.suffix in ('.py', '.json', '.xml', '.log', '.md'), 'unapproved archive input suffix')
    return path


def write_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    # Read/hash each selected input once; parse and copy this same immutable payload.
    payloads = {}

    def read(path):
        path = safe(path)
        if path not in payloads:
            raw = path.read_bytes()
            require(len(raw) <= 2*1024**2, 'per-input cap')
            payloads[path] = raw
            require(sum(map(len, payloads.values())) <= 10*1024**2, 'whole archive-input cap')
        return payloads[path]

    def load(path):
        return json.loads(read(path))

    stages = []
    for label, expected, cap, status, peak_cap in (
            ('sakt_research_data01', 20, 60, 'ACCEPTED_SAKT_DATA_FIXTURE_ONLY', 512*1024**2),
            ('sakt_lazy_exports01', 3, 30, 'ACCEPTED_SAKT_NATIVE_EXPORT_FIXTURE_ONLY', 1024**3)):
        child = load(RUNNER / label / 'result.json')
        owned = load(RUNNER / (label+'-owned') / 'receipt.json')
        final = load(RUNNER / (label+'-owned') / 'final.json')
        tree = ET.fromstring(read(RUNNER / label / 'junit.xml'))
        cases = list(tree.iter('testcase'))
        counts = {key: sum(int(s.get(key, '0')) for s in tree.iter('testsuite'))
                  for key in ('tests', 'failures', 'errors', 'skipped')}
        require(counts == dict(tests=expected, failures=0, errors=0, skipped=0)
                and len(cases) == expected and not any(list(tree.iter(key)) for key in ('failure', 'error', 'skipped')), 'exact JUnit counts')
        require(final['status'] == status and final['counts'] == counts
                and final['cap_seconds'] == cap and 0 < final['elapsed_seconds'] < cap, 'outer acceptance/budget')
        require(not (RUNNER/(label+'-owned')/'postwrite_rejection.json').exists(), 'postwrite rejection exists')
        require(child['pytest_exit_code'] == 0 and child['source_unchanged'] is True
                and child['source_before'] == child['source_after']
                and child['environment_restored'] is True
                and child['actual_subprocess_attempts'] == child['heavy_modules_loaded'] == [], 'child guards')
        require(child['available_ram_start'] >= 1024**3 and child['available_ram_end'] >= 1024**3
                and 0 < child['process_peak_rss_bytes'] <= peak_cap, 'observed resource bounds')
        require(owned['accepted'] is True and owned['cleanup_accepted'] is True
                and owned['actual_worker_in_job_before_GO'] is True
                and owned['job_active_after_cleanup'] == 0 and owned['popen_handle_closed'] is True
                and owned['cleanup_errors'] == [] and owned['returncode'] == 0, 'owned cleanup/exit')
        controller = RUNNER / ('check_'+label+'.py')
        require(owned['worker_sha256'] == sha(read(controller)), 'executed child source binding')
        for name, digest in child['source_before'].items():
            require(sha(read(ROOT/name)) == digest, 'current source differs from actual trial: '+name)
        if label == 'sakt_research_data01':
            require(child['model_calls'] == child['solver_fits'] == 0, 'data-only scope')
        else:
            require(child['native_counts'] == dict(constructors=2, forwards=8)
                    and final['model_calls'] == child['native_counts']
                    and child['model_calls'] == 0 and final['optimizer_steps'] == 0
                    and child['solver_fits'] == 0 and child['cuda_initialized'] is False
                    and child['torch_version'] == '2.7.1+cpu', 'lazy native proof/known erratum')
        stages.append(dict(label=label, counts=counts, outer_elapsed_seconds=final['elapsed_seconds'],
            cap_seconds=cap, child_elapsed_seconds=child['elapsed_seconds'],
            observed_peak_rss_bytes=child['process_peak_rss_bytes'],
            available_ram_start=child['available_ram_start'], available_ram_end=child['available_ram_end'],
            owned_cleanup_accepted=owned['cleanup_accepted'], result_sha256=sha(read(RUNNER/label/'result.json'))))

    for name, digest in FINAL_PINS.items():
        require(sha(read(ROOT/name)) == digest, 'final accepted source pin')
    controllers = ('check_sakt_research_data01.py', 'run_sakt_research_data01.py',
                   'check_sakt_lazy_exports01.py', 'run_sakt_lazy_exports01.py')
    for name in controllers:
        read(RUNNER/name)
    for label in ('sakt_research_data01', 'sakt_lazy_exports01'):
        for name in ('before.json', 'junit.xml', 'pytest.log', 'result.json'):
            read(RUNNER/label/name)
        for name in ('final.json', 'GO.json', 'launch.json', 'ready.json', 'receipt.json', 'stderr.log', 'stdout.log'):
            read(RUNNER/(label+'-owned')/name)
    for name in ('initializer-before-inventory.json', 'sakt_init.before.py', 'frozen-handoff01.json',
                 'phase-isolation-fix01-handoff.json', 'pre-phase-isolation-fix01/inventory.json',
                 'pre-phase-isolation-fix01/sakt_init.py', 'pre-phase-isolation-fix01/research_data.py',
                 'pre-phase-isolation-fix01/test_research_data.py'):
        read(PREP/name)
    for name in ('docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md',
                 'docs/thesis_recovery/EXPERIMENT_ALLOCATION_V1.json'):
        read(ROOT/name)
    read(Path(__file__))
    inventory = [dict(source=path.relative_to(ROOT).as_posix(), bytes=len(raw), sha256_before_copy=sha(raw))
                 for path, raw in sorted(payloads.items())]
    # Fail before creating a run if any cached source/receipt drifted during inspection.
    for item in inventory:
        require(sha(safe(ROOT/item['source']).read_bytes()) == item['sha256_before_copy'], 'precopy source drift')

    data_stage, lazy_stage = stages
    note = f'''# SAKT research data và lazy public exports — engineering

Hai lượt kiểm actual Windows CPU độc lập: **20 data fixtures PASS** và **3 native export/math fixtures PASS**, không failure/error/skip. Không full SAKT suite hoặc full software Gate.

Data stage: outer {data_stage['outer_elapsed_seconds']:.9f}s/cap60s; child {data_stage['child_elapsed_seconds']:.9f}s. Import đúng package public, NumPy được phép, Torch bị chặn;0model/solver/corpus thật. Scope gồm bốn roles/phases, optimization-only vocabulary, freeze/refit lineage, full-target OOV/cold accounting, masks/local positions, label-prefix/peer isolation và read-only arrays.

Lazy exports stage: outer {lazy_stage['outer_elapsed_seconds']:.9f}s/cap30s; child {lazy_stage['child_elapsed_seconds']:.9f}s. Actual Torch2.7.1+cpu, **2 tiny constructors/8 forwards**,0optimizer/solver, CUDA chưa initialized. So public exports với class/function thật và chạy ba phép kiểm core hiện có. Không thể mô tả cả bundle là0model calls; xem ERRATUM.json. Child heavy_modules_loaded=[] ở stage này chỉ kiểm danh sách trainer/AKT model cụ thể, không nói Torch vắng mặt.

Docstring lịch sử của run_sakt_lazy_exports01.py còn nói45giây/không model; code và actual receipts mới là authority: outer30s, owned27s,2constructors/8forwards. Giữ nguyên controller/raw receipt; erratum bổ sung giải thích, không thay lịch sử hoặc verdict.

Observed peak RSS lần lượt {data_stage['observed_peak_rss_bytes']}B và {lazy_stage['observed_peak_rss_bytes']}B; RAM available đầu/cuối ghi trong validated_summary.json. Đây là Windows peak/snapshot, không continuous RAM monitor hoặc hard OS quota. Hai owned Job receipts đều xác nhận membership trướcGO, cleanupaccepted, active0 và Popen handleclosed. Allocations60/30s tách biệt; không suy9,33s là thời gian train hoặc throughput.

View nhận corpus qua InitVar, sau kiểm tra chỉ giữ SHA provenance/read limits và shards của phase đã chọn; TRAIN view không giữ selection/calibration labels. Initial initializer và bản WIP còn giữ full corpus được snapshot trước static fix; chúng chưa được chạy test, không dựng RED giả. Hand-off19/20cases chỉ là kế hoạch tại thời điểm viết; XML actual mới quyết định counts. Both first-target policies query_only/unsupported và padding vẫn explicit; không tuyên bố protocol21 bắt buộc một cold policy.

Không sửa old toy caps/engineering checkpoint roles/fitted validators. Chưa research trainer selection→refit→calibration, selected-fit checkpoint/OnlineSession, Junyi adapter, CUDA, actual corpus fit, scientific efficacy hoặc RQ completion. SHA/seals kiểm consistency hợp tác; không source-origin/disk-byte attestation độc lập. Iterator dừng sớm không phải full-population acceptance.

Raw logs/JSON/XML được giữ byte-exact; copy_inventory.json gắn đường dẫn gốc và SHA trước/sau. execution.log chỉ là lần đóng gói, không phải phép chạy test mới. Existing owned helper xem ../windows-owned-worker-engineering-20261108-01/README.md; bundle này không chạy lại helper/test/model.
'''
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    with record_evidence_run(ROOT, RUN_ID,
            metadata=dict(kind='SAKT_ROLE_AWARE_DATA_AND_LAZY_EXPORT_ENGINEERING', actual_stages=stages,
                data_fixture_tests=20, lazy_native_tests=3, native_model_constructors=2, native_forwards=8,
                optimizer_steps=0, actual_corpus_reads=0, selected_fit=False, online_session_ready=False),
            sources=list(sorted(payloads)), note=note) as out:
        for index, item in enumerate(inventory):
            path = ROOT/item['source']
            raw = payloads[path]
            copy = out / f'input-{index:02d}__{path.name}'
            with copy.open('xb') as stream:
                stream.write(raw)
            after = sha(copy.read_bytes())
            require(after == item['sha256_before_copy'] == sha(safe(path).read_bytes()), 'postcopy SHA mismatch')
            item.update(copy=copy.name, sha256_after_copy=after, source_sha256_after_copy=after)
        write_json(out/'copy_inventory.json', inventory)
        write_json(out/'ERRATUM.json', dict(
            status='RAW_RECEIPT_PRESERVED_FIELD_INTERPRETATION_CORRECTED',
            affected_source='artifacts/akt/local-tests/akt-research-runner-20261108-01/sakt_lazy_exports01/result.json',
            affected_source_sha256=lazy_stage['result_sha256'], field='model_calls', raw_value=0,
            authoritative_native_counts=dict(constructors=2, forwards=8), optimizer_steps=0,
            authority='native_counts in raw child plus outer final.model_calls; raw controller instruments both methods',
            historical_outer_docstring=dict(
                source='artifacts/akt/local-tests/akt-research-runner-20261108-01/run_sakt_lazy_exports01.py',
                source_sha256=sha(read(RUNNER/'run_sakt_lazy_exports01.py')),
                misleading_text='bound45giây; không train/model', actual_outer_cap_seconds=30,
                actual_owned_cap_seconds=load(RUNNER/'sakt_lazy_exports01-owned/receipt.json')['max_seconds'],
                correction_vi='Docstring copy-paste lỗi thời; executed code+actual receipts ghi outer30/owned27 và2constructors/8forwards,0optimizer.'),
            correction_vi='model_calls=0 là metadata hardcoded sai ở child lazy check, không0native inference. Giữ nguyên raw; dùng2constructors/8forwards. Data stage riêng vẫn0model. Không thay numerical assertions/verdict hoặc rerun.'))
        write_json(out/'validated_summary.json', dict(status='ARCHIVE_OF_EXISTING_ACCEPTED_ENGINEERING_CHECKS',
            stages=stages, final_source_pins=FINAL_PINS, inputs=len(inventory),
            native_counts=dict(constructors=2, forwards=8), optimizer_steps=0,
            limitation_vi='Không nghiên cứu fitted/OnlineSession/fullGate/CUDA; nguồn và fixtures tự dựng, không corpus thật.'))
    directory = ROOT/'research_tracking/runs'/RUN_ID
    verified = verify_evidence_bundle(directory)
    for item in inventory:
        require(sha(safe(ROOT/item['source']).read_bytes()) == item['sha256_before_copy'], 'source drift after closure')
    force_list = PREP/'force-add-paths01.txt'
    with force_list.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write('\n'.join(path.relative_to(ROOT).as_posix() for path in sorted(directory.iterdir()))+'\n')
    print(json.dumps(dict(bundle=directory.relative_to(ROOT).as_posix(), verification=verified,
        manifest_sha256=sha((directory/'manifest.json').read_bytes()),
        files_including_manifest=len(list(directory.iterdir())),
        force_add_list=force_list.relative_to(ROOT).as_posix()), ensure_ascii=False))


if __name__ == '__main__':
    main()
