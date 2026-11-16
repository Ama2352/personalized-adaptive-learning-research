# Rà soát độc lập phạm vi dọn lịch sử AKT

Ngày 17/11/2026. Phạm vi chỉ đọc metadata, source và biên nhận đã có. Người dùng đã duyệt dọn 35 ZIP lịch sử sau sao lưu Drive. Nhánh review không xóa, di chuyển, hash lại archive lớn hoặc chạy model.

## Kết luận

Không phát hiện ZIP nào trong đúng 35 mục của `drive-offload-history-20261116-01/MANIFEST.json` cần giữ local để tiếp tục lifecycle hiện hành của calibration, đánh giá Junyi hoặc refit/đánh giá Grade10. Kết luận áp dụng cho việc bỏ bản container ZIP, trong khi compact exports, checkpoint gốc còn cần dùng, metadata và cache tiếp tục giữ trên D.

Các ZIP này vẫn có giá trị truy vết. Nếu cần tái mở gói recovery Colab hoặc replay cơ chế download/đóng gói cũ, phải lấy lại ZIP tương ứng từ Drive đã nghiệm thu. Đây là chuyển vị trí lưu lịch sử, không phải kết luận rằng nội dung lịch sử hết giá trị audit.

## Đối chiếu inventory và sao lưu

Đã đọc đủ 35 dòng manifest, tổng 35.154.218.914 byte. Mỗi `upload_path` có dòng tương ứng trong `research_tracking/runs/drive-history-upload-20261116-01/READBACK_ACCEPTANCE.json`. Kích thước, SHA nguồn và SHA-256 server khớp từng mục. Biên nhận toàn đợt có 37 file, gồm 35 ZIP và hai file hỗ trợ, trạng thái `REMOTE_METADATA_CHECKSUM_READBACK_VERIFIED`.

Đây là kiểm lại quan hệ giữa hai hồ sơ đã nghiệm thu. Nhánh này không tải lại 35 GB hoặc gọi Drive API lần nữa.

Tại snapshot metadata của lượt review, cả 35 source ZIP và 35 đường dẫn upload đều tồn tại, từng cặp cùng volume/file identity và `st_nlink=2`. Vì đã xác định đủ hai tên của từng identity, chưa thấy hardlink thứ ba ngoài source và thư mục history tại thời điểm đó. Các bản sao có cùng byte nhưng khác identity nằm ngoài kết luận này.

35,15 GB là tổng kích thước của 35 identity được xét. Dung lượng vật lý giải phóng phải dựa vào lần đo của root sau thao tác. Các cơ chế allocation/compression và hoạt động khác trên D có thể làm số đo khác tổng logic. Chỉ bỏ một trong hai hardlink vẫn giữ dữ liệu ở link còn lại.

## Phụ thuộc code đã kiểm

Đã quét 355 file được liệt kê trong `src/`, `scripts/`, `experiments/akt/configs/`, `notebooks/`, `tests/akt/` và các entrypoint Python trực tiếp trong `experiments/akt/`. Phần notebook chỉ xét code cells. Tìm các run name của 35 ZIP, cùng các đường đọc ZIP/index/support hiện hành.

| Consumer | Phụ thuộc thực tế | Ảnh hưởng của việc dọn 35 ZIP |
|---|---|---|
| `src/knowledge_tracing/akt/research_junyi_calibration.py`, `attach_refit_export`, khoảng dòng 85–110 | Đọc `MODEL_INDEX.json`, checkpoint được chỉ bởi `checkpoint_file` và `SUPPORT.zip` trong compact refit export. SUPPORT chứa cấu hình, roles, metadata và inventory để kiểm identity | Những file này nằm ngoài danh sách 35 ZIP và phải giữ |
| `scripts/akt/export_junyi_refit_model.py` | Xuất model/index/support từ hồ sơ refit đã giải nén, tạo SUPPORT riêng | Việc bỏ container lịch sử không thay compact export. Không dọn folder run hoặc member đã giải nén bằng thao tác recursive |
| `scripts/akt/audit_junyi_comparison.py`, dòng 87 | Mở `experiments/akt/results/modal-junyi-a0-b128-h100-20261112-03/artifacts.zip` để đọc manifest và initial backbone A0 | ZIP này có tồn tại, khoảng 555,84 MB, nằm ngoài 35 ZIP đang xét. Cần giữ để kiểm lại so sánh A0 |
| `notebooks/akt_colab_a3_refit_resume.ipynb`, code có INDEX recovery | Dùng `COLAB_RESUME.zip` cùng trạng thái recovery A3 trước khi refit hoàn tất | Notebook recovery cũ cần lấy ZIP từ Drive nếu chạy lại. A3 đã có refit cuối được nghiệm thu, nên đây không phải đầu vào cho calibration hay Grade10 tiếp theo |
| `experiments/akt/modal_a0_gpu_pilot.py`, RUN Main60 A0 | Tạo/download `artifacts.zip` của pilot selected-fit Main60 | Gói cũ có thể cần khi replay pilot. Refit/đánh giá Grade10 tiếp theo dùng selected checkpoint/export được giữ, không cần chạy lại pilot chỉ vì bỏ ZIP lịch sử |

