# RQ2 — cơ chế học thay đổi trong khi bài và đáp án phần lớn giữ nguyên

Ngày 09/11/2026. Phân tích thứ cấp của pilot CPU09 đã lưu, trên mười seed blocks21000–21009. Kết quả mới bổ sung exposure theo từng arm và điểm bắt đầu phân kỳ của query/nhãn. Các endpoint, seed, mô hình và công thức simulator giữ đúng nguồn thí nghiệm ngày07/11. Ba block controlled-ability ngày08/11 là một nghiên cứu riêng.

## Vì sao cần đọc lại từng quỹ đạo?

Paper2 đặt mô hình ước lượng kiến thức và bộ chọn bài trong một world có trạng thái kiến thức thật. Trong world này, thiếu kiến thức tiên quyết làm giảm lượng học ngay sau một lượt luyện. Câu trả lời chỉ là một quan sát nhị phân, còn kiến thức thật thay đổi liên tục. Vì thế, cùng bài và cùng đáp án quan sát được vẫn có thể đi kèm các lượng học khác nhau.

Pilot CPU09 đã đo sự tương tác giữa hai parent pathways của GAM và hệ số prerequisite learning penalty. Báo cáo trước có endpoint contrast và tỷ lệ gặp deficit gộp theo persona. Chỗ còn thiếu là biết deficit xuất hiện trong những arm/seed nào, và việc đổi world mechanism hay policy pathways đã làm hai lịch sử bài/đáp án tách nhau đến đâu. Phân tích này đọc lại trace để nối các đại lượng đó với đủ ba mươi contrast đã có. Phạm vi là chẩn đoán simulator có điều kiện, với population đã được xem trước khi đóng băng kế hoạch phân tích thứ cấp. [Nguồn pilot](../runs/cpu-factorial-20261107-01/README.md) và [phân tích exposure trước](rq2_conditions_evidence_20261108.md).

## Thiết kế và đơn vị

Mỗi seed có ba persona PG/PY/PYH. Trong mỗi persona, bốn world kết hợp hai policy settings và hai mức prerequisite penalty λ0/.55, mỗi world120lượt. Policy treatment bật parent signal và parent adaptation cùng nhau, control tắt cả hai, local adaptation tắt ở cả hai. World/controller giữ historical graph đầy đủ. Vì vậy đây là parent-pathway switch contrast. Phép đối chiếu estimator full–empty của các diagnostic RQ1 và thí nghiệm controlled ability ngày08 có định nghĩa khác.

Có120worlds và14.400event records đã lưu. Với mỗi seed/persona, hai phép so λ giữ policy cố định, hai phép so policy giữ λ cố định. Tổng cộng120 paired comparisons gồm60 mechanism pairs và60 policy pairs. Mỗi axis sử dụng lại cùng các world nguồn. Mười seed clusters là đơn vị ghép, các persona/arms/events lặp bên trong seed. Số seed families chưa từng được dùng bằng0.

Bốn arms trong mỗi seed/persona có cùng latent identity và step-indexed outcome/learning uniforms. Giữa persona trong cùng seed, U identity giống nhau nhưng latent vectors khác. Các persona mang khác biệt initialization và residual, nên chúng chưa tạo can thiệp chỉ thay scalar ability. CRN ở đây được ràng bởi source và recorded identities. Sau khi query hoặc nhãn đã tách, cùng chỉ số step vẫn có thể thuộc những lịch sử khác nhau.

World trả `prerequisite_deficit` từ true parent theta trước cập nhật theo mean clip((1150−theta_parent)/300,0,1). Đây là latent world information dành cho chẩn đoán sau chạy. GAM không nhận field này làm feature hoặc confidence. Root concepts có deficit0. λ0 bỏ tác dụng của deficit lên multiplier học, nhưng giá trị deficit vẫn có thể dương.

Outcome Y là mean28 final theta minus own base sau lịch120steps. Δλ=Y(policy-on,λ)−Y(policy-off,λ), còn I=Δ.55−Δ0. Đơn vị đều là điểm Elo net trung bình qua28concepts. Endpoint Y được lấy đúng artifact gốc. `learning_gain` từng event là gross immediate gain và chịu ảnh hưởng cap/decay, nên nó có ý nghĩa khác endpoint Y.

