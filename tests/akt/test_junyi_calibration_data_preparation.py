"""Tiền xử lý calibration riêng trên fixtures Parquet, không dataset thật."""
import importlib.util
from pathlib import Path

import duckdb
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('prepare_calibration_data',ROOT/'scripts/akt/prepare_junyi_calibration_data.py')
prep=importlib.util.module_from_spec(spec)
spec.loader.exec_module(prep)


def make_source(tmp_path,**changes):
    frame=pd.DataFrame(dict(user_id=['calib','train','calib','outer','holdout'],
        exercise=['known','known','unknown','known','known'],time_done=[3,2,1,1,1],
        source_row=[11,12,13,14,15],correct=[1,0,0,1,1],suggested=[0,0,1,0,0]))
    for column,value in changes.items():
        frame.loc[0,column]=value
    source=tmp_path/'source.parquet'
    with duckdb.connect() as con:
        con.register('data',frame)
        con.execute('COPY data TO ? (FORMAT PARQUET)',[str(source)])
    return source


def register(con):
    prep.register_inputs(con,pd.DataFrame(dict(user_id=['calib'],fold=[2])),['known'])


def test_exact_calibration_targets_and_oov_without_other_roles(tmp_path):
    source=make_source(tmp_path)
    with duckdb.connect() as con:
        register(con)
        counts=prep.count_population(con,str(source))
    assert counts==dict(targets=2,learners=1,unique_source_rows=2,positive_labels=1,negative_labels=1,
                        invalid_rows=0,oov_targets=1,exercises=2,max_learner_events=2)


def test_copy_preserves_events_and_orders_timeline_and_assignments(tmp_path):
    source=make_source(tmp_path);destination=tmp_path/'calibration.parquet';assignments=tmp_path/'assignments.parquet'
    with duckdb.connect() as con:
        register(con)
        con.execute(prep.COPY_SQL,dict(source=str(source),destination=str(destination)))
        con.execute(prep.COPY_ASSIGNMENTS_SQL,dict(destination=str(assignments)))
        assert con.execute('SELECT source_row FROM read_parquet(?)',[str(destination)]).fetchall()==[(13,),(11,)]
        assert con.execute('SELECT * FROM read_parquet(?)',[str(assignments)]).fetchall()==[('calib',2,'development')]
        assert prep.count_population(con,str(source))==prep.count_population(con,str(destination))


@pytest.mark.parametrize('change',[dict(correct=2),dict(suggested=4),dict(source_row=-1),dict(time_done=-1),dict(exercise='')])
def test_invalid_calibration_values_rejected(tmp_path,change):
    source=make_source(tmp_path,**change)
    with duckdb.connect() as con:
        register(con)
        with pytest.raises(ValueError,match='Invalid calibration'):
            prep.count_population(con,str(source))


def test_duplicate_source_rows_rejected(tmp_path):
    source=make_source(tmp_path,source_row=13)
    with duckdb.connect() as con:
        register(con)
        with pytest.raises(ValueError,match='duplicated source_row'):
            prep.count_population(con,str(source))


def test_protected_output_rejected():
    with pytest.raises(ValueError,match='Owned'):
        prep.owned(ROOT/'artifacts/bkt_baseline/derived/new',ROOT/'artifacts/akt/junyi-cohorts')


def test_new_json_never_overwrites(tmp_path):
    path=tmp_path/'manifest.json'
    prep.write_new(path,dict(status='complete'))
    with pytest.raises(FileExistsError):
        prep.write_new(path,dict(status='changed'))
