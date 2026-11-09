"""Dựng notebook tự chứa từ aggregate đóng băng; không chạy nghiên cứu/model."""
from contextlib import redirect_stdout
from pathlib import Path
import copy,hashlib,io,json,time

ROOT=Path(__file__).resolve().parents[4];PREP=Path(__file__).resolve().parent
TARGET=ROOT/'research_tracking/supervisor_reports/2026-11-08/01_tien_do/KET_QUA_NGHIEN_CUU.ipynb'
START=time.perf_counter();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
PINS={
'rq1-fixed-edge-set-contrast-20261108-01':'906d1698482b78708cf16ce9453a8ed866e7dc0ef47cf0b8dca81c2d89b7b044',
'rq1-history-availability-20261108-02':'3fab490cc520aa5207f7483b3b33a8b031da15d2fa0c10c6da3c62252e59c5ca',
'rq2-retention-readout-separation-20261108-01':'e048a7dc87510c7fe1e5b243b4b38e4f436f01e745e61c9ce6970d5387666b01',
'cpu-rq12-20261107-03':'6592a80768e6608355cde1fd545ee90f6ca4ec937b2284a1e3eb42fae4f766f0',
'rq2-controlled-ability-prerequisite-20261108-01':'a910612fdb0b3c728a715a3f5250eb9736016fdd9e691bc8fd29cdc89a146f57',
'rq2-conditions-evidence-20261108-01':'ed31bed55099c6e360d63dee47384b366744abc2f278b89d8a009a655c7ffc61',
'development-corpus-native-20261108-01':'cbd81b65363b2d50c62fb1d145793375cb44e523410d2aea2a062ba974624c9c'}
sources={};cache={};manifests={};records=[]
canonical=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def pointer(value,path):
    for part in path.split('/')[1:]:
        part=part.replace('~1','/').replace('~0','~')
        value=value[int(part)] if isinstance(value,list) else value[part]
    return value
def take(key,run,name,ptr=''):
    base=ROOT/'research_tracking/runs'/run;mp=base/'manifest.json'
    if run not in manifests:
        raw=mp.read_bytes();assert hashlib.sha256(raw).hexdigest()==PINS[run]
        manifests[run]=json.loads(raw);assert manifests[run]['status']=='completed'
        sources[mp.relative_to(ROOT).as_posix()]={'sha256':PINS[run],'bytes':len(raw),'role':'closed_manifest'}
    path=base/name;relative=path.relative_to(ROOT).as_posix()
    if relative not in cache:
        raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
        assert digest==manifests[run]['outputs_sha256'][name]
        sources[relative]={'sha256':digest,'bytes':len(raw),'manifest':mp.relative_to(ROOT).as_posix(),'manifest_sha256':PINS[run],'manifest_pointer':'/outputs_sha256/'+name.replace('~','~0').replace('/','~1')}
        cache[relative]=json.loads(raw)
    value=pointer(cache[relative],ptr) if ptr else cache[relative]
    records.append({'id':key,'source_path':relative,'source_sha256':sources[relative]['sha256'],'json_pointer':ptr,'value':value})

F='rq1-fixed-edge-set-contrast-20261108-01';H='rq1-history-availability-20261108-02';A='rq2-controlled-ability-prerequisite-20261108-01';R='rq2-retention-readout-separation-20261108-01';J='rq2-conditions-evidence-20261108-01';C='development-corpus-native-20261108-01'
take('fixed_groups',F,'summary.json','/groups')
take('history_groups',H,'analysis__summary.json','/groups');take('history_aliases',H,'analysis__summary.json','/aliases')
for key in ('unique_targets','unique_native_target_window_pairs','native_endpoint_arms','expanded_nominal_pairs_including_aliases','summary_rows'):
    take('history_'+key,H,'analysis__summary.json','/'+key)
take('history_controls',H,'native__control_parity.json')
take('retention_linear','cpu-rq12-20261107-03','retention.json')
for state in ('A','B'):
    for phase in ('T','D14'):take('retention_'+state+'_'+phase,R,'readouts.json','/states/'+state+'/'+phase)
take('retention_orderings',R,'readouts.json','/orderings')
for key,name in [('ability_Y','native__outcomes.json'),('ability_delta','native__graph_deltas.json'),('ability_psi','native__interactions.json'),('ability_omega','native__ability_moderation.json'),('ability_summary','native__summary.json'),('ability_controls','native__high_controls.json')]:take(key,A,name)
for key in ('corrected_base','controls','common_population_sensitivity','order_unit_vi','common_unit_vi'):take('junyi_'+key,J,'conditions.json','/junyi/'+key)
for key in ('roles','canonical_files','canonical_bytes','clock','unique_source_rows','support_coverage_only_not_oof_confidence','canonical_oracle_json_parsed'):
    take('corpus_'+key,C,'input-04__independent-verification01.json','/'+key)
