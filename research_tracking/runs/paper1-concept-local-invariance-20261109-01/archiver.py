"""Đóng proof/fixture đã chạy; dry và close không chạy lại tests hoặc simulator."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PREFIX = PREP.relative_to(ROOT).as_posix() + '/'
RUN = 'paper1-concept-local-invariance-20261109-01'
DESTINATION = ROOT / 'research_tracking/runs' / RUN
FILES = (
    ('test_concept_local_invariance.py', 'tests/paper1_pdf/test_concept_local_invariance.py', 'e38a72290e51b2e9b9bd418829bbe2344b85604ce3f6e8ebad5f6bd845a70780'),
    ('test_candidate.py', PREFIX+'test_paper1_concept_local_invariance_candidate01.py', 'dfa6b07572a76fcf53e48d7815f957bda40c00755ea44cb3d5fc705f2767104f'),
    ('test_review_plan.md', PREFIX+'PAPER1_CONCEPT_LOCAL_INVARIANCE_TEST_REVIEW_PLAN01.md', 'b22bf71a5808a5f7e9760673a6fffdfb9e1394105f04053a3af04e1da3054bc2'),
    ('prepare_tests.py', PREFIX+'prepare_paper1_invariance_tests01.py', '6b4c72cfbd89d42e555895ae9ae480d212e4063d22701bd500290f54f2564215'),
    ('apply_receipt.json', PREFIX+'paper1_invariance_test_apply01.json', '212136014c007a1e3824dd96c5349b7e386b5b4570a4bc3d98c839efc7681579'),
    ('run_tests.py', PREFIX+'run_paper1_invariance_tests01.py', 'e8e0e8770de6c54675a9ed3fd70e06287e97f777e52a110ab48b6731fc9e718e'),
    ('result.json', PREFIX+'paper1-invariance-tests01/result.json', '2790d7245b1ee548c63d994f6bc4335ae07d1cadb1f344dc34ce9e0f7c2659aa'),
    ('stdout.log', PREFIX+'paper1-invariance-tests01/stdout.log', 'f94217bc2b5df8ff47dfa08ac033951fe5e8442f2827f043dc1f0560b7f0947e'),
    ('stderr.log', PREFIX+'paper1-invariance-tests01/stderr.log', '4b8955400bd4dde947b4d3f84a27fcf4190de8cd9ebef20b4036b4906f201f41'),
    ('next_evidence_source_review.md', PREFIX+'RQ2_NEXT_EVIDENCE_SOURCE_REVIEW01.md', '4f547c0fd3ed9040e1b7b0e5b95e67da5c9e565f09f79a40adb2f49c94d57ead'),
    ('report.md', PREFIX+'PAPER1_CONCEPT_LOCAL_INVARIANCE_REPORT_DRAFT01.md', '196ad75444382d485b17bb6bb1c65ea33c92005eed8982cb2226801003f1390f'),
)
REFERENCES = {
    'src/knowledge_tracing/paper1_pdf/__init__.py': '0a9e0faa63680643c3526ce13135de2c033f105d82bf5ea8e7a55afdc2df7df7',
    'src/knowledge_tracing/paper1_pdf/simulator.py': 'b73057bc0523742fe9f8d84f543e305652c032973facbd327437331affb3d37f',
    'src/knowledge_tracing/paper1_pdf/domain.py': 'c37e32420c90f98289b9e21c2e6ea9197324f77a2452b7faae79f8c60985fb18',
    'src/knowledge_tracing/paper1_pdf/episode.py': 'e01fc94656e206101a6ab6dfc960eb24ac331a677f3711c2b4561fbcd840b471',
    'src/knowledge_tracing/paper1_pdf/seeded_episode.py': '7c7ac305cd49fd79f5768173198705be7fa32586114acf5871950c7540dda1b2',
    'src/knowledge_tracing/simulator_bridge.py': 'b29105acd8de84b060ca27573bb7f7cf8e85599a4596e50e4a21ab63c82329d2',
    'src/knowledge_tracing/evidence.py': '414e3d834c46d081c7d9c05beff17a3e2d9c479a0e121394aabe321929235e49',
    'tests/paper1_pdf/test_simulator.py': '0810c04847a0461bcb2ed8ddf5cb17fda13ab90dca1709adc7bc16ee847c8a03',
    'tests/paper1_pdf/test_domain.py': '5443ff36d437c4ed9a758089a0114e6a5b4da1396a137ec5b7ec5e4b16e9afdb',
    'tests/paper1_pdf/test_reentry_mechanism.py': '365b062098ea2edcb5ac320b469d593024fd577a7801c7a4b9fd35eff7b86074',
    'tests/paper1_pdf/test_episode.py': 'd0bf6e052d9e2618b0b2d3ecf729164da68d99fc49a42e4c6dc0eadf6b4db1c0',
    'tests/paper1_pdf/test_seeded_episode.py': 'f97674bc764988271c091a00560bf31f2afba2f951b72819a150ae64a83b48e2',
    'paper1/Paper1_RIVF_2026_Graph_vs_Policy_Adaptive_Sequencing.pdf': '984e2f825968c212ca7e76db23a4c9501659ed880ecff6dce437590ad49167f4',
    'research_tracking/runs/paper1-seeded-domain-smoke-engineering-20261109-01/manifest.json': 'a12e409be45a3c900154b2f7f1d1118bd2e3cda59a66476d6cb32b886da85131',
    'research_tracking/runs/paper1-seeded-domain-smoke-engineering-20261109-01/scientific__result.json': 'cbe892e42cdcf969b4c1c7e8ef5b7f8462d66f0a72d39ed9c07b990c01704e0b',
}
GENERATED = ('README.md', 'execution.log', 'copy_inventory.json', 'source_checks.json', 'closure_review.json')
NEW_METHODS = {
    'test_capped_latent_can_change_aggregate_gain_at_same_horizon',
    'test_complete_dags_preserve_local_stopping_states_but_allow_a_b_a',
    'test_complete_local_prefixes_include_nontrivial_wrong_feedback',
    'test_finite_horizon_preserves_overlapping_local_prefix_not_allocation',
    'test_isolated_concept_matches_complete_interleavings_through_item_and_k_changes',
    'test_without_clipped_updates_fixed_feedback_count_gives_twelve_n',
}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def safe_file(relative, cap=262144):
    need(type(relative) is str and '\\' not in relative and '\t' not in relative
         and '\n' not in relative and '\r' not in relative, 'Đường dẫn relative POSIX bắt buộc')
    value = ROOT / relative
    need(not Path(relative).is_absolute() and '..' not in Path(relative).parts, 'Không thoát workspace')
    for path in (value, *value.parents):
        if path == ROOT:
            break
        need(not path.is_symlink() and not getattr(path.lstat(), 'st_file_attributes', 0) & 0x400,
             'Không theo symlink/junction/reparse point')
    need(value.resolve().is_relative_to(ROOT) and value.is_file()
         and value.stat().st_size <= cap, 'Input phải là file nhỏ trong workspace')
    return value


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory():
    copies = {}
    own = Path(__file__).relative_to(ROOT).as_posix()
    rows = (*FILES, ('archiver.py', own, sha(Path(__file__))))
    for alias, relative, expected in rows:
        need(re.fullmatch(r'[A-Za-z0-9_.-]+', alias) and alias not in copies, 'Alias duy nhất')
        need(re.fullmatch(r'[a-f0-9]{64}', expected), 'SHA256 đúng64hex')
        source = safe_file(relative)
        need(sha(source) == expected, 'Source SHA '+relative)
        copies[alias] = dict(source=relative, sha256=expected, bytes=source.stat().st_size)
    need(sum(row['bytes'] for row in copies.values()) <= 524288, 'Tổng nguồn copy≤512KiB')
    for relative, expected in REFERENCES.items():
        path = safe_file(relative, cap=8388608)
        need(sha(path) == expected, 'Reference SHA '+relative)
    return copies


def validate_actual(copies):
    result = json.loads(safe_file(copies['result.json']['source']).read_text(encoding='utf-8'))
    observed = result['counts']
    counts = dict(tests=91, failures=0, errors=0, skipped=0, expected_failures=0, unexpected_successes=0)
    need(result['status'] == 'ACCEPTED91_PAPER1_CASES_WITH6_LOCAL_INVARIANCE_FIXTURES'
         and type(result['returncode']) is int and result['returncode'] == 0
         and result['timed_out'] is False and result['whole_cap_seconds'] == 30
         and 0 < result['elapsed_seconds'] < 30, 'Actual terminal/cap bắt buộc')
    need(observed['accepted'] is True and observed['counts'] == counts
         and observed['scientific_modules_absent'] is True and observed['denied'] == [], 'Actual91/0FES và child guards')
    ids = observed['collected_ids']
    need(len(ids) == len(set(ids)) == 91 and ids == observed['started_ids'] == observed['completed_ids'],
         '91ID exact collected/started/completed')
    new_ids = [name for name in ids if name.startswith('test_concept_local_invariance.')]
    need(new_ids == observed['new_ids'] and len(new_ids) == 6
         and {name.rsplit('.', 1)[1] for name in new_ids} == NEW_METHODS, 'Exact sáu fixture mới')
    before = result['source_before']
    need(before == result['source_after'] and len(before) == 11, 'Actual11source trước/sau')
    expected = {name: value for name, value in REFERENCES.items()
                if name.startswith('src/knowledge_tracing/paper1_pdf/') or name.startswith('tests/paper1_pdf/')}
    expected[copies['test_concept_local_invariance.py']['source']] = copies['test_concept_local_invariance.py']['sha256']
    need(before == expected, 'Exact tested11source không thiếu/thêm')
    stdout = safe_file(copies['stdout.log']['source']).read_text(encoding='utf-8')
    need(json.loads(stdout.splitlines()[-1]) == observed, 'Raw stdout khớp counts receipt')
    stderr = safe_file(copies['stderr.log']['source']).read_text(encoding='utf-8')
    need('Ran 91 tests in ' in stderr and stderr.rstrip().endswith('OK'), 'Raw unittest terminal')
    applied = json.loads(safe_file(copies['apply_receipt.json']['source']).read_text(encoding='utf-8'))
    need(applied['candidate_sha256'] == copies['test_candidate.py']['sha256']
         and applied['test_sha256'] == copies['test_concept_local_invariance.py']['sha256']
         and applied['runner_sha256'] == copies['run_tests.py']['sha256']
         and applied['source_pins'] == 11 and applied['expected_tests'] == 91 and applied['new_tests'] == 6,
         'Apply receipt giữ riêng candidate/applied source')
    candidate = safe_file(copies['test_candidate.py']['source']).read_text(encoding='utf-8')
    converted = candidate.replace('Fixtures dựng tay cho mệnh đề có điều kiện, chưa chạy test hoặc matrix.',
                                  'Fixtures dựng tay cho bất biến concept-local có điều kiện và các ranh giới.')
    converted = converted.replace('A nonempty comparison, not vacuous disjoint prefixes.',
                                  'Prefix chung có dữ liệu, không chỉ so hai prefix rỗng.')
    need(converted == safe_file(copies['test_concept_local_invariance.py']['source']).read_text(encoding='utf-8'),
         'Delta candidate chỉ docstring/comment đã review')
    need(result['new_fixture_methods'] == 6 and result['static_new_fixture_upper_bounds'] == dict(
        episode_calls=13, feedback_horizon_sum=464, extra_ready_only_controllers=1), 'Giữ static bounds riêng measured counts')
    return result


def write_json(path, payload):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--dry', action='store_true')
    modes.add_argument('--close', action='store_true')
    parser.add_argument('--dry-file', required=True)
    parser.add_argument('--dry-sha256')
    parser.add_argument('--approval-reference')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT/'.venv', 'Chỉ dùng repository .venv')
    need(not DESTINATION.exists(), 'Run mới độc quyền, không overwrite/retry')
    for parent in (DESTINATION.parent, DESTINATION.parent.parent):
        need(parent.is_dir() and not parent.is_symlink()
             and not getattr(parent.lstat(), 'st_file_attributes', 0) & 0x400, 'Run parent phải là thư mục thật')
    before = inventory()
    result = validate_actual(before)
    outputs = sorted((*before, *GENERATED))
    dry = dict(status='DRY_VERIFIED_INPUTS_NOT_CLOSED', run_id=RUN, copies=before,
               references=REFERENCES, outputs_excluding_manifest=outputs,
               output_count_excluding_manifest=len(outputs), actual_tests=91, new_methods=6,
               static_new_fixture_upper_bounds=result['static_new_fixture_upper_bounds'],
               tests_rerun=False, scientific_matrix_executed=False)
    dry_relative = Path(args.dry_file)
    need(not dry_relative.is_absolute() and '..' not in dry_relative.parts, 'Dry path relative workspace')
    dry_path = ROOT/dry_relative
    need(dry_path.parent.resolve() == PREP and not dry_path.is_symlink(), 'Dry file chỉ thuộc P')
    if args.dry:
        need(not dry_path.exists(), 'Dry mới, không overwrite')
        need(inventory() == before, 'Source drift lúc dry')
        write_json(dry_path, dry)
        print(json.dumps(dict(status=dry['status'], dry_sha256=sha(dry_path), copies=len(before),
                              outputs=len(outputs)), ensure_ascii=False))
        return
    need(type(args.dry_sha256) is str and re.fullmatch(r'[a-f0-9]{64}', args.dry_sha256)
         and type(args.approval_reference) is str and 1 <= len(args.approval_reference) <= 256,
         'Close cần exact dry SHA và ROOT review reference')
    safe_file(dry_path.relative_to(ROOT).as_posix())
    need(sha(dry_path) == args.dry_sha256 and json.loads(dry_path.read_text(encoding='utf-8')) == dry,
         'Exact approved dry không đổi input/membership')
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    note = ('# Bất biến quỹ đạo cục bộ có điều kiện của Paper1\n\n'
            'Proof nguồn và6fixture xác định đã chạy trong91tests/0FES,5.624195799988229s/30. '
            'Điều kiện cả hai nhánh complete là thiết yếu. FiniteH/cap và uncapped control được giữ.\n\n'
            '13episodes/464feedback là static upper bound của6fixture, không actual interaction ledger. '
            'Witness US42/domain28 tham chiếu SHA riêng; không matrix/independent learner N/PDF contradiction/RQ completion.\n\n'
            'report.md giữ bytes canonical candidate trước closure. Bản canonical khi công bố ở '
            '../../reports/paper1_concept_local_invariance_20261109.md. Closure thật xem manifest completed.\n')
    sources = [ROOT/row['source'] for row in before.values()] + [ROOT/name for name in REFERENCES] + [dry_path]
    with record_evidence_run(ROOT, RUN, metadata=dict(kind='PAPER1_CONDITIONAL_LOCAL_TRAJECTORY_INVARIANCE',
        tests=91, new_fixture_methods=6, test_elapsed_seconds=result['elapsed_seconds'],
        static_new_fixture_upper_bounds=result['static_new_fixture_upper_bounds'],
        empirical_matrix_executed=False, new_independent_learners=0), sources=sources, note=note) as out:
        copied = {}
        for alias, row in before.items():
            source = safe_file(row['source'])
            raw = source.read_bytes()
            need(hashlib.sha256(raw).hexdigest() == row['sha256'], 'SHA trước copy')
            with (out/alias).open('xb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            need(sha(out/alias) == sha(source) == row['sha256']
                 and (out/alias).stat().st_size == row['bytes'], 'Copy source trước/sau/readback')
            copied[alias] = dict(row, copy_sha256=sha(out/alias), source_after_sha256=sha(source))
        need(inventory() == before, 'Tất cả source/ref sau copy không đổi')
        write_json(out/'copy_inventory.json', dict(before=before, after=copied, unchanged=True))
        write_json(out/'source_checks.json', dict(tested_before=result['source_before'],
            tested_after=result['source_after'], current_references=REFERENCES, tests_rerun=False))
        write_json(out/'closure_review.json', dict(dry_relative=dry_path.relative_to(ROOT).as_posix(),
            dry_sha256=args.dry_sha256, approval_reference=args.approval_reference,
            scope='ROOT review của archive, không grant methodology/fit/matrix'))
        need(sorted(path.name for path in out.iterdir() if path.name != 'manifest.json') == outputs,
             'Exact membership trước closure')
    verification = verify_evidence_bundle(DESTINATION)
    need(verification['artifacts'] == len(outputs) and inventory() == before,
         'Closed count và source/ref không đổi')
    manifest = json.loads((DESTINATION/'manifest.json').read_text(encoding='utf-8'))
    need(set(manifest['outputs_sha256']) == set(outputs), 'Manifest output inventory exact')
    print(json.dumps(dict(verification=verification, manifest_sha256=sha(DESTINATION/'manifest.json'))))


if __name__ == '__main__':
    main()
