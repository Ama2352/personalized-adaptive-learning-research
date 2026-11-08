"""Bounded CPU synthetic SAKT training; không selection/refit/research fitted backend."""

from dataclasses import asdict, dataclass
import hashlib
import math
from pathlib import Path
import time

import torch
from torch.nn import functional as F

from .config import SAKTConfig
from .model import SAKTCore
from .tensors import collate_sequences
from .training_data import ENGINEERING_ROLE, SAKTTrainingData, identity_hash


@dataclass(frozen=True)
class SAKTTrainingConfig:
    optimizer: str
    lr: float
    betas: tuple[float, float]
    eps: float
    weight_decay: float
    max_grad_norm: float
    epochs: int
    batch_size: int
    shuffle_seed: int
    objective: str
    max_steps: int
    max_targets: int
    max_seconds: float
    device: str
    precision: str

    def __post_init__(self):
        if (self.optimizer != 'adam' or self.objective != 'mean_bce_on_eligible_targets'
                or self.device != 'cpu' or self.precision != 'float32'):
            raise ValueError('explicit supported optimizer/objective/CPU FP32 required')
        for name in ('lr', 'eps', 'max_grad_norm', 'max_seconds', 'weight_decay'):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError('finite optimizer/budget numbers required')
        if min(self.lr, self.eps, self.max_grad_norm, self.max_seconds) <= 0 or self.weight_decay < 0 or self.max_seconds > 120:
            raise ValueError('invalid optimizer or engineering time budget')
        if (type(self.betas) is not tuple or len(self.betas) != 2
                or any(type(x) not in (int, float) or not math.isfinite(x) or not 0 <= x < 1 for x in self.betas)):
            raise ValueError('explicit valid Adam betas required')
        for name in ('epochs', 'batch_size', 'max_steps', 'max_targets'):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError('positive integer training geometry/budget required')
        if type(self.shuffle_seed) is not int or self.shuffle_seed < 0 or self.max_steps > 32:
            raise ValueError('explicit seed and at most32 engineering optimizer steps required')
        if self.batch_size > 32 or self.epochs > 32:
            raise ValueError('engineering batch_size/epochs ceiling is32, not a research default')


def validate_engineering_geometry(model_config, training_config, *, context, vocabulary_size):
    """Fail trước allocation; chỉ ceiling kỹ thuật, không chọn hyperparameters."""
    if (type(model_config) is not SAKTConfig or type(training_config) is not SAKTTrainingConfig
            or model_config.num_items != vocabulary_size or not 1 <= vocabulary_size <= 256
            or model_config.d_model > 64 or model_config.num_heads > 8 or model_config.head_dim > 64
            or model_config.max_length > 257 or model_config.max_length < context + 1):
        raise ValueError('synthetic engineering geometry ceiling or vocabulary/context mismatch')


def source_identity():
    root = Path(__file__).resolve().parents[3]
    names = [f'src/knowledge_tracing/sakt/{name}' for name in
             ('config.py', 'model.py', 'tensors.py', 'training_data.py', 'training.py', 'training_checkpoint.py')]
    names += ['src/knowledge_tracing/akt/windows.py', 'src/knowledge_tracing/akt/encoding.py',
              'src/knowledge_tracing/akt/types.py', 'src/knowledge_tracing/shared_kt.py']
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names}


def state_digest(model):
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        digest.update(name.encode()); digest.update(str((value.dtype, tuple(value.shape))).encode())
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def _validate_model(model, data):
    data.assert_integrity()
    if (type(model) is not SAKTCore or model.config.num_items != len(data.vocabulary.values)
            or model.config.max_length < data.recipe.context + 1
            or any(p.device.type != 'cpu' or p.dtype != torch.float32 for p in model.parameters())):
        raise ValueError('model/data/geometry must match CPU FP32 training identity')


def collate_target_batch(records, *, model_config, recipe):
    """Forward inputs không chứa targets; loss mask chỉ terminal query, không context."""
    if not records or any(not record.eligible or record.inputs is None for record in records):
        raise ValueError('only eligible targets may enter model collation')
    batch = collate_sequences([x.inputs for x in records], num_items=model_config.num_items,
                              max_length=model_config.max_length, padding_side=recipe.padding_side, device='cpu')
    labels = torch.zeros_like(batch.item_ids, dtype=torch.float32)
    mask = torch.zeros_like(batch.valid_mask)
    for row, record in enumerate(records):
        position = len(record.inputs.item_ids) - 1 if recipe.padding_side == 'right' else batch.item_ids.shape[1] - 1
        labels[row, position] = record.target
        mask[row, position] = True
    return batch, labels, mask & batch.valid_mask