## 1. Mechanism switch hiếm khi làm đổi bài hoặc nhãn trong population này

| Persona | Mechanism pairs | Có query khác | Có nhãn khác | Policy pairs | Có query khác | Có nhãn khác |
|---|---:|---:|---:|---:|---:|---:|
|PG|20|0|0|20|20|16|
|PY|20|1|1|20|20|16|
|PYH|20|0|1|20|20|20|

“Có query khác” nghĩa là ít nhất một step có cặp concept/question khác nhau. “Có nhãn khác” nghĩa là ít nhất một đáp án y khác nhau. Mỗi ô đếm paired comparisons, mỗi persona có10seeds×2giá trị cố định của trục còn lại. Toàn bộ sixty mechanism pairs chỉ có hai pairs xuất hiện nhãn khác. Trong khi đó policy switch tạo query khác ở cả20/20pairs của từng persona. [Đủ120comparisons](../runs/rq2-cached-mechanism-diagnostic-20261109-01/paired_trajectories.json).

Hai mechanism pairs có observable divergence được giữ rõ định danh. PYH/seed21006/policy-off giữ nguyên query tuple ở cả120steps, nhưng có một nhãn khác, lần đầu tại step80. PY/seed21007/policy-on có nhãn khác lần đầu tại step67, query khác lần đầu tại step70, tổng31query differences và3label differences. Step dùng index0-based. Thứ tự này ghi nhận diễn tiến của hai world, chưa tách được vai trò nhân quả riêng của nhãn, trạng thái ước lượng và bộ chọn bài.

### Cầu nối từ world feedback đến quyết định của KT

Callsite factorial tại `scripts/research/run_approved_cpu_pilots.py` dòng69–84 tạo fresh policy cho từng arm. Trong mỗi step, policy chọn bài, tự tính P, world tương tác với cùng step-indexed uniforms, rồi policy.update chỉ nhận concept/question/difficulty/time, y và P của chính policy. λ được dùng để dựng world class tại dòng37 và environment tại dòng71. Các callsite chọn bài/cập nhật KT không truyền true theta, true deficit hoặc λ. Current runner SHA `55e8e3c74c8daa92d572c809353da5546fa435b55e18b8ab30fdcf46e8413e8e` giữ factorial AST giống exact historical source aea2ff…c157 theo hồ sơ nguồn đã đối chiếu.

Trong pinned notebook353f…, cell11 dòng6–13 chọn question bằng distance/seen/question_id, còn dòng45–81 chọn concept bằng các khóa score/chapter/visits/CID và cập nhật bookkeeping. Các bước này không lấy thêm RNG draws. Cell13 dòng37–46 khởi tạo GAM state cố định, dòng117–149 tính P và cập nhật từ own state, question feature, time và observed y. Pathway adapter chỉ thay context theo S/P/L đã cố định. Vì vậy, với cùng initial KT, features, clock và g, nguồn hỗ trợ điều kiện đủ rằng cùng observable query/y history giữ cùng diễn tiến KT/selector cho đến khi feedback khác. Đây là kiểm tra wiring theo source và dữ liệu ghép, chưa phải runtime tracer độc lập của toàn bộ internal state ở mỗi bước.

Trong hai pairs có y khác, PY ghi y divergence tại67 trước query divergence tại70. PYH ghi y divergence tại80 nhưng query tuple vẫn giữ tới cuối120steps. Các quan sát này phù hợp với việc λ đi đến KT thông qua observable feedback, và khác biệt feedback có thể xuất hiện hiếm dưới coupled uniforms trong horizon hiện tại. Việc thay chính policy pathways tạo query divergence ở toàn bộ60policy pairs. Các giới hạn về simulator, coupling và horizon vẫn cần giữ khi giải thích kết quả.

Số query/label changes thấp khi đổi λ không cho phép bỏ qua hiệu ứng latent learning. Công thức world nhân lượng học với `(1−λD)` trước cập nhật theta. Khi D>0, λ có thể đổi lượng học dù một uniform vẫn cho cùng y và controller vẫn chọn cùng câu tiếp theo. Ngưỡng nhị phân của y cùng tính rời rạc của lựa chọn có thể che các khác biệt liên tục. Phân tích hiện tại xác định mức ổn định của observables, còn các chênh lệch endpoint được giữ riêng trong I và Δ.

