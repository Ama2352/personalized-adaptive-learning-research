"""Chuẩn bị hậu kiểm stdlib: source-reconstructed C/B/key, không chạy native policy."""
import argparse
import ast
from collections import Counter
import csv
import gzip
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OLD = 'research_tracking/runs/rq1-fixed-edge-set-contrast-20261108-01/'
CROSS = 'research_tracking/runs/rq1-cross-ready-membership-20261109-01/'
PAPER = 'paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/'
NOTEBOOK = PAPER+'source/adaptive_lms_bkt_gam_graph_gam_kt_research_ready_v2_1.ipynb'
DATA = PAPER+'data/simulator_inputs/'
PROVENANCE = 'research_tracking/runs/rq1-query-observability-reproduction-20261108-01/historical__source_provenance.json'
JOIN = 'scripts/research/analyze_rq1_cross_ready.py'
CONTRACT = PREP/'rq1_fixed_controller_candidates_contract02_20261109.md'
PINS = {
    OLD+'manifest.json':'906d1698482b78708cf16ce9453a8ed866e7dc0ef47cf0b8dca81c2d89b7b044',
    OLD+'observed_legacy.jsonl.gz':'eeef1796da63e3fb8c9c02b4af2065491a9ff744cfe276b05f78d12f90f4206d',
    OLD+'observed_query_sidecar.jsonl.gz':'6452e88c62c4fe33b1ce759015c6ef0f1cab4c79f82d57e1a029069662564939',
    OLD+'event_flags.json':'1cdbba3f3d66f99f87bb14d35e3f664877d246026db473b1b399a8ab6ed9d188',
    OLD+'parity.json':'4636f1caef8d121b919922928b1f785e81d62eb4be2f378424b34424fd5e980f',
    OLD+'historical_runner.py':'402dca905694d850f126e41f3b5dcc91b327e986ae2cfbb240dda739eed8dd45',
    OLD+'source__paper2_reference.py':'a12edc72a00ad980799ec50ff26f0cb68f2529e3699e8a57e4f11295693c2cd1',
    PROVENANCE:'8b296d89d869e90696be04592a5dc627e617af6c39055a863b9eb88b6cd5560d',
    NOTEBOOK:'353f487a3d6ed3826f2546d03c0aa2ad2279cf5c4b7fe8e375f4cafb0408280f',
    DATA+'nodes.csv':'6db464d1fd3df5d4215d51c9f90dc0f7e24f252517252784c80bdb5fa6291650',
    DATA+'edges.csv':'ecd910d8df52f8790997391de657ea0f9e8357446212c168b73e500d0facc2fb',
    DATA+'concept_to_chapter_map.csv':'aa99cffb251ce6757258d2e87fe707455bc74b6b3917ead1acf48c5e96ee0a17',
    JOIN:'423968f864c84c8fc66a6678bf9351b195cc3ce47d38eb8696ddbab0ee830398',
    CROSS+'manifest.json':'057a968bef91bfb9111002119c06e72b4b67605358a770bcde848e173a3b0919',
    CROSS+'summary.json':'a6860a4f01ea650292bd9c7d237e21048aa0e219e85144c299f3e0e3d1abd3c4',
}
DEFS = {'CoverageAwareSelectorMixin':(11,'fc616cb9d5067419950cfc4a5e0ae0c2a02afc0d78b6ae86dd72f87224f42310'),
        'GAMKTPolicy':(13,'99d10d26d5c3eee9bf48c6530c8a7ed5ea885d1585750316dd6d0db41f8925f1')}
SEEDS = (20000,20001,20002)
PROFILES = ('PG','PY','PYH')
VARIANTS = ('graph_package','empty_graph_package')


def need(ok,message):
    if not ok:
        raise ValueError(message)


def source_ready(nodes, parents, mastered, visits):
    """Literal source rule; order reconstructed from nodes, not observed in set trace."""
    unmastered = [c for c in nodes if c not in mastered]
    ready = [c for c in unmastered if all(p in mastered or visits[p] >= 6 for p in parents[c])]
    if ready:
        return ready,'frontier'
    if not unmastered:
        return list(nodes),'all_mastered'
    deficits = {c:sum(p not in mastered for p in parents[c]) for c in unmastered}
    minimum = min(deficits.values())
    return [c for c in unmastered if deficits[c] == minimum],'minimum_unresolved'


