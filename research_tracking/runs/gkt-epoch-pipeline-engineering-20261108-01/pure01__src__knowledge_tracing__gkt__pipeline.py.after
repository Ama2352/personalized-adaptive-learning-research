"""Bounded observable GKT epoch→selection→CSV engineering; chưa research fit.

Không đổi GKT03/04/05, không checkpoint/resume format mới hoặc OnlineSession.
COMPLETE của run bind mapping đã thực dùng; không chứng minh semantic map đúng.
"""
from dataclasses import asdict, dataclass
import csv
import io
import json
import math
import os
from pathlib import Path
import random
import time
import traceback

import numpy as np
import torch
from torch.nn import functional as F

from knowledge_tracing.simulator_bridge import identity_hash
from . import adapter as inference
from . import training as step_training
from . import training_checkpoint as checkpoint
from .training_data import GKTPreparedData, GKTPreparedSequence, source_identity as data_sources


@dataclass(frozen=True)
class GKTEpochPlan:
    max_epochs: int
    batch_size: int
    shuffle_seed: int
    selection_policy: str
    min_delta: float
    tie_policy: str

    def __post_init__(self):
        if (type(self.max_epochs) is not int or not 1 <= self.max_epochs <= 2
                or type(self.batch_size) is not int or not 1 <= self.batch_size <= 2
                or type(self.shuffle_seed) is not int or self.shuffle_seed < 0
                or self.selection_policy not in ('min_selection_mean_bce', 'last_complete_epoch_no_selection')
                or type(self.min_delta) not in (int, float) or not math.isfinite(self.min_delta) or self.min_delta < 0
                or self.tie_policy != 'earliest_epoch'
                or (self.selection_policy == 'last_complete_epoch_no_selection' and self.min_delta != 0)):
            raise ValueError('explicit bounded epoch/order/selection/tie policy required')


@dataclass(frozen=True)
class GKTPipelineBudget:
    max_steps: int
    max_targets: int
    max_seconds: float
    max_checkpoint_bytes: int
    max_prediction_bytes: int
    approval_reference: str

    def __post_init__(self):
        if (type(self.max_steps) is not int or not 1 <= self.max_steps <= 4
                or type(self.max_targets) is not int or not 1 <= self.max_targets <= 96
                or type(self.max_seconds) not in (int, float) or not math.isfinite(self.max_seconds)
                or not 0 < self.max_seconds <= 60 or type(self.max_prediction_bytes) is not int
                or not 1 <= self.max_prediction_bytes <= 1024 * 1024
                or type(self.approval_reference) is not str or not self.approval_reference.strip()
                or len(self.approval_reference) > 256):
            raise ValueError('explicit tiny engineering run budget/approval required')
        checkpoint._limit(self.max_checkpoint_bytes)


def source_identity():
    root = Path(__file__).resolve().parents[3]
    return {**data_sources(), **inference.source_identity(),
            'src/knowledge_tracing/gkt/pipeline.py': checkpoint._sha(Path(__file__).read_bytes())}


def select_epoch(epochs, plan):
    """Pure selector over complete fixed-population epoch receipts, no Test access."""
    if (type(plan) is not GKTEpochPlan or type(epochs) not in (list, tuple)
            or len(epochs) != plan.max_epochs or [x['epoch'] for x in epochs] != list(range(1, plan.max_epochs + 1))
            or any(x.get('complete_epoch') is not True for x in epochs)):
        raise ValueError('all requested epochs must be complete before final selection')
    fingerprints = {(x['selection']['eligible_population_sha256'], x['selection']['expected_population_sha256']) for x in epochs}
    if len(fingerprints) != 1:
        raise ValueError('selection populations differ across epochs')
    for row in epochs:
        value = row['selection']['mean_loss']
        if (row['selection']['population']['scored_targets'] < 1 or type(value) not in (int, float)
                or not math.isfinite(value) or value < 0):
            raise ValueError('nonempty finite selection objective required')
    if plan.selection_policy == 'last_complete_epoch_no_selection':
        return epochs[-1]['epoch']
    best = epochs[0]
    for row in epochs[1:]:
        if row['selection']['mean_loss'] < best['selection']['mean_loss'] - plan.min_delta:
            best = row
    return best['epoch']


