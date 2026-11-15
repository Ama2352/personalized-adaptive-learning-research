"""Sao lưu checkpoint Colab theo SHA, xuất manifest trước khi cập nhật LATEST."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import uuid


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def position(folder):
    full = re.fullmatch(r'epoch-(\d{3})', folder.name)
    if full:
        return int(full[1]), 2040, 1
    partial = re.fullmatch(r'refit-batch-epoch-(\d+)-step-(\d+)-[a-f0-9]+', folder.name)
    if partial:
        return int(partial[1]), int(partial[2]), 0
    raise ValueError('Tên checkpoint không hợp lệ')


def restore(root, backup_root):
    root, backup_root = Path(root), Path(backup_root)
    pointer = json.loads((backup_root/'LATEST.json').read_text())
    manifest = (backup_root/pointer['manifest']).resolve()
    assert manifest.is_relative_to(backup_root.resolve())
    assert sha(manifest) == pointer['sha256']
    receipt = json.loads(manifest.read_text())
    assert receipt['status'] == 'PASS_DRIVE_CHECKPOINT_BACKUP'
    root.mkdir(parents=True,exist_ok=True)
    for relative,pin in receipt['files'].items():
        source = (backup_root/pin['drive_relative']).resolve()
        destination = (root/relative).resolve()
        assert source.is_relative_to(backup_root.resolve()) and destination.is_relative_to(root.resolve())
        assert source.stat().st_size == pin['bytes'] and sha(source) == pin['sha256']
        destination.parent.mkdir(parents=True,exist_ok=True)
        if destination.exists():
            assert destination.stat().st_size == pin['bytes'] and sha(destination) == pin['sha256']
            continue
        temporary = root/('.restoring-'+uuid.uuid4().hex)
        with source.open('rb') as origin, temporary.open('xb') as target:
            shutil.copyfileobj(origin,target)
        assert temporary.stat().st_size == pin['bytes'] and sha(temporary) == pin['sha256']
        temporary.replace(destination)
    assert sha(root/receipt['checkpoint']) == receipt['checkpoint_sha256']
    return receipt


def backup(root, operation, backup_root):
    root, operation, backup_root = map(Path, (root, operation, backup_root))
    execution = json.loads((operation/'execution.json').read_text())
    worker = json.loads((root/'gpu-stage-request.json').read_text())
    logical = root/'experiments/akt/results'/worker['logical_run_id']
    folders = [marker.parent for marker in (logical/'checkpoints').glob('*/COMPLETE.json')]
    latest = max(folders, key=position)
    selected = [latest, *(folder for folder in folders if folder.name.startswith('epoch-') and folder != latest)]
    files = []
    for folder in selected:
        marker = json.loads((folder/'COMPLETE.json').read_text())
        metadata = json.loads((folder/'metadata.json').read_text())
        assert sha(folder/'metadata.json') == marker['metadata_sha256']
        assert metadata['checkpoint_sha256'] == marker['checkpoint_sha256']
        assert (folder/'state.pt').stat().st_size == metadata['checkpoint_bytes']
        assert sha(folder/'state.pt') == marker['checkpoint_sha256']
        files.extend(folder/name for name in ('state.pt','metadata.json','COMPLETE.json'))
    files.extend(path for path in logical.iterdir() if path.is_file() and path.suffix in ('.json','.jsonl'))
    files.extend(path for path in operation.iterdir() if path.is_file()
                 and path.suffix in ('.json','.log') and path.name != 'controller-result.json')
    entries = {}
    for source in files:
        relative = source.relative_to(root).as_posix()
        if '/checkpoints/epoch-' in relative:
            drive_relative = 'completed/'+relative
        else:
            drive_relative = 'tranches/'+execution['execution_id']+'/files/'+relative
        destination = backup_root/drive_relative
        pin = dict(bytes=source.stat().st_size, sha256=sha(source), drive_relative=drive_relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            temporary = backup_root/('.uploading-'+uuid.uuid4().hex)
            with source.open('rb') as origin, temporary.open('xb') as target:
                shutil.copyfileobj(origin,target)
            assert temporary.stat().st_size == pin['bytes'] and sha(temporary) == pin['sha256']
            temporary.replace(destination)
        assert destination.stat().st_size == pin['bytes'] and sha(destination) == pin['sha256']
        entries[relative] = pin
    epoch, step, full = position(latest)
    state = latest/'state.pt'
    assert sha(state) == json.loads((latest/'COMPLETE.json').read_text())['checkpoint_sha256']
    receipt = dict(status='PASS_DRIVE_CHECKPOINT_BACKUP', execution_id=execution['execution_id'],
        checkpoint=state.relative_to(root).as_posix(), checkpoint_sha256=sha(state),
        complete_epochs=epoch if full else epoch-1, partial_epoch=None if full else epoch,
        partial_optimizer_step=None if full else step, frozen_epochs=worker['frozen_epochs'],
        refit_complete=(logical/'COMPLETE.json').exists(), files=entries)
    manifest = backup_root/'tranches'/execution['execution_id']/'BACKUP_COMPLETE.json'
    manifest.parent.mkdir(parents=True, exist_ok=True)
    if manifest.exists():
        assert json.loads(manifest.read_text()) == receipt
    else:
        with manifest.open('x') as stream:
            json.dump(receipt,stream,indent=2)
    assert json.loads(manifest.read_text()) == receipt
    pointer = backup_root/'LATEST.json'
    if pointer.exists():
        previous = json.loads(pointer.read_text())
        previous_manifest = (backup_root/previous['manifest']).resolve()
        assert previous_manifest.is_relative_to(backup_root.resolve())
        assert sha(previous_manifest) == previous['sha256']
        previous_receipt = json.loads(previous_manifest.read_text())
        previous_folder = Path(previous_receipt['checkpoint']).parent
        if position(previous_folder) > position(latest):
            return manifest
    temporary = backup_root/('LATEST.uploading-'+uuid.uuid4().hex+'.json')
    temporary.write_text(json.dumps(dict(manifest=manifest.relative_to(backup_root).as_posix(),
                                         sha256=sha(manifest)),indent=2))
    temporary.replace(pointer)
    return manifest
