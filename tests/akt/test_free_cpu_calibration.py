import ast
import hashlib
import json
from pathlib import Path
import zipfile
from types import SimpleNamespace

import pytest

from scripts.akt import free_cpu_calibration as free
from test_cloud_calibration_fit import cloud_case
from test_junyi_calibration_producer import case
from test_cloud_calibration_numeric_join import numeric_case


class Response:
    def __init__(self, body, *, status=200, headers=None, metadata=None):
        self.body, self.status_code = body, status
        self.headers = headers or {}
        self.metadata = metadata

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def iter_content(self, size):
        yield self.body

    def json(self):
        return self.metadata


class Session:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, *args, **kwargs):
        self.calls.append(kwargs)
        return self.response


def pin(data):
    return dict(file_id='testid', bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def test_download_range_resume_and_sha(tmp_path):
    target = tmp_path / 'numeric.zip'
    target.with_suffix('.zip.part').write_bytes(b'ab')
    session = Session(Response(b'cdef', status=206, headers={'Content-Range': 'bytes 2-5/6'}))
    assert free.download(session, pin(b'abcdef'), target).read_bytes() == b'abcdef'
    assert session.calls[0]['headers'] == {'Range': 'bytes=2-'}
    assert free.download(session, pin(b'abcdef'), target) == target
    assert len(session.calls) == 1


def test_download_bad_sha_keeps_partial(tmp_path):
    target = tmp_path / 'numeric.zip'
    with pytest.raises(ValueError, match='SHA'):
        free.download(Session(Response(b'wrong!')), pin(b'abcdef'), target)
    assert not target.exists() and target.with_suffix('.zip.part').exists()


def test_numeric_zip_safe_restore(tmp_path):
    source = tmp_path / 'source.zip'
    name = free.RUN + '/a2-numeric/payloads/RECEIPT.json'
    with zipfile.ZipFile(source, 'w') as archive:
        archive.writestr(name, b'{}')
    metadata = dict(sha256=free.sha(source), source_members=1)
    free.extract_numeric(source, metadata, tmp_path / 'scratch', 'A2')
    free.extract_numeric(source, metadata, tmp_path / 'scratch', 'A2')
    assert (tmp_path / 'scratch' / name).read_bytes() == b'{}'
    (tmp_path / 'scratch' / name).write_bytes(b'changed')
    with pytest.raises(ValueError, match='Restaged'):
        free.extract_numeric(source, metadata, tmp_path / 'scratch', 'A2')


def test_numeric_zip_rejects_traversal(tmp_path):
    source = tmp_path / 'source.zip'
    with zipfile.ZipFile(source, 'w') as archive:
        archive.writestr(free.RUN + '/a2-numeric/payloads/../../bad', b'{}')
    with pytest.raises(ValueError, match='Unsafe'):
        free.extract_numeric(source, dict(sha256=free.sha(source), source_members=1), tmp_path / 'scratch', 'A2')


@pytest.mark.parametrize('changed', [False, True])
def test_completed_publication_rechecked_on_drive(changed):
    data = b'{}'
    metadata = dict(name='temperature.json', size='2', parents=['folder'],
                    sha256Checksum='bad' if changed else pin(data)['sha256'])
    receipt = dict(status='DRIVE_SHA256_VERIFIED', files=[dict(path='fit/temperature.json',
        file_id='file', folder_id='folder', bytes=2, sha256=pin(data)['sha256'])])
    session = Session(Response(b'', metadata=metadata))
    if changed:
        with pytest.raises(ValueError, match='changed'):
            free.verify_publication(session, receipt)
    else:
        free.verify_publication(session, receipt)
    assert len(session.calls) == 1


def test_pending_output_changed_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(free, 'VOLUME', tmp_path)
    publication = dict(run_id=free.RUN, tranche_id='a2-raw-freecpu-a2-001', files=['config.json','RAW_EXPORT.zip','COMPLETE.json'])
    payload = tmp_path / free.RUN / publication['tranche_id'] / 'payloads'
    payload.mkdir(parents=True)
    for name in publication['files']:
        (payload / name).write_bytes(b'{}')
    expected = free.publication_pins(publication)
    assert free.pending_exists(publication, expected)
    (payload / 'COMPLETE.json').write_bytes(b'bad')
    with pytest.raises(ValueError, match='changed'):
        free.pending_exists(publication, expected)


def test_notebook_cells_and_embedded_runner_parse():
    notebook = Path(__file__).resolve().parents[2] / 'notebooks/akt_colab_response_calibration_cpu.ipynb'
    document = json.loads(notebook.read_text(encoding='utf-8'))
    assert all(not cell.get('outputs') for cell in document['cells'])
    for cell in document['cells']:
        if cell['cell_type'] != 'code':
            continue
        tree = ast.parse(''.join(cell['source']))
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'FILES' for t in node.targets):
                embedded = ast.literal_eval(node.value)
                for name, text in embedded.items():
                    actual = notebook.parents[1] / 'scripts/akt' / name
                    assert actual.read_text(encoding='utf-8') == text
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'write_text':
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    ast.parse(node.args[0].value)


def test_publication_cannot_hash_arbitrary_path(tmp_path, monkeypatch):
    monkeypatch.setattr(free, 'VOLUME', tmp_path)
    with pytest.raises(ValueError, match='identity'):
        free.publication_source(dict(run_id=free.RUN, tranche_id='../private', files=['COMPLETE.json']))
    with pytest.raises(ValueError, match='allowlist'):
        free.publication_source(dict(run_id=free.RUN, tranche_id='a2-fit-freecpu-a2-001', files=['../private']))


