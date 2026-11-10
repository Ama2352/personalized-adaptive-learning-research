"""Kiểm canonical và exports đã có, không NN/selection/refit hoặc mạng."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
OUT = P / 'selected-rows-integration01'
OUT.mkdir(exist_ok=False)
(OUT / 'workspace').mkdir()
tempfile.tempdir = str(OUT / 'workspace')
START = time.perf_counter()
assert Path(sys.prefix).resolve() == ROOT / '.venv' and sys.dont_write_bytecode
blocked = {'torch', 'numpy', 'pandas', 'scipy', 'sklearn', 'modal', 'boto3', 'pyBKT'}


def audit(event, values):
    if (event == 'import' and str(values[0]).split('.')[0] in blocked
            or event == 'subprocess.Popen' or event.startswith('socket.')):
        raise RuntimeError('No model runtime/process/network')


sys.addaudithook(audit)
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing import research_admission as admission
from knowledge_tracing.research_selected_rows import decode_selected_claim, normalize_selected_row
from knowledge_tracing.research_selection_io import FileRef, FileReadLimits, BoundedArtifactReader
from knowledge_tracing.akt.authorization import gate2_build_hashes

sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
source_before = gate2_build_hashes()
suite = unittest.TestSuite(unittest.defaultTestLoader.discover(str(ROOT / 'tests/shared_kt'), pattern=name)
    for name in ('test_research_selected_rows.py', 'test_research_selection_io.py', 'test_research_population.py'))
assert suite.countTestCases() == 24
test_result = unittest.TextTestRunner(verbosity=2).run(suite)
assert test_result.wasSuccessful() and not test_result.skipped
expected_file = P / 'main-selection-population-integration02/grade10-main-lifecycle-engineering10x84-20261109-01.json'
expectation = json.loads(expected_file.read_bytes())['expectation']
inputs = {expected_file.relative_to(ROOT).as_posix(): sha(expected_file)}
runs = {'A0': 'experiments/akt/results/main-a0-graph29-continuous-engineering10x84-20261110-01',
        'A1_EXPERT': 'experiments/akt/results/main-a1-expert-engineering10x84-20261110-01',
        'SAKT': 'experiments/sakt/results/sakt-selected-engineering10x84-20261110-03',
        'GKT': 'experiments/gkt/results/gkt-selected-engineering10x84-20261110-01'}
limits = FileReadLimits(2 * 2**20, 32 * 2**20, 12, 1, 2**20, 2 * 2**20,
    16384, 1260, 10000, 16384, 64, 4096, 20.)
summaries = {}
with BoundedArtifactReader(ROOT, limits) as reader:
    for candidate_id, run in runs.items():
        path = ROOT / run / 'selected-claim.json'
        ref = FileRef(path.relative_to(ROOT).as_posix(), sha(path), path.stat().st_size)
        inputs[ref.path] = ref.sha256
        claim = decode_selected_claim(reader.read_json(ref))
        assert claim.candidate_id == candidate_id
        indices = {}
        for kind in ('predictions', 'targets'):
            path = ROOT / run / 'selection' / (kind + '.csv')
            ref = FileRef(path.relative_to(ROOT).as_posix(), sha(path), path.stat().st_size)
            inputs[ref.path] = ref.sha256
            declared = claim.raw_predictions if kind == 'predictions' else claim.targets
            assert (declared.sha256, declared.size_bytes) == (ref.sha256, ref.size_bytes)
            indices[kind] = reader.index_csv(ref, candidate_id=candidate_id, kind=kind)
        predictions, targets = indices['predictions'], indices['targets']
        assert predictions.keys == targets.keys and len(targets.keys) == 84
        full_hash, label_hash = hashlib.sha256(), hashlib.sha256()
        for key in targets.keys:
            raw = predictions.row(key)
            normalized = normalize_selected_row(raw, targets.row(key), claim)
            assert normalized.key == key and normalized.probability == float(raw['probability'])
            full_hash.update(admission._canonical(key.values()))
            label_hash.update(admission._canonical((key.values(), normalized.correct)))
        assert full_hash.hexdigest() == expectation['full_keys_sha256']
        assert label_hash.hexdigest() == expectation['full_keys_labels_sha256']
        summaries[candidate_id] = dict(normalized_rows=84, independent_K_y_match=True,
            binary64_preserved=True, claim_is_declaration_only=True)
    verified = reader.verify_unchanged()
assert gate2_build_hashes() == source_before and all(sha(ROOT / path) == digest for path, digest in inputs.items())
assert not blocked.intersection(sys.modules) and time.perf_counter() - START < 25
result = dict(status='ACCEPTED_ROW_NORMALIZATION_NOT_METADATA_OR_NINE_MODEL_ADMISSION',
    tests=24, failures=0, errors=0, skipped=0, sources_before=source_before, sources_after=source_before,
    inputs_sha256=inputs, exports=summaries, file_reader=verified, source_build_files=len(source_before),
    software_gate_requires_refresh=True, model_calls=0, actual_model_selection=False,
    external_freeze_authority=False, elapsed_seconds=time.perf_counter() - START)
(OUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('PASS24 tests, four claims / 336 normalized rows, independent K/y and binary64 unchanged.')
