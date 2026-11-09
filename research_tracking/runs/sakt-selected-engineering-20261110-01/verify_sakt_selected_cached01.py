"""Đối chiếu artifact đã có, không Torch/load checkpoint hoặc chạy mô hình."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OUTPUT = PREP/'sakt_selected_cached_comparison01.json'
RUNS = tuple(ROOT/'experiments/sakt/results'/n for n in (
    'sakt-selected-engineering10x84-20261110-02', 'sakt-selected-engineering10x84-20261110-03'))


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    need(path.stat().st_size <= 2**20, 'small cached metadata')
    return json.loads(path.read_bytes())


def main():
    need(Path(sys.prefix).resolve() == ROOT/'.venv' and not OUTPUT.exists(), 'new metadata verification in repository venv')
    outer = read(PREP/'sakt-selected-fit05/outer-final.json')
    need(outer['status'] == 'ACCEPTED_ACTUAL_SAKT_SELECTED_ONLY_ENGINEERING' and outer['errors'] == [], 'actual accepted outer')
    need(outer['owned_receipt']['cleanup_accepted'] is True and outer['owned_receipt']['job_active_after_cleanup'] == 0, 'actual Job0')
    before = {}
    for d in RUNS:
        for name in ['selected-terminal.json', 'selected-claim.json', 'selection/predictions.csv', 'selection/targets.csv', 'selection/coverage.json', *('epoch-'+str(i)+'.json' for i in range(1, 7))]:
            before[(d/name).relative_to(ROOT).as_posix()] = sha(d/name)
    epoch_checks = []
    for i in range(1, 7):
        rows = [read(d/('epoch-'+str(i)+'.json')) for d in RUNS]
        fields = ('epoch', 'seed', 'progress', 'selection')
        need(all(rows[0][n] == rows[1][n] for n in fields), 'epoch numeric/objective/population mismatch')
        epoch_checks.append(dict(epoch=i, compared_fields=fields, exact=True,
            checkpoint_raw_sha256=[row['checkpoint_sha256'] for row in rows],
            native_selection_bce=rows[1]['selection']['native_bce_mean'],
            prediction_sha256=rows[1]['selection']['prediction_sha256']))
    exports = {}
    for name in ('predictions.csv', 'targets.csv', 'coverage.json'):
        paths = [d/'selection'/name for d in RUNS]
        need(paths[0].read_bytes() == paths[1].read_bytes(), 'cached export bytes mismatch')
        exports[name] = dict(sha256=sha(paths[0]), bytes=paths[0].stat().st_size, exact_raw_bytes=True)
    claims = [read(d/'selected-claim.json') for d in RUNS]
    terminals = [read(d/'selected-terminal.json') for d in RUNS]
    for terminal in terminals:
        need(terminal['complete_fit_epochs'] == 6 and terminal['selected_epoch'] == 1, 'actual6/best1')
        need(terminal['counters']['returned'] == terminal['counters']['completed'] == 36
             and terminal['counters']['completed_targets'] == 4032, 'actual36/4032')
    need(claims[0]['initial_model_sha256'] == claims[1]['initial_model_sha256'], 'same declared initial model state')
    binary_refs = []
    for d in RUNS:
        path = d/'epoch-1/state.pt'
        digest = sha(path)
        need(digest == read(d/'selected-terminal.json')['checkpoint_sha256'], 'current physical checkpoint byte SHA')
        binary_refs.append(dict(path=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size,
            sha256=digest, physical_bytes_verified=True, deserialized=False, copy=False))
    need(all(sha(ROOT/n) == h for n,h in before.items()), 'cached source unchanged after comparison')
    result = dict(status='VERIFIED_CACHED_EXPORT_AND_SIX_EPOCH_REPORT_PARITY_NO_MODEL',
        source_before=before, source_after=before, epochs=epoch_checks, exports=exports,
        initial_model_sha256=claims[1]['initial_model_sha256'], checkpoint_binary_refs=binary_refs,
        prior_run_wrapper_accepted=False, current_run_wrapper_accepted=True,
        previous_physical_updates=36, accepted_physical_updates=36, total_physical_updates=72,
        previous_train_targets=4032, accepted_train_targets=4032, total_physical_train_targets=8064,
        native_state_tensor_equality_checked=False, new_model_calls=0, new_independent_samples=0,
        limitation_vi='Chỉ đối chiếu báo cáo số học và exports đã lưu. Không suy diễn telemetry đã mất hoặc tensor equality từ checkpoint bytes khác nhau.')
    with OUTPUT.open('xb') as stream:
        stream.write((json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode())
    print(json.dumps(dict(status=result['status'], result_sha256=sha(OUTPUT))))


if __name__ == '__main__':
    main()
