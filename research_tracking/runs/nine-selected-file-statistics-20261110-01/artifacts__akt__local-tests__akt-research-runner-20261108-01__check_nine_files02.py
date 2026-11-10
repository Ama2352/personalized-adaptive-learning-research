"""Kiểm tích hợp bằng fixtures file thật nhỏ, không đọc dataset/model thật."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
OUT = P / 'nine-selected-files02'
OUT.mkdir(exist_ok=False)
(OUT / 'workspace').mkdir()
tempfile.tempdir = str(OUT / 'workspace')
started = time.perf_counter()
assert Path(sys.prefix).resolve() == ROOT / '.venv' and sys.dont_write_bytecode
blocked = {'torch', 'numpy', 'pandas', 'scipy', 'sklearn', 'modal', 'pyBKT'}


def audit(event, args):
    if ((event == 'import' and str(args[0]).split('.')[0] in blocked)
            or event == 'subprocess.Popen' or event.startswith('socket.')):
        raise RuntimeError('Manufactured file integration only')


sys.addaudithook(audit)
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.akt.authorization import gate2_build_hashes
from knowledge_tracing.research_selection import SelectionKernelLimits, select_from_common_statistics

before = gate2_build_hashes()
suite = unittest.TestSuite(unittest.defaultTestLoader.discover(str(ROOT / 'tests/shared_kt'), pattern=name)
    for name in ('test_research_selected_files.py', 'test_research_selected_metadata.py',
                 'test_research_selected_checkpoint.py', 'test_research_selected_rows.py',
                 'test_research_selection_io.py', 'test_research_population.py',
                 'test_research_admission.py', 'test_research_selection.py'))
assert suite.countTestCases() == 67
tests = unittest.TextTestRunner(verbosity=2).run(suite)
if not tests.wasSuccessful() or tests.skipped:
    raise RuntimeError('Integration suite failed; keep stdout/stderr and current source')
from test_research_selected_files import SelectedFilesTests
case = SelectedFilesTests(methodName='test_nine_files_to_common_statistics_without_authority')
case.root = OUT / 'manufactured-fixture'
case.root.mkdir()
request, population = case.fixture()
result = case.read(request, population)
stats = result.statistics
global_rng = random.getstate()
kernel = select_from_common_statistics(stats.common_statistics,
    coverage=stats.common_population_coverage,
    limits=SelectionKernelLimits(8, 32, 32, 20000, 200000, 10.))
assert kernel.proposed_winner_id == 'A0' and kernel.replicates == 2000
assert not kernel.external_freeze_authority and random.getstate() == global_rng
assert (stats.full_targets, stats.common_targets, stats.row_checks) == (4, 3, 36)
assert before == gate2_build_hashes() and not blocked.intersection(sys.modules)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
fixture_inventory = {path.relative_to(ROOT).as_posix(): dict(sha256=sha(path), size_bytes=path.stat().st_size)
                     for path in case.root.rglob('*') if path.is_file()}
(OUT / 'fixture-inventory.json').write_text(json.dumps(fixture_inventory, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
payload = dict(status='ACCEPTED_NINE_FILE_STATISTICS_FIXTURES_NOT_RESEARCH_OR_OPERATION_ADMISSION',
    tests=tests.testsRun, failures=len(tests.failures), errors=len(tests.errors), skipped=len(tests.skipped),
    source_before=before, source_after=before, source_build_files=len(before),
    manufactured_statistics=asdict(result), manufactured_kernel=asdict(kernel), fixture_files=len(fixture_inventory),
    real_model_calls=0, actual_model_selection=False, main_file_admission=False, software_gate_requires_refresh=True,
    elapsed_seconds=time.perf_counter()-started)
(OUT / 'result.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('PASS', tests.testsRun, 'tests, manufactured nine-files -> full4/common3/36checks -> frozen2000-draw kernel.')

