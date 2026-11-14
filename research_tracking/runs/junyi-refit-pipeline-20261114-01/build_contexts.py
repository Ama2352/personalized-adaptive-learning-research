"""Tiếp tục từ cache90 đã niêm phong và dựng context CPU tuần tự."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'experiments/akt'))
from junyi_staged_io import sha, write_new


def main():
    cache = ROOT / 'artifacts/akt/window-cache/full-refit90-20261114-01'
    manifest = json.loads((cache / 'manifest.json').read_text())
    assert sha(cache / 'manifest.json') == json.loads((cache / 'COMPLETE.json').read_text())['manifest_sha256']
    admission = ROOT / 'artifacts/akt/window-cache/full-refit90-cpu-admission-20261114-01.json'
    admitted = json.loads(admission.read_text())
    assert admitted['key'] == manifest['key']
    encoding = ROOT / 'artifacts/akt/window-cache/full-refit90-20261114-01.encoding.json'
    write_new(HERE / 'refit90-cache-receipt.json', dict(
        status='FULL_JUNYI_REFIT90_WINDOWS_PREPARED_NOT_TRAINED', summary=manifest['summary'],
        manifest_sha256=sha(cache / 'manifest.json'), encoding_sha256=sha(encoding),
        cpu_admission_sha256=sha(admission), recovered_after_receipt_path_error=True,
        failed_preparer_log_sha256=sha(HERE / 'cache90-preparation01.log'),
        note_vi='Cache/encoding đã hoàn tất trước lỗi ghi relative_to. Strict reader đã kiểm toàn bộ261.111record. '
        'Tái dùng cache đã có, không chạy lại tiền xử lý.', neural_training_performed=False))
    state_path = HERE / 'STATE.json'
    state = json.loads(state_path.read_text(encoding='utf-8'))
    state.update(status='BUILDING_REFIT90_GRAPH_CONTEXTS_CPU', active_cpu_session=None,
        window_cache_complete=True, window_records=261111, window_targets=14947674,
        source_receipt_recovered=True)
    for variant in ('a1', 'a2', 'a3'):
        request = json.loads((HERE / f'graph-request-{variant}.json').read_text())
        request.update(admission_file=admission.relative_to(ROOT).as_posix(), admission_sha256=sha(admission))
        request_path = HERE / f'graph-admitted-{variant}.json'
        write_new(request_path, request)
        with (HERE / f'context-{variant}.log').open('x', encoding='utf-8') as log:
            process = subprocess.Popen([sys.executable, '-B', str(ROOT / 'scripts/akt/build_junyi_graph_context_cache.py'),
                                       '--request', str(request_path)], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            state.update(active_graph_variant=variant.upper(), active_cpu_child_pid=process.pid)
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            try:
                code = process.wait(timeout=1500)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                raise
        if code != 0:
            raise RuntimeError('CPU context failed: ' + variant)
        receipt = json.loads((HERE / f'context-{variant}.log').read_text(encoding='utf-8'))
        assert receipt['status'] == 'COMPLETE' and receipt['targets'] == 14947674 and receipt['windows'] == 261111
        assert sha(ROOT / request['output_file']) == receipt['cache_sha256']
        write_new(HERE / f'context-{variant}.receipt.json', receipt)
        state.setdefault('completed_graph_contexts', []).append(variant.upper())
        state.update(active_cpu_child_pid=None, active_graph_variant=None)
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    state['status'] = 'FULL_REFIT90_CPU_CACHES_COMPLETE'
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=state['status'])))


if __name__ == '__main__':
    main()
