"""Mở rộng notebook quy trình từ cached outputs; không chạy nghiên cứu gốc."""
from pathlib import Path
import ast
import copy
import hashlib
import io
import json
import math
import time
from contextlib import redirect_stdout

ROOT=Path(__file__).resolve().parents[4];PREP=Path(__file__).resolve().parent
TARGET=ROOT/'research_tracking/supervisor_reports/2026-11-08/01_tien_do/KET_QUA_NGHIEN_CUU.ipynb'
BEFORE=PREP/'supervisor_notebook_before_process02.ipynb'
OLD_SHA='0f2130aba7b04a187b31ac9c0fd9d4b81df290ced470e5aa04bbf92625267620'
START=time.perf_counter()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
canonical=lambda value:json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
assert sha(BEFORE)==sha(TARGET)==OLD_SHA
old=json.loads(BEFORE.read_bytes());bootstrap=''.join(old['cells'][1]['source'])
tree=ast.parse(bootstrap)
literal=next(node.value for node in tree.body if isinstance(node,ast.Assign)
             and any(isinstance(t,ast.Name) and t.id=='EMBEDDED_JSON' for t in node.targets))
evidence=json.loads(ast.literal_eval(literal));sources=evidence['source_inventory'];records=evidence['records']
old_records=copy.deepcopy(records);old_sources=copy.deepcopy(sources)
for path,row in sources.items():assert sha(ROOT/path)==row['sha256'],path
PINS={path.split('/')[2]:row['sha256'] for path,row in sources.items() if path.endswith('/manifest.json')}
PINS.update({
'rq1-score-vector-20261108-01':'8553154474091bf3ee4e0e072c45b7421a1381a2b9d8887eeb36283a0d66e481',
'rq1-query-observability-reproduction-20261108-01':'112cd15f69b63fec730a4b4a67acf98650986adc58138f68ef4a5105adbf81d7',
'rq1-closed-loop-reconstruction-20261108-02':'c8bd8f387e5101fca641098257dd5a99d67d2f838cefc3b53b7d9d55248bcb16',
'paper1-revision-audit-20261107-01':'04eae39f87842fb43b892b8d0d9fa5606e998e278979ba85be8487c3535371c6'})
cache={};manifest={}


def pointer(value, path):
    for part in path.split('/')[1:]:
        part=part.replace('~1','/').replace('~0','~')
        value=value[int(part)] if isinstance(value,list) else value[part]
    return value


def register(run,name,role='experiment_artifact'):
    base=ROOT/'research_tracking/runs'/run;mp=base/'manifest.json'
    if run not in manifest:
        assert sha(mp)==PINS[run]
        manifest[run]=json.loads(mp.read_bytes());assert manifest[run]['status']=='completed'
        sources[mp.relative_to(ROOT).as_posix()]=dict(sha256=PINS[run],bytes=mp.stat().st_size,role='closed_manifest')
    path=base/name;relative=path.relative_to(ROOT).as_posix();digest=sha(path)
    assert digest==manifest[run]['outputs_sha256'][name],relative
    sources[relative]=dict(sha256=digest,bytes=path.stat().st_size,role=role,
        manifest=mp.relative_to(ROOT).as_posix(),manifest_sha256=PINS[run],
        manifest_pointer='/outputs_sha256/'+name.replace('~','~0').replace('/','~1'))
    return relative,path


def take(key,run,name,ptr=''):
    relative,path=register(run,name)
    value=cache.setdefault(relative,json.loads(path.read_bytes()))
    records.append(dict(id=key,source_path=relative,source_sha256=sources[relative]['sha256'],
                        json_pointer=ptr,value=pointer(value,ptr) if ptr else value))


