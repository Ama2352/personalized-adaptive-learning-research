# Collector và adapter simulator — fixture CPU

Dùng phương trình môi trường Paper2 và84item/28concept; train-only fixture 2learner×12events với logging policy không đọc latent theta. Các roles khác chỉ có assignments, không sinh dữ liệu trong collector. Không train NN, dùng Junyi/Test hoặc GPU; không có kết luận predictive/learning benefit.

observable.json là whitelist có thể đưa vào KT. oracle_sidecar.json chỉ cho replay/đối chiếu, không đưa vào features. collection_manifest.json ghi source/recipe/RNG/clock/support; proof.json ghi repeat và windows/collation. tests.log/JUnit kiểm guards/parity/OOV. Counts, profile allocation và gap là fixture, chưa là protocol nghiên cứu.
