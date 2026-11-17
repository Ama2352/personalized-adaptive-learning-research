"""Nối mốc A2 đã nghiệm thu vào hai báo cáo cho GVHD."""
import base64
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BUNDLE=Path(__file__).resolve().parent


def main():
    accepted=json.loads((BUNDLE/'LOCAL_A2_FIT_ACCEPTANCE100.json').read_text(encoding='utf-8'))
    assert accepted['status']=='A2_LOCAL_CALIBRATION_INDEPENDENT_DRIVE_READBACK_ACCEPTED'
    calibration=accepted['calibration']
    summary=dict(mo_hinh='A2 — AKT có trọng số độ tin cậy cạnh',
        pham_vi='Junyi, fold4, nhóm calibration riêng; đánh giá độc lập còn chờ',
        nguoi_hoc=15847,tuong_tac=calibration['total_targets'],
        temperature=calibration['temperature'],log_loss_truoc=calibration['raw_log_loss'],
        log_loss_sau=calibration['calibrated_log_loss'],
        nghiem_thu='Đã đọc lại artifact trên Drive Sang và đối chiếu binding, số target, toàn vẹn dữ liệu ngày17/11/2026')
    data=(json.dumps(summary,ensure_ascii=False,indent=2)+'\n').encode()
    (BUNDLE/'A2_CALIBRATION_SUMMARY100.json').write_bytes(data)
    files=ROOT/'research_tracking/supervisor_reports/2026-11-16/01_tien_do'
    replacements={
        'A0/A1 đã hoàn tất hiệu chỉnh xác suất; A2/A3 đã lưu đủ dự báo để tiếp tục.':
            'A0, A1 và A2 đã hoàn tất hiệu chỉnh xác suất; A3 đang tiếp tục xử lý từ dự báo đã lưu.',
        'A0/A1 đã hiệu chỉnh và xác minh artifact; A2/A3 còn fit hệ số':
            'A0–A2 đã hiệu chỉnh và xác minh artifact; A3 còn fit hệ số',
        'A0/A1 đã fit hệ số; A2/A3 đã sao lưu đầy đủ dự báo để tiếp tục bước này.':
            'A0–A2 đã fit hệ số và nghiệm thu trên Drive; A3 đang tiếp tục từ dự báo đã sao lưu.',
        'A0/A1 đã có hệ số hiệu chỉnh được nghiệm thu. A2/A3 còn bước fit hệ số từ các dự báo đã lưu.':
            'A0–A2 đã có hệ số hiệu chỉnh được nghiệm thu. A3 còn bước fit hệ số từ các dự báo đã lưu.',
        'Hiệu chỉnh đã hoàn tất cho hai mô hình Junyi':'Hiệu chỉnh đã hoàn tất cho ba mô hình Junyi',
        'Dự báo số A2/A3 đã được lưu đầy đủ và kiểm toàn vẹn trên Drive; hệ số hiệu chỉnh của hai mô hình còn chờ fit.':
            'A2 đã hoàn tất fit và được đọc lại từ Drive để đối chiếu model, nhóm dữ liệu và toàn vẹn artifact. A3 còn bước fit. Các tỷ lệ này thuộc giao thức Junyi fold4 hiện hành.',
        'Hoàn tất hiệu chỉnh A2/A3 và đánh giá độc lập A0–A3':
            'Hoàn tất hiệu chỉnh A3 và đánh giá độc lập A0–A3',
    }
    for name in ('BAO_CAO.md','BAO_CAO_NGHIEN_CUU.html'):
        path=files/name;s=path.read_text(encoding='utf-8')
        for old,new in replacements.items():
            assert old in s,(name,old)
            s=s.replace(old,new)
        if name.endswith('.md'):
            s=s.replace('| Junyi · fit hệ số hiệu chỉnh đã nghiệm thu | 2/4 | 50% |',
                '| Junyi · fit hệ số hiệu chỉnh đã nghiệm thu | 3/4 | 75% |')
            old='| A1 | 1,02635 | 0,358434 | 0,358324 |'
            assert old in s;s=s.replace(old,old+'\n| A2 | 1,02953 | 0,358448 | 0,358311 |')
            history=next(line for line in s.splitlines() if line.startswith('5. **17/11'))
            s=s.replace(history,history+'\n6. **17/11 — hoàn tất hiệu chỉnh A2 trên CPU local.** A2 đã được đối chiếu đầy đủ trên cùng 1.621.484 tương tác và nghiệm thu artifact trên Drive. Mốc hiệu chỉnh đạt 3/4 mô hình. A3 đang xử lý tiếp; so sánh hiệu quả dự báo còn cần nhóm đánh giá độc lập.')
            s+='\nNguồn mốc A2 tại [biên bản nghiệm thu trên Drive](../../../runs/junyi-calibration-real-20261117-01/LOCAL_A2_FIT_ACCEPTANCE100.json).\n'
        else:
            s=s.replace('Junyi · fit hệ số hiệu chỉnh đã nghiệm thu</td><td>2/4</td><td>50%',
                'Junyi · fit hệ số hiệu chỉnh đã nghiệm thu</td><td>3/4</td><td>75%')
            old='<tr><td>A1</td><td>1,02635</td><td>0,358434</td><td>0,358324</td></tr>'
            assert old in s;s=s.replace(old,old+'<tr><td>A2</td><td>1,02953</td><td>0,358448</td><td>0,358311</td></tr>')
            history=next(line for line in s.splitlines() if '<li><strong>17/11 — đưa mô hình' in line)
            s=s.replace(history,history+'\n<li><strong>17/11 — hoàn tất hiệu chỉnh A2 trên CPU local.</strong> A2 đã được đối chiếu đầy đủ trên cùng 1.621.484 tương tác và nghiệm thu artifact trên Drive. Mốc hiệu chỉnh đạt 3/4 mô hình. A3 đang xử lý tiếp; so sánh hiệu quả dự báo còn cần nhóm đánh giá độc lập.</li>')
            download='<p><a download="A2_Ket_qua_hieu_chinh.json" href="data:application/json;base64,'+base64.b64encode(data).decode()+'">Tải số liệu hiệu chỉnh A2 đã nghiệm thu</a></p>'
            anchor='<div class="remaining"><h3>Hiệu chỉnh đã hoàn tất cho ba mô hình Junyi</h3>'
            assert anchor in s;s=s.replace(anchor,download+'\n'+anchor)
        path.write_text(s,encoding='utf-8')
    state_path=BUNDLE/'STATE.json';state=json.loads(state_path.read_text(encoding='utf-8'))
    state['status']='A0_A1_A2_CALIBRATION_ACCEPTED_A3_JOIN_AUDIT_PENDING'
    state['active_cpu_job'].update(phase='fit_accepted',accepted=True,acceptance='LOCAL_A2_FIT_ACCEPTANCE100.json')
    state['calibration_acceptance_current']={'accepted':['A0','A1','A2'],'pending':['A3'],'count':3,'total':4,'percentage_of_phase':75,'scope':'Junyi fold4 calibration10'}
    state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('REPORTS_A2_CALIBRATION_3_OF_4_UPDATED',flush=True)


if __name__=='__main__':main()
