# A0 Junyi — selected fit toàn TRAIN80 và phục hồi sau preemption

Logical model run là `modal-junyi-main-selected-t4-20261112-01`. Các execution01/02 là những lượt cấp tài nguyên nối tiếp cho cùng model, không là hai mô hình độc lập. Source04/Gate2.218 được ghim xuyên suốt, tách khỏi nguồn A1 source07 đang phát triển.

## Quần thể và protocol

TRAIN80 có126.774learners/13.347.331targets, selection10 có15.847learners/1.600.343targets. Vocabulary717 chỉ fitTRAIN80. Cùng split/seed42/FP32/batch4/context100/targetblock100, tối đa20epochs/patience3. Mỗi epoch dùng toàn TRAIN80. Calibration, outer validation, Holdout và refit nằm ngoài lượt selected.

## Execution01 đã xảy ra gì

Modal đã thu hồi container do preemption. Log GPU ghi rõ nguyên nhân. Lần re-execute cùng input gặp durable directory đã có, nên không bắt đầu fit mới. Tại thời điểm phục hồi, Volume còn46checkpoint, mới nhất epoch1/step46000. Đã tải state/metadata/COMPLETE của checkpoint đó và đối chiếu SHA/bytes. Epoch đầu chưa hoàn tất. Số bước sau checkpoint cuối trước khi bị thu hồi chưa xác định.

Guard ban đầu ghi stop-unconfirmed. Sau đó đã đọc lại server, xác nhận đúng App stopped/tasks0. `STOP_RECONCILIATION.json` giữ nguồn và hash của phép đối chiếu. Giữ nguyên chẩn đoán guard cũ. Một lần gọi stop CLI trước đó đã bị hủy ở prompt, không dừng App. Callgraph chưa hiện task ID trong khi container thực tế đã tồn tại, nên dùng thêm container list/file inspection để xác định tiến độ.

