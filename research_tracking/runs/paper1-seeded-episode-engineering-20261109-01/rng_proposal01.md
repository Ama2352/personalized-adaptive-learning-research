# RNG wrapper tối thiểu cho episode continuity theo PDF Paper1

Ngày09/11/2026. Đề xuất nguồn, chưa triển khai/import/test/simulation/Git. E1/E3 đã có episode supplied và72regression tests đạt, gồm18case mới. Gói tiếp theo chỉ tạo draws bằng RNG riêng rồi gọi lại episode đó, giữ nguyên controller/domain/primitives và continuity policy.

## Nguồn và điều đã biết

PDF chính thức SHA `984e2f825968c212ca7e76db23a4c9501659ed880ecff6dce437590ad49167f4`, tr.3 IV.A, xác định US Normal(1400,50²), UW Normal(1050,50²), FW Normal(1000,50²) ở unit hàm số và Normal(1250,50²) nơi khác. Estimate bắt đầu1200, riêng FW/unit hàm số1050. D37 xác định PDF là nguồn có thẩm quyền. PDF không định từng seed ID, PRNG, thứ tự rút mẫu hoặc coupling giữa branch.

`episode.py` SHA `e01fc94656e206101a6ab6dfc960eb24ac331a677f3711c2b4561fbcd840b471` đã scale suppliedz và giữ literal cap sau feedback. `test_episode.py` SHA `d0bf6e052d9e2618b0b2d3ecf729164da68d99fc49a42e4c6dc0eadf6b4db1c0` kiểm dữ liệu dựng tay. Spec02 SHA `2c83655f63d973e3d009a5d091bfd2405513b89e00f782b1f68ab2b03268b176` đề nghị key theo concept-local practice count. RNG wrapper sẽ cụ thể hóa một phiên bản prospective, không nhận historical draw identity.

Đã đọc tĩnh stdlib `C:/Users/AmaDev/AppData/Local/Programs/Python/Python313/Lib/random.py`, SHA `b8586e6bdd037fcd0e53e9529f0e257afaac5fa62eaf59d5d4ac02829656897e`. `Random.seed` dòng128 xử lý seed của instance; `gauss` dòng555 dùng generator riêng và có Gaussian cache. Một instance mới cho mỗi init key, gọi gauss một lần, nên cache dư không nối sang concept khác. Đây là source inspection, chưa có runtime proof mới.

## API đề nghị và scope hai file mới

Thêm `src/knowledge_tracing/paper1_pdf/seeded_episode.py` và `tests/paper1_pdf/test_seeded_episode.py`. Không cần sửa `episode.py`, `simulator.py`, domain CSV hoặc export chung.

- `prepare_seeded_draws(bank, *, chapters, persona, function_chapter, root_seed, replicate_id, horizon)` trả frozen object gồm `InitialProfile`, tuple tape theo node, key-scheme identity, profile/tape SHA và logical draw counts. `root_seed` là int tường minh0..2**63−1, reject bool; replicate_id là logical learner/replicate identifier không rỗng, có giới hạn độ dài. Persona, function chapter và horizon được kiểm trước tạo RNG. Bank/tape bounds giữ1..28concept, horizon1..500 như core.
- `run_continuity_episode_seeded(bank, *, chapters, edges, traversal_order, draws)` gọi đúng `run_continuity_episode_supplied` với profile/tape đã chuẩn bị, trả kết quả core kèm draw identity. Không thêm loop cập nhật estimator/world. Một draws object có thể dùng lại qua các branch với graph/order khác nhau, vì nó bất biến.

Việc chuẩn bị draws là riêng của wrapper, controller chỉ được cấp các estimate ban đầu như API supplied hiện hành. Oracle latent do initializer chuyển vào world. Profile/tape gắn bank và chapter map; đổi domain, persona, logical replicate hoặc seed phải có identity riêng.

## Công thức key và RNG prospective

Chọn version `paper1-pdf-keyed-private-random-v1`, chờ Root xác nhận. Canonical JSON UTF-8 dùng ensure_ascii=False, sort_keys=True, separators=(',',':'), allow_nan=False. SHA256 của key object được đổi thành integer seed đầy đủ256bits cho một `random.Random` mới. Không dùng `hash()` của Python, global seed hoặc generator toàn module.

| Event | Key object |
|---|---|
| Init z tại node v | `{version,root_seed,replicate_id,persona,event:'initial_normal',concept_id:v}` |
| Uniform của practice n tại v | `{version,root_seed,replicate_id,persona,event:'response_uniform',concept_id:v,previous_interactions:n}` |

Init gọi đúng `Random(key_seed).gauss(0.,1.)` rồi đưa z vào `initialize_profile`; scale50 chỉ diễn ra một lần trong core. Response gọi đúng `Random(key_seed).random()`, bảo đảm0≤u<1. Tạo tape theo sorted node IDs và local n=0..horizon−1. Mỗi event có key riêng nên đảo thứ tự dựng node hoặc thêm branch không làm tiến stream của event khác. Tách key namespaces là lựa chọn mô hình pseudorandom; một test không chứng minh độc lập thống kê hoặc normality.

