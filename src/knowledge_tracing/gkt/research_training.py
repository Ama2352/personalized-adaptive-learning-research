"""Compute epoch/raw prediction GKT29, không fit hoặc execution authority.

Candidate cho gkt/research_training.py. Caller cấp actual authorization và
owned process budget trước model allocation. Không checkpoint/refit tự động.
"""
from dataclasses import asdict, dataclass, field, replace
import hashlib
import math
from pathlib import Path
import random
import time

import torch

from knowledge_tracing.akt.resources import memory_snapshot
from knowledge_tracing.akt import resources as resource_module
from knowledge_tracing import research_selection as reporting_module
from knowledge_tracing.research_selection import binary_row_log_loss
from knowledge_tracing.simulator_bridge import identity_hash
from knowledge_tracing.sakt.training import masked_bce, state_digest
from knowledge_tracing.sakt import training as loss_module
from knowledge_tracing.gkt import config as config_module, core, recurrent
from knowledge_tracing.gkt import research_model as model_module, research_data as data
from knowledge_tracing.gkt.research_model import GKTResearchModel
from knowledge_tracing.gkt.training import GKTTrainingSettings, _optimizer_identity
from knowledge_tracing.gkt import training as optimizer_module


_now = time.perf_counter
ROLE = 'gkt_research_compute_only_no_fit_attestation'
SETTINGS = GKTTrainingSettings('adam', 0.001, (0.9, 0.999), 1e-8, 0., 1.,
                               'mean_bce_on_explicit_loss_mask', 'float32')
_COUNTERS = ('input_targets', 'input_prefix_events', 'model_calls_started', 'model_calls_returned',
    'sequence_started', 'sequence_returned', 'tail_started', 'tail_returned', 'returned_sequence_observe_events',
    'padded_readout_slots', 'backward_started', 'backward_returned', 'clip_started', 'clip_returned',
    'adam_started', 'adam_returned', 'optimized_targets', 'scored_targets', 'complete_train_epochs')


def _need(ok, message):
    if not ok:
        raise ValueError(message)


@dataclass(frozen=True)
class GKTResearchSpec:
    epoch: int
    batch_size: int
    max_grad_norm: float

    def __post_init__(self):
        _need(type(self.epoch) is int and 1 <= self.epoch <= 50
              and type(self.batch_size) is int and self.batch_size == 4
              and type(self.max_grad_norm) in (int, float) and self.max_grad_norm == 1.,
              'Recipe29 epoch1..50/batch4/clip1 required')


@dataclass(frozen=True)
class GKTResearchBudget:
    started_at: float
    max_seconds: float
    max_rss_bytes: int
    min_available_ram_bytes: int
    max_input_targets: int
    max_prefix_events: int
    max_model_calls: int
    max_optimizer_steps: int
    max_optimized_targets: int
    max_scored_targets: int

    def __post_init__(self):
        _need(all(type(x) in (int, float) and math.isfinite(x) for x in
                  (self.started_at, self.max_seconds)) and self.max_seconds > 0,
              'Finite fixed monotonic origin and positive allowance required')
        for name in ('max_rss_bytes', 'min_available_ram_bytes', 'max_input_targets',
                     'max_prefix_events', 'max_model_calls', 'max_optimizer_steps',
                     'max_optimized_targets', 'max_scored_targets'):
            value = getattr(self, name)
            _need(type(value) is int and value >= 0, 'Nonnegative integer budget required')
        _need(self.max_rss_bytes > 0 and self.min_available_ram_bytes > 0, 'Memory caps required')


@dataclass
class GKTResearchProgress:
    model_binding_sha256: str
    rng_state: torch.Tensor
    counters: dict = field(default_factory=lambda: dict.fromkeys(_COUNTERS, 0))
    budget_sha256: str | None = None
    parameter_identity: tuple | None = None
    optimizer_object_id: int | None = None
    sources_sha256: tuple | None = None
    poisoned: bool = False

    def __post_init__(self):
        _need(type(self.model_binding_sha256) is str and len(self.model_binding_sha256) == 64,
              'Model binding required')
        _need(isinstance(self.rng_state, torch.Tensor) and self.rng_state.device.type == 'cpu'
              and self.rng_state.dtype == torch.uint8
              and self.rng_state.shape == torch.get_rng_state().shape, 'Actual owned CPU RNG bytes required')
        self.rng_state = self.rng_state.detach().clone()
        _need(type(self.counters) is dict and set(self.counters) == set(_COUNTERS)
              and all(type(x) is int and x >= 0 for x in self.counters.values()), 'Exact cumulative counters required')


