"""Không phát hành Gate2 từ zero tests hoặc suite có skip/failure."""

from pathlib import Path
import hashlib
import json
import runpy
from types import SimpleNamespace

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
    path.write_text('<testsuites><testsuite tests="3" failures="0" skipped="0" errors="0">'
                    '<testcase classname="fixture" name="a"/><testcase classname="fixture" name="b"/>'
                    '<testcase classname="fixture" name="c"/></testsuite></testsuites>', encoding='utf-8')
    assert parse(path) == {'passed': 3, 'failed': 0, 'errors': 0, 'skipped': 0}


def test_gate2_junit_counts_items_and_preserves_passed_call_surplus(tmp_path):
    import xml.etree.ElementTree as ET
    module = runpy.run_path(str(Path('scripts/akt/refresh_gate2.py')))
    groups = []
    before = {}
    for index, reported in enumerate((1, 1, 4)):
        path = tmp_path / f'group-{index}.xml'
        path.write_text(f'<testsuites><testsuite tests="{reported}" failures="0" errors="0" skipped="0">'
                        f'<testcase classname="group{index}" name="test_item"/>'
                        '</testsuite></testsuites>', encoding='utf-8')
        before[path] = path.read_bytes()
        actual = module['test_result'](path)
        assert actual == {'passed': 1, 'failed': 0, 'errors': 0, 'skipped': 0}
        groups.append({'junit_path': str(path), 'test_result': actual})
    output = tmp_path / 'merged.xml'
    assert module['combine_junit'](groups, output) == {'passed': 3, 'failed': 0, 'errors': 0, 'skipped': 0}
    merged = ET.fromstring(output.read_bytes())
    assert [suite.get('tests') for suite in merged] == ['1', '1', '4']
    assert len(list(merged.iter('testcase'))) == 3
    assert all(path.read_bytes() == raw for path, raw in before.items())


@pytest.mark.parametrize('field,value', [
    ('tests', '-1'), ('tests', '1.5'), ('tests', 'NaN'), ('tests', 'True'),
    ('tests', ' 2'), ('failures', '-1'), ('errors', '0.0'), ('skipped', '')],
    ids=['negative-tests', 'fraction-tests', 'nonfinite-tests', 'boolean-tests',
         'space-tests', 'negative-failures', 'fraction-errors', 'missing-skipped'])
def test_gate2_junit_rejects_malformed_count_attributes(tmp_path, field, value):
    module = runpy.run_path(str(Path('scripts/akt/refresh_gate2.py')))
    attributes = dict(tests='2', failures='0', errors='0', skipped='0')
    attributes[field] = value
    rendered = ' '.join(f'{key}="{item}"' for key, item in attributes.items())
    path = tmp_path / 'malformed.xml'
    path.write_text(f'<testsuite {rendered}><testcase classname="fixture" name="one"/></testsuite>', encoding='utf-8')
    with pytest.raises(ValueError):
        module['test_result'](path)


@pytest.mark.parametrize('tag', ['failure', 'error', 'skipped'])
def test_gate2_junit_rejects_hidden_subtest_outcome_despite_zero_attributes(tmp_path, tag):
    module = runpy.run_path(str(Path('scripts/akt/refresh_gate2.py')))
    path = tmp_path / 'hidden.xml'
    path.write_text('<testsuite tests="4" failures="0" errors="0" skipped="0">'
                    f'<testcase classname="fixture" name="parent"><{tag} message="subtest outcome"/>'
                    '</testcase></testsuite>', encoding='utf-8')
    with pytest.raises(ValueError, match='without failures/errors/skips'):
        module['test_result'](path)


