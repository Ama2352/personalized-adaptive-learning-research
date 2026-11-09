"""Ghi nhận QA đã quan sát và cập nhật chỉ mục, không mở trình duyệt lại."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
assert Path(sys.prefix).resolve() == ROOT / '.venv'
proof_path = ROOT / 'docs/thesis_recovery/evidence/supervisor_masking_update_20261109.json'
index_path = ROOT / 'research_tracking/supervisor_reports/README.md'
map_path = ROOT / 'docs/REPOSITORY_MAP.md'
files = [proof_path, index_path, map_path]
snapshot = PREP / 'supervisor-mask-qa-before-finalize01'
snapshot.mkdir(exist_ok=False)
inventory = []
for index, path in enumerate(files):
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    inventory.append(dict(path=path.relative_to(ROOT).as_posix(), sha256=digest, bytes=len(raw)))
    target = snapshot / (str(index) + '__' + path.name)
    with target.open('xb') as stream:
        stream.write(raw)
    assert hashlib.sha256(target.read_bytes()).hexdigest() == digest
(snapshot / 'inventory-before.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

browser_path = PREP / 'supervisor_masking_managed_browser_QA01.json'
browser = json.loads(browser_path.read_bytes())
assert browser['status'] == 'RENDERED_DESKTOP_AND_MOBILE_CHECKED_OWN_TAB_CLOSED'
assert browser['owned_tab_closed'] and not browser['preview_server_started']
assert browser['desktop']['qa']['overlaps'] == []
assert browser['desktop']['svgCount'] == browser['mobile']['svgCount'] == 11
assert browser['desktop']['tables'] == browser['mobile']['tables'] == 11
assert browser['mobile']['brokenLocalAnchors'] == 0
image = ROOT / browser['screenshot']
assert image.is_file() and image.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
base = ROOT / 'research_tracking/supervisor_reports/2026-11-09/01_tien_do'
html = (base / 'BAO_CAO_NGHIEN_CUU.html').read_text(encoding='utf-8')
old_html = (PREP / 'supervisor-before-masking01/BAO_CAO_NGHIEN_CUU.html').read_text(encoding='utf-8')
svg = re.findall(r'<svg\b.*?</svg>', html, flags=re.DOTALL)
assert len(svg) == 11 and svg[:10] == re.findall(r'<svg\b.*?</svg>', old_html, flags=re.DOTALL)
assert html.count('<table') == 11
ids = re.findall(r'\bid="([^"]+)"', html)
assert len(ids) == len(set(ids))
assert all(anchor in ids for anchor in re.findall(r'href="#([^"]+)"', html))
proof = json.loads(proof_path.read_bytes())
assert proof['status'] == 'SUPERVISOR_STAGE11_UPDATED_STATIC_QA_PENDING_RENDER'
proof['status'] = 'SUPERVISOR_STAGE11_UPDATED_DESKTOP_MOBILE_QA_OBSERVED'
proof['after'] = {name: dict(bytes=(base / name).stat().st_size,
    sha256=hashlib.sha256((base / name).read_bytes()).hexdigest())
    for name in ('BAO_CAO.md', 'BAO_CAO_NGHIEN_CUU.html')}
proof['visual_render'] = True
proof['browser_qa'] = dict(path=browser_path.relative_to(ROOT).as_posix(),
    sha256=hashlib.sha256(browser_path.read_bytes()).hexdigest(),
    desktop_viewport=1280, mobile_viewport=390, owned_tab_closed=True,
    preview_server_started=False,
    geometry_scope='BBox được đo trước hai chỉnh khoảng trắng cuối ở title/footnote. Screenshot sau chỉnh đã được ROOT xem trực tiếp.',
    screenshot=dict(path=image.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(image.read_bytes()).hexdigest()),
    failed_local_render='Giữ logs crashpad của Chrome local tại supervisor-masking-render01; owned Job0, không có screenshot từ lượt này.')
proof_path.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

index_text = index_path.read_text(encoding='utf-8')
first_end = index_text.index('\n\n', index_text.index('\n\n') + 2)
opening = ('Đợt09/11 hiện đã có chặng11 giải thích bước từ nhãn thành thạo đến tập sẵn sàng ban đầu. '
    'Trên cùng1.080cặp thời điểm đã lưu,90cặp có nhãn khác nhau,60cặp có tập R khác nhau và30cặp giữ R. '
    'Đã kiểm lại trực tiếp đủ30trường hợp, gồm18khái niệm không có con trực tiếp và12trường hợp có con đã mang nhãn thành thạo, '
    'trong đó4trường hợp đồng thời thỏa ngoại lệ số lần luyện. Hai file giữ diễn tiến nghiên cứu và phần độ đúng mastery còn thiếu. '
    'HTML có11SVG và11bảng, đã xem desktop1280px/mobile390px và đóng tab kiểm riêng. '
    'Hồ sơ ở [bằng chứng cập nhật](../../docs/thesis_recovery/evidence/supervisor_masking_update_20261109.json).')
index_text = index_text[:index_text.index('\n\n') + 2] + opening + index_text[first_end:]
index_text = index_text.replace('Bổ sung hiện hành09/11: chặng5', 'Mốc xuất bản trước trong ngày09/11, chặng5')
index_path.write_text(index_text, encoding='utf-8')

map_text = map_path.read_text(encoding='utf-8')
old = 'một HTML độc lập với mười biểu đồ'
assert map_text.count(old) == 1
map_text = map_text.replace(old, 'một HTML độc lập với mười một biểu đồ')
old = ('Báo cáo đi từ ngữ cảnh hai paper qua tiến độ và mười chặng đến phần còn phải chứng minh. '
       'Hai chặng mới nhất kiểm điểm tổng hợp trên cùng dòng dữ liệu và giải thích điều kiện không quay lại chương.')
assert map_text.count(old) == 1
map_text = map_text.replace(old,
    'Báo cáo đi từ ngữ cảnh hai paper qua tiến độ và mười một chặng đến phần còn phải chứng minh. '
    'Chặng mới nhất giải thích30thời điểm khác nhãn thành thạo mà giữ tập sẵn sàng ban đầu, giữ rõ các điều kiện chồng lấp. '
    'Các chặng trước kiểm điểm tổng hợp trên cùng dòng dữ liệu và điều kiện không quay lại chương.')
old = ('Bộ kiểm Paper1 hiện đạt72ca, gồm18episode cases. '
       '[Readiness](../research_tracking/reports/paper1_supplied_episode_readiness_20261109.md). '
       'RNG-owned runner và các policy so sánh còn ở bước tiếp theo.')
assert map_text.count(old) == 1
map_text = map_text.replace(old,
    'Mốc supplied core đạt72ca, gồm18episode cases. '
    '[Readiness lịch sử](../research_tracking/reports/paper1_supplied_episode_readiness_20261109.md). '
    'Bộ kiểm hiện hành sau seeded runner đạt85ca, còn matrix policy nghiên cứu chưa chạy.')
map_path.write_text(map_text, encoding='utf-8')
print(json.dumps(dict(status=proof['status'], svg=len(svg), tables=11,
    previous_svg_byte_identical=10, bundle_manifest_sha256='9cbb7a276b750bf079f544ba69a4d0cf1ea28b89140707957630630a20aa9a4b')))
