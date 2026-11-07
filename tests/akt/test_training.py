import pandas as pd
import pytest
import torch
import random
from dataclasses import replace

from knowledge_tracing.akt.config import AKTConfig
from knowledge_tracing.akt.encoding import fit_vocabulary
from knowledge_tracing.akt.model import AKTAdapter
from knowledge_tracing.akt.checkpoint import load_checkpoint
from knowledge_tracing.akt.splits import InnerSplit, make_inner_split
import knowledge_tracing.akt.training as training_module
from knowledge_tracing.akt.training import (EarlyStopping, EpochStats, fit_fixed_budget_outer_train,
                                            select_checkpoint, refit_outer_train, train_epoch)
from knowledge_tracing.akt.types import KTEvent, LearnerEvents
from knowledge_tracing.akt.windows import iter_windows


def test_inner_split_is_disjoint_deterministic_and_outer_free():
    frame = pd.DataFrame({'user_id': [f'u{i}' for i in range(20)],
                          'partition': ['development'] * 20,
                          'fold': [0] * 4 + [1] * 4 + [2] * 4 + [3] * 4 + [4] * 4})
    a = make_inner_split(frame, outer_fold=0)
    b = make_inner_split(frame.sample(frac=1, random_state=3), outer_fold=0)
    assert a == b
    assert not set(a.inner_train_users) & set(a.inner_val_users)
    assert not set(frame.loc[frame.fold == 0, 'user_id']) & (set(a.inner_train_users) | set(a.inner_val_users))
    assert len(a.inner_train_users) == 14
    assert len(a.inner_val_users) == 2


def test_inner_split_rejects_holdout_rows_and_too_few_learners():
    frame = pd.DataFrame({'user_id': ['dev', 'hold'], 'partition': ['development', 'test'], 'fold': [1, -1]})
    with pytest.raises(ValueError, match='development'):
        make_inner_split(frame, outer_fold=0)
    with pytest.raises(ValueError, match='learners'):
        make_inner_split(frame.iloc[:1], outer_fold=0)


def test_early_stopping_uses_inner_loss_and_keeps_earliest_tie():
    stop = EarlyStopping(patience=3, min_delta=0.0001)
    decisions = [stop.observe(epoch, loss) for epoch, loss in enumerate([0.4, 0.3, 0.3, 0.31, 0.32], 1)]
    assert stop.best_epoch == 2
    assert decisions == [False, False, False, False, True]


def test_early_stopping_rejects_nonfinite_or_repeated_epochs():
    stop = EarlyStopping(patience=3, min_delta=0.0001)
    stop.observe(1, 0.5)
    with pytest.raises(ValueError):
        stop.observe(1, 0.4)
    with pytest.raises(ValueError):
        stop.observe(2, float('nan'))


def test_epoch_budget_marks_partial_run_incomplete():
    events = tuple(KTEvent('u', 'A', i+1, i+1, i % 2, 0, 1) for i in range(3))
    user = LearnerEvents('u', 1, events)
    enc = fit_vocabulary([user])
    cfg = AKTConfig(d_model=32, heads=4, d_ff=64, final_fc=32, dropout=0,
                    context=1, target_block=1, batch_size=1)
    model = AKTAdapter(cfg, enc)
    opt = torch.optim.Adam(model.native.parameters(), lr=cfg.lr)
    factory = lambda: iter_windows(user, enc, context=1, target_block=1, training=True)
    result = train_epoch(model, factory, optimizer=opt, epoch=1, budget={'max_steps': 1})
    assert result.complete is False
    assert result.optimizer_steps == 1
    assert result.valid_targets == 1
    assert result.windows_processed == 2
    assert result.processed_target_rows == 2
    assert result.optimized_target_rows == 1