F='rq1-fixed-edge-set-contrast-20261108-01';H='rq1-history-availability-20261108-02'
A='rq2-controlled-ability-prerequisite-20261108-01';R='rq2-retention-readout-separation-20261108-01'
J='rq2-conditions-evidence-20261108-01';C='development-corpus-native-20261108-01'
Q='rq1-query-observability-reproduction-20261108-01';B='rq1-closed-loop-reconstruction-20261108-02'
take('historical_score_groups','rq1-score-vector-20261108-01','analysis.json','/groups')
take('query_reproduction_parity',Q,'parity.json')
take('closedloop_ranking',B,'posthoc__ranking_candidate.json')
take('closedloop_closure',B,'closure_review.json')
take('chapter_counterexample','cpu-rq12-20261107-03','paper1_counterexample.json')
take('paper1_revision_verdict','paper1-revision-audit-20261107-01','paper1_revision_reconciliation_20261107.json','/verdict')
take('retention_negative_controls',R,'readouts.json','/negative_controls')
take('retention_base',R,'readouts.json','/base')
take('fixed_analysis_command',F,'run.json','/command')
take('fixed_analysis_unchanged',F,'run.json','/source_input_unchanged')
take('history_worker_args',H,'native__dispatch.json','/worker_args')
take('history_worker_status',H,'native__run.json','/status')
take('history_model_update_scope',H,'native__run.json','/native_state_updates_are_model_calls')
take('ability_proposed_cli',A,'proposed_cli.json','/argv')
take('ability_actual_status',A,'native__run.json','/status')
take('ability_actual_calls',A,'native__run.json','/direct_attempts')
take('retention_command',R,'run.json','/command')
take('corpus_config',C,'input-03__simulator-research-corpus01.json')
take('corpus_native_clock',C,'input-12__run.json','/clock') if 'clock' in json.loads((ROOT/'research_tracking/runs'/C/'input-12__run.json').read_bytes()) else None
for run,names in {
 F:['plan.json','analyze_full_empty_fixed.py','run.json','execution.log'],
 H:['source__history_availability_plan02.json','source__history_availability_worker02.py','native__run.json','native__owned-launch__stdout.log','analysis__recipe.md','analysis__analyzer.py'],
 R:['plan.json','analyze_readouts.py','source_excerpts.json','stdout.log','run.json'],
 A:['plan.json','worker.py','verify_saved_results.py','independent_verification01.json','native__run.json','native__owned-launch__stdout.log'],
 J:['analysis_source.py','execution.log'],
 C:['input-06__run_native01.py','input-12__run.json','input-04__independent-verification01.json'],
 Q:['source__run_reproduction.py'] if (ROOT/'research_tracking/runs'/Q/'source__run_reproduction.py').exists() else ['attempt01__source__run_reproduction.py'],
 B:['current_candidate_runner.py','prep__closed_loop_native_source_snapshot.json','closure_review.json'],
 'paper1-revision-audit-20261107-01':['paper1_source_cells.txt','audit_verification.log']
}.items():
    for name in names:register(run,name,'frozen_protocol_code_receipt_or_log')
evidence['kind']='SELF_CONTAINED_EXPERIMENT_PROCESS_AND_CACHED_RESULTS_NOT_REEXECUTION'
evidence['preserved_previous_notebook_sha256']=OLD_SHA
evidence['run_all_scope']='Cached arithmetic/tables/SVG only; no original experimental execution, network, install, train, teacher or GPU'
assert records[:len(old_records)]==old_records
raw=canonical(evidence);digest=hashlib.sha256(raw.encode()).hexdigest()
lines=bootstrap.splitlines(keepends=True)
for node in reversed(tree.body):
    if isinstance(node,ast.Assign):
        names=[t.id for t in node.targets if isinstance(t,ast.Name)]
        if 'EMBEDDED_JSON' in names:lines[node.lineno-1:node.end_lineno]=['EMBEDDED_JSON = '+repr(raw)+'\n']
        if 'EXPECTED_EMBEDDED_SHA256' in names:lines[node.lineno-1:node.end_lineno]=['EXPECTED_EMBEDDED_SHA256 = '+repr(digest)+'\n']
bootstrap=''.join(lines)


def md(text):return dict(cell_type='markdown',metadata={},source=text.splitlines(keepends=True))
def code(text):return dict(cell_type='code',metadata={},execution_count=None,outputs=[],source=text.splitlines(keepends=True))
def link(run,name,label):return f'[{label}](../../../../research_tracking/runs/{run}/{name})'
def process(title,kind,question,contrast,fixed,changed,steps,checks,allowed,limits,artifacts):
    return md(f'''## {title}

**Loại bằng chứng:** {kind}

**Câu hỏi/giả thuyết được kiểm:** {question}

| Thiết kế | Nội dung |
|---|---|
| Treatment/control | {contrast} |
| Giữ cố định | {fixed} |
| Chủ động thay đổi | {changed} |

**Quá trình thí nghiệm gốc — không phải các cell Run All:**
{steps}

**Kiểm tính hợp lệ:** {checks}

**Được phép kết luận:** {allowed}

**Giới hạn/chưa xử lý:** {limits}

**Mở protocol, code, receipt/log trong checkout:** {' · '.join(artifacts)}. Các link không được tải khi Run All; nếu chỉ mở file riêng trên Colab, dùng paths/SHA/pointers ở cuối để tra repository.
''')


