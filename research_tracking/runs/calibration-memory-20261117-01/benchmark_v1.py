"""Đo RAM V1 bằng dữ liệu tổng hợp, từng process riêng, không fit Junyi thật."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def worker(count, max_rss_mib, max_seconds):
    import psutil
    process = psutil.Process()
    started = time.perf_counter()
    rss_cap = max_rss_mib * 1024**2
    peak = [process.memory_info().rss]
    stop = threading.Event()
    path = HERE / f'V1_{count:06d}.json'

    def sample():
        while not stop.wait(.01):
            memory = process.memory_info()
            peak[0] = max(peak[0], memory.rss, getattr(memory, 'peak_wset', 0))
            reason = None
            if memory.rss > rss_cap:
                reason = 'MAX_RSS'
            elif time.perf_counter() - started > max_seconds:
                reason = 'MAX_SECONDS'
            if reason:
                write(HERE / f'V1_{count:06d}_RESOURCE_FAILURE.json',
                      dict(status='RESOURCE_STOP', reason=reason, rss=memory.rss,
                           peak_rss=peak[0], count=count))
                os._exit(124)
    sampler = threading.Thread(target=sample, daemon=True)
    sampler.start()
    sys.path.insert(0, str(ROOT / 'src'))
    from knowledge_tracing.response_calibration import (CalibrationTarget, PredictionBinding,
        CalibrationPartition, fit_temperature)
    imported = time.perf_counter()
    baseline = process.memory_info().rss
    learners = tuple(f'{i:010d}' for i in range((count + 99)//100))
    items = tuple(f'synthetic_math_exercise_{i:04d}' for i in range(717))
    rows = []
    keys = []
    for i in range(count):
        row = CalibrationTarget(learners[i//100], f'{i+1:09d}', items[i % len(items)],
            hashlib.sha256(str(i).encode()).hexdigest(), i % 2,
            .1 + .8 * (i % 997) / 996, 'supported')
        rows.append(row)
        keys.append((row.learner_id, row.event_id, row.item_id, row.history_sha256))
    prepared = time.perf_counter()
    prepared_rss = process.memory_info().rss
    binding = PredictionBinding('synthetic-memory-probe', *(['a'*64]*7))
    partition = CalibrationPartition('a'*64, learners, ('synthetic-train-excluded',), None)
    fit_started = time.perf_counter()
    calibration = fit_temperature(rows, binding=binding, partition=partition,
                                  expected_target_keys=tuple(keys), max_evaluations=4)
    finished = time.perf_counter()
    stop.set()
    sampler.join()
    info = process.memory_info()
    peak[0] = max(peak[0], info.rss, getattr(info, 'peak_wset', 0))
    result = dict(status='SYNTHETIC_RESOURCE_MEASUREMENT', count=count,
        evaluations=calibration.objective_evaluations, max_evaluations=4,
        baseline_rss_bytes=baseline, source_materialized_rss_bytes=prepared_rss,
        peak_rss_bytes=peak[0], end_rss_bytes=info.rss,
        import_seconds=imported-started, generation_seconds=prepared-imported,
        fit_seconds=finished-fit_started, total_seconds=finished-started,
        rss_cap_bytes=rss_cap, time_cap_seconds=max_seconds,
        history_ids_unique=count, learner_count=len(learners),
        event_id_length=9, learner_id_length=10, exercise_id_length=len(items[0]),
        history_sha_length=64, supported_targets=calibration.supported_targets,
        targets_sha256=calibration.targets_sha256,
        evidence_vi='Chỉ số tài nguyên tổng hợp, không phải temperature hoặc metric nghiên cứu Junyi.',
        resource_limit_vi='Watchdog RSS10ms và peak working set OS nếu có, không phải cgroup/kernel memory hard limit.')
    write(path, result)
    print(json.dumps(result, ensure_ascii=False), flush=True)


def controller(counts, max_rss_mib, max_seconds, summary_name):
    import psutil
    HERE.mkdir(parents=True, exist_ok=True)
    summary_path = HERE / summary_name
    if Path(summary_name).name != summary_name or summary_path.exists():
        raise ValueError('Tên summary mới trong bundle là bắt buộc khi chạy lại.')
    receipts = []
    for count in counts:
        destination = HERE / f'V1_{count:06d}.json'
        if destination.exists():
            receipts.append(json.loads(destination.read_text(encoding='utf-8')))
            continue
        available = psutil.virtual_memory().available
        minimum = (max_rss_mib + 128) * 1024**2
        if available < minimum:
            write(HERE / f'V1_{count:06d}_{summary_path.stem}_ADMISSION.json',
                  dict(status='RAM_ADMISSION_DEFERRED', available_bytes=available,
                       required_headroom_bytes=minimum, count=count))
            print('Thiếu RAM cho lượt kế tiếp, chưa tạo child.', flush=True)
            break
        args = [sys.executable, '-B', str(Path(__file__).resolve()), '--worker', str(count),
                '--max-rss-mib', str(max_rss_mib), '--max-seconds', str(max_seconds)]
        with (HERE / f'V1_{count:06d}.txt').open('x', encoding='utf-8') as log:
            child = subprocess.Popen(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            try:
                child.wait(timeout=max_seconds + 15)
            except subprocess.TimeoutExpired:
                owned = psutil.Process(child.pid)
                descendants = owned.children(recursive=True)
                for process in reversed(descendants):
                    try:
                        process.terminate()
                    except psutil.NoSuchProcess:
                        pass
                child.terminate()
                child.wait(timeout=10)
                write(HERE / f'V1_{count:06d}_PARENT_TIMEOUT.json',
                      dict(status='OWNED_CHILD_TIMEOUT', count=count))
                break
        if child.returncode != 0:
            print(f'Lượt {count} dừng với code {child.returncode}, giữ log.', flush=True)
            break
        result = json.loads(destination.read_text(encoding='utf-8'))
        result['available_before_bytes'] = available
        receipts.append(result)
        print(json.dumps(dict(count=count, peak_mib=result['peak_rss_bytes']/1024**2,
                              fit_seconds=result['fit_seconds']), ensure_ascii=False), flush=True)
    write(summary_path, dict(status='SYNTHETIC_V1_RESOURCE_BENCHMARK',
        at=datetime.now(timezone.utc).isoformat(), counts_requested=counts, cases=receipts,
        max_rss_mib=max_rss_mib, max_seconds=max_seconds,
        full_junyi_fit=False, cloud_called=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=int)
    parser.add_argument('--counts', type=int, nargs='+', default=[25000, 50000, 100000])
    parser.add_argument('--max-rss-mib', type=int, default=640)
    parser.add_argument('--max-seconds', type=int, default=120)
    parser.add_argument('--summary', default='BENCHMARK.json')
    args = parser.parse_args()
    if args.max_rss_mib > 640 or args.max_seconds > 120 or min(args.counts) < 1 or max(args.counts) > 100000:
        parser.error('Chỉ nhận probes tối đa100k targets,640MiB và120giây.')
    if args.worker is not None:
        if not 1 <= args.worker <= 100000:
            parser.error('Worker count ngoài phạm vi.')
        worker(args.worker, args.max_rss_mib, args.max_seconds)
    else:
        controller(args.counts, args.max_rss_mib, args.max_seconds, args.summary)
