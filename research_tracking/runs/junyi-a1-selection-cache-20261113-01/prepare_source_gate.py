"""Đóng gói nguồn Gate A1 selection cache, không dispatch hoặc sửa ledger.

Tái dùng bundle_contents và fixtures Gate A0 đã ghim. Bản sao notebook giữ
provenance biến đổi. Tính build inventory trên đúng bytes trong ZIP bằng chính
hàm gate2_build_hashes của source được đóng gói, không import Torch.
"""

import ast
import fnmatch
import hashlib
import json
from pathlib import Path, PurePosixPath
import runpy
import zipfile


ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
RUN = 'modal-junyi-a1-selection-cpu-20261113-01'
SOURCE = ROOT/'artifacts/akt/modal/junyi-a1-selection-cache-20261113-01/source.zip'
ORIGINAL = ROOT/'artifacts/akt/modal/junyi-a0-h100-batch128-20261112-01/source.zip'
EXTRA = (
    'research_tracking/runs/cpu-junyi-graph-reconstruction-20261107-01/graph.json',
    'research_tracking/runs/junyi-comparison-preflight-20261113-01/data-audit.json',
)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def virtual_gate_build_hashes(contents):
    """Chạy riêng AST hàm inventory trên filesystem ảo từ bytes đã đóng gói."""
    class PackagePath:
        def __init__(self, name=''):
            self.path = str(name).strip('/')

        def __truediv__(self, other):
            return PackagePath('/'.join(part for part in (self.path, str(other)) if part))

        def glob(self, pattern):
            prefix = self.path + '/' if self.path else ''
            return [PackagePath(name) for name in contents
                    if name.startswith(prefix) and '/' not in name[len(prefix):]
                    and fnmatch.fnmatchcase(name[len(prefix):], pattern)]

        def relative_to(self, root):
            if root.path:
                raise ValueError('Virtual inventory root must be empty')
            return PurePosixPath(self.path)

        @property
        def name(self):
            return PurePosixPath(self.path).name

        def __lt__(self, other):
            return self.path < other.path

        def __eq__(self, other):
            return isinstance(other, PackagePath) and self.path == other.path

        def __hash__(self):
            return hash(self.path)

    source = contents['src/knowledge_tracing/akt/authorization.py'].decode('utf-8-sig')
    function = next(node for node in ast.parse(source).body
                    if isinstance(node, ast.FunctionDef) and node.name == 'gate2_build_hashes')
    namespace = dict(Path=PackagePath, PROJECT_ROOT=PackagePath(),
                     sha256_file=lambda path: digest(contents[path.path]))
    exec(compile(ast.Module(body=[function], type_ignores=[]), '<packaged-gate-inventory>', 'exec'), namespace)
    return namespace['gate2_build_hashes'](PackagePath())


def main():
    if SOURCE.exists() or (BUNDLE/'source-gate-preparation.json').exists():
        raise FileExistsError('Source freeze đã tồn tại, cần bundle mới khi đổi nguồn')
    contents, transforms = runpy.run_path(str(ROOT/'scripts/akt/build_colab_bundle.py'))['bundle_contents']()
    for relative in EXTRA:
        contents[relative] = (ROOT/relative).read_bytes()
    inherited = []
    with zipfile.ZipFile(ORIGINAL) as saved:
        old_pins = json.loads(saved.read('MANIFEST.json'))['files']
        if set(saved.namelist()) != set(old_pins) | {'MANIFEST.json'}:
            raise ValueError('Original source inventory mismatch')
        for relative, expected in old_pins.items():
            raw = saved.read(relative)
            if digest(raw) != expected:
                raise ValueError('Original source member changed')
            if relative not in contents:
                contents[relative] = raw
                inherited.append(relative)
    paper2 = ROOT/'paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20'
    for path in [*sorted((ROOT/'paper1').glob('*.ipynb')),
                 *sorted((paper2/'data/simulator_inputs').glob('*.csv'))]:
        contents.setdefault(path.relative_to(ROOT).as_posix(), path.read_bytes())
    pins = {name: digest(raw) for name, raw in sorted(contents.items())}
    build_hashes = virtual_gate_build_hashes(contents)
    build_sha = digest(json.dumps(build_hashes, sort_keys=True, separators=(',', ':')).encode())
    SOURCE.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(SOURCE, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as saved:
        for name, raw in sorted(contents.items()):
            saved.writestr(name, raw)
        saved.writestr('MANIFEST.json', json.dumps(dict(files=pins,
            notebook_copy_transforms=transforms), sort_keys=True))
    with zipfile.ZipFile(SOURCE) as saved:
        if saved.testzip() is not None or set(saved.namelist()) != set(pins) | {'MANIFEST.json'}:
            raise ValueError('New source ZIP verification failed')
        if any(digest(saved.read(name)) != expected for name, expected in pins.items()):
            raise ValueError('New source member verification failed')
    result = dict(status='SOURCE_GATE_PREPARED_NOT_DISPATCHED', run_id=RUN,
        source=SOURCE.relative_to(ROOT).as_posix(), source_sha256=digest(SOURCE.read_bytes()),
        bytes=SOURCE.stat().st_size, files=len(pins), transforms=transforms,
        source_files=pins, gate2_build_hashes=build_hashes, source_build_sha256=build_sha,
        inventory_authority='AST gate2_build_hashes từ authorization.py trong source.zip',
        inherited_fixture_source=ORIGINAL.relative_to(ROOT).as_posix(),
        inherited_fixture_source_sha256=digest(ORIGINAL.read_bytes()), inherited_members=inherited,
        worker_sha256=digest((BUNDLE/'cpu_worker.py').read_bytes()),
        controller_sha256=digest((BUNDLE/'cpu_controller.py').read_bytes()),
        max_cpu_seconds=600, reserved_usd=.15, gpu_requested=False,
        prerequisites_vi='Root thêm allocation CPU0,15USD, kiểm source freeze và ledger trước --run.')
    with (BUNDLE/'source-gate-preparation.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('source_files', 'transforms', 'gate2_build_hashes', 'inherited_members')},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
