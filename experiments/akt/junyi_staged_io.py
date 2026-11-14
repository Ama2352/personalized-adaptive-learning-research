"""Chuẩn bị và thu artifact bằng CPU local cho function GPU Junyi."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import uuid
import zipfile


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_relative(name):
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or '..' in path.parts or ':' in name or '\\' in name
            or path.as_posix() != name):
        raise ValueError('Đường dẫn artifact phải tương đối và chuẩn hóa')
    return path


def owned_input(root, name):
    path = root / Path(*safe_relative(name).parts)
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Input ra ngoài repository')
    if 'private' in path.resolve().parts or path.name in ('.env', 'modal.toml', 'credentials'):
        raise ValueError('Input chứa vùng thông tin đăng nhập')
    return path


def allowed_snapshot_member(name):
    path=safe_relative(name)
    if (path.parts[0] in ('dataset','venv','.venv','.wsl','.git')
            or path.parts[:2]==('artifacts','bkt_baseline')
            or 'private' in path.parts or path.name in ('.env','modal.toml','credentials')):
        raise ValueError('Snapshot chứa vùng được bảo vệ hoặc thông tin private')
    return path


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def _copy_verified(source, destination, pin):
    if source.stat().st_size != pin['bytes'] or sha(source) != pin['sha256']:
        raise ValueError('Input thay đổi trước sao chép')
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.stat().st_size != pin['bytes'] or sha(destination) != pin['sha256']:
            raise ValueError('Hai input có cùng đường dẫn nhưng khác byte')
        return
    with source.open('rb') as original, destination.open('xb') as target:
        shutil.copyfileobj(original, target, 1024 * 1024)
    if sha(destination) != pin['sha256']:
        raise ValueError('Sai SHA sau sao chép')


def prepare_project(root, request, destination):
    """Giải nén và kiểm input hoàn toàn trên local, trước upload/cấp GPU.

    Archives dùng MANIFEST.json của pipeline hiện có. Gate ZIP dùng SHA256.json.
    Hàm không import Modal, không tạo container hoặc cài dependency.
    """
    root, destination = Path(root).resolve(), Path(destination).resolve()
    if not destination.is_relative_to(root / 'artifacts/akt') or destination.exists():
        raise ValueError('Snapshot mới phải nằm trong artifacts/akt')
    inventory = {}
    archives = []
    # Kiểm mọi archive trước khi tạo snapshot, giữ nguồn trước chuyển artifact.
    for kind in ('source', 'data', 'cpu_gate'):
        pin = request['archives'][kind]
        archive = owned_input(root, pin['path'])
        if sha(archive) != pin['sha256']:
            raise ValueError('Archive SHA không khớp')
        archives.append((kind, archive))
    extras = request['local_files']
    for name, pin in extras.items():
        allowed_snapshot_member(name)
        source = owned_input(root, pin['path'])
        if sha(source) != pin['sha256'] or source.stat().st_size != pin['bytes']:
            raise ValueError('File chuẩn bị local không khớp pin')
    destination.mkdir(parents=True)
    project = destination / 'project'
    expanded = 0
    for kind, archive in archives:
        with zipfile.ZipFile(archive) as saved:
            marker = 'SHA256.json' if kind == 'cpu_gate' else 'MANIFEST.json'
            manifest = json.loads(saved.read(marker))
            entries = manifest if kind == 'cpu_gate' else manifest['files']
            if set(saved.namelist()) != set(entries) | {marker}:
                raise ValueError('Inventory ZIP không đầy đủ hoặc trùng tên')
            if len(saved.namelist()) != len(set(saved.namelist())):
                raise ValueError('ZIP có member trùng tên')
            for name, raw_pin in entries.items():
                safe_relative(name)
                pin = {'sha256': raw_pin} if type(raw_pin) is str else raw_pin
                info = saved.getinfo(name)
                expanded += info.file_size
                if info.file_size > 2 * 1024**3 or expanded > 12 * 1024**3:
                    raise ValueError('Archive vượt giới hạn byte giải nén')
                if kind == 'cpu_gate':
                    if not name.startswith('gate2-') or Path(name).name != name:
                        continue
                    target_name = 'artifacts/akt/preflight/' + name
                else:
                    target_name = name
                allowed_snapshot_member(target_name)
                target = project / Path(*PurePosixPath(target_name).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    if sha(target) != pin['sha256']:
                        raise ValueError('Archive chồng input có nội dung khác nhau')
                    continue
                with saved.open(name) as source, target.open('xb') as output:
                    shutil.copyfileobj(source, output, 1024 * 1024)
                if target.stat().st_size != info.file_size or sha(target) != pin['sha256']:
                    raise ValueError('Member ZIP sai SHA/bytes')
                inventory[target_name] = dict(bytes=target.stat().st_size, sha256=pin['sha256'])
    for name, pin in extras.items():
        source = owned_input(root, pin['path'])
        target = project / Path(*PurePosixPath(name).parts)
        _copy_verified(source, target, pin)
        inventory[name] = dict(bytes=pin['bytes'], sha256=pin['sha256'])
    # Worker request đã được CPU xác minh, không mang đường dẫn file private.
    write_new(project / 'gpu-stage-request.json', request['worker'])
    inventory['gpu-stage-request.json'] = dict(bytes=(project / 'gpu-stage-request.json').stat().st_size,
                                              sha256=sha(project / 'gpu-stage-request.json'))
    receipt = dict(status='LOCAL_INPUT_SNAPSHOT_COMPLETE', files=inventory,
                   archives=request['archives'], project='project')
    write_new(destination / 'INPUTS.json', receipt)
    return receipt


def verify_project(destination):
    destination = Path(destination)
    receipt = json.loads((destination / 'INPUTS.json').read_text(encoding='utf-8'))
    if receipt['status'] != 'LOCAL_INPUT_SNAPSHOT_COMPLETE':
        raise ValueError('Snapshot local chưa hoàn tất')
    for name, pin in receipt['files'].items():
        path = destination / 'project' / Path(*allowed_snapshot_member(name).parts)
        if not path.is_file() or path.stat().st_size != pin['bytes'] or sha(path) != pin['sha256']:
            raise ValueError('Snapshot local thay đổi')
    return receipt


def upload_snapshot(volume,destination,receipt):
    """Upload trước GPU; retry chỉ bổ sung file thiếu, giữ byte cũ bất biến."""
    destination=Path(destination)
    marker='project/INPUTS.json'
    raw=(destination/'INPUTS.json').read_bytes()
    try:
        previous=b''.join(volume.read_file(marker))
    except FileNotFoundError:
        previous=None
    if previous is not None:
        if previous!=raw:
            raise ValueError('Input Volume cũ có manifest khác')
        return
    existing={}
    for entry in volume.iterdir('/',recursive=True):
        name=entry.path.lstrip('/')
        if name.startswith('project/') and entry.type.name!='DIRECTORY':
            if entry.type.name!='FILE':
                raise ValueError('Input Volume có alias hoặc file đặc biệt')
            existing[name]=entry
    expected={'project/'+name for name in receipt['files']}
    if set(existing)-expected:
        raise ValueError('Upload dở có file ngoài snapshot; giữ lại để điều tra')
    for name,pin in receipt['files'].items():
        remote='project/'+name
        if remote in existing:
            digest=hashlib.sha256()
            size=0
            for block in volume.read_file(remote):
                digest.update(block)
                size+=len(block)
            if size!=pin['bytes'] or digest.hexdigest()!=pin['sha256']:
                raise ValueError('Upload dở có byte khác, không ghi đè')
    with volume.batch_upload(force=False) as batch:
        for name in receipt['files']:
            if 'project/'+name not in existing:
                batch.put_file(destination/'project'/name,'/project/'+name)
    verify_project(destination)
    with volume.batch_upload(force=False) as batch:
        batch.put_file(destination/'INPUTS.json','/'+marker)


def collect_outputs(receipt, destination, read_file, *, stop_acknowledged, reuse_from=None):
    """Tải/đối chiếu và nén bằng CPU sau xác nhận dừng GPU.

    read_file là Volume.read_file hoặc reader local trong tests.
    Ghi COMPLETE cuối cùng, giữ file partial khi lỗi để điều tra.
    """
    if stop_acknowledged is not True:
        raise PermissionError('Phải xác nhận GPU đã dừng trước CPU postprocess')
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    cached = None if reuse_from is None else Path(reuse_from)
    cached_files = {}
    if cached is not None:
        complete = json.loads((cached/'COMPLETE.json').read_text(encoding='utf-8'))
        if complete['status']!='LOCAL_ARTIFACTS_VERIFIED_GPU_STOPPED':
            raise ValueError('Chỉ tái dùng artifact local đã nghiệm thu')
        cached_files=json.loads((cached/'remote-inventory.json').read_text(encoding='utf-8'))['files']
    inventory_path=destination / 'remote-inventory.json'
    if inventory_path.exists():
        if json.loads(inventory_path.read_text(encoding='utf-8'))!=receipt:
            raise ValueError('Inventory thay đổi khi retry tải artifact')
    else:
        write_new(inventory_path, receipt)
    verified_local = {}
    for name, pin in receipt['files'].items():
        safe_relative(name)
        target = destination / 'files' / Path(*PurePosixPath(name).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        blob = (pin['sha256'], pin['bytes'])
        if target.exists():
            if target.stat().st_size != pin['bytes'] or sha(target) != pin['sha256']:
                raise ValueError('File local cũ khác artifact remote')
            verified_local[blob] = target
            continue
        # File tạm ở root đợt tải để recovery trên Windows không vượt MAX_PATH.
        partial = destination / (target.name + '.download.' + uuid.uuid4().hex)
        reusable = verified_local.get(blob)
        if reusable is None and cached_files.get(name)==pin:
            reusable = cached/'files'/Path(*safe_relative(name).parts)
        if reusable is not None:
            if reusable.stat().st_size != pin['bytes'] or sha(reusable) != pin['sha256']:
                raise ValueError('Output đã nghiệm thu thay đổi trước tái dùng')
            # Output đã niêm phong giữ chỉ đọc. Hardlink giữ mọi đường dẫn/bằng chứng trên D.
            try:
                os.link(reusable, partial)
            except OSError:
                _copy_verified(reusable,partial,pin)
            if sha(partial) != pin['sha256']:
                raise ValueError('Tái dùng output sai SHA')
            partial.rename(target)
            verified_local[blob] = target
            continue
        with partial.open('xb') as stream:
            for block in read_file(name):
                stream.write(block)
            stream.flush()
            os.fsync(stream.fileno())
        if partial.stat().st_size != pin['bytes'] or sha(partial) != pin['sha256']:
            raise ValueError('Artifact tải về sai bytes/SHA')
        partial.rename(target)
        verified_local[blob] = target
    archive = destination / 'artifacts.zip'
    packed=destination/('artifacts.packing.'+uuid.uuid4().hex+'.zip')
    if not archive.exists():
        with zipfile.ZipFile(packed, 'x', zipfile.ZIP_DEFLATED, compresslevel=1) as saved:
            for name in receipt['files']:
                saved.write(destination / 'files' / Path(*PurePosixPath(name).parts), name)
            saved.writestr('SHA256.json', json.dumps(receipt['files'], sort_keys=True))
        with zipfile.ZipFile(packed) as saved:
            for name,pin in receipt['files'].items():
                with saved.open(name) as stream:
                    if hashlib.file_digest(stream,'sha256').hexdigest()!=pin['sha256']:
                        raise ValueError('Artifact thay đổi trong lúc nén local')
        packed.rename(archive)
    with zipfile.ZipFile(archive) as saved:
        if (set(saved.namelist())!=set(receipt['files'])|{'SHA256.json'}
                or json.loads(saved.read('SHA256.json'))!=receipt['files']):
            raise ValueError('Archive local sai inventory')
        for name,pin in receipt['files'].items():
            with saved.open(name) as stream:
                if hashlib.file_digest(stream,'sha256').hexdigest()!=pin['sha256']:
                    raise ValueError('Archive local sai SHA member')
    result = dict(status='LOCAL_ARTIFACTS_VERIFIED_GPU_STOPPED', files=len(receipt['files']),
                  archive_sha256=sha(archive), archive_bytes=archive.stat().st_size)
    complete=destination / 'COMPLETE.json'
    if complete.exists():
        if json.loads(complete.read_text(encoding='utf-8'))!=result:
            raise ValueError('Archive local thay đổi sau COMPLETE')
    else:
        write_new(complete, result)
    return result
