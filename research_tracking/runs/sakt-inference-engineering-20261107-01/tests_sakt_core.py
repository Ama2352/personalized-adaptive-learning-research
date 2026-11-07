"""Forward/backward CPU synthetic; không optimizer, dữ liệu thật hay benchmark."""

from dataclasses import replace
import math

import numpy as np
import pytest
import torch
from torch.nn import functional as F

from knowledge_tracing.sakt import SAKTConfig, SAKTCore, SAKTInputs, collate_sequences
from knowledge_tracing.shared_kt import CausalSequenceInputs, StableVocabulary, build_causal_sequence_inputs


@pytest.fixture(autouse=True)
def bounded_cpu_rng():
    threads = torch.get_num_threads()
    torch.set_num_threads(1)
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(42)
        yield
    torch.set_num_threads(threads)


def model(**changes):
    # Chỉ smoke geometry, không phải cấu hình benchmark đã chọn.
    values = dict(num_items=6, max_length=12, d_model=8, num_heads=2,
                  head_dim=8, dropout=0.0, layer_norm_eps=1e-5)
    values.update(changes)
    return SAKTCore(SAKTConfig(**values)).eval()


def sequence(items=(0, 1, 2, 1, 4, 3), labels=(1, 0, 1, 0, 1, 0), user='u'):
    n = len(items)
    return CausalSequenceInputs(np.asarray(items, dtype=np.int64), np.arange(n),
                                np.asarray([-1, *labels[:-1]], dtype=np.int64),
                                np.arange(1, n + 1), np.asarray([0, n]), (user,) * n)


def collate(sequences, padding_side='right'):
    return collate_sequences(sequences, num_items=6, max_length=12,
                             padding_side=padding_side, device='cpu')


def test_current_and_future_responses_do_not_change_current_or_earlier_predictions():
    native = model()
    labels = [1, 0, 1, 0, 1, 0]
    original = native(collate([sequence(labels=labels)])).logits
    for target in range(len(labels)):
        changed = labels[:target] + [1 - value for value in labels[target:]]
        modified = native(collate([sequence(labels=changed)])).logits
        torch.testing.assert_close(modified[:, :target + 1], original[:, :target + 1], rtol=0, atol=1e-7)


def test_future_items_do_not_change_current_or_earlier_predictions():
    native = model()
    original = native(collate([sequence()])).logits
    items = [0, 1, 2, 1, 4, 3]
    for target in range(len(items)):
        changed = items[:target + 1] + [(value + 1) % 6 for value in items[target + 1:]]
        modified = native(collate([sequence(items=changed)])).logits
        torch.testing.assert_close(modified[:, :target + 1], original[:, :target + 1], rtol=0, atol=1e-7)


def test_history_response_and_current_item_have_observable_effects():
    native = model()
    original = native(collate([sequence()])).logits
    history_changed = native(collate([sequence(labels=(0, 0, 1, 0, 1, 0))])).logits
    item_changed = native(collate([sequence(items=(0, 1, 5, 1, 4, 3))])).logits
    torch.testing.assert_close(history_changed[:, 0], original[:, 0], rtol=0, atol=0)
    assert (history_changed[:, 1:] - original[:, 1:]).abs().max() > 1e-5
    torch.testing.assert_close(item_changed[:, :2], original[:, :2], rtol=0, atol=1e-7)
    assert (item_changed[:, 2] - original[:, 2]).abs().max() > 1e-5


def test_reordering_past_interactions_can_change_same_target_prediction():
    native = model()
    original = native(collate([sequence()])).logits
    # Đổi thứ tự hai interaction đầu, giữ nguyên multiset item-response và query cuối.
    reordered = sequence(items=(1, 0, 2, 1, 4, 3), labels=(0, 1, 1, 0, 1, 0))
    modified = native(collate([reordered])).logits
    assert (modified[:, -1] - original[:, -1]).abs().max() > 1e-5


def test_attention_has_strict_past_event_geometry_without_double_shift():
    output = model()(collate([sequence()]))
    attention = output.attention_weights[0]
    assert output.has_history.tolist() == [[False, True, True, True, True, True]]
    assert torch.count_nonzero(attention[:, 0]) == 0
    for target in range(1, 6):
        # Shifted slot 1 chứa event 0; slot target chứa event target-1.
        assert torch.count_nonzero(attention[:, target, 0]) == 0
        assert torch.count_nonzero(attention[:, target, target + 1:]) == 0
        assert torch.all(attention[:, target, target] > 0)
        torch.testing.assert_close(attention[:, target].sum(dim=-1), torch.ones(2))


