"""Hậu kiểm cache full–empty: joint M/R/fullpreview và cross-ready membership.

Chỉ stdlib, không import/execute source lịch sử hoặc policy/model. Main cần ROOT
owned dispatch; import module chỉ cung cấp pure helpers cho synthetic tests.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
PREP=ROOT/'artifacts/akt/local-tests/akt-research-runner-20261108-01'
BUNDLE=ROOT/'research_tracking/runs/rq1-fixed-edge-set-contrast-20261108-01'
PINS={
 'manifest.json':'906d1698482b78708cf16ce9453a8ed866e7dc0ef47cf0b8dca81c2d89b7b044',
 'event_flags.json':'1cdbba3f3d66f99f87bb14d35e3f664877d246026db473b1b399a8ab6ed9d188',
 'observed_legacy.jsonl.gz':'eeef1796da63e3fb8c9c02b4af2065491a9ff744cfe276b05f78d12f90f4206d',
 'observed_query_sidecar.jsonl.gz':'6452e88c62c4fe33b1ce759015c6ef0f1cab4c79f82d57e1a029069662564939',
 'parity.json':'4636f1caef8d121b919922928b1f785e81d62eb4be2f378424b34424fd5e980f',
}
SEEDS=(20000,20001,20002);PROFILES=('PG','PY','PYH')
VARIANTS=('graph_free','graph_package','empty_graph_package')
PHASES=['before_predict','after_predict','preview_deepcopy','after_preview_select',
        'legacy_pre_update','before_update_pairing_verified','after_update']
OLD_MARGINALS=dict(P_changed=963,S_event_changed=1080,S_concept_pairs_changed=27000,
 M_event_changed=90,M_concept_crossings=90,R_event_changed=60,R_membership_symmetric_difference=80,
 preview_concept_changed=22,preview_question_changed=22,preview_difficulty_changed=0,full_preview_tuple_changed=22)
MAX_OUTPUT=4*1024**2


def need(ok,message):
    if not ok:raise ValueError(message)


def exact(a,b):
    if type(a) is not type(b):return False
    if type(a) is float:return struct.pack('>d',a)==struct.pack('>d',b)
    if type(a) is dict:return set(a)==set(b) and all(exact(a[k],b[k]) for k in a)
    if type(a) in (tuple,list):return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    return a==b


def row_sha(row):
    raw=json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def unique(pairs):
    out={}
    for key,value in pairs:need(key not in out,'duplicate JSON key');out[key]=value
    return out


def decode(raw):
    def bad(value):raise ValueError('nonfinite JSON: '+value)
    return json.loads(raw,object_pairs_hook=unique,parse_constant=bad)


def logical_key(row):
    event=row['event_id'];learner=row['learner_id']
    need(type(event) is str and event.isdigit() and str(int(event))==event,'canonical event string')
    need(type(learner) is str and learner.count('-')==1,'seed-profile learner key')
    seed,profile=learner.split('-')
    need(seed.isdigit() and str(int(seed))==seed,'canonical seed key')
    return int(seed),profile,int(event)


def index_records(rows,expected_keys):
    need(type(rows) is list,'JSON record list required')
    indexed={}
    for row in rows:
        logical=logical_key(row);key=(row['variant'],*logical)
        need(logical in expected_keys and row['variant'] in VARIANTS and key not in indexed,'foreign/duplicate event key')
        indexed[key]=row
    need(set(indexed)=={(v,*k) for k in expected_keys for v in VARIANTS},'missing/extra full population; no intersection')
    return indexed


def paired_events(legacy,sidecars,old_flags,*,expected_keys,node_count,check=lambda:None):
    left=index_records(legacy,expected_keys);right=index_records(sidecars,expected_keys)
    need(type(old_flags) is list,'old event flags list')
    old={}
    for flag in old_flags:
        k=logical_key(flag)
        need(k in expected_keys and k not in old and flag['seed']==k[0] and flag['profile']==k[1],'old flag key drift')
        old[k]=flag
    need(set(old)==set(expected_keys),'old flags full population')
    nodes=None;events=[]
    for key in sorted(expected_keys):
        check();arms={}
        for variant in VARIANTS:
            row,meta=left[(variant,*key)],right[(variant,*key)]
            need(meta['seed']==key[0] and meta['profile']==key[1] and type(meta['seed']) is int,'sidecar seed/profile')
            need(meta['legacy_row_sha256']==row_sha(row),'sidecar legacy SHA pairing')
            need(meta['preview_is_served'] is False and meta['preview_timestamp_argument'] is None
                 and meta['preview_capture_phase']=='after_native_preview_select'
                 and meta['query_capture_phase']=='before_delegate_predict'
                 and meta['update_pairing_verified'] is True and meta['phases']==PHASES,'instrumentation phase/preview semantics')
            need(type(row['correct']) is int and row['correct'] in (0,1)
                 and exact(row['correct'],meta['correct']) and exact(row['probability'],meta['probability']),'label/probability pairing')
            need(type(row['probability']) is float and math.isfinite(row['probability']) and 0<=row['probability']<=1,'finite P')
            scores=row['mastery']
            need(type(scores) is dict and len(scores)==node_count
                 and all(type(c) is str and type(s) is float and math.isfinite(s) and 0<=s<=1 for c,s in scores.items()),'native S domain')
            if nodes is None:nodes=set(scores)
            need(set(scores)==nodes,'concept universe drift')
            for field in ('mastered','ready'):
                value=row[field]
                need(type(value) is list and len(value)==len(set(value)) and set(value)<=nodes,'stored set identity')
            need(type(meta['query']) is dict and set(meta['query'])=={'concept','question','difficulty','timestamp_iso','timestamp_ns'},'query identity fields')
            need(type(meta['preview']) is dict and set(meta['preview'])=={'concept','question','difficulty'}
                 and meta['preview']['concept'] in nodes and row['action']==meta['preview']['concept'],'legacy/fullpreview identity')
            for item in (meta['query'],meta['preview']):
                need(type(item['concept']) is str and item['concept'] in nodes and type(item['question']) is str and item['question']
                     and type(item['difficulty']) is float and math.isfinite(item['difficulty']),'valid query/preview tuple')
            arms[variant]=(row,meta)
        f,fs=arms['graph_package'];e,es=arms['empty_graph_package'];g,gs=arms['graph_free']
        need(exact(fs['query'],es['query']) and exact(fs['query'],gs['query'])
             and exact(f['correct'],e['correct']) and exact(f['correct'],g['correct']),'same1080query/y join')
        fm,em=set(f['mastered']),set(e['mastered']);fr,er=set(f['ready']),set(e['ready'])
        values=dict(P_changed=not exact(f['probability'],e['probability']),S_event_changed=not exact(f['mastery'],e['mastery']),
            S_concept_pairs_changed=sum(not exact(f['mastery'][c],e['mastery'][c]) for c in nodes),
            M_event_changed=fm!=em,M_concept_crossings=len(fm^em),R_event_changed=fr!=er,R_membership_symmetric_difference=len(fr^er),
            preview_concept_changed=fs['preview']['concept']!=es['preview']['concept'],
            preview_question_changed=fs['preview']['question']!=es['preview']['question'],
            preview_difficulty_changed=not exact(fs['preview']['difficulty'],es['preview']['difficulty']),
            full_preview_tuple_changed=not exact(fs['preview'],es['preview']))
        need(all(exact(old[key][name],value) for name,value in values.items()),'old per-event flag mismatch')
        fc,ec=fs['preview']['concept'],es['preview']['concept']
        ownf,owne,crossf,crosse=fc in fr,ec in er,fc in er,ec in fr
        membership=''.join('1' if x else '0' for x in (ownf,owne,crossf,crosse))
        if not (ownf and owne):category='OWN_RECORDED_R_MEMBERSHIP_LIMITED'
        elif crossf and crosse:category='BOTH_WINNERS_CROSS_RECORDED_READY'
        elif not crossf and not crosse:category='NEITHER_WINNER_CROSS_RECORDED_READY'
        elif not crossf:category='FULL_WINNER_NOT_IN_EMPTY_RECORDED_R'
        else:category='EMPTY_WINNER_NOT_IN_FULL_RECORDED_R'
        events.append(dict(seed=key[0],profile=key[1],event_id=str(key[2]),learner_id=f'{key[0]}-{key[1]}',**values,
            M_added=sorted(fm-em),M_removed=sorted(em-fm),R_added=sorted(fr-er),R_removed=sorted(er-fr),
            R_intersection=sorted(fr&er),R_full=sorted(fr),R_empty=sorted(er),
            full_preview=fs['preview'],empty_preview=es['preview'],query=fs['query'],
            full_preview_in_own_R=ownf,empty_preview_in_own_R=owne,full_preview_in_empty_R=crossf,empty_preview_in_full_R=crosse,
            MRA_signature=''.join('1' if values[k] else '0' for k in ('M_event_changed','R_event_changed','full_preview_tuple_changed')),
            membership_signature=membership,membership_category=category,
            interpretation_limited_by_own_R=not (ownf and owne)))
    return events


def summarize_group(rows,name):
    need(rows,'nonempty group')
    patterns=Counter(r['MRA_signature'] for r in rows);memberships=Counter(r['membership_signature'] for r in rows)
    joint=[dict(signature=f'{m}{r}{a}',M_changed=bool(m),R_changed=bool(r),full_preview_changed=bool(a),count=patterns[f'{m}{r}{a}'])
           for m in (0,1) for r in (0,1) for a in (0,1)]
    membership=[dict(signature=f'{i:04b}',count=memberships[f'{i:04b}']) for i in range(16)]
    need(sum(c['count'] for c in joint)==sum(c['count'] for c in membership)==len(rows),'complete joint partitions')
    return dict(group=name,paired_snapshots=len(rows),joint_MRA_cells=joint,membership_cells=membership,
        marginal_counts={k:sum(r[k] for r in rows) for k in OLD_MARGINALS},
        own_R_limited_snapshots=sum(r['interpretation_limited_by_own_R'] for r in rows),
        full_preview_outside_own_R=sum(not r['full_preview_in_own_R'] for r in rows),
        empty_preview_outside_own_R=sum(not r['empty_preview_in_own_R'] for r in rows),
        joint_R_preview_change_membership={label:sum(r['R_event_changed'] and r['full_preview_tuple_changed'] and r['membership_category']==label for r in rows)
            for label in ('OWN_RECORDED_R_MEMBERSHIP_LIMITED','BOTH_WINNERS_CROSS_RECORDED_READY','NEITHER_WINNER_CROSS_RECORDED_READY',
                          'FULL_WINNER_NOT_IN_EMPTY_RECORDED_R','EMPTY_WINNER_NOT_IN_FULL_RECORDED_R')})


def physical(path):
    path=path.absolute();need(path.is_relative_to(ROOT),'workspace only')
    cursor=ROOT
    for part in path.relative_to(ROOT).parts:
        cursor/=part;need(not cursor.is_symlink() and not getattr(cursor,'is_junction',lambda:False)(),'path alias')
    need(path.resolve()==path,'physical path required');return path


def bounded(path,cap):
    path=physical(path);need(path.is_file() and path.stat().st_size<=cap,'bounded regular input')
    with path.open('rb') as stream:raw=stream.read(cap+1)
    need(len(raw)<=cap and len(raw)==path.stat().st_size,'input byte drift');return raw


def main():
    started,wall=time.perf_counter(),time.time()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True);parser.add_argument('--plan-sha256',required=True)
    parser.add_argument('--source-sha256',required=True);parser.add_argument('--output-name',required=True)
    args=parser.parse_args()
    def check():need(max(time.perf_counter()-started,time.time()-wall)<=7,'cooperative worker7s exceeded')
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import worker_gate
    owner=worker_gate()
    def audit(event,values):
        if event=='subprocess.Popen' or event.startswith('socket.') or event in ('os.system','os.posix_spawn','os.spawn'):
            raise RuntimeError('network/child process denied')
        if event=='import' and str(values[0]).split('.')[0] in ('torch','numpy','pandas','sklearn','scipy','knowledge_tracing'):
            raise RuntimeError('model/scientific import denied')
    sys.addaudithook(audit)
    need(not any(n in sys.modules for n in ('torch','numpy','pandas','sklearn','scipy','knowledge_tracing')),'pure stdlib worker only')
    source=Path(__file__).resolve();plan_path=physical(args.plan)
    need(plan_path.parent==PREP and hashlib.sha256(bounded(source,65536)).hexdigest()==args.source_sha256,'source/plan location')
    plan_bytes=bounded(plan_path,32768);need(hashlib.sha256(plan_bytes).hexdigest()==args.plan_sha256,'plan pin')
    plan=decode(plan_bytes)
    need(plan['source_sha256']==args.source_sha256 and plan['inputs_sha256']==PINS and plan['expected_primary_rows']==1080
         and plan['worker_seconds']==7 and plan['outer_seconds']==10,'reviewed fixed scope')
    raw={}
    for name,pin in PINS.items():
        check();raw[name]=bounded(BUNDLE/name,2*1024**2);need(hashlib.sha256(raw[name]).hexdigest()==pin,'committed input pin: '+name)
    manifest=decode(raw['manifest.json'])
    need(manifest['status']=='completed' and manifest['candidate']=='graph_package'
         and manifest['reference']=='empty_graph_package' and manifest['both_package_enabled'] is True,'closed same-enabled-package source bundle')
    for name,pin in PINS.items():
        if name!='manifest.json':need(manifest['outputs_sha256'].get(name)==pin,'manifest selected-output binding')
    parity=decode(raw['parity.json'])
    need(parity['status']=='PASS_EXACT_LEGACY_PARITY_NEW_OBSERVATIONS_ONLY' and parity['logical_event_keys']==1080
         and parity['new_independent_N']==0,'C13 parity semantics')
    def gzip_rows(name,cap):
        rows=[];total=0
        with gzip.GzipFile(fileobj=io.BytesIO(raw[name])) as stream:
            while True:
                check();line=stream.readline(65537)
                if not line:break
                total+=len(line);need(len(line)<=65536 and line.endswith(b'\n') and total<=cap and len(rows)<3240,'decompressed line/byte/population cap')
                rows.append(decode(line))
        need(len(rows)==3240,'full3variant population');return rows
    keys={(s,p,t) for s in SEEDS for p in PROFILES for t in range(120)}
    events=paired_events(gzip_rows('observed_legacy.jsonl.gz',16*1024**2),
        gzip_rows('observed_query_sidecar.jsonl.gz',8*1024**2),decode(raw['event_flags.json']),expected_keys=keys,node_count=28,check=check)
    groups=[summarize_group(events,'pooled')]
    groups += [summarize_group([r for r in events if r['profile']==p],'profile:'+p) for p in PROFILES]
    groups += [summarize_group([r for r in events if r['seed']==s],'seed:'+str(s)) for s in SEEDS]
    groups += [summarize_group([r for r in events if r['seed']==s and r['profile']==p],f'trajectory:{s}:{p}') for s in SEEDS for p in PROFILES]
    need(groups[0]['marginal_counts']==OLD_MARGINALS and len(groups)==16,'old marginal reconstruction; no study count changes')
    need(args.output_name and len(args.output_name)<=64 and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.output_name),'exclusive output basename')
    output=physical(PREP/args.output_name);need(not output.exists(),'no overwrite/retry/resume')
    check();output.mkdir()
    try:
        def write(name,value):
            check()
            with (output/name).open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
            need((output/name).stat().st_size<=MAX_OUTPUT,'output file4MiB cap');check()
        write('summary.json',dict(role='POST_HOC_CACHED_RECORDED_READY_MEMBERSHIP_NOT_POLICY_INTERVENTION',groups=groups,
            membership_signature_order=['full_in_own_R','empty_in_own_R','full_in_empty_R','empty_in_full_R'],
            interpretation='recorded R only; C/B not captured, ownmembership not forced; no score-only explanation or causal funnel',
            new_independent_N=0,model_calls=0))
        write('event_flags.json',events)
        write('validation.json',dict(rows=1080,raw_rows_per_stream=3240,groups=16,joint_cells=128,membership_cells=256,
            exact_query_label_key_join=True,old_per_event_flags_exact=True,old_marginals_exact=True,
            own_preview_in_own_R_not_required=True,no_dropped_rows=True,inputs_sha256=PINS,
            source_sha256=args.source_sha256,plan_sha256=args.plan_sha256,new_independent_N=0,actual_model_calls=0))
        for name,pin in PINS.items():check();need(hashlib.sha256(bounded(BUNDLE/name,2*1024**2)).hexdigest()==pin,'input drift after analysis')
        write('result.json',dict(status='INNER_COMPLETE_PENDING_OWNED_OUTER_ACCEPTANCE',worker_seconds=max(time.perf_counter()-started,time.time()-wall),
            owned_gate_status=owner['status'],worker_cap_seconds=7,outputs_sha256={p.name:hashlib.sha256(bounded(p,MAX_OUTPUT)).hexdigest() for p in output.iterdir() if p.is_file()}))
        for name,pin in PINS.items():check();need(hashlib.sha256(bounded(BUNDLE/name,2*1024**2)).hexdigest()==pin,'input drift after publication')
        need(hashlib.sha256(bounded(source,65536)).hexdigest()==args.source_sha256
             and hashlib.sha256(bounded(plan_path,32768)).hexdigest()==args.plan_sha256,'source/plan drift')
        need(sum(p.stat().st_size for p in output.iterdir())<=8*1024**2,'total output8MiB cap');check()
    except BaseException as error:
        with (output/'failure.json').open('x',encoding='utf-8') as stream:json.dump(dict(status='REJECTED_KEEP_PARTIAL',type=type(error).__name__,reason=str(error)),stream)
        raise
    print(json.dumps(dict(status='PENDING_OUTER_CLEANUP_POSTWRITE_ACCEPTANCE',output=output.relative_to(ROOT).as_posix(),
        result_sha256=hashlib.sha256(bounded(output/'result.json',32768)).hexdigest())))
    check()


if __name__=='__main__':main()
