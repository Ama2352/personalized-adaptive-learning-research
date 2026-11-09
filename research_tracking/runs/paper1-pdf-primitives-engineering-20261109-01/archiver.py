"""Đóng evidence synthetic PDF primitives đã chạy, không rerun tests hoặc simulator."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
WORK = Path(__file__).resolve().parent
RUN = 'paper1-pdf-primitives-engineering-20261109-01'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

if __name__ == '__main__':
    if Path(sys.prefix).resolve() != ROOT/'.venv':
        raise ValueError('Repository .venv required')
    result = json.loads((WORK/'paper1-pdf-primitives-test03/result.json').read_text(encoding='utf-8'))
    assert result['status'] == 'ACCEPTED_SYNTHETIC_PRIMITIVES' and result['tests'] == 26
    assert result['source_before'] == result['source_after']
    copies = {Path(name).name: ROOT/name for name in result['source_before']}
    for name in ('run_paper1_pdf_tests01.py', 'run_paper1_pdf_tests02.py', 'run_paper1_pdf_tests03.py', 'PAPER1_PDF_IMPLEMENTATION_SPEC01.md', 'paper1_pdf_before_pending_fix_inventory.json', 'PAPER1_PDF_ROOT_REVIEW01.md'):
        copies[name] = WORK/name
    copies['archiver.py'] = Path(__file__).resolve()
    for source in WORK.glob('paper1_pdf_before_pending_fix__*'):
        copies[source.name] = source
    for attempt in ('01', '02', '03'):
        for name in ('stdout.log', 'stderr.log', 'result.json'):
            copies['attempt'+attempt+'__'+name] = WORK/('paper1-pdf-primitives-test'+attempt)/name
    before = {alias: dict(source=path.relative_to(ROOT).as_posix(), sha256=digest(path), bytes=path.stat().st_size)
              for alias, path in copies.items()}
    for name, pin in result['source_before'].items():
        assert digest(ROOT/name) == pin
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
    note = ('# Kiểm quy tắc mô phỏng theo PDF Paper1\n\n'
            'Nguồn chuẩn là PDF theo D37. Module riêng giữ nguồn notebook và kết quả kế thừa. '
            '25unittests nhỏ đạt ở attempt02. Peer review sau đó yêu cầu bind nguyên prediction ban đầu khi observe. Attempt03 kiểm26ca sau sửa consistency này, cap30giây. '
            'Attempt01 không import được package do thiếu đường src, giữ đủ logs. '
            'Bộ kiểm dùng fixture dựng tay, chưa chạy matrix, B0, unlock hoặc profile generator. '
            'Không có kết quả tái lập số liệu PDF hoặc nghiệm thu RQ từ các kiểm kỹ thuật này.\n')
    with record_evidence_run(ROOT, RUN, metadata=dict(kind='PAPER1_PDF_PRIMITIVES_ENGINEERING', tests=26,
            reproduction_matrix_completed=False), sources=list(copies.values()), note=note) as output:
        for alias, path in copies.items():
            assert digest(path) == before[alias]['sha256']
            (output/alias).write_bytes(path.read_bytes())
            assert digest(path) == digest(output/alias) == before[alias]['sha256']
        (output/'copy_inventory.json').write_text(json.dumps(before, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(verify_evidence_bundle(ROOT/'research_tracking/runs'/RUN), ensure_ascii=False))
