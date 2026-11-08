"""Pure ledger metadata; không model, optimizer, corpus hoặc execution proof."""
from dataclasses import FrozenInstanceError, replace
import ast
import builtins
import json
from pathlib import Path
import subprocess
import sys

import pytest

from knowledge_tracing.akt import config as cfg
from knowledge_tracing.akt.research_execution import ResearchResourceBudget, SimulatorResearchSpec
from knowledge_tracing.akt import research_lifecycle as life
from knowledge_tracing.simulator_research_data import SelectionFreeze

SHA = 'a' * 64
CLOCK = dict(wall_seconds=1., training_seconds=.5)


@pytest.fixture(autouse=True)
def no_execution(monkeypatch):
    assert 'torch' not in sys.modules
    original = builtins.__import__
    def checked(name, *args, **kwargs):
        if name.split('.')[0] in ('torch', 'numpy', 'pandas') or name in (
                'knowledge_tracing.akt.model', 'knowledge_tracing.akt.training',
                'knowledge_tracing.simulator_corpus_reader'):
            raise AssertionError('no neural/data execution imports in pure suite')
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', checked)
    def forbidden(*args, **kwargs):
        raise AssertionError('no subprocess/model/optimizer call allowed')
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    yield
    assert 'torch' not in sys.modules


@pytest.fixture
def invocation():
    # Handmade metadata only: these SHA strings do not attest corpus/auth/files.
    b = ResearchResourceBudget(8, 1, 1, 8, 1, 1, 1, 8, 100, 10., 20.,
                               2*1024**3, 1024**3, 8*1024**2, 1024**2, 4*1024**2)
    c = cfg.AKTConfig(phase='simulator-research', run_id='pure-lifecycle', execution_enabled=True,
        output_dir=cfg.PROJECT_ROOT/'experiments/akt/results/pure-lifecycle',
        max_train_users=9, max_val_users=1, max_targets_per_side=9, max_total_targets=10,
        max_steps=8, max_seconds=10., max_wall_seconds=20., max_rss_bytes=2*1024**3,
        min_available_ram_bytes=1024**3)
    spec = SimulatorResearchSpec(c, 'pure-metadata-not-corpus', SHA, SHA, b)
    return life.LifecycleInvocation(spec, SHA, SHA, SHA, SHA,
        (('train', 'b'*64), ('selection', 'c'*64), ('calibration', 'd'*64)),
        'e'*64, 'f'*64, SHA, life.PURPOSE)


def step(ledger, targets):
    reserved = ledger.reserve_step(targets, **CLOCK)
    returned = reserved.body_returned(reserved.pending, **CLOCK)
    return returned.complete_step(reserved.pending, **CLOCK)


def epoch_record(invocation, number):
    return life.EpochRecord(number, '1'*64, '2'*64,
                            invocation.selection_population_sha256, 1, 1, .7)


def fit_complete(invocation):
    ledger = life.LifecycleLedger.begin(invocation).start_epoch(**CLOCK)
    ledger = step(ledger, 8)
    return ledger.complete_fit_epoch(epoch_record(invocation, 1), **CLOCK)


def freeze(invocation, epoch=1):
    hashes = dict(invocation.role_shard_sha256)
    return SelectionFreeze(invocation.research_plan_sha256, invocation.bank_sha256,
        hashes['train'], hashes['selection'], '3'*64, epoch, 'raw_selection_before_refit')


def refit_complete(invocation):
    ledger = fit_complete(invocation).freeze_selection(freeze(invocation), **CLOCK)
    ledger = step(ledger.start_epoch(**CLOCK), 9).complete_refit_epoch(**CLOCK)
    return ledger.seal_refit('4'*64, '5'*64, **CLOCK)


def test_full_metadata_lifecycle_preserves_global_counters_and_roles(invocation):
    initial = life.LifecycleLedger.begin(invocation)
    assert initial.inputs('select_train80').role_shards == invocation.role_shard_sha256[:1]
    ledger = refit_complete(invocation)
    assert (ledger.reserved_steps, ledger.body_returned_steps, ledger.completed_steps) == (2, 2, 2)
    assert (ledger.reserved_targets, ledger.completed_targets) == (17, 17)
    assert ledger.inputs('calibration_predict').role_shards == invocation.role_shard_sha256[2:]
    ledger = ledger.predictions_complete(checkpoint_sha256='4'*64, predictions_sha256='6'*64,
        population_sha256=invocation.calibration_population_sha256, full_targets=1, supported_targets=1, **CLOCK)
    assert ledger.inputs('temperature_fit').role_shards == invocation.role_shard_sha256[2:]
    done = ledger.finish('7'*64, '8'*64, **CLOCK)
    assert done.phase == 'complete' and done.completed_steps == 2
    assert json.loads(done.events[-1])['event'] == 'metadata_lifecycle_complete_not_execution_proof'
    assert initial.phase == 'ready' and initial.events == ()


