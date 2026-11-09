# GKT trainer04 — từ chối Adam second moment âm trước compute

Sửa đúng hai canonical files theo ROOT release. Không sửa legacy training.py, model, recipe hoặc harness. Before snapshots có SHA copy bằng source, inventory `gkt-negative-second-moment-before04/inventory.json` SHA `bef39eb60efa1af89f07a47fc40041e2141a0e0630948cd6104839db84ffa7ac`.

| File | Trước | Sau |
|---|---|---|
| src/knowledge_tracing/gkt/research_training.py | a9a145d1930544b2c9a961267c5e35b4bdd4e9bcd4dde8ae1de979dcd583997e | 305fccf1038f41751a1137444cb2be469baf6f15090e27dc1595334ce3cb19cc |
| tests/gkt/test_research_training.py | e3446e780713f5acb3ec2a6dfb03ab236b107911338868f2a50806e2f52aba4c | c039444b9dc0650047a2377bc1fd6fbdcb23d1b880f2af7c0922d62d7cf1385f |

Owned `_optimizer` bổ sung second moment exp_avg_sq≥0 sau genuine legacy finite/geometry/ownership checks và scalarFP32 check. Không đổi optimizer equations, loss, hyperparameters hoặc state khác. Native ordinary Adam dùng sqrt(exp_avg_sq), nên finite negative tensor phải reject trước forward/backward/update thay vì chờ hậu kiểm phát hiện NaN parameters.

Subcase nằm trong existing preflight test. Tạo finiteFP32 scalar step và finite negative moment, yêu cầu ValueError trước model/backward/Adam, model/BN/caller RNG và tất cả supplied state tensors giữ nguyên. Finally xóa riêng malformed fixture state. Giữ8physical functions,8model/6Adam constructors,10sequence/60predict/48observe,4backward/clip/Adam,64actual optimized target exposures nếu bộ được chạy. Thêm đúng1train API preflight attempt/ValueError, vì vậy expected attempts19/value_errors12 thay18/11. Không tăng NN-body caps.

Đã chạy đúng `.venv/Scripts/python.exe -I -S` với stdlib ast.parse hai files,0Torch/NumPy imports. Actual parse0.016593500040471554s, tool shell wall1.2497545s. Receipt `gkt-negative-second-moment-before04/ast-after.json` ghi hashes,2AST parses và8test definitions. Cap5s trong receipt là kiểm elapsed của phần AST, không hard process quota. Chưa chạy tests hoặc native/model/RAM workload.

Harness trainer01 packet5936331b… hiện có đúng2stale source pins ở bảng trên; worker1c091…/outercde44… còn nguyên byte và expected train-attempt/value-error caps cũng cần ROOT hoặc owner refresh sau review. Không được dispatch packet01 như current. Model02/test03 vẫn4b866ca…/5255fcaf…, legacy training6def666d… không đổi, nên không tự gán stale cho model11 từ patch này. Không Git hoặc promotion hiện hành.
