# Kiểm ranh giới kết quả reference calibration —08/11/2026

Đây là sửa lỗi hợp đồng đầu ra local với fixture quan sát tổng hợp, không phải kết quả RQ hoặc huấn luyện NN. Chỉ sửa `src/knowledge_tracing/response_calibration.py` và `tests/shared_kt/test_response_calibration.py`. Các bundle lịch sử, controller, bridge và protocol21 giữ nguyên.

## Lỗi và phạm vi sửa

`score_reference_bank` trước đây chấp nhận session bất kỳ và giả định mỗi query có một kết quả. Khi một `probe_many` bị override trả83 thay vì84 hàng, `zip` cắt ngắn nhưng concept cuối vẫn được ghi `supported_items=3`; tổng hợp có thể báo đủ28concept. `OnlineSession.probe_many` nguyên bản đã kiểm ranh giới này; lớp override hoặc duck-typed session có thể bỏ qua nó.

Bản sửa yêu cầu `isinstance(session, OnlineSession)`, số kết quả đúng bằng số query, mỗi hàng là `OnlineScore` và có `global_rank` khớp history trước probe. Các kiểm tra diễn ra trước tổng hợp. Giữ nguyên84 actual reference items,28concept, trọng số1/3, scalarT, mẫu số support, xử lý null và semantics mean calibrated response correctness. Không đổi thuật toán/recipe thành latent mastery.

Regression dùng **actual OnlineSession** với fake backend hợp lệ, chỉ override `probe_many` để thiếu hàng, trả hàng sai kiểu hoặc sai rank. Một bẫy đặt ở `_sigmoid` chứng minh không được bắt đầu tổng hợp. Kiểm thứ tư dùng proxy duck-typed đầy đủ để chứng minh bắt buộc OnlineSession.

## Bằng chứng thực chạy

| Lượt | Nguồn | Kết quả JUnit | Thời gian controller |
|---|---|---|---|
| `trial01-red` | nguồn cũ134277…; test mới |4FAIL,0errors/skips |0.978534500s |
| `trial02-green` | nguồn mớic78496…; test giữ nguyên |67PASS,0fail/errors/skips |1.003942000s |

Lượt GREEN gồm43cases calibration và24cases controller, đếm từ `testcase.classname` trong XML (số31+36 từng nhắn là diễn giải sai, đã sửa trước đóng bundle; raw XML không thay đổi). Tổng thời gian hai lượt1.982476500s≤30s; không reset ngân sách, không lượt thứ ba. Cả hai lượt có snapshot nguồn/input và SHA trước/sau; `final-verification.json` đối chiếu XML và bytes snapshot. Log giữ cảnh báo pytest không ghi được root `.pytest_cache` do quyền Windows; không dùng cảnh báo đó để đổi verdict.

Lệnh thực tế:

```powershell
.venv\Scripts\python.exe artifacts/akt/local-tests/response-calibration-boundary-20261108-01/run_boundary.py trial01-red tests/shared_kt/test_response_calibration.py::test_reference_probe_rejects_invalid_rows_before_aggregation tests/shared_kt/test_response_calibration.py::test_reference_probe_requires_online_session
.venv\Scripts\python.exe artifacts/akt/local-tests/response-calibration-boundary-20261108-01/run_boundary.py trial02-green tests/shared_kt/test_response_calibration.py tests/shared_kt/test_reference_controller.py
```

Nguồn trước: `134277e291a768913576c83c593d40419597134fc6f7dd443ee5dd77b414e0aa`; nguồn sau: `c7849654eff35862e61602a4f95e401ed88b9070a77832e05d6a7173e72ebacb`. Test trước: `235c5381458521f27e5e406a11a52a282ebd27e5e78d22a9bb185590652af1aa`; test sau: `dd5d607e6fe280d7565d3675f976ed7127b53079216f19c6b0e5796d90ccd757`. Controller và các input liên quan có SHA đầy đủ trong inventory.

## Giới hạn và tích hợp

0NN,0optimizer,0remote, không đọc realdata/Holdout, không chạy Gate tổng thể. Scalar calibration fit trên label fixture tổng hợp vẫn là kiểm thử thuật toán, không bằng chứng calibrated model thực tế. Guard không chứng minh predictor đã train/refit đúng manifest, seed families hay không từng nhìn label; caller vẫn phải nối pipeline role/selection/refit/calibration đúng protocol21 và giữ snapshot predictor frozen.

Source identity của calibration bao gồm SHA file implementation nên các calibration payload cũ phải bị coi stale khi dùng nguồn mới; không sửa payload hoặc bundle cũ để khớp nguồn mới. Bundle mới `research_tracking/runs/response-calibration-boundary-20261108-01` giữ RED/GREEN, snapshots và copy inventory có SHA trước/sau; parent quản lý Git và chỉ mục. Manifest `completed` chỉ mô tả đóng gói thành công, không biến RED thành PASS.