cells=[md('''# Quá trình thí nghiệm và bằng chứng nghiên cứu KLTN
Ngày08/11/2026 · đọc cùng [báo cáo tiến độ](BAO_CAO.md)

**File tự chứa, Colab CPU đủ:** có outputs để đọc ngay; `Runtime → Run all` chỉ nạp số liệu nhúng đã ghim, kiểm số học và vẽ bảng/SVG. **Không chạy lại thí nghiệm gốc**, không cần repo/dataset, không network/install/teacher/model/training/GPU. Chạy lại bảng không tạo thí nghiệm hoặc mẫu độc lập mới. Local đã kiểm stdlib cellcode; chưa kiểm giao diện/runtime Colab thật.

Mỗi nhánh bên dưới trả lời: hỏi gì; can thiệp/control nào; giữ/đổi gì; thực hiện theo bước nào; kiểm sai lệch ra sao; đã thấy gì; được/chưa được kết luận gì. MãK1–K6 khớp báo cáo ngắn. “Đầy đủ quá trình” ở đây là thiết kế, nguồn và bằng chứng thực thi được lưu, **không khẳng định đã tái lập toàn nghiên cứu hoặc tất cả mô hình đề cương**.

| Nhánh | Bằng chứng gốc | Đơn vị và kết luận còn giới hạn |
|---|---|---|
|K1: prediction/decision|Reanalysis fixed stream, reproduction observer; giải thích ranking hậu nghiệm|3reused seed blocks; preview≠served action; không causal funnel|
|K2: available history|Controlled native replay trên cached targets|27targets; thay whole-policy history, chưa KT-only memory|
|K3: chapter/retention traps|Source counterexample và arithmetic/readout diagnostic|Không PDF reproduction; constructed states chưa reachable|
|K4: ability/prerequisite|New finite controlled simulator contrasts|36worlds nhưng3reused blocks, không36independent learners|
|K5: Junyi order|Logged-order/graph-control observational diagnostics|Coverage/denominator nhạy; không instructional causal benefit|
|K6: nền RQ3|Actual role-aware corpus collection/publication|60learners/12.600events; chưa fittedCG-AKT efficacy|

Luôn tách **P** của current/served query, **S28/native B-score** chưa calibrated mastery, **M** boolean, **R** membership và **A** preview/served theo từng thiết kế. Không vẽ các counts song song thành funnel lồng nhau. Các kết quả âm và không kết luận được được giữ; chưa RQ nào hoàn tất.
'''),code(bootstrap)]

cells.append(process('K1a — Dự báo đổi có đồng nghĩa quyết định đổi?',
 'Cached descriptive reanalysis + observer reproduction; C14 là post-hoc source-local explanation.',
 'Kiểm sự không tương ứng một-một giữa P/S/M/R và preview; sau đó quan sát actual query/full preview và key ranking ở common prefix.',
 'Full package−graph-free; empty-enabled package−graph-free là negative control riêng.',
 'Fixed logged query/history trong nhánh fixed-stream;3seed20000–20002×PG/PY/PYH×120steps; toàn bộ groups được giữ.',
 'Estimator package; empty vẫn có local nonedge branches. Closed-loop sau divergence không còn cùng histories/items/labels.',
 '1. Ghép legacy keys/labels; tính riêng event flags và concept×event flags.\n2. Reproduction có control và observer, ghi query arguments trước predict và full preview trên policy copy; không backfill metadata vào trace cũ.\n3. Nhánh closed-loop source-local ghi đủ native B-score keys, replay exact min trên B; so first served-tuple break chỉ khi common-before context còn giống.',
 'C13 exact legacy parity và1.080logical shared queries; C14 replay3.240/3.240ranking events. C14 raw candidate có chữ pending tại snapshot; closure review parent-reviewed giữ riêng. P-same không là full-state-same.',
 'Thay đổi scalarP có thể cùng preview giữ; source-local ranking giải thích CID component tại first break.',
 'C01–C14 không chứng minh mediator causal chain, calibrated mastery, learning benefit hay individual-edge truth. C14 không replay choose_question; không ghépΔP sau divergence.',
 [link(Q,'parity.json','query/parity'),link(Q,'attempt01__source__run_reproduction.py','reproduction code'),link(B,'current_candidate_runner.py','closed-loop code'),link(B,'prep__closed_loop_native_source_snapshot.json','source/call order'),link(B,'closure_review.json','closure review')]))
cells.append(code('''historical=[r for r in D['historical_score_groups'] if r['scope']=='pooled']
table(['So graph-free','Event pairs','P đổi','S28 snapshot đổi','M đổi','R đổi','Concept preview đổi'],[(r['candidate'],r['paired_events'],r['p_changed_events'],r['s_changed_events'],r['m_changed_events'],r['r_changed_events'],r['a_changed_events']) for r in historical])
q=D['query_reproduction_parity']
table(['C13 logical keys','Variant rows','Preview served?','Backfilled historical metadata?'],[(q['logical_event_keys'],q['variant_rows'],q['preview_is_served'],q['historical_metadata_backfilled'])])
rank=D['closedloop_ranking']; rows=[]
for candidate in ('graph_package','empty_graph_package'):
    cases=[r for r in rank['comparisons'] if r['candidate']==candidate]
    same=sum(r['first_prefix_break'] is not None and all(r['first_prefix_break']['same_membership_sets'].values()) for r in cases)
    none=sum(r['first_prefix_break'] is None for r in cases)
    rows.append((candidate,len(cases),same,len(cases)-same-none,none))
table(['C14 so graph-free','Comparisons','First break cùngM/R/C/B','Membership khác','Không break120steps'],rows)
print('Native closed-loop: select(B-score/ties) → served-query predict(P) → environment.interact → update(y,P).')
print('P của served item được tính SAU select, không gây ra chính same-step select. P có thể ảnh hưởng update/state tương lai.')
print('Empty package:37Pchanges nhưng0previewchanges; package≠edges. C14 post-hoc giải thích CID, không causal mediation.')
source_note('historical_score_groups','query_reproduction_parity','closedloop_ranking','closedloop_closure')
'''))

