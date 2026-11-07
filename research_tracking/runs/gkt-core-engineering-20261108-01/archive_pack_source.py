"""Đóng archive GKT Batch A đã freeze; không gọi model/tests/training."""

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
RUN_ID = 'gkt-core-engineering-20261108-01'
ATTEMPT = ROOT / 'artifacts/akt/local-tests/parallel-gkt-core-20261108-01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def relative(path):
    return path.relative_to(ROOT).as_posix()


def main():
    trial = json.loads((ATTEMPT / 'run.json').read_text(encoding='utf-8'))
    assert trial['exit_code'] == 0 and trial['sources_unchanged']
    assert trial['optimizer_steps'] == trial['new_training_or_simulator_events'] == 0
    suite = ET.parse(ATTEMPT / 'pytest.xml').getroot().find('testsuite')
    acceptance = {key: int(suite.attrib[key]) for key in ('tests', 'failures', 'errors', 'skipped')}
    assert acceptance == dict(tests=43, failures=0, errors=0, skipped=0)
    assert sha(ATTEMPT / 'pytest.log') == trial['log_sha256']
    assert sha(ATTEMPT / 'pytest.xml') == trial['junit_sha256']
    for source, digest in trial['source_sha256_before'].items():
        assert sha(ROOT / source) == digest == trial['source_sha256_after'][source]
    for item in trial['copy_inventory']:
        assert sha(ROOT / item['snapshot']) == item['before_sha256'] == item['copied_sha256']

    copies = {
        'gkt_config.py': ROOT / 'src/knowledge_tracing/gkt/config.py',
        'gkt_core.py': ROOT / 'src/knowledge_tracing/gkt/core.py',
        'gkt_init.py': ROOT / 'src/knowledge_tracing/gkt/__init__.py',
        'test_gkt_core.py': ROOT / 'tests/gkt/test_core.py',
        'gkt_core_readiness.md': ROOT / 'research_tracking/reports/gkt_core_readiness_20261108.md',
        'gkt_source_and_core_plan.md': ROOT / 'research_tracking/reports/gkt_source_and_core_plan_20261108.md',
        'gkt_source_and_core_plan.json': ROOT / 'research_tracking/reports/gkt_source_and_core_plan_20261108.json',
        'trial01_pytest.log': ATTEMPT / 'pytest.log',
        'trial01_pytest.xml': ATTEMPT / 'pytest.xml',
        'trial01_run.json': ATTEMPT / 'run.json',
        'archive_pack_source.py': Path(__file__).resolve(),
        'evidence_helper.py': ROOT / 'src/knowledge_tracing/evidence.py',
    }
    expected_report = '4ee7d0251a3edc09e8fc57fa9fd227f9e6a6ee6aa8a07861993c72064f388802'
    assert sha(copies['gkt_core_readiness.md']) == expected_report
    before = [dict(source=relative(p), destination=name, bytes=p.stat().st_size,
                   source_sha256=sha(p)) for name, p in copies.items()]
    sources = list(dict.fromkeys([*copies.values(), *(ROOT / x['snapshot'] for x in trial['copy_inventory'])]))
    note = '''# GKT Batch A: pure kernel engineering — 08/11/2026

Immutable run `gkt-core-engineering-20261108-01` giữ kết quả43CPUcases PASS
1,957s(controller2,827425s),0failure/error/skip; chỉ archive, không chạy lại tests.
Source/test/report freeze, source SHA trước/sau và pre/post-copy SHA được giữ.

**GKT vẫn INCOMPLETE:** aggregate_after_observation, static incoming/outgoing
message arithmetic và readout với state/embeddings/precomputed transforms do
caller cung cấp. Không h0, G_ea, GRU/recurrence, MLP/normalization, trainer,
fitted scores, checkpoint/export, sequence/OnlineSession hoặc end-to-end proof.
0optimizer/GPU/cloud/realdata/Holdout; không pseudotrained artifact hoặc efficacy.
Positive numerical fixtures CPU FP64; FP32 API chưa có positive suite riêng.
Query→observe chronology và input origin vẫn caller contract; metadata hashes
không attest training provenance. Support mask không chọn sparse recurrent policy.
S04/S05 và graph/capacity/history/model-environment allocation vẫn pending.

## Đọc bằng chứng

- [Snapshot readiness](gkt_core_readiness.md) và [report canonical](../../reports/gkt_core_readiness_20261108.md).
- [Source audit/plan](gkt_source_and_core_plan.md), [primary-source provenance](source_provenance.json).
- [Trial receipt](trial01_run.json), [log](trial01_pytest.log), [XML](trial01_pytest.xml).
- [Copy inventory trước](archive_copy_inventory_before.json) và [đối chiếu sau](archive_copy_inventory.json).
- [Selected link checks](selected_links.json), [force-add paths](force_add_paths.json).

Source snapshots `gkt_config.py`, `gkt_core.py`, `gkt_init.py`, `test_gkt_core.py`
khớp source/test snapshots của trial01; không giả đây là trial mới. Archive không
copy .pt/dataset/Parquet hoặc dependencies/runtime. Source-plan JSON giữ raw
external hashes=null: web primary text đã đọc, không downloaded PDF/visual check
hoặc author-code parity. `jhljx/GKT` không được gọi author-official implementation.

## Tái lập và giới hạn

Repo/runtime tương thích cần có để tái lập tests; snapshots là evidence, không
standalone runtime. Canonical report/plan còn dùng repository-relative links;
giữ nguyên bytes và kiểm từ original directory trong selected_links.json, không
claim mọi relative link của archived snapshot tự resolve tại đây. Test command
và env/timeout ở trial receipt; lần tái chạy phải chọn attempt/basetemp mới.
Pack script chỉ inventory/copy/hash/XML parsing/helper closure, không model/test
execution. Helper verify chỉ kiểm output integrity, không scientific validity.
Không sửa indices/state/tasks/Git/native AKT/shared hoặc chạy thêm experiment.
Không thêm/sửa file sau closure; parent quản review/index/commit riêng.
'''
    with record_evidence_run(ROOT, RUN_ID, metadata={
        'kind': 'GKT_BATCH_A_STATIC_KERNEL_CPU_ENGINEERING_ARCHIVE',
        'evidence_role': 'software_partial_kernel_not_fitted_efficacy',
        'tests_reused': acceptance,
        'test_seconds': float(suite.attrib['time']),
        'new_test_runs_in_archive': 0,
        'optimizer_steps': 0,
        'new_training_or_simulator_events': 0,
        'gpu_cloud_calls': 0,
        'realdata_holdout_queries': 0,
        'gkt_complete': False,
        'fitted_model': False,
        'sequence_or_end_to_end_bridge_verified': False,
        'scope_vi': 'Pure static message/readout arithmetic, caller state/transforms; không recurrence/trainer hoặc S04/S05 adoption.',
    }, sources=sources, note=note) as out:
        dump(out / 'archive_copy_inventory_before.json', before)
        after = []
        for item in before:
            source = ROOT / item['source']
            destination = out / item['destination']
            shutil.copyfile(source, destination)
            post, copied = sha(source), sha(destination)
            assert item['source_sha256'] == post == copied
            after.append({**item, 'source_after_sha256': post,
                          'copied_sha256': copied, 'exact_match': True})
        dump(out / 'archive_copy_inventory.json', after)
        links = []
        for name in ('gkt_core_readiness.md', 'gkt_source_and_core_plan.md'):
            source = copies[name]
            for target in re.findall(r'\]\(([^)]+)\)', source.read_text(encoding='utf-8')):
                if '://' in target:
                    continue
                resolved = (source.parent / unquote(target.split('#')[0])).resolve()
                assert resolved.is_relative_to(ROOT) and resolved.exists()
                links.append(dict(source=relative(source), target=target,
                                  resolved=relative(resolved), exists=True,
                                  sha256=sha(resolved) if resolved.is_file() else None))
        dump(out / 'selected_links.json', {
            'scope_vi': 'Kiểm local links từ canonical source directory; không network fetch/archived relative-link rewrite.',
            'checked': len(links), 'links': links,
        })
        primary = json.loads(copies['gkt_source_and_core_plan.json'].read_text(encoding='utf-8'))
        dump(out / 'source_provenance.json', {
            'evidence_role': 'GKT_partial_static_kernel_no_author_code_parity',
            'source_audit_sha256': sha(copies['gkt_source_and_core_plan.json']),
            'external_primary_sources': primary['external_sources'],
            'source_audit_local_inputs': primary['source_files_read'],
            'under_specified': primary['under_specified'],
            'kernel_source_sha256': trial['source_sha256_after'],
            'raw_external_hashes_deliberately_null': True,
            'caller_chronology_origin_and_transform_isolation_not_attested': True,
            'S04_S05_approved': False,
        })
        dump(out / 'frozen_test_acceptance.json', {
            **acceptance, 'test_seconds': float(suite.attrib['time']),
            'controller_seconds': trial['elapsed_seconds'],
            'source_snapshots_equal_trial': True, 'source_unchanged_since_trial': True,
            'new_tests_rerun': False, 'optimizer_steps': 0,
            'numeric_positive_dtype': 'CPU_FP64',
            'gkt_complete': False, 'fitted_efficacy': False,
        })
        # git check-ignore chỉ đọc; ghi danh sách trước closure để bundle không đổi sau đó.
        paths = [relative(p) for p in out.iterdir()]
        paths += [relative(out / 'force_add_paths.json')]
        query = subprocess.run(['git', 'check-ignore', '--stdin'], cwd=ROOT,
                               input='\n'.join(paths) + '\n', text=True, capture_output=True, check=False)
        assert query.returncode in (0, 1), query.stderr
        ignored = sorted(query.stdout.splitlines())
        dump(out / 'force_add_paths.json', {
            'scope_vi': 'Danh sách exact ignored bundle paths; chỉ dùng cho parent review/add, chưa git add.',
            'git_check_ignore_exit': query.returncode,
            'ignored_paths_requiring_force_add': ignored,
            'unignored_pack_source': relative(Path(__file__).resolve()),
        })
    verified = verify_evidence_bundle(ROOT / 'research_tracking/runs' / RUN_ID)
    manifest = ROOT / 'research_tracking/runs' / RUN_ID / 'manifest.json'
    print(json.dumps({**verified, 'run_id': RUN_ID,
                      'manifest_sha256': sha(manifest),
                      'copies_verified': len(after), 'selected_links_checked': len(links),
                      'force_add': ignored}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
