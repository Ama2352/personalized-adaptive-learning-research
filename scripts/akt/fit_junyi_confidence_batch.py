"""Tái dùng tiến trình CPU, gọi nguyên CLI fitter TRAIN80 đã ghim cho từng child."""
import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]


def pending_children(request, output):
    graph = json.loads((ROOT/request['topology_file']).read_text())
    children = sorted({child for _, child in graph['corrected_edges']})
    return [child for child in children if not
            (output/'children'/hashlib.sha256(child.encode()).hexdigest()/'COMPLETE.json').exists()]


def run_children(args, children, journal):
    """Giữ nguyên source, recipe và đường gọi fit-child của CLI gốc."""
    legacy = runpy.run_path(str(ROOT/'scripts/akt/fit_junyi_confidence.py'))['main']
    for child in children:
        with journal.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(dict(child=child, started=time.monotonic()))+'\n')
        sys.argv = ['fit_junyi_confidence.py', '--request', str(args.request),
                    '--output', str(args.output), '--action', 'fit-child', '--child', child,
                    '--max-seconds', '300', '--max-rows', str(args.max_rows),
                    '--max-rss-mib', str(args.max_rss_mib), '--worker']
        legacy()
        gc.collect()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-seconds', type=int, default=3600)
    parser.add_argument('--max-rows', type=int, default=350000)
    parser.add_argument('--max-rss-mib', type=int, default=768)
    parser.add_argument('--max-children', type=int, default=736)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--journal', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    args.output = args.output.resolve()
    if Path(sys.executable).resolve() != (ROOT/'.venv/Scripts/python.exe').resolve():
        raise ValueError('Chỉ dùng Python .venv local của repository')
    if not args.output.is_relative_to(ROOT/'artifacts/akt/confidence'):
        raise ValueError('Output confidence phải thuộc artifacts/akt/confidence trên D')
    if not (1 <= args.max_seconds <= 3600 and 1 <= args.max_children <= 736
            and 1 <= args.max_rows <= 1000000 and 128 <= args.max_rss_mib <= 1024):
        raise ValueError('Cần giới hạn CPU/RAM hữu hạn')
    request = json.loads(args.request.read_text(encoding='utf-8'))
    children = pending_children(request, args.output)[:args.max_children]
    if args.worker:
        if args.journal is None or args.journal.parent.resolve() != args.output:
            raise ValueError('Journal phải thuộc output của lượt fit')
        run_children(args, children, args.journal)
        return
    if not children:
        print(json.dumps(dict(status='ALL_CHILD_CHECKPOINTS_PRESENT')))
        return
    import psutil
    journal = args.output/('batch-stages-'+str(time.time_ns())+'.jsonl')
    command = [sys.executable, '-u', '-B', str(Path(__file__).resolve()),
               '--request', str(args.request.resolve()), '--output', str(args.output),
               '--max-seconds', str(args.max_seconds), '--max-rows', str(args.max_rows),
               '--max-rss-mib', str(args.max_rss_mib), '--max-children', str(args.max_children),
               '--worker', '--journal', str(journal)]
    env = dict(os.environ, OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
               PYTHONDONTWRITEBYTECODE='1')
    started = time.monotonic()
    process = subprocess.Popen(command, cwd=ROOT, env=env)
    tracked = psutil.Process(process.pid)
    telemetry = journal.with_suffix('.telemetry.jsonl')
    result = dict(status='FAILED', requested_children=len(children),
                  driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    try:
        with telemetry.open('x', encoding='utf-8') as stream:
            while process.poll() is None:
                try:
                    tree = [tracked, *tracked.children(recursive=True)]
                    rss = sum(item.memory_info().rss for item in tree if item.is_running())
                except psutil.NoSuchProcess:
                    continue
                elapsed = time.monotonic()-started
                child_started = started
                if journal.exists():
                    lines = journal.read_text().splitlines()
                    try:
                        child_started = json.loads(lines[-1])['started']
                    except (ValueError, IndexError):
                        pass  # Worker có thể đang ghi dòng kế tiếp.
                available = psutil.virtual_memory().available
                stream.write(json.dumps(dict(seconds=elapsed, rss=rss, available_ram=available))+'\n')
                stream.flush()
                if (rss > args.max_rss_mib*1024**2 or available < 96*1024**2
                        or elapsed > args.max_seconds or time.monotonic()-child_started > 345):
                    raise RuntimeError('Dừng batch theo cap RAM/thời gian; giữ checkpoint child đã hoàn tất')
                time.sleep(1)
        code = process.wait()
        if code:
            raise RuntimeError('Batch worker thất bại, exit='+str(code))
        result['status'] = 'BATCH_COMPLETED'
    finally:
        if process.poll() is None:
            for item in reversed([tracked, *tracked.children(recursive=True)]):
                try:
                    item.terminate()
                except psutil.NoSuchProcess:
                    pass
            process.wait(timeout=10)
        result['seconds'] = time.monotonic()-started
        journal.with_suffix('.result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