def controller(nodes,parents,chapters,mastered,stored_ready,scores,visits,recent,current_chapter,expected_cid):
    """Pure arithmetic only: never calls policy; never predicts qid/difficulty."""
    universe = set(nodes)
    need(len(nodes) == len(universe) and universe and set(parents) == set(scores) == set(visits) == universe
         and universe <= set(chapters),
         'exact controller domain')
    need(set(mastered) <= universe and len(stored_ready) == len(set(stored_ready)) and set(stored_ready) <= universe,
         'M/R domain')
    need(all(type(v) is int and v >= 0 for v in visits.values()) and len(recent) <= 3 and set(recent) <= universe,
         'past-only selector context')
    need(all(type(v) is float and math.isfinite(v) and 0 <= v <= 1 for v in scores.values()),'finite native scores')
    need(all(set(ps) <= universe for ps in parents.values()),'parent domain')
    ready,ready_branch = source_ready(nodes,parents,set(mastered),visits)
    need(set(ready) == set(stored_ready),'source M-to-R membership mismatch: STOP')
    candidates = list(ready); branch = 'unchanged'
    if len(set(recent)) == 1 and len(recent) == 3:
        alternatives = [c for c in candidates if c != recent[-1]]
        branch = 'anti_repeat_within_R'
        if not alternatives:
            alternatives = [c for c in nodes if c != recent[-1]
                            and all(p in mastered or visits[p] >= 6 for p in parents[c])]
            branch = 'escape_all_nodes'
        if alternatives:
            candidates = alternatives
        else:
            branch = 'anti_repeat_no_alternative_keep_R'
    need(candidates,'nonempty source C')
    minimum = min(visits[c] for c in candidates)
    balanced = [c for c in candidates if visits[c] <= minimum+1]
    def key(c):
        return scores[c],0 if chapters[c] == current_chapter else 1,visits[c],c
    chosen = min(balanced,key=key)
    need(chosen == expected_cid,'native CID ranking mismatch: STOP, no hidden-state fill')
    need(chosen in balanced and set(balanced) <= set(candidates),'CID in B subset C')
    return dict(R=ready,C=candidates,B=balanced,C_branch=branch,R_branch=ready_branch,
                selected=chosen,selected_key=list(key(chosen)),minimum_visits=minimum)


def advance_logged(visits,recent,cid,chapters):
    """Only AFTER current snapshot; no answer/probability/preview argument."""
    need(cid in visits,'logged CID domain')
    visits[cid] += 1
    recent.append(cid)
    if len(recent) > 3:
        del recent[0]
    return chapters[cid]


def definitions(raw, decode):
    notebook = decode(raw[NOTEBOOK]); provenance = decode(raw[PROVENANCE])
    need(provenance['notebook_sha256'] == PINS[NOTEBOOK],'native notebook provenance')
    constants = {};found = {}
    for index,cell in enumerate(notebook['cells']):
        if cell['cell_type'] != 'code':
            continue
        text = ''.join(cell['source']); tree = ast.parse(text)
        for node in tree.body:
            if isinstance(node,ast.ClassDef) and node.name in DEFS:
                need(node.name not in found,'duplicate native definition')
                found[node.name] = index,hashlib.sha256(ast.get_source_segment(text,node).encode()).hexdigest()
            if isinstance(node,ast.Assign):
                for target in node.targets:
                    if isinstance(target,ast.Name) and target.id in ('MAX_CONSECUTIVE_CONCEPT','MIN_PREREQUISITE_EXPOSURES','MASTERY_ELO'):
                        need(target.id not in constants,'duplicate native constant')
                        constants[target.id] = ast.literal_eval(node.value)
    need(found == DEFS and constants == dict(MAX_CONSECUTIVE_CONCEPT=3,MIN_PREREQUISITE_EXPOSURES=6,MASTERY_ELO=1250.),
         'exact source rules/constants, no exec')
    for name,(cell,digest) in DEFS.items():
        need(provenance['definitions'][name] == dict(cell=cell,sha256=digest),'C13 exact class provenance')


def native_chapter_mapping(nodes, rows):
    """Loader lines61–67: full dict, last wins, required node coverage, no default."""
    need(type(rows) is list and all(type(r) is dict and type(r.get('concept_id')) is str and r['concept_id']
         and type(r.get('chapter')) is str and r['chapter'] for r in rows),'native chapter metadata strings')
    chapters={r['concept_id']:r['chapter'] for r in rows}
    missing=sorted(set(nodes)-set(chapters))
    need(not missing,'native chapter lookup missing required node: '+','.join(missing))
    counts=Counter(r['concept_id'] for r in rows)
    certificate=dict(node_count=len(nodes),input_chapter_rows=len(rows),input_unique_chapter_ids=len(chapters),
        missing_required_node_ids=missing,extra_unused_chapter_ids=sorted(set(chapters)-set(nodes)),
        duplicate_chapter_ids=sorted(n for n,c in counts.items() if c>1),
        native_chapter_names_for_nodes=sorted({chapters[n] for n in nodes}),
        resolution='NATIVE_FULL_DICT_LAST_WINS_REQUIRED_NODE_LOOKUP_NO_DEFAULT')
    return chapters,certificate


