"""Chỉ in schema/scalars của các receipt đã đóng, không khởi chạy job."""
from pathlib import Path
import json

root = Path(__file__).resolve().parents[4]
paths = {
    'A0': 'research_tracking/runs/akt-public-selected-resume-20261110-01/execution/graph29-a0-continuous01/outer-final.json',
    'A1_EXPERT': 'research_tracking/runs/a1-expert-selected-engineering-20261110-01/accepted__outer-final.json',
    'SAKT': 'research_tracking/runs/sakt-selected-engineering-20261110-01/fit05__outer-final.json',
    'GKT': 'research_tracking/runs/gkt-selected-engineering-20261110-01/gkt-selected-fit03__outer-final.json'}
for candidate, name in paths.items():
    path = root / name
    print(candidate, 'exists', path.is_file())
    if not path.is_file():
        continue
    value = json.loads(path.read_bytes())
    print('outer status', value['status'])
    for field in ('owned_receipt', 'worker_result'):
        child = value.get(field)
        if isinstance(child, dict):
            if field == 'worker_result':
                print('resources', child['resources'])
