"""Review bằng đọc source/bằng chứng; không import Torch hoặc chạy lại kiểm thử."""
from pathlib import Path
import hashlib
import json
import math
import xml.etree.ElementTree as ET

PREP = Path(__file__).resolve().parent
ROOT = PREP.parents[3]
PINNED = {
    'src/knowledge_tracing/akt/graph_prototype.py':'9fc6b8271da503ce16d25147a320bf0ffb9312e5416abae40fbb034f26d3157a',
    'tests/akt/test_graph_prototype.py':'17cdfe58dfdbb2e3c4eaba05f62020e3b1289e6a06a69b35b9eddca9af5e09bd',
}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
inputs = [ROOT/p for p in PINNED]
inputs += [ROOT/'docs/thesis_recovery/06_AKT_CGAKT_ARCHITECTURE_PLAN.md',
           ROOT/'src/knowledge_tracing/graph_context.py',ROOT/'src/knowledge_tracing/graph_augmentation.py',
           ROOT/'src/knowledge_tracing/akt/simulator_data.py',ROOT/'src/knowledge_tracing/akt/authorization.py',
           ROOT/'artifacts/akt/dependencies/upstream/akt.py']
for label in ('attempt01','attempt02','attempt03'):
    inputs += [PREP/label/p for p in ('receipt.json','pytest.xml','stdout.log','stderr.log','source_before.json',
                                     'graph_prototype.py','test_graph_prototype.py')]
