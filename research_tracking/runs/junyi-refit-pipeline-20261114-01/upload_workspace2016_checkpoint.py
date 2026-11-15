"""Upload tối thiểu bốn file resume, trước GPU, giữ allocation đã cấp."""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def main():
    assert os.environ['MODAL_PROFILE'] == 'kltn2016'
    import modal
    proof = json.loads((HERE / 'a3-drive023-import-proof.json').read_text())
    request = json.loads((HERE / 'a3-refit-workspace2016-execution01.json').read_text())
    local = ROOT / proof['output']
    inventory = json.loads((local / 'remote-inventory.json').read_text())['files']
    checkpoint = 'outputs/' + proof['checkpoint'].removeprefix('experiments/akt/results/')
    names = [checkpoint.rsplit('/', 1)[0] + '/' + name for name in ('metadata.json', 'COMPLETE.json')]
    names.extend(['outputs/junyi-a3-refit-20261114-01/run-manifest.json', checkpoint])
    volume = modal.Volume.from_name('kltn-staged-junyi-a3-refit-20261114-01-outputs', version=2)
    with modal.enable_output():
        for name in names:
            path = local / 'files' / name
            with path.open('rb') as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == inventory[name]['sha256']
            try:
                raw = b''.join(volume.read_file(name))
            except FileNotFoundError:
                print(json.dumps(dict(uploading=path.name, bytes=path.stat().st_size)), flush=True)
                with volume.batch_upload(force=False) as batch:
                    batch.put_file(path, '/' + name)
                raw = b''.join(volume.read_file(name))
            assert len(raw) == inventory[name]['bytes']
            assert hashlib.sha256(raw).hexdigest() == inventory[name]['sha256']
            print(json.dumps(dict(verified=path.name, bytes=len(raw))), flush=True)
    result = dict(status='PASS_CHECKPOINT_UPLOADED_BEFORE_GPU', workspace=request['workspace_name'],
                  files=4, checkpoint=checkpoint, checkpoint_sha256=proof['checkpoint_sha256'],
                  checkpoint_bytes=inventory[checkpoint]['bytes'], gpu_started=False,
                  volume='kltn-staged-junyi-a3-refit-20261114-01-outputs')
    with (HERE / 'workspace2016-checkpoint-volume01.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
