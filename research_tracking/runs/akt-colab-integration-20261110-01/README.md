# Kiểm tích hợp AKT trên Colab CPU ngày 10/11

## Kết quả nghiệm thu

Lượt cuối đạt **1.992 ca**, không failure, error hoặc skip, trên ba tiến trình độc lập và 92 module. Một ca được loại trừ rõ ràng vì kiểm yêu cầu Torch/NumPy nằm trong venv cô lập, còn phiên này kế thừa thư viện Colab. Do đó kết quả được ghi là `PASS_SCOPED_PORTABILITY_ONLY`; chưa phát hành Gate mới hoặc quyền training chính.

| Nhóm | Số module | Ca đạt |
|---|---|---|
| stdlib | 1 | 19 |
| no-torch | 6 | 274 |
| remaining | 85 | 1.699 |

Lượt cuối mất 294,935 giây, dưới trần 600 giây. SHA toàn bộ 279 thành viên gói giữ nguyên trước–sau và khớp bộ đóng gói local. Inventory production hiện có 198 file nguồn/fixture. Một ca được tách riêng là `tests/akt/test_runtime.py::test_native_akt_import_cpu`; log nhóm cuối ghi đúng một deselection.

## Vì sao phải sửa trước khi dùng GPU

1. Gói Colab thiếu `simulator-research-corpus01.json` mà kiểm tạo corpus đọc. Đã bổ sung đúng file cấu hình có sẵn vào allowlist, giữ nguyên nội dung.
2. Kiểm bất biến lớp AKTConfig phụ thuộc snapshot trong `artifacts/` chưa được Git lưu. Đã sao chép nguyên byte snapshot sang `tests/akt/fixtures/legacy_config_before_simulator_research.py.txt`, ghim SHA trong test và đưa fixture vào cả inventory Gate lẫn gói Colab. Snapshot cũ vẫn giữ nguyên, không thực thi file fixture như chương trình.
3. Vùng tạm phải nằm trong `artifacts/akt/tmp/` để các kiểm đường dẫn hoạt động trong phạm vi đã cho phép. Lượt sửa đầu thiếu bước tạo thư mục cha, gây lỗi điều phối. Đã bổ sung tạo thư mục trước chạy; giữ nguyên log lỗi.
4. Một kiểm giả định ghi file sẽ luôn đổi timestamp. Trên filesystem Colab, hai lần ghi có thể cùng timestamp. Kiểm timestamp nay chủ động đặt thời gian khác. Ca mới mô phỏng timestamp giữ nguyên và xác nhận `verify_unchanged` vẫn từ chối byte bị đổi bằng SHA. Không thay đổi reader production hoặc giảm kiểm tính toàn vẹn.

Local đã đạt 101 ca pure cho bộ đóng gói và execution contract, cùng 13 ca IO. Giữ cả lỗi thiếu PYTHONPATH và lỗi TEMP ngoài workspace của các lượt local trước; lượt đạt đặt TEMP/TMP rõ trong repository.

## Diễn tiến được lưu đầy đủ

| Lượt Colab | Ca ghi nhận | Failure | Error | Kết luận |
|---|---|---|---|---|
| 01 | 1.989 | 4 | 19 | Thiếu cấu hình/snapshot và vùng tạm chưa đúng vị trí |
| 02 | 1.991 | 26 | 749 | Chưa tạo thư mục cha vùng tạm; chưa nghiệm thu |
| 03 | 1.991 | 1 | 0 | Còn giả định timestamp phụ thuộc filesystem |
| 04 | 1.992 | 0 | 0 | Đạt trong phạm vi portability, một ca môi trường cô lập được tách riêng |

Không cộng các lượt lặp thành số kiểm độc lập. Không dùng exit code của driver thay kết luận; driver có thể thoát 0 trong khi trạng thái vẫn FAILED.

Các cell MCP có lúc trả outputs rỗng. Đã đối chiếu nguồn cell và quan sát kernel trước khi thử tiếp, không suy thành công hoặc tự chạy lại job từ trạng thái rỗng. Lượt 03/04 dùng tiến trình có PID, file trạng thái và deadline, giữ lần lượt PID 18719/23468 để theo dõi. Việc đọc cell mới đã xác nhận lượt 04 hoàn tất. Đây là workaround vận hành trong lượt kiểm, chưa khẳng định nguyên nhân nội bộ của Colab.

## Nơi đọc bằng chứng

- `verification.json` là kết quả nghiệm thu độc lập sau tải đủ 12 phần. Archive 279.901 byte chứa 39 file, đã kiểm CRC, SHA từng file, số ca JUnit, ID không trùng và giới hạn thời gian.
- `remote/04-stdlib.xml`, `04-no-torch.xml`, `04-remaining.xml` giữ từng ca của lượt đạt; bốn file `*-status.json` giữ trạng thái mỗi lượt.
- Toàn bộ logs và JUnit của bốn lượt nằm trong `experiments/akt/results/colab-integration-20261110-01/logs.zip`, SHA `b5229857ddf499028a4f9a7f675839b54606d9552d30ecbae6194bdc14902704`. Bản nhỏ chỉ trích JUnit lượt đạt để kiểm độc lập thuận tiện.
- `diagnostics*.json` giữ nguyên nhân thất bại được đọc từ JUnit; `legacy-fixture-provenance.json` xác nhận snapshot nguồn/đích cùng SHA.
- `remote_cell*.py`, `detached_runner*.py`, `remote_export.py` và `receive.py` mô tả các lượt thực thi và cách nghiệm thu. Không lưu token, thông tin xác thực hoặc toàn bộ biến môi trường vào bundle.

## Phần còn thiếu trước training chính

Phiên dùng Python 3.13.18 và Torch 2.14.1+cpu kế thừa qua venv; `remote/runtime.json` ghi phiên bản thực tế. Cần môi trường Linux cô lập đúng dependency/profile, bộ Gate đầy đủ không deselect, CUDA hiện hành, phục hồi checkpoint, đo throughput và phê duyệt lượt chạy/ngân sách. Đây là kiểm fixtures, chưa Main fits/refits/calibration hoặc bằng chứng CG-AKT hiệu quả hơn. Không đọc Junyi/Holdout, không full CV, không cấp GPU hoặc dùng Modal.
