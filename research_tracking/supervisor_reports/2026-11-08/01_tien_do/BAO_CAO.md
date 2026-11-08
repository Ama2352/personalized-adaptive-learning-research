# Báo cáo tiến độ KLTN — 08/11/2026

**Đề tài:** Nghiên cứu và phát triển hệ thống học tập thích ứng cá nhân hóa dựa trên mô hình hóa tri thức và tối ưu hóa lộ trình.

**GVHD:** TS. Lê Văn Tuấn. **Sinh viên:** Phạm Triều Dương và Hồ Nguyễn Minh Sang.

**Tóm tắt:** Đã có kết quả chẩn đoán RQ1–RQ2 và corpus mô phỏng để phát triển RQ3. Chưa có so sánh nghiên cứu CG-AKT đã huấn luyện với các mô hình đối chứng; chưa RQ nào hoàn tất. Các kết quả được tích lũy đến ngày 08/11, gồm công việc kế thừa; không phải tất cả chạy trong một ngày.

Bản này tóm tắt thành quả, giới hạn và việc tiếp theo. **[Notebook kết quả nghiên cứu](KET_QUA_NGHIEN_CUU.ipynb)** trình bày đầy đủ thiết kế, bảng số liệu, đối chứng và nguồn. Thư mục hiện hành chỉ giữ hai file này.

## 1. Sáu kết quả chính

| Mã | Đã làm và kết quả | Giới hạn cần giữ |
|---|---|---|
| **K1 — RQ1: dự báo và quyết định** | So sánh full–empty trên cùng 1.080 query/nhãn: 963 điểm đổi xác suất, nhưng 943 trong số đó giữ lựa chọn khái niệm xem trước; tổng 22 lựa chọn đổi. | Dự báo đổi chưa chắc quyết định đổi. Đây là preview, không hành động đã phục vụ hoặc lợi ích học tập; chưa chứng minh chuỗi nhân quả. |
| **K2 — RQ1/RQ2: lượng lịch sử** | Đã chạy 108 policy arms trên 27 targets ; 54 đối chứng đủ lịch sử khớp các đầu ra gốc trước khi rút ngắn đầu vào. Hiệu ứng graph không đơn điệu theo lượng lịch sử. | Can thiệp toàn policy, gồm bộ ghi nhớ controller; chưa tách riêng KT hoặc tác động của luyện tập thực tế. |
| **K3 — RQ2: retention** | Với không luyện sau T, decay đồng nhất và gain không âm quanh base cố định: net mean-theta gain sau14 ngày bằng 0,4317105×final gain. Soft-mastery có phản ví dụ đảo thứ hạng. | Chỉ một metric tuyến tính dư thừa trong điều kiện này. Phản ví dụ là states dựng sẵn, chưa chứng minh reachable bằng policy; không loại mọi retention metric. |
| **K4 — RQ2: kiểm soát năng lực** |36 quỹ đạo/4.320 tương tác giữ residual và chuỗi ngẫu nhiên chung, thay scalar năng lực/penalty tiên quyết. Tương tác graph–penalty nhỏ, không nhất quán dương; high-ability zero được dự kiến trước. | Đơn vị là Elo net trung bình 28 concepts tại T = 41 ngày, không tác động trên học sinh thật. Graph vẫn khác khi penalty inactive; không quy mọi lợi thế cho tiên quyết. |
| **K5 — RQ2: thứ tự Junyi** | Phân tích order-only trên 256 inner-train learners/12.575 tương tác, có graph controls và kiểm tập so sánh chung. | Logged-order association còn nhạy coverage/mẫu số, không là predictive hoặc instructional causal benefit. |
| **K6 — nền RQ3: dữ liệu** | Đã sinh/publish 60 người học/12.600 tương tác: 48 train, 6 chọn epoch, 6 calibration; đủ 84 bài tập mỗi vai. | Đây là corpus Development thực, vượt smoke 12 events; chưa có model fitted, calibration fitted hoặc bằng chứng đủ cho mọi kết luận. |

K1 chỉ có 3 seed blocks × 3 profiles × 120 bước, không 1.080 người học độc lập. K2/K4 tái sử dụng các block đã có; số arms/events không tạo thêm seed độc lập. Full–empty K1 thay estimator edges trong cùng package, giữ graph môi trường/controller; không đồng nhất với bật/tắt cả package. Notebook giữ mọi kết quả âm và chưa kết luận được.