inputs += [PREP/'attempt03/controller.py',PREP/'run_bounded_tests.py']
gate_path = ROOT/'artifacts/akt/colab/gpu09-cpu-worker-kit-20261108-01/received-linux-gate24/artifacts/akt/preflight/gate2-evidence-20261108-linux-native-24.json'
inputs.append(gate_path)
before = {p.relative_to(ROOT).as_posix():sha(p) for p in inputs}
assert all(before[k]==v for k,v in PINNED.items())
attempts=[]
for label in ('attempt01','attempt02','attempt03'):
    receipt=json.loads((PREP/label/'receipt.json').read_text(encoding='utf-8'))
    tree=ET.parse(PREP/label/'pytest.xml').getroot()
    counts={k:sum(int(n.get(k,'0')) for n in tree.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
    assert counts==receipt['counts']
    assert receipt['source_before']==receipt['source_after']
    for filename,key in [('graph_prototype.py','src/knowledge_tracing/akt/graph_prototype.py'),
                         ('test_graph_prototype.py','tests/akt/test_graph_prototype.py')]:
        assert sha(PREP/label/filename)==receipt['source_before'][key]
    attempts.append(dict(attempt=label,counts=counts,controller_seconds=receipt['controller_seconds'],
                         status=receipt['status'],source=receipt['source_before'],returncode=receipt['returncode']))
last=json.loads((PREP/'attempt03/receipt.json').read_text())
assert last['counts']==dict(tests=43,failures=0,errors=0,skipped=0)
assert len(list(ET.parse(PREP/'attempt03/pytest.xml').getroot().iter('testcase')))==43
assert last['source_before']==PINNED and last['returncode']==0 and last['child_reaped'] is True
spent=sum(a['controller_seconds'] for a in attempts)
assert math.isclose(spent,last['cumulative_seconds'],abs_tol=1e-10) and spent<=120
assert all(json.loads((PREP/a['attempt']/'receipt.json').read_text())['optimizer_steps']==0 for a in attempts)
assert 'train data changed after vocabulary fit' in (PREP/'attempt02/stdout.log').read_text()
assert 'dubious ownership' in (PREP/'attempt01/stdout.log').read_text()
gate=json.loads(gate_path.read_text())
gate_difference={key:dict(gate24=gate['build_hashes'].get(key),current=value)
                 for key,value in PINNED.items() if gate['build_hashes'].get(key)!=value}
assert len(gate_difference)==2
after = {p.relative_to(ROOT).as_posix():sha(p) for p in inputs}
assert before==after
result=dict(status='SCOPED_READ_ONLY_REVIEW_PASS',reviewer='graph_gate_prototype subagent',
    review_scope='Đọc source và kiểm lại SHA/XML/receipt; không chạy model/test/controller',
    input_sha256_before=before,input_sha256_after=after,current_source=PINNED,attempts=attempts,
    cumulative_controller_seconds=spent,cumulative_cap_seconds=120,gate24_source_difference=gate_difference,
    reviewer_test_reruns=0,reviewer_optimizer_steps=0,reviewer_cloud_calls=0,
    findings=[],resolved=['Native-control/gradient thread context thống nhất và khôi phục ambient1/2.',
    'A2/A3 phải nhận confidence caller-explicit; uniform control vẫn khai báo được.',
    'Fixture perturbation chuyển sang selection; encoding train-shard hash không bị nới.'],
    limits=['Chỉ prototype toy CPU/dropout0/forward-backward; không fit/optimizer/CG-AKT result.',
    'Confidence provenance/role là khai báo consistency, không proof estimator train-only/calibration.',
    'Gate được nối gradient nhưng chưa học bằng optimizer; gate thấp không chứng minh cạnh causal false.',
    'Cùng effective-window/OOV/global anchors; max12 chưa thực nghiệm rollover context100.',
    'Disable trả backbone cùng model; chưa có system fallback chọn checkpoint A0 độc lập.',
    'Gate24 lịch sử vẫn giữ nguyên; source hiện tại khác nên chưa là Gate24 accepted cho A2/A3.',
    'Controller chỉ chứng nhận pre/post hai target files; helper hashes trong review là hiện tại, không giả before-run certificate.',
    'Module caller-provided và SHA seal là cooperative in-process contract, không hostile-source attestation.'])
with (PREP/'peer-review-graph-agent.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
md='''# Review độc lập A2/A3 engineering — 08/11/2026

Kết luận scoped PASS: không thấy P1/P2 còn mở trong source `9fc6b827…` và tests `17cdfe58…`. Reviewer chỉ đọc mã và đối chiếu bằng chứng đã có; không chạy lại model, test, optimizer hay cloud. JSON đi kèm ghi đầy đủ SHA input trước/sau, counts từ XML và source snapshots.

Hai điểm pretest đã sửa: native control và backbone gradient dùng cùng thread context, vẫn giữ `torch.equal` và khôi phục ambient1/2; constructor A2/A3 bắt buộc confidence caller-explicit, còn uniform-control được khai báo rõ. Attempt03 có 43 tests, không failure/error/skip; stdout xác nhận 11,92 giây pytest. Controller15,340583 giây; cả ba attempt39,650895/120 giây, 0 optimizer. Attempt01 giữ lỗi Git ownership (3 pass/16 failure/24 error); attempt02 giữ41 pass/2 failure do fixture đổi train shard đã bind encoding. Final fixture dùng selection riêng để perturb và window train gốc để đối chiếu peer/padding; guard train-hash vẫn nguyên.

## Nhân quả, thông tin và arithmetic

Batch builder lấy prefix đầy đủ `observations[:rank]`, rồi dùng `prepare_graph_context`/window geometry sẵn có để giới hạn đúng effective history; OOV reset vẫn giữ global rank. Không dùng latent simulator, current answer hay future answer làm message/gate feature. Source-row, window, domain/vocab, graph, confidence/provenance và gate recipe đều nằm trong consistency binding. Cạnh concept không được coi là item index; native vẫn dùng encoding train-only thật. Toy tối đa12 events chưa chứng minh runtime rollover context100.

Message vẫn chỉ nhận mean observed correctness của parent. A2 dùng gate1; A3 nhận module trainable của caller, sigmoid scalar từ `S/(1+S)`, mean confidence, population variance confidence và observed-parent fraction. Mean/variance tính trên ALL declared parents của query, gồm parent chưa quan sát; các giá trị này không được gọi mastery/calibrated confidence. Kernel dùng `sum(c*observed*message)/max(1,mass)`, giữ absolute-confidence effect và signed residual. Test kiểm công thức signed residual riêng; backward tới backbone/message/readout/gate, weights không được optimizer cập nhật.

Disable, graph-empty, no-support và zero observed-confidence mass đi thẳng native tuple trước branch ops. Mixed inactive dùng base logits của chính forward đó; không chạy backbone lần hai để tạo control. Six-op path vẫn khớp pinned NonRasch n_pid0/separate_qaFalse. Oracle bị reject tại normal boundary ngay cả ý định disable. Estimated probability vẫn chỉ mang train-role/provenance do caller khai báo: chưa có estimator, kiểm chứng artifact fit hay calibration. Gate còn là tham số khởi tạo nối được gradient, chưa là gate đã học; gate thấp không chứng minh cạnh causal false.

## Giới hạn kết luận

Đây là software engineering toy A0–A3, không adoption S04/S05, nghiên cứu fitted CG-AKT, epoch trainer/collator hay selected checkpoint. Tắt nhánh chỉ trả backbone cùng model; không thay bằng checkpoint A0 độc lập. System checkpoint fallback vẫn chưa triển khai. SHA/dataclass binding phát hiện drift hợp tác trong process, không chống caller giả toàn metadata/module.

Hai target-file SHA hiện khác raw Gate24 build_hashes. Gate24 lịch sử không bị sửa; không được dùng PASS đó để chứng nhận source A2/A3 hiện tại. Cần refresh software evidence do parent điều phối. Controller attempt03 lưu pre/post hai target files; các helper SHA được reviewer ghi hiện tại, không tái tạo certificate trước khi test.
'''
with (PREP/'peer-review-graph-agent.md').open('x',encoding='utf-8') as f:f.write(md)
assert all(sha(ROOT/name)==value for name,value in before.items())
print(json.dumps(dict(status=result['status'],review_json_sha256=sha(PREP/'peer-review-graph-agent.json'),
                     review_md_sha256=sha(PREP/'peer-review-graph-agent.md'),input_count=len(inputs),tests=43,cumulative=spent)))