Các cách dùng `artifacts.zip` khác trong entrypoint Modal là đóng gói/download output hoặc dùng CPU gate archive riêng. Lượt rà source/config không tìm thấy đường đọc bắt buộc một trong 35 ZIP làm đầu vào của calibration hiện hành. Tìm kiếm tĩnh chưa chứng minh được mọi lệnh tùy ý mà người dùng có thể gọi về sau, vì vậy biên nhận Drive và lineage phải được giữ.

## Những file phải nằm ngoài thao tác dọn

- Bốn thư mục `model-export-a0-refit-20261114-01/` đến `model-export-a3-refit-20261114-01/`. Đã kiểm metadata thấy đủ checkpoint `A0_JUNYI_REFIT.pt` đến `A3_JUNYI_REFIT.pt`, `SUPPORT.zip` và `MODEL_INDEX.json` của mỗi export. Không hash lại neural checkpoint trong lượt review.
- Toàn bộ `experiments/akt/results/model-export-20261112-01/`. Đã thấy đủ bảy checkpoint Grade10 `A0.pt`, `A1_EXPERT.pt`, `A1_LEARNED.pt`, `A2_EXPERT.pt`, `A2_LEARNED.pt`, `A3_EXPERT.pt`, `A3_LEARNED.pt`. Folder cũng có model/index/support lịch sử cần tiếp tục theo dõi.
- Các selected-fit compact export A0–A3, checkpoint các epoch A0 cần đối chiếu lựa chọn vòng học và archive A0 H100 được entrypoint audit đọc như nêu trên.
- Các refit checkpoint/optimizer/RNG đang giữ, log/prediction, inputs đã giải nén và lineage. Danh sách này chỉ duyệt ZIP, không cho phép suy tiếp rằng cả thư mục run có thể bỏ.
- Cache window/encoding/roles và graph/confidence TRAIN80/TRAIN90 trong `artifacts/akt/`. Chúng là đầu vào của việc dựng predictor, binding và pipeline tiếp theo.
- Hai file hỗ trợ trong thư mục history, manifest nguồn, biên nhận upload/readback và hồ sơ dọn. Thư mục duplicates là đợt khác, không thuộc phạm vi review này.

## Danh sách loại trừ và rủi ro

Danh sách cần loại trừ khỏi chính 35 ZIP là rỗng theo bằng chứng hiện có. Các vùng giữ ở trên vốn nằm ngoài danh sách. Root cần tiếp tục kiểm SHA/pin trước unlink và ghi kết quả từng đường dẫn.

Rủi ro chính là mở lại notebook recovery hoặc script kiểm lịch sử vốn trông đợi ZIP local. Cách phục hồi là tải đúng file Drive theo checksum và relocation manifest, không sửa manifest/model lịch sử. Việc dọn chỉ được thực hiện trên đúng các tên source ZIP và hardlink đã duyệt, giữ các member/metadata khác trong cùng thư mục.

Uploader lịch sử đã hoàn tất đợt này. Sau khi bỏ các ZIP trong thư mục upload, chạy lại `drive_resumable_upload.py` với nguồn mặc định sẽ gặp guard thiếu archive so với manifest. Đây là hành vi đúng khi inventory nguồn đã được chuyển sang lưu trên Drive. Cần ghi trạng thái đợt đã hoàn tất/lưu remote và vị trí phục hồi, giữ manifest cũ. Muốn khôi phục nguồn để chạy lại đúng đợt phải lấy lại các file đã dọn. Đây là phụ thuộc của thao tác upload lại lịch sử, không phải prerequisite của calibration hoặc Grade10.
