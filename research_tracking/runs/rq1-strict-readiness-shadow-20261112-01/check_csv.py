"""Đối chiếu số đếm từ CSV, không import analyzer hoặc đọc lại trace."""

from collections import Counter
import csv
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
with (HERE / 'events.csv').open(encoding='utf-8', newline='') as stream:
    rows = list(csv.DictReader(stream))
with (ROOT / 'research_tracking/runs/rq1-ready-set-exposure-20261108-01/event_membership_flags.csv').open(
        encoding='utf-8-sig', newline='') as stream:
    source = {(row['seed'], row['profile'], row['variant'], row['step']): row
              for row in csv.DictReader(stream)}
summary = json.loads((HERE / 'summary.json').read_text(encoding='utf-8'))
totals = {}
seen = set()
for row in rows:
    key = row['seed'], row['profile'], row['variant'], row['step']
    assert key not in seen and key in source
    seen.add(key)
    baseline = int(row['ready_size'])
    strict = int(row['strict_frontier_size'])
    removed = int(row['removed_by_exposure_count'])
    assert baseline >= strict >= 0 and baseline - strict == removed
    assert int(source[key]['ready_size']) == baseline
    outside = row['served_outside_strict_frontier'] == 'True'
    assert outside == (source[key]['served_class'] == 'exposure_exception')
    empty = row['strict_frontier_empty'] == 'True'
    assert empty == (strict == 0)
    assert row['served_is_root'] == source[key]['served_is_root']
    measurements = dict(events=1, ready_memberships=baseline, strict_frontier_memberships=strict,
                        removed_by_exposure_memberships=removed, changed_frontier_events=int(removed > 0),
                        strict_frontier_empty_events=int(empty), served_outside_strict_frontier=int(outside),
                        served_roots=int(row['served_is_root'] == 'True'))
    for group in ('pooled', f'variant:{key[2]}', f'profile:{key[1]}:{key[2]}',
                  f'trajectory:{key[0]}:{key[1]}:{key[2]}'):
        totals.setdefault(group, Counter()).update(measurements)
assert len(rows) == len(seen) == len(source) == 3240
assert {key: dict(value) for key, value in totals.items()} == summary['groups']
result = dict(status='PASS_CSV_AGGREGATES_AND_SOURCE_EXPOSURE_FLAGS', rows=3240, groups=len(totals),
              scope_vi='Kiểm độc lập số học và identity của CSV output, không chứng minh lại M28 từ gzip.',
              source_trace_reads=0, model_calls=0, world_calls=0)
with (HERE / 'independent-check.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
print(json.dumps(result, ensure_ascii=False))
