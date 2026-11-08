# Microbenchmark observer — kết quả trên state giả, không là tốc độ GAM

Đây là bằng chứng vận hành để chọn cách giảm overhead của trace θ/pi. **Không chạy NumPy/Pandas/GAM, không đọc dữ liệu/cache/oracle, không teacher/RNG nghiên cứu hay optimizer.** Batch native trước vẫn dừng ở56.3709122/60s; benchmark dùng allocation riêng≤5s và không cấp quyền retry native.

ROOT quan sát terminal accepted1.2128429s; `final.json` ghi1.177621300s trước receipt, worker ghi0.709127800s trước receipt. Ba đồng hồ có phạm vi khác nhau. Ownedreceipt đã accepted cleanup/Job0 và profiler được restore.

## Kết quả thực đo

Fixture cố định28concept states. Nguồn `MemoryState` cell13 dùng memory float32; loader có28nodes+3chapters+7features=38values, tức152B/concept, recent_outcomesmax8 và recent_conceptsmax3. Fixture dùng bytes/ISO/ns giả lập; không chứa NumPyarray hay PandasTimestamp thật.

| So sánh trên cùng fixture | Cách cũ | Cách đối chiếu | Tỷ số thời gian cũ/đối chiếu |
|---|---:|---:|---:|
|64vòng×4full-state representations|256JSON/SHA:0.132620200s|256immutable byte/tupleviews:0.104554500s|1.2684313|
|Cùng4000dummybranch/8000dummyleaf calls|Globalprofile:0.044765100s|Directledger:0.004988600s|8.9734795|

Dummychecksum đều16008000; attempts=returns=4000branch/8000leaf. Globalcallback nhận48321events, directledger không cài profiler. Equal-state checks, signedzero và19singlefield mutations đều đạt: cả JSON/SHA và view nhận ra thay đổi. Đây là19fixture checks, không19researchsamples.

Tỷ số8.97 **không có nghĩa GAM sẽ nhanh9lần**;1.268 cũng không chứng minh JSON là nguyên nhân duy nhất của timeout. Hai arm chạy fixedorder, không counterbalance/CI; byteview dùng memorybytes đã materialize nên không đo chi phí `np.ndarray.tobytes`, pd.Timestamp hoặc actualnative schema verification. Native model/selector/graphsummary/I/O không thuộc workload này. Không suy runtime của2160trace hoặc tính chi phíGPU từ bảng trên.

Nguồn/raw được bind bởi plan/source/schema SHA; result giữ đầy đủ19mutation cases, counts và ratios. Đóng gói sau ROOT review chỉ nghiệm thu tính toàn vẹn của benchmark vận hành này, không trả lời RQ1 hay chứng nhận một observer native thay thế.

## Đề xuất revision nhỏ nhất — source review trước, chưa implement/native

Ưu tiên callback, không tự cho rằng đổi4JSON sang views sẽ đủ. Revision đầu nên giữ nguyên source native, điều kiệnall2160legacy/fullpreview exact và18initial/final C13fingerprints, cùng2160updates/6480predict. Không bỏ θ/pi/ref observables hoặc tạo subset. Không mở ngân sách60cũ.

**Một early-return trên mọi code-ID không khớp là chưa an toàn:** guard cũ xét RNG namespace chính trên những unmatchedframes. Không được bỏ dòng đó rồi vẫn ghi “guard RNG không đổi”. Safe nhỏ nhất hiện tại là:

1. Tách fastpath nativecodes và forbidden-teacher codes trước; chỉ nativecodes đã bind exactnamespace/source mới được bỏ việc phân loại module lại. `return`events không cần RNG-module inspection nhưng vẫn đếm native returns. Unknown `call`/`c_call` giữ guard cũ. Có thể cache phép phân loại theo **giá trị module name hiện tại**, nhưng vẫn đọc currentbinding; không cachecode→safe vô điều kiện vì cùngcode có thể chạy với globals khác. Việc này chưa loại hết globalprofile overhead, phải đo lại trên fixture trước khi kỳ vọng ích lợi.
2. Nếu muốn bỏ globalprofiling để dùng directmethod wrappers: counters phải gọi đúng tên **direct calls**, không actualallnativecalls. Các S/M/R calls bên trong native selector không tự được wrappers composition nhìn thấy. Đồng thời cần một guardreplacement riêng được ROOT review cho teacher/RNG reachability; chưa chấp nhận chuyển sang sourceassertion một cách im lặng hoặc thay namespace NumPy/nativeclasses. Đây là phương án rộng hơn, chưa tự chọn từ benchmark.
3. Byteview chỉ triển khai sau schema certificate thật: exact `vars`/dataclass fields của MemoryState và policy/selector, unknownfields failclosed; actualNumPy dtype/shape/bytes và NumPyscalar/PandasTimestamp/Counter/deque mapping. Schema hiện tại chỉ map10source fields với fake fixture, **nativecoverage=false**. Giữ canonicalC13fingerprints ở18initial/final; nếu đổi serializer per-event phải versionnaming rõ, không gọi viewhash mới là C13hash cũ.
4. Persist realmetadata receipt ngay khi phase đóng và durablecounter progress theo trajectory, tránh hardkill làm mất terminalmetadata như native02. Không điền hồi tố metadata/counters của batch cũ.

Một source-only revision đề xuất tiếp theo cần nêu chính xác phạm vi dynamic guard/counters, sourcebindings và tổngwork finite trước khi ROOT duyệt bất kỳ test/nativebatch mới. Kết quả benchmark này không tự authorize run hoặc chứng minh equivalence native. Failure report và gói63 trước giữ nguyên.