def domain(raw):
    def rows(name):
        return list(csv.DictReader(io.StringIO(raw[DATA+name].decode('utf-8-sig'))))
    nodes = [r['concept_id'] for r in rows('nodes.csv')]
    need(len(nodes) == len(set(nodes)) == 28,'native node order/domain28')
    chapters,chapter_coverage = native_chapter_mapping(nodes,rows('concept_to_chapter_map.csv'))
    parents = {n:[] for n in nodes}; children = {n:[] for n in nodes}; edges = rows('edges.csv')
    pairs = [(r['source'],r['target']) for r in edges]
    need(len(pairs) == len(set(pairs)) == 31 and all(p in parents and c in parents and p != c for p,c in pairs),'fixed full controller31edges')
    for p,c in pairs:
        parents[c].append(p);children[p].append(c)
    degree = {n:len(parents[n]) for n in nodes};pending = [n for n in nodes if not degree[n]];visited=0
    while pending:
        n = pending.pop();visited += 1
        for c in children[n]:
            degree[c] -= 1
            if not degree[c]:pending.append(c)
    need(visited == 28,'fixed controller DAG')
    return nodes,parents,chapters,chapter_coverage


def summarize(rows,name):
    patterns = Counter(''.join('1' if r[k] else '0' for k in ('M_changed','R_changed','C_changed','B_changed','CID_changed')) for r in rows)
    bcid = Counter((r['B_changed'],r['CID_changed']) for r in rows)
    return dict(group=name,paired_snapshots=len(rows),joint_MRCBcid=[dict(signature=f'{i:05b}',count=patterns[f'{i:05b}']) for i in range(32)],
        B_CID_cells=[dict(B_changed=b,CID_changed=a,count=bcid[(b,a)]) for b in (False,True) for a in (False,True)],
        R_changes_C_same=sum(r['R_changed'] and not r['C_changed'] for r in rows),
        C_changes_B_same=sum(r['C_changed'] and not r['B_changed'] for r in rows),
        B_changes_CID_same=sum(r['B_changed'] and not r['CID_changed'] for r in rows),
        same_B_CID_changed_local_key_explanation=sum(not r['B_changed'] and r['CID_changed'] for r in rows),
        qid_or_difficulty_only_preview_changes=sum(r['full_preview_changed'] and not r['CID_changed'] for r in rows),
        prior_strata={label:dict(count=len(selected),C_changed=sum(r['C_changed'] for r in selected),B_changed=sum(r['B_changed'] for r in selected),
            CID_changed=sum(r['CID_changed'] for r in selected),same_B_CID_changed=sum(not r['B_changed'] and r['CID_changed'] for r in selected))
            for label,selected in (
                ('R_changed_preview_kept',[r for r in rows if r['R_changed'] and not r['full_preview_changed']]),
                ('M_R_kept_preview_changed',[r for r in rows if not r['M_changed'] and not r['R_changed'] and r['full_preview_changed']]),
                ('M_R_preview_changed',[r for r in rows if r['M_changed'] and r['R_changed'] and r['full_preview_changed']]))})