def test_progress_callback_marks_partial_epoch_as_in_progress():
    user = LearnerEvents('progress', 1, (
        KTEvent('progress', 'A', 1, 1, 1, 0, 1),
        KTEvent('progress', 'A', 2, 2, 0, 0, 1),
    ))
    enc = fit_vocabulary([user])
    cfg = AKTConfig(d_model=32, heads=4, d_ff=64, final_fc=32, dropout=0,
                    context=1, target_block=1, batch_size=1)
    model = AKTAdapter(cfg, enc)
    opt = torch.optim.Adam(model.native.parameters(), lr=cfg.lr)
    observed = []

    def fail_after_progress(payload):
        observed.append(payload)
        raise OSError('synthetic progress persistence failure')

    with pytest.raises(OSError, match='progress persistence'):
        train_epoch(model, lambda: iter_windows(user, enc, context=1, target_block=1, training=True),
                    optimizer=opt, epoch=1, budget={'max_steps': 5},
                    progress_callback=fail_after_progress)

    assert len(observed) == 1
    assert observed[0]['complete_epoch'] is False
    assert observed[0]['stop_reason'] == 'training_in_progress'


def test_epoch_stats_record_gradient_and_parameter_update_behavior():
    user = LearnerEvents('gradient', 1, (
        KTEvent('gradient', 'A', 1, 1, 1, 0, 1),
        KTEvent('gradient', 'B', 2, 2, 0, 0, 1),
    ))
    enc = fit_vocabulary([user])
    cfg = AKTConfig(d_model=32, heads=4, d_ff=64, final_fc=32, dropout=0,
                    context=1, target_block=2, batch_size=1)
    model = AKTAdapter(cfg, enc)
    opt = torch.optim.Adam(model.native.parameters(), lr=cfg.lr)
    factory = lambda: iter_windows(user, enc, context=1, target_block=2, training=True)
    result = train_epoch(model, factory, optimizer=opt, epoch=1, budget={'max_steps': 20})
    assert result.optimizer_steps == 1
    assert result.nonzero_gradient_steps == 1
    assert result.parameter_update_steps == 1
    assert result.max_pre_clip_grad_norm > 0
    assert 0 < result.max_post_clip_grad_norm <= cfg.max_grad_norm


def test_training_aborts_when_rss_crosses_cap_during_optimizer_update(monkeypatch):
    user = LearnerEvents('u', 1, (KTEvent('u', 'A', 1, 1, 1, 0, 1),))
    enc = fit_vocabulary([user])
    cfg = AKTConfig(d_model=32, heads=4, d_ff=64, final_fc=32, dropout=0,
                    context=1, target_block=1, batch_size=1)
    model = AKTAdapter(cfg, enc)
    readings = iter([100, 200])
    def snapshot():
        value = next(readings)
        return {'pid': 1, 'process_rss_bytes': value, 'process_peak_rss_bytes': value,
                'system_available_ram_bytes': 10_000, 'system_total_ram_bytes': 20_000}
    monkeypatch.setattr(training_module, 'memory_snapshot', snapshot)
    monkeypatch.setattr(model, 'step', lambda batch, optimizer: {
        'stepped': True, 'valid_targets': 1, 'loss_sum': 0.5})
    factory = lambda: iter_windows(user, enc, context=1, target_block=1, training=True)
    with pytest.raises(MemoryError, match='RSS ceiling'):
        train_epoch(model, factory, optimizer=torch.optim.Adam(model.native.parameters()), epoch=1,
                    budget={'max_steps': 2, 'max_rss_bytes': 150})


