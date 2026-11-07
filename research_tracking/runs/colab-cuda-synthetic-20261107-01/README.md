# Actual Colab T4 synthetic lifecycle và recovery — 07/11/2026

Chỉ archive actual artifacts đã chạy, không thêm model/GPU/cloud run hoặc sửa notebook. ZIP SHA64392c70b03162b923740dbe73c0b991a0e7f3f03eea31e6912172db2158f188,28657701bytes; tự verify44RESULT_MANIFEST outputs trong ZIP/local,144chunk SHA và144response SHA. receive_verification_144chunks.json giữ hash/path metadata; không copy144Base64 receipts hoặc private auth. Giữ6stage03receipts/raw responses exact bytes.

Actual Linux/Colab CPU505pass0fail/error/skip117.23s với2explicit deselections(nativeCPUimport/frozenassignmentsrealdata); portable/software suite, không main realdataGate2. Actual TeslaT4 lifecycle400targets,1optimizer step0.916326333s,peakVRAM187200000bytes,export400predictions. Gate4false.

ActualT4 recovery17targets/branch,continuous5updates so với interrupt2+resume3;3fresh processes,total10updates28.943933268s. Target ledger/RNG/sampler/source immutability exact,max state/prediction absdelta0 với atol=rtol1e-5. Controlled optimizer boundary trong same runtime, không hardkill/preemption/runtime replacement/ModalVolume/durability proof. Không fulltraining/realdata/Holdout/RQefficacy.

Source execution identity là historical GitHEAD e7dcf6b63a92bb532663eec40948b835f5b7155f cộng working-file changes verify139source SHA, không cleanGit/HEADalone claim. Archive HEAD hiện e25 là commit sau execution, ghi riêng trong metadata/helper manifest. Exact local notebookv12 SHA e75004d1... và embedded sourcebundle ddb35b8e... khớp returned manifest. Ba Paper notebooks chỉ strip outputs/metadata trong bundle copies; kiểm original SHA và cell source equality, không sửa historical notebooks.

Small JSON/log/XML/TXT copy theo inventory. synthetic_predictions.csv là derived400unique rows đọc2verified synthetic Parquet, không original CSV từ Colab. .pt/Parquet/28MB ZIP giữ vị trí gốc; large_file_inventory.json giữ locations/sizes/SHA, không unpickle checkpoints. archive_copy_inventory.json có SHA trước/sau copy và manifest hash mọi output.

Guarded release03 kiểm đúng workspace/ZIP/144chunks và GPU worker trước unassign; raw receipt có KLTN_RUNTIME_RELEASE_ACCEPTED. Official [google.colab.runtime.unassign](https://raw.githubusercontent.com/googlecolab/colabtools/main/google/colab/runtime.py) lines13–35 raises nếu HTTPstatus khác200 rồi request frontend disconnect. HTTP200 APIacceptance là suy ra có điều kiện từ return và reference code, không rawHTTPstatus capture/independent cloudlist/frontenddisconnect verification. Không gọi release thêm hoặc đụng runtime khác.

Một archive preflight guard trước bundle creation đã fail vì HEAD vừa đổi e7→e25. Đây là archive metadata guard, không GPU failure; không có output/source-file snapshot riêng cho invocation lỗi. Không regenerate ZIP/notebook/results; sửa cách phân biệt execution-source historical HEAD với archive HEAD rồi kiểm lại all artifact/source hashes. Lỗi tool launcher trước đó cũng không thực thi Python/GPU. Parent acceptance/adversarial reports được snapshot nguyên bytes.

Không sửa bundle sau closure. force_add_paths.txt liệt kê logs cần force-add; không sửa Git/.gitattributes/index/state/docs. Manifest có private-path/SHA references không có nghĩa cần commit private files. Parent review/commit riêng.
