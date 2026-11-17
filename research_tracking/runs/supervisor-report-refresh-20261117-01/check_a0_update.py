"""Kiểm tĩnh báo cáo và metadata A0, không đọc predictions/dataset/model."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
REPORT = ROOT/'research_tracking/supervisor_reports/2026-11-16/01_tien_do'
SOURCE = ROOT/'research_tracking/runs/junyi-calibration-real-20261117-01'


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.ids, self.anchors, self.prose = [], [], [], []
        self.skipped = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag not in ('meta', 'link', 'br', 'hr', 'img', 'input'):
            self.stack.append(tag)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'a' and attrs.get('href', '').startswith('#'):
            self.anchors.append(attrs['href'][1:])
        if tag in ('svg', 'style'):
            self.skipped += 1

    def handle_endtag(self, tag):
        assert self.stack and self.stack.pop() == tag, tag
        if tag in ('svg', 'style'):
            self.skipped -= 1

    def handle_data(self, data):
        if not self.skipped:
            self.prose.append(data)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check():
    result = json.loads((SOURCE/'A0_GPU_RESULT01.json').read_text())
    usage = json.loads((SOURCE/'A0_GPU_USAGE_SUMMARY01.json').read_text())
    diagnostics = json.loads((SOURCE/'A0_NUMERIC_DIAGNOSTICS01.json').read_text())
    cache = json.loads((SOURCE/'CPU_CACHE_RESULT02.json').read_text())['result']
    assert result['status'] == 'STAGE_COMMITTED'
    assert result['result']['counts']['targets'] == 1621484
    assert result['result']['counts']['oov_targets'] == 0
    assert cache['windows']['summary']['learners'] == 15847
    assert round(result['worker_seconds']) == 58
    assert round(diagnostics['timings']['core_seconds']) == 12
    assert round(diagnostics['timings']['inference_seconds'], 2) == 6.88
    assert usage['samples'] == 55 and round(usage['mean_utilization_all'], 1) == 6.2
    assert usage['max_utilization'] == 43
    html = (REPORT/'BAO_CAO_NGHIEN_CUU.html').read_text(encoding='utf-8')
    md = (REPORT/'BAO_CAO.md').read_text(encoding='utf-8')
    page = Page()
    page.feed(html)
    page.close()
    assert not page.stack and len(page.ids) == len(set(page.ids))
    assert set(page.anchors) <= set(page.ids)
    prose = ' '.join(page.prose)
    phrases = ('Số liệu đến 17/11', '1.621.484', '15.847', '58 giây', '6,88 giây',
               '6,2%', '43%', 'mốc 50% chưa đạt', 'chưa có kết quả nghiệm thu',
               'đánh giá độc lập', 'A1–A3 sẽ tiếp tục cùng quy trình')
    for phrase in phrases:
        assert phrase in md and phrase in prose, phrase
    assert html.count('<svg ') == 1
    original_svg = ROOT/'research_tracking/runs/rq12-existing-evidence-20261117-01/rq1-ready-preview-v01.svg'
    status = dict(status='PASS_A0_SOURCE_AND_STATIC_REPORT', checks=list(phrases),
        targets=1621484, learners=15847, source_experiment='A0 full calibration inference',
        calibration_fit_accepted=False, independent_model_comparison_completed=False,
        visual_browser_tested=False, figure_modified=False, original_svg_sha256=digest(original_svg))
    output = BUNDLE/'QA04.json'
    if output.exists():
        assert json.loads(output.read_text(encoding='utf-8')) == status
    else:
        with output.open('x', encoding='utf-8') as stream:
            json.dump(status, stream, ensure_ascii=False, indent=2)
    print('PASS — A0 source counts/timing/usage, HTML structure/anchors, MD/HTML claim agreement')


if __name__ == '__main__':
    check()