@pytest.mark.parametrize('body', [
    '<testsuite tests="2" failures="0" errors="0" skipped="0"/>',
    '<testsuites/>',
    '<other><testsuite tests="1" failures="0" errors="0" skipped="0"/></other>',
    '<testsuites><wrapper><testsuite tests="1" failures="0" errors="0" skipped="0"/></wrapper></testsuites>',
    '<testsuite tests="2" failures="0" errors="0" skipped="0"><testsuite tests="1" failures="0" errors="0" skipped="0"><testcase classname="f" name="a"/></testsuite></testsuite>',
    '<testsuite tests="2" failures="0" errors="0" skipped="0"><testcase classname="f" name="a"><testcase classname="f" name="b"/></testcase></testsuite>',
    '<testsuite tests="1" failures="0" errors="0" skipped="0"><testcase classname="f" name="a"/><testcase classname="f" name="b"/></testsuite>'],
    ids=['positive-attribute-empty', 'empty-root', 'foreign-root', 'wrapped-suite',
         'nested-suite', 'nested-case', 'underreported-items'])
def test_gate2_junit_rejects_empty_nested_or_underreported_cases(tmp_path, body):
    module = runpy.run_path(str(Path('scripts/akt/refresh_gate2.py')))
    path = tmp_path / 'structure.xml'
    path.write_text(body, encoding='utf-8')
    with pytest.raises(ValueError):
        module['test_result'](path)


@pytest.mark.parametrize('second', ['<testcase classname="f" name="a"/>', '<testcase classname="f"/>'],
    ids=['duplicate', 'missing-name'])
def test_gate2_junit_rejects_duplicate_or_missing_item_identity(tmp_path, second):
    module = runpy.run_path(str(Path('scripts/akt/refresh_gate2.py')))
    path = tmp_path / 'identity.xml'
    path.write_text('<testsuite tests="3" failures="0" errors="0" skipped="0">'
                    '<testcase classname="f" name="a"/>'+second+'</testsuite>', encoding='utf-8')
    with pytest.raises(ValueError, match='duplicate or invalid testcase'):
        module['test_result'](path)


def test_gate2_junit_merge_rejects_stale_report_count_before_output(tmp_path):
    module = runpy.run_path(str(Path('scripts/akt/refresh_gate2.py')))
    path = tmp_path / 'one.xml'
    path.write_text('<testsuite tests="4" failures="0" errors="0" skipped="0">'
                    '<testcase classname="f" name="a"/></testsuite>', encoding='utf-8')
    output = tmp_path / 'aggregate.xml'
    groups = [{'junit_path': str(path), 'test_result': dict(passed=4, failed=0, errors=0, skipped=0)}]
    with pytest.raises(ValueError, match='actual shard count'):
        module['combine_junit'](groups, output)
    assert not output.exists()