def test_selection_uses_only_inner_scopes_and_keeps_earliest_best(tmp_path, monkeypatch):
    train = LearnerEvents('train', 1, (KTEvent('train', 'A', 1, 1, 1, 0, 1),))
    val = LearnerEvents('val', 2, (KTEvent('val', 'A', 1, 2, 0, 0, 2),))
    split = InnerSplit(('train',), ('val',), 0, 'split-hash')
    cfg = AKTConfig(output_dir=tmp_path, d_model=32, heads=4, d_ff=64, final_fc=32, dropout=0)
    losses = iter([0.4, 0.3, 0.3, 0.31, 0.32])
    observed = []
    def fake_train(model, factory, **kwargs):
        observed.extend(w.window.inputs.user_ids[0] for w in factory())
        return EpochStats(1.0, 1, 1, True, {})
    def fake_evaluate(model, factory, allowed_users):
        observed.extend(u.user_id for u in factory())
        return next(losses), {'predicted_rows': 1}
    monkeypatch.setattr(training_module, 'train_epoch', fake_train)
    monkeypatch.setattr(training_module, 'evaluate_inner', fake_evaluate)
    result = select_checkpoint(cfg, inner_split=split,
                               train_learners_factory=lambda: iter([train]),
                               val_learners_factory=lambda: iter([val]), identity={'run': 'synthetic'},
                               budget={'max_steps': 10})
    assert result.selected_epoch == 2
    assert len(result.history) == 5
    assert result.checkpoint.is_file()
    payload = torch.load(result.checkpoint, map_location='cpu', weights_only=True)
    assert payload['progress']['sampler_seed'] == cfg.seed + result.selected_epoch
    assert payload['progress']['history'][0]['training']['mean_loss'] == 1.0
    assert set(observed) == {'train', 'val'}
    assert 'outer' not in observed


def test_refit_fits_fresh_vocabulary_on_all_outer_train_users():
    users = [LearnerEvents('a', 1, (KTEvent('a', 'A', 1, 1, 1, 0, 1),)),
             LearnerEvents('b', 2, (KTEvent('b', 'B', 1, 2, 0, 0, 2),))]
    cfg = AKTConfig(d_model=32, heads=4, d_ff=64, final_fc=32, dropout=0, batch_size=2)
    model = refit_outer_train(cfg, outer_train_users=('a', 'b'),
                              train_learners_factory=lambda: iter(users), selected_epochs=1,
                              identity={'run': 'synthetic'}, budget={'max_steps': 10})
    assert model.encoding.vocabulary.values == ('A', 'B')
    assert model.encoding.train_support_students == {'A': 1, 'B': 1}


def test_selection_rejects_outside_learner_before_fit(tmp_path):
    outside = LearnerEvents('outer', 0, (KTEvent('outer', 'A', 1, 1, 1, 0, 0),))
    split = InnerSplit(('train',), ('val',), 0, 'split-hash')
    cfg = AKTConfig(output_dir=tmp_path, d_model=32, heads=4, d_ff=64, final_fc=32, dropout=0)
    with pytest.raises(ValueError, match='scope'):
        select_checkpoint(cfg, inner_split=split, train_learners_factory=lambda: iter([outside]),
                          val_learners_factory=lambda: iter([]), identity={}, budget={'max_steps': 1})


@pytest.mark.parametrize('fold', [-1, 5])
def test_scope_rejects_invalid_development_fold_ids(fold):
    learner = LearnerEvents('bad', fold,
                            (KTEvent('bad', 'A', 1, 1, 1, 0, fold),))
    with pytest.raises(ValueError, match='fold'):
        list(training_module._scoped(lambda: iter([learner]), ('bad',), outer_fold=4))


def test_scope_rejects_event_fold_mismatched_with_learner_fold():
    learner = LearnerEvents('mismatch', 2,
                            (KTEvent('mismatch', 'A', 1, 1, 1, 0, 3),))
    with pytest.raises(ValueError, match='fold'):
        list(training_module._scoped(lambda: iter([learner]), ('mismatch',), outer_fold=4))


@pytest.mark.parametrize('outer_fold', [-1, 5])
def test_scope_rejects_invalid_outer_fold_ids(outer_fold):
    learner = LearnerEvents('valid', 0,
                            (KTEvent('valid', 'A', 1, 1, 1, 0, 0),))
    with pytest.raises(ValueError, match='fold'):
        list(training_module._scoped(lambda: iter([learner]), ('valid',), outer_fold=outer_fold))