@pytest.mark.parametrize('variant', ['A2', 'A3'])
@pytest.mark.parametrize('interrupt_fit_upload', [False, True])
def test_run_variant_joins_numeric_and_calls_v1_without_model(cloud_case, monkeypatch, variant, interrupt_fit_upload):
    from knowledge_tracing.akt import research_junyi_inference as inference
    from knowledge_tracing.akt import research_junyi_calibration as producer
    from knowledge_tracing.akt.research_junyi_graph_cache import _digest, FORMAT
    value = cloud_case
    kwargs = numeric_case(value, variant)
    root = kwargs['artifact_root'].root
    monkeypatch.setattr(free, 'VOLUME', root)
    monkeypatch.setattr(producer, 'inference_source_identity', lambda: kwargs['binding'].model_source_sha256)
    assets = dict(index={'model': variant + '_JUNYI_REFIT', 'checkpoint_sha256': kwargs['binding'].checkpoint_sha256},
                  encoding=value['encoding'], calibration=value['phase'])
    monkeypatch.setattr(inference, 'inspect_cpu_refit_export', lambda *args, **options: assets)
    population_path = root / 'population.json'
    population_path.write_text(json.dumps(value['population']))
    windows = root / 'windows'
    windows.mkdir()
    (windows / 'manifest.json').write_bytes(kwargs['window_manifest'].read_bytes())
    graph = {'sha256': 'f' * 64, 'binding': {}}
    cache = dict(population=value['population'], source_data_sha256=free.sha(value['paths'].canonical),
        graphs={variant: graph}, windows=dict(path=str(windows), admission_path=str(kwargs['window_admission']),
        admission_sha256=kwargs['expected_window_admission_sha256']))
    receipt = json.loads(kwargs['gpu_receipt'].read_text())
    receipt['graph_cache_identity'] = _digest((FORMAT, graph['sha256'], json.dumps(graph['binding'], sort_keys=True)))
    kwargs['gpu_receipt'].write_text(json.dumps(receipt))
    dummy = dict(path=str(population_path), sha256=free.sha(population_path))
    request = dict(variant=variant, mode='full', full_cohort_approved=True,
        source_identity=kwargs['binding'].model_source_sha256, exports={v: dummy for v in ('A0','A1','A2','A3')},
        data_paths={name:dict(path=str(getattr(value['paths'], name)), sha256=free.sha(getattr(value['paths'], name)))
                    for name in ('canonical','assignments','canonical_manifest','split_manifest')},
        population=dummy, source_pins=value['pins'],
        cache_receipt=dict(sha256=hashlib.sha256(json.dumps(cache).encode()).hexdigest()),
        cpu_budget=dict(max_targets=20,max_learner_events=10,max_users=2,max_seconds=60,
            max_rss_bytes=1024**3,min_available_ram_bytes=1,prediction_batch_size=128))
    gpu = dict(receipt_path=str(kwargs['gpu_receipt']), receipt_sha256=free.sha(kwargs['gpu_receipt']))
    state_root = root / 'private-state'
    state_root.mkdir()
    publications = []
    def publisher(session, publication, state_root):
        publications.append(publication)
        if interrupt_fit_upload and len(publications) == 2:
            raise ConnectionError('Synthetic interruption after fit completed')
        return dict(status='DRIVE_SHA256_VERIFIED', tranche_id=publication['tranche_id'], files=[])
    monkeypatch.setattr(free, 'publish', publisher)
    checked = []
    monkeypatch.setattr(free, 'verify_publication', lambda session, receipt: checked.append(receipt))
    if interrupt_fit_upload:
        with pytest.raises(ConnectionError):
            free.run_variant(request, gpu, cache, object(), state_root)
        saved = json.loads((state_root / (variant + '_PROGRESS.json')).read_text())
        assert saved['raw_verified'] and saved['pending_fit']
        from knowledge_tracing.akt import cloud_calibration_fit as fit_module
        from knowledge_tracing.akt import cloud_calibration_numeric_join as join_module
        def cannot_repeat_fit(*args, **kwargs):
            raise AssertionError('Completed fit must not be repeated')
        monkeypatch.setattr(fit_module, 'fit_volume_calibration', cannot_repeat_fit)
        monkeypatch.setattr(join_module, 'fit_volume_calibration', cannot_repeat_fit)
    state = free.run_variant(request, gpu, cache, object(), state_root)
    assert state['raw_verified'] and state['fit_verified']
    assert len(publications) == (3 if interrupt_fit_upload else 2)
    fitted = root / free.RUN / publications[1]['tranche_id'] / 'payloads/fit/temperature.json'
    assert fitted.is_file()
    payload = json.loads(fitted.read_text())
    assert payload['total_targets'] == 20 and payload['supported_targets'] == 18
    assert free.run_variant(request, gpu, cache, object(), state_root) == state
    assert len(publications) == (3 if interrupt_fit_upload else 2)
    assert len(checked) == (3 if interrupt_fit_upload else 2)
    changed = dict(request, cpu_budget=dict(request['cpu_budget'], max_seconds=61))
    with pytest.raises(ValueError, match='different inputs'):
        free.run_variant(changed, gpu, cache, object(), state_root)