@pytest.mark.parametrize('padding_side', ['left', 'right'])
def test_variable_length_batch_padding_and_permutation_preserve_predictions(padding_side):
    native = model()
    short = sequence(items=(2, 1, 3), labels=(0, 1, 0), user='a')
    long = sequence(user='b')
    batch = collate([short, long], padding_side)
    output = native(batch)
    permuted = native(collate([long, short], padding_side))
    for row, seq in enumerate((short, long)):
        solo = native(collate([seq], padding_side))
        torch.testing.assert_close(output.logits[row, batch.valid_mask[row]], solo.logits[0], rtol=0, atol=1e-6)
        torch.testing.assert_close(output.logits[row], permuted.logits[1 - row], rtol=0, atol=1e-6)
    assert torch.count_nonzero(output.probabilities[~batch.valid_mask]) == 0
    assert torch.isfinite(output.attention_weights).all()


def test_other_learner_responses_do_not_affect_batch_peer():
    native = model()
    original = native(collate([sequence(user='a'), sequence(user='b')])).logits
    modified = native(collate([sequence(user='a'), sequence(labels=(0, 1, 0, 1, 0, 1), user='b')])).logits
    torch.testing.assert_close(original[0], modified[0], rtol=0, atol=0)
    assert (original[1] - modified[1]).abs().max() > 1e-5


def test_first_target_and_all_padding_are_finite_with_zero_attention():
    native = model()
    batch = SAKTInputs(torch.tensor([[0, 0, 0], [0, 4, 0]]),
                       torch.full((2, 3), -1, dtype=torch.long),
                       torch.tensor([[False, False, False], [False, True, False]]))
    output = native(batch)
    for tensor in (output.logits, output.probabilities, output.attention_weights):
        assert torch.isfinite(tensor).all()
    assert torch.count_nonzero(output.attention_weights) == 0
    assert torch.count_nonzero(output.has_history) == 0
    assert 0 < output.probabilities[1, 1] < 1
    assert torch.count_nonzero(output.logits[0]) == 0
    # Padding embedding bị đổi mạnh vẫn không trở thành history hoặc query hợp lệ.
    with torch.no_grad():
        native.interaction_embedding.weight[0].fill_(1000)
        native.exercise_embedding.weight[0].fill_(-1000)
    torch.testing.assert_close(native(batch).logits, output.logits)


def test_backward_cannot_reach_current_or_future_interaction_activations():
    native = model()
    captured = []

    def retain(module, args, output):
        output.retain_grad()
        captured.append(output)

    hook = native.interaction_embedding.register_forward_hook(retain)
    try:
        output = native(collate([sequence()]))
        output.logits[0, 2].backward()
    finally:
        hook.remove()
    gradients = captured[0].grad
    assert torch.count_nonzero(gradients[:, 0]) == 0
    assert torch.count_nonzero(gradients[:, 3:]) == 0
    assert torch.count_nonzero(gradients[:, 1:3]) > 0
    assert torch.isfinite(gradients).all()


def test_padding_only_backward_is_finite_and_has_zero_gradients():
    native = model()
    batch = SAKTInputs(torch.zeros((2, 3), dtype=torch.long),
                       torch.full((2, 3), -1, dtype=torch.long),
                       torch.zeros((2, 3), dtype=torch.bool))
    output = native(batch)
    output.logits.sum().backward()
    gradients = [parameter.grad for parameter in native.parameters() if parameter.grad is not None]
    assert gradients
    assert all(torch.isfinite(gradient).all() and torch.count_nonzero(gradient) == 0
               for gradient in gradients)


@pytest.mark.parametrize('dropout', [0.0, 0.2])
def test_masked_synthetic_backward_is_finite_without_parameter_updates(dropout):
    native = model(dropout=dropout).train()
    batch = collate([sequence(), sequence(items=(1,), labels=(0,), user='cold')])
    before = {key: value.detach().clone() for key, value in native.state_dict().items()}
    output = native(batch)
    labels = torch.zeros_like(output.logits)
    labels[0] = torch.tensor([1., 0., 1., 0., 1., 0.])
    loss = F.binary_cross_entropy_with_logits(output.logits[batch.valid_mask], labels[batch.valid_mask])
    loss.backward()
    assert torch.isfinite(loss)
    gradients = [parameter.grad for parameter in native.parameters() if parameter.grad is not None]
    assert gradients and all(torch.isfinite(gradient).all() for gradient in gradients)
    assert any(torch.count_nonzero(gradient) > 0 for gradient in gradients)
    for key, value in native.state_dict().items():
        assert torch.equal(value, before[key])