@pytest.mark.parametrize('fold', range(5))
def test_scope_accepts_valid_development_folds_when_not_outer(fold):
    outer_fold = (fold + 1) % 5
    learner = LearnerEvents('valid', fold,
                            (KTEvent('valid', 'A', 1, 1, 1, 0, fold),))
    assert list(training_module._scoped(lambda: iter([learner]), ('valid',), outer_fold=outer_fold)) == [learner]


def test_selection_requires_explicit_epoch_budget_and_rejects_protected_output(tmp_path):
    protected = tmp_path / 'artifacts/bkt_baseline/results'
    cfg = AKTConfig(project_root=tmp_path, output_dir=protected, d_model=32, heads=4,
                    d_ff=64, final_fc=32, dropout=0)
    split = InnerSplit(('train',), ('val',), 0, 'split-hash')
    learners = lambda: iter([])
    with pytest.raises(ValueError, match='protected'):
        select_checkpoint(cfg, inner_split=split, train_learners_factory=learners,
                          val_learners_factory=learners, identity={}, budget={'max_steps': 1})
    assert not protected.exists()

    cfg = replace(cfg, output_dir=tmp_path / 'safe')
    with pytest.raises(ValueError, match='budget'):
        select_checkpoint(cfg, inner_split=split, train_learners_factory=learners,
                          val_learners_factory=learners, identity={})
    assert not cfg.output_dir.exists()


def test_fixed_budget_is_explicit_and_writes_final_epoch_without_validation(tmp_path, monkeypatch):
    user = LearnerEvents('train', 1, (KTEvent('train', 'A', 1, 1, 1, 0, 1),))
    cfg = AKTConfig(output_dir=tmp_path, d_model=32, heads=4, d_ff=64, final_fc=32, dropout=0)
    epochs = []

    def fake_train(adapter, factory, *, optimizer, epoch, budget):
        epochs.append((epoch, dict(budget)))
        return EpochStats(1.0, 1, 1, True, {})

    monkeypatch.setattr(training_module, 'train_epoch', fake_train)
    adapter = fit_fixed_budget_outer_train(
        cfg, outer_train_users=('train',), train_learners_factory=lambda: iter([user]),
        epochs=3, identity={'run': 'fixed-synthetic'}, budget={'max_steps': 5})
    payload = load_checkpoint(
        tmp_path / 'fixed-budget-epoch-3.pt', expected_identity=adapter.run_identity, device='cpu')
    assert [epoch for epoch, _ in epochs] == [1, 2, 3]
    assert payload['progress']['epoch'] == 3
    assert payload['progress']['complete'] is True
    assert payload['progress']['sampler_seed'] == cfg.seed + 3
    assert adapter.completed_epochs == 3


def test_epoch_time_limit_stops_before_update(monkeypatch):
    user = LearnerEvents('u', 1, (KTEvent('u', 'A', 1, 1, 1, 0, 1),))
    enc = fit_vocabulary([user])
    cfg = AKTConfig(d_model=32, heads=4, d_ff=64, final_fc=32, dropout=0, batch_size=1)
    model = AKTAdapter(cfg, enc)
    optimizer = torch.optim.Adam(model.native.parameters())
    clock = iter([0.0, 2.0, 2.0, 2.0])
    progress = []
    monkeypatch.setattr(training_module.time, 'perf_counter', lambda: next(clock))
    result = train_epoch(model, lambda: iter_windows(user, enc, training=True),
                         optimizer=optimizer, epoch=1,
                         budget={'max_seconds': 1}, progress_callback=progress.append)
    assert not result.complete and result.optimizer_steps == 0
    assert result.stop_reason == 'time_budget'
    assert progress[-1]['complete_epoch'] is False
    assert progress[-1]['training']['windows_processed'] == 1
    assert progress[-1]['training']['processed_target_rows'] == 1
    assert progress[-1]['training']['optimized_target_rows'] == 0


