# Corpus60 đã qua kiểm dữ liệu trước training

Public reader chuẩn đã đọc corpus mô phỏng có48train/6selection/6calibration, mỗi người210events. Ba nhóm learner disjoint. Train10080targets, selection1260, calibration1260, mỗi role đủ84items và hai nhãn. Encoding chỉfitTRAIN80 đủ84items, khôngOOV trong tập chọn checkpoint. AKT144trainwindows và18selectionwindows, mỗi target được chấm đúng một lần, context100/target100/maxlen200. Các28concept được47–48trainlearners quan sát. Độ phủ concept chưa tự chứng minh độ phủ từng cặp cạnh.

Actualdata preflight2,546s, publicreader0,368s, RSS tại cuối50.839.552bytes. Đây không phải số đo peak toàn job hoặc throughput training. Không model/optimizer/world calls, không đọc Holdout hoặc sửa corpus. Bản sao nguồn là source tại lúc đóng bundle sau run, không giả source-before chưa ghi. Data/encoding tự revalidate nguồn theo canonical API. Giữ rawinputSHA và giới hạn reader trong result.

Bảng targetcounts là mức trần giả định mọi condition dùng hết số epoch tối đa ở selected/refit, chưa là allocation chạy hoặc thời gianGPU đã đo. Chưa gồm validation/calibration/inference/failed attempts. Không dùng counts để tự cấp quyền chi Modal.
