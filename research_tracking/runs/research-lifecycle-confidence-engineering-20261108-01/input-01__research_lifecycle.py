"""Ledger thuần metadata cho A0 pilot; KHÔNG là trainer hoặc execution proof.

Trạng thái bất biến phát hiện sai thứ tự và counter của caller hợp tác. Caller
phải giữ duy nhất head hiện hành, fsync sự kiện trước Adam body và cung cấp thời
gian đo thật. Không ngăn fork/reset ledger, không chứng minh source/runtime,
fresh model, optimizer ownership hoặc rollback. Không đọc file/tạo model ở đây.
Wrapper sau này reuse train_epoch/EarlyStopping/checkpoint hiện có; chưa wired.
"""
from dataclasses import asdict, dataclass, is_dataclass, replace
import json
import math
import re

from .research_execution import SimulatorResearchSpec
from ..simulator_bridge import identity_hash
from ..simulator_research_data import SelectionFreeze

PURPOSE = 'a0_single_candidate_lifecycle_pilot'
ROLES = ('train', 'selection', 'calibration')


def _check(ok, message):
    if not ok:
        raise ValueError(message)


def _sha(value):
    _check(type(value) is str and re.fullmatch('[0-9a-f]{64}', value), 'SHA256 required')


def _positive(value):
    _check(type(value) is int and value > 0, 'positive integer required')


def _json(value):
    return json.loads(json.dumps(value, sort_keys=True, allow_nan=False,
                                default=lambda x: asdict(x) if is_dataclass(x) else str(x)))


@dataclass(frozen=True)
class LifecycleInvocation:
    """Bindings của caller; không consume authorization hoặc xác minh file."""
    spec: SimulatorResearchSpec
    authorization_sha256: str
    done_sha256: str
    research_plan_sha256: str
    bank_sha256: str
    role_shard_sha256: tuple[tuple[str, str], ...]
    selection_population_sha256: str
    calibration_population_sha256: str
    source_inventory_sha256: str
    purpose: str

    def __post_init__(self):
        _check(type(self.spec) is SimulatorResearchSpec and self.purpose == PURPOSE,
               'typed spec and single-candidate A0 pilot required')
        for key, value in asdict(self).items():
            if key.endswith('sha256') and key != 'role_shard_sha256':
                _sha(value)
        _check(type(self.role_shard_sha256) is tuple
               and all(type(x) is tuple and len(x) == 2 for x in self.role_shard_sha256)
               and tuple(x[0] for x in self.role_shard_sha256) == ROLES,
               'exact immutable train/selection/calibration shard bindings required')
        for _, digest in self.role_shard_sha256:
            _sha(digest)

    @property
    def identity(self):
        return identity_hash(_json(asdict(self)))


@dataclass(frozen=True)
class PhaseInputs:
    """Chỉ refs, không chứa corpus/labels/callback; không cấp quyền thực thi."""
    scope: str
    role_shards: tuple[tuple[str, str], ...]
    selection_freeze_sha256: str | None
    refit_checkpoint_sha256: str | None


@dataclass(frozen=True)
class StepTicket:
    invocation_sha256: str
    sequence: int
    phase: str
    epoch: int
    targets: int


@dataclass(frozen=True)
class EpochRecord:
    epoch: int
    # None: epoch này không được persist, không ghép bytes của prior best.
    checkpoint_sha256: str | None
    predictions_sha256: str
    population_sha256: str
    full_targets: int
    supported_targets: int
    raw_selection_loss: float


class LifecycleBudgetExceeded(ValueError):
    """Trả failed ledger trong exception; body-return đã xảy ra không bị xóa."""
    def __init__(self, ledger):
        self.ledger = ledger
        super().__init__('cumulative lifecycle time budget exceeded')