def _publisher(tmp_path, monkeypatch, *, elapsed):
    """Fake child only: no pytest subprocess, Torch, optimizer or Gate publication."""
    module = runpy.run_path(str(Path('scripts/akt/refresh_gate2.py')))
    namespace = module['refresh'].__globals__
    root = tmp_path / 'project'
    directory = root / 'artifacts/akt/preflight'
    directory.mkdir(parents=True)
    (root / 'requirements-akt.lock.txt').write_text('synthetic lock', encoding='utf-8')
    pointer = directory / 'gate2-current.json'
    pointer.write_bytes(b'original pointer must remain intact\n')
    observed = {}
    modules = [*module['STRICT_STDLIB'], *module['NO_TORCH'], 'tests/akt/test_fixture_remaining.py']
    for relative in modules:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('def test_fixture(): pass\n', encoding='utf-8')
    clock = SimpleNamespace(now=100.0)

    def child(command, **kwargs):
        observed.update(kwargs)
        files = command[command.index('pytest')+1:command.index('-q')]
        group = ('stdlib' if files == list(module['STRICT_STDLIB']) else
                 'no-torch' if files == list(module['NO_TORCH']) else 'remaining')
        calls = observed.setdefault('children', [])
        calls.append(dict(group=group, files=files, timeout=kwargs['timeout']))
        problem = observed.get('xml_problems', {}).get(group)
        counts = dict(tests=len(files), failures=0, errors=0, skipped=0)
        if problem == 'zero':
            counts['tests'] = 0
        elif problem:
            counts[problem] = 1
        cases = ''.join('<testcase classname="'+relative[:-3].replace('/', '.')+'" name="test_fixture"/>'
                        for relative in files) if counts['tests'] else ''
        if observed.get('duplicate_case') and group == 'no-torch':
            cases = cases.replace(files[0][:-3].replace('/', '.'), module['STRICT_STDLIB'][0][:-3].replace('/', '.'))
        attrs = ' '.join(name+'="'+str(value)+'"' for name,value in counts.items())
        Path(command[command.index('--junitxml') + 1]).write_text(
            '<testsuites><testsuite '+attrs+'>'+cases+'</testsuite></testsuites>', encoding='utf-8')
        kwargs['stdout'].write(b'Synthetic process group only; no actual pytest/native execution.\n')
        costs = observed.get('per_child_seconds')
        if costs is None:
            clock.now = 100.0 + elapsed
        else:
            clock.now += costs[len(calls)-1]
        return SimpleNamespace(returncode=observed.get('returncodes', {}).get(group, 0))

    monkeypatch.setitem(namespace, 'ROOT', root)
    monkeypatch.setitem(namespace, 'sys', SimpleNamespace(prefix=str(root / '.venv'), executable='fixture-python'))
    monkeypatch.setitem(namespace, 'time', SimpleNamespace(perf_counter=lambda: clock.now))
    monkeypatch.setitem(namespace, '_fixture_clock', clock)
    monkeypatch.setitem(namespace, 'subprocess', SimpleNamespace(run=child, STDOUT=-2))
    monkeypatch.setitem(namespace, 'verify_upstream', lambda *args: {'commit': 'synthetic source'})
    monkeypatch.setitem(namespace, 'gate2_build_hashes', lambda: {'fixture.py': 'source hash'})
    def reader(*args, **kwargs):
        observed['reader_kwargs'] = kwargs
        if 'reader_elapsed' in observed:
            clock.now = 100.0 + observed['reader_elapsed']
        return {'status': 'PASS'}
    monkeypatch.setitem(namespace, 'require_gate2_evidence', reader)
    # Track/revert keys changed by the real function; never alter Git config on disk.
    monkeypatch.setenv('GIT_CONFIG_COUNT', '0')
    monkeypatch.setenv('GIT_CONFIG_KEY_0', 'fixture.previous')
    monkeypatch.setenv('GIT_CONFIG_VALUE_0', 'fixture')
    return module['refresh'], directory, pointer, observed


def test_gate2_exit_zero_clock_overrun_rejected_without_pointer_change(tmp_path, monkeypatch):
    refresh, directory, pointer, observed = _publisher(tmp_path, monkeypatch, elapsed=1084.0)
    original = pointer.read_bytes()
    with pytest.raises(TimeoutError, match='elapsed'):
        refresh('synthetic-overrun', publish_current=True, timeout_seconds=540)
    assert pointer.read_bytes() == original
    report = directory / 'gate2-evidence-synthetic-overrun.json'
    rejected = json.loads(report.read_text())
    assert rejected['status'] == 'REJECTED_RESOURCE_BOUND'
    assert rejected['elapsed_seconds'] == 1084.0 and rejected['timeout_seconds'] == 540
    assert rejected['test_result']['passed'] == 1  # First process finished before the clock overrun.
    assert rejected['build_hashes'] == {'fixture.py': 'source hash'}
    assert rejected['test_log_sha256'] == hashlib.sha256(
        (directory / 'gate2-tests-synthetic-overrun.log').read_bytes()).hexdigest()
    assert not (directory / 'gate2-pointer-before-synthetic-overrun.json').exists()
    assert not list(directory.glob('gate2-current-*.tmp'))
    with pytest.raises(FileExistsError):
        refresh('synthetic-overrun', publish_current=True, timeout_seconds=540)