def collate_sequences(records, *, dtype):
    """Whole learners only; model-valid mask is separate from real target ledger."""
    if (type(records) not in (tuple, list) or not 1 <= len(records) <= 2
            or any(type(x) is not GKTPreparedSequence for x in records)
            or dtype not in (torch.float32, torch.float64)):
        raise ValueError('bounded exact prepared learner sequences required')
    width = max(len(x.items) for x in records)
    if not 1 <= width <= 12:
        raise ValueError('whole learner exceeds toy cap; no chunking/reset workaround')
    shape = (len(records), width)
    ids = torch.full(shape, -1, dtype=torch.long, device='cpu')
    labels = torch.full(shape, -1, dtype=torch.long, device='cpu')
    rows = torch.full(shape, -1, dtype=torch.long, device='cpu')
    ranks = torch.full(shape, -1, dtype=torch.long, device='cpu')
    model_valid = torch.zeros(shape, dtype=torch.bool, device='cpu')
    loss = torch.zeros(shape, dtype=torch.bool, device='cpu')
    real = torch.zeros(shape, dtype=torch.bool, device='cpu')
    for i, record in enumerate(records):
        n = len(record.items)
        ids[i, :n] = torch.tensor(record.node_indices, dtype=torch.long, device='cpu')
        labels[i, :n] = torch.tensor(record.targets, dtype=torch.long, device='cpu')
        rows[i, :n] = torch.tensor(record.source_rows, dtype=torch.long, device='cpu')
        ranks[i, :n] = torch.arange(n, dtype=torch.long, device='cpu')
        model_valid[i, :n] = torch.tensor(record.model_valid_mask, dtype=torch.bool, device='cpu')
        loss[i, :n] = torch.tensor(record.loss_mask, dtype=torch.bool, device='cpu')
        real[i, :n] = True
    return ids, labels, model_valid, loss, rows, ranks, real


def _model_contract(model, data, settings):
    data.assert_integrity()
    if (type(model) is not step_training.GKTStaticRecurrentCandidate or model.config != data.model_config
            or model.binding != data.binding or model.graph_sha256 != data.training_encoding_identity['graph_sha256']
            or model.recipe_sha256 != data.recurrent_recipe_sha256 or settings.precision != data.recipe.precision):
        raise ValueError('current model must match bound data/node graph/recipe')
    model._bound(data.binding, model.graph_sha256)


