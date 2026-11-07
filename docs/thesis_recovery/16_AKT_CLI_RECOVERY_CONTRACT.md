# Contract tích hợp recovery vào CLI AKT

Ngày07/11/2026. Engineering design cho bước tiếp theo, chưa là chức năng CLI đã triển khai. Không thay protocol, hyperparameters hoặc cấp quyền full fold/GPU.

## Hiện có và khoảng trống

Selection và refit có complete-epoch recovery với config/split/encoding/budget identity. Bounded resumable epoch có model/Adam/RNG/cursor và cumulative step/time/target caps. Public smoke/pilot CLI vẫn reserve một run directory mới và chưa nhận recovery options. Recovery complete-epoch hiện khóa cả output_dir trong config hash, vì vậy không thể nối qua CLI bằng cách truyền một đường dẫn checkpoint rồi đổi run_id.

## Quyết định kỹ thuật đề xuất

Mỗi lần resume tạo attempt/run mới được authorization riêng, tham chiếu run/checkpoint cũ bằng SHA. Manifest cũ giữ nguyên. Không tái sử dụng authorization lịch sử sau source/build thay đổi. Checkpoint recovery không được dùng làm selected model hoặc đưa vào đánh giá nếu epoch chưa hoàn chỉnh.

Cho resume-fork, phân biệt training semantic identity với execution attempt identity. Semantic identity bao gồm source/runtime/lock, dataset/split/cohort/encoding, model/windowing/seed/optimizer/selection rule và tổng budget. Attempt identity chứa run_id/output_dir, authorization, checkpoint SHA, attempt index và wall watchdog của attempt. Chỉ bỏ run_id/output_dir khỏi semantic comparison sau khi tất cả trường semantic đã được so tường minh. Không xóa config identity checking để làm resume chạy được.

## Gói triển khai và nghiệm thu

| ID | Mục tiêu | Nghiệm thu |
|---|---|---|
| REC01 | Schema recovery request trong config, default off | Unknown/missing hash, protected path, malformed source manifest bị từ chối; caller hiện tại giữ hành vi |
| REC02 | Bind authorization với checkpoint SHA và semantic identity | Thay model/window/seed/split/budget hoặc checkpoint bytes bị chặn trước data load |
| REC03 | Adapter cho checkpoint epoch-complete selection/refit | Fork với cùng semantics khớp next epoch và selected epoch, giữ stale epochs và best checkpoint evidence |
| REC04 | Nối batch recovery vào cùng train/selection/refit accounting | Không skip/duplicate target, telemetry không reset prefix, pending batch chưa update không commit cursor |
| REC05 | Watchdog attempt và tổng workload counters | Timeout/step/target caps cumulative, retry không tự tăng budget, mỗi attempt có log/manifests mới |
| REC06 | Public CLI synthetic lifecycle | Thực thi qua subprocess thật, interrupt tại batch/epoch/export boundary, resume-fork và predictions khớp within documented tolerance |

REC01–03 làm trước, rồi REC04–06. Không bật real-data resume hoặc full-fold entrypoint chỉ vì API tests đã đạt. Source changes làm Gate2 cũ stale, phải làm mới sau batch ổn định.

## Cases bắt buộc

- Snapshot best checkpoint đã ghi nhưng recovery snapshot chưa ghi. Retry giữ orphan cũ, tạo output mới có provenance, không overwrite.
- Đã train xong epoch nhưng validation/export thất bại. Resume phải ghi rõ bước nào chạy lại, tránh train lại một epoch ngoài selected budget.
- Step cap đúng bằng số update cần thiết. Stream hết thì epoch complete, không bị giữ incomplete vô hạn.
- Có OOV barrier hoặc partial last batch. Target IDs và counts vẫn khớp original chronological population.
- File checkpoint hợp lệ về format nhưng sai dataset, split, graph augmentation hoặc runtime. Không cho resume dựa trên tên file.
- RNG và data factory. Data replay không tiêu thụ model RNG, dropouts tiếp tục đúng, cần CUDA comparison riêng sau CPU.

## Giới hạn và chi phí

O(prefix) replay phải đo throughput trước large-data resume. Checkpoint cadence ảnh hưởng I/O và số update phải replay sau kill, không thay target population. CPU unit fixtures dùng resource snapshots xác định. Real execution vẫn đo RAM/VRAM thật và dừng khi vi phạm caps. Gate2 software PASS không chứng minh máy hiện tại đủ RAM cho pilot thật.
