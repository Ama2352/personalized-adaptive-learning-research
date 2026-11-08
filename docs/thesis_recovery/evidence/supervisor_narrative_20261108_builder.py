"""Dựng bản báo cáo theo diễn tiến nghiên cứu; không chạy lại thí nghiệm."""
from pathlib import Path
import hashlib
import html
import json
import re

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PACKET = ROOT/'research_tracking/supervisor_reports/2026-11-08/01_tien_do'
SOURCE_SHA = 'd87468ef6297178ee58a3ed85d6330e0f6e6023078d1dfad85ee2b7963a6a33f'
NATIVE = ROOT/'artifacts/akt/local-tests/akt-research-runner-20261108-01'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    source = (PACKET/'BAO_CAO_NGHIEN_CUU.html').read_bytes()
    assert sha(source) == SOURCE_SHA
    text = source.decode('utf-8')
    figures = re.findall(r'<figure\b.*?</figure>', text, re.S)
    tables = re.findall(r'<div class="table-scroll[^\"]*"[^>]*><table>.*?</table></div>', text, re.S)
    assert len(figures) == 8 and len(tables) == 5
    run_raw = (NATIVE/'method24_run01.json').read_bytes()
    assert sha(run_raw) == 'd7740acd6b9cf59d34e9964ffef69de149af6b48dd822ed51882ec8cb6df4492'
    run = json.loads(run_raw)
    result_raw = (NATIVE/'method24-native01/worker_result.json').read_bytes()
    result = json.loads(result_raw)
    graph_raw = (NATIVE/'method24-native01/graph.json').read_bytes()
    graph = json.loads(graph_raw)
    terminal_raw = (NATIVE/'method24_terminal_observation01.json').read_bytes()
    terminal = json.loads(terminal_raw)
    assert run['status'] == 'ACCEPTED_CONDITIONAL_TRAIN_SURROGATE_NOT_EDGE_TRUTH'
    assert run['actual_solver_calls'] == result['actual_solver_calls'] == 2352
    assert result['edge_summaries'] == result['supported_edges'] == 756
    assert result['oof_rows'] == 272160 and result['graph_edges'] == 31
    assert graph['status'] == 'SUPPORTED_DAG' and len(graph['edges']) == graph['requested_edges'] == 31
    assert terminal['observed_exit_code'] == 0 and terminal['stdout_json']['run_sha256'] == sha(run_raw)
    assert not (NATIVE/'method24_postbudget_failure01.json').exists()
    assert result['teacher_calls'] == result['neural_optimizer_steps'] == result['modal_spend_usd'] == 0
    for name, item in run['artifacts'].items():
        raw = (NATIVE/'method24-native01'/name).read_bytes()
        assert len(raw) == item['bytes'] and sha(raw) == item['sha256']
    assert len(run['artifacts']) == 14
    # Snapshot/inventory trước khi thay bản trình bày; không sửa bằng chứng gốc.
    before = {'BAO_CAO_NGHIEN_CUU.html':source, 'BAO_CAO.md':(PACKET/'BAO_CAO.md').read_bytes()}
    inventory = {name:{'bytes':len(raw),'sha256':sha(raw)} for name, raw in before.items()}
    with (PREP/'supervisor_narrative02d_before_inventory.json').open('x',encoding='utf-8') as f:
        json.dump(inventory,f,ensure_ascii=False,indent=2)
    for name, raw in before.items():
        dest = PREP/('narrative02d_before_'+name)
        with dest.open('xb') as f:f.write(raw)
        assert sha(dest.read_bytes()) == inventory[name]['sha256']
    head = text[:text.index('<body>')]
    head = head.replace('</style>', '@media(max-width:700px){.progress-table caption{display:block;width:100%}.progress-table table,.progress-table tbody,.progress-table tr,.progress-table th,.progress-table td{display:block;width:100%;min-width:0}.progress-table thead{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}.progress-table tr{margin-bottom:1.2rem;border:1px solid var(--line)}.progress-table tbody th{background:var(--pale);padding:.8rem}.progress-table td{padding:.8rem;border-bottom:0}.progress-table td::before{content:attr(data-label);display:block;font-weight:600;color:var(--navy);margin-bottom:.35rem}}\n</style>')
    masthead = re.search(r'<header class="masthead">.*?</header>',text,re.S).group()
    masthead = masthead.replace('Từ hai nghiên cứu đã có, khóa luận tiếp tục tìm nguyên nhân, kiểm tra điều kiện hiệu lực và phát triển cách sử dụng đồ thị theo độ tin cậy.',
        'Báo cáo quá trình đi từ kết quả của hai paper đến các chẩn đoán mới, những điều đã làm rõ và các phép kiểm còn thiếu để kết luận khóa luận.')
    sources = re.search(r'<ol class="sources">.*?</ol>',text,re.S).group()
    body = f'''<body><a class="skip" href="#noi-dung">Đến nội dung</a><main class="page" id="noi-dung">
{masthead}
<nav aria-label="Mục lục"><a href="#boi-canh">Điểm xuất phát</a><a href="#tien-do">Tiến độ hiện tại</a><a href="#chang-1">1. Kiểm nền thí nghiệm</a><a href="#chang-2">2. Tách tác động</a><a href="#chang-3">3. Kiểm điều kiện</a><a href="#chang-4">4. Chuẩn bị giải pháp</a><a href="#con-thieu">Phần còn thiếu</a></nav>

<section id="boi-canh" class="opening"><h2>Điểm xuất phát: hai paper đã cho biết gì?</h2>
<div class="measure"><p>Một hệ thống học tập thích ứng phải trả lời: <strong>với những bài người học đã làm, nên giao bài nào tiếp theo?</strong> Để trả lời, hệ thống ước lượng người học đang biết gì, đối chiếu những kiến thức nền cần có, rồi chọn hoạt động tiếp theo. Đồ thị tiên quyết mô tả quan hệ kiến thức nền ấy. Tuy nhiên, có bản đồ tốt chưa bảo đảm hệ thống sử dụng được nó để chọn bài tốt hơn.</p></div>
{figures[0]}
<div class="measure"><p><strong>Paper 1</strong> đã tách vai trò của đồ thị với vai trò của cách chọn đường đi. Ưu tiên học liên tục trong chương giúp giảm chuyển chương và quay lại chương, nhưng đồ thị mở rộng chưa cải thiện ổn định mức thành thạo. Phương án mở rộng thay cả quan hệ nội chương và liên chương, nên chưa tách riêng hiệu quả của cạnh liên chương. Paper đã gắn tính liên tục của lộ trình với chính sách lựa chọn; khóa luận không coi nhận định đó là phát hiện mới.</p>
<p><strong>Paper 2</strong> đi tiếp vào mô hình ước lượng tri thức. Phần bổ sung có đồ thị cải thiện nhẹ dự báo ở một số nhóm mô phỏng, nhưng chưa phát hiện cải thiện rõ ở hai kết quả học tập chính sau hiệu chỉnh thống kê. Trên Junyi, bước chọn cấu hình phát triển ưu tiên tắt các cơ chế đồ thị đã thử. Paper cũng thừa nhận phép bật/tắt còn gộp nhiều cơ chế, nên chưa tách được phần đóng góp của riêng các cạnh.</p>
<p>Khoảng trống cần giải quyết vì vậy không chỉ là cài một mô hình mạnh hơn. Khóa luận giữ ba câu hỏi trong đề cương: <strong>RQ1</strong> tìm nguyên nhân lợi ích chưa ổn định; <strong>RQ2</strong> xác định khi nào thông tin tiên quyết hữu ích, trung tính hoặc bất lợi; <strong>RQ3</strong> kiểm tra CG-AKT, một cách điều chỉnh ảnh hưởng của đồ thị theo độ tin cậy trên nền AKT.</p></div></section>

<section id="tien-do"><h2>Đến ngày 08/11, nghiên cứu đã đi đến đâu?</h2>
<div class="finding"><strong>Đã có bằng chứng chẩn đoán mới cho RQ1 và RQ2, cùng dữ liệu và bước ước lượng độ tin cậy cạnh đã thực chạy cho RQ3. Chưa RQ nào hoàn tất.</strong> Chưa có phép so sánh các mô hình đã huấn luyện đủ để kết luận CG-AKT cải thiện dự báo, chọn bài hoặc kết quả học.</div>
<div class="table-scroll progress-table" tabindex="0"><table><caption>Phân biệt phần đã làm với kết luận còn thiếu</caption><thead><tr><th>Câu hỏi</th><th>Đã thực hiện và phát hiện</th><th>Chưa chứng minh</th></tr></thead><tbody>
<tr><th scope="row">RQ1 — nguyên nhân</th><td data-label="Đã thực hiện và phát hiện">Đã so riêng đầu vào cạnh trên cùng 1.080 tình huống; dự báo thường đổi nhưng đề xuất thử giữ nguyên. Đã xác định ngoại lệ đủ số lần luyện được dùng trong quyết định cho phép học tiếp.</td><td data-label="Chưa chứng minh">Chưa lượng hóa đầy đủ vai trò của hiệu chỉnh xác suất, ngưỡng thành thạo và chính sách; chưa nối các thay đổi đó thành lợi ích học tập.</td></tr>
<tr><th scope="row">RQ2 — điều kiện</th><td data-label="Đã thực hiện và phát hiện">Đã kiểm giả định về quay lại chương, duy trì kiến thức và thứ tự Junyi; đã làm đối chứng lịch sử và năng lực. Tác động quan sát được không đồng nhất giữa các điều kiện.</td><td data-label="Chưa chứng minh">Chưa có đánh giá đầy đủ qua mức nhiễu đồ thị, nhóm khái niệm và người học mới; chưa suy rộng thành quy luật về học sinh thật.</td></tr>
<tr><th scope="row">RQ3 — giải pháp</th><td data-label="Đã thực hiện và phát hiện">Đã tạo corpus mô phỏng phân vai; đã chạy bước ước lượng mức hỗ trợ dự báo cho các cạnh và tạo đồ thị ứng viên từ TRAIN.</td><td data-label="Chưa chứng minh">Chưa có CG-AKT đã huấn luyện được nghiệm thu và phép so sánh đầy đủ với AKT không đồ thị, AKT đồ thị cố định cùng các mô hình bắt buộc.</td></tr>
</tbody></table></div>
<div class="measure"><p>Diễn tiến dưới đây đi từ việc kiểm lại nền thí nghiệm, đến tách tác động cụ thể, mở rộng điều kiện kiểm tra và chuẩn bị giải pháp mới. Các kết quả kế thừa được giữ riêng với phát hiện bổ sung; những nhánh khảo sát có thể triển khai song song nhưng cùng phục vụ chuỗi lập luận này.</p>
<p><strong>Mốc dự báo đã có trước các chẩn đoán mới:</strong> BKT và GAM-KT đã có kết quả Development trên Junyi. Khi chỉ so các tương tác có dự đoán từ mô hình đã huấn luyện ở cả hai bên, BKT tốt hơn trên cả năm thước đo trong từng fold. Đây là kết quả tham chiếu về dự báo, chưa nói BKT dạy hoặc chọn bài tốt hơn.</p></div>
<details><summary>Xem mốc BKT–GAM-KT và ý nghĩa các thước đo dự báo</summary>
<p class="measure">Các thước đo kiểm tra dự báo đáp án đúng, mức tự tin và độ phù hợp của xác suất với đáp án. Chúng cần thiết để kiểm tra đầu vào của quyết định học tập, nhưng không trực tiếp đo người học đã học thêm bao nhiêu.</p>
{tables[0]}{tables[1]}
<p class="small">Bảng lịch sử dùng 20.706.014 dòng có dự đoán fitted ở cả hai hệ thống, trong 20.706.208 dòng Development ghép được; 194 dòng còn lại nằm trong kiểm tra độ phủ. Trung bình5fold ± độ lệch chuẩn mẫu, không phải khoảng tin cậy95%. ECE có15khoảng đều; Accuracy dùng xác suất ≥0,5, khác ngưỡng thành thạo. Paper2 dùng ECE10khoảng trong thiết kế khác. Không dùng bảng này thay kết quả mô phỏng hoặc kết quả CG-AKT.</p></details></section>

<section id="chang-1"><h2>Chặng 1. Kiểm lại nền thí nghiệm trước khi giải thích kết quả</h2>
<div class="measure"><p>Trước khi hỏi “tại sao đồ thị chưa giúp”, nhóm cần biết các kết quả đang đo có thực sự phân biệt được phương án tốt và kém hay không. Nếu một kết quả chủ yếu do quy tắc điều khiển hoặc công thức mô phỏng quyết định, việc bổ sung mô hình chưa chắc tạo ra bằng chứng mới. Từ đây, nhóm kiểm ba nguy cơ được GVHD lưu ý.</p>
<h3>Lộ trình không quay lại chương: do đồ thị hay do bộ chọn bài?</h3>
<p>Nhóm đối chiếu quy tắc ưu tiên tính liên tục trong Paper1 với mã đang có, rồi dựng một đồ thị nhỏ và diễn biến thành thạo định trước. Mã hiện tại tạo được lộ trình A → B → A. Như vậy, phiên bản này không bảo đảm tuyệt đối rằng mọi lộ trình đều không quay lại chương.</p></div>
{figures[4]}
<div class="measure"><p><strong>Điều đã làm rõ:</strong> cần tách kết quả quan sát trong những lượt chạy của paper khỏi một bảo đảm của thuật toán trong mọi tình huống. <strong>Điều chưa làm rõ:</strong> chưa xác minh đúng phiên bản mã tạo ra PDF Paper1, nên phản ví dụ này không bác bỏ kết quả paper và không xác định tần suất quay lại chương trong điều kiện gốc.</p>
<h3>Giữ lại kiến thức sau hai tuần có cung cấp bằng chứng khác không?</h3>
<p>Tiếp theo, nhóm kiểm công thức quên của Paper2. Khi tiến bộ ròng quanh mức nền cố định không âm, các khái niệm có cùng tốc độ quên và không luyện thêm sau khi kết thúc, tiến bộ ròng còn giữ sau14ngày bằng0,4317105lần tiến bộ ròng cuối lịch. Trong điều kiện ấy, hai số có cùng thứ hạng; không nên đếm chúng như hai xác nhận độc lập về thứ hạng phương án.</p>
<p>Nhưng kết quả học thêm tức thời của Paper2 là phần học được ngay sau luyện, trước các lần quên về sau, khác tiến bộ ròng cuối lịch. Vì vậy, quan hệ tỷ lệ trên <strong>không chứng minh hai kết quả chính của Paper2 dư thừa</strong>. Nhóm còn dựng hai trạng thái và kiểm một cách đọc mức thành thạo phi tuyến: thứ hạng có thể đảo sau14ngày.</p></div>
{figures[5]}
<div class="measure"><p><strong>Phát hiện bổ sung là giới hạn của cách đo, không phải lỗi phần mềm:</strong> cùng một cơ chế quên có thể cho phép đo ít hoặc nhiều khả năng phân biệt, tùy cách đọc trạng thái. Hai trạng thái phản ví dụ được dựng sẵn; chưa chứng minh một chính sách chọn bài thực tế tạo ra chúng hoặc đồ thị giúp duy trì kiến thức tốt hơn.</p>
<h3>Junyi: đồ thị khớp thứ tự luyện có phải đồ thị hữu ích?</h3>
<p>Một nguy cơ khác xuất hiện ở dữ liệu thật: thứ tự luyện của người học Junyi vốn có thể chịu ảnh hưởng của bản đồ kiến thức. Nhóm vì thế kiểm các đối chứng thay cạnh và số quan hệ thật sự được cùng một người học quan sát, trước khi xem việc khớp thứ tự là bằng chứng về chất lượng đồ thị.</p></div>
{figures[7]}
<div class="measure"><p>Trên256người học và12.575tương tác Development, một đối chứng giảm số trường hợp kiến thức nền xuất hiện trước từ575xuống574. Nhưng mẫu số đủ điều kiện cũng giảm từ649xuống645, khiến tỷ lệ gộp tăng. Khi cho mỗi người học trọng số bằng nhau, chiều chênh lệch âm; trên tập cùng đủ điều kiện quan sát, chênh lệch bằng0.</p>
<p><strong>Nhóm đã lượng hóa một nguy cơ kết luận sai do mẫu số và khả năng quan sát.</strong> Chưa thể từ đó kết luận đồ thị thật tốt hơn, đồ thị đối chứng tốt hơn hoặc hai bên tương đương. Tập chung chỉ yêu cầu có quan hệ được cùng quan sát ở mỗi đồ thị, không nhất thiết cùng một cạnh. Đây là liên hệ trên nhật ký luyện, chưa là lợi ích giảng dạy.</p>
<p>Sau bước này, các kết quả của hai paper vẫn được giữ nguyên. Phần tiếp nối phải dùng đối chứng rõ hơn, thay vì quy mọi khác biệt cho chất lượng đồ thị.</p></div></section>

<section id="chang-2"><h2>Chặng 2. Giữ cùng đầu vào để tìm nơi tác động của đồ thị dừng lại</h2>
<div class="measure"><p>Kiểm giả định chưa đủ trả lời RQ1. Nhóm chuyển sang câu hỏi hẹp hơn: nếu chỉ thay các cạnh mà mô hình được nhận, trong khi giữ câu hỏi và lịch sử như nhau, dự báo và đề xuất có đổi không?</p>
<p>Trên Graph-GAM-KT kế thừa từ Paper2, nhóm so nhận đủ cạnh với nhận tập cạnh rỗng; các cơ chế đi kèm vẫn cùng bật. Câu hỏi, đáp án, lịch sử, tham số và trạng thái ban đầu giống nhau; đồ thị của môi trường và bộ chọn bài giữ nguyên. Đây là phần tách mới so với bật/tắt cả gói cơ chế. Nó chưa phải phép so sánh AKT có và không có đồ thị.</p>
<p>Đầu tiên cần xem thông tin cạnh có làm dự báo phù hợp đáp án hơn không. Log Loss phạt trường hợp dự báo sai nhưng quá tự tin; Brier đo độ lệch xác suất so với nhãn. Giá trị thấp hơn thuận lợi hơn, chưa biểu thị lượng kiến thức học thêm. Ba hồ sơ PG, PY và PYH lần lượt là năng lực cao, năng lực thấp và yếu ở phần hàm số trong mô phỏng Paper2.</p></div>
{tables[2]}{figures[1]}
<div class="measure"><p>Kết quả gộp nghiêng nhẹ về đủ cạnh, nhưng ba quỹ đạo của hồ sơ năng lực cao đều cho chiều bất lợi; hai hồ sơ còn lại thuận lợi hơn theo phép đo này. <strong>Chưa có một tác động đồng nhất cho mọi hồ sơ.</strong> Điều đó dẫn đến việc kiểm đầu ra tiếp theo, thay vì dừng ở điểm dự báo trung bình.</p></div>
<div class="finding"><strong>Trong963tình huống xác suất thay đổi,943vẫn giữ đề xuất khái niệm xem trước.</strong> Tổng cộng22/1.080đề xuất thử đầy đủ thay đổi. Thông tin cạnh đã tác động đến dự báo nhưng thường chưa làm hệ thống đề xuất khác trong các tình huống này.</div>
{tables[3]}
<div class="measure"><p>Các số đếm trên là những đầu ra được so riêng, không phải các tầng của một phễu nhân quả. Đề xuất được thử trên bản sao trạng thái, chưa là bài thực sự giao cho người học. Vì vậy, chưa thể kết luận số đề xuất ít đổi đã gây ra kết quả học tập ít đổi.</p>
<p>Để giải thích thêm quyết định “được phép chọn”, nhóm quay lại bộ điều khiển và phân tích bản tái dựng bằng mã hiện có, đã kiểm khớp các đầu ra của quỹ đạo lưu trước đó. Thông tin về điều kiện cho phép chọn được ghi từ bản tái dựng; chưa tìm lại được runner tạo quỹ đạo gốc, nên không coi đây là các trường đã được lưu trực tiếp trong nhật ký gốc. Paper2 cho phép kiến thức nền đáp ứng điều kiện nếu đã được đánh dấu thành thạo <strong>hoặc đã được chọn ít nhất sáu lần</strong>. Trên3.240lượt thuộc27quỹ đạo,500lượt là khái niệm gốc. Trong2.740lượt còn lại,699thỏa mọi kiến thức nền thành thạo, còn2.041cần ngoại lệ đủ số lần luyện.</p></div>
{figures[2]}
<div class="measure"><p>Như vậy, nhóm không chỉ thấy dự báo và đề xuất ít đi cùng nhau, mà còn xác định được một cơ chế điều khiển thực sự được sử dụng: <strong>tập được phép học không chỉ phụ thuộc nhận định thành thạo.</strong> Ngoại lệ này chưa được chứng minh gây lợi, gây hại hoặc che khuất bao nhiêu tác động của đồ thị. Những quỹ đạo trên dùng lại ba khối ngẫu nhiên; không phải hàng nghìn người học độc lập.</p>
<p>Đến đây, RQ1 đã có điểm chẩn đoán cụ thể. Câu hỏi kế tiếp là liệu những quan sát ấy có phụ thuộc lượng lịch sử và đặc điểm người học hay không.</p></div></section>

<section id="chang-3"><h2>Chặng 3. Thay điều kiện người học để kiểm tra kết luận có ổn định không</h2>
<div class="measure"><p>Nhóm tiếp tục bằng hai đối chứng phục vụ RQ2, vẫn dùng bộ ước lượng và quy tắc chọn bài kế thừa từ Paper2. Mục tiêu là phân biệt “đồ thị luôn ít hữu ích” với “đồ thị chỉ hữu ích trong một số điều kiện”.</p>
<h3>Trước hết, thay lượng lịch sử được quan sát</h3>
<p>Nhóm giữ cùng tình huống cần dự báo, rồi rút ngắn phần quá khứ hệ thống được xem. Các trường hợp dùng đầy đủ quá khứ được kiểm khớp với đầu ra gốc trước khi can thiệp. Trong hình, H là thời điểm cần dự báo sau10,50hoặc100lượt; L là số lượt quá khứ được giữ. Chỉ so các cột trong cùng H, vì các H có thể ứng với câu hỏi và đáp án khác nhau.</p></div>
{figures[3]}
<div class="measure"><p><strong>Kết quả không cho một chiều tăng hoặc giảm đều theo lượng lịch sử.</strong> Đây là bằng chứng điều kiện cụ thể, chưa là quy luật chung. Phép rút ngắn còn thay bộ nhớ của bộ chọn bài, nên chưa cô lập riêng bộ nhớ của mô hình theo dõi tri thức.</p>
<h3>Sau đó, tách năng lực chung khỏi cơ chế thiếu nền tảng</h3>
<p>Một nhóm vốn có năng lực cao có thể học tốt dù đồ thị có giúp hay không. Nhóm giữ cấu trúc mạnh/yếu giữa28khái niệm và cùng chuỗi ngẫu nhiên theo khối, rồi thay mức năng lực chung và bật/tắt mức phạt do thiếu kiến thức nền. Phép so lấy lợi thế của đủ cạnh so với rỗng khi bật mức phạt, trừ lợi thế tương ứng khi tắt mức phạt.</p>
<p>Thiết kế có36quỹ đạo và4.320tương tác, dùng lại ba khối ngẫu nhiên. Trục kết quả là tiến bộ ròng trên thang Elo của mô phỏng, không phải điểm kiểm tra học sinh. Giá trị dương mới cho thấy lợi thế tương đối của đồ thị tăng khi bật cơ chế thiếu nền tảng; không phải thành tích tuyệt đối.</p></div>
{figures[6]}
<div class="measure"><p><strong>Việc bật cơ chế thiếu nền tảng không làm lợi thế tương đối của đồ thị tăng nhất quán.</strong> Đồ thị vẫn tạo khác biệt khi tắt mức phạt, nên chưa thể quy mọi lợi thế cho riêng cơ chế tiên quyết. Ở năng lực cao, tương tác bằng0là đối chứng đã được thiết kế dự kiến vì không thiếu nền tảng, không phải một phát hiện bất ngờ.</p>
<p>Đây là so sánh hai chênh lệch trong thế giới mô phỏng có kiểm soát, không phải phân tích trước–sau trên học sinh thật. Cùng chuỗi ngẫu nhiên theo bước không giữ câu hỏi và đáp án giống nhau sau khi các lộ trình tách ra. Ba khối ngẫu nhiên cũng chưa đủ để suy rộng thành quy luật về năng lực.</p>
<p>Những đối chứng này cho thấy hướng đánh giá tiếp theo cần giữ riêng lịch sử, hồ sơ người học và chất lượng đồ thị. Chúng chưa thay thế ma trận đánh giá đồ thị nhiễu và khả năng khái quát mà đề cương yêu cầu.</p></div></section>

<section id="chang-4"><h2>Chặng 4. Biến các chẩn đoán thành điều kiện kiểm chứng CG-AKT</h2>
<div class="measure"><p>Chuỗi kết quả trên dẫn đến giả thuyết RQ3: không nên buộc mô hình tin mọi quan hệ tiên quyết với cùng mức độ. CG-AKT sẽ điều chỉnh ảnh hưởng từng quan hệ và có cổng kiểm soát ảnh hưởng đồ thị, với phương án không dùng đồ thị khi bằng chứng phát triển chưa ủng hộ nó. Đây vẫn là giải pháp cần kiểm chứng.</p>
<p><strong>Việc đầu tiên đã hoàn tất là chuẩn bị dữ liệu đúng môi trường đánh giá.</strong> Junyi có bài tập và từ vựng riêng; checkpoint học trên Junyi không tự trở thành mô hình dùng được trong mô phỏng Toán10. Nhóm đã tạo corpus mô phỏng riêng và tách người học cho huấn luyện, chọn số vòng học, hiệu chỉnh xác suất.</p></div>
{tables[4]}
<div class="measure"><p>Corpus có60người học,12.600tương tác và210lượt mỗi người; đủ84bài tập ở mỗi vai trò. Quy tắc thu thập chọn bài ngẫu nhiên đều, không dùng trạng thái thật để chọn bài. Tuy nhiên, cơ chế học của môi trường vẫn có quan hệ tiên quyết; đây chưa phải tập dữ liệu trung tính với mọi giả định mô phỏng.</p>
<p><strong>Tiếp theo, bước ước lượng mức hỗ trợ cho từng cạnh đã thực chạy trên CPU.</strong> Chỉ48người học TRAIN đi vào việc khớp mô hình. Nhóm xét756quan hệ có hướng có thể có giữa28khái niệm và so mô hình dự báo có/không có thông tin quá khứ của khái niệm cha. Việc chia theo người học giữ dự đoán dùng để chấm nằm ngoài tập dùng khớp từng mô hình.</p>
<p>Lượt chạy hoàn tất2.352lần khớp mô hình, xuất272.160bản ghi dự đoán theo cạnh và tạo đồ thị ứng viên31cạnh theo ngân sách cạnh và quy tắc tránh chu trình đã định trước. Thời gian khoảng45giây trên CPU; chưa có bước huấn luyện neural CG-AKT trong lượt này.</p>
<p><strong>Điểm độ tin cậy hiện đo mức ổn định của lợi ích dự báo có điều kiện.</strong> Nó không phải xác suất một quan hệ tiên quyết là đúng.756quan hệ đủ điều kiện tính không có nghĩa là756quan hệ thật;31cạnh của đồ thị ứng viên cũng không có nghĩa đã khôi phục đúng đồ thị mô phỏng. Chưa đối chiếu khả năng nhận diện cạnh đúng/sai và chưa đưa điểm này vào CG-AKT đã huấn luyện.</p>
<p>Về phần mềm, AKT và các mô hình so sánh tiếp tục được nối vào cùng quy trình dữ liệu, huấn luyện và xuất dự đoán. Cầu nối dữ liệu SAKT đã được kiểm tra, nhưng kiểm thử phần mềm chưa thay phép đánh giá mô hình. Việc còn thiếu bây giờ là hoàn tất và nghiệm thu chuỗi huấn luyện → chọn → huấn luyện lại → hiệu chỉnh → đánh giá chung.</p></div>
<div class="finding"><strong>RQ3 đã tiến từ chuẩn bị dữ liệu sang có thành phần ước lượng từ dữ liệu đã thực chạy xong trên corpus mô phỏng.</strong> Chưa có kết quả để khẳng định CG-AKT hơn AKT không đồ thị hoặc AKT đồ thị cố định.</div></section>

<section id="con-thieu"><h2>Từ tiến độ hiện tại đến kết luận khóa luận còn thiếu gì?</h2>
<div class="measure"><p><strong>Với RQ1,</strong> cần kiểm tra mức tự tin của xác suất quanh ngưỡng thành thạo và tách ảnh hưởng của các cơ chế điều khiển. Mục tiêu là xác định nơi tác động dừng lại, thay vì chỉ thấy hai đầu dự báo và kết quả học khác nhau.</p>
<p><strong>Với RQ2,</strong> cần kiểm tra kết quả ngoài các trường hợp đã khảo sát: thay mức nhiễu và loại cạnh, giữ rõ dữ liệu được cùng quan sát, đánh giá trên người học mới và báo cả trường hợp bất lợi. Các đối chứng mô phỏng cho phép kiểm soát cơ chế, còn Junyi cung cấp bằng chứng dự báo quan sát; hai loại bằng chứng không thay thế nhau.</p>
<p><strong>Với RQ3,</strong> cần hoàn thiện CG-AKT tối thiểu và các mô hình bắt buộc, kiểm chứng confidence trước khi dùng, rồi so không đồ thị / đồ thị cố định / có độ tin cậy / có cổng trên cùng dữ liệu và ranh giới thông tin. Sau đó mới đánh giá quyết định chọn bài và kết quả học vòng kín. Kết quả cổng tắt đồ thị vẫn có giá trị nếu được quy trình đánh giá hỗ trợ.</p>
<p>AKT, SAKT, GKT, GAM-KT, Graph-GAM-KT và BKT tham chiếu vẫn trong phạm vi đề cương, cùng đồ thị chuyên gia, đồ thị học từ dữ liệu, đồ thị gây nhiễu và demo nghiên cứu. Demo và bản thảo tiếp tục được phát triển, nhưng chưa được báo cáo như sản phẩm nghiên cứu đã nghiệm thu.</p>
<p>Như vậy, thành quả hiện tại là <strong>các đối chứng và phép định lượng cụ thể bổ sung cho hai paper</strong>, cùng nền thực nghiệm cho giải pháp mới. Chưa có cơ sở tuyên bố đã chứng minh hiệu quả giáo dục trên học sinh thật hoặc hoàn tất một trong ba RQ.</p></div></section>

<section id="nguon"><h2>Tài liệu nền và giới hạn kế thừa</h2><div class="measure">{sources}
<p>Hai paper cung cấp kết quả kế thừa; các chẩn đoán và đối chứng trong báo cáo là phần phát triển tiếp. Không chạy lại toàn bộ nghiên cứu trước để thay các bảng lịch sử. Chưa xác minh đúng phiên bản mã tạo ra kết quả Paper1; các phản ví dụ trên mã hiện có được giữ riêng và không dùng để bác bỏ PDF.</p>
<p>Các kết quả mô phỏng được hiểu trong cơ chế và số tình huống đã nêu. Phân tích Junyi không tự xác lập lợi ích giảng dạy. Kiểm thử phần mềm, tạo corpus và khớp mô hình ước lượng cạnh được phân biệt với bằng chứng CG-AKT cải thiện kết quả học.</p></div></section>
<footer>Phạm Triều Dương · Hồ Nguyễn Minh Sang — KLTN, 08/11/2026.</footer></main></body></html>'''
    # Bổ sung khoảng cách chữ–số ở prose, không động SVG/tables kế thừa.
    # Nội dung có đơn vị ở đây viết rõ; không dùng phép thay toàn cục lên dữ liệu.
    replacements = {'sau14ngày':'sau 14 ngày','sau14':'sau 14','bằng0,4317105lần':'bằng 0,4317105 lần',
        '14ngày':'14 ngày','Paper1':'Paper 1','Paper2':'Paper 2','Trên256người':'Trên 256 người',
        'và12.575tương':'và 12.575 tương','từ575xuống574':'từ 575 xuống 574','từ649xuống645':'từ 649 xuống 645',
        'bằng0.':'bằng 0.','Trong963tình':'Trong 963 tình','đổi,943vẫn':'đổi, 943 vẫn','cộng22/1.080đề':'cộng 22/1.080 đề',
        'Trên3.240lượt':'Trên 3.240 lượt','thuộc27quỹ':'thuộc 27 quỹ','đạo,500lượt':'đạo, 500 lượt',
        'Trong2.740lượt':'Trong 2.740 lượt','lại,699thỏa':'lại, 699 thỏa','còn2.041cần':'còn 2.041 cần',
        'sau10,50hoặc100lượt':'sau 10, 50 hoặc 100 lượt','giữa28khái':'giữa 28 khái','có36quỹ':'có 36 quỹ',
        'và4.320tương':'và 4.320 tương','tác bằng0là':'tác bằng 0 là','Toán10':'Toán 10',
        'có60người':'có 60 người','học,12.600tương':'học, 12.600 tương','và210lượt':'và 210 lượt',
        'đủ84bài':'đủ 84 bài','Chỉ48người':'Chỉ 48 người','xét756quan':'xét 756 quan','giữa28khái':'giữa 28 khái',
        'tất2.352lần':'tất 2.352 lần','xuất272.160bản':'xuất 272.160 bản','viên31cạnh':'viên 31 cạnh',
        'khoảng45giây':'khoảng 45 giây','đúng.756quan':'đúng. 756 quan','là756quan':'là 756 quan',
        ';31cạnh':'; 31 cạnh','bình5fold':'bình 5 fold','cậy95%':'cậy 95%','có15khoảng':'có 15 khoảng','ECE10khoảng':'ECE 10 khoảng'}
    # Chỉ sửa text ngoài những đoạn hình/bảng được giữ byte-exact.
    tokens = re.split(r'(<figure\b.*?</figure>|<div class="table-scroll[^\"]*"[^>]*><table>.*?</table></div>)',body,flags=re.S)
    for i, token in enumerate(tokens):
        if token.startswith('<figure') or token.startswith('<div class="table-scroll'):continue
        for a,b in replacements.items():token=token.replace(a,b)
        tokens[i]=token
    final = head+''.join(tokens)
    old_svgs = re.findall(r'<svg\b.*?</svg>',text,re.S)
    new_svgs = re.findall(r'<svg\b.*?</svg>',final,re.S)
    assert sorted(map(sha,map(str.encode,old_svgs))) == sorted(map(sha,map(str.encode,new_svgs)))
    assert len(new_svgs) == 8 and all(table in final for table in tables)
    assert not re.search(r'[0-9a-f]{64}|file://|D:[/\\]|artifacts/|research_tracking/',final)
    candidate = PREP/'supervisor_narrative02d_candidate.html'
    with candidate.open('x',encoding='utf-8',newline='\n') as f:f.write(final)
    receipt = {'status':'CANDIDATE_NOT_YET_PUBLISHED','source_html_sha256':SOURCE_SHA,
        'candidate_sha256':sha(candidate.read_bytes()),'candidate_bytes':candidate.stat().st_size,
        'svg_count':8,'all_svg_bytes_preserved':True,'all_old_tables_preserved':True,
        'native_run_sha256':sha(run_raw),'native_result_sha256':sha(result_raw),'native_graph_sha256':sha(graph_raw),
        'native_terminal_sha256':sha(terminal_raw),'new_model_runs':0,'new_simulator_runs':0}
    with (PREP/'supervisor_narrative02d_build_receipt.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
    print(json.dumps(receipt,ensure_ascii=False))


if __name__ == '__main__':
    main()
