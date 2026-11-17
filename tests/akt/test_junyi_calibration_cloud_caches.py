"""Cache calibration theo learner đầy đủ, chỉ fixture và không Torch."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from knowledge_tracing.shared_kt import StableVocabulary, PrerequisiteGraph
from knowledge_tracing.akt.config import DataPaths
from knowledge_tracing.akt.encoding import ExerciseEncoding
from knowledge_tracing.akt.research_junyi_roles import JunyiResearchRoles
from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView, JunyiResearchEncoding
from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition, JunyiGraphPhaseSession
from knowledge_tracing.akt.research_junyi_confidence_binding import JunyiConfidenceBinding
from knowledge_tracing.akt.research_graph_condition import OperationalEdgeWeight
from knowledge_tracing.akt.research_junyi_compact import build_compact_context, build_compact_confidence_context
from knowledge_tracing.akt.research_junyi_graph_cache import GraphContextCache
from knowledge_tracing.akt.research_junyi_window_cache import JunyiWindowCacheSession
from knowledge_tracing.akt.types import KTEvent, LearnerEvents
from knowledge_tracing.akt.windows import iter_windows
from knowledge_tracing.akt import cache_artifacts

SPEC = importlib.util.spec_from_file_location('prepare_cloud_caches',
    Path(__file__).resolve().parents[2] / 'scripts/akt/prepare_junyi_calibration_caches.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


@pytest.fixture
def case(tmp_path, monkeypatch):
    cloud = tmp_path / 'volume'
    cloud.mkdir()
    monkeypatch.setattr(cache_artifacts, 'CLOUD_CACHE_ROOT', cloud)
    root = cache_artifacts.JunyiCacheArtifactRoot(cloud)
    roles = JunyiResearchRoles(('t',), ('s',), ('c1', 'c2'), ('o',))
    train = JunyiPhaseView(roles, 'select_train80', roles.train_users, roles.identity)
    refit = JunyiPhaseView(roles, 'refit_union90', ('s', 't'), roles.identity)
    calibration = JunyiPhaseView(roles, 'calibration_predict', roles.calibration_users, roles.identity)
    native = ExerciseEncoding(StableVocabulary(('A', 'B')), dict(A=1, B=1))
    encoding = JunyiResearchEncoding(native, refit)
    origin = JunyiResearchEncoding(native, train)
    confidence = JunyiConfidenceBinding(train.identity, origin.identity, 'a'*64, 'b'*64,
        'c'*64, (OperationalEdgeWeight('A', 'B', True, .7, None, .7),))
    assets = {}
    for variant in ('A0', 'A1', 'A2', 'A3'):
        condition = None if variant == 'A0' else JunyiGraphCondition(encoding,
            PrerequisiteGraph.from_edges(('A', 'B'), (('A', 'B'),)), 'a'*64,
            variant=variant, confidence=None if variant == 'A1' else confidence, train80_origin=origin)
        assets[variant] = dict(encoding=encoding, calibration=calibration, condition=condition)
    learners = tuple(LearnerEvents(user, 0, tuple(KTEvent(user, ('A','B')[i%2], i+1,
        offset+i+1, i%2, 0, 0) for i in range(count)))
        for user, count, offset in (('c1', 305, 0), ('c2', 3, 305)))
    records = tuple(record for learner in learners for record in iter_windows(learner, native, training=False))
    import knowledge_tracing.akt.research_junyi_data as data
    monkeypatch.setattr(data, 'iter_junyi_research_windows', lambda *args: iter(records))
    source = tmp_path / 'input'
    source.mkdir()
    canonical, assignments = source/'canonical.parquet', source/'assignments.parquet'
    canonical.write_bytes(b'canonical fixture')
    assignments.write_bytes(b'assignments fixture')
    manifest, splits = source/'manifest.json', source/'splits.json'
    manifest.write_text(json.dumps(dict(outputs={p.name:dict(bytes=p.stat().st_size,
        sha256=module._sha(p)) for p in (canonical, assignments)})))
    splits.write_text('{}')
    paths = DataPaths(canonical, assignments, manifest, splits)
    pins = dict(canonical_manifest=module._sha(manifest), split_manifest=module._sha(splits))
    population = dict(source_pins=pins, targets=308, phase_identity=calibration.identity,
        roles_identity=roles.identity, population_sha256='d'*64, prefix_keys_sha256='e'*64)
    population['identity'] = identity(population)
    return dict(cloud=cloud, artifact_root=root, assets=assets, paths=paths, source_pins=pins,
                population=population, records=records)


def run(case):
    return module.prepare_calibration_caches(case['assets'], case['paths'], case['source_pins'],
        case['population'], output_root=case['cloud']/'cache01', artifact_root=case['artifact_root'],
        max_seconds=60, max_rss_bytes=2*1024**3, volume_commit=lambda: None)


def test_full_calibration_cache_all_variants_roundtrip(case):
    before = 'torch' in sys.modules
    receipt = run(case)
    assert receipt['windows']['summary']['target_rows'] == 308
    assert receipt['windows']['summary']['learners'] == 2
    assert receipt['population'] == case['population']
    baseline = case['assets']['A0']
    window = receipt['windows']
    session = JunyiWindowCacheSession(Path(window['path']), baseline['calibration'], baseline['encoding'],
        receipt['source_data_sha256'], 308, window['manifest_sha256'],
        admission_receipt=Path(window['admission_path']),
        expected_admission_sha256=window['admission_sha256'], artifact_root=case['artifact_root'])
    restored = tuple(session.iter_windows())
    assert all(not hasattr(record, 'targets') for record in restored)
    assert [r.window_id for r in restored] == [r.window_id for r in case['records']]
    for variant, pin in receipt['graphs'].items():
        asset = case['assets'][variant]
        phase = JunyiGraphPhaseSession(asset['condition'], asset['calibration'])
        reader = GraphContextCache.open(Path(pin['path']), pin['sha256'], phase,
            dataset_sha256=receipt['dataset_sha256'], window_manifest_sha256=window['manifest_sha256'],
            artifact_root=case['artifact_root'])
        build = build_compact_context if variant == 'A1' else build_compact_confidence_context
        assert reader.batch(restored, phase) == build(restored, phase)
    assert ('torch' in sys.modules) == before


@pytest.mark.parametrize('kind', ['population', 'source', 'foreign_root'])
def test_changed_population_source_or_root_rejected_before_build(case, kind):
    if kind == 'population':
        case['population']['targets'] += 1
    if kind == 'source':
        case['paths'].canonical.write_bytes(b'changed')
    if kind == 'foreign_root':
        case['artifact_root'] = cache_artifacts.JunyiCacheArtifactRoot(case['cloud'].parent)
    with pytest.raises(ValueError):
        run(case)
    assert not (case['cloud']/'cache01').exists()


def test_cloud_root_opt_in_required(case):
    from knowledge_tracing.akt.research_junyi_window_cache import _owned_root
    with pytest.raises(ValueError, match='Owned'):
        _owned_root(case['cloud']/'cache01')
    assert case['artifact_root'].validate(case['cloud']/'cache01') == case['cloud']/'cache01'


def test_mount_alias_resolves_only_trusted_root(case, tmp_path, monkeypatch):
    mount = tmp_path/'mount'
    try:
        mount.symlink_to(case['cloud'], target_is_directory=True)
    except OSError:
        pytest.skip('Windows không cấp quyền tạo symbolic link trong fixture')
    monkeypatch.setattr(cache_artifacts, 'CLOUD_CACHE_ROOT', mount)
    assert case['artifact_root'].validate(case['cloud']/'cache01') == case['cloud']/'cache01'
    alias = case['cloud']/'alias'
    alias.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match='alias'):
        case['artifact_root'].validate(alias/'escaped')


def test_modified_cpu_admission_rejected(case):
    receipt = run(case)
    window = receipt['windows']
    admission = Path(window['admission_path'])
    admission.write_text('{}')
    baseline = case['assets']['A0']
    with pytest.raises(ValueError, match='SHA'):
        JunyiWindowCacheSession(Path(window['path']), baseline['calibration'], baseline['encoding'],
            receipt['source_data_sha256'], 308, window['manifest_sha256'],
            admission_receipt=admission, expected_admission_sha256=window['admission_sha256'],
            artifact_root=case['artifact_root'])


def test_portable_metadata_inspection_pins_all_variants(tmp_path, monkeypatch):
    import knowledge_tracing.akt.research_junyi_inference as inference
    calls = []
    def inspect(path, **kwargs):
        calls.append((path, kwargs['expected_index_sha256']))
        return dict(index=dict(identity=dict(variant=path.name)))
    monkeypatch.setattr(inference, 'inspect_cpu_refit_export', inspect)
    indexes = {variant:dict(path=tmp_path/variant/'MODEL_INDEX.json', sha256='a'*64)
               for variant in ('A0', 'A1', 'A2', 'A3')}
    result = module.inspect_calibration_exports(indexes, run_id='unit', budget=object())
    assert set(result) == set(indexes) and len(calls) == 4
    indexes['A0']['path'] = tmp_path/'A1/MODEL_INDEX.json'
    with pytest.raises(ValueError, match='variant'):
        module.inspect_calibration_exports(indexes, run_id='unit', budget=object())
