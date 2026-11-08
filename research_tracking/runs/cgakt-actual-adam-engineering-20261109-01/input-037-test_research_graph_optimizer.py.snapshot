"""GRAPH10: một A3/Adam thật, ba batch fixture; không fitted/corpus/checkpoint.

ROOT phải cấp bounded worker riêng. Proposal:3Architecture.forward/3logical
backward/3clip bodies/3Adam steps,18targets nếu mask thực xác nhận6/batch.
Không thêm inference/control model hoặc dùng case fixture8forwards của module cũ.
ACTUAL_ADAM_LEDGER chỉ là diagnostics live để ROOT export sau pytest, không
checkpoint, chứng nhận provenance, hoặc file publication từ test.
"""
from dataclasses import fields, replace
import math
import time

import torch

from knowledge_tracing.akt import research_graph_model as model
import test_research_graph_model as core_fixture

ACTUAL_ADAM_LEDGER = []
ACTUAL_ADAM_ATTEMPTS = []
ACTUAL_ADAM_RESERVATION = {}
PLANNED_INVENTORY = dict(adapter_constructors=1, backbone_constructors=1, wrapper_constructors=1,
    gate_constructors=1, adam_constructors=1, architecture_forwards=3,
    logical_backwards=3, clip_calls=3, adam_steps=3, target_rows=18)


def state_snapshot(optimizer, named):
    """Giữ tensors tạm trong test; không serialize hoặc dùng làm resume state."""
    return {name: None if parameter not in optimizer.state else {
        key: value.detach().clone() if isinstance(value, torch.Tensor) else value
        for key, value in optimizer.state[parameter].items()}
        for name, parameter in named.items()}


def state_step(state):
    if state is None:
        return None
    step = state['step']
    assert type(step) is torch.Tensor and step.device.type == 'cpu' and step.numel() == 1
    value = float(step.item())
    assert math.isfinite(value) and value >= 1 and value.is_integer()
    return int(value)


def live_gradient_metadata(named):
    rows = {}
    for name, parameter in named.items():
        gradient = parameter.grad
        if gradient is None:
            rows[name] = dict(kind='none', finite=True, l2=None)
        else:
            assert gradient.device.type == 'cpu' and gradient.shape == parameter.shape
            finite = bool(torch.isfinite(gradient).all())
            rows[name] = dict(kind='nonzero' if bool(torch.any(gradient != 0)) else 'zero',
                              finite=finite, l2=float(torch.linalg.vector_norm(gradient.detach().double().reshape(-1)).item()))
    return rows


