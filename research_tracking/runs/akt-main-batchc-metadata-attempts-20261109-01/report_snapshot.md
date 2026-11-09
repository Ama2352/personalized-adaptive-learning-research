# Main CUDA Batch C — hồ sơ collection01–05

Ngày09/11/2026, ROOT đã thử kiểm metadata trên Windows sau khi áp dụng tám file Batch C. Chưa có lượt collection thành công hoặc test body thực chạy. Bốn lượt đầu giữ `REJECTED_BATCHC_METADATA_KEEP_ALL`; lượt05 giữ `NO_GO_METADATA_RAM` trước khi tạo child. Các kết quả này chưa kiểm chứng hành vi CPU mới hoặc CUDA.

## Diễn tiến thực tế

| Lượt | Điểm dừng | Child seconds | Outer stored seconds | Population/kết quả test |
|---|---|---|---|---|
|01|Mẫu RAM đầu dưới floor1536MiB|0,5437661000178196|1,002320600033272|counts NULL; IDs0; body0|
|02|Guard đọc file chặn trong phase metadata_pytest; chưa ghi target|1,2008954999619164|1,8787577000330202|counts NULL; IDs0; body0|
|03|Chẩn đoán xác định đọc `nul` ở Pytest capture.py489|1,0477757999906316|1,6755241999635473|counts NULL; IDs0; body0|
|04|Đọc stdin NUL đã qua; chặn bốn cache Pytest và ba target `<unknown>` khi định dạng lỗi|1,3237590999924578|1,7263450000318699|counts NULL; IDs0; body0; collection_errors4|
|05|Admission trước launch dưới cushion2GiB|Chưa tạo child|Receipt không có elapsed|Chưa collection; chưa có Job/child receipt|

`IDs0` mô tả quan sát trước khi có population được nghiệm thu. Không dùng các số này làm số lượng test cần kiểm. Lượt04 trả pytest exit3 và có bốn collection error; chưa phải bốn test body thất bại. Không có JUnit trong năm lượt.

Lượt01 đo available1.583.316.992B dưới floor1.610.612.736B, peak worker26.374.144B. Lượt02–04 lần lượt đo minimum available2.188.365.824B,2.382.319.616B,2.106.781.696B và peak worker31.952.896B,32.010.240B,31.944.704B. Các mẫu là cooperative worker hooks, chưa đo liên tục hoặc toàn process family. Giới hạn worker512MiB và floor1536MiB giữ nguyên. Từ02, admission trước launch yêu cầu2GiB. Lượt05 available1.654.325.248B dưới admission2.147.483.648B nên chưa gọi owned launcher.

## Guard và nguồn chẩn đoán

Raw02 không có đường dẫn bị chặn. Raw03 ghi target nguyên `nul`, mode `r`, flags32896, caller `_pytest/capture.py` function `__init__` line489. ROOT chuẩn bị04 từ quan sát này, thêm ngoại lệ đọc stdin hẹp theo phase, raw target, mode/flags, caller và source SHA; tối đa bốn lần. Raw04 ghi một lần đọc hợp lệ. Các guard đọc file khác được giữ.

Raw04 tiếp tục ghi bốn target `*-pytest-9.1.1.pyc` của bốn test module tại cache cũ. Ba target `<unknown>` còn lại có caller `ast.parse` trong đường định dạng traceback. Giữ cả bảy denial. Không mở rộng allowlist cho cache cũ hoặc target `<unknown>`.

ROOT chuẩn bị05 với `sys.pycache_prefix` mới thuộc runtime-temp của lượt, đặt trước import Pytest và có nhánh phục hồi cuối lượt; giữ assertion rewriting, source guards và `dont_write_bytecode=True`. Packet05 thêm anchor của `_pytest/assertion/rewrite.py`, nâng runtime anchors8→9→10 qua các bản01–05. Source vẫn33bindings, chỉ đổi hai tên/hash worker và outer giữa các lượt. Lượt05 chưa chạy child nên việc dùng prefix và phục hồi mới chỉ được kiểm bằng đọc nguồn, chưa có bằng chứng runtime.

Trong bước chuẩn bị05, ROOT cho biết một assertion ban đầu đã giả định tổng denial4. Receipt04 thực có7 gồm4PYC và3`<unknown>`. Source `prepare_batchc_metadata05.py` hiện kiểm đúng7 và hai nhóm này. Đây là sửa điều kiện kiểm metadata chuẩn bị. Chưa tìm thấy raw stderr riêng hoặc snapshot của assertion ban đầu; ghi chú này dựa trên message điều phối của ROOT và raw04, không dựng lại transcript.

## Bảo toàn và giới hạn

Hồ sơ gộp giữ15worker/outer/packet,40file raw phẳng, hai Root preparer04/05, báo cáo và archiver. Raw theo lượt có8/10/10/11/1file. Không copy runtime-temp, cache tree, dependencies hoặc corpus. Hai stream owned stdout/stderr của01–04 đều0B; pytest.log04 có nội dung lỗi và được giữ nguyên. Nguồn33 và runtime8/9 quan sát trước/sau trùng trong các child01–04. Lượt05 chỉ có admission receipt, không được kế thừa source-after hoặc cleanup từ các lượt trước.

Owned receipts01–04 ghi returncode1, cleanup accepted và Job active sau cleanup0; môi trường/sys phục hồi và scientific modules thực tế vắng mặt. Chưa có forward/backward, optimizer hoặc workload mô hình/CUDA trong các lượt này. Metadata Windows vẫn dùng helper đã ghim với lệnh hệ thống giới hạn, có raw receipt riêng. Lượt05 không tạo owned Job. Không tự retry, hạ floor hoặc thêm node loại trừ. Bộ kiểm vẫn chỉ loại đúng `tests/akt/test_runtime.py::test_native_akt_import_cpu`, và tests mode chỉ được phép sau khi ROOT ghim một collection thành công cùng source.

Bundle gộp dùng `akt-main-batchc-metadata-attempts-20261109-01`. Archiver01 riêng trước đó chưa được thực chạy theo điều phối ROOT; source/note của nó được reference bằng SHA và giữ tại chỗ. `completed` của manifest gộp chỉ xác nhận lưu bằng chứng. Nó không đổi trạng thái các operation thành PASS. Main C vẫn tests pending; checkpoint04 chưa chạy và chưa tạo native05. Cap checkpoint1GiB hiện đo worker RSS, còn family monitoring là scope riêng chờ chuẩn bị sau metadata PASS. Những nhánh cached/stdlib độc lập tiếp tục theo phân công ROOT.
