"""Đóng nguồn refit mới, tái dùng worker Gate CPU đã nghiệm thu; chưa dispatch."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts/akt')]
from build_colab_bundle import bundle_contents
from knowledge_tracing.akt.authorization import gate2_build_hashes


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    prior = ROOT / 'research_tracking/runs/junyi-confidence-completion-20261114-01/linux03'
    target = HERE / 'linux01'
    target.mkdir(exist_ok=False)
    previous = json.loads((prior / 'source-gate-preparation.json').read_text())
    old_run = 'modal-junyi-a2-a3-final-cpu-20261114-03'
    run = 'modal-junyi-refit-source-cpu-20261114-01'
    for name in ('cpu_controller.py', 'cpu_worker.py'):
        raw = (prior / name).read_bytes().replace(old_run.encode(), run.encode())
        raw = raw.replace(b'junyi-a2-a3-final-source-cpu-20261114-02', b'junyi-refit-source-cpu-20261114-01')
        (target / name).write_bytes(raw)
    members = {}
    with zipfile.ZipFile(ROOT / previous['source']) as old:
        for name, digest in previous['source_files'].items():
            raw = old.read(name)
            assert hashlib.sha256(raw).hexdigest() == digest
            members[name] = raw
    current, _ = bundle_contents()
    for name, raw in current.items():
        # Giữ bản notebook đã sạch dùng tạo corpus lịch sử.
        if not name.endswith('.ipynb') or name not in members:
            members[name] = raw
    pins = {name: hashlib.sha256(raw).hexdigest() for name, raw in members.items()}
    source = ROOT / 'artifacts/akt/modal/junyi-refit-source-20261114-01/source.zip'
    source.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source, 'x', zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
        for name, raw in members.items():
            archive.writestr(name, raw)
        archive.writestr('MANIFEST.json', json.dumps(dict(files=pins), sort_keys=True))
    build_hashes = {name: pins[name] for name in gate2_build_hashes()}
    build = hashlib.sha256(json.dumps(build_hashes, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    preparation = dict(status='SOURCE_GATE_PREPARED_NOT_DISPATCHED', run_id=run,
        source=source.relative_to(ROOT).as_posix(), source_sha256=sha(source), bytes=source.stat().st_size,
        source_files=pins, gate2_build_hashes=build_hashes, source_build_sha256=build,
        worker_sha256=sha(target / 'cpu_worker.py'), controller_sha256=sha(target / 'cpu_controller.py'))
    (target / 'source-gate-preparation.json').write_text(
        json.dumps(preparation, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=preparation['status'], source=preparation['source'], source_sha256=sha(source))))


if __name__ == '__main__':
    main()
