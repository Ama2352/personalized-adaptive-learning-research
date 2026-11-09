# Admission guard Main A0 trên corpus simulator ngày09/11/2026

## Kết quả đã quan sát

Ba operation local CPU đã được ROOT chạy và chấp nhận. Bước thứ ba gọi factory guard thật `require_main_selected_authorization` rồi tái xác nhận identity. Đây là bằng chứng admission của envelope Main A0 hữu hạn. Selected fit chưa chạy.

| Operation | Trạng thái outer | Thời gian outer lưu trong receipt | Git provenance | Peak RSS worker | RAM khả dụng nhỏ nhất |
|---|---|---:|---:|---:|---:|
| Chuẩn bị dry proposal | ACCEPTED_METADATA_PACKAGE_ONLY | 6,0798704000s | 10 | 77.668.352B | 4.365.664.256B |
| Materialize config/auth/request | ACCEPTED_METADATA_PACKAGE_ONLY | 5,7246374000s | 10 | 77.377.536B | 4.146.929.664B |
| Actual admission guard | ACCEPTED_ACTUAL_MAIN_GUARD_ONLY | 10,9232783000s trước ghi receipt | 20 | 82.972.672B | 4.372.598.784B |

Mỗi operation có budget whole60s, worker50s và owned cleanup3s. Profile launcher bao ngoài ghi thời gian riêng, không cộng hoặc thay các thời gian outer trên. Các owned receipts đều có returncode0, actual worker trong Job trước GO, cleanup thành công, Job còn0 process và handle Popen đóng. Các worker không ghi nhận denied attempts hoặc lỗi monitor. Các phép đo tài nguyên là quan sát hợp tác theo samples.

## Vì sao cần ba bước

Dry proposal được tạo bằng public typed contracts và genuine `_metadata`, có runtime schema2, Gate05, lock, nguồn hiện hành và public corpus được kiểm thật. ROOT đọc exact dry SHA trước khi cho phép materialize. Materialize dựng lại metadata rồi so toàn bộ wrapped proposal, ghi exclusive ba file mới và kiểm bytes sau ghi. Actual guard đọc những file đã materialize, gọi validator thật và revalidate, nên có hai vòng provenance tương ứng20Git commands.

Ba bước giữ cùng approval reference `ROOT_MAIN_A0_GUARD_PACKAGE_REVIEW01`. Review riêng cho materialize dùng review-reference khác mà không đổi identity. Dry file có SHA `7ff29a16c0e0a6573032f1eaec69f40956ca7f7bf9cc9497c00b68d423a2dcfd`.

| Artifact được tạo | SHA-256 |
|---|---|
| Native config Main A0 guard-only | ba0aee4990597c218a2d31c5d2e941cc26e335825acf79d01e754d4faed35646 |
| Authorization cùng envelope | 212b78911bae2228e984eabe0ec292bd4d4b52ad748f834c6ed53b6177703f03 |
| Actual guard request | ef07d3430baa81d45d6eda2354c5ff03721ff97bd73093c5fe2115626797e50f |
| Actual guard outer receipt | 5a0a0b7e8d03f2f9fd3b5d123fea86f7071f3d4a5aa9069baeee6822ce18ff2d |

Independent static review đã đối chiếu GraphTrain80Binding, A0 empty condition, context/spec, config roundtrip và deterministic identity. Review chỉ ra parent-alias gap tiềm ẩn của writer. ROOT ghi nhận đã kiểm physical ancestors của configs/authorizations/prep và các output còn absent trước materialize trong toolg2:3402, đồng thời giữ yêu cầu này trong exact-dry review. Tool006417 là kiểm bytes sau metadata, không phải precheck. Sau actual guard, ROOT chạy kiểm độc lập và lưu `main_guard_parent_postcheck01.json`, SHA `b7347f991815e576a5753d56ac058d98c671f6e3d7a71a404fbd94d65bc7dbdd`, cùng source recipe. Receipt mới có scope POST_MATERIALIZATION_AND_GUARD. Đây là kiểm tra những đường dẫn thực dùng của lần chạy, chưa chứng minh writer tự từ chối mọi junction/symlink hoặc race. Bundle giữ postcheck thật và reference đến observation precheck của ROOT, không dựng raw tool log thay thế.

## Dữ liệu và ranh giới khoa học

Guard audit corpus Grade10 simulator canonical với48train/6selection/6calibration learners và10.080/1.260/1.260events. Reference bank đầy đủ84items/28concepts. Public reader được phép kiểm ba roles theo Protocol22, còn operation này không tối ưu weights, chọn epoch, fit temperature, sinh teacher response hoặc đọc oracle/final. Main stage giữ A0 graph disabled. Identity của empty implementation condition được kiểm riêng đúng API.

Config giữ seed42, context100/target100, batch4, dropout0,05,20epochs và patience3. Resource envelope cho guard là tối đa1optimizer step,1optimized target,1training second,45s main wall, RSS1GiB và free2GiB. Actual worker/admission ghi0model,0optimizer,0teacher calls, `run_main_selected_candidate_called=false`, `actual_selected_fit=false`. Envelope này không đủ cho một minibatch đầy đủ của corpus. Actual admission không chứng minh selected training, checkpoint, raw-best selection export, system selector, refit90 hoặc calibration đã hoàn thành.

## Runtime, môi trường và lưu bằng chứng

Các operation sử dụng actual schema2 runtime SHA `3fdddca8d9a39cf80e597cb6dd02701a3c619d64fc0f7ddadb1b6fb885ecd20b` và explicit Gate05 index SHA `e8162f6efce3ca0a443f6c40f69308b06b610e95d5a02504ba146e92b6f87366`. Gate05 có177sources/81modules/1.748physical testcases. Global current pointer vẫn mang SHA `9e768aadcf084482a2eeb9be814fc399100dd1a507eaa89afbbae87100365cd6`. Các artifact này được tham chiếu SHA, không chạy Gate/runtime lại trong admission.

ROOT profile launcher dựng exact Win03 environment cho child, chỉ loại hai biến hiển thị GH_PAGER/GIT_PAGER đã được review. Ba process Git configs là fsmonitor=false, safe.directory đúng physical upstream và autocrlf=true. Parent environment giữ nguyên theo từng profile receipt. Không có thay đổi global Git hoặc dependency installation. Nhận định này bao gồm việc setup child environment tường minh.

Bundle `akt-main-guard-admission-20261109-01` giữ raw receipts/logs của ba operation và ba profile launchers, dry/config/auth/request, source controllers, reviews và inventory SHA trước/sau copy. Corpus10files, source177, native Gate/log/JUnit, runtime và dependencies chỉ là references. ROOT phải review dry inventory rồi mới đóng bundle. Report không cấp quyền fit, CUDA/cloud, fullCV hoặc Holdout.
