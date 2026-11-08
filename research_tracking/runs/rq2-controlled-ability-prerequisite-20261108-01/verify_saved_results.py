"""Kiểm dữ liệu đã lưu bằng stdlib; không import/chạy simulator hoặc RNG."""
import ast
import hashlib
import json
import math
import struct
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
RAW = PREP / 'attempt01'
START = time.perf_counter()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
canonical = lambda v: json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
digest = lambda v: hashlib.sha256(canonical(v).encode()).hexdigest()
read = lambda name: json.loads((RAW / name).read_bytes())
rows = lambda name: [json.loads(x) for x in (RAW / name).read_bytes().splitlines()]
checks = 0
def check(ok, why):
    global checks
    checks += 1
    if not ok: raise AssertionError(why)
def close(a,b): return math.isclose(a,b,rel_tol=0,abs_tol=1e-12)

raw_before = {p.relative_to(RAW).as_posix(): sha(p) for p in RAW.rglob('*') if p.is_file()}
run, worker, plan = read('run.json'), read('worker_run.json'), json.loads((PREP/'plan.json').read_bytes())
check(sha(RAW/'run.json') == '2042b5e30b2b124767458e603287f2002c289124a3af1016179f3de01f3389e1', 'root actual run pin')
check(run['error'] is None and run['status']=='ACCEPTED_FINITE_CONTROLLED_ABILITY_PREREQUISITE_EXPERIMENT', 'accepted original')
check(0<run['elapsed_seconds']<=run['max_cumulative_seconds']==60, 'original elapsed')
bindings=run['source_input_before_sha256']
check(len(bindings)==25 and bindings==run['source_input_after_sha256']==worker['source_input_before_sha256']==worker['source_input_after_sha256'], 'all25 source bindings')
check(all(sha(ROOT/n)==d for n,d in bindings.items()), 'current exact source/input bytes')
for receipt in (run,worker):
    for name,d in receipt['outputs_sha256'].items(): check(sha(RAW/name)==d, 'output '+name)
check(worker['completed_cells']==36 and worker['reserved_interact_attempts']==4320 and worker['high_negative_pairs']==6, 'complete population')
check(run['direct_attempts']==worker['direct_attempts']==worker['direct_returns']==plan['direct_call_caps'], 'all direct counts')
owned=read('owned_launch_receipt.json')
check(owned['accepted'] and owned['cleanup_accepted'] and owned['actual_worker_in_job_before_GO'] and owned['job_active_after_cleanup']==0 and owned['popen_handle_closed'] and not owned['cleanup_errors'] and owned['returncode']==0, 'owned process cleanup')
check(worker['nn_optimizer_calls']==run['nn_optimizer_calls']==0 and run['new_independent_seed_blocks']==0, 'no NN optimizer/new blocks')
limits=plan['resource_limits']
for sample in worker['memory_events']:
    check(max(sample['process_rss_bytes'],sample['process_peak_rss_bytes'] or 0)<=limits['max_rss_bytes'] and sample['system_available_ram_bytes']>=limits['min_available_ram_bytes'], 'all memory samples')

