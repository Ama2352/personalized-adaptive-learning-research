from dataclasses import replace

import numpy as np
import pytest
import torch

from knowledge_tracing.akt.config import AKTConfig
from knowledge_tracing.akt.encoding import fit_vocabulary
from knowledge_tracing.akt.model import AKTAdapter
from knowledge_tracing.akt.tensors import collate_windows
from knowledge_tracing.akt.types import KTEvent, LearnerEvents, TrainingWindow
from knowledge_tracing.akt.windows import iter_windows


def example():
    events = tuple(KTEvent('u', e, i+1, i+1, r, 0, 0)
                   for i, (e, r) in enumerate(zip(['A', 'B', 'C'], [1, 0, 1])))
    learner = LearnerEvents('u', 0, events)
    enc = fit_vocabulary([learner])
    window = list(iter_windows(learner, enc, training=True))[0]
    assert isinstance(window, TrainingWindow)
    return enc, window


def adapter(enc):
    torch.manual_seed(42)
    cfg = AKTConfig(d_model=32, heads=4, d_ff=64, final_fc=32, dropout=0.0,
                    max_grad_norm=1e6)
    return AKTAdapter(cfg, enc)


def test_mean_gradient_equals_sum_divided_by_valid_count():
    enc, training = example()
    model = adapter(enc)
    batch = collate_windows([training.window], n_items=3, device='cpu', targets=[training.targets])
    model.native.train()
    loss, _, count = model.native(batch.q_data, batch.qa_data, batch.loss_targets)
    loss.backward()
    gradients = {name: p.grad.detach().clone() / count.item() for name, p in model.native.named_parameters()
                 if p.grad is not None}
    before = {name: p.detach().clone() for name, p in model.native.named_parameters()}
    optimizer = torch.optim.SGD(model.native.parameters(), lr=0.01)
    result = model.step(batch, optimizer)
    assert result['valid_targets'] == 3
    assert result['stepped'] is True
    assert abs(result['mean_loss'] - loss.item() / 3) < 1e-6
    for name, p in model.native.named_parameters():
        if name in gradients:
            torch.testing.assert_close(p, before[name] - 0.01 * gradients[name], atol=1e-6, rtol=1e-6)


def test_zero_valid_targets_does_not_step_optimizer():
    enc, training = example()
    model = adapter(enc)
    batch = collate_windows([training.window], n_items=3, device='cpu')
    optimizer = torch.optim.SGD(model.native.parameters(), lr=0.1)
    before = [p.detach().clone() for p in model.native.parameters()]
    result = model.step(batch, optimizer)
    assert result['stepped'] is False
    assert all(torch.equal(a, b) for a, b in zip(before, model.native.parameters()))


@pytest.mark.parametrize('invalid', [-0.5, float('nan')])
def test_step_rejects_invalid_target_sentinels(invalid):
    enc, training = example()
    model = adapter(enc)
    batch = collate_windows([training.window], n_items=3, device='cpu')
    batch.loss_targets[0, 0] = invalid
    optimizer = torch.optim.SGD(model.native.parameters(), lr=0.1)
    with pytest.raises(ValueError, match='target'):
        model.step(batch, optimizer)


def test_predict_preserves_order_unknown_and_training_mode():
    enc, training = example()
    model = adapter(enc)
    model.native.train()
    inputs = training.window.inputs
    with_oov = replace(inputs, item_ids=np.asarray([0, -1, 2], dtype=np.int64))
    predictions = model.predict(with_oov)
    assert predictions.shape == (3,)
    assert np.isnan(predictions[1])
    assert np.isfinite(predictions[[0, 2]]).all()
    assert model.native.training is True


def test_fit_uses_shared_inputs_and_changes_parameters():
    enc, training = example()
    model = adapter(enc)
    before = [p.detach().clone() for p in model.native.parameters()]
    assert model.fit(training.window.inputs, training.targets) is model
    assert any(not torch.equal(a, b) for a, b in zip(before, model.native.parameters()))


def test_fit_rejects_unknown_exercise_before_any_weight_update():
    enc, training = example()
    model = adapter(enc)
    model.config = replace(model.config, context=1, target_block=1, batch_size=1)
    inputs = replace(training.window.inputs, item_ids=np.asarray([0, 1, -1], dtype=np.int64))
    before = [p.detach().clone() for p in model.native.parameters()]
    with pytest.raises(ValueError, match='unseen'):
        model.fit(inputs, training.targets)
    assert all(torch.equal(a, b) for a, b in zip(before, model.native.parameters()))


def test_eval_repeats_while_native_train_dropout_changes_output():
    enc, training = example()
    cfg = AKTConfig(d_model=32, heads=4, d_ff=64, final_fc=32, dropout=0.5)
    torch.manual_seed(42)
    model = AKTAdapter(cfg, enc)
    first = model.predict(training.window.inputs)
    second = model.predict(training.window.inputs)
    np.testing.assert_allclose(first, second, rtol=1e-6, atol=1e-6)
    batch = collate_windows([training.window], n_items=3, device='cpu')
    model.native.train()
    p1 = model.native(batch.q_data, batch.qa_data, batch.loss_targets)[1]
    p2 = model.native(batch.q_data, batch.qa_data, batch.loss_targets)[1]
    assert not torch.equal(p1, p2)
