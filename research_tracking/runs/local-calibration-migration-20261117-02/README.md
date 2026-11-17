# Entry local cho join/audit và calibration A2/A3

## Nghiệm thu tổng hợp

Nguồn driver ngoài KT dùng public join_numeric_calibration_snapshot để giữ nguyên mọi kiểm phase/checkpoint/roles/cache/numeric/source. Callback raw-ready kết thúc invocation trước khi fitter gom RAM cũ được gọi. Fit là phase riêng dùng SQLite adapter đã kiểm parity V1.26kiểm thử đạt7,72giây trong tests02, gồm20ca fitter và6ca migration. Có ca A2/A3 nối numeric20target18supported2OOV rồi fit khớp toàn payload V1. Có ca khôi phục10row/1learner đầu từ snapshot, bổ sung learner còn lại, final20row/2learner; shard cũ và snapshot không đổi SHA. Tests01 đạt26ca trên bản trước bổ sung ràng buộc stop-marker gắn đúng manifest.

## Cây staging

D:/Dev/KLTN/artifacts/akt/local-calibration/<run>/VOLUME là root vật lý khai báo cho invocation. Bên trong giữ đường dẫn tương đối giống Volume gốc.

- calibration-inputs-20261117-01/source chứa INPUT.zip đã giải nén giữ nguyên bytes. src được đặt trước checkout khi import. Source identity d22 phải khớp; upstream/akt.py cần đúng payload nguồn LF nếu archive không chứa.
- junyi-calibration-real-20261117-01/a2-numeric/payloads hoặc a3-numeric/payloads chứa receipt,224manifest và224NPZ nguyên bytes từ Drive đã kiểm.
- Cache window manifest/admission đặt đúng đường dẫn tương đối trong cache receipt.
- local-migration-metadata/A2 hoặc A3 giữ GPU_RELOCATED.json và RELOCATION.json mới. Receipt GPU gốc giữ nguyên. Chỉ thay prefix path trong bản dẫn xuất, ghi SHA trước/sau và nguồn adapter.
- Kết quả nằm trong junyi-calibration-real-20261117-01/a2-raw-freecpu-a2-100/payloads và a2-fit-freecpu-a2-100/payloads; tương tự A3. Không sửa thư mục dataset hoặc BKT artifacts của checkout chính.

CLI chỉ chạy bằng D:/Dev/KLTN/.venv/Scripts/python.exe, yêu cầu4GiB disk trống. Việc kiểm đầy đủ source pin, roles và dữ liệu diễn ra trước join. Artifact-root declaration được đặt có phạm vi tới D root, khôi phục sau invocation. Guard canonical path và alias gốc giữ nguyên.

## Lệnh join

Dùng scripts/akt/local_calibration_migration.py với --phase join --volume <VOLUME> --payload <PAYLOAD.json> --payload-sha256 <SHA> --variant A2 --attempt100. Nếu có snapshot cũ, thêm --partial-snapshot <SNAPSHOT.json>. Snapshot khai báo path,manifest_sha256,files với bytes/SHA từng manifest+Parquet đã hoàn tất, và writer_stop_receipt gồm path/SHA. Marker đã pin phải có status COLAB_CPU_WRITER_STOPPED,remote_process_absent true,raw_manifest_sha256 khớp snapshot. Snapshot nguồn được giữ nguyên; driver copy sang output mới trước public export resume. Không mang audit DB cũ hoặc pending shard chưa hoàn tất sang snapshot đã khai báo.

Nếu thêm --drive-token-file <đường dẫn OAuth private hiện hữu>, raw được publish và SHA đọc lại bằng publisher hiện có. Credential phải nằm dưới artifacts/akt/private của checkout chính. Không gửi credentials cho source frozen hoặc ghi chúng vào output. Bỏ tùy chọn này thì trả publish_request để nhánh chính upload riêng, chưa được coi Drive verified.

## Lệnh fit

Cùng CLI với --phase fit và thêm --raw <raw directory> --raw-manifest-sha256 <SHA complete>. Có thể đặt --max-seconds7200, mặc định như vậy. Fit replay observations hai lần độc lập để target/prefix và expected keys tiếp tục do canonical reader kiểm; không dùng tee. Target database SQLite nằm trong output fit, nhưng file publish allowlist chỉ gồm config.json,fit/temperature.json,fit/manifest.json,resource.json,COMPLETE.json. Database không tự upload hoặc xóa.

Nguồn raw phải complete và đúng calibration_predict/fullrolecoverage,checkpoint,source,partition,population. Adapter giữ200evaluation mặc định và source V1 làm authority toán học. Execution receipt ghi riêng adapter/solverAST SHA và resource, không đổi identity fitter nguồn.

## Giới hạn và phần nghiệm thu tiếp

Chưa chạy full calibration local hoặc network từ nhánh này. Root cần chuẩn bị input/download/checkSHA, stop receipt thật, giám sát tổng RSS process khoảng1GiB và đối chiếu Drive. Guard budget của fitter SQLite là512MiB sampledRSS; lần đo100k trong bundle local-calibration-spool-20261117-01 đạt khoảng34MiB nhưng chưa đo toàn pipeline1,62triệurow. Không dùng số fit calibration làm đánh giá độc lập outer-fold. Không training, không GPU hoặc Modal CPU.