def evaluate_selection(model, data, *, deadline):
    """Stable logit BCE, frozen values, predict-before-observe; no fit/adapter freeze."""
    data.assert_integrity()
    if (type(model) is not step_training.GKTStaticRecurrentCandidate or model.config != data.model_config
            or model.binding != data.binding or model.graph_sha256 != data.training_encoding_identity['graph_sha256']
            or model.recipe_sha256 != data.recurrent_recipe_sha256):
        raise ValueError('selection model/data/graph/recipe binding mismatch')
    before = step_training.model_digest(model)
    flags = tuple(m.training for m in model.modules())
    predictions = {}; total = 0.; count = 0
    with torch.inference_mode(), torch.device('cpu'):
        for record in data.selection:
            if time.perf_counter() >= deadline:
                raise TimeoutError('selection deadline before forward')
            ids, labels, valid, loss, _, _, _ = collate_sequences((record,), dtype=model.adjacency.dtype)
            state = model.initial_state(1, binding=data.binding, graph_sha256=model.graph_sha256)
            result = model.sequence(ids, labels, valid, initial_state=state, binding=data.binding, graph_sha256=model.graph_sha256)
            if loss.any():
                selected = result.logits[loss]
                objective = F.binary_cross_entropy_with_logits(selected, labels[loss].to(selected.dtype), reduction='sum')
                if not torch.isfinite(objective):
                    raise ValueError('nonfinite selection objective')
                total += float(objective); count += int(loss.sum())
            # Predictions recorded before joining the row's correct label for export.
            for rank, source in enumerate(record.source_rows):
                predictions[source] = (float(result.probabilities[0, rank]) if record.loss_mask[rank] else None,
                                       float(result.logits[0, rank]) if record.loss_mask[rank] else None)
            if time.perf_counter() >= deadline:
                raise TimeoutError('selection deadline after forward')
    rows = []
    for record in data.selection:
        for rank, source in enumerate(record.source_rows):
            probability, logit = predictions[source]; node = record.node_indices[rank]
            rows.append(dict(learner_id=record.learner_id, source_row=source, item_id=record.items[rank],
                node_id=None if node < 0 else data.binding.node_ids[node], timestamp=record.timestamps[rank],
                global_rank=rank, role='selection', correct=record.targets[rank], probability=probability, logit=logit,
                support_reason=record.support_reasons[rank], history_available=rank,
                history_used=rank if probability is not None else 0, context_reset=False,
                score_kind='uncalibrated_node_response_probability', weight_role=step_training.WEIGHT_ROLE,
                research_fitted=False))
    expected = [source for record in data.selection for source in record.source_rows]
    assert [x['source_row'] for x in rows] == expected and len(predictions) == len(expected)
    eligible = [x['source_row'] for x in rows if x['probability'] is not None]
    if count != len(eligible) or count < 1:
        raise ValueError('selection requires nonempty fully accounted eligible population')
    if step_training.model_digest(model) != before or tuple(m.training for m in model.modules()) != flags:
        raise ValueError('selection changed model weights/flags')
    data.assert_integrity()
    return dict(loss_sum=total, mean_loss=total / count, predictions=rows,
        population=dict(expected_targets=len(expected), scored_targets=count, unsupported_targets=len(expected) - count,
                        research_fitted_targets=0), eligible_population_sha256=identity_hash(eligible),
        expected_population_sha256=identity_hash([(x['learner_id'], x['source_row'], x['item_id'], x['global_rank']) for x in rows]))


