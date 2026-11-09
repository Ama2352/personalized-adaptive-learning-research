# Learned19 — adversarial review source-only

Ngày09/11/2026. Verdict `SCOPED_STATIC_PASS_NO_P1_BLOCKER_FOUND`, với một hạn chế P2 về failure presentation. Không execute/import/compile/test/native/Git hoặc sửa các nguồn frozen. Đây không phải actual19PASS, quyền dispatch, full runtime equivalence hay RQ completion.

## Phạm vi cố định

- Worker c1f1c4cd11cb16e236c4acc09725ab9a4b523135ec8a80a23f62c63f42831e94.
- Outer829437c4fc8268cc1750bb5be2fadff13cd6a06628ac6281b9a114b1f6c8fecd.
- Plan26302c3b74649ae67340866e502c3853d373eb2f23b31f946bd567ce8a4ea7fd.
- Old36manifest a910612fdb0b3c728a715a3f5250eb9736016fdd9e691bc8fd29cdc89a146f57, worker973a1973da7982aac9a44b4112786915a127447ac57c6bce07f51c06e381f119.
- Paper2 reference a12edc72a00ad980799ec50ff26f0cb68f2529e3699e8a57e4f11295693c2cd1; notebook353f487a3d6ed3826f2546d03c0aa2ad2279cf5c4b7fe8e375f4cafb0408280f.

20source/43input SHA vẫn khớp lúc review. Đã đọc literal GAMKTPolicy constructor, MemoryState, selector initialization và persona generator từ notebook, chỉ JSON/source inspection. Constructor tạo theta1200, memory zeros và counters/deques; không scientific random draw. Persona dùng private default_rng; worker mới không gọi generator mà nhận saved base/U. Như vậy bỏ ba anchor/U generator calls không làm lệch global scientific RNG qua initializer này.

## Initial state và old36 là evidence loại nào

Old36 là actual accepted controlled simulator study với3seedblocks dùng lại, không dữ liệu mới độc lập. Old worker có assertion fingerprint(vars(policy)) bằng nhau giữa36worlds và alltheta1200 nhưng không lưu raw initial-policy hash. New worker lines263–278 ghi state/hash mới, treatmentgraph binding riêng; không được diễn giải new initial hash thành giá trị raw đã ghi trong old36.

Nguồn và runtime version được ghim, cùng literal deterministic constructor, old static namespace check lines196–198 và sentinel là cơ sở `SOURCE_RECONSTRUCTED_INITIAL_STATE`. Root có thể chấp nhận giả thiết này cho finite contrast. Một sentinel không chứng minh equivalence của mọi implementation/library/hardware hoặc mọi oldarm. Oldunloggedfield vẫn null. Không có kết luận rằng oldinitialstate đã được đối chiếu bytehash trực tiếp.

## Q18/K9 đo gì

Worker350–366 ghép oldexpert18Y với newlearned18Y theo exact(block,ability,λ), kiểm base/U IDs, tính Q=expert−learned và K=Q(.55)−Q(0). Công thức, chiều dấu và population đúng plan. Mỗi a có ba block, không18subjects hoặc2.280independent observations. Các contrasts mô tả graph-source intervention trong simulator/package đã chọn; graph đã fit từ TRAIN48 được giữ cố định, không biết trước là graph tốt/xấu hơn.

K là effect modification của graph-source contrast khi đổi world prerequisite penalty, không mechanical humanDiD, mediation, ability law hoặc calibrated edge-truth effect. Sau action divergence, cùng ordinal step không cùng query/y, nên không paired responseLL. Known high controls kiểm λinactive ở a1300; K1300=0 không hàm ý Q1300=0 hoặc graph trung tính ở λ0. Giữ negative/zero của mọi cell; không yêu cầu metric đẹp.

## Sentinel và ranh giới thông tin

Sentinel c26 trước learned worlds được kiểm exact120observable+oracle rows ở308–310 và full endpoint/state ở324–328; lệch bất kỳ phần nào STOP. Cell metadata c26→S01 là projection đã khai, không sửa số liệu. Sourceclock +6h/72h tại28/56/84/112 và predict-before-update giữ đúng oldworker. Oracle theta/prob/result chỉ evaluator/response world, không vào select/predict/update ngoài current observedy đúng source. Saved U float64/C-order và node-order/base checks trước world, không redraw/renormalize.

NativeGAM online update2280 là actual adaptive state work.0fits chỉ là0new graph/offline/neural solver fits. Learned31 nhận qua loader ECC313 và source/role/runtime/producer envelope cũ; score không đưa làm GAM weight, không P(edge true). G_env/G_controller và S1P1L0 không đổi khi G_estimator đổi. Nonedge initialization equality không ép full treatment graph fingerprints bằng nhau.

## Tài nguyên/output/failure

Source50/owned55cleanup3/whole60, prelaunch2GiB và family512MiB/free1536MiB giữ nguyên. Monitor0,1s và case/progress guards là cooperative/sample coverage, không OS hard RSS guarantee. Streaming Method24 hash có20s/160MiB innercap. Output cố định experiments/simulator, exclusive writes, giới hạn16MiB/max40nativefiles, actual raw row counts và Job0/returncode cần outer verify. Source được pin trước/sau; không thấy một đường native math ghi oldartifact hoặc đọc dataset/Holdout từ các API đã inspect. Audit không phải general filesystem sandbox cho caller đối kháng hoặc dependency tùy ý.

P2 cụ thể ở outer75–78. Status/RC check đứng trước đọc worker_run.json. Nếu child kết thúc nonzero với partial receipt đã ghi, outer sẽ giữ worker_result=null và nhãn UNKNOWN dù raw receipt thực còn trong scientific output. Đây là bảo thủ, không false0 và không thay đổi acceptance của completed19, nhưng làm thiếu chi tiết known partial counts ở top-level. Nên derivative sau nếu cần, đọc/preserve bounded raw worker receipt trước status assertion, vẫn reject và không promote counts thành acceptance. Không sửa nguồn frozen hoặc trì hoãn bằng claim có lỗi scientific math.

Khi không có child receipt thật, UNKNOWN≤durable reservations đúng hơn0. Parent dispatch global cap2280 không phải2280actual; cell reserve120 không phải120returns. Root phải đọc actual GO/owned/ledger nếu launch bị từ chối hoặc hardkill. Crash/partial/sentinel mismatch không được gộp19 như đã complete hay silently ghép old36.
