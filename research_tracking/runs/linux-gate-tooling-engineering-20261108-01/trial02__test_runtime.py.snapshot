import json
import hashlib
from pathlib import Path
import sys
import types

import pytest

import scripts.akt.check_runtime as runtime_module
import knowledge_tracing.akt.authorization as authorization_module
import knowledge_tracing.akt.config as config_module
from scripts.akt.check_runtime import inspect_runtime, validate_output_path, write_lock_from_report


def report_entry(url, sha='a' * 64):
    return {'metadata': {'name': 'Example', 'version': '1.2.3'},
            'download_info': {'url': url, 'archive_info': {'hashes': {'sha256': sha}}}}


def test_lock_report_requires_wheel_hashes_and_exact_urls(tmp_path):
    report = tmp_path / 'report.json'
    lock = tmp_path / 'lock.txt'
    url = 'https://files.pythonhosted.org/example-1.2.3-py3-none-any.whl'
    report.write_text(json.dumps({'install': [report_entry(url)]}), encoding='utf-8')
    write_lock_from_report(report, lock)
    assert lock.read_text(encoding='utf-8').strip() == f'Example @ {url} --hash=sha256:{"a" * 64}'
    for entry in (report_entry(url, 'bad'), report_entry('https://example.invalid/example.tar.gz')):
        report.write_text(json.dumps({'install': [entry]}), encoding='utf-8')
        with pytest.raises(ValueError):
            write_lock_from_report(report, tmp_path / 'bad.txt')


def test_lock_report_uses_public_packaging_without_target_pip(tmp_path, monkeypatch):
    """Target runtime deliberately has no pip; tooling must use pinned packaging."""
    import builtins
    original = builtins.__import__

    def without_pip(name, *args, **kwargs):
        if name == 'pip' or name.startswith('pip.'):
            raise ModuleNotFoundError('target pip intentionally unavailable')
        return original(name, *args, **kwargs)

    report = tmp_path / 'report.json'
    report.write_text(json.dumps({'install': [report_entry(
        'https://files.pythonhosted.org/example-1.2.3-py3-none-any.whl')]}), encoding='utf-8')
    monkeypatch.setattr(builtins, '__import__', without_pip)
    lock = tmp_path / 'without-pip.lock.txt'
    write_lock_from_report(report, lock)
    assert lock.read_text().startswith('Example @ https://files.pythonhosted.org/')


def test_probe_rejects_wrong_interpreter_before_loading_source(tmp_path):
    with pytest.raises(ValueError, match='interpreter'):
        inspect_runtime(tmp_path, expected_env=tmp_path / 'not-current-env')


@pytest.mark.parametrize('platform_tag', ['win_amd64', 'manylinux_2_17_x86_64'])
def test_lock_accepts_percent_encoded_wheel_name(tmp_path, monkeypatch, platform_tag):
    from packaging import tags

    # Chọn môi trường resolver giả lập rõ ràng, độc lập Python/OS của host chạy test.
    monkeypatch.setattr(tags, 'sys_tags', lambda: iter([tags.Tag('cp313', 'cp313', platform_tag)]))
    url = f'https://download-r2.pytorch.org/torch-2.7.1%2Bcpu-cp313-cp313-{platform_tag}.whl'
    entry = report_entry(url)
    entry['metadata'] = {'name': 'torch', 'version': '2.7.1+cpu'}
    report = tmp_path / 'report.json'
    report.write_text(json.dumps({'install': [entry]}), encoding='utf-8')
    lock = tmp_path / 'lock.txt'
    write_lock_from_report(report, lock)
    assert lock.read_text(encoding='utf-8') == f'torch @ {url} --hash=sha256:{"a" * 64}\n'


@pytest.mark.parametrize(('wheel_platform', 'runtime_platform'), [
    ('win_amd64', 'manylinux_2_17_x86_64'),
    ('manylinux_2_17_x86_64', 'win_amd64'),
])
def test_lock_rejects_percent_encoded_wheel_for_incompatible_platform(
        tmp_path, monkeypatch, wheel_platform, runtime_platform):
    from packaging import tags

    monkeypatch.setattr(tags, 'sys_tags', lambda: iter([tags.Tag('cp313', 'cp313', runtime_platform)]))
    url = f'https://download-r2.pytorch.org/torch-2.7.1%2Bcpu-cp313-cp313-{wheel_platform}.whl'
    entry = report_entry(url)
    entry['metadata'] = {'name': 'torch', 'version': '2.7.1+cpu'}
    report = tmp_path / 'report.json'
    report.write_text(json.dumps({'install': [entry]}), encoding='utf-8')
    lock = tmp_path / 'lock.txt'

    with pytest.raises(ValueError, match='invalid wheel identity, platform or SHA-256'):
        write_lock_from_report(report, lock)

    assert not lock.exists()


