# Bổ sung pip cho cloud venv sau lỗi image build

Root ghi nhận lượt preflight CPU đầu lỗi `No module named pip` trong `.venv` kế thừa từ image uv-style. Upstream git fetch/checkout đúng commit đã thành công. Root giữ log lỗi gốc, chưa chạy GPU tại điểm lỗi này.

Layer image mới chạy `/opt/kltn/.venv/bin/python -m ensurepip --upgrade` trước lệnh cài các dependency CPU/Modal đã ghim. Lệnh chỉ tác động venv trong layer image cloud, không cài global/local và không thay pin Torch. Preflight tiếp tục kiểm chính xác Torch2.7.1+cu126/CUDA12.6 sau build. Chưa có kết quả ensurepip thực trong nhánh này, root sẽ chạy lại CPU preflight.

`TESTS07.txt` ghi23ca đạt trong2,54giây. Regression kiểm ensurepip đứng trước pip install và gọi đúng Python của cloud venv. Không thực hiện image build/cloud call trong lượt sửa này.

Thông tin allocation0,40USD trong README là quyết định trước. Root đang dùng reservation bảo thủ0,75USD gồm dư địa startup/runtime/scaledown. Source hiện hỗ trợ trần0,75, không cố định0,40. Allocation thực phải có admission provider/ledger riêng, không suy chi phí thực bằng reservation.
