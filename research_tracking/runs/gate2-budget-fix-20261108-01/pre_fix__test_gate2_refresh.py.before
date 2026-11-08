"""Không phát hành Gate2 từ zero tests hoặc suite có skip/failure."""

from pathlib import Path
import runpy

import pytest


@pytest.mark.parametrize('seconds', [0, -1, 601, True, 4.2, '420'])
def test_gate2_timeout_rejects_unbounded_or_invalid_values(seconds):
    validate = runpy.run_path(str(Path('scripts/akt/refresh_gate2.py')))['validate_timeout']
    with pytest.raises(ValueError, match='timeout'):
        validate(seconds)


def test_gate2_timeout_is_explicit_bounded_and_default_unchanged():
    import inspect
    module = runpy.run_path(str(Path('scripts/akt/refresh_gate2.py')))
    assert module['validate_timeout'](420) == 420
    assert module['validate_timeout'](600) == 600
    assert inspect.signature(module['refresh']).parameters['timeout_seconds'].default == 300


@pytest.mark.parametrize('attribute', ['tests="0"', 'tests="2" failures="1"', 'tests="2" skipped="1"', 'tests="2" errors="1"'])
def test_gate2_refresh_rejects_incomplete_suite(tmp_path, attribute):
    parse = runpy.run_path(str(Path('scripts/akt/refresh_gate2.py')))['test_result']
    path = tmp_path / 'junit.xml'
    path.write_text(f'<testsuites><testsuite {attribute}/></testsuites>', encoding='utf-8')
    with pytest.raises(ValueError, match='without failures'):
        parse(path)


def test_gate2_refresh_accepts_complete_suite(tmp_path):
    parse = runpy.run_path(str(Path('scripts/akt/refresh_gate2.py')))['test_result']
    path = tmp_path / 'junit.xml'
    path.write_text('<testsuites><testsuite tests="3" failures="0" skipped="0" errors="0"/></testsuites>', encoding='utf-8')
    assert parse(path) == {'passed': 3, 'failed': 0, 'errors': 0, 'skipped': 0}
