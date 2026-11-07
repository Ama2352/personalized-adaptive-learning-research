"""Known-answer CPU kernel tests; 0 optimizer, no recurrence/fitted efficacy."""

from dataclasses import replace
import inspect

import pytest
import torch

from knowledge_tracing.gkt import GKTBinding, GKTKernelConfig, StaticGKTKernel, dense_adjacency


DTYPE = torch.float64


@pytest.fixture(autouse=True)
def bounded_cpu():
    threads = torch.get_num_threads()
    torch.set_num_threads(1)
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(42)
        yield
    torch.set_num_threads(threads)


def config(**changes):
    values = dict(num_nodes=3, state_dim=2, embedding_dim=1, message_dim=1,
                  adjacency_kind='static', node_unit='concept',
                  require_zero_diagonal=True, require_nonnegative=True)
    values.update(changes)
    return GKTKernelConfig(**values)


def binding():
    return GKTBinding('synthetic-kernel-fixture', 'a' * 64, ('A', 'B', 'C'), 'concept')


def kernel(adjacency=None, **changes):
    if adjacency is None:
        adjacency = torch.tensor([[0, .2, 0], [.7, 0, .4], [0, .3, 0]], dtype=DTYPE)
    return StaticGKTKernel(config(**changes), binding(), adjacency)


def bound(k):
    return dict(binding=k.binding, graph_sha256=k.adjacency_sha256)


def test_asymmetric_incoming_outgoing_known_answer():
    k = kernel()
    result = k.combine_messages(torch.tensor([1]), torch.tensor([[5.]], dtype=DTYPE),
                                torch.tensor([[[10.], [20.], [30.]]], dtype=DTYPE),
                                torch.tensor([[[100.], [200.], [300.]]], dtype=DTYPE), **bound(k))
    torch.testing.assert_close(result.values, torch.tensor([[[27.], [5.], [102.]]], dtype=DTYPE))
    assert result.support_mask.tolist() == [[True, True, True]]


def test_aggregate_preserves_neighbor_embeddings_and_pairs_answered_concept_response():
    k = kernel()
    state = torch.arange(12, dtype=DTYPE).reshape(2, 3, 2)
    ec = torch.tensor([[10.], [11.], [12.]], dtype=DTYPE)
    ex = torch.arange(20, 26, dtype=DTYPE).reshape(6, 1)
    actual = k.aggregate_after_observation(state, torch.tensor([1, 2]), torch.tensor([0, 1]), ec, ex, **bound(k))
    torch.testing.assert_close(actual[..., :2], state)
    assert actual[..., 2].tolist() == [[10., 21., 12.], [10., 11., 25.]]


def test_readout_known_answer_has_no_current_answer_argument():
    k = kernel()
    state = torch.tensor([[[1., 2.], [3., 4.], [5., 6.]]], dtype=DTYPE)
    result = k.readout(state, torch.tensor([1]), torch.tensor([2., -1.], dtype=DTYPE),
                       torch.tensor([0., .5, 0.], dtype=DTYPE), **bound(k))
    torch.testing.assert_close(result.logits, torch.tensor([2.5], dtype=DTYPE))
    torch.testing.assert_close(result.probabilities, torch.sigmoid(torch.tensor([2.5], dtype=DTYPE)))
    assert 'response' not in ' '.join(inspect.signature(k.readout).parameters)
    assert result.evidence_role == 'caller_tensor_kernel_no_fit_attestation'
    with pytest.raises(TypeError):
        k.readout(state, torch.tensor([1]), torch.zeros(2, dtype=DTYPE), torch.zeros(3, dtype=DTYPE),
                  responses=torch.tensor([1]), **bound(k))


@pytest.mark.parametrize('nodes', [2, 3, 5])
def test_dense_exact_formula_and_row_mass(nodes):
    a = dense_adjacency(nodes, dtype=DTYPE)
    assert torch.equal(a.diagonal(), torch.zeros(nodes, dtype=DTYPE))
    assert torch.all(a[~torch.eye(nodes, dtype=torch.bool)] == 1 / (nodes - 1))
    torch.testing.assert_close(a.sum(1), torch.ones(nodes, dtype=DTYPE))


def test_dense_constructor_rejects_nonformula_without_normalizing():
    a = dense_adjacency(3, dtype=DTYPE)
    k = kernel(a, adjacency_kind='dense')
    assert k.config.adjacency_kind == 'dense'
    a[0, 1] = .6
    with pytest.raises(ValueError, match='formula'):
        kernel(a, adjacency_kind='dense')


@pytest.mark.parametrize('n', [0, 1, -1, True])
def test_dense_undefined_geometry_rejected(n):
    with pytest.raises(ValueError):
        dense_adjacency(n, dtype=DTYPE)