cells.append(process('K1b — Tách cạnh khỏi toàn package: full–empty',
 'Cached reanalysis trên source/observability đã tái lập; new independentN=0.',
 'Khi cùng package được bật, việc thay edge set full/empty đi kèm thay đổi raw loss và preview như thế nào?',
 'Enabled full Graph-GAM so enabled empty Graph-GAM; không lấy graph-free làm empty.',
 'Actual1.080query/y/time; fixed prior records; item features, parameters và initial state; fullG_env/G_controller.',
 'Estimator edge set; edges có downstream state/update effects, không chỉ direct logit.',
 '1. Freeze analysis plan/source SHA.\n2. Join toàn bộ keys/query/y, không intersection/drop rows.\n3. Tính LLclip1e−15/Brier, P/S/M/R/full-preview flags và từng profile/seed/trajectory.\n4. Kiểm baseline cancellation full−GF=(full−empty)+(empty−GF) trên cùng rows.',
 'All1.080keys;36legacyLL/Brier checks và16groups; source/input SHA trước=sau; không threshold search/CI/p-value.',
 'Pooled rawLL/Brier có thể thấp hơn empty nhưng không đồng đều profile; PG xấu hơn cả3trajectories.',
 'ScalarP current query khác toàn vectorS28;22preview changes không là22learning improvements. Counts song song không nested funnel.',
 [link(F,'plan.json','analysis plan'),link(F,'analyze_full_empty_fixed.py','analysis code'),link(F,'run.json','actual command/receipt'),link(F,'summary.json','all numeric groups')]))
cells.append(copy.deepcopy(old['cells'][3]))
cells.append(code("table(['Actual cached-analysis argv (readonly provenance)'],[(json.dumps(D['fixed_analysis_command'],ensure_ascii=False),)])\nprint('Source/input unchanged:',D['fixed_analysis_unchanged'])\n"))

cells.append(process('K2 — Can thiệp lịch sử toàn policy',
 'Controlled native replay, không teacher outcome mới; các native GAM state updates vẫn là model calls.',
 'Trên CÙNG target, last10/last50/full available records làm graph contrast/preview đổi ra sao?',
 'Full và empty estimator tại cùngH; mỗi arm còn có window−full-history control.',
 '27cached targets tạiHpast10/50/100; currentquery/y/time; RNG không draw; G_env/G_controller source giữ nguyên.',
 'History cấp cho cả estimator và controller visits/question counts/recent/chapter; L=min(k,H).',
 '1. Pin cached legacy/query sidecars và worker/plan.\n2. Dựng54full-prefix controls, so exactP/S28/M/R/full-preview TRƯỚC truncated phase.\n3. Replay retained prior records bằng native predict→cachedy→update và literal bookkeeping.\n4. Probe target/preview readonly; lưu108arm endpoints/54unique target-window pairs.\n5. Analysis freeze trước effect estimates; giữ144cells và81nominal aliases, không pool alias thành samples.',
 'Full-prefix parity54/54; unchanged input SHA/counters; owned cleanup accepted. Full-prefix endpoint parity không chứng minh mọi hidden state snapshot giống lịch sử.',
 'Graph/history response không đơn điệu trong các targets đã chọn; rút history có thể đổi preview cảhai arms.',
 'Không KT-only memory intervention, không learning/ability effect. H khác nhau là target/y khác nhau; không soH10→H100 như cùngtarget. Preview chưa served;0independentseed mới.',
 [link(H,'source__history_availability_plan02.json','native plan'),link(H,'source__history_availability_worker02.py','native worker'),link(H,'native__control_parity.json','control checks'),link(H,'native__run.json','actual receipt'),link(H,'native__owned-launch__stdout.log','native stdout'),link(H,'analysis__recipe.md','analysis recipe'),link(H,'analysis__analyzer.py','cached analyzer')]))
cells.append(copy.deepcopy(old['cells'][5]))
cells.append(code("table(['Worker arguments from actual dispatch record'],[(json.dumps(D['history_worker_args'],ensure_ascii=False),)])\nprint('Actual status:',D['history_worker_status'],'; native state updates count as model calls:',D['history_model_update_scope'])\n"))