Không clip Gaussian ban đầu. Tail trên1500 được giữ, sau feedback áp dụng literal operator hiện có `min(1500,before+12)`. Không rejection-resample để tránh tail, không tìm seed cho kết quả thuận lợi.

Root seed/replicate/persona giữ trong key. Graph ID, policy ID, run folder, global step và item ID không nằm trong key. Vì thế B1/GA continuity branches của cùng logical learner có cùng init latent và cùng u ở lần thực hành thứ n của cùng concept. Khi item difficulty khác nhau, cùng u vẫn được so với p_true của item thực chọn. World không có forgetting nên latent trước cùng local n là cùng một giá trị dưới cùng init. Đây là common-random-number coupling được khai báo cho phiên bản mới, không biến hai branch thành một observable fixed stream.

Khác persona có namespace riêng trong đề xuất này. Không gọi đó là đối chứng thay riêng mean ability trên cùng z. Nếu cần shared-z xuyên persona về sau thì phải khai báo một coupling version khác trước nghiên cứu.

Ghi Python implementation/version, random.py raw SHA và key scheme trong runtime receipt. Cùng phiên bản/runtime và input phải tái tạo draws và episode. Chưa hứa bitwise cross-OS hoặc cross-version, vì gauss dùng cả thư viện toán.

## Kiểm chứng nhỏ trước actual domain episode

Đề nghị10–14 unittest methods mới, stdlib-only, được Root review source/pins trước một lượt cap30giây. Các case chính gồm các kiểm tra sau.

1. Spy trên RNG factory cục bộ xác nhận mỗi init event chỉ gọi gauss(0,1), mỗi response event chỉ gọi random. Không patch global profiler hoặc toàn bộ scientific runtime.
2. Trên supplied Gaussian z đã biết, initializer vẫn trả đúng US/UW/FW mean và scale; spy xác nhận wrapper không nhân sigma hai lần. Giữ tail/cap convention đã kiểm ở E1/E3.
3. Cùng seed/persona/replicate/node/local count cho cùng draw; đổi từng identity field đổi key. Thứ tự node không đổi kết quả keyed mapping. Không dùng assert mọi draw ngẫu nhiên khác nhau như một định lý chống collision.
4. Chuẩn bị một draws object rồi chạy hai branch theo cả hai thứ tự cho cùng từng kết quả của branch. Cùng concept-local count nhận cùng u, kể cả khi global step hoặc item thực chọn khác nhau.
5. So sánh seeded wrapper với lời gọi supplied core nhận chính profile/tape đã tạo, equality toàn trace/snapshot/metrics. Không viết một estimator thay thế làm control.
6. Caller global `random.getstate()` giữ nguyên qua prepare/run; profile và tape tuples bất biến; sai persona/key/horizon hoặc domain drift bị chặn trước interaction.
7. Một fixture nhỏ kiểm early stop không đổi dữ liệu draws của branch còn lại; generated tape counts và consumed feedback counts được phân biệt.

Không kiểm Gaussian bằng yêu cầu sample mean phải đẹp trên vài node. Kiểm chính xác API/công thức và lưu provenance trước; một ma trận phân phối lớn không cần thiết để nối episode.

## Packet bounded đầu tiên nếu Root chấp nhận source/tests

Đề xuất một logical learner US, root_seed42 và replicate_id `paper1-rng-smoke01`, domain28/84 đã pin. Chuẩn bị một profile và một tape h=500 dùng lại cho hai continuity branches B1 và GA. Giữ đủ hai graph/order từ actual domain loader. Đây là integration engineering với tối đa1000feedback,2controller và2world containers, không mở50seed matrix hoặc policy ablation.

Logical RNG events là28init keys và28×500response keys, chỉ tối đa500draws được tiêu thụ trong mỗi branch. Cần ghi cả số generated và consumed. Không nhân số learner lên theo tape entries hoặc hai branch. Metrics chỉ kiểm tính nhất quán/stop/coverage của từng episode, không dùng threshold lợi thế hoặc ép GA zero re-entry để accept.

Packet phải pin module/test mới, core/domain/primitives, năm input CSV, canonical PDF và exact runtime/source recipe. Root chọn output run ID mới và lưu profile/tape SHA, branch-spec identity, observable traces và oracle sidecars riêng. Chỉ summary/metadata cần vào evidence bundle nhỏ, không dump mọi unused uniform.

Đề nghị initial allocation stdlib-only whole35giây, owned tối đa30 với cleanup reserve3, worker26; RSS256MiB và free RAM512MiB là caps/floor đề xuất cần Root kiểm khả dụng trước dispatch, chưa là phép đo feasibility. Đây là allocation mới dành riêng cho code nhẹ, không sửa floor của CPU09/AKT. Không có Torch/NumPy/pandas, neural fit, dataset/Holdout, GPU/cloud hoặc baseline study. Root có thể chỉ chạy pure tests trước và giữ native packet ở trạng thái chưa dispatch.

Kết quả chấp nhận sẽ chứng minh RNG wrapper nối đúng supplied episode trong một phiên bản thực thi có provenance. B0, global/unlock policies và nghiên cứu50seeds vẫn cần batch/approval riêng. Không có implementation hoặc execution mới trong đề xuất này.
