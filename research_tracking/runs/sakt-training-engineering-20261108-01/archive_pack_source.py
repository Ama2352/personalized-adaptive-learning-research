"""Đóng SAKT trainer evidence đã freeze; stdlib/hash-only, không model/tests rerun."""

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import unquote
import xml.etree.ElementTree as ET

from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle

ROOT = Path(__file__).resolve().parents[4]
LOCAL = ROOT / 'artifacts/akt/local-tests'
RUN_ID = 'sakt-training-engineering-20261108-01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def xml_counts(path):
    root = ET.parse(path).getroot()
    suites = list(root) if root.tag == 'testsuites' else [root]
    return {**{name: sum(int(s.attrib.get(name, 0)) for s in suites)
               for name in ('tests', 'failures', 'errors', 'skipped')},
            'junit_seconds': sum(float(s.attrib.get('time', 0)) for s in suites)}


def select():
    selected = {}
    def add(name, path):
        assert name not in selected and path.is_file() and path.suffix != '.pt'
        selected[name] = path
    owned = ['src/knowledge_tracing/sakt/training_data.py', 'src/knowledge_tracing/sakt/training.py',
             'src/knowledge_tracing/sakt/training_checkpoint.py', 'tests/sakt/test_training.py',
             'tests/sakt/test_training_checkpoint.py']
    for name in owned:
        add('final__' + ('test__' if name.startswith('tests/') else 'source__') + Path(name).name, ROOT / name)
    add('sakt_training_readiness.md', ROOT / 'research_tracking/reports/sakt_training_readiness_20261108.md')
    for i in (1, 2):
        attempt = LOCAL / f'parallel-sakt-training-20261108-0{i}'
        for path in sorted(attempt.iterdir()):
            if path.is_file(): add(f'trial0{i}__' + path.name, path)
        positive = list((attempt / 't').glob('sakt_ckpt*/synthetic_engineering_state.json'))
        assert len(positive) == 1
        add(f'trial0{i}__completed_engineering_sidecar.json', positive[0])
    for path in sorted((LOCAL / 'sakt-training-pretest-review-20261108-01').iterdir()):
        if path.is_file(): add('pretest_review__' + path.name, path)
    for path in sorted((LOCAL / 'sakt-training-budget-20261108-01').iterdir()):
        if path.is_file(): add('budget__' + path.name, path)
    final = read(LOCAL / 'parallel-sakt-training-20261108-02/run.json')
    for name in final['source_sha256_before']:
        if name not in owned:
            add('frozen__' + name.replace('/', '--'), ROOT / name)
    add('archive_pack_source.py', Path(__file__).resolve())
    add('evidence_helper.py', ROOT / 'src/knowledge_tracing/evidence.py')
    return selected, owned