def _write_json(path, value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode('utf-8') + b'\n'
    if len(raw) > 65536:
        raise ValueError('bounded run JSON exceeded64KiB')
    with path.open('xb') as stream:
        stream.write(raw)
    return checkpoint._sha(raw)


def export_predictions(path, rows, *, checkpoint_manifest_sha256, max_bytes):
    """Full original population, including None probabilities; no fitted export route."""
    if (type(rows) not in (list, tuple) or not 1 <= len(rows) <= 24
            or any(type(x) is not dict for x in rows) or len({x['source_row'] for x in rows}) != len(rows)
            or any(x.get('research_fitted') is not False for x in rows)
            or not step_training._sha(checkpoint_manifest_sha256)):
        raise ValueError('aligned explicit engineering population required')
    for row in rows:
        p = row['probability']
        if (type(row['source_row']) is not int or row['source_row'] < 1 or row['role'] != 'selection'
                or type(row['correct']) is not int or row['correct'] not in (0, 1)
                or (p is not None and (type(p) not in (int, float) or not math.isfinite(p) or not 0 <= p <= 1))
                or (p is None) != (row['support_reason'] not in ('known_history', 'cold_query_only'))):
            raise ValueError('finite supported probabilities or explicit None reason required')
    rows = [{**row, 'checkpoint_manifest_sha256': checkpoint_manifest_sha256} for row in rows]
    buffer = io.StringIO(newline=''); writer = csv.DictWriter(buffer, fieldnames=tuple(rows[0]))
    writer.writeheader(); writer.writerows(rows); raw = buffer.getvalue().encode('utf-8')
    if type(max_bytes) is not int or not 1 <= len(raw) <= max_bytes <= 1024 * 1024:
        raise ValueError('explicit prediction CSV byte budget exceeded')
    with Path(path).open('xb') as stream:
        stream.write(raw)
    return checkpoint._sha(raw)


@dataclass(frozen=True)
class GKTRunResult:
    output_directory: Path
    manifest_sha256: str
    selected_epoch: int
    completed_epochs: int
    optimizer_steps: int
    role: str = 'synthetic_selected_engineering_only'


class GKTPipelineFailure(RuntimeError):
    """Failure keeps artifacts/counters, not a rollback or resume promise."""


def run_gkt_epochs(data, *, model, optimizer, settings, plan, budget, output_directory):
    if (type(data) is not GKTPreparedData or type(settings) is not step_training.GKTTrainingSettings
            or type(plan) is not GKTEpochPlan or type(budget) is not GKTPipelineBudget):
        raise ValueError('typed explicit engineering data/model/run configuration required')
    _model_contract(model, data, settings)
    initial_optimizer_sha256 = step_training._optimizer_identity(optimizer, model, settings)
    initial_model_sha256 = step_training.model_digest(model)
    train_eligible = [source for record in data.train for source, selected in zip(record.source_rows, record.loss_mask) if selected]
    if (math.ceil(len(data.train) / plan.batch_size) * plan.max_epochs > budget.max_steps
            or len(train_eligible) * plan.max_epochs > budget.max_targets
            or any(not any(x.loss_mask) for x in data.train)):
        raise ValueError('planned whole-learner epochs exceed budget or contain no-loss learner; no silent skip')
    directory = checkpoint._directory(output_directory)
    if not directory.parent.is_dir():
        raise ValueError('caller must create approved run parent')
    directory.mkdir(exist_ok=False)
    started = time.perf_counter(); deadline = started + budget.max_seconds
    sources = source_identity(); encoding = data.training_encoding_identity
    count = dict(started_steps=0, returned_steps=0, started_targets=0, returned_targets=0)
    epochs = []; usage = []; pending = {}; handles = []; rng = torch.random.get_rng_state().clone()
    def check():
        data.assert_integrity()
        if source_identity() != sources:
            raise ValueError('pipeline source changed')
        if time.perf_counter() >= deadline:
            raise TimeoutError('engineering run deadline')
    def event(value):
        with (directory / 'optimizer_events.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(value, sort_keys=True, allow_nan=False) + '\n'); stream.flush(); os.fsync(stream.fileno())
    def before_step(opt, args, kwargs):
        check()
        if count['started_steps'] >= budget.max_steps or count['started_targets'] + pending['targets'] > budget.max_targets:
            raise TimeoutError('cumulative optimizer budget exhausted')
        event(dict(event='step_started', ordinal=count['started_steps'] + 1, **pending))
        count['started_steps'] += 1; count['started_targets'] += pending['targets']
    def after_step(opt, args, kwargs):
        count['returned_steps'] += 1; count['returned_targets'] += pending['targets']
        event(dict(event='step_returned', ordinal=count['returned_steps'], **pending))
    try:
        handles = [optimizer.register_step_pre_hook(before_step), optimizer.register_step_post_hook(after_step)]
        for epoch in range(1, plan.max_epochs + 1):
            check(); records = list(data.train); random.Random(plan.shuffle_seed + epoch).shuffle(records)
            processed = []; losses = 0.; last = None; epoch_steps_before = count['started_steps']
            for offset in range(0, len(records), plan.batch_size):
                block = tuple(records[offset:offset + plan.batch_size]); check()
                ids, labels, valid, loss, rows, ranks, real = collate_sequences(block, dtype=model.adjacency.dtype)
                state = model.initial_state(len(block), binding=data.binding, graph_sha256=model.graph_sha256)
                batch = step_training.bind_train_batch(query_ids=ids, responses=labels, event_valid_mask=valid,
                    loss_mask=loss, initial_state=state, learner_ids=tuple(x.learner_id for x in block),
                    source_rows=rows, global_ranks=ranks, binding=data.binding, graph_sha256=model.graph_sha256,
                    recipe_sha256=model.recipe_sha256, initial_state_model_sha256=step_training.model_digest(model),
                    role=step_training.TRAIN_ROLE, synthetic_only=True, source_sha256=step_training.source_identity())
                proof = dict(epoch=epoch, batch_sha256=batch.content_sha256, source_rows=rows[real].tolist(),
                    mapped_node_indices=ids[real].tolist(), eligible_source_rows=rows[loss].tolist(),
                    training_encoding_sha256=identity_hash(encoding), mapping_sha256=encoding['mapping_sha256'],
                    model_sha256_before=batch.initial_state_model_sha256)
                used = dict(prepared=proof, prepared_sha256=identity_hash(proof), completed=None)
                usage.append(used); pending.clear(); pending.update(targets=int(loss.sum()), epoch=epoch, mapping_usage_sha256=used['prepared_sha256'])
                used_before = count['started_steps']
                last = step_training.train_gkt_batch(model, optimizer, batch, settings=settings,
                    budget=step_training.GKTStepBudget(budget.max_steps, budget.max_targets, budget.max_seconds,
                        count['started_steps'], count['started_targets'], started))
                if not last.complete_train_step or last.optimizer_steps != 1:
                    raise TimeoutError('incomplete optimizer batch; retain partial run')
                assert count['started_steps'] == count['returned_steps'] == used_before + 1
                assert last.model_sha256_before == proof['model_sha256_before']
                used['completed'] = dict(model_sha256_after=last.model_sha256_after, optimizer_steps=last.optimizer_steps,
                    optimizer_sha256_before=last.optimizer_sha256_before, optimizer_sha256_after=last.optimizer_sha256_after)
                processed.extend(last.selected_source_rows); losses += last.loss_sum
            if len(processed) != len(set(processed)) or set(processed) != set(train_eligible):
                raise ValueError('incomplete/duplicate epoch training population')
            check(); evaluation = evaluate_selection(model, data, deadline=deadline); check()
            epoch_directory = directory / f'epoch-{epoch:03d}'; epoch_directory.mkdir(exist_ok=False)
            saved = checkpoint.save_engineering_weights(epoch_directory / 'weights', model, last,
                approval_reference=budget.approval_reference, max_checkpoint_bytes=budget.max_checkpoint_bytes)
            csv_sha = export_predictions(epoch_directory / 'selection.csv', evaluation['predictions'],
                checkpoint_manifest_sha256=saved['manifest_sha256'], max_bytes=budget.max_prediction_bytes)
            check()
            evaluation.pop('predictions')
            row = dict(epoch=epoch, complete_epoch=True, train_loss_sum=losses,
                train_mean_loss=losses / len(processed), optimized_source_rows=processed,
                optimizer_steps=count['started_steps'] - epoch_steps_before, selection=evaluation,
                checkpoint_relative_directory=str(saved['directory'].relative_to(directory)),
                checkpoint_manifest_sha256=saved['manifest_sha256'], checkpoint_identity=saved['identity'],
                selection_csv_sha256=csv_sha)
            epochs.append(row); _write_json(epoch_directory / 'epoch.json', row)
        check(); selected_epoch = select_epoch(epochs, plan); chosen = epochs[selected_epoch - 1]
        chosen_path = directory / chosen['checkpoint_relative_directory']
        spec = inference.GKTInferenceSpec(data.recipe.history_policy, data.recipe.first_target_policy,
            data.recipe.oov_policy, data.selection_shard.max_events_per_learner, 'cpu', data.recipe.precision)
        inference_binding = inference.inference_identity(chosen['checkpoint_identity'],
            checkpoint_manifest_sha256=chosen['checkpoint_manifest_sha256'], bank=data.selection_shard.bank,
            item_vocabulary=data.train_item_vocabulary, item_to_node=dict(data.training_map), spec=spec)
        loaded = inference.load_frozen_engineering_gkt(chosen_path,
            expected_manifest_sha256=chosen['checkpoint_manifest_sha256'], expected_checkpoint_identity=chosen['checkpoint_identity'],
            bank=data.selection_shard.bank, item_vocabulary=data.train_item_vocabulary,
            item_to_node=dict(data.training_map), spec=spec, expected_inference_binding=inference_binding,
            max_checkpoint_bytes=budget.max_checkpoint_bytes)
        # Stable export already exists. Verify selected loader parity against the complete row population.
        selected_csv = directory / f'epoch-{selected_epoch:03d}/selection.csv'
        raw_csv = selected_csv.read_bytes()
        if checkpoint._sha(raw_csv) != chosen['selection_csv_sha256']:
            raise ValueError('selected prediction bytes changed')
        old_rows = list(csv.DictReader(io.StringIO(raw_csv.decode('utf-8')))); observed = []
        for record in data.selection:
            lookup = {x: i for i, x in enumerate(data.train_item_vocabulary.values)}
            from knowledge_tracing.shared_kt import CausalSequenceInputs
            n = len(record.items)
            inputs = CausalSequenceInputs(np.asarray([lookup.get(x, -1) for x in record.items], dtype=np.int64),
                np.asarray(record.timestamps, dtype=np.int64), np.asarray([-1, *record.targets[:-1]], dtype=np.int64),
                np.asarray(record.source_rows, dtype=np.int64), np.asarray([0, n], dtype=np.int64), (record.learner_id,) * n)
            observed.extend(loaded.predict_details(inputs))
        if (len(observed) != len(old_rows) or any(int(row['source_row']) != score.source_row
                or (row['probability'] == '') != (score.probability is None)
                or (score.probability is not None and float(row['probability']) != score.probability)
                or row['support_reason'] != score.support_reason for row, score in zip(old_rows, observed))):
            raise ValueError('selected checkpoint/offline export parity mismatch')
        check()
        if not torch.equal(rng, torch.random.get_rng_state()):
            raise ValueError('pipeline changed caller Torch CPU RNG')
        with (directory / 'selected_predictions.csv').open('xb') as stream:
            stream.write(raw_csv)
        if count['started_steps'] != count['returned_steps'] or len(usage) != count['returned_steps'] or any(x['completed'] is None for x in usage):
            raise ValueError('incomplete optimizer/mapping usage evidence')
        for handle in handles:
            handle.remove()
        handles.clear()
        check()
        selected_usage = [x for x in usage if x['prepared']['epoch'] <= selected_epoch]
        payload = dict(schema_version=1, status='complete_epoch_candidates_ready_for_publication',
            role='synthetic_selected_engineering_only', data_sha256=data.content_sha256,
            training_encoding=encoding, graph_provenance=asdict(data.graph_provenance), recipe=asdict(data.recipe),
            plan=asdict(plan), budget=asdict(budget), sources_sha256=sources, epochs=epochs,
            optimizer_counters=count, mapping_usage=usage, selected_epoch=selected_epoch,
            selected_checkpoint_manifest_sha256=chosen['checkpoint_manifest_sha256'],
            selected_prediction_sha256=checkpoint._sha(raw_csv), selected_mapping_usage_sha256=identity_hash(selected_usage),
            training_mapping_usage_verified=True, mapping_origin='caller_declared_static_registry; mechanical usage only',
            initialization_provenance='caller_owned_initial_parameters_NOT_fit_attested',
            initial_model_sha256=initial_model_sha256, initial_optimizer_sha256=initial_optimizer_sha256,
            adapter_mapping_provenance=inference_binding['mapping_provenance'], optimizer_saved=False, rng_saved=False,
            hidden_state_saved=False, resume_supported=False, fitted_research_model=False,
            elapsed_seconds=time.perf_counter() - started)
        check(); manifest_sha = _write_json(directory / 'run.json', payload); check()
        marker = checkpoint._json(dict(status='COMPLETE_ENGINEERING_EPOCH_RUN', run_manifest_sha256=manifest_sha,
                                       selected_prediction_sha256=checkpoint._sha(raw_csv)))
        checkpoint._publish(directory, 'COMPLETE.json', marker)
        # A late commit remains historical evidence; failure receipt overrides it.
        # Consumers require returned success AND no failure.json plus controller budget acceptance.
        if time.perf_counter() >= deadline:
            raise TimeoutError('deadline after final publication; reject resource acceptance')
        return GKTRunResult(directory, manifest_sha, selected_epoch, len(epochs), count['returned_steps'])
    except Exception as error:
        with (directory / 'failure.log').open('x', encoding='utf-8') as stream:
            stream.write(traceback.format_exc())
        _write_json(directory / 'failure.json', dict(status='FAILED_RETAIN_PARTIAL_NO_RESUME', error_type=type(error).__name__,
            error=str(error), optimizer_counters=count, complete_epochs=len(epochs), mapping_usage=usage,
            data_sha256=data.content_sha256, source_sha256=sources, elapsed_seconds=time.perf_counter() - started,
            rollback_promised=False, fitted_research_model=False))
        raise GKTPipelineFailure('GKT engineering run failed; exact partial artifacts retained') from error
    finally:
        for handle in handles:
            handle.remove()
