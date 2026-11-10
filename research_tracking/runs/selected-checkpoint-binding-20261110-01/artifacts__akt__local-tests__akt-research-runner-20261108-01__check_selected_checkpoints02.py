"""Kiểm schema checkpoint thật đã có, không tensor, model hoặc quyền admission."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
OUT = P / 'selected-checkpoint-integration02'
OUT.mkdir(exist_ok=False)
(OUT / 'workspace').mkdir()
tempfile.tempdir = str(OUT / 'workspace')
started = time.perf_counter()
assert Path(sys.prefix).resolve() == ROOT / '.venv' and sys.dont_write_bytecode
blocked = {'torch', 'numpy', 'pandas', 'scipy', 'sklearn', 'modal', 'pyBKT'}


def audit(event, args):
    if ((event == 'import' and str(args[0]).split('.')[0] in blocked)
            or event.startswith('socket.') or event == 'subprocess.Popen'):
        raise RuntimeError('Pure cached metadata only')


sys.addaudithook(audit)
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.research_selected_rows import decode_selected_claim
from knowledge_tracing.research_selected_checkpoint import validate_selected_checkpoint
from knowledge_tracing.research_selection_io import BoundedArtifactReader, FileReadLimits, FileRef
from knowledge_tracing.akt.authorization import gate2_build_hashes

before = gate2_build_hashes()
suite = unittest.TestSuite(unittest.defaultTestLoader.discover(str(ROOT / 'tests/shared_kt'), pattern=name)
    for name in ('test_research_selected_checkpoint.py', 'test_research_selected_rows.py',
                 'test_research_selection_io.py', 'test_research_population.py'))
assert suite.countTestCases() == 32
tests = unittest.TextTestRunner(verbosity=2).run(suite)
assert tests.wasSuccessful() and not tests.skipped
runs = {'A0': ('akt', 'main-a0-graph29-continuous-engineering10x84-20261110-01', 'checkpoints/epoch-4'),
        'A1_EXPERT': ('akt', 'main-a1-expert-engineering10x84-20261110-01', 'checkpoints/epoch-4'),
        'SAKT': ('sakt', 'sakt-selected-engineering10x84-20261110-03', 'epoch-1'),
        'GKT': ('gkt', 'gkt-selected-engineering10x84-20261110-01', 'epoch-6')}
pins, identity_pins = {}, {}
for candidate, (family, name, checkpoint) in runs.items():
    directory = ROOT / 'experiments' / family / 'results' / name
    paths = {'claim': directory / 'selected-claim.json',
             'complete': directory / checkpoint / 'COMPLETE.json',
             'metadata': directory / checkpoint / 'metadata.json', 'state': directory / checkpoint / 'state.pt'}
    pins[candidate] = {}
    for kind, path in paths.items():
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        pins[candidate][kind] = FileRef(path.relative_to(ROOT).as_posix(), digest, path.stat().st_size)
    # Rehearsal pins from actual metadata; this is NOT an independent reviewed
    # provenance request or an operation receipt. No final admission is claimed.
    identity_pins[candidate] = json.loads(paths['metadata'].read_bytes())['identity']
(OUT / 'preflight-pins.json').write_text(json.dumps(dict(refs={candidate: {kind: ref.__dict__
    for kind, ref in refs.items()} for candidate, refs in pins.items()}, identities=identity_pins,
    scope='ENGINEERING_REHEARSAL_NOT_REVIEWED_ADMISSION_REQUEST'), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
limits = FileReadLimits(64 * 2**20, 512 * 2**20, 16, 1, 2**20, 2**20,
    16384, 1260, 10000, 16384, 64, 4096, 25.)
accepted = {}
with BoundedArtifactReader(ROOT, limits) as reader:
    for candidate, refs in pins.items():
        claim = decode_selected_claim(reader.read_json(refs['claim']))
        complete = reader.read_json(refs['complete'])
        metadata = reader.read_json(refs['metadata'])
        reader.verify_file(refs['state'])
        validate_selected_checkpoint(claim=claim, complete=complete, metadata=metadata,
            complete_ref=refs['complete'], metadata_ref=refs['metadata'], checkpoint_ref=refs['state'],
            expected_identity=identity_pins[candidate])
        accepted[candidate] = dict(selected_epoch=claim.selected_epoch,
            completed_fit_epochs=claim.complete_fit_epochs, checkpoint_bytes=refs['state'].size_bytes,
            tensor_deserialized=False)
    verified = reader.verify_unchanged()
assert before == gate2_build_hashes() and not blocked.intersection(sys.modules)
assert time.perf_counter() - started < 40
result = dict(status='ACCEPTED_CHECKPOINT_BINDING_REHEARSAL_NOT_PRODUCER_ADMISSION', tests=32,
    source_before=before, source_after=before, source_build_files=len(before), checkpoints=accepted,
    inputs_file='preflight-pins.json', reader=verified, elapsed_seconds=time.perf_counter() - started,
    model_calls=0, actual_model_selection=False, external_freeze_authority=False,
    reviewed_operation_receipts=False, software_gate_requires_refresh=True)
(OUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('PASS32 tests / four actual checkpoint schemas and streaming byte checks, no tensor load.')

