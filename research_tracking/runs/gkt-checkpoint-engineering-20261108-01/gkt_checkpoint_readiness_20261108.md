# GKT weights-only checkpoint engineering — 08/11/2026

**Targeted trial02 đạt40/40 CPU tests; chưa GKT baseline nghiên cứu hoặc resume.** Một shared handmade toy fixture dùng1 actual Adam update trong lượt02. Lượt01 trước đó đã dùng1 update rồi fail ở quyền tạo hard link; tổng2/4 updates. Cả hai dùng cùng bytes source/test. Không corpus/realdata/Holdout, GPU/cloud, install/network hoặc broad45/88-case rerun.

## Hợp đồng và hành vi đã kiểm

Chỉ thêm [training_checkpoint.py](../../src/knowledge_tracing/gkt/training_checkpoint.py) và [test_training_checkpoint.py](../../tests/gkt/test_training_checkpoint.py), theo [contract đã được parent duyệt](../../artifacts/akt/local-tests/gkt04-checkpoint-preparation-20261108-01/CONTRACT.md). Training/recurrent/core/config/shared/AKT/exports giữ nguyên trong tiểu tác vụ. Recipe vẫn `gkt_static_recurrent_convention_v1`; không chọn mapping/graph-source/scientific protocol S04/S05.

`save_engineering_weights` yêu cầu typed ordinary completed GKT train-step result: actual optimizer_steps1, engineering role, current model digest khớp weights-after, graph/recipe/domain/node-order/vocab/source/settings/counters/selected row identities khớp. Không nhận zero-step/bounded/unchanged-receipt-but-mutated-weights như một fitted artifact. Identity là cooperative consistency, không chứng nhận caller truth hoặc chống forge/reseal toàn bộ metadata.

Save chỉ vào fresh child dưới `artifacts/akt/local-tests` hoặc `experiments/gkt/results`, parent phải tồn tại; reject existing path, outside root hoặc symlink parent. Payload≤1MiB và metadata≤64KiB. Ghi pending bằng exclusive open, flush/fsync, kiểm byte lại; atomic hard-link publication không clobber final path. **COMPLETE được publish cuối** sau weights/metadata và source/model check; không có fallback overwrite. COMPLETE.pending được giữ làm alias sau commit để không còn potentially failing cleanup sau publication. Reader chỉ chấp nhận COMPLETE cùng hai final files nó liệt kê; không coi pending alias là artifact riêng hoặc tuyên bố cặp files là một filesystem transaction duy nhất. Partial attempt giữ nguyên và không reuse.

`load_engineering_weights` yêu cầu expected manifest SHA và exact identity từ caller. Kiểm strict schema/role/source/geometry/flags, file allowlist/size/SHA và metadata identity trước `torch.load` từ chính verified BytesIO với `weights_only=True,map_location='cpu'`. Sau deserialize, kiểm exact registered keys, shape/layout/dtype/finite; actual adjacency phải khớp bound graph. Constructor dùng saved adjacency đã kiểm để fixed kernel và registered buffer cùng graph, explicit CPU context và `fork_rng(devices=[])`; caller Torch CPU RNG giữ nguyên. Check model/recipe digest, source và file bytes lại sau load. Đây không phải API cho arbitrary/untrusted pickle hoặc production fitted certificate.

Payload chỉ có weights/buffers. Metadata ghi **optimizer_saved=False, rng_saved=False, hidden_state_saved=False, resume_supported=False, fitted_research_model=False, completion_unit=train_step**. Optimizer settings/digests/counters chỉ là provenance; không restored. Không serialize preupdate diagnostic hidden state như current-model continuation. Loaded model ở eval; candidate readout vẫn giữ unfitted-convention evidence role, không tự promote fitted inference adapter.

## Hai lượt thực tế và đối chiếu quyền

