# Nghiệm thu CPU cloud và Drive ngày 17/11

Đã kiểm trên Modal workspace `honguyenminhsang2016`, ghi trực tiếp Drive `honguyenminhsang2005@gmail.com`. Secret được người dùng cho phép tạo, chỉ gắn CPU worker đồng bộ. Trường hợp Secret có sẵn từ lượt tạo đầu được tra cứu và giữ nguyên, sau đó kiểm quyền thực từ worker.

## Kết quả thực

`CLOUD_PROBE01.json` và `cloud-probe03.log` xác nhận hai worker CPU tách phiên. Worker đầu lưu ACK 262.144 byte rồi chủ động ngắt sau commit Volume. Worker mới reload, đọc offset 262.144, hoàn tất file 1.048.576 byte cùng config 190 byte. Drive trả đúng SHA-256 cả hai file và batch được đọc lại. Thời gian phần function 13,01 và 14,71 giây. Log worker mới in 25%, 50%, 75% trước hoàn tất. Receipt xác nhận khôi phục state; không bổ sung fingerprint URI riêng để khẳng định mọi trường hợp mạng đều tránh gửi lại.

[Thư mục kiểm trên Drive](https://drive.google.com/drive/folders/17Addi4D_jWHJlF0xBScxch7WUoduvGvy) giữ hai payload thử. Bản binary được tạo trên cloud và giữ trên Drive/Volume. PC chỉ nhận log và receipt nhỏ. App kết thúc sau lượt thứ hai. Không dùng GPU. Dự phòng toàn đợt probe tối đa 0,05 USD, đây là cận dự phòng, chưa phải hóa đơn đo riêng.

## Cấu hình sử dụng tiếp

`scripts/akt/modal_drive_artifact_worker.py::publish` nhận run/tranche, filelist rõ ràng và trần byte. Mỗi tranche tối đa 2 GiB, cần config.json, một CPU writer tuần tự, timeout 900 giây, không retry toàn function. Mọi snapshot phải đóng file và commit Volume trước khi gọi. GPU trả trước bước CPU upload. State URI chỉ giữ cloud riêng, không upload hoặc trả về PC. Config chung nằm ở `experiments/akt/configs/drive_cloud_artifact_policy.json`.

Sink được kiểm thực. Worker publish dùng chung sink đã compile nhưng chưa có lượt production calibration. Producer calibration và worker inference thật còn phải nối Volume/sink đúng policy trước lượt GPU kế tiếp. Không coi probe này là calibration Junyi đã xong hoặc bằng chứng RQ3.

## Lỗi đã xử lý

- Tạo Secret lần đầu bị treo do trộn task context SDK. Đã dừng riêng tiến trình, dùng RPC cùng loop với timeout; lookup xác nhận Secret đã có, không overwrite.
- Scale-down 0 bị SDK từ chối trước provisioning. Đã sửa 2 giây.
- Probe cloud đầu lỗi ROOT.parents do module remote nằm /root. Đã dùng root cloud /opt/kltn.
- Probe cloud tiếp theo bị kiểm alias chặn mount symlink do Modal quản lý. Worker resolve mount một lần rồi giữ kiểm canonical/alias cho payload.

MANIFEST.json giữ kết quả nhánh offline 22 tests. ROOT_MANIFEST.json nối source/receipt/log của nghiệm thu thực, không sửa manifest đã đóng của nhánh.
