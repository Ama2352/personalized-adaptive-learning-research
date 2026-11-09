"""Áp dụng observer đã qua sáu fixture, chưa chạy panel nghiên cứu."""
from pathlib import Path
import ast
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OUT = PREP / 'native-panel-canonical-apply01'
SOURCE = PREP / 'native_panel_observer_candidate01.py'
TEST = PREP / 'test_native_panel_observer_candidate01.py'
DEST = ROOT / 'src/knowledge_tracing/gam_kt/native_panel_observer.py'
TEST_DEST = ROOT / 'tests/gam_kt/test_native_panel_observer.py'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


source, test = SOURCE.read_bytes(), TEST.read_bytes()
assert sha(source) == 'b54b5f9a0899ec46b3e90d98b283fb34c84adaae5d2f47a581e405962bc936ba'
assert sha(test) == '8f2da30e9dfc299e1608658bec8b64a28b622d5b1e7ac6a3708feea08b62a9d1'
receipt = json.loads((PREP / 'native-panel-pure01/result.json').read_bytes())
assert receipt['status'] == 'ACCEPTED_SIX_MANUFACTURED_PANEL_FIXTURES'
assert receipt['counts'] == dict(tests=6, failures=0, errors=0, skipped=0, expected_failures=0, unexpected_successes=0)
text = test.decode('utf-8')
start = text.index('NAME = "_native_panel_observer_candidate01"')
end = text.index('CONCEPTS = ', start)
text = text[:start] + ('from knowledge_tracing.gam_kt.native_panel_observer import (\n'
    '    NativePanelRecorder as Recorder, PanelObserverError as PanelError,\n)\n') + text[end:]
for line in ['import importlib.util\n', 'from pathlib import Path\n', 'import sys\n']:
    text = text.replace(line, '')
test_output = text.encode('utf-8')
ast.parse(source)
ast.parse(test_output)
assert not OUT.exists() and not DEST.exists() and not TEST_DEST.exists()
OUT.mkdir()
inventory = dict(source_sha256=sha(source), source_test_sha256=sha(test),
    destination=DEST.relative_to(ROOT).as_posix(), destination_test=TEST_DEST.relative_to(ROOT).as_posix(),
    destination_test_sha256=sha(test_output), native_panel_execution_authorized=False,
    change='Recorder exact bytes; test import wiring only and unused imports removed.')
with (OUT / 'inventory_before_copy.json').open('x') as stream:
    json.dump(inventory, stream, indent=2)
for path, content in [(DEST, source), (TEST_DEST, test_output)]:
    with path.open('xb') as stream:
        stream.write(content)
    assert path.read_bytes() == content
with (OUT / 'result.json').open('x') as stream:
    json.dump(dict(applied=True, source_sha256=sha(DEST.read_bytes()),
        test_sha256=sha(TEST_DEST.read_bytes()), canonical_tests_pending=True,
        native_panel_pending=True), stream, indent=2)
print('Applied exact recorder; canonical synthetic test pending')
