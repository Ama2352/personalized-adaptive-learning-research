"""Cập nhật hai báo cáo từ checkpoint/figure đã kiểm, giữ các chặng cũ."""
import argparse
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',required=True)
    parser.add_argument('--final',action='store_true')
    args=parser.parse_args()
    assert args.version.isalnum()
    title='13/11 — A1 đã nối epoch1, có validation toàn selection và training nhanh hơn'
    paragraphs=[
        'Điểm còn thiếu trước đợt này là checkpoint A1 đã học đủ một epoch nhưng chưa hoàn tất validation. '
        'Đường chuẩn bị thông tin đồ thị làm H100 chờ CPU nhiều. Nhóm tập trung giảm thời gian đọc và chuẩn bị dữ liệu, '
        'đồng thời kiểm khả năng giữ lại epoch đã học để tiếp tục thí nghiệm.',
        'Phần dữ liệu selection được đối chiếu trên toàn bộ 1.600.343 lượt trả lời của 15.847 người học, '
        'giữ nguyên input, nhãn, thứ tự và tập target so với tham chiếu A0. Cache selection trên đĩa vẫn chậm hơn '
        'đường raw trong phép kiểm CPU đầy đủ. Cấu hình H100 hiện dùng compact A1 và đọc trước dữ liệu có giới hạn. '
        'Cache trên đĩa được giữ ở mức thử nghiệm. Bộ kiểm nguồn Linux cuối đạt 2.528 ca.',
        'Checkpoint A1 thật được đối chiếu giữa source2 và compact trên CPU, sau đó kiểm trực tiếp trên H100 '
        'với các window có thông tin đồ thị. Loss, gradient, trọng số, Adam và RNG khớp hoàn toàn trong phần kiểm. '
        'Sau khi chạy validation epoch1 trên đủ selection, toàn bộ model, optimizer và RNG vẫn bằng trạng thái '
        'checkpoint gốc. Bước học của epoch1 được giữ lại và counters ghi đúng 13.347.331 target, 1.818 bước.',
        'Để chọn checkpoint, mô hình được chấm trên nhóm selection tách biệt với nhóm cập nhật trọng số. '
        'Log Loss được dùng theo quy tắc đã chốt vì phạt các dự đoán tự tin nhưng sai. '
        'Bản chụp đã kiểm đến epoch6 cho các giá trị lần lượt 0,36000; 0,35689; 0,35573; 0,35555; 0,35484; 0,35434. '
        'Đây là tiến trình chọn checkpoint trên Development. Refit, hiệu chỉnh xác suất và đánh giá độc lập còn chờ.',
        'Epoch2 và epoch3 đều học đủ 13.347.331 target, mất lần lượt 202,10 và 202,64 giây. '
        'Epoch1 source2 trước đó mất 1.343,56 giây trên H100. Mức tăng thông lượng quan sát khoảng 6,65 lần, '
        'với các epoch khác nhau. Validation toàn selection mất khoảng 36,5–36,7 giây mỗi lượt. '
        'GPU-Util theo các cửa sổ đo gần đây khoảng 33–36%, còn dưới mục tiêu 50%, VRAM khoảng 5,8 GB.',
        'Lượt H100 đầu đã dừng đúng giới hạn thời gian và giữ trạng thái gần cuối epoch7. Lượt nối tiếp có trần riêng 3 USD trong tổng ngân sách KLTN 30 USD. Lượt canary đầu dừng sớm do thiếu metadata '
        'chọn shard, đã sửa phụ thuộc và lưu lỗi. Lượt tiếp theo đạt canary CUDA trong 6,22 giây. '
        'Toàn bộ checkpoint hoàn tất đến epoch6 cùng checkpoint epoch7 còn 21 bước đã tải về ổ D và kiểm toàn vẹn. '
        'Kết quả hiện xác nhận training và tiếp nối checkpoint hoạt động trên dữ liệu đầy đủ. '
        'Kết luận RQ3 về tác dụng của đồ thị cần hoàn tất so sánh mô hình và đánh giá độc lập.'
    ]
    if args.final:
        title='13/11 — A1 hoàn tất chọn checkpoint Junyi với dữ liệu so sánh đã kiểm'
        terminal=json.loads((HERE/'validated-history09.json').read_text())
        assert terminal['status']=='JUNYI_A1_SELECTED_ONLY_COMPLETE'
        assert terminal['complete_epochs']==12 and terminal['selected_epoch']==9
        assert terminal['comparison_population_matched'] is True
        paragraphs[3]=(
            'A1 dùng đồ thị cố định đã hoàn tất bước chọn checkpoint trên Junyi, học 12 epoch và chọn epoch 9. '
            'Mỗi epoch dùng đủ 13.347.331 lượt trả lời của 126.774 người học train; selection gồm 1.600.343 lượt '
            'của 15.847 người học tách biệt, cùng 717 mã bài tập. Split, input, target và cấu hình batch128 được giữ '
            'theo hợp đồng so sánh A0. Log Loss được dùng để chọn epoch vì phạt dự đoán tự tin nhưng sai. '
            'Epoch 9 đạt 0,35356185. Quy tắc cố định yêu cầu cải thiện ít nhất 0,0001 và dừng sau ba epoch '
            'liên tiếp không đạt mức này. Epoch 12 có giá trị số học thấp hơn một chút, 0,35352761, '
            'nhưng mức giảm 0,00003424 chưa đạt tiêu chí đổi checkpoint. Vì vậy checkpoint được giữ ở epoch 9.')
        paragraphs[4]=(
            'Sau khi nối nguồn đã kiểm, các epoch 2–6 mất khoảng 202–206 giây train. Các epoch 8–12 mất '
            '182–194 giây, cộng 32–34 giây validation toàn selection, tổng khoảng 3,6–3,8 phút. '
            'Epoch 1 của bản cài đặt trước tối ưu mất 1.343,56 giây. So sánh này dùng các epoch khác nhau trên H100. '
            'GPU-Util trong các cửa sổ đang training khoảng 35–38%, VRAM khoảng 5,8 GiB. '
            'Trung bình toàn khoảng lấy mẫu của hai lượt H100 khoảng 27,7%, gồm cả admission, validation '
            'và xuất dự đoán; số này thấp hơn trung bình các cửa sổ đang train. '
            'GPU còn chờ CPU ở một số bước. Kiểm đầu vào, chuyển tensor về CPU để kiểm lặp và đóng gói '
            'artifact là các phần cần tiếp tục tách khỏi thời gian giữ GPU. Việc tách này chưa áp dụng vào lượt vừa chạy.')
        paragraphs[5]=(
            'Checkpoint epoch 9 đã được nạp lại và chấm lại đủ selection. Tập target, xác suất và Log Loss '
            'khớp lượt validation đã dùng chọn checkpoint. Toàn bộ checkpoint, 1.600.343 dự đoán selection '
            'và logs đã tải về ổ D, kiểm toàn vẹn; H100 đã dừng. Một lượt nối gặp lỗi đường dẫn khi import '
            'bộ khởi chạy, được dừng và sửa trước lượt thành công. Bước chọn epoch A1 đã hoàn tất. '
            'Refit, hiệu chỉnh xác suất, đánh giá độc lập và các điều kiện Junyi A2/A3 còn chờ. '
            'Kết quả selection này chưa đủ kết luận đồ thị cải thiện RQ3.')
    heading='## '+title
    old_heading='## 13/11 — A1 đã nối epoch1, có validation toàn selection và training nhanh hơn'
    md=heading+'\n\n'+'\n\n'.join(paragraphs)+'\n\n[Hồ sơ nối A1 và số liệu nguồn](../../../runs/junyi-a1-selection-cache-20261113-01/README.md)\n\n'
    folder=ROOT/'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
    path=folder/'BAO_CAO.md'
    with path.open(encoding='utf-8',newline='') as stream:text=stream.read()
    if args.final:text=text.replace(old_heading,heading,1)
    if heading in text:
        start=text.index(heading);end=text.index('## ',start+len(heading))
    else:start=end=text.index('## 13/11 — cache A1')
    with path.open('w',encoding='utf-8',newline='') as stream:stream.write(text[:start]+md.replace('\n','\r\n')+text[end:])
    svg=(HERE/('a1-resume-h100-'+args.version+'.svg')).read_text(encoding='utf-8')
    svg=svg[svg.index('<svg'):]
    for identifier in sorted(re.findall(r'\bid="([^"]+)"',svg),key=len,reverse=True):
        svg=svg.replace('id="'+identifier+'"','id="a1-resume-'+identifier+'"').replace('url(#'+identifier+')','url(#a1-resume-'+identifier+')').replace('href="#'+identifier+'"','href="#a1-resume-'+identifier+'"')
    block='<section id="a1-continued-h100-20261113"><h2>'+title+'</h2>'+''.join('<p>'+p+'</p>' for p in paragraphs[:5])
    block+='<figure>'+svg+'<figcaption>Đo training H100 và quá trình chọn checkpoint. Thời gian dùng các epoch khác nhau; selection phục vụ lựa epoch theo quy tắc cố định.</figcaption></figure>'
    block+=''.join('<p>'+p+'</p>' for p in paragraphs[5:])+'</section>\r\n'
    path=folder/'BAO_CAO_NGHIEN_CUU.html'
    with path.open(encoding='utf-8',newline='') as stream:text=stream.read()
    marker='<section id="a1-continued-h100-20261113">'
    if marker in text:
        start=text.index(marker);end=text.index('<section id="a1-graph-cache-integrated-20261113">',start)
    else:start=end=text.index('<section id="a1-graph-cache-integrated-20261113">')
    text=text[:start]+block+text[end:]
    text=text.replace('<title>Báo cáo nghiên cứu KLTN — 12/11/2026</title>','<title>Báo cáo nghiên cứu KLTN — 13/11/2026</title>')
    with path.open('w',encoding='utf-8',newline='') as stream:stream.write(text)
    entry='## '+title+'\n\n[Hồ sơ](LINK) giữ source Gate 2.528 ca, toàn selection 1.600.343 target khớp, '
    entry+='checkpoint epoch1 được giữ nguyên qua validation và nối H100. Hai epoch mới mất khoảng 202 giây, '
    entry+='bản chụp đến epoch6. Checkpoint đã tải D, H100 đầu đã dừng. GPU 33–36%, đang nối gần cuối epoch7 cùng source.\n\n'
    if args.final:
        entry='## '+title+'\n\n[Hồ sơ](LINK) giữ Gate2.528ca, parity checkpoint thật CPU/CUDA, '
        entry+='A1 Junyi selected-fit hoàn tất12epoch/chọn9 theo min_delta0,0001, reload/prediction khớp. '
        entry+='Train mới182–206giây/epoch, GPU gần đây35–38%. Mọi checkpoint/predictions/logs đã tảiD, '
        entry+='H100 dừng. Refit/calibration/đánh giá độc lập và A2/A3 Junyi còn chờ.\n\n'
    for path,link in [(ROOT/'docs/REPOSITORY_MAP.md','../research_tracking/runs/junyi-a1-selection-cache-20261113-01/README.md'),
                      (ROOT/'research_tracking/reports/README.md','../runs/junyi-a1-selection-cache-20261113-01/README.md')]:
        with path.open(encoding='utf-8',newline='') as stream:text=stream.read()
        if args.final:text=text.replace(old_heading,heading,1)
        if heading in text:
            start=text.index(heading);end=text.index('## ',start+len(heading))
        else:start=end=text.index('## 13/11 — cache A1')
        with path.open('w',encoding='utf-8',newline='') as stream:stream.write(text[:start]+entry.replace('LINK',link).replace('\n','\r\n')+text[end:])
    print('Updated both reports and evidence indices from verified snapshot')


if __name__=='__main__':main()