def test_fixed_budget_refuses_incomplete_epoch(tmp_path, monkeypatch):
    user = LearnerEvents('u', 1, (KTEvent('u', 'A', 1, 1, 1, 0, 1),))
    cfg = AKTConfig(output_dir=tmp_path, d_model=32, heads=4, d_ff=64, final_fc=32, dropout=0)
    monkeypatch.setattr(training_module, 'train_epoch',
                        lambda *args, **kwargs: EpochStats(0, 0, 0, False, {}))
    with pytest.raises(RuntimeError, match='incomplete'):
        fit_fixed_budget_outer_train(cfg, outer_train_users=('u',), train_learners_factory=lambda: iter([user]),
                                     epochs=3, identity={}, budget={'max_seconds': 1})
    assert not list(tmp_path.glob('*.pt'))


def test_refit_reseeds_and_uses_fresh_model_and_optimizer(monkeypatch):
    users = [LearnerEvents('a', 1, (KTEvent('a', 'A', 1, 1, 1, 0, 1),)),
             LearnerEvents('b', 2, (KTEvent('b', 'B', 1, 2, 0, 0, 2),))]
    cfg = AKTConfig(d_model=32, heads=4, d_ff=64, final_fc=32, dropout=0)
    seen = []
    def fake_train(model, factory, *, optimizer, epoch, budget):
        seen.append((model, optimizer, random.random(), torch.rand(1).item()))
        return EpochStats(1, 1, 1, True, {})
    monkeypatch.setattr(training_module, 'train_epoch', fake_train)
    for _ in range(2):
        refit_outer_train(cfg, outer_train_users=('a', 'b'), train_learners_factory=lambda: iter(users),
                          selected_epochs=1, identity={}, budget={'max_steps': 1})
        random.random()
        torch.rand(1)
    assert seen[0][0] is not seen[1][0] and seen[0][1] is not seen[1][1]
    assert seen[0][2:] == seen[1][2:]


def test_outer_label_mutation_does_not_enter_inner_selection(tmp_path, monkeypatch):
    train = LearnerEvents('train', 1, (KTEvent('train', 'A', 1, 1, 1, 0, 1),))
    val = LearnerEvents('val', 2, (KTEvent('val', 'A', 1, 2, 0, 0, 2),))
    split = InnerSplit(('train',), ('val',), 0, 'split-hash')
    requests = []
    monkeypatch.setattr(training_module, 'train_epoch',
                        lambda *args, **kwargs: EpochStats(1, 1, 1, True, {}))
    monkeypatch.setattr(training_module, 'evaluate_inner', lambda *args: (0.5, {'predicted_rows': 1}))
    results = []
    for response in (0, 1):
        rows = {'train': train, 'val': val,
                'outer': LearnerEvents('outer', 0, (KTEvent('outer', 'X', 1, 3, response, 0, 0),))}
        def factory(users):
            requests.append(tuple(users))
            return iter(rows[user] for user in users)
        cfg = AKTConfig(output_dir=tmp_path / str(response), d_model=32, heads=4,
                        d_ff=64, final_fc=32, dropout=0, max_epochs=1)
        result = select_checkpoint(cfg, inner_split=split,
                                   train_learners_factory=lambda: factory(split.inner_train_users),
                                   val_learners_factory=lambda: factory(split.inner_val_users),
                                   identity={'run': 'synthetic'}, budget={'max_steps': 1})
        checkpoint = load_checkpoint(result.checkpoint, expected_identity={
            'run': 'synthetic', 'split_hash': split.split_hash,
            'encoding_hash': training_module._encoding_hash(fit_vocabulary([train]))}, device='cpu')
        results.append((result.selected_epoch, checkpoint['encoding']))
    assert results[0] == results[1]
    assert all('outer' not in users for users in requests)