def masked_bce(logits, labels, mask):
    if logits.shape != labels.shape or logits.shape != mask.shape or mask.dtype != torch.bool or not mask.any():
        raise ValueError('nonempty eligible target mask required')
    selected, targets = logits[mask], labels[mask]
    if not torch.isfinite(selected).all() or not torch.isfinite(targets).all() or torch.any((targets != 0) & (targets != 1)):
        raise ValueError('nonfinite logits or invalid selected labels')
    total = F.binary_cross_entropy_with_logits(selected, targets, reduction='sum')
    return total, int(mask.sum())


def population_ledger(records, optimized=()):
    optimized = tuple(optimized)
    if len(optimized) != len(set(optimized)):
        raise ValueError('duplicate optimized target in epoch')
    eligible = {x.source_row for x in records if x.eligible}
    if not set(optimized) <= eligible:
        raise ValueError('optimized target outside eligible population')
    return {'expected_targets': len(records), 'eligible_targets': len(eligible),
            'oov_targets': sum(x.reason == 'oov_item' for x in records),
            'cold_excluded_targets': sum(x.reason == 'cold_unsupported' for x in records),
            'optimized_targets': len(optimized), 'optimized_source_rows': list(optimized),
            'unprocessed_eligible_targets': len(eligible - set(optimized))}


def evaluate_sakt(model, data: SAKTTrainingData, *, batch_size: int, deadline: float | None = None):
    _validate_model(model, data)
    if type(batch_size) is not int or batch_size < 1:
        raise ValueError('positive evaluation batch size required')
    was_training, before = model.training, state_digest(model)
    records = data.validation
    active = [x for x in records if x.eligible]
    probabilities = {}
    total, count = 0., 0
    try:
        model.eval()
        with torch.inference_mode():
            for offset in range(0, len(active), batch_size):
                if deadline is not None and time.perf_counter() >= deadline:
                    raise TimeoutError('synthetic validation deadline reached')
                block = active[offset:offset + batch_size]
                batch, labels, mask = collate_target_batch(block, model_config=model.config, recipe=data.recipe)
                output = model(batch)
                loss, n = masked_bce(output.logits, labels, mask)
                total += float(loss); count += n
                for record, value in zip(block, output.probabilities[mask].tolist()):
                    probabilities[record.source_row] = float(value)
                if deadline is not None and time.perf_counter() >= deadline:
                    raise TimeoutError('synthetic validation deadline reached')
    finally:
        model.train(was_training)
    data.assert_integrity()
    if state_digest(model) != before:
        raise ValueError('validation changed model weights')
    if deadline is not None and time.perf_counter() >= deadline:
        raise TimeoutError('synthetic validation deadline reached')
    rows = tuple({'learner_id': x.learner_id, 'source_row': x.source_row, 'reason': x.reason,
                  'probability': probabilities.get(x.source_row), 'history_available': x.history_available,
                  'history_used': x.history_used, 'context_reset': x.context_reset} for x in records)
    ledger = population_ledger(records)
    ledger.pop('optimized_targets'); ledger.pop('optimized_source_rows')
    ledger.update(evaluated_targets=count, evaluated_source_rows=list(probabilities),
                  unprocessed_eligible_targets=ledger['eligible_targets'] - count)
    return {'role': 'synthetic_evaluation_no_fit_attestation', 'loss_sum': total, 'eligible_targets': count,
            'mean_loss': total / count if count else None,
            'population': ledger, 'predictions': rows}


@dataclass(frozen=True)
class SAKTTrainingResult:
    model: SAKTCore
    model_config: SAKTConfig
    training_config: SAKTTrainingConfig
    data_identity: dict
    source_sha256: dict
    status: str
    stop_reason: str
    completed_epochs: int
    optimizer_steps: int
    optimized_targets: int
    history: tuple[dict, ...]
    model_state_sha256: str
    role: str


