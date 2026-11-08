# Collection05: ROOT namespace thật, lần cuối batch, chưa chạy

04 terminal ROOT38.9863628s/60; remaining collected984 nhưng3collection errors:
`test_runtime.py` import `scripts.akt.check_runtime`,
`test_synthetic_context_builder.py` import `scripts.akt.prepare_synthetic_context`,
`test_rq2_controls.py` import `scripts.research.analyze_rq2_controls` đều lỗi
ModuleNotFoundError. RC2, không GatePASS. Guard0/Jobcleanup accepted. Không lấy984
làm expectedcount hoặc chấp nhận partial; không retry reporting hypothesis cũ.

Source worker04 chỉ thêm scripts/research vàthird_party; load_refresh thêm src,
không có ROOT. CLI canonical `python -m pytest` từ ROOT có current-directory
import entry, còn programmatic pytest.main trong script artifact không tự có
entry đó. Repo scripts không có __init__.py; pyproject chỉ tìm package dướisrc.
Raw04 chưa ghi origin thực tế của namespace scripts, không suy diễn origin cũ.

05 chỉ thêm fixed physical ROOT vào sys.path ngay sau worker_gate/GO. Giữ các
entry cũ, imports libraries sauGO vàguard nguyên. Dùng importlib.import_module
thật cho scripts/scripts.akt/scripts.research dưới call/audit guard; không tạo
package giả hoặc sửa sys.modules/tests. Namespace __file__/spec.origin phảiNone,
namespace __path__/searchlocations phải đúng duy nhất ROOT/scripts[/akt|research].
Lưu before/after namespace cùngsys.path, yêu cầu origins không đổi trước/sau
collection; outer nhận field root_namespace_verified chỉ sau kiểm actual.

New outputs gate-collection05 vàgate-collection05-outer. Cùng frozen154source/
69module packet bacc6e49d14d244396b7be03cf68c62daefa8c14adf056b1f0c5cde8b8f1ed90,
3freshgroups/60whole/4GiBadmission/1GiBfloor/3GiBprocess; no terminal/no body/
no fit/no model/data/network/CUDA. Không reuse warmedprocess hoặc partialcount.

Agent chưa chạy AST/pytest/import/collection. ROOT review exactpins trước
dispatch05; đây là lần thử cuối của batch. Nếu thất bại, giữ mọi logs/receipts
và dừng để focused nextbatch, không tự sửa/rerun hoặc tăngcap.