cells.append(process('K3a — Chapter continuity có phải bảo đảm của controller?',
 'Source-level counterexample trên revision hiện có; không exact Paper1 PDF reproduction.',
 'Một selector có bảo đảm không quay lại chapter trên mọi graph hay không?',
 'Hai chiến lược lowest_elo/cross_chapter_unlock trên cùng synthetic DAG và scripted mastery transitions.',
 'Source selector/cell/notebook hash, đồ thị/kịch bản mastery; không chọn nhiều seeds để tìm route đẹp.',
 'Chiến lược controller; mastery transitions là ngoại sinh dựng sẵn, không quỹ đạo học sinh thật.',
 '1. Reconcile notebook/PDF/source/manifest trong phạm vi local đã audit.\n2. Dùng selector revision hiện có trên DAG nhỏ với mastery script đã khai báo.\n3. Ghi concept/chapter route và re-entry.\n4. Tách kết luận counterexample khỏi khả năng tái lập bảng của PDF.',
 'Artifact giữ notebookSHA/selectorSHA/cell và route; audit không tìm exact submitted source+inputs+outputs trong phạm vi đã tìm, không chứng minh bản đúng không tồn tại nơi khác.',
 'A→B→A là counterexample cho bảo đảm phổ quát zero-reentry của revision đang xét.',
 'Không kết luận PDF sai, graph vô dụng hoặc route này xảy ra dưới mọi learner/policy; chưa giải quyết source revision gốc.',
 [link('cpu-rq12-20261107-03','paper1_counterexample.json','actual counterexample'),link('paper1-revision-audit-20261107-01','paper1_source_cells.txt','selector source excerpts'),link('paper1-revision-audit-20261107-01','paper1_revision_reconciliation_20261107.json','revision audit'),link('paper1-revision-audit-20261107-01','audit_verification.log','audit log')]))
cells.append(code('''chapter=D['chapter_counterexample']
table(['Selector','Concept route','Chapter route','Re-entry'],[(name,' → '.join(r['concepts']),' → '.join(r['chapters']),r['chapter_reentries']) for name,r in chapter['routes'].items()])
print('Source counterexample status:',chapter['status'],'; revision audit:',D['paper1_revision_verdict'])
s=svg_open('Counterexample controller: A → B → A','Synthetic DAG và scripted mastery, không learning trajectory.',920,210)
for i,label in enumerate(('A1 / chươngA','B1 / chươngB','A2 / chươngA (re-entry)')):
    x=30+i*300;s+='<rect x="%s" y="80" width="270" height="55" rx="8" fill="#e8f2f5"/><text x="%s" y="113" text-anchor="middle" font-family="sans-serif" font-size="14">%s</text>'%(x,x+135,escape(label))
    if i<2:s+='<text x="%s" y="113" font-size="24">→</text>'%(x+275)
s+='<text x="25" y="180" font-family="sans-serif" font-size="13">Cảhai selectors córoute này trong constructed test; không là ước lượng xác suất re-entry.</text></svg>';emit('image/svg+xml',s)
source_note('chapter_counterexample','paper1_revision_verdict')
'''))

cells.append(process('K3b — Retention tuyến tính và soft-mastery phi tuyến',
 'Arithmetic source diagnostic + fixed constructed-state counterexample; không native trajectory/model execution.',
 'Retention14 có luôn chỉ lặp lại ranking final gain? Điều đó phụ thuộc readout nào?',
 'Hai trạng tháiA/B cùng28base, đọc tạiT vàT+14; scalar net theta gain so soft/hard mastery readouts.',
 'Fixedbase; nonnegative gain; no practice sauT; decay0.06/ngày; cùng hàm response/mastery nguồn.',
 'Cách phân bố gain của2states dựng sẵn và metric readout, không thay dynamics.',
 '1. Đối chiếu AST/source equations và C08 cũ.\n2. Suy c=exp(−0.06×14) cho net-theta gain.\n3. Tính các readouts ở hai states đã chốt; không state search/tuning sau quan sát.\n4. Kiểm zero-gain/identical-state/threshold và linear residual; ghi full28dimensions trong rawreadouts.',
 'Linear residual<1e−12; oldC08 không đổi; source hash trước=sau; không thực thi native functions. Hard readout chỉ tie→A>B, không strict reversal.',
 'Retained net-theta redundant với final net-theta trong điều kiện này; soft readout có thể đảo ranking.',
 'Constructed states chưa chứng minh reachable từ persona/policy; không graph benefit, latent calibrated mastery hoặc độc lập thống kê của endpoints.',
 [link(R,'plan.json','fixed plan'),link(R,'analyze_readouts.py','arithmetic code'),link(R,'source_excerpts.json','equation source'),link(R,'run.json','actual command/receipt'),link(R,'stdout.log','stdout'),link(R,'readouts.json','states/readouts/negative controls')]))
cells.append(copy.deepcopy(old['cells'][7]))
cells.append(code("table(['Negative control','Stored result'],list(D['retention_negative_controls'].items()))\ntable(['Actual arithmetic argv'],[(json.dumps(D['retention_command'],ensure_ascii=False),)])\n"))

