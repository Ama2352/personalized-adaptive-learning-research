"""Kiểm số liệu, HTML tự chứa và render cục bộ bằng Chrome có sẵn."""
import hashlib
import json
import subprocess
from html.parser import HTMLParser
from pathlib import Path

BUNDLE = Path(__file__).resolve().parent
ROOT = BUNDLE.parents[2]
report = ROOT/'research_tracking/supervisor_reports/2026-11-13/BAO_CAO_A0_H100.html'

class CheckHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.ids = []
        self.headings = []
        self.scripts = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'img':
            self.images.append(values.get('src', ''))
        if 'id' in values:
            self.ids.append(values['id'])
        if tag in ('h1', 'h2'):
            self.headings.append(tag)
        self.scripts += tag == 'script'

html = report.read_text(encoding='utf-8')
parser = CheckHTML()
parser.feed(html)
assert len(parser.images) == 1 and parser.images[0].startswith('data:image/png;base64,')
assert parser.headings[0] == 'h1' and parser.headings.count('h1') == 1
assert not parser.scripts and 'sha256' not in html.lower()
for token in ['12 epoch', 'epoch 9', '$5,39', '$21,33', '1.600.343', '26,49%', '0,805990', '0,353580']:
    assert token in html, token
progress = json.loads((BUNDLE/'epoch12-analysis-input.json').read_text())
assert len(progress['progress']['history']) == 12
assert all(t['complete'] and t['valid_targets'] == 13347331 for t in progress['training'])
verification = json.loads((BUNDLE/'modal-junyi-a0-b128-h100-20261112-03-verification.json').read_text())
assert verification['status'].startswith('PASS_')
assert verification['exported_prediction_rows'] == 1600343
stop = json.loads((BUNDLE/'stop-confirmation-final.json').read_text())
assert all(app['state'] == 'stopped' and app['tasks'] == '0' for app in stop['apps'])
model = ROOT/'experiments/akt/results/model-export-a0-batch128-20261112-01/A0_JUNYI_SELECTED.pt'
export = json.loads((BUNDLE/'selected-export-result.json').read_text())
assert hashlib.sha256(model.read_bytes()).hexdigest() == export['checkpoint_sha256']
current_html = (ROOT/'research_tracking/supervisor_reports/2026-11-10/01_tien_do/BAO_CAO_NGHIEN_CUU.html').read_text(encoding='utf-8')
assert current_html.index('<h1') < current_html.index('id="boi-canh"') < current_html.index('id="a0-h100-progress-current"')
current_parser = CheckHTML()
current_parser.feed(current_html)
assert len(current_parser.ids) == len(set(current_parser.ids))

chrome = Path('C:/Program Files/Google/Chrome/Application/chrome.exe')
renders = []
for label, width in [('desktop', 1440), ('narrow600', 600)]:
    profile = ROOT/f'artifacts/figure_runtime/h100-report-{label}'
    profile.mkdir(parents=True, exist_ok=True)
    screenshot = BUNDLE/f'report-{label}.png'
    command = [str(chrome), '--headless', '--disable-gpu', '--no-first-run',
               '--disable-background-networking', '--hide-scrollbars',
               '--no-default-browser-check', '--allow-file-access-from-files',
               f'--user-data-dir={profile}', f'--window-size={width},1100',
               f'--screenshot={screenshot}', report.as_uri()]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = process.communicate(timeout=45)
        assert process.returncode == 0 and screenshot.exists(), stderr.decode(errors='replace')[-500:]
        renders.append(dict(view=label, screenshot=screenshot.name, exit_code=process.returncode))
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=10)

result = dict(status='PASS_STATIC_DATA_AND_RENDER', model_sha_verified=True,
              epochs=12, selected_epoch=9, prediction_rows=1600343,
              current_report_context_before_update=True, standalone_offline=True,
              renders=renders, preview_server_started=False,
              browser_processes_waited=True)
(BUNDLE/'report-check.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