for key in ('status','actual_interact_attempts','actual_interact_returns','final_events','model_calls','modal_spend_usd'):
    take('corpus_'+key,C,'input-12__run.json','/'+key)
take('corpus_access_erratum',C,'input-16__structural_support01_access_erratum.json')
originals={'scripts/research/build_thesis_evidence_notebook.py':sha(ROOT/'scripts/research/build_thesis_evidence_notebook.py'),'notebooks/thesis_evidence_report.ipynb':sha(ROOT/'notebooks/thesis_evidence_report.ipynb')}
assert originals=={'scripts/research/build_thesis_evidence_notebook.py':'5f49bb44138087ebd2d783fa6d8bca7d1ec028bcc970ebde2cfd3e0500b94952','notebooks/thesis_evidence_report.ipynb':'ed1b7cad329d453d535a233ac8effdf4abf7a22d030a011962f9f04486ef090c'}
embedded={'kind':'FROZEN_AGGREGATES_NOT_RAW_EVENTS_OR_MODEL','as_of':'2026-11-08','records':records,'source_inventory':sources,'previous_repository_notebook_unchanged':originals}
raw=canonical(embedded);digest=hashlib.sha256(raw.encode()).hexdigest()
def md(s):return {'cell_type':'markdown','metadata':{},'source':s.splitlines(keepends=True)}
def code(s):return {'cell_type':'code','execution_count':None,'metadata':{},'outputs':[],'source':s.splitlines(keepends=True)}
cells=[md('''# Kết quả nghiên cứu và so sánh RQ — 08/11/2026

**Có thể mở đọc outputs ngay hoặc chọn Runtime → Run all trong Colab.** File này tự chứa các aggregate nhỏ đã kiểm nguồn; chỉ dùng Python chuẩn. Không upload repo/dataset, không network, cài thư viện, training, simulator replay, GPU hay chi phí cloud. Colab CPU là đủ.

Đây là **kết quả chẩn đoán hữu hạn**, chưa báo cáo hoàn tất RQ1/RQ2/RQ3. Các block được tái sử dụng; counts không trở thành mẫu độc lập mới, không CI/p-value. Kết quả âm được giữ.

- **RQ1:** số dự báo đổi nhiều hơn quyết định; ảnh hưởng graph/history không đồng đều.
- **RQ2:** retention phụ thuộc metric; controlled ability không cho lợi ích graph–prerequisite nhất quán dương; Junyi còn nhiễu thứ tự và mẫu số.
- **RQ3:** corpus Development đã sinh/kiểm được; **chưa có model research-fitted hoặc efficacy CG-AKT**.

Mỗi slice được nhúng cùng exact path, SHA-256 và JSON Pointer nguồn. Mở phần cuối để xem provenance. SHA embedded kiểm bytes nội bộ; Colab không tự tải lại repository để xác minh nguồn bên ngoài.
''')]
bootstrap='''import json, hashlib, math
from html import escape

EMBEDDED_JSON = __PAYLOAD__
EXPECTED_EMBEDDED_SHA256 = __DIGEST__
if hashlib.sha256(EMBEDDED_JSON.encode('utf-8')).hexdigest() != EXPECTED_EMBEDDED_SHA256:
    raise ValueError('Embedded evidence payload đã đổi')
EVIDENCE = json.loads(EMBEDDED_JSON)
D = {r['id']: r['value'] for r in EVIDENCE['records']}
assert len(D) == len(EVIDENCE['records'])

def emit(mime, text):
    capture = globals().get('_NOTEBOOK_CAPTURE')
    if capture is not None:
        capture(mime, text)
        return
    try:
        from IPython.display import HTML, SVG, display
    except ImportError:
        print(text)  # CPU stdlib fallback; không tự cài IPython.
    else:
        display(SVG(text) if mime == 'image/svg+xml' else HTML(text))

def fmt(v):
    if isinstance(v, float): return format(v, '.9g')
    if isinstance(v, (dict,list)): return json.dumps(v, ensure_ascii=False)
    return str(v)

def table(headers, rows, caption='', collapsed=False):
    text = '<div style="overflow-x:auto"><table style="border-collapse:collapse;font:14px sans-serif"><thead><tr>'
    text += ''.join('<th style="padding:7px;border:1px solid #ccd5df;text-align:left">'+escape(str(h))+'</th>' for h in headers)+'</tr></thead><tbody>'
    for row in rows:
        text += '<tr>'+''.join('<td style="padding:7px;border:1px solid #ccd5df">'+escape(fmt(v))+'</td>' for v in row)+'</tr>'
    text += '</tbody></table></div>'
    if caption: text = '<p>'+escape(caption)+'</p>'+text
    if collapsed: text='<details><summary>Mở bảng đầy đủ: '+escape(caption)+'</summary>'+text+'</details>'
    emit('text/html',text)

def source_note(*ids):
    records = [r for r in EVIDENCE['records'] if r['id'] in ids]
    table(['Slice','Đường dẫn gốc','JSON Pointer'], [(r['id'],r['source_path'],r['json_pointer'] or '(root)') for r in records], 'Nguồn của các bảng/biểu đồ phía trên', True)

def svg_open(title,desc,w=920,h=360):
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s" role="img"><title>%s</title><desc>%s</desc><rect width="100%%" height="100%%" fill="white"/><text x="25" y="28" font-size="18" font-family="sans-serif" fill="#142c46">%s</text>'%(w,h,escape(title),escape(desc),escape(title))

def signed_bars(title, labels, values, unit):
    h=110+len(labels)*58; s=svg_open(title,'Tất cả nhóm; không error bars hay CI.',920,h)
    maximum=max(abs(v) for v in values) or 1; zero=455; scale=290/maximum
    s+='<line x1="455" y1="55" x2="455" y2="%s" stroke="#718096"/>'%(h-35)
    for i,(label,v) in enumerate(zip(labels,values)):
        y=65+i*58; x=zero+min(0,v)*scale; width=abs(v)*scale
        s+='<text x="25" y="%s" font-size="14" font-family="sans-serif">%s</text><rect x="%s" y="%s" width="%s" height="24" fill="%s"/><text x="%s" y="%s" text-anchor="%s" font-size="13" font-family="monospace">%s</text>'%(y+17,escape(label),x,y,max(width,1), '#a73539' if v>0 else '#126f85',zero+v*scale+(8 if v>=0 else -8),y+17,'start' if v>=0 else 'end',format(v,'+.7g'))
    s+='<text x="25" y="%s" font-size="13" font-family="sans-serif">%s — âm: metric full thấp hơn; dương: metric full cao hơn.</text></svg>'%(h-12,escape(unit))
    emit('image/svg+xml',s)

print('Tự chứa:', len(EVIDENCE['source_inventory']), 'source/manifest files;', len(EVIDENCE['records']), 'verified pointer slices.')
print('Không chạy native/model/RNG. Không kiểm repository từ Colab; provenance đã xác minh lúc dựng file.')
'''.replace('__PAYLOAD__',repr(raw)).replace('__DIGEST__',repr(digest))
cells.append(code(bootstrap))
cells += [md('''## RQ1. Graph full so với empty trong cùng package

Đối chiếu cùng1.080query/label, từ3seed blocks×3profiles×120steps. Chỉ estimator edge set thay đổi; graph môi trường/controller giữ nguyên. Edges còn ảnh hưởng update/state: đây không là individual-edge quality hoặc direct-logit-only effect.

**Δ = full − empty.** Log Loss dùng natural log (nats/target); Brier là sai số bình phương xác suất. Âm nghĩa metric thấp hơn. Các số P/M/R/preview dưới đây có cùng mẫu số1.080, là counts song song, **không causal funnel**. Preview là lựa chọn giả định trên bản sao state, chưa là action thực sự được phục vụ.
'''),code('''fixed = D['fixed_groups']
main = [r for r in fixed if r['group'] == 'pooled' or r['group'].startswith('profile:')]
table(['Nhóm','Target pairs','ΔLog Loss','ΔBrier','Preview đổi'],[(r['group'],r['paired_snapshot_targets'],r['LL_full_minus_empty'],r['Brier_full_minus_empty'],r['full_preview_tuple_changed']) for r in main])
p = fixed[0]
table(['P đổi','M classification đổi/event','Ready set đổi/event','Full preview đổi','Mẫu số'],[(p['P_changed'],p['M_event_changed'],p['R_event_changed'],p['full_preview_tuple_changed'],p['paired_snapshot_targets'])])
table(['P đổi?','Preview đổi?','Số đếm','Mẫu số theo P'],[(r['P_changed'],r['full_preview_changed'],r['count'],r['conditional_denominator']) for r in p['P_preview_table']])
signed_bars('ΔLog Loss: pooled và từng profile', [r['group']+' (n='+str(r['paired_snapshot_targets'])+')' for r in main],[r['LL_full_minus_empty'] for r in main],'nats/target')
table(['Context','n','ΔLL','ΔBrier','Preview đổi'],[(r['group'],r['paired_snapshot_targets'],r['LL_full_minus_empty'],r['Brier_full_minus_empty'],r['full_preview_tuple_changed']) for r in fixed], 'Đủ16contexts, giữ cả9trajectories và dấu ngược', True)
print('Kết quả: pooled nhỏ và không đồng nhất profile; PG có LL/Brier cao hơn empty. Không suy graph cải thiện học tập.')
source_note('fixed_groups')
''')]
cells += [md('''## RQ1/RQ2. Giữ ít lịch sử có làm graph/decision đổi không?

27cached targets tạiHpast10/50/100; last10/last50/full là lịch sử **toàn policy, gồm controller bookkeeping**. 54full-prefix controls khớp exactP/S28/M/R/full-preview trước truncated phase.108fresh arms,54unique target–window pairs;81nominal rows có aliases, không là81đối tượng mới.

Trong cùngH, query/y/time giữ nguyên. GiữaH khác nhau, target/label khác nhau: không đọc đường biểu đồ giữaH như causal history-length effect. Full preview khác served action. Không teacher/NNoptimizer hoặc independent seed mới trong replay.
'''),code('''history = D['history_groups']; pooled=[r for r in history if r['context']=='pooled']
control=D['history_controls']
table(['Targets','Unique target-window pairs','Native arms','Exact full-prefix controls','Nominal alias pairs'],[(D['history_unique_targets'],D['history_unique_native_target_window_pairs'],D['history_native_endpoint_arms'],control['arms'],D['history_expanded_nominal_pairs_including_aliases'])])
headers=['H','Nominal k','Actual L','n','Δp','ΔLLgraph','ΔBriergraph','Graph preview đổi','Window preview full E','Window preview empty E']
def histrow(r):return (r['Hpast'],r['nominal_window'],r['available_length'],r['same_target_pairs'],r['mean_graph_delta_p'],r['mean_graph_delta_LL'],r['mean_graph_delta_Brier'],r['graph_full_preview_changed'],r['full_arm_preview_vs_full_history_changed'],r['empty_arm_preview_vs_full_history_changed'])
table(headers,[histrow(r) for r in pooled], 'Pooled; giữ aliases rõ ràng, không pool chúng thành mẫu mới')
profiles=[r for r in history if r['context'].startswith('profile:')]
table(['Profile']+headers,[(r['context'],)+histrow(r) for r in profiles], 'Cả3profiles; n=3target pairs/cell', True)
# Ba panels táchH; chỉ vẽ mỗi actual L một lần để tránh aliases thành repeated evidence.
selected=[]
for H in (10,50,100):
    bylength={}
    for r in pooled:
        if r['Hpast']==H:bylength[r['available_length']]=r
    selected.append((H,[bylength[L] for L in sorted(bylength)]))
ymin=min(r['mean_graph_delta_LL'] for _,rs in selected for r in rs); ymax=max(r['mean_graph_delta_LL'] for _,rs in selected for r in rs)
pad=(ymax-ymin)*.18 or .001; ymin-=pad;ymax+=pad
s=svg_open('ΔLog Loss graph theo available history — tách từng targetH','Mỗi panel có target riêng. Không CI. Alias không vẽ lặp.',920,360)
for panel,(H,rs) in enumerate(selected):
    x0=70+panel*300; y=lambda v:285-(v-ymin)/(ymax-ymin)*220
    s+='<text x="%s" y="62" font-size="15" font-family="sans-serif">H=%s, n=9/cell</text>'%(x0,H)
    s+='<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="#aaa"/>'%(x0,y(0),x0+225,y(0))
    points=[]
    for i,r in enumerate(rs):
        x=x0+30+i*80; yy=y(r['mean_graph_delta_LL']);points.append('%s,%s'%(x,yy))
        s+='<circle cx="%s" cy="%s" r="5" fill="#126f85"/><text x="%s" y="%s" text-anchor="middle" font-size="12" font-family="monospace">%s</text><text x="%s" y="310" text-anchor="middle" font-size="13" font-family="sans-serif">L=%s</text>'%(x,yy,x,yy-12,format(r['mean_graph_delta_LL'],'.5g'),x,r['available_length'])
    s+='<polyline points="%s" fill="none" stroke="#126f85" stroke-width="1.5"/>'%' '.join(points)
s+='<text x="25" y="345" font-size="13" font-family="sans-serif">Đơn vị nats/target; cùng y-scale. Không nối cácH khác target. Không đường CI/p-value.</text></svg>'
emit('image/svg+xml',s)
table(['Context']+headers,[(r['context'],)+histrow(r) for r in history], 'Đủ144cells; không loại nhóm âm hoặc aliases', True)
print('H100/L50: graph preview đổi2/9 so full-history0/9. Window đổi preview6–8/9 ở cảhai arms.')
print('ΔLLgraph không đơn điệu theoL. PYH H100 có window−full LL âm: không kết luận full history luôn tốt hơn.')
source_note('history_groups','history_aliases','history_controls')
''')]
cells += [md('''## RQ2. Retention: metric nào dư thừa, metric nào có thể đổi thứ hạng?

Với no-practice sauT, decay đồng nhất0,06/ngày và nonnegative gain, retained **net mean-theta gain** sau14ngày là một hệ số cố định nhân final gain. Không suy practice-order trướcT vô nghĩa.

Soft-mastery là readout phi tuyến: phản ví dụ hai state28chiều dựng sẵn có thể đảo thứ tự A/B. **Không chứng minh state reachable từ persona/policy; không phải trajectory hoặc graph benefit.** Native soft readout chưa là calibrated latent mastery.
'''),code('''linear=D['retention_linear']
table(['Decay/ngày','Retention days','Hệ số net gain','Sai số fixture'],[(linear['true_forget_rate'],linear['retention_days'],linear['scaling_factor'],linear['absolute_error'])])
readouts=[(state,phase,D['retention_'+state+'_'+phase]) for state in ('A','B') for phase in ('T','D14')]
table(['Constructed state','Time','Mean theta net gain/Elo','Soft-mastery gain','Hard-mastered concepts'],[(a,t,r['mean_theta_gain'],r['native_soft_mastery_gain'],r['native_hard_mastery_count']) for a,t,r in readouts])
s=svg_open('Soft-mastery gain: phản ví dụ readout, không trajectory','Chỉ hai time readouts của states dựng sẵn; không native simulation.',920,350)
top=max(r['native_soft_mastery_gain'] for _,_,r in readouts)*1.2
for state,color in (('A','#126f85'),('B','#a73539')):
    points=[]
    for i,t in enumerate(('T','D14')):
        v=D['retention_'+state+'_'+t]['native_soft_mastery_gain'];x=220+i*400;y=285-v/top*220;points.append('%s,%s'%(x,y))
        s+='<circle cx="%s" cy="%s" r="5" fill="%s"/><text x="%s" y="%s" font-size="14" font-family="monospace" fill="%s">%s: %s</text>'%(x,y,color,x+12,y,color,state,format(v,'.7g'))
    s+='<polyline points="%s" fill="none" stroke="%s" stroke-width="2"/>'%(' '.join(points),color)
s+='<text x="220" y="310" font-size="14" font-family="sans-serif">T</text><text x="620" y="310" font-size="14" font-family="sans-serif">T+14ngày</text><text x="25" y="340" font-size="13" font-family="sans-serif">Đơn vị probability/readout points; hai endpoints, không ước lượng đường học hoặc CI.</text></svg>'
emit('image/svg+xml',s)
print('Soft B>A tạiT nhưng A>B sau14ngày. Net mean-theta vẫn B>A. Hard: tie→A>B, không strict reversal.')
source_note('retention_linear','retention_A_T','retention_A_D14','retention_B_T','retention_B_D14')
''')]
cells += [md('''## RQ2. Controlled ability × prerequisite penalty

36worlds =3reused blocks×3ability scalars×2estimator edge sets×2world penalties,4.320actual interactions. Giữ centered residual28chiều và U step-index chung; S/P bật, local-adaptation tắt. Model initialization1200; G environment/controller giữ full.

Y là **net theta gain trung bình28concepts tạiT41ngày (điểm Elo)**. Δ(a,λ)=Yfull−Yempty; Ψ(a)=Δ(a,0,55)−Δ(a,0); Ω=chênhΨ giữa hai ability scalars. MeanΨ nhỏ không đồng nghĩa ý nghĩa thực tiễn. ÂmΔ là ít gain hơn empty, không mặc định học thụt lùi dưới base.

Đây là finite conditional simulator potential-outcome contrasts, không observational DiD hay general causal ability effect. Actions/exposures/labels có thể phân kỳ dù U ghép theo step. HighΨ0 **design-known** vì deficit luôn0; không là discovery rằng người giỏi không cần graph.
'''),code('''ys=D['ability_Y']; keyed={(r['seed'],int(r['profile'][1:]),r['graph_on'],r['prerequisite_mechanism_on']):r['outcome'] for r in ys}
psis=D['ability_psi']; deltas=D['ability_delta']
table(['a','Ψ21000','Ψ21001','Ψ21002','Mean3blocks'],[(a,)+tuple(next(r['interaction_contrast'] for r in psis if r['seed']==b and r['profile']=='A'+str(a)) for b in (21000,21001,21002))+(D['ability_summary']['abilities'][str(a)]['mean_interaction'],) for a in (1000,1150,1300)])
rows=[]
for b in (21000,21001,21002):
    for a in (1000,1150,1300):
        delta=lambda m:next(r['graph_delta'] for r in deltas if r['block']==b and r['ability']==a and r['mechanism_strength']==m)
        psi=next(r['interaction_contrast'] for r in psis if r['seed']==b and r['profile']=='A'+str(a))
        rows.append((b,a,keyed[(b,a,True,False)],keyed[(b,a,False,False)],keyed[(b,a,True,True)],keyed[(b,a,False,True)],delta(0),delta(.55),psi))
table(['Block','a','Y fullλ0','Y emptyλ0','Y fullλ.55','Y emptyλ.55','Δλ0','Δλ.55','Ψ'],rows,'Đủ36Y/18Δ/9Ψ: không bỏ block âm',True)
s=svg_open('Ψ theo ability: cả3block, đơn vị Elo net trung bình28concepts','Không CI, không independentN mới; high0 là known negative.',920,360)
values=[r['interaction_contrast'] for r in psis]; lo=min(values)-.01;hi=max(values)+.01;y=lambda v:285-(v-lo)/(hi-lo)*215
s+='<line x1="85" y1="%s" x2="835" y2="%s" stroke="#aaa"/>'%(y(0),y(0))
colors=['#126f85','#a73539','#70519b']
for i,a in enumerate((1000,1150,1300)):
    for j,b in enumerate((21000,21001,21002)):
        v=next(r['interaction_contrast'] for r in psis if r['seed']==b and r['profile']=='A'+str(a));x=200+i*280+(j-1)*12
        s+='<circle cx="%s" cy="%s" r="5" fill="%s"/><text x="%s" y="%s" font-size="11" font-family="monospace">%s</text>'%(x,y(v),colors[j],x+8,y(v)+(j-1)*15,format(v,'+.6g'))
    s+='<text x="%s" y="310" text-anchor="middle" font-size="14" font-family="sans-serif">a=%s</text>'%(200+i*280,a)
for j,b in enumerate((21000,21001,21002)):
    s+='<text x="%s" y="55" font-size="13" font-family="sans-serif" fill="%s">Block%s</text>'%(100+j*260,colors[j],b)
s+='<text x="25" y="345" font-size="13" font-family="sans-serif">Vị trí x lệch nhẹ chỉ để thấy điểm trùng; không jitter dữ liệu hoặc precision claim.</text></svg>'
emit('image/svg+xml',s)
table(['Block','a thấp','a cao','Ω/Elo'],[(r['block'],r['ability_low'],r['ability_high'],r['interaction_difference']) for r in D['ability_omega']], 'Đủ6ability-moderation contrasts',True)
table(['Block','High a','Δgraph tại λ0'],[(r['block'],r['ability'],r['graph_delta']) for r in deltas if r['ability']==1300 and r['mechanism_strength']==0], 'HighΨ0 nhưng graphΔλ0 vẫn dương cả3blocks')
print('a1000: Ψ +/−/+; a1150: −/−/− nhỏ. Sáuλ-pairs high khớp720events và6finalstates; knownD0.')
print('Không quy mọi graph advantage cho true prerequisite mechanism; residual/controller/challenge/update paths còn lại.')
source_note('ability_Y','ability_delta','ability_psi','ability_omega','ability_summary','ability_controls')
''')]
cells += [md('''## RQ2. Junyi: thứ tự quan sát và mẫu số có thể đổi dấu

Đây là cached **order-only observational analysis** trên Development inner-train, không mở raw learner/Holdout hoặc correctness trong notebook này. Control thay20/976edges,40changed entries tính cả removed+added. Co-observation khác global endpoint coverage.

Pair-weighted alignment, fixed learner-weighted và common-coobserved dùng mẫu số/quần thể khác nhau. Không xếp chất lượng graph hoặc instructional benefit từ pooled order score. Common subsets mất nhiều coverage; zero không chứng minh equivalence.
'''),code('''controls=D['junyi_controls']; common=D['junyi_common_population_sensitivity']; base=D['junyi_corrected_base']
table(['Graph','Parent-first pairs','Co-observed pairs','Pair-weighted rate'],[('Corrected base',base['parent_first_pairs'],base['coobserved_edge_learner_pairs'],base['pair_weighted_parent_first_fraction'])]+[('Control'+str(r['seed']),r['control']['parent_first_pairs'],r['control']['coobserved_edge_learner_pairs'],r['control']['pair_weighted_parent_first_fraction']) for r in controls])
table(['Control','Removed edges','Symmetric-diff entries','Changed entries same-learner co-observed','Δpair-rate','Δfixed-learner prior','Δcommon prior','Common learners/eligible'],[(r['seed'],r['removed']['edges'],r['symmetric_difference_entries'],r['changed_entries_coobserved_same_learner'],r['delta_pair_weighted_fraction'],c['all_fixed']['categories']['observed_prior_fraction']['delta_control_minus_base'],c['common_coobserved']['categories']['observed_prior_fraction']['delta_control_minus_base'],str(c['common_coobserved']['learners'])+'/'+str(c['eligible_learners'])) for r,c in zip(controls,common)])
print('Control2: parent-first count−1, denominator−4 → pooled rate tăng; fixed-learner contrast âm, common0.')
print('Các estimands khác nhau, không arithmetic contradiction hoặc causal graph benefit. Không bootstrap/CI từ aggregate means.')
source_note('junyi_corrected_base','junyi_controls','junyi_common_population_sensitivity')
''')]
cells += [md('''## RQ3. Đầu vào đã có; hiệu quả mô hình chưa được chứng minh

Corpus Development đã thực sinh/publish và được typed public reader đọc lại:48train/6selection/6calibration,210events/người. Logging policy uniform-items; profiles chỉ phục vụ collection/audit, không là model features. Final150learners mới ở metadata, **không final events**.

Support/coverage là điều kiện dữ liệu, không learned graph, confidence OOF, response calibration hoặc CG-AKT efficacy. Actual corpus closure được xác nhận bởi manifest đã pin; câu “dự kiến” trong report snapshot preclosure không đảo actual manifest status.
'''),code('''roles=D['corpus_roles']
table(['Role','Learners','Events','Label0','Label1','Covered items'],[(role,r['learners'],r['events'],r['class_counts']['0'],r['class_counts']['1'],r['covered_items']) for role,r in roles.items()])
table(['Actual attempts','Actual returns','Final events','Model calls','Modal USD','Canonical files','Canonical bytes'],[(D['corpus_actual_interact_attempts'],D['corpus_actual_interact_returns'],D['corpus_final_events'],D['corpus_model_calls'],D['corpus_modal_spend_usd'],D['corpus_canonical_files'],D['corpus_canonical_bytes'])])
table(['Coverage condition','Value'],list(D['corpus_support_coverage_only_not_oof_confidence'].items()))
print('Đã đạt: corpus/source/role/readback/cleanup. Chưa đạt: research-fitted NN, epoch-selection/refit/calibration, confidenceOOF, final evaluation.')
print('Notebook chỉ nhúng aggregate QA; không mở9model-input files hoặc7oracle files. QA lịch sử hashoracle opaque, không parse; access erratum giữ nguyên.')
source_note('corpus_roles','corpus_support_coverage_only_not_oof_confidence','corpus_actual_interact_attempts','corpus_status','corpus_access_erratum')
''')]
cells += [md('''## Kết luận được phép và hồ sơ nguồn

| Câu hỏi | Kết luận hiện có | Chưa thể nói |
|---|---|---|
|RQ1|Dự báo đổi chưa chắc preview đổi; graph/history response không đồng đều.|Graph làm người học tiến bộ, causal mediation hoặc edge truth.|
|RQ2|Metric retention khác nhau; ability×mechanism có dấu âm/known-null; Junyi nhạy mẫu số/coverage.|Population ability law, practice-order causal benefit hoặc RQcomplete.|
|RQ3|Có corpus Development đã kiểm.|CG-AKT vượt baseline hoặc đã fitted/calibrated research model.|

Nguồn dưới là đường dẫn repository gốc. Notebook tự chứa và **không phụ thuộc các file đó khi RunAll**. SHA/pointers đã xác minh lúc dựng: không tự fetch GitHub trong Colab. Embedded digest chỉ phát hiện nội dung nhúng đổi so với pin của file này, không chữ ký hay independent source authentication.

Notebook báo cáo cũ ở `notebooks/thesis_evidence_report.ipynb` được giữ nguyên. Phiên bản này không cập nhật C01–C14, không sửa notebook/world lịch sử hoặc làm phát sinh observations.
'''),code('''table(['Slice ID','Source path','SHA-256','JSON Pointer'],[(r['id'],r['source_path'],r['source_sha256'],r['json_pointer'] or '(root)') for r in EVIDENCE['records']], 'Toàn bộ numeric slices và exactJSONPointers',True)
table(['Source/manifest','SHA-256','Bytes'],[(path,r['sha256'],r['bytes']) for path,r in EVIDENCE['source_inventory'].items()], 'Source inventory đã kiểm khi dựng',True)
print('Embedded payload SHA-256:',EXPECTED_EMBEDDED_SHA256)
print('RunAll chỉ render lại bảng/SVG từ giá trị đã lưu. Không fit/replay/teacher/newN/CI/p-value.')
''')]
def execute(cells):
    ns={};count=0
    for i,c in enumerate(cells):
        c['id']='gvhd-results-%02d'%i
        if c['cell_type']!='code':continue
        count+=1;outputs=[];stream=io.StringIO()
        ns['_NOTEBOOK_CAPTURE']=lambda mime,text:outputs.append({'output_type':'display_data','data':{mime:text},'metadata':{}})
        with redirect_stdout(stream):exec(compile(''.join(c['source']),'<GVHD stdlib cell%d>'%i,'exec'),ns)
        if stream.getvalue():outputs.append({'output_type':'stream','name':'stdout','text':stream.getvalue()})
        c.update(execution_count=count,outputs=outputs)
    return count
