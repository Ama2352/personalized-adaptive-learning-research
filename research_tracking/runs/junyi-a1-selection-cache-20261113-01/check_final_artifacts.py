"""Nghiệm thu selected-fit, population, xuất dự đoán và hai báo cáo bằng file đã tải."""
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


class ReportParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key == 'id':
                self.ids.append(value)


def main():
    output = ROOT / 'experiments/akt/results/modal-junyi-a1-b128-h100-20261113-07'
    terminal = json.loads((output / 'selected-terminal.json').read_text())
    complete = json.loads((output / 'COMPLETE.json').read_text())
    assert sha(output / 'selected-terminal.json') == complete['terminal_sha256']
    assert terminal['status'] == 'JUNYI_A1_SELECTED_ONLY_COMPLETE'
    assert terminal['complete_epochs'] == 12 and terminal['selected_epoch'] == 9
    assert terminal['optimizer_steps'] == 1818 * 12
    assert terminal['trained_targets'] == 13347331 * 12
    best_epoch, best_loss, stale = None, float('inf'), 0
    for row in terminal['history']:
        value = row['validation']
        assert value['targets'] == value['supported'] == 1600343 and value['oov'] == 0
        assert value['population_sha256'] == terminal['validation']['population_sha256']
        if value['native_bce'] < best_loss - .0001:
            best_epoch, best_loss, stale = row['epoch'], value['native_bce'], 0
        else:
            stale += 1
    assert best_epoch == 9 and stale == 3
    assert sha(output / 'checkpoints/epoch-009/state.pt') == terminal['checkpoint_sha256']
    assert terminal['validation'] == terminal['history'][8]['validation']
    predictions = output / terminal['predictions_file']
    digest, lines = hashlib.sha256(), 0
    with predictions.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
            lines += block.count(b'\n')
    assert digest.hexdigest() == terminal['predictions_sha256'] and lines == 1600343
    folder = ROOT / 'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
    html = (folder / 'BAO_CAO_NGHIEN_CUU.html').read_text(encoding='utf-8')
    markdown = (folder / 'BAO_CAO.md').read_text(encoding='utf-8')
    for text in (html, markdown):
        assert 'A1 hoàn tất chọn checkpoint Junyi' in text
        assert '27,7%' in text and '0,00003424' in text
        assert 'Refit' in text and 'A2/A3' in text
    parser = ReportParser()
    parser.feed(html)
    duplicated = [key for key, count in Counter(parser.ids).items() if count > 1]
    assert not duplicated, duplicated
    result = {'status': 'PASS_FINAL_A1_ACCEPTANCE', 'complete_epochs': 12, 'selected_epoch': 9,
              'early_stop_recomputed': True, 'selection_rows_verified': lines,
              'checkpoint_sha256': terminal['checkpoint_sha256'], 'reload_matches_selection': True,
              'reports_updated': True, 'html_duplicate_ids': duplicated,
              'refit_completed': False, 'calibration_completed': False,
              'files': {path.relative_to(ROOT).as_posix(): sha(path) for path in
                        (output / 'selected-terminal.json', predictions, folder / 'BAO_CAO.md',
                         folder / 'BAO_CAO_NGHIEN_CUU.html')}}
    (HERE / 'final-acceptance.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('status', 'complete_epochs', 'selected_epoch', 'selection_rows_verified', 'html_duplicate_ids')}))


if __name__ == '__main__':
    main()
