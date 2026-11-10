"""Lượt synthetic1260, tối đa128MiB RSS/45giây reader, không model thật."""
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
OUT = P / 'nine-file-scaling02'
OUT.mkdir(exist_ok=False)
(OUT / 'workspace').mkdir()
tempfile.tempdir = str(OUT / 'workspace')
started = time.perf_counter()
assert Path(sys.prefix).resolve() == ROOT / '.venv' and sys.dont_write_bytecode
blocked = {'torch', 'numpy', 'pandas', 'scipy', 'sklearn', 'modal', 'pyBKT'}


def audit(event, args):
    if ((event == 'import' and str(args[0]).split('.')[0] in blocked)
            or event == 'subprocess.Popen' or event.startswith('socket.')):
        raise RuntimeError('Synthetic file scaling only')


sys.addaudithook(audit)
sys.path.insert(0, str(ROOT / 'src'))
import psutil
from knowledge_tracing.akt.authorization import gate2_build_hashes
from knowledge_tracing.research_admission import AdmissionLimits
from knowledge_tracing.research_selected_files import read_nine_selected_statistics
from knowledge_tracing.research_selection_io import FileReadLimits

before = gate2_build_hashes()
process = psutil.Process()
available_before = psutil.virtual_memory().available
assert available_before >= 256 * 2**20, 'Require256MiB system headroom; no model RAM floor change'
suite = unittest.TestSuite(unittest.defaultTestLoader.discover(str(ROOT / 'tests/shared_kt'), pattern=name)
    for name in ('test_research_selected_files.py', 'test_research_selected_metadata.py',
                 'test_research_selected_checkpoint.py', 'test_research_selected_rows.py',
                 'test_research_selection_io.py', 'test_research_population.py',
                 'test_research_admission.py', 'test_research_selection.py'))
assert suite.countTestCases() == 71
tests = unittest.TextTestRunner(verbosity=2).run(suite)
assert tests.wasSuccessful() and not tests.skipped
from test_research_selected_files import SelectedFilesTests
case = SelectedFilesTests(methodName='test_fixture_scales_without_changing_original_population')
case.root = OUT / 'manufactured-fixture'
case.root.mkdir()
fixture_start = time.perf_counter()
request, population = case.fixture(learner_targets=tuple((f'learner-{index}', 210) for index in range(6)))
request_ref = case.json('request.json', request)
fixture_seconds = time.perf_counter()-fixture_start
fixture_files = list(path for path in case.root.rglob('*') if path.is_file())
fixture_bytes = sum(path.stat().st_size for path in fixture_files)
assert fixture_bytes <= 16 * 2**20
io_limits = FileReadLimits(4 * 2**20, 128 * 2**20, 256, 18, 2**20, 4 * 2**20,
    16384, 1260, 24000, 16384, 64, 4096, 45.)
admission_limits = AdmissionLimits(6, 1260, 210, 11340, 45.)
read_started = time.perf_counter()
try:
    result = read_nine_selected_statistics(case.root, request_ref=request_ref, population=population,
        io_limits=io_limits, admission_limits=admission_limits)
except BaseException as error:
    (OUT / 'failure.json').write_text(json.dumps(dict(type=type(error).__name__, message=str(error),
        elapsed_seconds=time.perf_counter()-read_started, fixture_bytes=fixture_bytes,
        io_limits=asdict(io_limits), admission_limits=asdict(admission_limits)), indent=2) + '\n')
    raise
read_seconds = time.perf_counter()-read_started
memory = process.memory_info()
peak = memory.peak_wset
assert peak <= 128 * 2**20 and psutil.virtual_memory().available >= 256 * 2**20
assert (result.statistics.full_targets, result.statistics.common_targets, result.statistics.row_checks,
        result.index_entries) == (1260, 1259, 11340, 22680)
assert before == gate2_build_hashes() and not blocked.intersection(sys.modules)
inventory = {path.relative_to(ROOT).as_posix(): dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    size_bytes=path.stat().st_size) for path in fixture_files}
(OUT / 'fixture-inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
payload = dict(status='ACCEPTED_SYNTHETIC1260_FILE_SCALING_NOT_TRAINING_THROUGHPUT',
    tests=71, failures=0, errors=0, skipped=0, source_before=before, source_after=before,
    source_build_files=len(before), full_targets=1260, common_targets=1259, learners=6,
    row_checks=11340, index_entries=22680, fixture_files=len(fixture_files), fixture_bytes=fixture_bytes,
    fixture_seconds=fixture_seconds, file_read_seconds=read_seconds, reader_bytes=result.bytes_read,
    reader_seconds=result.elapsed_seconds, peak_worker_rss_bytes=peak,
    available_ram_before=available_before, available_ram_after=psutil.virtual_memory().available,
    io_limits=asdict(io_limits), admission_limits=asdict(admission_limits),
    real_model_calls=0, actual_model_selection=False, main_file_admission=False,
    training_throughput_measured=False, elapsed_seconds=time.perf_counter()-started)
(OUT / 'result.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('PASS71 / synthetic1260,', round(read_seconds, 3), 'reader seconds,', peak, 'peak RSS bytes.')

