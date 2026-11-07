import importlib.util
from pathlib import Path
import sys

import torch

from knowledge_tracing.akt.config import AKTConfig, SOURCE_COMMIT
from knowledge_tracing.akt.provenance import verify_upstream
from knowledge_tracing.akt.upstream import build_native, load_upstream


ROOT = Path('artifacts/akt/dependencies/upstream')


def config():
    return AKTConfig(source_root=ROOT, d_model=32, heads=4, d_ff=64,
                     final_fc=32, dropout=0.0)


def original_module():
    spec = importlib.util.spec_from_file_location('independent_akt_reference', ROOT / 'akt.py')
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    module.device = torch.device('cpu')
    return module


def forward_with_logits(model, q, qa, targets):
    logits = []
    handle = model.out.register_forward_hook(lambda _m, _i, out: logits.append(out))
    try:
        loss, probs, count = model(q, qa, targets)
    finally:
        handle.remove()
    return loss, probs, count, logits[0]


def test_wrapper_matches_reference_probabilities_sum_loss_and_gradients():
    module = original_module()
    torch.manual_seed(42)
    reference = module.AKT(2, 0, 32, 1, 1, 0.0, 'akt', 32, 4, 64)
    candidate = build_native(config(), n_items=2)
    candidate.load_state_dict(reference.state_dict())
    reference.eval()
    candidate.eval()
    q = torch.tensor([[1, 2, 1]])
    qa = torch.tensor([[3, 2, 1]])
    targets = torch.tensor([[1., 0., 1.]])
    ref_loss, ref_p, ref_n, ref_logits = forward_with_logits(reference, q, qa, targets)
    got_loss, got_p, got_n, got_logits = forward_with_logits(candidate, q, qa, targets)
    assert ref_n.item() == got_n.item() == 3
    torch.testing.assert_close(got_logits, ref_logits, atol=1e-6, rtol=1e-6)
    torch.testing.assert_close(got_p, ref_p, atol=1e-6, rtol=1e-6)
    torch.testing.assert_close(got_loss, ref_loss, atol=1e-6, rtol=1e-6)
    ref_loss.backward()
    got_loss.backward()
    for (name, ref_param), (other_name, param) in zip(reference.named_parameters(), candidate.named_parameters()):
        assert name == other_name
        assert (param.grad is None) == (ref_param.grad is None)
        if param.grad is not None:
            torch.testing.assert_close(param.grad, ref_param.grad, atol=1e-6, rtol=1e-6)


def test_cpu_request_overrides_cuda_auto_selection(monkeypatch):
    monkeypatch.setattr(torch.cuda, 'is_available', lambda: True)
    module = load_upstream(ROOT, device='cpu')
    assert module.device == torch.device('cpu')


def test_no_pid_or_graph_parameters_in_nonrasch():
    model = build_native(config(), n_items=2)
    assert model.n_pid == 0
    assert not any('graph' in name or 'difficult' in name for name, _ in model.named_parameters())
    assert len(model.model.blocks_1) == 1
    assert len(model.model.blocks_2) == 2


def test_source_files_unchanged_after_import_and_forward():
    before = verify_upstream(ROOT, SOURCE_COMMIT)
    model = build_native(config(), n_items=2).eval()
    q = torch.tensor([[1, 2]])
    out1 = model(q, q, torch.tensor([[-1., -1.]]))[1]
    out2 = model(q, q, torch.tensor([[-1., -1.]]))[1]
    torch.testing.assert_close(out1, out2, atol=1e-6, rtol=1e-6)
    assert verify_upstream(ROOT, SOURCE_COMMIT) == before