class GKTResearchExecutionError(RuntimeError):
    def __init__(self, message, result):
        super().__init__(message)
        self.result = result


class _Limit(RuntimeError):
    pass


def model_source_identity():
    return tuple((name, hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()) for name, module in
                 (('config', config_module), ('core', core), ('recurrent', recurrent), ('research_model', model_module)))


def source_identity():
    helpers = tuple((name, hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest())
        for name, module in (('gkt/training.py', optimizer_module), ('sakt/training.py', loss_module),
                             ('akt/resources.py', resource_module), ('research_selection.py', reporting_module)))
    root = Path(config_module.__file__).resolve().parents[3]
    recipe = ('recipe29', hashlib.sha256((root/'docs/thesis_recovery/29_GKT_RESEARCH_NUMERICAL_RECIPE_V1.md').read_bytes()).hexdigest())
    return tuple(sorted((*data.source_identity(), *model_source_identity(), *helpers, recipe,
        ('gkt/research_training.py', hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))))


def _check(budget, resources):
    elapsed = _now()-budget.started_at
    _need(math.isfinite(elapsed) and elapsed >= 0, 'Invalid monotonic budget origin')
    if elapsed >= budget.max_seconds:
        raise _Limit('cumulative_deadline')
    snapshot = memory_snapshot()
    rss, peak, available = (snapshot[name] for name in
                           ('process_rss_bytes', 'process_peak_rss_bytes', 'system_available_ram_bytes'))
    _need(type(rss) is int and rss >= 0 and type(available) is int and available >= 0
          and (peak is None or type(peak) is int and peak >= 0), 'Unknown resource telemetry')
    resources['samples'] += 1
    resources['peak_rss_bytes'] = max(resources['peak_rss_bytes'], rss, peak or 0)
    resources['min_available_bytes'] = min(resources.get('min_available_bytes', available), available)
    if max(rss, peak or 0) > budget.max_rss_bytes or available < budget.min_available_ram_bytes:
        raise _Limit('memory_budget')
    if _now()-budget.started_at >= budget.max_seconds:
        raise _Limit('cumulative_deadline_after_sample')


def _optimizer(model, optimizer):
    _need(torch.get_default_dtype() == torch.float32, 'Recipe29 ambient default dtype must be FP32')
    _need(type(optimizer) is torch.optim.Adam, 'Exact native Adam required')
    for group in optimizer.param_groups:
        _need(group.get('decoupled_weight_decay', False) is False, 'Decoupled weight decay forbidden')
    _need(optimizer.defaults.get('decoupled_weight_decay', False) is False,
          'Decoupled weight decay default forbidden')
    digest = _optimizer_identity(optimizer, model, SETTINGS)
    for state in optimizer.state.values():
        if state:
            _need(state['step'].dtype == torch.float32 and state['step'].ndim == 0,
                  'Ordinary Adam scalar step must be FP32')
            _need(bool((state['exp_avg_sq'] >= 0).all()),
                  'Ordinary Adam second moment must be nonnegative before compute')
    return digest


