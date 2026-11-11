"""Đối chiếu archive checkpoint CUDA bằng metadata và bytes, không import Torch."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(native):
    receipt = json.loads((native / 'receipt.json').read_text())
    assert receipt['status'] == 'CUDA_CHECKPOINT_FRESH_PROCESS_RESTORE_VERIFIED'
    archive = native / 'artifacts.zip'
    assert archive.stat().st_size == receipt['archive_bytes']
    with archive.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == receipt['archive_sha256']
    with zipfile.ZipFile(archive) as saved:
        assert saved.testzip() is None
        inventory = json.loads(saved.read('SHA256.json'))
        assert set(saved.namelist()) == set(inventory) | {'SHA256.json'}
        for name, expected in inventory.items():
            raw = saved.read(name)
            assert len(raw) == expected['bytes'] and sha(raw) == expected['sha256'], name
        base = 't4-checkpoint-recovery-20261110-01/'
        controller = json.loads(saved.read(base + 'result.json'))
        assert controller['status'] == receipt['status']
        assert len(controller['processes']) == 6
        assert len({row['pid'] for row in controller['processes']}) == 6
        results = {}
        checkpoints = []
        physical_steps = physical_targets = 0
        for variant in ('A0', 'A3'):
            for phase in ('continuous', 'interrupted', 'resumed'):
                prefix = base + variant + '/' + phase + '/'
                result = json.loads(saved.read(prefix + 'result.json'))
                assert result['source_unchanged'] is True
                assert result['status'] == ('CHECKPOINT_SAVED_AT_EPOCH1' if phase == 'interrupted' else 'COMPLETE')
                assert result['optimizer_steps'] == (2 if phase == 'interrupted' else 4)
                physical_steps += sum(row['epoch_steps'] for row in result['receipts'])
                physical_targets += sum(row['epoch_targets'] for row in result['receipts'])
                results[(variant, phase)] = result
                if phase != 'continuous':
                    checkpoint = prefix + 'checkpoint/'
                    raw_meta = saved.read(checkpoint + 'metadata.json')
                    metadata = json.loads(raw_meta)
                    raw_complete = saved.read(checkpoint + 'COMPLETE.json')
                    complete = json.loads(raw_complete)
                    state = saved.read(checkpoint + 'state.pt')
                    assert sha(raw_meta) == complete['metadata_sha256']
                    assert sha(state) == complete['checkpoint_sha256'] == metadata['checkpoint_sha256']
                    assert len(state) == metadata['checkpoint_bytes']
                    assert sha(raw_complete) == result['checkpoint']['complete_sha256']
                    assert metadata['restore_scope'] == 'completed_epoch_boundary'
                    checkpoints.append(dict(variant=variant, phase=phase, bytes=len(state)))
            continuous = results[(variant, 'continuous')]
            resumed = results[(variant, 'resumed')]
            for field in ('model_sha256', 'optimizer_sha256', 'rng_hashes', 'participation',
                          'completed_epochs', 'optimized_targets', 'optimizer_steps', 'predictions'):
                assert continuous[field] == resumed[field], (variant, field)
            assert resumed['continuous_resumed_exact'] is True
        assert physical_steps == 16 and physical_targets == 384
        assert len(checkpoints) == 4
    return dict(status='VERIFIED_DOWNLOADED_CUDA_EPOCH_RECOVERY', run_id=native.name,
                physical_steps=physical_steps, physical_targets=physical_targets,
                checkpoints=checkpoints, archive_sha256=receipt['archive_sha256'],
                archive_bytes=receipt['archive_bytes'], processes=6,
                main_training=False, full_lifecycle_recovery=False,
                unexpected_fault_recovery=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('native', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = verify(args.native)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(result))