cells.append(process('K4 — Scalar ability × prerequisite mechanism',
 'New finite controlled simulator experiment; không population/human causal study.',
 'Giữ residual để hỏi thay scalar ability/λ có luôn làm graph-relative gain tăng không?',
 '3blocks21000–21002×a1000/1150/1300×full/empty estimator×λ0/0.55 =36worlds.',
 'Mỗi block chung centered residual28chiều và U[120,2] theo step; model init1200; parent signal/adaptation bật, local adaptation tắt; fullG_env/G_controller.',
 'Ability scalar, estimator edge set, hệ số penalty world; residual gốc còn graph correlation.',
 '1. Freeze protocol/36-cell plan trướcnative.\n2. Generate chung một PYanchor/block, center/bound residual60 và freeze U bytes/SHA trước world đầu.\n3. Thực hiện highλ paired controls theo thiết kế; giữ counters/cell reservations.\n4. Native select→predict served→interact→update; chạy toàn36worlds/4320events.\n5. Tính36Y/18Δ/9Ψ/6Ω và đọc raw độc lập bằng cached verifier, giữ mọi dấu.',
 'Same residual/U provenance;6highλ-pairs exact720pairedpositions+6final states;4320reserved=attempted=returned; source/copy hashes; parent independent raw verifier. Telemetry không hard OSquota.',
 'Ψ không nhất quán dương; highΨ0 design-knownD0 nhưng graphΔ tạiλ0 vẫn dương, nên graph advantage không chỉ là penalty.',
 '3reused blocks không36independent learners. U ghép theo step, không cùng question/y sau divergence; không pairedΔP trên khácquery, noCI/p-value/ability-population law.',
 [link(A,'plan.json','36cell plan'),link(A,'worker.py','native code'),link(A,'proposed_cli.json','prepared CLI—not sole execution proof'),link(A,'native__run.json','actual counters/receipt'),link(A,'native__owned-launch__stdout.log','native stdout'),link(A,'verify_saved_results.py','readonly verifier'),link(A,'independent_verification01.json','verification receipt')]))
cells.append(copy.deepcopy(old['cells'][9]))
cells.append(code("table(['Actual operation','Count'],list(D['ability_actual_calls'].items()))\nprint('Actual acceptance:',D['ability_actual_status'])\ntable(['Prepared CLI (historical proposal; actualreceipt/counters separately shown)'],[(json.dumps(D['ability_proposed_cli'],ensure_ascii=False),)])\n"))

cells.append(process('K5 — Junyi: order confounding và denominator sensitivity',
 'Observed logged-order/graph-controls + cached common-population reanalysis; không causal sequencing study.',
 'Graph khớp thứ tự luyện đã ghi có được hiểu như prerequisite/learning benefit không?',
 'Corrected976edge graph so3controls:20removed+20added=40symmetric-difference entries; raw979edge reference giữ riêng.',
 'Stored Development inner-train cohort256learners/12,575events;≤300events/learner; timestamp/source-row order; degree/topic/support constraints.',
 'Parent sets ở controls và estimand/denominator: pair-weighted vs fixed learner-weighted vs common-coobserved subsets.',
 '1. Chốt cohort/graph corrections và controls; source analysis không dùng Holdout để chọn.\n2. Đo first-exposure parent-first alignment trên co-observed edge–learner pairs.\n3. Kiểm bao nhiêu changed entries thực sự co-observed trong cùng learner.\n4. Giữ cùng learner–child opportunities, dùng incomingdegree làm denominator, childmean rồi equal learnerweight.\n5. Báo common-coobserved attrition và sensitivity; không pool các denominator thành cùngquầnthể.',
 'Stored source/control/common-population SHA checked; exact aggregate denominators và sign examples được giữ. Common subset cần ít nhất1parent co-observed trong MỖI graph, không nhất thiết cùngparent.',
 'Dấu contrast phụ thuộc population/weights; order association có thể lẫn exposure và logged policy.',
 'Chỉ cachedaggregates trongnotebook, không mở raw Junyi/correctness/Holdout. Matching không bảo đảm co-observation; zero commoncontrast không equivalence; không causal instructional benefit.',
 [link(J,'analysis_source.py','cached analysis code'),link(J,'conditions.json','denominators/controls'),link(J,'manifest.json','selected input hashes'),link(J,'execution.log','archive log—not original experiment trace')]))
cells.append(copy.deepcopy(old['cells'][11]))
cells.append(code('''rows=[(str(r['seed']),r['symmetric_difference_entries'],r['changed_entries_coobserved_same_learner']) for r in D['junyi_controls']]
table(['Control','Changed entries','Actually co-observed entries'],rows)
s=svg_open('Junyi controls: thay cạnh không đồng nghĩa có exposure','Không rate chất lượng cạnh; mẫu số changed entries40/control.',920,290)
for i,(name,total,exposed) in enumerate(rows):
    y=70+i*60;s+='<text x="25" y="%s" font-family="sans-serif" font-size="14">Control%s</text><rect x="180" y="%s" width="600" height="24" fill="#e1e6eb"/><rect x="180" y="%s" width="%s" height="24" fill="#126f85"/><text x="795" y="%s" font-family="monospace" font-size="14">%s/%s</text>'%(y+18,name,y,y,600*exposed/total,y+18,exposed,total)
s+='<text x="25" y="275" font-family="sans-serif" font-size="13">Đây là coverage diagnostic, không xác suất prerequisite đúng hoặc effectsize dạy học.</text></svg>';emit('image/svg+xml',s)
'''))

