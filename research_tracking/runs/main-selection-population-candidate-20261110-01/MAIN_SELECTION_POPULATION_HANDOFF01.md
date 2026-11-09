# Helper F/K-y · candidate nguồn

API `prepare_selection_population(role_data, context, expected_provenance_sha256=..., expected_audit_receipt_sha256=..., limits=...)` chỉ nhận đúng `PublicRoleData` role selection đã audit từ trusted reader. Không mở file/corpus hoặc chạy audit/model. Caller phải ghim context và hai receipt identities đúng nguồn trước khi gọi. Typed role/receipt không tự chứng minh reader đã thực thi.

K dùng đúng `research_admission.ModelNeutralKey`, record hash dùng lại `_canonical` của module đó. Prefix chain dùng `simulator_bridge.identity_hash` theo hai phương trình của `research_simulator_data.research_scoring_targets`, đưa Observation hiện tại vào chain sau key hiện tại. Không import module data AKT chứa NumPy. Chỉ sort statistical K, giữ nguyên chronology/input. Recompute role shard SHA theo payload learner-sorted để phát hiện thay nhãn dù class_counts được đổi theo.

Kết quả có `PopulationExpectation`, learner counts, class counts và receipt SHA. Ba flags file_admission/freezerefitauthority đều false. Chưa phải validator chín artifacts, freeze, winner hoặc execution grant. Không đòi hai lớp hoặc84reference support mới, vì public reader đã chịu trách nhiệm audit đó.

Sáu unittest methods, toàn bộ dùng manufactured RoleData/audit-shaped records. Không tuyên bố fixtures là corpus thật đã được native reader nghiệm thu. Bao gồm chronology khác canonical item order và hai lớp, label mutation, duplicate source/learner, wrong role/empty, row caps/bool label, one-class accepted/domain mismatch. Không thêm model/world hoặc thay canonical source/Gate.

Root có thể chạy sáu methods dưới outer stdlib cap10s khi cửa sổ RAM cho phép. Agent bàn giao nguồn chưa chạy vì A1 native đang dùng tài nguyên. Command đọc source và chạy unittest riêng, cần Root wrapper lưu stdout/stderr/RC.

```powershell
.venv/Scripts/python.exe -B -c "import sys,unittest; sys.path[:0]=['src','artifacts/akt/local-tests/akt-research-runner-20261108-01']; import test_main_selection_population_candidate01 as tests; unittest.main(module=tests,verbosity=2)"
```

Không gọi loader/model/Git/actual corpus trong command này. Nếu test fail, giữ output trước sửa. Sáu ca chỉ chứng minh helper trên dữ liệu chế tạo, không nghiệm thu actual population chuẩn bị sau này.

## SHA snapshot

| Source | SHA-256 |
|---|---|
| artifacts/akt/local-tests/akt-research-runner-20261108-01/main_selection_population_candidate01.py | 8709f62a4aeed14bb3bfd8581e419205a0e8695d7eb3312832c96d7b64ef1906 |
| artifacts/akt/local-tests/akt-research-runner-20261108-01/test_main_selection_population_candidate01.py | ce9c8626193326ab2a43ebc65da81917b49f2139da3066885bf4e11005f66627 |
| src/knowledge_tracing/research_admission.py | b8601da03a972834cfd2f5596ea6a6b9c5759437796b4f4b65720f7abc1a92f2 |
| src/knowledge_tracing/simulator_corpus_reader.py | e582bf293e7699f1dc98096fcc693437610f2253bddb11ba4fff8952a35f6a90 |
| src/knowledge_tracing/simulator_bridge.py | b29105acd8de84b060ca27573bb7f7cf8e85599a4596e50e4a21ab63c82329d2 |
| src/knowledge_tracing/simulator_data.py | 79e28c1a8fc9b3bd5f3283868d7aba1a5bbc7c76764725a8b01098b2ae33cd9f |
| src/knowledge_tracing/simulator_research_data.py | 51eb7275a6a4a6b26b763a21a8fe6dc15b0973fc19b3c5557175eaa298db7e53 |
| src/knowledge_tracing/akt/research_simulator_data.py | 9596c2dc5ae86cdf89e5f68c15224a6794b6056093dabee6b26502dfabdf092b |

Work ledger tĩnh gồm6physicalmethods và13helper invocations, dự kiến2success/11ValueError theo các fixture hiện tại. Chưa được thực thi, đây không phải counters quan sát.
