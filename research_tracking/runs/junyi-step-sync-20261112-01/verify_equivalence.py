"""Đối chiếu hai primitive trên cùng dữ liệu giả và trạng thái RNG."""
import ast
import copy
import json
from pathlib import Path
import sys
import time


def load_step(path, torch):
    tree = ast.parse(Path(path).read_text(encoding='utf-8-sig'))
    adapter = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'AKTAdapter')
    method = next(node for node in adapter.body if isinstance(node, ast.FunctionDef) and node.name == 'step')
    namespace = dict(torch=torch, time=time, AKTBatch=object)
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(path), 'exec'), namespace)
    return namespace['step']


def assert_equal(left, right):
    import torch
    if isinstance(left, torch.Tensor):
        assert torch.equal(left, right)
    elif isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            assert_equal(left[key], right[key])
    elif isinstance(left, (tuple, list)):
        assert len(left) == len(right)
        for a, b in zip(left, right):
            assert_equal(a, b)
    else:
        assert left == right


def verify(before, candidate, device='cpu'):
    import numpy as np
    import torch
    from knowledge_tracing.akt.config import AKTConfig
    from knowledge_tracing.akt.encoding import fit_vocabulary
    from knowledge_tracing.akt.model import AKTAdapter
    from knowledge_tracing.akt.tensors import collate_windows
    from knowledge_tracing.akt.types import KTEvent, LearnerEvents
    from knowledge_tracing.akt.windows import iter_windows

    torch.set_num_threads(2)
    torch.manual_seed(42)
    learner = LearnerEvents('synthetic', 0, tuple(
        KTEvent('synthetic', str(index % 3), index + 1, index + 1, index % 2, 0, 0)
        for index in range(24)))
    encoding = fit_vocabulary([learner])
    entry = next(iter_windows(learner, encoding, training=True))
    config = AKTConfig(d_model=32, heads=4, d_ff=64, final_fc=32, dropout=.05,
                       device=device)
    adapter = AKTAdapter(config, encoding)
    initial = copy.deepcopy(adapter.native.state_dict())
    batch = collate_windows([entry.window] * 4, n_items=3, device=device,
                            targets=[entry.targets] * 4)
    cpu_rng = torch.get_rng_state().clone()
    cuda_rng = torch.cuda.get_rng_state().clone() if device == 'cuda' else None
    records = []
    outputs = []
    for source in (before, candidate):
        adapter.native.load_state_dict(initial)
        adapter.native.train()
        optimizer = torch.optim.Adam(adapter.native.parameters(), lr=config.lr,
                                      foreach=False, fused=False)
        torch.set_rng_state(cpu_rng)
        if cuda_rng is not None:
            torch.cuda.set_rng_state(cuda_rng)
        step = load_step(source, torch)
        metrics = []
        for _ in range(8):
            result = step(adapter, batch, optimizer)
            metrics.append({key: value for key, value in result.items() if not key.endswith('_seconds')})
        records.append(dict(model=copy.deepcopy(adapter.native.state_dict()),
                            optimizer=copy.deepcopy(optimizer.state_dict()),
                            gradients=[p.grad.detach().clone() if p.grad is not None else None
                                       for p in adapter.native.parameters()],
                            cpu_rng=torch.get_rng_state().clone(),
                            cuda_rng=torch.cuda.get_rng_state().clone() if cuda_rng is not None else None,
                            metrics=metrics))
        outputs.append(adapter.predict_window(entry.window))
        empty = collate_windows([entry.window], n_items=3, device=device)
        assert step(adapter, empty, optimizer)['stepped'] is False
        empty.loss_targets[0, 0] = float('nan')
        try:
            step(adapter, empty, optimizer)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid targets must be rejected')
    assert_equal(records[0], records[1])
    assert np.array_equal(outputs[0], outputs[1])
    return dict(status='PASS_EXACT_SYNTHETIC_EQUIVALENCE', device=device, updates_per_variant=8,
                exact=['model', 'Adam', 'gradients', 'RNG', 'metrics', 'predictions'],
                zero_target_and_invalid_target_checks=True, speed_claim=False)


if __name__ == '__main__':
    folder = Path(__file__).resolve().parent
    sys.path.insert(0, str(folder.parents[2] / 'src'))
    result = verify(folder / 'model-before.py', folder / 'model-candidate.py')
    (folder / 'cpu-equivalence.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result), flush=True)
