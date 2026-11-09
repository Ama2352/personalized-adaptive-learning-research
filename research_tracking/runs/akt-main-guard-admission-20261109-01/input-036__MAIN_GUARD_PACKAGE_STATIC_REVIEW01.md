# Review tĩnh độc lập package Main A0 guard

## Kết luận và phạm vi

Scoped PASS cho bước chuẩn bị metadata trên cây thư mục hiện tại. Chưa thấy lỗi xác định về constructor, số lượng, identity hoặc roundtrip có thể chặn dry proposal. Review chỉ đọc source và metadata đường dẫn, không import module, chạy Python/test, gọi Git, mở oracle hoặc tạo package. Chưa có bằng chứng actual prepare, materialize hay guard admission từ review này.

Ba input được hash lại trước và sau review, giữ nguyên bytes.

| Input | SHA-256 |
|---|---|
| prepare_main_selected_guard_package01.py | f1ca0b7f04f021e0e8a57f5c43ca806e1cd6aa94e2c127858ef076a51934d7fb |
| run_prepare_main_selected_guard_package01.py | f49b3741c652726aaf45636694f497231612d0d4a9aedee6d31c34793b4f1235 |
| MAIN_GUARD_PACKAGE_SOURCE_CONTRACT01.md | dc867f35e7ccf2b5a7f23732362a09ed3b843ac7c2e48614b26212b5ec119b4b |

## Đối chiếu có ý nghĩa

- Builder dòng 122–146 dùng đúng field order của GraphTrain80Binding, MainSelectionContext, MainSelectedStageSpec, MainGraphInput và MainSelectedExecutionSpec. Raw train JSONL hash và audited semantic shard hash được đặt đúng vai trò. Cách dựng A0 condition khớp research_main_execution._actual_condition. A0 internal empty condition khác external estimator condition `None` theo API hiện hành.
- Budget 48/6/6 learners và 10.080/1.260/1.260 events khớp public corpus và ResearchResourceBudget. CorpusReadLimits cho phép tối đa 48 learners mỗi role, 210 events mỗi learner, 12.600 events toàn bộ. Reference completeness được kiểm lại. Reader được phép audit ba public roles, còn bước này không fit hoặc chọn epoch bằng selection/calibration.
- Stage source identity được tính từ map177 trước khi thêm tài liệu và prep source pins vào request. `_metadata` dùng genuine preflight/require_gate2_evidence và public metadata audit. Giá trị identity không đưa live clock, live RAM hoặc owned PID vào payload. Runtime RAM trong identity là nội dung report đã hash, không phải phép đo mới. Khi source/data/runtime/index/config giữ nguyên, dry proposal và identity của actual authorization có thể so canonical chính xác.
- Config JSON đi qua canonical/asdict rồi public load_config, với Path và optimizer tuple được khôi phục theo loader. Request main_parameters bỏ riêng native_config, đúng consumer check_main_selected_guard01.request. Các typed caps và requested phases khớp `_auth`.
- Dry và materialize là hai owned operation độc lập. Materialize tái audit và so toàn bộ wrapped proposal trước ba exclusive writes. Ghi dở được giữ lại khi lỗi. Outer chỉ chấp nhận owned cleanup/Job0, worker metadata status, actual Git10, nguồn không đổi, không denied attempts và tài nguyên quan sát trong giới hạn. Không gọi guard factory hoặc runner từ builder.
- Worker chặn Torch/pandas/solver/teacher/selected-runner imports và chỉ cho exact public10 trong corpus. NumPy là dependency dữ liệu hợp lệ của shared contracts. Không có model constructor hoặc fit entrypoint trong đường chạy được review. Các số zero trong receipt là phạm vi source/audit, chưa phải quan sát của một lần chạy mới.

## Hai điểm cần giữ rõ

1. Cùng một `approval_reference` phải được dùng cho dry, materialize và actual guard consumer. Trường này nằm trong wrapped proposal, authorization và request. Đổi reference theo từng mode làm dry equality hoặc guard request equality từ chối đúng thiết kế. Review riêng cho materialize đi qua `--review-reference`. Câu “operation reference riêng” trong contract không nên được hiểu là cho phép đổi trường approval đã đóng băng.
2. Có lỗ hổng fail-closed đường dẫn mức P2 tiềm ẩn ở `emit` dòng 78–82 và materialize dòng 269–271. `open('xb')` bảo vệ overwrite của leaf nhưng theo parent alias. `parent.is_dir()` không từ chối junction/symlink. Vì vậy một parent aliased có thể nhận file mới trước khi posthash `sha()` từ chối. Tại thời điểm review, configs, authorizations và P đều là Directory bình thường, không có LinkType/Target, nên đây không phải blocker quan sát trên current tree. Nếu yêu cầu materialization fail-closed khi gặp alias, kiểm physical/no-symlink/no-junction mọi component của output parent trước mọi ghi là chỉnh sửa tối thiểu. Review không tự sửa source.

## Giới hạn

Chưa đo feasibility của Git10 cộng public reader trong worker50s hoặc actual guard trong wall45s. Caps 1 step/1 optimized target/1 training second chỉ giới hạn admission-only envelope. Không được suy thành khả năng hoàn thành selected fit 20 epochs, main matrix, refit hoặc calibration. Parent launcher phải tạo đúng reviewed Win03 child profile, chỉ loại GH_PAGER/GIT_PAGER đã được review, và giữ parent environment. Review này không tự cấp execution authority.