def _binding(model, view, spec, budget, progress, optimizer, training):
    _need(type(model) is GKTResearchModel and type(view) is data.GKTResearchView
          and type(spec) is GKTResearchSpec and type(budget) is GKTResearchBudget
          and type(progress) is GKTResearchProgress, 'Exact research compute types required')
    _need(torch.get_default_dtype() == torch.float32, 'Recipe29 ambient default dtype must be FP32')
    spec.__post_init__()
    budget.__post_init__()
    progress.__post_init__()
    _need(not progress.poisoned, 'Incomplete progress cannot be retried or resumed')
    view.assert_integrity()
    model._bound(model.binding, model.graph_sha256)
    encoding = view.encoding
    _need(model.spec.phase_scope == encoding.optimization_scope
          and model.spec.phase_sha256 == encoding.optimization_phase_sha256
          and model.spec.encoding_sha256 == encoding.identity
          and model.spec.vocabulary_sha256 == identity_hash(list(encoding.exercise_encoding().vocabulary.values))
          and model.graph == view.graph and model.spec.sources_sha256 == model_source_identity(),
          'Research source/graph/optimization encoding binding mismatch')
    _need(not training or view.phase.scope in data.OPTIMIZATION_SCOPES, 'Prediction role cannot optimize')
    if training:
        _need(view.phase.scope == model.spec.phase_scope and view.phase.identity == model.spec.phase_sha256,
              'Optimization phase mismatch')
        _need(not torch.is_inference_mode_enabled(), 'Training inside inference_mode forbidden')
        _optimizer(model, optimizer)
        _need(spec.epoch == progress.counters['complete_train_epochs']+1, 'Contiguous complete epochs required')
    parameters = tuple((name, id(value), value.requires_grad) for name, value in model.named_parameters())
    _need(all(value.requires_grad for value in model.parameters()), 'All registered parameters must be trainable')
    stamp = identity_hash(asdict(budget))
    sources = source_identity()
    _need(dict(sources)['recipe29'] == model.spec.recipe_source_sha256, 'Recipe29 source changed')
    _need(progress.model_binding_sha256 == model.model_binding_sha256
          and progress.budget_sha256 in (None, stamp)
          and progress.parameter_identity in (None, parameters)
          and progress.sources_sha256 in (None, sources)
          and (not training or progress.optimizer_object_id in (None, id(optimizer))),
          'Cumulative progress/model/optimizer/budget changed')
    progress.budget_sha256, progress.parameter_identity = stamp, parameters
    progress.sources_sha256 = sources
    if training:
        progress.optimizer_object_id = id(optimizer)
    return sources


