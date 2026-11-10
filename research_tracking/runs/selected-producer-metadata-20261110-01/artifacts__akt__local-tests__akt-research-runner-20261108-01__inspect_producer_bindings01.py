"""Đọc cấu trúc JSON thật, chỉ in field names để giữ output gọn."""
from pathlib import Path
import json

root = Path(__file__).resolve().parents[4]
for family, run in (
    ('akt', 'main-a1-expert-engineering10x84-20261110-01'),
    ('sakt', 'sakt-selected-engineering10x84-20261110-03'),
    ('gkt', 'gkt-selected-engineering10x84-20261110-01')):
    directory = root / 'experiments' / family / 'results' / run
    print('\n', family)
    for filename in ('invocation.json', 'COMPLETE.json', 'selection/coverage.json'):
        value = json.loads((directory / filename).read_bytes())
        print(filename, list(value))
        if filename == 'invocation.json':
            identity = value['identity']
            runtime = identity.get('runtime_files') or identity['native_evidence']['runtime']
            print('runtime reference', json.dumps(runtime, sort_keys=True))
            for name in ('spec', 'identity'):
                print(name, list(value[name]))
                for key in ('spec', 'stage', 'native_evidence', 'context'):
                    if isinstance(value[name].get(key), dict):
                        print(name + '.' + key, list(value[name][key]))
        if filename.endswith('coverage.json'):
            print('coverage scalars', {key: item for key, item in value.items()
                if not isinstance(item, (dict, list))})
