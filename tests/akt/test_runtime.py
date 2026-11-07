import json
import hashlib
from pathlib import Path
import sys
import types

import pytest

import scripts.akt.check_runtime as runtime_module
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


def test_probe_rejects_wrong_interpreter_before_loading_source(tmp_path):
    with pytest.raises(ValueError, match='interpreter'):
        inspect_runtime(tmp_path, expected_env=tmp_path / 'not-current-env')


@pytest.mark.parametrize('platform_tag', ['win_amd64', 'manylinux_2_17_x86_64'])
def test_lock_accepts_percent_encoded_wheel_name(tmp_path, monkeypatch, platform_tag):
    from pip._vendor.packaging import tags

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
    from pip._vendor.packaging import tags

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
