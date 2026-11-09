# GKT data candidate02 — sửa vị trí negative assertion

09/11/2026. Chỉ source derivative dưới prep, chưa Python/import/test/Git hoặc canonical apply. Candidate module01 giữ byteSHA `1650509a3e0baaf91504355e67d4c1857ac2e020071d8f7463ea53887ac65873`.

## Lượt01 được bảo toàn

Actual `gkt-research-data-candidate-pure01-outer/final.json` SHA `edbbb77fac8cc1e04db80cf8ed1fb1dc29a2c6ee27cf1cb4f583c54140a5a09e`, elapsed4.383052825927734s/30.17tests gồm16PASS/1ERROR/0failure/0skip. Shared audit từ chối malformed bank ngay trong fixture(), trước khối assertRaises cũ, nên test chưa bắt đúng boundary. Đây là lỗi đặt negative assertion, không được đổi thành17PASS.

Worker result SHA `957758df1172f08ccf44afd2edd9e8936cc13fdf63f6a83b86d07d0e15af8986`. Owned receipt cho returncode1, cleanup_accepted=true, job_active_after_cleanup0, popen_handle_closed=true. Giữ toàn bộ source01/packet01/raw/owned/outer nguyên vẹn. Chi phí cũ4.383052825927734s vẫn là actual, không reset khỏi lịch sử.

## Derivative02 duy nhất

- `test_gkt_research_data_candidate02.py` SHA `ec6b4248828ff0aaaf39a6a9fee1bb4c4ce8fe15e6894ffe66d221881b91d69a`. Thay một method bằng `test_public_shard_boundary_rejects_invalid_reference_bank`, đặt `assertRaisesRegex(ValueError, 'protocol V1 requires')` quanh `fixture(levels)`. Hai malformed variants vẫn được kiểm; không dựng object giả để lách validator.16methods khác giữ nguyên logic.
- `run_gkt_research_data_candidate02.py` SHA `c58019ee3e391beecbdc13de77da6868e3094703b626e869e616633f694ec5d9`. Chỉ đổi packet/test-discovery/output namespaces01→02. Candidate module alias vẫn01, không đổi monitor/audit/limits/helper.
- `gkt_research_data_candidate02_packet.json` SHA `f963e4ac852834dd9046ba0be82410a79e3a06323d31157d220b41edd5cb645a`. Actualsource refresh22pins gồm16current source/config và6old failure/review/source references; candidate logical source identity vẫn12keys. Exact17 IDs mang testmodule02 với một method đổi tên.

Namespace mới `gkt-research-data-candidate-pure02`, `...-owned`, `...-outer` đều dành riêng, không dùng lại output01. Giữ whole30/owned24/worker20/cleanup3, RSS512MiB/free1536MiB và prelaunch2GiB. Root cần review trước dispatch, không tự retry hoặc hạ floor.

## Review độc lập và nghĩa support

`GKT_RESEARCH_DATA_INDEPENDENT_REVIEW01.md` SHA `605fdc53c5fad0347436fd9f390b44ff032a7dc93875125dc007f5a0f9a6f513` là scoped static review của source01, không actual PASS. Giữ caveat future exporter phải lấy input.eligible/support_reason. Sidecar public trường thật tên `ResearchScoringTarget.trained_item`, chỉ nói current item thuộc train vocabulary. Sau OOV, current item có thể trained_item=true mà fullprefix GKT vẫn unsupported_history/eligible=false. Không dùng item-support flag làm fitted-valid mask hoặc âm thầm bỏ unsupported rows.

Fixture vẫn manufactured typed metadata, không corpus publication,84support, model fit hoặc probability/mastery evidence.

Root command sau review, chưa chạy

`.venv/Scripts/python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/run_gkt_research_data_candidate02.py --packet-sha256 f963e4ac852834dd9046ba0be82410a79e3a06323d31157d220b41edd5cb645a`
