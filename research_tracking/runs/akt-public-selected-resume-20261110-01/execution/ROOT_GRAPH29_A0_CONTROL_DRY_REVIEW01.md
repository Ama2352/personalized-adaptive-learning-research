# ROOT nghiệm thu dry metadata cho continuous control

10/11/2026. Dry `graph29_a0_control_package01_dry.json` có SHA `14bedf23db546fac72535ff76915d5b668f175bf38e9b654782578f3f85a100f`. Outer trả `ACCEPTED_METADATA_PACKAGE_ONLY`, worker và owned Job đóng sạch, parent environment giữ nguyên. Dry đã đi qua reader/preflight thật, chưa chạy model.

ROOT đã đọc config, authorization proposal, request và caps. Run A0 mới dùng corpus engineering10×84 đã có, với672 targets của8train,84targets của1selection và84targets của1calibration. Selected-only dùng train80 và selection10. Calibration vẫn là phần kiểm corpus, không chọn epoch từ calibration.

Config giữ d256/d_ff1024/final512, một block/tám heads, context100/targetblock100, batch4, dropout0,05, lr0,0001, seed42,20epochs tối đa, patience3/min_delta0,0001. Training reserve40steps/13.440targets/300s, main wall540s. Hai model/Adam constructors gồm fresh-best reload, selection tối đa21passes/1.764targets và tối đa61Architectureforwards. Output cap1,5GiB và checkpoint64MiB giữ theo contract cũ, có disk/free-RAM guard trước native.

Current Gate index183 đã được public reader chấp nhận. Corpus/DONE, runtime, protocol, source bốn scripts và output mới đều có SHA trong proposal. Approval reference tiếp tục là `ROOT_GRAPH29_A0_CONTROL_REVIEW01`. ROOT duyệt materialization đúng ba file mới từ dry này. Materialization chưa cấp dispatch tự động. Cần đọc request thực và kiểm RAM trước actual control.

Đây là kiểm tích hợp có training trên corpus nhỏ đã xuất bản. Kết quả có vai trò engineering, chưa là bằng chứng main matrix hoặc lợi ích học tập. Giữ riêng control, parent và resumed child. Chưa cấp scope refit/calibration/fullCV/Holdout/Modal.
