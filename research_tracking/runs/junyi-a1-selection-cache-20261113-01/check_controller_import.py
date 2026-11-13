"""Kiểm import controller tại đường dẫn tự gắn /root của Modal, không cấp tài nguyên."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def check(name):
    path = HERE / name
    source = path.read_text(encoding='utf-8-sig')
    source = source.replace('from pathlib import Path',
        'from pathlib import PurePosixPath\nclass Path(PurePosixPath):\n    def resolve(self):\n        return self')
    namespace = {'__name__': 'modal_import_probe', '__file__': '/root/resume_controller.py'}
    try:
        exec(compile(source, '/root/resume_controller.py', 'exec'), namespace)
    except IndexError:
        return {'status': 'FAIL_INDEX_ERROR_AT_MODAL_IMPORT', 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    assert namespace['ROOT'].as_posix() == '/'
    assert callable(namespace['remote_probe'])
    return {'status': 'PASS_MODAL_IMPORT_PATH', 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


if __name__ == '__main__':
    old = check('resume_controller08_failed.py')
    current = check('resume_controller.py')
    assert old['status'] == 'FAIL_INDEX_ERROR_AT_MODAL_IMPORT'
    assert current['status'] == 'PASS_MODAL_IMPORT_PATH'
    result = {'status': 'PASS_REGRESSION_REPRODUCED_AND_FIXED', 'failed08': old, 'current': current,
              'scope': 'Giả lập ngữ nghĩa đường dẫn POSIX tại import, không gọi Modal hoặc training.'}
    (HERE / 'controller-import-regression.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
