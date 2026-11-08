"""Đóng targeted tooling evidence; không chạy tests/model/install hoặc full Gate."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle

LOCAL = ROOT / 'artifacts/akt/local-tests'
RUN = 'linux-gate-tooling-engineering-20261108-01'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_text(encoding='utf-8'))


def rel(path):
    return path.relative_to(ROOT).as_posix()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def counts(path):
    suites = list(ET.parse(path).getroot().iter('testsuite'))
    return {**{key: sum(int(s.attrib.get(key, 0)) for s in suites)
               for key in ('tests', 'failures', 'errors', 'skipped')},
            'junit_seconds': sum(float(s.attrib.get('time', 0)) for s in suites)}


def ignored(paths):
    result = []
    for start in range(0, len(paths), 24):
        call = subprocess.run(['git', '-c', 'core.quotepath=false', 'check-ignore', '--no-index', '--',
                               *paths[start:start + 24]], cwd=ROOT, capture_output=True, text=True)
        assert call.returncode in (0, 1), call.stderr
        result += call.stdout.splitlines()
    return sorted(set(result))


selected = {}


def add(name, path):
    assert name not in selected and path.is_file() and not path.is_symlink()
    assert path.suffix.lower() not in {'.pt', '.parquet', '.zip'}
    assert path.stat().st_size < 2 * 1024**2
    selected[name] = path


owned = ['scripts/akt/check_runtime.py', 'scripts/akt/refresh_gate2.py',
         'tests/akt/test_runtime.py', 'tests/akt/test_gate2_refresh.py']
for name in owned:
    add('final__' + Path(name).name, ROOT / name)
report = ROOT / 'research_tracking/reports/akt_linux_gate_tooling_readiness_20261108.md'
draft = ROOT / 'artifacts/akt/colab/gpu08-linux-20261108-01/NEXT_LINUX_WORKER_GATE_DRAFT.md'
add('readiness_report.md', report)
add('NEXT_LINUX_WORKER_GATE_DRAFT.md', draft)
for prefix, folder in [('pre_fix', 'linux-gate-tooling-pretest-20261108-01'),
                       ('trial01', 'linux-gate-tooling-trial-20261108-01'),
                       ('trial02', 'linux-gate-tooling-trial-20261108-02')]:
    for path in sorted((LOCAL / folder).iterdir()):
        if path.is_file():
            add(prefix + '__' + path.name, path)
add('windows_hashlock_fixture.txt', ROOT / 'requirements-akt.lock.txt')
add('candidate_linux_hashlock_reference.txt', ROOT / 'research_tracking/runs/akt-linux-dependency-resolution-20261108-01/candidate-linux-cuda.lock.txt')
gate21 = ROOT / 'artifacts/akt/preflight/gate2-evidence-20261108-elapsed-guard-21.json'
add('historical_gate21_report.json', gate21)
add('archive_pack_source.py', Path(__file__).resolve())
add('evidence_helper.py', ROOT / 'src/knowledge_tracing/evidence.py')

first = read(LOCAL / 'linux-gate-tooling-trial-20261108-01/run.json')
last = read(LOCAL / 'linux-gate-tooling-trial-20261108-02/run.json')
cs = [counts(LOCAL / f'linux-gate-tooling-trial-20261108-0{i}/pytest.xml') for i in (1, 2)]
assert cs[0]['tests'] == cs[1]['tests'] == 118
assert cs[0]['failures'] == 11 and first['returncode'] == 1
assert cs[1]['failures'] == 0 and last['returncode'] == 0
assert all(c['errors'] == c['skipped'] == 0 for c in cs)
assert first['elapsed_seconds'] + last['elapsed_seconds'] < 120
for receipt in [first, last]:
    assert receipt['all_sources_unchanged']
    assert receipt['source_sha256_before'] == receipt['source_sha256_after']
    assert receipt['optimizer_steps'] == receipt['model_fit_calls'] == 0
for name, expected in last['source_sha256_after'].items():
    assert sha(ROOT / name) == expected
assert sha(LOCAL / 'linux-gate-tooling-trial-20261108-02/run.json') == '98cbeba165885b2085b2b32e791aadd0d2b243c3175fcd0f5ec89f3b6b34452b'
assert sha(ROOT / 'requirements-akt.lock.txt') == '3e721fdb49543ad0888cf02a863826ebc6144c0d1dd670f2490ebcc0d69b8c0a'
assert sha(selected['candidate_linux_hashlock_reference.txt']) == '60dad3de310562db4f775d1977e2097a6d1c8f57a22bfa4f7afc3ceab35cc45a'
assert sha(gate21) == 'b74f4b96fe6a288f380b3ec69cfba2c01f95c089a8f8d98cdadc0aeb5f8d9c8e'
old = read(gate21)
for row in read(LOCAL / 'linux-gate-tooling-pretest-20261108-01/source_inventory.json')['copies']:
    assert (sha(LOCAL / 'linux-gate-tooling-pretest-20261108-01' / row['copy'])
            == row['sha256_before'] == row['sha256_after_copy'] == old['build_hashes'][row['source']])
assert all(last['source_sha256_after'][name] != old['build_hashes'][name] for name in owned)
assert sum(p.stat().st_size for p in selected.values()) < 3 * 1024**2
before = [{'source': rel(path), 'destination': name, 'bytes': path.stat().st_size,
           'source_before_sha256': sha(path)} for name, path in selected.items()]

note = '''# Linux Gate tooling engineering — 08/11/2026

Local WindowsCPU targeted118PASS, không actualLinuxGate hoặc GPU09/runtime acceptance.
Publicpackaging26.3 thay pip._vendor imports; defaultWindowslock giữ nguyên.
refresh(lock_file=None)/--lock-file chọn existing project-root/artifactsAKT lock,
kiểmprotected/private/outside/missing/directlink; selectedSHA trước/sau và path
provenance; finalreader nhận chính selectedlock. Schema1/source/upstream/elapsed
1..600/default300/threadenv2 giữ nguyên. Không đổi model/hypers/data/method.

## Red/green thật và archive

Actual01:118tests107PASS11FAIL/14.835028scontroller; actual02:118PASS0fail/error/skip,
15.195849scontroller/13.088sJUnit. Cộng30.030877s<120,0optimizer/model fit.
Giữ4physicalsource snapshots trước sửa và từngtrial, sourcepre/post receipts,
log/XML; không fake red và không xóa failures. Haipeerreview chỉđọc/scopedPASS.
Khóa Linux trong unittest là textfixture, không giả installability.

[Report](readiness_report.md), [draft](NEXT_LINUX_WORKER_GATE_DRAFT.md),
[verification](archive_verification.json), [before](archive_copy_inventory_before.json),
[after](archive_copy_inventory.json), [review](peer_review_note.json),
[links](selected_links.json), [ignored](force_add_paths.json),
[raw whitespace](raw_whitespace_inventory.json).
Canonical report links giữ context repo, snapshot không rewrite.

## Gate và bước tương lai

Gate21 source cũ vẫn acceptedhistorical757 nhưng cả4sourceSHA đổi; cần newsourceGate.
Parent chạy WindowsGate22 riêng; archive này không quan sát/publish verdict của nó.
ActualLinuxfull tests/akt+shared vẫn cần cùng frozenkit/installedprofile/Linuxlock.
No exclusion/rehashWindowspass hoặc runtimevalidatorbypass. Runtimeinspection hash
lock không xác minh installed44versions; installation/pipcheck/origins cần riêng.

Remote resolution-attempt01 lock ngoàiallowlist; future phải exclusivecopy cóSHA
inventory sang artifacts/akt/dependencies/linux-cu126/candidate-linux-cuda.lock.txt,
giữ source cũ, same60dad. Không copy/rename remote bởi archive này.
Draft commands chưa chạy/không cấp ngân sách; no .pt/Parquet/wheels/ZIP/tempdirs.
Không remote/network/install/GPU/Modal/realdata/Holdout/fullGate trong archive.
record_evidence_run/verify kiểm integrity, không efficacy hoặc S04/S05 approval.
Raw failures giữ nguyên bytes; không sửa bundle sau closure. Tái lập dùng paths
mới và budget explicit; snapshots không standalone runtime kit.
'''
with record_evidence_run(ROOT, RUN, metadata={
    'kind': 'LINUX_GATE_TOOLING_TARGETED_ENGINEERING_ARCHIVE',
    'role': 'local_CPU_tooling_targeted_pass_not_actual_Linux_Gate_or_runtime',
    'trial01_counts': cs[0], 'trial02_counts': cs[1],
    'cumulative_targeted_controller_seconds': first['elapsed_seconds'] + last['elapsed_seconds'],
    'cumulative_targeted_budget_seconds': 120, 'optimizer_steps': 0, 'model_fit_calls': 0,
    'new_test_model_install_calls_during_archive': 0, 'actual_Linux_Gate_executed': False,
    'full_Gate22_acceptance_in_this_bundle': False, 'Gate21_historical_for_changed_source': True,
    'new_research_protocol_or_GPU_authorization': False,
    'selected_copy_bytes': sum(path.stat().st_size for path in selected.values()),
}, sources=list(dict.fromkeys(selected.values())), note=note) as out:
    dump(out / 'archive_copy_inventory_before.json', before)
    after = []
    for row in before:
        source = ROOT / row['source']
        destination = out / row['destination']
        shutil.copyfile(source, destination)
        assert sha(source) == sha(destination) == row['source_before_sha256']
        after.append({**row, 'source_after_sha256': sha(source), 'copied_sha256': sha(destination), 'exact_match': True})
    dump(out / 'archive_copy_inventory.json', after)
    dump(out / 'archive_verification.json', {
        'trial01': cs[0], 'trial02': cs[1], 'all_final_source_hashes_match_trial02': True,
        'four_pre_fix_sources_match_Gate21': True, 'four_final_sources_differ_from_Gate21': True,
        'windows_hashlock_unchanged_sha256': sha(ROOT / 'requirements-akt.lock.txt'),
        'linux_hashlock_reference_sha256': sha(selected['candidate_linux_hashlock_reference.txt']),
        'full_Gate22_or_actual_Linux_Gate_observed': False, 'new_execution_in_archive': False,
    })
    dump(out / 'peer_review_note.json', {
        'reviewers': ['platform_fixture_compat', 'graph_gate_prototype'],
        'verdict': 'scoped read-only PASS reported by parent; no remaining blocker in four-file change',
        'reviewer_model_or_test_execution': False,
        'limitations': 'Selected lock byte hash remains reader identity; path string provenance is additional metadata, not a substitute. No Linux/runtime/CUDA/research acceptance.',
    })
    links = []
    for target in re.findall(r'\]\(([^)]+)\)', report.read_text(encoding='utf-8')):
        if '://' in target:
            continue
        path = (report.parent / target.split('#')[0]).resolve()
        assert path.is_relative_to(ROOT) and path.exists(), target
        links.append({'source': rel(report), 'target': target, 'resolved': rel(path), 'exists': True})
    dump(out / 'selected_links.json', {'scope': 'canonical report directory; byte-exact snapshot', 'links': links})
    whitespace = []
    for name, path in selected.items():
        lines = [i for i, line in enumerate(path.read_bytes().splitlines(), 1) if re.search(rb'[ \t]+$', line)]
        if lines:
            whitespace.append({'source': rel(path), 'bundle_path': rel(out / name), 'trailing_space_lines': lines,
                               'raw_log_or_xml': path.suffix in {'.log', '.xml'}, 'bytes_preserved': True})
    dump(out / 'raw_whitespace_inventory.json', {'rewrite': False, 'files': whitespace})
    force = ignored([rel(path) for path in out.iterdir()] + [rel(out / 'force_add_paths.json')])
    dump(out / 'force_add_paths.json', {'method': 'git check-ignore --no-index exact argv chunks24',
                                      'ignored_paths_requiring_force_add': force})
out = ROOT / 'research_tracking/runs' / RUN
verified = verify_evidence_bundle(out)
assert all(sha(ROOT / row['source']) == sha(out / row['destination']) == row['source_before_sha256'] for row in before)
assert set(force) == set(ignored([rel(path) for path in out.iterdir()]))
assert all(path.is_file() and path.suffix.lower() not in {'.pt', '.parquet', '.zip'} for path in out.iterdir())
result = {**verified, 'run_id': RUN, 'manifest_sha256': sha(out / 'manifest.json'),
          'copy_pairs': len(after), 'sources': len(selected),
          'bundle_bytes': sum(path.stat().st_size for path in out.iterdir()),
          'report_sha256': sha(report), 'report_links': len(links), 'force_add_paths': force,
          'raw_whitespace_paths': [item['bundle_path'] for item in whitespace]}
dump(Path(__file__).parent / 'closure_verification.json', result)
print(json.dumps(result, indent=2, ensure_ascii=False))
