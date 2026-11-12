"""Đối chiếu record với iterator lịch sử bằng adapter giả, không nạp Torch."""
import ast
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from knowledge_tracing.akt.encoding import ExerciseEncoding
from knowledge_tracing.akt.prediction_batch import iter_predictions_batched
from knowledge_tracing.akt.types import KTEvent, LearnerEvents, PredictionRecord, UnseenTarget
from knowledge_tracing.akt.windows import iter_windows
from knowledge_tracing.shared_kt import StableVocabulary


def historical_iterator():
    """Compile nguyên hai hàm từ file hiện hành, tránh import adapter Torch."""
    path = Path(__file__).resolve().parents[2]/'src/knowledge_tracing/akt/prediction.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    nodes = [node for node in tree.body if isinstance(node,ast.FunctionDef)
             and node.name in ('_checkpoint_id','iter_predictions')]
    module = ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*nodes],
                        type_ignores=[])
    namespace = dict(np=np,hashlib=hashlib,json=json,math=math,LearnerEvents=LearnerEvents,
        PredictionRecord=PredictionRecord,UnseenTarget=UnseenTarget,iter_windows=iter_windows)
    exec(compile(ast.fix_missing_locations(module),str(path),'exec'),namespace)
    return namespace['iter_predictions']


def learner(user, items, *, start_row=1):
    return LearnerEvents(user,0,tuple(KTEvent(user,item,100+i,start_row+i,i%2,i%2,0)
                                     for i,item in enumerate(items)))


class FakeAdapter:
    def __init__(self, *, batch_size=4):
        self.config = SimpleNamespace(batch_size=batch_size,context=100,target_block=100)
        self.encoding = ExerciseEncoding(StableVocabulary(('A','B')),dict(A=8,B=5))
        self.checkpoint_id = 'checkpoint-test'
        self.calls = []

    def predict_window(self, window):
        return self.predict_windows([window])[0]

    def predict_windows(self, windows):
        self.calls.append(tuple(windows))
        result = []
        for window in windows:
            assert not hasattr(window,'targets')
            assert not hasattr(window.inputs,'correct')
            responses = window.inputs.prior_responses
            values = [0.15+0.7*int(responses[1:index+1].sum())/(index+1)
                      for index in range(len(responses))]
            result.append(np.asarray(values,dtype=np.float64))
        return result


@pytest.mark.parametrize('items',[
    ['A','B','A'],
    ['A','B']*260,
    ['OOV','A','B','OOV','B','OOV'],
    ['A']*101+['OOV']+['B']*205,
    ['OOV']*205,
])
def test_exact_historical_records_for_geometry_and_oov(items):
    students = [learner('u',items)]
    expected = list(historical_iterator()(FakeAdapter(),students))
    actual = list(iter_predictions_batched(FakeAdapter(),students))
    assert actual == expected
    assert len(actual) == len(items)


def test_batch_across_learners_with_same_output_order():
    students = [learner(str(i),['A','B'],start_row=10*i+1) for i in range(6)]
    adapter = FakeAdapter()
    actual = list(iter_predictions_batched(adapter,iter(students)))
    expected = list(historical_iterator()(FakeAdapter(),students))
    assert actual == expected
    assert [len(call) for call in adapter.calls] == [4,2]
    assert len({window.inputs.user_ids[0] for window in adapter.calls[0]}) == 4


def test_explicit_smaller_batch_and_final_partial_batch():
    adapter = FakeAdapter()
    students = [learner('u',['A']*450)]
    actual = list(iter_predictions_batched(adapter,students,batch_size=2))
    assert actual == list(historical_iterator()(FakeAdapter(),students))
    assert [len(call) for call in adapter.calls] == [2,2,1]


def test_batch_flush_before_oov_preserves_oov_position():
    adapter = FakeAdapter()
    records = list(iter_predictions_batched(adapter,[learner('u',['A','OOV','B'])]))
    assert [record.prediction_kind for record in records] == ['fitted','unseen','fitted']
    assert [len(call) for call in adapter.calls] == [1,1]
    assert records[1].prediction is None and records[1].is_fallback is False
    assert records[2].history_used == 0


def test_all_oov_never_calls_adapter():
    adapter = FakeAdapter()
    records = list(iter_predictions_batched(adapter,[learner('u',['OOV']*1000)]))
    assert len(records) == 1000
    assert adapter.calls == []


def test_current_and_future_outcome_do_not_change_current_probability():
    original = learner('u',['A','B']*80)
    events = list(original.events)
    events[120] = replace(events[120],correct=1-events[120].correct)
    changed = replace(original,events=tuple(events))
    before = list(iter_predictions_batched(FakeAdapter(),[original]))
    after = list(iter_predictions_batched(FakeAdapter(),[changed]))
    assert [record.prediction for record in before[:121]] == [record.prediction for record in after[:121]]
    assert before[120].correct != after[120].correct
    assert before[121].prediction != after[121].prediction


def test_fallback_checkpoint_hash_matches_history():
    adapter = FakeAdapter()
    del adapter.checkpoint_id
    adapter.run_identity = dict(run='test',phase='selection')
    old_adapter = FakeAdapter()
    del old_adapter.checkpoint_id
    old_adapter.run_identity = dict(run='test',phase='selection')
    students = [learner('u',['A'])]
    assert list(iter_predictions_batched(adapter,students)) == list(historical_iterator()(old_adapter,students))


@pytest.mark.parametrize('batch_size',[0,5,True,1.5,-1])
def test_invalid_requested_batch_rejected(batch_size):
    with pytest.raises(ValueError,match='prediction batch'):
        list(iter_predictions_batched(FakeAdapter(),[learner('u',['A'])],batch_size=batch_size))


def test_configured_batch_ceiling():
    with pytest.raises(ValueError,match='prediction batch'):
        list(iter_predictions_batched(FakeAdapter(batch_size=2),[learner('u',['A'])],batch_size=3))


@pytest.mark.parametrize('mode',['count','shape','nan','probability'])
def test_invalid_adapter_outputs_fail(mode):
    adapter = FakeAdapter()
    outputs = dict(count=[],shape=[np.array([.2,.3])],nan=[np.array([np.nan])],probability=[np.array([1.2])])
    adapter.predict_windows = lambda _: outputs[mode]
    with pytest.raises(ValueError):
        list(iter_predictions_batched(adapter,[learner('u',['A'])]))


@pytest.mark.parametrize('mode',['unsorted','duplicate','source_row','time','identity','label','support','checkpoint'])
def test_invalid_inputs_fail_like_historical_iterator(mode):
    adapter = FakeAdapter()
    students = [learner('a',['A','B'])]
    if mode == 'unsorted':
        students = [learner('b',['A']),learner('a',['A'],start_row=5)]
    elif mode == 'duplicate':
        students *= 2
    elif mode == 'source_row':
        students = [learner('a',['A'],start_row=0)]
    elif mode == 'time':
        events = students[0].events
        students = [replace(students[0],events=(events[1],events[0]))]
    elif mode == 'identity':
        events = students[0].events
        students = [replace(students[0],events=(replace(events[0],user_id='other'),events[1]))]
    elif mode == 'label':
        events = students[0].events
        students = [replace(students[0],events=(replace(events[0],correct=2),events[1]))]
    elif mode == 'support':
        adapter.encoding.train_support_students['A'] = 0
    elif mode == 'checkpoint':
        del adapter.checkpoint_id
    with pytest.raises(ValueError):
        list(iter_predictions_batched(adapter,students))
