# SAKT — bước tính một epoch và dự đoán trên dữ liệu phân vai

## Phần cài đặt đã hoàn tất

`src/knowledge_tracing/sakt/research_training.py` bổ sung hai API: `train_research_epoch` và `predict_research_sakt`. Chúng nhận `SAKTResearchView` cùng model, optimizer và giới hạn do caller khai báo; không gọi trainer toy, nới caps cũ hoặc tự chọn hyperparameters. Hiện hỗ trợ CPU FP32. Training chỉ nhận TRAIN80 hoặc refit90; selection/calibration chỉ dự đoán. Đây là cầu tính toán vào lifecycle nghiên cứu, chưa là một baseline đã huấn luyện và nghiệm thu.

Một epoch phải đối chiếu đủ danh tính mục tiêu với các quan sát của phase. Kết quả phân biệt mục đã đọc, hợp lệ, unsupported, đã tối ưu, đã chấm và còn thiếu; dừng vì budget không thành complete. Nhãn dùng trong loss/truth sidecar, không đưa vào forward hiện tại. Prediction giữ weights bất biến và phục hồi mode của từng module; training phục hồi RNG/mode nhưng không giả rollback khi optimizer đã bắt đầu cập nhật.

## Bằng chứng đã chạy

Lượt02 đạt **22 PASS,0fail/error/skip** trong13,7538533giây theo receipt outer, trần80giây; terminal ROOT quan sát13,7559205giây là ranh giới đo riêng. Có16tiny constructors,11forwards,5logical backwards và5SGD step bodies thật. Các giá trị d4/context2/batch≤32/SGD0,2 là fixture, không phải profile SAKT nghiên cứu đã adopt. Một fixture cố ý ném lỗi sau actual update để kiểm ledger không khai rollback.

Các kiểm số có nghiệm biết trước xác nhận BCE tại logit0 và cập nhật bias−0,1, dự đoán không nhìn đáp án hiện tại/tương lai và không lẫn người học. Negative controls kiểm tổng loss tràn dù logits còn hữu hạn, input đủ số lượng nhưng sai danh tính, truth sidecar đủ số lượng nhưng ghép sai khóa, generator bị cắt và thay đổi optimizer giữa call. Chưa dùng corpus thật hoặc checkpoint.

Peak RSS quan sát295.948.288B, RAM available nhỏ nhất5.260.562.432B; monitor114samples. Đây là quan sát hợp tác, không hard OS quota. Owned Job có membership trướcGO, cleanup accepted/active0/handle closed. Không CUDA, Adam, teacher, Holdout, full CV hoặc Modal.

## Lượt thất bại được giữ nguyên

Lượt01 có19PASS/3FAIL và verdict rejected. Observer đếm từng lần vào `Tensor.backward`; PyTorch device-mode gọi lại API này qua dispatch nên bị đếm hai lần. Cap observer chặn công việc sau đó. Bản02 giữ nguyên source/test, đếm logical call tại public `torch.autograd.backward` và ghi riêng10raw Tensor dispatch entries. Không đổi model/assertion để làm test qua. Hai lượt có cùng22testcase identities, không44thí nghiệm độc lập; tổng7SGD bodies qua hai lượt chỉ là công việc kiểm kỹ thuật.

[Bundle68outputs](../runs/sakt-research-epoch-engineering-20261109-01/README.md) giữ logs/XML/receipts của cả hai lượt, nguồn đã chạy, snapshots trước sửa finite-objective/population và `counter_diagnosis.json`. Inventory kiểm SHA trước/sau copy; raw receipts không bị sửa.

## Phần chưa hoàn tất

Chưa có profile numerical SAKT nghiên cứu được chốt, orchestration chọn epoch → freeze → refit → calibration, portable checkpoint/recovery hoặc fitted OnlineSession. API hiện ghi rõ `fitted_research_model=False` và `resume_supported=False`. Những phần này cần hoàn tất trước lượt huấn luyện nghiên cứu; không dùng22PASS thay full software Gate, CUDA readiness hoặc bằng chứng trả lời RQ3.