assert not TARGET.exists(),'new notebook exclusive'
before={p:sha(ROOT/p) for p in sources}
executable=execute(cells)
replayed=copy.deepcopy(cells);assert execute(replayed)==executable
assert [c.get('outputs') for c in replayed]==[c.get('outputs') for c in cells],'deterministic cached output verification'
assert before=={p:sha(ROOT/p) for p in sources}
assert originals=={p:sha(ROOT/p) for p in originals}
notebook={'nbformat':4,'nbformat_minor':5,'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3 (CPU stdlib)','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.10+'},'colab':{'provenance':[]},'kltn':{'role':'self_contained_frozen_research_diagnostics_not_RQcompletion','embedded_sha256':digest,'source_files':len(sources),'pointer_slices':len(records),'network_install_training_gpu_calls':0,'execution_scope':'local stdlib cell execution; not actual Colab or Jupyter-kernel QA'}}}
TARGET.parent.mkdir(parents=True,exist_ok=True)
payload=(json.dumps(notebook,ensure_ascii=False,indent=1,allow_nan=False)+'\n').encode()
with TARGET.open('xb') as f:f.write(payload)
assert json.loads(TARGET.read_bytes())==notebook
inventory={'source_inventory':sources,'records':[{k:v for k,v in r.items() if k!='value'} for r in records],'embedded_sha256':digest,'previous_notebook_builder_hashes_unchanged':originals,'new_notebook':TARGET.relative_to(ROOT).as_posix(),'new_notebook_sha256':sha(TARGET),'builder_sha256':sha(Path(__file__)),'no_circular_inventory':'input catalogue contains closed source aggregates/manifests only; no generated notebook/builder/report as input'}
with (PREP/'supervisor_research_notebook_sources01.json').open('x',encoding='utf-8') as f:json.dump(inventory,f,ensure_ascii=False,indent=2);f.write('\n')
receipt={'status':'BUILT_AND_EXECUTED_STDLIB_CELLS_TWICE_IDENTICAL_OUTPUTS','notebook':TARGET.relative_to(ROOT).as_posix(),'notebook_sha256':sha(TARGET),'notebook_bytes':len(payload),'builder_sha256':sha(Path(__file__)),'source_inventory_sha256':sha(PREP/'supervisor_research_notebook_sources01.json'),'source_files':len(sources),'manifest_count':len(PINS),'pointer_slices':len(records),'cells':len(cells),'executable_cells':executable,'execution_passes':2,'svg_outputs':sum('image/svg+xml' in o.get('data',{}) for c in cells for o in c.get('outputs',[])),'elapsed_seconds':time.perf_counter()-START,'source_before_after_unchanged':True,'root_notebook_builder_unchanged':originals,'native_model_rng_teacher_network_install_gpu_calls':0,'limitations':['No actual Colab/Jupyter kernel/visual QA yet','Embedded SHA checks internal payload; external sources verified locally at build, not fetched remotely','Finite diagnostics only, no newN/CI/pvalues/fitted model efficacy/RQ completion']}
with (PREP/'supervisor_research_notebook_build01.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(receipt,ensure_ascii=False))
