# Nối AKT với phép chấm kiến thức tham chiếu — 08/11/2026

Để dùng AKT trong simulator, file mô hình và file hiệu chỉnh xác suất phải đi cùng đúng ngân hàng bài tập và phải đọc lại được bằng API công khai. Sai dây nối có thể làm quy trình dừng dù từng thành phần riêng đã có kiểm thử. Batch này sửa hai lỗi cụ thể trước bất kỳ lượt training nghiên cứu nào.

## Thay đổi và bằng chứng

- Trường `bank_sha256` nay nhận SHA ngân hàng bài tập đúng hợp đồng; SHA toàn miền vẫn ở `domain_sha256`. Model ID đúng SHA checkpoint mà native online backend sử dụng.
- Calibrator được xuất qua `to_payload()`, gồm recipe/clip/bounds; không xuất thiếu schema bằng `asdict()`.
- Không giữ model/Adam refit cũ trong lúc tải checkpoint; không giữ payload/reload Adam khi dự báo; bỏ tham chiếu model sau dự báo trước bước fit scalar temperature. Không đổi trọng số, dữ liệu, RNG restore, epoch selection, fresh-refit hay cấu hình học.

Hai source revisions được kiểm riêng bằng cùng suite 36 cases. Lượt binding01 trước sửa vòng đời qua36; lượt binding02 sau sửa qua36,0failure/error/skip. Thời gian outer lần lượt2,804354100 và2,822563171 giây, mỗi cap45. Không cộng thành72case độc lập. Các orchestration cases nạp JSON calibrator thật qua strict loader rồi chấm84bài/28khái niệm bằng reference scorer thật với backend scalar **giả lập, chưa train**; sai bank bị từ chối trước thêm probe, thiếu recipe bị từ chối. Weakrefs kiểm model/optimizer/payload hết tham chiếu tại các điểm dự kiến.

Source trước/sau khớp; không import Torch/NumPy/pandas/sklearn/SciPy hoặc tạo subprocess từ test. Owned Job đã cleanup/job0/đóng handles. Các input/metadata là fixture; fit temperature chỉ trên các probability tự dựng, không trên corpus nghiên cứu.

## Giới hạn và bước tiếp

Đây là bằng chứng tích hợp phần mềm, không chất lượng AKT/CG-AKT, calibration ngoài mẫu, CUDA hay full Gate. Object hết tham chiếu không bảo đảm RSS trả về OS ngay; exception traceback có thể giữ tensor đến khi worker kết thúc. Phép kiểm bằng weakrefs không thay phép đo RAM thật trên native lifecycle. Cần full Gate/runtime hiện hành và bounded native resource probe trước cấp budget cho toàn lifecycle20epoch.

[Bundle nguồn và log hai revisions](../runs/akt-reference-binding-engineering-20261108-01/README.md). Không sửa dữ liệu, artifacts lịch sử, Holdout, full CV hoặc chi Modal.
