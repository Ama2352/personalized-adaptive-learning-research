"""Ghim snapshot refit sau Gate Linux, dùng chung các cache có sẵn trên D."""
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'experiments/akt'))
from junyi_staged_io import sha, write_new


def main():
    result = ROOT / 'experiments/akt/results/modal-junyi-refit-source-cpu-20261114-02'
    receipt = json.loads((result / 'receipt.json').read_text())
    guard = json.loads((result / 'app-budget-guard.json').read_text())
    preparation = json.loads((HERE / 'linux02/source-gate-preparation.json').read_text())
    assert receipt['status'] == 'MODAL_CPU_GATE_VERIFIED' and receipt['download_inventory_verified']
    assert guard['stop_acknowledged'] and receipt['source_build_sha256'] == preparation['source_build_sha256']
    gate_zip = result / 'artifacts.zip'
    assert sha(gate_zip) == receipt['archive_sha256']
    with zipfile.ZipFile(gate_zip) as archive:
        gate = archive.read('gate2-current.json')
        (HERE / 'linux02/gate2-current.json').write_bytes(gate)
    empty = ROOT / 'artifacts/akt/modal/junyi-refit-source-20261114-02/empty-data.zip'
    with zipfile.ZipFile(empty, 'x') as archive:
        archive.writestr('MANIFEST.json', json.dumps(dict(files={})))
    old = json.loads((ROOT / 'research_tracking/runs/junyi-confidence-completion-20261114-01/a2-stage-inputs03.json').read_text())
    upstream = {name: pin for name, pin in old['local_files'].items()
                if name.startswith('artifacts/akt/dependencies/upstream/')}
    assert upstream
    for variant in ('a0', 'a1', 'a2', 'a3'):
        worker = json.loads((HERE / ('worker-' + variant + '.json')).read_text())
        refit = json.loads((HERE / ('refit-request-' + variant + '.json')).read_text())
        files = dict(upstream)
        def add(path):
            path = path.resolve()
            name = path.relative_to(ROOT).as_posix()
            assert path.is_file() and 'private' not in path.parts
            files[name] = dict(path=name, sha256=sha(path), bytes=path.stat().st_size)
        add(HERE / ('refit-request-' + variant + '.json'))
        for key in ('config', 'cuda_profile', 'epoch_plan', 'selected_index', 'lock_file', 'graph', 'confidence'):
            if refit.get(key) is not None:
                add(ROOT / refit[key]['path'])
        for value in refit['inputs'].values():
            if isinstance(value, dict) and 'path' in value:
                add(ROOT / value['path'])
        for key in ('selected_cache_root', 'window_cache90'):
            folder = ROOT / refit['inputs'][key]
            for path in sorted(folder.rglob('*')):
                if path.is_file():
                    add(path)
        if variant != 'a0':
            add(ROOT / refit['graph_context_cache90']['path'])
        request = dict(worker=worker, local_files=files, archives=dict(
            source=dict(path=preparation['source'], sha256=preparation['source_sha256']),
            data=dict(path=empty.relative_to(ROOT).as_posix(), sha256=sha(empty)),
            cpu_gate=dict(path=gate_zip.relative_to(ROOT).as_posix(), sha256=sha(gate_zip))))
        write_new(HERE / ('stage-inputs-' + variant + '.json'), request)
        print(json.dumps(dict(variant=variant.upper(), files=len(files), bytes=sum(p['bytes'] for p in files.values()))), flush=True)


if __name__ == '__main__':
    main()
