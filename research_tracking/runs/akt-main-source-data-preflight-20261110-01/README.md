# Gói nguồn và public corpus cho kiểm Colab CPU

Cold public reader thực tế đã đọc hai corpus từ vị trí giải nén mới trên Windows. Corpus development có train/selection/calibration 48/6/6 người mô phỏng, tương ứng 10080/1260/1260 targets. Corpus engineering có 8/1/1, tương ứng 672/84/84. Không tạo model, optimizer hoặc đọc oracle trong phép kiểm.

Notebook có bốn ô mã được kiểm AST. Generator đã được đồng bộ với kiểm symlink tại ancestor và tái tạo đúng byte notebook cuối. Dòng scope prospective trong payload được sửa từ Windows sang runtime đang chạy. Logs Windows gốc vẫn giữ nguyên. Chưa thực thi ô notebook trên Colab/Linux hoặc tạo venv ở máy đích. Torch, Git, CUDA, checkpoint và training chưa được nghiệm thu bởi hồ sơ này.

Gói ZIP gốc 1127266 byte giữ tại artifacts/akt/colab/akt-main-source-data-20261110-01.zip. Tất cả 283 thành viên source/data và embedded manifest đã được đọc lại với CRC và SHA khớp. Hồ sơ này chỉ tham chiếu ZIP cùng các data members bằng SHA/size, không nhân đôi ZIP, corpus hoặc cây giải nén.

Default source bundler bỏ output/execution metadata và serialize notebook Paper2 nên tạo SHA khác dù bản gốc không có output. Public corpus source_inventory ràng buộc raw SHA gốc. Gói Main riêng giữ nguyên bytes notebook nguồn Paper2 để đáp ứng provenance đó. Manifest lưu biến đổi còn lại ở các notebook khác. Không sửa corpus source pins để chấp nhận bản transformed.

Các snapshot trước đồng bộ generator/notebook, logs Windows và logs render/reproduce được giữ riêng. Manifest completed xác nhận integrity đóng gói. Hướng dẫn người dùng ở notebooks/README.md, notebook kiểm dữ liệu tại notebooks/akt_colab_main_data_preflight.ipynb.
