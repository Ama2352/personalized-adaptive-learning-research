"""Đóng hồ sơ đã nghiệm thu, inventory file nhỏ và ghim nguồn/artifact lớn trên D."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    destination = HERE / 'MANIFEST.json'
    assert not destination.exists(), 'Bundle đã đóng, bằng chứng tiếp nối dùng hồ sơ mới'
    assert json.loads((HERE / 'final-acceptance.json').read_text())['status'] == 'PASS_FINAL_A1_ACCEPTANCE'
    assert json.loads((HERE / 'budget-settlement.json').read_text())['status'] == 'CLOSED_BOUNDED_TRANCHES'
    for path in HERE.glob('*.py'):
        ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
    state_path = HERE / 'STATE.json'
    state = json.loads(state_path.read_text())
    assert state['h100_active'] is False and state['artifacts_verified_on_d'] is True
    state['bundle_closed'] = True
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    request = json.loads((HERE / 'h100-request09.json').read_text())
    receipt_path = ROOT / 'experiments/akt/results/modal-junyi-a1-b128-h100-20261113-09/receipt.json'
    receipt = json.loads(receipt_path.read_text())
    files = {path.relative_to(HERE).as_posix(): {'bytes': path.stat().st_size, 'sha256': sha(path)}
             for path in sorted(HERE.rglob('*')) if path.is_file() and '__pycache__' not in path.parts}
    result = {'status': 'CLOSED_VERIFIED_A1_SELECTED_FIT', 'date': '2026-11-13',
              'inputs': request['archives'], 'source_build_sha256': request['source_build_sha256'],
              'files': files,
              'large_artifacts': {'receipt': receipt_path.relative_to(ROOT).as_posix(),
                                  'receipt_sha256': sha(receipt_path),
                                  'archive_path': 'experiments/akt/results/modal-junyi-a1-b128-h100-20261113-09/artifacts.zip',
                                  'archive_sha256': receipt['archive_sha256'], 'archive_bytes': receipt['archive_bytes']},
              'limitations_vi': ['Selected-fit A1, chưa refit/calibration/đánh giá độc lập.',
                                 'GPU-Util toàn khoảng mẫu khoảng27,7%, còn chờ CPU.',
                                 'CPU preparation/postprocessing ngoài GPU là việc tiếp theo.']}
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'files': len(files)}))


if __name__ == '__main__':
    main()
