# Batch CPU controls, exact-step recovery và portable kit

Run32learner và expanded256learner được lưu riêng, report cpu_matched_controls_20261107.md ghi strata/coverage/giới hạn. Đây là engineering/evidence-archive run, không là model effectiveness experiment.

Gate2support-cap03 có239passed1failed vì host RAM floor được chạm trong lifecycle fixture. Giữ log/JUnit; khôngpublish pointer cho run fail. Sửa riêng test fixture về deterministic resource readings, production guards giữ nguyên. Gate2support-cap04 và expanded-controls05 đạt240test cho các build tương ứng. Gate2portable-kit06 đạt241test cho build cuối.

Kitv4 thiếu host fixtures, v5 còn GAM local-data dependency. Lượt kiểm đầu đã chạy khi upstream checkout chưa sẵn,66failed175passed, log được giữ. Sau chuẩn bị checkout, v4 còn5failed235passed1deselected. Local Git clone gặp ownership/MSYS restriction; dùng source-copy104files có SHA trước/sau, không sửa upstream gốc hoặc Git global config.

Kitv5 AKT/shared240passed1deselected. Kitv6 chỉ đổi test_core.py của GAM so với v5, manifest comparison chứng minh source/dependencies AKT/shared giống v5. GAM trênv6 đạt31passed1deselected. Hai test loại rõ là local native-runtime integration và frozen-assignments integration, không chuyển dữ liệu learner vào kit.

Kitv6 có113files, source-only notebook copies, project venv dùng system-site-packages để kế thừa runtimeTorch, installs chỉ vào venv. CPU worker ẩn CUDA; GPU probe giữ runtime visibility. Chưa có actual Colab/Linux/CUDA execution. Public CLI recovery vẫn pending theo contract16. Windows lock trong kit chỉ là hash fixture, không là Linux installation recipe.

ZIP manifests và archive SHA được giữ để tái dựng. ZIP gốc ở artifacts/akt/colab, được ignore; source files đã commit. Copy inventory và manifest xác minh tính toàn vẹn, không tự chứng minh scientific validity.
