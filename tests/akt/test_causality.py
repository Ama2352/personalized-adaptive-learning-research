from dataclasses import replace

import numpy as np
import torch

from knowledge_tracing.akt.config import AKTConfig
from knowledge_tracing.akt.encoding import fit_vocabulary
from knowledge_tracing.akt.tensors import causal_masks, collate_windows
from knowledge_tracing.akt.types import KTEvent, LearnerEvents
from knowledge_tracing.akt.upstream import build_native
from knowledge_tracing.akt.windows import iter_windows


def learner(user, exercises, responses):
    return LearnerEvents(user, 0, tuple(KTEvent(user, e, i+1, i+1, r, 0, 0)
                                        for i, (e, r) in enumerate(zip(exercises, responses))))


def window(exercises, responses, user='u'):
    enc = fit_vocabulary([learner('train', ['A', 'B', 'C'], [0, 1, 0])])
    return list(iter_windows(learner(user, exercises, responses), enc, training=False))[0]


def model():
    torch.manual_seed(42)
    cfg = AKTConfig(d_model=32, heads=4, d_ff=64, final_fc=32, dropout=0.0)
    return build_native(cfg, n_items=3).eval()


def predict(m, *windows):
    batch = collate_windows(windows, n_items=3, device='cpu')
    _, out, _ = m(batch.q_data, batch.qa_data, batch.loss_targets)
    return out.reshape(batch.q_data.shape)


def test_reconstructs_aligned_interactions_without_double_shift():
    w = window(['A', 'B', 'C'], [1, 0, 1])
    assert w.inputs.prior_responses.tolist() == [-1, 1, 0]
    batch = collate_windows([w], n_items=3, device='cpu')
    assert batch.q_data.tolist() == [[1, 2, 3]]
    assert batch.qa_data.tolist() == [[4, 2, 3]]
    assert batch.loss_targets.tolist() == [[-1.0, -1.0, -1.0]]
    assert batch.valid_mask.tolist() == [[True, True, True]]


def test_current_and_future_response_do_not_change_own_or_earlier_prediction():
    m = model()
    a = window(['A', 'B', 'C'], [1, 0, 1])
    b = window(['A', 'B', 'C'], [1, 1, 0])
    pa, pb = predict(m, a), predict(m, b)
    torch.testing.assert_close(pa[:, :2], pb[:, :2], atol=1e-6, rtol=1e-6)
    c = window(['A', 'B', 'A'], [1, 1, 0])
    torch.testing.assert_close(pb[:, :2], predict(m, c)[:, :2], atol=1e-6, rtol=1e-6)


def test_past_response_has_detectable_effect_on_later_probability():
    m = model()
    a = window(['A', 'B', 'C'], [0, 0, 0])
    b = window(['A', 'B', 'C'], [1, 0, 0])
    pa, pb = predict(m, a), predict(m, b)
    torch.testing.assert_close(pa[:, 0], pb[:, 0], atol=1e-6, rtol=1e-6)
    assert abs((pa[0, 1] - pb[0, 1]).item()) > 1e-7


def test_right_padding_and_other_learner_do_not_change_predictions():
    m = model()
    short = window(['A', 'B'], [1, 0], user='short')
    long = window(['C', 'B', 'A'], [0, 1, 1], user='long')
    alone = predict(m, short)
    batch = collate_windows([short, long], n_items=3, device='cpu')
    assert batch.q_data[0].tolist() == [1, 2, 0]
    assert batch.qa_data[0].tolist() == [4, 2, 0]
    assert batch.valid_mask[0].tolist() == [True, True, False]
    torch.testing.assert_close(alone[0], predict(m, short, long)[0, :2], atol=1e-6, rtol=1e-6)
    batch.q_data[0, 2], batch.qa_data[0, 2] = 1, 4
    _, mutated, _ = m(batch.q_data, batch.qa_data, batch.loss_targets)
    torch.testing.assert_close(alone[0], mutated.reshape(2, 3)[0, :2], atol=1e-6, rtol=1e-6)


def test_single_target_prefix_matches_batched_retained_context():
    m = model()
    prefix = window(['A', 'B'], [1, 0])
    whole = window(['A', 'B', 'C'], [1, 0, 1])
    torch.testing.assert_close(predict(m, prefix)[0], predict(m, whole)[0, :2], atol=1e-6, rtol=1e-6)


def test_current_response_at_block_boundary_does_not_leak():
    m = model()
    enc = fit_vocabulary([learner('train', ['A', 'B', 'C'], [0, 1, 0])])
    exercises = ['A'] * 103
    responses = [0] * 103
    changed = responses.copy()
    changed[100] = 1
    first = list(iter_windows(learner('u', exercises, responses), enc, training=False))
    second = list(iter_windows(learner('u', exercises, changed), enc, training=False))
    a, b = predict(m, first[1]), predict(m, second[1])
    torch.testing.assert_close(a[0, 100], b[0, 100], atol=1e-6, rtol=1e-6)


def test_oov_response_does_not_cross_the_barrier():
    m = model()
    enc = fit_vocabulary([learner('train', ['A', 'B', 'C'], [0, 1, 0])])
    a = list(iter_windows(learner('u', ['A', 'X', 'B'], [1, 0, 1]), enc, training=False))
    b = list(iter_windows(learner('u', ['A', 'X', 'B'], [1, 1, 1]), enc, training=False))
    torch.testing.assert_close(predict(m, a[2]), predict(m, b[2]), atol=1e-6, rtol=1e-6)


def test_actual_attention_forbids_future_and_current_response():
    m = model()
    observed = []
    layers = [m.model.blocks_1[0], m.model.blocks_2[0], m.model.blocks_2[1]]
    handles = [layer.masked_attn_head.dropout.register_forward_hook(
        lambda _m, _i, output: observed.append(output.detach().clone())) for layer in layers]
    try:
        out = predict(m, window(['A', 'B', 'C'], [1, 0, 1]))
    finally:
        for handle in handles:
            handle.remove()
    encoder, strict = causal_masks(3, device='cpu')
    assert encoder.tolist() == [[True, False, False], [True, True, False], [True, True, True]]
    assert strict.tolist() == [[False, False, False], [True, False, False], [True, True, False]]
    assert torch.isfinite(out).all()
    for weights in observed[:2]:
        assert torch.all(weights[..., ~encoder] == 0)
    assert torch.all(observed[2][..., ~strict] == 0)


def test_current_response_activation_has_zero_gradient_for_current_prediction():
    m = model()
    activations = []
    def capture(_module, _inputs, output):
        output.retain_grad()
        activations.append(output)
    handle = m.qa_embed.register_forward_hook(capture)
    try:
        out = predict(m, window(['A', 'B', 'C'], [1, 0, 1]))
        out[0, 1].backward()
    finally:
        handle.remove()
    assert torch.count_nonzero(activations[0].grad[0, 1]).item() == 0