## 2. Bảng theo arm làm rõ điều mà pooled exposure che khuất

Mỗi hàng dưới gộp10seed blocks, đủ1.200events. Count đếm các event có true deficit>0, còn meanD lấy cả các event bằng0. Bảng đầy đủ theo120seed/persona/arm nằm trong [arm exposures](../runs/rq2-cached-mechanism-diagnostic-20261109-01/arm_exposures.json).

| Persona | Parent pathways | λ | Events D>0/1.200 | Mean true D |
|---|---|---:|---:|---:|
|PG|off|0|0|0|
|PG|off|.55|0|0|
|PG|on|0|0|0|
|PG|on|.55|0|0|
|PY|off|0|955|.242174460|
|PY|off|.55|955|.246382997|
|PY|on|0|959|.241605227|
|PY|on|.55|964|.244679075|
|PYH|off|0|602|.149301350|
|PYH|off|.55|602|.152835589|
|PYH|on|0|595|.151605458|
|PYH|on|.55|595|.154975424|

Chẳng hạn PY/policy-off có cùng955event deficit-positive ở cả hai λ nhưng meanD khác nhau. PYH cũng giữ cùng số event deficit-positive trong từng policy setting trong khi meanD thay đổi. Đếm exposure có/không đã bỏ qua độ lớn của continuous deficit. Các bảng theo seed/cell mới cho phép đặt thông tin này bên cạnh từng endpoint contrast, thay vì dùng một tỷ lệ pooled cho mọi seed.

Exposure và các bài đã luyện có thể thay theo quá trình tương tác. Vì vậy bảng này mô tả nơi mechanism được gặp trong quỹ đạo thực tế. Nó chưa nhận dạng một dose–response hoặc phần tác động được trung gian qua exposure. Phân tích giữ toàn bộ root events, zero-deficit events và các contrast âm.

## 3. Mechanism-null và graph-relative gain trả lời những câu hỏi khác nhau

| Persona | Mean Δλ0 | Mean Δλ.55 | Mean I | Seed I dương/âm/zero |
|---|---:|---:|---:|---:|
|PG|+.110853316|+.110853316|0|0/0/10|
|PY|+.017468639|+.051485897|+.034017258|7/3/0|
|PYH|+.324553209|+.378081797|+.053528587|7/3/0|

Các số này tái lập endpoint contrasts đã công bố trong CPU09. Điểm mới là chúng đã được ghép với exposure và divergence của đúng các arms/seed, giữ đủ30rows và bốn Y ở mỗi row. [Bảng ghép đủ30contrasts](../runs/rq2-cached-mechanism-diagnostic-20261109-01/joined_contrasts.json).

PG giữ D0 trong toàn bộ các arms và hai mechanism worlds khớp semantic trace/endpoint tại mỗi fixed policy. Do đó I0 là negative control có giải thích theo nguồn và cohort. Policy effect của PG vẫn có mean+.110853316 ở cả hai λ, và mọi policy pair đều thay query ở ít nhất một step. Gỡ tác dụng prerequisite penalty vì vậy vẫn để lại những đường qua policy pathways, challenge và lịch sử luyện. Kết quả thu hẹp cách giải thích graph-relative gain vào đúng intervention đang xét.

PY/PYH đều có ba seed với I âm bên cạnh bảy seed dương. Mean dương trong hai persona này cần được đọc cùng sự khác biệt giữa seed và initialization. Các báo cáo cũ đã chỉ ra profile ordering nhạy với leave-one-seed-out. Phân tích mới giữ lại các trường hợp đó, với mô tả điều kiện ở mức seed/cell, thay vì chọn các quỹ đạo thuận lợi cho graph.

## 4. Giới hạn và ý nghĩa cho RQ2

Kết quả bổ sung bằng chứng rằng thay đổi prerequisite learning mechanism có thể ít biểu hiện qua bài/nhãn được quan sát, trong khi continuous world state và endpoint contrast vẫn thay đổi. Nó cũng cho thấy graph-relative gain có thể xuất hiện ở điều kiện mechanism không hoạt động. Hai điều này giúp phân biệt learning equation, observable response và policy sequence khi diễn giải RQ2.