@pytest.mark.parametrize('value', [(), ((),), (('train',),), (['train', SHA],),
    (('train', SHA), ('selection', SHA)),
    (('selection', SHA), ('train', SHA), ('calibration', SHA)),
    (('train', SHA), ('selection', SHA), ('final', SHA)),
    (('train', SHA), ('selection', SHA), ('calibration', 'x'*64))])
def test_invocation_rejects_bad_role_shapes_before_indexing(invocation, value):
    with pytest.raises(ValueError):
        replace(invocation, role_shard_sha256=value)


def test_invocation_frozen_identity_and_no_mainmatrix_claim(invocation):
    with pytest.raises(FrozenInstanceError):
        invocation.purpose = 'main_matrix_winner'
    with pytest.raises(ValueError):
        replace(invocation, purpose='main_matrix_winner')
    with pytest.raises(ValueError):
        replace(invocation, done_sha256=True)
    assert replace(invocation, authorization_sha256='9'*64).identity != invocation.identity


@pytest.mark.parametrize('scope', ['raw_selection10', 'refit_union90', 'calibration_predict',
                                   'temperature_fit', 'final', 'train'])
def test_initial_phase_cannot_access_other_inputs(invocation, scope):
    with pytest.raises(ValueError):
        life.LifecycleLedger.begin(invocation).inputs(scope)


def test_raw_selection_only_after_all_training_targets(invocation):
    ledger = life.LifecycleLedger.begin(invocation).start_epoch(**CLOCK)
    with pytest.raises(ValueError):
        ledger.inputs('raw_selection10')
    ledger = step(ledger, 8)
    assert ledger.inputs('raw_selection10').role_shards == invocation.role_shard_sha256[1:2]
    assert 'calibration' not in dict(ledger.inputs('raw_selection10').role_shards)


def test_refit_inputs_keep_real_origin_roles_and_actual_freeze(invocation):
    ledger = fit_complete(invocation).freeze_selection(freeze(invocation), **CLOCK)
    refs = ledger.inputs('refit_union90')
    assert refs.role_shards == invocation.role_shard_sha256[:2]
    assert refs.selection_freeze_sha256 == freeze(invocation).identity
    assert refs.refit_checkpoint_sha256 is None  # No fake fresh-model declaration.


def test_pending_ticket_and_return_order(invocation):
    ledger = life.LifecycleLedger.begin(invocation).start_epoch(**CLOCK).reserve_step(8, **CLOCK)
    ticket = ledger.pending
    with pytest.raises(ValueError):
        ledger.reserve_step(1, **CLOCK)
    with pytest.raises(ValueError):
        ledger.complete_step(ticket, **CLOCK)
    with pytest.raises(ValueError):
        ledger.body_returned(replace(ticket, sequence=2), **CLOCK)
    returned = ledger.body_returned(ticket, **CLOCK)
    with pytest.raises(ValueError):
        returned.body_returned(ticket, **CLOCK)
    complete = returned.complete_step(ticket, **CLOCK)
    with pytest.raises(ValueError):
        complete.complete_step(ticket, **CLOCK)


@pytest.mark.parametrize('when', ['reserved', 'body_returned'])
def test_failures_do_not_rollback_or_claim_zero_updates(invocation, when):
    ledger = life.LifecycleLedger.begin(invocation).start_epoch(**CLOCK).reserve_step(8, **CLOCK)
    if when == 'body_returned':
        ledger = ledger.body_returned(ledger.pending, **CLOCK)
    failed = ledger.fail('INJECTED_AFTER_STEP_EVENT')
    assert failed.reserved_steps == 1 and failed.body_returned_steps == int(when == 'body_returned')
    assert failed.completed_steps == 0 and failed.pending == ledger.pending
    with pytest.raises(ValueError):
        failed.complete_step(failed.pending, **CLOCK)


def test_late_body_return_preserved_in_rejected_exception(invocation):
    ledger = life.LifecycleLedger.begin(invocation).start_epoch(**CLOCK).reserve_step(8, **CLOCK)
    with pytest.raises(life.LifecycleBudgetExceeded) as caught:
        ledger.body_returned(ledger.pending, wall_seconds=21., training_seconds=2.)
    failed = caught.value.ledger
    assert failed.phase == 'failed' and failed.reserved_steps == failed.body_returned_steps == 1
    assert failed.completed_steps == 0 and failed.wall_seconds == 21.
    assert json.loads(failed.events[-1])['outcome'] == 'REJECTED_TIME_BUDGET'


