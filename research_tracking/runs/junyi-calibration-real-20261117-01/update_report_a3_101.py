"""Nối mốc calibration Junyi4/4 vào báo cáo và giữ rõ bước đánh giá còn lại."""
import base64
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BUNDLE=Path(__file__).resolve().parent


def main():
    accepted=json.loads((BUNDLE/'LOCAL_A3_FIT_ACCEPTANCE101.json').read_text(encoding='utf-8'))
    assert accepted['status']=='A3_LOCAL_CALIBRATION_INDEPENDENT_DRIVE_READBACK_ACCEPTED'
    calibration=accepted['calibration']
    summary=dict(mo_hinh='A3 — CG-AKT có cổng điều tiết ảnh hưởng đồ thị',
        pham_vi='Junyi, fold4, nhóm calibration riêng; đánh giá độc lập còn chờ',
        nguoi_hoc=15847,tuong_tac=calibration['total_targets'],temperature=calibration['temperature'],
        log_loss_truoc=calibration['raw_log_loss'],log_loss_sau=calibration['calibrated_log_loss'],
        nghiem_thu='Đã đọc lại artifact trên Drive Sang và đối chiếu model, cohort và lineage ngày17/11/2026')
    data=(json.dumps(summary,ensure_ascii=False,indent=2)+'\n').encode()
    replacements={
        'A0, A1 và A2 đã hoàn tất hiệu chỉnh xác suất; A3 đang tiếp tục xử lý từ dự báo đã lưu.':
            'Cả A0–A3 đã hoàn tất hiệu chỉnh xác suất trên nhóm người học riêng và được nghiệm thu trên Drive.',
        'A0–A2 đã hiệu chỉnh và xác minh artifact; A3 còn fit hệ số':
            'A0–A3 đã hiệu chỉnh và xác minh artifact',
        'A0–A2 đã fit hệ số và nghiệm thu trên Drive; A3 đang tiếp tục từ dự báo đã sao lưu.':
            'Cả bốn mô hình đã fit hệ số và được nghiệm thu trên Drive.',
        'A0–A2 đã có hệ số hiệu chỉnh được nghiệm thu. A3 còn bước fit hệ số từ các dự báo đã lưu.':
            'Cả A0–A3 đã có hệ số hiệu chỉnh được nghiệm thu trên Drive.',
        'Hiệu chỉnh đã hoàn tất cho ba mô hình Junyi':'Hiệu chỉnh đã hoàn tất cho bốn mô hình Junyi',
        'A2 đã hoàn tất fit và được đọc lại từ Drive để đối chiếu model, nhóm dữ liệu và toàn vẹn artifact. A3 còn bước fit. Các tỷ lệ này thuộc giao thức Junyi fold4 hiện hành.':
            'Bộ hệ số A0–A3 đã được nghiệm thu trên Drive trong giao thức Junyi fold4 hiện hành.',
        'Hoàn tất hiệu chỉnh A3 và đánh giá độc lập A0–A3':'Đánh giá độc lập A0–A3 trên Junyi',
        'hiệu chỉnh và đánh giá dự báo độc lập, hoàn thiện mô hình Grade10':
            'đánh giá dự báo độc lập trên Junyi, học lại và hiệu chỉnh mô hình Grade10',
        'từ các dự báo đã lưu, rồi đánh giá độc lập để so sánh dự báo và độ tin cậy xác suất.':
            'bằng bốn mô hình và hệ số đã đóng băng, giữ cùng nhóm người học và tương tác để so sánh dự báo và độ tin cậy xác suất.',
    }
    directory=ROOT/'research_tracking/supervisor_reports/2026-11-16/01_tien_do'
    prepared={}
    history='17/11 — hoàn tất hiệu chỉnh A3 và khép bước calibration Junyi. Kết quả của cả bốn mô hình đã được đọc lại trên Drive để kiểm đúng model và nhóm dữ liệu. Mốc hiệu chỉnh đạt 4/4. Chặng tiếp theo là đánh giá dự báo trên nhóm người học độc lập.'
    for name in ('BAO_CAO.md','BAO_CAO_NGHIEN_CUU.html'):
        path=directory/name;s=path.read_text(encoding='utf-8')
        for old,new in replacements.items():
            assert old in s,(name,old)
            s=s.replace(old,new)
        if name.endswith('.md'):
            s=s.replace('| Junyi · fit hệ số hiệu chỉnh đã nghiệm thu | 3/4 | 75% |',
                '| Junyi · fit hệ số hiệu chỉnh đã nghiệm thu | 4/4 | 100% |')
            row='| A2 | 1,02953 | 0,358448 | 0,358311 |'
            assert row in s;s=s.replace(row,row+'\n| A3 | 1,02561 | 0,358413 | 0,358310 |')
            previous=next(line for line in s.splitlines() if line.startswith('6. **17/11'))
            s=s.replace(previous,previous+'\n7. **'+history.split('. ')[0]+'.** '+'. '.join(history.split('. ')[1:]))
            row=next(line for line in s.splitlines() if line.startswith('| Hiệu chỉnh |'))
            s=s.replace(row,row.replace('Còn phải thực hiện','Đã hoàn tất trên Junyi fold4'))
            s+='\nNguồn mốc A3 tại [biên bản nghiệm thu trên Drive](../../../runs/junyi-calibration-real-20261117-01/LOCAL_A3_FIT_ACCEPTANCE101.json).\n'
        else:
            s=s.replace('Junyi · fit hệ số hiệu chỉnh đã nghiệm thu</td><td>3/4</td><td>75%',
                'Junyi · fit hệ số hiệu chỉnh đã nghiệm thu</td><td>4/4</td><td>100%')
            row='<tr><td>A2</td><td>1,02953</td><td>0,358448</td><td>0,358311</td></tr>'
            assert row in s;s=s.replace(row,row+'<tr><td>A3</td><td>1,02561</td><td>0,358413</td><td>0,358310</td></tr>')
            previous=next(line for line in s.splitlines() if '<li><strong>17/11 — hoàn tất hiệu chỉnh A2' in line)
            s=s.replace(previous,previous+'\n<li><strong>'+history.split('. ')[0]+'.</strong> '+'. '.join(history.split('. ')[1:])+'</li>')
            row=next(line for line in s.splitlines() if '<tr><td><strong>Hiệu chỉnh</strong>' in line)
            s=s.replace(row,row.replace('Còn phải thực hiện','Đã hoàn tất trên Junyi fold4'))
            link='<p><a download="A3_Ket_qua_hieu_chinh.json" href="data:application/json;base64,'+base64.b64encode(data).decode()+'">Tải số liệu hiệu chỉnh A3 đã nghiệm thu</a></p>'
            anchor='<div class="remaining"><h3>Hiệu chỉnh đã hoàn tất cho bốn mô hình Junyi</h3>'
            assert anchor in s;s=s.replace(anchor,link+'\n'+anchor)
        prepared[path]=s
    (BUNDLE/'A3_CALIBRATION_SUMMARY101.json').write_bytes(data)
    for path,text in prepared.items():path.write_text(text,encoding='utf-8')
    print('REPORTS_CALIBRATION_4_OF_4_UPDATED',flush=True)


if __name__=='__main__':main()