def test_gate2_inbudget_publisher_retains_counts_and_bounds_child_threads(tmp_path, monkeypatch):
    import time
    real_counter = time.perf_counter
    refresh, directory, pointer, observed = _publisher(tmp_path, monkeypatch, elapsed=1.0)
    result = refresh('synthetic-valid', publish_current=True, timeout_seconds=30)
    assert result['published_current'] is True
    report = json.loads((directory / 'gate2-evidence-synthetic-valid.json').read_text())
    assert report['status'] == 'PASS' and report['elapsed_seconds'] == 1.0
    assert report['timeout_seconds'] == 30 and report['test_result']['passed'] == 8
    assert json.loads(pointer.read_text())['evidence_file'] == 'gate2-evidence-synthetic-valid.json'
    assert [r['timeout'] for r in observed['children']] == [30, 29, 29]
    assert [r['name'] for r in report['process_groups']] == ['stdlib', 'no-torch', 'remaining']
    flat = [p for r in report['process_groups'] for p in r['modules']]
    assert len(flat) == len(set(flat)) == 8
    assert report['suite'] == 'tests/akt tests/shared_kt' and report['schema_version'] == 1
    assert observed['env']['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] == '1'
    assert observed['env']['PYTEST_ADDOPTS'] == observed['env']['PYTEST_PLUGINS'] == ''
    assert {name: observed['env'][name] for name in
            ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'CUDA_VISIBLE_DEVICES')} == {
                'OMP_NUM_THREADS': '2', 'MKL_NUM_THREADS': '2', 'OPENBLAS_NUM_THREADS': '2',
                'CUDA_VISIBLE_DEVICES': ''}
    assert time.perf_counter is real_counter  # Only the loaded script's clock was replaced.


def test_gate2_unique_run_root_supports_real_nested_pytest_basetemps(tmp_path_factory, monkeypatch):
    """Real pytest temp-path implementation/filesystem, fake test subprocess only."""
    from _pytest.tmpdir import TempPathFactory
    owned = tmp_path_factory.mktemp('g2')
    refresh, directory, pointer, observed = _publisher(owned, monkeypatch, elapsed=1.)
    namespace = refresh.__globals__
    root = directory.parents[2]
    fake_child = namespace['subprocess'].run
    bases, markers = [], []

    def child(command, **kwargs):
        base = Path(command[command.index('--basetemp') + 1])
        # getbasetemp recursively removes an existing given_basetemp: only
        # permit a fresh, absent leaf inside this newly owned fake project.
        assert base.is_absolute() and base.resolve().is_relative_to(root.resolve())
        assert not base.exists() and not base.is_symlink() and not base.is_junction()
        assert base.name in ('stdlib', 'no-torch', 'remaining')
        factory = TempPathFactory(given_basetemp=base, retention_count=0,
                                  retention_policy='all', trace=lambda *args: None,
                                  _ispytest=True)
        actual = factory.getbasetemp()  # Real mkdir(parents=False), failed before fix.
        payload = factory.mktemp('payload', numbered=False) / 'probe.txt'
        payload.write_text('real nested pytest temporary directory', encoding='utf-8')
        assert payload.read_text(encoding='utf-8') == 'real nested pytest temporary directory'
        bases.append(actual); markers.append(payload)
        return fake_child(command, **kwargs)

    monkeypatch.setitem(namespace, 'subprocess', SimpleNamespace(run=child, STDOUT=-2))
    before = pointer.read_bytes()
    long_run_id = 'g' * 80  # Longest valid public run ID must not inflate scratch paths.
    result = refresh(long_run_id, publish_current=False, timeout_seconds=30)
    assert result['published_current'] is False and pointer.read_bytes() == before
    assert [p.name for p in bases] == ['stdlib', 'no-torch', 'remaining']
    assert len({p.parent for p in bases}) == 1 and len(observed['children']) == 3
    run_root = bases[0].parent
    assert run_root.parent == root / 'artifacts/akt/local-tests'
    assert run_root.name.startswith('gate2-') and len(run_root.name) == len('gate2-') + 32
    assert all(character in '0123456789abcdef' for character in run_root.name[len('gate2-'):])
    assert long_run_id not in run_root.name
    assert result['report'].endswith(f'gate2-evidence-{long_run_id}.json')
    assert (directory / f'gate2-tests-{long_run_id}.log').is_file()
    assert (directory / f'gate2-tests-{long_run_id}.xml').is_file()
    assert run_root.is_dir() and not run_root.is_symlink() and not run_root.is_junction()
    assert all(path.is_file() for path in markers)  # Later groups did not delete prior evidence.


