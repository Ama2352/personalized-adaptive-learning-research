# GRAPH29 pause5 phiên bản02, chỉ chuẩn bị nguồn

## Lỗi thực tế của01

Nguồn chuẩn research_selected_runner.py dòng240–241 tạo trước fit80, selection và checkpoints. Đọc filesystem sau lượt01 thấy selection tồn tại, rỗng. Tất cả COMPLETE.json, selected-terminal.json, selected-claim.json, stage-completion.json, failure.json, refit90 và calibration đều vắng. Worker01 dòng329 đã từ chối chỉ vì thư mục selection tồn tại.

Result01 ghi 5epoch, 10optimizer steps, 3360training target exposures, 15native forwards, 5validation passes/420targets và 5checkpoint saves. Worker89.69250139995711s, outer lưu91.72829509997973s. Đây là công việc thực đã tiêu thụ. Lượt01 vẫn REJECTED, không có sealed terminal, không được phục hồi bằng seal hồi tố. Inventory mới tham chiếu SHA nguyên byte của result, observer, outer-final và failure.log. Lỗi launcher đầu tiên thiếu src xảy ra trước construct thành công, trước owned/native dispatch theo ROOT. Lần launcher sau dùng đường dẫn nguồn đã đi qua native.

## Thay đổi nguồn02

Bốn bản01 được inventory trước copy và kiểm SHA source/copy lại trong graph29-pause5-v02-before01. Bốn bản02 dùng tên request, dry, config, auth, metadata outputs, native outputs và run-id mới kết thúc02.

Hai thay đổi hành vi duy nhất ngoài đổi tên đường dẫn

- Outer02 thêm repo/src vào sys.path ngay trước gọi worker.construct(request). Không đặt PYTHONPATH.
- Worker02 kiểm vắng mọi file terminal/claim/stage-completion/failure và các phase refit/calibration. Thư mục selection phải là thư mục có thật và rỗng hoàn toàn. Các exported leaves predictions.csv, targets.csv và coverage.json cũng vì thế bị cấm.

Các so sánh five-epoch receipts, native BCE, raw prediction semantic SHA, initialization, latest5 khác best4, stale1 và accounting giữ nguyên. Producer/public authorization/Gate183/nguồn Main không đổi. Không sửa dữ liệu hoặc các đầu ra01.

## Đề nghị hạn mức cho ROOT review

Giữ parent outer180, owned170, worker160, cleanup3. Chính sách ghi charged_parent_wall_seconds180, là khoản dự trù bảo thủ. Dòng parent02+child tương lai bị chặn bởi wall540, training300, 40steps/13440targets và tối đa3model/Adam constructors. Child whole tối đa360. Khoản dự trù và elapsed quan sát là hai trường riêng. Chi phí actual01 ở trên vẫn được lưu và phải tính trong hồ sơ kỹ thuật chung.

Giữ native admission4GiB/free floor2GiB/workerRSS1GiB/disk2GiB. Metadata preparation outer60/owned57/worker50, free2GiB/RSS1GiB. Đây là đề xuất nguồn chờ ROOT duyệt, chưa cấp quyền chạy.

## Entry points đề nghị cho ROOT

Chạy bằng .venv Python -B và exact Win03 process Git profile đã review, sau khi ROOT kiểm cú pháp/diff. Không thực thi các entrypoint trong lượt chuẩn bị này.

1. run_prepare_graph29_a0_pause5_package02.py --prepare-dry --approval-reference ROOT_GRAPH29_A0_PAUSE5_REVIEW02 --worker-sha256 e3d54aea0806c6158c51558e565d7f84929b790b540b656424a4c2e81622eb81 --outer-sha256 3fc4597f0d7ead0d28eca8ceb672bbacf21ff02246cc35207df46666f5ec3ee2
2. Cùng outer02 --materialize sau khi ROOT đọc actual dry, truyền actual --expected-dry-sha256 và --review-reference. Không có SHA mặc định.
3. run_graph29_a0_pause5_02.py --request artifacts/akt/local-tests/akt-research-runner-20261108-01/graph29_a0_pause5_02_request.ROOT.json --request-sha256 SHA_THUC_TE_DO_ROOT_CUNG_CAP --worker-sha256 1a01f445690ad5f41573df3faaf92d5a9856985f4e97755762d6b5a6908b4664 --outer-sha256 33530306d58def1b53e61710464b55d754fbfca3ac7b7a67d6140bcaccb161d0 --approval-reference ROOT_GRAPH29_A0_PAUSE5_REVIEW02

Chuỗi SHA_THUC_TE_DO_ROOT_CUNG_CAP là chỉ dẫn văn bản, không là giá trị hợp lệ để dispatch.

Chưa có actual parent02 terminal hoặc SHA để nhận child. Child preparer phải chờ external actual accepted parent outer/sealed terminal/owned receipt/request/spec SHA. Chuẩn bị metadata chỉ kiểm raw bytes và launch lineage, không gọi full canonical inspect_parent vốn nhập Torch. Canonical inspector chỉ chạy sau genuine GO trong NN child được duyệt, trước constructors. Không tạo child authorization từ bool hoặc metadata-only PASS. Phase1 chỉ intentional pause, chưa giải quyết unexpected crash recovery.

Không Python/import/AST/test/native/Git nào được chạy bởi agent. Chưa có kết quả02.
