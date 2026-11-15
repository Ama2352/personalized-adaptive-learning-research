"""Index phục hồi chỉ có checkpoint phải mang đúng run manifest khi đóng gói."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('a3_package', ROOT/'research_tracking/runs/junyi-refit-pipeline-20261114-01/package_a3_recovery.py')
PACKAGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGE)


@pytest.fixture
def package_case(tmp_path,monkeypatch):
    root = tmp_path/'p'
    here = root/'bundle'
    here.mkdir(parents=True)
    output = root/'experiments/akt/results/source'
    relative = 'outputs/junyi-a3-refit-20261114-01/checkpoints/epoch-003/'
    folder = output/'files'/relative
    folder.mkdir(parents=True)
    (folder/'state.pt').write_bytes(b'fake checkpoint')
    identity = dict(epochs=9,variant='A3')
    (folder/'metadata.json').write_text(json.dumps(dict(identity=identity)))
    (folder/'COMPLETE.json').write_text('{}')
    files = {relative+name:dict(bytes=(folder/name).stat().st_size,sha256=PACKAGE.sha(folder/name))
             for name in ('state.pt','metadata.json','COMPLETE.json')}
    (output/'remote-inventory.json').write_text(json.dumps(dict(files=files)))
    source = root/'source.zip'
    with zipfile.ZipFile(source,'w') as saved:
        saved.writestr('project/example.py','pass')
    (here/'a3-portable-source01.json').write_text(json.dumps(dict(archive='source.zip',sha256=PACKAGE.sha(source))))
    checked = dict(status='PASS_A3_LOCAL_RECOVERY_CHECKPOINT',source_receipt='experiments/akt/results/source/remote-inventory.json',
        checkpoint=(folder/'state.pt').relative_to(root).as_posix(),
        remote_checkpoint='experiments/akt/results/'+relative.removeprefix('outputs/')+'state.pt',
        checkpoint_sha256=PACKAGE.sha(folder/'state.pt'),complete_epochs=3,partial_epoch=None,partial_optimizer_step=None)
    (here/'a3-checkpoint-verified01.json').write_text(json.dumps(checked))
    manifest = output/'run-manifest.json'
    manifest.write_text(json.dumps(identity))
    monkeypatch.setattr(PACKAGE,'ROOT',root)
    monkeypatch.setattr(PACKAGE,'HERE',here)
    return root,manifest


def test_checkpoint_only_index_requires_original_manifest(package_case,monkeypatch):
    monkeypatch.setattr(sys,'argv',['package','--attempt','1'])
    with pytest.raises(ValueError,match='run manifest'):
        PACKAGE.main()


def test_wrong_manifest_identity_rejected(package_case,monkeypatch):
    root,manifest = package_case
    manifest.write_text('{"epochs":8}')
    monkeypatch.setattr(sys,'argv',['package','--attempt','1','--manifest-source',str(manifest)])
    with pytest.raises(AssertionError):
        PACKAGE.main()


def test_original_manifest_and_full_epoch_position_included(package_case,monkeypatch):
    root,manifest = package_case
    monkeypatch.setattr(sys,'argv',['package','--attempt','1','--manifest-source',str(manifest)])
    PACKAGE.main()
    export = root/'experiments/akt/results/model-export-a3-refit-recovery-20261115-01'
    index = json.loads((export/'RESUME_INDEX.json').read_text())
    member = 'recovery/experiments/akt/results/junyi-a3-refit-20261114-01/run-manifest.json'
    assert member in index['entries']
    with zipfile.ZipFile(export/'COLAB_RESUME.zip') as saved:
        assert saved.read(member) == manifest.read_bytes()
    assert 'epoch 4' in (export/'README.md').read_text(encoding='utf-8')