shared=read('shared_inputs.json'); nodes=shared['node_order']; check(len(nodes)==28 and len(set(nodes))==28,'node order')
blocks={x['block']:x for x in shared['blocks']}; check(set(blocks)=={21000,21001,21002},'reused blocks')
historical=json.loads((ROOT/plan['historical_outcomes']).read_bytes())
for block,b in blocks.items():
    old=[r for r in historical if r['seed']==block and r['profile']=='PY']
    anchor_sha=hashlib.sha256(json.dumps(b['anchor'],sort_keys=True).encode()).hexdigest()
    check(anchor_sha==b['source_anchor_sha256'] and len(old)==4 and {r['latent_identity'] for r in old}=={anchor_sha},'old anchor binding')
    check(close(sum(b['anchor'][c] for c in nodes)/28,b['anchor_mean']), 'anchor mean arithmetic')
    z={c:b['anchor'][c]-b['anchor_mean'] for c in nodes}
    check(z==b['centered_before_scaling'], 'centered raw')
    scale=max(1.,max(abs(v) for v in z.values())); check(scale==b['centering_denominator'],'residual scale')
    residual={c:60.*(z[c]/scale) for c in nodes}
    check(residual==b['centered_residual'] and digest(residual)==b['residual_sha256'], 'residual identity')
    check(abs(math.fsum(residual.values())/28)<=1e-10 and max(map(abs,residual.values()))<=60,'centered bounded residual')
    for a in (1000,1150,1300):
        base={c:a+residual[c] for c in nodes}
        check(base==b['bases'][str(a)] and digest(base)==b['base_sha256'][str(a)] and all(850<=v<=1500 for v in base.values()),'same residual bases')
    check(b['uniform_dtype']=='float64' and b['uniform_shape']==[120,2] and len(b['uniforms'])==120,'U geometry')
    flat=[v for pair in b['uniforms'] for v in pair]
    check(len(flat)==240 and all(0<=v<1 for v in flat),'U bounds')
    ush=hashlib.sha256(struct.pack(('<' if sys.byteorder=='little' else '>')+'240d',*flat)).hexdigest()
    check(ush==b['uniform_sha256'] and {r['random_stream_identity'] for r in old}=={ush},'exact cached native float64 U bytes, no RNG')

cells=plan['cells']; check(len(cells)==36 and len({(c['block'],c['ability'],c['graph'],c['mechanism_strength']) for c in cells})==36,'full36 factorial')
check(all(c['ability']==1300 and c['phase']=='high_negative' for c in cells[:12]) and all(c['phase']=='main' for c in cells[12:]),'six negatives before main source order')
ledger=rows('cell_ledger.jsonl'); check(len(ledger)==72,'all durable reserve/terminal rows')
obs=rows('observables.jsonl'); oracle=rows('oracle.jsonl'); endpoints=rows('oracle_endpoints.jsonl')
check(len(obs)==len(oracle)==4320 and len(endpoints)==36,'complete traces')
obsby={(r['cell_id'],r['step']):r for r in obs}; orby={(r['cell_id'],r['step']):r for r in oracle}; endby={r['cell_id']:r for r in endpoints}
check(len(obsby)==len(orby)==4320 and len(endby)==36,'unique event and cell identities')
outcomes=read('outcomes.json'); check(len(outcomes)==36,'all36 outcomes')
source=ast.parse((PREP/'worker.py').read_text())
calls=[n for n in ast.walk(source) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='call']
line={n.args[0].value:n.lineno for n in calls if n.args and isinstance(n.args[0],ast.Constant)}
check(line['select']<line['predict']<line['oracle_theta_probe']<line['oracle_probability_probe']<line['interact']<line['update'],'source chronological call sites')
update=next(n for n in calls if isinstance(n.args[0],ast.Constant) and n.args[0].value=='update')
check(isinstance(update.args[-1],ast.Name) and update.args[-1].id=='prediction','update receives model p, not oracle')
nb=json.loads((ROOT/next(n for n in bindings if n.endswith('.ipynb'))).read_bytes())
constants={}
for cell in nb['cells']:
    if cell['cell_type']=='code':
        for n in ast.parse(''.join(cell['source'])).body:
            if isinstance(n,ast.Assign) and isinstance(n.value,ast.Constant):
                for target in n.targets:
                    if isinstance(target,ast.Name):constants[target.id]=n.value.value
