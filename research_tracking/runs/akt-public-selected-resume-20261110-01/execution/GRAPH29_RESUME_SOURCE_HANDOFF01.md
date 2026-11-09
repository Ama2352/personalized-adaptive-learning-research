# GRAPH29 child tiếp tục parent02, nguồn chờ ROOT duyệt

## Ràng buộc thực đã có

Control thực hoàn tất E7, best4. Parent02 thực dừng ở complete E5, latest5 khác best4, stale1 và next6. ROOT đã nghiệm thu parent02, Job0, outer khoảng86.468s. Dòng child này nhận duy nhất parent02, giữ failure parent01 riêng. Không seal hồi tố hoặc lấy checkpoint từ failure01.

Năm SHA sau bắt buộc do ROOT truyền vào cả metadata dry và materialize, đồng thời nguồn đối chiếu với giá trị đã nghiệm thu

- outer `06b12918cdaae355048650948d72bbfda513e060101ac7aa62114732a2cd87ad`
- terminal `68a741ab3b835e60ee85c0da4afd28d1cac19ce4bd4ef8e8e8eff00e00bdc5f3`
- owned receipt `7447ecd57d97f997bd4e49dfb5a78886b60a1e606d1f20d402bf7edda090aba5`
- request `46f38b0439ef1536c624c8056c06d2e7c5683e3dbad9bdc6c840a82266b31bce`
- execution spec `27fc1fbf1f232cf5a23c4144df4f39bb4d99cd467f2ba1c3728a62e8dfb4534b`

## Bốn nguồn mới

| File trong prep hiện hành | SHA-256 |
|---|---|
| prepare_graph29_a0_resume_package01.py | 45ed89b2feaeda8a954a2e5f4c51bb8a63f3ae9c8e6dde148f9d5709bf64504f |
| run_prepare_graph29_a0_resume_package01.py | f13d3267d5ac565c99275f159b1079447212d4a899daab0b55ec2a8a582aef25 |
| check_graph29_a0_resume01.py | fa3b61b7c5fb36533ecbbe9792fdf0554530b7680300a0cd090ca65da9dada79 |
| run_graph29_a0_resume01.py | 49ad1fa16ef8c3a7a5ffda8f1b3d0da395e34f9c79a8e2f4709ecf2b88cda176 |

Inventory nguồn cuối `graph29_resume_source_inventory02.json` SHA `d1ba2a0541e609692548d6e6132aab3e3a61dcccab5e1d94e3f7ca50308f4686` tham chiếu inventory đầu trước bổ sung kiểm claim của bản xuất control. Các nguồn parent/control gốc giữ nguyên.

## Phạm vi từng pha

Metadata chuẩn bị dùng dataclass thật, `_metadata` thật, public10 thật, current Gate183/publicindex và runtime schema2 đã nghiệm thu. Không gọi factory thực thi hoặc producer. Parent validator ghim external SHA, actual accepted outer/owned correspondence, `_launch_proof` chuẩn, marker/sidecars, exact output population/opaque hashes, latest5/best4 metadata và `validate_history`. Nó không gọi `reference`, `inspect_parent`, `torch.load` hay nhập Torch. Kết quả nêu rõ RAW_BYTES_AND_LAUNCH_BINDINGS_ONLY_CANONICAL_INSPECTION_PENDING_NATIVE.

Dry ghi một proposal. Materialize yêu cầu SHA và nội dung dry bằng nhau, ba đường dẫn config/auth/request mới đều vắng. Auth mới dùng đúng decision AUTHORIZE_BOUNDED_MAIN_SELECTED_COMPLETE_EPOCH_RESUME và `control_binding(spec,(None,resume_request))`. Không tạo metadata-only execution grant.

Worker native bắt đầu bằng genuine worker_gate. Normal public `run_main_selected_resume` tự gọi guard và canonical `inspect_parent` sau GO, trước constructors. Canonical inspector có thể nhập Torch để tạo typed checkpoint references. Không thay inspector/reader/model factory hoặc bỏ kiểm preflight. Outer thêm repo/src trước pure construct, không đặt PYTHONPATH. Win03 process Git profile và original upstream verification giữ nguyên.

## Công việc vật lý và nghiệm thu đề nghị

