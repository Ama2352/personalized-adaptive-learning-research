"""Selection cache phải giữ đầy đủ record, OOV, metrics và biên model."""
from dataclasses import replace
import json
import sqlite3

import pytest

from test_junyi_window_cache import case, SOURCE
from test_prediction_batch import FakeAdapter, learner
from knowledge_tracing.akt.prediction_batch import iter_predictions_batched,iter_prepared_predictions_batched
from knowledge_tracing.akt.research_junyi_selection_cache import build_selection_cache,SelectionCacheSession


def test_cpu_admission_replays_same_population_and_cannot_reauthorize(case,tmp_path):
    from knowledge_tracing.akt.research_junyi_selection_cache import write_selection_cpu_admission
    from knowledge_tracing.akt.research_junyi_engineering import file_sha
    _,strict,receipt=build(case,['OOV','A','B']*90)
    admission=tmp_path/'selection-admission.json'
    window=tmp_path/'window-admission.json'
    write_selection_cpu_admission(strict,admission,window)
    restored=SelectionCacheSession(strict.root,view=case[2],encoding=case[3],source_sha256=SOURCE,
        expected_targets=270,expected_manifest_sha256=receipt['manifest_sha256'],
        admission_file=admission,expected_admission_sha256=file_sha(admission),
        window_admission_file=window,expected_window_admission_sha256=file_sha(window))
    first=FakeAdapter();second=FakeAdapter()
    first.encoding=second.encoding=case[3].native
    assert list(iter_prepared_predictions_batched(first,restored.iter_prepared(),batch_size=4))==list(
        iter_prepared_predictions_batched(second,strict.iter_prepared(),batch_size=4))
    with pytest.raises(ValueError,match='Fresh full selection join'):
        write_selection_cpu_admission(restored,tmp_path/'bad.json',tmp_path/'bad-window.json')


@pytest.mark.parametrize('change',['receipt_sha','window_sha','population','validator'])
def test_cpu_admission_mismatch_is_rejected(case,tmp_path,change):
    from knowledge_tracing.akt import research_junyi_selection_cache as module
    from knowledge_tracing.akt.research_junyi_engineering import file_sha
    _,strict,receipt=build(case,['A','B']*5)
    admission=tmp_path/'selection-admission.json';window=tmp_path/'window-admission.json'
    module.write_selection_cpu_admission(strict,admission,window)
    if change in ('population','validator'):
        payload=json.loads(admission.read_text())
        if change=='population':payload['population_sha256']='b'*64
        else:payload['validator_sources']['selection_join']='b'*64
        admission.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        SelectionCacheSession(strict.root,view=case[2],encoding=case[3],source_sha256=SOURCE,
            expected_targets=10,expected_manifest_sha256=receipt['manifest_sha256'],
            admission_file=admission,expected_admission_sha256='b'*64 if change=='receipt_sha' else file_sha(admission),
            window_admission_file=window,expected_window_admission_sha256='b'*64 if change=='window_sha' else file_sha(window))


def build(case,items):
    root,_,view,encoding=case
    student=learner(view.users[0],items)
    receipt=build_selection_cache(root,[student],view=view,encoding=encoding,source_sha256=SOURCE,
        expected_targets=len(items),max_seconds=60,max_rss_bytes=2*1024**3)
    session=SelectionCacheSession(root,view=view,encoding=encoding,source_sha256=SOURCE,
        expected_targets=len(items),expected_manifest_sha256=receipt['manifest_sha256'])
    return student,session,receipt


@pytest.mark.parametrize('items',[['A','B']*260,['OOV','A','B','OOV','B','OOV'],['OOV']*205])
@pytest.mark.parametrize('batch',[1,4,128])
def test_exact_records_labels_stay_outside_model(case,items,batch):
    student,session,_=build(case,items)
    first=FakeAdapter(batch_size=batch);second=FakeAdapter(batch_size=batch)
    first.encoding=second.encoding=case[3].native
    expected=list(iter_predictions_batched(first,[student],batch_size=batch))
    actual=list(iter_prepared_predictions_batched(second,session.iter_prepared(),batch_size=batch))
    assert actual==expected
    assert [tuple(w.window_id for w in group) for group in first.calls]==[
        tuple(w.window_id for w in group) for group in second.calls]


@pytest.mark.parametrize('kind',['pin','phase','source','database','missing_marker'])
def test_cache_changes_rejected(case,kind):
    _,session,receipt=build(case,['A','B','A'])
    root,train,view,encoding=case
    expected=receipt['manifest_sha256'];source=SOURCE
    if kind=='pin':expected='0'*64
    if kind=='phase':view=train
    if kind=='source':source='b'*64
    if kind=='database':
        with sqlite3.connect(root/'events.sqlite') as connection:connection.execute('UPDATE events SET correct=1-correct')
    if kind=='missing_marker':(root/'COMPLETE.json').unlink()
    with pytest.raises((ValueError,FileNotFoundError)):
        SelectionCacheSession(root,view=view,encoding=encoding,source_sha256=source,
            expected_targets=3,expected_manifest_sha256=expected)


def test_incomplete_build_has_failure_without_complete(case):
    root,_,view,encoding=case
    with pytest.raises(ValueError):
        build_selection_cache(root,[learner(view.users[0],['A','B'])],view=view,encoding=encoding,
            source_sha256=SOURCE,expected_targets=3,max_seconds=60,max_rss_bytes=2*1024**3)
    assert (root/'failure.json').exists() and not (root/'COMPLETE.json').exists()


def test_live_metadata_mutation_stops_replay(case):
    _,session,_=build(case,['A','B'])
    with sqlite3.connect(session.root/'events.sqlite') as connection:connection.execute('UPDATE events SET correct=0')
    with pytest.raises(ValueError,match='metadata changed'):list(session.iter_prepared())


def test_evaluate_cache_equals_live_and_export(case):
    import io
    from knowledge_tracing.akt.research_junyi_selection import _evaluate
    student,session,_=build(case,['A','B','OOV','A']*60)
    first=FakeAdapter();second=FakeAdapter()
    first.encoding=second.encoding=case[3].native
    outputs=[io.StringIO(),io.StringIO()]
    live=_evaluate(first,[student],240,batch_size=4,output=outputs[0])
    cached=_evaluate(second,None,240,batch_size=4,output=outputs[1],selection_cache=session)
    assert live==cached and outputs[0].getvalue()==outputs[1].getvalue()
