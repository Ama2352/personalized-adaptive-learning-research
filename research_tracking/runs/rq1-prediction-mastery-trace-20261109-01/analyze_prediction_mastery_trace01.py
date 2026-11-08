"""Post-hoc stdlib analysis AFTER all2160native parity, not calibration/accuracy.

Import exposes pure helpers only. main requires exact ROOT outer SHA BEFORE
parsing that receipt; never reads partial01/02, never invokes native code.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys
import time

ROOT=Path(__file__).resolve().parents[4];PREP=Path(__file__).resolve().parent
PLAN=PREP/'prediction_mastery_analysis_plan01.json'
OUTER=PREP/'prediction-mastery-native-outer03/final.json'
TRACE=PREP/'prediction-mastery-trace-attempt03'
OUTER_SHA='81cf9dd9df724338d6c8d57e01be16b5d2120d27b9730c186b5eb539803e4594'
WORKER_RUN_SHA='891a69a3546599782e530d04c3fa29b53fd832f130399404fe159a5fcab2b178'
NATIVE_PLAN_SHA='f1c6488348ce36dc64b322d623ad444e778bd6e71c3de774570ada7e2057ba3c'
OLD=ROOT/'research_tracking/runs/rq1-fixed-edge-set-contrast-20261108-01'
OLD_PINS={'manifest.json':'906d1698482b78708cf16ce9453a8ed866e7dc0ef47cf0b8dca81c2d89b7b044',
    'event_flags.json':'1cdbba3f3d66f99f87bb14d35e3f664877d246026db473b1b399a8ab6ed9d188',
    'observed_legacy.jsonl.gz':'eeef1796da63e3fb8c9c02b4af2065491a9ff744cfe276b05f78d12f90f4206d',
    'observed_query_sidecar.jsonl.gz':'6452e88c62c4fe33b1ce759015c6ef0f1cab4c79f82d57e1a029069662564939'}
SEEDS=(20000,20001,20002);PROFILES=('PG','PY','PYH');VARIANTS=('graph_package','empty_graph_package')


def need(ok,message):
    if not ok:raise ValueError(message)


def exact(a,b):
    if type(a) is not type(b):return False
    if type(a) is float:return struct.pack('>d',a)==struct.pack('>d',b)
    if type(a) is dict:return set(a)==set(b) and all(exact(a[k],b[k]) for k in a)
    if type(a) in (list,tuple):return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    return a==b


def digest(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def decode(raw):
    def pairs(items):
        out={}
        for k,v in items:need(k not in out,'duplicate JSON key');out[k]=v
        return out
    def bad(v):raise ValueError('nonfinite JSON '+v)
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)


def gates(state):
    need(type(state) is list and len(state)==5,'theta/pi/predicate vector')
    theta,pi,a,b,m=state
    need(type(theta) is float and type(pi) is float and math.isfinite(theta) and math.isfinite(pi) and 0<=pi<=1,'finite native state')
    need(type(a) is type(b) is type(m) is bool and (a,b,m)==(theta>=1250.,pi<=.55,theta>=1250. and pi<=.55),'native predicate exact')
    return a,b,m


def signature(left,right):
    a,b=gates(left),gates(right)
    value=''.join(str(int(x!=y)) for x,y in zip(a,b))
    need(value!='001','impossible changed M with both gates unchanged')
    return value


def joint_cells(signatures):
    counts=Counter(signatures);need(set(counts)<=set(f'{i:03b}' for i in range(8)) and counts['001']==0,'all8 nativeAND cells,001impossible')
    return [dict(signature=f'{i:03b}',count=counts[f'{i:03b}']) for i in range(8)]


def four_cells(values,names):
    counts=Counter(values)
    need(all(type(a) is type(b) is bool for a,b in values),'boolean4cell values')
    return [{names[0]:a,names[1]:b,'count':counts[(a,b)]} for a in (False,True) for b in (False,True)]


def finite_delta_summary(values):
    need(all(type(x) is float and math.isfinite(x) for x in values),'finite full-empty deltas')
    n=len(values)
    return dict(n=n,numerically_changed=sum(v!=0 for v in values),positive=sum(v>0 for v in values),negative=sum(v<0 for v in values),zero=sum(v==0 for v in values),
        mean=math.fsum(values)/n if n else None,mean_absolute=math.fsum(abs(v) for v in values)/n if n else None,
        minimum=min(values) if n else None,maximum=max(values) if n else None,maximum_absolute=max(map(abs,values)) if n else None)


def summarize(rows,nodes,group,only_concept=None):
    indices=list(range(len(nodes))) if only_concept is None else [only_concept]
    cells=[];theta=[];pi=[];M_any=0;theta_any=0;pi_any=0;M_concepts=0;readouts=[];byvariant={v:[] for v in VARIANTS};paired=[]
    for row in rows:
        local=[]
        for i in indices:
            f,e=row['full_state'][i],row['empty_state'][i];s=signature(f,e);cells.append(s);local.append(s)
            theta.append(float(f[0]-e[0]));pi.append(float(f[1]-e[1]))
        M_any+=any(s[2]=='1' for s in local);theta_any+=any(s[0]=='1' for s in local);pi_any+=any(s[1]=='1' for s in local)
        M_concepts+=sum(s[2]=='1' for s in local)
        q=row['query_index'];fM=gates(row['full_state'][q])[2];eM=gates(row['empty_state'][q])[2]
        if only_concept is None:
            for variant,m,r in (('graph_package',fM,row['full_raw_criterion']),('empty_graph_package',eM,row['empty_raw_criterion'])):
                need(type(r) is bool,'raw reference criterion boolean');readouts.append((m,r));byvariant[variant].append((m,r))
            paired.append((fM!=eM,row['full_raw_criterion']!=row['empty_raw_criterion']))
    joint=joint_cells(cells)
    need(sum(c['count'] for c in joint)==len(rows)*len(indices),'complete conceptpair partition')
    result=dict(group=group,paired_event_snapshots=len(rows),paired_concept_snapshots=len(cells),M_any_events=M_any,
        M_concept_crossings=M_concepts,theta_gate_any_events=theta_any,pi_gate_any_events=pi_any,joint_predicate_change_cells=joint,
        raw_theta_full_minus_empty=finite_delta_summary(theta),raw_pi_full_minus_empty=finite_delta_summary(pi))
    if only_concept is None:
        result.update(queried_arm_rows=len(readouts),queried_nativeM_vs_raw_reference=four_cells(readouts,('native_M','raw_reference_criterion')),
            queried_nativeM_vs_raw_reference_by_variant={v:four_cells(x,('native_M','raw_reference_criterion')) for v,x in byvariant.items()},
            paired_query_Mchange_vs_raw_criterion_change=four_cells(paired,('query_native_M_changed','query_raw_criterion_changed')))
    return result


def make_event(row):
    sig=[signature(f,e) for f,e in zip(row['full_state'],row['empty_state'])];q=row['query_index']
    return dict(seed=row['seed'],profile=row['profile'],event_id=row['event_id'],query_index=q,
        M_any=any(s[2]=='1' for s in sig),M_concept_crossings=sum(s[2]=='1' for s in sig),
        theta_gate_changed_indices=[i for i,s in enumerate(sig) if s[0]=='1'],pi_gate_changed_indices=[i for i,s in enumerate(sig) if s[1]=='1'],
        M_changed_indices=[i for i,s in enumerate(sig) if s[2]=='1'],
        theta_value_changed_indices=[i for i,(f,e) in enumerate(zip(row['full_state'],row['empty_state'])) if f[0]!=e[0]],
        pi_value_changed_indices=[i for i,(f,e) in enumerate(zip(row['full_state'],row['empty_state'])) if f[1]!=e[1]],
        query_native_M_changed=row['full_state'][q][4]!=row['empty_state'][q][4],
        query_raw_criterion_changed=row['full_raw_criterion']!=row['empty_raw_criterion'])


def main():
    started,wall=time.perf_counter(),time.time()
    p=argparse.ArgumentParser();p.add_argument('--outer-sha256',required=True);p.add_argument('--source-sha256',required=True)
    p.add_argument('--plan-sha256',required=True);p.add_argument('--output-name',required=True);args=p.parse_args()
    need(args.outer_sha256==OUTER_SHA and re.fullmatch('[a-f0-9]{64}',args.source_sha256) and re.fullmatch('[a-f0-9]{64}',args.plan_sha256),'exact prospective pins before reading outputs')
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import worker_gate
    owner=worker_gate()
    def audit(event,values):
        if event=='subprocess.Popen' or event.startswith('socket.') or event in ('os.system','os.posix_spawn','os.spawn'):raise RuntimeError('no child/network')
        if event=='import' and str(values[0]).split('.')[0] in ('numpy','pandas','torch','knowledge_tracing','sklearn','scipy'):raise RuntimeError('stdlib/no native')
        if event=='open' and values and isinstance(values[0],(str,bytes)):
            name=str(values[0]).replace('\\','/').lower()
            if any(t in name for t in ('/dataset/','/artifacts/simulator/corpora/','/oracle/','/realdata/','/holdout/')):raise RuntimeError('no oracle/corpus/realdata')
    sys.addaudithook(audit)
    need(not any(n in sys.modules for n in ('numpy','pandas','torch','knowledge_tracing')),'fresh stdlib only')
    def check():need(max(time.perf_counter()-started,time.time()-wall)<7,'cached analyzer worker7s')
    def read(path,cap=4*1024**2):
        check();path=path.absolute();need(path.is_relative_to(ROOT) and path.resolve()==path,'workspace physical input')
        cursor=ROOT
        for part in path.relative_to(ROOT).parts:
            cursor/=part;need(not cursor.is_symlink() and not getattr(cursor,'is_junction',lambda:False)(),'no source/input aliases')
        need(path.is_file() and path.stat().st_size<=cap,'bounded regularfile')
        with path.open('rb') as f:raw=f.read(cap+1)
        need(len(raw)<=cap and len(raw)==path.stat().st_size,'bounded stablepayload');check();return raw
    pins={}
    def pinned(path,pin,cap=4*1024**2):
        raw=read(path,cap);need(hashlib.sha256(raw).hexdigest()==pin,'SHA before parsing '+path.name)
        pins[path.relative_to(ROOT).as_posix()]=pin;return raw
    source=Path(__file__).resolve();pinned(source,args.source_sha256,65536)
    plan=decode(pinned(PLAN,args.plan_sha256,65536));need(plan['outer_sha256']==args.outer_sha256 and plan['source_sha256']==args.source_sha256,'analysisplan source/acceptedouterpin')
    outer=decode(pinned(OUTER,args.outer_sha256))  # Mandatory actualSHA verified BEFORE JSON parse.
    need(outer['status']=='ACCEPTED_FIXED_HISTORY_MASTERY_TRACE_ONLY' and outer['errors']==[] and outer['phase']=='native'
         and outer['source_before']==outer['source_after'] and outer['plan_sha256']==NATIVE_PLAN_SHA
         and outer['worker_run_sha256']==WORKER_RUN_SHA and outer['new_explicit_allocation_seconds']==300,'whole native accepted admission')
    need(not (OUTER.parent/'postwrite_rejection.json').exists() and not any((TRACE/n).exists() for n in ('failure.log','postwrite_rejection.json')),'no late rejection')
    for name,pin in outer['source_before'].items():pinned(ROOT/name,pin)
    for name,pin in outer['files_sha256'].items():pinned(PREP/name,pin)
    owned=decode(read(OUTER.parent/'owned/receipt.json'))
    need(owned['accepted'] is True and owned['cleanup_accepted'] is True and owned['job_active_after_cleanup']==0
         and owned['popen_handle_closed'] is True and owned['actual_worker_in_job_before_GO'] is True,'ownedcleanup accepted')
    need(hashlib.sha256(read(OUTER.parent/'owned/receipt.json')).hexdigest()==outer['owned_receipt_sha256'],'owned receipt pin')
    run=decode(pinned(TRACE/'worker_run.json',WORKER_RUN_SHA))
    need(run['status']=='INNER_ALL2160_LEGACY_AND18_FINAL_FINGERPRINTS_EXACT_PENDING_ROOT' and run['errors']==[]
         and run['legacy_rows_exact']==2160 and len(run['completed_trajectories'])==18 and run['profiler_restored'] is True
         and run['source_input_before']==run['source_input_after']==outer['source_before'],'all2160/18 native admission')
    nodes=run['node_order'];need(len(nodes)==len(set(nodes))==28,'exact node order')
    need(run['native_attempts']==run['native_returns'] and all(run['native_attempts'][k]==v for k,v in
        dict(predict=6480,update=2160,select=2160,ready_set=4320).items()),'actual nativecounts, analyzeradds0')
    for name,pin in run['outputs_sha256'].items():pinned(TRACE/name,pin)
    def gzip_rows(raw,limit,count):
        import io
        rows=[];size=0
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f:
            while True:
                check();line=f.readline(65537)
                if not line:break
                size+=len(line);need(size<=limit and len(line)<=65536 and line.endswith(b'\n') and len(rows)<count,'bounded complete gzip')
                rows.append(decode(line))
        need(len(rows)==count,'allrecords/gzipCRC');return rows
    oldraw={n:pinned(OLD/n,pin) for n,pin in OLD_PINS.items()}
    legacy=gzip_rows(oldraw['observed_legacy.jsonl.gz'],16*1024**2,3240)
    side=gzip_rows(oldraw['observed_query_sidecar.jsonl.gz'],8*1024**2,3240)
    def oldindex(rows):
        indexed={}
        for r in rows:
            key=r['variant'],r['learner_id'],r['event_id'];need(key not in indexed,'duplicateoldrow');indexed[key]=r
        need(len(indexed)==3240,'all3240oldkeys');return indexed
    L,S=oldindex(legacy),oldindex(side);expected={(s,p,str(t)) for s in SEEDS for p in PROFILES for t in range(120)}
    oldflags={}
    for row in decode(oldraw['event_flags.json']):
        key=row['seed'],row['profile'],row['event_id'];need(key in expected and key not in oldflags,'oldflag key/duplicates');oldflags[key]=row
    need(set(oldflags)==expected,'old1080flags')
    new={};total_bytes=0
    for ordinal,trajectory in enumerate(run['completed_trajectories'],1):
        name=f'trace-{ordinal:02d}.jsonl.gz'
        need(trajectory['trace_file']==name and trajectory['gzip_closed'] is True and trajectory['trace_records']==120,'18closed native streams')
        raw=pinned(TRACE/name,trajectory['trace_sha256']);need(len(raw)==trajectory['trace_bytes'],'closedstream size')
        rows=gzip_rows(raw,2*1024**2,120);local=set()
        for row in rows:
            k=row['seed'],row['profile'],row['event_id'];key=row['variant'],*k
            need(k in expected and row['variant'] in VARIANTS and key not in new,'all2160new unique keys')
            need((row['seed'],row['profile'],row['variant'])==(trajectory['seed'],trajectory['profile'],trajectory['variant']),'stream trajectory identity')
            oldkey=row['variant'],f'{k[0]}-{k[1]}',k[2];a,b=L[oldkey],S[oldkey]
            need(row['legacy_row_sha256']==digest(a)==b['legacy_row_sha256'] and exact(row['query'],b['query'])
                 and exact(row['probability'],a['probability']) and exact(row['full_preview'],b['preview']),'all2160query/P/fullpreview/legacy SHA')
            need(row['phase']=='PRE_CURRENT_UPDATE_NO_LABEL_IN_CAPTURE' and len(row['native_state'])==28,'pre-label states')
            mastered={n for n,state in zip(nodes,row['native_state']) if gates(state)[2]}
            need(mastered==set(a['mastered']),'all2160M fromtheta/pi matches cachedlegacy')
            refs=row['raw_references'];need(len(refs)==3 and len({r['question'] for r in refs})==3
                 and sorted(r['difficulty'] for r in refs)==[1050.,1200.,1350.]
                 and all(type(r['probability']) is float and math.isfinite(r['probability']) and 0<=r['probability']<=1 for r in refs),'rawrefs finite/real difficulties')
            need(row['raw_reference_mean']==sum(r['probability'] for r in refs)/3
                 and type(row['raw_reference_criterion']) is bool and row['raw_reference_criterion']==(row['raw_reference_mean']>=.5637150147511514),'raw reference arithmetic')
            new[key]=row;local.add(k)
        need(local=={(trajectory['seed'],trajectory['profile'],str(t)) for t in range(120)},'perstream120exact keys/CRC')
        total_bytes+=sum(len(json.dumps(r)) for r in rows);need(total_bytes<=16*1024**2,'allnewtrace unpackedbound')
    need(set(new)=={(v,*k) for v in VARIANTS for k in expected},'all2160joined, no intersection/subset')
    paired=[];events=[]
    for key in sorted(expected):
        check();f,e=(new[(v,*key)] for v in VARIANTS)
        need(exact(f['query'],e['query']),'samecurrent fullquery identity1080')
        oldkey=f'{key[0]}-{key[1]}',key[2]
        need(exact(L[('graph_package',*oldkey)]['correct'],L[('empty_graph_package',*oldkey)]['correct']),'samecached y1080')
        row=dict(seed=key[0],profile=key[1],event_id=key[2],query_index=nodes.index(f['query']['concept']),
            full_state=f['native_state'],empty_state=e['native_state'],full_raw_criterion=f['raw_reference_criterion'],empty_raw_criterion=e['raw_reference_criterion'])
        event=make_event(row);prior=oldflags[key]
        need(event['M_any']==prior['M_event_changed'] and event['M_concept_crossings']==prior['M_concept_crossings'],
             'per-event oldMSET and separateconceptcrossings reconciliation')
        paired.append(row);events.append(event)
    specs=[('pooled',lambda r:True)]+[(f'profile:{p}',lambda r,p=p:r['profile']==p) for p in PROFILES]
    specs += [(f'seed:{s}',lambda r,s=s:r['seed']==s) for s in SEEDS]
    specs += [(f'trajectory:{s}:{p}',lambda r,s=s,p=p:r['seed']==s and r['profile']==p) for s in SEEDS for p in PROFILES]
    groups=[]
    for name,predicate in specs:check();groups.append(summarize([r for r in paired if predicate(r)],nodes,name))
    concepts=[]
    for i,n in enumerate(nodes):check();concepts.append(dict(concept=n,**summarize(paired,nodes,'pooled',i)))
    need(groups[0]['M_any_events']==90 and groups[0]['paired_concept_snapshots']==30240,'90EVENTS nothardcoded90concepts; all30240')
    need(sum(c['M_concept_crossings'] for c in concepts)==groups[0]['M_concept_crossings'],'perconcept reconstruction')
    need(args.output_name=='prediction-mastery-analysis-attempt01','one new fixedoutputname')
    output=PREP/args.output_name;need(not output.exists(),'exclusive/no retry');check();output.mkdir()
    try:
        def write(name,value):
            check();raw=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode();need(len(raw)<=4*1024**2,'small analysisoutput')
            with (output/name).open('xb') as f:f.write(raw)
            check()
        write('summary.json',dict(kind='POST_HOC_NATIVE_BOOLEAN_MASTERY_RAW_REFERENCE_READOUT_NOT_CALIBRATION',node_order=nodes,
            groups=groups,per_concept_pooled=concepts,units=dict(theta='native estimated Elo-scale units, notteachertruth',pi='dimensionless nativeuncertaintyparameter',
            event='reusedfixedquerysnapshot',concept_pair='oneconcept at onepairedfixedsnapshot',queried_arm_row='onevariant queriedconcept snapshot'),
            new_independent_N=0,scope='Rawreferencecriterion is notcalibratedV1/knowledgeprobability/truth; noaccuracy/causal/CI/pvalues'))
        write('event_flags.json',events)
        write('validation.json',dict(paired_events=1080,arm_rows=2160,paired_concept_snapshots=30240,groups=16,per_concept_rows=28,
            M_any_events_equals_old90=True,M_concept_crossings_separately_counted=True,impossible001_zero=True,
            all18CRC=True,all2160legacy_admission=True,legacy_admission_scope='InheritedfrozenROOTouterS28Rparity; analyzerindependentlyP/M/query/previewchecks',all_query_label_joins=True,no_rows_dropped=True,
            outer_sha256=args.outer_sha256,worker_run_sha256=WORKER_RUN_SHA,inputs_sha256=pins,source_sha256=args.source_sha256,
            plan_sha256=args.plan_sha256,native_calls=0,oracle_reads=0,new_independent_N=0))
        for name,pin in list(pins.items()):pinned(ROOT/name,pin)
        write('result.json',dict(status='INNER_CACHED_MASTERY_ANALYSIS_PENDING_ROOT_OWNED_ACCEPTANCE',worker_seconds=max(time.perf_counter()-started,time.time()-wall),
            cap_seconds=7,owned_gate=owner,outputs_sha256={f.name:hashlib.sha256(read(f)).hexdigest() for f in output.iterdir() if f.is_file()}))
        check()
    except BaseException as exc:
        with (output/'failure.json').open('x',encoding='utf-8') as f:json.dump(dict(status='REJECTED_KEEP_PARTIAL',type=type(exc).__name__,reason=str(exc)),f)
        raise
    print(json.dumps(dict(status='PENDING_ROOT_POSTWRITE_OWNED_ACCEPTANCE',result_sha256=hashlib.sha256(read(output/'result.json')).hexdigest())))
    check()


if __name__=='__main__':main()


