"""Publisher-produced tmp corpus from hand-built observables; no teacher/NN.

Publisher fixture source/memory checks are explicit synthetic mocks. Reader itself
uses production typed validators and has no publisher/AKT guard dependency.
"""
from dataclasses import FrozenInstanceError,replace
import ast
import builtins
import hashlib
import inspect
import json
from pathlib import Path
import sys

import pytest

from knowledge_tracing import simulator_corpus_reader as reader
# Explicit fixture-only imports: existing publisher tests never call a teacher.
from test_simulator_corpus_publisher import template,case,publish


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(autouse=True)
def no_neural_import(monkeypatch):
    original=builtins.__import__
    def checked(name,*a,**kw):
        if name=='torch' or name.startswith('torch.') or name in ('knowledge_tracing.akt.model','knowledge_tracing.akt.training'):
            raise AssertionError('reader tests cannot allocate neural models')
        return original(name,*a,**kw)
    monkeypatch.setattr(builtins,'__import__',checked)
    assert 'torch' not in sys.modules
    yield
    assert 'torch' not in sys.modules


@pytest.fixture
def public(case,monkeypatch):
    receipt=publish(case)
    monkeypatch.setattr(reader,'ROOT',case.root)
    case.published=receipt
    case.read_limits=reader.CorpusReadLimits(2*1024**2,8*1024**2,512*1024,8,84,840,15.)
    return case


def load(case,**kwargs):
    options=dict(expected_corpus_sha256=case.published.corpus_sha256,
        expected_done_sha256=case.published.done_sha256,limits=case.read_limits)
    options.update(kwargs)
    return reader.read_public_research_corpus(case.corpus_id,**options)


