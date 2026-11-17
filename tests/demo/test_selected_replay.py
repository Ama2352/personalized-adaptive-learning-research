"""Replay model selected Grade10 thật, routing bình thường và fixture Range."""
import copy
from email.message import Message
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest

from src.research_demo.evidence import EvidenceError, EvidenceStore
from src.research_demo.selected import MODELS, SelectedReplay
from src.research_demo import selected, server

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT/'research_tracking/runs/demo-grade10-selected-replay-20261117-01'


@pytest.fixture(scope='module')
def selected_store():
    return SelectedReplay()


def test_all_selected_probabilities_cohort_and_graph_fields(selected_store):
    catalog = selected_store.catalog()
    assert catalog['dataset'] == 'Grade10' and catalog['phase'] == 'raw_selection10'
    assert catalog['cohort'] == dict(learners=6,targets=1260,steps=210,concepts=28,items=84)
    assert [row['id'] for row in catalog['models']] == list(MODELS)
    for model in MODELS:
        for learner in selected_store.learners:
            for step in (0,1,99,100,209):
                snapshot = selected_store.snapshot(model,learner,step)
                assert snapshot['probability'] == selected_store.models[model]['probabilities'][learner][step]
                assert len(snapshot['observed_history']) == step
                assert len(snapshot['query_route']) == step+1
                assert sum(row['observed'] for row in snapshot['observed_concepts'].values()) == step
                assert len(snapshot['observed_concepts']) == 28
                assert snapshot['graph']['gate_value'] is None
                assert snapshot['graph']['edges'] == selected_store.models[model]['edges']
                assert snapshot['recommendation_available'] is snapshot['calibrated_mastery_available'] is False
                assert not {'correct','mastered_bool','theta','junyi','learner_id'} & snapshot.keys()


def test_current_and_future_answers_are_not_exposed_as_history(selected_store):
    store = copy.deepcopy(selected_store)
    before = store.snapshot('A3_EXPERT','learner-1',100)
    for event in store.learners['learner-1'][100:]:
        event['correct'] = 1-event['correct']
    after = store.snapshot('A3_EXPERT','learner-1',100)
    assert before == after
    assert after['history_used'] <= after['history_available']


@pytest.mark.parametrize('mutation',['domain','phase','label_scope','nan','cohort','edge','learner','metric','gate'])
def test_selected_schema_rejects_corrupt_projection(selected_store,mutation):
    data = copy.deepcopy(selected_store.data)
    if mutation == 'domain':data['dataset']='Junyi'
    elif mutation == 'phase':data['phase']='outer_evaluation'
    elif mutation == 'label_scope':data['labels_are_synthetic']=False
    elif mutation == 'nan':data['models']['A0']['probabilities']['learner-1'][0]=float('nan')
    elif mutation == 'cohort':data['cohort']['targets']=1259
    elif mutation == 'edge':data['models']['A3_EXPERT']['edges'][0]['child']='unknown'
    elif mutation == 'learner':data['learners'][0]['events'].pop()
    elif mutation == 'metric':data['models']['A0']['metrics']['brier']=0
    else:data['models']['A3_EXPERT']['gate_values_archived']=True
    with pytest.raises(EvidenceError):SelectedReplay.validate(data)


@pytest.mark.parametrize('filename',['REPLAY_MANIFEST.json','selected-replay.json.gz'])
def test_pinned_source_changed_refused_before_listener(monkeypatch,filename):
    original = selected.bounded_read
    def read(path,limit):
        raw = original(path,limit)
        return raw+b' ' if path.name == filename else raw
    monkeypatch.setattr(selected,'bounded_read',read)
    with pytest.raises(EvidenceError,match='SHA'):SelectedReplay()


@pytest.fixture(scope='module')
def complete_store():
    return EvidenceStore()


@pytest.fixture
def routed(complete_store,monkeypatch):
    monkeypatch.setattr(server,'ThreadingHTTPServer',lambda address,handler:SimpleNamespace(handler=handler,address=address))
    facade=server.make_server(8765,store=complete_store)
    handler=object.__new__(facade.handler)
    handler.server=SimpleNamespace(server_address=facade.address)
    handler.headers=Message();handler.headers['Host']='127.0.0.1:8765'
    replies=[]
    handler.respond=lambda *args:replies.append(args)
    return handler,replies


