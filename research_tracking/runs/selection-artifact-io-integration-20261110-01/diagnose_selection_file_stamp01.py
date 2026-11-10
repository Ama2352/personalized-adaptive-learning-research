"""Quan sát tuple stat/fstat trong fixture lỗi, không đổi kết quả kiểm."""
from pathlib import Path
import hashlib
import io
import json
import os
import sys
import tempfile
import threading
import time
import unittest

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
out = prep / 'selection-file-stamp-diagnostic01'
out.mkdir(exist_ok=False)
workspace = out / 'workspace'
workspace.mkdir()
tempfile.tempdir = str(workspace)
assert Path(sys.prefix).resolve() == root / '.venv' and sys.dont_write_bytecode
sys.path[:0] = [str(root / 'src'), str(prep)]
import test_main_selection_file_primitives_candidate01 as tests

timer = threading.Timer(10, lambda: os._exit(124))
timer.daemon = True
timer.start()
module = tests.m
original_stamp, original_need = module.BoundedArtifactReader._stamp, module.need
recent, mismatches = [], []


def observed_stamp(value):
    token = original_stamp(value)
    recent.append(token)
    del recent[:-4]
    return token


def observed_need(ok, message):
    if not ok and message in ('Opened exact file identity', 'Input changed during read'):
        mismatches.append({'message': message, 'recent_stamp_tuples': list(recent)})
    return original_need(ok, message)


log = io.StringIO()
started = time.perf_counter()
try:
    module.BoundedArtifactReader._stamp = staticmethod(observed_stamp)
    module.need = observed_need
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
finally:
    module.BoundedArtifactReader._stamp = staticmethod(original_stamp)
    module.need = original_need
    timer.cancel()
(out / 'unittest.log').write_text(log.getvalue(), encoding='utf-8')
record = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
    elapsed_seconds=time.perf_counter() - started, mismatches=mismatches,
    source_sha256=hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
    scope_vi='Chỉ quan sát stamp trong chín fixture, không thay guard hoặc chạy model.')
(out / 'result.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
