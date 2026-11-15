"""Kiểm và giải gói A3 trên Colab, giữ nguyên snapshot số học đã đóng."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def checked_destination(root, name):
    destination = (root / name).resolve()
    if not destination.is_relative_to(root.resolve()):
        raise ValueError('Member vượt thư mục đích')
    return destination


def copy_member(saved, member, destination, pin=None):
    if destination.exists():
        if pin and destination.stat().st_size == pin['bytes'] and digest(destination) == pin['sha256']:
            return
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with saved.open(member) as source, destination.open('xb') as target:
        shutil.copyfileobj(source, target)
    if pin and (destination.stat().st_size != pin['bytes'] or digest(destination) != pin['sha256']):
        raise ValueError('Member không khớp inventory ' + member)


def bootstrap(index, archive_path=None):
    transfer = Path('/content/kltn-a3-transfer')
    archive = Path(archive_path) if archive_path is not None else transfer / index['archive']
    assert archive.stat().st_size == index['archive_bytes']
    assert digest(archive) == index['archive_sha256']
    root = Path(index['project_root'])
    source_zip = transfer / 'SOURCE.zip'
    with zipfile.ZipFile(archive) as saved:
        expected = {'SOURCE.zip', *index['entries']}
        assert set(saved.namelist()) == expected
        assert len(saved.namelist()) == len(expected)
        copy_member(saved, 'SOURCE.zip', source_zip,
                    dict(bytes=saved.getinfo('SOURCE.zip').file_size, sha256=index['source_zip_sha256']))
        with zipfile.ZipFile(source_zip) as source:
            inventory = json.loads(source.read('INPUTS.json'))
            assert set(source.namelist()) == {'INPUTS.json', 'CPU_CHECK.json',
                                             *('project/' + name for name in inventory['files'])}
            assert json.loads(source.read('CPU_CHECK.json'))['status'] == 'PASS_LOCAL_STAGE_INPUTS'
            for name, pin in inventory['files'].items():
                copy_member(source, 'project/' + name, checked_destination(root, name), pin)
        for name, pin in index['entries'].items():
            assert name.startswith('recovery/')
            copy_member(saved, name, checked_destination(root, name.removeprefix('recovery/')), pin)
    assert digest(root / index['resume_checkpoint']) == index['resume_sha256']
    (transfer / 'resume-index.json').write_text(json.dumps(index,indent=2))
    proof = dict(status='PASS_COLAB_A3_INPUT_SHA256', project_root=str(root),
                 source_files=len(inventory['files']), recovery_files=len(index['entries']),
                 checkpoint_sha256=index['resume_sha256'], complete_epochs=index['complete_epochs'],
                 partial_epoch=index['partial_epoch'], partial_optimizer_step=index['partial_optimizer_step'],
                 training_started=False)
    (transfer / 'bootstrap-verified.json').write_text(json.dumps(proof, indent=2))
    print(json.dumps(proof))
