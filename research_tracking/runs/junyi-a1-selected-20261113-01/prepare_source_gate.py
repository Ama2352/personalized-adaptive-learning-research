"""Đóng gói nguồn hiện hành và chuẩn bị CPU Gate A1, không dispatch Modal."""
import ast
import hashlib
import json
from pathlib import Path
import runpy
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
BASE = ROOT / 'research_tracking/runs/junyi-a0-h100-batch128-20261112-01'
RUN = 'modal-junyi-a1-selected-cpu-20261113-01'
SOURCE = ROOT / 'artifacts/akt/modal/junyi-a1-selected-20261113-01/source.zip'
EXTRA = (
    'research_tracking/runs/cpu-junyi-graph-reconstruction-20261107-01/graph.json',
    'research_tracking/runs/junyi-comparison-preflight-20261113-01/data-audit.json',
)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    SOURCE.parent.mkdir(parents=True, exist_ok=True)
    contents, transforms = runpy.run_path(str(ROOT / 'scripts/akt/build_colab_bundle.py'))['bundle_contents']()
    for relative in EXTRA:
        contents[relative] = (ROOT / relative).read_bytes()
    # Giữ toàn bộ dependency đã có ở source A0, cập nhật source/test hiện hành.
    original = ROOT / 'artifacts/akt/modal/junyi-a0-h100-batch128-20261112-01/source.zip'
    with zipfile.ZipFile(original) as saved:
        old_pins = json.loads(saved.read('MANIFEST.json'))['files']
        for relative, expected in old_pins.items():
            raw = saved.read(relative)
            assert digest(raw) == expected
            contents.setdefault(relative, raw)
    # Gate kiểm mọi notebook Paper1 và CSV simulator, gồm cả input phụ.
    paper2 = ROOT / 'paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20'
    for path in [*sorted((ROOT / 'paper1').glob('*.ipynb')),
                 *sorted((paper2 / 'data/simulator_inputs').glob('*.csv'))]:
        relative = path.relative_to(ROOT).as_posix()
        contents.setdefault(relative, path.read_bytes())
    pins = {name: digest(raw) for name, raw in sorted(contents.items())}
    with zipfile.ZipFile(SOURCE, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as saved:
        for name, raw in sorted(contents.items()):
            saved.writestr(name, raw)
        saved.writestr('MANIFEST.json', json.dumps(dict(files=pins), sort_keys=True))
    with zipfile.ZipFile(SOURCE) as saved:
        assert saved.testzip() is None
        assert set(saved.namelist()) == set(pins) | {'MANIFEST.json'}
        assert all(digest(saved.read(name)) == expected for name, expected in pins.items())
    worker = (BASE / 'cpu_worker.py').read_text(encoding='utf-8')
    worker = worker.replace('modal-junyi-a0-batch128-cpu-20261112-01', RUN)
    worker = worker.replace('junyi-source06.zip', 'junyi-a1-source.zip')
    worker = worker.replace('Full Gate CPU source06', 'CPU Gate nguồn A1 hiện hành')
    controller = (BASE / 'cpu_controller.py').read_text(encoding='utf-8')
    controller = controller.replace('modal-junyi-a0-batch128-cpu-20261112-01', RUN)
    controller = controller.replace('junyi-a0-batch128-cpu-20261112-01', 'junyi-a1-selected-cpu-20261113-01')
    controller = controller.replace('junyi-source06.zip', 'junyi-a1-source.zip')
    controller = controller.replace('CPU04 full Gate source06', 'CPU Gate nguồn A1 hiện hành')
    for name, text in (('cpu_worker.py', worker), ('cpu_controller.py', controller)):
        ast.parse(text)
        destination = BUNDLE / name
        if destination.exists():
            raise FileExistsError(destination)
        destination.write_text(text, encoding='utf-8')
    result = dict(status='SOURCE_GATE_PREPARED_NOT_DISPATCHED', run_id=RUN,
        source=SOURCE.relative_to(ROOT).as_posix(), source_sha256=digest(SOURCE.read_bytes()),
        bytes=SOURCE.stat().st_size, files=len(pins), transforms=transforms,
        source_files=pins, upstream='Có sẵn trong image im-ldjZsYO21pzaupmQXGLhnS, refresh_gate2 xác minh commit và tree.',
        max_cpu_seconds=600, reserved_usd=0.15, gpu_requested=False,
        prerequisites_vi='Root cần thêm allocation CPU 0,15 USD vào ledger trước --run. Không sửa policy hoặc phát hành Gate giả.')
    (BUNDLE / 'source-gate-preparation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in result.items() if key not in ('source_files', 'transforms')}, ensure_ascii=False))

if __name__ == '__main__':
    main()
