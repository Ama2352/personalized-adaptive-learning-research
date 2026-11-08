# GRAPH11 — review độc lập nguồn checkpoint01

Phạm vi: đọc tĩnh `research_graph_checkpoint.py` SHAa2f9fdcaf0370d82640c17867941a538d92ba12e43e90fbc15b0007944d767f3 và `test_research_graph_checkpoint.py` SHA538eeeb74e3f9caf93e36f8550b8e3789498fa15b4431aa25e580aba72b3de46; đối chiếu training/model/context và source Adam local. Không import/AST/test/model/data/Git. Chưa là chấp thuận native allocation. Không lặp finding protocol21 mà ROOT đã chuyển tác giả.

## Finding cần xử lý hoặc giới hạn lời tuyên bố

**P2 — ca native hiện chưa trực tiếp assert restore RNG và modes.** Tests:212–226 bảo toàn RNG/modes quanh evaluation, 297–304 so prediction/model/Adam; không assert trạng thái Python/NumPy/Torch RNG hay từng module mode ngay sau restore. Fixture không override dropout; kế thừa frozen simulator-research dropout0,05. Vì vậy continuation equality có thể cung cấp kiểm tra gián tiếp việc khôi phục Torch RNG; không được nói continuation dùng dropout0 hoặc tự kết luận nó không nhạy với RNG. Source:696–704 thực sự validate RNG bằng generators tạm và mode names/bool trước mutation; source:730 mới restore RNG cuối. Đây là khoảng trống kiểm tra trực tiếp ba RNG/modes, không lỗi restore đã được quan sát và không phủ nhận indirect continuation parity. Sửa nhỏ trong fixture có sẵn: trước restore đặt fresh module modes khác snapshot; ngay sau restore, trước evaluation, đối chiếu ba RNG states và toàn bộ modes với payload. Thêm malformed RNG/mode payload vào negative validation trước hai `load_state_dict` spies; không thêm forward/optimizer/constructor.

**P2 nhỏ — dtype mặc định đổi sau constructor có thể chỉ bị phát hiện sau Adam body.** Model:234–235 chỉ kiểm defaultdtype tại constructor. Checkpoint `_owned`:209–234 kiểm tham số FP32 nhưng không recheck defaultdtype; `_pre`:370–381 có thể cho body chạy. Adam local `optimizer.py`:209–214 / `adam.py`:166–173 tạo scalar step float64 nếu ambient defaultdtype đã đổi sang float64; `_post`→`_validate_states`:282 sẽ reject vì đòi float32 sau body. Không false-complete, nhưng fail có mutation tránh được. Sửa tối thiểu: kiểm `torch.get_default_dtype()==torch.float32` ở `_owned` trước body, không tự đổi globaldtype. Đây là edge case đọc nguồn; chưa execute, không khẳng định xảy ra trong runtime ROOT định dùng.

## Các điểm đã đối chiếu, chưa thấy blocker mới

- Callback tương thích native `train_epoch`: training:188–198 tạo đúng `EpochStats`; :211–246,:323,:350–353 phát progress và final. Checkpoint:399–430 dùng đúng keys/attributes; final callback không cộng batch hai lần.
- Full phase là equality thật: :293–301 lấy toàn bộ windows/target keys từ index; :354–365 chặn lặp/ngoại lai; :424–430 reconcile full set, target count và actual steps. Hai partial E2 trong tests không được cấp complete receipt.
- Named participation :375,:391 đếm gradTensor kể cả tensor0; :274–286 phân biệt absent/empty/initialized, cấm literalNone, step bằng count riêng từng parameter. Không ép late graph branch có globalstep bằng backbone.
- Restore :675–704 yêu cầu fresh ownership/source/initial backbone, bounded hashed payload, state/Adam/RNG/modes/population validation trước :707–710 mutation. Lỗi sau mutation poison/discard, không rollback. Không phát hiện thay đổi methodology: chỉ select_train80/refit_union90; checkpoint không selector/iterator/global-budget resume hoặc quyền fit. SHA-shaped profile/freeze là binding, không authority.

Đề xuất: tác giả cân nhắc hai sửa nhỏ trên trước source freeze; ROOT quyết định native workload4updates/6forwards sau review. Không cần framework/checkpoint format mới.

## Đính chính tiền đề sau ROOT review

Bản trước SHA7990a3b0384cf23a49d3b983d055a5086b77235baa9bcd76d96c191c8fc729b8 được giữ nguyên ở `GRAPH11_INDEPENDENT_REVIEW01.before_dropout_erratum.md`. Câu dropout0 là suy đoán sai của reviewer, không có nguồn fixture hỗ trợ. `test_research_graph_model.py:81–85` dùng AKTConfig(phase='simulator-research'); checkpoint fixture:175–176 chỉ replace namespace và max_steps; config.py:52,164 giữ dropout0,05. Đính chính này không sửa code/test/native outputs hay protocol và không tuyên bố actual test đã chạy.
