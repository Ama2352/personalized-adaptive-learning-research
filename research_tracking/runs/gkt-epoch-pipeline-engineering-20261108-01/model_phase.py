"""DO NOT RUN before parent source/pure-test review. One2epoch toy,2planned updates."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path.cwd().resolve(); PREP = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--remaining-seconds', type=int, required=True); parser.add_argument('--parent-approval-reference', required=True)
args = parser.parse_args()
assert args.parent_approval_reference.strip() and 1 <= args.remaining_seconds <= 57
assert args.output.is_absolute() and args.output.is_relative_to(ROOT / 'artifacts/akt/local-tests') and not args.output.exists()
contract = json.loads((PREP / 'pre_update_contract.json').read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert all(sha(ROOT / name) == h for name, h in contract['sources_sha256'].items())

import torch
from knowledge_tracing.gkt.recurrent import GKTStaticRecurrentCandidate
from knowledge_tracing.gkt import training as step
from knowledge_tracing.gkt import pipeline
from knowledge_tracing.gkt.training_data import prepare_gkt_training_data

# Explicitly reused HANDMADE test fixture definitions, no pytest execution or auto fixtures.
test_path = ROOT / 'tests/gkt/test_pipeline.py'
spec = importlib.util.spec_from_file_location('gkt06_handmade_fixture_only', test_path)
fixture = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture)
parts = fixture.data_parts(); data = prepare_gkt_training_data(**parts)
sources_before = pipeline.source_identity(); input_sha = data.content_sha256
with torch.random.fork_rng(devices=[]), torch.device('cpu'):
    torch.random.default_generator.manual_seed(42)
    model = GKTStaticRecurrentCandidate(data.model_config, data.binding, data.adjacency, **data.recipe.recurrent_kwargs())
    model.eval(); model.self_mlp[0].train(True)
    caller_flags = tuple(x.training for x in model.modules())
    settings = step.GKTTrainingSettings('adam', .01, (.8, .9), 1e-7, 0., .5,
                                       'mean_bce_on_explicit_loss_mask', 'float64')
    optimizer = torch.optim.Adam(model.parameters(), lr=settings.lr, betas=settings.betas, eps=settings.eps,
        weight_decay=settings.weight_decay, foreach=False, fused=False)
    plan = pipeline.GKTEpochPlan(2, 2, 42, 'min_selection_mean_bce', 0., 'earliest_epoch')
    budget = pipeline.GKTPipelineBudget(2, 12, args.remaining_seconds, 1_000_000, 20000, args.parent_approval_reference)
    before = step.model_digest(model); rng = torch.random.get_rng_state().clone()
    result = pipeline.run_gkt_epochs(data, model=model, optimizer=optimizer, settings=settings,
                                     plan=plan, budget=budget, output_directory=args.output)
    assert torch.equal(rng, torch.random.get_rng_state()) and tuple(x.training for x in model.modules()) == caller_flags
    assert all(p.requires_grad for p in model.parameters())
    assert len(optimizer._optimizer_step_pre_hooks) == len(optimizer._optimizer_step_post_hooks) == 0
    max_state_step = max(int(s['step'].item()) for s in optimizer.state.values())
    assert max_state_step == 2 and step.model_digest(model) != before
assert result.completed_epochs == result.optimizer_steps == 2 and not (args.output / 'failure.json').exists()
manifest = json.loads((args.output / 'run.json').read_bytes()); complete = json.loads((args.output / 'COMPLETE.json').read_bytes())
assert sha(args.output / 'run.json') == result.manifest_sha256 == complete['run_manifest_sha256']
events = [json.loads(line) for line in (args.output / 'optimizer_events.jsonl').read_text().splitlines()]
assert [x['event'] for x in events] == ['step_started', 'step_returned', 'step_started', 'step_returned']
assert manifest['optimizer_counters'] == dict(started_steps=2, returned_steps=2, started_targets=12, returned_targets=12)
lookup = {source: node for record in data.train for source, node in zip(record.source_rows, record.node_indices)}
for used in manifest['mapping_usage']:
    proof = used['prepared']
    assert set(proof['source_rows']) == set(lookup) and len(proof['source_rows']) == 6
    assert [lookup[source] for source in proof['source_rows']] == proof['mapped_node_indices']
    assert used['completed']['optimizer_steps'] == 1
assert all(x['selection']['population'] == dict(expected_targets=4, scored_targets=2,
    unsupported_targets=2, research_fitted_targets=0) for x in manifest['epochs'])
assert manifest['selected_epoch'] == pipeline.select_epoch(manifest['epochs'], plan)
assert manifest['training_mapping_usage_verified'] and manifest['fitted_research_model'] is False
assert manifest['adapter_mapping_provenance'] == 'caller_declared_inference_mapping_NOT_training_attested'
assert data.content_sha256 == input_sha and pipeline.source_identity() == sources_before
value = dict(status='ACTUAL_TWO_EPOCH_ENGINEERING_PIPELINE_ACCEPTED_NOT_RESEARCH_FITTED',
    role=result.role, completed_epochs=2, optimizer_step_returns=2, optimizer_step_started=2,
    selected_epoch=result.selected_epoch, max_optimizer_parameter_step=max_state_step,
    parameter_delta_present=True, mapping_usage_mechanically_verified=True, source_before=sources_before,
    source_after=pipeline.source_identity(), data_sha256=input_sha, training_encoding=data.training_encoding_identity,
    selection_population=manifest['epochs'][result.selected_epoch - 1]['selection']['population'],
    run_manifest_sha256=result.manifest_sha256, complete_marker_sha256=sha(args.output / 'COMPLETE.json'),
    selected_prediction_sha256=sha(args.output / 'selected_predictions.csv'),
    checkpoint_sha256_references={x['epoch']: x['checkpoint_manifest_sha256'] for x in manifest['epochs']},
    caller_flags_and_rng_preserved=True, owned_step_hooks_removed=True, no_resume_or_fitted_promotion=True)
target = args.output.parent / 'result.json'
with target.open('x', encoding='utf-8') as stream:
    json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps({k: value[k] for k in ('status', 'completed_epochs', 'optimizer_step_returns', 'selected_epoch',
    'selection_population', 'run_manifest_sha256', 'selected_prediction_sha256')}))
