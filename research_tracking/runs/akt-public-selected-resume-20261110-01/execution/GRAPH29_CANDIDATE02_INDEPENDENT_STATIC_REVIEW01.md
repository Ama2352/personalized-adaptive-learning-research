# GRAPH29 candidate02 — review độc lập đường pause/resume

Nguồn-only09/11/2026. Đọc sáu candidate files, helper0dc và các primitive checkpoint/training liên quan. Không import, Python, compile, test, native hoặc Git. Chưa phát hiện blocker cụ thể trên các đường được hỏi.42ca là inventory tĩnh của tác giả, chưa là kết quả thực thi.

## Các ràng buộc đã đối chiếu

- `research_selected_resume.py:96–168,206–235,358–395` nối worker result với external request/spec SHA, invocation/auth bytes, launch/ready/GO byteSHA, worker/owner native tokens, job/nonce, exact argv/command và helper/worker pins. Nhánh direct-worker phân biệt đúng shim. Trộn receiptA với resultB cùng worker source vẫn vướng token/job/request/ready/GO. Đây là consistency của bytes được ROOT ghim, không tự tạo process authority từ manufactured fixtures.
- `research_main_execution.py:389–422,510–558,565–576` giữ genuine factory. Pause/resume dùng closed decision riêng cùng full control payload. Parent terminal được SHA-check và charge trước metadata/data work. Current runtime/Gate/source/corpus vẫn đi qua `_auth/_metadata` và public reader. Public runner tự gọi factory, không nhận guard hoặc verified callback từ caller.
- `research_selected_runner.py:45–65,98–110,146–179,274–306` seed logical committed counters/training/wall/output từ cha trước restore. Restored tracker event có nhánh riêng, không tăng một bước Adam giả. Bước sau dùng remaining cumulative quotas. Parent1+child2 constructors bị giới hạn3. Hạn retained bytes phải bằng exact spec cap trong policy/request, rồi parent retained cộng vào usage child.
- `research_selected_resume.py:181–203,268–299` cùng runner`:274–306,313–335` tách latestE và bestB. History1..E replay bằng genuine EarlyStopping, natural stop/maxepoch không được tiếp tục. Latest inspect trước constructor, fresh initial state phải trùng rồi mới restore. Nếu best còn ở cha, copy có source/copy/source-after SHA và quota trước final reload.
- Low-level `research_graph_checkpoint.py:818–854` restore named state/participation/modes, rồi Python/NumPy/Torch RNG sau constructor và restore event. Từ runner restore tới next train chỉ có metadata/hash/guard/index operations trong source đã đọc. `training.py:94–109,326` dùng private shuffle seed+epoch. Chưa có actual fresh-process equality chứng minh phần này.
- Fresh default vẫn chọn original authorization factory, không thêm resume fields vào spec/auth/invocation wire. `_Run` mặc định parent=None và counters0. Optional controlled branch chỉ Windows CPU, không cấp CUDA, refit hoặc calibration. Các imports mới là lazy ở selected path.

## Giới hạn trước apply/run

Bộ test hiện thêm metadata/stopper/quota/crosswire fixtures, chưa điều khiển toàn bộ public resume success path hoặc CP thật. Future worker phải ghi ownership trực tiếp từ genuine `worker_gate()` và parse actual request theo đúng six-argument convention. Future ROOT outer còn phải kiểm final whole elapsed SAU seal/hash/write, giữ postwrite failure override. Intentional pause không đóng unexpected-fault/partial-epoch physical-cost recovery. Không có kết luận numerical continuity, fitted model hoặc GPU readiness từ review này.

## Exact candidate SHA

| Path dưới cgakt-selected-resume-candidate02 | SHA-256 |
| --- | --- |
| src/knowledge_tracing/akt/research_selected_resume.py | 49f74a87a5fa6f11b923c102389695c2c582257d7a782d9cf32caab819cf70d1 |
| src/knowledge_tracing/akt/research_main_execution.py | 0c27b05312c723e34c0590ddec00009e849687cd2a1c5c303c5f93723ca64e77 |
| src/knowledge_tracing/akt/research_selected_runner.py | b2b045d4673ff6cbc8e4e4ade8e5599806e52e501f5c8612e894ff636c2f7a46 |
| tests/akt/test_research_selected_resume.py | 7d363fbc100263b577243bcc6b4fe98a4b0d499cdb89796e09dcadf28d4e393d |
| tests/akt/test_research_main_execution.py | 88301abdf84456022827349fa5196576fce25b155042a4e5edf6be91eeeb9a7f |
| tests/akt/test_research_selected_runner.py | 2fe4526620d14b2d8cf809590185f50abf8b1f3d742a5fec083d6fb88eeccfd4 |