@pytest.mark.parametrize('elapsed', [-1.0, float('nan'), float('inf')])
def test_gate2_publisher_rejects_invalid_elapsed_and_preserves_strict_json(tmp_path, monkeypatch, elapsed):
    refresh, directory, pointer, _ = _publisher(tmp_path, monkeypatch, elapsed=elapsed)
    original = pointer.read_bytes()
    with pytest.raises(TimeoutError, match='elapsed'):
        refresh('synthetic-bad-clock', publish_current=True, timeout_seconds=30)
    raw = (directory / 'gate2-evidence-synthetic-bad-clock.json').read_text()
    def reject_numeric_constant(value):
        raise AssertionError(f'nonstandard JSON constant: {value}')
    rejected = json.loads(raw, parse_constant=reject_numeric_constant)
    assert rejected['status'] == 'REJECTED_RESOURCE_BOUND'
    assert rejected['timeout_seconds'] == 30 and rejected['test_result']['passed'] == 1
    assert pointer.read_bytes() == original


def _reader_report(tmp_path, **resource):
    from knowledge_tracing.akt.authorization import require_gate2_evidence
    from knowledge_tracing.akt.config import AKTConfig
    config = AKTConfig()
    lock = tmp_path / 'lock'
    lock.write_bytes(b'synthetic lock')
    log = tmp_path / 'gate2-tests-synthetic.log'
    log.write_bytes(b'1 passed synthetic receipt\n')
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    report = tmp_path / 'gate2-evidence-synthetic.json'
    payload = {'schema_version': 1, 'status': 'PASS', 'source_commit': config.source_commit,
               'suite': 'tests/akt tests/shared_kt',
               'test_result': {'passed': 1, 'failed': 0, 'errors': 0, 'skipped': 0},
               'lock_sha256': sha(lock), 'build_hashes': {'fixture.py': 'current hash'},
               'test_log_sha256': sha(log), **resource}
    report.write_text(json.dumps(payload), encoding='utf-8')
    pointer = tmp_path / 'gate2-current.json'
    pointer.write_text(json.dumps({'schema_version': 1, 'evidence_file': report.name,
        'evidence_sha256': sha(report), 'test_log_file': log.name, 'test_log_sha256': sha(log)}), encoding='utf-8')
    return lambda: require_gate2_evidence(config, gate2_report=pointer, lock_file=lock,
                                         build_hashes_fn=lambda: payload['build_hashes'])


@pytest.mark.parametrize('resource', [
    {}, {'elapsed_seconds': 1.0}, {'timeout_seconds': 30},
    {'elapsed_seconds': 31.0, 'timeout_seconds': 30},
    *({'elapsed_seconds': value, 'timeout_seconds': 30}
      for value in (True, False, None, '1.0', [], {}, -1.0, float('nan'), float('inf'), -float('inf'), 10**400)),
    *({'elapsed_seconds': 1.0, 'timeout_seconds': value}
      for value in (True, False, None, '30', 30.0, 0, 601, float('nan'), float('inf'))),
])
def test_gate2_reader_rejects_resource_bypass_even_after_rehash(tmp_path, resource):
    with pytest.raises(ValueError, match='elapsed|timeout|resource'):
        _reader_report(tmp_path, **resource)()


