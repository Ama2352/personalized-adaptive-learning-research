# Sửa bootstrap venv Colab CPU sau lỗi ensurepip

## Bằng chứng và mục đích

Lượt A2 đầu dừng trước calibration với CalledProcessError. Probe CPU thật do nhánh chính thực hiện xác nhận source và Python trong venv tồn tại, pip trong venv thiếu, còn uv có sẵn tại /usr/local/bin/uv. Log và receipt gốc nằm trong bundle `junyi-calibration-real-20261117-01`; bundle này giữ bản sửa và kiểm hồi quy local.

## Thay đổi

Runner tạo venv mới bằng `with_pip=False`, dùng uv có sẵn để cài chín phiên bản dependency cố định vào đúng Python của venv. Venv dở dang được tái sử dụng. Cache uv đặt trong source/artifacts/akt/uv-cache. Không cài vào Python global và không gọi ensurepip. Khi subprocess lỗi chỉ ghi tên chương trình và mã thoát, không ghi tham số hoặc output có thể chứa thông tin riêng.

Notebook hiện hành được dựng bằng build_notebook.py trong bundle này. Generator V1 và các hồ sơ V1 đã đóng giữ nguyên. Payload nguồn 6fa3012a6d2f321d12d4ae42be2c1fb4ee2e832f26f45459cdb2c51e8e652647 và source KT d22 không thay đổi. Runner mới có SHA b80c20a05a1ad7c7733785fdf6d03e9e68fe7c03b1f4538989db6231bdf14ea1, phải staging tên mới và phase mới trước khi chạy.

## Kiểm tra và giới hạn

Tests kiểm đường venv dở dang, venv mới không ensurepip, command uv chỉ đích venv, cache có phạm vi dự án, thông báo lỗi không lộ token và bootstrap notebook. Các kiểm tra wrapper raw/fit/Drive-resume cũ được chạy cùng. tests01 đạt 25 ca, sau đó bổ sung kiểm notebook nhập os. tests02 ghi lỗi thiếu import Path của fixture, đã giữ nguyên log. Sau sửa fixture, tests03 đạt 26 ca trong 8,28 giây trên nguồn cuối.

Đây là sửa môi trường vận hành. Chưa chứng minh cài dependency thành công trên phiên Colab thật, chưa chạy lại calibration và chưa tạo số liệu nghiên cứu mới. Nhánh chính sở hữu staging và thực thi Colab, không có compute cloud từ bundle kiểm local này.
