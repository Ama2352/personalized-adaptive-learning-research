"""Kiểm pilot closed-loop tái lập được và xuất đủ actual events."""

import io
import json
from pathlib import Path
import runpy

from knowledge_tracing.paper2_reference import load_reference


def test_closed_loop_pilot_replays_exactly(monkeypatch):
    scripts = Path(__file__).resolve().parents[2] / 'scripts/research'
    monkeypatch.syspath_prepend(str(scripts))
    pilot = runpy.run_path(str(scripts / 'run_cpu_diagnostics.py'))['closed_loop_pilot']
    reference, empty = load_reference(), load_reference(estimator_edges=[])
    first, second = io.StringIO(), io.StringIO()
    expected = pilot(reference, empty, seed=20000, profile='PY', steps=6, stream=first)
    actual = pilot(reference, empty, seed=20000, profile='PY', steps=6, stream=second)
    assert actual == expected
    assert first.getvalue() == second.getvalue()
    events = [json.loads(line) for line in first.getvalue().splitlines()]
    assert len(events) == 18
    assert {row['variant'] for row in events} == {'graph_free', 'graph_package', 'empty_graph_package'}
    assert all(0 < row['prediction'] < 1 for row in events)
