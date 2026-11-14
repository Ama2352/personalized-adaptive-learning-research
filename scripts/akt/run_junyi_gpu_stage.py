"""Chỉ train/validation Junyi trong container GPU đã nhận input chuẩn bị local.

Không giải nén source/data, fit confidence, tạo cache, nén hoặc tải artifact.
Checkpoint và predictions ghi thẳng vào output Volume của logical run.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def relative(name):
    path = Path(name)
    if path.is_absolute() or '..' in path.parts or ':' in name or '\\' in name:
        raise ValueError('Đường dẫn worker phải tương đối')
    return ROOT / path


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def prepare_runtime_report(root, operation, upstream, lock, device):
    """Dùng đúng vùng output của CLI, giữ bản báo cáo trong artifact theo lượt."""
    generated=root/'artifacts/akt/preflight'/(operation.name+'-runtime.json')
    subprocess.run([str(root/'.venv/bin/python'),'-I','-B',str(root/'scripts/akt/check_runtime.py'),
        '--upstream',str(upstream),'--device',device,'--lock-file',str(lock),
        '--output',str(generated)],check=True,timeout=90)
    report=operation/'runtime.json'
    shutil.copyfile(generated,report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--execution', type=Path, required=True)
    args = parser.parse_args()
    request = json.loads(args.request.read_text())
    execution = json.loads(args.execution.read_text())
    operation = relative('experiments/akt/results/' + execution['execution_id'] + '-operation')
    # Controller đã tạo riêng thư mục này để giữ log khi worker lỗi.
    started = time.monotonic()
    result = dict(status='FAILED', refit_completed=False, calibration_completed=False)
    try:
        os.environ.update(CUBLAS_WORKSPACE_CONFIG=':4096:8', CUDA_VISIBLE_DEVICES='0',
            OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1',
            GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_COUNT='3',
            GIT_CONFIG_KEY_0='core.fsmonitor', GIT_CONFIG_VALUE_0='false',
            GIT_CONFIG_KEY_1='safe.directory', GIT_CONFIG_VALUE_1=str(ROOT/'artifacts/akt/dependencies/upstream'),
            GIT_CONFIG_KEY_2='core.autocrlf', GIT_CONFIG_VALUE_2='false', GIT_OPTIONAL_LOCKS='0',
            GIT_TERMINAL_PROMPT='0', GIT_ALLOW_PROTOCOL='__NO_TRANSPORT__')
        import torch
        from knowledge_tracing.akt.config import load_config, ResearchCUDAExecutionProfile
        from knowledge_tracing.akt.authorization import require_gate2_evidence, preflight, config_hash
        from knowledge_tracing.akt.research_junyi_selection import load_full_selected_cache, run_junyi_selected
        from knowledge_tracing.akt.research_junyi_data import load_prepared_junyi_encoding
        from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition
        from knowledge_tracing.akt.research_junyi_confidence_binding import load_binding
        from knowledge_tracing.akt.research_junyi_prepared import prepared_cache_options
        from knowledge_tracing.shared_kt import PrerequisiteGraph
        torch.set_num_threads(2)
        torch.set_default_dtype(torch.float32)
        torch.use_deterministic_algorithms(True, warn_only=False)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cudnn.benchmark = False
        torch.set_float32_matmul_precision('highest')
        if execution['gpu'] not in torch.cuda.get_device_name(0):
            raise ValueError('GPU thực tế khác loại đã dự toán')
        profile = ResearchCUDAExecutionProfile(**request['profile'])
        torch.cuda.set_per_process_memory_fraction(
            profile.max_vram_bytes / torch.cuda.get_device_properties(0).total_memory, 0)
        config_file = operation / 'config.json'
        write(config_file, request['config'])
        config = load_config(config_file, cuda_profile=profile)
        assert str(config.project_root) == str(ROOT)
        assert request['variant'] in ('A2','A3')
        assert config.run_id == request['logical_run_id']
        assert config.output_dir == ROOT/'experiments/akt/results'/config.run_id
        assert sha(args.request) == execution['worker_request_sha256']
        lock = Path('/opt/locked-cu126.txt')
        assert sha(lock) == request['runtime_lock_sha256']
        runtime = prepare_runtime_report(ROOT,operation,config.source_root,lock,'cuda')
        gate = require_gate2_evidence(config, lock_file=lock)
        preflight(config, runtime_report_path=runtime, lock_file=lock, cuda_profile=profile)
        data = request['inputs']
        inputs = load_full_selected_cache(relative(data['selected_cache_root']), relative(data['roles_path']),
            expected_manifest_sha256=data['selected_cache_manifest_sha256'], expected_roles_sha256=data['roles_sha256'])
        encoding = load_prepared_junyi_encoding(relative(data['encoding_file']), relative(data['encoding_receipt']),
            view=inputs.train, source_data_sha256=inputs.source_identity,
            expected_file_sha256=data['encoding_sha256'], expected_receipt_sha256=data['encoding_receipt_sha256'])
        graph = relative(request['graph_file'])
        assert sha(graph) == request['graph_sha256']
        topology = json.loads(graph.read_text())
        confidence = load_binding(relative(request['confidence_file']), expected_sha256=request['confidence_sha256'])
        condition = JunyiGraphCondition(encoding,
            PrerequisiteGraph.from_edges(topology['nodes'],topology['corrected_edges']), request['graph_sha256'],
            variant=request['variant'], confidence=confidence)
        prepared = dict(encoding_sha256=data['encoding_sha256'], encoding_receipt_sha256=data['encoding_receipt_sha256'],
            train_window_manifest_sha256=data['train_window_manifest_sha256'], graph_condition_sha256=condition.identity,
            comparison_reference_sha256=request['comparison_reference_sha256'], validation_batch_size=128,
            prefetch_train_windows=True, prefetch_selection_windows=True,
            edge_confidence_identity=confidence.identity, edge_confidence_sha256=confidence.fit_artifact_sha256,
            train_cache_admission_sha256=request['train_admission_sha256'])
        cache_options,cache_pins=prepared_cache_options(request,relative)
        prepared.update(cache_pins)
        resume = execution.get('resume_checkpoint')
        if resume is not None:
            if not resume.startswith('experiments/akt/results/'+config.run_id+'/checkpoints/'):
                raise ValueError('Resume phải thuộc đúng logical run')
            prepared['resume_checkpoint_sha256'] = execution['resume_sha256']
        grant = dict(status='USER_APPROVED', approval_reference=execution['approval_reference'],
            purpose=request['purpose'], workload_epochs=request['workload_epochs'], prepared_inputs=prepared,
            binding=dict(candidate_id=request['variant']+'_EXPERT', phase='junyi_selected_only',
                config_sha256=config_hash(config), inputs_identity=inputs.identity,
                gate_sha256=gate['report_sha256'], runtime_sha256=sha(runtime)))
        authorization = operation/'authorization.json'
        write(authorization, grant)
        terminal = run_junyi_selected(config, profile, inputs,
            authorization_file=authorization, expected_authorization_sha256=sha(authorization),
            runtime_report=runtime, lock_file=lock, encoding_file=relative(data['encoding_file']),
            expected_encoding_sha256=data['encoding_sha256'], encoding_receipt=relative(data['encoding_receipt']),
            expected_encoding_receipt_sha256=data['encoding_receipt_sha256'],
            train_window_cache=relative(data['train_window_cache']),
            expected_train_window_manifest_sha256=data['train_window_manifest_sha256'],
            graph_condition=condition, comparison_reference_file=relative(request['comparison_reference_file']),
            expected_comparison_reference_sha256=request['comparison_reference_sha256'], validation_batch_size=128,
            prefetch_train_windows=True, prefetch_selection_windows=True,
            train_cache_admission_receipt=relative(request['train_admission_file']),
            expected_train_cache_admission_sha256=request['train_admission_sha256'],
            resume_checkpoint=None if resume is None else relative(resume),
            expected_resume_sha256=execution.get('resume_sha256'),**cache_options)
        result.update(status=terminal['status'],terminal=terminal,gpu=torch.cuda.get_device_name(0))
    except BaseException as error:
        result.update(error_type=type(error).__name__,error=str(error))
        (operation/'failure.log').write_text(traceback.format_exc())
    result['wall_seconds'] = time.monotonic()-started
    write(operation/'result.json', result)
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return 1 if result['status']=='FAILED' else 0


if __name__ == '__main__':
    raise SystemExit(main())