Functions có thể bị preempt và Modal sẽ gọi lại cùng input. `retries=0` không loại bỏ cơ chế preemption này. Driver tiếp theo phát hiện durable execution đã có và trả recovery-required hoặc receipt đã lưu, bảo vệ khỏi fit mới ngoài ý muốn. [Tài liệu chính thức](https://modal.com/docs/guide/preemption).

## Phục hồi forensic

Execution01 chưa kịp tạo archive, hai control files ở filesystem tạm chưa được lưu bền vững. Run manifest được tái dựng từ `metadata.identity` đã kiểm SHA. Initial-backbone hash được tính lại bằng đúng source04/encoder717/CPUinitializer seed42, không optimizer update. Có nhãn RECONSTRUCTED_FROM_PINNED_SOURCE_AND_CHECKPOINT. Không có phép đối chiếu hash initial cũ vì file gốc đã mất.

Đây là tái dựng metadata khởi tạo. Trọng số, Adam, các RNG, sampler và counters dùng checkpoint46000 nguyên byte. Native sẽ seed lại, kiểm identity rồi restore checkpoint. Hai control files tái dựng được commit lên Volume và worker chờ acknowledgment trước continuation. Các checkpoint batch được rehydrate thêm vào raw batch-recovery path để giữ tên epoch/step khi không có bước mới.

## Đường dẫn và cách đọc tiến độ

- Execution01 native `experiments/akt/results/modal-junyi-main-selected-t4-20261112-01/`, có index và `recovered-checkpoints/`.
- Execution02 native `experiments/akt/results/modal-junyi-main-selected-t4-20261112-02/`, giữ dispatch/guard/receipt/archive khi có.
- Volume dùng chung `kltn-akt-modal-junyi-main-selected-t4-20261112-01`, mỗi execution có prefix riêng và checkpoint-index.
- `request02.json` ghim điểm46000, control reconstruction, nguồn/data và trần0,85USD. `monitor02.py` chỉ đọc Volume, không cấp GPU.
- Checkpoint đầu ở index execution02 là checkpoint46000 được nhập lại. Chỉ các bước vượt46000 là continuation mới. Counter terminal là cumulative logical run, không cộng hai terminal với nhau.

`local-resume-review.json` và review độc lập ghi các rủi ro đã xét. `prepare_resume.py` chọn checkpoint theo epoch, stage và numeric step; giữ các epoch checkpoint để có thể nạp best cũ. Bundle đang mở, kết quả continuation/epoch/evaluation cần ghi khi thực thi xong.

## Đối chiếu sau execution02 — 12/11

Đã tải archive2.080.202.385byte, kiểmSHA và xác nhận stop acknowledgment. Epoch1/2 hoàn tất, mỗi epoch13.347.331targets/58.166updates. Epoch3 dở dang29updates/6.432targets, không tính là epoch hoàn tất. Thời gian train lần lượt1607,621s và1595,808s. Validation lần lượt248,421s và263,354s, mỗi lần1.600.343targets/0OOV. Log Loss selection0,359648→0,356651. Chưa selected cuối/refit/calibration. `training-status-20261112.json` và `build_training_status.py` giữ đối chiếu có thể chạy lại. Bảng tổng hợp hiện hành tại `research_tracking/reports/AKT_TRAINING_STATUS_20261112.md`.

## Tiếp tục hữu hạn sau execution03

`continue_a0_bounded.py` chỉ tiếp tục cùng logicalA0/source04/data/split/seed/hyperparameter. Đã kiểm3positive/7negative cases bằng stdlib. Chờ execution03 córeceiptinventoryverified vàstopack, rồi tối đa baexecution04/05/06, mỗi lượttrần0,85USD, tổngthêm2,55USD đã đượcRootpreallocate trongledger30USD. Mỗi lượt tự kiểm projectbudget, requestđượcso với lượttrước ở các trườngnguồn/dữliệu/giới hạn/GPU. Partial hợp lệ đượcresume từlatestcheckpoint, complete thìdừng. Lỗi/preemption/thiếuartifact/stop chưa xác nhận đều dừng đểreview. Khôngrefit, graphfit, Holdout hoặc đổi protocol trong bộđiềukhiển này. Cácallocationchưa dùng tiếp tục là dự phòng, không được báo thành chi phí thực.

Tiến độ ở `bounded-continuation-state.json`, log `bounded-continuation.log`. Filelockexclusive chặn khởi độngtrùng, cácchươngtrìnhkhông tự xóaoutputcũ. ROOT vẫn cần nghiệmthu kếtquả cuốivàcậpnhật báo cáo.

## Execution03 nghiệm thu và continuation04

Đã tải archive2.129.675.285byte, kiểmSHA/CRC/inventory vàstopack. Epoch3đủ13.347.331target/58.166updates, train1753,718s vàvalidation266,045s trên1.600.343target/0OOV. LogLossselection0,355650902, history1/2khớp nguyên trạng. Epoch4partial3.431.632targets/15.016updates đã đượcgiữ. `verify_execution03.py` và `execution03-verification.json` kiểmcumulative3epochs+partial, khôngcộnglại importedsteps. Selectedcuối/refit/calibration cònmở.

Bộnốilượt đã dùng sai nhãnreview trongrequest04lầnđầu, controllerdừng trướcbilling/App/GPU. `gpu-execution04.log`, `request04-rejected-before-dispatch.json` vàstatecũgiữnguyên. Đãsửabộnốiđúnghợpđồngcontroller, bổsungASTcontractcheck vàdryplans3/2/1lượt. `bounded-continuation-remediation.json` giữkiểm. `gpu-execution04-reviewed.log` làlượt thựcthi04tiếptụctừepoch4step15016. Bộnối mới chạy `--after-execution04`, chờ04córeceiptverified+stopack rồi tốiđa05/06, cap1,70USDđãpreallocate. Log/state/lock cóhậutốafter04 đểgiữfailurecũ, khôngtăngallocationtừlỗilocal.
