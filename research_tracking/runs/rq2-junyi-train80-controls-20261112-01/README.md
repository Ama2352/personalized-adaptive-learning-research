# Đối chứng catalog khớp degree và support TRAIN80 outer4

## Trạng thái

Đã chuẩn bị generator tái dùng `rewire_matched_graph`, inputpack TRAIN80 và16synthetictests đạt. **Chưa dựng control nào trên graph Junyi thật**, chưa scan candidateedge, chưa chạy mô hình hoặc cloud. Recipe đang frozen cho review của nhánh chính, chưa được nhận làm protocol benchmark. Không thay catalogprimary976cạnh.

## Câu hỏi nghiên cứu và estimand

Để kiểm bẫy thứ tự Junyi, cần biết predictive difference giữa catalog và graphđối chứng có còn khi số cạnh, degree, topic/area và support huấn luyện được giữ như nhau. Generator này chỉ tạo sensitivitytopology. Nó không bảo đảm nullgraph có cùng learner-level/native-window exposure hoặc là mẫu đều từ mọi DAG. Những điều đó được kiểm bằng audit riêng trước benchmark, không suy từ constraint cấu trúc.

Đơn vị tạo graph là toàn bộ catalog835node/976edges. Đơn vị matching là jointpair của nhãn node ở hai đầu cạnh. Đơn vị exposure audit là edge–target và TRAINlearner, giữ tất cả target của cùng learner làm một cụm. Đơn vị so predictive metrics sau này là learner trên cùng targetpopulation, chưa thực hiện ở bundle này.

## Recipe đề xuất đã ghi trước dựng graph

- Seeds0/1/2 giữ cố định, mỗi seed yêu cầu10double-edge swaps, tương ứng20cạnh removed và20cạnh added, tổng40symmetricdifferenceentries. Không đổi seed hoặc hạ workload khi thiếu swap hợp lệ. Ghi unavailable/inconclusive và giữ nguyên failure.
- Giữ toàn nodes và nodecôlập, số cạnh, indegree/outdegree từng node, DAG và số cạnh của mọi jointtopic/area/supportpair. Dùng thuật toán swap đã có, không reimplement productiongraphcode. Mỗi originaledge chỉ dùng một lần, không đưa originaledge trở lại.
- Support là **số learner TRAIN80 phân biệt theo exercise**, lấy từ `train_support_students` của encoding717. Nó khác tần suất số lượt tương tác. Bins log10đềxuất là0/1–9/10–99/100–999/1000–9999/10000+. Trong835catalognodes có lần lượt118/17/142/311/226/21node. Bins có phân biệt ở quy mô fullTRAIN, thay bins0/1–2/3–5/6+ của prefixpilot cũ. Không tái dùng support hoặc bins outer0.
- Topic/area là metadata staticcatalog. Đã đối chiếu SHA catalog hiện tại với nguồn extraction cũ và đối chiếu từngnode.19node có literalN/A được chuẩn hóa thành chuỗi rỗng đúng cách extractor pandas.fillna lịch sử đã dùng. `preparation-attempt01.json` giữ guard ban đầu dừng do khác cách biểu diễn, catalogbytes không đổi.
- Không dùng correctness, selection/calibration/Holdout hoặc bất kỳ predictive metric nào để tạo, chọn hay đổi seeds/control. Inputpack ghim phaseidentity/encodingidentity/rolesSHA/cachemanifestSHA và các nguồn. Metadata topology chứa118unfittednodes vẫn được giữ, không silentlyprune.

## Exposure gate còn cần review

`recipe.json` ghi mục tiêu chẩn đoán trước khi biết candidateedgeexposure. Mỗi phía added/removed cần ít nhất10cạnh có parentprefix ở ít nhất20TRAINlearner. Uniontarget chịu changededgeexposure cần ít nhất1.000TRAINlearner. Đây là ngưỡng coverage đề xuất để tránh đối chứng hầu như không chạm dữ liệu, chưa là poweranalysis hay bảo đảm khả năng phát hiện predictive effect. Nhánh chính có thể sửa đề xuất **trước** realconstruction/audit và phải ghi lý do, không sửa sau khi xem metric để làm control được thông qua.

