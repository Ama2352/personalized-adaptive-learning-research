"""Một train-batch GKT engineering explicit; không epoch/trainer nghiên cứu/resume.

Identity là kiểm tra nhất quán cooperative, không chứng nhận nguồn synthetic,
train-only graph hoặc lịch sử state do caller khai báo.
"""
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import math
from pathlib import Path
import time

import torch
from torch.nn import functional as F

from .config import GKTBinding
from .recurrent import GKTRecurrentState, GKTStaticRecurrentCandidate, RECIPE_ID

TRAIN_ROLE = 'synthetic_engineering_train_only'
WEIGHT_ROLE = 'synthetic_trained_engineering_only'


def source_identity():
    root = Path(__file__).resolve().parents[3]
    names = [f'src/knowledge_tracing/gkt/{n}' for n in ('config.py', 'core.py', 'recurrent.py', 'training.py')]
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names}


def _sha(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def _digest(metadata, tensors):
    h = hashlib.sha256(json.dumps(metadata, sort_keys=True, allow_nan=False, separators=(',', ':')).encode())
    for name, value in tensors:
        if not isinstance(value, torch.Tensor) or value.device.type != 'cpu' or value.layout != torch.strided:
            raise ValueError('CPU strided tensor required before digest')
        h.update(name.encode()); h.update(str((value.dtype, tuple(value.shape))).encode())
        h.update(value.detach().contiguous().numpy().tobytes())
    return h.hexdigest()


def model_digest(model):
    return _digest({}, sorted(model.state_dict().items()))


@dataclass(frozen=True)
class GKTTrainingSettings:
    optimizer: str
    lr: float
    betas: tuple[float, float]
    eps: float
    weight_decay: float
    max_grad_norm: float
    objective: str
    precision: str

    def __post_init__(self):
        if self.optimizer != 'adam' or self.objective != 'mean_bce_on_explicit_loss_mask' or self.precision not in ('float32', 'float64'):
            raise ValueError('explicit Adam/objective/CPU precision required')
        for name in ('lr', 'eps', 'weight_decay', 'max_grad_norm'):
            x = getattr(self, name)
            if type(x) not in (int, float) or not math.isfinite(x) or x < 0 or (name != 'weight_decay' and x == 0):
                raise ValueError('finite positive optimizer settings required')
        if (type(self.betas) is not tuple or len(self.betas) != 2
                or any(type(x) not in (int, float) or not math.isfinite(x) or not 0 <= x < 1 for x in self.betas)):
            raise ValueError('explicit finite Adam betas required')


@dataclass(frozen=True)
class GKTStepBudget:
    max_steps: int
    max_targets: int
    max_seconds: float
    steps_used: int
    targets_used: int
    started_at: float

    def __post_init__(self):
        for name in ('max_steps', 'max_targets', 'steps_used', 'targets_used'):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError('nonnegative integer cumulative budget required')
        if not 1 <= self.max_steps <= 8 or not 1 <= self.max_targets <= 192:
            raise ValueError('tiny engineering cumulative caps required')
        if (type(self.max_seconds) not in (int, float) or not math.isfinite(self.max_seconds)
                or not 0 < self.max_seconds <= 60 or type(self.started_at) not in (int, float)
                or not math.isfinite(self.started_at) or self.steps_used > self.max_steps
                or self.targets_used > self.max_targets):
            raise ValueError('finite bounded clock/counters required')


@dataclass(frozen=True)
class GKTTrainBatch:
    query_ids: torch.Tensor
    responses: torch.Tensor
    event_valid_mask: torch.Tensor
    loss_mask: torch.Tensor
    initial_state: GKTRecurrentState
    learner_ids: tuple[str, ...]
    source_rows: torch.Tensor
    global_ranks: torch.Tensor
    binding: GKTBinding
    graph_sha256: str
    recipe_sha256: str
    initial_state_model_sha256: str
    role: str
    synthetic_only: bool
    source_sha256: dict
    content_sha256: str


def _batch_digest(batch):
    if type(batch.initial_state) is not GKTRecurrentState or type(batch.binding) is not GKTBinding:
        raise ValueError('typed caller-owned state/binding required')
    state = batch.initial_state
    ids = batch.query_ids
    if (not isinstance(ids, torch.Tensor) or ids.ndim != 2 or not 1 <= ids.shape[0] <= 2
            or not 1 <= ids.shape[1] <= 12 or len(batch.binding.node_ids) > 4
            or not isinstance(state.values, torch.Tensor) or state.values.ndim != 3
            or state.values.shape[:2] != (ids.shape[0], len(batch.binding.node_ids))
            or not 1 <= state.values.shape[2] <= 8
            or not isinstance(state.history_counts, torch.Tensor) or state.history_counts.shape != (ids.shape[0],)):
        raise ValueError('toy batch/state shape bound before payload hashing')
    for name in ('responses', 'event_valid_mask', 'loss_mask', 'source_rows', 'global_ranks'):
        if not isinstance(getattr(batch, name), torch.Tensor) or getattr(batch, name).shape != ids.shape:
            raise ValueError('matching bounded batch shapes before payload hashing')
    metadata = {name: getattr(batch, name) for name in ('learner_ids', 'graph_sha256', 'recipe_sha256',
                'initial_state_model_sha256', 'role', 'synthetic_only', 'source_sha256')}
    metadata.update(binding=asdict(batch.binding), state_binding=asdict(state.binding),
                    state_graph=state.graph_sha256, state_recipe=state.recipe_sha256)
    tensors = [(name, getattr(batch, name)) for name in ('query_ids', 'responses', 'event_valid_mask',
               'loss_mask', 'source_rows', 'global_ranks')]
    return _digest(metadata, tensors + [('state_values', state.values), ('state_counts', state.history_counts)])


def bind_train_batch(**explicit_fields):
    """Seal bytes đã cấp; không tự fit vocabulary/graph, đổi mask hoặc dựng state."""
    batch = GKTTrainBatch(**explicit_fields, content_sha256='')
    return replace(batch, content_sha256=_batch_digest(batch))


def _optimizer_identity(optimizer, model, settings):
    if type(optimizer) is not torch.optim.Adam or len(optimizer.param_groups) != 1:
        raise ValueError('one explicit native Adam parameter group required')
    group = optimizer.param_groups[0]
    expected = list(model.parameters()); actual = group['params']
    if (not all(p.requires_grad for p in expected) or len(actual) != len(expected)
            or len({id(p) for p in actual}) != len(actual) or {id(p) for p in actual} != {id(p) for p in expected}):
        raise ValueError('optimizer must cover exactly registered trainable parameters once')
    for name in ('lr', 'betas', 'eps', 'weight_decay'):
        if group[name] != getattr(settings, name):
            raise ValueError('optimizer settings differ from explicit settings')
    if any(group.get(k) is not False for k in ('amsgrad', 'maximize', 'capturable', 'differentiable', 'foreach', 'fused')):
        raise ValueError('explicit ordinary CPU Adam flags required')
    names = {id(p): name for name, p in model.named_parameters()}
    metadata, tensors = [], []
    for p, state in optimizer.state.items():
        if id(p) not in names or type(state) is not dict:
            raise ValueError('foreign optimizer state')
        metadata.append((names[id(p)], sorted(state)))
        for key, value in sorted(state.items()):
            if (not isinstance(value, torch.Tensor) or value.device.type != 'cpu' or value.requires_grad
                    or value.grad_fn is not None
                    or not torch.isfinite(value).all()):
                raise ValueError('finite CPU Adam tensor state required')
            if key == 'step':
                if value.numel() != 1 or value.item() < 0 or value.item() != int(value.item()):
                    raise ValueError('nonnegative integral Adam step required')
            elif key not in ('exp_avg', 'exp_avg_sq') or value.shape != p.shape or value.dtype != p.dtype:
                raise ValueError('Adam state geometry/dtype mismatch')
            tensors.append((names[id(p)] + '.' + key, value))
        if state and set(state) != {'step', 'exp_avg', 'exp_avg_sq'}:
            raise ValueError('complete ordinary Adam state required')
    return _digest({'settings': asdict(settings), 'parameter_order': [names[id(p)] for p in actual],
                    'state_keys': metadata}, tensors)


def _validate(model, optimizer, batch, settings):
    if type(model) is not GKTStaticRecurrentCandidate or type(batch) is not GKTTrainBatch or type(settings) is not GKTTrainingSettings:
        raise ValueError('typed explicit GKT training inputs required')
    c = model.config
    if (c.num_nodes > 4 or max(c.state_dim, c.embedding_dim, c.message_dim, model.mlp_hidden_dim) > 8
            or model.recipe_id != RECIPE_ID or batch.role != TRAIN_ROLE or batch.synthetic_only is not True):
        raise ValueError('toy engineering geometry/train role required')
    if batch.source_sha256 != source_identity() or not _sha(batch.content_sha256) or _batch_digest(batch) != batch.content_sha256:
        raise ValueError('batch/source identity changed')
    if (batch.binding != model.binding or batch.graph_sha256 != model.graph_sha256
            or batch.recipe_sha256 != model.recipe_sha256 or batch.initial_state_model_sha256 != model_digest(model)):
        raise ValueError('model/binding/state parameter-version mismatch; recompute or reset state')
    batch_size = model._state(batch.initial_state, batch.binding, batch.graph_sha256)
    dtype = getattr(torch, settings.precision)
    if model.adjacency.dtype != dtype or batch.initial_state.values.requires_grad or batch.initial_state.values.grad_fn is not None:
        raise ValueError('detached caller state and explicit matching precision required')
    shape = tuple(batch.query_ids.shape)
    if len(shape) != 2 or shape[0] != batch_size or not 1 <= shape[0] <= 2 or not 1 <= shape[1] <= 12:
        raise ValueError('toy B<=2/T<=12 nonempty batch required')
    for name in ('query_ids', 'responses', 'source_rows', 'global_ranks'):
        value = getattr(batch, name)
        if value.shape != shape or value.dtype != torch.long:
            raise ValueError('integer event tensor geometry required')
    for name in ('event_valid_mask', 'loss_mask'):
        value = getattr(batch, name)
        if value.shape != shape or value.dtype != torch.bool:
            raise ValueError('boolean event/loss masks required')
    valid, loss = batch.event_valid_mask, batch.loss_mask
    if not loss.any() or torch.any(loss & ~valid):
        raise ValueError('nonempty selected loss mask must be subset of observed events')
    if (torch.any((batch.query_ids[valid] < 0) | (batch.query_ids[valid] >= c.num_nodes))
            or torch.any((batch.responses[valid] != 0) & (batch.responses[valid] != 1))):
        raise ValueError('active unknown node/nonbinary response forbidden')
    learners = batch.learner_ids
    if (type(learners) is not tuple or len(learners) != batch_size or len(set(learners)) != batch_size
            or any(type(x) is not str or not x.strip() for x in learners)):
        raise ValueError('distinct explicit learner identities required')
    rows = batch.source_rows[valid]
    if torch.any(rows < 1) or rows.unique().numel() != rows.numel():
        raise ValueError('positive unique source-row identity required')
    for i in range(batch_size):
        ranks = batch.global_ranks[i][valid[i]]
        if torch.any(ranks < 0) or torch.any(ranks[1:] <= ranks[:-1]):
            raise ValueError('caller event ranks must already increase; no sorting')
        if len(ranks) and ranks[0].item() != batch.initial_state.history_counts[i].item():
            raise ValueError('state history count must anchor first event rank')
        if torch.any(ranks[1:] - ranks[:-1] != 1):
            raise ValueError('contiguous observed ranks required; no implicit missing-history policy')
    if torch.any(batch.initial_state.history_counts > torch.iinfo(torch.long).max - valid.sum(1)):
        raise ValueError('history counter would overflow')
    return _optimizer_identity(optimizer, model, settings)


def _elapsed(budget):
    elapsed = time.perf_counter() - budget.started_at
    if not math.isfinite(elapsed) or elapsed < 0:
        raise ValueError('invalid caller monotonic budget origin')
    return elapsed


@dataclass(frozen=True)
class GKTTrainBatchResult:
    status: str
    stop_reason: str
    role: str
    complete_train_step: bool
    optimizer_steps: int
    cumulative_steps: int
    cumulative_targets: int
    loss_sum: float | None
    mean_loss: float | None
    selected_targets: int
    selected_source_rows: tuple[int, ...]
    observed_events: int
    grad_norm: float | None
    model_sha256_before: str
    model_sha256_after: str
    optimizer_sha256_before: str
    optimizer_sha256_after: str
    batch_sha256: str
    source_sha256: dict
    settings: GKTTrainingSettings
    binding: GKTBinding
    graph_sha256: str
    recipe_sha256: str
    final_state: GKTRecurrentState | None
    state_computed_with_model_sha256: str
    elapsed_seconds: float


def train_gkt_batch(model, optimizer, batch, *, settings, budget):
    """Một update, không đổi module flags/RNG hoặc tiếp tục hidden state ngầm.

    final_state là diagnostic state tính với weights BEFORE update. Không epoch,
    checkpoint hay recovery; exception không hứa rollback optimizer/gradients.
    """
    if type(budget) is not GKTStepBudget:
        raise ValueError('explicit cumulative engineering budget required')
    opt_before = _validate(model, optimizer, batch, settings)
    before = model_digest(model); source = source_identity()
    n = int(batch.loss_mask.sum()); rows = tuple(batch.source_rows[batch.loss_mask].tolist())
    total = norm = final = None; steps = 0
    reason = ('max_steps' if budget.steps_used >= budget.max_steps else
              'max_targets' if budget.targets_used + n > budget.max_targets else
              'max_seconds' if _elapsed(budget) >= budget.max_seconds else '')
    with torch.device('cpu'):
        if not reason:
            optimizer.zero_grad(set_to_none=True)
            output = model.sequence(batch.query_ids, batch.responses, batch.event_valid_mask,
                     initial_state=batch.initial_state, binding=batch.binding, graph_sha256=batch.graph_sha256)
            selected = output.logits[batch.loss_mask]
            if not torch.isfinite(selected).all():
                raise ValueError('nonfinite selected logits')
            total = F.binary_cross_entropy_with_logits(selected, batch.responses[batch.loss_mask].to(selected.dtype), reduction='sum')
            (total / n).backward()
            norm = torch.nn.utils.clip_grad_norm_(model.parameters(), settings.max_grad_norm, error_if_nonfinite=True)
            if not torch.isfinite(norm):
                raise ValueError('nonfinite training gradients')
            if _validate(model, optimizer, batch, settings) != opt_before or model_digest(model) != before:
                raise ValueError('model/optimizer changed before authorized step')
            final = replace(output.final_state, values=output.final_state.values.detach().clone(),
                            history_counts=output.final_state.history_counts.detach().clone())
            if _elapsed(budget) >= budget.max_seconds:
                reason = 'max_seconds_before_update'
            else:
                optimizer.step(); steps = 1
                model._bound(batch.binding, batch.graph_sha256)
                if _elapsed(budget) >= budget.max_seconds:
                    reason = 'max_seconds_after_update'
    if source_identity() != source or _batch_digest(batch) != batch.content_sha256:
        raise ValueError('source/input changed during train step')
    after = model_digest(model); opt_after = _optimizer_identity(optimizer, model, settings)
    elapsed = _elapsed(budget)
    if elapsed >= budget.max_seconds and not reason:
        reason = 'max_seconds_final_stage'
    return GKTTrainBatchResult('bounded' if reason else 'complete', reason or 'train_step_complete',
        WEIGHT_ROLE if steps else 'synthetic_untrained_engineering_attempt', not reason, steps,
        budget.steps_used + steps, budget.targets_used + (n if steps else 0),
        None if total is None else float(total.detach()), None if total is None else float(total.detach()) / n,
        n, rows, int(batch.event_valid_mask.sum()), None if norm is None else float(norm), before, after,
        opt_before, opt_after, batch.content_sha256, source, settings, batch.binding, batch.graph_sha256,
        batch.recipe_sha256, final, before, elapsed)