def preflight(selected, owned):
    first = read(LOCAL / 'parallel-sakt-training-20261108-01/run.json')
    final = read(LOCAL / 'parallel-sakt-training-20261108-02/run.json')
    counts = [xml_counts(LOCAL / f'parallel-sakt-training-20261108-0{i}/pytest.xml') for i in (1, 2)]
    assert first['returncode'] == 1 and final['returncode'] == 0
    assert counts[0]['tests'] == counts[1]['tests'] == 139
    assert counts[0]['failures'] == 1 and counts[1]['failures'] == 0
    assert all(x['errors'] == x['skipped'] == 0 for x in counts)
    assert sha(LOCAL / 'parallel-sakt-training-20261108-02/run.json') == 'e94be1dbe4a40c87521dce404729bc7328c18c14624b1b9df93ab0e13a0c07f5'
    for i, receipt in [(1, first), (2, final)]:
        assert receipt['all_sources_unchanged']
        assert receipt['source_sha256_before'] == receipt['source_sha256_after']
        assert sha(LOCAL / f'parallel-sakt-training-20261108-0{i}/pytest.log') == receipt['pytest_log_sha256']
        assert sha(LOCAL / f'parallel-sakt-training-20261108-0{i}/pytest.xml') == receipt['junit_sha256']
        for item in receipt['copy_inventory']:
            assert sha(ROOT / item['snapshot']) == item['pre_copy_sha256'] == item['post_copy_sha256']
    for path, expected in final['source_sha256_after'].items():
        assert sha(ROOT / path) == expected
        if path not in owned: assert first['source_sha256_after'][path] == expected
    budget = read(LOCAL / 'sakt-training-budget-20261108-01/budget.json')
    ledger_path = LOCAL / 'sakt-training-budget-20261108-01/optimizer_updates.jsonl'
    ledger = [json.loads(line) for line in ledger_path.read_text(encoding='utf-8').splitlines()]
    assert [x['step'] for x in ledger] == list(range(1, 19))
    assert budget['optimizer_step_calls_charged'] == len(ledger) == final['optimizer_step_calls_after_attempt'] == 18
    assert final['optimizer_step_calls_before_attempt'] == final['optimizer_step_calls_this_attempt'] == 9
    assert len(ledger) <= budget['limit'] == 32
    elapsed = first['elapsed_seconds'] + final['elapsed_seconds']
    assert abs(budget['suite_seconds_total'] - elapsed) < 1e-9 and elapsed < 120
    binaries = []
    for i in (1, 2):
        base = LOCAL / f'parallel-sakt-training-20261108-0{i}/t'
        for path in sorted(base.rglob('*.pt')):
            if path.name not in {'synthetic_engineering_state.pt', 'negative_control.pt'}:
                continue  # Old random fixtures được old suite lưu; không claim full binary inventory.
            entry = dict(path=rel(path), bytes=path.stat().st_size, sha256=sha(path), copied=False,
                         role='completed_engineering_raw_state' if path.name.startswith('synthetic_')
                         else 'negative_control_not_a_valid_model_artifact')
            if path.name == 'synthetic_engineering_state.pt':
                metadata = read(path.with_suffix('.json'))
                assert metadata['checkpoint_sha256'] == entry['sha256']
                assert metadata['identity']['role'] == 'synthetic_trained_engineering_only'
                assert metadata['complete'] is True and metadata['resume_supported'] is False
                assert metadata['completed_epoch'] == metadata['optimizer_steps'] == 1
                assert metadata['optimized_targets'] == 4
                assert metadata['fitted_research_model'] is False
            binaries.append(entry)
    assert len(binaries) == 20
    total = sum(p.stat().st_size for p in selected.values())
    assert total < 4 * 1024**2
    return counts, budget, binaries, total


def ignored(paths):
    result = []
    for start in range(0, len(paths), 24):
        call = subprocess.run(['git', '-c', 'core.quotepath=false', 'check-ignore', '--no-index', '--',
                               *paths[start:start+24]], cwd=ROOT, capture_output=True, text=True)
        assert call.returncode in (0, 1), call.stderr
        result.extend(call.stdout.splitlines())
    return sorted(set(result))


