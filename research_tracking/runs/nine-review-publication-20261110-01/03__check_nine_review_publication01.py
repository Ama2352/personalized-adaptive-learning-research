"""Kiểm công bố review thống kê bằng fixtures, không chọn mô hình thật."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
OUT = P / 'nine-review-publication01'
OUT.mkdir(exist_ok=False)
(OUT / 'workspace').mkdir()
tempfile.tempdir = str(OUT / 'workspace')
started = time.perf_counter()
assert Path(sys.prefix).resolve() == ROOT / '.venv' and sys.dont_write_bytecode
blocked = {'torch', 'numpy', 'pandas', 'scipy', 'sklearn', 'modal', 'pyBKT'}


def audit(event, args):
    if ((event == 'import' and str(args[0]).split('.')[0] in blocked)
            or event == 'subprocess.Popen' or event.startswith('socket.')):
        raise RuntimeError('Manufactured statistics publication only')


sys.addaudithook(audit)
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.akt.authorization import gate2_build_hashes

before = gate2_build_hashes()
suite = unittest.TestSuite(unittest.defaultTestLoader.discover(str(ROOT / 'tests/shared_kt'), pattern=name)
    for name in ('test_research_selected_files.py', 'test_research_selected_metadata.py',
                 'test_research_selected_checkpoint.py', 'test_research_selected_rows.py',
                 'test_research_selection_io.py', 'test_research_population.py',
                 'test_research_admission.py', 'test_research_selection.py'))
assert suite.countTestCases() == 78
tests = unittest.TextTestRunner(verbosity=2).run(suite)
assert tests.wasSuccessful() and not tests.skipped
from test_research_selected_files import SelectedFilesTests
case = SelectedFilesTests(methodName='test_publication_readback_and_no_selection_authority')
case.root = OUT / 'manufactured-fixture'
case.root.mkdir()
request, population = case.fixture()
complete_ref = case.publish(request, population)
complete = json.loads((case.root / complete_ref.path).read_bytes())
assert complete['caller_operation_acceptance_required'] and not complete['actual_model_selection']
assert not complete['external_freeze_authority'] and not complete['main_refit_authorized']
assert not (case.root / complete_ref.path).with_name('FAILURE.json').exists()
assert before == gate2_build_hashes() and not blocked.intersection(sys.modules)
inventory = {path.relative_to(ROOT).as_posix(): dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    size_bytes=path.stat().st_size) for path in case.root.rglob('*') if path.is_file()}
(OUT / 'fixture-inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
result = dict(status='ACCEPTED_CACHED_STATISTICS_PUBLICATION_FIXTURES_NOT_MAIN_FREEZE',
    tests=78, failures=0, errors=0, skipped=0, source_before=before, source_after=before,
    source_build_files=len(before), manufactured_complete=asdict(complete_ref),
    fixture_files=len(inventory), real_model_calls=0, actual_model_selection=False,
    external_freeze_authority=False, main_refit_authorized=False, software_gate_requires_refresh=True,
    elapsed_seconds=time.perf_counter()-started)
(OUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('PASS78 tests, cached statistics review published exclusively, no selection/freeze/refit authority.')