def _collect(view, training, budget, progress, resources):
    trajectories = view.phase.trajectories
    total = sum(len(t.observations) for t in trajectories)
    prefixes = sum(len(t.observations)*(len(t.observations)-1)//2 for t in trajectories)
    _need(all(0 < len(t.observations) <= 210 for t in trajectories), 'Whole trajectories length1..210 required')
    if (progress.counters['input_targets']+total > budget.max_input_targets
            or progress.counters['input_prefix_events']+prefixes > budget.max_prefix_events):
        raise _Limit('input_quota_before_collection')
    roles = {t.learner_id: shard.role for shard in view.phase.shards for t in shard.trajectories}
    expected = [(t.learner_id, rank, o.query, roles[t.learner_id]) for t in trajectories
                for rank, o in enumerate(t.observations)]
    mapping = dict(view.train_item_node_map)
    phase_id, encoding_id, graph_id = view.phase.identity, view.encoding.identity, view.graph.identity
    groups, seen = {}, set()
    stream = data.iter_gkt_research_inputs(view, training=training,
        limits=data.GKTResearchInputLimits(total, prefixes))
    try:
        for learner, rank, query, role in expected:
            if _now()-budget.started_at >= budget.max_seconds:
                raise _Limit('cumulative_deadline_during_inputs')
            if rank == 0:
                _check(budget, resources)
            entry = next(stream)
            _need(type(entry) is (data.GKTResearchTrainingTarget if training else data.GKTResearchInput),
                  'Research iterator record type mismatch')
            record = entry.inputs if training else entry
            progress.counters['input_targets'] += 1
            progress.counters['input_prefix_events'] += rank
            key = (learner, query.source_row, rank)
            _need(key not in seen and (record.learner_id, record.global_rank, record.query, record.origin_role)
                  == (learner, rank, query, role), 'Canonical population/order/query/role mismatch')
            seen.add(key)
            group = groups.setdefault(learner, dict(records=[], nodes=[], labels=[], past_answers=(), broken=False))
            node = mapping.get(query.item_id)
            reason = ('oov_item' if node is None else 'unsupported_history' if group['broken']
                      else 'known_history' if rank else 'cold_query_only')
            _need(record.support_reason == reason and record.phase_scope == view.phase.scope
                  and record.phase_sha256 == phase_id and record.encoding_sha256 == encoding_id
                  and record.graph_sha256 == graph_id and record.history_available == rank
                  and record.history_used == (rank if record.eligible else 0), 'Input support/lineage mismatch')
            if record.eligible:
                _need(record.query_node_id == node and record.past_queries == tuple(r.query for r in group['records'])
                      and record.past_node_ids == tuple(group['nodes'])
                      and type(record.past_responses) is tuple and len(record.past_responses) == rank
                      and all(type(y) is int and y in (0, 1) for y in record.past_responses),
                      'Full observable prefix mismatch')
                if training:
                    consistent = record.past_responses == tuple(group['labels'])
                elif rank:
                    consistent = record.past_responses[:-1] == group['past_answers']
                else:
                    consistent = record.past_responses == ()
                _need(consistent, 'Past responses changed')
                group['past_answers'] = record.past_responses
            else:
                _need(record.query_node_id is None and record.past_queries is None
                      and record.past_node_ids is None and record.past_responses is None,
                      'Unsupported suffix must stay null')
            if training:
                _need(record.eligible and type(entry.target) is int and entry.target in (0, 1),
                      'Every optimization target must be eligible and binary')
                group['labels'].append(entry.target)
            group['records'].append(replace(record, past_queries=None, past_node_ids=None, past_responses=None))
            group['nodes'].append(node)
            group['broken'] = group['broken'] or not record.eligible
        _need(next(stream, None) is None and len(seen) == total, 'Exact population required')
    finally:
        stream.close()
    _check(budget, resources)
    return list(groups.values())


def _batch(groups, training):
    lengths = [len(group['records']) if training else sum(r.eligible for r in group['records']) for group in groups]
    steps = max(lengths) if training else max(length-1 for length in lengths)
    ids = torch.zeros((len(groups), steps), dtype=torch.long, device='cpu')
    answers = torch.zeros_like(ids)
    valid = torch.zeros_like(ids, dtype=torch.bool)
    for index, (group, length) in enumerate(zip(groups, lengths)):
        used = length if training else length-1
        ids[index, :used] = torch.tensor(group['nodes'][:used], dtype=torch.long, device='cpu')
        answers[index, :used] = torch.tensor(group['labels'] if training else group['past_answers'],
                                           dtype=torch.long, device='cpu')
        valid[index, :used] = True
    return ids, answers, valid, lengths


def _run(model, view, *, optimizer, spec, budget, progress, training):
    resources = dict(samples=0, peak_rss_bytes=0)
    _check(budget, resources)
    sources = _binding(model, view, spec, budget, progress, optimizer, training)
    view_identity = view.identity
    model_identity = model.model_binding_sha256
    before, modes = state_digest(model), tuple((module, module.training) for module in model.modules())
    counts_before = dict(progress.counters)
    normalization_before = model.normalization_counts
    status, reason, error, cleanup_errors = 'bounded', 'not_started', None, []
    pending, rows, loss_values, groups = (), {}, [], []
    try:
        groups = _collect(view, training, budget, progress, resources)
        active = groups if training else [g for g in groups if any(r.eligible for r in g['records'])]
        if training:
            random.Random(42+spec.epoch).shuffle(active)
        blocks = [active[i:i+4] for i in range(0, len(active), 4)]
        targets = sum(len(g['records']) if training else sum(r.eligible for r in g['records']) for g in active)
        calls = len(blocks) if training else sum(1+int(max(sum(r.eligible for r in g['records']) for g in b) > 1) for b in blocks)
        c = progress.counters
        if (c['model_calls_started']+calls > budget.max_model_calls
                or training and (c['adam_started']+len(blocks) > budget.max_optimizer_steps
                                 or c['optimized_targets']+targets > budget.max_optimized_targets)
                or not training and c['scored_targets']+targets > budget.max_scored_targets):
            raise _Limit('whole_phase_quota_before_model_mutation')
        _check(budget, resources)
        with torch.random.fork_rng(devices=[]), torch.device('cpu'), torch.set_grad_enabled(training):
            if training:
                torch.set_rng_state(progress.rng_state)
            try:
                model.train(training)
                for block in blocks:
                    _check(budget, resources)
                    ids, answers, valid, lengths = _batch(block, training)
                    _check(budget, resources)
                    pending = tuple((r.learner_id, r.query.source_row, r.global_rank) for g in block
                                    for r in g['records'] if r.eligible)
                    if training:
                        _optimizer(model, optimizer)
                        optimizer.zero_grad(set_to_none=True)
                    if training or ids.shape[1]:
                        c['model_calls_started'] += 1
                        c['sequence_started'] += 1
                        with torch.set_grad_enabled(training):
                            output = model(ids, answers, valid, initial_state=None,
                                binding=model.binding, graph_sha256=model.graph_sha256)
                        c['sequence_returned'] += 1
                        c['model_calls_returned'] += 1
                        c['returned_sequence_observe_events'] += int(valid.sum())
                        c['padded_readout_slots'] += ids.numel()-int(valid.sum())
                    else:
                        output = None
                    _check(budget, resources)
                    if training:
                        total, count = masked_bce(output.logits, answers.float(), valid)
                        value = float(total.detach())
                        _need(count == len(pending) and math.isfinite(value) and value >= 0,
                              'Finite exact batch loss denominator required')
                        c['backward_started'] += 1
                        (total/count).backward()
                        c['backward_returned'] += 1
                        _check(budget, resources)
                        c['clip_started'] += 1
                        norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1., error_if_nonfinite=True)
                        c['clip_returned'] += 1
                        _need(bool(torch.isfinite(norm)), 'Finite clipped gradient norm required')
                        _optimizer(model, optimizer)
                        _check(budget, resources)
                        c['adam_started'] += 1
                        optimizer.step()
                        c['adam_returned'] += 1
                        c['optimized_targets'] += count
                        loss_values.append(value)
                        _optimizer(model, optimizer)
                    else:
                        state = (output.final_state if output is not None else model.initial_state(len(block),
                            binding=model.binding, graph_sha256=model.graph_sha256))
                        _need(state.history_counts.tolist() == [length-1 for length in lengths],
                              'Tail state must contain exact available history')
                        tail_ids = torch.tensor([g['nodes'][length-1] for g, length in zip(block, lengths)],
                                                device='cpu', dtype=torch.long)
                        c['model_calls_started'] += 1
                        c['tail_started'] += 1
                        tail = model.predict(state, tail_ids, binding=model.binding, graph_sha256=model.graph_sha256)
                        c['tail_returned'] += 1
                        c['model_calls_returned'] += 1
                        for index, (group, length) in enumerate(zip(block, lengths)):
                            probabilities = ([] if length == 1 else output.probabilities[index, :length-1].tolist())
                            probabilities.append(float(tail.probabilities[index]))
                            _need(all(math.isfinite(p) and 0 <= p <= 1 for p in probabilities), 'Finite raw probabilities required')
                            for record, probability in zip(group['records'][:length], probabilities):
                                rows[record.learner_id, record.query.source_row, record.global_rank] = probability
                                c['scored_targets'] += 1
                    pending = ()
                    _check(budget, resources)
            finally:
                if training:
                    progress.rng_state = torch.get_rng_state().clone()
        _need(c['model_calls_started']-counts_before['model_calls_started'] == calls
              and c['model_calls_returned']-counts_before['model_calls_returned'] == calls,
              'Whole phase model-call accounting mismatch')
        if training:
            _need(c['adam_returned']-counts_before['adam_returned'] == len(blocks)
                  and c['optimized_targets']-counts_before['optimized_targets'] == targets,
                  'Whole epoch optimizer/target accounting mismatch')
        else:
            expected_keys = {(r.learner_id, r.query.source_row, r.global_rank)
                             for group in groups for r in group['records'] if r.eligible}
            _need(set(rows) == expected_keys
                  and c['scored_targets']-counts_before['scored_targets'] == targets,
                  'Whole raw-prediction population mismatch')
        status, reason = 'complete', 'epoch_complete' if training else 'raw_prediction_complete'
    except _Limit as caught:
        reason = str(caught)
    except Exception as caught:
        status, reason, error = 'failed', str(caught), caught
    except BaseException:
        # Giữ original cancellation; BN/RNG/Adam có thể đã đổi trước interrupt.
        progress.poisoned = True
        raise
    finally:
        for module, mode in modes:
            try:
                module.training = mode
            except Exception as caught:
                cleanup_errors.append(str(caught))
    after, normalization_after = None, None
    try:
        after = state_digest(model)
        normalization_after = model.normalization_counts
        _need(source_identity() == sources, 'Source drift after compute')
        view.assert_integrity()
        _need(tuple((name, id(p), p.requires_grad) for name, p in model.named_parameters())
              == progress.parameter_identity, 'Registered parameter identity changed')
        model._bound(model.binding, model.graph_sha256)
        _need(training or before == after, 'Raw prediction mutated model/BN/counters')
        _need(not cleanup_errors, 'Module mode restoration failed')
        _check(budget, resources)
    except _Limit as caught:
        if error is None:
            status, reason = 'bounded', str(caught)
    except Exception as caught:
        if error is None:
            status, reason, error = 'failed', str(caught), caught
    except BaseException:
        progress.poisoned = True
        raise
    if status != 'complete':
        progress.poisoned = True
    records = [r for g in groups for r in g['records']]
    predictions = tuple(dict(learner_id=r.learner_id, query=asdict(r.query), global_rank=r.global_rank,
        origin_role=r.origin_role, history_sha256=r.history_sha256, history_hash_scheme=r.history_hash_scheme,
        support_reason=r.support_reason, probability=rows.get((r.learner_id, r.query.source_row, r.global_rank)),
        prediction_status=('unsupported' if not r.eligible else 'scored' if
            (r.learner_id, r.query.source_row, r.global_rank) in rows else 'unprocessed')) for r in records) if not training else ()
    optimized = progress.counters['optimized_targets']-counts_before['optimized_targets']
    loss_sum = math.fsum(loss_values) if loss_values else None
    result = dict(status=status, stop_reason=reason, complete=status == 'complete', role=ROLE,
        model_binding_sha256=model_identity, spec=asdict(spec), budget_sha256=progress.budget_sha256,
        fitted_research_model=False, resume_supported=False, rollback=False, counters=dict(progress.counters),
        counters_before=counts_before, pending_batch_keys=pending, cleanup_errors=cleanup_errors,
        resources=resources, model_state_before=before, model_state_after=after,
        normalization_before=normalization_before, normalization_after=normalization_after,
        loss_sum=loss_sum, mean_loss=loss_sum/optimized if optimized and loss_sum is not None else None,
        predictions=predictions, raw_predictions_sha256=identity_hash(predictions) if not training else None,
        view_sha256=view_identity, source_sha256=sources, elapsed_seconds=_now()-budget.started_at,
        original_module_modes_restored=all(module.training == mode for module, mode in modes),
        owned_rng_sha256=hashlib.sha256(progress.rng_state.contiguous().numpy().tobytes()).hexdigest(),
        unreturned_sequence_work=('UNKNOWN_WITHIN_PENDING_BATCH' if
            progress.counters['sequence_started'] != progress.counters['sequence_returned'] else None),
        optimized_target_semantics='Confirmed returned Adam calls; unreturned pending batch may be partially updated')
    if error is None and result['elapsed_seconds'] >= budget.max_seconds:
        result.update(status='bounded', complete=False, stop_reason='deadline_after_result')
        progress.poisoned = True
    if error is not None:
        raise GKTResearchExecutionError(reason, result) from error
    if result['complete'] and training:
        progress.counters['complete_train_epochs'] += 1
        result['counters'] = dict(progress.counters)
    return result


