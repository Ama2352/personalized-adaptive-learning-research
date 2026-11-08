"""Kiểm tra runtime AKT hoặc tạo lock file từ báo cáo resolver của pip."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import platform
import re
import shutil
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

from knowledge_tracing.akt.config import SOURCE_COMMIT  # noqa: E402
from knowledge_tracing.akt.authorization import validate_runtime_interpreter  # noqa: E402
from knowledge_tracing.akt.provenance import sha256_file, verify_upstream  # noqa: E402


def validate_output_path(path: Path, *, kind: str, project_root: Path = ROOT) -> Path:
    root, output = project_root.resolve(), path.resolve()
    protected = (root / 'dataset', root / 'artifacts/bkt_baseline', root / 'venv', root / '.wsl')
    if any(output.is_relative_to(item.resolve()) for item in protected):
        raise ValueError('invalid output path')
    if kind == 'lock':
        allowed = output == root / 'requirements-akt.lock.txt'
    elif kind == 'runtime':
        base = (root / 'artifacts/akt').resolve()
        allowed = output.is_relative_to(base) and output != base
    else:
        allowed = False
    if not allowed:
        raise ValueError('invalid output path')
    return output


def write_lock_from_report(report_path: Path, output_path: Path, *,
                           requirements_path: Path | None = None) -> None:
    from packaging.requirements import Requirement
    from packaging.tags import sys_tags
    from packaging.utils import canonicalize_name, parse_wheel_filename

    report = json.loads(report_path.read_text(encoding='utf-8'))
    entries = report.get('install')
    if not isinstance(entries, list) or not entries:
        raise ValueError('resolver report has no distributions')
    compatible = set(sys_tags())
    rows = []
    seen = set()
    selected = {}
    for entry in entries:
        metadata = entry['metadata']
        name, version = metadata['name'], metadata['version']
        download = entry['download_info']
        url = download['url']
        parsed = urlsplit(url)
        if parsed.scheme != 'https' or not parsed.path.endswith('.whl'):
            raise ValueError('only HTTPS wheel downloads are permitted')
        if parsed.hostname not in {'files.pythonhosted.org', 'download.pytorch.org', 'download-r2.pytorch.org'}:
            raise ValueError('untrusted wheel host')
        wheel_name, wheel_version, _, tags = parse_wheel_filename(unquote(Path(parsed.path).name))
        digest = download['archive_info'].get('hashes', {}).get('sha256', '')
        if (canonicalize_name(name) != canonicalize_name(wheel_name)
                or str(wheel_version) != version or not (tags & compatible)
                or not re.fullmatch(r'[0-9a-f]{64}', digest)
                or canonicalize_name(name) in seen):
            raise ValueError('invalid wheel identity, platform or SHA-256')
        seen.add(canonicalize_name(name))
        selected[canonicalize_name(name)] = (version, parsed, digest)
        rows.append(f'{name} @ {url} --hash=sha256:{digest}')
    if requirements_path is not None:
        for line in requirements_path.read_text(encoding='utf-8').splitlines():
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            req = Requirement(line.strip())
            key = canonicalize_name(req.name)
            if key not in selected:
                raise ValueError(f'missing direct requirement: {req.name}')
            version, parsed, digest = selected[key]
            if req.url:
                required = urlsplit(req.url)
                if (required._replace(fragment='') != parsed._replace(fragment='')
                        or required.fragment != f'sha256={digest}'):
                    raise ValueError(f'direct wheel mismatch: {req.name}')
            elif not req.specifier.contains(version, prereleases=True):
                raise ValueError(f'version mismatch: {req.name}')
    with output_path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write('\n'.join(sorted(rows, key=str.casefold)) + '\n')


def inspect_runtime(upstream_root: Path, *, required_device: str = 'cpu',
                    expected_env: Path | None = None, project_root: Path = ROOT,
                    lock_file: Path | None = None) -> dict:
    project_root = project_root.resolve()
    expected_env = expected_env if expected_env is not None else project_root / '.venv'
    lock_file = lock_file if lock_file is not None else project_root / 'requirements-akt.lock.txt'
    executable = validate_runtime_interpreter(expected_env, executable=sys.executable,
                                              prefix=sys.prefix, platform_id=sys.platform)
    if required_device not in {'cpu', 'cuda'}:
        raise ValueError('unsupported device')
    source = verify_upstream(upstream_root, SOURCE_COMMIT)
    import numpy
    import psutil
    import torch

    environment = expected_env.resolve()
    for name, module in (('torch', torch), ('numpy', numpy)):
        origin = getattr(module, '__file__', None)
        if not origin or not Path(origin).resolve().is_relative_to(environment):
            raise ValueError(f'{name} origin is outside the isolated environment')
    if required_device == 'cuda' and not torch.cuda.is_available():
        raise ValueError('CUDA requested but unavailable')
    spec = importlib.util.spec_from_file_location('akt_upstream_reference', upstream_root / 'akt.py')
    if spec is None or spec.loader is None:
        raise ValueError('unable to load upstream module')
    module = importlib.util.module_from_spec(spec)
    previous_bytecode_setting = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous_bytecode_setting
    module.device = torch.device(required_device)
    if not hasattr(module, 'AKT'):
        raise ValueError('upstream AKT class missing')
    return {'runtime_schema_version': 2, 'platform_id': sys.platform,
            'python': str(executable), 'python_prefix': str(Path(sys.prefix).resolve()),
            'project_root': str(project_root), 'lock_file': str(lock_file.resolve()),
            'python_version': sys.version,
            'platform': platform.platform(),
            'lock_sha256': sha256_file(lock_file),
            'available_ram_bytes': psutil.virtual_memory().available,
            'disk_free_bytes': shutil.disk_usage(project_root).free,
            'torch_version': torch.__version__, 'torch_origin': torch.__file__,
            'numpy_version': numpy.__version__, 'numpy_origin': numpy.__file__,
            'device': required_device, 'cuda_available': torch.cuda.is_available(),
            'source': source}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--resolution-report', type=Path)
    parser.add_argument('--write-lock', type=Path)
    parser.add_argument('--upstream', type=Path)
    parser.add_argument('--device', default='cpu')
    parser.add_argument('--lock-file', type=Path,
                        help='lock đầu vào cho runtime report; không dùng lock Windows để cài Linux/CUDA')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.resolution_report and args.write_lock:
        output = validate_output_path(args.write_lock, kind='lock', project_root=ROOT)
        write_lock_from_report(args.resolution_report, output,
                               requirements_path=ROOT / 'requirements-akt.in')
    elif args.upstream and args.output:
        output = validate_output_path(args.output, kind='runtime', project_root=ROOT)
        result = inspect_runtime(args.upstream, required_device=args.device,
                                 project_root=ROOT, lock_file=args.lock_file)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, indent=2)
    else:
        parser.error('supply a report and lock, or upstream and output')


if __name__ == '__main__':
    main()
