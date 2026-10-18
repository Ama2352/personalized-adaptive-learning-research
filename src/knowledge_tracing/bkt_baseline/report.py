"""Render measured experiment manifests as a Vietnamese thesis report."""

from __future__ import annotations

import json
from pathlib import Path
import statistics


METRICS = ("auc", "log_loss", "brier", "ece", "accuracy")


def _read(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def _fmt(value) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.6f}"
    return f"{value:,}" if isinstance(value, int) else str(value)


def _metric_row(label: str, summary: dict) -> str:
    metrics = summary["metrics"]
    cells = [label, _fmt(summary["total_rows"]), _fmt(summary["scored_rows"]), _fmt(summary["coverage"])]
    cells.extend(_fmt(metrics[name]) for name in METRICS)
    return "| " + " | ".join(cells) + " |"


def render_report(artifacts_dir: str | Path, output_file: str | Path) -> Path:
    root = Path(artifacts_dir)
    output = Path(output_file)
    derived = _read(root / "derived" / "manifest.json")
    splits = _read(root / "splits" / "manifest.json")
    pilot = _read(root / "pilot" / "pilot.json")
    cv = _read(root / "cv" / "cv.json")
    cv_progress = _read(root / "cv" / "cv_progress.json")
    final = _read(root / "final" / "final.json")
    test = _read(root / "test" / "test.json")
    scale = _read(root / "scale_probe_status.json")
    lines = [
        "# Baseline Bayesian Knowledge Tracing chuẩn trên Junyi Academy",
        "",
        "## Phương pháp cố định",
        "",
        "Mỗi `exercise` được fit bằng một mô hình BKT chuẩn của CAHLR/pyBKT 1.4.3. "
        "Nhãn là `correct` gốc của Junyi: dùng hint khiến nhãn false. "
        "Dự đoán tuần tự một bước tại tương tác `t` chỉ dùng phản hồi đến `t−1` của cùng học sinh và exercise. "
        "`suggested` chỉ dùng để phân nhóm báo cáo.",
        "",
        "Chia 80% Development/20% Test theo `user_id` toàn cục bằng SHA-256 với seed 42. "
        "Năm fold trong Development cũng rời nhau theo học sinh. "
        "Pilot so sánh `num_fits` 1, 5, 10 trên Development; Test chỉ được đánh giá sau CV và refit mới trên toàn Development.",
        "",
        "Dòng trùng hoàn toàn theo 17 trường chỉ bị bỏ trong dữ liệu phái sinh, giữ dòng nguồn đầu tiên và lưu lineage. "
        "Thứ tự dùng `time_done`, rồi số dòng nguồn để phá tie khi cần; số dòng nguồn không được coi là thời gian thực. "
        "Skill chưa thấy trong train được đếm vào coverage, không có dự đoán BKT đã fit và không tham gia metric.",
        "",
        "AUC, Log Loss, Brier, ECE 15 bin độ rộng bằng nhau và Accuracy ngưỡng 0,5 được tính trên các dòng có model. "
        "AUC một lớp được ghi N/A. Các nhóm hiếm dựa trên số học sinh train của từng skill, không dựa trên số học sinh Test.",
        "",
        "pyBKT local có bản vá tương thích NumPy 2: lấy scalar từ mảng likelihood 1×1 bằng `.item()`; phương trình EM không đổi. "
        "API công khai `Model.fit` không trả likelihood huấn luyện, vì vậy trường này được ghi không khả dụng nếu không có nguồn đo ổn định.",
        "",
        "## Dữ liệu phái sinh và lineage",
        "",
    ]
    if derived is None:
        lines += ["Chưa chạy tiền xử lý toàn bộ dữ liệu.", ""]
    else:
        lines += [
            f"- Dòng nguồn: **{_fmt(derived['raw_rows'])}**.",
            f"- Dòng sau khử trùng lặp: **{_fmt(derived['canonical_rows'])}**.",
            f"- Dòng dư loại khỏi bản phái sinh: **{_fmt(derived['duplicate_rows_removed'])}**.",
            f"- Timestamp tie dư sau khử trùng lặp: **{_fmt(derived.get('timestamp_tie_excess_after_dedupe'))}**.",
            f"- SHA-256 tệp gốc: `{derived.get('input_sha256', 'N/A')}`.",
            "",
        ]
    lines += ["## Phân chia học sinh", ""]
    if splits is None:
        lines += ["Chưa chạy phép chia học sinh.", ""]
    else:
        lines += [
            f"- Development: **{_fmt(splits['development_students'])}** học sinh.",
            f"- Test: **{_fmt(splits['test_students'])}** học sinh.",
            f"- Fold Development: `{splits['development_fold_students']}`.",
            "",
        ]
    lines += ["## Pilot Development", ""]
    if pilot is None:
        lines += ["Chưa chạy pilot; chưa chọn `num_fits`.", ""]
    else:
        lines += [
            f"Skill pilot: `{pilot['selected_skills']}`. Seed: `{pilot['seeds']}`. "
            f"Quy tắc chọn: {pilot['selection_rule']}",
            "",
            "| num_fits | Log Loss trung bình | SD giữa seed | Thời gian trung bình (s) |",
            "|---:|---:|---:|---:|",
        ]
        lines[-2:] = [
            "| num_fits | AUC | Log Loss | Brier | ECE | Accuracy | SD Log Loss giữa seed | Thời gian trung bình (s) | RAM đỉnh (GB) |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for name, summary in pilot["candidate_summary"].items():
            runs = [run for run in pilot["runs"] if run["num_fits"] == int(name)]
            metrics = {}
            for metric in METRICS:
                values = [run["pooled_validation_metrics"][metric] for run in runs]
                values = [value for value in values if value is not None]
                metrics[metric] = statistics.mean(values) if values else None
            max_rss = max(
                (skill["peak_rss_bytes"] for run in runs for skill in run["skills"]),
                default=0,
            ) / (1024 ** 3)
            lines.append(
                f"| {name} | {_fmt(metrics['auc'])} | {_fmt(metrics['log_loss'])} | "
                f"{_fmt(metrics['brier'])} | {_fmt(metrics['ece'])} | {_fmt(metrics['accuracy'])} | "
                f"{_fmt(summary['sd_log_loss'])} | {_fmt(summary['mean_wall_seconds'])} | {_fmt(max_rss)} |"
            )
        lines += ["", f"Cấu hình được chọn: **num_fits={pilot['selected_num_fits']}**.", ""]
    lines += ["## Khả thi tính toán ở quy mô dữ liệu", ""]
    if scale is None:
        lines += ["Chưa có phép đo tải lớn để ước tính thời gian benchmark toàn bộ.", ""]
    else:
        lines += [
            f"Phép đo Development trên exercise `{scale['skill']}` dùng **{_fmt(scale['train_rows'])}** dòng train "
            f"mất **{scale['wall_seconds']:,.2f} giây** ở `num_fits={scale['num_fits']}`; RAM đỉnh "
            f"**{scale['peak_rss_gb']:.2f} GB**. Fit phát cảnh báo số học NumPy, nhưng hệ số và metric đã lưu đều hữu hạn.",
            f"Ngoại suy tuyến tính từ throughput đo được cho phần fit của CV 5-fold là khoảng "
            f"**{scale['estimated_cv_hours']:,.2f} giờ**. Đây là ước lượng, không phải runtime CV đã đo; "
            f"nó giả định chi phí tỷ lệ với số dòng và không phản ánh chính xác khác biệt giữa exercise.",
            "Trạng thái: **đã dừng sau một fit tải lớn**. Mình dừng phép đo tải bổ sung sau khi fit exercise lớn nhất mất 26,4 phút. CV toàn bộ đã được khởi chạy rồi dừng ở checkpoint 1/3.600 để tránh giữ CPU nhiều ngày; có thể tiếp tục từ checkpoint. Thời gian CV nêu trên là ngoại suy, không phải runtime đo được.",
            "",
        ]
    lines += ["## Năm fold Development", ""]
    if cv is None:
        if cv_progress is None:
            lines += ["Chưa chạy cross-validation toàn Development.", ""]
        else:
            completed = len(cv_progress.get("completed", {}))
            total = len(cv_progress["protocol"]["skills"]) * cv_progress["protocol"]["folds"]
            lines += [
                f"CV chưa hoàn tất: **{completed}/{total}** skill-fold đã fit; chưa có metric gộp. "
                "Có thể tiếp tục từ checkpoint bằng lệnh `python -m bkt_baseline.cli cv`.",
                "",
            ]
    else:
        lines += ["| Metric | Mean | SD | Fold xác định |", "|---|---:|---:|---:|"]
        for name in METRICS:
            row = cv["aggregate"][name]
            lines.append(f"| {name} | {_fmt(row['mean'])} | {_fmt(row['sd'])} | {row['defined_folds']} |")
        lines += ["", "Các số trên là mean/SD không trọng số qua năm fold; metric mỗi fold được lưu trong artifact CV.", ""]
    lines += ["## Refit và holdout Test", ""]
    if final is None:
        lines += ["Chưa refit model trên toàn Development.", ""]
    else:
        lines += [f"Đã lưu **{_fmt(len(final['fits']))}** model theo exercise; `num_fits={final['num_fits']}`.", ""]
    if test is None:
        lines += ["Chưa đánh giá holdout Test; không có metric Test để báo cáo.", ""]
    else:
        lines += [
            "| Nhóm | Tất cả dòng | Dòng có model | Coverage | AUC | Log Loss | Brier | ECE | Accuracy |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            _metric_row("Tổng thể", test["overall"]),
            _metric_row("Suggested", test["suggested"]["suggested"]),
            _metric_row("Non-suggested", test["suggested"]["non_suggested"]),
            "",
            f"Skill chưa thấy trong Development: **{_fmt(test['overall']['unseen_skills'])}** skill, "
            f"**{_fmt(test['overall']['unseen_rows'])}** tương tác, "
            f"**{_fmt(test['overall']['unseen_students'])}** học sinh. Các dòng này không nằm trong metric BKT.",
            "",
            "| Độ phủ skill theo số học sinh train | Tất cả dòng | Dòng có model | Coverage | AUC | Log Loss | Brier | ECE | Accuracy |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for label, group in test["rarity"].items():
            lines.append(_metric_row(label, group))
        lines.append("")
    lines += [
        "## Giới hạn diễn giải",
        "",
        "Các exercise hiếm có ít học sinh train nên tham số và metric nhóm có thể kém ổn định. "
        "`suggested` phản ánh chính sách đề xuất của hệ thống và không cho phép suy luận nhân quả từ chênh lệch metric. "
        "Giá trị `correct=false` khi dùng hint là định nghĩa outcome của Junyi, không phải lỗi gán nhãn của pipeline.",
        "",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    return output