cells.append(process('K6 — Corpus Development cho pipeline RQ3',
 'Actual data collection/publication/typed-reader engineering; chưa fitted CG-AKT research result.',
 'Có thể tạo một corpus observable role-aware đủ84items để sau này train/selection/refit/calibration đúnglineage không?',
 'Không contrast model ở batch này;48train/6selection/6calibration,210events/người;150final IDs chỉmetadata.',
 'Pinned Paper2rawsource/graph/bank; rootseed42; profiles role-local16/2/2 mỗiPG/PY/PYH; UTC/gap6h; cùngrecipe qua roles.',
 'Fresh role/learner namespaces; logging uniform84items bằng behavior RNG riêng, không selector theo mastery/oracle.',
 '1. Freeze plan/profile/caps/source/runtime và ownedprocess approval.\n2. Collect chỉtrain/selection/calibration, durableattempt/return counters; no finalevents.\n3. Serialize9publicinputs +oracle sidecars tách riêng, SHA/readback rồiDONElast.\n4. Sharedreader chỉ mở9public+DONE, reconstruct typedplan/provenance, kiểmcounts/clock/rows/classes/support.\n5. Independentcached QA và opaquehash inventory; không promote support thànhconfidence/modelquality.',
 'Actual12,600attempts=returns;60learners disjoint,84items/role,2classes/role; source trước=sau/ownedcleanup accepted. HistoricalQA đã hashoracle opaque: giữaccesserratum, không giảneveropenedbytes.',
 'Đã có dữ liệu để nối researchpipeline; train coverage/strict-prior pair support là structural opportunity.',
 'Uniformlogging khônggraph-freeworld: teacher dynamics vẫncóG_env. ChưaNNfitted/refit/calibration/confidenceOOF/CG-AKT efficacy hoặc finaleval. Corpus support không chứng minh learner diversity.',
 [link(C,'input-03__simulator-research-corpus01.json','frozen collection config'),link(C,'input-06__run_native01.py','actual driver'),link(C,'input-12__run.json','actual counts/receipt'),link(C,'input-04__independent-verification01.json','public roundtrip QA'),link(C,'input-16__structural_support01_access_erratum.json','access erratum')]))
cells.append(copy.deepcopy(old['cells'][13]))
cells.append(md('''## Đọc kết quả nào, còn thiếu gì?

K1–K5 là các chẩn đoán có nguồn và đối chứng, không thay bộ so sánh fitted modern models. K6 mới cung cấp dữ liệu. AKT/CG-AKT research-fitted, confidence OOF, main matrix selector trướcrefit, full-target calibration/evaluation và kết quả closed-loop với mô hình đó vẫn phải nghiệm thu riêng. Không gọi source/stub tests hoặc điểm AUC/LL của5hàng manufactured evaluator là kết quả AKT; không dùng các lượt Gate-partition thiếu finalJUnit/result như PASS.

Các protocol/code/log links cho phép kiểm tra quá trình, nhưng không mang dataset/checkpoint/rawlearners vào file. Một số `execution.log` chỉ log đóng gói; native receipt/stdout được ghi riêng trong từng mục, không dùng log đóng gói làm proof nativeexecution. NguồnPaper1PDF khớp vẫnchưa tìm; rawC14statuspending là snapshot trướcclosureparentreview, không bị sửa lại.

**Chạy lại nghiên cứu gốc** còn cần đúng source/input/runtime/config/authorization/resource receipts và từng originalworker, không phải chỉ RunAll notebook. **RunAll ở đây** chỉ xác minh số học trên cachedslices và dựng lại output; không notebookkernel/Colabvisual acceptance, causal human efficacy, statistical confirmation hoặc RQcompletion.
'''))
cells.append(code('''# Kiểm số học cached, không simulation/replay/inference mới.
pool=D['fixed_groups'][0]
assert pool['P_changed']==963 and pool['paired_snapshot_targets']==1080
assert sum(r['count'] for r in pool['P_preview_table'])==1080
assert sum(r['count'] for r in pool['P_preview_table'] if r['full_preview_changed'])==22
assert D['history_controls']['arms']==54 and D['history_native_endpoint_arms']==108
assert D['chapter_counterexample']['routes']['lowest_elo']['chapter_reentries']==1
assert abs(D['retention_linear']['scaling_factor']-math.exp(-.06*14))<1e-12
for r in D['ability_psi']:
    a=int(r['profile'][1:]);b=r['seed']
    y=lambda g,m:next(q['outcome'] for q in D['ability_Y'] if q['seed']==b and q['profile']==r['profile'] and q['graph_on']==g and q['prerequisite_mechanism_on']==m)
    computed=(y(True,True)-y(False,True))-(y(True,False)-y(False,False))
    assert abs(computed-r['interaction_contrast'])<1e-12
for a in (1000,1150,1300):
    values=[r['interaction_contrast'] for r in D['ability_psi'] if r['profile']=='A'+str(a)]
    assert abs(math.fsum(values)/len(values)-D['ability_summary']['abilities'][str(a)]['mean_interaction'])<1e-12
assert sum(r['events'] for r in D['corpus_roles'].values())==12600
assert sum(r['learners'] for r in D['corpus_roles'].values())==60
assert D['corpus_final_events']==0
print('Cached arithmetic/denominator checks PASS; không additional independentN/model/teacher/CI/p-value.')
'''))
cells.append(md('''## Hồ sơ đầy đủ để tra cứu nguồn

Mỗi numeric slice dưới có JSON Pointer, fileSHA và manifestSHA xác nhận selectedoutput khi dựng. Source inventory còn liệt kê protocol/code/receipt/log được dẫn; không có dữ liệu bí mật, Holdout hoặc checkpoint trongpayload. SHAembedded chỉ kiểm internalconsistency, không chữ ký hay sourceauthentication độc lập; file tựchứa không fetchrepo trênColab. Bản notebook trước0f2130…7620 được giữ nguyên ở externalprep; không sửa C01–C14/notebook nghiên cứu lịch sử.
'''))
cells.append(copy.deepcopy(old['cells'][15]))

