"""Kiểm metadata hiện có, không model hoặc cấp quyền chọn/refit."""
from pathlib import Path
from dataclasses import asdict
import hashlib
import json
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
OUT = P / 'selected-metadata-integration02'
OUT.mkdir(exist_ok=False)
(OUT / 'workspace').mkdir()
tempfile.tempdir = str(OUT / 'workspace')
started = time.perf_counter()
assert Path(sys.prefix).resolve() == ROOT / '.venv' and sys.dont_write_bytecode
blocked = {'torch', 'numpy', 'pandas', 'scipy', 'sklearn', 'modal', 'pyBKT'}


def audit(event, args):
    if ((event == 'import' and str(args[0]).split('.')[0] in blocked)
            or event.startswith('socket.') or event == 'subprocess.Popen'):
        raise RuntimeError('Cached metadata only')


sys.addaudithook(audit)
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing import research_admission as admission
from knowledge_tracing.research_selected_metadata import validate_selected_metadata, DOCUMENT_ROLES, CLAIM_ARTIFACTS
from knowledge_tracing.research_selection_io import BoundedArtifactReader, FileReadLimits, FileRef
from knowledge_tracing.akt.authorization import gate2_build_hashes


def ref(path):
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return FileRef(path.relative_to(ROOT).as_posix(), digest, path.stat().st_size)


before = gate2_build_hashes()
suite = unittest.TestSuite(unittest.defaultTestLoader.discover(str(ROOT / 'tests/shared_kt'), pattern=name)
    for name in ('test_research_selected_metadata.py', 'test_research_selected_checkpoint.py',
                 'test_research_selected_rows.py', 'test_research_selection_io.py', 'test_research_population.py'))
assert suite.countTestCases() == 39
tests = unittest.TextTestRunner(verbosity=2).run(suite)
assert tests.wasSuccessful() and not tests.skipped
runs = {'A0': ('akt', 'main-a0-graph29-continuous-engineering10x84-20261110-01', 'checkpoints/epoch-4'),
        'A1_EXPERT': ('akt', 'main-a1-expert-engineering10x84-20261110-01', 'checkpoints/epoch-4'),
        'SAKT': ('sakt', 'sakt-selected-engineering10x84-20261110-03', 'epoch-1'),
        'GKT': ('gkt', 'gkt-selected-engineering10x84-20261110-01', 'epoch-6')}
expectation_file = P / 'main-selection-population-integration02/grade10-main-lifecycle-engineering10x84-20261109-01.json'
expectation = json.loads(expectation_file.read_bytes())['expectation']
population = admission.PopulationExpectation(context=admission.MainSelectionContext(**expectation['context']),
    **{name: value for name, value in expectation.items() if name != 'context'})
runtime_candidates = [ROOT / 'artifacts/akt/preflight' / name for name in (
    'runtime-schema2-main177-20261109-01.json', 'runtime-v2.json', 'runtime.json')]
summaries, pins = {}, {}
limits = FileReadLimits(64 * 2**20, 1024 * 2**20, 1024, 1, 2**20, 2**20,
    16384, 1260, 10000, 16384, 64, 4096, 30.)
with BoundedArtifactReader(ROOT, limits) as reader:
    for candidate, (family, name, checkpoint) in runs.items():
        directory = ROOT / 'experiments' / family / 'results' / name
        paths = dict(invocation='invocation.json', complete='COMPLETE.json', terminal='selected-terminal.json',
            claim='selected-claim.json', coverage='selection/coverage.json',
            checkpoint_complete=checkpoint + '/COMPLETE.json', checkpoint_metadata=checkpoint + '/metadata.json',
            checkpoint=checkpoint + '/state.pt', predictions='selection/predictions.csv',
            targets='selection/targets.csv', events='events.jsonl')
        refs = {kind: ref(directory / filename) for kind, filename in paths.items()}
        documents = {kind: reader.read_json(refs[kind]) for kind in DOCUMENT_ROLES}
        wire, identity = documents['claim'], documents['invocation']['identity']
        runtime_matches = [path for path in runtime_candidates if path.is_file() and ref(path).sha256 == wire['runtime_sha256']]
        assert runtime_matches
        refs['runtime'] = ref(runtime_matches[0])
        # Invocation contains exact spec object. Raw enclosing file is pinned
        # separately from semantic config/spec identity, never equate the hashes.
        refs['config_or_spec'] = refs['invocation']
        hashes = identity['native_evidence']['build_hashes'] if family == 'akt' else identity['source_files']
        source_refs = {}
        for logical, expected_hash in hashes.items():
            source = ref(ROOT / logical)
            assert source.sha256 == expected_hash, ('Historical source snapshot needed', candidate, logical)
            reader.verify_file(source)
            source_refs[logical] = source
        for pinned in refs.values():
            reader.verify_file(pinned)
        claim = validate_selected_metadata(documents=documents, artifact_refs=refs,
            expected_claim_binding={key: value for key, value in wire.items() if key not in CLAIM_ARTIFACTS},
            expected_checkpoint_identity=documents['checkpoint_metadata']['identity'],
            producer_source_files=source_refs, population=population)
        summaries[candidate] = dict(full_targets=claim.full_targets, selected_epoch=claim.selected_epoch,
            verified_historical_source_files=len(source_refs), metadata_checked=True)
        pins[candidate] = dict(refs={key: asdict(value) for key, value in refs.items()},
            sources={key: asdict(value) for key, value in source_refs.items()})
    verified = reader.verify_unchanged()
assert before == gate2_build_hashes() and not blocked.intersection(sys.modules)
result = dict(status='ACCEPTED_PRODUCER_METADATA_REHEARSAL_NOT_OPERATION_ADMISSION', tests=39,
    source_before=before, source_after=before, source_build_files=len(before), producers=summaries,
    inputs=pins, reader=verified, elapsed_seconds=time.perf_counter()-started, model_calls=0,
    operation_receipts_reviewed=False, expected_claim_pins_independent=False,
    actual_model_selection=False, external_freeze_authority=False, software_gate_requires_refresh=True)
(OUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('PASS39 tests / four producer metadata rehearsals; source bytes checked, no operation admission.')