def test_normal_handler_catalog_and_selected_endpoint(routed,complete_store):
    handler,replies=routed
    handler.path='/api/catalog';handler.do_GET()
    assert replies[-1][1]['selected_model_results']['cohort']['targets']==1260
    for model in MODELS:
        handler.path=f'/api/selected-replay?model={model}&learner=learner-6&step=209'
        handler.do_GET()
        assert replies[-1] == (200,complete_store.selected.snapshot(model,'learner-6',209))
    handler.path='/assets/selected-demo.js';handler.do_GET()
    assert replies[-1][0] == 200 and b'initSelected' in replies[-1][1]


@pytest.mark.parametrize('query',['','model=A0&learner=learner-1','model=A0&learner=learner-1&step=210',
    'model=A0&learner=learner-1&step=-1','model=A0&learner=learner-1&step=01',
    'model=A0&learner=learner-1&step=1.0','model=A0&learner=learner-1&step=１',
    'model=Junyi&learner=learner-1&step=1','model=A0&learner=private&step=1',
    'model=A0&learner=learner-1&step=1&step=2','model=A0&learner=learner-1&step=1&file=token'])
def test_selected_query_allowlist(routed,query):
    handler,replies=routed;handler.path='/api/selected-replay?'+query;handler.do_GET()
    assert replies[-1][0] == 400


def test_selected_route_retains_origin_guard(routed):
    handler,replies=routed
    handler.path='/api/selected-replay?model=A0&learner=learner-1&step=0'
    handler.headers['Origin']='https://foreign.invalid';handler.do_GET()
    assert replies[-1][0] == 403


def test_ui_ids_script_safety_and_labels():
    html=(server.STATIC/'index.html').read_text(encoding='utf-8')
    js=(server.STATIC/'selected-demo.js').read_text(encoding='utf-8')
    ids=re.findall(r'id="([^"]+)"',html)
    assert len(ids)==len(set(ids))
    assert set(re.findall(r'\$\("([^"]+)"\)',js)) <= set(ids)
    assert 'innerHTML' not in js and 'eval(' not in js
    assert 'raw_selection10' in (ROOT/'src/research_demo/selected.py').read_text()
    assert 'Giá trị cổng ở từng bước chưa ghi nhận' in js
    assert 'Các bản Junyi dùng từ vựng riêng' in html


def test_fresh_process_no_torch_or_training_import():
    checked=subprocess.run([sys.executable,'-B','-c',
        'import sys;from src.research_demo.evidence import EvidenceStore;'
        's=EvidenceStore();assert len(s.selected.models)==7;assert "torch" not in sys.modules'],
        cwd=ROOT,capture_output=True,text=True,timeout=30)
    assert checked.returncode==0,checked.stderr


def range_module():
    spec=importlib.util.spec_from_file_location('demo_range_fixture',BUNDLE/'fetch_a0_members.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_remote_zip_range_reads_only_members_and_enforces_budget():
    import zipfile
    module=range_module();data=io.BytesIO()
    with zipfile.ZipFile(data,'w',compression=zipfile.ZIP_STORED) as archive:
        archive.writestr('wanted.csv','synthetic')
        archive.writestr('weights.pt',b'x'*200000)
    raw=data.getvalue()
    class Response:
        def __init__(self,start,stop):
            self.start,self.stop=start,stop;self.status_code=206
            self.headers={'Content-Range':f'bytes {start}-{stop}/{len(raw)}'}
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def iter_content(self,size):yield raw[self.start:self.stop+1]
    class Session:
        def get(self,url,**kwargs):
            start,stop=map(int,kwargs['headers']['Range'].split('=')[1].split('-'))
            return Response(start,stop)
    stream=module.RangedZip(Session(),'fixture',len(raw),8192)
    with zipfile.ZipFile(stream) as archive:
        assert archive.read('wanted.csv')==b'synthetic'
    assert stream.bytes_read<8192
    stream.seek(0)
    with pytest.raises(ValueError,match='ngân sách'):stream.read()


def test_real_range_receipts_respect_combined_four_mib():
    receipts=[json.loads(path.read_text()) for path in BUNDLE.glob('*_RANGE_RECEIPT.json')]
    assert len(receipts)==2
    assert sum(row['response_bytes'] for row in receipts)<=4*1024**2
    assert all(row['full_archive_downloaded'] is row['model_weights_downloaded'] is False for row in receipts)