# Mọi cells được chạy là cached/stdlibrary only. Không exec source artifacts.
allowed_imports={'json','hashlib','math','html','IPython.display'}
for cell in cells:
    if cell['cell_type']!='code':continue
    for node in ast.walk(ast.parse(''.join(cell['source']))):
        if isinstance(node,ast.Import):assert all(a.name in allowed_imports for a in node.names)
        if isinstance(node,ast.ImportFrom):assert node.module in allowed_imports
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):assert node.func.id not in {'open','exec','eval','compile','__import__'}


def execute(items):
    ns={};count=0
    for i,cell in enumerate(items):
        cell['id']='process-evidence-%02d'%i
        if cell['cell_type']!='code':continue
        count+=1;outputs=[];out=io.StringIO()
        ns['_NOTEBOOK_CAPTURE']=lambda mime,text:outputs.append(dict(output_type='display_data',data={mime:text},metadata={}))
        with redirect_stdout(out):exec(compile(''.join(cell['source']),'<cached-process-cell%d>'%i,'exec'),ns)
        if out.getvalue():outputs.append(dict(output_type='stream',name='stdout',text=out.getvalue()))
        cell.update(execution_count=count,outputs=outputs)
    return count


before={path:sha(ROOT/path) for path in sources}
executed=execute(cells);replay=copy.deepcopy(cells);assert execute(replay)==executed
assert [c.get('outputs') for c in cells]==[c.get('outputs') for c in replay]
assert before=={path:sha(ROOT/path) for path in sources}
assert sha(TARGET)==sha(BEFORE)==OLD_SHA
notebook=dict(nbformat=4,nbformat_minor=5,cells=cells,metadata=dict(
    kernelspec=dict(display_name='Python 3 (CPU stdlib)',language='python',name='python3'),
    language_info=dict(name='python',version='3.10+'),colab=dict(provenance=[]),
    kltn=dict(role='self_contained_experimental_process_and_evidence_not_full_reproduction',
        embedded_sha256=digest,source_files=len(sources),pointer_slices=len(records),
        original_notebook_sha256=OLD_SHA,network_install_training_gpu_calls=0,
        execution_scope='Local cached stdlib cells twice; not actual Colab/Jupyter/visual QA')))
payload=(json.dumps(notebook,ensure_ascii=False,indent=1,allow_nan=False)+'\n').encode()
candidate=PREP/'supervisor_process02_candidate.ipynb'
with candidate.open('xb') as stream:stream.write(payload)
assert json.loads(candidate.read_bytes())==notebook
with TARGET.open('wb') as stream:stream.write(payload)
assert sha(TARGET)==sha(candidate) and json.loads(TARGET.read_bytes())==notebook
receipt=dict(status='CACHED_PROCESS_NOTEBOOK_BUILT_AND_REPLAYED_TWICE_IDENTICAL',
    notebook=TARGET.relative_to(ROOT).as_posix(),notebook_sha256=sha(TARGET),notebook_bytes=len(payload),
    builder_sha256=sha(Path(__file__)),preserved_old_notebook_sha256=OLD_SHA,
    source_files=len(sources),pointer_slices=len(records),cells=len(cells),code_cells=executed,
    svg_outputs=sum('image/svg+xml' in o.get('data',{}) for c in cells for o in c.get('outputs',[])),
    original_numeric_records_preserved=len(old_records),selected_sources_before=before,
    selected_sources_after={path:sha(ROOT/path) for path in sources},
    original_experiment_execution=False,model_teacher_training_network_gpu_calls=0,
    elapsed_seconds=time.perf_counter()-START,
    limits=['Cached arithmetic/render only; not original research rerun','No actual Colab/Jupyter/visual QA',
            'C01-C14 and original research sources unchanged','No current Gate/NNfit/effectiveness/RQcompletion claim'])
with (PREP/'supervisor_process_notebook02_validation.json').open('x',encoding='utf-8') as stream:
    json.dump(receipt,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({key:value for key,value in receipt.items() if key not in ('selected_sources_before','selected_sources_after')},ensure_ascii=False))
