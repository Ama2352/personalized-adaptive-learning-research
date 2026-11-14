"""Bộ Colab phải đủ fixture và không mang outputs notebook lịch sử."""

import ast
import hashlib
import json
from pathlib import Path
import runpy

import pytest


def test_bundle_contains_current_test_dependencies_and_source_only_notebooks():
    collect = runpy.run_path('scripts/akt/build_colab_bundle.py')['bundle_contents']
    contents, transforms = collect()
    for name in ('scripts/akt/refresh_gate2.py','scripts/research/run_cpu_diagnostics.py',
                 'experiments/akt/modal_budget_guard.py',
                 'experiments/akt/junyi_staged_io.py','experiments/akt/modal_junyi_staged.py',
                 'experiments/akt/modal_junyi_refit.py',
                 'src/knowledge_tracing/paper2_reference.py',
                 'experiments/akt/configs/simulator-research-corpus01.json',
                 'tests/akt/fixtures/legacy_config_before_simulator_research.py.txt'):
        assert name in contents
    assert 'requirements-akt.lock.txt' in contents
    contract_files = runpy.run_path('scripts/akt/build_colab_bundle.py')['RESEARCH_CONTRACT_FILES']
    assert len(contract_files) == 8
    assert {name for name in contents if name.startswith('docs/')} == set(contract_files)
    assert all(contents[name] == Path(name).read_bytes() for name in contract_files)
    assert not any(name.startswith(('dataset/','artifacts/')) or '/results/' in name for name in contents)
    notebook_names = [name for name in contents if name.endswith('.ipynb')]
    assert len(notebook_names) == 3
    for name in notebook_names:
        copied = json.loads(contents[name])
        assert all(not cell.get('outputs') and cell.get('execution_count') is None
                   for cell in copied['cells'] if cell['cell_type'] == 'code')
        if name not in transforms:
            assert contents[name] == Path(name).read_bytes()
    for name, metadata in transforms.items():
        original_bytes = Path(name).read_bytes()
        assert hashlib.sha256(original_bytes).hexdigest() == metadata['original_sha256']
        original, copied = json.loads(original_bytes), json.loads(contents[name])
        assert [cell['source'] for cell in original['cells']] == [cell['source'] for cell in copied['cells']]
        assert all(not cell.get('outputs') and cell.get('execution_count') is None
                   for cell in copied['cells'] if cell['cell_type']=='code')


def constants(path):
    result = {}
    for node in ast.parse(Path(path).read_bytes(), filename=path).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                result[node.targets[0].id] = node.value.value
    return result


def test_graph_runtime_contract_paths_and_adopted_ids_are_in_local_inventory():
    contents, _ = runpy.run_path('scripts/akt/build_colab_bundle.py')['bundle_contents']()
    condition = constants('src/knowledge_tracing/akt/research_graph_condition.py')
    checkpoint = constants('src/knowledge_tracing/akt/research_graph_checkpoint.py')
    admission = constants('src/knowledge_tracing/research_admission.py')
    stage = constants('src/knowledge_tracing/akt/research_main_stage.py')
    expected = {
        checkpoint['PROTOCOL21_PATH']: admission['PROTOCOL21'],
        condition['RECIPE_PATH']: condition['RECIPE_SHA256'],
        'docs/thesis_recovery/22_A0_RESEARCH_LIFECYCLE_CONTRACT.md': stage['PROTOCOL22'],
        'docs/thesis_recovery/23_TRAINING_MATRIX_ACCOUNTING_V1.md': stage['ACCOUNTING23'],
        'docs/thesis_recovery/EXPERIMENT_ALLOCATION_V1.json': admission['ALLOCATION'],
    }
    assert len(expected) == 5
    assert all(hashlib.sha256(contents[name]).hexdigest() == digest for name,digest in expected.items())


