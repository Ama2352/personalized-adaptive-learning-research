"""Một epoch/prediction SAKT role-aware; không orchestration/fitted authority.

Caller tạo model/optimizer và freeze mọi giá trị numerical trước call. Budget
cooperative tính từ đầu call, không gồm model construction trước đó; owned outer
controller vẫn phải giới hạn RAM/process/time và cumulative work qua các calls.
Không dùng synthetic trainer/caps/checkpoint hoặc gán research-fitted role.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import time

import torch

from knowledge_tracing.simulator_bridge import identity_hash
from .model import SAKTCore
from .research_data import (SAKTResearchInput, SAKTResearchTrainingTarget, SAKTResearchView,
                            iter_sakt_research_inputs, sakt_research_scoring_targets,
                            source_identity as data_source_identity)
from .tensors import collate_sequences
from .training import masked_bce, state_digest


@dataclass(frozen=True)
class SAKTResearchSpec:
    batch_size: int
    max_grad_norm: float
    epoch_seed: int
    order: str
    device: str
    precision: str
    objective: str

    def __post_init__(self):
        if (type(self.batch_size) is not int or self.batch_size < 1
                or type(self.epoch_seed) is not int or not 0 <= self.epoch_seed < 2**63
                or type(self.max_grad_norm) not in (int, float) or not math.isfinite(self.max_grad_norm)
                or self.max_grad_norm <= 0 or self.order not in ('in_order', 'seeded_permutation')
                or self.device != 'cpu' or self.precision != 'float32'
                or self.objective != 'mean_bce_on_eligible_targets'):
            raise ValueError('explicit supported CPU FP32 epoch/order/objective/geometry required')


@dataclass(frozen=True)
class SAKTResearchBudget:
    max_seconds: float
    max_seen_targets: int
    max_processed_targets: int
    max_optimizer_steps: int

    def __post_init__(self):
        if (type(self.max_seconds) not in (int, float) or not math.isfinite(self.max_seconds)
                or self.max_seconds <= 0
                or any(type(getattr(self, name)) is not int or getattr(self, name) < 0 for name in
                       ('max_seen_targets', 'max_processed_targets', 'max_optimizer_steps'))):
            raise ValueError('explicit finite time and nonnegative target/step budgets required')


class SAKTResearchExecutionError(RuntimeError):
    """Failure kèm partial ledger; không rollback optimizer đã bắt đầu."""
    def __init__(self, message, result):
        super().__init__(message)
        self.result = result


def source_identity():
    root = Path(__file__).resolve().parents[3]
    sources = dict(data_source_identity())
    for name in ('sakt/research_training.py', 'sakt/model.py', 'sakt/tensors.py', 'sakt/config.py', 'sakt/training.py'):
        sources[name] = hashlib.sha256((root/'src/knowledge_tracing'/name).read_bytes()).hexdigest()
    return tuple(sorted(sources.items()))


def _json(value):
    return json.loads(json.dumps(value, sort_keys=True, allow_nan=False))


def _optimizer_identity(model, optimizer):
    if not isinstance(optimizer, torch.optim.Optimizer):
        raise ValueError('caller must supply an optimizer')
    owned = {id(parameter): name for name, parameter in model.named_parameters()}
    actual = [parameter for group in optimizer.param_groups for parameter in group['params']]
    ids = [id(parameter) for parameter in actual]
    if len(ids) != len(set(ids)) or set(ids) != set(owned):
        raise ValueError('optimizer must own every model parameter exactly once and no foreign parameter')
    if any(id(parameter) not in owned for parameter in optimizer.state):
        raise ValueError('optimizer state contains foreign parameter')
    return _json(dict(optimizer_class=type(optimizer).__module__+'.'+type(optimizer).__qualname__,
        optimizer_object_id=id(optimizer), defaults=optimizer.defaults,
        step_callable_id=id(getattr(optimizer.step, '__func__', optimizer.step)),
        zero_grad_callable_id=id(getattr(optimizer.zero_grad, '__func__', optimizer.zero_grad)),
        groups=[dict(parameters=[owned[id(p)] for p in group['params']],
            parameter_object_ids=[id(p) for p in group['params']],
            settings={key: value for key, value in group.items() if key != 'params'}) for group in optimizer.param_groups]))


def _binding(model, view, spec, optimizer, budget):
    view_id = view.identity
    vocabulary = view.encoding.exercise_encoding().vocabulary.values
    if (type(model) is not SAKTCore or model.config.num_items != len(vocabulary)
            or model.config.max_length < view.recipe.context+1
            or any(p.device.type != 'cpu' or p.dtype != torch.float32 or not torch.isfinite(p).all()
                   for p in model.parameters())):
        raise ValueError('model config/vocabulary/geometry/finite CPU FP32 binding mismatch')
    return _json(dict(model='sakt', model_config=asdict(model.config), view_sha256=view_id,
        parameter_identity=[(name, id(parameter), parameter.requires_grad) for name, parameter in model.named_parameters()],
        phase_scope=view.phase.scope, encoding_sha256=view.encoding.identity,
        vocabulary_sha256=identity_hash(list(vocabulary)), recipe=asdict(view.recipe),
        spec=asdict(spec), budget=asdict(budget), sources_sha256=source_identity(),
        optimizer=None if optimizer is None else _optimizer_identity(model, optimizer)))


def _record(entry, training):
    expected = SAKTResearchTrainingTarget if training else SAKTResearchInput
    if type(entry) is not expected:
        raise ValueError('unexpected research iterator record')
    return entry.inputs if training else entry


def _key(record):
    return (record.learner_id, record.query.source_row, record.global_rank)


def _collect(view, training, spec, budget, started, ledger):
    entries = []
    stream = iter_sakt_research_inputs(view, training=training)
    seen = set()
    try:
        while ledger['seen_targets'] < ledger['expected_targets']:
            if time.perf_counter()-started >= budget.max_seconds:
                return entries, 'max_seconds_during_inputs'
            if ledger['seen_targets'] >= budget.max_seen_targets:
                return entries, 'max_seen_targets'
            try:
                entry = next(stream)
            except StopIteration as error:
                raise ValueError('research iterator ended before full target population') from error
            record = _record(entry, training)
            if _key(record) in seen:
                raise ValueError('duplicate research target')
            seen.add(_key(record))
            entries.append(entry)
            ledger['seen_targets'] += 1
            ledger['seen_source_rows'].append(record.query.source_row)
            if record.eligible:
                ledger['eligible_targets_seen'] += 1
            else:
                ledger['unsupported_targets_seen'] += 1
                reasons = ledger['unsupported_reasons']
                reasons[record.support_reason] = reasons.get(record.support_reason, 0)+1
        try:
            next(stream)
        except StopIteration:
            ledger['input_population_complete'] = True
            ledger['expected_eligible_targets'] = ledger['eligible_targets_seen']
        else:
            raise ValueError('research iterator yielded extra target')
    finally:
        stream.close()
    return entries, None


def _batch(entries, view, model, training):
    records = [_record(entry, training) for entry in entries]
    batch = collate_sequences([record.inputs for record in records], num_items=model.config.num_items,
        max_length=model.config.max_length, padding_side=view.recipe.padding_side, device='cpu')
    positions = [len(record.inputs.item_ids)-1 if view.recipe.padding_side == 'right'
                 else batch.item_ids.shape[1]-1 for record in records]
    mask = torch.zeros_like(batch.valid_mask)
    labels = torch.zeros_like(batch.item_ids, dtype=torch.float32) if training else None
    for row, (entry, position) in enumerate(zip(entries, positions)):
        mask[row, position] = True
        if training:
            labels[row, position] = entry.target
    return batch, labels, mask & batch.valid_mask


def _run(model, view, *, optimizer, spec, budget, training):
    started = time.perf_counter()
    if type(view) is not SAKTResearchView or type(spec) is not SAKTResearchSpec or type(budget) is not SAKTResearchBudget:
        raise ValueError('typed research view/spec/budget required')
    if training and view.phase.scope not in ('select_train80', 'refit_union90'):
        raise ValueError('prediction-only selection/calibration phase cannot train')
    if training and torch.is_inference_mode_enabled():
        raise ValueError('training under caller inference_mode is unsupported')
    if training and any(not p.requires_grad for p in model.parameters()):
        raise ValueError('training optimizer must cover trainable model parameters')
    if training:
        _optimizer_identity(model, optimizer)
    binding = _binding(model, view, spec, optimizer, budget)
    before = state_digest(model)
    modes = [(module, module.training) for module in model.modules()]
    ledger = dict(expected_targets=sum(s.audit['audit']['targets'] for s in view.phase.shards),
        seen_targets=0, eligible_targets_seen=0, unsupported_targets_seen=0, unsupported_reasons={},
        input_population_complete=False, expected_eligible_targets=None, processed_targets=0,
        optimized_targets=0, scored_targets=0, optimizer_steps_started=0, optimizer_steps_body_returned=0,
        seen_source_rows=[], processing_order_source_rows=[], processed_source_rows=[],
        possibly_updated_source_rows=[], rollback=False)
    entries, outputs, truth = [], {}, ()
    loss_sum = 0.
    status, stop_reason, error = 'bounded', 'not_started', None
    try:
        entries, stop_reason = _collect(view, training, spec, budget, started, ledger)
        if stop_reason is None:
            active = [entry for entry in entries if _record(entry, training).eligible]
            if not active and training:
                raise ValueError('no eligible target under explicit support/cold policy')
            with torch.random.fork_rng(devices=[]), torch.device('cpu'), torch.set_grad_enabled(training):
                if training:
                    torch.random.default_generator.manual_seed(spec.epoch_seed)
                    if spec.order == 'seeded_permutation':
                        generator = torch.Generator(device='cpu').manual_seed(spec.epoch_seed)
                        active = [active[i] for i in torch.randperm(len(active), generator=generator, device='cpu').tolist()]
                ledger['processing_order_source_rows'] = [_record(entry, training).query.source_row for entry in active]
                model.train(training)
                for offset in range(0, len(active), spec.batch_size):
                    block = active[offset:offset+spec.batch_size]
                    if time.perf_counter()-started >= budget.max_seconds:
                        stop_reason = 'max_seconds_before_batch'; break
                    if ledger['processed_targets']+len(block) > budget.max_processed_targets:
                        stop_reason = 'max_processed_targets'; break
                    if training and ledger['optimizer_steps_started'] >= budget.max_optimizer_steps:
                        stop_reason = 'max_optimizer_steps'; break
                    batch, labels, mask = _batch(block, view, model, training)
                    if training:
                        if _optimizer_identity(model, optimizer) != binding['optimizer']:
                            raise ValueError('optimizer identity changed')
                        optimizer.zero_grad(set_to_none=True)
                        output = model(batch)
                        total, count = masked_bce(output.logits, labels, mask)
                        if count != len(block):
                            raise ValueError('terminal loss mask denominator mismatch')
                        batch_loss = float(total.detach())
                        (total/count).backward()
                        norm = torch.nn.utils.clip_grad_norm_(model.parameters(), spec.max_grad_norm, error_if_nonfinite=True)
                        if not torch.isfinite(norm):
                            raise ValueError('nonfinite gradient norm')
                        if time.perf_counter()-started >= budget.max_seconds:
                            stop_reason = 'max_seconds_before_optimizer'; break
                        ledger['possibly_updated_source_rows'] = [entry.inputs.query.source_row for entry in block]
                        ledger['optimizer_steps_started'] += 1
                        optimizer.step()
                        ledger['optimizer_steps_body_returned'] += 1
                        loss_sum += batch_loss
                        ledger['optimized_targets'] += count
                    else:
                        with torch.inference_mode():
                            output = model(batch)
                            values = output.probabilities[mask].tolist()
                        if len(values) != len(block) or any(not math.isfinite(p) or not 0 <= p <= 1 for p in values):
                            raise ValueError('invalid full-population prediction')
                        for record, probability in zip(block, values):
                            outputs[_key(record)] = float(probability)
                        ledger['scored_targets'] += len(block)
                    ledger['processed_targets'] += len(block)
                    ledger['processed_source_rows'].extend(_record(entry, training).query.source_row for entry in block)
                    if training:
                        ledger['possibly_updated_source_rows'] = []
                    if training and _optimizer_identity(model, optimizer) != binding['optimizer']:
                        raise ValueError('optimizer identity changed after step')
                    if time.perf_counter()-started >= budget.max_seconds:
                        stop_reason = 'max_seconds_after_batch'; break
                else:
                    status, stop_reason = 'complete', 'epoch_complete' if training else 'prediction_complete'
        if (not training and ledger['input_population_complete']
                and time.perf_counter()-started < budget.max_seconds):
            # Only after all attempted forwards: separate full truth sidecar.
            truth = sakt_research_scoring_targets(view)
    except Exception as caught:
        error = caught
    finally:
        for module, mode in modes:
            module.training = mode
    after = None
    try:
        after = state_digest(model)
        if _binding(model, view, spec, optimizer, budget) != binding:
            raise ValueError('research source/config/phase/vocabulary/optimizer binding changed')
        if not training and after != before:
            raise ValueError('prediction changed model weights')
    except Exception as caught:
        if error is None:
            error = caught
    if error is not None:
        status, stop_reason = 'failed', type(error).__name__+': '+str(error)
    elif time.perf_counter()-started >= budget.max_seconds:
        status, stop_reason = 'bounded', 'max_seconds_finalization'
    complete = (status == 'complete' and ledger['input_population_complete']
        and ledger['processed_targets'] == ledger['expected_eligible_targets']
        and ledger['optimizer_steps_started'] == ledger['optimizer_steps_body_returned'])
    if status == 'complete' and not complete:
        error = ValueError('incomplete computation cannot be accepted as complete')
        status, stop_reason = 'failed', str(error)
    ledger.update(complete=complete, unseen_targets=ledger['expected_targets']-ledger['seen_targets'],
        unprocessed_seen_eligible_targets=ledger['eligible_targets_seen']-ledger['processed_targets'])
    rows = tuple(dict(learner_id=record.learner_id, item_id=record.query.item_id,
        timestamp=record.query.timestamp, source_row=record.query.source_row, global_rank=record.global_rank,
        history_sha256=record.history_sha256, history_hash_scheme=record.history_hash_scheme,
        origin_role=record.origin_role, phase_sha256=record.phase_sha256, encoding_sha256=record.encoding_sha256,
        history_available=record.history_available, history_used=record.history_used, context_reset=record.context_reset,
        support_reason=record.support_reason, probability=outputs.get(_key(record)),
        prediction_status='unsupported' if not record.eligible else 'scored' if _key(record) in outputs else 'unprocessed')
        for record in entries) if not training else ()
    result = dict(status=status, stop_reason=stop_reason, ledger=ledger, binding=binding, budget=asdict(budget),
        model_state_before=before, model_state_after=after, weights_changed=before != after,
        loss_sum=loss_sum if training else None,
        mean_loss=loss_sum/ledger['optimized_targets'] if training and ledger['optimized_targets'] else None,
        predictions=rows, truth_sidecar=truth,
        truth_sidecar_complete=not training and len(truth) == ledger['expected_targets'],
        elapsed_seconds=time.perf_counter()-started,
        role='research_computation_only_no_selected_fit_attestation', resume_supported=False, fitted_research_model=False)
    # Late result materialization counts as work; no success after the deadline.
    result['elapsed_seconds'] = time.perf_counter()-started
    if error is None and result['elapsed_seconds'] >= budget.max_seconds:
        result.update(status='bounded', stop_reason='max_seconds_after_result')
        ledger['complete'] = False
    if error is not None:
        raise SAKTResearchExecutionError(stop_reason, result) from error
    return result


def train_research_epoch(model, view, *, optimizer, spec, budget):
    """Một epoch exact eligible population; thiếu budget giữ partial, không fit role."""
    return _run(model, view, optimizer=optimizer, spec=spec, budget=budget, training=True)


def predict_research_sakt(model, view, *, spec, budget):
    """Frozen raw predictions; không temperature/selector, labels ở truth_sidecar."""
    return _run(model, view, optimizer=None, spec=spec, budget=budget, training=False)