@pytest.mark.parametrize('elapsed,timeout', [(1.0, 30), (30.0, 30), (0, 1), (600.0, 600)])
def test_gate2_reader_accepts_finite_elapsed_within_declared_budget(tmp_path, elapsed, timeout):
    assert _reader_report(tmp_path, elapsed_seconds=elapsed, timeout_seconds=timeout)()['status'] == 'PASS'


@pytest.mark.parametrize('relative', [False, True])
def test_gate2_explicit_linux_lock_is_bound_to_report_and_reader(tmp_path, monkeypatch, relative):
    refresh, directory, _, observed = _publisher(tmp_path, monkeypatch, elapsed=1.0)
    root = directory.parents[2]
    selected = root / 'artifacts/akt/runtime/linux/candidate-linux-cuda.lock.txt'
    selected.parent.mkdir(parents=True)
    selected.write_bytes(b'example @ https://files.pythonhosted.org/example.whl --hash=sha256:fixture\n')
    argument = selected.relative_to(root) if relative else selected
    refresh('synthetic-linux', publish_current=True, timeout_seconds=30, lock_file=argument)
    payload = json.loads((directory / 'gate2-evidence-synthetic-linux.json').read_text())
    assert payload['lock_sha256'] == hashlib.sha256(selected.read_bytes()).hexdigest()
    assert payload['lock_sha256'] != hashlib.sha256((root / 'requirements-akt.lock.txt').read_bytes()).hexdigest()
    assert payload['lock_file'] == str(selected.resolve())
    assert observed['reader_kwargs']['lock_file'] == selected.resolve()
    assert observed['reader_kwargs']['project_root'] == root.resolve()


def test_gate2_default_lock_provenance_remains_windows_fixture(tmp_path, monkeypatch):
    refresh, directory, _, observed = _publisher(tmp_path, monkeypatch, elapsed=1.0)
    expected = directory.parents[2] / 'requirements-akt.lock.txt'
    refresh('synthetic-default', publish_current=True, timeout_seconds=30)
    payload = json.loads((directory / 'gate2-evidence-synthetic-default.json').read_text())
    assert payload['lock_file'] == str(expected.resolve())
    assert payload['lock_sha256'] == hashlib.sha256(expected.read_bytes()).hexdigest()
    assert observed['reader_kwargs']['lock_file'] == expected.resolve()


@pytest.mark.parametrize('case', ['outside', 'missing', 'private', 'protected', 'directory', 'unapproved_root'])
def test_gate2_invalid_selected_lock_rejects_before_child(tmp_path, monkeypatch, case):
    refresh, directory, pointer, observed = _publisher(tmp_path, monkeypatch, elapsed=1.0)
    root = directory.parents[2]
    paths = {'outside': tmp_path / 'outside.lock.txt',
             'missing': root / 'artifacts/akt/missing.lock.txt',
             'private': root / 'artifacts/akt/private/lock.txt',
             'protected': root / 'dataset/lock.txt',
             'directory': root / 'artifacts/akt/runtime',
             'unapproved_root': root / 'other.lock.txt'}
    selected = paths[case]
    if case == 'directory':
        selected.mkdir(parents=True)
    elif case != 'missing':
        selected.parent.mkdir(parents=True, exist_ok=True)
        selected.write_bytes(b'not an allowed lock')
    original = pointer.read_bytes()
    with pytest.raises(ValueError, match='lock'):
        refresh('synthetic-invalid', publish_current=True, lock_file=selected)
    assert not observed and pointer.read_bytes() == original
    assert not (directory / 'gate2-evidence-synthetic-invalid.json').exists()


def test_gate2_selected_lock_drift_rejects_before_publication(tmp_path, monkeypatch):
    refresh, directory, pointer, observed = _publisher(tmp_path, monkeypatch, elapsed=1.0)
    selected = directory.parents[2] / 'artifacts/akt/runtime/linux.lock.txt'
    selected.parent.mkdir(parents=True)
    selected.write_bytes(b'original selected Linux lock')
    namespace = refresh.__globals__
    child = namespace['subprocess'].run

    def drift(*args, **kwargs):
        result = child(*args, **kwargs)
        selected.write_bytes(b'changed during synthetic child')
        return result

    monkeypatch.setitem(namespace, 'subprocess', SimpleNamespace(run=drift, STDOUT=-2))
    original = pointer.read_bytes()
    with pytest.raises(ValueError, match='source or lock changed'):
        refresh('synthetic-drift', publish_current=True, timeout_seconds=30, lock_file=selected)
    assert observed and pointer.read_bytes() == original
    assert not (directory / 'gate2-evidence-synthetic-drift.json').exists()


