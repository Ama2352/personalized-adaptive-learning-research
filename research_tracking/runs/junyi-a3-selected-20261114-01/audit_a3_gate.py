"""Đọc gate đã học trên cache selection, CPU-only, không dự đoán lại backbone."""
import json
from pathlib import Path
import sqlite3
import sys
import time
import zlib

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'experiments/akt')]
from junyi_staged_io import sha, write_new


def distribution(values):
    import numpy as np
    return dict(count=int(values.size), minimum=float(values.min()), mean=float(values.mean()),
                p05=float(np.quantile(values, .05)), median=float(np.median(values)),
                p95=float(np.quantile(values, .95)), maximum=float(values.max()))


def main():
    import numpy as np
    import torch
    from knowledge_tracing.akt.research_junyi_compact import CompactA1Context, CompactConfidenceContext
    started = time.monotonic()
    torch.set_num_threads(1)
    accepted = json.loads((HERE / 'a3-final-acceptance.json').read_text())
    assert accepted['status'] == 'PASS_A3_SELECTED_FIT80_ARTIFACT_AND_PREDICTION_CONTRACT'
    request = json.loads((ROOT / 'artifacts/akt/staged/junyi-a3-expert-20261114-03/project/gpu-stage-request.json').read_text())
    model_index = json.loads((ROOT / 'experiments/akt/results/model-export-a3-batch128-20261114-01/MODEL_INDEX.json').read_text())
    pin = request['cpu_prepared']['selection_graph']
    cache = ROOT / pin['path']
    assert sha(cache) == pin['sha256']
    parameters = json.loads((HERE / 'a3-learned-graph-parameters.json').read_text())['parameters']
    weights = torch.tensor(next(value for name, value in parameters.items() if name.endswith('gate.weight')), dtype=torch.float32)
    bias = torch.tensor(next(value for name, value in parameters.items() if name.endswith('gate.bias')), dtype=torch.float32)
    alpha = torch.tensor(next(value for name, value in parameters.items() if name.endswith('alpha')), dtype=torch.float32)
    assert weights.shape == (1, 4) and bias.shape == (1,) and alpha.numel() == 1
    gates, changes = [], []
    targets, windows = 0, 0
    connection = sqlite3.connect(cache.resolve().as_uri() + '?mode=ro', uri=True)
    try:
        metadata = json.loads(connection.execute('SELECT payload FROM metadata').fetchone()[0])
        binding = metadata['binding']
        assert binding['condition_sha256'] == model_index['graph_condition_sha256']
        for window_id, width, payload in connection.execute('SELECT window_id,width,payload FROM contexts'):
            assert time.monotonic() - started < 120
            raw = zlib.decompress(payload)
            assert len(raw) == width * 31
            base = CompactA1Context((1, width), (window_id,), binding['condition_sha256'],
                binding['encoding_sha256'], binding['phase_sha256'], raw[:4 * width],
                raw[4 * width:5 * width], raw[5 * width:6 * width], raw[6 * width:7 * width],
                raw[7 * width:15 * width])
            context = CompactConfidenceContext(base, 'A3', raw[15 * width:])
            messages, active, target, valid, features = context.arrays()
            targets += int((target & valid).sum())
            windows += 1
            if active.any():
                inputs = torch.from_numpy(features[active].copy())
                with torch.no_grad():
                    gate = torch.sigmoid(torch.nn.functional.linear(inputs, weights, bias)).reshape(-1)
                    residual = alpha * gate * torch.from_numpy(messages[active].copy())
                gates.append(gate.numpy())
                changes.append(residual.numpy())
    finally:
        connection.close()
    assert targets == metadata['targets'] == 1600343 and windows == metadata['windows'] == 28449
    assert gates and changes
    gate_values, residuals = np.concatenate(gates), np.concatenate(changes)
    assert np.isfinite(gate_values).all() and np.isfinite(residuals).all()
    assert ((gate_values >= 0) & (gate_values <= 1)).all()
    result = dict(status='PASS_CPU_SELECTED_GATE_CONTEXT_AUDIT', phase='raw_selection10',
        targets=targets, windows=windows, active_targets=len(gate_values),
        active_fraction=len(gate_values) / targets, inactive_targets=targets - len(gate_values),
        alpha=float(alpha), gate_on_active_targets=distribution(gate_values),
        absolute_logit_residual_on_active_targets=distribution(np.abs(residuals)),
        mean_absolute_logit_residual_all_targets=float(np.abs(residuals).sum(dtype=np.float64) / targets),
        probability_change_upper_bound_on_active_targets=distribution(np.abs(residuals) * .25),
        gate_below_005=int((gate_values < .05).sum()), gate_above_095=int((gate_values > .95).sum()),
        cache_sha256=pin['sha256'], checkpoint_sha256=accepted['checkpoint_sha256'],
        source_sha256=sha(ROOT / 'src/knowledge_tracing/akt/research_graph_model.py'),
        seconds=time.monotonic() - started,
        limits_vi='Tái tính gate/residual bằng TorchCPU FP32 từ tham số đã chọn và cache quá khứ đã ghim. '
        'Chưa đối chiếu parity CUDA riêng cho thống kê này. Bound xác suất dựa trên đạo hàm sigmoid≤1/4, '
        'không phải thay đổi xác suất quan sát. Đây là mô tả trên selection, '
        'chưa chứng minh hiệu quả cổng hoặc tác động nhân quả, graph-off replay độc lập còn chờ.')
    assert sha(cache) == pin['sha256']
    write_new(HERE / 'a3-gate-selection-audit.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