@dataclass(frozen=True)
class LifecycleLedger:
    invocation: LifecycleInvocation
    phase: str = 'ready'
    epoch: int = 0
    fit_epochs: tuple[EpochRecord, ...] = ()
    refit_epochs: int = 0
    selection_freeze: SelectionFreeze | None = None
    refit_checkpoint_sha256: str | None = None
    reload_proof_sha256: str | None = None
    calibration_predictions_sha256: str | None = None
    calibrator_sha256: str | None = None
    export_sha256: str | None = None
    reserved_steps: int = 0
    body_returned_steps: int = 0
    completed_steps: int = 0
    reserved_targets: int = 0
    completed_targets: int = 0
    epoch_targets: int = 0
    pending: StepTicket | None = None
    pending_body_returned: bool = False
    wall_seconds: float = 0.0
    training_seconds: float = 0.0
    events: tuple[str, ...] = ()

    @classmethod
    def begin(cls, invocation):
        _check(type(invocation) is LifecycleInvocation, 'typed invocation required')
        return cls(invocation)

    def _next(self, event, *, wall_seconds, training_seconds, **changes):
        _check(self.phase not in ('failed', 'complete'), 'terminal ledger')
        for value, old in ((wall_seconds, self.wall_seconds), (training_seconds, self.training_seconds)):
            _check(type(value) in (int, float) and math.isfinite(value) and value >= old,
                   'finite monotonic cumulative clocks required')
        _check(training_seconds <= wall_seconds, 'training clock exceeds wall clock')
        b = self.invocation.spec.budget
        payload = _json(dict(event=event, invocation_sha256=self.invocation.identity,
                            previous_event_sha256=None if not self.events else identity_hash(self.events[-1]),
                            wall_seconds=wall_seconds, training_seconds=training_seconds, changes=changes))
        if wall_seconds > b.max_wall_seconds or training_seconds > b.max_training_seconds:
            # Sau body, counter phải giữ cả khi controller phát hiện quá giờ.
            observed = changes if event in ('optimizer_body_returned', 'batch_complete') else {}
            failed = replace(self, **observed, phase='failed', wall_seconds=wall_seconds,
                             training_seconds=training_seconds, events=self.events + (
                                 json.dumps({**payload, 'outcome': 'REJECTED_TIME_BUDGET'}, sort_keys=True),))
            raise LifecycleBudgetExceeded(failed)
        return replace(self, wall_seconds=wall_seconds, training_seconds=training_seconds,
                       events=self.events + (json.dumps(payload, sort_keys=True, allow_nan=False),), **changes)

    def inputs(self, scope):
        roles = {'select_train80': ('train',), 'raw_selection10': ('selection',),
                 'refit_union90': ('train', 'selection'), 'calibration_predict': ('calibration',),
                 'temperature_fit': ('calibration',)}
        allowed = {'select_train80': ('ready', 'fit80'), 'raw_selection10': ('fit80',),
                   'refit_union90': ('selection_frozen', 'refit90'),
                   'calibration_predict': ('refit_complete', 'calibration'),
                   'temperature_fit': ('temperature',)}
        _check(scope in roles and self.phase in allowed[scope], 'scope/phase mismatch')
        if scope == 'raw_selection10':
            _check(self.epoch > 0 and self.pending is None
                   and self.epoch_targets == self.invocation.spec.budget.train_targets,
                   'raw selection requires all fit targets completed')
        hashes = dict(self.invocation.role_shard_sha256)
        return PhaseInputs(scope, tuple((r, hashes[r]) for r in roles[scope]),
                           None if self.selection_freeze is None else self.selection_freeze.identity,
                           self.refit_checkpoint_sha256)

    def start_epoch(self, *, wall_seconds, training_seconds):
        _check(self.pending is None and self.epoch == 0, 'epoch/step already pending')
        if self.phase in ('ready', 'fit80'):
            number = len(self.fit_epochs) + 1
            _check(number <= self.invocation.spec.native_config.max_epochs, 'fit epoch cap exceeded')
            phase = 'fit80'
        else:
            _check(self.phase in ('selection_frozen', 'refit90') and self.selection_freeze is not None,
                   'refit requires raw-selection freeze')
            number = self.refit_epochs + 1
            _check(number <= self.selection_freeze.selected_epoch, 'refit selected epoch cap exceeded')
            phase = 'refit90'
        return self._next('epoch_started', wall_seconds=wall_seconds, training_seconds=training_seconds,
                          phase=phase, epoch=number, epoch_targets=0)

    def reserve_step(self, targets, *, wall_seconds, training_seconds):
        _positive(targets)
        _check(self.phase in ('fit80', 'refit90') and self.epoch > 0 and self.pending is None,
               'optimizer not allowed or step pending')
        b = self.invocation.spec.budget
        expected = b.train_targets + (b.selection_targets if self.phase == 'refit90' else 0)
        _check(self.reserved_steps < b.max_optimizer_steps
               and self.reserved_targets + targets <= b.max_optimized_targets
               and self.epoch_targets + targets <= expected, 'cumulative optimizer/target budget exceeded')
        ticket = StepTicket(self.invocation.identity, self.reserved_steps + 1, self.phase, self.epoch, targets)
        return self._next('optimizer_reserved', wall_seconds=wall_seconds, training_seconds=training_seconds,
                          reserved_steps=self.reserved_steps + 1, reserved_targets=self.reserved_targets + targets,
                          pending=ticket, pending_body_returned=False)

    def body_returned(self, ticket, *, wall_seconds, training_seconds):
        _check(type(ticket) is StepTicket and ticket == self.pending and not self.pending_body_returned,
               'stale/foreign/already-returned step ticket')
        return self._next('optimizer_body_returned', wall_seconds=wall_seconds, training_seconds=training_seconds,
                          body_returned_steps=self.body_returned_steps + 1, pending_body_returned=True)

    def complete_step(self, ticket, *, wall_seconds, training_seconds):
        _check(type(ticket) is StepTicket and ticket == self.pending and self.pending_body_returned,
               'step body has not returned or ticket mismatch')
        return self._next('batch_complete', wall_seconds=wall_seconds, training_seconds=training_seconds,
                          completed_steps=self.completed_steps + 1, completed_targets=self.completed_targets + ticket.targets,
                          epoch_targets=self.epoch_targets + ticket.targets, pending=None, pending_body_returned=False)

    def complete_fit_epoch(self, record, *, wall_seconds, training_seconds):
        b = self.invocation.spec.budget
        _check(self.phase == 'fit80' and self.epoch > 0 and self.pending is None
               and self.epoch_targets == b.train_targets, 'incomplete fit epoch')
        _check(type(record) is EpochRecord and type(record.epoch) is int and record.epoch == self.epoch
               and type(record.full_targets) is int and record.full_targets == b.selection_targets
               and type(record.supported_targets) is int and 0 < record.supported_targets <= record.full_targets
               and record.population_sha256 == self.invocation.selection_population_sha256,
               'raw selection full population/epoch mismatch')
        if record.checkpoint_sha256 is not None:
            _sha(record.checkpoint_sha256)
        for value in (record.predictions_sha256, record.population_sha256):
            _sha(value)
        _check(type(record.raw_selection_loss) in (int, float) and math.isfinite(record.raw_selection_loss)
               and record.raw_selection_loss >= 0, 'finite raw response loss required')
        return self._next('fit_epoch_complete', wall_seconds=wall_seconds, training_seconds=training_seconds,
                          fit_epochs=self.fit_epochs + (record,), epoch=0, epoch_targets=0)

    def freeze_selection(self, freeze, *, wall_seconds, training_seconds):
        _check(self.phase == 'fit80' and self.epoch == 0 and self.pending is None,
               'freeze requires complete raw-selection epoch')
        inv = self.invocation
        _check(type(freeze) is SelectionFreeze and 1 <= freeze.selected_epoch <= len(self.fit_epochs)
               and freeze.research_plan_sha256 == inv.research_plan_sha256 and freeze.bank_sha256 == inv.bank_sha256
               and freeze.train_shard_sha256 == dict(inv.role_shard_sha256)['train']
               and freeze.selection_shard_sha256 == dict(inv.role_shard_sha256)['selection'], 'foreign selection freeze')
        _check(self.fit_epochs[freeze.selected_epoch-1].checkpoint_sha256 is not None,
               'selected epoch requires its own persisted checkpoint')
        # Epoch choice is owned by existing EarlyStopping, NOT recomputed here.
        return self._next('raw_selection_frozen', wall_seconds=wall_seconds, training_seconds=training_seconds,
                          phase='selection_frozen', selection_freeze=freeze)

    def complete_refit_epoch(self, *, wall_seconds, training_seconds):
        b = self.invocation.spec.budget
        _check(self.phase == 'refit90' and self.epoch > 0 and self.pending is None
               and self.epoch_targets == b.train_targets + b.selection_targets, 'incomplete refit epoch')
        return self._next('refit_epoch_complete', wall_seconds=wall_seconds, training_seconds=training_seconds,
                          refit_epochs=self.epoch, epoch=0, epoch_targets=0)

    def seal_refit(self, checkpoint_sha256, reload_proof_sha256, *, wall_seconds, training_seconds):
        _sha(checkpoint_sha256); _sha(reload_proof_sha256)
        _check(self.phase == 'refit90' and self.epoch == 0 and self.pending is None
               and self.refit_epochs == self.selection_freeze.selected_epoch, 'refit epochs incomplete')
        return self._next('refit_sealed', wall_seconds=wall_seconds, training_seconds=training_seconds,
                          phase='refit_complete', refit_checkpoint_sha256=checkpoint_sha256,
                          reload_proof_sha256=reload_proof_sha256)

    def predictions_complete(self, *, checkpoint_sha256, predictions_sha256, population_sha256,
                             full_targets, supported_targets, wall_seconds, training_seconds):
        _sha(predictions_sha256)
        _check(self.phase == 'refit_complete' and checkpoint_sha256 == self.refit_checkpoint_sha256
               and population_sha256 == self.invocation.calibration_population_sha256
               and type(full_targets) is int and full_targets == self.invocation.spec.budget.calibration_targets
               and type(supported_targets) is int and 0 <= supported_targets <= full_targets,
               'calibration checkpoint/full population mismatch')
        return self._next('calibration_predictions_complete', wall_seconds=wall_seconds, training_seconds=training_seconds,
                          phase='temperature', calibration_predictions_sha256=predictions_sha256)

    def finish(self, calibrator_sha256, export_sha256, *, wall_seconds, training_seconds):
        _sha(calibrator_sha256); _sha(export_sha256)
        _check(self.phase == 'temperature' and self.pending is None, 'calibration export not ready')
        return self._next('metadata_lifecycle_complete_not_execution_proof', wall_seconds=wall_seconds,
                          training_seconds=training_seconds, phase='complete', calibrator_sha256=calibrator_sha256,
                          export_sha256=export_sha256)

    def fail(self, error_code):
        """Giữ reservation/body-return kể cả lỗi sau Adam; không rollback/0step."""
        _check(self.phase not in ('complete', 'failed') and type(error_code) is str
               and re.fullmatch('[A-Z][A-Z0-9_]{0,79}', error_code), 'nonterminal ledger/error code required')
        payload = json.dumps(dict(event='failed', error_code=error_code,
                                  invocation_sha256=self.invocation.identity,
                                  previous_event_sha256=None if not self.events else identity_hash(self.events[-1]),
                                  counters=dict(reserved=self.reserved_steps, body_returned=self.body_returned_steps,
                                                completed=self.completed_steps)), sort_keys=True)
        return replace(self, phase='failed', events=self.events + (payload,))
