"""CPUcacheouter dùng API gốc, tinyfixtures và không Torch."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from test_junyi_calibration_cloud_caches import case as calibration_case
from knowledge_tracing.akt import research_junyi_data as data
from knowledge_tracing.akt import research_junyi_window_cache as windows
from knowledge_tracing.akt import research_junyi_graph_cache as graphs
from knowledge_tracing.akt.types import KTEvent, LearnerEvents, UnseenTarget
from knowledge_tracing.akt.windows import iter_windows


@pytest.fixture
def module():
    path = Path(__file__).resolve().parents[2]/'scripts/akt/prepare_junyi_outer_caches.py'
    spec = importlib.util.spec_from_file_location('prepare_outer_cache_test', path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@pytest.fixture
def case(calibration_case, monkeypatch, tmp_path):
    case = calibration_case
    baseline = case['assets']['A0']
    roles = baseline['calibration'].roles
    outer = data.JunyiPhaseView(roles, 'outer_evaluation', roles.outer_validation_users, roles.identity)
    learner = LearnerEvents('o', 4, tuple(KTEvent('o', item, i+1, i+1, i%2, 0, 4)
        for i, item in enumerate(('A', 'NEW', 'B', 'A'))))
    records = list(iter_windows(learner, baseline['encoding'].native, training=False))
    monkeypatch.setattr(data, 'iter_junyi_research_windows', lambda *args: iter(records))
    monkeypatch.setattr(windows, 'CACHE_BASE', case['cloud']/'windows')
    monkeypatch.setattr(graphs, 'CACHE_ROOT', case['cloud']/'graphs')
    manifest = json.loads(case['paths'].canonical_manifest.read_text())
    manifest.update(status='FULL_OUTER_SOURCE_PREPARED', purpose='JUNYI_REFIT90_OUTER_EVALUATION_SOURCE',
        phase_identity=outer.identity, roles_identity=roles.identity,
        encoding_identity=baseline['encoding'].identity, counts=dict(targets=4, learners=1, oov_targets=1))
    case['paths'].canonical_manifest.write_text(json.dumps(manifest))
    pins = dict(case['source_pins'])
    pins['canonical_manifest'] = hashlib.sha256(case['paths'].canonical_manifest.read_bytes()).hexdigest()
    return case, outer, records, pins


def run(module, case, *, max_seconds=60):
    values, _, _, pins = case
    return module.prepare_outer_caches(values['assets'], values['paths'], source_pins=pins,
        cache_tag='outer01', receipt_path=values['cloud']/'OUTER_RECEIPT.json',
        disk_budget_root=values['cloud'], max_disk_bytes=16*1024**2,
        max_seconds=max_seconds, max_rss_bytes=1024**3)


def test_full_outer_cache_keeps_oov_and_three_graphs_exclude_oov(module, case):
    before = 'torch' in sys.modules
    receipt = run(module, case)
    assert receipt['phase'] == 'outer_evaluation'
    assert receipt['windows']['summary']['target_rows'] == 4
    assert receipt['windows']['summary']['unseen_targets'] == 1
    assert receipt['oov_targets_recounted'] == 1
    assert set(receipt['graphs']) == {'A1', 'A2', 'A3'}
    assert all(row['targets'] == 3 for row in receipt['graphs'].values())
    assert ('torch' in sys.modules) == before


@pytest.mark.parametrize('damage', ['calibration_phase', 'oov_count', 'source_sha'])
def test_phase_count_or_source_mismatch_cannot_publish(module, case, damage):
    values, _, _, pins = case
    path = values['paths'].canonical_manifest
    manifest = json.loads(path.read_text())
    if damage == 'calibration_phase':
        manifest['status'] = 'FULL_CALIBRATION10_SOURCE_PREPARED'
    if damage == 'oov_count':
        manifest['counts']['oov_targets'] = 0
    if damage == 'source_sha':
        manifest['outputs'][values['paths'].canonical.name]['sha256'] = '9'*64
    path.write_text(json.dumps(manifest))
    pins['canonical_manifest'] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError):
        run(module, case)
    assert not (values['cloud']/'OUTER_RECEIPT.json').exists()


@pytest.mark.parametrize('seconds', [float('nan'),float('inf'),True])
def test_bad_wall_caps_rejected_before_writing(module, case, seconds):
    with pytest.raises(ValueError, match='CPU limits'):
        run(module, case, max_seconds=seconds)


def test_partial_refit_role_rejected(module, case):
    values, _, _, _ = case
    encoding = values['assets']['A0']['encoding']
    partial = data.JunyiPhaseView(encoding.fit_view.roles, 'refit_union90', ('t',), encoding.fit_view.roles.identity)
    for asset in values['assets'].values():
        asset['encoding'] = data.JunyiResearchEncoding(encoding.native, partial)
    with pytest.raises(ValueError, match='refit90'):
        run(module, case)