def test_probe_rejects_modules_imported_from_outside_isolated_environment(tmp_path, monkeypatch):
    env = tmp_path / 'isolated'
    env.mkdir()
    monkeypatch.setattr(sys, 'prefix', str(env))
    entry = env / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    monkeypatch.setattr(sys, 'executable', str(entry))
    monkeypatch.setattr(runtime_module, 'verify_upstream', lambda *args: {})
    for name in ('torch', 'numpy'):
        module = types.ModuleType(name)
        module.__file__ = str(tmp_path / 'outside' / name / '__init__.py')
        monkeypatch.setitem(sys.modules, name, module)
    with pytest.raises(ValueError, match='origin'):
        inspect_runtime(tmp_path, expected_env=env)


def test_probe_does_not_write_bytecode_into_upstream_checkout(tmp_path, monkeypatch):
    env = tmp_path / 'isolated'
    env.mkdir()
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'akt.py').write_text('class AKT: pass\n', encoding='utf-8')
    monkeypatch.setattr(sys, 'prefix', str(env))
    entry = env / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    monkeypatch.setattr(sys, 'executable', str(entry))
    monkeypatch.setattr(sys, 'dont_write_bytecode', False)
    monkeypatch.setattr(runtime_module, 'verify_upstream', lambda *args: {})
    numpy = types.ModuleType('numpy')
    numpy.__file__, numpy.__version__ = str(env / 'numpy.py'), '1'
    torch = types.ModuleType('torch')
    torch.__file__, torch.__version__ = str(env / 'torch.py'), '1'
    torch.device = lambda name: name
    torch.cuda = types.SimpleNamespace(is_available=lambda: False)
    monkeypatch.setitem(sys.modules, 'numpy', numpy)
    monkeypatch.setitem(sys.modules, 'torch', torch)
    inspect_runtime(source, expected_env=env)
    assert not (source / '__pycache__').exists()
    assert sys.dont_write_bytecode is False


def isolated_runtime_fixture(tmp_path, monkeypatch, platform_id):
    """Giả lập module-local sys; không sửa os.name hoặc cấp/cài runtime thật."""
    env = tmp_path / '.venv'
    env.mkdir()
    entry = env / ('Scripts/python.exe' if platform_id == 'win32' else 'bin/python')
    interpreter = types.SimpleNamespace(executable=str(entry), prefix=str(env),
                                       platform=platform_id, version='synthetic-python',
                                       dont_write_bytecode=sys.dont_write_bytecode)
    monkeypatch.setattr(runtime_module, 'sys', interpreter)
    monkeypatch.setattr(authorization_module, 'sys', interpreter)
    monkeypatch.setattr(config_module, 'PROJECT_ROOT', tmp_path)
    source = {'commit': config_module.SOURCE_COMMIT, 'files': {'akt.py': 'synthetic-source'}}
    monkeypatch.setattr(runtime_module, 'verify_upstream', lambda *args: source)
    monkeypatch.setattr(authorization_module, 'verify_upstream', lambda *args: source)
    upstream = tmp_path / 'upstream'
    upstream.mkdir()
    (upstream / 'akt.py').write_text('class AKT: pass\n', encoding='utf-8')
    lock = tmp_path / 'requirements-linux-cuda.lock.txt'
    lock.write_text('synthetic lock; không là artifact cài runtime\n', encoding='utf-8')
    for name in ('torch', 'numpy'):
        module = types.ModuleType(name)
        module.__file__ = str(env / 'lib/site-packages' / name / '__init__.py')
        module.__version__ = 'synthetic-version'
        if name == 'torch':
            module.device = lambda name: name
            module.cuda = types.SimpleNamespace(is_available=lambda: False)
        monkeypatch.setitem(sys.modules, name, module)
    config = config_module.AKTConfig(project_root=tmp_path, source_root=upstream,
                                     output_dir=tmp_path / 'artifacts/akt/preflight-fixture')
    report = inspect_runtime(upstream, project_root=tmp_path, lock_file=lock)
    report_path = tmp_path / 'runtime.json'
    return config, report, report_path, lock, interpreter