def synthetic_collector(tmp_path, monkeypatch, missing=None):
    namespace = runpy.run_path('scripts/akt/build_colab_bundle.py')
    collect = namespace['bundle_contents']
    contracts = namespace['RESEARCH_CONTRACT_FILES']
    paper = 'paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20'
    names = [*contracts, 'requirements-akt.in', 'requirements-akt.lock.txt',
        'tests/akt/fixtures/legacy_config_before_simulator_research.py.txt',
        *(f'experiments/akt/configs/{n}.json' for n in ('smoke','pilot','fold0','simulator-research-corpus01')),
        'experiments/akt/modal_budget_guard.py',
        'experiments/akt/junyi_staged_io.py','experiments/akt/modal_junyi_staged.py',
        'experiments/akt/modal_junyi_refit.py',
        'paper1/AdaptiveEngineSimulation_Enhanced.ipynb',
        *(paper+'/source/'+n+'.ipynb' for n in ('adaptive_lms_bkt_gam_graph_gam_kt_research_ready_v2_1',
                                               'junyi_cycle_corrected_ablation_confirmation')),
        *(paper+'/data/simulator_inputs/'+n+'.csv' for n in
          ('nodes','edges','edges_baseline','question_bank','concept_to_chapter_map'))]
    for name in names:
        if name == missing:
            continue
        path = tmp_path/name; path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == '.ipynb':
            path.write_text(json.dumps(dict(metadata={'preserve_original':True}, cells=[
                dict(cell_type='code', source=['x = 1\n'], metadata={'secret_output':True},
                     outputs=[{'text':'old output'}], execution_count=9)])), encoding='utf-8')
        else:
            path.write_bytes(('PUBLIC_FIXTURE '+name+'\r\n').encode())
    # Unselected documents must never enter the fixed dependency closure.
    extra = tmp_path/'docs/unselected-local-note.md'; extra.parent.mkdir(exist_ok=True)
    extra.write_bytes(b'UNSELECTED_LOCAL_ONLY')
    monkeypatch.setitem(collect.__globals__, 'ROOT', tmp_path)
    return collect, contracts


def test_fixed_docs_raw_bytes_and_notebook_transform_without_zip(tmp_path_factory, monkeypatch):
    tmp_path = tmp_path_factory.mktemp('b')  # Bound Windows ancestor length for Paper2 fixture filenames.
    collect, contracts = synthetic_collector(tmp_path, monkeypatch)
    contents, transforms = collect()
    assert {name for name in contents if name.startswith('docs/')} == set(contracts)
    assert all(contents[name] == (tmp_path/name).read_bytes() for name in contracts)
    assert not any(b'UNSELECTED_LOCAL_ONLY' in raw for raw in contents.values())
    assert len(transforms) == 3
    for name, metadata in transforms.items():
        original = (tmp_path/name).read_bytes()
        copied = json.loads(contents[name])
        assert metadata == dict(original_sha256=hashlib.sha256(original).hexdigest(),
            transform='strip notebook outputs/execution metadata in bundle copy')
        assert json.loads(original)['cells'][0]['outputs']  # Original bytes untouched.
        assert copied['metadata'] == {} and copied['cells'][0]['metadata'] == {}
        assert copied['cells'][0]['source'] == ['x = 1\n']
        assert copied['cells'][0]['outputs'] == [] and copied['cells'][0]['execution_count'] is None
    assert not list(tmp_path.rglob('*.zip'))


def test_output_free_notebook_keeps_corpus_source_identity(tmp_path_factory, monkeypatch):
    tmp_path = tmp_path_factory.mktemp('b')
    collect, _ = synthetic_collector(tmp_path, monkeypatch)
    name = 'paper1/AdaptiveEngineSimulation_Enhanced.ipynb'
    original = b'{"metadata":{"kernelspec":{"name":"python3"}},"cells":[{"cell_type":"code","source":["x=1"],"metadata":{},"outputs":[],"execution_count":null}]}\r\n'
    (tmp_path/name).write_bytes(original)
    contents, transforms = collect()
    assert contents[name] == original
    assert name not in transforms
    assert len(transforms) == 2


@pytest.mark.parametrize('missing', [
    'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md',
    'docs/thesis_recovery/22_A0_RESEARCH_LIFECYCLE_CONTRACT.md',
    'docs/thesis_recovery/23_TRAINING_MATRIX_ACCOUNTING_V1.md',
    'docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md',
    'docs/thesis_recovery/28_CUDA_EXECUTION_PROFILE_V1.md',
    'docs/thesis_recovery/29_GKT_RESEARCH_NUMERICAL_RECIPE_V1.md',
    'docs/thesis_recovery/30_SAKT_RESEARCH_NUMERICAL_RECIPE_V1.md',
    'docs/thesis_recovery/EXPERIMENT_ALLOCATION_V1.json',
    'experiments/akt/configs/simulator-research-corpus01.json',
    'tests/akt/fixtures/legacy_config_before_simulator_research.py.txt',
])
def test_missing_fixed_contract_stops_local_inventory_without_zip(tmp_path_factory, monkeypatch, missing):
    tmp_path = tmp_path_factory.mktemp('b')
    collect, _ = synthetic_collector(tmp_path, monkeypatch, missing)
    with pytest.raises(FileNotFoundError): collect()
    assert not list(tmp_path.rglob('*.zip'))
