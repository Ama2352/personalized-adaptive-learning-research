"""Giới hạn mở rộng phải được kiểm trước khi chạm assignments/data."""

from pathlib import Path
import runpy

import pytest


@pytest.mark.parametrize('field,value', [('max_learners',257),('prefix_events',301),
                                      ('query_timeout',181),('max_learners',True),('prefix_events',0)])
def test_junyi_pilot_rejects_excess_workload_before_reading_data(field,value):
    script = Path(__file__).resolve().parents[2]/'scripts/research/run_approved_cpu_pilots.py'
    function = runpy.run_path(str(script))['junyi_order']
    def denied(*args,**kwargs):
        raise AssertionError('invalid request reached data access')
    function.__globals__['read_development_assignments'] = denied
    with pytest.raises(ValueError,match='approved CPU limits'):
        function('synthetic-limit-test',**{field:value})
