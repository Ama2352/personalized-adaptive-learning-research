# Audit tĩnh fixture model02 sau actual01 setup failure

Ngày09/11/2026. Không import/test/model/AST/Git. ROOT đã chạy01:18setup errors,
0test body, mọi native counter0; failure là fixture bank, không phải bằng chứng
core forward/gradient thất bại. Raw12files01 giữ tại chỗ và SHA trước/sau; snapshot
5source/controller/packet ở `pre-cgakt-bank84-fix01/inventory.json`.

Sửa duy nhất testbank:28concepts, mỗi concept đủ1050/1200/1350; item1200 giữ ID
`i0`…`i27`, hai item kia có suffixdifficulty. Observations vẫn chỉ `i0/i1/i2`,
vocabulary train vẫn3. Không đổi events, labels, source rows hoặc global ranks.
Model7ed087/context5a5ada91 và validators không sửa.

Đối chiếu source toàn phần fixture:

- `simulator_research_data.py:41–55`: development10 cho exact8train/1selection/
  1calibration; final1 chỉ là metadata, không tạo final observations.
- `simulator_research_data.py:126–185`: bank mới84items/28concepts/đúng3difficulty;
  reference_items chính toàn bank; expected learners từng role đủ. Missing81
  reference items trong observed train là coverage ledger, validator không đòi
  mọi item đã xuất hiện và không cho chúng thành fitted vocabulary.
- `ResearchProvenance`: role/plan/split/domain và own identity được dựng từ cùng
  object; UTC/Unixseconds; collector/environment bindings và logging policy khớp.
  Các SHA H là manufactured metadata, không bằng chứng collector/Method24 chạy.
- `simulator_data.py:119–163` + `ItemQuery`: source_row=role×100000+ordinal×100+
  rank+1, duy nhất và>=1; timestamp1000+rank tăng trong từng learner. Không có
  yêu cầu đồng hồ tăng xuyên các learner. Binary labels là Pythonint; đúng typed
  ObservableTrajectory, ItemQuery, Observation; mỗi learner6events.
- ShardLimits đúng8/1/1learners,6events/learner và48/6/6events/role. Context
  train48targets/8windows; selection6targets/1window, không OOV. Geometry thật
  context100/targetblock100/max200, inputwindow6; prefix đúng nguồn iterator.
  Mỗi childtarget có1parent, tổng parentrecords24 và observedrows120 cho train;
  dưới limits100/1000. Byte/time caps chưa đo, vẫn phải runtime-check.
- Train80 graph binding dùng actual typed plan/domain/provenance/shard identities
  của fixture. Encoding fit chỉ train; rawselection index cùng encoding80,
  selection shard hash khớp binding; không refit/calibration constructor.
- Method24 containers là giả lập rõ ràng, không parser/solver:10publicSHA fields,
  method source binding và bank/train lineage khớp metadata; nodes giữ đủ28;
  c00→c01 supported.75 và c00→c02 unsupportednull/operational0. Không privileged
  truth hoặc fake confidence estimate được fit.
- Actual dataclass attributes đối chiếu: CausalSequenceInputs không có labels;
  current context dùng exacttype và concept_idsNone; model dùng đúng arrays,
  WindowInputs metadata, AKTBatch fields, ResearchGraphAudit.parents và encoding.
- Config giữ actual research256/8heads/1block/1024/512/dropout.05, CPUFP32;
  nn.fixture tối đa2learners×6tokens. Test CPUdefault_generator.manual_seed
  không gọi all-device torch.manual_seed. Không thay toy/profile validator.

Proposal02 giữ18cases/1backbone+1wrapper+1gate/8Architecture.forward/
5logicalautograd.backward/0optimizer ctor-body-or-step. Timer80/owned<=87 gồm
cleanup3/outer90 gồm final3; observedRSS<=1GiB/free>=2GiB vẫn là giả thuyết chưa
được chứng minh bởi01 (01 không dựng NN). Original provenance loader vẫn thật,
exact10localGit read-only commands; audit executableNone được giữ như quan sát,
process-only safe.directory chỉ exact physical upstream path, không globalGit.

ROOT phải review và dispatch02 riêng. Audit tĩnh này không gọi fixture hoặc coi
absence của lỗi tĩnh khác là runtime PASS. Maintraining còn chi phí7fullcache
hash/batch; tinycore PASS nếu có không chứng minh lifecycle/throughput/fit.
