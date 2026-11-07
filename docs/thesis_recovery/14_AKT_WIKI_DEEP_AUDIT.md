# Kiểm toán mở rộng DeepWiki và AKT KLTN

Ngày 07/11/2026. Mở rộng báo cáo 13 theo chín URL và các trang con người dùng cung cấp.

## Kết luận và phạm vi

KLTN dùng nguyên class AKT ở commit `01b7e8d7d7c862cabc9467108e3e7f2555653a88`, cùng commit DeepWiki index. Adapter hiện tại là **AKT-NonRasch exercise-level cho Junyi**. Kiến trúc attention và tính nhân quả kế thừa upstream. Vocabulary, windowing, loss reduction và protocol chọn epoch có điều chỉnh. Chưa có bằng chứng tái lập kết quả bài báo hoặc hoàn tất training CUDA.

Nguồn quyết định là `artifacts/akt/dependencies/upstream/{akt.py,load_data.py,main.py,utils.py,run.py}`. Checkout upstream sạch khi kiểm tra. Nguồn online cố định tại [commit upstream](https://github.com/arghosh/AKT/tree/01b7e8d7d7c862cabc9467108e3e7f2555653a88). Các fixture mới chỉ dùng dữ liệu tổng hợp.

## Phạm vi trang đã truy cập

Các đường dẫn dưới đây nối với `https://deepwiki.com/arghosh/AKT/`. Inventory máy đọc được nằm trong `evidence/akt-wiki-deep-audit-20261107.json`.

| Nhóm | Trang đã đọc thành công |
|---|---|
| Chín trang yêu cầu | `1-home`, `2.1-installation-and-dependencies`, `2.2-running-models`, `3-model-architecture`, `3.1-core-components`, `3.2-model-variants`, `4-datasets`, `4.1-assistments-2009-dataset`, `4.1.1-training-data-format` |
| Kiến trúc con | `3.1.1-akt-class`, `3.1.2-architecture-class`, `3.1.4-multiheadattention-and-distance-aware-attention` |
| Dữ liệu con | `4.1.2-test-and-validation-splits`, `4.1.3-metadata-files`, `4.2-assistments-2015-dataset`, `4.2.1-data-schema-and-organization` |
| Giải thích bổ sung | `5-knowledge-tracing-concepts`, `5.1-student-interaction-modeling`, `5.2-skill-and-opportunity-tracking`, `6.1-known-issues-and-bug-fixes` |

Ba trang con không tải được sau thử mở trực tiếp và qua mục lục gồm `3.1.3-transformerlayer-class`, `3.2.1-akt-rasch-(akt_pid)`, `3.2.2-akt-nonrasch-(akt_cid)`. Không suy diễn nội dung các trang này. Cơ chế tương ứng được kiểm bằng `akt.py` và `utils.py`. Một số trang đã đọc thành công trước đó có lỗi khi tải lại.

## Đối chiếu cơ chế mô hình

| Thành phần | Mã upstream thực tế | KLTN và kết luận |
|---|---|---|
| NonRasch | `utils.load_model` gán `n_pid=-1`, Rasch chỉ bật khi `n_pid>0` | Adapter truyền 0, cùng tắt nhánh difficulty |
| Embedding | Khi `separate_qa=False`, giải mã correctness bằng `(qa-q)//N`, cộng embedding đáp án với embedding q | Dùng nguyên source, không thay bằng embedding trực tiếp combined QA |
| Transformer | `blocks_1` có n block, `blocks_2` có 2n block | KLTN n=1, giữ nguyên stack |
| Mask | Mask 1 cho current/past, mask 0 strict-past và zero attention hàng đầu | Không đồng nghĩa full bidirectional visibility |
| Distance-aware attention | Gammas học được điều chỉnh attention theo khoảng cách ngữ cảnh | Giữ native implementation, chưa có graph augmentation |
| Position | `apply_pos` điều khiển FFN trong layer, các class positional embedding không được instantiate trong đường forward AKT | Không diễn giải tên biến thành việc đã thêm positional embedding |
| Output | Ghép hidden với q embedding, FFN ra sigmoid probability | Native parity đã kiểm tại cùng cấu hình |
| Loss | BCE tổng trên label > -0.9, cộng regularization nếu Rasch | KLTN chia theo số target được chấm trước backward, gradient scale khác |

Trang AKT Class còn đảo mô tả correctness 0/1 trong bảng embedding. Convention của loader và labels là 1 đúng, 0 sai. Cần đọc biểu thức source khi gặp mâu thuẫn giữa các trang wiki.

## Các sai lệch quan trọng trong mô tả dữ liệu

### Encoding QA

Trang Training Data Format viết `qa = question_index * 2 + correct`. Loader được pin thực hiện `qa = q + correct * n_question`, q bắt đầu từ 1 và padding bằng 0. Với N=3, q=[1,2,1,3,2], y=[1,0,1,0,1], QA=[4,2,4,3,5]. Test mới xác nhận bằng cách gọi thẳng loader upstream.

### File đầu vào

Wiki mô tả bảng event với user/problem/skill/timestamp/opportunity. Loader training thực nhận nhóm dòng. `DATA` nhận ba dòng gồm header, Q và A. `PID_DATA` nhận bốn dòng gồm header, problem IDs, skill IDs và A. Loader không sort timestamp hay dùng metadata JSON để tự dựng chuỗi.

`DATA` trả ba giá trị gồm q, qa, student indices. `PID_DATA` cũng trả ba giá trị nhưng giá trị cuối là problem IDs. Không có bằng chứng lỗi unpack hai thành ba trong checkout này. Phải phân biệt kiểu dữ liệu thứ ba theo loader khi xây integration.

### Skill và problem

Trong PID_DATA, q là skill ID, pid là problem ID riêng. Mô tả q_data là problem ID trên trang ASSIST2009 không khớp loader. KLTN dùng exercise Junyi làm q trong NonRasch. Đây là thay đổi đơn vị token cần công bố rõ khi báo cáo kết quả.

### Header và thống kê

Header như `891,78276` bị diễn giải khác nhau giữa các trang wiki. Loader bỏ qua giá trị header và gán student index theo vị trí nhóm dòng. Fixture thay header tùy ý giữ nguyên mọi array đầu ra. Vì vậy không dùng header mẫu hoặc số file để chứng minh số learner, số interaction hay learner-disjoint CV.

### Căn chỉnh target

Native AKT dùng q_t và response quá khứ để dự đoán y_t ở cùng vị trí. Strict-past attention chặn response hiện tại. KLTN nhận `prior_responses`, dựng lại aligned QA từ các đáp án đã quan sát, đặt placeholder ở vị trí cuối. Không dịch target thêm một lần.

Fixture mới xác nhận q và QA prefix trùng native loader. Các test nhân quả hiện có xác nhận đổi đáp án hiện tại/tương lai không đổi dự đoán hiện tại/quá khứ, và đáp án quá khứ có thể ảnh hưởng dự đoán tiếp theo. Đây là kiểm tra synthetic CPU với tolerance, không chứng minh mọi đường dữ liệu thật hoặc CUDA.

### Fold và metadata

Main upstream dùng train/valid/test theo chỉ số cấu hình. Gợi ý ghép tùy ý train/test hoặc dùng test để validation trên wiki không xác lập một protocol hợp lệ. File counts không chứng minh learner disjointness. KLTN phải giữ split manifest, train-only vocabulary, inner validation và Holdout guard của dự án. Không đọc nội dung Test để thực hiện kiểm toán này.

## Các khác biệt cấu hình cần công bố

| Hạng mục | Upstream CLI mặc định | KLTN hiện tại |
|---|---|---|
| d_model / heads / blocks | 256 / 8 / 1 | 256 / 8 / 1 |
| d_ff thực chạy | 2048 vì utils không truyền parser d_ff=1024 | Truyền tường minh 1024 |
| Dropout / final FC | 0.05 / 512 | 0.05 / 512 |
| Learning rate / batch | 1e-5 / 24 | 1e-4 / 4 |
| Seed / clipping | 224 / tắt mặc định | 42 / 1 |
| Chuỗi | Chunk rời, seqlen 200 | H100/T100, tối đa 200 |
| Chọn epoch | Validation AUC, max300, heuristic >40 | Inner validation Log Loss, patience3, max20, outer refit |
| Môi trường | README lịch sử Torch1.2/Linux | .venv hiện tại Torch2.7.1 CPU/Windows |

Chi tiết d_ff và số parameter trên vocabulary tổng hợp nằm ở báo cáo 13. Native parity cùng cấu hình không chứng minh training recipe parity hoặc numerical parity với Torch1.2. Khác runtime cần kiểm CUDA thực trước cloud training. Không tự thay hyperparameter trong lần đối chiếu này.

## Hệ quả cho KLTN và thứ tự tiếp theo

1. Giữ native core cùng provenance. Dùng tên AKT-NonRasch exercise-level adapted for Junyi trong manifests và luận văn.
2. Chốt architecture identity d_ff1024 hoặc một thay đổi được duyệt trước khi tạo GPU artifacts. Không cần sửa lên2048 chỉ vì CLI upstream mặc định thực chạy như vậy.
3. Giữ encoding theo loader gốc và các kiểm tra causal, padding, OOV. Không sửa theo công thức QA sai trên wiki.
4. Hoàn thiện nối checkpoint/resume vào CLI selection/refit/early-stopper và làm mới evidence Gate2 theo source hiện tại.
5. Thực hiện bounded CUDA lifecycle, resume, export và throughput checks trước full training. Chưa có successful Task14 mới trong bằng chứng đã kiểm trước đó.
6. Tách vocabulary và training Junyi với simulator Grade10. Checkpoint embedding Junyi không tự tương thích 28 concept. Cần contract item/concept, synthetic train/validation learner và mastery query cho simulator trước RQ3 closed-loop.
7. AKT đang kiểm là baseline graph-free. Fixed-graph và CG-AKT cần đường triển khai và ablation riêng theo research plan. Wiki không cung cấp bằng chứng cho các nhánh này.

## Bằng chứng xác minh mới

`tests/akt/test_upstream_data_contract.py` bổ sung bốn test fixture cho DATA, PID_DATA, header và alignment adapter. Chạy cùng `test_upstream_parity.py` và `test_causality.py` bằng `.venv/Scripts/python.exe -B` đạt **17 passed in 11.28s**, log `evidence/akt-wiki-data-contract-tests.log`.

Không cài thư viện, không chạy benchmark dữ liệu thật, không đọc Holdout hoặc cấp GPU. Thay đổi của lần kiểm toán chỉ gồm tests, tài liệu và tracking. Các file có sẵn chưa commit trong working tree được giữ riêng.

## Kiểm tra tiếp sáu trang kiến trúc theo yêu cầu

Đã mở lại AKT Class, Architecture Class và MultiHeadAttention thành công. TransformerLayer và hai trang Rasch/NonRasch tiếp tục fetch failure khi mở trực tiếp, qua mục lục và URL có query. Trạng thái truy cập ba trang này vẫn chưa giải quyết. Cơ chế được đối chiếu từ source đã pin, không coi đây là đã đọc nội dung wiki bị lỗi.

Architecture Class mô tả đúng hai stack và thứ tự attention. Các block chẵn của blocks_2 dùng q/q/q, mask1 và bỏ FFN. Block lẻ dùng q/q/history, mask0 và bật FFN. `apply_pos` điều khiển position-wise FFN. Không có positional embedding mới được cộng trong forward này.

Trang attention có hai giải thích cần thu hẹp. `zero_pad` zero hàng attention đầu tiên vì chưa có lịch sử dưới strict-past mask. Đây không phải cơ chế tổng quát phát hiện padding token. Gammas được khởi tạo Xavier uniform, rồi đi qua negative softplus. Gamma thô bằng0 vẫn cho hệ số -log(2), nên không thể kết luận khởi tạo gần0 có nghĩa attention chuẩn không decay.

Nhánh Rasch trong source thêm difficulty scalar theo pid, các embedding chênh lệch và L2 trên difficulty. NonRasch tắt nhánh đó khi n_pid≤0. KLTN hiện n_pid0 và separate_qaFalse. Việc wiki có trang Rasch không tạo thêm yêu cầu tự đổi baseline sang Rasch. Các quyết định model của KLTN tiếp tục dựa đề cương và experiment plan.

Nguồn kiểm tra gồm [Architecture Class](https://deepwiki.com/arghosh/AKT/3.1.2-architecture-class), [Attention](https://deepwiki.com/arghosh/AKT/3.1.4-multiheadattention-and-distance-aware-attention) và [akt.py tại commit đã pin](https://github.com/arghosh/AKT/blob/01b7e8d7d7c862cabc9467108e3e7f2555653a88/akt.py).