def test_time_guard_before_reservation_does_not_charge_unstarted_body(invocation):
    ledger = life.LifecycleLedger.begin(invocation).start_epoch(**CLOCK)
    with pytest.raises(life.LifecycleBudgetExceeded) as caught:
        ledger.reserve_step(8, wall_seconds=21., training_seconds=2.)
    assert caught.value.ledger.reserved_steps == 0 and caught.value.ledger.pending is None


@pytest.mark.parametrize('clocks', [dict(wall_seconds=.5, training_seconds=.5),
    dict(wall_seconds=1., training_seconds=2.), dict(wall_seconds=float('nan'), training_seconds=.5),
    dict(wall_seconds=True, training_seconds=.5)])
def test_invalid_cumulative_clocks(invocation, clocks):
    ledger = life.LifecycleLedger.begin(invocation).start_epoch(**CLOCK)
    with pytest.raises(ValueError):
        ledger.reserve_step(1, **clocks)


def test_refit_does_not_reset_global_step_cap(invocation):
    b = replace(invocation.spec.budget, max_optimizer_steps=1)
    c = replace(invocation.spec.native_config, max_steps=1)
    inv = replace(invocation, spec=replace(invocation.spec, budget=b, native_config=c))
    ledger = fit_complete(inv).freeze_selection(freeze(inv), **CLOCK).start_epoch(**CLOCK)
    with pytest.raises(ValueError):
        ledger.reserve_step(9, **CLOCK)
    assert ledger.reserved_steps == 1 and ledger.completed_targets == 8


def test_target_cap_and_incomplete_epoch(invocation):
    ledger = life.LifecycleLedger.begin(invocation).start_epoch(**CLOCK)
    with pytest.raises(ValueError):
        ledger.reserve_step(9, **CLOCK)
    ledger = step(ledger, 7)
    with pytest.raises(ValueError):
        ledger.complete_fit_epoch(epoch_record(invocation, 1), **CLOCK)
    with pytest.raises(ValueError):
        ledger.freeze_selection(freeze(invocation), **CLOCK)


@pytest.mark.parametrize('changes', [dict(full_targets=2), dict(population_sha256=SHA),
    dict(supported_targets=0), dict(raw_selection_loss=float('inf')), dict(epoch=True)])
def test_raw_selection_no_partial_population_or_nonfinite_loss(invocation, changes):
    ledger = step(life.LifecycleLedger.begin(invocation).start_epoch(**CLOCK), 8)
    with pytest.raises(ValueError):
        ledger.complete_fit_epoch(replace(epoch_record(invocation, 1), **changes), **CLOCK)


@pytest.mark.parametrize('changes', [dict(research_plan_sha256='9'*64), dict(bank_sha256='9'*64),
    dict(train_shard_sha256='9'*64), dict(selection_shard_sha256='9'*64), dict(selected_epoch=2)])
def test_foreign_or_uncompleted_freeze_rejected(invocation, changes):
    ledger = fit_complete(invocation)
    with pytest.raises(ValueError):
        ledger.freeze_selection(replace(freeze(invocation), **changes), **CLOCK)


def test_refit_exact_selected_epochs_and_calibration_cannot_optimize(invocation):
    ledger = fit_complete(invocation).freeze_selection(freeze(invocation), **CLOCK)
    ledger = step(ledger.start_epoch(**CLOCK), 9).complete_refit_epoch(**CLOCK)
    with pytest.raises(ValueError):
        ledger.start_epoch(**CLOCK)
    sealed = ledger.seal_refit('4'*64, '5'*64, **CLOCK)
    with pytest.raises(ValueError):
        sealed.reserve_step(1, **CLOCK)
    with pytest.raises(ValueError):
        sealed.inputs('select_train80')


@pytest.mark.parametrize('changes', [dict(checkpoint_sha256=SHA), dict(population_sha256=SHA),
    dict(full_targets=0), dict(supported_targets=2)])
def test_calibration_rejects_checkpoint_or_coverage_drift(invocation, changes):
    args = dict(checkpoint_sha256='4'*64, predictions_sha256='6'*64,
        population_sha256=invocation.calibration_population_sha256, full_targets=1, supported_targets=1, **CLOCK)
    args.update(changes)
    with pytest.raises(ValueError):
        refit_complete(invocation).predictions_complete(**args)


def test_no_io_heavy_imports_training_loop_or_freshness_claim():
    tree = ast.parse(Path(life.__file__).read_text(encoding='utf-8'))
    imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert 'training' not in imports and 'model' not in imports
    calls = [node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute)]
    assert not set(calls) & {'open', 'read_bytes', 'write_bytes', 'mkdir', 'load', 'step', 'backward'}
    assert 'torch' not in sys.modules