def test_gate2_partition_is_disjoint_complete_and_keeps_pure_import_contexts(tmp_path, monkeypatch):
    refresh, directory, _, _ = _publisher(tmp_path, monkeypatch, elapsed=0.)
    ns = refresh.__globals__; root = directory.parents[2]
    groups = ns['test_partition'](root)
    assert groups[0] == ('stdlib', list(ns['STRICT_STDLIB']))
    assert groups[1] == ('no-torch', list(ns['NO_TORCH']))
    assert 'tests/shared_kt/test_simulator_corpus_publisher.py' in groups[1][1]
    assert 'tests/shared_kt/test_simulator_corpus_reader.py' in groups[1][1]
    flat = [p for _, modules in groups for p in modules]
    expected = sorted(p.relative_to(root).as_posix() for base in ('tests/akt', 'tests/shared_kt')
                      for p in (root / base).glob('test_*.py'))
    assert sorted(flat) == expected and len(flat) == len(set(flat)) == 8


@pytest.mark.parametrize('index', range(7))
def test_gate2_missing_required_pure_module_fails_before_child(tmp_path, monkeypatch, index):
    refresh, directory, pointer, observed = _publisher(tmp_path, monkeypatch, elapsed=0.)
    ns = refresh.__globals__; root = directory.parents[2]
    (root / (*ns['STRICT_STDLIB'], *ns['NO_TORCH'])[index]).unlink()
    original = pointer.read_bytes()
    with pytest.raises(ValueError, match='every explicit pure'):
        refresh('missing-group', publish_current=True, timeout_seconds=30)
    assert not observed and pointer.read_bytes() == original


def test_gate2_empty_remaining_group_is_not_silently_omitted(tmp_path, monkeypatch):
    refresh, directory, pointer, observed = _publisher(tmp_path, monkeypatch, elapsed=0.)
    (directory.parents[2] / 'tests/akt/test_fixture_remaining.py').unlink()
    original = pointer.read_bytes()
    with pytest.raises(ValueError, match='without empty groups'):
        refresh('empty-group', publish_current=True, timeout_seconds=30)
    assert not observed and pointer.read_bytes() == original


@pytest.mark.parametrize('group,completed_calls', [('stdlib', 1), ('no-torch', 2), ('remaining', 3)])
def test_gate2_any_child_failure_stops_and_never_publishes(tmp_path, monkeypatch, group, completed_calls):
    refresh, directory, pointer, observed = _publisher(tmp_path, monkeypatch, elapsed=0.)
    observed['returncodes'] = {group: 1}; original = pointer.read_bytes()
    with pytest.raises(RuntimeError, match='group .* failed'):
        refresh('child-failure', publish_current=True, timeout_seconds=30)
    assert len(observed['children']) == completed_calls and pointer.read_bytes() == original
    assert not (directory / 'gate2-evidence-child-failure.json').exists()


@pytest.mark.parametrize('problem', ['failures', 'errors', 'skipped', 'zero'])
def test_gate2_bad_second_group_junit_never_publishes(tmp_path, monkeypatch, problem):
    refresh, directory, pointer, observed = _publisher(tmp_path, monkeypatch, elapsed=0.)
    observed['xml_problems'] = {'no-torch': problem}; original = pointer.read_bytes()
    with pytest.raises(ValueError, match='without failures'):
        refresh('bad-group-xml', publish_current=True, timeout_seconds=30)
    assert len(observed['children']) == 2 and pointer.read_bytes() == original
    assert not (directory / 'gate2-evidence-bad-group-xml.json').exists()


