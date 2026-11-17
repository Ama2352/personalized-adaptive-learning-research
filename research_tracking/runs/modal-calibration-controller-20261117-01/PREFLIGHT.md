# Bổ sung preflight CPU actual image

`create_app()` nay trả thêm key `preflight`. Function này không GPU/Secret,1CPU,4096MiB,timeout120s. Child `.venv/bin/python` chạy tối đa90s, không model hoặc data. Function trả JSON nhỏ, chưa chạy cloud trong nhánh triển khai này.

`runtime_preflight` gọi verify_upstream thật để kiểm commit/tree/remote, working tree sạch và hash-object của source upstream. Sau đó import Torch chỉ đọc metadata CPU, bắt buộc Python3.13.18, Torch2.7.1+cu126, CUDA build12.6, kiểm `torch.cuda.is_initialized()` vẫn false trước/sau source hashing. Không gọi cuda.is_available hoặc tạo tensor CUDA.

Receipt trả actual inference_source_identity trên image, cùng SHA của sáu script controller/worker/helper. Root dùng identity thực này cho request A0–A3 và CPU join, đối chiếu worker/controller SHA với plan đã đóng. Không suy source identity local bằng image, vì upstream Git checkout Linux có thể khác line ending của checkout local dù cùng commit.

`TESTS06.txt` ghi23ca đạt trong5,45giây. Test mới dùng fake Torch và fake verifier để kiểm wiring/path/commit, tránh import Torch local khi RAM thấp. Existing test SDK thực vẫn kiểm nested serialization. Chưa xác minh runtime actual image của wrapper mới, root cần gọi preflight trước CPU cache hoặc GPU. Đây là tiến bộ phần mềm, chưa có số đo inference hoặc kết quả nghiên cứu mới.

`MANIFEST02.json` ghim source bổ sung và log mới. Hồ sơ TESTS05/MANIFEST trước được giữ.