def main():
    selected, owned = select()
    counts, budget, binaries, total = preflight(selected, owned)
    before = [dict(source=rel(path), destination=name, bytes=path.stat().st_size,
                   source_sha256=sha(path)) for name, path in selected.items()]
    sources = list(dict.fromkeys([*selected.values(), *(ROOT / x['path'] for x in binaries)]))
    note = '''# SAKT synthetic trainer engineering — 08/11/2026

Immutable archive, không model/test rerun. Final tests/sakt139PASS/17,32s;
trial01 giữ138PASS/1meta-defaultAdamfailure/18,11s. Hai controllers cộng39,980828s
<120s. Ledger charge18Adam.step calls gồm1calllỗi, không18committed updates;
trial02 có9calls thànhcông. Global engineering cap32 không reset giữa retries.

## Phạm vi

3trainer modules +2test modules mới; existing core/adapter/config/__init__,
native AKT/shared giữ nguyên. Train-only vocab/disjoint chronology/target_block1,
loss chỉ terminal eligible query, OOV/cold masks và explicit CPUFP32/optimizer.
Không chọn best epoch, training hyperparameters, refit/fullCV hoặc S04/S05.
Artifact role synthetic_trained_engineering_only, chưa fitted research baseline
hoặc OnlineSession. LearnerEvents/KTEvent có fold chỉ là fixture input contract;
chưa role-aware Grade10 simulator training bridge, không fake folds để adoption.
Ceilings geometry là engineering bounds, không scientific defaults.

## Failure và source versions

Pretest review snapshots là static findings,0tests/0optimizer; không red log giả.
01failure có log/XML/source thật: model ctor CPU chưa bảo vệ Adam lazy state
khi caller default meta.02bọc whole training scope CPU, giữ meta regression.
Read-only reviewer đã đối chiếu source và actual139PASS receipts, không rerun.

[Readiness report](sakt_training_readiness.md), [verification](archive_verification.json),
[copy before](archive_copy_inventory_before.json), [copy after](archive_copy_inventory.json),
[binary inventory](training_binary_inventory.json), [review](reviewer_note.json),
[selected links](selected_links.json), [ignored paths](force_add_paths.json).

## Checkpoint và tái lập

Raw state_dict + canonical JSON sidecar chỉ khi requested engineering epoch
hoàn tất; bound source/config/vocab/domain/input/geometry/cold/counters/hash.
Single bounded hashed BytesIO load; không optimizer/RNG resume/selected-fit
promotion. Valid sidecars của1optimizerstep/4targets được snapshot;20selected
new-training/negative-control .ptfiles chỉ SHA inventory, không copy binaries.
Không inventory toàn bộ old random fixtures hoặc pytest temp tree.
Source bindings và snapshots cần repo/runtime tương thích; không standalone kit.
Report relative links được check từ canonical directory, giữ originalbytes.
Lượt tái lập phải dùng run/budget/attempt paths mới; không append ledger hiện có.

Deadlines là cooperative stage/operator checks + outer invocation timeout;
không hard interrupt/peakRAM attestation. Serialized byte cap không bảo đảm
PyTorch peak allocation. Synthetic origin là caller declaration, không certificate.
Toy validation loss không efficacy; correctness không tự là mastery/calibration.
Không GPU/realdata/Holdout/cloud/install, không source edits sauPASS. Archive
chỉ copy/hash/XML; helper verify kiểm integrity, không scientific validity.
Rawfailure whitespace giữ byte-exact; parent xử lý integration nếu cần.
Không sửa index/state/tasks/Git; không sửa bundle sau closure.
'''
    with record_evidence_run(ROOT, RUN_ID, metadata={
        'kind': 'SAKT_SYNTHETIC_CPU_TRAINER_ENGINEERING_ARCHIVE',
        'role': 'synthetic_trained_engineering_only_not_research_fitted',
        'trial01_counts': counts[0], 'final_counts': counts[1],
        'charged_optimizer_step_calls_across_attempts': 18,
        'charged_calls_include_failed_call': True,
        'optimizer_step_call_budget': 32,
        'cumulative_controller_seconds': budget['suite_seconds_total'],
        'cumulative_controller_budget_seconds': 120,
        'new_model_or_test_runs_in_archive': 0,
        'new_optimizer_steps_in_archive': 0,
        'gpu_cloud_calls': 0, 'raw_realdata_holdout_queries': 0,
        'research_selected_fit': False, 'optimizer_rng_resume_supported': False,
        'complete_online_session_or_Grade10_training_bridge': False,
        'scope_vi': 'Partial CPU synthetic training/validation/raw-state checkpoint readiness; không complete proposal baseline/S04/S05 adoption.',
        'selected_copy_bytes': total,
    }, sources=sources, note=note) as out:
        dump(out / 'archive_copy_inventory_before.json', before)
        after = []
        for item in before:
            source = ROOT / item['source']; destination = out / item['destination']
            shutil.copyfile(source, destination)
            post, copied = sha(source), sha(destination)
            assert post == copied == item['source_sha256']
            after.append({**item, 'source_after_sha256': post, 'copied_sha256': copied, 'exact_match': True})
        dump(out / 'archive_copy_inventory.json', after)
        for entry in binaries:
            entry['after_copy_sha256'] = sha(ROOT / entry['path'])
            assert entry['after_copy_sha256'] == entry['sha256']
        dump(out / 'training_binary_inventory.json', {
            'scope_vi': '20selected trainer positive/negative state files hash-only, không deserialize/copy; không all old random fixtures.',
            'files': binaries,
        })
        dump(out / 'archive_verification.json', {
            'source_versions': {'pretest': 'static review only', 'trial01': counts[0], 'trial02': counts[1]},
            'budget': budget, 'all_final_source_hashes_match_trial02': True,
            'existing_core_adapter_shared_native_sources_unchanged': True,
            'new_source_test_files': owned,
            'new_model_test_execution': False,
        })
        dump(out / 'reviewer_note.json', {
            'reviewer': 'platform_fixture_compat', 'review_role': 'read-only source/tests/receipt review',
            'final_scope_verdict': 'PASS no blocking finding in engineering scope',
            'actual_final_tests': 139, 'actual_final_failures_errors_skips': 0,
            'final_receipt_sha256': sha(LOCAL / 'parallel-sakt-training-20261108-02/run.json'),
            'reviewer_executed_models_or_tests': False,
            'pretest_static_findings_not_fabricated_red_tests': True,
            'S04_S05_or_fitted_research_approved': False,
        })
        links = []
        original = selected['sakt_training_readiness.md']
        for target in re.findall(r'\]\(([^)]+)\)', original.read_text(encoding='utf-8')):
            if '://' in target: continue
            path = (original.parent / unquote(target.split('#')[0])).resolve()
            assert path.is_relative_to(ROOT) and path.exists(), target
            links.append(dict(source=rel(original), target=target, resolved=rel(path), exists=True))
        dump(out / 'selected_links.json', {'scope_vi': 'Canonical report directory; không rewrite archived snapshot.', 'count': len(links), 'links': links})
        whitespace = []
        for name, path in selected.items():
            numbers = [i for i, line in enumerate(path.read_bytes().splitlines(), 1) if re.search(rb'[ \t]+$', line)]
            if numbers:
                whitespace.append(dict(source=rel(path), bundle_path=rel(out / name), trailing_space_lines=numbers,
                                       raw_log_or_xml=path.suffix in {'.log', '.xml'}, bytes_preserved=True))
        dump(out / 'raw_whitespace_inventory.json', {'files': whitespace, 'rewrite': False})
        paths = [rel(p) for p in out.iterdir()] + [rel(out / 'force_add_paths.json')]
        ignored_paths = ignored(paths)
        dump(out / 'force_add_paths.json', {
            'method': 'git check-ignore --no-index exact argv, no stdin newline conversion',
            'ignored_paths_requiring_force_add': ignored_paths,
            'pt_binaries_not_to_add': True,
        })
    directory = ROOT / 'research_tracking/runs' / RUN_ID
    verified = verify_evidence_bundle(directory)
    print(json.dumps({**verified, 'run_id': RUN_ID, 'manifest_sha256': sha(directory / 'manifest.json'),
                      'copies': len(after), 'sources': len(sources), 'selected_copy_bytes': total,
                      'bundle_bytes': sum(p.stat().st_size for p in directory.iterdir()),
                      'binary_inventory': len(binaries), 'links': len(links),
                      'ignored_paths': ignored_paths,
                      'raw_whitespace_paths': [x['bundle_path'] for x in whitespace]}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