check(constants['TRUE_GAIN_SCALE']==12. and constants['TRUE_FORGET_RATE']==.06 and constants['PREREQUISITE_READY_ELO']==1150.,'pinned native constants')
start_ns=1767225600000000000; final_ns=start_ns+41*86400*10**9
table=[]; coverage=[]; Y={}
for i,c in enumerate(cells):
    cid=c['cell_id']; b=blocks[c['block']]; base=b['bases'][str(c['ability'])]
    reserve,terminal=ledger[2*i:2*i+2]
    check(reserve['event']=='RESERVED_BEFORE_CELL_WORLD_WORK' and reserve['cell']==c and reserve['actual_attempts'] is None and reserve['interact_reservation']==120 and reserve['cumulative_reserved']==(i+1)*120,'durable upfront full cell reservation')
    check(terminal['event']=='COMPLETED_CELL' and terminal['cell_id']==cid and terminal['actual_interact_attempts']==terminal['actual_interact_returns']==120 and terminal['cumulative_direct_attempts']==terminal['cumulative_direct_returns'],'terminal real counts')
    check(reserve['base_sha256']==b['base_sha256'][str(c['ability'])] and reserve['residual_sha256']==b['residual_sha256'] and reserve['uniform_sha256']==b['uniform_sha256'],'cell uses same coupled inputs')
    deficits=caps=0
    for step in range(120):
        o,q=obsby[(cid,step)],orby[(cid,step)]; r=q['result']
        check(set(o)=={'cell_id','step','query','probability','correct'} and set(o['query'])=={'concept','question','difficulty','timestamp_iso','timestamp_ns'},'opaque observable no oracle/ability/condition features')
        check(o['query']['timestamp_ns']==start_ns+(step+1)*21600*10**9+(step//28)*237600*10**9,'clock sequence')
        check([q['outcome_uniform'],q['learning_uniform']]==b['uniforms'][step], 'step coupled U exact')
        p=1./(1.+10.**((o['query']['difficulty']-q['oracle_theta_before'])/400.))
        check(p==q['oracle_probability']==r['p_true'] and q['oracle_theta_before']==r['theta_before'],'oracle probability arithmetic')
        check(o['correct']==r['y']==int(q['outcome_uniform']<p) and 0<=o['probability']<=1,'observed label and bounded model p')
        challenge=math.exp(-.5*((p-.65)/.22)**2)
        gain=12.*challenge*(1.15 if r['y']==0 else .85)*(1.+.20*min(r['gap_days'],7.)/7.)*(1.-c['mechanism_strength']*r['prerequisite_deficit'])*(.85+.30*q['learning_uniform'])
        check(challenge==r['challenge_match'] and gain==r['learning_gain'],'logged scalar learning equation')
        check(q['ceiling_hit']==(r['theta_before']+gain>=1600.),'cap flag')
        if c['ability']==1300:check(r['prerequisite_deficit']==0 and r['prereq_violation']==0,'high known D0')
        deficits+=int(r['prerequisite_deficit']>0); caps+=q['ceiling_hit']
    e=endby[cid]; check(e['timestamp_ns']==final_ns and set(e['final_snapshot'])==set(nodes),'all28 sameT41days')
    check(e['base_sha256']==b['base_sha256'][str(c['ability'])] and terminal['final_environment_sha256']==digest(e['final_environment_state']) and terminal['final_policy_sha256']==e['final_policy_state_sha256'],'endpoint bindings')
    for concept in nodes:
        state=e['final_environment_state']; v=float.fromhex(state['theta'][concept]['float_hex']); bs=float.fromhex(state['base'][concept]['float_hex']); last=state['last_seen'][concept]
        expected=v if last is None else bs+max(0.,v-bs)*math.exp(-.06*((final_ns-last['ns'])/86400/10**9))
        check(expected==e['final_snapshot'][concept] and bs==base[concept],'endpoint closed-form readout from stored state only')
    y=math.fsum(e['final_snapshot'][n]-base[n] for n in nodes)/28
    check(close(y,e['net_mean_theta_gain']) and close(y,outcomes[i]['outcome']) and terminal['outcome']==outcomes[i], 'all36 Y recomputation')
    check(deficits==terminal['positive_deficit_events'] and caps==terminal['ceiling_hit_events'],'logged coverage counts')
    Y[(c['block'],c['ability'],c['graph'],c['mechanism_strength'])]=outcomes[i]['outcome']
    coverage.append({'cell_id':cid,'positive_deficit_events':deficits,'ceiling_hit_events':caps})

high=read('high_controls.json'); check(len(high['pairs'])==6 and high['design_known_not_discovery'],'all six controls')
for pair in high['pairs']:
    a,b=pair['lambda0_cell'],pair['lambda55_cell']; sem=[]
    for step in range(120):
        values=[]
        for cellid in (a,b):
            o,q=obsby[(cellid,step)],orby[(cellid,step)]
            values.append({'step':step,'query':o['query'],'probability':o['probability'],'correct':o['correct'],'oracle_probability':q['oracle_probability'],'theta_before':q['oracle_theta_before'],'U':[q['outcome_uniform'],q['learning_uniform']],'result':q['result'],'readonly_state_sha256':q['environment_readonly_probe_sha256']})
        check(values[0]==values[1],'all720 high semantic event pairs exact')
        sem.append(canonical(values[0]))
    check(hashlib.sha256('\n'.join(sem).encode()).hexdigest()==pair['trace_sha256'],'high trace digest')
    check({k:v for k,v in endby[a].items() if k!='cell_id'}=={k:v for k,v in endby[b].items() if k!='cell_id'},'all six high final-state records exact')

deltas=read('graph_deltas.json'); interactions=read('interactions.json'); moderation=read('ability_moderation.json')
check((len(deltas),len(interactions),len(moderation))==(18,9,6),'all contrast populations')
D={};P={}
for block in plan['blocks']:
    for ability in plan['ability_levels']:
        d0=Y[(block,ability,'full',0.)]-Y[(block,ability,'empty',0.)]
        d1=Y[(block,ability,'full',.55)]-Y[(block,ability,'empty',.55)]
        psi=d1-d0;P[(block,ability)]=psi;D[(block,ability,0.)]=d0;D[(block,ability,.55)]=d1
        table.append({'block':block,'ability':ability,'Y_full0':Y[(block,ability,'full',0.)],'Y_empty0':Y[(block,ability,'empty',0.)],'Y_full55':Y[(block,ability,'full',.55)],'Y_empty55':Y[(block,ability,'empty',.55)],'delta0':d0,'delta55':d1,'psi':psi})
for r in deltas:check(r['graph_delta']==D[(r['block'],r['ability'],r['mechanism_strength'])],'all18 delta exact')
for r in interactions:check(r['interaction_contrast']==P[(r['seed'],int(r['profile'][1:]))],'all9 psi exact')
for r in moderation:check(r['interaction_difference']==P[(r['block'],r['ability_high'])]-P[(r['block'],r['ability_low'])],'all6 omega exact')
for ability in plan['ability_levels']:
    check(close(math.fsum(P[(b,ability)] for b in plan['blocks'])/3,read('summary.json')['abilities'][str(ability)]['mean_interaction']),'all3 mean psi')
check(all(P[(b,1300)]==0 and D[(b,1300,0.)]>0 for b in plan['blocks']),'important high null/nonzero graph controls')
check(raw_before=={p.relative_to(RAW).as_posix():sha(p) for p in RAW.rglob('*') if p.is_file()},'all original raw unchanged')
check(all(sha(ROOT/n)==d for n,d in bindings.items()),'all25 post-verification source hashes')
receipt={'status':'VERIFIED_SAVED_RAW_ARITHMETIC_AND_SOURCE_CONTRACT_NO_NATIVE_REPLAY','checks':checks,'elapsed_seconds':time.perf_counter()-START,'source_input_sha256':bindings,'raw_before_sha256':raw_before,'raw_after_sha256':raw_before,'coverage':{'worlds':36,'events':4320,'high_semantic_event_pairs':720,'high_final_pairs':6,'contrasts':{'delta':18,'psi':9,'omega':6}},'all9rows':table,'all6omega':moderation,'all36cell_coverage':coverage,'units_vi':'Y/Delta/Psi/Omega: điểm Elo net trung bình28concepts tạiT41ngày, không nats/phần trăm/calibrated mastery','scope_vi':'Stdlib đọc raw; kiểm số học logged scalar/state và source AST, không khởi tạo native world/policy hoặc RNG. Call counters/readonly probes do frozen worker ghi, không independent runtime instrumentation.','nn_optimizer_calls':0,'native_calls':0,'new_independent_seed_blocks':0}
with (PREP/'independent_verification01.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':receipt['status'],'checks':checks,'elapsed_seconds':receipt['elapsed_seconds'],'raw_files':len(raw_before)},ensure_ascii=False))