def train_synthetic_sakt(data, *, model_config: SAKTConfig, training_config: SAKTTrainingConfig):
    """Không chọn best epoch, không external data loader, không optimizer/RNG resume."""
    if type(data) is not SAKTTrainingData or type(model_config) is not SAKTConfig or type(training_config) is not SAKTTrainingConfig:
        raise ValueError('typed explicit training inputs/configs required')
    data.assert_integrity()
    validate_engineering_geometry(model_config, training_config, context=data.recipe.context,
                                  vocabulary_size=len(data.vocabulary.values))
    config = training_config
    source = source_identity()
    start = time.perf_counter()
    history, steps, optimized, completed = [], 0, 0, 0
    reason, status = 'epochs_complete', 'complete'
    # Preserve caller Torch RNG; shuffle dùng Generator local. Không đổi global Python/NumPy RNG.
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(config.shuffle_seed)
        with torch.device('cpu'):
            model = SAKTCore(model_config).to(device='cpu', dtype=torch.float32)
        _validate_model(model, data)
        optimizer = torch.optim.Adam(model.parameters(), lr=config.lr, betas=config.betas,
                                     eps=config.eps, weight_decay=config.weight_decay)
        active = [x for x in data.train if x.eligible]
        for epoch in range(1, config.epochs + 1):
            data.assert_integrity()
            generator = torch.Generator(device='cpu').manual_seed(config.shuffle_seed + epoch)
            order = torch.randperm(len(active), generator=generator, device='cpu').tolist()
            processed, loss_sum = [], 0.
            model.train()
            for offset in range(0, len(order), config.batch_size):
                block = [active[i] for i in order[offset:offset + config.batch_size]]
                if steps >= config.max_steps: reason = 'max_steps'
                elif optimized + len(block) > config.max_targets: reason = 'max_targets'
                elif time.perf_counter() - start >= config.max_seconds: reason = 'max_seconds'
                else: reason = 'epoch_in_progress'
                if reason != 'epoch_in_progress':
                    status = 'bounded'; break
                batch, labels, mask = collate_target_batch(block, model_config=model_config, recipe=data.recipe)
                optimizer.zero_grad(set_to_none=True)
                output = model(batch)
                total, n = masked_bce(output.logits, labels, mask)
                (total / n).backward()
                norm = torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm, error_if_nonfinite=True)
                if not torch.isfinite(norm): raise ValueError('nonfinite training gradients')
                if time.perf_counter() - start >= config.max_seconds:
                    reason, status = 'max_seconds', 'bounded'; break
                optimizer.step()
                if any(not torch.isfinite(p).all() for p in model.parameters()):
                    raise ValueError('nonfinite trained model state')
                steps += 1; optimized += n; loss_sum += float(total.detach())
                processed.extend(x.source_row for x in block)
                if time.perf_counter() - start >= config.max_seconds:
                    reason, status = 'max_seconds_after_optimizer', 'bounded'; break
            training_complete = len(processed) == len(active)
            validation = None
            if training_complete and status != 'bounded':
                try:
                    validation = evaluate_sakt(model, data, batch_size=config.batch_size,
                                               deadline=start + config.max_seconds)
                except TimeoutError:
                    reason, status = 'max_seconds_validation', 'bounded'
            complete = training_complete and validation is not None and status != 'bounded'
            history.append({'epoch': epoch, 'complete_epoch': complete, 'loss_sum': loss_sum,
                            'training_complete': training_complete,
                            'mean_loss': loss_sum / len(processed) if processed else None,
                            'population': population_ledger(data.train, processed), 'validation': validation})
            if complete:
                completed += 1
            if status == 'bounded': break
        model.eval()
    if status == 'complete': reason = 'epochs_complete'
    data.assert_integrity()
    if source_identity() != source: raise ValueError('training source changed during execution')
    if time.perf_counter() - start >= config.max_seconds and status == 'complete':
        reason, status = 'max_seconds_final_stage', 'bounded'
    return SAKTTrainingResult(model, model_config, config, data.identity, source, status, reason,
                               completed, steps, optimized, tuple(history), state_digest(model),
                               ENGINEERING_ROLE if steps else 'synthetic_untrained_engineering_attempt')