@pytest.mark.parametrize('kind', ['empty', 'one_direction'])
def test_disconnected_messages_zero_support_is_not_recurrent_update(kind):
    a = torch.zeros((3, 3), dtype=DTYPE)
    if kind == 'one_direction':
        a[0, 1] = .8
    k = kernel(a)
    out = k.combine_messages(torch.tensor([0]), torch.tensor([[2.]], dtype=DTYPE),
                              torch.ones((1, 3, 1), dtype=DTYPE),
                              torch.ones((1, 3, 1), dtype=DTYPE) * 3, **bound(k))
    expected = [2., .8 if kind == 'one_direction' else 0., 0.]
    torch.testing.assert_close(out.values[0, :, 0], torch.tensor(expected, dtype=DTYPE))
    assert out.support_mask.tolist() == [[True, kind == 'one_direction', False]]
    assert not hasattr(k, 'observe') and not hasattr(k, 'fit')


def test_arithmetic_batch_independence_for_all_three_operations():
    k = kernel()
    h = torch.randn(2, 3, 2, dtype=DTYPE)
    ids, responses = torch.tensor([0, 2]), torch.tensor([0, 1])
    ec, ex = torch.randn(3, 1, dtype=DTYPE), torch.randn(6, 1, dtype=DTYPE)
    self_m = torch.randn(2, 1, dtype=DTYPE)
    out_m, in_m = torch.randn(2, 3, 1, dtype=DTYPE), torch.randn(2, 3, 1, dtype=DTYPE)
    w, bias = torch.randn(2, dtype=DTYPE), torch.randn(3, dtype=DTYPE)
    aggregate = k.aggregate_after_observation(h, ids, responses, ec, ex, **bound(k))
    messages = k.combine_messages(ids, self_m, out_m, in_m, **bound(k))
    scores = k.readout(h, ids, w, bias, **bound(k))
    for i in range(2):
        s = slice(i, i + 1)
        torch.testing.assert_close(aggregate[s], k.aggregate_after_observation(h[s], ids[s], responses[s], ec, ex, **bound(k)))
        torch.testing.assert_close(messages.values[s], k.combine_messages(ids[s], self_m[s], out_m[s], in_m[s], **bound(k)).values)
        torch.testing.assert_close(scores.logits[s], k.readout(h[s], ids[s], w, bias, **bound(k)).logits)
    h[1] += 999
    torch.testing.assert_close(scores.logits[:1], k.readout(h, ids, w, bias, **bound(k)).logits[:1])


def test_finite_gradients_to_caller_tensors_no_optimizer():
    k = kernel()
    h = torch.randn(2, 3, 2, dtype=DTYPE, requires_grad=True)
    ec = torch.randn(3, 1, dtype=DTYPE, requires_grad=True)
    ex = torch.randn(6, 1, dtype=DTYPE, requires_grad=True)
    w = torch.randn(2, dtype=DTYPE, requires_grad=True)
    bias = torch.randn(3, dtype=DTYPE, requires_grad=True)
    ids = torch.tensor([0, 1])
    z = k.aggregate_after_observation(h, ids, torch.tensor([0, 1]), ec, ex, **bound(k))
    # Toy caller transforms for gradient arithmetic, not a selected GKT MLP.
    self_m = z[torch.arange(2), ids].sum(-1, keepdim=True)
    out_m, in_m = z.sum(-1, keepdim=True), z.square().sum(-1, keepdim=True)
    msg = k.combine_messages(ids, self_m, out_m, in_m, **bound(k))
    score = k.readout(h, ids, w, bias, **bound(k))
    (msg.values.sum() + score.probabilities.sum()).backward()
    for tensor in (h, ec, ex, w, bias):
        assert tensor.grad is not None and torch.isfinite(tensor.grad).all()
        assert tensor.grad.abs().sum() > 0


def test_inputs_and_graph_copy_immutable():
    a = dense_adjacency(3, dtype=DTYPE)
    k = kernel(a)
    h, ec, ex = torch.randn(1, 3, 2, dtype=DTYPE), torch.randn(3, 1, dtype=DTYPE), torch.randn(6, 1, dtype=DTYPE)
    ids, responses = torch.tensor([1]), torch.tensor([1])
    before = [x.clone() for x in (a, h, ec, ex, ids, responses)]
    k.aggregate_after_observation(h, ids, responses, ec, ex, **bound(k))
    k.readout(h, ids, torch.ones(2, dtype=DTYPE), torch.zeros(3, dtype=DTYPE), **bound(k))
    for old, new in zip(before, (a, h, ec, ex, ids, responses)):
        assert torch.equal(old, new)
    sha = k.adjacency_sha256
    a.zero_()
    assert sha == k.adjacency_sha256
    out = k.combine_messages(ids, torch.zeros(1, 1, dtype=DTYPE), torch.ones(1, 3, 1, dtype=DTYPE),
                              torch.zeros(1, 3, 1, dtype=DTYPE), **bound(k))
    assert out.values[0, 0, 0] == .5


