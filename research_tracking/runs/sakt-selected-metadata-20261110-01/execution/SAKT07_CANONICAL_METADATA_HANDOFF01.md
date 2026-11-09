# SAKT07 canonical apply và metadata34

Đã tạo riêng `src/knowledge_tracing/sakt/research_execution.py` và `research_runner.py` bằng bản sao byte chính xác của candidate được Root duyệt. Test mới `tests/sakt/test_research_selected_runner.py` dùng normal import, bỏ fixture load file riêng cùng ba import không còn dùng. 34 ca dự kiến giữ nguyên. Bản candidate trong P giữ nguyên.

Before inventory d0618fc1530e29d5648fd33cd8e0eddd34f18ae969cce3a57b8c93ddd18ec223 và after inventory4ae1d0ad882924247daa5e3fbac3b429c122e259b5c00f024a9c0a6913243b41 nằm tại `sakt-selected-canonical-apply01/`. SHA Main execution, Main selected runner, shared research_selection và Gate writer trước–sau khớp.

Canonical execution có SHA183d37545e1aa87144aaab2c21efef000bda658ecc2d707670f0f4c7b623ff57. Runner có SHA2d6ec4f6f0be78013c610964479ee085d9effecace83259ba525bd066ae8de7f. Test có SHA8ae28c4c93b6933254bcb9513b906c24fd27f0533463139f8062e1ce904b876f.

Worker `check_sakt_selected_metadata01.py` có SHA3683aa87fd0d35a03a740cddc7f3c051afa2dcb30d4bd1d5d4ee2f3d97aa0a2c. Outer `run_sakt_selected_metadata01.py` có SHA7881f7249008438fb263555d43385a0838fdc49fef31c972a2f9e6e74a9aff4e. Packet `sakt_selected_metadata01_packet.json` có SHA1ec5707d5cf892e466a692944f296f2d859c85b08ff2ff1d64a2009b980997f9, ghim54source và11runtime files.

Worker tái dùng warmup Windows thật từ helper fc067, chỉ cho tối đa hai cmd /c ver trong phase metadata với whitelist helper đã có. Sau khi đóng phase, mọi Popen/socket/scientific import bị chặn. Không thay API OS. COLUMNS/LINES chỉ cố định terminal display, được khôi phục sau test. All34IDs được thu trong cùng pytest invocation trước test body và kiểm phân bố chín hàm, uniqueness cùng exactJUnit IDs. Không fake successful guard hoặc corpus/runtime evidence.

Whole30s, owned tối đa27s gồm cleanup3s, worker20s. RAM profile dùng peak worker128MiB/free1GiB với prelaunch1280MiB. Resource scope là cooperative hook samples. Owned helper bảo đảm hard deadline và cleanup Job0. Không gán số đo worker thành toàn Job RSS. Timer trong worker là fallback phụ thuộc GIL, không hard CPU quota.

Root chỉ chạy sau review, bằng lệnh sau trong repository `.venv`.

```powershell
.venv/Scripts/python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/run_sakt_selected_metadata01.py --packet-sha256 1ec5707d5cf892e466a692944f296f2d859c85b08ff2ff1d64a2009b980997f9 --worker-sha256 3683aa87fd0d35a03a740cddc7f3c051afa2dcb30d4bd1d5d4ee2f3d97aa0a2c --controller-sha256 7881f7249008438fb263555d43385a0838fdc49fef31c972a2f9e6e74a9aff4e --approval-reference ROOT_REVIEWED_SAKT07_CANONICAL_METADATA34_ONLY
```

Đầu ra riêng dự kiến là P/sakt-selected-metadata01 và P/sakt-selected-metadata01-owned, fixtures tại artifacts/akt/local-tests/ssm01. Chưa tạo những output này hoặc chạy bất kỳ test nào. Đã kiểm AST ba canonical files cùng worker/outer. Typed producer vẫn chưa được xác nhận bằng actual normal-entry fit. Metadata34 nếu đạt chỉ nghiệm thu quyền sai bị chặn và data joins, còn phép native producer d200, selected fit, external systemfreeze, refit/calibration và GPU cần review/allocation riêng.