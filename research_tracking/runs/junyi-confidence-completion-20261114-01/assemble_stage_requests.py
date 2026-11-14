"""Ghim toàn bộ đầu vào CPU vào request staged; chưa upload hoặc cấp GPU."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CACHES = ROOT/'artifacts/akt/graph-context-cache/full-train80-staged-20261114-01'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    source = json.loads((HERE/'linux02/source-gate-preparation.json').read_text())
    legacy = json.loads((ROOT/'research_tracking/runs/junyi-a1-selection-cache-20261113-01/h100-request09.json').read_text())
    gate_root = ROOT/'experiments/akt/results/modal-junyi-a2-a3-final-cpu-20261114-02'
    gate = json.loads((gate_root/'receipt.json').read_text())
    if gate['status'] != 'MODAL_CPU_GATE_VERIFIED' or not gate['download_inventory_verified']:
        raise ValueError('Cần Gate Linux đã đạt và artifact đã kiểm')
    archives = dict(source=dict(path=source['source'], sha256=source['source_sha256']),
        data=legacy['archives']['data'],
        cpu_gate=dict(path=(gate_root/'artifacts.zip').relative_to(ROOT).as_posix(),
                      sha256=gate['archive_sha256']))
    for pin in archives.values():
        if sha(ROOT/pin['path']) != pin['sha256']:
            raise ValueError('Archive đầu vào đã đổi byte')
    upstream = json.loads((HERE/'upstream-portable-inventory.json').read_text())
    common = {}

    def add(path, alias=None):
        path = Path(path)
        if not path.resolve().is_relative_to(ROOT):
            raise ValueError('Đầu vào ra ngoài repository')
        name = alias or path.relative_to(ROOT).as_posix()
        common[name] = dict(path=path.relative_to(ROOT).as_posix(),
                            bytes=path.stat().st_size, sha256=sha(path))

    for relative, pin in upstream['files'].items():
        # Reflog chứa danh tính local; hooks mẫu không cần cho kiểm checkout.
        if relative.startswith(('.git/logs/', '.git/hooks/')):
            continue
        path = ROOT/upstream['local_path']/relative
        if sha(path) != pin['sha256']:
            raise ValueError('Portable upstream đổi byte')
        add(path, upstream['snapshot_path']+'/'+relative)
    # Inventory chỉ chứa file nên thư mục refs rỗng không đi theo snapshot.
    # Một ref public giữ cấu trúc Git hợp lệ sau copy/upload, không đổi HEAD.
    head = ROOT/upstream['local_path']/'.git/HEAD'
    if head.read_text().strip() != upstream['identity']['commit']:
        raise ValueError('Portable upstream cần HEAD detached đúng commit')
    add(head, upstream['snapshot_path']+'/.git/refs/heads/kltn-pinned')
    outputs = []
    for variant in ('A2', 'A3'):
        worker = json.loads((HERE/(variant.lower()+'-worker-base.json')).read_text())
        worker['cpu_prepared'] = json.loads((CACHES/(variant.lower()+'-cpu-prepared.json')).read_text())
        # Hai variant chia sẻ đúng confidence và encoding; graph cache có binding riêng.
        names = [worker[key] for key in ('confidence_file', 'confidence_fit_artifact',
                                         'graph_file', 'comparison_reference_file',
                                         'train_admission_file', 'runtime_lock_file')]
        data = worker['inputs']
        names += [data[key] for key in ('encoding_file', 'encoding_receipt', 'roles_path')]
        names.append(data['train_window_cache'])
        names += [entry['path'] for entry in worker['cpu_prepared'].values()]
        extras = dict(common)
        for name in names:
            path = ROOT/name
            paths = sorted(item for item in path.rglob('*') if item.is_file()) if path.is_dir() else [path]
            for item in paths:
                relative = item.relative_to(ROOT).as_posix()
                extras[relative] = dict(path=relative, bytes=item.stat().st_size, sha256=sha(item))
        request = dict(worker=worker, archives=archives, local_files=extras)
        path = HERE/(variant.lower()+'-stage-inputs02.json')
        raw = (json.dumps(request, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
        if path.exists():
            if path.read_bytes() != raw:
                raise ValueError('Request cũ khác byte, dùng version mới')
        else:
            path.write_bytes(raw)
        outputs.append(dict(variant=variant, path=path.relative_to(ROOT).as_posix(),
                            sha256=sha(path), extra_files=len(extras)))
    (HERE/'stage-inputs-assembly02.json').write_text(json.dumps(dict(status='REAL_STAGE_INPUTS_ASSEMBLED',
        outputs=outputs, source_build_sha256=gate['source_build_sha256'], gpu_started=False), indent=2)+'\n')
    print(json.dumps(dict(status='REAL_STAGE_INPUTS_ASSEMBLED', outputs=outputs)))


if __name__ == '__main__':
    main()
