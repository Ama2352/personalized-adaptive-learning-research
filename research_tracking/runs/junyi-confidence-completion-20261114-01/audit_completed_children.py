"""Kiểm lineage, coverage và SHA checkpoint confidence đã hoàn tất trên D."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUTPUT = ROOT/'artifacts/akt/confidence/full-train80-20261114-02'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


identity = json.loads((OUTPUT/'IDENTITY.json').read_text())
spool = json.loads((OUTPUT/'SPOOL_COMPLETE.json').read_text())
request = json.loads((ROOT/'research_tracking/runs/junyi-confidence-train80-20261114-01/request.json').read_text())
graph = json.loads((ROOT/request['topology_file']).read_text())
expected_edges = {tuple(pair) for pair in graph['corrected_edges']}
reasons = Counter()
children = []
edges = []
targets = 0
solver_exceptions = []
for marker_path in sorted((OUTPUT/'children').glob('*/COMPLETE.json')):
    marker = json.loads(marker_path.read_text())
    folder = marker_path.parent
    for name, digest in marker['files'].items():
        path = folder/name
        assert path.resolve().is_relative_to(folder.resolve())
        assert sha(path) == digest
    summary = json.loads((folder/'summary.json').read_text())
    child = summary['child']
    assert child == marker['child'] and child not in children
    assert summary['train_view_identity'] == identity['train_view_identity']
    assert summary['recipe_identity'] == identity['recipe_identity']
    assert summary['targets'] == spool['child_counts'].get(child, 0)
    assert {(edge['parent_id'], edge['child_id']) for edge in summary['edges']} == {
        pair for pair in expected_edges if pair[1] == child}
    assert summary['oof_rows'] == summary['targets']*len(summary['edges'])
    for edge in summary['edges']:
        reasons[edge['reason'] or 'SUPPORTED'] += 1
        if edge['supported']:
            assert 0 <= edge['confidence'] <= 1
    for fit in summary['fit_ledger']:
        if (fit.get('reason') or '').startswith('SOLVER_EXCEPTION:'):
            solver_exceptions.append(dict(child=child, reason=fit['reason']))
    children.append(child)
    edges.extend(summary['edges'])
    targets += summary['targets']
assert not solver_exceptions, solver_exceptions
result = dict(status='COMPLETED_CHILD_ARTIFACTS_VERIFIED', children=len(children),
              expected_children=len({child for _, child in expected_edges}), edges=len(edges),
              child_targets=targets, reason_counts=dict(reasons), solver_exceptions=solver_exceptions)
(HERE/'child-audit-current.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result))
