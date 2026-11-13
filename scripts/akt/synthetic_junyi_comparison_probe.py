"""Kiểm A0/A1 Junyi batch128 trên T4 bằng dữ liệu tổng hợp hữu hạn."""
import argparse
from dataclasses import replace
import gc
import hashlib
import json
import os
from pathlib import Path
import sys
import time

os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT/'experiments/akt/results') or output.exists():
        parser.error('Dùng output mới trong experiments/akt/results')
    import numpy as np
    import torch
    from knowledge_tracing.akt.checkpoint import load_checkpoint, restore_checkpoint, save_checkpoint
    from knowledge_tracing.akt.config import AKTConfig, ResearchCUDAExecutionProfile
    from knowledge_tracing.akt.encoding import ExerciseEncoding
    from knowledge_tracing.akt.model import AKTAdapter
    from knowledge_tracing.akt.research_junyi_data import JunyiPhaseView, JunyiResearchEncoding
    from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition, JunyiGraphPhaseSession
    from knowledge_tracing.akt.research_junyi_graph_model import JunyiGraphAKTAdapter
    from knowledge_tracing.akt.research_junyi_roles import make_junyi_research_roles
    from knowledge_tracing.akt.research_runner import _state_hash
    from knowledge_tracing.akt.training import _seed
    from knowledge_tracing.akt.types import KTEvent, LearnerEvents
    from knowledge_tracing.akt.windows import iter_windows
    from knowledge_tracing.shared_kt import PrerequisiteGraph, StableVocabulary

    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise ValueError('Một GPU CUDA thực được yêu cầu')
    if 'T4' not in torch.cuda.get_device_name(0):
        raise ValueError('Probe này dành cho T4 miễn phí')
    output.mkdir(parents=True)
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.set_float32_matmul_precision('highest')
    total = torch.cuda.get_device_properties(0).total_memory
    max_vram = 12*1024**3
    torch.cuda.set_per_process_memory_fraction(max_vram/total, 0)
    torch.cuda.reset_peak_memory_stats()
    profile = ResearchCUDAExecutionProfile(max_vram, recipe_id='cgakt-cuda-fp32-batch128-v2')
    run_id = output.name
    config = replace(AKTConfig(), phase='junyi-research',device='cuda',outer_fold=4,
        run_id=run_id, output_dir=output, execution_enabled=True, batch_size=128,
        protocol_version='akt-nr-exercise-v2-batch128', max_train_users=256,
        max_val_users=32,max_targets_per_side=25600,max_total_targets=100000,
        max_steps=3,max_seconds=240,max_wall_seconds=280,max_rss_bytes=8*1024**3,
        min_available_ram_bytes=1)
    roles = make_junyi_research_roles([(str(i),i%5,'development') for i in range(400)])
    view = JunyiPhaseView(roles,'select_train80',roles.train_users,roles.identity)
    values = tuple(['A','B','C']+[f'fixture-{i:03d}' for i in range(714)])
    encoding = JunyiResearchEncoding(ExerciseEncoding(StableVocabulary(values),
        {item:1 for item in values}), view)
    graph = PrerequisiteGraph.from_edges(values, (('A','C'),('B','C')))
    condition = JunyiGraphCondition(encoding, graph, 'f'*64)

    def entries(*, flip=False):
        result = []
        for index,user in enumerate(view.users[:128]):
            events = tuple(KTEvent(user,('A','B','C')[j%3],j+1,index*200+j+1,
                ((index+j)%2) ^ int(flip and j>=150),0,0) for j in range(200))
            result.append(tuple(iter_windows(LearnerEvents(user,0,events),encoding.native,training=True))[-1])
        return result

    original = entries()
    changed = entries(flip=True)
    windows = [entry.window for entry in original]

    def build():
        _seed(42)
        with torch.device('cpu'):
            return JunyiGraphAKTAdapter(config=config,encoding=encoding,condition=condition,
                phase=JunyiGraphPhaseSession(condition,view),cuda_profile=profile)

    def adam(adapter):
        return torch.optim.Adam(adapter.native.parameters(),lr=config.lr,betas=config.betas,
            eps=config.eps,weight_decay=config.weight_decay,foreach=False,fused=False)

    def step(adapter, optimizer):
        adapter.native.train()
        result = adapter.step(adapter.collate_training(original), optimizer)
        if not result['stepped'] or result['valid_targets'] != 12800:
            raise ValueError('Batch128 target/optimizer mismatch')
        return result

    started = time.monotonic()
    _seed(42)
    baseline = AKTAdapter(config, encoding.native)
    initial_a0 = _state_hash(baseline)
    a0_prediction = baseline.predict_window(windows[0])
    del baseline
    gc.collect()
    torch.cuda.empty_cache()
    adapter = build()
    from types import SimpleNamespace
    initial_a1 = _state_hash(SimpleNamespace(native=adapter.native.backbone))
    if initial_a0 != initial_a1:
        raise ValueError('A0/A1 initial backbone differs')
    adapter.set_graph_enabled(False)
    np.testing.assert_allclose(adapter.predict_window(windows[0]), a0_prediction, atol=1e-6, rtol=1e-6)
    adapter.set_graph_enabled(True)
    with torch.no_grad():
        adapter.native.alpha.fill_(1.)
    before = adapter.predict_window(windows[0])
    after = adapter.predict_window(changed[0].window)
    np.testing.assert_allclose(before[:151],after[:151],atol=1e-6,rtol=1e-6)
    with torch.no_grad():
        adapter.native.alpha.zero_()
    optimizer = adam(adapter)
    steps = [step(adapter,optimizer)]
    identity = dict(kind='synthetic_junyi_batch128_t4_v1',encoding=encoding.identity,
        graph=condition.identity,initial_backbone=initial_a1)
    checkpoint = output/'step1.pt'
    save_checkpoint(checkpoint,adapter,optimizer,identity=identity,
        progress=dict(epoch=1,complete=True,optimizer_steps=1))
    steps.append(step(adapter,optimizer))
    expected = {key:value.detach().cpu().clone() for key,value in adapter.native.state_dict().items()}
    expected_optimizer = optimizer.state_dict()
    # Trạng thái optimizer chuyển về CPU trước khi giải phóng model.
    expected_moments = {key:{name:value.detach().cpu().clone() if torch.is_tensor(value) else value
        for name,value in state.items()} for key,state in expected_optimizer['state'].items()}
    del expected_optimizer, optimizer, adapter
    gc.collect()
    torch.cuda.empty_cache()
    clone = build()
    clone_optimizer = adam(clone)
    restore_checkpoint(clone,clone_optimizer,load_checkpoint(checkpoint,expected_identity=identity,device='cuda'))
    resumed = step(clone,clone_optimizer)
    for key,value in clone.native.state_dict().items():
        if not torch.equal(expected[key],value.detach().cpu()):
            raise ValueError(f'Resume model mismatch: {key}')
    for key,state in clone_optimizer.state_dict()['state'].items():
        for name,value in state.items():
            expected_value = expected_moments[key][name]
            equal = torch.equal(expected_value,value.detach().cpu()) if torch.is_tensor(value) else expected_value == value
            if not equal:
                raise ValueError('Resume Adam mismatch')
    prediction = clone.predict_window(windows[0])
    np.save(output/'prediction.npy',prediction,allow_pickle=False)
    report = dict(status='PASS_SYNTHETIC_A0_A1_T4_BATCH128',torch=torch.__version__,
        cuda=torch.version.cuda,gpu=torch.cuda.get_device_name(0),vocabulary=717,
        batch_size=128,max_length=200,steps_continuous=steps,resumed_step=resumed,
        initial_backbone_sha256=initial_a1,checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
        prediction_rows=len(prediction),model_and_adam_resume_exact=True,
        causal_current_future_test=True,graph_off_matches_a0=True,
        max_vram_allocated=torch.cuda.max_memory_allocated(),seconds=time.monotonic()-started,
        a2_a3_junyi_tested=False,real_junyi_data_used=False,
        limits_vi='Kiểm tổng hợp A0/A1 batch128 trên T4. Chưa nghiệm thu A2/A3 Junyi, full producer hoặc H100 môi trường khác.')
    (output/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__ == '__main__':
    main()
