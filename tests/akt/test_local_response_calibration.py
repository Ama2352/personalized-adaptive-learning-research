"""Kiểm parity fitter V1 với biểu diễn SQLite trên đĩa."""
from dataclasses import replace
import hashlib
import pytest

from knowledge_tracing import response_calibration as v1
from scripts.akt.local_response_calibration import fit_temperature_spooled, LocalCalibrationBudget


def fixture():
    binding = v1.PredictionBinding('A2', *('a'*64 for _ in range(7)))
    partition = v1.CalibrationPartition(binding.split_sha256, ('c1','c2'), ('train',), None)
    rows = [v1.CalibrationTarget('c'+str(1+i%2),str(i),'item-'+str(i%3),
        hashlib.sha256(str(i).encode()).hexdigest(),i%2,p, 'supported' if p is not None else 'oov')
        for i,p in enumerate((0.,1.,.4,.6,None,.5,.8,.2))]
    keys = [(r.learner_id,r.event_id,r.item_id,r.history_sha256) for r in rows]
    return binding,partition,rows,keys


@pytest.mark.parametrize('evaluations',[4,17,200])
@pytest.mark.parametrize('condition',['mixed','unsupported','oneclass','ties'])
def test_entire_payload_exactly_matches_public_v1(tmp_path,evaluations,condition):
    binding,partition,rows,keys = fixture()
    if condition == 'unsupported':
        rows=[replace(r,probability=None,support_reason='oov') for r in rows]
    if condition == 'oneclass':
        rows=[replace(r,correct=1) for r in rows]
    if condition == 'ties':
        rows=[replace(r,probability=.5,support_reason='supported') for r in rows]
    expected=v1.fit_temperature(rows,binding=binding,partition=partition,expected_target_keys=tuple(keys),max_evaluations=evaluations)
    actual=fit_temperature_spooled(iter(reversed(rows)),binding=binding,partition=partition,
        expected_target_keys=iter(keys),database=tmp_path/'fit.sqlite',
        budget=LocalCalibrationBudget(max_targets=100,max_seconds=30),max_evaluations=evaluations)
    assert actual.to_payload() == expected.to_payload()


@pytest.mark.parametrize('failure',['duplicate','missing','extra','wronglearner','binding'])
def test_coverage_and_binding_fail_closed_like_v1(tmp_path,failure):
    binding,partition,rows,keys=fixture()
    if failure=='duplicate': rows.append(rows[0])
    if failure=='missing': rows.pop()
    if failure=='extra': keys.pop()
    if failure=='wronglearner': rows[0]=replace(rows[0],learner_id='train')
    if failure=='binding': binding=replace(binding,split_sha256='b'*64)
    with pytest.raises(ValueError):
        v1.fit_temperature(rows,binding=binding,partition=partition,expected_target_keys=tuple(keys))
    with pytest.raises(ValueError):
        fit_temperature_spooled(iter(rows),binding=binding,partition=partition,
            expected_target_keys=iter(keys),database=tmp_path/'fit.sqlite',budget=LocalCalibrationBudget(max_targets=100))


def test_refuses_existing_database_and_target_budget(tmp_path):
    binding,partition,rows,keys=fixture()
    database=tmp_path/'existing.sqlite';database.write_bytes(b'preserve')
    with pytest.raises(ValueError,match='new physical'):
        fit_temperature_spooled(rows,binding=binding,partition=partition,expected_target_keys=keys,
            database=database,budget=LocalCalibrationBudget(max_targets=100))
    assert database.read_bytes()==b'preserve'
    with pytest.raises(MemoryError,match='target budget'):
        fit_temperature_spooled(rows,binding=binding,partition=partition,expected_target_keys=keys,
            database=tmp_path/'bounded.sqlite',budget=LocalCalibrationBudget(max_targets=2))


def test_bounded_resource_admission_is_explicit(tmp_path):
    binding,partition,rows,keys=fixture()
    with pytest.raises(MemoryError,match='RSS budget'):
        fit_temperature_spooled(rows,binding=binding,partition=partition,expected_target_keys=keys,
            database=tmp_path/'smallrss.sqlite',budget=LocalCalibrationBudget(max_targets=100,max_rss_bytes=1))
    with pytest.raises(ValueError,match='wall time'):
        LocalCalibrationBudget(max_targets=100,max_seconds=float('inf'))


def test_unicode_order_unsupported_reasons_and_nearby_probabilities_exact(tmp_path):
    binding,partition,rows,keys=fixture()
    rows=[replace(r,event_id=('é','a','中','🐍','9','000','ß','z')[i],
        probability=None if i%3==0 else .5000000000000001,
        support_reason=('missing','oov')[i%2] if i%3==0 else 'supported') for i,r in enumerate(rows)]
    keys=[(r.learner_id,r.event_id,r.item_id,r.history_sha256) for r in rows]
    expected=v1.fit_temperature(rows,binding=binding,partition=partition,expected_target_keys=tuple(keys))
    actual=fit_temperature_spooled(rows,binding=binding,partition=partition,expected_target_keys=keys,
        database=tmp_path/'unicode.sqlite',budget=LocalCalibrationBudget(max_targets=100))
    assert actual.to_payload()==expected.to_payload()
    import sqlite3
    with sqlite3.connect(tmp_path/'unicode.sqlite') as connection:
        plans=connection.execute('EXPLAIN QUERY PLAN SELECT reason,COUNT(*) FROM targets INDEXED BY unsupported_reasons WHERE probability IS NULL GROUP BY reason ORDER BY reason').fetchall()
    assert not any('TEMP B-TREE' in str(plan) for plan in plans)
