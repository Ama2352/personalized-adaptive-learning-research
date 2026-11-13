"""Fit confidence TRAIN80 trên CPU local, spool và checkpoint theo child trên D."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--action', choices=('spool', 'fit-child', 'fit-all', 'finalize'), required=True)
    parser.add_argument('--child')
    parser.add_argument('--max-seconds', type=int, default=600)
    parser.add_argument('--max-rows', type=int, default=200000)
    parser.add_argument('--max-rss-mib', type=int, default=448)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / 'artifacts/akt/confidence'):
        raise ValueError('Confidence phải nằm dưới artifacts/akt/confidence trên D')
    if not 1 <= args.max_seconds <= 3600 or not 1 <= args.max_rows <= 1000000:
        raise ValueError('Workload CPU cần cap hữu hạn')
    if not 128 <= args.max_rss_mib <= 1024:
        raise ValueError('Cap RSS CPU ngoài giới hạn')
    request = json.loads(args.request.read_text(encoding='utf-8'))
    if not args.worker:
        import psutil
        output.mkdir(parents=True, exist_ok=True)
        # Điều phối nhẹ, worker mới cho từng child để trả RAM sau mỗi fit.
        if args.action == 'fit-all':
            graph = json.loads((ROOT / request['topology_file']).read_text())
            children = sorted({child for _, child in graph['corrected_edges']})
        else:
            children = [args.child]
        began = time.monotonic()
        for child in children:
            if args.action == 'fit-all':
                folder = output / 'children' / hashlib.sha256(child.encode()).hexdigest()
                if (folder / 'COMPLETE.json').exists():
                    continue  # Finalize xác minh lại mọi child SHA.
            remaining = args.max_seconds - (time.monotonic() - began)
            if remaining < 10:
                raise TimeoutError('Hết tranche CPU, chạy tiếp từ checkpoint child')
            action = 'fit-child' if args.action == 'fit-all' else args.action
            cap = min(int(remaining), 300) if action == 'fit-child' else int(remaining)
            command = [sys.executable, '-B', str(Path(__file__).resolve()), '--request', str(args.request),
                '--output', str(output), '--action', action, '--max-seconds', str(cap),
                '--max-rows', str(args.max_rows), '--max-rss-mib', str(args.max_rss_mib), '--worker']
            if child is not None:
                command.extend(('--child', child))
            environment = dict(os.environ, OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                               PYTHONDONTWRITEBYTECODE='1')
            log_path = output / ('controller-' + str(time.time_ns()) + '.jsonl')
            with log_path.open('x', encoding='utf-8') as log:
                process = subprocess.Popen(command, cwd=ROOT, env=environment)
                try:
                    tracked = psutil.Process(process.pid)
                    started = time.monotonic()
                    while process.poll() is None:
                        try:
                            tree = [tracked, *tracked.children(recursive=True)]
                            rss = sum(item.memory_info().rss for item in tree if item.is_running())
                        except psutil.NoSuchProcess:
                            continue
                        available = psutil.virtual_memory().available
                        log.write(json.dumps(dict(child=child, seconds=time.monotonic() - started,
                                                  rss=rss, available_ram=available)) + '\n')
                        log.flush()
                        if (rss > args.max_rss_mib * 1024**2 or available < 96 * 1024**2
                                or time.monotonic() - started > cap + 45):
                            raise RuntimeError('Dừng worker theo cap RAM/thời gian, giữ checkpoint đã commit')
                        time.sleep(1)
                    code = process.wait()
                    if code:
                        raise RuntimeError('CPU worker thất bại, xem log và checkpoint, exit=' + str(code))
                finally:
                    if process.poll() is None:
                        for item in reversed([tracked, *tracked.children(recursive=True)]):
                            try:
                                item.terminate()
                            except psutil.NoSuchProcess:
                                pass
                        process.wait(timeout=10)
        return

    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.akt.research_junyi_selection import load_full_selected_cache
    from knowledge_tracing.akt.research_junyi_data import load_prepared_junyi_encoding
    from knowledge_tracing.akt.research_junyi_graph import JunyiGraphCondition, JunyiGraphPhaseSession
    from knowledge_tracing.akt.research_junyi_window_cache import JunyiWindowCacheSession
    from knowledge_tracing.shared_kt import PrerequisiteGraph
    from knowledge_tracing.akt.research_junyi_confidence_run import (
        run_identity, spool_windows, fit_one_child, finalize, sha, write_closed,
    )
    from knowledge_tracing.edge_confidence import EdgeRuntimeBinding
    import importlib.metadata
    data = request['inputs']

    def local(name):
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or 'private' in path.parts:
            raise ValueError('Input phải thuộc repository và ngoài vùng private')
        return path

    inputs = load_full_selected_cache(local(data['selected_cache_root']), local(data['roles_path']),
        expected_manifest_sha256=data['selected_cache_manifest_sha256'], expected_roles_sha256=data['roles_sha256'])
    encoding = load_prepared_junyi_encoding(local(data['encoding_file']), local(data['encoding_receipt']),
        view=inputs.train, source_data_sha256=inputs.source_identity,
        expected_file_sha256=data['encoding_sha256'], expected_receipt_sha256=data['encoding_receipt_sha256'])
    graph_file = local(request['topology_file'])
    if sha(graph_file) != request['topology_sha256']:
        raise ValueError('Topology khác SHA')
    graph = json.loads(graph_file.read_text())
    condition = JunyiGraphCondition(encoding, PrerequisiteGraph.from_edges(graph['nodes'], graph['corrected_edges']),
                                   request['topology_sha256'])
    output.mkdir(parents=True, exist_ok=True)
    versions = {name: importlib.metadata.version(name) for name in ('numpy', 'scikit-learn', 'scipy', 'joblib', 'threadpoolctl')}
    write_closed(output / 'runtime-versions.json', dict(python=sys.version, dependencies=versions))
    runtime = EdgeRuntimeBinding(versions['scikit-learn'], versions['numpy'],
        sha(output / 'runtime-versions.json'), sha(ROOT / 'src/knowledge_tracing/edge_confidence.py'))
    identity = run_identity(condition, data['train_window_manifest_sha256'], runtime)
    if args.action == 'spool':
        admitted = request['train_cpu_admission']
        session = JunyiWindowCacheSession(local(data['train_window_cache']), inputs.train, encoding,
            inputs.source_identity, inputs.train_targets, data['train_window_manifest_sha256'],
            admission_receipt=local(admitted['path']), expected_admission_sha256=admitted['sha256'])
        result = spool_windows(output, windows=session.iter_windows(),
            session=JunyiGraphPhaseSession(condition, inputs.train), identity=identity,
            expected_targets=inputs.train_targets, expected_records=session.strict_records_verified,
            max_seconds=max(1, args.max_seconds - 20))
    elif args.action == 'fit-child':
        result = fit_one_child(output, condition=condition, runtime=runtime, child=args.child,
                               max_rows=args.max_rows, max_seconds=max(1, args.max_seconds - 20))
        result = dict(status='CHILD_COMPLETE', child=args.child, targets=result['targets'],
                      edges=len(result['edges']), wall_seconds=result['wall_seconds'])
    else:
        result = finalize(output, condition=condition, runtime=runtime)
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
