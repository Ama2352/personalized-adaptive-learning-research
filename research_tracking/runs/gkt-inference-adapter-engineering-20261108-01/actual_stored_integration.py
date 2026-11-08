"""Actual stored GKT04 weights integration only; not part of portable unit suite."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

ROOT = Path.cwd().resolve(); BUNDLE = ROOT / 'research_tracking/runs/gkt-checkpoint-engineering-20261108-01'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True); args = parser.parse_args()
assert not args.output.exists() and args.output.parent.is_relative_to(ROOT / 'artifacts/akt/local-tests')
assert sha(BUNDLE / 'manifest.json') == '0e0f0a19e466fd9c334e7fc279a1ebe4669babd0c2b8dd000542c009207b4cac'
manifest = json.loads((BUNDLE / 'manifest.json').read_bytes())
input_names = ['acceptance.json', 'successful_checkpoint__metadata.json', 'successful_checkpoint__COMPLETE.json']
for name in input_names:
    assert sha(BUNDLE / name) == manifest['outputs_sha256'][name]
acceptance = json.loads((BUNDLE / 'acceptance.json').read_bytes())
binary = next(x for x in acceptance['selected_binary_inventory_no_copy'] if x['path'].endswith('/weights.pt'))
checkpoint_path = ROOT / binary['path']; assert sha(checkpoint_path) == binary['sha256']
directory = checkpoint_path.parent
assert sha(directory / 'metadata.json') == manifest['outputs_sha256']['successful_checkpoint__metadata.json']
assert sha(directory / 'COMPLETE.json') == manifest['outputs_sha256']['successful_checkpoint__COMPLETE.json']
metadata = json.loads((BUNDLE / 'successful_checkpoint__metadata.json').read_bytes())
identity = metadata['identity']; complete_sha = sha(directory / 'COMPLETE.json')
inputs_before = {str(p.relative_to(ROOT)): sha(p) for p in
    [BUNDLE / 'manifest.json', *[BUNDLE / name for name in input_names], checkpoint_path,
     directory / 'metadata.json', directory / 'COMPLETE.json']}

import numpy as np
import torch
from knowledge_tracing.gkt import adapter as ga
from knowledge_tracing.gkt import training_checkpoint as cp
from knowledge_tracing.shared_kt import CausalSequenceInputs, StableVocabulary
from knowledge_tracing.simulator_bridge import ItemQuery, Observation, SimulatorBank, SimulatorItem

def forbidden(*a, **k): raise AssertionError('integration must not optimize/train')
torch.optim.Adam.step = forbidden
bank = SimulatorBank(identity['binding']['domain'], tuple(SimulatorItem(item, node, 1.) for item, node in
    [('a', 'A'), ('a2', 'A'), ('b', 'B'), ('c', 'C'), ('u', 'C'), ('o', 'B')]))
vocabulary = StableVocabulary(('a', 'b', 'c', 'a2', 'u')); mapping = {'a': 'A', 'a2': 'A', 'b': 'B', 'c': 'C'}
spec = ga.GKTInferenceSpec('full_prefix', 'query_only', 'unsupported_history', 12, 'cpu', 'float64')
binding = ga.inference_identity(identity, checkpoint_manifest_sha256=complete_sha, bank=bank,
                                item_vocabulary=vocabulary, item_to_node=mapping, spec=spec)
before_sources = ga.source_identity(); rng = torch.random.get_rng_state().clone(); calls = []
original_load = cp.torch.load
def counted(payload, **kwargs):
    assert kwargs == dict(weights_only=True, map_location='cpu')
    calls.append('ACTUAL_VERIFIED_BYTESIO_TORCH_LOAD'); return original_load(payload, **kwargs)
cp.torch.load = counted
try:
    adapter = ga.load_frozen_engineering_gkt(directory, expected_manifest_sha256=complete_sha,
        expected_checkpoint_identity=identity, bank=bank, item_vocabulary=vocabulary, item_to_node=mapping,
        spec=spec, expected_inference_binding=binding, max_checkpoint_bytes=1_000_000)
finally:
    cp.torch.load = original_load
assert calls == ['ACTUAL_VERIFIED_BYTESIO_TORCH_LOAD'] and torch.equal(rng, torch.random.get_rng_state())
source = CausalSequenceInputs(np.asarray([0, 1, 4, 2, -1, 0]), np.arange(6),
    np.asarray([-1, 0, 1, 0, 1, 0]), np.arange(101, 107), np.asarray([0, 6]), ('handmade-integration',) * 6)
scores = adapter.predict_details(source)
coverage = ga.population_summary(scores, expected_source_rows=tuple(range(101, 107)))
assert coverage['expected_targets'] == 6 and coverage['scored_targets'] == 2 and coverage['unsupported_targets'] == 4
assert coverage['research_fitted_targets'] == 0
assert [x.global_rank for x in scores] == list(range(6))
assert [x.support_reason for x in scores] == ['cold_query_only', 'known_history', 'unmapped_item',
                                            'unsupported_history', 'oov_item', 'unsupported_history']
history = ga.GKTHistory('handmade-integration', ())
assert adapter.query(history, ItemQuery('a', 0, 101), learner_id=history.learner_id).probability == scores[0].probability
history = ga.GKTHistory(history.learner_id, (Observation(ItemQuery('a', 0, 101), 0),))
assert adapter.query(history, ItemQuery('b', 1, 102), learner_id=history.learner_id).probability == scores[1].probability
aliases = adapter.query_many(history, (ItemQuery('a', 1, 102), ItemQuery('a2', 1, 102)), learner_id=history.learner_id)
assert aliases[0].probability == aliases[1].probability and len(history.observations) == 1
try:
    adapter.as_online_backend()
except NotImplementedError:
    fitted_rejected = True
else:
    raise AssertionError('engineering must not become fitted OnlineSession')
assert {x.weight_role for x in scores} == {'synthetic_trained_engineering_only'} and not any(x.research_fitted for x in scores)
assert adapter.binding['mapping_provenance'] == 'caller_declared_inference_mapping_NOT_training_attested'
assert ga.source_identity() == before_sources and all(sha(ROOT / name) == h for name, h in inputs_before.items())
value = dict(status='ACTUAL_STORED_GKT04_ADAPTER_ACCEPTED_NOT_FITTED_RESEARCH', actual_torch_loads=1,
    mock_loads=0, optimizer_steps=0, source_before=before_sources, source_after=ga.source_identity(),
    input_sha256=inputs_before, inputs_unchanged=True, target_population=coverage, scores=[asdict(x) for x in scores],
    offline_query_parity=True, same_node_alias_parity=True, immutable_probe=True, fitted_online_promotion_rejected=fitted_rejected,
    inference_binding=binding, input_limitations='Handmade observables; caller-declared inference map NOT train-attested; no scientific fit/domain certificate.')
with args.output.open('x', encoding='utf-8') as stream:
    json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps(dict(status=value['status'], actual_torch_loads=1, optimizer_steps=0, target_population=coverage,
                     result_sha256=sha(args.output))))