| Evidence | Kết quả xác nhận | Giới hạn |
|---|---|---|
| Trial01 |1PASS/39fixtureERROR; controller14,230893s;1update | Cùng lỗi `WinError5 Access denied` tại hard-link weights.pending→weights, không COMPLETE. Không source/test bugfix hoặc relabelPASS |
| Owned file control01 | Default execution hard link thất bại WinError5;0model/optimizer | Chỉ34-byte owned file; không data/GPU/network |
| Owned file control02 | Exact process escalation hard link thành công, link_count2;0model/optimizer | Chứng minh permission boundary ở môi trường chạy này, không whole-host filesystem attestation |
| Trial02 |**40PASS/0fail/error/skip**, pytest5,73s/controller7,378965s,1newupdate | Exact bounded process escalation, source/test vẫn5ddf/494e; không weakening publication guards |

Cumulative test-controller21,609858s; cộng2s bảo thủ cho static checks và1s control-probe reserve thành **24,609858/60s**. Ledger global ghi TRƯỚC mỗi actual Adam.step, tổng2/4; không cộng fixture errors thành independent model experiments. Trial02 dùng remaining timeout42s và postelapsed check, không nới60s cap. Permission contrast không thêm optimizer step.

Acceptance40cases có exact weights/model digest/adjacency và **bitwise prediction parity** trên fixed fresh-state toy sequence; CPU/default-meta constructor và caller RNG preservation; explicit CPU weights_only call; source/role/domain/node-order/vocab/graph/config/recipe/counter/flag drift reject trước deserialize; serialized key/shape/dtype/nonfinite/graph mismatch reject; payload/manifest bounds và fixed path allowlist; bounded/zero-step/mutated-model receipt reject save; atomic no-clobber giữ existing destination; injected failure trước COMPLETE giữ partial và reader reject. Symlink test là simulated parent-is-symlink contract, không claim actual Windows symlink creation.

Hai actual trials giữ raw stdout/stderr/JUnit, run receipts và24source snapshots (6source/test×before/after×2). Shared successful checkpoint và trial01 pending weights giữ trong artifact tmp theo run, chỉ SHA/size references được chọn để archive, không copy binaries. Metadata gốc của successful checkpoint đủ kiểm complete-step/settings/provenance. Không rerun model khi kiểm/đóng evidence.

| Tệp | SHA-256 frozen |
|---|---|
| Source checkpoint | `5ddfea74c17cddf8f3ba72e60dcde1f2d36c6950ad2b22f7d2d55361ed2a89d8` |
| New tests | `494ea9e719898a5d4c5deda50bc280fa0f2ff8d569b6934b34145281fc0d692e` |
| Trial02 run | `3d5f5dfc45a544072a0e85e52545dcf343865b0835974dd2f6f393a38d128d13` |
| Trial02 JUnit | `113d2c60bacde4e0c719e28f558d6a25c07651e1b2b7ac919479c384d3369060` |
| Acceptance/inventory | `f9e8e0443c97d7acc3db9c7d5bd49a8b1c6e372a1202cf074fc5cf9f8f211971` |

Actual [receipts/selected inventory](../../artifacts/akt/local-tests/gkt04-checkpoint-preparation-20261108-01/acceptance.json) phân biệt source/test acceptance, environment failure và binary references. Parent review implementation/actual receipts là bước trước đóng [bundle](../runs/gkt-checkpoint-engineering-20261108-01/README.md); chỉ ghi actual review provenance, không dựng independent-agent PASS nếu không có.

## Phần còn thiếu

Weights-only persistence không tạo epoch/corpus runner, selection/refit, optimizer/RNG/hidden-state restoration, interruption recovery, fitted adapter hoặc final comparator. GKT03 caller-owned budgets/state/source vẫn cooperative, không nonresettable authorization; exception sau update không hứa rollback/checkpoint. GKT04 publication/loader không nâng những claims đó. Scientific mapping, graph construction/provenance/variants, cold/OOV/calibration, journal recurrence parity, research optimizer/splits/seeds/capacity matching và S04/S05 vẫn pending. Không kết luận predictive efficacy, RQ3 hoàn tất hoặc graph giúp học tập từ40software tests.
