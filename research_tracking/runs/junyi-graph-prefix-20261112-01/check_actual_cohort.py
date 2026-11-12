"""Đối chiếu prefix Junyi thực với graph976cạnh, không nạp model/Torch."""
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.akt.research_junyi_engineering import prepare_inputs
from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition, JunyiGraphPhaseSession
from knowledge_tracing.akt.windows import iter_windows
from knowledge_tracing.akt.types import UnseenTarget
from knowledge_tracing.shared_kt import PrerequisiteGraph

BUNDLE = Path(__file__).parent
request = json.loads((ROOT/'research_tracking/runs/junyi-akt-cuda-engineering-20261112-01/gpu-request.json').read_text())
views,encoding,learners,_ = prepare_inputs(
    ROOT/'artifacts/akt/junyi-cohorts/cuda-engineering320x300-20261112-01',
    ROOT/'artifacts/akt/junyi-roles/outer4-research-v1-20261112-01/roles.json',
    cohort_sha256=request['cohort_sha256'],roles_sha256=request['roles_sha256'])
graph_path = ROOT/'research_tracking/runs/cpu-junyi-graph-reconstruction-20261107-01/graph.json'
raw = graph_path.read_bytes()
stored = json.loads(raw)
graph = PrerequisiteGraph.from_edges(stored['nodes'],stored['corrected_edges'])
condition = JunyiGraphCondition(encoding,graph,hashlib.sha256(raw).hexdigest())
session = JunyiGraphPhaseSession(condition,views['selection'])
counts = dict(windows=0,supported_targets=0,oov_targets=0,targets_with_observed_parent=0)
started = time.perf_counter()
for learner in learners['selection']:
    for window in iter_windows(learner,encoding.native,training=False):
        if isinstance(window,UnseenTarget):
            counts['oov_targets'] += 1
            continue
        evidence = session.prefix_evidence(window)
        counts['windows'] += 1
        for row in evidence:
            if row is not None:
                counts['supported_targets'] += 1
                counts['targets_with_observed_parent'] += int(any(p.support for p in row.audit.parents))
session.assert_boundary()
assert counts['supported_targets']==1405 and counts['oov_targets']==125
result = dict(status='ACTUAL_JUNYI_PREFIX_CHECKED_NO_NEURAL_FORWARD',counts=counts,
    full_graph_nodes=len(graph.nodes),full_graph_edges=len(graph.edges),
    encoding=encoding.identity,condition=condition.identity,seconds=time.perf_counter()-started,
    neural_training_performed=False)
with (BUNDLE/'actual-cohort-prefix.json').open('x') as stream:
    json.dump(result,stream,indent=2)
print(json.dumps(result))
