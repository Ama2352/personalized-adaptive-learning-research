"""Chỉ đọc JSON checkpoint đã có để đối chiếu producer, không mở state.pt."""
from pathlib import Path
import json

root = Path(__file__).resolve().parents[4]
runs = {'A0': ('akt', 'main-a0-graph29-continuous-engineering10x84-20261110-01', 'checkpoints/epoch-4'),
        'A1_EXPERT': ('akt', 'main-a1-expert-engineering10x84-20261110-01', 'checkpoints/epoch-4'),
        'SAKT': ('sakt', 'sakt-selected-engineering10x84-20261110-03', 'epoch-1'),
        'GKT': ('gkt', 'gkt-selected-engineering10x84-20261110-01', 'epoch-6')}
for candidate, (family, name, checkpoint) in runs.items():
    directory = root / 'experiments' / family / 'results' / name / checkpoint
    print('\nCANDIDATE', candidate)
    complete = json.loads((directory / 'COMPLETE.json').read_bytes())
    metadata = json.loads((directory / 'metadata.json').read_bytes())
    print('COMPLETE', json.dumps(complete, sort_keys=True))
    print('METADATA_FIELDS', {key: list(value) if isinstance(value, dict) else type(value).__name__
                              for key, value in metadata.items()})
    identity = metadata['identity']
    print('IDENTITY_KEYS', list(identity))
    for key in ('neural_binding', 'profile', 'model_spec'):
        if key in identity:
            print(key, json.dumps({name: value for name, value in identity[key].items()
                if name != 'sources_sha256'}, sort_keys=True))
    for key in ('receipt', 'progress', 'checkpoint_bytes'):
        if key in metadata:
            print(key, json.dumps(metadata[key], sort_keys=True))
