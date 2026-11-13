"""Kiểm nhanh checkpoint A0 thật trên lịch sử tổng hợp, chỉ dự đoán CPU."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from dataclasses import replace

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
os.environ['GIT_CONFIG_COUNT'] = '1'
os.environ['GIT_CONFIG_KEY_0'] = 'safe.directory'
os.environ['GIT_CONFIG_VALUE_0'] = (ROOT / 'artifacts/akt/dependencies/upstream').as_posix()

def main():
    import psutil
    if psutil.virtual_memory().available < 2 * 1024**3:
        raise RuntimeError('Kiểm CPU nhỏ cần tối thiểu 2 GiB RAM khả dụng')
    import numpy as np
    import torch
    from knowledge_tracing.akt.config import AKTConfig
    from knowledge_tracing.akt.encoding import ExerciseEncoding
    from knowledge_tracing.akt.model import AKTAdapter
    from knowledge_tracing.akt.prediction import iter_predictions
    from knowledge_tracing.akt.prediction_batch import iter_predictions_batched
    from knowledge_tracing.akt.types import KTEvent, LearnerEvents
    from knowledge_tracing.shared_kt import StableVocabulary

    started = time.monotonic()
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    folder = ROOT / 'experiments/akt/results/model-export-a0-batch128-20261112-01'
    checkpoint = folder / 'A0_JUNYI_SELECTED.pt'
    index = json.loads((folder / 'MODEL_INDEX.json').read_text(encoding='utf-8'))
    digest = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    assert digest == index['checkpoint_sha256']
    payload = torch.load(checkpoint, map_location='cpu', weights_only=True)
    assert payload['identity'] == index['metadata']['identity']
    assert payload['progress']['complete'] is True
    assert payload['progress']['epoch'] == 9
    values = tuple(payload['encoding']['values'])
    assert len(values) == 717
    encoding = ExerciseEncoding(StableVocabulary(values), payload['encoding']['train_support_students'])
    original = payload['identity']['config']
    architecture = {key: original[key] for key in (
        'context', 'target_block', 'max_length', 'd_model', 'heads', 'blocks',
        'd_ff', 'final_fc', 'dropout', 'kq_same', 'separate_qa', 'n_pid')}
    config = replace(AKTConfig(), **architecture, device='cpu', batch_size=128)
    adapter = AKTAdapter(config, encoding)
    adapter.native.load_state_dict(payload['model_state_dict'], strict=True)
    adapter.checkpoint_id = digest
    adapter.native.eval()
    del payload
    def model_hash():
        hasher = hashlib.sha256()
        for key, tensor in adapter.native.state_dict().items():
            hasher.update(key.encode())
            hasher.update(tensor.detach().cpu().numpy().tobytes())
        return hasher.hexdigest()
    before = model_hash()
    lengths = [16 + i % 17 for i in range(128)] + [201, 301]
    learners = tuple(LearnerEvents(f'fixture-{i:03d}', 0, tuple(
        KTEvent(f'fixture-{i:03d}', values[(i * 17 + rank) % len(values)], rank + 1,
            i * 1000 + rank + 1, (rank + i) % 2, 0, 0)
        for rank in range(length))) for i, length in enumerate(lengths))
    legacy = list(iter_predictions(adapter, iter(learners)))
    batched = list(iter_predictions_batched(adapter, iter(learners), batch_size=128))
    assert [replace(row, prediction=None) for row in legacy] == [replace(row, prediction=None) for row in batched]
    p = np.asarray([row.prediction for row in legacy])
    q = np.asarray([row.prediction for row in batched])
    assert len(p) == sum(lengths) and np.isfinite(p).all() and np.isfinite(q).all()
    parity = bool(np.allclose(p, q, atol=1e-6, rtol=1e-6))
    labels = np.asarray([event.correct for learner in learners for event in learner.events])
    def log_loss(probabilities):
        probabilities = np.clip(probabilities, 1e-7, 1-1e-7)
        return float(-np.mean(labels*np.log(probabilities) + (1-labels)*np.log1p(-probabilities)))
    assert model_hash() == before
    assert hashlib.sha256(checkpoint.read_bytes()).hexdigest() == digest
    result = dict(status='PASS_REAL_A0_WEIGHTS_SYNTHETIC_CPU_PARITY' if parity else 'FAIL_STRICT_PROBABILITY_PARITY', checkpoint_sha256=digest,
        selected_epoch=9, vocabulary=717, learners=len(learners), targets=len(p),
        validation_batch_size=128, device='cpu', torch=torch.__version__,
        max_probability_delta=float(np.max(np.abs(p-q))), probability_atol=1e-6, probability_rtol=1e-6,
        probability_parity_passed=parity,
        legacy_log_loss=log_loss(p), batched_log_loss=log_loss(q),
        absolute_log_loss_delta=abs(log_loss(p)-log_loss(q)),
        metadata_order_exact=True, model_weights_unchanged=True, checkpoint_unchanged=True,
        seconds=time.monotonic()-started, peak_rss_bytes=psutil.Process().memory_info().peak_wset,
        modal_spent_usd=0, training_epochs=0, full_junyi_selection_replayed=False,
        limits_vi='Trọng số A0 thật, lịch sử tổng hợp trên CPU. Chưa kiểm toàn selection Junyi, CUDA checkpoint này hoặc giữ nguyên chọn epoch từ 12 checkpoint.')
    (OUTPUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    if not parity:
        raise AssertionError('Giữ nguyên ngưỡng kiểm, chưa nghiệm thu batch128 với checkpoint thật')

if __name__ == '__main__':
    main()
