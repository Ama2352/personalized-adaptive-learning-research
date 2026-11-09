# GKT positive02 — bàn giao nguồn cho ROOT

Bốn nguồn đã đóng băng, chỉ chuẩn bị nguồn. Agent không chạy Python, AST, imports, tests, auth, NN hoặc Git.

| Nguồn dưới P | SHA-256 |
|---|---|
| check_gkt_selected_fit02.py | ecc9d3168b20e692a783ad55f7efdc746df6bd5d6d049da267e6be6fe4698a93 |
| run_gkt_selected_fit02.py | 010c3404bd558dca04ce8589f967a9487dea8bd5239db610c77e4b65b6e3adcb |
| materialize_gkt_selected_positive03.py | 4a0d9c391282104b37f2a6b23c13e2696bd04e6cc044b29157550a9897994698 |
| check_gkt_wrapper_restoration02.py | 2e49b0c024c46a1e458b7278b589f9ae3cc42ab129320df7170eea6e8d36b422 |

P là artifacts/akt/local-tests/akt-research-runner-20261108-01. Inventory gkt_native_positive_sources02.json SHA a25f688871571e9327728021e3b1d884d589932f7768cb28b3fd22f4a868ff45. Bốn bản gốc được inventory trước copy, đọc lại SHA sau copy tại gkt-native01-static-monitor-hold-before02/. Native01 chỉ bị giữ qua review tĩnh, chưa có actual GKT failure.

## Thay đổi vận hành

Ba helper và vòng lấy mẫu member trùng văn bản với check_a1_expert_engineering03.py a6fa2e3838d27e288ad1be8ecb33058ef3f7062c0258b4d8b3fb6c765038cc42. Handle có QUERY_LIMITED_INFORMATION và SYNCHRONIZE. Chỉ bỏ qua member đã có đúng PID, Wait0 và GetExitCodeProcess thành công trên chính handle đó. Member live vẫn kiểm Job, creation-time, RSS. PID/ctime mismatch, unknown wait, live permission errors đều reject. Kernel.token của helper gốc không đổi. Log monitor thêm phase và traceback10, tối đa32 ví dụ verified exit.

Proof ROOT đã chạy9 canary tại a1-resource-wait-guard-canaries02/result.json SHA608aa127dfd07ffbbee776cf94d1e4afa5305a0763f0620acecbf9469eb37b64. Precheck02 kiểm SHA proof/source, AST ba helper giống bản đã kiểm và projection env finally. Root cần chạy precheck02 trên worker02 để tạo receipt mới.

Nguyên nhân Win5 ban đầu chưa xác định. ROOT ghi nhận image query Win31 ở handle đã kết thúc trong probe, membership sau Wait0 thành công. Đây là sửa phòng vệ có nhánh fail-closed đã kiểm, chưa chứng minh nguồn Win5.

Mọi quota, recipe29, public source/corpus guards, fresh-best reload và NN observer giữ nguyên. Worker560/owned580/whole600/entry540/training300; worker và Job-family2GiB, free2GiB, admission4GiB. Không thêm workload NN.

## ROOT thực thi từng bước

ROOT AST bốn nguồn rồi chạy precheck stdlib trong5s. Output mới gkt-wrapper-restoration-precheck02.json.

    .venv/Scripts/python.exe P/check_gkt_wrapper_restoration02.py --worker-sha256 ecc9d3168b20e692a783ad55f7efdc746df6bd5d6d049da267e6be6fe4698a93

ROOT kiểm physical parent experiments/gkt, chỉ tạo parent đã review nếu vắng. Chạy materializer với dry02 thực, cùng Win03 process profile đã được review.

    .venv/Scripts/python.exe P/materialize_gkt_selected_positive03.py --materialize --self-sha256 4a0d9c391282104b37f2a6b23c13e2696bd04e6cc044b29157550a9897994698 --fit-worker-sha256 ecc9d3168b20e692a783ad55f7efdc746df6bd5d6d049da267e6be6fe4698a93 --fit-outer-sha256 010c3404bd558dca04ce8589f967a9487dea8bd5239db610c77e4b65b6e3adcb --dry-sha256 ff6ab7ca392e34b31b2053b9bd6b43c329aadca1b180c2a155eee36a8e81a590 --proposal-sha256 a8f8a041c98886c104ee92c5cf322c47ce38c173c23e1237f61be91dff5ead3d --packet-sha256 0f9b461c1f7d25833179a5620975001a86a3722dd290ddfddbd40e12fa98dcb4 --approval-reference ROOT_REVIEWED_GKT_SELECTED_ENGINEERING02

P trong command là viết tắt đường dẫn prep trên, Root thay bằng đường dẫn thật. Không phải runnable placeholder proof.

Kết quả là auth cùng scientific runID01 và request mới gkt_selected_fit02_request.ROOT.json. Auth/request chưa được agent tạo. Output materializer gkt-selected-materialization03. Dry02 giữ nguyên.

Sau Root kiểm actual auth/request và fresh RAM, gọi run_gkt_selected_fit02.py với mandatory --request-sha256 từ actual request mới, --restoration-precheck-sha256 từ actual precheck mới, worker/outer/materializer SHA trong bảng và cùng approval-reference. Hai SHA actual này chưa tồn tại nên không có giá trị giả thay thế.

Operational output gkt-selected-fit02/ và gkt-selected-fit02-owned/. Scientific output experiments/gkt/results/gkt-selected-engineering10x84-20261110-01. Không chạy song song NN, không retry tự động.

## Acceptance hữu hạn

Hai genuine model và hai Adam, tối đa50epoch/100steps/33600train targets, max151forward và151sequence,51tailqueries,100logical backward/clip,50saves/1restore. Với actual E và S đối chiếu 3E+1forward/sequence, E+1tail, 2EAdam và672Etrain targets,84(E+1)selection targets, Ssave/1restore và full84 unique prediction/truth keys. Criterion dừng GKT29 response-pooled binary64 log loss.

Actual dry02 chỉ là evidence metadata. Chưa có actual GKT selected fit, full matrix, refit/calibration, CUDA hoặc long-run/crash recovery proof từ bộ nguồn này.