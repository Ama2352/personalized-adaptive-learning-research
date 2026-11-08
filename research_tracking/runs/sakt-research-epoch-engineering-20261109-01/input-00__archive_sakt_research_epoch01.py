"""ROOT đóng archive SAKT09/11 từ receipts có sẵn; không chạy lại test/model."""
from pathlib import Path
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RUN_ID = 'sakt-research-epoch-engineering-20261109-01'
PINS = {
    'check_sakt_research_epoch01.py': '95cbfdde0a0d7e93e8e829fa1b7779aa867d2df7e6ef2e137843552e81816832',
    'run_sakt_research_epoch01.py': '1c5cfb871060a94c1c34e550e85309dded018167d887374dd36dc82869519282',
    'sakt_research_epoch01_allocation.json': '1c7a9962dd75cbb4f6e0bde7fd24278cd3d5588cc5b503f7ee345c44287bd9f5',
    'check_sakt_research_epoch02.py': 'f8ec38aa3149e420f7725a3e27289bbe37a77b4ef6b49e3bb47b3c8b12b03630',
    'run_sakt_research_epoch02.py': 'ce5e33253055d1fe52181455299ff8b2cf7be82316df8343d238f5cea1854c1f',
    'sakt_research_epoch02_allocation.json': '6d0824232bd4d3d41f393e5bff8457456a4c77bb0d9221a0edb955a10716fef1',
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe(path):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts and path.is_relative_to(ROOT), 'fixed ROOT input')
    cursor = ROOT
    for part in (None, *path.relative_to(ROOT).parts):
        if part is not None:
            cursor /= part
        need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'aliased archive input')
    need(path.is_file() and path.suffix in ('.py','.json','.jsonl','.xml','.log','.txt','.md'), 'regular small evidence input')
    return path