def test_owned_adam_inactive_then_two_active_steps_have_live_updates_and_participation(monkeypatch):
    assert ACTUAL_ADAM_LEDGER == []  # Fresh ROOT process, not a hidden warm retry.
    assert ACTUAL_ADAM_ATTEMPTS == [] and ACTUAL_ADAM_RESERVATION == {}
    assert core_fixture.model is model and core_fixture.context is model.contexts
    fixture = core_fixture.handmade()  # Normal cached module; no reload/duplicate class namespace.
    original_config = fixture['config']
    config = replace(original_config, max_steps=3)
    assert {field.name for field in fields(config)
            if getattr(config, field.name) != getattr(original_config, field.name)} == {'max_steps'}
    assert config.d_model == 256 and config.context == config.target_block == 100 and config.dropout == .05
    assert config.max_seconds == 60. and config.max_steps == 3
    entries = (fixture['entries'][1], fixture['entries'][0], fixture['entries'][0])
    assert entries[0].window.window_id != entries[1].window.window_id == entries[2].window.window_id
    assert fixture['index'].condition_sha256 == fixture['condition'].identity
    assert fixture['index'].encoding_sha256 == fixture['encoding'].identity
    assert fixture['index'].neural_binding.phase_scope == 'select_train80'
    assert fixture['encoding'].domain_sha256 == fixture['condition'].train80.domain_sha256
    precheck = fixture['index'].for_windows(tuple(entry.window for entry in entries[:2]))
    for entry, evidence, expected_mass in zip(entries[:2], precheck, (False, True)):
        assert entry.window.inputs.item_ids.shape == entry.targets.shape == (6,)
        assert int(entry.window.target_mask.sum()) == 6 and set(entry.targets.tolist()) <= {0, 1}
        assert any(item is not None and any(p.support > 0 and p.confidence > 0 for p in item.audit.parents)
                   for item in evidence) is expected_mass
    ACTUAL_ADAM_RESERVATION.update(kind='SYNTHETIC_ADAM_ENGINEERING_NOT_RESEARCH_FIT',
        planned_steps=3, planned_targets=18, adapter_step_wrapper_returns=None, rollback=False,
        native_work_seconds_cap=config.max_seconds, planned_inventory=PLANNED_INVENTORY.copy())
    clip_observations = []
    total_targets = 0

    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(42)
        native_started = time.perf_counter()
        adapter = model.ResearchGraphAKTAdapter(config=config, encoding=fixture['encoding'],
            index=fixture['index'], condition=fixture['condition'])
        adapter.native.train()
        named = dict(adapter.native.named_parameters())
        graph_names = ('alpha', 'gate.weight', 'gate.bias')
        assert all(name in named for name in graph_names) and any(name.startswith('backbone.') for name in named)
        assert named['alpha'].item() == 0. and all(torch.count_nonzero(named[name]) == 0 for name in graph_names[1:])
        optimizer = torch.optim.Adam(adapter.native.parameters(), lr=config.lr, betas=config.betas,
            eps=config.eps, weight_decay=config.weight_decay, amsgrad=False, foreach=False,
            maximize=False, capturable=False, differentiable=False, fused=False, decoupled_weight_decay=False)
        assert type(optimizer) is torch.optim.Adam and not optimizer.state
        owned = tuple(p for group in optimizer.param_groups for p in group['params'])
        assert len(owned) == len(named) and len({id(p) for p in owned}) == len(owned)
        assert {id(p) for p in owned} == {id(p) for p in named.values()}
        original_clip = torch.nn.utils.clip_grad_norm_

        def observe_actual_clip(parameters, max_norm, *args, **kwargs):
            actual = tuple(parameters)
            assert tuple(id(p) for p in actual) == tuple(id(p) for p in named.values())
            assert max_norm == config.max_grad_norm and kwargs.get('error_if_nonfinite') is True
            before = live_gradient_metadata(named)
            pre_norm = original_clip(actual, max_norm, *args, **kwargs)  # Exactly one REAL clip body.
            after = live_gradient_metadata(named)
            # Recompute the norm from LIVE post-clip grads; do not reuse the
            # primitive's derived min(pre,max) diagnostic as measured post norm.
            squares = [torch.sum(p.grad.detach().double().square()) for p in actual if p.grad is not None]
            assert squares
            post_norm = float(torch.sqrt(torch.stack(squares).sum()).item())
            clip_observations.append(dict(pre_norm=float(pre_norm.item()), live_post_norm=post_norm,
                gradients_before_clip=before, gradients_after_clip=after))
            return pre_norm

        monkeypatch.setattr(torch.nn.utils, 'clip_grad_norm_', observe_actual_clip)
        adapter.audit_context_boundary()
        for ordinal, entry in enumerate(entries):
            phase = ('inactive_first', 'active_alpha0', 'active_after_alpha_update')[ordinal]
            weights_before = {name: p.detach().clone() for name, p in named.items()}
            optimizer_before = state_snapshot(optimizer, named)
            batch = adapter.collate_training((entry,))
            actual_targets = int((batch.loss_targets >= 0).sum().item())
            assert batch.q_data.shape == (1, 6) and actual_targets == 6
            assert actual_targets == int((batch.target_mask & batch.valid_mask).sum().item())
            evidence = adapter._ticket.context[0]
            has_mass = any(item is not None and any(p.support > 0 and p.confidence > 0 for p in item.audit.parents)
                           for item in evidence)
            assert has_mass is (ordinal != 0)
            assert time.perf_counter()-native_started < config.max_seconds
            attempt = dict(ordinal=ordinal+1, targets_reserved=actual_targets,
                status='STARTED_BODY_RETURN_UNKNOWN', rollback=False)
            ACTUAL_ADAM_ATTEMPTS.append(attempt)
            try:
                stats = adapter.step(batch, optimizer)  # Actual frozen public primitive, no stub.
            except BaseException as error:
                attempt.update(status='STEP_WRAPPER_RAISED_POSSIBLE_PARTIAL_UPDATE', error_type=type(error).__name__)
                raise
            attempt['status'] = 'STEP_WRAPPER_RETURNED'
            gradients = live_gradient_metadata(named)
            optimizer_after = state_snapshot(optimizer, named)
            changes = {name: not torch.equal(weights_before[name], p.detach()) for name, p in named.items()}
            total_targets += actual_targets
            row = dict(role='synthetic_optimizer_engineering_not_fitted', ordinal=ordinal+1, phase=phase,
                valid_targets=actual_targets, total_targets=total_targets, stats=stats,
                gradients=gradients, state_step_before={name: state_step(value) for name, value in optimizer_before.items()},
                state_step_after={name: state_step(value) for name, value in optimizer_after.items()},
                parameter_changed=changes, clip=clip_observations[-1] if clip_observations else None)
            ACTUAL_ADAM_LEDGER.append(row)  # Preserve actual partial diagnostics before assertions.
            assert stats['stepped'] is True and stats['valid_targets'] == actual_targets and stats['parameter_updated'] is True
            assert all(math.isfinite(stats[key]) for key in ('loss_sum','mean_loss','pre_clip_norm','post_clip_norm'))
            assert all(math.isfinite(stats[key]) and stats[key] >= 0 for key in
                       ('forward_seconds','backward_seconds','gradient_clip_seconds','optimizer_seconds'))
            assert len(clip_observations) == ordinal+1
            clip = clip_observations[-1]
            assert math.isfinite(clip['pre_norm']) and math.isfinite(clip['live_post_norm'])
            assert clip['live_post_norm'] <= config.max_grad_norm*(1+1e-5)+1e-8
            assert clip['pre_norm'] == stats['pre_clip_norm']  # No assertion that pre_norm must exceed1.
            assert any(changed for name, changed in changes.items() if name.startswith('backbone.'))
            assert all(torch.isfinite(p).all() and p.device.type == 'cpu' for p in named.values())
            for name, parameter in named.items():
                previous, current = optimizer_before[name], optimizer_after[name]
                assert gradients[name]['finite']
                if parameter.grad is None:
                    assert state_step(current) == state_step(previous) and not changes[name]
                    if previous is not None:
                        assert current.keys() == previous.keys()
                        assert all(torch.equal(current[key], previous[key]) for key in previous)
                else:
                    assert current is not None and set(current) == {'step','exp_avg','exp_avg_sq'}
                    assert state_step(current) == (state_step(previous) or 0)+1
                    assert all(type(value) is torch.Tensor and value.device.type == 'cpu' and torch.isfinite(value).all()
                               for value in current.values())
                    assert current['exp_avg'].shape == current['exp_avg_sq'].shape == parameter.shape
                    assert torch.all(current['exp_avg_sq'] >= 0)
            if ordinal == 0:
                assert all(gradients[name]['kind'] == 'none' and optimizer_after[name] is None
                           and not changes[name] for name in graph_names)
                assert named['alpha'].item() == 0.
            elif ordinal == 1:
                assert gradients['alpha']['kind'] == 'nonzero' and changes['alpha'] and named['alpha'].item() != 0.
                assert all(gradients[name]['kind'] == 'zero' and not changes[name] for name in graph_names[1:])
                assert all(state_step(optimizer_after[name]) == 1 for name in graph_names)
            else:
                assert all(gradients[name]['kind'] == 'nonzero' and changes[name] for name in graph_names[1:])
                assert all(state_step(optimizer_after[name]) == 2 for name in graph_names)
            assert adapter.native._call is None and adapter._ticket is None and not adapter._failed
            assert time.perf_counter()-native_started < config.max_seconds
        adapter.audit_context_boundary()
        assert total_targets == 18 and len(ACTUAL_ADAM_LEDGER) == len(clip_observations) == 3
        assert len(ACTUAL_ADAM_ATTEMPTS) == 3 and all(row['status'] == 'STEP_WRAPPER_RETURNED' for row in ACTUAL_ADAM_ATTEMPTS)
        assert time.perf_counter()-native_started < config.max_seconds
        ACTUAL_ADAM_RESERVATION['adapter_step_wrapper_returns'] = 3
        # State step3 applies ONLY to parameters whose actual grads participated
        # all3 times. Do not impose universal backbone/all-parameter participation.
        for name in named:
            if all(row['gradients'][name]['kind'] != 'none' for row in ACTUAL_ADAM_LEDGER):
                assert ACTUAL_ADAM_LEDGER[-1]['state_step_after'][name] == 3
