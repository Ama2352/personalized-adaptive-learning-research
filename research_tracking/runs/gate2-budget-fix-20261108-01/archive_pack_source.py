"""Đóng evidence operational budget fix; chỉ copy/hash/XML, không tests/models."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
from knowledge_tracing.akt.authorization import require_gate2_evidence
from knowledge_tracing.akt.config import AKTConfig

LOCAL = ROOT / 'artifacts/akt/local-tests'
PRE = ROOT / 'artifacts/akt/preflight'
RUN = 'gate2-budget-fix-20261108-01'
OLD = '9d86b215bd936f04880bcd9bc775f2016784f279572109c39c017d46375fe351'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8'))


def rel(p):
    return p.relative_to(ROOT).as_posix()


def dump(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def counts(p):
    suites = list(ET.parse(p).getroot().iter('testsuite'))
    return {**{n: sum(int(s.attrib.get(n, 0)) for s in suites)
               for n in ['tests', 'failures', 'errors', 'skipped']},
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
    assert path.suffix.lower() not in {'.pt', '.parquet', '.pq'}
    assert path.stat().st_size < 2 * 1024 ** 2
    selected[name] = path


owned = ['src/knowledge_tracing/akt/authorization.py', 'scripts/akt/refresh_gate2.py',
         'tests/akt/test_gate2_refresh.py', 'tests/akt/test_runner.py']
for name in owned:
    add('final__' + Path(name).name, ROOT / name)
report = ROOT / 'research_tracking/reports/gate2_elapsed_budget_fix_20261108.md'
add('gate2_elapsed_budget_fix_report.md', report)
for prefix, folder in [('pre_fix', 'gate2-budget-fix-pretest-20261108-01'),
                       ('trial01', 'gate2-budget-fix-trial-20261108-01'),
                       ('trial02', 'gate2-budget-fix-trial-20261108-02'),
                       ('refit_diagnostic', 'gate20-refit-diagnostic-20261108-01')]:
    for path in sorted((LOCAL / folder).iterdir()):
        if path.is_file():
            add(prefix + '__' + path.name, path)
for name in ['gate2-evidence-20261108-graph-prototype-20.json',
             'gate2-tests-20261108-graph-prototype-20.log',
             'gate2-tests-20261108-graph-prototype-20.xml',
             'gate2-resource-audit-20261108-graph-prototype-20.json',
             'gate2-resource-audit-20261108-20-verification.json',
             'gate2-pointer-before-resource-audit-20261108-20.json',
             'gate2-pointer-before-20261108-graph-prototype-20.json']:
    add('historical__' + name, PRE / name)
add('current_rejected_pointer_snapshot.json', PRE / 'gate2-current.json')
add('historical_revocation_script_snapshot.py', LOCAL / 'revoke_overbudget_gate20.py')
for stem in ['20261108-context-18', '20261108-sim-trainer-19']:
    for name in [f'gate2-evidence-{stem}.json', f'gate2-tests-{stem}.xml']:
        add('comparison__' + name, PRE / name)
add('archive_pack_source.py', Path(__file__).resolve())
add('evidence_helper.py', ROOT / 'src/knowledge_tracing/evidence.py')

first = read(LOCAL / 'gate2-budget-fix-trial-20261108-01/run.json')
last = read(LOCAL / 'gate2-budget-fix-trial-20261108-02/run.json')
diag = read(LOCAL / 'gate20-refit-diagnostic-20261108-01/run.json')
cs = [counts(LOCAL / f'gate2-budget-fix-trial-20261108-0{i}/pytest.xml') for i in (1, 2)]
assert cs[0]['tests'] == 44 and cs[0]['failures'] == 25 and first['returncode'] == 1
assert cs[1]['tests'] == 47 and cs[1]['failures'] == cs[1]['errors'] == cs[1]['skipped'] == 0
assert last['returncode'] == 0 and all(c['errors'] == c['skipped'] == 0 for c in cs)
assert first['elapsed_seconds'] + last['elapsed_seconds'] < 60
for receipt in [first, last, diag]:
    assert receipt['all_sources_unchanged']
    assert receipt['source_sha256_before'] == receipt['source_sha256_after']
for name, digest in last['source_sha256_after'].items():
    assert sha(ROOT / name) == digest
pre_source = read(LOCAL / 'gate2-budget-fix-pretest-20261108-01/source_inventory.json')['copies']
oldreport = read(PRE / 'gate2-evidence-20261108-graph-prototype-20.json')
for item in pre_source:
    assert (sha(LOCAL / 'gate2-budget-fix-pretest-20261108-01' / item['copy'])
            == item['sha256_before'] == item['sha256_after_copy']
            == oldreport['build_hashes'][item['source']])
assert sha(PRE / 'gate2-evidence-20261108-graph-prototype-20.json') == OLD
assert sha(PRE / 'gate2-tests-20261108-graph-prototype-20.log') == oldreport['test_log_sha256']
assert sha(PRE / 'gate2-tests-20261108-graph-prototype-20.xml') == oldreport['junit_sha256']
audit = read(PRE / 'gate2-resource-audit-20261108-graph-prototype-20.json')
rev = read(PRE / 'gate2-resource-audit-20261108-20-verification.json')
pointer = read(PRE / 'gate2-current.json')
assert audit['original_evidence_sha256'] == OLD and audit['status'] == 'REJECTED_RESOURCE_BOUND'
assert (sha(PRE / 'gate2-resource-audit-20261108-graph-prototype-20.json')
        == rev['audit_sha256'] == pointer['evidence_sha256'])
assert (sha(PRE / 'gate2-pointer-before-resource-audit-20261108-20.json')
        == rev['pointer_before_sha256'] == rev['pointer_backup_sha256'])
assert sha(PRE / 'gate2-current.json') == rev['pointer_after_sha256']
try:
    require_gate2_evidence(AKTConfig())
except ValueError as error:
    actual_rejection = {'accepted': False, 'error': str(error)}
else:
    raise AssertionError('current Gate must remain rejected before new source-bound Gate')
assert diag['returncode'] == 0 and not diag['timed_out'] and diag['elapsed_seconds'] < 45
assert counts(LOCAL / 'gate20-refit-diagnostic-20261108-01/pytest.xml')['tests'] == 1
comparison = read(LOCAL / 'gate20-refit-diagnostic-20261108-01/comparison_and_findings.json')
assert comparison['host_suspend_status'] == 'UNKNOWN'
assert comparison['system_event_query']['exception_type'] == 'System.UnauthorizedAccessException'
raw = (LOCAL / 'gate20-refit-diagnostic-20261108-01/process_metadata.json').read_text()
norm = read(LOCAL / 'gate20-refit-diagnostic-20261108-01/process_metadata.normalized.json')
assert raw.endswith('\\n') and json.loads(raw[:-2]) == norm['metadata']
assert norm['normalization']['raw_sha256'] == sha(LOCAL / 'gate20-refit-diagnostic-20261108-01/process_metadata.json')
assert norm['metadata']['threads'] == 2 and norm['metadata']['cuda_available'] is False
assert sha(report) == 'c4fd61bf1283b2509b7bffdbe8d58a9946f827faf26119c711f4a28e0dd5ceb3'
assert sum(p.stat().st_size for p in selected.values()) < 3 * 1024 ** 2
before = [{'source': rel(p), 'destination': name, 'bytes': p.stat().st_size,
           'source_before_sha256': sha(p)} for name, p in selected.items()]
note = '''# Sửa ngân sách Gate2 — evidence đóng ngày08/11/2026

Gói operational bugfix targetedPASS, không là full Gate chấp nhận source mới,
không training acceptance/efficacy, không adoption S04/S05. Archive chỉ copy/hash/XML;
0tests/model/optimizer/GPU/data/cloud chạy trong lúc đóng gói.

## Bằng chứng giữ lại

4source/test trước sửa khớp buildSHA của Gate20; actual RED01:44tests19PASS25FAIL.
Final02:47PASS0fail/error/skip, gồm3invalid-clock cases thêm sauRED.
Controllers10.797052+9.366551=20.163603s<60s,0optimizer/fit ở targetedGate tests.
Fake successful child/nonemptyJUnit nhưng1084s>540 phải giữ pointer nguyên byte,
ghi reportREJECTED_RESOURCE_BOUND độc quyền rồiTimeoutError; reader từ chối cả
resourcefields đãrehash. Timeout1..600/default300 và schema1 giữ nguyên.
OMP/MKL/OpenBLAS2 là childsoftwareCI bound, không scientific model default.

[Report nguyên byte](gate2_elapsed_budget_fix_report.md),
[verification](archive_verification.json), [before](archive_copy_inventory_before.json),
[after](archive_copy_inventory.json), [binding](source_binding_comparison.json),
[docs chính thức](official_primary_sources.json), [links](selected_links.json),
[ignored paths](force_add_paths.json), [whitespace](raw_whitespace_inventory.json).
Report snapshot giữ relative links theo canonical report directory; không rewrite.

## Gate20 và trạng thái lúc snapshot

Gate20 original SHA9d86b215bd936f04880bcd9bc775f2016784f279572109c39c017d46375fe351
bất biến.724functionalPASS nhưng1083.995106s>540: ngân sách không đạt.
Giữ report/log/XML, auditrejection, helperrevocation snapshot và pointers trước/sau.
Currentpointer tại closure trỏ rejection; actualreader từ chối. Gate21/source mới
chưa được gói này chấp nhận. Snapshot pointer có thời điểm; không tự cập nhật
khi parent phát hành Gate mới. Không rerun scriptrevocation đã lưu: đây chỉ là
historical source snapshot và nó có sideeffects ngoài phạm vi archive này.

## Exact refit diagnosis và giới hạn

Giữ1testsynthetic refit chạy riêng:1PASS/8.452sJUnit7.896stest,
12.055534scontroller<45s, threadenv2/actualintraop2interop12, CUDAfalse.
Không gọi lượt đó là0optimizer: testrefit gốc có tiny training/recovery updates.
Archive không chạy lại và không copy/load .pt/Parquet hoặc pytest temp dirs.
G18/G19 cùngtest1.682/3.087s với4selectedcodeSHA giốngG20; G20test922.520s.
Không xác định nguyên nhân: query10KernelPower42/107timestamps bịAccessDenied;
không escalation. Sleep/suspendUNKNOWN. OfficialWait/QPC semantics là cơ chế
có thể phù hợp, không là causal evidence. ClockgapUTC không xác nhận sleep.
Rawmetadata có trailerliteralbackslash-n giữbyteexact; normalized companion
bỏ đúng2ký tự vớiSHA/provenance. Không fake failure/model rerun vì lỗi format.
Initial metadata-only helperimportpathmiss được ghi ở finalverification.

Postelapsedguard chặn falsePASS sau khi child hoàn tất, không hardinterrupt
tronghostsleep/OSblocking call. Không trừ elapsed theo sleep suy đoán.
No rootindex/state/Git/source changes trong archive; helperverification chỉ
integrity, không validity nghiên cứu. Giữ rawfailure whitespace nguyên byte.
Không sửa bundle sau closure. Tái lập dùng runpath mới, .venv và cap rõ ràng;
nguồn snapshot cần repo/runtime tương thích, không standalone executable kit.
'''
with record_evidence_run(ROOT, RUN, metadata={
    'kind': 'GATE2_ELAPSED_BUDGET_OPERATIONAL_BUGFIX_ARCHIVE',
    'role': 'operational_bugfix_targeted_pass_not_full_gate_acceptance',
    'targeted_trial01': cs[0], 'targeted_trial02': cs[1],
    'targeted_controller_seconds': first['elapsed_seconds'] + last['elapsed_seconds'],
    'targeted_controller_cap_seconds': 60, 'targeted_optimizer_steps': 0,
    'targeted_model_fit_calls': 0, 'separate_refit_diagnostic_contains_synthetic_training': True,
    'new_model_or_test_runs_during_archive': 0, 'new_optimizer_steps_during_archive': 0,
    'full_current_gate_accepted': False, 'source_bound_gate21_pending_at_snapshot': True,
    'original_gate20_report_sha256': OLD, 'host_suspend_status': 'UNKNOWN',
    'raw_realdata_holdout_access': False,
    'selected_copy_bytes': sum(p.stat().st_size for p in selected.values()),
}, sources=list(dict.fromkeys(selected.values())), note=note) as out:
    dump(out / 'archive_copy_inventory_before.json', before)
    after = []
    for item in before:
        src = ROOT / item['source']
        dst = out / item['destination']
        shutil.copyfile(src, dst)
        assert sha(src) == sha(dst) == item['source_before_sha256']
        after.append({**item, 'source_after_sha256': sha(src), 'copied_sha256': sha(dst), 'exact_match': True})
    dump(out / 'archive_copy_inventory.json', after)
    dump(out / 'archive_verification.json', {
        'trial01': cs[0], 'trial02': cs[1], 'all_final_source_hashes_match_trial02': True,
        'original_gate20_unchanged_sha256': sha(PRE / 'gate2-evidence-20261108-graph-prototype-20.json'),
        'current_rejected_pointer_sha256': sha(PRE / 'gate2-current.json'),
        'actual_reader_current_rejection': actual_rejection,
        'refit_diagnostic_receipt_sha256': sha(LOCAL / 'gate20-refit-diagnostic-20261108-01/run.json'),
        'raw_metadata_preserved_and_normalization_verified': True,
        'binary_or_temp_tree_copies': 0, 'new_test_or_model_execution': False,
    })
    dump(out / 'source_binding_comparison.json', {
        'files': [{'source': name, 'gate20_pre_fix_sha256': oldreport['build_hashes'][name],
                   'final_trial02_sha256': last['source_sha256_after'][name], 'current_sha256': sha(ROOT / name)}
                  for name in owned], 'historical_gate20_cannot_authorize_changed_source': True,
    })
    dump(out / 'official_primary_sources.json', {
        'role': 'primary docs read in diagnosis, paraphrase only; not host-suspend proof',
        'sources': comparison['primary_sources'], 'host_suspend_status': 'UNKNOWN',
        'event_query': comparison['system_event_query'],
    })
    links = []
    for target in re.findall(r'\]\(([^)]+)\)', report.read_text(encoding='utf-8')):
        if '://' in target:
            continue
        path = (report.parent / unquote(target.split('#')[0])).resolve()
        assert path.is_relative_to(ROOT) and path.exists(), target
        links.append({'source': rel(report), 'target': target, 'resolved': rel(path), 'exists': True})
    dump(out / 'selected_links.json', {'scope': 'canonical report directory, snapshot not rewritten', 'links': links})
    whitespace = []
    for name, path in selected.items():
        numbers = [i for i, line in enumerate(path.read_bytes().splitlines(), 1) if re.search(rb'[ \t]+$', line)]
        if numbers:
            whitespace.append({'source': rel(path), 'bundle_path': rel(out / name), 'trailing_space_lines': numbers,
                               'raw_log_or_xml': path.suffix in {'.log', '.xml'}, 'bytes_preserved': True})
    dump(out / 'raw_whitespace_inventory.json', {'rewrite': False, 'files': whitespace})
    force = ignored([rel(path) for path in out.iterdir()] + [rel(out / 'force_add_paths.json')])
    dump(out / 'force_add_paths.json', {
        'method': 'git check-ignore --no-index exact argv chunks24, no stdin',
        'ignored_paths_requiring_force_add': force, 'binaries_or_temp_dirs_not_to_add': True,
    })
out = ROOT / 'research_tracking/runs' / RUN
verified = verify_evidence_bundle(out)
assert sha(PRE / 'gate2-evidence-20261108-graph-prototype-20.json') == OLD
assert all(sha(ROOT / x['source']) == x['source_before_sha256'] == sha(out / x['destination']) for x in before)
assert set(force) == set(ignored([rel(path) for path in out.iterdir()]))
assert not any(path.is_dir() or path.suffix.lower() in {'.pt', '.parquet', '.pq'} for path in out.iterdir())
result = {**verified, 'run_id': RUN, 'manifest_sha256': sha(out / 'manifest.json'),
          'copies': len(after), 'sources': len(selected), 'selected_copy_bytes': sum(x['bytes'] for x in before),
          'bundle_bytes': sum(path.stat().st_size for path in out.iterdir()), 'report_links': len(links),
          'ignored_paths': force, 'raw_whitespace_paths': [x['bundle_path'] for x in whitespace]}
dump(Path(__file__).parent / 'closure_verification.json', result)
print(json.dumps(result, indent=2, ensure_ascii=False))