def write_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    payloads = {}

    def read(path):
        path = safe(path)
        if path not in payloads:
            raw = path.read_bytes()
            need(len(raw) <= 2*1024**2, 'per-input2MiB cap')
            payloads[path] = raw
            need(sum(map(len, payloads.values())) <= 10*1024**2, 'total10MiB cap')
        return payloads[path]

    def load(path):
        return json.loads(read(path))

    for name, digest in PINS.items():
        need(sha(read(PREP/name)) == digest, 'dispatched controller/allocation drift: '+name)
    allocations = [load(PREP/f'sakt_research_epoch0{i}_allocation.json') for i in (1, 2)]
    need(allocations[0]['source_pins'] == allocations[1]['source_pins']
         and len(allocations[1]['source_pins']) == 27, 'same27source population')
    sources = allocations[1]['source_pins']
    for name, digest in sources.items():
        need(sha(read(ROOT/name)) == digest, 'current accepted source drift: '+name)
    need(sources['src/knowledge_tracing/sakt/research_training.py'] == '3c9b785685fc17739d1ae4ddc98f52597a70e7c3f2ef1cfb4d06433153968af5'
         and sources['tests/sakt/test_research_training.py'] == 'f6dc9264d397c2d39249aaa0a6a8207cb3d8d76a54edfdcac17189a27941584d', 'final production/test pins')
    for allocation in allocations:
        need(all(not (ROOT/name).exists() for name in allocation['absent_source_paths']), 'namespace absence changed')
    stages = []
    testcase_sets = []
    for index, failures in ((1, 3), (2, 0)):
        label = f'sakt-research-epoch0{index}'
        child = load(PREP/label/'result.json')
        owned = load(PREP/(label+'-owned')/'receipt.json')
        final = load(PREP/(label+'-owned')/'final.json')
        tree = ET.fromstring(read(PREP/label/'junit.xml'))
        cases = list(tree.iter('testcase'))
        counts = {key: sum(int(s.get(key, '0')) for s in tree.iter('testsuite'))
                  for key in ('tests','failures','errors','skipped')}
        need(counts == dict(tests=22, failures=failures, errors=0, skipped=0) and len(cases) == 22
             and counts == child['counts'] == final['counts'], 'actual22case XML/receipt agreement')
        testcase_sets.append(sorted((case.get('classname'), case.get('name')) for case in cases))
        need(child['source_before'] == child['source_after'] == sources and child['source_unchanged'] is True
             and child['methods_restored'] is True and child['runtime_restored'] is True
             and child['environment_restored'] is True and child['monitor_stopped'] is True
             and child['monitor_errors'] == [] and child['forbidden_attempts'] == [], 'source/restoration/access guards')
        need(owned['cleanup_accepted'] is True and owned['job_active_after_cleanup'] == 0
             and owned['popen_handle_closed'] is True and owned['cleanup_errors'] == []
             and owned['actual_worker_in_job_before_GO'] is True, 'owned Job cleanup/membership')
        need(owned['worker_sha256'] == PINS[f'check_sakt_research_epoch0{index}.py'], 'actual executed worker pin')
        need(final['cap_seconds'] == 80 and 0 < final['elapsed_seconds'] < 80
             and child['child_timer_seconds'] == 70 and 0 < child['elapsed_seconds'] < 70, 'actual budgets')
        need(not any((PREP/label/name).exists() for name in ('resource-failure.json','postwrite_rejection.json'))
             and not (PREP/(label+'-owned')/'postwrite_rejection.json').exists(), 'late/resource rejection')
        resources = child['resources']
        need(0 < resources['observed_peak_rss_bytes'] <= 512*1024**2
             and resources['observed_minimum_available_ram_bytes'] >= 1024**3
             and resources['pre_torch_available_ram_bytes'] >= 1024**3 and resources['samples'] > 0, 'observed resources')
        need(child['torch_profile']['version'] == '2.7.1+cpu'
             and child['torch_profile']['cuda_build'] is None
             and child['torch_profile']['cuda_initialized_after'] is False
             and child['native_os_metadata']['phase_closed'] is True, 'actual CPU/native metadata')
        if index == 1:
            need(final['status'] == 'REJECTED_SAKT_RESEARCH_EPOCH_CHECK' and child['pytest_exit_code'] == 1
                 and child['native_started']['backwards'] == 8 and child['native_body_returned']['backwards'] == 4
                 and child['native_body_returned']['sgd_steps'] == 2, 'preserve rejected01 observation')
            log = read(PREP/label/'pytest.log').decode('utf-8')
            need('native reservation exceeded: backwards' in log and 'handle_torch_function' in log
                 and '__torch_function__' in log, 'actual dispatcher traceback evidence')
        else:
            need(final['status'] == 'ACCEPTED_SAKT_RESEARCH_EPOCH_ENGINEERING_ONLY'
                 and child['pytest_exit_code'] == 0 and owned['accepted'] is True and owned['returncode'] == 0
                 and child['native_started'] == child['native_body_returned'] == allocations[1]['expected_native_counts'], 'accepted02 exact native inventory')
            journal = [json.loads(line) for line in read(PREP/label/'case_events.jsonl').splitlines()]
            need(journal and journal[-1]['native_body_returned'] == child['native_body_returned'], 'per-case actual counter journal')
        failed_names = [case.get('name') for case in cases if list(case.iter('failure'))]
        stages.append(dict(label=label, status=final['status'], counts=counts, failed_cases=failed_names,
            stored_outer_elapsed_seconds=final['elapsed_seconds'], child_elapsed_seconds=child['elapsed_seconds'],
            pytest_seconds=float(next(tree.iter('testsuite')).get('time')), cap_seconds=80,
            native_started=child['native_started'], native_body_returned=child['native_body_returned'],
            resources=resources, owned_cleanup_accepted=owned['cleanup_accepted'],
            result_sha256=sha(read(PREP/label/'result.json')), junit_sha256=sha(read(PREP/label/'junit.xml'))))
        for name in ('case_events.jsonl','junit.xml','pytest.log','reservation.json','result.json'):
            read(PREP/label/name)
        for name in ('final.json','GO.json','launch.json','ready.json','receipt.json','stderr.log','stdout.log'):
            read(PREP/(label+'-owned')/name)
    need(testcase_sets[0] == testcase_sets[1], 'same22test identities across attempts')
    for index in (1, 2):
        review = load(PREP/f'sakt_research_epoch0{index}_root_review.json')
        for name, digest in review['controller_pins'].items():
            need(sha(read(PREP/name)) == digest, 'ROOT-reviewed dispatched source')
    need(load(PREP/'sakt_research_epoch02_root_review.json')['production_and_test_sources_unchanged'] is True, 'ROOT new-hypothesis review')
    before = PREP/'pre-sakt-objective-population-review01'
    inventory = load(before/'inventory.json')
    for entry in inventory['files']:
        path = ROOT/entry['snapshot']
        need(sha(read(path)) == entry['sha256_before_copy'] == entry['sha256_after_copy'], 'before finite/population static-fix snapshot')
    prior = PREP/'pre-sakt-backward-dispatch02'
    inventory = load(prior/'inventory.json')
    for entry in inventory['snapshots']:
        need(sha(read(prior/entry['snapshot'])) == entry['sha256_before_copy'] == entry['sha256_after_copy'], 'pre-dispatch02 snapshot')
    for entry in inventory['raw_trial01_inventory']:
        need(sha(read(ROOT/entry['source'])) == entry['sha256'], 'raw01 changed since observer diagnosis')
    for name in ('docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md',
                 'docs/thesis_recovery/EXPERIMENT_ALLOCATION_V1.json'):
        read(ROOT/name)
    read(Path(__file__))
    inputs = [dict(source=path.relative_to(ROOT).as_posix(), bytes=len(raw), sha256_before_copy=sha(raw))
              for path, raw in sorted(payloads.items())]
    for item in inputs:
        need(sha(safe(ROOT/item['source']).read_bytes()) == item['sha256_before_copy'], 'source drift before archive creation')
    a, b = stages
    note = f'''# SAKT research epoch/prediction — engineering09/11/2026

Đóng bằng chứng hai lượt Windows CPU trên cùng22case IDs:01 **19PASS/3FAIL**, verdict REJECTED;02 **22PASS/0failure/error/skip**, verdict ACCEPTED engineering. Không đổi assertion/production/test giữa01 và02. Folder làm việc20261108 giữ tên lịch sử dù bundle đóng09/11. Không chạy lại tests/model khi archive.

## Source và phạm vi

Hai module mới cung cấp một optimizer epoch và raw prediction trên SAKTResearchView đã kiểm roles. Config/model/optimizer/budget do caller truyền rõ, không numerical scientific defaults. Labels chỉ vào loss/truth sidecar; selection/calibration không được optimize. Có exact observable key/query/role population, truth join sau forwards, terminal masks/local positions, causal/peer positive controls, mode/RNG restoration, ownership/identity guards và complete/partial/failed ledgers. Finite logits nhưng BCEsum overflow phải fail trước backward/step; source trước static finite/population review được giữ, chưa có testRED của bản đó.

Reuse dữ liệu roles và math helpers; không gọi trainer toy hoặc sửa256targets/32steps/engineering checkpoint guards. Tests dùng typed observables tự dựng in-memory, không đọc canonical corpus/oracle/final/Holdout hoặc gọi teacher. Metadata/source seals là cooperative consistency, không độc lập xác nhận actual data origin. Partial iterator/budget không thành complete epoch; failure sau optimizer mutation không được gọi rollback.

## Vì sao giữ failure01?

01 đặt observer trên Tensor.backward và nhầm dispatch entries với logical backward. Trong explicit torch.device(cpu), Torch_tensor.py638–649 đi qua handle_torch_function/__torch_function__ rồi tái nhập patchedTensor.backward. Cap5observer chặn backward tiếp theo: raw started8/bodyreturned4, SGD bodies2. Ba failures là actual và giữ nguyên log/XML/ROOT review; không gọi chúng là production model bug hoặc relabelPASS. Raw key backwards ở01 không thể cộng như logical calls của02.

02 dùng public torch.autograd.backward để đếm **5logical backwards**; observer Tensor.backward riêng ghi **10raw dispatch entries**. Actual inventory02:16SAKT constructors,11forwards,5logical backwards,10raw entries,5SGD bodies và15SGD constructors; cả started/bodyreturned khớp. Một fixture cố ý để instance step wrapper raise sau underlying SGD body đã đổi weights, nhằm chứng minh failed/possibly-updated ledger; vì thế5internal SGD body returns không phủ nhận failure-wrapper test. Cộng hai lượt là7SGD bodies toy, không7research fits. Journal02 ghi counters theo test; không nới logical5/step5 và không auto retry.

## Runtime và budget đã quan sát

Stored outer receipts:01 {a['stored_outer_elapsed_seconds']:.9f}s/80;02 {b['stored_outer_elapsed_seconds']:.9f}s/80; mỗi allocation độc lập80s, tổng ceiling160s. Đây là boundaries trong final.json; không thay bằng thời gian terminal/GUI hoặc pytest. Pytest XML lần lượt {a['pytest_seconds']:.3f}s và {b['pytest_seconds']:.3f}s. Child timer70s; owned ceiling77s, cleanup3s, finalization reserve3s từ original outer clock, không reset sau setup.

Monitor vòngwait0,1s và Windows peak working-set/RSS observations:01 peak{a['resources']['observed_peak_rss_bytes']}B/minimum free{a['resources']['observed_minimum_available_ram_bytes']}B/{a['resources']['samples']}samples;02 peak{b['resources']['observed_peak_rss_bytes']}B/minimum free{b['resources']['observed_minimum_available_ram_bytes']}B/{b['resources']['samples']}samples. Admission free1GiB, observed peak cap512MiB; cooperative polling/late rejection không là hard OS RAM quota. FullGate floor4GiB giữ nguyên.

Actual .venv CPython3.13.5, Torch2.7.1+cpu/NumPy2.5.4; origins/prefix trong raw receipts. Intra-op2; interop12 ghi nhận, không claim toàn process chỉ2threads. Actual platform.uname bootstrap chạy đúng fixed systemcmd /c "ver" trong ownedJob, phase đóng trước test processes deny; không fake OS/cache. Hai lượt đều mode/method/env restored, monitor stopped, Jobactive0/cleanupaccepted/Popen handleclosed. 0CUDA initialization/execution; đây không phải toàn bộ dependency syscall attestation.

## Còn thiếu trước required baseline

Đây là computational primitive được kiểm trên toy fixtures, **không actual research corpus fit, selected-epoch lifecycle, fresh refit90 certificate, persisted/reloaded research checkpoint, public resume hoặc fitted OnlineSession**. Chưa Junyi research training/CUDA/fullGate/benchmark/calibration efficacy/RQ completion. Protocol21/allocation adopted không tự chọn dimension/lr/epochs hoặc cấp run authority. Các bước chọn epoch, system selector, refit, calibration và OnlineSession vẫn cần wiring/identity/actual receipts đúng scope; không nâng engineering weights thành fitted bằng cờ caller.

copy_inventory.json chứa SHA trước/sau và aliases byte-identical; raw outputs/ROOT reviews/allocations/controller sources giữ nguyên. counter_diagnosis.json phân biệt đơn vị; validated_summary.json chỉ tổng hợp receipts. execution.log là archive closure, không một native run mới. Không binaries/checkpoints/caches/real corpus/private RPC.
'''
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    with record_evidence_run(ROOT, RUN_ID, sources=list(sorted(payloads)), note=note,
            metadata=dict(kind='SAKT_RESEARCH_EPOCH_TOY_ENGINEERING_TWO_ATTEMPTS', stages=stages,
                distinct_testcases=22, accepted_attempt='02', actual_sgd_bodies_both_attempts=7,
                actual_research_fit=False, checkpoint_resume=False, fitted_online_session=False)) as out:
        copies = {}
        for item in inputs:
            path = ROOT/item['source']
            raw = payloads[path]
            digest = item['sha256_before_copy']
            if digest not in copies:
                copy = out/f'input-{len(copies):02d}__{path.name}'
                with copy.open('xb') as stream:
                    stream.write(raw)
                copies[digest] = copy
            copy = copies[digest]
            need(copy.read_bytes() == raw and sha(safe(path).read_bytes()) == digest, 'exact source/copy bytes after copy')
            item.update(copy=copy.name, sha256_after_copy=sha(copy.read_bytes()), source_sha256_after_copy=digest)
        write_json(out/'copy_inventory.json', inputs)
        write_json(out/'counter_diagnosis.json', dict(status='OBSERVER_CORRECTION_NOT_PRODUCTION_OR_TEST_CHANGE',
            failed01=stages[0], accepted02=stages[1],
            raw01_backward_field_is_logical=False, logical_backward01_directly_measured=False,
            logical_api02='torch.autograd.backward', raw_dispatch_api02='torch.Tensor.backward',
            preserved_source_and_test_sha256={name: sources[name] for name in (
                'src/knowledge_tracing/sakt/research_training.py','tests/sakt/test_research_training.py')},
            note_vi='01raw Tensor observer cap5 là lỗi instrumentation. 02logical cap5 không tăng; raw10 tách đơn vị. Không sửa oldverdict/raw files.'))
        write_json(out/'validated_summary.json', dict(kind='EXISTING_RECEIPTS_ONLY_NO_RERUN', stages=stages,
            source_files_verified=27, distinct_testcase_population=22, input_path_occurrences=len(inputs),
            unique_byte_copies=len(copies), actual_research_fit=False, actual_teacher_calls=0,
            research_checkpoint_or_resume=False, fitted_online_session=False,
            limit_vi='SHA/receipt validation không chứng nhận efficacy, fullGate hoặc independent source attestation.'))
    directory = ROOT/'research_tracking/runs'/RUN_ID
    verified = verify_evidence_bundle(directory)
    for item in inputs:
        need(sha(safe(ROOT/item['source']).read_bytes()) == item['sha256_before_copy'], 'source changed after closure')
    force_list = PREP/'sakt_research_epoch_archive_force_paths01.txt'
    with force_list.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write('\n'.join(path.relative_to(ROOT).as_posix() for path in sorted(directory.iterdir()))+'\n')
    print(json.dumps(dict(run_id=RUN_ID, verification=verified,
        manifest_sha256=sha((directory/'manifest.json').read_bytes()),
        files_including_manifest=len(list(directory.iterdir())), force_paths=force_list.relative_to(ROOT).as_posix()), ensure_ascii=False))


if __name__ == '__main__':
    main()
