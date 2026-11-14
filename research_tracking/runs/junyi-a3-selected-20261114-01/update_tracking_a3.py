"""Nối kết quả A3 đã nghiệm thu vào các chỉ mục hiện hành, giữ lịch sử cũ."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def prepend(path, section):
    original = path.read_bytes()
    position = original.index(b'\n') + 1
    path.write_bytes(original[:position] + ('\n' + section.strip() + '\n\n').encode('utf-8') + original[position:])


def main():
    read = lambda path: json.loads(path.read_text(encoding='utf-8'))
    acceptance = read(HERE / 'a3-final-acceptance.json')
    assert acceptance['status'] == 'PASS_A3_SELECTED_FIT80_ARTIFACT_AND_PREDICTION_CONTRACT'
    performance = read(HERE / 'a3-final-performance.json')
    gate = read(HERE / 'a3-gate-selection-audit.json')
    billing = read(HERE / 'billing-after.json')
    ledger = read(ROOT / 'research_tracking/COMPUTE_BUDGET.json')
    assert ledger['new_allocations'] == []
    native_bce = read(HERE / 'a3-selection-metrics.json')['native_epoch_selection_bce']
    summary = (f"A3 đã hoàn tất {acceptance['complete_epochs']} epoch, chọn epoch {acceptance['selected_epoch']}, "
        'học đủ TRAIN80 13.347.331 target mỗi epoch. Đã kiểm đủ 1.600.343 dự đoán selection, '
        'target/order/probability identity, 0 OOV, checkpoint/Adam/RNG và gói model bốn file trên D. '
        f'Log Loss native selection {native_bce:.8f}. A0–A3 expert đã hoàn tất selected-fit, '
        'đánh giá độc lập và các bước cuối còn chờ.')
    resource = (f"Hai lượt A3 có tổng function {performance['gpu_function_seconds_total'] / 60:.2f} phút, "
        f"mẫu NVML trung bình {performance['mean_sampled_gpu_utilization']:.2f}%, "
        f"VRAM đỉnh {performance['peak_vram_mib']:.0f} MiB. H100 đã dừng trước tải/nén artifact. "
        'Mục tiêu GPU trung bình trên 50% còn thiếu. Lượt đầu mất kết nối local, '
        'server đã kết thúc đúng giới hạn và đã phục hồi checkpoint partial epoch7/bước271. '
        f"Metered toàn workspace {float(billing['billing']['metered_cost']):.2f} USD, billed0. "
        f"Cận lịch sử {ledger['historical_usage_reserved_upper_usd']:.4f} USD cộng dự phòng "
        f"{ledger['safety_and_final_inference_reserve_usd']:.2f} USD nằm trong trần toàn KLTN30USD.")
    evidence = '[Hồ sơ A3](runs/junyi-a3-selected-20261114-01/README.md)'
    accepted = '[nghiệm thu](runs/junyi-a3-selected-20261114-01/a3-final-acceptance.json)'
    comparison = '[đối chiếu](runs/junyi-a3-selected-20261114-01/a3-comparison-audit.json)'
    for filename, heading, content in (
        ('RESEARCH_PROGRESS.md', 'Mốc 14/11 — A0–A3 expert Junyi đã selected-fit, A3 đã xuất model',
         summary + '\n\n' + resource + '\n\n' + evidence + ', ' + accepted + ', ' + comparison +
         '. Đã cập nhật hai báo cáo GVHD và giữ figure SVG/PNG/CSV cùng nguồn. '
         'Refit/calibration, graph-off, ổn định đa seed, perturbation, learned-graph và kết quả vòng kín còn chờ.'),
        ('EVIDENCE_INDEX.md', '14/11 — A3 selected-fit, model và cơ chế cổng đã lưu',
         evidence + ', ' + accepted + ' và ' + comparison + '. ' + summary + '\n\n' +
         f"[Thống kê gate CPU](runs/junyi-a3-selected-20261114-01/a3-gate-selection-audit.json) có "
         f"{gate['active_targets']} target với ngữ cảnh đủ điều kiện trên toàn selection. "
         'Đây là mô tả từ checkpoint/cache, kiểm CUDA riêng và graph-off độc lập còn chờ. '
         'Hồ sơ giữ cả lỗi mạng local, bằng chứng server dừng, resume và mọi checkpoint/predictions trên D.'),
        ('EXPERIMENT_LEDGER.md', 'Mốc 14/11 — A3 Junyi học xong và đóng hai lượt H100',
         summary + '\n\n' + resource + '\n\n' + evidence + ' và ' + accepted +
         '. Lượt01 có115artifact, lượt02 có216artifact đã tải/kiểm. '
         'Chỉ sử dụng TRAIN80/selection, không truy cập calibration, outer validation hoặc Holdout.'),
        ('CLAIM_EVIDENCE_MATRIX.md', 'Mốc 14/11 — A3 đã học thật, kết luận hiệu quả còn chờ đánh giá độc lập',
         'CLM-RQ3-JUNYI-A3-SELECTED-FIT80-20261114. ' + summary + '\n\n' + accepted + ' và ' + comparison +
         ' ghim cùng dữ liệu, 27 trường training, seed và backbone khởi tạo. '
         'Các điểm selection A0–A3 gần nhau, một seed. A0 chỉ checkpoint9 đã replay batch128, '
         'ranking đầy đủ còn chờ. Thống kê gate CPU không thay cho đối chứng graph-off, '
         'CI learner-level hoặc kết quả vòng kín. Chưa kết luận lợi ích nhân quả hay tương đương thống kê.')
    ):
        prepend(ROOT / 'research_tracking' / filename, '## ' + heading + '\n\n' + content)
    prepend(ROOT / 'research_tracking/reports/README.md',
        '## 14/11 — A3 hoàn tất selected-fit, đã cập nhật báo cáo GVHD\n\n'
        '[Hồ sơ](../runs/junyi-a3-selected-20261114-01/README.md) và '
        '[nghiệm thu](../runs/junyi-a3-selected-20261114-01/a3-final-acceptance.json) giữ ' + summary +
        ' Có figure SVG/PNG/CSV, thống kê gate CPU, hai lượt H100 đã dừng và '
        '[HTML GVHD](../supervisor_reports/2026-11-10/01_tien_do/BAO_CAO_NGHIEN_CUU.html) đã cập nhật.')
    prepend(ROOT / 'docs/REPOSITORY_MAP.md',
        '## 14/11 — A3 hoàn tất selected-fit, đủ A0–A3 expert trên Junyi\n\n'
        '[Hồ sơ A3](../research_tracking/runs/junyi-a3-selected-20261114-01/README.md) giữ ' + summary +
        ' Model chính tại `experiments/akt/results/model-export-a3-batch128-20261114-01/`. '
        'Đã có figure và hai báo cáo GVHD cập nhật. Đọc STATE/CLOSEOUT_MANIFEST trước công việc tiếp theo.')
    tasks_path = ROOT / 'docs/thesis_recovery/TASKS.json'
    tasks = read(tasks_path)
    tasks['latest_authorization_vi'] = ('Người dùng14/11 cho phép chuẩn bị và training A3, '
        'giữ cấu hình A0–A2, trần toàn KLTN30USD, lưu checkpoint/artifact và cập nhật report. '
        'Hai lượt A3 đã đóng, nhiệm vụ tiếp theo vẫn theo phạm vi người dùng giao và ledger hiện hành.')
    task = next(item for item in tasks['tasks'] if item['id'] == 'AKTJ02')
    task['previous_status_before_a3_20261114'] = task['status']
    task['status'] = 'PARTIALLY_VERIFIED_A0_A1_A2_A3_EXPERT_SELECTED_COMPLETE_FINAL_EVALUATION_PENDING'
    task['verification_steps'] = ('A0–A3 expert Junyi đều12epoch/chọn9. A3 Gate numerical2615, controller41ca riêng, '
        'đủTRAIN80/1.600.343prediction, strict chronology/population/probability khớp,0OOV, '
        'checkpoint/Adam/RNG và sampler partial271 đã kiểm. Đã replay early stopping từ history, '
        'export và hai báo cáo/figure. Thống kê gateCPU riêng, refit/calibration/finaleval còn chờ.')
    task['status_change_reason_vi'] = ('Đã nghiệm thu A3 thật, tải216artifact cuối trênD, '
        'so khớp A0–A2 và xuất model bốn file. Giữ giới hạn selection/mộtseed và A0rankingbatch1.')
    task['blockers'] = [
        'Refit/calibration, learned-graph, đủ baseline và đánh giá độc lập còn cần nghiệm thu',
        'A0 chưa replay toàn ranking epoch bằng batch128',
        'RQ3 còn graph-off/perturbation/ổn định/quyết định và vòng kín',
        'Đối soát dự toán và chọn workload có ích trước khoản Modal tiếp theo trong trần30USD']
    task['verification_evidence'] = 'research_tracking/runs/junyi-a3-selected-20261114-01/a3-final-acceptance.json'
    tasks_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    note = ('\n## Kết quả đã nghiệm thu\n\n' + summary + '\n\n' + resource + '\n\n'
        '`a3-selection-metrics.json` tái chấm prediction bằng hàm metrics chung GAM-KT. '
        '`a3-comparison-audit.json` giữ giới hạn A0 và thông tin so sánh. '
        '`a3-gate-selection-audit.json` mô tả cơ chế gate từ checkpoint và cache trênCPU. '
        'Figure độc lập nằm trong `figures/`, có SVG/PNG/CSV/provenance và script dựng lại. '
        'Hai báo cáo tại `research_tracking/supervisor_reports/2026-11-10/01_tien_do/` đã cập nhật. '
        'HTML đã kiểm tĩnh, PNG được xem trực tiếp. API inference độc lập của gói export còn chờ kiểm.\n')
    with (HERE / 'README.md').open('a', encoding='utf-8') as stream:
        stream.write(note)
    print(json.dumps(dict(status='A3_TRACKING_UPDATED', selected_epoch=acceptance['selected_epoch'])))


if __name__ == '__main__':
    main()