Đây là secondary exploratory analysis trên endpoints và seeds đã được xem. Báo cáo giữ mười reused clusters, toàn bộ ba persona và bốn arms, với new independent seed families0. Chưa có kiểm định significance, CI, đánh giá thực tiễn của độ lớn effect, causal mediation hoặc luật tổng quát về ability. PG/PY/PYH chưa cô lập scalar ability. Thí nghiệm controlled scalar ability36worlds ngày08 được dẫn riêng và giữ estimand/initialization khác. [Controlled ability](rq2_controlled_ability_prerequisite_results_20261108.md).

Các rates trong báo cáo này thuộc served closed-loop trajectories của CPU09. RQ1 fixed-stream chín chuỗi/preview dùng cùng query/y cache giữa estimator contrasts, nên có population và cơ chế ghép khác. Các tỷ lệ masking hoặc preview-change của RQ1 cần giữ tại thí nghiệm gốc. Các kết quả hiện tại tiếp tục là bằng chứng GAM/world simulator, còn fitted-model comparison và kết quả học tập theo các models trong đề cương vẫn cần được thực hiện.

## Bằng chứng thực thi và nguồn

Pure16 fixtures được Root chạy thành công, gồm known-answer sign/zero arithmetic, divergence đầu/cuối/không có, grid/identity/negative controls và bounded gzip/CRC. Native-cache01 bị từ chối trước GO vì default argparse HelpFormatter lazy-import shutil sau khi read allowlist đã đóng. Owned receipt còn có startup PermissionError/cleanup failure, dù Jobactive0. Không có inner analysis outputs của lượt01. Raw failure được giữ đầy đủ.

Revision02 preimport đúng stdlib shutil, đặt COLUMNS80/LINES24 chỉ trong child để source get_terminal_size lấy env branch, rồi khôi phục trong finally. Parser/test/contract giữ SHA của pure16. Outer/owned02 dùng namespace mới, còn INNER01 là lần đầu được tạo theo frozen contract. Native02 hoàn tất actual parser main với120arms/120pairs/30contrasts, input/source hashes khớp trước/sau, scope audit sạch và Job0/cleanup accepted.

| Phạm vi thời gian/nguồn | Giá trị đã ghi |
|---|---:|
|Pure16 stored whole / terminal observation|.889350000s / 1.3827869s|
|Native-cache01 stored outer / terminal observation|.696765700s / 1.5640956s|
|Native-cache02 parser body receipt|.316282500s|
|Native-cache02 owned helper gồm cleanup|.736867666s|
|Native-cache02 stored outer / printed / terminal observation|.968993600s / .9854834s / 1.6758054s|
|Native02 monitored family peak / minimum free RAM|93.372.416B / 5.332.639.744B|

Các ranh giới thời gian lồng nhau giữ riêng. Allocation mới có whole60s/owned57/worker54/cleanup3, family RSS1GiB và freeRAM2GiB. Monitor là quan sát/cooperative. Đợt phân tích này có0model calls và0world transitions mới. Root còn chạy deterministic synthesis từ ba output JSON đã kiểm SHA để tạo các bảng gộp trong báo cáo, source SHA `646b7f350fb270acc3613b1c021cd141df6be3b066e556dadea131d37f1bd170`.

Hồ sơ theo run được chuẩn bị tại [rq2-cached-mechanism-diagnostic-20261109-01](../runs/rq2-cached-mechanism-diagnostic-20261109-01/README.md). Closure được Root thực hiện riêng sau khi duyệt dry inventory. Gzip gốc, corpus và runtime dependencies được tham chiếu SHA. Các alias công khai sau closure gồm [synthesis.json](../runs/rq2-cached-mechanism-diagnostic-20261109-01/synthesis.json), [native02 final](../runs/rq2-cached-mechanism-diagnostic-20261109-01/native02_outer__final.json), [native01 failure](../runs/rq2-cached-mechanism-diagnostic-20261109-01/native01_outer__final.json) và [contract](../runs/rq2-cached-mechanism-diagnostic-20261109-01/rq2_cache_mechanism_contract01.json).

Native02 outer SHA `ad5170d4cd312b126b78f4fc96b01a4f1809962a7cee820010e2ab86a44d757c`. Synthesis JSON SHA `157b65c5ecc10c848eef4b054420356a61eedd860c824c17552ce5564f1e69db`. Bản báo cáo này diễn giải các artifact đã lưu, giữ riêng chẩn đoán cơ chế và những phần RQ2 còn mở.
