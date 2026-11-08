# Chia tiến trình kiểm AKT — 08/11/2026

Pipeline cần một lần kiểm toàn bộ phần mềm trên đúng nguồn hiện hành trước khi dùng kết quả đó cho training. Tuy nhiên, một số test kiểm nghiêm không được import Torch hoặc thư viện dữ liệu, trong khi test neural khác đã import chúng ngay khi collection. Chạy chung một Python process làm hai yêu cầu hợp lệ xung đột. Sửa này chia tiến trình, không bỏ test hoặc hạ điều kiện kiểm.

## Cách sửa

Inventory hiện có67test modules được chia3processes:1stdlib-only,6no-Torch,60còn lại. Kiểm union đầy đủ/mỗi module đúng một lần; ghép JUnit không trùng testcase; giữ cùng global deadline và source/lock identity xuyên các nhóm. Pointer hiện hành chỉ công bố sau tất cả nhóm đạt. Nếu quá hạn ngay sau công bố, khôi phục đúng bytes pointer cũ và ghi rejected cho report mới thuộc invocation đó; không sửa report lịch sử.

## Bằng chứng hiện có

76fixture cases thực sự PASS,0failure/error/skip,62,045502901 giây/240. Các child process, upstream verifier và full Gate trong fixture là stubs. Nguồn8files trước/sau khớp;228setup/call/teardown reports,76unique node IDs; không import Torch/NumPy/pandas/sklearn/SciPy, không Popen hoặc mở vùng dữ liệu thật bị cấm từtest; environment restored. Owned Job cleanup còn0process và đóng handles.

Hai lượt kiểm trước chỉ có52/57dấu chấm, không JUnit cuối, vẫn giữ UNKNOWN/REJECTED trong bundle cũ; không đổi thànhPASS. Một diagnostic riêng2nodes đã qua và một probe8files mất0,1153giây. Chúng không chứng minh nguyên nhân thời gian chậm trước. Allocation phần mềm240giây được ghi trước lượt76cases, không tăng cap training/fit. Không dùng Timer trong child; outer owned Job có giới hạn237giây gồm5giâycleanup, tổng240gồmfinalization.

## Chưa hoàn tất

Đây chưa phải full Gate đã chạy đủ67modules và chưa phát hành source-bound Gate mới. Cần admission RAM thực, actual full software suite trong3processes có globaldeadline≤600, source/lock trước=sau và ownedcleanup. Sau đó mới dùng Gate cho native runtime/resource probe. Không suy readiness CUDA hoặc fulltraining từ76fixtures.

[Bundle76checks/diagnostics](../runs/akt-gate-process-isolation-engineering-20261108-01/README.md); [hai lượt thiếu nghiệm thu trước](../runs/akt-gate-isolation-bounded-checks-20261108-01/README.md). Không Holdout, training nghiên cứu, GPU hoặc chi Modal.