def train_research_epoch(model, view, *, optimizer, spec, budget, progress):
    return _run(model, view, optimizer=optimizer, spec=spec, budget=budget, progress=progress, training=True)


def predict_research_gkt(model, view, *, spec, budget, progress):
    return _run(model, view, optimizer=None, spec=spec, budget=budget, progress=progress, training=False)


def score_raw_predictions(view, result):
    _need(type(view) is data.GKTResearchView and result['complete'] and result['status'] == 'complete'
          and result['view_sha256'] == view.identity
          and result['raw_predictions_sha256'] == identity_hash(result['predictions']),
          'Complete unchanged raw predictions required before labels')
    truth = data.gkt_research_scoring_targets(view)
    rows = result['predictions']
    _need(len(rows) == len(truth), 'Full scoring population required')
    losses, unsupported = [], {}
    for row, target in zip(rows, truth):
        _need((row['learner_id'], row['query'], row['global_rank'], row['origin_role'],
               row['history_sha256'], row['history_hash_scheme']) ==
              (target.learner_id, asdict(target.query), target.global_rank, target.origin_role,
               target.history_sha256, target.history_hash_scheme), 'Exact scoring key/query/history/role join required')
        _need(row['support_reason'] in ('cold_query_only', 'known_history', 'oov_item', 'unsupported_history')
              and (row['prediction_status'] == 'scored') ==
                  (row['support_reason'] in ('cold_query_only', 'known_history'))
              and target.trained_item == (row['support_reason'] != 'oov_item'),
              'Scored eligibility differs from item support or unsupported suffix')
        if row['prediction_status'] == 'scored':
            losses.append(binary_row_log_loss(row['probability'], target.correct))
        else:
            _need(row['prediction_status'] == 'unsupported' and row['probability'] is None,
                  'Incomplete prediction cannot be scored')
            reason = row['support_reason']
            unsupported[reason] = unsupported.get(reason, 0)+1
    return dict(full_targets=len(rows), eligible_targets=len(losses), unsupported_reasons=unsupported,
                raw_response_log_loss=math.fsum(losses)/len(losses) if losses else None)
