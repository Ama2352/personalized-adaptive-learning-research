"""Đóng bằng chứng cơ chế đã chạy, dry chỉ kiểm hash/count, không chạy test."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
WORK = Path(__file__).resolve().parent
RUN = 'paper1-reentry-mechanism-20261109-01'
PREP = WORK.relative_to(ROOT).as_posix()+'/'
FILES = (
    ('analytic_note.md', PREP+'PAPER1_ZERO_REENTRY_ANALYTIC01.md', 'f296133c4b40eddaa0c0fff22ade830d92d78b6cd4f3fe4ee2a2d58e6701e847'),
    ('test_reentry_mechanism.py', 'tests/paper1_pdf/test_reentry_mechanism.py', '365b062098ea2edcb5ac320b469d593024fd577a7801c7a4b9fd35eff7b86074'),
    ('run_paper1_reentry_tests01.py', PREP+'run_paper1_reentry_tests01.py', 'a46594694b6e4de0f4bcc07e5bf0e6cd4246aa22ed4d260296e4dfd6ecebb793'),
    ('result.json', PREP+'paper1-reentry-mechanism-tests01/result.json', 'b59b4a1384ce8c97ebab03e0e27935788e11f8ba475cb63d6cafeda82c88deab'),
    ('stdout.log', PREP+'paper1-reentry-mechanism-tests01/stdout.log', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
    ('stderr.log', PREP+'paper1-reentry-mechanism-tests01/stderr.log', '7b260d887add9240ddbc01bd207c60f532cad896a1ec103d742f3e4618346982'),
    ('report_draft.md', PREP+'PAPER1_REENTRY_MECHANISM_REPORT_DRAFT01.md', '0f268cd971d43b3b980d58d42b035ec29352312061c7c488cfbf29833d3b9a21'),
)
REFERENCES = {
    'src/knowledge_tracing/paper1_pdf/simulator.py': 'b73057bc0523742fe9f8d84f543e305652c032973facbd327437331affb3d37f',
    'src/knowledge_tracing/paper1_pdf/__init__.py': '0a9e0faa63680643c3526ce13135de2c033f105d82bf5ea8e7a55afdc2df7df7',
    'src/knowledge_tracing/evidence.py': '414e3d834c46d081c7d9c05beff17a3e2d9c479a0e121394aabe321929235e49',
    'paper1/Paper1_RIVF_2026_Graph_vs_Policy_Adaptive_Sequencing.pdf': '984e2f825968c212ca7e76db23a4c9501659ed880ecff6dce437590ad49167f4',
    'docs/thesis_recovery/evidence/paper1.txt': 'b6d2d4a518a0b40f27c695bdde3ca624ce16ee976cb59151b15b85cee11eda85',
}
GENERATED = ('README.md', 'execution.log', 'copy_inventory.json', 'source_checks.json')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory():
    rows = (*FILES, ('archiver.py', Path(__file__).relative_to(ROOT).as_posix(), sha(Path(__file__))))
    result = {}
    for alias, relative, expected in rows:
        source = ROOT/relative
        need(source.is_file() and not source.is_symlink() and sha(source) == expected, 'source SHA '+relative)
        result[alias] = dict(source=relative, sha256=expected, bytes=source.stat().st_size)
    for relative, expected in REFERENCES.items():
        need(sha(ROOT/relative) == expected, 'reference SHA '+relative)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry', action='store_true')
    args = parser.parse_args()
    need(Path(sys.prefix).resolve() == ROOT/'.venv', 'Repository .venv required')
    need(not (ROOT/'research_tracking/runs'/RUN).exists(), 'exclusive new run required')
    before = inventory()
    result = json.loads((WORK/'paper1-reentry-mechanism-tests01/result.json').read_text(encoding='utf-8'))
    need(result['status'] == 'ACCEPTED_FOUR_REENTRY_MECHANISM_FIXTURES' and result['tests'] == 4
         and result['returncode'] == 0 and result['timeout'] is False
         and 0 <= result['elapsed_seconds'] < result['cap_seconds'] == 30, 'actual four-test receipt required')
    need(result['source_before'] == result['source_after'], 'test source drift')
    for relative, expected in result['source_before'].items():
        need(sha(ROOT/relative) == expected, 'current tested source drift')
    outputs = sorted((*before, *GENERATED))
    dry = dict(status='DRY_INPUTS_VERIFIED_NOT_CLOSED', run_id=RUN, copies=len(before),
               outputs_excluding_manifest=len(outputs), outputs=outputs, inventory=before,
               references=REFERENCES, source_checks='current SHA match', tests_rerun=False)
    if args.dry:
        print(json.dumps(dry, ensure_ascii=False, indent=2))
        return
    with (WORK/'paper1_reentry_copy_inventory_before01.json').open('x', encoding='utf-8') as stream:
        json.dump(dry, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    note = ('# Cơ chế không quay lại chương theo PDF Paper1\n\n'
            'Chứng minh điều kiện đủ cho DAG nội chương và bốn fixture đã đạt. '
            'Phản ví dụ liên chương vẫn có chapter quotient DAG. '
            'Không chạy matrix, world hoặc tái lập số liệu PDF; không kết luận lợi ích học tập.\n\n'
            'report_draft.md và analytic_note.md giữ nguyên trạng thái, đường dẫn và wording trước chạy. '
            'result.json + stderr.log ghi kết quả actual sau đó. Đây là hai thời điểm bằng chứng khác nhau.\n')
    sources = list(dict.fromkeys([ROOT/row['source'] for row in before.values()]+[ROOT/p for p in REFERENCES]))
    with record_evidence_run(ROOT, RUN, metadata=dict(kind='PAPER1_REENTRY_MECHANISM_DIAGNOSTIC',
        tests=4, test_elapsed_seconds=result['elapsed_seconds'], reproduction_matrix_completed=False,
        instructional_benefit_claimed=False), sources=sources, note=note) as out:
        copied = {}
        for alias, row in before.items():
            source = ROOT/row['source']
            raw = source.read_bytes()
            need(hashlib.sha256(raw).hexdigest() == row['sha256'], 'input changed before copy')
            with (out/alias).open('xb') as stream:
                stream.write(raw)
            need(sha(out/alias) == sha(source) == row['sha256'], 'copy/input post-SHA mismatch')
            need((out/alias).stat().st_size == row['bytes'], 'copy size mismatch')
            copied[alias] = dict(row, copy_sha256=sha(out/alias), source_after_sha256=sha(source))
        need(inventory() == before, 'full selected input inventory changed')
        (out/'copy_inventory.json').write_text(json.dumps(copied, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        (out/'source_checks.json').write_text(json.dumps(dict(tested_before=result['source_before'],
            tested_after=result['source_after'], current_verified=True, references=REFERENCES), indent=2)+'\n', encoding='utf-8')
        need(sorted(path.name for path in out.iterdir() if path.name != 'manifest.json') == outputs, 'exact output membership')
    verification = verify_evidence_bundle(ROOT/'research_tracking/runs'/RUN)
    need(verification['artifacts'] == len(outputs), 'exact closed output count')
    print(json.dumps(dict(verification=verification, manifest_sha256=sha(ROOT/'research_tracking/runs'/RUN/'manifest.json'))))


if __name__ == '__main__':
    main()