def write(path,value):
    path.write_text(json.dumps(value,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')


def resign(case):
    corpus=json.loads((case.base/'corpus.json').read_bytes())
    corpus['bank_sha256']=digest(case.base/'bank.json');corpus['plan_sha256']=digest(case.base/'plan.json')
    for role in ('train','selection','calibration'):
        entry=corpus['roles'][role];entry['observable_sha256']=digest(case.base/(role+'.jsonl'))
        manifest=json.loads((case.base/(role+'.manifest.json')).read_bytes())
        manifest['observable_sha256']=entry['observable_sha256'];write(case.base/(role+'.manifest.json'),manifest)
        entry['manifest_sha256']=digest(case.base/(role+'.manifest.json'))
    write(case.base/'corpus.json',corpus)
    done=dict(schema_version=1,status='COMPLETE_SIMULATOR_CORPUS',corpus_sha256=digest(case.base/'corpus.json'),
        files_sha256={name:digest(case.base/name) for name in reader.PUBLIC_FILES})
    write(case.base/'DONE.json',done)
    case.published=replace(case.published,corpus_sha256=done['corpus_sha256'],done_sha256=digest(case.base/'DONE.json'))


def payloads(case,role):return [json.loads(line) for line in (case.base/(role+'.jsonl')).read_bytes().splitlines()]


def write_rows(case,role,rows):
    (case.base/(role+'.jsonl')).write_bytes(b''.join(json.dumps(r,sort_keys=True,allow_nan=False).encode()+b'\n' for r in rows))
    resign(case)


def test_publisher_to_production_reader_full_typed_roundtrip(public):
    result=load(public)
    assert result.plan==public.plan and result.bank==public.results['train'].bank
    assert len(result.files_sha256)==9 and result.done_sha256==public.published.done_sha256
    assert result.input_bytes==sum((public.base/n).stat().st_size for n in (*reader.PUBLIC_FILES,'DONE.json'))
    assert result.manifest['source_inventory']==public.sources
    assert len(result.identity)==64 and result.identity==load(public).identity
    total=0
    for role,learners,events in [('train',8,672),('selection',1,84),('calibration',1,84)]:
        value=result.role_data(role)
        assert value.trajectories==tuple(sorted(public.results[role].trajectories,key=lambda t:t.learner_id))
        assert value.provenance==public.results[role].provenance
        assert len(value.trajectories)==learners and value.audit['audit']['targets']==events
        assert value.reference_complete and value.two_class_support
        assert value.class_counts==(events//2,events//2)
        total+=events
    assert total==840


def test_only_public_inputs_open_no_oracle_final_or_source_paths(public,monkeypatch):
    allowed={public.base/name for name in (*reader.PUBLIC_FILES,'DONE.json')}
    original=Path.open;opened=[]
    def checked(path,*a,**kw):
        assert path in allowed,'reader opened non-public source/oracle/final path'
        opened.append(path)
        return original(path,*a,**kw)
    monkeypatch.setattr(Path,'open',checked)
    result=load(public)
    assert set(opened)==allowed and result.role_data('calibration').two_class_support
    with pytest.raises(ValueError,match='final/unknown'):result.role_data('final')


def test_immutable_result_and_fresh_metadata_accessors(public):
    result=load(public);role=result.role_data('selection')
    with pytest.raises(FrozenInstanceError):result.corpus_id='other'
    with pytest.raises(FrozenInstanceError):role.trajectories[0].observations[0].correct=0
    audit=role.audit;audit['reference_complete']=False
    corpus=result.manifest;corpus['source_inventory'].clear()
    assert role.reference_complete and result.manifest['source_inventory']
    result.assert_integrity()
    object.__setattr__(result,'corpus_manifest_json','{}')
    with pytest.raises(ValueError,match='result changed'):result.assert_integrity()


@pytest.mark.parametrize('kind',['missing_done','failure','bad_done_hash','bad_corpus_hash','wrong_map'])
def test_closed_publication_and_external_pins(public,kind):
    options={}
    if kind=='missing_done':(public.base/'DONE.json').unlink()
    elif kind=='failure':write(public.base/'failure.json',{'status':'FAILED'})
    elif kind=='bad_done_hash':options['expected_done_sha256']='a'*64
    elif kind=='bad_corpus_hash':options['expected_corpus_sha256']='a'*64
    else:
        done=json.loads((public.base/'DONE.json').read_bytes());done['files_sha256']['oracle/train.json']='a'*64
        write(public.base/'DONE.json',done);options['expected_done_sha256']=digest(public.base/'DONE.json')
    with pytest.raises(ValueError):load(public,**options)


@pytest.mark.parametrize('kind',['trajectory_extra','observation_extra','query_extra','bool_label','nonbinary_label',
    'foreign_item','wrong_role','duplicate_learner','clock','global_row','duplicate_row','plan','policy'])
def test_exact_observable_payload_and_actual_audits_reject_forged_metadata(public,kind):
    rows=payloads(public,'selection');first=rows[0];obs=first['observations']
    if kind=='trajectory_extra':first['true_theta']=999
    elif kind=='observation_extra':obs[0]['latent']=999
    elif kind=='query_extra':obs[0]['query']['correct']=1
    elif kind=='bool_label':obs[0]['correct']=True
    elif kind=='nonbinary_label':obs[0]['correct']=2
    elif kind=='foreign_item':obs[0]['query']['item_id']='Junyi-not-in-simulator-bank'
    elif kind=='wrong_role':first['learner_id']=public.plan.split_plan.assignments('final')[0].learner_id
    elif kind=='duplicate_learner':rows.append(first)
    elif kind=='clock':obs[0]['query']['timestamp']+=1
    elif kind=='global_row':obs[0]['query']['source_row']+=1
    elif kind=='duplicate_row':obs[1]['query']['source_row']=obs[0]['query']['source_row']
    elif kind=='plan':first['plan_sha256']='a'*64
    else:first['collection_policy_id']='unbound-policy'
    write_rows(public,'selection',rows)
    with pytest.raises(ValueError):load(public)


@pytest.mark.parametrize('raw',[b'{"x":1,"x":2}\n',b'{"x":NaN}\n',b'{"x":Infinity}\n',b'{"observations":',b'\n'])
def test_malformed_duplicate_nonfinite_and_truncated_jsonl(public,raw):
    (public.base/'selection.jsonl').write_bytes(raw);resign(public)
    with pytest.raises(ValueError):load(public)


def test_missing_reference_and_single_class_are_reported_not_fitted_claims(public):
    rows=payloads(public,'calibration');known=public.results['train'].bank.item_ids[0]
    for observation in rows[0]['observations']:
        observation['query']['item_id']=known;observation['correct']=1
    write_rows(public,'calibration',rows)
    result=load(public);role=result.role_data('calibration')
    assert role.reference_complete is False and len(role.audit['missing_reference_items'])==83
    assert role.class_counts==(0,84) and role.two_class_support is False
    assert role.audit['audit']['targets']==84  # No favorable population filtering.
    assert 'fitted' not in result.manifest


@pytest.mark.parametrize('kind',['line','file','total_bytes','trajectories','perlearner_events','whole_events'])
def test_explicit_streaming_and_whole_corpus_limits(public,kind):
    limits=public.read_limits
    if kind=='line':limits=replace(limits,max_line_bytes=100)
    elif kind=='file':limits=replace(limits,max_file_bytes=100,max_line_bytes=100)
    elif kind=='total_bytes':
        sizes=[(public.base/n).stat().st_size for n in (*reader.PUBLIC_FILES,'DONE.json')]
        limits=replace(limits,max_total_bytes=sum(sizes)-1,max_file_bytes=max(sizes),max_line_bytes=max(sizes))
    elif kind=='trajectories':limits=replace(limits,max_trajectories_per_role=7)
    elif kind=='perlearner_events':limits=replace(limits,max_events_per_learner=83)
    else:limits=replace(limits,max_total_events=839)
    with pytest.raises(ValueError):load(public,limits=limits)


@pytest.mark.parametrize('field,value',[('max_file_bytes',None),('max_total_events',True),('max_wall_seconds',float('nan')),('max_line_bytes',0)])
def test_limit_schema_has_no_implicit_or_nonfinite_values(public,field,value):
    with pytest.raises(ValueError):replace(public.read_limits,**{field:value})


def test_source_public_metadata_changed_after_parse_is_rejected(public,monkeypatch):
    original=reader._Read.verify_after
    def changed(value):
        with (public.base/'corpus.json').open('ab') as stream:stream.write(b' ')
        return original(value)
    monkeypatch.setattr(reader._Read,'verify_after',changed)
    with pytest.raises(ValueError,match='metadata changed'):load(public)


def test_source_inventory_binding_tamper_with_resigned_files_rejected(public):
    path=public.base/'selection.manifest.json';value=json.loads(path.read_bytes())
    value['provenance']['source_bindings'][0][1]='a'*64
    # Identity stays old; all file byte hashes legitimately refreshed in the negative fixture.
    write(path,value);resign(public)
    with pytest.raises(ValueError,match='provenance identity'):load(public)


def test_no_root_override_and_alias_rejects_before_any_read(public,monkeypatch):
    assert 'project_root' not in inspect.signature(reader.read_public_research_corpus).parameters
    with pytest.raises(TypeError):reader.read_public_research_corpus(public.corpus_id,project_root=public.root)
    monkeypatch.setattr(reader,'_alias',lambda path:path==public.root/'artifacts/simulator/corpora')
    monkeypatch.setattr(Path,'open',lambda *a,**kw:pytest.fail('alias must reject before any read'))
    with pytest.raises(ValueError,match='junction'):load(public)


@pytest.mark.parametrize('corpus_id',['../dataset','a/b','/absolute','a\\b',''])
def test_fixed_root_id_cannot_traverse(public,monkeypatch,corpus_id):
    monkeypatch.setattr(Path,'open',lambda *a,**kw:pytest.fail('unsafe ID read'))
    with pytest.raises(ValueError,match='safe corpus'):reader.read_public_research_corpus(corpus_id,
        expected_corpus_sha256='a'*64,expected_done_sha256='b'*64,limits=public.read_limits)


def test_production_reader_imports_only_stdlib_and_public_validators():
    source=Path(reader.__file__).read_text(encoding='utf-8');tree=ast.parse(source)
    imports=[n.module or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    imports += [a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
    assert not any(any(part in name for part in ('torch','numpy','pandas','publisher','collection','akt')) for name in imports)


def test_post_read_wall_limit_is_fail_closed(public,monkeypatch):
    monkeypatch.setattr(reader.time,'monotonic',lambda:0.)
    clocks=iter((0.,16.))
    monkeypatch.setattr(reader.time,'time',lambda:next(clocks))
    with pytest.raises(ValueError,match='wall limit'):load(public)