def test_gate2_budget_is_cumulative_and_no_third_child_after_exhaustion(tmp_path, monkeypatch):
    refresh, directory, pointer, observed = _publisher(tmp_path, monkeypatch, elapsed=0.)
    observed['per_child_seconds'] = [15., 15., 0.]; original = pointer.read_bytes()
    with pytest.raises(TimeoutError, match='elapsed'):
        refresh('global-deadline', publish_current=True, timeout_seconds=30)
    assert [c['timeout'] for c in observed['children']] == [30., 15.]
    report = json.loads((directory / 'gate2-evidence-global-deadline.json').read_bytes())
    assert report['status'] == 'REJECTED_RESOURCE_BOUND' and report['elapsed_seconds'] == 30.
    assert report['test_result']['passed'] == 7 and pointer.read_bytes() == original


def test_gate2_exit_zero_final_child_overruns_remaining_global_budget(tmp_path, monkeypatch):
    refresh, directory, pointer, observed = _publisher(tmp_path, monkeypatch, elapsed=0.)
    observed['per_child_seconds'] = [12., 12., 12.]; original = pointer.read_bytes()
    with pytest.raises(TimeoutError, match='elapsed'):
        refresh('late-child', publish_current=True, timeout_seconds=30)
    assert [c['timeout'] for c in observed['children']] == [30., 18., 6.]
    report = json.loads((directory / 'gate2-evidence-late-child.json').read_bytes())
    assert report['status'] == 'REJECTED_RESOURCE_BOUND' and report['elapsed_seconds'] == 36.
    assert report['test_result']['passed'] == 8 and pointer.read_bytes() == original


def test_gate2_duplicate_testcase_across_processes_rejects_aggregate(tmp_path, monkeypatch):
    refresh, directory, pointer, observed = _publisher(tmp_path, monkeypatch, elapsed=0.)
    observed['duplicate_case'] = True; original = pointer.read_bytes()
    with pytest.raises(ValueError, match='duplicate or invalid testcase'):
        refresh('duplicate-case', publish_current=True, timeout_seconds=30)
    assert len(observed['children']) == 3 and pointer.read_bytes() == original
    assert not (directory / 'gate2-evidence-duplicate-case.json').exists()


def test_gate2_final_reader_deadline_rejects_fresh_report_before_pointer(tmp_path, monkeypatch):
    refresh, directory, pointer, observed = _publisher(tmp_path, monkeypatch, elapsed=1.)
    observed['reader_elapsed'] = 31.; original = pointer.read_bytes()
    with pytest.raises(TimeoutError, match='elapsed'):
        refresh('late-reader', publish_current=True, timeout_seconds=30)
    assert pointer.read_bytes() == original
    report = json.loads((directory / 'gate2-evidence-late-reader.json').read_bytes())
    assert report['status'] == 'REJECTED_RESOURCE_BOUND' and report['elapsed_seconds'] == 31.
    assert report['test_result']['passed'] == 8


def test_gate2_postpublication_deadline_restores_exact_previous_pointer(tmp_path, monkeypatch):
    refresh, directory, pointer, _ = _publisher(tmp_path, monkeypatch, elapsed=1.)
    clock = refresh.__globals__['_fixture_clock']; original = pointer.read_bytes()
    replace = Path.replace
    def late_replace(path, target):
        result = replace(path, target)
        if Path(target) == pointer:
            clock.now = 131.
        return result
    monkeypatch.setattr(Path, 'replace', late_replace)
    with pytest.raises(TimeoutError, match='elapsed'):
        refresh('late-publication', publish_current=True, timeout_seconds=30)
    assert pointer.read_bytes() == original
    report = json.loads((directory / 'gate2-evidence-late-publication.json').read_bytes())
    assert report['status'] == 'REJECTED_RESOURCE_BOUND' and report['late_pointer_rollback'] is True
