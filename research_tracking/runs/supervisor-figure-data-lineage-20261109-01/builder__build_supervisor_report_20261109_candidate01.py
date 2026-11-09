"""SOURCE ONLY: ROOT tạo ứng viên09/11 trong prep, chưa publish packet.

Giữ nguyên8SVG và các bảng số liệu HTML08; chỉ thêm một hình2x2 từ cache
đã đóng và cập nhật diễn giải tiến độ. Không model/tests/network/dependency.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OLD = 'research_tracking/supervisor_reports/2026-11-08/01_tien_do/'
BUNDLE = 'research_tracking/runs/rq1-cross-ready-membership-20261109-01/'
PINS = {
    OLD+'BAO_CAO_NGHIEN_CUU.html': 'c911b1311c1b5c3668e8167675249f092c7d4248e0914749add95007fba804c3',
    OLD+'BAO_CAO.md': 'aa2422d6c4bcf220fd58cc1e1ce12cdf4f9708b9dfcc462ab04c0dad424886ab',
    BUNDLE+'manifest.json': '057a968bef91bfb9111002119c06e72b4b67605358a770bcde848e173a3b0919',
    BUNDLE+'summary.json': 'a6860a4f01ea650292bd9c7d237e21048aa0e219e85144c299f3e0e3d1abd3c4',
    BUNDLE+'validation.json': 'deb84f6d340507f9a7c4377faebc6b4894fd186ebb1f044cb6c5c12c95c24789',
    BUNDLE+'report_snapshot.md': '2819ed214aeb366f15935d13756b8e777a43d8825abc4877bfc257af7d4621a8',
    'research_tracking/reports/sakt_research_epoch_readiness_20261109.md': 'cb14ae82444bd01d0d6c19053076bec61c9243e38c02834da77ff81f08356abc',
    'research_tracking/runs/sakt-research-epoch-engineering-20261109-01/manifest.json': '225dd5f7dcab5ca833bf96ac89966c75cb48a1b1e8a627badd2418ff4239492f',
    'artifacts/akt/local-tests/akt-research-runner-20261108-01/edge-artifact-native03-owned/final.json': 'bf103739bafdf83732b465f3f424f58693896a12cead9e96bea323bb16188f99',
    'artifacts/akt/local-tests/akt-research-runner-20261108-01/edge-artifact-native03/result.json': '0b5de848f8f50b214cf5038641d2d71c9c5b21ba96c3409bcdbe3dfcf21089f6',
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_inputs():
    raw = {}
    for relative, pin in PINS.items():
        path = ROOT/relative
        cursor = ROOT
        for part in path.relative_to(ROOT).parts:
            cursor /= part
            need(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(), 'input alias')
        need(path.is_file() and path.stat().st_size <= 2*1024**2, 'bounded frozen input')
        raw[relative] = path.read_bytes()
        need(sha(raw[relative]) == pin, 'frozen input changed: '+relative)
    return raw


def once(text, old, new):
    need(text.count(old) == 1, 'exact unique narrative anchor: '+old[:70])
    return text.replace(old, new, 1)


def svg_blocks(raw):
    return re.findall(rb'<svg\b.*?</svg>', raw, flags=re.DOTALL)


def validate_sources(raw):
    manifest = json.loads(raw[BUNDLE+'manifest.json'])
    need(manifest['status'] == 'completed' and len(manifest['outputs_sha256']) == 32, 'closed32 source bundle')
    for name in ('summary.json', 'validation.json', 'report_snapshot.md'):
        need(manifest['outputs_sha256'][name] == PINS[BUNDLE+name], 'closed output SHA binding')
    need(b'e4e6a262bddcdd3b6b6de8c1115ef0eb54b3240a' in raw[BUNDLE+'report_snapshot.md'], 'fixed-source recovered provenance')
    summary = json.loads(raw[BUNDLE+'summary.json']); validation = json.loads(raw[BUNDLE+'validation.json'])
    need(validation['rows'] == 1080 and validation['groups'] == 16 and validation['joint_cells'] == 128
         and validation['membership_cells'] == 256 and validation['exact_query_label_key_join'] is True
         and validation['old_per_event_flags_exact'] is True and validation['old_marginals_exact'] is True
         and validation['no_dropped_rows'] is True and validation['new_independent_N'] == 0, 'exact all-row cached coverage')
    pooled = summary['groups'][0]
    need(pooled['group'] == 'pooled' and pooled['paired_snapshots'] == 1080, 'pooled1080')
    joint = {row['signature']:row['count'] for row in pooled['joint_MRA_cells']}
    need(joint == {'000':973,'001':17,'010':0,'011':0,'100':30,'101':0,'110':55,'111':5}, 'reviewed joint table')
    cells = {(r,a):sum(n for sig,n in joint.items() if int(sig[1]) == r and int(sig[2]) == a)
             for r in (0,1) for a in (0,1)}
    need(cells == {(0,0):1003,(0,1):17,(1,0):55,(1,1):5}, 'two-by-two exact collapse')
    need(pooled['joint_R_preview_change_membership']['FULL_WINNER_NOT_IN_EMPTY_RECORDED_R'] == 5
         and pooled['own_R_limited_snapshots'] == 0, 'cross-membership source')
    sakt = json.loads(raw['research_tracking/runs/sakt-research-epoch-engineering-20261109-01/manifest.json'])
    need(sakt['status'] == 'completed', 'closed SAKT engineering only')
    final = json.loads(raw['artifacts/akt/local-tests/akt-research-runner-20261108-01/edge-artifact-native03-owned/final.json'])
    child = json.loads(raw['artifacts/akt/local-tests/akt-research-runner-20261108-01/edge-artifact-native03/result.json'])
    need(final['status'] == 'ACCEPTED_ACTUAL_ARTIFACT_READ_ONLY_NOT_MODEL_EFFICACY' and final['error'] is None
         and final['score_count'] == 31 and final['model_calls'] == final['new_solver_calls'] == 0
         and final['child_result_sha256'] == sha(raw['artifacts/akt/local-tests/akt-research-runner-20261108-01/edge-artifact-native03/result.json'])
         and child['source_unchanged'] is True and child['score_count'] == 31 and child['error'] is None,
         'actual data-only confidence read acceptance')
    return joint, cells


def new_figure(cells):
    labels = {(0,0):'1.003', (0,1):'17', (1,0):'55', (1,1):'5'}
    need(all(labels[k].replace('.', '') == str(v) for k,v in cells.items()), 'display numbers from validated cells')
    rects = []
    for r in (0,1):
        for a in (0,1):
            x,y = 280+290*a,115+100*r
            rects.append(f'<rect x="{x}" y="{y}" width="270" height="85" rx="6" fill="{("#edf2f5" if r == 0 else "#e3f0f1")}"/>'
                         f'<text x="{x+135}" y="{y+53}" text-anchor="middle" font-size="32" font-weight="600">{labels[(r,a)]}</text>')
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 390" role="img" aria-labelledby="cross-ready-title cross-ready-desc">'
        '<title id="cross-ready-title">Ready set và đề xuất thử: bốn trường hợp cùng được giữ</title>'
        '<desc id="cross-ready-desc">1080 snapshot pairs: Rgiữ/Agiữ1003;Rgiữ/Ađổi17;Rđổi/Agiữ55;Rđổi/Ađổi5. Không phễu nhân quả.</desc>'
        '<rect width="920" height="390" fill="white"/><g font-family="Segoe UI,Arial,sans-serif" fill="#17324d">'
        '<text x="30" y="35" font-size="21" font-weight="600">Tập cho phép đổi chưa đủ làm đề xuất thử đổi</text>'
        '<text x="415" y="85" text-anchor="middle" font-size="17">Đề xuất thử giữ nguyên</text>'
        '<text x="705" y="85" text-anchor="middle" font-size="17">Đề xuất thử thay đổi</text>'
        '<text x="30" y="165" font-size="18">Tập cho phép giữ nguyên</text>'
        '<text x="30" y="265" font-size="18">Tập cho phép thay đổi</text>'+''.join(rects)+
        '<text x="30" y="345" font-size="17">Cùng 1.080 tình huống; đọc lại mẫu cũ, không tăng số mẫu độc lập.</text>'
        '<text x="30" y="375" font-size="16">Bốn ô là đồng xuất hiện của thay đổi, không phải một chuỗi nguyên nhân.</text></g></svg>')
    ET.fromstring(svg)
    return ('<figure><div class="svg-frame">'+svg+'</div><figcaption>R là tập được ghi trên trạng thái gốc, không phải toàn bộ tập ứng viên sau lọc và cân bằng bên trong bộ chọn bài. Đề xuất thử là tuple khái niệm/bài tập/độ khó trên bản sao, chưa được phục vụ. Không quy các khác biệt còn lại cho riêng điểm xếp hạng; số mẫu độc lập mới bằng 0.</figcaption></figure>')


def make_html(raw, cells):
    original = raw[OLD+'BAO_CAO_NGHIEN_CUU.html']
    old_svgs = svg_blocks(original)
    need(len(old_svgs) == 8, 'exact frozen8 SVGs')
    text = original.decode('utf-8')
    # Date tokens occur outside the historical figures; every old SVG is byte-checked below.
    text = text.replace('08/11/2026', '09/11/2026')
    text = once(text, 'Đến ngày 08/11, nghiên cứu đã đi đến đâu?', 'Đến ngày 09/11, nghiên cứu đã đi đến đâu?')
    text = once(text,
        'Đã so riêng đầu vào cạnh trên cùng 1.080 tình huống; dự báo thường đổi nhưng đề xuất thử giữ nguyên. Đã xác định ngoại lệ đủ số lần luyện được dùng trong quyết định cho phép học tiếp.',
        'Đã so riêng đầu vào cạnh trên cùng 1.080 tình huống. Kiểm tiếp cho thấy 55 lần tập cho phép đổi nhưng đề xuất thử giữ nguyên; 17 lần đề xuất thử đổi dù tập thành thạo và tập cho phép giữ nguyên. Đã xác định ngoại lệ đủ số lần luyện trong bộ điều khiển.')
    text = once(text,
        'Đã tạo corpus mô phỏng phân vai; đã chạy bước ước lượng mức hỗ trợ dự báo cho các cạnh và tạo đồ thị ứng viên từ TRAIN.',
        'Đã tạo corpus mô phỏng phân vai, ước lượng cạnh từ TRAIN và đọc lại điểm cạnh theo đúng hợp đồng dữ liệu. Cầu tính toán huấn luyện SAKT đã được kiểm tra ở mức phần mềm; chưa là kết quả mô hình nghiên cứu.')
    insertion = ('<div class="measure"><h3>Kiểm tra tiếp: thay đổi tập cho phép có đi cùng đề xuất thử?</h3>'
        '<p>Nhóm đọc lại cùng các tình huống trên, ghép đúng câu hỏi, đáp án và thời điểm, thay vì chỉ đặt các tổng số cạnh nhau. '
        '<strong>Trong 60 lần tập cho phép thay đổi, 55 lần đề xuất thử vẫn giữ nguyên.</strong> '
        'Ở chiều ngược lại, 17 lần đề xuất thử thay đổi dù cả tập được đánh dấu thành thạo lẫn tập cho phép giữ nguyên. '
        'Thay đổi tập cho phép vì thế chưa là điều kiện cần hoặc đủ cho thay đổi đề xuất thử trong mẫu này.</p></div>'+new_figure(cells)+
        '<div class="measure"><p>Ở 5 lần cả thành thạo, tập cho phép và đề xuất thử cùng đổi, khái niệm full chọn không nằm trong tập cho phép đã ghi của empty; '
        'khái niệm empty chọn vẫn nằm trong tập của full. Cả 5 lần nằm trong một quỹ đạo của hồ sơ PG. '
        'Các trường hợp không đổi và các hồ sơ còn lại đều được giữ, không chọn riêng trường hợp thuận lợi.</p>'
        '<p>Mỗi đề xuất thử đều thuộc tập cho phép của chính nhánh đó trong mẫu đã lưu. Tuy nhiên, mã tạo mẫu cũ đã dừng nếu điều này bị vi phạm; '
        'không thể nâng nó thành quy luật đúng cho mọi trạng thái. Tập ghi lại cũng chưa cho biết toàn bộ các bước lọc và cân bằng của lần chọn thử. '
        'Đây là chẩn đoán quyết định, chưa chỉ ra tác động nhân quả hoặc lợi ích học tập.</p>'
        '<p>Với nhánh giữ chung câu hỏi này, nhóm đã tìm lại mã chạy gốc và kiểm khớp nhật ký giữa các lần quan sát và đối chứng. '
        'Hồ sơ đó khác với bản tái dựng quỹ đạo vòng kín được trình bày tiếp theo; hạn chế thiếu mã chạy gốc của nhánh sau không áp dụng sang nhánh này.</p></div>')
    anchor = '<div class="measure"><p>Các số đếm trên là những đầu ra được so riêng, không phải các tầng của một phễu nhân quả.'
    text = once(text, anchor, insertion+'\n'+anchor)
    text = once(text,
        'Về phần mềm, AKT và các mô hình so sánh tiếp tục được nối vào cùng quy trình dữ liệu, huấn luyện và xuất dự đoán. Cầu nối dữ liệu SAKT đã được kiểm tra, nhưng kiểm thử phần mềm chưa thay phép đánh giá mô hình. Việc còn thiếu bây giờ là hoàn tất và nghiệm thu chuỗi huấn luyện → chọn → huấn luyện lại → hiệu chỉnh → đánh giá chung.',
        'Về phần mềm, điểm của 31 cạnh đã được đọc lại đúng hợp đồng dữ liệu, không khớp thêm mô hình. Cầu tính toán một epoch của SAKT cũng đã được kiểm tra trên dữ liệu nhỏ. Hai việc này giúp nối các thành phần vào cùng quy trình, nhưng chưa tạo ra một baseline SAKT hoặc CG-AKT đã được huấn luyện và đánh giá. Việc còn thiếu là hoàn tất và nghiệm thu chuỗi huấn luyện → chọn → huấn luyện lại → hiệu chỉnh → đánh giá chung.')
    # Giữ ngữ cảnh trước, tiến độ ngay sau đó rồi mới đến bốn chặng nghiên cứu.
    opening = re.search(r'<section id="boi-canh"[^>]*>.*?</section>', text, flags=re.DOTALL)
    progress = re.search(r'<section id="tien-do"[^>]*>.*?</section>', text, flags=re.DOTALL)
    need(opening and progress and opening.end() < progress.start(), 'unique context/progress ordering')
    result = text.encode('utf-8')
    all_svgs = svg_blocks(result)
    need(len(all_svgs) == 9 and [s for s in all_svgs if s in old_svgs] == old_svgs, 'all8 inherited SVG bytes/order unchanged')
    for s in all_svgs:
        ET.fromstring(s)
    # Preserve every inherited non-progress data table verbatim, including all numeric cells.
    old_tables = re.findall(rb'<table\b.*?</table>', original, flags=re.DOTALL)
    for table in old_tables:
        if b'Ph\xc3\xa2n bi\xe1\xbb\x87t ph\xe1\xba\xa7n' not in table:
            need(table in result, 'inherited numeric table changed')
    need(len(re.findall(r'<section id="chang-[1-4]"', text)) == 4 and '<script' not in text.lower(), 'four stages/static standalone')
    return result, old_svgs


def make_summary(raw):
    text = raw[OLD+'BAO_CAO.md'].decode('utf-8').replace('08/11/2026', '09/11/2026')
    anchor = '**Tiếp theo, nhóm kiểm điều kiện người học.**'
    addition = ('**Trở lại 1.080 tình huống giữ chung câu hỏi, nhóm kiểm nơi quyết định được giữ lại.** Có 55 lần tập cho phép thay đổi nhưng đề xuất thử giữ nguyên; '
        '17 lần đề xuất thử đổi dù cả tập thành thạo và tập cho phép giữ nguyên. Trong 5 lần cả ba đầu ra cùng đổi, '
        'khái niệm full chọn nằm ngoài tập cho phép đã ghi của empty. Đây là đề xuất thử, chưa là bài giao cho người học; '
        'tập ghi lại chưa phản ánh mọi bước lọc của bộ chọn bài và không cho phép quy riêng cho điểm xếp hạng. '
        'Phân tích đọc lại mẫu cũ, không tăng số người học hay mẫu độc lập.\n\n')
    text = once(text, anchor, addition+anchor)
    text = once(text, 'Các pipeline mô hình tiếp tục được hoàn thiện và kiểm tra.',
        'Điểm của 31 cạnh đã được đọc lại theo đúng hợp đồng dữ liệu; cầu tính toán SAKT cũng đã được kiểm tra trên dữ liệu nhỏ. '
        'Đây là chuẩn bị phần mềm, chưa là kết quả SAKT hoặc CG-AKT đã huấn luyện trên corpus nghiên cứu.')
    return text.encode('utf-8')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-name', default='supervisor-report-20261109-candidate01')
    p.add_argument('--provenance-name', default='supervisor_report_20261109_candidate01_provenance.json')
    args = p.parse_args()
    for value in (args.output_name, args.provenance_name):
        need(value and len(value) <= 100 and not any(c in value for c in '/\\:\t\r\n') and value not in ('.','..'), 'direct prep basename')
    raw = read_inputs(); joint, cells = validate_sources(raw)
    html, old_svgs = make_html(raw, cells); summary = make_summary(raw)
    need(len(html) <= 128*1024 and len(summary) <= 16*1024, 'small static report caps')
    output = PREP/args.output_name; provenance_path = PREP/args.provenance_name
    need(not output.exists() and not provenance_path.exists(), 'exclusive candidate; no overwrite/publish')
    source = Path(__file__).resolve(); source_sha = sha(source.read_bytes())
    output.mkdir()
    for name, data in (('BAO_CAO.md',summary),('BAO_CAO_NGHIEN_CUU.html',html)):
        with (output/name).open('xb') as f:
            f.write(data)
    need(read_inputs() == raw and sha(source.read_bytes()) == source_sha, 'input/builder changed during build')
    proof = dict(status='CANDIDATE_ONLY_ROOT_QA_BEFORE_PUBLISH', intended_packet='research_tracking/supervisor_reports/2026-11-09/01_tien_do',
        builder_sha256=source_sha, inputs_sha256=PINS, source_bytes={n:len(b) for n,b in raw.items()},
        old_svg_sha256=[sha(s) for s in old_svgs], old_svg_exact_bytes_preserved=8, output_svg_count=9,
        inputs_sha256_before_after_equal=True, outputs_sha256={n:sha((output/n).read_bytes()) for n in ('BAO_CAO.md','BAO_CAO_NGHIEN_CUU.html')},
        mapping=[dict(feature='RQ1 joint-MRA and cross-membership', source=BUNDLE+'summary.json', pointers=[
            '/groups/0/joint_MRA_cells','/groups/0/joint_R_preview_change_membership/FULL_WINNER_NOT_IN_EMPTY_RECORDED_R',
            '/groups/0/own_R_limited_snapshots'], display_cells=[dict(R_changed=r,preview_changed=a,count=cells[(r,a)]) for r in (0,1) for a in (0,1)],
            counts_MRA=joint, scope='posthoc recordedR/notC-B/previewnotserved/no score-only/newN0'),
            dict(feature='SAKT epoch bridge',source='research_tracking/reports/sakt_research_epoch_readiness_20261109.md',
                 scope='verified tiny software only, no fitted research baseline/efficacy'),
            dict(feature='actual typed31 confidence read',source='artifacts/akt/local-tests/akt-research-runner-20261108-01/edge-artifact-native03-owned/final.json',
                 pointers=['/status','/score_count','/new_solver_calls','/model_calls','/elapsed_seconds'],scope='read-only preparation, not graph truth or RQ3 benefit'),
            dict(feature='fixed-vs-closedloop provenance',source=BUNDLE+'report_snapshot.md',
                 scope='fixed runner recovered; separate closedloop original missing limitation retained unchanged')],
        no_model_training_or_tests_run=True, public_html_contains_no_added_hashes_paths_testcounts=True,
        no_circular_inventory='Inputs list contains frozen sources only; candidate output hashes are separate, not inputs.',
        inherited_source_scope='Old HTML is preserved numeric presentation; this builder does not revalidate its earlier scientific evidence.')
    with provenance_path.open('x',encoding='utf-8') as f:
        json.dump(proof,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(status=proof['status'],candidate_directory=output.relative_to(ROOT).as_posix(),
        provenance_sha256=sha(provenance_path.read_bytes()),outputs_sha256=proof['outputs_sha256'])))


if __name__ == '__main__':
    main()