def test_one_history_event_matches_independent_paper_equation_calculation():
    native = model(d_model=2, num_heads=1, head_dim=2, layer_norm_eps=1e-6)
    with torch.no_grad():
        for parameter in native.parameters():
            parameter.zero_()
        native.interaction_embedding.weight[1] = torch.tensor([1., 3.])
        native.value_projection.weight.copy_(torch.eye(2))
        native.output_projection.weight.copy_(torch.eye(2))
        native.attention_norm.weight.fill_(1)
        native.feedforward_norm.weight.fill_(1)
        native.prediction.weight[0, 0] = 1
    output = native(collate([sequence(items=(0, 1), labels=(0, 1))]))
    # Một past value=(1,3); LN lần đầu cho (-a,a), lần hai cho (-b,b).
    a = 1 / math.sqrt(1 + 1e-6)
    b = a / math.sqrt(a * a + 1e-6)
    assert output.logits[0, 1].item() == pytest.approx(-b, abs=1e-6)
    assert output.probabilities[0, 1].item() == pytest.approx(1 / (1 + math.exp(b)), abs=1e-6)
    assert output.attention_weights[0, 0, 1].tolist() == [0., 1.]


def test_shared_sequence_contract_is_used_without_targets_or_reordering():
    rows = [dict(user_id='u', exercise_id=item, time_done=t, source_row=t, correct=label)
            for t, (item, label) in enumerate((('b', 1), ('a', 0), ('c', 1)), start=1)]
    vocab = StableVocabulary.from_values(['a', 'b', 'c'])
    inputs, labels = build_causal_sequence_inputs(rows, item_vocabulary=vocab)
    batch = collate_sequences([inputs], num_items=3, max_length=3, padding_side='left', device='cpu')
    assert labels.tolist() == [1, 0, 1]
    assert batch.item_ids.tolist() == [[2, 1, 3]]
    assert batch.prior_responses.tolist() == [[-1, 1, 0]]
    assert batch.valid_mask.all()


@pytest.mark.parametrize(('field', 'value'), [
    ('num_items', 0), ('max_length', -1), ('d_model', True), ('num_heads', 0),
    ('head_dim', 1.5), ('dropout', float('nan')), ('dropout', 1),
    ('layer_norm_eps', 0), ('layer_norm_eps', float('inf')),
])
def test_config_rejects_invalid_or_implicit_dimensions(field, value):
    with pytest.raises(ValueError):
        model(**{field: value})


@pytest.mark.parametrize('invalid', ['unknown', 'mask', 'first_response', 'binary', 'gap', 'dtype', 'overlength'])
def test_core_rejects_invalid_inputs(invalid):
    native = model(max_length=6)
    batch = collate([sequence()])
    if invalid == 'unknown':
        batch.item_ids[0, 2] = 7
    elif invalid == 'mask':
        batch.valid_mask[0, 2] = False
    elif invalid == 'first_response':
        batch.prior_responses[0, 0] = 0
    elif invalid == 'binary':
        batch.prior_responses[0, 2] = 2
    elif invalid == 'gap':
        batch.item_ids[0, 2] = 0
        batch.valid_mask[0, 2] = False
        batch.prior_responses[0, 2] = -1
    elif invalid == 'dtype':
        batch = replace(batch, prior_responses=batch.prior_responses.float())
    elif invalid == 'overlength':
        native = model(max_length=5)
    with pytest.raises(ValueError):
        native(batch)


@pytest.mark.parametrize('invalid', ['unknown', 'fractional', 'unshifted', 'multi_learner', 'overlength', 'empty'])
def test_collator_refuses_oov_implicit_context_or_bad_sequence(invalid):
    inputs = sequence()
    if invalid == 'unknown':
        inputs = replace(inputs, item_ids=np.asarray([-1, 1, 2, 1, 4, 3]))
    elif invalid == 'fractional':
        inputs = replace(inputs, item_ids=inputs.item_ids.astype(float))
    elif invalid == 'unshifted':
        inputs = replace(inputs, prior_responses=np.asarray([1, 0, 1, 0, 1, 0]))
    elif invalid == 'multi_learner':
        inputs = replace(inputs, sequence_offsets=np.asarray([0, 3, 6]), user_ids=('a',) * 3 + ('b',) * 3)
    elif invalid == 'empty':
        inputs = replace(inputs, item_ids=np.asarray([], dtype=np.int64))
    with pytest.raises(ValueError):
        collate_sequences([inputs], num_items=6, max_length=5 if invalid == 'overlength' else 12,
                          padding_side='right', device='cpu')