def main():
    started,wall = time.perf_counter(),time.time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-sha256',required=True);parser.add_argument('--contract-sha256',required=True)
    parser.add_argument('--output-name',required=True)
    args = parser.parse_args()
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import worker_gate
    owner = worker_gate()
    def audit(event,values):
        if event == 'subprocess.Popen' or event.startswith('socket.') or event in ('os.system','os.posix_spawn','os.spawn'):
            raise RuntimeError('child/network forbidden')
        if event == 'import' and str(values[0]).split('.')[0] in {'knowledge_tracing','numpy','pandas','torch','sklearn','scipy'}:
            raise RuntimeError('native/scientific import forbidden')
    sys.addaudithook(audit)
    need(not any(n in sys.modules for n in ('knowledge_tracing','numpy','pandas','torch','sklearn','scipy')),'stdlib-only process')
    def check():
        need(max(time.perf_counter()-started,time.time()-wall) <= 7,'worker7s cooperative cap')
    def read(path,cap=2*1024**2):
        check();path=path.absolute();need(path.is_relative_to(ROOT),'workspace only')
        cursor=ROOT
        for part in path.relative_to(ROOT).parts:
            cursor/=part;need(not cursor.is_symlink() and not getattr(cursor,'is_junction',lambda:False)(),'input/output alias')
        need(path.resolve() == path and path.is_file() and path.stat().st_size <= cap,'bounded regular input')
        with path.open('rb') as stream:data=stream.read(cap+1)
        need(len(data) <= cap and len(data) == path.stat().st_size,'bounded stable input');check();return data
    digest = lambda b:hashlib.sha256(b).hexdigest()
    source=Path(__file__).resolve()
    need(digest(read(source,65536)) == args.source_sha256 and digest(read(CONTRACT,32768)) == args.contract_sha256,'source/contract pins')
    raw={n:read(ROOT/n) for n in PINS}
    need(all(digest(raw[n]) == h for n,h in PINS.items()),'exact frozen input pins')
    spec=importlib.util.spec_from_file_location('fixed_join_frozen',ROOT/JOIN)
    join=importlib.util.module_from_spec(spec);spec.loader.exec_module(join)  # Definitions only, SHA423968 reviewed; no main.
    decode=join.decode
    manifest=decode(raw[OLD+'manifest.json']);cross_manifest=decode(raw[CROSS+'manifest.json'])
    need(manifest['status'] == cross_manifest['status'] == 'completed','closed input bundles')
    for n in ('observed_legacy.jsonl.gz','observed_query_sidecar.jsonl.gz','event_flags.json','parity.json','historical_runner.py','source__paper2_reference.py'):
        need(manifest['outputs_sha256'][n] == PINS[OLD+n],'old manifest output binding')
    need(cross_manifest['outputs_sha256']['summary.json'] == PINS[CROSS+'summary.json'],'closed32 summary binding')
    parity=decode(raw[OLD+'parity.json'])
    need(parity['status'] == 'PASS_EXACT_LEGACY_PARITY_NEW_OBSERVATIONS_ONLY' and parity['logical_event_keys'] == 1080
         and parity['new_independent_N'] == 0,'C13 same-source parity provenance')
    definitions(raw,decode);nodes,parents,chapters,chapter_coverage=domain(raw);idx={n:i for i,n in enumerate(nodes)}
    def gzip_rows(name,cap):
        rows=[];size=0
        with gzip.GzipFile(fileobj=io.BytesIO(raw[OLD+name])) as stream:
            while True:
                check();line=stream.readline(65537)
                if not line:break
                size+=len(line);need(len(line)<=65536 and line.endswith(b'\n') and size<=cap and len(rows)<3240,'gzip budget/population')
                rows.append(decode(line))
        need(len(rows)==3240,'exact3240 raw rows/CRC');return rows
    legacy=gzip_rows('observed_legacy.jsonl.gz',16*1024**2);side=gzip_rows('observed_query_sidecar.jsonl.gz',8*1024**2)
    keys={(s,p,t) for s in SEEDS for p in PROFILES for t in range(120)}
    paired=join.paired_events(legacy,side,decode(raw[OLD+'event_flags.json']),expected_keys=keys,node_count=28,check=check)
    left=join.index_records(legacy,keys);right=join.index_records(side,keys);base={(r['seed'],r['profile'],int(r['event_id'])):r for r in paired}
    cross_summary=decode(raw[CROSS+'summary.json'])
    group_specs=[('pooled',lambda r:True)]+[(f'profile:{p}',lambda r,p=p:r['profile']==p) for p in PROFILES]
    group_specs += [(f'seed:{s}',lambda r,s=s:r['seed']==s) for s in SEEDS]
    group_specs += [(f'trajectory:{s}:{p}',lambda r,s=s,p=p:r['seed']==s and r['profile']==p) for s in SEEDS for p in PROFILES]
    for name,predicate in group_specs:
        old_group=next(g for g in cross_summary['groups'] if g['group']==name)
        need(join.summarize_group([r for r in paired if predicate(r)],name)==old_group,'all16 old marginal/joint reconstructions')
    events=[];validated=0
    for seed in SEEDS:
        for profile in PROFILES:
            visits={n:0 for n in nodes};recent=[];chapter=None
            for t in range(120):
                check();key=(seed,profile,t);prior=base[key];arms={}
                for variant in VARIANTS:
                    row=left[(variant,*key)];meta=right[(variant,*key)]
                    need(row['action'] == meta['preview']['concept'],'legacy CID/fullpreview CID identity')
                    arms[variant]=controller(nodes,parents,chapters,set(row['mastered']),row['ready'],row['mastery'],visits,recent,chapter,row['action'])
                    validated+=1
                f,e=(arms[v] for v in VARIANTS);fB,eB=set(f['B']),set(e['B'])
                record=dict(seed=seed,profile=profile,event_id=str(t),query=prior['query'],
                    past_visits=[visits[n] for n in nodes],past_recent=[idx[n] for n in recent],past_chapter=chapter,
                    M_changed=prior['M_event_changed'],R_changed=prior['R_event_changed'],C_changed=set(f['C'])!=set(e['C']),B_changed=fB!=eB,
                    CID_changed=f['selected']!=e['selected'],full_preview_changed=prior['full_preview_tuple_changed'],
                    full_preview=prior['full_preview'],empty_preview=prior['empty_preview'],
                    full_CID_in_empty_B=f['selected'] in eB,empty_CID_in_full_B=e['selected'] in fB,
                    C_added=[idx[n] for n in sorted(set(f['C'])-set(e['C']))],C_removed=[idx[n] for n in sorted(set(e['C'])-set(f['C']))],
                    B_added=[idx[n] for n in sorted(fB-eB)],B_removed=[idx[n] for n in sorted(eB-fB)])
                need(record['CID_changed'] == prior['preview_concept_changed'],'CID not fulltuple conflation')
                for label,arm in (('full',f),('empty',e)):
                    record[label]=dict(R=[idx[n] for n in arm['R']],C=[idx[n] for n in arm['C']],B=[idx[n] for n in arm['B']],
                        R_branch=arm['R_branch'],C_branch=arm['C_branch'],selected_index=idx[arm['selected']],native_key=arm['selected_key'])
                events.append(record)
                chapter=advance_logged(visits,recent,prior['query']['concept'],chapters)  # Current y/preview are never inputs.
    need(validated==2160 and len(events)==1080,'all2160 sourceR/CID, no partial claims')
    groups=[summarize([r for r in events if predicate(r)],name) for name,predicate in group_specs]
    need(all(sum(c['count'] for c in g['joint_MRCBcid'])==sum(c['count'] for c in g['B_CID_cells'])==g['paired_snapshots'] for g in groups),'all32/4 zero-preserving partitions')
    need(args.output_name and len(args.output_name)<=80 and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.output_name),'direct prep output')
    output=PREP/args.output_name;need(not output.exists(),'no overwrite/retry');check();output.mkdir()
    try:
        def write(name,value):
            check();data=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
            need(len(data)<=4*1024**2,'small output4MiB cap')
            with (output/name).open('xb') as stream:stream.write(data)
            check()
        write('summary.json',dict(role='POST_HOC_SOURCE_RECONSTRUCTED_FIXED_CONTROLLER_NOT_MEDIATION',groups=groups,node_order=nodes,
            chapter_coverage=chapter_coverage,
            scope='CID only, C/B reconstructed not directlylogged, fixedcontrollergraph, no calibratedmastery or newN'))
        write('event_flags.json',events)
        write('validation.json',dict(paired_snapshots=1080,source_R_membership_exact=2160,source_CID_exact=2160,
            old_groups_reconciled=16,raw_rows_per_stream=3240,joint_cells=512,B_CID_cells=64,observed_R_order_parity_claimed=False,
            node_index_mapping='summary.json/node_order',inputs_sha256=PINS,source_sha256=args.source_sha256,contract_sha256=args.contract_sha256,
            chapter_coverage=chapter_coverage,
            original_fixed_runner_recovered_git='e4e6a262bddcdd3b6b6de8c1115ef0eb54b3240a',new_independent_N=0,native_model_simulator_calls=0))
        need(all(digest(read(ROOT/n))==h for n,h in PINS.items()),'input drift after computation')
        need(digest(read(source,65536))==args.source_sha256 and digest(read(CONTRACT,32768))==args.contract_sha256,'source/contract drift')
        write('result.json',dict(status='INNER_COMPLETE_PENDING_ROOT_OWNED_POSTWRITE_ACCEPTANCE',worker_seconds=max(time.perf_counter()-started,time.time()-wall),
            cap_seconds=7,owned_gate_status=owner['status'],outputs_sha256={p.name:digest(read(p,4*1024**2)) for p in output.iterdir()}))
        need(sum(p.stat().st_size for p in output.iterdir())<=8*1024**2,'total8MiB outputs');check()
    except BaseException as error:
        with (output/'failure.json').open('x',encoding='utf-8') as stream:
            json.dump(dict(status='REJECTED_KEEP_PARTIAL',type=type(error).__name__,reason=str(error)),stream)
        raise
    print(json.dumps(dict(status='PENDING_ROOT_OWNED_POSTWRITE_ACCEPTANCE',output=output.relative_to(ROOT).as_posix(),result_sha256=digest(read(output/'result.json')))))
    check()


if __name__ == '__main__':
    main()
