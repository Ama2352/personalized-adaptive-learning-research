# SAKT research epoch/prediction — engineering09/11/2026

Đóng bằng chứng hai lượt Windows CPU trên cùng22case IDs:01 **19PASS/3FAIL**, verdict REJECTED;02 **22PASS/0failure/error/skip**, verdict ACCEPTED engineering. Không đổi assertion/production/test giữa01 và02. Folder làm việc20261108 giữ tên lịch sử dù bundle đóng09/11. Không chạy lại tests/model khi archive.

## Source và phạm vi

Hai module mới cung cấp một optimizer epoch và raw prediction trên SAKTResearchView đã kiểm roles. Config/model/optimizer/budget do caller truyền rõ, không numerical scientific defaults. Labels chỉ vào loss/truth sidecar; selection/calibration không được optimize. Có exact observable key/query/role population, truth join sau forwards, terminal masks/local positions, causal/peer positive controls, mode/RNG restoration, ownership/identity guards và complete/partial/failed ledgers. Finite logits nhưng BCEsum overflow phải fail trước backward/step; source trước static finite/population review được giữ, chưa có testRED của bản đó.

Reuse dữ liệu roles và math helpers; không gọi trainer toy hoặc sửa256targets/32steps/engineering checkpoint guards. Tests dùng typed observables tự dựng in-memory, không đọc canonical corpus/oracle/final/Holdout hoặc gọi teacher. Metadata/source seals là cooperative consistency, không độc lập xác nhận actual data origin. Partial iterator/budget không thành complete epoch; failure sau optimizer mutation không được gọi rollback.

## Vì sao giữ failure01?

01 đặt observer trên Tensor.backward và nhầm dispatch entries với logical backward. Trong explicit torch.device(cpu), Torch_tensor.py638–649 đi qua handle_torch_function/__torch_function__ rồi tái nhập patchedTensor.backward. Cap5observer chặn backward tiếp theo: raw started8/bodyreturned4, SGD bodies2. Ba failures là actual và giữ nguyên log/XML/ROOT review; không gọi chúng là production model bug hoặc relabelPASS. Raw key backwards ở01 không thể cộng như logical calls của02.

02 dùng public torch.autograd.backward để đếm **5logical backwards**; observer Tensor.backward riêng ghi **10raw dispatch entries**. Actual inventory02:16SAKT constructors,11forwards,5logical backwards,10raw entries,5SGD bodies và15SGD constructors; cả started/bodyreturned khớp. Một fixture cố ý để instance step wrapper raise sau underlying SGD body đã đổi weights, nhằm chứng minh failed/possibly-updated ledger; vì thế5internal SGD body returns không phủ nhận failure-wrapper test. Cộng hai lượt là7SGD bodies toy, không7research fits. Journal02 ghi counters theo test; không nới logical5/step5 và không auto retry.

## Runtime và budget đã quan sát

Stored outer receipts:01 17.748528700s/80;02 13.753853300s/80; mỗi allocation độc lập80s, tổng ceiling160s. Đây là boundaries trong final.json; không thay bằng thời gian terminal/GUI hoặc pytest. Pytest XML lần lượt 9.306s và 8.835s. Child timer70s; owned ceiling77s, cleanup3s, finalization reserve3s từ original outer clock, không reset sau setup.

Monitor vòngwait0,1s và Windows peak working-set/RSS observations:01 peak312983552B/minimum free6123180032B/155samples;02 peak295948288B/minimum free5260562432B/114samples. Admission free1GiB, observed peak cap512MiB; cooperative polling/late rejection không là hard OS RAM quota. FullGate floor4GiB giữ nguyên.

Actual .venv CPython3.13.5, Torch2.7.1+cpu/NumPy2.5.4; origins/prefix trong raw receipts. Intra-op2; interop12 ghi nhận, không claim toàn process chỉ2threads. Actual platform.uname bootstrap chạy đúng fixed systemcmd /c "ver" trong ownedJob, phase đóng trước test processes deny; không fake OS/cache. Hai lượt đều mode/method/env restored, monitor stopped, Jobactive0/cleanupaccepted/Popen handleclosed. 0CUDA initialization/execution; đây không phải toàn bộ dependency syscall attestation.

## Còn thiếu trước required baseline

Đây là computational primitive được kiểm trên toy fixtures, **không actual research corpus fit, selected-epoch lifecycle, fresh refit90 certificate, persisted/reloaded research checkpoint, public resume hoặc fitted OnlineSession**. Chưa Junyi research training/CUDA/fullGate/benchmark/calibration efficacy/RQ completion. Protocol21/allocation adopted không tự chọn dimension/lr/epochs hoặc cấp run authority. Các bước chọn epoch, system selector, refit, calibration và OnlineSession vẫn cần wiring/identity/actual receipts đúng scope; không nâng engineering weights thành fitted bằng cờ caller.

copy_inventory.json chứa SHA trước/sau và aliases byte-identical; raw outputs/ROOT reviews/allocations/controller sources giữ nguyên. counter_diagnosis.json phân biệt đơn vị; validated_summary.json chỉ tổng hợp receipts. execution.log là archive closure, không một native run mới. Không binaries/checkpoints/caches/real corpus/private RPC.
