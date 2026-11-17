"""Sourcewriter chỉ xuất Developmentfold4, toàn bộ dữ liệu đều tổng hợp."""
import hashlib
import importlib.util
import json
from pathlib import Path

import duckdb
import pytest

from knowledge_tracing.akt.config import DataPaths
from knowledge_tracing.akt.encoding import ExerciseEncoding
from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView, JunyiResearchEncoding
from knowledge_tracing.akt.research_junyi_roles import JunyiResearchRoles
from knowledge_tracing.shared_kt import StableVocabulary


@pytest.fixture
def writer():
    path = Path(__file__).resolve().parents[2]/'scripts/akt/prepare_junyi_outer_source.py'
    spec = importlib.util.spec_from_file_location('prepare_outer_source_test', path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@pytest.fixture
def case(tmp_path):
    source = tmp_path/'source'
    source.mkdir()
    canonical = source/'canonical.parquet'
    assignments = source/'assignments.parquet'
    con = duckdb.connect(config={'threads':'1'})
    con.execute('''CREATE TABLE events(user_id VARCHAR,exercise VARCHAR,time_done BIGINT,
        source_row BIGINT,correct INTEGER,suggested INTEGER)''')
    con.executemany('INSERT INTO events VALUES(?,?,?,?,?,?)', [
        ('train','A',1,1,1,0), ('calib','A',2,2,0,0), ('outer','A',4,4,1,0),
        ('outer','NEW',3,3,0,1), ('heldout','A',5,5,7,0)])
    con.execute('COPY events TO ? (FORMAT PARQUET)', [str(canonical)])
    con.execute('''CREATE TABLE assignment(user_id VARCHAR,fold INTEGER,partition VARCHAR)''')
    con.executemany('INSERT INTO assignment VALUES(?,?,?)', [
        ('train',0,'development'), ('selection',1,'development'), ('calib',2,'development'),
        ('outer',4,'development'), ('heldout',-1,'holdout')])
    con.execute('COPY assignment TO ? (FORMAT PARQUET)', [str(assignments)])
    con.close()
    manifest, split = source/'manifest.json', source/'split.json'
    manifest.write_text('{}'); split.write_text('{}')
    paths = DataPaths(canonical, assignments, manifest, split)
    roles = JunyiResearchRoles(('train',), ('selection',), ('calib',), ('outer',))
    refit = JunyiPhaseView(roles, 'refit_union90', ('selection','train'), roles.identity)
    encoding = JunyiResearchEncoding(ExerciseEncoding(StableVocabulary(('A','B')), {'A':1,'B':1}), refit)
    assets = {variant:dict(encoding=encoding, expected_index_sha256='a'*64,
        index=dict(checkpoint_sha256='b'*64, identity=dict(condition=None if variant=='A0' else 'c'*64)))
        for variant in ('A0','A1','A2','A3')}
    pins = {path.relative_to(tmp_path).as_posix():hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (canonical,assignments,manifest,split)}
    inventory = source/'inventory.json'
    inventory.write_text(json.dumps({'source_sha256':pins}))
    budget = tmp_path/'cache'
    budget.mkdir()
    return dict(paths=paths, assets=assets, inventory=inventory, source_root=tmp_path,
                output=budget/'outer', budget=budget)


def run(writer, case, *, max_seconds=30):
    return writer.prepare_outer_source(case['assets'], case['paths'],
        source_repo_root=case['source_root'], inventory_path=case['inventory'],
        inventory_sha256=hashlib.sha256(case['inventory'].read_bytes()).hexdigest(),
        output_root=case['output'], disk_budget_root=case['budget'],
        expected_targets=2, expected_learners=1, expected_oov_targets=1,
        max_seconds=max_seconds, max_rss_bytes=1024**3, max_disk_bytes=16*1024**2)


def test_only_outer_rows_exported_in_canonical_order(writer, case):
    result = run(writer, case)
    assert result['status'] == 'FULL_OUTER_SOURCE_PREPARED'
    assert result['counts']['targets'] == 2
    assert result['counts']['oov_targets'] == 1
    assert result['counts']['max_learner_events'] == 2
    assert set(result['portable_export_pins']) == {'A0','A1','A2','A3'}
    con = duckdb.connect(config={'threads':'1'})
    rows = con.execute('SELECT user_id,source_row,correct FROM read_parquet(?)',
        [str(case['output']/'canonical.parquet')]).fetchall()
    con.close()
    assert rows == [('outer',3,0), ('outer',4,1)]
    assert result['holdout_events_included'] is False
    assert result['training_performed'] is False
    assert result['resource_contract']['spill_cap_bytes'] == 12*1024**2
    assert result['resource_contract']['disk_scan_interval_seconds'] == 30


@pytest.mark.parametrize('seconds', [float('nan'),float('inf'),True])
def test_nonfinite_or_boolean_wall_cap_rejected(writer, case, seconds):
    with pytest.raises(ValueError, match='resource limits'):
        run(writer, case, max_seconds=seconds)


def test_partial_refit_role_cannot_prepare_outer(writer, case):
    encoding = case['assets']['A0']['encoding']
    partial = JunyiPhaseView(encoding.fit_view.roles, 'refit_union90', ('train',), encoding.fit_view.roles.identity)
    replacement = JunyiResearchEncoding(encoding.native, partial)
    for asset in case['assets'].values():
        asset['encoding'] = replacement
    with pytest.raises(ValueError, match='full refit90'):
        run(writer, case)


@pytest.mark.parametrize('damage', ['duplicate', 'label', 'fold'])
def test_invalid_outer_or_assignment_rejected(writer, case, damage):
    con = duckdb.connect(config={'threads':'1'})
    file = case['paths'].assignments if damage == 'fold' else case['paths'].canonical
    con.execute('CREATE TABLE source AS SELECT * FROM read_parquet(?)', [str(file)])
    if damage == 'duplicate':
        con.execute("INSERT INTO source SELECT * FROM source WHERE user_id='outer' AND source_row=3")
    if damage == 'label':
        con.execute("UPDATE source SET correct=9 WHERE user_id='outer'")
    if damage == 'fold':
        con.execute("UPDATE source SET fold=3 WHERE user_id='outer'")
    con.execute('COPY source TO ? (FORMAT PARQUET)', [str(file)])
    con.close()
    payload = json.loads(case['inventory'].read_text())
    payload['source_sha256'][file.relative_to(case['source_root']).as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
    case['inventory'].write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        run(writer, case)
    assert not (case['output']/'manifest.json').exists()


def test_prepared_source_feeds_real_generic_outer_cache_apis(writer, case, monkeypatch):
    from knowledge_tracing.akt import research_junyi_window_cache as windows
    from knowledge_tracing.akt import research_junyi_graph_cache as graphs
    from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition
    from knowledge_tracing.akt.research_junyi_confidence_binding import JunyiConfidenceBinding
    from knowledge_tracing.akt.research_graph_condition import OperationalEdgeWeight
    from knowledge_tracing.shared_kt import PrerequisiteGraph
    import sys
    before = 'torch' in sys.modules
    assert before is False
    result = run(writer, case)
    encoding = case['assets']['A0']['encoding']
    train = JunyiPhaseView(encoding.fit_view.roles, 'select_train80', ('train',), encoding.fit_view.roles.identity)
    origin = JunyiResearchEncoding(encoding.native, train)
    confidence = JunyiConfidenceBinding(train.identity, origin.identity, 'a'*64,'b'*64,'c'*64,
        (OperationalEdgeWeight('A','B',True,.7,None,.7),))
    for variant, asset in case['assets'].items():
        asset['condition'] = None if variant == 'A0' else JunyiGraphCondition(encoding,
            PrerequisiteGraph.from_edges(('A','B'),(('A','B'),)), 'a'*64, variant=variant,
            confidence=None if variant == 'A1' else confidence, train80_origin=origin)
    monkeypatch.setattr(windows, 'CACHE_BASE', case['budget']/'windows')
    monkeypatch.setattr(graphs, 'CACHE_ROOT', case['budget']/'graphs')
    path = Path(__file__).resolve().parents[2]/'scripts/akt/prepare_junyi_outer_caches.py'
    spec = importlib.util.spec_from_file_location('outer_cache_integration', path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    prepared = DataPaths(**{name:Path(value) for name,value in result['data_paths'].items()})
    pins = {name:hashlib.sha256(getattr(prepared,name).read_bytes()).hexdigest()
            for name in ('canonical_manifest','split_manifest')}
    cached = helper.prepare_outer_caches(case['assets'], prepared, source_pins=pins,
        cache_tag='outer01', receipt_path=case['budget']/'CACHE.json', disk_budget_root=case['budget'],
        max_disk_bytes=16*1024**2, max_seconds=60, max_rss_bytes=1024**3)
    assert cached['windows']['summary']['target_rows'] == 2
    assert cached['oov_targets_recounted'] == 1
    assert all(graph['targets'] == 1 for graph in cached['graphs'].values())
    assert ('torch' in sys.modules) == before
