"""Đọc PDF đề cương thật, gắn bản PDF offline và kiểm scope báo cáo hiện hành."""
import base64
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re

from pypdf import PdfReader

from check_a0_update import BUNDLE, Page, REPORT, ROOT, digest


class Attachments(HTMLParser):
    def __init__(self):
        super().__init__()
        self.pdfs = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'a' and values.get('href', '').startswith('data:application/pdf;base64,'):
            self.pdfs.append(values['href'].split(',', 1)[1])


def write_new_or_check(path, value):
    if path.exists():
        assert json.loads(path.read_text(encoding='utf-8')) == value
    else:
        with path.open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)


def check():
    proposal = ROOT/'paper2/DC KLTN0127 23520355&23521338_LeVanTuan.pdf'
    raw = proposal.read_bytes()
    inventory = json.loads((ROOT/'docs/thesis_recovery/evidence/user_documents_20261108_inventory.json').read_text())
    approved = next(row for row in inventory['documents'] if row['id'] == 'proposal')
    assert hashlib.sha256(raw).hexdigest() == approved['sha256']
    reader = PdfReader(proposal)
    assert len(reader.pages) == approved['pages'] == 5
    texts = [' '.join(page.extract_text().split()) for page in reader.pages]
    requirements = {
        'models_page3': (2, ('AKT', 'SAKT', 'GKT', 'GAM-KT', 'Graph-GAM-KT', 'BKT')),
        'metrics_page3': (2, ('Log Loss', 'AUC', 'Brier Score', 'ECE', 'bootstrap', 'Holm')),
        'conditions_page3': (2, ('xóa, thêm hoặc đảo cạnh', 'cold-start', 'ít/nhiều dữ liệu', 'nội chương', 'liên chương')),
        'demo_page4': (3, ('hồ sơ người học', 'độ tin cậy dự báo', 'lộ trình', 'mã nguồn')),
        'deliverables_page5': (4, ('báo cáo KLTN', 'bản thảo bài báo', 'Sprint 1', 'Sprint 6')),
    }
    for name, (index, phrases) in requirements.items():
        assert all(phrase in texts[index] for phrase in phrases), name
    desktop = Path(approved['desktop_source'])
    desktop_sha = digest(desktop) if desktop.is_file() else None
    assert desktop_sha is None or desktop_sha == approved['sha256']
    pdf_audit = dict(status='APPROVED_PDF_READ_DIRECTLY', source=str(proposal.relative_to(ROOT)),
        sha256=approved['sha256'], bytes=len(raw), pages=5, desktop_sha256=desktop_sha,
        checked_requirement_groups={name: dict(page=index+1, phrases=list(phrases))
                                    for name, (index, phrases) in requirements.items()})
    write_new_or_check(BUNDLE/'PROPOSAL_PDF_RECHECK06.json', pdf_audit)

    html_path = REPORT/'BAO_CAO_NGHIEN_CUU.html'
    html = html_path.read_text(encoding='utf-8')
    if 'APPROVED_PROPOSAL_DATA_URI' in html:
        encoded = base64.b64encode(raw).decode('ascii')
        html = html.replace('APPROVED_PROPOSAL_DATA_URI', 'data:application/pdf;base64,'+encoded)
        html_path.write_text(html, encoding='utf-8')
    attachment = Attachments()
    attachment.feed(html)
    assert len(attachment.pdfs) == 1
    assert hashlib.sha256(base64.b64decode(attachment.pdfs[0], validate=True)).hexdigest() == approved['sha256']

    md = (REPORT/'BAO_CAO.md').read_text(encoding='utf-8')
    page = Page()
    page.feed(html)
    page.close()
    assert not page.stack and len(page.ids) == len(set(page.ids))
    assert set(page.anchors) <= set(page.ids)
    assert all(anchor in md for anchor in ('id="history"', 'id="rq1"', 'id="rq2"', 'id="rq3"'))
    text = ' '.join(page.prose)
    claims = ('Từ chọn vòng học đến kết luận trên dữ liệu độc lập', 'Đã chọn vòng 4 hoặc 5',
        'SAKT/GKT có mã và bản chọn mô hình trên 84 tương tác kiểm kỹ thuật',
        'đầu ra bắt buộc', 'Graph-GAM-KT', 'độ ổn định chọn cấu hình', 'phương án chuyển về A0',
        'thêm–xóa–đảo cạnh', 'nội/liên chương', 'Log Loss và Brier Score', 'ECE', 'Holm',
        'luận văn hoàn chỉnh', 'gói tái lập', 'BKT đóng vai trò tham chiếu',
        'cần GVHD xác nhận', 'công bố sau KLTN', 'chưa có kết quả nghiệm thu')
    for claim in claims:
        assert claim.lower() in md.lower() and claim.lower() in text.lower(), claim
    for model, relative in (
        ('SAKT', 'experiments/sakt/results/sakt-selected-engineering10x84-20261110-03/selected-claim.json'),
        ('GKT', 'experiments/gkt/results/gkt-selected-engineering10x84-20261110-01/selected-claim.json')):
        selected = json.loads((ROOT/relative).read_text())
        assert selected['candidate_id'] == model and selected['status'] == 'SELECTED_ONLY_COMPLETE'
        assert selected['full_targets'] == selected['supported_targets'] == 84
        assert selected['refit_started'] is False
    a0 = json.loads((ROOT/'research_tracking/runs/modal-akt-recovery-20261112-01/main60-a0-verification.json').read_text())
    graphs = json.loads((ROOT/'research_tracking/runs/modal-akt-graph-selected-20261112-01/batch-summary.json').read_text())
    assert a0['selected_epoch'] == 5 and a0['refit_complete'] is False
    assert graphs['condition_count'] == 6 and graphs['final_refit_calibration_complete'] is False
    assert set(row['selected_epoch'] for row in graphs['conditions']) == {4, 5}
    assert len(re.findall(r'<svg\s', html)) == 1
    write_new_or_check(BUNDLE/'QA06.json', dict(status='PASS_SCOPE_LIFECYCLE_AND_OFFLINE_PROPOSAL',
        checks=list(claims), approved_pdf_verified=True, embedded_pdf_byte_identical=True,
        required_models_retained=True, baselines_supporting_role_from_proposal=True,
        sakt_gkt_main_benchmark_completed=False, junyi_four_refits_completed=True,
        junyi_numeric_predictions_completed=True, calibration_fit_acceptance_pending=True,
        independent_outer_evaluation_pending=True, visual_browser_tested=False,
        source_or_model_changes=False, figure_modified=False))
    print('PASS — approved PDF, offline attachment, scope, lifecycle, selected artifacts and static HTML')


if __name__ == '__main__':
    check()