## 2. Những phần đã xử lý

- **Baseline:** có Development 5-fold BKT/GAM-KT; aggregates khác supported population nên chưa coi là paired comparison công bằng cho mọi mô hình. BKT Holdout từng được truy cập trong lịch sử, không còn untouched final test.
- **Pipeline AKT:** đã cài ranh giới train → chọn epoch → fresh refit → calibration → xuất dự báo; giữ target identity, OOV null và provenance. Kiểm bằng stubs chưa là native research lifecycle hoàn tất.
- **Metric:** đã tách raw/calibrated canonical metrics khỏi temperature-fit objective, kiểm evaluator trên 5 hàng tự dựng; không dùng fixture scores làm hiệu quả AKT.
- **Confidence cạnh:** có module train-only, whole-learner cross-fitting/strict-past; chưa fit trên corpus. Confidence đo predictive stability dự kiến, không xác suất cạnh tiên quyết đúng.

## 3. Chưa đạt và điều kiện trước chạy thật

RQ1/RQ2 đã có chẩn đoán và đối chứng hữu ích, nhưng chưa đủ kết luận tổng quát về nguyên nhân, điều kiện hiệu quả hoặc lợi ích closed-loop. Exact revision Paper1 khớp PDF vẫn chưa tìm được. RQ3 còn thiếu benchmark research-fitted trên giao thức chung; Junyi và simulator Toán10 khác vocabulary, phải train riêng.

**Native A0 chưa đủ điều kiện dispatch:** cần current-source full Gate, runtime đúng schema và nghiệm thu tài nguyên/owned-process. Hai lượt thử phân nhóm Gate thiếu JUnit/result cuối nên chưa được nghiệm thu; không tính dấu tiến độ thành PASS. Chưa chạy full Gate trong batch này. Không nới điều kiện hoặc dùng pure tests thay runtime/Gate thật.

Demo hiện đọc bằng chứng đã lưu, chưa cá nhân hóa bằng research-fitted model. Chương kết quả cuối và đánh giá còn tiếp tục; số tests/files không là phần trăm hoàn thành khóa luận.

## 4. Mốc tiếp theo

1. Nghiệm thu bộ kiểm tổng tách process và môi trường native; giữ đủ coverage và failures.
2. Khi đủ điều kiện, chạy một A0 lifecycle giới hạn trên corpus đã freeze; kiểm chọn epoch, checkpoint, fresh refit, calibration, exports và tài nguyên. Pilot một candidate chưa là chọn winner chung.
3. Fit confidence từ train; nối graph-free/fixed/confidence/gated, SAKT/GKT và các baseline bắt buộc; freeze so sánh trước GPU/evaluation. Đo prediction, quyết định và learning outcomes riêng, giữ negative findings.

**Ngân sách:** chỉ 30 USD free credits, trả thêm 0 USD; chưa dùng Modal trong các batch tổng hợp. Chưa có throughput nghiên cứu để dự toán đầy đủ. Chỉ chạy khi RAM và các cổng admission đạt; không suy đủ tài nguyên từ tests/smoke nhỏ.

## 5. Đọc số liệu và kiểm chứng

Mở [notebook](KET_QUA_NGHIEN_CUU.ipynb) trên Colab, giữ CPU, chọn **Run all**. File có outputs sẵn và source path/SHA/JSON Pointer; chỉ dựng lại bảng/biểu đồ từ số liệu đóng băng, không chạy lại simulator/training. Chưa actual Colab/kernel/visual QA.

Nguồn repository: [full–empty](../../../reports/rq1_fixed_edge_set_contrast_20261108.md), [history](../../../runs/rq1-history-availability-20261108-02/README.md), [ability](../../../runs/rq2-controlled-ability-prerequisite-20261108-01/README.md), [retention](../../../reports/rq2_retention_metric_separation_20261108.md), [Junyi](../../../reports/rq2_conditions_evidence_20261108.md), [corpus](../../../runs/development-corpus-native-20261108-01/README.md), [metric integration](../../../runs/akt-calibrated-reporting-engineering-20261108-01/README.md). Các links cần checkout repo; notebook xem riêng được. Gói nhiều file cũ giữ trong Git tại commit `2e63cd9`; không sửa/di chuyển dữ liệu hoặc run gốc.
