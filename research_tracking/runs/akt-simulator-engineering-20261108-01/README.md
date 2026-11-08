# AKT simulator engineering-only lifecycle — 08/11/2026

Đây là plumbing một epoch toy, không scientific simulator trainer/selected-fit/RQ3.
Reuse native AKT d32CPU smoke, train_epoch/windows/checkpoint primitives; không giả
Junyifold, collector, calibration/final/refit, production bridge, realdata/GPU/cloud.
Explicit approval/budgets:2train+1selection learners,12events/learner,4steps,60s,
2GiBRSS/floor1GiB; cooperative checks, không OS isolation/hardkill.

Final trial03 40pass/17.67s; happy8train targets/1update,selection3known+1OOV,
checkpoint reload delta0. Intentionalpartial1step cófailure JSON/log vàkhông.pt/result.
3targetedinvocations:6totaloptimizersteps. Giữ trial01=33pass vàtrial02=36pass/source
riêng; fixes CPUambientdevice/dependencycoverage đến từ parent source review,
không có pre-fix failedtests được thực hiện cho hai review findings.

Gate19 chỉ CPU software/synthetic acceptance; report/log/XML/currentpointer được
kiểm exactSHA vàbuild binding trướccopy. Không nâng thành CUDA/fulltraining/efficacy.
Source32 snapshots là currentbytes khớp actualtrial03pre/postSHA+Gate19SHA;
không tuyên bố cả32files đều có physicalcopy trướctrial03. Hai owned source files
có physical pre-trial snapshots cho cả3lượt. Historical subset9 coverage giữ nguyên.

Không copy.pt/Parquet/binaries; heavy_checkpoint_inventory.json ghi exacthash/size.
copy_inventory.json cópre/postsource vàcopySHA. Sauclosure không sửabundle.
Đọc readiness_report.md vàparent_review_fix_provenance.json đểbiếtsemantics/limits.
S04/S05vẫnpending. Không bảo toàncallerRNG; chỉCPUdevicecontext/threadcount scope.