Child có2model và2Adam constructors,4optimizer steps/1344train target exposures,7native forwards gồm4train và3selection,252selection target exposures. Không save checkpoint mới. Có5checkpoint inspections và2restores, gồm latest5 inspect/restore, opaque inherited-best4 relocation và final best4 inspect/restore. Cả constructors và adapter/native/CP calls có guard cap trước original body. Không ép max_epochs7, scientific max20/patience3 giữ nguyên. Nếu thực tế không trùng control và đòi công việc vượt cap, worker từ chối trước body dư và giữ failure.

Các kiểm sau normal entry

- Complete E7/best4 và full84raw selection targets, không OOV thiếu.
- History E1–5 giữ nguyên dictionary từ parent. Toàn bộ E1–7 có cùng receipt, epoch/best, native selection summary, raw prediction semantic SHA và training loss_sum với control. Không so elapsed/training duration giữa hai tiến trình.
- Initial full model/backbone cùng control. Latest5 được canonical restore, chỉ epoch6/7 có epoch files mới trong child.
- Best4 được copy bằng đường chuẩn, cả ba file checkpoint phải byte-identical với parent. Không có checkpoint epoch mới.
- predictions.csv, targets.csv, coverage.json trùng SHA control đã gắn ArtifactClaim gốc. Hai CSV join84unique keys, đúng raw_selection10/origin selection.
- Durable child journal chỉ4actual optimizer reservations/returns/commits. Terminal cumulative14steps/4704targets, lineage parent10+child4 và cumulative3models.
- Parent source/proof/output bytes không đổi; parent+child cùng retained quota1536MiB. Không refit/calibration/system winner/CUDA hoặc crash-recovery claim.

## Hạn mức chờ ROOT review

Child whole360/owned350/worker340, cleanup3, finalization reserve10. Planned parent charge180 cộng child whole tối đa360 bằng lineage540. Training300, cumulative40steps/13440targets, max3constructors vẫn do canonical guard/tracker thực thi. Parent elapsed quan sát86.468s không thay charge180. Failure01 đã tiêu thụ10steps/3360targets/15forwards, outer91.7282951s, vẫn ghi chi phí riêng trong hồ sơ kỹ thuật. Tổng chi phí các lượt đối chứng và failure không được đổi tên thành một dòng540s đã kiểm.

Giữ prelaunch4GiB, workerRSS1GiB/free floor2GiB/disk2GiB, CPU2threads. Bộ đo RSS worker tái sử dụng profile cũ, không tuyên bố đo tổng familyRSS. Owned Job đảm bảo ownership/cleanup. Metadata outer60/owned57/worker50/free2GiB/RSS1GiB. Không nhánh nào tự retry.

## Lệnh cho ROOT sau review cú pháp và nguồn

Dùng `.venv` Python -B, exact Win03 profile do ROOT cung cấp. Với metadata outer truyền đủ

`--worker-sha256 45ed89b2feaeda8a954a2e5f4c51bb8a63f3ae9c8e6dde148f9d5709bf64504f --outer-sha256 f13d3267d5ac565c99275f159b1079447212d4a899daab0b55ec2a8a582aef25 --approval-reference ROOT_GRAPH29_A0_RESUME_REVIEW01`

Và cùng năm đối số ở trên dưới tên `--parent-outer-sha256`, `--parent-terminal-sha256`, `--parent-owned-sha256`, `--parent-request-sha256`, `--parent-spec-sha256`.

1. `run_prepare_graph29_a0_resume_package01.py --prepare-dry` với các đối số đã nêu.
2. Cùng entrypoint `--materialize` sau ROOT đọc actual dry, kèm actual `--expected-dry-sha256` và `--review-reference`.
3. `run_graph29_a0_resume01.py --request artifacts/akt/local-tests/akt-research-runner-20261108-01/graph29_a0_resume01_request.ROOT.json --request-sha256 SHA_THUC_DO_ROOT_CUNG_CAP --worker-sha256 fa3b61b7c5fb36533ecbbe9792fdf0554530b7680300a0cd090ca65da9dada79 --outer-sha256 49ad1fa16ef8c3a7a5ffda8f1b3d0da395e34f9c79a8e2f4709ecf2b88cda176 --approval-reference ROOT_GRAPH29_A0_RESUME_REVIEW01`.

Chuỗi SHA_THUC_DO_ROOT_CUNG_CAP chỉ là hướng dẫn, không là input hợp lệ. Agent chưa chạy Python/import/AST/tests/native/Git hoặc materialize proposal. Cần ROOT review và thực thi riêng. Đây là Phase1 intentional complete-epoch resume, Phase2 unexpected fault/partial-epoch recovery vẫn còn thiếu trước paid long training.