Cạnh mới chưa có trong fullcatalogCSV, nên `active_new_edge_counts` luônnull và `benchmark_eligible=false` sau construction. Chỉ scan nativeprefix riêng cho unioncatalog+addededges, dùng trainonlywindowcache và cùngmask như fullscan đã đóng, mới xác định được exposure. Removededges có thể tra fullcatalogCSV nhưng không dùng nó để đoán addededges. Giữ toàn bộ candidategraph của cả ba fixedseeds và mọi kết quả không đạt support, không lấy riêng graph có effect đẹp. Nếu điều kiện support không đạt, ghi `INCONCLUSIVE_EXPOSURE_TOO_LOW`, không kết luận graphneutral/equivalent và không tự chọn seedmới.

MatchingTRAINlearnerfrequency không bảo đảm matchingnativeprefixexposure. Sau audit cần báo cả số removed/addededges có support, edge–targetopportunities, edge–targetactive và affectedtargetunion/learnerunion, cùng attrition nếu dùng giao. Predictive comparison vẫn giữ commonloggedtargets và OOVcoverage, không lọc riêng mỗi graph để tạo quần thể thuận lợi.

## Đã cài và kiểm gì

`generator.py` nhận typedgraph, mapstatic, TRAINsupport, phasepins và recipe. Nó gọi thuật toán swap hiện có, kiểm lại degree/jointstrata/sốchangedentries, trả graphpendingaudit hoặc typedunavailable. Không đọc file, model hoặc dữ liệu tương tác bên trong hàm. Caller phải bind inputpack đã pin trước khi gọi thật. Input SHA trong output ghi nguồn phase/metadata/recipe, không tự xác nhận nguồn thật nếu caller cung cấp dữ liệu giả.

`test_generator.py` dùng toyDAG4nodes/2edges, không gọi generator trên catalog Junyi.16ca kiểm swap đúng, degree/strata, privateRNG/determinism, newedgeexposureunknown, infeasible không giảm workload, topic/supportconstraints, logbins/biên, invalidsupport, wrongphase/missingpin, foreignnode/seed/map và cyclicinput. `tests02.log` ghi16PASS trong0,007giây. `tests01.log` giữ15PASS của binsdraft ban đầu, `tests01-source-pins.json` ghi nó đã được thay sau khi Root yêu cầu xem histogramlog10. Hai lượt test không tạo mẫu nghiên cứu hoặc controlJunyi.

Chạy lại synthetic bằng `.venv\Scripts\python.exe -B -m unittest discover -s research_tracking/runs/rq2-junyi-train80-controls-20261112-01 -p test_generator.py -v` với `PYTHONPATH=src` ở process của lệnh. Không cài dependency hoặc importTorch. `preparation-proof.json` ghim source recipe và inputpack hiện hành. `manifest.json` giữ inventory bundle mở chờ Rootreview.

## Phần tiếp theo cần Root review

1. Nhận hoặc sửa recipe10swaps/logbins và coveragegate trước realconstruction.
2. Ghim lại generator/graph/catalog/staticmaps/encoding/roles/cachepins, dựng ba fixedseedcontrols với CPU/RAM/wallcap rõ. Lưu cả unavailable. Chưa có authorization chạy bước này trong batch hiện tại.
3. Nếu dựng được, review workload unionaddededges rồi cho phép scan label-free nativewindow riêng, kiểm cơ hội target/learner của changededges. Không gọi oldouter0controls là controlTRAIN80 hiện hành.
4. Chỉ sau khi graph/audit được đóng mới ghép predictive protocol. Claim dương/âm/inconclusive đều hợp lệ nếu các giới hạn thông tin và mẫu số được giữ.

## Order-only graph là đối chứng riêng

Một đồ thị chỉ học recency/co-exposure từ TRAIN có thể giúp kiểm catalog đang làm proxy cho practiceorder đến đâu. Nó cần recipecandidatepool hữu hạn, tie rule và orientation/DAG/edgebudget được freeze độc lập. Khớp số cạnh với catalog có thể cần lấy số cảhaiendpointfitted thay vì cắt âmthầm976cạnh. Nó không thuộc generatordegreepreserving ở đây và chưa được tạo hoặc dùng benchmark. Không gọi directedprecedence là prerequisite thật chỉ vì có predictive advantage.