def preflight_fixture(config, report, report_path, lock):
    report_path.write_text(json.dumps(report), encoding='utf-8')
    return authorization_module.preflight(config, project_root=config.project_root,
                                          runtime_report_path=report_path, lock_file=lock)


@pytest.mark.parametrize('platform_id', ['win32', 'linux'])
def test_fresh_runtime_report_binds_explicit_root_lock_and_actual_interpreter(tmp_path, monkeypatch, platform_id):
    config, report, path, lock, interpreter = isolated_runtime_fixture(tmp_path, monkeypatch, platform_id)
    assert report['runtime_schema_version'] == 2
    assert report['platform_id'] == platform_id
    assert report['python'] == interpreter.executable
    assert report['python_prefix'] == str((tmp_path / '.venv').resolve())
    assert report['project_root'] == str(tmp_path.resolve())
    assert report['lock_file'] == str(lock.resolve())
    assert report['lock_sha256'] == hashlib.sha256(lock.read_bytes()).hexdigest()
    result = preflight_fixture(config, report, path, lock)
    assert result['status'] == 'ready'
    assert result['runtime_report_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize('platform_id', ['win32', 'linux'])
@pytest.mark.parametrize('module_name', ['torch', 'numpy'])
def test_inherited_runtime_module_is_not_accepted_by_inspection_or_preflight(
        tmp_path, monkeypatch, platform_id, module_name):
    config, report, path, lock, _ = isolated_runtime_fixture(tmp_path, monkeypatch, platform_id)
    outside = str(tmp_path / 'global/site-packages' / module_name / '__init__.py')
    monkeypatch.setattr(sys.modules[module_name], '__file__', outside)
    with pytest.raises(ValueError, match='origin'):
        inspect_runtime(config.source_root, project_root=tmp_path, lock_file=lock)
    report[module_name + '_origin'] = outside
    with pytest.raises(ValueError, match='Gate 1'):
        preflight_fixture(config, report, path, lock)


def test_linux_symlink_entry_remains_distinct_from_base_interpreter(tmp_path, monkeypatch):
    env = tmp_path / '.venv'
    entry = env / 'bin/python'
    base = tmp_path / 'global/bin/python'
    original_resolve = Path.resolve

    def simulated_symlink_resolution(path, *args, **kwargs):
        return base if path == entry else original_resolve(path, *args, **kwargs)

    # Không tạo symlink cần đặc quyền Windows; giả lập resolve của đúng executable entry.
    with monkeypatch.context() as patch:
        patch.setattr(Path, 'resolve', simulated_symlink_resolution)
        assert entry.resolve() == base
        result = authorization_module.validate_runtime_interpreter(
            env, executable=str(entry), prefix=str(env), platform_id='linux')
        assert result == entry
        with pytest.raises(ValueError, match='interpreter'):
            authorization_module.validate_runtime_interpreter(
                env, executable=str(base), prefix=str(env), platform_id='linux')


@pytest.mark.parametrize('platform_id', ['win32', 'linux'])
@pytest.mark.parametrize('field', ['executable', 'prefix'])
def test_actual_interpreter_binding_cannot_be_replaced_by_a_matching_report(
        tmp_path, monkeypatch, platform_id, field):
    config, report, path, lock, interpreter = isolated_runtime_fixture(tmp_path, monkeypatch, platform_id)
    setattr(interpreter, field, str(tmp_path / 'global/python'))
    with pytest.raises(ValueError, match='interpreter'):
        preflight_fixture(config, report, path, lock)
    with pytest.raises(ValueError, match='interpreter'):
        inspect_runtime(config.source_root, project_root=tmp_path, lock_file=lock)


@pytest.mark.parametrize(('field', 'bad_value'), [
    ('runtime_schema_version', True), ('runtime_schema_version', 2.0),
    ('runtime_schema_version', None), ('runtime_schema_version', 3),
    ('platform_id', 'win32'), ('platform_id', True),
    ('python', False), ('python_prefix', None), ('project_root', '.'),
    ('lock_file', False), ('source', []), ('lock_sha256', True),
    ('torch_origin', None), ('numpy_origin', '../global/numpy.py'),
    ('device', True), ('cuda_available', 1),
])
def test_linux_report_schema_and_types_are_strict(tmp_path, monkeypatch, field, bad_value):
    config, report, path, lock, _ = isolated_runtime_fixture(tmp_path, monkeypatch, 'linux')
    report[field] = bad_value
    with pytest.raises(ValueError, match='Gate 1'):
        preflight_fixture(config, report, path, lock)


@pytest.mark.parametrize('changed', ['python', 'python_prefix', 'project_root', 'lock_file', 'source', 'lock_sha256'])
def test_fresh_report_rejects_changed_identity_even_when_types_are_valid(tmp_path, monkeypatch, changed):
    config, report, path, lock, _ = isolated_runtime_fixture(tmp_path, monkeypatch, 'linux')
    if changed == 'source':
        report[changed] = {'commit': 'wrong-source'}
    elif changed == 'lock_sha256':
        report[changed] = '0' * 64
    else:
        report[changed] = str(tmp_path / 'different' / changed)
    with pytest.raises(ValueError, match='Gate 1'):
        preflight_fixture(config, report, path, lock)


@pytest.mark.parametrize('platform_id', ['win32', 'linux'])
def test_legacy_report_remains_windows_only_without_reusing_it_for_linux(tmp_path, monkeypatch, platform_id):
    config, report, path, lock, _ = isolated_runtime_fixture(tmp_path, monkeypatch, platform_id)
    for key in ('runtime_schema_version', 'platform_id', 'python_prefix', 'project_root', 'lock_file'):
        del report[key]
    report['platform'] = 'Windows-fixture'
    if platform_id == 'win32':
        assert preflight_fixture(config, report, path, lock)['status'] == 'ready'
    else:
        with pytest.raises(ValueError, match='Gate 1'):
            preflight_fixture(config, report, path, lock)


@pytest.mark.parametrize('field', ['torch_origin', 'numpy_origin', 'lock_sha256', 'python'])
def test_legacy_windows_report_still_rejects_invalid_origin_lock_or_executable(tmp_path, monkeypatch, field):
    config, report, path, lock, _ = isolated_runtime_fixture(tmp_path, monkeypatch, 'win32')
    for key in ('runtime_schema_version', 'platform_id', 'python_prefix', 'project_root', 'lock_file'):
        del report[key]
    report['platform'] = 'Windows-fixture'
    report[field] = '0' * 64 if field == 'lock_sha256' else str(tmp_path / 'global' / field)
    with pytest.raises(ValueError, match='Gate 1'):
        preflight_fixture(config, report, path, lock)


@pytest.mark.parametrize('changed', ['source', 'lock'])
def test_report_becomes_stale_when_actual_source_or_lock_changes(tmp_path, monkeypatch, changed):
    config, report, path, lock, _ = isolated_runtime_fixture(tmp_path, monkeypatch, 'linux')
    if changed == 'source':
        monkeypatch.setattr(authorization_module, 'verify_upstream', lambda *args: {'commit': 'changed'})
    else:
        lock.write_text('changed lock', encoding='utf-8')
    with pytest.raises(ValueError, match='Gate 1'):
        preflight_fixture(config, report, path, lock)


def test_unsupported_runtime_platform_is_rejected_before_source_load(tmp_path, monkeypatch):
    interpreter = types.SimpleNamespace(executable=str(tmp_path / '.venv/bin/python'),
                                       prefix=str(tmp_path / '.venv'), platform='darwin')
    monkeypatch.setattr(runtime_module, 'sys', interpreter)
    monkeypatch.setattr(runtime_module, 'verify_upstream', lambda *args: pytest.fail('source must not load'))
    with pytest.raises(ValueError, match='platform'):
        inspect_runtime(tmp_path, project_root=tmp_path)


def test_runtime_cli_can_bind_an_explicit_linux_lock_with_trusted_output_guard(tmp_path, monkeypatch):
    config, _, _, lock, interpreter = isolated_runtime_fixture(tmp_path, monkeypatch, 'linux')
    monkeypatch.setattr(runtime_module, 'ROOT', tmp_path)
    interpreter.argv = ['check_runtime', '--upstream', str(config.source_root), '--device', 'cpu',
                        '--lock-file', str(lock), '--output', str(tmp_path / 'artifacts/akt/runtime-linux.json')]
    monkeypatch.setattr(sys, 'argv', interpreter.argv)
    runtime_module.main()
    report = json.loads((tmp_path / 'artifacts/akt/runtime-linux.json').read_text(encoding='utf-8'))
    assert report['runtime_schema_version'] == 2 and report['platform_id'] == 'linux'
    assert report['lock_file'] == str(lock.resolve())
    assert report['lock_sha256'] == hashlib.sha256(lock.read_bytes()).hexdigest()


@pytest.mark.parametrize(('requested', 'reported', 'cuda_available', 'accepted'), [
    ('cpu', 'cpu', False, True), ('cpu', 'cpu', True, True),
    ('cuda', 'cpu', True, False), ('cpu', 'cuda', True, False),
    ('cuda', 'cuda', False, False), ('cuda', 'cuda', True, True),
])
def test_report_device_binds_requested_mode_without_importing_torch_in_preflight(
        tmp_path, monkeypatch, requested, reported, cuda_available, accepted):
    from dataclasses import replace
    import builtins

    config, report, path, lock, _ = isolated_runtime_fixture(tmp_path, monkeypatch, 'linux')
    config = replace(config, device=requested)
    report.update(device=reported, cuda_available=cuda_available)
    original_import = builtins.__import__

    def no_heavy_import(name, *args, **kwargs):
        if name.split('.')[0] in {'torch', 'numpy'}:
            raise AssertionError('preflight phải giữ nhẹ, không import Torch/NumPy')
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', no_heavy_import)
    if accepted:
        assert preflight_fixture(config, report, path, lock)['status'] == 'ready'
    else:
        with pytest.raises(ValueError, match='Gate 1'):
            preflight_fixture(config, report, path, lock)


def test_cli_output_guard_rejects_protected_paths_without_creating_them(tmp_path):
    frozen = tmp_path / 'artifacts/bkt_baseline/new/runtime.json'
    with pytest.raises(ValueError, match='output'):
        validate_output_path(frozen, kind='runtime', project_root=tmp_path)
    with pytest.raises(ValueError, match='output'):
        validate_output_path(tmp_path / 'dataset/lock.txt', kind='lock', project_root=tmp_path)
    assert not frozen.parent.exists()
    assert validate_output_path(tmp_path / 'requirements-akt.lock.txt', kind='lock',
                                project_root=tmp_path).name == 'requirements-akt.lock.txt'


def test_lock_rejects_untrusted_wheel_host(tmp_path):
    report = tmp_path / 'report.json'
    report.write_text(json.dumps({'install': [report_entry('https://evil.invalid/example-1.2.3-py3-none-any.whl')]}), encoding='utf-8')
    with pytest.raises(ValueError, match='host'):
        write_lock_from_report(report, tmp_path / 'lock.txt')


def test_lock_rejects_report_missing_direct_requirement(tmp_path):
    report = tmp_path / 'report.json'
    report.write_text(json.dumps({'install': [report_entry('https://files.pythonhosted.org/example-1.2.3-py3-none-any.whl')]}), encoding='utf-8')
    requirements = tmp_path / 'requirements.in'
    requirements.write_text('example==1.2.3\nmissing==1.0\n', encoding='utf-8')
    with pytest.raises(ValueError, match='missing'):
        write_lock_from_report(report, tmp_path / 'lock.txt', requirements_path=requirements)


def test_cli_writes_only_to_approved_lock_path(tmp_path, monkeypatch):
    report = tmp_path / 'report.json'
    report.write_text(json.dumps({'install': [report_entry('https://files.pythonhosted.org/example-1.2.3-py3-none-any.whl')]}), encoding='utf-8')
    (tmp_path / 'requirements-akt.in').write_text('example==1.2.3\n', encoding='utf-8')
    monkeypatch.setattr(runtime_module, 'ROOT', tmp_path)
    output = tmp_path / 'requirements-akt.lock.txt'
    monkeypatch.setattr(sys, 'argv', ['check_runtime', '--resolution-report', str(report), '--write-lock', str(output)])
    runtime_module.main()
    assert output.is_file()
    forbidden = tmp_path / 'artifacts/bkt_baseline/forbidden.txt'
    monkeypatch.setattr(sys, 'argv', ['check_runtime', '--resolution-report', str(report), '--write-lock', str(forbidden)])
    with pytest.raises(ValueError, match='output'):
        runtime_module.main()
    assert not forbidden.parent.exists()


def test_native_akt_import_cpu():
    root = Path('artifacts/akt/dependencies/upstream')
    result = inspect_runtime(root, required_device='cpu', expected_env=Path('.venv'))
    assert result['device'] == 'cpu'
    assert Path(result['python']).resolve() == Path(sys.executable).resolve()
    assert result['torch_version']
    assert result['source']['commit'] == '01b7e8d7d7c862cabc9467108e3e7f2555653a88'
    assert result['lock_sha256'] == hashlib.sha256(Path('requirements-akt.lock.txt').read_bytes()).hexdigest()
    assert result['available_ram_bytes'] > 0
    assert result['disk_free_bytes'] > 0
