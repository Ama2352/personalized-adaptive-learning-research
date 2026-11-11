"""Kiểm cách công bố file trên native filesystem và Volume v2; không train."""
import hashlib
import json
import os
from pathlib import Path

if __name__ == '__main__':
    ROOT = Path(__file__).resolve().parent.parent.parent.parent
    os.environ['MODAL_CONFIG_PATH'] = str(ROOT/'artifacts/akt/private/modal.toml')
    os.environ['MODAL_PROFILE'] = 'kltn'
import modal

app = modal.App('kltn-akt-storage-v2-check')
volume = modal.Volume.from_name('kltn-akt-storage-v2-check-20261112-01', create_if_missing=True, version=2)


def check():
    import runpy
    publish = runpy.run_path('/opt/filesystem.py')['publish_new_file']
    native = Path('/opt/kltn/experiments/akt/results/storage-check')
    native.mkdir(parents=True, exist_ok=False)
    assert native.resolve() == native.absolute()
    assert not any(p.is_symlink() for p in (native, *native.parents))
    result = dict(status='PASS', training=False, gpu=False, volume_version=2, files={})
    for root in (native, Path('/durable')):
        pending, final = root/'state.pending', root/'state.bin'
        pending.write_bytes(b'verified checkpoint storage fixture\n')
        publish(pending, final)
        assert final.read_bytes() == b'verified checkpoint storage fixture\n'
        assert not pending.exists()
        pending.write_bytes(b'new bytes must not overwrite existing state\n')
        try:
            publish(pending, final)
        except FileExistsError:
            pass
        else:
            raise AssertionError('existing file overwritten')
        assert final.read_bytes() == b'verified checkpoint storage fixture\n'
        result['files'][str(final)] = hashlib.sha256(final.read_bytes()).hexdigest()
    volume.commit()
    return result


if __name__ == '__main__':
    image = modal.Image.debian_slim(python_version='3.13').add_local_file(
        ROOT/'src/knowledge_tracing/akt/filesystem.py', '/opt/filesystem.py', copy=True)
    function = app.function(image=image, timeout=30, startup_timeout=60, retries=0,
                            max_containers=1, volumes={'/durable': volume})(check)
    with modal.enable_output(), app.run(environment_name='main'):
        result = function.spawn().get(timeout=180)
        data = b''.join(volume.read_file('state.bin'))
        assert hashlib.sha256(data).hexdigest() == result['files']['/durable/state.bin']
        result['download_verified'] = True
        with (Path(__file__).parent/'storage-probe-result.json').open('x', encoding='utf-8') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
        print(json.dumps(result), flush=True)