@pytest.mark.parametrize('change', ['domain', 'vocabulary', 'node_order', 'node_unit', 'graph'])
def test_binding_rejection(change):
    k = kernel()
    b, sha = k.binding, k.adjacency_sha256
    if change == 'domain': b = replace(b, domain='other-domain')
    if change == 'vocabulary': b = replace(b, vocabulary_sha256='b' * 64)
    if change == 'node_order': b = replace(b, node_ids=('B', 'A', 'C'))
    if change == 'node_unit': b = replace(b, node_unit='exercise_tag')
    if change == 'graph': sha = '0' * 64
    with pytest.raises(ValueError, match='binding'):
        k.readout(torch.zeros(1, 3, 2, dtype=DTYPE), torch.tensor([0]), torch.zeros(2, dtype=DTYPE),
                  torch.zeros(3, dtype=DTYPE), binding=b, graph_sha256=sha)


@pytest.mark.parametrize('change', ['negative', 'self_edge', 'nonfinite', 'requires_grad', 'shape'])
def test_bad_adjacency(change):
    a = dense_adjacency(3, dtype=DTYPE)
    if change == 'negative': a[0, 1] = -.1
    if change == 'self_edge': a[0, 0] = .1
    if change == 'nonfinite': a[0, 1] = float('nan')
    if change == 'requires_grad': a.requires_grad_(True)
    if change == 'shape': a = a[:2]
    with pytest.raises(ValueError): kernel(a)


@pytest.mark.parametrize('change', [dict(num_nodes=True), dict(state_dim=0), dict(embedding_dim=-1),
                                    dict(message_dim=1.5), dict(adjacency_kind='PAM'),
                                    dict(node_unit='item84-with-difficulty'),
                                    dict(require_zero_diagonal=False), dict(require_nonnegative=False)])
def test_unsupported_config(change):
    with pytest.raises(ValueError): config(**change)


@pytest.mark.parametrize('ids', [torch.tensor([-1]), torch.tensor([3]), torch.tensor([0.]), torch.tensor([0, 1])])
def test_oov_padding_or_invalid_ids_reject_without_score(ids):
    k = kernel()
    with pytest.raises(ValueError):
        k.readout(torch.zeros(1, 3, 2, dtype=DTYPE), ids, torch.zeros(2, dtype=DTYPE), torch.zeros(3, dtype=DTYPE), **bound(k))


@pytest.mark.parametrize('response', [-1, 2])
def test_invalid_observed_response(response):
    k = kernel()
    with pytest.raises(ValueError):
        k.aggregate_after_observation(torch.zeros(1, 3, 2, dtype=DTYPE), torch.tensor([0]),
                                      torch.tensor([response]), torch.zeros(3, 1, dtype=DTYPE),
                                      torch.zeros(6, 1, dtype=DTYPE), **bound(k))


def test_nonfinite_readout_and_mismatched_dtype_rejected():
    k = kernel()
    for w in (torch.tensor([float('inf'), 0.], dtype=DTYPE), torch.zeros(2, dtype=torch.float32)):
        with pytest.raises(ValueError):
            k.readout(torch.zeros(1, 3, 2, dtype=DTYPE), torch.tensor([0]), w, torch.zeros(3, dtype=DTYPE), **bound(k))


def test_binding_node_order_digest_and_constructor_geometry():
    b = binding()
    assert b.node_order_sha256 != replace(b, node_ids=('B', 'A', 'C')).node_order_sha256
    with pytest.raises(ValueError): GKTBinding('x', 'bad', ('A',), 'concept')
    with pytest.raises(ValueError): GKTBinding('x', 'a' * 64, ('A', 'A'), 'concept')
    with pytest.raises(ValueError): StaticGKTKernel(config(), replace(b, node_ids=('A',)), dense_adjacency(3, dtype=DTYPE))


def test_graph_mutation_detected_and_output_does_not_become_state():
    k = kernel()
    k._adjacency[0, 1] += .1
    with pytest.raises(ValueError, match='changed'):
        k.readout(torch.zeros(1, 3, 2, dtype=DTYPE), torch.tensor([0]), torch.zeros(2, dtype=DTYPE), torch.zeros(3, dtype=DTYPE), **bound(k))
