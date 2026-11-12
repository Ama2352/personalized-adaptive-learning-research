"""COPY dùng tên tham số rõ ràng và giữ nguyên target chỉ trong train/selection."""
import importlib.util
from pathlib import Path

import duckdb
import pandas as pd


def test_copy_named_parameters_preserve_filtered_events(tmp_path):
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location('junyi_cache_script',root/'scripts/akt/prepare_junyi_selected_cache.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = tmp_path/'source.parquet'
    destination = tmp_path/'selected.parquet'
    source_frame = pd.DataFrame(dict(user_id=['a','b','c'],exercise=['x','y','z'],
        time_done=[3,2,1],source_row=[11,12,13],correct=[1,0,1],suggested=[0,1,0]))
    with duckdb.connect() as con:
        con.register('raw_events',source_frame)
        con.execute('COPY raw_events TO ? (FORMAT PARQUET)',[str(source)])
        con.register('requested_development_users',pd.DataFrame(dict(user_id=['a','b'],fold=[0,3])))
        con.execute(module.SELECTED_COPY_SQL,dict(source=str(source),destination=str(destination)))
        actual = con.execute('SELECT * FROM read_parquet(?) ORDER BY source_row',[str(destination)]).df()
        assignments = tmp_path/'assignments.parquet'
        con.execute(module.ASSIGNMENTS_COPY_SQL,dict(destination=str(assignments)))
        roles = con.execute('SELECT * FROM read_parquet(?) ORDER BY user_id',[str(assignments)]).fetchall()
        assert roles == [('a',0,'development'),('b',3,'development')]
    pd.testing.assert_frame_equal(actual,source_frame.iloc[:2].reset_index(drop=True))
