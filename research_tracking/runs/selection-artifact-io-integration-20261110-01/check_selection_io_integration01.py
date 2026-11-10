"""Kiểm IO canonical bằng fixture và tám CSV đã có, không chạy hoặc chọn model."""
from pathlib import Path
import hashlib
import json
import os
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
OUT = P / 'selection-io-integration01'
OUT.mkdir(exist_ok=False)
(OUT / 'workspace').mkdir()
tempfile.tempdir = str(OUT / 'workspace')
START = time.perf_counter()
assert Path(sys.prefix).resolve() == ROOT / '.venv' and sys.dont_write_bytecode
blocked = {'torch', 'numpy', 'pandas', 'scipy', 'sklearn', 'modal', 'boto3', 'pyBKT'}


def audit(event, values):
    if (event == 'import' and str(values[0]).split('.')[0] in blocked
            or event == 'subprocess.Popen' or event.startswith('socket.')):
        raise RuntimeError('No scientific runtime/process/network')


sys.addaudithook(audit)
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing import research_admission as admission
from knowledge_tracing.research_selection_io import FileRef, FileReadLimits, BoundedArtifactReader
from knowledge_tracing.akt.authorization import gate2_build_hashes

sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
source_before = gate2_build_hashes()
assert len(source_before) == 187
suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests/shared_kt'), pattern='test_research_selection_io.py')
assert suite.countTestCases() == 10
test_result = unittest.TextTestRunner(verbosity=2).run(suite)
assert test_result.wasSuccessful() and not test_result.skipped
expected_file = P / 'main-selection-population-integration02/grade10-main-lifecycle-engineering10x84-20261109-01.json'
expectation = json.loads(expected_file.read_bytes())['expectation']
inputs = {expected_file.relative_to(ROOT).as_posix(): sha(expected_file)}
runs = {'A0': 'experiments/akt/results/main-a0-graph29-continuous-engineering10x84-20261110-01',
        'A1_EXPERT': 'experiments/akt/results/main-a1-expert-engineering10x84-20261110-01',
        'SAKT': 'experiments/sakt/results/sakt-selected-engineering10x84-20261110-03',
        'GKT': 'experiments/gkt/results/gkt-selected-engineering10x84-20261110-01'}
limits = FileReadLimits(2 * 2**20, 16 * 2**20, 8, 1, 2**20, 2 * 2**20,
    16384, 1260, 10000, 16384, 32, 4096, 10.)
summaries = {}
with BoundedArtifactReader(ROOT, limits) as reader:
    for candidate_id, run in runs.items():
        indices = {}
        for kind in ('predictions', 'targets'):
            path = ROOT / run / 'selection' / (kind + '.csv')
            ref = FileRef(path.relative_to(ROOT).as_posix(), sha(path), path.stat().st_size)
            inputs[ref.path] = ref.sha256
            indices[kind] = reader.index_csv(ref, candidate_id=candidate_id, kind=kind)
        predictions, targets = indices['predictions'], indices['targets']
        assert predictions.keys == targets.keys and len(targets.keys) == 84
        full_hash, label_hash = hashlib.sha256(), hashlib.sha256()
        for key in targets.keys:
            truth, prediction = targets.row(key), predictions.row(key)
            assert truth['correct'] in ('0', '1')
            assert prediction['probability'] != '' and prediction['support_reason'] == 'supported'
            full_hash.update(admission._canonical(key.values()))
            label_hash.update(admission._canonical((key.values(), int(truth['correct']))))
        assert full_hash.hexdigest() == expectation['full_keys_sha256']
        assert label_hash.hexdigest() == expectation['full_keys_labels_sha256']
        summaries[candidate_id] = dict(targets=84, independently_matched_population=True,
            headers={'predictions': predictions.header, 'targets': targets.header})
    verified = reader.verify_unchanged()
assert gate2_build_hashes() == source_before and all(sha(ROOT / path) == digest for path, digest in inputs.items())
assert not blocked.intersection(sys.modules) and time.perf_counter() - START < 18
result = dict(status='ACCEPTED_CANONICAL_IO_FOUR_EXPORTS_NOT_NINE_MODEL_ADMISSION',
    tests=10, failures=0, errors=0, skipped=0, source_before=source_before, source_after=source_before,
    inputs_sha256=inputs, exports=summaries, file_reader=verified,
    source_build_files=187, software_gate_requires_refresh=True, model_calls=0,
    actual_model_selection=False, external_freeze_authority=False, elapsed_seconds=time.perf_counter() - START)
(OUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('PASS10 canonical fixtures, actual8CSV/fourmodels full84K/y match independent expectation, source187 stable.')
